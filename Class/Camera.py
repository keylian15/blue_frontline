import pygame
from Global import *

class Camera(pygame.sprite.Sprite):
    """Classe pour gérer la caméra."""

    def __init__(self, x, y):
        super().__init__()
        # Déplacement de la caméra (en pixels)
        self.camera_move = 20

        # === Test visuel de la caméra ===
        # On fait un sprite pour la caméra (image de munitions pour l'instant)
        # self.sprite_sheet = pygame.image.load(BULLET_IMAGE_PATH)
        # self.image = self.get_image(x, y)
        # self.image.set_colorkey([0, 0, 0]) # On enleve le noir
        # === Test visuel de la caméra ===
        
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.position = [x, y]
        
    # === Test visuel de la caméra ===
    def get_image(self, x, y):
        """Récupère une image de la sprite sheet."""
        image = pygame.Surface([32, 32], pygame.SRCALPHA)
        image.blit(self.sprite_sheet, (0, 0), (x, y, 32, 32))
        return image
    
    def update(self):
        """Met à jour la position du rectangle de la caméra."""
        self.rect.topleft = self.position

    def move(self, dx, dy):
        """Déplace la caméra."""
        self.position[0] += dx
        self.position[1] += dy