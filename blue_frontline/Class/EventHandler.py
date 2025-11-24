import pygame
from Class.OptionsMenu import OptionsMenu
from Global import get_action_key
from Global import UNIT_CONFIGS
from Class.units.Chaloupe import ChaloupeRouge, ChaloupeVerte
from Class.units.Bateau import BateauRouge, BateauVert
from Class.units.Eclaireur import EclaireurRouge, EclaireurVert
from Class.units.Paquebot import PaquebotRouge, PaquebotVert
from Class.units.Sousmarin import SousMarinRouge, SousMarinVert
from Class.units.PompePetroliere import PompePetroliereRouge, PompePetroliereVert

class EventHandler:
    """Gestionnaire d'événements pour le jeu."""
    
    def __init__(self, game: "Game"):
        """Initialise le gestionnaire d'événements avec une référence au jeu.

        Args:
            game (Game): Référence au jeu.
        """
        self.game = game
    
    def handle_events(self):
        """Gère tous les événements ponctuels.
        
        Returns:
            bool: True si le jeu doit continuer, False sinon.
        """
        
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
                if hasattr(self.game.renderer, 'map_needs_refresh') and self.game.renderer.map_needs_refresh:
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
                if not self.handle_keydown_events(event):
                    continue

            # Gestion des clics souris
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_events(event)
        
        return True
    
    def handle_keydown_events(self, event: pygame.event):
        """Gère les événements de touches pressées.

        Args:
            event (pygame.event): Événement pygame.

        Returns:
            bool: True si l'événement a été traité, False sinon.
        """
        
        if event.key == pygame.K_ESCAPE:
            options_menu = OptionsMenu(self.game.screen)
            retour = options_menu.run()
            if type(retour) == tuple and len(retour) == 2:
                changed, new_gameplay_settings = retour
                if changed:
                    # Appliquer les nouveaux paramètres de gameplay au jeu
                    from Global import set_gameplay_setting
                    set_gameplay_setting(new_gameplay_settings)
            
            return True

        # Entrée via le HUD (bandeau bas) pour spawn l'unité sélectionnée (coût géré dans Game.spawn_unit)
        if event.key == pygame.K_RETURN :
            hud = self.game.hud
            selection_index = hud.popup_selection
            team_key = hud.popup_team  # 'red' ou 'green'
            # Récupérer la clé de config de l'unité (le type d'unité)
            if selection_index < 0 or selection_index >= len(hud.unit_config_keys):
                return True
            config_key = hud.unit_config_keys[selection_index]
            
            # Vérifier le coût en pétrole
            cost = UNIT_CONFIGS.get(config_key, {}).get('cost')
            if not cost:
                return
            if self.check_cost(team_key, cost):
                self.apply_cost(config_key, team_key, cost)
                self.spawn_unit(config_key, team_key)
                return True

        # Volume
        if event.key == get_action_key("VOLUME_UP"):
            self.game.sound.increase_volume()
        elif event.key == get_action_key("VOLUME_DOWN"):
            self.game.sound.decrease_volume()

        if event.key == get_action_key("HUD_LEFT"):
            self.game.hud.popup_selection = (self.game.hud.popup_selection - 1) % len(self.game.hud.unit_names)
            return True
        if event.key == get_action_key("HUD_RIGHT"):
            self.game.hud.popup_selection = (self.game.hud.popup_selection + 1) % len(self.game.hud.unit_names)
            return True

        if event.key == get_action_key("TIME_SPEED"):
            # Cycler la vitesse du temps
            new_speed = self.game.hud.timer.cycle_speed()
            # Synchroniser la vitesse du pétrole avec le timer
            self.game.hud.petrole_red.set_speed(new_speed)
            self.game.hud.petrole_green.set_speed(new_speed)
            
            # Synchorniser les vitesses de bateaux avec la nouvelle vitesse
            for unit in self.game.units:
                # Verification sur l'entité
                if hasattr(unit, 'is_moving') and unit.is_moving : 
                    # unit.speed * new_speed
                    unit.move_to(unit.target_position[0], unit.target_position[1])
            return True
        
        if event.key ==  get_action_key("SWITCH_TEAM"):
            # Changer d'équipe dans le HUD:
            self.game.hud.toggle_popup_team()
            self.game.hud.switch_team()
            self.game.overlay_menu.switch_team()
            return True
        
        # === COMMANDES DEBUG Q-LEARNING ===
        
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
        
        if event.key == get_action_key("MINE"):
            world_x, world_y = self.screen_to_world_coordinates(pygame.mouse.get_pos())

            # Si un sous-marin est sélectionné, poser une mine
            if (self.game.selected_unit and
                self.game.selected_unit.is_alive and
                hasattr(self.game.selected_unit, 'special_ability') and
                self.game.selected_unit.special_ability == "mines"):

                # Vérifier que la position n'est pas dans un obstacle
                from Utils import point_in_many_polygons
                if not point_in_many_polygons(self.game.obstacles, (world_x, world_y)):
                    x, y = self.game.selected_unit.position

                    # Utiliser la méthode spéciale pour le sous-marin
                    if hasattr(self.game.selected_unit, 'can_place_mine') and self.game.selected_unit.can_place_mine():
                        self.game.selected_unit.place_mine(x, y)
        
        return True
    
    # ==========================================
    # MÉTHODES Q-LEARNING DEBUG
    # ==========================================
    
    def _toggle_qlearning_all_chaloupes(self):
        """Active/désactive le Q-Learning pour toutes les chaloupes."""
        chaloupes = [unit for unit in self.game.units if hasattr(unit, 'unit_type') and unit.unit_type == 'chaloupe']
        
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
        chaloupes = [unit for unit in self.game.units if hasattr(unit, 'unit_type') and unit.unit_type == 'chaloupe']
        
        saved_count = 0
        for chaloupe in chaloupes:
            if chaloupe.is_qlearning_enabled():
                chaloupe.save_qlearning_progress()
                saved_count += 1
        
        print(f"[Q-Learning Debug] Progrès sauvegardé pour {saved_count} chaloupes")
    
    def _show_qlearning_stats(self):
        """Affiche les statistiques Q-Learning dans la console."""
        chaloupes = [unit for unit in self.game.units if hasattr(unit, 'unit_type') and unit.unit_type == 'chaloupe']
        
        print("\n=== STATISTIQUES Q-LEARNING ===")
        for i, chaloupe in enumerate(chaloupes):
            stats = chaloupe.get_qlearning_stats()
            if stats:
                print(f"Chaloupe {chaloupe.team} #{i+1}:")
                print(f"  - Épisodes: {stats['total_episodes']}")
                print(f"  - Récompenses totales: {stats['total_rewards']:.1f}")
                print(f"  - Récompense moyenne: {stats['avg_reward']:.2f}")
                print(f"  - Epsilon (exploration): {stats['epsilon']:.3f}")
                print(f"  - Taille Q-table: {stats['q_table_size']} états")
                print(f"  - Dernière récompense: {stats['last_reward']:.1f}")
            else:
                print(f"Chaloupe {chaloupe.team} #{i+1}: Q-Learning désactivé")
        print("=================================\n")
    
    def _reset_qlearning_all(self):
        """Reset le Q-Learning pour toutes les chaloupes."""
        chaloupes = [unit for unit in self.game.units if hasattr(unit, 'unit_type') and unit.unit_type == 'chaloupe']
        
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
        """Active/désactive le debug visuel pour toutes les chaloupes."""
        chaloupes = [unit for unit in self.game.units if hasattr(unit, 'unit_type') and unit.unit_type == 'chaloupe']
        
        if not chaloupes:
            print("[Visual Debug] Aucune chaloupe trouvée")
            return
        
        # Prendre l'état du premier pour toggle
        first_chaloupe = chaloupes[0]
        current_debug = getattr(first_chaloupe, 'visual_debug_enabled', False)
        new_state = not current_debug
        
        debug_count = 0
        for chaloupe in chaloupes:
            if chaloupe.use_advanced_ai and chaloupe.ai_system:
                chaloupe.visual_debug_enabled = new_state
                debug_count += 1
        
        state_text = "activé" if new_state else "désactivé"
        print(f"[Visual Debug] Debug visuel {state_text} pour {debug_count} chaloupes")
        
        return True
    
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
        if event.button == get_action_key("SELECT_MOVE"):  # Clic gauche
            world_x, world_y = self.screen_to_world_coordinates(pygame.mouse.get_pos())
            # Chercher une unité à cette position
            clicked_unit = self.game.find_unit_at_position(world_x, world_y)

            if clicked_unit:
                self.game.select_unit(clicked_unit)
            elif self.game.selected_unit and self.game.selected_unit.is_alive:
                # Déplacer l'unité sélectionnée vers la position cliquée
                if hasattr(self.game.selected_unit, 'move_to_click'):
                    # Utiliser le pathfinding pour les Chaloupes
                    self.game.selected_unit.move_to_click((world_x, world_y))
                elif hasattr(self.game.selected_unit, 'move_to_position'):
                    # Déplacement direct pour les autres unités
                    self.game.selected_unit.move_to_position((world_x, world_y))
            else:
                self.game.select_unit(None)
                        
        # Molette haut
        elif event.button == get_action_key("ZOOM_IN"):
            if not getattr(self.game, 'paused', False):
                self.game.camera.zoom_in()
        
        # Molette bas
        elif event.button == get_action_key("ZOOM_OUT"):
            if not getattr(self.game, 'paused', False):
                self.game.camera.zoom_out()

        # Désélectionner l'unité
        if event.button == 3 : 
            self.game.select_unit(None)
    
    def screen_to_world_coordinates(self, mouse_pos: tuple[int, int]):
        """Convertit les coordonnées écran en coordonnées monde.

        Args:
            mouse_pos (tuple[int, int]): Coordonnées écran.

        Returns:
            tuple[int, int]: Coordonnées monde.
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
    
    def check_cost(self, team_key: str, cost: int ):
        """Fonction permettant de vérifier le coût d'une unité.
        
        Args:
            team_key (str): Clé de l'équipe.
            cost (int): Coût de l'unité.
        
        Returns:
            bool: True si le coût est valide, False sinon.
        """
        
        # S'il n'y a pas assez de pétrole.
        if team_key == "red"  :
            if self.game.hud.petrole_red.count < cost:
                return False
            else : 
                # self.game.hud.petrole_red.count -= cost
                # succes()
                return True
        else : 
            if self.game.hud.petrole_green.count < cost: 
                return False
            else :
                # self.game.hud.petrole_green.count -= cost
                # succes()
                return True
        
    def apply_cost(self, config_key: str, team_key: str, cost:int):
        """Applique le coût de l'unité.

        Args:
            config_key (str): Clé de configuration de l'unité.
            team_key (str): Clé de l'équipe.
            cost (int): Coût de l'unité.
        """
        
        def succes():
            """Fonction interne pour gérer les succès liés aux unités créées."""

            # Suivre les statistiques pour les succès selon l'équipe qui crée l'unité
            if team_key == 'red' and hasattr(self.game, 'achievements_system_rouge') and self.game.achievements_system_rouge:
                self.game.achievements_system_rouge.track_unit_created(config_key, cost)
                # Mettre à jour le nombre maximum d'unités vivantes
                alive_units = len([u for u in self.game.units if u.is_alive and hasattr(u, 'unit_type')])
                self.game.achievements_system_rouge.update_max_units_alive(alive_units)
            elif team_key == 'green' and hasattr(self.game, 'achievements_system_vert') and self.game.achievements_system_vert:
                self.game.achievements_system_vert.track_unit_created(config_key, cost)
                # Mettre à jour le nombre maximum d'unités vivantes
                alive_units = len([u for u in self.game.units if u.is_alive and hasattr(u, 'unit_type')])
                self.game.achievements_system_vert.update_max_units_alive(alive_units)
            else:
                pass
            
            # Marquer le type d'unité comme créé dans cette partie
            self.game.units_created_this_game.add(config_key)

        if team_key == "red"  :
            self.game.hud.petrole_red.count -= cost
        else : 
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
            'chaloupe': {'red': ChaloupeRouge, 'green': ChaloupeVerte},
            'bateau': {'red': BateauRouge, 'green': BateauVert},
            'paquebot': {'red': PaquebotRouge, 'green': PaquebotVert},
            'eclaireur': {'red': EclaireurRouge, 'green': EclaireurVert},
            'sousmarin': {'red': SousMarinRouge, 'green': SousMarinVert},
            'pompe_petroliere': {'red': PompePetroliereRouge, 'green': PompePetroliereVert},
        }
        unit_class = class_map.get(config_key)[team_key]
        
        # On instancie l'unité
        from Global import GAMEPLAY_SETTINGS
        unit = unit_class(self.game, is_ia=GAMEPLAY_SETTINGS["AI_ACTIVATION"][unit_class.__name__])
        
        if config_key == "pompe_petroliere" :
            if team_key == "red" : 
                self.game.nbPompePetroliereRouge += 1
            else : 
                self.game.nbPompePetroliereVert += 1
        
        # Ajouter au système de combat et au groupe de sprites
        self.game.combat_system.add_unit(unit)
        self.game.units.append(unit)
        self.game.group.add(unit)
        
        # On envoi la map a toutes les instances
        self.game.refresh_all_references(self.game)
        return True