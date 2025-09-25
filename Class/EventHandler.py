import pygame
import time
from Class.OptionsMenu import OptionsMenu
from Global import UNIT_CONFIGS
from Class.units.Chaloupe import ChaloupeRouge, ChaloupeVerte
from Class.units.Bateau import BateauRouge, BateauVert
from Class.units.Eclaireur import EclaireurRouge, EclaireurVert
from Class.units.Paquebot import PaquebotRouge, PaquebotVert
from Class.units.Sousmarin import SousMarinRouge, SousMarinVert

class EventHandler:
    """Gestionnaire d'événements pour le jeu."""
    
    def __init__(self, game):
        """Initialise le gestionnaire d'événements avec une référence au jeu."""
        self.game = game
    
    def handle_events(self):
        """Gère tous les événements ponctuels."""
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                return False

            # Gestion des événements HUD
            self.game.hud.petrole.handle_event(event)
            self.game.hud.timer.handle_event(event)

            # Gestion du changement de marée                   
            if self.game.hud.timer.maree_changed:
                self.game.initializer.switch_layer()
                
                # Reconstruire la map
                if hasattr(self.game.renderer, 'map_needs_refresh') and self.game.renderer.map_needs_refresh:
                    self.game.renderer.refresh_map()  
                    
                # Marquer le changement comme traité
                self.game.hud.timer.maree_changed = False
                
                if self.game.hud.timer.maree_haute:
                    self.game.quantique()


            # Gestion des touches
            elif event.type == pygame.KEYDOWN:
                if not self._handle_keydown_events(event):
                    continue
            
            # Gestion des clics souris
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_events(event)
        
        return True
    
    def _handle_keydown_events(self, event):
        """Gère les événements de touches pressées."""
        if event.key == pygame.K_p:
            # Toggle pause
            self.game.paused = not self.game.paused
            if self.game.paused:
                # Mettre les timers en pause
                self.game.hud.timer.pause()
                self.game.hud.petrole.pause()
            else:
                # Reprendre les timers
                self.game.hud.timer.resume()
                self.game.hud.petrole.resume()
            print(f"Pause: {'ON' if self.game.paused else 'OFF'}")
            return True

        if event.key == pygame.K_e:
            self.game.show_unit_popup = not self.game.show_unit_popup
            self.game.popup_selection = 0
            return True
        
        elif event.key == pygame.K_ESCAPE:
            options_menu = OptionsMenu(self.game.screen)
            options_menu.run()
            return True

        # Entrée via le HUD (bandeau bas) pour spawn l'unité sélectionnée (coût géré dans Game.spawn_unit)
        if event.key == pygame.K_RETURN and not self.game.show_unit_popup:
                hud = self.game.hud
                selection_index = hud.popup_selection
                team_key = hud.popup_team  # 'red' ou 'green'
                # Récupérer la clé de config de l'unité
                if selection_index < 0 or selection_index >= len(hud.unit_config_keys):
                    return True
                config_key = hud.unit_config_keys[selection_index]

                # Mapping type + équipe -> classe
                class_map = {
                    'chaloupe': {'red': ChaloupeRouge, 'green': ChaloupeVerte},
                    'bateau': {'red': BateauRouge, 'green': BateauVert},
                    'paquebot': {'red': PaquebotRouge, 'green': PaquebotVert},
                    'eclaireur': {'red': EclaireurRouge, 'green': EclaireurVert},
                    'sousmarin': {'red': SousMarinRouge, 'green': SousMarinVert},
                }
                team_to_class = class_map.get(config_key)

                unit_class = team_to_class[team_key]
                unit = self.game.spawn_unit(unit_class)
                if unit is not None:
                    print(f"Unité produite: {unit_class.__name__}")
                return True


        elif self.game.show_unit_popup:
            return self._handle_popup_navigation(event)
        
        elif event.key == pygame.K_UP:  

            self.game.sound.increase_volume()
        
        elif event.key == pygame.K_DOWN:
            self.game.sound.decrease_volume()

        if event.key == pygame.K_LEFT:
            self.game.hud.popup_selection = (self.game.hud.popup_selection - 1) % len(self.game.hud.unit_names)
            time.sleep(0.1)
        if event.key == pygame.K_RIGHT:
            self.game.hud.popup_selection = (self.game.hud.popup_selection + 1) % len(self.game.hud.unit_names)
            time.sleep(0.1)

        return True
    
    
    def _handle_popup_navigation(self, event):
        """Gère la navigation dans le popup d'unités."""
        if event.key == pygame.K_UP:
            self.game.popup_selection = (self.game.popup_selection - 1) % len(self.game.unit_classes)
        elif event.key == pygame.K_DOWN:
            self.game.popup_selection = (self.game.popup_selection + 1) % len(self.game.unit_classes)
        elif event.key == pygame.K_RETURN:
            try:
                unit_name, unit_class = self.game.unit_classes[self.game.popup_selection]
                print(f"Unité sélectionnée: {unit_name}")
                unit = self.game.spawn_unit(unit_class)
                if unit is not None:
                    print(f"Unité produite: {unit_class.__name__}")
                    self.game.show_unit_popup = False
            except Exception as e:
                print(f"Erreur lors de la sélection de l'unité: {e}")
        return True
    
    def _handle_mouse_events(self, event):
        """Gère les événements de souris."""
        # Clic gauche
        if event.button == 1 and not self.game.show_unit_popup:  # Clic gauche
            world_x, world_y = self._screen_to_world_coordinates(pygame.mouse.get_pos())
            
            # Chercher une unité à cette position
            clicked_unit = self.game.find_unit_at_position(world_x, world_y)
            
            if clicked_unit:
                self.game.select_unit(clicked_unit)
            elif self.game.selected_unit and self.game.selected_unit.is_alive:
                # Déplacer l'unité sélectionnée vers la position cliquée
                if hasattr(self.game.selected_unit, 'move_to_position'):
                    self.game.selected_unit.move_to_position(world_x, world_y)
            else:
                self.game.select_unit(None)
        
        # Clic droit
        elif event.button == 3 and self.game.hud.timer.maree_haute:
            self.game.quantique()
        
        # Molette haut
        elif event.button == 4:
            if not getattr(self.game, 'paused', False):
                self.game.camera.zoom_in()
        
        # Molette bas
        elif event.button == 5:
            if not getattr(self.game, 'paused', False):
                self.game.camera.zoom_out()
    
    def _screen_to_world_coordinates(self, mouse_pos):
        """Convertit les coordonnées écran en coordonnées monde."""
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