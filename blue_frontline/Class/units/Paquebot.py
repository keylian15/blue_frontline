import threading
import time
import math
import pygame
from Class.units.Unit import Unit
from Class.Combat import CombatSystem
from Global import UNIT_CONFIGS


class Paquebot(Unit):
    """Classe unifiée pour les unités Paquebot (Rouge et Vert)."""
    def __init__(self, game: "Game", team: str, is_ia: bool = True):
        """Fonction d'initialisation de la classe Paquebot.

        Args:
            game (Game): L'instance du jeu.
            team (str): L'équipe de l'unité.
            is_ia (bool): Si True, l'unité est contrôlée par l'IA.
        """
        
        config = UNIT_CONFIGS["paquebot"]
        super().__init__(game, team=team, unit_type="paquebot")

        self.cost = config["cost"]
        self.max_speed = config["max_speed"]
        self.reducte_speed = self.max_speed // 2
        self.speed = self.max_speed
        self.max_health = config["max_health"]
        self.current_health = self.max_health
        self.range = config["range"]
        self.damage = config["damage"]
        self.fire_rate = config["fire_rate"]
        self.unit_type = config["unit_type"]
        self.unit_name = f"Paquebot {team.capitalize()}"
        self.range_color = config["range_color"][team]

        # Variables pathfinding / mouvement
        self.is_moving = False
        self.target_position = None
        self.path_to_follow = []
        self.current_path_index = 0

        # Détection blocage
        self._last_positions = []
        self._block_check_interval = 1.0
        self._last_block_check_time = time.time()

        # Prise en main manuelle (désactive IA)
        self.manual_override = False

        # Tick IA
        self.is_ia = is_ia        
        self._last_ia_tick = time.time()
        self._ia_tick_interval = 0.15

        # Mode défense
        self.in_defense_mode = False
        self.last_defense_time = 0
        self.defense_cooldown = 4  # secondes

    def update(self, dt=0, combat_system=None, screen=None, camera_offset=(0, 0), all_units=None):
        """Mise à jour de l'unité Paquebot.

        Args:
            dt (int, optional): La différence de temps entre chaque frame. Par défaut à 0.
            combat_system (CombatSystem, optional): Le système de combat. Par défaut à None.
            screen (pygame.Surface, optional): L'écran sur lequel afficher. Par défaut à None.
            camera_offset (tuple[float, float], optional): Le décalage de la caméra. Par défaut à (0, 0).
            all_units (list[Unit], optional): La liste de toutes les unités dans le jeu. Par défaut à None.
        """
        super().update(dt, combat_system, screen, camera_offset, all_units)

        # Chargement du chemin calculé par le thread (si présent)
        if not (self.path_thread and self.path_thread.is_alive()):
            if getattr(self, "path_found", False):
                self.path_to_follow = self.new_path
                self.current_path_index = 0
                if self.path_to_follow:
                    self.move_to_position(self.path_to_follow[0])
                self.path_found = False

        # Suivi du chemin
        if self.path_to_follow and not self.manual_override:
            if not self.is_moving:
                self.current_path_index += 1
                if self.current_path_index < len(self.path_to_follow):
                    self.move_to_position(self.path_to_follow[self.current_path_index])
                else:
                    self.path_to_follow = []
                    self.current_path_index = 0

        # Tick IA
        if self.is_ia:
            now_ia = time.time()
            if now_ia - self._last_ia_tick >= self._ia_tick_interval:
                self._last_ia_tick = now_ia
                self.ia_decision(all_units)

        # Attaque actuelle si possible
        target = getattr(self, "target", None)
        if target and hasattr(target, "position") and hasattr(target, "team") and getattr(target, "is_alive", True):
            if target.team != self.team:
                try:
                    if self.is_in_range(target) and self.can_attack():
                        if combat_system is not None:
                            self.attack(target, combat_system)
                        else:
                            self.attack(target)
                except Exception:
                    pass

        if screen:
            self.draw_range(screen, camera_offset)

    def pos_base_ennemie(self):
        """Retourne la position de la base ennemie.

        Returns:
            tuple: La position de la base ennemie et l'objet de la plateforme.
        """
        if self.team == "red":
            return (self.game.plateformes["green"].position, self.game.plateformes["green"])
        elif self.team == "green":
            return (self.game.plateformes["red"].position, self.game.plateformes["red"])
        return None, None

    def calcul_chemin(self):
        """Lance le calcul du chemin vers la base ennemie dans un thread séparé."""
        if getattr(self, "path_thread", None) and self.path_thread.is_alive():
            return
        self.need_recalculate_path = False
        self.start_pathfinding_thread(self.compute_path)

    def compute_path(self):
        """Calcule le chemin vers la base ennemie."""
        start = self.position
        target_pos, _ = self.pos_base_ennemie()
        if not start or not target_pos:
            return
        path = self.ia_a_star_search(start, target_pos)
        if path:
            self.new_path = path
            self.path_found = True

    def compute_path_to(self, target_pos):
        """Calcule le chemin vers une position cible donnée.
        Args:
            target_pos (tuple): La position cible (x, y).
        """
        start = self.position
        if not start or not target_pos:
            return
        path = self.ia_a_star_search(start, target_pos)
        if path:
            self.new_path = path
            self.path_found = True

    def ia_a_star_search(self, start, goal):
        """Implémentation A* améliorée sur grille 32x32 pixels avec mouvements diagonaux.
        Args:
            start (tuple): (x, y) position départ
            goal (tuple): (x, y) position but

        Returns:
            list: Liste de positions (x, y) formant le chemin, ou None si pas de chemin.
        """
        def pos_to_grid(pos):
            """Convertit une position en coordonnées de grille.
            
            Args:
                pos (tuple): Position (x, y) en pixels.
            
            Returns:
                tuple: Coordonnées de la grille (x, y).
            """
            return (int(pos[0] // 32), int(pos[1] // 32))

        def grid_to_pos(grid):
            """Convertit des coordonnées de grille en position.
            
            Args:
                grid (tuple): Coordonnées de la grille (x, y).
            
            Returns:
                tuple: Position (x, y) en pixels.
            """
            return (grid[0] * 32 + 16, grid[1] * 32 + 16)

        start_grid = pos_to_grid(start)
        goal_grid = pos_to_grid(goal)

        obstacles = set()
        # Obstacles physiques existants
        for poly in getattr(self.game, "obstacles", []):
            min_x = min(p[0] for p in poly) // 32
            max_x = max(p[0] for p in poly) // 32
            min_y = min(p[1] for p in poly) // 32
            max_y = max(p[1] for p in poly) // 32
            for x in range(int(min_x), int(max_x) + 1):
                for y in range(int(min_y), int(max_y) + 1):
                    obstacles.add((x, y))
            
        # Zones quantiques cachées actuelles
        if hasattr(self.game, 'quantique_area'):
            for poly in self.game.quantique_area:
                min_x = min(p[0] for p in poly) // 32
                max_x = max(p[0] for p in poly) // 32
                min_y = min(p[1] for p in poly) // 32
                max_y = max(p[1] for p in poly) // 32
                for x in range(int(min_x), int(max_x) + 1):
                    for y in range(int(min_y), int(max_y) + 1):
                        obstacles.add((x, y))

        neighbors = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]

        open_set = set([start_grid])
        came_from = {}

        g_score = {start_grid: 0}
        f_score = {start_grid: self.heuristic(start_grid, goal_grid)}

        while open_set:
            current = min(open_set, key=lambda x: f_score.get(x, float("inf")))
            if current == goal_grid:
                path = []
                while current in came_from:
                    path.append(grid_to_pos(current))
                    current = came_from[current]
                path.append(grid_to_pos(start_grid))
                path.reverse()
                return path

            open_set.remove(current)
            for dx, dy in neighbors:
                neighbor = (current[0] + dx, current[1] + dy)
                if neighbor in obstacles:
                    continue
                movement_cost = 1.4 if dx != 0 and dy != 0 else 1
                tentative_g_score = g_score[current] + movement_cost
                if tentative_g_score < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal_grid)
                    open_set.add(neighbor)

        return None


    def heuristic(self, a, b):
        """Heuristique de distance de Manhattan pour A*.
        
        Args:
            a (tuple): Position (x, y) 1.
            b (tuple): Position (x, y) 2.

        Returns:
            (float): Distance de Manhattan entre a et b.
        """
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def ia_decision(self, all_units=None):
        """IA agressive : attaque d'abord les ennemis proches, sinon comportement classique.
        Args:
            all_units (list, optional): Liste de toutes les unités dans le jeu. Par défaut à None.
        """
        if getattr(self, "manual_override", False):
            return

        units = all_units if all_units is not None else getattr(self.game, "units", [])
        enemies = [u for u in units if getattr(u, "team", None) != self.team and getattr(u, "is_alive", True)]

        # --- 1. PRIORITÉ : si un ennemi est à portée, attaquer ---
        closest_enemy = None
        closest_dist = float("inf")

        for enemy in enemies:
            dist = math.hypot(enemy.position[0] - self.position[0], enemy.position[1] - self.position[1])
            if dist < closest_dist:
                closest_enemy = enemy
                closest_dist = dist

        # Si un ennemi est dans la portée
        if closest_enemy and closest_dist <= self.range * 32:
            self.stop()
            self.target = closest_enemy
            return  # on ne bouge pas, on tire

        # --- 2. Si une cible précédente existe et qu’elle n’est pas morte, on la poursuit ---
        if getattr(self, "target", None) and getattr(self.target, "is_alive", False):
            target = self.target
            dist = math.hypot(target.position[0] - self.position[0], target.position[1] - self.position[1])
            if dist > self.range * 32:
                # Elle est hors de portée : on la suit
                if not (self.path_thread and self.path_thread.is_alive()):
                    self.start_pathfinding_thread(lambda: self.compute_path_to(target.position))
            return

        # --- 3. Si pas d’ennemi à proximité, comportement normal (attaque ou défense) ---
        self.ia_defense_ou_attaque(units)

    def ia_defense_ou_attaque(self, units):
        """Décide entre défendre la base alliée ou attaquer la base ennemie.
        
        Args:
            units (list): Liste de toutes les unités dans le jeu.
        """
        allied_base_obj = self.game.plateformes.get(self.team)
        allied_pos = getattr(allied_base_obj, "position", None) if allied_base_obj else None
        enemy_pos, _ = self.pos_base_ennemie()

        # Défense de la base
        if allied_pos:
            defend_radius = 6 * 32
            for u in units:
                if (getattr(u, "team", None) and u.team != self.team and getattr(u, "is_alive", True)):
                    u_pos = getattr(u, "position", (0, 0))
                    d_enemy_to_base = math.hypot(u_pos[0] - allied_pos[0], u_pos[1] - allied_pos[1])
                    d_self_to_base = math.hypot(self.position[0] - allied_pos[0], self.position[1] - allied_pos[1])

                    if d_enemy_to_base <= defend_radius:
                        self.in_defense_mode = True
                        self.last_defense_time = time.time()

                        if d_enemy_to_base < d_self_to_base + 8:
                            self.path_to_follow = []
                            self.current_path_index = 0
                            self.stop()
                            if not (self.path_thread and self.path_thread.is_alive()):
                                self.start_pathfinding_thread(lambda: self.compute_path_to(allied_pos))
                            return
                        else:
                            self.target = u
                            if not (self.path_thread and self.path_thread.is_alive()):
                                self.start_pathfinding_thread(lambda: self.compute_path_to(u_pos))
                            return

        if self.in_defense_mode:
            if time.time() - self.last_defense_time < self.defense_cooldown:
                return
            else:
                self.in_defense_mode = False

        # Par défaut : aller vers la base ennemie
        if enemy_pos and not self.path_to_follow and not (self.path_thread and self.path_thread.is_alive()):
            self.calcul_chemin()


class PaquebotRouge(Paquebot):
    def __init__(self, game, is_ia: bool = True):
        super().__init__(game, team="red", is_ia=is_ia)


class PaquebotVert(Paquebot):
    def __init__(self, game, is_ia: bool = True):
        super().__init__(game, team="green", is_ia=is_ia)
