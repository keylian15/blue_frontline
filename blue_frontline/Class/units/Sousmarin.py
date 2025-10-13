import time
import pygame
import heapq
from Class.units.Unit import Unit
from Class.Combat import CombatSystem, Mine
from math import * 
from Global import UNIT_CONFIGS
from Utils import point_in_many_polygons, random_point_in_polygon

class SousMarin(Unit):

    """Classe unifiée pour les unités Sous-marin (Rouge et Vert)."""
    
    def __init__(self, game, team: str):
        """Initialise une instance de SousMarin.

        Args:
            game: Instance du jeu.
            team (str): Équipe de l'unité.
        """
        # Récupérer la configuration depuis Global.py
        config = UNIT_CONFIGS["sousmarin"]
        
        # Initialiser avec l'image appropriée et le type d'unité
        super().__init__(game, team=team, unit_type="sousmarin")
        
        # === Spécifications du Sous-marin depuis Global.py ===
        self.cost = config["cost"]
        
        self.max_speed = config["max_speed"]
        self.reducte_speed = self.max_speed // 2
        self.speed = self.max_speed # Par défaut speed = speed max
        self.max_health = config["max_health"]
        self.current_health = self.max_health
        self.range = 0  # Les sous-marins ne tirent pas
        self.damage = 0
        self.fire_rate = 0
        
        # Type d'unité et capacité spéciale
        self.unit_type = config["unit_type"]
        self.unit_name = f"Sous-marin {team.capitalize()}"
        self.special_ability = config.get("special_ability", None)
        
        # Couleur de portée selon l'équipe
        self.range_color = config["range_color"][team]
        
        # État de mouvement
        self.is_moving = False
        self.target_position = None
        
        # Variables pour l'IA A*
        self.current_path = []
        self.path_index = 0
        self.recalculate_path = True
        self.enemy_base_position = None
        
            
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

        self.ia_action(all_units)

    def can_place_mine(self):
        """Vérifie si le sous-marin peut poser une mine (cooldown respecté, mais fire_rate ignoré)."""
        current_time = time.time()
        time_since_last_shot = current_time - self.last_shot_time
        multiplica = self.game.hud.timer.get_speed_multiplier() if hasattr(self.game, 'hud') and hasattr(self.game.hud, 'timer') else 1
        # Cooldown d'une seconde par défaut
        return time_since_last_shot >= (1.0 / multiplica)
    
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
                self.last_shot_time = time.time()
            # -- AUDIO : drop mine --
            try:
                if hasattr(self.game, "sound") and self.game.sound:
                    self.game.sound.on_mine_dropped((x, y))
            except Exception:
                # ne jamais crasher pour du son
                pass
            return True
        return False
    
    def get_enemy_base_position(self):
        """Récupère la position de la base ennemie."""
        if self.enemy_base_position is None:
            if self.team == "red":
                # Base ennemie = base verte
                base_zone = self.game.green_platform_zone
            else:
                # Base ennemie = base rouge  
                base_zone = self.game.red_platform_zone
                
            if base_zone:
                # Prendre le centre approximatif de la zone de la base
                self.enemy_base_position = random_point_in_polygon(base_zone)
        
        return self.enemy_base_position
    
    def world_to_grid(self, x, y):
        """Convertit les coordonnées monde en coordonnées grille."""
        grid_x = int(x // 32)  # 32 pixels par case
        grid_y = int(y // 32)
        return grid_x, grid_y
    
    def grid_to_world(self, grid_x, grid_y):
        """Convertit les coordonnées grille en coordonnées monde."""
        world_x = grid_x * 32 + 16  # Centre de la case
        world_y = grid_y * 32 + 16
        return world_x, world_y
    
    def is_position_valid(self, x, y):
        """Vérifie si une position est valide (pas dans un obstacle)."""
        world_pos = (x, y)
        
        # Vérifier si la position est dans les limites de la carte avec une marge
        margin = 50  # Marge de sécurité pour éviter les bords
        if x < margin or y < margin or x >= (self.game.map_width - margin) or y >= (self.game.map_height - margin):
            return False
        
        # Vérifier si la position est dans un obstacle (île) avec une zone de sécurité
        if hasattr(self.game, 'obstacles') and self.game.obstacles:
            if point_in_many_polygons(self.game.obstacles, world_pos):
                return False
                
        # Vérifier les zones quantiques cachées (obstacles pour le sous-marin)
        if hasattr(self.game, 'quantique_area_hidden') and self.game.quantique_area_hidden:
            if point_in_many_polygons(self.game.quantique_area_hidden, world_pos):
                return False
        
        # Vérifier s'il y a une autre unité à cette position
        if self.game.find_unit_at_position(x, y, self):
            return False
            
        return True
    
    def heuristic(self, pos1, pos2):
        """Calcule la distance de Manhattan entre deux positions."""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def get_neighbors(self, pos):
        """Retourne les voisins valides d'une position."""
        x, y = pos
        neighbors = []
        
        # Utiliser une grille plus fine (16 pixels au lieu de 32)
        step_size = 16
        
        # 8 directions (incluant les diagonales)
        directions = [
            (0, 1), (1, 0), (0, -1), (-1, 0),  # orthogonales
            (1, 1), (1, -1), (-1, 1), (-1, -1)  # diagonales
        ]
        
        for dx, dy in directions:
            new_x, new_y = x + dx * step_size, y + dy * step_size
            
            # Vérifier plusieurs points le long du trajet pour détecter les collisions
            valid = True
            steps = max(abs(dx), abs(dy))
            if steps > 0:
                for i in range(1, steps + 1):
                    check_x = x + (dx * step_size * i) // steps
                    check_y = y + (dy * step_size * i) // steps
                    if not self.is_position_valid(check_x, check_y):
                        valid = False
                        break
            
            if valid and self.is_position_valid(new_x, new_y):
                neighbors.append((new_x, new_y))
                
        return neighbors
    
    def astar(self, start, goal):
        """Implémente l'algorithme A* pour trouver le chemin optimal."""
        # Convertir en coordonnées monde si nécessaire
        start = (int(start[0]), int(start[1]))
        goal = (int(goal[0]), int(goal[1]))
        
        # Aligner sur la grille pour éviter les problèmes de précision
        start = (start[0] - start[0] % 16, start[1] - start[1] % 16)
        goal = (goal[0] - goal[0] % 16, goal[1] - goal[1] % 16)
        
        # Vérifier que le point de départ et d'arrivée sont valides
        if not self.is_position_valid(start[0], start[1]):
            # Trouver le point valide le plus proche du départ
            for radius in range(16, 100, 16):
                for angle in range(0, 360, 45):
                    test_x = start[0] + radius * cos(radians(angle))
                    test_y = start[1] + radius * sin(radians(angle))
                    if self.is_position_valid(test_x, test_y):
                        start = (int(test_x), int(test_y))
                        break
                if self.is_position_valid(start[0], start[1]):
                    break
        
        # Structures de données pour A*
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}
        closed_set = set()
        
        max_iterations = 1000  # Limite pour éviter les boucles infinies
        iterations = 0
        
        while open_set and iterations < max_iterations:
            iterations += 1
            current = heapq.heappop(open_set)[1]
            
            if current in closed_set:
                continue
                
            closed_set.add(current)
            
            # Vérifier si nous avons atteint le but avec une tolérance plus grande
            distance_to_goal = sqrt((current[0] - goal[0])**2 + (current[1] - goal[1])**2)
            if distance_to_goal < 80:  # Proche du but (5 cases)
                # Reconstruire le chemin
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                
                # Lisser le chemin pour éviter les zigzags
                return self.smooth_path(path)
            
            # Explorer les voisins
            for neighbor in self.get_neighbors(current):
                if neighbor in closed_set:
                    continue
                
                # Calculer le coût du mouvement (distance euclidienne réelle)
                dx = neighbor[0] - current[0]
                dy = neighbor[1] - current[1]
                move_cost = int(sqrt(dx*dx + dy*dy))
                
                tentative_g_score = g_score[current] + move_cost
                
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal)
                    
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        # Aucun chemin trouvé, essayer un chemin direct simplifié
        return self.fallback_path(start, goal)
    
    def smooth_path(self, path):
        """Lisse le chemin pour éviter les zigzags."""
        if len(path) <= 2:
            return path
        
        smoothed = [path[0]]  # Commencer par le premier point
        
        i = 0
        while i < len(path) - 1:
            current = smoothed[-1]
            
            # Chercher le point le plus lointain accessible directement
            furthest = i + 1
            for j in range(i + 2, len(path)):
                if self.can_move_directly(current, path[j]):
                    furthest = j
                else:
                    break
            
            smoothed.append(path[furthest])
            i = furthest
        
        return smoothed
    
    def can_move_directly(self, start, end):
        """Vérifie si on peut aller directement d'un point A à un point B."""
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        distance = sqrt(dx*dx + dy*dy)
        
        if distance == 0:
            return True
        
        # Vérifier plusieurs points le long de la ligne
        steps = max(1, int(distance / 8))  # Un point tous les 8 pixels
        for i in range(1, steps + 1):
            t = i / steps
            check_x = start[0] + t * dx
            check_y = start[1] + t * dy
            
            if not self.is_position_valid(check_x, check_y):
                return False
        
        return True
    
    def fallback_path(self, start, goal):
        """Crée un chemin de secours simple en cas d'échec de A*."""
        # Essayer un chemin en L (horizontal puis vertical)
        mid_point = (goal[0], start[1])
        
        if (self.can_move_directly(start, mid_point) and 
            self.can_move_directly(mid_point, goal)):
            return [start, mid_point, goal]
        
        # Essayer l'autre direction (vertical puis horizontal)
        mid_point = (start[0], goal[1])
        
        if (self.can_move_directly(start, mid_point) and 
            self.can_move_directly(mid_point, goal)):
            return [start, mid_point, goal]
        
        # En dernier recours, retourner le chemin direct
        return [start, goal]
    
    def follow_path(self, dt):
        """Suit le chemin calculé par A*."""
        if not self.current_path or self.path_index >= len(self.current_path):
            self.is_moving = False
            return
        
        target = self.current_path[self.path_index]
        
        # Calculer la distance au point cible actuel
        dx = target[0] - self.position[0]
        dy = target[1] - self.position[1]
        distance = sqrt(dx*dx + dy*dy)
        
        # Si nous sommes assez proches du point, passer au suivant
        if distance < 20:  # Distance plus généreuse
            self.path_index += 1
            if self.path_index >= len(self.current_path):
                self.is_moving = False
                self.target_position = None
                return
            target = self.current_path[self.path_index]
            dx = target[0] - self.position[0]
            dy = target[1] - self.position[1]
            distance = sqrt(dx*dx + dy*dy)
        
        # Vérifier si le prochain mouvement va nous faire rentrer dans un mur
        next_x = self.position[0] + self.speed_x * dt / 1000.0
        next_y = self.position[1] + self.speed_y * dt / 1000.0
        
        if not self.is_position_valid(next_x, next_y):
            # Obstacle détecté, recalculer le chemin
            self.recalculate_path = True
            self.is_moving = False
            return
        
        # Se déplacer vers le point cible
        if distance > 0:
            self.target_position = target
            self.move_to(target[0], target[1])
            self.is_moving = True
    
    def ia_action(self, all_units):
        """IA du sous-marin utilisant A* pour aller à la base adverse."""
        # Obtenir la position de la base ennemie
        enemy_base = self.get_enemy_base_position()
        if not enemy_base:
            return
        
        # Vérifier si on est arrivé à destination
        distance_to_goal = sqrt((self.position[0] - enemy_base[0])**2 + (self.position[1] - enemy_base[1])**2)
        if distance_to_goal < 100:  # Proche de la base ennemie
            self.is_moving = False
            self.current_path = []
            # Poser une mine près de la base ennemie
            if self.can_place_mine():
                self.place_mine(int(self.position[0]), int(self.position[1]))
            return
        
        # Recalculer le chemin si nécessaire ou périodiquement
        should_recalculate = (
            self.recalculate_path or 
            not self.current_path or 
            not self.is_moving or
            (hasattr(self, 'last_path_calc_time') and 
             time.time() - self.last_path_calc_time > 5.0)  # Recalculer toutes les 5 secondes
        )
        
        if should_recalculate:
            print(f"Sous-marin {self.team}: Recalcul du chemin depuis {self.position} vers {enemy_base}")
            self.current_path = self.astar(self.position, enemy_base)
            self.path_index = 0
            self.recalculate_path = False
            self.last_path_calc_time = time.time()
            
            if self.current_path:
                print(f"Nouveau chemin trouvé avec {len(self.current_path)} points")
                self.is_moving = True
            else:
                print("Aucun chemin trouvé, déplacement direct")
                # Aucun chemin trouvé, essayer un déplacement direct
                if self.can_move_directly(self.position, enemy_base):
                    self.target_position = enemy_base
                    self.move_to(enemy_base[0], enemy_base[1])
                    self.is_moving = True
                else:
                    # Essayer de contourner l'obstacle le plus proche
                    self.try_avoid_obstacle(enemy_base)
        
        # Suivre le chemin
        if self.current_path and self.is_moving:
            self.follow_path(1)
        
        # Poser des mines pendant le trajet si possible
        if self.can_place_mine():
            self.place_mine(int(self.position[0]), int(self.position[1]))
    
    def try_avoid_obstacle(self, goal):
        """Essaie de contourner un obstacle en se dirigeant vers un point intermédiaire."""
        # Essayer différents angles pour contourner l'obstacle
        angles = [45, -45, 90, -90, 135, -135]
        distance = 100  # Distance du point intermédiaire
        
        for angle in angles:
            # Calculer un point intermédiaire
            rad = radians(angle)
            intermediate_x = self.position[0] + distance * cos(rad)
            intermediate_y = self.position[1] + distance * sin(rad)
            
            # Vérifier si ce point est valide et si on peut l'atteindre
            if (self.is_position_valid(intermediate_x, intermediate_y) and
                self.can_move_directly(self.position, (intermediate_x, intermediate_y))):
                
                print(f"Point intermédiaire trouvé à {angle}°: ({intermediate_x}, {intermediate_y})")
                self.target_position = (intermediate_x, intermediate_y)
                self.move_to(intermediate_x, intermediate_y)
                self.is_moving = True
                
                # Marquer pour recalculer le chemin une fois le point intermédiaire atteint
                self.recalculate_path = True
                return
        
        print("Aucun point d'évitement trouvé, sous-marin bloqué")

# Classes d'alias pour la compatibilité avec l'ancien code
class SousMarinRouge(SousMarin):
    def __init__(self, game):
        """Constructeur de SousMarinRouge.

        Args:
            game: L'instance de la classe Game.
        """
        super().__init__(game, team="red")

class SousMarinVert(SousMarin):
    def __init__(self, game):
        """Constructeur de SousMarinVert.

        Args:
            game: L'instance de la classe Game.
        """
        super().__init__(game, team="green")
