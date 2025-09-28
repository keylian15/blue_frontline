import pygame
from Class.units.Unit import Unit
from Global import UNIT_CONFIGS

class Paquebot(Unit):
    """Classe unifiée pour les unités Paquebot (Rouge et Vert)."""
    
    def __init__(self, x, y, team="red"):
        # Récupérer la configuration depuis Global.py
        config = UNIT_CONFIGS["paquebot"]
        
        # Déterminer le chemin de l'image selon l'équipe
        image_path = config["image_paths"][team]
        
        # Initialiser avec l'image appropriée et le type d'unité
        super().__init__(x, y, image_path, team=team, unit_type="paquebot")
        
        # === Spécifications du Paquebot depuis Global.py ===
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
        self.unit_name = f"Paquebot {team.capitalize()}"
        
        # Couleur de portée selon l'équipe
        self.range_color = config["range_color"][team]
        
        # État de mouvement
        self.is_moving = False
        self.target_position = None
            
    def update(self, dt=0, combat_system=None, screen=None, camera_offset=(0, 0), all_units=None):
        """Met à jour le paquebot."""
        # Appeler la mise à jour de la classe parent
        super().update(dt, combat_system, screen, camera_offset, all_units)

        # Dessiner la portée en permanence
        if screen:
            self.draw_range(screen, camera_offset)
    
    def draw_range(self, screen, camera_offset=(0, 0)):
        """Dessine une zone de portée de tir autour du paquebot."""
        if not self.is_alive:
            return

        # Calculer le rayon en pixels (range en cases * 32 pixels par case)
        range_radius = self.range * 32

        # Position du paquebot avec décalage de la caméra
        center_x = int(self.position[0] - camera_offset[0])
        center_y = int(self.position[1] - camera_offset[1])

        # Dessiner un cercle semi-transparent pour la portée avec la couleur de l'équipe
        surface = pygame.Surface((range_radius * 2, range_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surface, self.range_color, (range_radius, range_radius), range_radius)
        screen.blit(surface, (center_x - range_radius, center_y - range_radius))
  
# Classes d'alias pour la compatibilité avec l'ancien code
class PaquebotRouge(Paquebot):
    def __init__(self, x, y):
        super().__init__(x, y, team="red")

class PaquebotVert(Paquebot):
    def __init__(self, x, y):
        super().__init__(x, y, team="green")