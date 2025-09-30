import pygame
import time
from Class.OptionsMenu import OptionsMenu
from Class.units.Unit import Unit
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
    
    def _handle_keydown_events(self, event):
        """Gère les événements de touches pressées."""        
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
            
            # S'il n'y a pas assez de pétrole.
            if team_key == "red"  :
                if self.game.hud.petrole_red.count < cost:
                    return None
                else : 
                    self.game.hud.petrole_red.count -= cost
            else : 
                if self.game.hud.petrole_green.count < cost: 
                    return None
                else :
                    self.game.hud.petrole_green.count -= cost
            
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

        elif event.key == pygame.K_UP:  

            self.game.sound.increase_volume()
        
        elif event.key == pygame.K_DOWN:
            self.game.sound.decrease_volume()

        if event.key == pygame.K_LEFT:
            self.game.hud.popup_selection = (self.game.hud.popup_selection - 1) % len(self.game.hud.unit_names)
            return True
        if event.key == pygame.K_RIGHT:
            self.game.hud.popup_selection = (self.game.hud.popup_selection + 1) % len(self.game.hud.unit_names)
            return True
        
        if event.key == pygame.K_v:
            # Cycler la vitesse du temps
            new_speed = self.game.hud.timer.cycle_speed()
            # Synchroniser la vitesse du pétrole avec le timer
            self.game.hud.petrole_red.set_speed(new_speed)
            self.game.hud.petrole_green.set_speed(new_speed)
            return True
        
        if event.key == pygame.K_j :
            self.game.hud.toggle_popup_team()
            self.game.hud.switch_team()
            return True
        
        return True
    

    def _handle_mouse_events(self, event):
        """Gère les événements de souris."""
        # Si le jeu est gagné, gérer les clics sur l'écran de victoire
        if self.game.game_won and event.button == 1:
            self.game.handle_victory_click(pygame.mouse.get_pos())
            return
        
        # Clic gauche
        if event.button == 1:  # Clic gauche
            world_x, world_y = self._screen_to_world_coordinates(pygame.mouse.get_pos())
            # Chercher une unité à cette position
            clicked_unit = self.game.find_unit_at_position(world_x, world_y)
            
            if clicked_unit:
                self.game.select_unit(clicked_unit)
            elif self.game.selected_unit and self.game.selected_unit.is_alive and hasattr(self.game.selected_unit, 'move_to_position'):
                # Déplacer l'unité sélectionnée vers la position cliquée
                self.game.selected_unit.move_to_position((world_x, world_y))
            else:
                self.game.select_unit(None)
        
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