from Class.units.Unit import Unit
from Global import UNIT_CONFIGS

class Paquebot(Unit):
    """Classe unifiée pour les unités Paquebot (Rouge et Vert)."""
    
    def __init__(self, game, team):
        # Récupérer la configuration depuis Global.py
        config = UNIT_CONFIGS["paquebot"]
       
        # Initialiser avec l'image appropriée et le type d'unité
        super().__init__(game, team=team, unit_type="paquebot")
        
        # === Spécifications du Paquebot depuis Global.py ===
        self.cost = config["cost"]
        
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

# Classes d'alias pour la compatibilité avec l'ancien code
class PaquebotRouge(Paquebot):
    def __init__(self, game):
        super().__init__(game, team="red")

class PaquebotVert(Paquebot):
    def __init__(self, game):
        super().__init__(game, team="green")