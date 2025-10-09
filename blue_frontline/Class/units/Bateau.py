import pygame
from Class.units.Unit import Unit
from Class.Combat import CombatSystem
from Global import UNIT_CONFIGS
from Utils import point_in_many_polygons


class Bateau(Unit):
    """Classe unifiée pour les unités Bateau (Rouge et Vert)."""
    
    def __init__(self, game: "Game", team: str, ia: bool = True):
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
        self.reducte_speed = self.max_speed // 2
        self.speed = self.max_speed # Par défaut speed = speed max
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
        
        self.ia =  ia
        self.current_goal = None
        self.path = []
        self._pi = 0

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
        
        if self.ia :
            if self.get_closest_enemy_in_range():
                self.attack(self.get_closest_enemy_in_range(), combat_system)

            if self.current_goal is None:
                self.find_goal()
            else:
                self.move_towards_goal()
        
   
        

    def find_goal(self):
        base_enemie = self.get_base()
        if base_enemie:
            self.current_goal = tuple(base_enemie.position)
            self.path = self.cree_chemin(self.position, self.current_goal)
            self._pi = 0
        else:
            self.current_goal = None

    def move_towards_goal(self):
        if not self.current_goal:
            return

        # Chemin fini ?
        if self._pi >= len(self.path):
            self.current_goal = None
            self.path = []
            self._pi = 0
            return

        target = self.path[self._pi]
        dx = target[0] - self.position[0]
        dy = target[1] - self.position[1]
        dist = (dx*dx + dy*dy) ** 0.5

        # Si proche du waypoint, passer au suivant
        if dist < 5:
            self._pi += 1
            if self._pi < len(self.path):
                target = self.path[self._pi]
                self.move_to_position(target)
            else:
                self.current_goal = None
                self.path = []
                self._pi = 0
            return

        
        # Continuer vers le waypoint courant
        self.move_to_position(target)
                
     
    def get_base(self):
        # Renvoie la base ennemie
        for p in self.game.plateformes.values():
            if p.team != self.team:
                return p
        return None
    
    
    def cree_chemin(self, depart, goal, depth: int = 0, max_depth: int = 3):
        # Chemin direct avec contournement simple en cas d'obstacle
        if not depart or not goal or depart == goal:
            return []

        x0, y0 = depart
        x1, y1 = goal
        dx = x1 - x0
        dy = y1 - y0
        dist = (dx*dx + dy*dy) ** 0.5
        if dist == 0:
            return []

        # Paramètres
        step = 32            # pas d'échantillonnage (pixels)
        back_margin = 16     # reculer avant l'obstacle
        detour_distance = 192  # distance latérale de contournement

        dir_x = dx / dist
        dir_y = dy / dist
        perp_x = -dir_y
        perp_y = dir_x

        steps = max(1, int(dist // step))
        path = []
        hit_obstacle = None

        # Échantillonnage sur la ligne directe
        for i in range(1, steps + 1):
            t = i / steps
            px = x0 + dx * t
            py = y0 + dy * t
            if point_in_many_polygons(self.game.obstacles, (px, py)) or point_in_many_polygons(self.game.quantique_area_hidden, (px, py)):
                hit_obstacle = (px, py)
                break
            path.append((px, py))

        # Pas d’obstacle: chemin direct
        if not hit_obstacle:
            return path

        # Profondeur max atteinte: rendre ce qu'on a avant l'obstacle
        if depth >= max_depth:
            return path

        # Point pivot avant l’obstacle
        pivot_x = hit_obstacle[0] - dir_x * back_margin
        pivot_y = hit_obstacle[1] - dir_y * back_margin

        # Essayer gauche puis droite
        for sign in (+1, -1):
            detour_x = pivot_x + perp_x * detour_distance * sign
            detour_y = pivot_y + perp_y * detour_distance * sign

            # Le détour ne doit pas tomber dans un obstacle
            if point_in_many_polygons(self.game.obstacles, (detour_x, detour_y)) or point_in_many_polygons(self.game.quantique_area_hidden, (detour_x, detour_y)):
                continue

            # Construire depart->detour et detour->goal
            segment1 = self.cree_chemin(depart, (detour_x, detour_y), depth + 1, max_depth)
            if not segment1:
                continue
            segment2 = self.cree_chemin((detour_x, detour_y), goal, depth + 1, max_depth)
            if not segment2:
                continue

            return segment1 + segment2

        # Aucun détour trouvé: retourner la portion valide
        return path
        
        
            
       

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