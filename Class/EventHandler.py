import pygame

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
                # Marquer le changement comme traité
                self.game.hud.timer.maree_changed = False
                        
            # Clic droit pour générer l'île
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
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
        if event.key == pygame.K_e:
            self.game.show_unit_popup = not self.game.show_unit_popup
            self.game.popup_selection = 0
            print(f"Popup {'ouvert' if self.game.show_unit_popup else 'fermé'}")
            return True

        elif self.game.show_unit_popup:
            return self._handle_popup_navigation(event)
        
        elif event.key == pygame.K_UP:
            self.game.sound.increase_volume()
        
        elif event.key == pygame.K_DOWN:
            self.game.sound.decrease_volume()
        
        return True
    
    def _handle_popup_navigation(self, event):
        """Gère la navigation dans le popup d'unités."""
        if event.key == pygame.K_UP:
            self.game.popup_selection = (self.game.popup_selection - 1) % len(self.game.unit_classes)
            print(f"Sélection précédente: {self.game.popup_selection}")
        elif event.key == pygame.K_DOWN:
            self.game.popup_selection = (self.game.popup_selection + 1) % len(self.game.unit_classes)
            print(f"Sélection suivante: {self.game.popup_selection}")
        elif event.key == pygame.K_RETURN:
            try:
                unit_name, unit_class = self.game.unit_classes[self.game.popup_selection]
                print(f"Unité sélectionnée: {unit_name}")
                self.game.spawn_unit(unit_class)
                self.game.show_unit_popup = False
            except Exception as e:
                print(f"Erreur lors de la sélection de l'unité: {e}")
        return True
    
    def _handle_mouse_events(self, event):
        """Gère les événements de souris."""
        if event.button == 1 and not self.game.show_unit_popup:  # Clic gauche
            world_x, world_y = self._screen_to_world_coordinates(pygame.mouse.get_pos())
            
            # Chercher une unité à cette position
            clicked_unit = self.game.find_unit_at_position(world_x, world_y)
            
            if clicked_unit:
                self.game.selected_unit = clicked_unit
                print(f"Unité sélectionnée: {clicked_unit.__class__.__name__}")
            elif self.game.selected_unit and self.game.selected_unit.is_alive:
                # Déplacer l'unité sélectionnée vers la position cliquée
                if hasattr(self.game.selected_unit, 'move_to_position'):
                    self.game.selected_unit.move_to_position(world_x, world_y)
                    print(f"Déplacement de {self.game.selected_unit.__class__.__name__}")
            else:
                self.game.selected_unit = None
    
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