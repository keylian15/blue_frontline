from __future__ import annotations

"""
IA_Eclaireur.py — Contrôleur IA de l'Éclaireur.

Comportement:
- choisir une zone quantique cachée à explorer
- essayer d'y aller avec A* local
- si A* échoue: soit aller direct vers la zone si elle est déjà pas trop loin,
  soit PATROUILLER
- patrouille = mouvement directionnel persistant :
    * le bateau garde un heading (direction)
    * avance tout droit
    * si bloqué -> on tourne un peu et on repart
    * dès qu'une zone cachée devient assez proche -> on quitte la patrouille
      et on tente d'y aller

Convention :
- toute IA a is_ia = True
- appel public = ia_tick()
"""

import csv
import heapq
import logging
import math
import random
import time
from dataclasses import dataclass
from typing import (Callable, Dict, Iterable, List, Optional, Sequence, Tuple,
                    Union)

# ---------------------------------------------------------------------------
# LOGGER
# ---------------------------------------------------------------------------
LOGGER_NAME = "EclaireurAI"
logger = logging.getLogger(LOGGER_NAME)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(name)s: %(message)s",
    )

Vec2 = Tuple[float, float]
Cell = Tuple[int, int]


# ---------------------------------------------------------------------------
# Shapely optionnel
# ---------------------------------------------------------------------------
try:
    from shapely.geometry import Polygon  # type: ignore
except Exception:
    class Polygon:  # type: ignore
        """fallback Polygon minimal pour tests"""

        def __init__(self, points: Sequence[Vec2]):
            self._points = list(points)

        @property
        def centroid(self):
            sx = sum(p[0] for p in self._points)
            sy = sum(p[1] for p in self._points)
            n = len(self._points)

            class _C:
                def __init__(self, x, y):
                    self.x = x
                    self.y = y

            return _C(sx / n, sy / n)


# ---------------------------------------------------------------------------
# File de priorité pour A*
# ---------------------------------------------------------------------------
class _PriorityQueue:
    def __init__(self) -> None:
        self._pq: List[Tuple[float, int, Cell]] = []
        self._tiebreak: int = 0

    def push(self, priority: float, item: Cell) -> None:
        self._tiebreak += 1
        heapq.heappush(self._pq, (priority, self._tiebreak, item))

    def pop(self) -> Cell:
        return heapq.heappop(self._pq)[2]

    def __bool__(self) -> bool:
        return bool(self._pq)


def octile(a: Cell, b: Cell) -> float:
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    return (dx + dy) + (math.sqrt(2.0) - 2.0) * min(dx, dy)


class AStar:
    """
    A* classique sur grille 8 directions.
    On met une limite d'expansions pour ne pas freeze le jeu.
    """

    def __init__(
        self,
        is_walkable: Callable[[Cell], bool],
        cost: Callable[[Cell], float],
        neighbors: Callable[[Cell], Iterable[Cell]],
        heuristic: Callable[[Cell, Cell], float] = octile,
    ) -> None:
        self.is_walkable = is_walkable
        self.cost = cost
        self.neighbors = neighbors
        self.heuristic = heuristic

    def find_path(
        self,
        start: Cell,
        goal: Cell,
        max_expansions: int = 1000,
    ) -> List[Cell]:
        if not self.is_walkable(start) or not self.is_walkable(goal):
            return []

        frontier = _PriorityQueue()
        frontier.push(0.0, start)

        came_from: Dict[Cell, Optional[Cell]] = {start: None}
        g_cost: Dict[Cell, float] = {start: 0.0}

        expansions = 0

        while frontier:
            current = frontier.pop()
            if current == goal:
                break

            expansions += 1
            if expansions > max_expansions:
                logger.warning(
                    "A*: expansions max atteintes (%d). Abandon.",
                    max_expansions,
                )
                return []

            for nxt in self.neighbors(current):
                if not self.is_walkable(nxt):
                    continue

                new_cost = g_cost[current] + max(1.0, float(self.cost(nxt)))
                if nxt not in g_cost or new_cost < g_cost[nxt]:
                    g_cost[nxt] = new_cost
                    priority = new_cost + self.heuristic(nxt, goal)
                    frontier.push(priority, nxt)
                    came_from[nxt] = current

        if goal not in came_from:
            return []

        # reconstruction du chemin
        path: List[Cell] = []
        cur: Optional[Cell] = goal
        while cur is not None:
            path.append(cur)
            cur = came_from[cur]
        path.reverse()
        return path


