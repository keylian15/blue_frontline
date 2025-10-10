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
        self.enemie_base = self.get_base()
        # Etat de contournement pour éviter les oscillations gauche/droite
        self._detour_side = None  # +1 ou -1, None = non défini

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
        
        if self.ia:
            #trouver un but
            enemy = self.get_closest_enemy_in_range()
            if enemy:
                #print le type de l'enemie attaquer
                print(f"ATTACK: {self.type} -> {getattr(enemy, 'type', 'unknown')}")
                self.attack(enemy, combat_system)

            if self.current_goal is None and not enemy:
                self.find_goal()

            else:
                self.move_towards_goal()
                
                
        
        # if self.ia :
        #     if self.get_closest_enemy_in_range():
        #         self.attack(self.get_closest_enemy_in_range(), combat_system)

        #     if self.current_goal is None:
        #         self.find_goal()
        #     else:
        #         self.move_towards_goal()
        
        

    def find_goal(self):
        enemy = self.get_closest_enemy_in_range()
        if enemy:
            self.current_goal = enemy
        else:
                self.current_goal = tuple(self.enemie_base.position)
        self.path = self.create_path(self.position,self.current_goal)
        self._pi = 0
        
        # base_enemie = self.get_base()
        # if base_enemie:
        #     self.current_goal = tuple(base_enemie.position)
        #     self.path = self.cree_chemin(self.position, self.current_goal)
        #     self._pi = 0
        # else:
        #     self.current_goal = None

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
    
    def create_path(self, depart, goal, depth: int = 0, max_depth: int = 3):
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
        step = 16          
        back_margin = 32
        detour_distance = 64
        max_detour_distance = 512        
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

        # Déterminer l'ordre de préférence des côtés (pour éviter l'oscillation)
        preferred_sides = (+1, -1) if self._detour_side is None else (self._detour_side, -self._detour_side)

        # Essayer le côté préféré en augmentant progressivement la distance de contournement
        for sign in preferred_sides:
            current_detour = detour_distance
            while current_detour <= max_detour_distance:
                detour_x = pivot_x + perp_x * current_detour * sign
                detour_y = pivot_y + perp_y * current_detour * sign

                # Le détour ne doit pas tomber dans un obstacle
                if point_in_many_polygons(self.game.obstacles, (detour_x, detour_y)) or point_in_many_polygons(self.game.quantique_area_hidden, (detour_x, detour_y)):
                    current_detour *= 1.5
                    continue

                # Vérifier que le segment depart -> détour est "suffisamment" dégagé
                seg_dx = detour_x - depart[0]
                seg_dy = detour_y - depart[1]
                seg_dist = (seg_dx*seg_dx + seg_dy*seg_dy) ** 0.5
                seg_steps = max(1, int(seg_dist // step))
                blocked = False
                for j in range(1, seg_steps + 1):
                    tj = j / seg_steps
                    sx = depart[0] + seg_dx * tj
                    sy = depart[1] + seg_dy * tj
                    if point_in_many_polygons(self.game.obstacles, (sx, sy)) or point_in_many_polygons(self.game.quantique_area_hidden, (sx, sy)):
                        blocked = True
                        break
                if blocked:
                    current_detour *= 1.5
                    continue

                # Construire depart->detour et detour->goal avec préférence du même côté
                self._detour_side = sign
                segment1 = self.create_path(depart, (detour_x, detour_y), depth + 1, max_depth)
                if not segment1:
                    current_detour *= 1.5
                    continue
                segment2 = self.create_path((detour_x, detour_y), goal, depth + 1, max_depth)
                if not segment2:
                    current_detour *= 1.5
                    continue

                return segment1 + segment2

        # Aucun détour viable: réinitialiser l'état de contournement pour réessayer plus tard
        self._detour_side = None

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