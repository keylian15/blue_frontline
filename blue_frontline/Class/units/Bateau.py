import pygame
from Class.units.Unit import Unit
from Class.Combat import CombatSystem
from Global import UNIT_CONFIGS

class Bateau(Unit):
    """Classe unifiée pour les unités Bateau (Rouge et Vert)."""
    
    def __init__(self, game: "Game", team: str):
        """Fonction d'initialisation de la classe Bateau.

        Args:
            game (Game): L'instance du jeu.
            team (str): L'équipe de l'unité.
        """
        
        # Récupérer la configuration depuis Global.py
        config = UNIT_CONFIGS["bateau"]
        
        # Initialiser avec l'image appropriée et le type d'unité
        super().__init__(game, team=team, unit_type="bateau")
        
        # === Spécifications du Bateau depuis Global.py ===
        self.cost = config["cost"]
        
        self.max_speed = config["max_speed"]
        self.max_health = config["max_health"]
        self.current_health = self.max_health
        self.range = config["range"]
        self.damage = config["damage"]
        self.fire_rate = config["fire_rate"]
        
        # Type d'unité
        self.unit_type = config["unit_type"]
        self.unit_name = f"Bateau {team.capitalize()}"
        
        # Couleur de portée selon l'équipe
        self.range_color = config["range_color"][team]
        
        # État de mouvement
        self.is_moving = False
        self.target_position = None
            
    def update(self, dt: int = 0, combat_system: CombatSystem = None, screen: pygame.Surface = None, camera_offset: tuple[float, float] =(0, 0), all_units: list[Unit] = None):
        """Met à jour l'unité en fonction de son état actuel.

        Args:
            dt (int, optional): La différence de temps entre chaque frame. Defaults to 0.
            combat_system (CombatSystem, optional): Le systeme de combat. Defaults to None.
            screen (pygame.Surface, optional): L'écran sur lequel affiché. Defaults to None.
            camera_offset (tuple[float, float], optional): La position de la caméra. Defaults to (0, 0).
            all_units (list[Unit], optional): Liste des unités. Defaults to None.
        """

        # Appeler la mise à jour de la classe parent
        super().update(dt, combat_system, screen, camera_offset, all_units)
        
        # Dessiner la portée en permanence
        if screen:
            self.draw_range(screen, camera_offset)

# Classes d'alias pour la compatibilité avec l'ancien code
class BateauRouge(Bateau):
    def __init__(self, game: "Game"):
        """Fonction d'initialisation de la classe BateauRouge.

        Args:
            game (Game): L'instance de la classe Game.
        """
        super().__init__(game, team="red")

class BateauVert(Bateau):
    def __init__(self, game: "Game"):
        """Fonction d'initialisation de la classe BateauVert.

        Args:
            game (Game): L'instance de la classe Game.
        """
        super().__init__(game, team="green")