# ---------------------------------------------------------------------------
# Grille / adapter
# ---------------------------------------------------------------------------
@dataclass
class GridAdapter:
    cell_size: int
    world_to_cell: Callable[[Vec2], Cell]
    cell_to_world: Callable[[Cell], Vec2]
    is_walkable: Callable[[Cell], bool]
    cost: Callable[[Cell], float]
    neighbors: Callable[[Cell], Iterable[Cell]]


class SimpleGrid:
    """
    Grille rectangulaire walkable + coûts.
    neighbors8 empêche de traverser un coin bloqué en diagonale.
    """

    def __init__(self, width: int, height: int, cell_size: int = 32) -> None:
        self.width = int(width)
        self.height = int(height)
        self.cell_size = int(cell_size)

        self.walkable: List[List[bool]] = [
            [True for _ in range(self.height)] for _ in range(self.width)
        ]
        self.costs: List[List[float]] = [
            [1.0 for _ in range(self.height)] for _ in range(self.width)
        ]

    def in_bounds(self, c: Cell) -> bool:
        x, y = c
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, c: Cell) -> bool:
        x, y = c
        return self.in_bounds(c) and self.walkable[x][y]

    def cost(self, c: Cell) -> float:
        x, y = c
        if not self.in_bounds(c):
            return float("inf")
        return self.costs[x][y]

    def neighbors8(self, c: Cell) -> Iterable[Cell]:
        x, y = c
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue

                nc = (x + dx, y + dy)
                if not self.in_bounds(nc):
                    continue

                # anti "corner cut"
                if dx != 0 and dy != 0:
                    if not (
                        self.is_walkable((x + dx, y))
                        and self.is_walkable((x, y + dy))
                    ):
                        continue

                yield nc

    def world_to_cell(self, p: Vec2) -> Cell:
        x, y = p
        return int(x // self.cell_size), int(y // self.cell_size)

    def cell_to_world(self, c: Cell) -> Vec2:
        cx, cy = c
        return (
            cx * self.cell_size + self.cell_size * 0.5,
            cy * self.cell_size + self.cell_size * 0.5,
        )


def make_grid_adapter_from_simplegrid(grid: SimpleGrid) -> GridAdapter:
    return GridAdapter(
        cell_size=grid.cell_size,
        world_to_cell=grid.world_to_cell,
        cell_to_world=grid.cell_to_world,
        is_walkable=grid.is_walkable,
        cost=grid.cost,
        neighbors=grid.neighbors8,
    )


# ---------------------------------------------------------------------------
# IA du Scout
# ---------------------------------------------------------------------------
class ScoutAI:
    """
    IA d'éclaireur.
    """

    is_ia: bool = True  # convention

    def __init__(
        self,
        unit: object,
        grid: GridAdapter,
        get_hidden_quantum_polygons: Callable[[], Sequence[object]],
        get_base_pos: Callable[[str], Vec2],
        return_to_base_when_done: bool = False,   # <= on force à rester en patrouille
        replan_interval: float = 1.0,
        proximity_epsilon: float = 8.0,
        world_width_px: float = 4096.0,
        world_height_px: float = 4096.0,
    ) -> None:
        self.unit = unit
        self.grid = grid
        self.get_hidden_quantum_polygons = get_hidden_quantum_polygons
        self.get_base_pos = get_base_pos
        self.return_to_base_when_done = return_to_base_when_done
        self.replan_interval = replan_interval
        self.proximity_epsilon = proximity_epsilon

        # bornes monde pour clamp
        self.world_w = float(world_width_px)
        self.world_h = float(world_height_px)

        self.astar = AStar(
            grid.is_walkable,
            grid.cost,
            grid.neighbors,
        )

        # Liste de waypoints monde [(x,y), ...] à suivre
        self._path_world: List[Vec2] = []

        # Objectif courant monde (but stratégique)
        self.current_goal_world: Optional[Vec2] = None

        # Timer replanif
        self._accum: float = 0.0

        # debug throttle
        self._last_debug_tick: float = 0.0

        # --- PATROUILLE DIRECTIONNELLE ---
        # direction persistante (dx,dy) normalisée environ, ou None si pas en patrouille
        self._wander_dir: Optional[Vec2] = None

        # distance "devant" pour poser un waypoint de patrouille
        self._wander_step_dist: float = 600.0  # pixels

        # anti-blocage
        self._last_pos_for_block: Vec2 = self.unit.position
        self._block_timer: float = 0.0
        self._BLOCK_THRESHOLD_SEC = 1.0
        self._BLOCK_MIN_MOVE = 5.0  # si on bouge < 5 px on considère pas de progrès

        # petit timer pour éviter "je viens de poser un WP et je dis déjà que je suis arrivé"
        self._just_assigned_wp_timer: float = 0.0
        # petit timer pour éviter "je viens de poser un WP et je dis déjà que je suis arrivé"
        self._just_assigned_wp_timer: float = 0.0

        # Simplified policy: we do NOT run heavy diagnostics here.
        # The scout will only attempt to access hidden zones in time windows
        # of 3 minutes ON / 3 minutes OFF. See `_zones_open_now()`.
        self.enabled: bool = True

    # ------------------------------------------------------------------
    # Méthodes publiques appelées par le moteur
    # ------------------------------------------------------------------
    def ia_tick(self, dt: float) -> None:
        if not self.enabled:
            return

        # timers internes
        self._accum += dt
        self._block_timer += dt
        if self._just_assigned_wp_timer > 0.0:
            self._just_assigned_wp_timer = max(0.0, self._just_assigned_wp_timer - dt)

        # avancer vers le WP courant
        self._follow_waypoints(dt)

        # replan régulier ou si on n'a plus de chemin
        need_plan = (self._accum >= self.replan_interval) or (not self._path_world)
        if need_plan:
            self._accum = 0.0
            self._ensure_objective_and_path()

        # debug log toutes les ~2s
        self._last_debug_tick += dt
        if self._last_debug_tick >= 2.0:
            self._last_debug_tick = 0.0
            logger.debug(
                "ScoutAI DEBUG TICK: pos=%s goal=%s path_len=%d wander_dir=%s",
                self.unit.position,
                self.current_goal_world,
                len(self._path_world),
                self._wander_dir,
            )
        # (No periodic diagnostic or teleport detection here in the simplified
        # version — keep the tick loop light and deterministic.)

    def ia_set_enabled(self, value: bool) -> None:
        self.enabled = bool(value)
        if not self.enabled:
            self._clear_path()
            self.unit.stop()

    # ------------------------------------------------------------------
    # PLANIF / OBJECTIF
    # ------------------------------------------------------------------
    def _ensure_objective_and_path(self) -> None:
        """
        Choisit une cible (zone cachée la plus proche, sinon on CONTINUE LA PATROUILLE)
        Puis essaie A*. Si A* échoue :
           - si la cible est proche -> on va tout droit
           - sinon -> patrouille
        """

        hidden = self.get_hidden_quantum_polygons()

        # Pré-calculer les centroïdes pour éviter plusieurs calculs
        centroid_list: List[Vec2] = []
        if hidden:
            logger.info("ScoutAI DEBUG: %d zones cachées reçues par l'IA", len(hidden))
            for i, poly in enumerate(hidden):
                c = self._compute_centroid_from_polygon_like(poly)
                if c:
                    centroid_list.append(c)
                    logger.info("  -> zone[%d] centroïde vu=(%.1f, %.1f)", i, c[0], c[1])

        # cible = zone cachée la plus proche (parmi les centroïdes valides)
        target: Optional[Vec2] = None
        if centroid_list:
            target = self._pick_best_hidden_zone(centroid_list)

        # S'il n'y a plus de zones cachées:
        # ancien comportement = rentrer à la base.
        # maintenant : NON, on reste en patrouille.
        if target is None:
            logger.info("ScoutAI: aucune zone cachée -> rester en patrouille.")
            self.current_goal_world = None
            # si on est déjà en patrouille, juste s'assurer qu'on a un WP
            if self._wander_dir is None:
                # lance patrouille si pas déjà dedans
                self._enter_or_update_patrol()
            else:
                # si pas de WP actif -> régénère
                if not self._path_world:
                    self._enter_or_update_patrol()
            return

        self.current_goal_world = target
        # If zones are currently closed by schedule, don't attempt pathing;
        # fallback to patrol but keep current_goal_world so we can retry later
        if not self._zones_open_now():
            logger.info(
                "ScoutAI: zones fermées par schedule (3min ON/OFF) -> éviter d'essayer d'y aller maintenant.")
            self._enter_or_update_patrol()
            return

        # tenter de planifier un chemin local (A*)
        got_path = self._plan_local_path_to(target)
        if got_path:
            # on quitte le mode patrouille libre
            self._wander_dir = None
            return

        # pas de chemin A* -> considérer la cible comme inacessible pour l'instant.
        # Ne pas forcer l'unité à y aller directement : on passe en patrouille,
        # mais on conserve `current_goal_world` pour pouvoir réessayer plus tard
        # quand la grille aura changé ou que la cible deviendra atteignable.
        logger.warning(
            "ScoutAI: aucun chemin local vers (%.1f, %.1f) -> zone temporairement inaccessible, patrouille (réessaiera).",
            target[0], target[1],
        )
        # enter patrol mode (keeps current_goal_world so future replans will retry)
        self._enter_or_update_patrol()
        return

    def _compute_centroid_from_polygon_like(self, poly: object) -> Optional[Vec2]:
        c = getattr(poly, "centroid", None)
        if c is not None and hasattr(c, "x") and hasattr(c, "y"):
            try:
                return (float(c.x), float(c.y))
            except Exception:
                pass

        if isinstance(poly, (list, tuple)) and len(poly) > 0:
            try:
                sx = 0.0
                sy = 0.0
                n = 0
                for pt in poly:
                    if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                        sx += float(pt[0])
                        sy += float(pt[1])
                        n += 1
                if n > 0:
                    return (sx / n, sy / n)
            except Exception:
                pass

        return None

    def _zones_open_now(self) -> bool:
        """
        Détermine si les zones quantiques sont "ouvertes" selon une fenêtre
        temporelle périodique : 3 minutes OPEN / 3 minutes CLOSED.

        On lit l'horloge de jeu via `self.unit.game_time` si disponible.
        La règle choisie : accessible quand floor(game_time / 180) % 2 == 1
        (donc accessibles sur [180..360), [540..720), ... ).
        """
        ts = getattr(self.unit, 'game_time', None)
        if ts is None:
            # si on ne connaît pas le temps de jeu, on considère fermé
            return False
        try:
            window = int(math.floor(float(ts) / 180.0))
            return (window % 2) == 1
        except Exception:
            return False

    def _pick_best_hidden_zone(self, hidden: Sequence[object]) -> Optional[Vec2]:
        """
        Choisit la zone la plus proche.

        `hidden` peut être une séquence d'objets polygonaux (tuples/objets) ou
        une séquence déjà transformée de centroïdes (tuples (x,y)). La méthode
        gère les deux cas pour éviter des recomputations inutiles.
        """

        ux, uy = self.unit.position
        best_goal: Optional[Vec2] = None
        best_d2: float = float("inf")

        for item in hidden:
            # si l'item est déjà une coordonnée (centroid pré-calculé)
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                try:
                    tx = float(item[0])
                    ty = float(item[1])
                    goal = (tx, ty)
                except Exception:
                    goal = None
            else:
                goal = self._compute_centroid_from_polygon_like(item)

            if goal is None:
                continue

            tx, ty = goal
            d2 = (tx - ux) ** 2 + (ty - uy) ** 2
            if d2 < best_d2:
                best_d2 = d2
                best_goal = (tx, ty)

        if best_goal is None:
            return None

        logger.info(
            "ScoutAI DEBUG: meilleure zone choisie = (%.1f, %.1f) dist=%.1f px",
            best_goal[0],
            best_goal[1],
            math.sqrt(best_d2),
        )
        return best_goal

    def _report_accessible_hidden_zones(self) -> None:
        """
        Diagnostic: pour chaque zone cachée, teste si l'éclaireur peut l'atteindre
        via A* (avec une limite d'expansions raisonnable). Logge le résultat et
        appelle le callback si défini.
        """
        # Diagnostic removed in simplified build: keep method as no-op to
        # preserve compatibility if external code calls it.
        return

    # ------------------------------------------------------------------
    # PATHFIND LOCAL
    # ------------------------------------------------------------------
    def _plan_local_path_to(self, world_goal: Vec2) -> bool:
        start_cell = self.grid.world_to_cell(self.unit.position)
        goal_cell = self.grid.world_to_cell(world_goal)

        # tentative directe
        path_cells = self.astar.find_path(start_cell, goal_cell, max_expansions=1000)

        # sinon chercher une cellule atteignable proche du but
        if not path_cells:
            alt_cell = self._find_reachable_cell_near(start_cell, goal_cell)
            if alt_cell is not None:
                path_cells = self.astar.find_path(
                    start_cell,
                    alt_cell,
                    max_expansions=1000,
                )

        if not path_cells:
            logger.warning(
                "ScoutAI: aucun chemin local vers %s -> échec A*.",
                world_goal,
            )
            return False
        # (Simplified) accept the found path immediately.

        # convertit en points monde
        self._path_world = [self.grid.cell_to_world(c) for c in path_cells]

        if self._path_world:
            logger.info(
                "ScoutAI: chemin LOCAL planifié (%d steps), 1er WP=(%.1f, %.1f)",
                len(self._path_world),
                self._path_world[0][0],
                self._path_world[0][1],
            )

        # on n'est plus en patrouille aveugle
        self._wander_dir = None

        # pousser le mouvement
        self._just_assigned_wp_timer = 0.5
        self._push_move_order_if_any()
        return True

    def _find_reachable_cell_near(
        self,
        start_cell: Cell,
        goal_cell: Cell,
        search_radius_cells: int = 6,
    ) -> Optional[Cell]:
        gx, gy = goal_cell

        # Collecte des cellules candidate walkable autour du goal
        candidates: List[Cell] = []
        for dx in range(-search_radius_cells, search_radius_cells + 1):
            for dy in range(-search_radius_cells, search_radius_cells + 1):
                cand = (gx + dx, gy + dy)
                if not self.grid.is_walkable(cand):
                    continue
                candidates.append(cand)

        if not candidates:
            logger.warning(
                "ScoutAI: _find_reachable_cell_near abandon (aucune cellule candidate walkable)",
            )
            return None

        # Si le start est déjà une candidate -> OK
        if start_cell in candidates:
            return start_cell

        # Run a single A*-like search from start and accept any of the candidate cells
        frontier = _PriorityQueue()
        frontier.push(0.0, start_cell)

        came_from: Dict[Cell, Optional[Cell]] = {start_cell: None}
        g_cost: Dict[Cell, float] = {start_cell: 0.0}

        expansions = 0
        max_expansions = max(500, (search_radius_cells * search_radius_cells) * 10)

        # For heuristic we use the original goal_cell as proxy (cheaper than min over candidates)
        while frontier:
            current = frontier.pop()
            if current in candidates:
                # found reachable candidate
                return current

            expansions += 1
            if expansions > max_expansions:
                logger.warning(
                    "A* multi-goal: expansions max atteintes (%d). Abandon.",
                    max_expansions,
                )
                return None

            for nxt in self.grid.neighbors(current):
                if not self.grid.is_walkable(nxt):
                    continue

                new_cost = g_cost[current] + max(1.0, float(self.grid.cost(nxt)))
                if nxt not in g_cost or new_cost < g_cost[nxt]:
                    g_cost[nxt] = new_cost
                    priority = new_cost + octile(nxt, goal_cell)
                    frontier.push(priority, nxt)
                    came_from[nxt] = current

        logger.warning(
            "ScoutAI: _find_reachable_cell_near abandon (aucune cellule atteignable proche)"
        )
        return None

    # ------------------------------------------------------------------
    # PATROUILLE DIRECTIONNELLE
    # ------------------------------------------------------------------
    def _enter_or_update_patrol(self) -> None:
        """
        Active / met à jour le mode patrouille.
        - si pas encore de direction => on choisit une direction random
        - on génère 1 waypoint devant nous dans cette direction
        """
        if self._wander_dir is None:
            self._wander_dir = self._pick_new_wander_dir()
            logger.info(
                "ScoutAI: patrouille activée. direction=(%.2f, %.2f)",
                self._wander_dir[0],
                self._wander_dir[1],
            )

        wp = self._make_forward_waypoint(self._wander_dir)
        self._path_world = [wp]
        self._just_assigned_wp_timer = 0.5
        logger.info(
            "ScoutAI: patrouille -> WP=(%.1f, %.1f) (1 step).",
            wp[0],
            wp[1],
        )
        self._push_move_order_if_any()

    def _pick_new_wander_dir(self) -> Vec2:
        ang = random.uniform(0.0, math.tau)
        return (math.cos(ang), math.sin(ang))

    def _rotate_wander_dir(self, cur: Vec2, max_angle_deg: float = 70.0) -> Vec2:
        (dx, dy) = cur
        base_ang = math.atan2(dy, dx)
        delta = math.radians(random.uniform(-max_angle_deg, max_angle_deg))
        new_ang = base_ang + delta
        return (math.cos(new_ang), math.sin(new_ang))

    def _make_forward_waypoint(self, direction: Vec2) -> Vec2:
        """
        Génère un WP devant nous le long de `direction`,
        clampé dans la carte, et en essayant de garder une cellule walkable.
        """

        ux, uy = self.unit.position
        dx, dy = direction

        # normalise
        n = math.hypot(dx, dy)
        if n < 1e-5:
            dx, dy = 1.0, 0.0
            n = 1.0
        dx /= n
        dy /= n

        max_dist = self._wander_step_dist

        def clamp_to_map(xf: float, yf: float) -> Tuple[float, float]:
            cx = min(max(xf, 0.0), self.world_w - 1.0)
            cy = min(max(yf, 0.0), self.world_h - 1.0)
            return (cx, cy)

        # distances qu'on essaye devant nous
        for frac in (1.0, 0.7, 0.4, 0.2):
            trial_x = ux + dx * (max_dist * frac)
            trial_y = uy + dy * (max_dist * frac)

            trial_x, trial_y = clamp_to_map(trial_x, trial_y)

            cell = self.grid.world_to_cell((trial_x, trial_y))
            if self.grid.is_walkable(cell):
                return (trial_x, trial_y)

        # fallback : rester sur place
        return (ux, uy)

    def _try_make_safe_patrol_wp(self, direction: Vec2) -> Optional[Vec2]:
        """
        Cherche un bon waypoint d'esquive après blocage.
        """

        ux, uy = self.unit.position
        dx, dy = direction

        # normalise
        n = math.hypot(dx, dy)
        if n < 1e-5:
            return None
        dx /= n
        dy /= n

        def clamp_to_map(xx: float, yy: float) -> Tuple[float, float]:
            cx = min(max(xx, 0.0), self.world_w - 1.0)
            cy = min(max(yy, 0.0), self.world_h - 1.0)
            return (cx, cy)

        # on teste plusieurs distances "courtes" pour contourner l'obstacle
        for dist_try in (200.0, 350.0, 500.0):
            tx = ux + dx * dist_try
            ty = uy + dy * dist_try
            tx, ty = clamp_to_map(tx, ty)

            # éviter les points trop proches
            if (tx - ux) ** 2 + (ty - uy) ** 2 < (50.0 ** 2):
                continue

            cell = self.grid.world_to_cell((tx, ty))
            if self.grid.is_walkable(cell):
                return (tx, ty)

        return None

    def _reorient_patrol_after_block(self) -> None:
        """
        Quand on est bloqué en patrouille :
        - on tourne la direction
        - on tente un waypoint safe
        """

        if self._wander_dir is None:
            # si pour une raison quelconque on n'a pas de direction -> relance patrouille
            self._enter_or_update_patrol()
            return

        # Essai 1 : petite rotation
        for angle_deg in (70.0, 140.0, 210.0, 300.0):
            new_dir = self._rotate_wander_dir(self._wander_dir, max_angle_deg=angle_deg)
            wp = self._try_make_safe_patrol_wp(new_dir)
            if wp is not None:
                self._wander_dir = new_dir
                self._path_world = [wp]
                self._just_assigned_wp_timer = 0.5
                logger.info(
                    "ScoutAI: blocage -> nouvelle dir=(%.2f, %.2f), nouveau WP=(%.1f, %.1f)",
                    self._wander_dir[0],
                    self._wander_dir[1],
                    wp[0],
                    wp[1],
                )
                return

        # si rien trouvé -> au moins rester dans la carte
        wp_fallback = self._make_forward_waypoint(self._wander_dir)
        self._path_world = [wp_fallback]
        self._just_assigned_wp_timer = 0.5
        logger.info(
            "ScoutAI: blocage -> fallback patrouille WP=(%.1f, %.1f)",
            wp_fallback[0],
            wp_fallback[1],
        )

    # ------------------------------------------------------------------
    # SUIVI DES WAYPOINTS / ANTI-BLOCAGE
    # ------------------------------------------------------------------
    def _follow_waypoints(self, dt: float) -> None:
        if not self._path_world:
            return

        wx, wy = self._path_world[0]
        ux, uy = self.unit.position

        # 1) check arrivée (sauf juste après avoir posé le point)
        if self._just_assigned_wp_timer <= 0.0:
            dist_sq = (ux - wx) ** 2 + (uy - wy) ** 2
            if dist_sq <= (self.proximity_epsilon ** 2):
                self._path_world.pop(0)
                self._after_waypoint_reached()
                return

        # 2) pousser ordre de mouvement
        self._push_move_order_if_any()

        # 3) détection de blocage
        moved_dist = math.hypot(
            ux - self._last_pos_for_block[0],
            uy - self._last_pos_for_block[1],
        )
        has_progress = moved_dist > self._BLOCK_MIN_MOVE

        close_but_not_entering = (
            (ux - wx) ** 2 + (uy - wy) ** 2 < (64.0 ** 2)
            and not has_progress
        )

        time_blocked_enough = (self._block_timer >= self._BLOCK_THRESHOLD_SEC)

        if has_progress:
            # reset blocage
            self._last_pos_for_block = (ux, uy)
            self._block_timer = 0.0
            return

        # pas de progrès -> on accumule le blocage
        self._block_timer += dt

        if not time_blocked_enough and not close_but_not_entering:
            return  # pas encore déclaré bloqué

        # BLOQUÉ
        logger.warning(
            "ScoutAI: unité bloquée sur WP (%.1f, %.1f) depuis %.2fs -> réorientation.",
            wx,
            wy,
            self._block_timer,
        )

        # retire le WP actuel
        if self._path_world:
            self._path_world.pop(0)

        # reset blocage
        self._last_pos_for_block = (ux, uy)
        self._block_timer = 0.0

        # si on est en mode patrouille : on pivote pour contourner
        if self._wander_dir is not None:
            self._reorient_patrol_after_block()
        else:
            # sinon juste stop temporairement
            self.unit.stop()

        # pousse move sur le nouveau WP si dispo
        self._push_move_order_if_any()

    def _after_waypoint_reached(self) -> None:
        ux, uy = self.unit.position

        # reset blocage pour le prochain segment
        self._last_pos_for_block = (ux, uy)
        self._block_timer = 0.0

        if self._path_world:
            # encore des WPs (genre chemin A*)
            self._push_move_order_if_any()
            return

        # plus de WPs
        if self._wander_dir is not None:
            # on continue de patrouiller : génère un nouveau point droit devant
            wp = self._make_forward_waypoint(self._wander_dir)
            self._path_world = [wp]
            self._just_assigned_wp_timer = 0.5
            logger.debug(
                "ScoutAI: patrouille continue -> nouveau WP=(%.1f, %.1f)",
                wp[0],
                wp[1],
            )
            self._push_move_order_if_any()
        else:
            self.unit.stop()

    def _push_move_order_if_any(self) -> None:
        if not self._path_world:
            self.unit.stop()
            return

        wx, wy = self._path_world[0]

        cur_target = getattr(self.unit, "target_position", None)
        if cur_target is not None:
            dx = cur_target[0] - wx
            dy = cur_target[1] - wy
            if (dx * dx + dy * dy) < 16.0:  # ~4px²
                return

        # Simplified: don't run short A* safety check here; issue move order
        # directly. Keep a defensive try/except to avoid crashing if the
        # underlying unit API misbehaves.
        try:
            self.unit.move_to_position((wx, wy))
            logger.debug(
                "ScoutAI DEBUG MOVE ORDER -> (%.1f, %.1f)",
                wx,
                wy,
            )
        except Exception:
            logger.exception("ScoutAI: erreur en envoyant l'ordre de mouvement")

    def _clear_path(self) -> None:
        self._path_world = []
        self.unit.stop()

# =====================================================================
# RUNTIME GLOBAL POUR LES ECLAIREURS
# =====================================================================
def _rebuild_nav_if_needed(game: "Game") -> None:
    """
    Met à jour les obstacles + nav_grid SEULEMENT si nécessaire
    (ex: changement de marée).

    On fait ça ici (dans l'IA éclaireur) pour éviter de toucher
    au moteur global et de casser les autres unités.
    """
    hud = getattr(game, "hud", None)
    if hud is None or not hasattr(hud, "timer"):
        return

    timer = hud.timer

    # si rien n'a changé, on ne touche à rien
    if not getattr(timer, "maree_changed", False):
        return

    # sinon on met à jour les obstacles et la grille de nav
    if hasattr(game, "setObstacles"):
        game.setObstacles()

    if hasattr(game, "build_nav_grid"):
        game.build_nav_grid()

    # très important : reset pour ne pas rebuild chaque frame
    timer.maree_changed = False


def update_all_scout_ai(game, dt: float):
    """
    Met à jour toutes les IA d'éclaireurs du jeu pour cette frame.

    - Rebuild la nav_grid si la marée a changé (donc obstacles changent)
    - Appelle ia_tick(dt) UNIQUEMENT pour les unités qui sont des éclaireurs
      et qui utilisent ScoutAI.

    Args:
        game: instance de Game
        dt (float): delta time
    """

    # 1. mettre à jour la grille nav si besoin
    _rebuild_nav_if_needed(game)

    # 2. mettre à jour SEULEMENT les éclaireurs
    for unit in list(game.units):
        # ignorer les unités mortes
        if not getattr(unit, "is_alive", True):
            continue

        # on veut seulement nos éclaireurs
        if getattr(unit, "type", None) != "eclaireur":
            continue

        ai_controller = getattr(unit, "ai", None)
        if ai_controller is None:
            continue

        # l'IA doit respecter la convention d'équipe :
        #   - ai.is_ia == True
        #   - ai.ia_tick(dt)
        if not getattr(ai_controller, "is_ia", False):
            continue
        if not hasattr(ai_controller, "ia_tick"):
            continue

        try:
            ai_controller.ia_tick(dt)
        except Exception as e:
            ux, uy = getattr(unit, "position", (None, None))
            logger.error(
                "Erreur ia_tick sur %s (pos=%s,%s) : %s",
                unit, ux, uy, e
            )


# ---------------------------------------------------------------------------
# TEST
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("[TEST] IA_Eclaireur sanity check (patrouille dirigée).")

    grid = SimpleGrid(40, 30, cell_size=32)

    # carré bloqué milieu
    for _x in range(15, 25):
        for _y in range(10, 20):
            grid.walkable[_x][_y] = False

    adapter = make_grid_adapter_from_simplegrid(grid)

    class DummyUnit:
        def __init__(self, pos: Vec2, team="red") -> None:
            self.position = pos
            self.team = team
            self.target_position = None
            self.is_moving = False

        def move_to_position(self, p: Vec2) -> None:
            # pour le mini test: téléporte direct
            self.position = (float(p[0]), float(p[1]))
            self.target_position = p
            self.is_moving = True

        def stop(self) -> None:
            self.is_moving = False

    # zones cachées
    class _Poly:
        def __init__(self, x: float, y: float) -> None:
            class _C:
                def __init__(self, x: float, y: float) -> None:
                    self.x = x
                    self.y = y
            self.centroid = _C(x, y)

    hidden_list: List[Union[Polygon, _Poly]] = [
        _Poly(900.0, 400.0),
        _Poly(200.0, 700.0),
    ]

    def get_hidden():
        return list(hidden_list)

    def get_base(team: str) -> Vec2:
        return (64.0, 64.0)

    u = DummyUnit(pos=(100.0, 100.0), team="red")

    ai = ScoutAI(
        unit=u,
        grid=adapter,
        get_hidden_quantum_polygons=get_hidden,
        get_base_pos=get_base,
        return_to_base_when_done=True,
        replan_interval=0.5,
        proximity_epsilon=8.0,
    )

    for _ in range(10):
        ai.ia_tick(0.2)

    print("[TEST] OK.")
