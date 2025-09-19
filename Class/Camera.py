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
        
        # === Système de zoom ===
        self.zoom_level = 1.0  # Niveau de zoom actuel (1.0 = normal)
        self.max_zoom = 2.0    # Zoom maximum
        self.zoom_speed = 0.02 # Vitesse de zoom
        self.default_zoom = 1.0  # Zoom par défaut pour retour normal
        
        # Calculer le zoom minimum pour voir toute la map
        self.min_zoom = self.calculate_min_zoom_for_full_map()
        
        # Calculer les limites pour centrer la caméra
        self.update_zoom_limits()
        
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
    
    def calculate_min_zoom_for_full_map(self):
        """Calcule le niveau de zoom minimum nécessaire pour voir toute la map."""
        # Calculer les ratios pour voir toute la map dans chaque dimension
        zoom_x = self.screen_width / self.map_width
        zoom_y = self.screen_height / self.map_height
        
        # Prendre le plus petit pour que toute la map soit visible
        min_zoom = min(zoom_x, zoom_y)
        
        # Ajouter une petite marge pour éviter les effets de bord
        min_zoom = min_zoom * 0.95
        
        print(f"Zoom minimum calculé: {min_zoom:.3f} (pour voir map {self.map_width}x{self.map_height} sur écran {self.screen_width}x{self.screen_height})")
        
        return min_zoom

    def update_zoom_limits(self):
        """Met à jour les limites de la caméra en fonction du niveau de zoom."""
        # Calculer les limites en fonction du zoom
        effective_screen_width = self.screen_width / self.zoom_level
        effective_screen_height = self.screen_height / self.zoom_level
        
        self.min_x = effective_screen_width // 2
        self.max_x = self.map_width - effective_screen_width // 2
        self.min_y = effective_screen_height // 2
        self.max_y = self.map_height - effective_screen_height // 2
        
        # S'assurer que min <= max
        if self.min_x > self.max_x:
            center_x = self.map_width // 2
            self.min_x = self.max_x = center_x
        if self.min_y > self.max_y:
            center_y = self.map_height // 2
            self.min_y = self.max_y = center_y

    def zoom_in(self):
        """Zoom avant (augmente le niveau de zoom)."""
        if self.zoom_level < self.max_zoom:
            self.zoom_level = min(self.max_zoom, self.zoom_level + self.zoom_speed)
            self.update_zoom_limits()
            # Recalculer la position pour rester dans les limites
            self.position[0] = max(self.min_x, min(self.max_x, self.position[0]))
            self.position[1] = max(self.min_y, min(self.max_y, self.position[1]))

    def zoom_out(self):
        """Zoom arrière (diminue le niveau de zoom)."""
        if self.zoom_level > self.min_zoom:
            new_zoom_level = max(self.min_zoom, self.zoom_level - self.zoom_speed)
            
            # Si on atteint le zoom minimum, afficher un message informatif
            if new_zoom_level == self.min_zoom and self.zoom_level > self.min_zoom:
                print(f"Zoom minimum atteint ({self.min_zoom:.3f}) - toute la map est maintenant visible")
            
            self.zoom_level = new_zoom_level
            self.update_zoom_limits()
            # Recalculer la position pour rester dans les limites
            self.position[0] = max(self.min_x, min(self.max_x, self.position[0]))
            self.position[1] = max(self.min_y, min(self.max_y, self.position[1]))

    def get_effective_screen_size(self):
        """Retourne la taille effective de l'écran selon le niveau de zoom."""
        return (self.screen_width / self.zoom_level, self.screen_height / self.zoom_level)

    def update(self):
        """Met à jour la position du rectangle de la caméra."""
        # CORRECTION CRITIQUE : pyscroll utilise rect.center, pas rect.topleft !
        self.rect.center = self.position

    def move(self, dx, dy):
        """Déplace la caméra avec contraintes de limites."""
        # Adapter le déplacement au niveau de zoom
        adjusted_dx = dx / self.zoom_level
        adjusted_dy = dy / self.zoom_level
        
        # Nouvelle position proposée
        new_x = self.position[0] + adjusted_dx
        new_y = self.position[1] + adjusted_dy
        
        # Appliquer les contraintes
        self.position[0] = max(self.min_x, min(self.max_x, new_x))
        self.position[1] = max(self.min_y, min(self.max_y, new_y))