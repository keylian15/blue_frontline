import pygame
from Class.units.Unit import Unit
from Class.Combat import CombatSystem
from Global import UNIT_CONFIGS

class Eclaireur(Unit):
    """Classe unifiée pour les unités Éclaireur (Rouge et Vert)."""
    
    def __init__(self, game: "Game", team: str):
        """Initialise l'unité Éclaireur.

        Args:
            game (Game): Instance du jeu.
            team (str): Équipe de l'unité.
        """
        # Récupérer la configuration depuis Global.py
        config = UNIT_CONFIGS["eclaireur"]
        
        # Initialiser avec l'image appropriée et le type d'unité
        super().__init__(game, team=team, unit_type="eclaireur")
        
        # === Spécifications de l'Éclaireur depuis Global.py ===
        self.cost = config["cost"]
        
        self.max_speed = config["max_speed"]
        self.reducte_speed = self.max_speed // 2
        self.speed = self.max_speed # Par défaut speed = speed max
        self.max_health = config["max_health"]
        self.current_health = self.max_health
        self.range = 0  # Les éclaireurs ne tirent pas
        self.damage = 0
        self.fire_rate = 0
        
        # Type d'unité
        self.unit_type = config["unit_type"]
        self.unit_name = f"Éclaireur {team.capitalize()}"
        
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
class EclaireurRouge(Eclaireur):
    def __init__(self, game: "Game"):
        """Constructeur de la classe EclaireurRouge.

        Args:
            game (Game): L'instance du jeu.
        """ 
        super().__init__(game, team="red")

class EclaireurVert(Eclaireur):
    def __init__(self, game: "Game"):
        """Constructeur de la classe EclaireurVert.

        Args:
            game (Game): L'instance du jeu.
        """
        super().__init__(game, team="green")