import pygame

class InputManager:
    """Gestionnaire des entrées continues pour le jeu."""
    
    def __init__(self, game):
        """Initialise le gestionnaire d'entrées avec une référence au jeu."""
        self.game = game
        self.last_hud_toggle_time = 0
        self.hud_toggle_cooldown = 200  # 200ms de cooldown
    
    def handle_continuous_input(self):
        """Gère les entrées continues (touches maintenues)."""
        if not self.game.show_unit_popup:
            self._handle_camera_movement()
            self._handle_hud_toggle()
            self._handle_zoom()
    
    def _handle_camera_movement(self):
        """Gère le déplacement de la caméra avec les touches directionnelles."""
        pressed = pygame.key.get_pressed()
        
        dx, dy = 0, 0
        if pressed[pygame.K_UP]:  # Haut
            dy -= self.game.camera.camera_move
        if pressed[pygame.K_DOWN]:  # Bas
            dy += self.game.camera.camera_move
        if pressed[pygame.K_LEFT]:  # Gauche 
            dx -= self.game.camera.camera_move
        if pressed[pygame.K_RIGHT]:  # Droite
            dx += self.game.camera.camera_move
        
        # Déplacer la caméra seulement s'il y a un déplacement
        if dx or dy:  
            self.game.camera.move(dx, dy)
    
    def _handle_hud_toggle(self):
        """Gère l'affichage/masquage du HUD avec cooldown non-bloquant."""
        pressed = pygame.key.get_pressed()
        current_time = pygame.time.get_ticks()
        
        if pressed[pygame.K_h] and current_time - self.last_hud_toggle_time > self.hud_toggle_cooldown:
            self.game.hud.switch()
            self.last_hud_toggle_time = current_time
    
    def _handle_zoom(self):
        """Gère le zoom avec les touches P et M."""
        pressed = pygame.key.get_pressed()
        
        if pressed[pygame.K_p]:  # Touche P pour dézoomer
            self.game.camera.zoom_out()
        if pressed[pygame.K_m]:  # Touche M pour zoomer
            self.game.camera.zoom_in()