from __future__ import annotations

from typing import TYPE_CHECKING

import pygame
from src.config.controls_manager import get_action_key
from src.config.settings_manager import get_gameplay_settings
from src.config.units import UNIT_CONFIGS
from src.menus.OptionsMenu import OptionsMenu
from src.units.Bateau import BateauRouge, BateauVert
from src.units.Chaloupe import ChaloupeRouge, ChaloupeVerte
from src.units.Eclaireur import EclaireurRouge, EclaireurVert
from src.units.Paquebot import PaquebotRouge, PaquebotVert
from src.units.PompePetroliere import PompePetroliereRouge, PompePetroliereVert
from src.units.Sousmarin import SousMarinRouge, SousMarinVert

if TYPE_CHECKING:
    from src.core.Game import Game


class EventHandler:
    """Gestionnaire d'événements pour le jeu."""

    def __init__(self, game: Game):
        """Initialise le gestionnaire d'événements avec une référence au jeu.

        Args:
            game (Game): Référence au jeu.
        """
        self.game = game
        self.last_hud_toggle_time = 0
        self.hud_toggle_cooldown = 200  # 200ms de cooldown

    def handle_events(self):
        """Gère tous les événements ponctuels.

        Returns:
            (bool): True si le jeu doit continuer, False sinon.
        """

        self.handle_continuous_input()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            # Gestion des événements HUD
            self.game.hud.petrole_green.handle_event(event, self.game.nbPompePetroliereVert)
            self.game.hud.petrole_red.handle_event(event, self.game.nbPompePetroliereRouge)
            self.game.hud.timer.handle_event(event)

            # Gestion du changement de marée
            if self.game.hud.timer.maree_changed:
                self.game.initializer.switch_layer()

                # Reconstruire la map
                if hasattr(self.game.renderer, "map_needs_refresh") and self.game.renderer.map_needs_refresh:
                    self.game.renderer.refresh_map()

                # Gestion des zones quantiques
                if self.game.hud.timer.maree_haute:
                    self.game.quantique()

                # On charge les obstacles
                self.game.setObstacles()

                # Marquer le changement comme traité
                self.game.hud.timer.maree_changed = False

            # Gestion des touches
            elif event.type == pygame.KEYDOWN:
                self.handle_keydown_events(event)

            # Gestion des clics souris
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_events(event)

        return True

    def handle_keydown_events(self, event: pygame.event):
        """Gère les événements de touches pressées.

        Args:
            event (pygame.event): Événement pygame.
        """

        # Menu Options
        if event.key == get_action_key("OPTIONS"):
            options_menu = OptionsMenu(self.game.screen)
            if options_menu.run():
                settings = get_gameplay_settings()
                if self.game.scale_unit != settings["SCALE"]:
                    self.game.scale_unit = settings["SCALE"]
                    if len(self.game.units) > 2:  # On ignore les plateformes pétrolieres
                        self.game.units[2].reload_sprites()

        # Création d'unité
        elif event.key == get_action_key("CREATE_UNIT"):
            hud = self.game.hud
            selection_index = hud.popup_selection
            team_key = hud.popup_team  # 'red' ou 'green'
            # Récupérer la clé de config de l'unité (le type d'unité)
            if selection_index < 0 or selection_index >= len(hud.unit_config_keys):
                return
            config_key = hud.unit_config_keys[selection_index]

            # Vérifier le coût en pétrole
            cost = UNIT_CONFIGS.get(config_key, {}).get("cost")
            if cost and self.check_cost(team_key, cost):
                self.apply_cost(config_key, team_key, cost)
                self.spawn_unit(config_key, team_key)

        # Volume
        elif event.key == get_action_key("VOLUME_UP"):
            self.game.sound.increase_volume()
        elif event.key == get_action_key("VOLUME_DOWN"):
            self.game.sound.decrease_volume()

        # HUD
        elif event.key == get_action_key("HUD_LEFT"):
            self.game.hud.popup_selection = (self.game.hud.popup_selection - 1) % len(self.game.hud.unit_names)
        elif event.key == get_action_key("HUD_RIGHT"):
            self.game.hud.popup_selection = (self.game.hud.popup_selection + 1) % len(self.game.hud.unit_names)
        elif event.key == get_action_key("HUD_TOGGLE"):
            self.game.hud.switch()

        # Temps
        elif event.key == get_action_key("TIME_SPEED"):
            # Cycler la vitesse du temps
            new_speed = self.game.hud.timer.cycle_speed()
            # Synchroniser la vitesse du pétrole avec le timer
            self.game.hud.petrole_red.set_speed(new_speed)
            self.game.hud.petrole_green.set_speed(new_speed)

            # Synchorniser les vitesses de bateaux avec la nouvelle vitesse
            for unit in self.game.units:
                # Verification sur l'entité
                if hasattr(unit, "is_moving") and unit.is_moving:
                    # unit.speed * new_speed
                    if unit.target_position:
                        unit.move_to(unit.target_position[0], unit.target_position[1])

        # Team
        elif event.key == get_action_key("SWITCH_TEAM"):
            # Changer d'équipe dans le HUD:
            self.game.hud.toggle_popup_team()
            self.game.hud.switch_team()
            self.game.overlay_menu.switch_team()

        # Mines
        elif event.key == get_action_key("MINE"):
            world_x, world_y = self.screen_to_world_coordinates(pygame.mouse.get_pos())

            # Si un sous-marin est sélectionné, poser une mine
            if (
                self.game.selected_unit
                and self.game.selected_unit.is_alive
                and hasattr(self.game.selected_unit, "special_ability")
                and self.game.selected_unit.special_ability == "mines"
            ):
                x, y = self.game.selected_unit.position

                # Vérifier que la position n'est pas dans un obstacle
                from src.utils.Utils import point_in_many_polygons

                if not point_in_many_polygons(self.game.obstacles, (x, y)):
                    # Utiliser la méthode spéciale pour le sous-marin
                    if hasattr(self.game.selected_unit, "can_place_mine") and self.game.selected_unit.can_place_mine():
                        self.game.selected_unit.place_mine(x, y)

        # Debbug Q-Learning
        self._input_qlearning(event)

    def handle_mouse_events(self, event: pygame.event):
        """Gère les événements de souris.

        Args:
            event (pygame.event): Événement de souris à traiter.
        """

        # Si le jeu est gagné, gérer les clics sur l'écran de victoire
        if self.game.game_won and event.button == 1:
            self.game.handle_victory_click(pygame.mouse.get_pos())
            return

        # Gérer les clics sur le menu superposé
        self.game.overlay_menu.handle_event(event)

        # Clic gauche
        if event.button == get_action_key("SELECT_MOVE"):
            # Séléctionner une unité dans le HUD
            if hasattr(self.game, "hud") and hasattr(self.game.hud, "popup_icon_rects"):
                # Ne permettre les clics sur le popup QUE si le HUD est visible
                if getattr(self.game.hud, "show", False):
                    rects = self.game.hud.popup_icon_rects
                    if rects:
                        pos = getattr(event, "pos", None)
                        if pos:
                            for i, rect in enumerate(rects):
                                if rect is None:
                                    continue
                                if rect.collidepoint(pos):
                                    # Mettre à jour la sélection dans le HUD
                                    self.game.hud.popup_selection = i
                                    # Appeler le callback si défini
                                    callback = getattr(self.game.hud, "unit_select_callback", None)
                                    if callable(callback):
                                        callback(i, self.game.hud.popup_team)
                                    return

            # Séléctionner une unité déjà créer
            world_x, world_y = self.screen_to_world_coordinates(pygame.mouse.get_pos())
            # Chercher une unité à cette position
            clicked_unit = self.game.find_unit_at_position(world_x, world_y)

            hud_visible = getattr(self.game, "hud", None) and getattr(self.game.hud, "show", False)

            if clicked_unit:
                # Sélectionner l'unité
                if clicked_unit.team == self.game.hud.player_team:
                    self.game.select_unit(clicked_unit)
            elif self.game.selected_unit and self.game.selected_unit.is_alive:
                # Déplacement direct pour les autres unités
                if hasattr(self.game.selected_unit, "move_to_position"):
                    self.game.selected_unit.move_to_position((world_x, world_y))
            else:
                # Si le HUD est visible et qu'aucune unité n'a été cliquée, désélectionner
                if hud_visible:
                    self.game.select_unit(None)

        # Molette haut
        elif event.button == get_action_key("ZOOM_IN"):
            if not getattr(self.game, "paused", False):
                self.game.camera.zoom_in()

        # Molette bas
        elif event.button == get_action_key("ZOOM_OUT"):
            if not getattr(self.game, "paused", False):
                self.game.camera.zoom_out()

        # Désélectionner l'unité
        elif event.button == 3:
            self.game.selected_unit = None

    def handle_continuous_input(self):
        """Gère les entrées continues (touches maintenues)."""

        pressed = pygame.key.get_pressed()
        self.handle_camera_movement(pressed)

        if pressed[get_action_key("SHOOT")]:
            self.trigger_shooting()

    # === Tuto ===
    # On a du redefinir certaines fonctions pour le bon fonctionnement du didacticiel.
    def handle_events_tuto(self):
        """Gère tous les événements ponctuels pour le tuto.
        Ici il n'y a pas :
        * La gestion du timer.
        * La gestion du pétrole.
        * Le changement de marée.
        * La reconstruction de la map liée au changement de marée.
        * Les obstacles et les zones quantiques.

        Returns:
            (bool): True si le jeu doit continuer, False sinon.
        """

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            # Verifier qu'on est pas en index out of range
            if self.game.tutorial.step >= len(self.game.tutorial.messages):
                self.game.tutorial.active = False
                return False
            seq = self.game.tutorial.messages[self.game.tutorial.step]
            # On verifie si des fonctions doivent etre exectués dans la sequence actuelle. Si oui, on les execute.
            if "function" in seq:
                self.game.tutorial.do_function = True

            # Gestion des touches
            if event.type == pygame.KEYDOWN:
                self.handle_keydown_events_tuto(event)

            # Gestion des clics souris
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_events_tuto(event)

        return True

    def handle_keydown_events_tuto(self, event: pygame.event):
        """Gère les événements de touches pressées dans le tuto.

        Args:
            event (pygame.event): Événement pygame.
        """

        # Menu options
        if event.key == get_action_key("OPTIONS"):
            options_menu = OptionsMenu(self.game.screen)
            options_menu.run()

        seq = self.game.tutorial.messages[self.game.tutorial.step]
        # On vérifie s'il existe une réstriction sur la séquence
        if "restriction" in seq:
            # Si la touche préssé est comprise dans les réstrictions
            if event.key in seq["restriction"]["keys"]:
                # Cas où plusieurs appuis sont necessaires
                if seq["count"]:
                    self.game.tutorial.count_to_next_step()
                    # Cas particulier.
                    if seq["restriction"]["name"] == "navigation":
                        if event.key == get_action_key("HUD_LEFT"):
                            self.game.hud.popup_selection = (self.game.hud.popup_selection - 1) % len(
                                self.game.hud.unit_names
                            )
                        elif event.key == get_action_key("HUD_RIGHT"):
                            self.game.hud.popup_selection = (self.game.hud.popup_selection + 1) % len(
                                self.game.hud.unit_names
                            )
                else:
                    # Cas particulier.
                    if seq["restriction"]["name"] == "spawn_chaloupe":
                        if self.spawn_unit("chaloupe", "red"):
                            self.game.units[-1].position = self.game.get_base_position("red")
                            self.game.units[-1].position = (
                                self.game.units[-1].position[0] + 100,
                                self.game.units[-1].position[1],
                            )
                            self.apply_cost("chaloupe", "red", 20)
                            self.game.tutorial.next_step()

                    # Cas particulier.
                    elif seq["restriction"]["name"] == "fire_mine":
                        x, y = self.game.selected_unit.position
                        self.game.selected_unit.place_mine(x, y)
                        self.game.selected_unit.position = (x + 50, y)
                        self.game.tutorial.next_step()

    def handle_mouse_events_tuto(self, event: pygame.event):
        """Gère les événements de souris dans le tuto.

        Args:
            event (pygame.event): Événement de souris à traiter.
        """

        # Passer le tuto avec clic gauche par défaut
        seq = self.game.tutorial.messages[self.game.tutorial.step]
        # On verifie les restrictions
        if "restriction" not in seq:
            if event.button == 1:
                self.game.tutorial.next_step()
        else:
            if event.button in seq["restriction"]["keys"]:
                # Cas où plusieurs appuis sont necessaires
                if seq["count"]:
                    self.game.tutorial.count_to_next_step()
                    # Cas particulier.
                    if seq["restriction"]["name"] == "zoom":
                        if event.button == get_action_key("ZOOM_IN"):
                            self.game.camera.zoom_in()

                        # Molette bas
                        elif event.button == get_action_key("ZOOM_OUT"):
                            self.game.camera.zoom_out()
                else:
                    if seq["restriction"]["name"] == "select_chaloupe":
                        rects = self.game.hud.popup_icon_rects
                        if rects:
                            pos = getattr(event, "pos", None)
                            if pos:
                                for i, rect in enumerate(rects):
                                    if rect is None:
                                        continue
                                    if rect.collidepoint(pos):
                                        # Mettre à jour la sélection dans le HUD
                                        self.game.hud.popup_selection = i
                                        # Appeler le callback si défini
                                        callback = getattr(self.game.hud, "unit_select_callback", None)
                                        if callable(callback):
                                            callback(i, self.game.hud.popup_team)
                                        if i == 0:
                                            self.game.tutorial.next_step()
                                        break

                    elif seq["restriction"]["name"] == "move_chaloupe":
                        world_x, world_y = self.screen_to_world_coordinates(pygame.mouse.get_pos())
                        # Chercher une unité à cette position
                        clicked_unit = self.game.find_unit_at_position(world_x, world_y)

                        if clicked_unit:
                            # Sélectionner l'unité
                            if clicked_unit.team == self.game.hud.player_team:
                                self.game.select_unit(clicked_unit)
                        elif self.game.selected_unit and self.game.selected_unit.is_alive:
                            # Déplacer l'unité sélectionnée vers la position cliquée
                            if hasattr(self.game.selected_unit, "move_to_position"):
                                # Déplacement direct pour les autres unités
                                self.game.selected_unit.move_to_position((world_x, world_y))
                                self.game.tutorial.next_step()

                    elif seq["restriction"]["name"] == "select_base":
                        world_x, world_y = self.screen_to_world_coordinates(pygame.mouse.get_pos())
                        # Chercher une unité à cette position
                        clicked_unit = self.game.find_unit_at_position(world_x, world_y)

                        if clicked_unit:
                            # Sélectionner l'unité
                            if clicked_unit.team == self.game.hud.player_team:
                                if hasattr(clicked_unit, "is_platform"):
                                    self.game.select_unit(clicked_unit)
                                    self.game.tutorial.next_step()

    def handle_continuous_input_tuto(self):
        """Gère les entrées continues (touches maintenues) pour le tuto"""
        pressed = pygame.key.get_pressed()

        # On vérifie que nous sommes pas dans le cas ou le tuto est fini
        if self.game.tutorial.step < len(self.game.tutorial.messages):
            seq = self.game.tutorial.messages[self.game.tutorial.step]
            if "restriction" in seq:
                if seq["restriction"]["name"] == "zqsd":
                    self.handle_camera_movement(pressed)
                elif seq["restriction"]["name"] == "fire_chaloupe":
                    if pressed[get_action_key("SHOOT")] and len(self.game.units) == 4:
                        self.trigger_shooting()
                        self.game.tutorial.next_step()
        else:
            from src.menus.Menu import Menu

            menu = Menu()
            menu.run()

    def handle_camera_movement(self, pressed: tuple[bool]):
        """Gère le déplacement de la caméra avec les touches directionnelles.

        Args:
            pressed (tuple[bool]): Un tuple de booléens indiquant si les touches sont enfoncées.
        """

        dx, dy = 0, 0
        if pressed[get_action_key("CAMERA_UP")]:  # Haut
            dy -= self.game.camera.camera_move
        if pressed[get_action_key("CAMERA_DOWN")]:  # Bas
            dy += self.game.camera.camera_move
        if pressed[get_action_key("CAMERA_LEFT")]:  # Gauche
            dx -= self.game.camera.camera_move
        if pressed[get_action_key("CAMERA_RIGHT")]:  # Droite
            dx += self.game.camera.camera_move

        # Déplacer la caméra seulement s'il y a un déplacement
        if dx or dy:
            self.game.camera.move(dx, dy)

    # === Utilitaires
    def screen_to_world_coordinates(self, mouse_pos: tuple[int, int]):
        """Convertit les coordonnées écran en coordonnées monde.

        Args:
            mouse_pos (tuple[int, int]): Coordonnées écran.

        Returns:
            (tuple[int, int]): Coordonnées monde.
        """

        mouse_x, mouse_y = mouse_pos
        camera_center = self.game.camera.rect.center
        screen_center_x = self.game.screen.get_width() // 2
        screen_center_y = self.game.screen.get_height() // 2

        # Transformation inverse adaptée au zoom
        offset_x = (mouse_x - screen_center_x) / self.game.camera.zoom_level
        offset_y = (mouse_y - screen_center_y) / self.game.camera.zoom_level
        world_x = camera_center[0] + offset_x
        world_y = camera_center[1] + offset_y

        return world_x, world_y

    def check_cost(self, team_key: str, cost: int):
        """Fonction permettant de vérifier le coût d'une unité.

        Args:
            team_key (str): Clé de l'équipe.
            cost (int): Coût de l'unité.

        Returns:
            (bool): True si le coût est valide, False sinon.
        """

        # S'il n'y a pas assez de pétrole.
        if team_key == "red":
            if self.game.hud.petrole_red.count < cost:
                return False
            else:
                # self.game.hud.petrole_red.count -= cost
                # succes()
                return True
        else:
            if self.game.hud.petrole_green.count < cost:
                return False
            else:
                # self.game.hud.petrole_green.count -= cost
                # succes()
                return True

    def apply_cost(self, config_key: str, team_key: str, cost: int):
        """Applique le coût de l'unité.

        Args:
            config_key (str): Clé de configuration de l'unité.
            team_key (str): Clé de l'équipe.
            cost (int): Coût de l'unité.
        """

        def succes():
            """Fonction interne pour gérer les succès liés aux unités créées."""

            # Suivre les statistiques pour les succès
            if self.game.achievements_system:
                self.game.achievements_system.track_unit_created(config_key, cost)
                # Mettre à jour le nombre maximum d'unités vivantes
                alive_units = len([u for u in self.game.units if u.is_alive and hasattr(u, "unit_type")])
                self.game.achievements_system.update_max_units_alive(alive_units)

            # Marquer le type d'unité comme créé dans cette partie
            self.game.units_created_this_game.add(config_key)

        if team_key == "red":
            self.game.hud.petrole_red.count -= cost
        else:
            self.game.hud.petrole_green.count -= cost
        succes()

    def spawn_unit(self, config_key: str, team_key: str):
        """Génère une unité.

        Args:
            config_key (str): Clé de configuration de l'unité.
            team_key (str): Clé de l'équipe.
        """

        # Créer l'unité
        # Mapping type + équipe -> classe
        class_map = {
            "chaloupe": {"red": ChaloupeRouge, "green": ChaloupeVerte},
            "bateau": {"red": BateauRouge, "green": BateauVert},
            "paquebot": {"red": PaquebotRouge, "green": PaquebotVert},
            "eclaireur": {"red": EclaireurRouge, "green": EclaireurVert},
            "sousmarin": {"red": SousMarinRouge, "green": SousMarinVert},
            "pompe_petroliere": {
                "red": PompePetroliereRouge,
                "green": PompePetroliereVert,
            },
        }
        unit_class = class_map.get(config_key)[team_key]

        # On instancie l'unité
        from src.config.settings_manager import get_gameplay_settings

        is_ia = get_gameplay_settings()["AI_ACTIVATION"].get(unit_class.__name__, None)
        if is_ia is None:
            unit = unit_class(self.game)
        else:
            unit = unit_class(self.game, is_ia=is_ia)
        if config_key == "pompe_petroliere":
            if team_key == "red":
                self.game.nbPompePetroliereRouge += 1
            else:
                self.game.nbPompePetroliereVert += 1

        # Ajouter au système de combat et au groupe de sprites
        self.game.combat_system.add_unit(unit)
        self.game.units.append(unit)
        self.game.group.add(unit)

        # === SON : drop de l'unité ===
        if hasattr(self.game, "sound") and self.game.sound:
            try:
                self.game.sound.on_unit_dropped(unit.__class__.__name__, pos=tuple(unit.position))
            except Exception:
                pass

        return True

    def trigger_shooting(self):
        """Déclenche le tir si toutes les conditions sont remplies."""

        # Vérifier s'il y a une unité sélectionnée
        if not hasattr(self.game, "selected_unit") or not self.game.selected_unit:
            return

        selected_unit = self.game.selected_unit

        # Vérifier que l'unité sélectionnée est vivante
        if not selected_unit.is_alive:
            return

        # Vérifier s'il y a des ennemis dans la portée
        if not hasattr(selected_unit, "enemies_in_range") or not selected_unit.enemies_in_range:
            return

        # Obtenir l'ennemi le plus proche
        target = selected_unit.get_closest_enemy_in_range()
        if not target:
            return

        # Vérifier le cooldown de tir
        current_time = pygame.time.get_ticks()
        if not selected_unit.can_shoot(current_time):
            return

        # Mettre à jour immédiatement le temps du dernier tir pour empêcher le spam
        selected_unit.last_shot_time = current_time

        # Tirer sur la cible en utilisant le système de combat
        if hasattr(self.game, "combat_system"):
            _projectile = self.game.combat_system.fire_projectile(selected_unit, target)

    # ==========================================
    # MÉTHODES Q-LEARNING DEBUG
    # ==========================================

    def _input_qlearning(self, event: pygame.event):
        """Gère les entrées clavier pour le debug du Q-Learning

        Args:
            event (pygame.event): Événement pygame

        Returns:
            (bool): True si une touche de debug a été pressée, False sinon.
        """
        # F1: Toggle Q-Learning pour toutes les chaloupes
        if event.key == pygame.K_F1:
            self._toggle_qlearning_all_chaloupes()
            return True

        # F2: Toggle debug visuel pour toutes les chaloupes
        if event.key == pygame.K_F2:
            self._toggle_visual_debug_all_chaloupes()
            return True

        # F3: Afficher les statistiques Q-Learning dans la console
        if event.key == pygame.K_F3:
            self._show_qlearning_stats()
            return True

        # F4: Reset Q-Learning (efface la Q-table)
        if event.key == pygame.K_F4:
            self._reset_qlearning_all()
            return True

        # F5: Sauvegarder le progrès Q-Learning de toutes les chaloupes
        if event.key == pygame.K_F5:
            self._save_qlearning_progress_all()
            return True

    def _toggle_qlearning_all_chaloupes(self):
        """Active/désactive le Q-Learning pour toutes les chaloupes."""
        chaloupes = [unit for unit in self.game.units if hasattr(unit, "unit_type") and unit.unit_type == "chaloupe"]

        if not chaloupes:
            print("[Q-Learning Debug] Aucune chaloupe trouvée")
            return

        # Déterminer l'état actuel (on prend la première chaloupe comme référence)
        current_state = chaloupes[0].is_qlearning_enabled() if chaloupes else False
        new_state = not current_state

        for chaloupe in chaloupes:
            chaloupe.toggle_qlearning(new_state)

        status = "activé" if new_state else "désactivé"
        print(f"[Q-Learning Debug] Q-Learning {status} pour {len(chaloupes)} chaloupes")

    def _save_qlearning_progress_all(self):
        """Sauvegarde le progrès Q-Learning de toutes les chaloupes."""
        chaloupes = [unit for unit in self.game.units if hasattr(unit, "unit_type") and unit.unit_type == "chaloupe"]

        saved_count = 0
        for chaloupe in chaloupes:
            if chaloupe.is_qlearning_enabled():
                chaloupe.save_qlearning_progress()
                saved_count += 1

        print(f"[Q-Learning Debug] Progrès sauvegardé pour {saved_count} chaloupes")

    def _show_qlearning_stats(self):
        """Affiche les statistiques Q-Learning dans la console."""
        chaloupes = [unit for unit in self.game.units if hasattr(unit, "unit_type") and unit.unit_type == "chaloupe"]

        print("\n=== STATISTIQUES Q-LEARNING ===")
        for i, chaloupe in enumerate(chaloupes):
            stats = chaloupe.get_qlearning_stats()
            if stats:
                print(f"Chaloupe {chaloupe.team} #{i + 1}:")
                print(f"  - Épisodes: {stats['total_episodes']}")
                print(f"  - Récompenses totales: {stats['total_rewards']:.1f}")
                print(f"  - Récompense moyenne: {stats['avg_reward']:.2f}")
                print(f"  - Epsilon (exploration): {stats['epsilon']:.3f}")
                print(f"  - Taille Q-table: {stats['q_table_size']} états")
                print(f"  - Dernière récompense: {stats['last_reward']:.1f}")
            else:
                print(f"Chaloupe {chaloupe.team} #{i + 1}: Q-Learning désactivé")
        print("=================================\n")

    def _reset_qlearning_all(self):
        """Reset le Q-Learning pour toutes les chaloupes."""
        chaloupes = [unit for unit in self.game.units if hasattr(unit, "unit_type") and unit.unit_type == "chaloupe"]

        reset_count = 0
        for chaloupe in chaloupes:
            if chaloupe.is_qlearning_enabled() and chaloupe.ai_system and chaloupe.ai_system.qlearning_agent:
                # Reset la Q-table
                chaloupe.ai_system.qlearning_agent.q_table = {}
                chaloupe.ai_system.qlearning_agent.total_episodes = 0
                chaloupe.ai_system.qlearning_agent.total_rewards = 0
                chaloupe.ai_system.qlearning_agent.epsilon = 0.2  # Reset exploration
                reset_count += 1

        print(f"[Q-Learning Debug] Q-Learning reset pour {reset_count} chaloupes")

    def _toggle_visual_debug_all_chaloupes(self):
        """Active/désactive le debug visuel pour toutes les chaloupes.

        Returns:
            (bool): True si le debug a été togglé, False sinon.
        """
        chaloupes = [unit for unit in self.game.units if hasattr(unit, "unit_type") and unit.unit_type == "chaloupe"]

        if not chaloupes:
            print("[Visual Debug] Aucune chaloupe trouvée")
            return

        # Prendre l'état du premier pour toggle
        first_chaloupe = chaloupes[0]
        current_debug = getattr(first_chaloupe, "visual_debug_enabled", False)
        new_state = not current_debug

        debug_count = 0
        for chaloupe in chaloupes:
            if chaloupe.use_advanced_ai and chaloupe.ai_system:
                chaloupe.visual_debug_enabled = new_state
                debug_count += 1

        state_text = "activé" if new_state else "désactivé"
        print(f"[Visual Debug] Debug visuel {state_text} pour {debug_count} chaloupes")

        return True
