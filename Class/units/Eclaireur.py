import pygame
from Class.units.Unit import Unit
from Global import UNIT_CONFIGS

class Eclaireur(Unit):
    """Classe unifiée pour les unités Éclaireur (Rouge et Vert)."""
    
    def __init__(self, x, y, team="red"):
        # Récupérer la configuration depuis Global.py
        config = UNIT_CONFIGS["eclaireur"]
        
        # Déterminer le chemin de l'image selon l'équipe
        image_path = config["image_paths"][team]
        
        # Initialiser avec l'image appropriée et le type d'unité
        super().__init__(x, y, image_path, team=team, unit_type="eclaireur")
        
        # === Spécifications de l'Éclaireur depuis Global.py ===
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
        self.unit_name = f"Éclaireur {team.capitalize()}"
        
        # Couleur de portée selon l'équipe
        self.range_color = config["range_color"][team]
        
        # État de mouvement
        self.is_moving = False
        self.target_position = None
        
    def move_to_position(self, target_x, target_y):
        """Déplace l'éclaireur vers une position cible."""
        self.target_position = (target_x, target_y)
        self.move_to(target_x, target_y, self.max_speed)
        self.is_moving = True
    
    def update(self, dt=0, combat_system=None, screen=None, camera_offset=(0, 0), all_units=None):
        """Met à jour l'éclaireur."""
        # Appeler la mise à jour de la classe parent
        super().update(dt, combat_system, screen, camera_offset, all_units)
        
        # Vérifier si on a atteint la destination
        if self.target_position and self.is_moving:
            distance_to_target = ((self.position[0] - self.target_position[0])**2 + 
                                (self.position[1] - self.target_position[1])**2)**0.5
            
            # Si on est proche de la destination (moins de 5 pixels)
            if distance_to_target < 5:
                self.stop()
                self.is_moving = False
                self.target_position = None
    
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
            "is_moving": self.is_moving,
            "is_selected": self.is_selected,
            "enemies_in_range": len(self.enemies_in_range)
        }
    
    @staticmethod
    def can_build():
        """Méthode statique pour vérifier si on peut construire un éclaireur."""
        # Cette méthode peut être utilisée pour vérifier les ressources
        # Retourne True si on a assez de pétrole (à implémenter avec le système de ressources)
        return True  # Pour l'instant, toujours possible
    
    @staticmethod
    def get_build_requirements():
        """Retourne les exigences pour construire cette unité."""
        config = UNIT_CONFIGS["eclaireur"]
        return {
            "cost": config["cost"],
            "build_time": config["build_time"],
            "required_building": None  # Pas de bâtiment requis pour l'éclaireur
        }

# Classes d'alias pour la compatibilité avec l'ancien code
class EclaireurRouge(Eclaireur):
    def __init__(self, x, y):
        super().__init__(x, y, team="red")

class EclaireurVert(Eclaireur):
    def __init__(self, x, y):
        super().__init__(x, y, team="green")