import pygame
from Class.units.Unit import Unit
from Global import *

class EclaireurVert(Unit):
    """Classe pour l'unité Éclaireur Vert."""

    def __init__(self, x, y):
        # Initialiser avec l'image de l'éclaireur vert
        super().__init__(x, y, GREEN_ECLAIREUR_IMAGE_PATH, team="green")

        # === Spécifications de l'Éclaireur Vert ===
        self.cost = 60
        self.build_time = 60  # en secondes
        self.max_speed = 18  # pixels par seconde
        self.max_health = 2
        self.current_health = self.max_health
        self.range = 0  # en cases
        self.damage = 0
        self.fire_rate = 0  # Pas de tir
        self.unit_type = "eclaireur"
        self.unit_name = "Éclaireur Vert"
        self.is_moving = False
        self.target_position = None

    def move_to_position(self, target_x, target_y):
        """Déplace l'éclaireur vers une position cible."""
        self.target_position = (target_x, target_y)
        self.move_to(target_x, target_y, self.max_speed)
        self.is_moving = True

    def update(self, dt=0, combat_system=None, screen=None, camera_offset=(0, 0)):
        """Met à jour l'éclaireur vert."""
        super().update(dt, combat_system)
        if self.target_position and self.is_moving:
            distance_to_target = ((self.position[0] - self.target_position[0])**2 + 
                                  (self.position[1] - self.target_position[1])**2)**0.5
            if distance_to_target < 5:
                self.stop()
                self.is_moving = False
                self.target_position = None

    @staticmethod
    def get_build_requirements():
        """Retourne les exigences pour construire cette unité."""
        return {
            "cost": 60,
            "build_time": 60,
            "required_building": None
        }

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
