import pygame
from Class.units.Unit import Unit
from Class.Combat import CombatSystem
from Global import UNIT_CONFIGS


class PompePetroliere(Unit):
    """Classe unifiée pour les unités Pompe Pétrolière (Rouge et Vert).
    
    Unité statique qui ne peut ni tirer ni se déplacer.
    """
    
    def __init__(self, game: "Game", team: str):
        """Initialise une instance de Pompe Pétrolière.
        
        Args:
            game (Game): Instance du jeu.
            team (str): Équipe de l'unité.
        """
        # Récupérer la configuration depuis Global.py
        config = UNIT_CONFIGS["pompe_petroliere"]
        
        # Initialiser avec l'image appropriée et le type d'unité
        super().__init__(game, team=team, unit_type="pompe_petroliere")
        
        # === Spécifications de la Pompe Pétrolière depuis Global.py ===
        self.cost = config["cost"]
        
        # Vitesse nulle - unité statique
        self.max_speed = 0
        self.reducte_speed = 0
        self.speed = 0
        
        self.max_health = config["max_health"]
        self.current_health = self.max_health
        
        # Pas de capacité de combat
        self.range = 0
        self.damage = 0
        self.fire_rate = 0
        
        # Type d'unité
        self.unit_type = config["unit_type"]
        self.unit_name = f"Pompe Pétrolière {team.capitalize()}"
        
        # Pas de portée à afficher
        self.range_color = (0, 0, 0, 0)  # Transparent
        
        # État de mouvement (toujours False)
        self.is_moving = False
        self.target_position = None
        
        # Désactiver les capacités de combat et mouvement
        self.can_move = False
        self.can_attack = False
    
    def move_to(self, target_position):
        """Empêche le déplacement de la pompe pétrolière.
        
        Args:
            target_position: Position cible (ignorée)
        """
        return
    
    def attack(self, target):
        """Empêche l'attaque de la pompe pétrolière.
        
        Args:
            target: Cible à attaquer (ignorée)
        """
        return
    
    def can_attack(self):
        """La pompe pétrolière ne peut jamais attaquer.
        
        Returns:
            bool: Toujours False
        """
        return False
    
    def update(self, dt: int = 0, combat_system: CombatSystem = None, 
               screen: pygame.Surface = None, camera_offset: tuple[float, float] = (0, 0), 
               all_units: list[Unit] = None):
        """Met à jour l'unité en fonction de son état actuel.
        
        Args:
            dt (int, optional): La différence de temps entre chaque frame. Defaults to 0.
            combat_system (CombatSystem, optional): Le système de combat. Defaults to None.
            screen (pygame.Surface, optional): L'écran sur lequel afficher. Defaults to None.
            camera_offset (tuple[float, float], optional): La position de la caméra. Defaults to (0, 0).
            all_units (list[Unit], optional): Liste des unités. Defaults to None.
        """
        # Appeler la mise à jour de la classe parent (sans combat ni mouvement)
        # Uniquement pour la gestion de la santé et l'affichage
        super().update(dt, combat_system=None, screen=screen, camera_offset=camera_offset, all_units=all_units)
        

# Classes d'alias pour la compatibilité avec l'ancien code
class PompePetroliereRouge(PompePetroliere):
    def __init__(self, game: "Game"):
        """Constructeur de la classe PompePetroliereRouge.
        
        Args:
            game (Game): L'instance du jeu.
        """
        super().__init__(game, team="red")
        
    def die(self, killer: "Unit"=None):
        """Gère la mort de l'unité et attribue des pièces à l'ennemi si applicable.

        Args:
            killer (Unit, optional): L'entité attaquante. Defaults to None.
        """
        
        super().die(killer) # On appelle la méthode die() de la classe Unit
        self.game.nbPompePetroliereRouge -= 1


class PompePetroliereVert(PompePetroliere):
    def __init__(self, game: "Game"):
        """Constructeur de la classe PompePetroliereVert.
        
        Args:
            game (Game): L'instance du jeu.
        """
        super().__init__(game, team="green")
        
    def die(self, killer: "Unit"=None):
        """Gère la mort de l'unité et attribue des pièces à l'ennemi si applicable.

        Args:
            killer (Unit, optional): L'entité attaquante. Defaults to None.
        """
        
        super().die(killer) # On appelle la méthode die() de la classe Unit
        self.game.nbPompePetroliereVert -= 1
