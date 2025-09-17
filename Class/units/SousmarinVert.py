import pygame
from Class.units.Unit import Unit
from Global import *

class SousMarinVert(Unit):
    """Classe pour l'unité Sous-Marin Vert."""

    def __init__(self, x, y):
        # Initialiser avec l'image du sous-marin vert
        super().__init__(x, y, GREEN_SUBMARINE_IMAGE_PATH, team="green")

        # === Spécifications du Sous-Marin Vert ===
        self.cost = 180
        self.build_time = 180  # en secondes
        self.max_speed = 65  # pixels par seconde
        self.max_health = 35
        self.current_health = self.max_health
        self.range = 5  # en cases (64 pixels)
        self.damage = 18  # dégâts par mine
        self.fire_rate = 1.0  # 1 mine par seconde
        self.unit_type = "sous-marin"
        self.unit_name = "Sous-Marin Vert"

        # État de mouvement
        self.is_moving = False
        self.target_position = None

    def move_to_position(self, target_x, target_y):
        """Déplace le sous-marin vers une position cible."""
        self.target_position = (target_x, target_y)
        self.move_to(target_x, target_y, self.max_speed)
        self.is_moving = True

    def update(self, dt=0, combat_system=None, screen=None, camera_offset=(0, 0)):
        """Met à jour le sous-marin vert."""
        super().update(dt, combat_system)

        if self.target_position and self.is_moving:
            distance_to_target = ((self.position[0] - self.target_position[0])**2 + 
                                  (self.position[1] - self.target_position[1])**2)**0.5

            if distance_to_target < 5:
                self.stop()
                self.is_moving = False
                self.target_position = None

        if screen:
            self.draw_range(screen, camera_offset)

    def draw_range(self, screen, camera_offset=(0, 0)):
        """Dessine une zone de portée de tir autour du sous-marin."""
        if not self.is_alive:
            return

        range_radius = self.range * 32
        center_x = int(self.position[0] - camera_offset[0])
        center_y = int(self.position[1] - camera_offset[1])

        surface = pygame.Surface((range_radius * 2, range_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surface, (0, 255, 0, 50), (range_radius, range_radius), range_radius)
        screen.blit(surface, (center_x - range_radius, center_y - range_radius))

    def get_info(self):
        """Retourne les informations de l'unité."""
        return {
            "name": self.unit_name,
            "type": self.unit_type,
            "team": self.team,
            "health": f"{self.current_health}/{self.max_health}",
            "cost": self.cost,
            "speed": self.max_speed,
            "range": self.range,
            "damage": self.damage,
            "fire_rate": self.fire_rate,
            "position": (int(self.position[0]), int(self.position[1])),
            "is_alive": self.is_alive,
            "is_moving": self.is_moving
        }

    @staticmethod
    def get_build_requirements():
        """Retourne les exigences pour construire cette unité."""
        return {
            "cost": 180,
            "build_time": 180,
            "required_building": None
        }
