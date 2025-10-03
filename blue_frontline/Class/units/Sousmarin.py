import pygame
from Class.units.Unit import Unit
from Class.Combat import CombatSystem, Mine
from math import * 
from Global import UNIT_CONFIGS

class SousMarin(Unit):
    """Classe unifiée pour les unités Sous-marin (Rouge et Vert)."""
    
    def __init__(self, game: "Game", team: str):
        """Initialise une instance de SousMarin.

        Args:
            game (Game): Instance du jeu.
            team (str): Équipe de l'unité.
        """
        # Récupérer la configuration depuis Global.py
        config = UNIT_CONFIGS["sousmarin"]
        
        # Initialiser avec l'image appropriée et le type d'unité
        super().__init__(game, team=team, unit_type="sousmarin")
        
        # === Spécifications du Sous-marin depuis Global.py ===
        self.cost = config["cost"]
        
        self.max_speed = config["max_speed"]
        self.max_health = config["max_health"]
        self.current_health = self.max_health
        self.range = config["range"]
        self.damage = config["damage"]
        self.fire_rate = config["fire_rate"]
        
        # Type d'unité et capacité spéciale
        self.unit_type = config["unit_type"]
        self.unit_name = f"Sous-marin {team.capitalize()}"
        self.special_ability = config.get("special_ability", None)
        
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
    
    def place_mine(self, x: int, y: int):
        """Place une mine à la position spécifiée (capacité spéciale du sous-marin).

        Args:
            x (int): La position x de la mine.
            y (int): La position y de la mine.

        Returns:
            bool : True si la mine a été placée, False sinon.
        """
        if self.special_ability == "mines":
            # Créer la mine à la position exacte du sous-marin
            mine = Mine(x, y, self.team, damage=18)
            if hasattr(self.game, 'combat_system') and self.game.combat_system:
                self.game.combat_system.add_mine(mine)
  

            # -- AUDIO : drop mine --
            try:
                if hasattr(self.game, "sound") and self.game.sound:
                    self.game.sound.on_mine_dropped((x, y))
            except Exception:
                # ne jamais crasher pour du son
                pass
            return True
        return False


# Classes d'alias pour la compatibilité avec l'ancien code
class SousMarinRouge(SousMarin):
    def __init__(self, game: "Game"):
        """Constructeur de SousMarinRouge.

        Args:
            game (Game): L'instance de la classe Game.
        """
        super().__init__(game, team="red")

class SousMarinVert(SousMarin):
    def __init__(self, game: "Game"):
        """Constructeur de SousMarinVert.

        Args:
            game (Game): L'instance de la classe Game.
        """
        super().__init__(game, team="green")
