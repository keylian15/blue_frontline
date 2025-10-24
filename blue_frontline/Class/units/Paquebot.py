import threading
import time
import math
import pygame
from Class.units.Unit import Unit
from Class.Combat import CombatSystem
from Global import UNIT_CONFIGS


class Paquebot(Unit):
    def __init__(self, game: "Game", team: str, is_ia: bool = True):
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

        # Variables pathfinding
        self.is_moving = False
        self.target_position = None
        self.path_to_follow = []
        self.current_path_index = 0

        # Pour détection blocage
        self._last_positions = []
        self._block_check_interval = 1.0
        self._last_block_check_time = time.time()

        # Gestion prise en main manuelle (désactive IA)
        self.manual_override = False

        # Mode d'exécution IA : tick depuis update() (pas de thread IA par unité)
        self.ia_enabled = is_ia
        self._last_ia_tick = time.time()
        self._ia_tick_interval = 0.15  # cadence IA en secondes

    def update(self, dt=0, combat_system=None, screen=None, camera_offset=(0, 0), all_units=None):
        """Met à jour l'état du paquebot.

        Args:
            dt (int, optional): Delta temps. Defaults to 0.
            combat_system (CombatSystem, optional): Système de combat. Defaults to None.
            screen (Surface, optional): Écran. Defaults to None.
            camera_offset (tuple, optional): Offset caméra. Defaults to (0, 0).
            all_units (list, optional): Liste des unités. Defaults to None.
        """
        super().update(dt, combat_system, screen, camera_offset, all_units)

        # Récupération base ennemie et sa position
        target_pos, target_base = self.pos_base_ennemie()
        
        if target_pos and target_base:
            # Calcul distance vers base
            dx = target_pos[0] - self.position[0]
            dy = target_pos[1] - self.position[1]
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Si à portée de tir, on s'arrête et on attaque
            if distance <= self.range * 32:  # range est en tuiles, conversion en pixels
                self.stop()
                self.is_moving = False
                self.path_to_follow = []
                self.current_path_index = 0
                
                # On définit la base comme cible pour l'attaque
                self.target = target_base
                return
    
        # Suivi du chemin pathfinding dans le thread
        if self.path_thread and self.path_thread.is_alive():
            # Le thread calcule encore, on attend
            pass
        else:
            # Si nouveau chemin calculé, on le charge
            if self.path_found:
                self.path_to_follow = self.new_path
                self.current_path_index = 0
                if self.path_to_follow:
                    self.move_to_position(self.path_to_follow[0])
                self.path_found = False

        # Suivi du déplacement sur chemin
        if self.path_to_follow and not self.manual_override:
            if not self.is_moving:
                self.current_path_index += 1
                if self.current_path_index < len(self.path_to_follow):
                    self.move_to_position(self.path_to_follow[self.current_path_index])
                else:
                    self.path_to_follow = []
                    self.current_path_index = 0

        # Reprise après déplacement manuel
        if self.manual_override and not self.is_moving:
            self.manual_override = False
            self.calcul_chemin()

        # Détection blocage simple
        now = time.time()
        if now - self._last_block_check_time > self._block_check_interval:
            self._last_block_check_time = now
            self._last_positions.append(self.position)
            if len(self._last_positions) > 5:
                self._last_positions.pop(0)
            if len(self._last_positions) == 5:
                dist_moved = math.sqrt(
                    (self._last_positions[-1][0] - self._last_positions[0][0]) ** 2 +
                    (self._last_positions[-1][1] - self._last_positions[0][1]) ** 2
                )
                if dist_moved < 5:
                    # Blocage détecté, recalculer chemin dans un thread
                    if not self.need_recalculate_path:
                        self.need_recalculate_path = True
                        self.start_pathfinding_thread(self.compute_path)

        # Tick IA non-bloquant (exécuté depuis la boucle principale)
        if self.ia_enabled:
            now_ia = time.time()
            if now_ia - self._last_ia_tick >= self._ia_tick_interval:
                self._last_ia_tick = now_ia
                self.ia_decision(all_units)
        if screen:
            self.draw_range(screen, camera_offset)

        # Si la cible est une unité ennemie et qu'elle est à portée, tirer via le combat_system
        # Vérifie que target est bien une unité (possède team/position) et est vivante
        target = getattr(self, "target", None)
        if target and hasattr(target, "position") and hasattr(target, "team") and getattr(target, "is_alive", True):
            # s'assurer qu'il s'agit d'un ennemi
            if target.team != self.team:
                try:
                    if self.is_in_range(target) and self.can_attack():
                        # Utilise le combat_system si fourni, sinon appel direct
                        if combat_system is not None:
                            self.attack(target, combat_system)
                        else:
                            self.attack(target)
                except Exception:
                    # silence sur erreurs d'attaque pour ne pas casser la boucle de jeu
                    pass

    def pos_base_ennemie(self):
        """Retourne la position de la base ennemie et l'objet base.

        Returns:
            tuple: (position (x,y), base) ou (None, None) si pas de base trouvée
        """
        if self.team == "red":
            return (self.game.plateformes["green"].position, self.game.plateformes["green"])
        elif self.team == "green":
            return (self.game.plateformes["red"].position, self.game.plateformes["red"])
        return None, None

    def aller_vers_base_ennemie(self):
        """Déplacement direct vers la base ennemie sans pathfinding."""
        target_pos, _ = self.pos_base_ennemie()
        if target_pos:
            self.move_to_position(target_pos)

    def calcul_chemin(self):
        """Démarre le calcul du chemin vers la base ennemie dans un thread."""
        if self.path_thread and self.path_thread.is_alive():
            return  # Un calcul est déjà en cours
        self.need_recalculate_path = False
        # Utilise la méthode de la classe parente
        self.start_pathfinding_thread(self.compute_path)

    def compute_path(self):
        """Calcule le chemin vers la base ennemie."""
        start = self.position
        target_pos, _ = self.pos_base_ennemie() # On ne récupère que la position
        if not start or not target_pos:
            return

        path = self.ia_a_star_search(start, target_pos)
        if path:
            self.new_path = path
            self.path_found = True

    def ia_a_star_search(self, start, goal):
        """Implémentation A* sur grille 32x32 pixels.

        Args:
            start (tuple): (x, y) position départ
            goal (tuple): (x, y) position but

        Returns:
            list de (x,y): chemin en pixels (centre des tuiles) ou None
        """
        def pos_to_grid(pos):
            return (int(pos[0] // 32), int(pos[1] // 32))

        def grid_to_pos(grid):
            return (grid[0] * 32 + 16, grid[1] * 32 + 16)

        start_grid = pos_to_grid(start)
        goal_grid = pos_to_grid(goal)

        obstacles = set()
        for poly in self.game.obstacles:
            min_x = min(p[0] for p in poly) // 32
            max_x = max(p[0] for p in poly) // 32
            min_y = min(p[1] for p in poly) // 32
            max_y = max(p[1] for p in poly) // 32
            for x in range(int(min_x), int(max_x)+1):
                for y in range(int(min_y), int(max_y)+1):
                    obstacles.add((x, y))

        neighbors = [(0, 1), (1, 0), (0, -1), (-1, 0)]

        open_set = set([start_grid])
        came_from = {}

        g_score = {start_grid: 0}
        f_score = {start_grid: self.heuristic(start_grid, goal_grid)}

        while open_set:
            current = min(open_set, key=lambda x: f_score.get(x, float('inf')))
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
                tentative_g_score = g_score[current] + 1
                if tentative_g_score < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal_grid)
                    open_set.add(neighbor)

        return None

    def heuristic(self, a, b):
        """Distance de Manhattan."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    # def recalculate_path(self):
    #     """Signale qu'il faut recalculer le chemin."""
    #     if not self.need_recalculate_path:
    #         self.need_recalculate_path = True
    #         self.start_pathfinding_thread()

    def ia_decision(self, all_units=None):
        """Décisions IA non bloquantes avec optimisation multithreading."""
        # Si prise en main manuelle, laisser l'utilisateur agir
        if getattr(self, "manual_override", False):
            return

        # Si besoin de recalculer chemin (blocage)
        if getattr(self, "need_recalculate_path", False):
            self.calcul_chemin()
            return

        # Vérification directe des ennemis à portée sans thread
        if getattr(self, "enemies_in_range", None):
            closest = self.get_closest_enemy_in_range()
            if closest:
                self.target = closest
                self.stop()
                return

        # Récupération des données nécessaires
        units = all_units if all_units is not None else getattr(self.game, "units", [])
        allied_base_obj = self.game.plateformes.get(self.team)
        allied_pos = getattr(allied_base_obj, "position", None) if allied_base_obj else None
        enemy_pos, _ = self.pos_base_ennemie()

        # Défense de la base
        if allied_pos:
            defend_radius = 6 * 32
            for u in units:
                if (getattr(u, "team", None) and u.team != self.team 
                    and getattr(u, "is_alive", True)):
                    u_pos = getattr(u, "position", (0, 0))
                    d = math.hypot(u_pos[0] - allied_pos[0], 
                                 u_pos[1] - allied_pos[1])
                    if d <= defend_radius:
                        self.target = u
                        if not (self.path_thread and self.path_thread.is_alive()):
                            self.start_pathfinding_thread(lambda: self.compute_path())
                        return

        # Si aucune action défensive n'est nécessaire, aller vers la base ennemie
        if enemy_pos and not self.path_to_follow and not (self.path_thread and self.path_thread.is_alive()):
            self.calcul_chemin()

# Alias pour compatibilité
class PaquebotRouge(Paquebot):
    def __init__(self, game):
        super().__init__(game, team="red")


class PaquebotVert(Paquebot):
    def __init__(self, game):
        super().__init__(game, team="green")
