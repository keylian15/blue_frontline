from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING

import pygame
from shapely.geometry import Point as ShapelyPoint
from shapely.geometry import Polygon
from src.config.units import UNIT_CONFIGS
from src.system.Combat import CombatSystem
from src.units.Unit import Unit

if TYPE_CHECKING:
    from src.core.Game import Game


class Bateau(Unit):
    """Classe unifiée pour les unités Bateau (Rouge et Vert)."""

    def __init__(self, game: Game, team: str, is_ia: bool = True):
        """Fonction d'initialisation de la classe Bateau.

        Args:
            game (Game): L'instance du jeu.
            team (str): L'équipe de l'unité.
            ia (bool): Si True, l'unité est contrôlée par l'IA.
        """

        # Récupérer la configuration depuis Global.py
        config = UNIT_CONFIGS["bateau"]

        # Initialiser avec l'image appropriée et le type d'unité
        super().__init__(game, team=team, unit_type="bateau")

        # === Spécifications du Bateau depuis Global.py ===
        self.cost = config["cost"]

        self.max_speed = config["max_speed"]
        self.reducte_speed = self.max_speed // 2
        self.speed = self.max_speed
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

        # === Pathfinding A* ===
        self.path_to_follow = []
        self.current_path_index = 0

        # Détection de blocage
        self._last_positions = []
        self._block_check_interval = 1.0
        self._last_block_check_time = time.time()

        # === Configuration IA ===
        self.is_ia = is_ia
        self.current_goal = None
        # "base_ennemie", "base_alliee", "attaque_ennemi", "suivre_eclaireur"
        self.current_goal_type = None

        self.enemie_base = self.IA_get_enemy_base()
        self.ally_base = self.IA_get_ally_base()

        # État de l'IA
        self.current_state = "chercher_but"

        # Éclaireur allié
        self._ally_scout = None
        self._scout_check_cooldown = 0
        self._scout_check_interval = 30

        # Ennemi actuel ciblé
        self._current_target = None

    def update(
        self,
        dt: int = 0,
        combat_system: CombatSystem = None,
        screen: pygame.Surface = None,
        camera_offset: tuple[float, float] = (0, 0),
        all_units: list[Unit] = None,
    ):
        """Met à jour l'unité en fonction de son état actuel.

        Args:
            dt (int, optional): Le delta time entre chaque frame. Par defaut à 0 .
            combat_system (CombatSystem, optional): Le système de combat pour gérer les attaques. Par defaut à None .
            screen (pygame.Surface, optional): La surface d'affichage pour dessiner la portée. Par defaut à None .
            camera_offset (tuple[float, float], optional): Le décalage de la caméra pour le rendu. Par defaut à (0, 0) .
            all_units (list[Unit], optional): La liste de toutes les unités dans le jeu. Par defaut à None .
        """
        # Appeler la mise à jour de la classe parent
        super().update(dt, combat_system, screen, camera_offset, all_units)

        # Dessiner la portée en permanence
        if screen:
            self.draw_range(screen, camera_offset)

        # Logique IA
        if self.is_ia and all_units:
            # Suivi du déplacement sur chemin A*
            if self.path_to_follow:
                if not self.is_moving:
                    self.current_path_index += 1
                    if self.current_path_index < len(self.path_to_follow):
                        self.move_to_position(self.path_to_follow[self.current_path_index])
                    else:
                        # Fin du chemin
                        self.path_to_follow = []
                        self.current_path_index = 0

            # Détection blocage avec recalcul automatique
            now = time.time()
            if now - self._last_block_check_time > self._block_check_interval:
                self._last_block_check_time = now
                self._last_positions.append(tuple(self.position))
                if len(self._last_positions) > 5:
                    self._last_positions.pop(0)
                if len(self._last_positions) == 5:
                    dist_moved = math.sqrt(
                        (self._last_positions[-1][0] - self._last_positions[0][0]) ** 2
                        + (self._last_positions[-1][1] - self._last_positions[0][1]) ** 2
                    )
                    if dist_moved < 5:
                        # Blocage détecté, retour au début du cycle
                        self.current_state = "chercher_but"
                        self.path_to_follow = []
                        self.current_path_index = 0

            self.IA_execute_logic(combat_system, all_units)

    # ========================================[LOGIQUE IA PRINCIPALE]=============================================

    def IA_execute_logic(self, combat_system: CombatSystem, all_units: list[Unit]):
        """Exécute la logique de l'IA selon le diagramme exact.

        Args:
            combat_system (CombatSystem): Le système de combat pour gérer les attaques.
            all_units (list[Unit]): La liste de toutes les unités dans le jeu.
        """

        # ÉTAPE 1: Chercher un ennemi proche
        enemy = self.get_closest_enemy_in_range()

        if enemy:
            # ENNEMI PROCHE = OUI
            self.current_state = "ennemi_proche"
            health_percentage = self.current_health / self.max_health

            if health_percentage > 0.5:
                # PV SUPÉRIEUR À 50% = OUI
                if self.IA_is_paquebot(enemy):
                    # PAQUEBOT = OUI -> BUT = fuite
                    self.current_state = "fuite"
                    self.current_goal_type = "base_alliee"
                    self.IA_flee_to_ally_base()
                else:
                    # PAQUEBOT = NON -> BUT = attaque ennemie
                    self.current_state = "attaquer"
                    self.current_goal_type = "attaque_ennemi"
                    self._current_target = enemy
            else:
                # PV SUPÉRIEUR À 50% = NON
                ally_scout = self.IA_find_ally_scout(all_units)

                if ally_scout:
                    # ÉCLAIREUR ALLIÉ = OUI -> BUT = suivre éclaireur allié
                    self.current_state = "suivre_eclaireur"
                    self.current_goal_type = "suivre_eclaireur"
                    self.IA_follow_scout(ally_scout)
                else:
                    # ÉCLAIREUR ALLIÉ = NON -> BUT = fuite (base alliée)
                    self.current_state = "fuite"
                    self.current_goal_type = "base_alliee"
                    self.IA_flee_to_ally_base()
        else:
            # ENNEMI PROCHE = NON
            self.current_state = "pas_ennemi"
            health_percentage = self.current_health / self.max_health

            if health_percentage > 0.5:
                # PV > 50% sans ennemi -> BUT = base ennemie
                self.current_state = "avancer"
                self.current_goal_type = "base_ennemie"
                self.IA_advance_to_enemy_base()
            else:
                # PV <= 50% sans ennemi -> vérifier éclaireur
                ally_scout = self.IA_find_ally_scout(all_units)

                if ally_scout:
                    # ÉCLAIREUR ALLIÉ = OUI
                    self.current_state = "suivre_eclaireur"
                    self.current_goal_type = "suivre_eclaireur"
                    self.IA_follow_scout(ally_scout)
                else:
                    # ÉCLAIREUR ALLIÉ = NON -> BUT = base alliée
                    self.current_state = "avancer"
                    self.current_goal_type = "base_alliee"
                    self.IA_flee_to_ally_base()

        # ÉTAPE 2: Gérer l'action selon l'état
        if self.current_state == "attaquer":
            # Logique spéciale pour l'attaque
            if self._current_target and self._current_target in all_units:
                self.IA_handle_attack_state(combat_system)
            else:
                # Cible perdue, retour à chercher un but
                self._current_target = None
                self.current_state = "chercher_but"

    def IA_handle_attack_state(self, combat_system: CombatSystem):
        """Gère l'état d'attaque: vérifier portée, tirer ou se rapprocher.

        Args:
            combat_system (CombatSystem): Le système de combat pour gérer les attaques.
        """

        if not self._current_target:
            return

        # Calculer la distance à la cible
        dx = self._current_target.position[0] - self.position[0]
        dy = self._current_target.position[1] - self.position[1]
        distance_to_enemy = (dx * dx + dy * dy) ** 0.5

        if distance_to_enemy <= self.range * 32:
            # À PORTÉE DE TIR = OUI -> Tirer
            self.attack(self._current_target, combat_system)
            # Arrêter le mouvement pour tirer
            self.is_moving = False
            self.path_to_follow = []
        else:
            # À PORTÉE DE TIR = NON -> Se rapprocher
            self.attack(self._current_target, combat_system)
            target_pos = tuple(self._current_target.position)
            # Mettre à jour le chemin vers la cible mobile
            if not self.path_to_follow or self.current_goal != target_pos:
                self.IA_calculate_path_to_goal(target_pos)

    # ========================================[COMPORTEMENTS IA (décisions)]=======================================

    def IA_find_ally_scout(self, all_units: list[Unit]):
        """Trouve l'éclaireur allié le plus proche (si disponible).

        Args:
            all_units (list[Unit]): La liste de toutes les unités dans le jeu.
        Returns:
            (Unit): L'unité éclaireur alliée la plus proche, ou None si aucun trouvé.
        """

        # Cooldown pour éviter de chercher trop souvent
        self._scout_check_cooldown -= 1
        if self._scout_check_cooldown > 0 and self._ally_scout:
            if self._ally_scout in all_units:
                return self._ally_scout

        self._scout_check_cooldown = self._scout_check_interval

        # Chercher un éclaireur allié
        closest_scout = None
        min_distance = float("inf")

        for unit in all_units:
            if unit.team == self.team and unit != self and hasattr(unit, "unit_type") and unit.unit_type == "eclaireur":
                dx = unit.position[0] - self.position[0]
                dy = unit.position[1] - self.position[1]
                distance = (dx * dx + dy * dy) ** 0.5

                if distance < min_distance:
                    min_distance = distance
                    closest_scout = unit

        self._ally_scout = closest_scout
        return closest_scout

    def IA_follow_scout(self, scout: Unit):
        """Suit un éclaireur allié en utilisant un système de pathfinding.

        Args:
            scout (Unit): L'unité éclaireur alliée à suivre.
        """
        if not scout or not hasattr(scout, "position"):
            return

        # Initialiser un timer de recalcul s’il n’existe pas
        if not hasattr(self, "_last_follow_update"):
            self._last_follow_update = 0

        # Recalcule au maximum toutes les 1.5 secondes
        now = time.time()
        if now - self._last_follow_update < 1.5:
            return

        scout_pos = tuple(scout.position)
        dx = scout_pos[0] - self.position[0]
        dy = scout_pos[1] - self.position[1]
        _distance_to_scout = math.sqrt(dx * dx + dy * dy)

        # Recalcule seulement si l’éclaireur s’est éloigné significativement
        if self.current_goal != scout_pos:
            self.IA_calculate_path_to_goal(scout_pos)
            self._last_follow_update = now

    def IA_flee_to_ally_base(self):
        """Déclenche une fuite vers la base alliée en calculant un chemin optimal.

        Utilise l'algorithme A* pour trouver le chemin le plus court vers la base alliée
        et s'y déplace automatiquement.
        """
        if self.ally_base:
            base_pos = tuple(self.ally_base.position)
            if self.current_goal != base_pos:
                self.IA_calculate_path_to_goal(base_pos)

    def IA_advance_to_enemy_base(self):
        """Avance vers la base ennemie en utilisant le pathfinding.

        Calcule et suit le chemin optimal pour atteindre la position de la base ennemie.
        """
        if self.enemie_base:
            base_pos = tuple(self.enemie_base.position)
            if self.current_goal != base_pos:
                self.IA_calculate_path_to_goal(base_pos)

    # ============================================[PATHFINDING (A*)]================================================

    def IA_calculate_path_to_goal(self, goal: tuple):
        """Suit un éclaireur allié en utilisant un système de pathfinding.

        Args:
            Goal (tuple): Position cible sous forme de tuple (x, y).
        """
        self.current_goal = goal
        path = self.IA_a_etoile(self.position, goal)

        if path:
            self.path_to_follow = path
            self.current_path_index = 0
            if self.path_to_follow:
                self.move_to_position(self.path_to_follow[0])
        else:
            # Pas de chemin trouvé, essayer déplacement direct
            self.move_to_position(goal)

    # PATHFINDING (A*)

    def IA_a_etoile(self, start, goal):
        """Implémente l'algorithme A* pour trouver le chemin le plus court.

        Args:
            start (tuple): Position de départ sous forme de tuple (x, y).
            goal (tuple): Position d'arrivée sous forme de tuple (x, y).

        Returns:
            (list): Liste des positions (x, y) formant le chemin du départ à l'arrivée.
                Retourne une liste vide si aucun chemin n'est trouvé.
        """

        def pos_to_grid(pos):
            return (int(pos[0] // 32), int(pos[1] // 32))

        def grid_to_pos(grid):
            return (grid[0] * 32 + 16, grid[1] * 32 + 16)

        start_grid = pos_to_grid(start)
        goal_grid = pos_to_grid(goal)

        # Préparer les zones d’eau peu profonde
        shallow_polygons = []
        if hasattr(self.game, "eau_peu_profondes"):
            for poly in self.game.eau_peu_profondes:
                shallow_polygons.append(Polygon([(p.x, p.y) for p in poly]))

        # Préparer les zones bloquantes (obstacles)
        obstacles = set()
        for poly in self.game.obstacles:
            min_x = min(p[0] for p in poly) // 32
            max_x = max(p[0] for p in poly) // 32
            min_y = min(p[1] for p in poly) // 32
            max_y = max(p[1] for p in poly) // 32
            for x in range(int(min_x), int(max_x) + 1):
                for y in range(int(min_y), int(max_y) + 1):
                    obstacles.add((x, y))

        # Zones cachées quantiques
        if hasattr(self.game, "quantique_area_hidden"):
            for poly in self.game.quantique_area_hidden:
                min_x = min(p[0] for p in poly) // 32
                max_x = max(p[0] for p in poly) // 32
                min_y = min(p[1] for p in poly) // 32
                max_y = max(p[1] for p in poly) // 32
                for x in range(int(min_x), int(max_x) + 1):
                    for y in range(int(min_y), int(max_y) + 1):
                        obstacles.add((x, y))

        # Directions de mouvement
        neighbors = [(0, 1), (1, 0), (0, -1), (-1, 0)]

        open_set = set([start_grid])
        came_from = {}
        g_score = {start_grid: 0}
        f_score = {start_grid: self.IA_heuristic(start_grid, goal_grid)}

        def is_in_shallow_water(grid):
            """Retourne True si la cellule se trouve dans une zone d’eau peu profonde.
            
            Args:
                grid (tuple): Coordonnées de la cellule (x, y)
            Returns:
                (bool): True si la cellule est dans une zone d’eau peu profonde, False sinon.
            """
            pos = grid_to_pos(grid)
            pt = ShapelyPoint(pos[0], pos[1])
            return any(poly.contains(pt) for poly in shallow_polygons)

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

                # Base cost = 1, shallow water adds penalty
                movement_cost = 1.0
                if is_in_shallow_water(neighbor):
                    movement_cost = 3.0  # Plus lent dans l’eau peu profonde

                tentative_g_score = g_score[current] + movement_cost

                if tentative_g_score < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.IA_heuristic(neighbor, goal_grid)
                    open_set.add(neighbor)

        return None

    def IA_heuristic(self, a: tuple, b: tuple) -> float:
        """Distance de Manhattan pour A*.

        Args :
            a (tuple): Position de départ sous forme de tuple (x, y).
            b (tuple): Position d'arrivée sous forme de tuple (x, y).
        Returns:
            (float): Distance heuristique entre a et b.
        """
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    # =============================================[UTILITAIRES IA]=================================================

    def IA_is_paquebot(self, unit: Unit) -> bool:
        """Vérifie si une unité est un paquebot.

        Args:
            unit (Unit): L'unité à vérifier.
        Returns:
            (bool): True si l'unité est un paquebot, False sinon.
        """
        return getattr(unit, "type", None) == "Paquebot" or getattr(unit, "unit_type", None) == "paquebot"

    def IA_get_enemy_base(self):
        """Renvoie la base ennemie.

        Returns:
            (Unit): La base ennemie.
        """
        for p in self.game.plateformes.values():
            if p.team != self.team:
                return p
        return

    def IA_get_ally_base(self):
        """Renvoie la base alliée.

        Returns:
            (Unit): La base alliée.
        """
        for p in self.game.plateformes.values():
            if p.team == self.team:
                return p
        return None


# Classes d'alias pour la compatibilité avec l'ancien code
class BateauRouge(Bateau):
    def __init__(self, game: Game, is_ia: bool = True):
        """Fonction d'initialisation de la classe BateauRouge."""
        super().__init__(game, team="red", is_ia=is_ia)


class BateauVert(Bateau):
    def __init__(self, game: Game, is_ia: bool = True):
        """Fonction d'initialisation de la classe BateauVert."""
        super().__init__(game, team="green", is_ia=is_ia)
