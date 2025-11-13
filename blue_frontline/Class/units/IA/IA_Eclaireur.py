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

import math
import random
from typing import (TYPE_CHECKING, Callable, List, Optional, Sequence, Tuple, Union)

if TYPE_CHECKING:
    from Class.Game import Game

# Import de toute la logique de pathfinding depuis le fichier séparé
from .PathfindingLogic import (
    AStar,
    GridAdapter,
    SimpleGrid,
    Polygon,
    Vec2,
    Cell,
    make_grid_adapter_from_simplegrid,
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
        self._BLOCK_THRESHOLD_SEC = 0.8  # Réduit pour réagir plus vite
        self._BLOCK_MIN_MOVE = 8.0  # Augmenté pour mieux détecter le blocage
        
        # Compteur de tentatives de blocage répétées (éviter de forcer l'entrée)
        self._consecutive_blocks = 0
        self._MAX_CONSECUTIVE_BLOCKS = 3  # Après 3 blocages, abandon complet du waypoint

        # petit timer pour éviter "je viens de poser un WP et je dis déjà que je suis arrivé"
        self._just_assigned_wp_timer: float = 0.0

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

        # cible = zone cachée la plus proche
        target: Optional[Vec2] = None
        if hidden:
            target = self._pick_best_hidden_zone(hidden)

        # S'il n'y a plus de zones cachées:
        # ancien comportement = rentrer à la base.
        # maintenant : NON, on reste en patrouille.
        if target is None:
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

        # tenter de planifier un chemin local (A*)
        got_path = self._plan_local_path_to(target)
        if got_path:
            # on quitte le mode patrouille libre
            self._wander_dir = None
            return

        # pas de chemin A*
        ux, uy = self.unit.position
        tx, ty = target
        dist = math.hypot(tx - ux, ty - uy)

        if dist < 1200.0:
            # "je fonce tout droit vers la cible"
            self._wander_dir = None
            self._path_world = [(tx, ty)]
            self._just_assigned_wp_timer = 0.5
            self._push_move_order_if_any()
            return

        # trop loin ET pas de chemin -> patrouille
        self._enter_or_update_patrol()

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

    def _pick_best_hidden_zone(self, hidden: Sequence[object]) -> Optional[Vec2]:
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

        return best_goal

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
            return False

        # convertit en points monde
        self._path_world = [self.grid.cell_to_world(c) for c in path_cells]

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
        candidates: List[Tuple[float, Cell]] = []

        for dx in range(-search_radius_cells, search_radius_cells + 1):
            for dy in range(-search_radius_cells, search_radius_cells + 1):
                cand = (gx + dx, gy + dy)
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
        wp = self._make_forward_waypoint(self._wander_dir)
        self._path_world = [wp]
        self._just_assigned_wp_timer = 0.5
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
                return

        # si rien trouvé -> au moins rester dans la carte
        wp_fallback = self._make_forward_waypoint(self._wander_dir)
        self._path_world = [wp_fallback]
        self._just_assigned_wp_timer = 0.5

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
            self._consecutive_blocks = 0  # Reset compteur de blocages consécutifs
            return

        # pas de progrès -> on accumule le blocage
        self._block_timer += dt

        if not time_blocked_enough and not close_but_not_entering:
            return  # pas encore déclaré bloqué

        # BLOQUÉ
        self._consecutive_blocks += 1

        # Si trop de blocages consécutifs, abandonner complètement ce waypoint
        if self._consecutive_blocks >= self._MAX_CONSECUTIVE_BLOCKS:
            # Vider tout le chemin et entrer en mode patrouille
            self._path_world = []
            self._consecutive_blocks = 0
            self._last_pos_for_block = (ux, uy)
            self._block_timer = 0.0
            
            # Force la patrouille pour éviter de rester coincé
            self._enter_or_update_patrol()
            return

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
        self._consecutive_blocks = 0  # Reset compteur après waypoint atteint

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

        self.unit.move_to_position((wx, wy))

    def _clear_path(self) -> None:
        self._path_world = []
        self.unit.stop()

# =====================================================================
# RUNTIME GLOBAL POUR LES ECLAIREURS
# (Ces fonctions sont appelées depuis GameUpdater, mais restent définies
#  ici pour isoler toute la logique IA dans le fichier de l'éclaireur)
# =====================================================================
def _rebuild_nav_if_needed(game: Game) -> None:
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
        except Exception:
            pass


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
