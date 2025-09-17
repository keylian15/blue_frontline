import pygame
from Class.units.Unit import Unit
from Global import *

class PaquebotRouge(Unit):
    """Classe pour l'unité Paquebot Rouge."""
    
    def __init__(self, x, y):
        # Initialiser avec l'image du paquebot rouge
        super().__init__(x, y, RED_PAQUEBOT_IMAGE_PATH, team="red")
        
        # === Spécifications du Paquebot Rouge ===
        # Coût : 120 pétroles (2 minutes)
        self.cost = 120
        self.build_time = 120  # en secondes
        
        # Vitesse : 50 x/s et 50 y/s
        self.max_speed = 50  # pixels par seconde
        
        # Blindage : 50
        self.max_health = 50
        self.current_health = self.max_health
        
        # Range : 15 cases
        self.range = 15  # en cases (64 pixels)
        
        # Puissance de tir : 12 dégâts / seconde
        self.damage = 12
        self.fire_rate = 1.0  # 1 tir par seconde pour faire 12 dégâts/seconde
        
        # Type d'unité
        self.unit_type = "paquebot"
        self.unit_name = "Paquebot Rouge"
        
        # État de mouvement
        self.is_moving = False
        self.target_position = None
        
    def move_to_position(self, target_x, target_y):
        """Déplace le paquebot vers une position cible."""
        self.target_position = (target_x, target_y)
        self.move_to(target_x, target_y, self.max_speed)
        self.is_moving = True
    
    def update(self, dt=0, combat_system=None, screen=None, camera_offset=(0, 0)):
        """Met à jour le paquebot rouge."""
        # Appeler la mise à jour de la classe parent
        super().update(dt, combat_system)
        
        # Vérifier si on a atteint la destination
        if self.target_position and self.is_moving:
            distance_to_target = ((self.position[0] - self.target_position[0])**2 + 
                                (self.position[1] - self.target_position[1])**2)**0.5
            
            # Si on est proche de la destination (moins de 5 pixels)
            if distance_to_target < 5:
                self.stop()
                self.is_moving = False
                self.target_position = None

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

        # Dessiner un cercle semi-transparent pour la portée
        surface = pygame.Surface((range_radius * 2, range_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surface, (255, 0, 0, 50), (range_radius, range_radius), range_radius)
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
    
    def can_build():
        """Méthode statique pour vérifier si on peut construire un paquebot."""
        # Cette méthode peut être utilisée pour vérifier les ressources
        # Retourne True si on a assez de pétrole (à implémenter avec le système de ressources)
        return True  # Pour l'instant, toujours possible
    
    @staticmethod
    def get_build_requirements():
        """Retourne les exigences pour construire cette unité."""
        return {
            "cost": 120,
            "build_time": 120,
            "required_building": None  # Pas de bâtiment requis pour le paquebot
        }
