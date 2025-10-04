import pygame
from Class.OptionsMenu import OptionsMenu
from Global import get_action_key
from Global import UNIT_CONFIGS
from Class.units.Chaloupe import ChaloupeRouge, ChaloupeVerte
from Class.units.Bateau import BateauRouge, BateauVert
from Class.units.Eclaireur import EclaireurRouge, EclaireurVert
from Class.units.Paquebot import PaquebotRouge, PaquebotVert
from Class.units.Sousmarin import SousMarinRouge, SousMarinVert

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
            self.game.hud.petrole_green.handle_event(event)
            self.game.hud.petrole_red.handle_event(event)
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
                if not self._handle_keydown_events(event):
                    continue

            # Gestion des clics souris
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_events(event)
        
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
            options_menu.run()
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
            
            def succes():
                """Fonction interne pour gérer les succès liés aux unités créées."""

                # Suivre les statistiques pour les succès
                if self.game.achievements_system:
                    self.game.achievements_system.track_unit_created(config_key, cost)
                    # Mettre à jour le nombre maximum d'unités vivantes
                    alive_units = len([u for u in self.game.units if u.is_alive and hasattr(u, 'unit_type')])
                    self.game.achievements_system.update_max_units_alive(alive_units)
                
                # Marquer le type d'unité comme créé dans cette partie
                self.game.units_created_this_game.add(config_key)

            # S'il n'y a pas assez de pétrole.
            if team_key == "red"  :
                if self.game.hud.petrole_red.count < cost:
                    return None
                else : 
                    self.game.hud.petrole_red.count -= cost
                    succes()
            else : 
                if self.game.hud.petrole_green.count < cost: 
                    return None
                else :
                    self.game.hud.petrole_green.count -= cost
                    succes()
            
            # Créer l'unité
            # Mapping type + équipe -> classe
            class_map = {
                'chaloupe': {'red': ChaloupeRouge, 'green': ChaloupeVerte},
                'bateau': {'red': BateauRouge, 'green': BateauVert},
                'paquebot': {'red': PaquebotRouge, 'green': PaquebotVert},
                'eclaireur': {'red': EclaireurRouge, 'green': EclaireurVert},
                'sousmarin': {'red': SousMarinRouge, 'green': SousMarinVert},
            }
            unit_class = class_map.get(config_key)[team_key]
            
            # On instancie l'unité
            unit = unit_class(self.game)
            
            # Ajouter au système de combat et au groupe de sprites
            self.game.combat_system.add_unit(unit)
            self.game.units.append(unit)
            self.game.group.add(unit)
            
            # On envoi la map a toutes les instances
            self.game.refresh_all_references(self.game)
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

        if event.key == get_action_key("SPEED_UP"):
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
            return True
        
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
        
        # Clic gauche
        if event.button == get_action_key("SELECT_MOVE"):  # Clic gauche
            world_x, world_y = self.screen_to_world_coordinates(pygame.mouse.get_pos())
            # Chercher une unité à cette position
            clicked_unit = self.game.find_unit_at_position(world_x, world_y)

            if clicked_unit:
                self.game.select_unit(clicked_unit)
            elif self.game.selected_unit and self.game.selected_unit.is_alive and hasattr(self.game.selected_unit, 'move_to_position'):
                # Déplacer l'unité sélectionnée vers la position cliquée
                self.game.selected_unit.move_to_position((world_x, world_y))
            else:
                self.game.select_unit(None)

        # Clic droit
        elif event.button == get_action_key("MINE"):  # Clic droit
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

                    # Poser la mine
                    if self.game.selected_unit.place_mine(x, y):
                        print(f"Mine posée à la position ({x}, {y}) par {self.game.selected_unit.unit_name}")
                else:
                    print("Impossible de poser une mine sur un obstacle")
        
        # Molette haut
        elif event.button == get_action_key("ZOOM_IN"):
            if not getattr(self.game, 'paused', False):
                self.game.camera.zoom_in()
        
        # Molette bas
        elif event.button == get_action_key("ZOOM_OUT"):
            if not getattr(self.game, 'paused', False):
                self.game.camera.zoom_out()
    
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