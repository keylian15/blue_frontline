import pygame
from Class.units.Unit import Unit
from Global import UNIT_CONFIGS

class Chaloupe(Unit):
    """Classe unifiée pour les unités Chaloupe (Rouge et Verte)."""
    
    def __init__(self, x, y, team="red"):
        # Récupérer la configuration depuis Global.py
        config = UNIT_CONFIGS["chaloupe"]
        
        # Déterminer le chemin de l'image selon l'équipe
        image_path = config["image_paths"][team]
        
        # Initialiser avec l'image appropriée et le type d'unité
        super().__init__(x, y, image_path, team=team, unit_type="chaloupe")
        
        # === Spécifications de la Chaloupe depuis Global.py ===
        self.cost = config["cost"]
        self.build_time = config["build_time"]
        self.max_speed = config["max_speed"]
        self.max_health = config["max_health"]
        self.current_health = self.max_health
        self.range = config["range"]
        self.damage = config["damage"]
        self.fire_rate = config["fire_rate"]
        
        # Type d'unité
        self.unit_type = config["unit_type"]
        self.unit_name = f"Chaloupe {team.capitalize()}"
        
        # Couleur de portée selon l'équipe
        self.range_color = config["range_color"][team]
        
        # État de mouvement
        self.is_moving = False
        self.target_position = None
        
    def update(self, dt=0, combat_system=None, screen=None, camera_offset=(0, 0), all_units=None):
        """Met à jour la chaloupe."""
        # Appeler la mise à jour de la classe parent
        super().update(dt, combat_system, screen, camera_offset, all_units)

        # Dessiner la portée en permanence
        if screen:
            self.draw_range(screen, camera_offset)# Classes d'alias pour la compatibilité avec l'ancien code
            
class ChaloupeRouge(Chaloupe):
    def __init__(self, x, y):
        super().__init__(x, y, team="red")

class ChaloupeVerte(Chaloupe):
    def __init__(self, x, y):
        super().__init__(x, y, team="green")