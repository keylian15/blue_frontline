import pygame
from Global import *

class Camera(pygame.sprite.Sprite):
    """Classe pour gérer la caméra."""

    def __init__(self, x, y, screen_size, map_size):
        super().__init__()
        # Déplacement de la caméra (en pixels)
        self.camera_move = 20

        # === Limites de la caméra ===
        self.screen_width, self.screen_height = screen_size
        self.map_width, self.map_height = map_size
        
        # Calculer les limites pour centrer la caméra
        self.min_x = self.screen_width // 2
        self.max_x = self.map_width - self.screen_width // 2
        self.min_y = self.screen_height // 2
        self.max_y = self.map_height - self.screen_height // 2
        
        print(f"Limites caméra: X({self.min_x}-{self.max_x}), Y({self.min_y}-{self.max_y})")

        # === Test visuel de la caméra ===
        # On fait un sprite pour la caméra (image de munitions pour l'instant)
        # self.sprite_sheet = pygame.image.load(BULLET_IMAGE_PATH)
        # self.image = self.get_image(x, y)
        # self.image.set_colorkey([0, 0, 0]) # On enleve le noir
        # === Test visuel de la caméra ===
        
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        
        # Position initiale avec contraintes
        self.position = [
            max(self.min_x, min(self.max_x, x)),
            max(self.min_y, min(self.max_y, y))
        ]
        
    # === Test visuel de la caméra ===
    def get_image(self, x, y):
        """Récupère une image de la sprite sheet."""
        image = pygame.Surface([32, 32], pygame.SRCALPHA)
        image.blit(self.sprite_sheet, (0, 0), (x, y, 32, 32))
        return image
    
    def update(self):
        """Met à jour la position du rectangle de la caméra."""
        # CORRECTION CRITIQUE : pyscroll utilise rect.center, pas rect.topleft !
        self.rect.center = self.position

    def move(self, dx, dy):
        """Déplace la caméra avec contraintes de limites."""
        # Nouvelle position proposée
        new_x = self.position[0] + dx
        new_y = self.position[1] + dy
        
        # Appliquer les contraintes
        self.position[0] = max(self.min_x, min(self.max_x, new_x))
        self.position[1] = max(self.min_y, min(self.max_y, new_y))