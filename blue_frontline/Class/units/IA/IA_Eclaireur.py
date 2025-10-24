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

Convention d'équipe:
- toute IA a is_ia = True
- appel public = ia_tick()
"""

import heapq
import logging
import math
import random
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
    Cerveau de l'éclaireur:
      - choisit une zone cachée (quantique_area_hidden)
      - essaie A* pour l'approcher
      - si A* échoue et que la zone est proche -> va tout droit vers la zone
      - sinon -> PATROUILLE
            * garde une direction persistante (wander_dir)
            * avance droit devant
            * si bloqué -> tourne sa direction et continue
      - dès qu'une zone devient proche -> stop patrouille, va vers elle

    L'unité doit fournir :
        self.position : (x,y)
        self.move_to_position((x,y))
        self.stop()
        self.team : "red"/"green"
        self.target_position : (x,y) ou None

    Game doit fournir :
        get_hidden_quantum_polygons() -> liste zones cachées
        get_base_position(team) -> (x,y)
        nav_grid_adapter
    """

    is_ia: bool = True  # convention

    def __init__(
        self,
        unit: object,
        grid: GridAdapter,
        get_hidden_quantum_polygons: Callable[[], Sequence[object]],
        get_base_pos: Callable[[str], Vec2],
        return_to_base_when_done: bool = True,
        replan_interval: float = 1.0,
        proximity_epsilon: float = 8.0,
    ) -> None:
        self.unit = unit
        self.grid = grid
        self.get_hidden_quantum_polygons = get_hidden_quantum_polygons
        self.get_base_pos = get_base_pos
        self.return_to_base_when_done = return_to_base_when_done
        self.replan_interval = replan_interval
        self.proximity_epsilon = proximity_epsilon

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
        # direction courante (vecteur unitaire environ)
        # None = pas en mode patrouille
        self._wander_dir: Optional[Vec2] = None

        # pour limiter la taille du segment qu'on pousse en patrouille
        self._wander_step_dist: float = 600.0  # pixels devant

        # anti blocage
        self._last_pos_for_block: Vec2 = self.unit.position
        self._block_timer: float = 0.0
        self._BLOCK_THRESHOLD_SEC = 1.0
        self._BLOCK_MIN_MOVE = 5.0

        self.enabled: bool = True

    # ------------------------------------------------------------------
    # Méthodes publiques appelées par le moteur
    # ------------------------------------------------------------------
    def ia_tick(self, dt: float) -> None:
        if not self.enabled:
            return

        self._accum += dt
        self._block_timer += dt

        # Avancer / donner les ordres movement vers le waypoint courant
        self._follow_waypoints(dt)

        # Régulièrement (ou si pas de chemin) :
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

    def ia_set_enabled(self, value: bool) -> None:
        self.enabled = bool(value)
        if not self.enabled:
            self._clear_path()
            self.unit.stop()

    # ------------------------------------------------------------------
    # PLANIFICATION / OBJECTIF
    # ------------------------------------------------------------------
    def _ensure_objective_and_path(self) -> None:
        """
        Choisit une cible globale:
          - zone cachée la plus proche
          - sinon base si tout est scouté
        Puis essaie A*. Si A* pas possible:
          - soit on va direct si la zone est proche
          - soit on passe en mode patrouille dirigée
        """
        hidden = self.get_hidden_quantum_polygons()

        # debug inventaire des zones cachées
        if hidden:
            logger.info("ScoutAI DEBUG: %d zones cachées reçues par l'IA", len(hidden))
            for i, poly in enumerate(hidden):
                c = self._compute_centroid_from_polygon_like(poly)
                if c:
                    logger.info("  -> zone[%d] centroïde vu=(%.1f, %.1f)", i, c[0], c[1])

        # Choisir la zone cachée la plus proche
        if hidden:
            target = self._pick_best_hidden_zone(hidden)
        else:
            # aucune zone cachée => retour base ?
            if self.return_to_base_when_done:
                target = self.get_base_pos(getattr(self.unit, "team", "red"))
            else:
                target = None

        self.current_goal_world = target

        if target is None:
            # plus rien à faire => stop
            self._wander_dir = None
            self._clear_path()
            self.unit.stop()
            return

        # Essayons de créer un chemin A* local
        got_path = self._plan_local_path_to(target)

        if got_path:
            # Puisqu'on a un vrai chemin A*, on n'est plus en patrouille libre
            self._wander_dir = None
            return

        # Pas de chemin A*!
        # On regarde la distance jusqu'à la cible: proche -> direct tout droit
        ux, uy = self.unit.position
        tx, ty = target
        dist = math.hypot(tx - ux, ty - uy)

        if dist < 1200.0:
            # mode "direct tout droit"
            self._wander_dir = None
            self._path_world = [(tx, ty)]
            logger.warning(
                "ScoutAI: aucun chemin local vers (%.1f, %.1f) -> je vais TOUT DROIT (dist=%.1f).",
                tx,
                ty,
                dist,
            )
            self._push_move_order_if_any()
            return

        # Trop loin et pas de chemin => Patrouille directionnelle
        self._enter_or_update_patrol()

    def _compute_centroid_from_polygon_like(self, poly: object) -> Optional[Vec2]:
        """
        poly peut être:
         - un objet shapely-like avec poly.centroid.x/y
         - une liste de points [(x,y), ...]
        """
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

    def _pick_best_hidden_zone(self, hidden: Sequence[object]) -> Optional[Vec2]:
        """
        Choisit la zone cachée la plus proche du bateau
        (distance euclidienne).
        """
        ux, uy = self.unit.position
        best_goal: Optional[Vec2] = None
        best_d2: float = float("inf")

        for poly in hidden:
            goal = self._compute_centroid_from_polygon_like(poly)
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

    # ------------------------------------------------------------------
    # PATHFINDING LOCAL
    # ------------------------------------------------------------------
    def _plan_local_path_to(self, world_goal: Vec2) -> bool:
        """
        Essaie d'obtenir un chemin A* entre la cellule courante
        et la cellule but (ou proche du but).
        Si trouvé:
          - stocke les waypoints monde dans self._path_world
          - envoie immédiatement un ordre de move_to_position()
        Retourne True si succès.
        """
        start_cell = self.grid.world_to_cell(self.unit.position)
        goal_cell = self.grid.world_to_cell(world_goal)

        # Tentative directe
        path_cells = self.astar.find_path(start_cell, goal_cell, max_expansions=1000)

        # sinon on cherche une cellule 'atteignable' autour du but
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

        # conversion en waypoints monde
        self._path_world = [self.grid.cell_to_world(c) for c in path_cells]
        if self._path_world:
            logger.info(
                "ScoutAI: chemin LOCAL planifié (%d steps), 1er WP=(%.1f, %.1f)",
                len(self._path_world),
                self._path_world[0][0],
                self._path_world[0][1],
            )

        # quitte le mode patrouille libre si on en avait un
        self._wander_dir = None

        # On pousse un move immédiat
        self._push_move_order_if_any()

        return True

    def _find_reachable_cell_near(
        self,
        start_cell: Cell,
        goal_cell: Cell,
        search_radius_cells: int = 6,
    ) -> Optional[Cell]:
        """
        Si la cellule du but est injouable, on essaye autour.
        On teste rapidement la faisabilité avec un A* limité.
        """
        gx, gy = goal_cell
        candidates: List[Tuple[float, Cell]] = []

        for dx in range(-search_radius_cells, search_radius_cells + 1):
            for dy in range(-search_radius_cells, search_radius_cells + 1):
                cx = gx + dx
                cy = gy + dy
                cand = (cx, cy)
                if not self.grid.is_walkable(cand):
                    continue
                dist2 = dx * dx + dy * dy
                candidates.append((dist2, cand))

        candidates.sort(key=lambda t: t[0])

        for _, cand_cell in candidates[:30]:
            test_path = self.astar.find_path(
                start_cell,
                cand_cell,
                max_expansions=500,
            )
            if test_path:
                return cand_cell

        logger.warning(
            "ScoutAI: _find_reachable_cell_near abandon (aucune cellule atteignable proche)"
        )
        return None

    # ------------------------------------------------------------------
    # PATROUILLE DIRECTIONNELLE ("wander")
    # ------------------------------------------------------------------
    def _enter_or_update_patrol(self) -> None:
        """
        Active / met à jour le mode patrouille dirigée.
        - Si on n'a pas encore de direction => on en choisit une (aléatoire).
        - On génère un seul waypoint loin devant dans cette direction.
        - self._path_world = [ce waypoint]
        """
        # si pas encore de direction persistante, on en crée une
        if self._wander_dir is None:
            self._wander_dir = self._pick_new_wander_dir()
            logger.info(
                "ScoutAI: patrouille activée. direction initiale = (%.2f, %.2f)",
                self._wander_dir[0],
                self._wander_dir[1],
            )

        # On pousse un waypoint "droit devant"
        wp = self._make_forward_waypoint(self._wander_dir)
        self._path_world = [wp]
        logger.info(
            "ScoutAI: patrouille -> WP=(%.1f, %.1f) (1 step).",
            wp[0],
            wp[1],
        )
        self._push_move_order_if_any()

    def _pick_new_wander_dir(self) -> Vec2:
        """
        Choisit une direction initiale pour la patrouille.
        On part d'un angle aléatoire.
        """
        ang = random.uniform(0.0, math.tau)
        return (math.cos(ang), math.sin(ang))

    def _rotate_wander_dir(self, cur: Vec2, max_angle_deg: float = 70.0) -> Vec2:
        """
        Quand on est bloqué, on change de cap en tournant la direction
        actuelle d'un angle +/- max_angle_deg.
        """
        (dx, dy) = cur
        base_ang = math.atan2(dy, dx)
        delta = math.radians(random.uniform(-max_angle_deg, max_angle_deg))
        new_ang = base_ang + delta
        return (math.cos(new_ang), math.sin(new_ang))

    def _make_forward_waypoint(self, direction: Vec2) -> Vec2:
        """
        Fabrique un waypoint à self._wander_step_dist pixels
        dans 'direction' à partir de la position actuelle du bateau.
        """
        ux, uy = self.unit.position
        dx, dy = direction
        # normaliser un peu au cas où
        n = math.hypot(dx, dy)
        if n < 1e-5:
            dx, dy = 1.0, 0.0
            n = 1.0
        dx /= n
        dy /= n

        return (
            ux + dx * self._wander_step_dist,
            uy + dy * self._wander_step_dist,
        )

    # ------------------------------------------------------------------
    # SUIVI DES WAYPOINTS / ANTI-BLOCAGE
    # ------------------------------------------------------------------
    def _follow_waypoints(self, dt: float) -> None:
        """
        Chaque tick IA :
        - si on est arrivé au WP courant -> on passe au suivant
        - si bloqué depuis trop longtemps -> on skip le WP courant
          et si on est en patrouille => on change de direction
        - envoie les ordres move_to_position() continuellement
        """

        if not self._path_world:
            return

        # WP courant
        wx, wy = self._path_world[0]
        ux, uy = self.unit.position

        # check si atteint
        dist_sq = (ux - wx) ** 2 + (uy - wy) ** 2
        if dist_sq <= (self.proximity_epsilon ** 2):
            # WP atteint : on le consomme
            self._path_world.pop(0)
            self._after_waypoint_reached()
            return

        # pas encore atteint -> on pousse l'ordre de bouger vers ce WP
        self._push_move_order_if_any()

        # anti-blocage
        moved_dist = math.hypot(ux - self._last_pos_for_block[0], uy - self._last_pos_for_block[1])
        if moved_dist > self._BLOCK_MIN_MOVE:
            # ok on a bougé, reset timer blocage
            self._last_pos_for_block = (ux, uy)
            self._block_timer = 0.0
        else:
            # on n'a pas assez bougé
            if self._block_timer >= self._BLOCK_THRESHOLD_SEC:
                # considéré bloqué
                logger.warning(
                    "ScoutAI: unité bloquée sur WP (%.1f, %.1f), je skip ce waypoint.",
                    wx,
                    wy,
                )
                self._path_world.pop(0)
                self._last_pos_for_block = (ux, uy)
                self._block_timer = 0.0

                # si on est en mode patrouille (wander_dir actif)
                if self._wander_dir is not None:
                    # tourne un peu la direction
                    self._wander_dir = self._rotate_wander_dir(self._wander_dir)
                    # nouveau waypoint droit devant
                    new_wp = self._make_forward_waypoint(self._wander_dir)
                    self._path_world = [new_wp]
                    logger.info(
                        "ScoutAI: réorientation patrouille -> nouvelle dir=(%.2f, %.2f), WP=(%.1f, %.1f)",
                        self._wander_dir[0],
                        self._wander_dir[1],
                        new_wp[0],
                        new_wp[1],
                    )

                # pousse le move sur le WP suivant (si il y en a encore)
                self._push_move_order_if_any()

    def _after_waypoint_reached(self) -> None:
        """
        Appelé quand on vient d'atteindre un waypoint.
        - Si on a encore d'autres waypoints (chemin A* long), on continue.
        - Si on était en patrouille (wander_dir != None) et qu'on a bouffé
          le seul waypoint de patrouille :
            -> on regénère UN autre waypoint dans la même direction.
        """
        ux, uy = self.unit.position

        # reset blocage pour le prochain segment
        self._last_pos_for_block = (ux, uy)
        self._block_timer = 0.0

        # si on avait encore des waypoints (cas chemin A* long), basta :
        if self._path_world:
            self._push_move_order_if_any()
            return

        # plus de wp
        if self._wander_dir is not None:
            # on continue d'avancer tout droit: nouveau WP
            wp = self._make_forward_waypoint(self._wander_dir)
            self._path_world = [wp]
            logger.debug(
                "ScoutAI: patrouille continue -> nouveau WP=(%.1f, %.1f)",
                wp[0],
                wp[1],
            )
            self._push_move_order_if_any()
        else:
            # pas en patrouille: stoppe
            self.unit.stop()

    def _push_move_order_if_any(self) -> None:
        """
        Donne un ordre move_to_position() vers le premier waypoint restant.
        On évite le spam si la target_position actuelle est quasi identique.
        """
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

        self.unit.move_to_position((wx, wy))
        logger.debug(
            "ScoutAI DEBUG MOVE ORDER -> (%.1f, %.1f)",
            wx,
            wy,
        )

    def _clear_path(self) -> None:
        self._path_world = []
        self.unit.stop()


# ---------------------------------------------------------------------------
# petit test rapide si on run ce fichier directement
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

    # zones cachées bidon
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
