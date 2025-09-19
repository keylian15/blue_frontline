import pygame
import time
class InputManager:
    """Gestionnaire des entrées continues pour le jeu."""
    
    def __init__(self, game):
        """Initialise le gestionnaire d'entrées avec une référence au jeu."""
        self.game = game
        self.last_hud_toggle_time = 0
        self.hud_toggle_cooldown = 200  # 200ms de cooldown
    
    def handle_continuous_input(self):
        """Gère les entrées continues (touches maintenues)."""
        pressed = pygame.key.get_pressed()
        
        # if not self.game.show_unit_popup:
        self._handle_camera_movement(pressed)
        self._handle_hud_toggle(pressed)
        self._handle_zoom(pressed)
        self._handle_unit_popup(pressed)
        self._handle_unit_popup_navigation(pressed)
    
    def _handle_camera_movement(self, pressed):
        """Gère le déplacement de la caméra avec les touches directionnelles."""
        
        dx, dy = 0, 0
        if pressed[pygame.K_z]:  # Haut
            dy -= self.game.camera.camera_move
        if pressed[pygame.K_s]:  # Bas
            dy += self.game.camera.camera_move
        if pressed[pygame.K_q]:  # Gauche 
            dx -= self.game.camera.camera_move
        if pressed[pygame.K_d]:  # Droite
            dx += self.game.camera.camera_move
        
        # Déplacer la caméra seulement s'il y a un déplacement
        if dx or dy:  
            self.game.camera.move(dx, dy)
    
    def _handle_hud_toggle(self, pressed):
        """Gère l'affichage/masquage du HUD avec cooldown non-bloquant."""
        current_time = pygame.time.get_ticks()
        
        if pressed[pygame.K_h] :
            if current_time - self.last_hud_toggle_time > self.hud_toggle_cooldown:
                self.game.hud.switch()
                self.last_hud_toggle_time = current_time
    
    def _handle_zoom(self, pressed):
        """Gère le zoom avec les touches P et M."""
        if pressed[pygame.K_p]:  # Touche P pour dézoomer
            self.game.camera.zoom_out()
        if pressed[pygame.K_m]:  # Touche M pour zoomer
            self.game.camera.zoom_in()
            
    def _handle_unit_popup(self, pressed):
        if pressed[pygame.K_j]:
            self.game.hud.toggle_popup_team()
            time.sleep(0.2)
            
    def _handle_unit_popup_navigation(self, pressed):
        if pressed[pygame.K_LEFT]:
            self.game.hud.popup_selection = (self.game.hud.popup_selection - 1) % len(self.game.hud.unit_names)
            time.sleep(0.1)
        if pressed[pygame.K_RIGHT]:
            self.game.hud.popup_selection = (self.game.hud.popup_selection + 1) % len(self.game.hud.unit_names)
            time.sleep(0.1)