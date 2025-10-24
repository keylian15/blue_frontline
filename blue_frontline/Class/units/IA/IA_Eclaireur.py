from __future__ import annotations
from Class.units.IA.IA_Eclaireur import ScoutAI

"""
IA_Eclaireur.py — Contrôleur IA de l'Éclaireur.

À placer dans: Class/units/IA/IA_Eclaireur.py

Conventions demandées par le chef de groupe:
    - Chaque classe d'IA expose un booléen public `is_ia: bool = True`.
    - Toutes les méthodes PUBLIQUES que le jeu appelle directement
      commencent par `ia_` (ex: ia_tick(), ia_set_enabled()).

But de cette IA:
    - L'Éclaireur doit explorer les zones quantiques cachées (non révélées).
    - Déplacement via A* sur une grille de navigation (8 directions).
    - Quand toutes les zones sont révélées: rentrer à la base alliée
      (plateforme pétrolière) ou rester à l'arrêt.

Ce module fournit aussi:
    - SimpleGrid / make_grid_adapter_from_simplegrid(): génération d'une
      grille de nav avec coûts de terrain.
    - Des sanity-checks exécutables en stand-alone (__main__).

Intégration rappel:
    - Game.build_nav_grid() construit la grille (self.nav_grid_adapter).
    - Game.get_hidden_quantum_polygons() renvoie les zones quantiques
      encore cachées.
    - Game.get_base_position(team) renvoie la position monde de la base
      de l'équipe.
    - Eclaireur.__init__ crée self.ai = ScoutAI(...).
    - GameUpdater.update() doit appeler ai.ia_tick(dt).

Logs / debug:
    - Le logger 'EclaireurAI' annonce les étapes clés:
      objectif atteint, retour à la base, aucun chemin, etc.
    - Les sanity-checks lèvent des asserts claires si quelque chose
      casse (A*, choix de cible, retour à la base...).
"""

import heapq
import logging
import math
from dataclasses import dataclass
from typing import (Callable, Dict, Iterable, List, Optional, Sequence,
                    Tuple, Union)

# ---------------------------------------------------------------------------
# LOGGER LOCAL À L'IA
# ---------------------------------------------------------------------------
LOGGER_NAME = "EclaireurAI"
logger = logging.getLogger(LOGGER_NAME)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(name)s: %(message)s",
    )

# ---------------------------------------------------------------------------
# TYPES UTILISÉS PARTOUT
# ---------------------------------------------------------------------------
Vec2 = Tuple[float, float]
Cell = Tuple[int, int]

# ---------------------------------------------------------------------------
# DÉPENDANCE SHAPELY (OPTIONNELLE)
# ---------------------------------------------------------------------------
try:
    from shapely.geometry import Polygon, Point  # type: ignore
    from shapely.ops import nearest_points  # type: ignore
except Exception:
    class Polygon:  # type: ignore
        """Fallback Polygon minimal pour tests unitaires sans Shapely.

        Stocke une liste de points et expose un attribut .centroid.
        Ce stub ne gère pas toutes les méthodes Shapely.
        """

        def __init__(self, points: Sequence[Vec2]):
            self._points = list(points)
            if not self._points:
                raise ValueError("Polygon fallback: points vides")

        @property
        def centroid(self):
            """Retourne un objet avec .x / .y calculés comme barycentre."""
            sx = sum(p[0] for p in self._points)
            sy = sum(p[1] for p in self._points)
            n = len(self._points)

            class _C:
                def __init__(self, x: float, y: float) -> None:
                    self.x = x
                    self.y = y

            return _C(sx / n, sy / n)

        @property
        def boundary(self):  # pragma: no cover (fallback simplifié)
            class _B:
                def __init__(self, pts: Sequence[Vec2]):
                    self._pts = pts

            return _B(self._points)

    class Point:  # type: ignore
        def __init__(self, p: Vec2):
            self.x = p[0]
            self.y = p[1]

    def nearest_points(a: Point, b: object) -> Tuple[Point, Point]:
        """Fallback très simple: renvoie le premier point de b.boundary.

        Dans le vrai jeu on utilisera Shapely, donc ce chemin est surtout
        utile pour les sanity-checks.
        """
        try:
            pt = b._pts[0]  # type: ignore[attr-defined]
        except Exception:
            pt = (a.x, a.y)

        class _P:
            def __init__(self, x: float, y: float) -> None:
                self.x = x
                self.y = y

        return (a, _P(pt[0], pt[1]))

# ---------------------------------------------------------------------------
# EXCEPTIONS DÉDIÉES
# ---------------------------------------------------------------------------
class ScoutAIError(RuntimeError):
    """Erreur lancée par l'IA Éclaireur en cas d'état incohérent."""

    pass


class GridAdapterError(RuntimeError):
    """Erreur lancée si la grille de navigation est invalide."""

    pass


# ---------------------------------------------------------------------------
# FILE DE PRIORITÉ POUR A*
# ---------------------------------------------------------------------------
class _PriorityQueue:
    """File de priorité minimale (min-heap) utilisée par A*.

    Stocke des triplets (priority, tiebreak, cell) pour que l'ordre soit
    stable même si deux entrées ont la même priorité.
    """

    def __init__(self) -> None:
        self._pq: List[Tuple[float, int, Cell]] = []
        self._tiebreak: int = 0

    def push(self, priority: float, item: Cell) -> None:
        """Ajoute une cellule avec la priorité donnée."""
        self._tiebreak += 1
        heapq.heappush(self._pq, (priority, self._tiebreak, item))

    def pop(self) -> Cell:
        """Retire et renvoie la cellule la plus prioritaire."""
        if not self._pq:
            raise ScoutAIError("PriorityQueue.pop() sur file vide")
        return heapq.heappop(self._pq)[2]

    def __bool__(self) -> bool:
        return bool(self._pq)


# ---------------------------------------------------------------------------
# A* SUR GRILLE 8-VOISINS
# ---------------------------------------------------------------------------
def octile(a: Cell, b: Cell) -> float:
    """Heuristique 'octile' pour grille où la diagonale est permise.

    Approxime le coût pour aller de a -> b quand on peut bouger en 8
    directions. dx, dy sont les distances en cases.
    """
    dx: int = abs(a[0] - b[0])
    dy: int = abs(a[1] - b[1])
    return (dx + dy) + (math.sqrt(2.0) - 2.0) * min(dx, dy)


class AStar:
    """Implémentation simplifiée de l'algorithme A*.

    Cette classe reste découplée du moteur de jeu.
    On lui fournit:
        - is_walkable(cell: Cell) -> bool
        - cost(cell: Cell) -> float
        - neighbors(cell: Cell) -> Iterable[Cell]
        - heuristic(a: Cell, b: Cell) -> float  (par défaut: octile)
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
        max_expansions: int = 100_000,
    ) -> List[Cell]:
        """Calcule un chemin de start -> goal en espace grille.

        Retourne:
            Liste de cellules [start, ..., goal].
            Liste vide si introuvable.

        Sécurité:
            max_expansions limite le nombre de noeuds visités pour éviter de
            tourner en boucle en cas de carte cassée.
        """

        if not self.is_walkable(start) or not self.is_walkable(goal):
            return []

        frontier = _PriorityQueue()
        frontier.push(0.0, start)

        came_from: Dict[Cell, Optional[Cell]] = {start: None}
        g_cost: Dict[Cell, float] = {start: 0.0}

        expansions: int = 0

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

                new_cost: float = (
                    g_cost[current] + max(1.0, float(self.cost(nxt)))
                )
                if nxt not in g_cost or new_cost < g_cost[nxt]:
                    g_cost[nxt] = new_cost
                    priority = new_cost + self.heuristic(nxt, goal)
                    frontier.push(priority, nxt)
                    came_from[nxt] = current

        if goal not in came_from:
            # Aucun chemin trouvé.
            return []

        # Reconstruction du chemin du but vers la source.
        path: List[Cell] = []
        cur: Optional[Cell] = goal
        while cur is not None:
            path.append(cur)
            cur = came_from[cur]
        path.reverse()
        return path


# ---------------------------------------------------------------------------
# ADAPTATEUR MONDE <-> GRILLE POUR L'A*
# ---------------------------------------------------------------------------
@dataclass
class GridAdapter:
    """Pont entre le monde du jeu (pixels) et la grille logique A*.

    Attributs:
        cell_size: taille (pixels) d'une case.
        world_to_cell: convertit (x,y monde) -> (cx,cy cellule).
        cell_to_world: convertit (cx,cy cellule) -> centre (x,y monde).
        is_walkable: True si la cellule est navigable.
        cost: coût de traversée de la cellule (>1 = lent).
        neighbors: génère les voisins accessibles.
    """

    cell_size: int
    world_to_cell: Callable[[Vec2], Cell]
    cell_to_world: Callable[[Cell], Vec2]
    is_walkable: Callable[[Cell], bool]
    cost: Callable[[Cell], float]
    neighbors: Callable[[Cell], Iterable[Cell]]


# ---------------------------------------------------------------------------
# CLASSE PRINCIPALE: IA DE L'ÉCLAIREUR
# ---------------------------------------------------------------------------
class ScoutAI:
    """Cerveau haut niveau de l'Éclaireur.

    Missions:
        1. Aller explorer les zones quantiques cachées les plus proches.
        2. Se déplacer via des waypoints calculés par A*.
        3. Replanifier régulièrement (marées, obstacles révélés, etc.).
        4. Quand il n'y a plus de zones cachées: rentrer à la base
           (plateforme de l'équipe) ou s'arrêter.

    Contrat attendu côté jeu:
        - L'unité contrôlée (self.unit) DOIT avoir:
            .position -> Tuple[float, float]
            .team -> str ("red" / "green" ...)
            .move_to(x: float, y: float) -> None
            .stop() -> None

        - Le Game DOIT fournir (via les callbacks passés au ctor):
            get_hidden_quantum_polygons() -> Sequence[Polygon]
            get_base_position(team: str) -> Vec2
            nav_grid_adapter: GridAdapter (construit via build_nav_grid)

    Contraintes chef de groupe:
        - Attribut public is_ia: bool = True
        - Méthodes publiques préfixées par ia_
    """

    # Flag imposé par la spec d'équipe: indique que ceci est une IA
    is_ia: bool = True

    def __init__(
        self,
        unit: object,
        grid: GridAdapter,
        get_hidden_quantum_polygons: Callable[[], Sequence[Polygon]],
        get_base_pos: Callable[[str], Vec2],
        return_to_base_when_done: bool = True,
        replan_interval: float = 2.0,
        proximity_epsilon: float = 4.0,
    ) -> None:
        self.unit = unit
        self.grid = grid
        self.get_hidden_quantum_polygons = get_hidden_quantum_polygons
        self.get_base_pos = get_base_pos
        self.return_to_base_when_done = return_to_base_when_done
        self.replan_interval = replan_interval
        self.proximity_epsilon = proximity_epsilon

        self.astar: AStar = AStar(
            grid.is_walkable,
            grid.cost,
            grid.neighbors,
        )

        # Chemin courant en monde (pixels)
        self._path_world: List[Vec2] = []
        # Objectif monde actuel (pixels)
        self.current_goal_world: Optional[Vec2] = None

        # Accumulateur temps pour replanifier périodiquement
        self._accum: float = 0.0

        # L'IA est active par défaut
        self.enabled: bool = True

        # Pour éviter le spam de logs "objectif atteint"
        self._logged_goal: Optional[Vec2] = None

    # ------------------------------------------------------------------
    # MÉTHODES PUBLIQUES IA_* (APPELÉES PAR LE JEU)
    # ------------------------------------------------------------------
    def ia_set_enabled(self, value: bool) -> None:
        """Active/désactive l'IA.

        Si on désactive l'IA:
            - purge du chemin courant,
            - stop immédiat de l'unité.
        """
        self.enabled = bool(value)
        if not self.enabled:
            logger.info("ScoutAI: IA désactivée -> purge chemin")
            self._clear_path()
            self.unit.stop()

    def ia_tick(self, dt: float) -> None:
        """Tick IA à appeler à chaque frame (depuis GameUpdater).

        Args:
            dt (float): durée (en secondes) depuis la frame précédente.
        """
        if not self.enabled:
            return

        self._accum += dt

        # Suivre (et éventuellement consommer) le waypoint courant.
        self._advance_waypoints()

        # Replanification régulière pour s'adapter aux changements
        # (marées, zones révélées, collisions dynamiques...).
        if self._accum >= self.replan_interval:
            self._accum = 0.0
            self._ensure_path()

    # ------------------------------------------------------------------
    # MÉTHODES INTERNES (PRIVÉES)
    # ------------------------------------------------------------------
    def _advance_waypoints(self) -> None:
        """Fait progresser le navire vers le prochain waypoint.

        - Si aucun chemin n'est défini -> _ensure_path().
        - Si le prochain waypoint est atteint -> passe au suivant.
        - Si l'objectif final est atteint -> _on_goal_reached().
        """
        if not self._path_world:
            self._ensure_path()
            return

        wx, wy = self._path_world[0]
        ux, uy = self.unit.position

        # Check si on a atteint le waypoint courant (distance²).
        if (
            (ux - wx) ** 2 + (uy - wy) ** 2
            <= self.proximity_epsilon ** 2
        ):
            # WP atteint -> on l'enlève
            self._path_world.pop(0)

            if self._path_world:
                # Prochain WP
                nx, ny = self._path_world[0]
                self.unit.move_to(nx, ny)
                logger.debug(
                    "ScoutAI: prochain waypoint -> (%.1f, %.1f)",
                    nx,
                    ny,
                )
            else:
                # Objectif global atteint
                if self.current_goal_world != self._logged_goal:
                    logger.info(
                        "ScoutAI: objectif atteint %s",
                        self.current_goal_world,
                    )
                    self._logged_goal = self.current_goal_world
                self._on_goal_reached()
        else:
            # Toujours en route vers le waypoint courant
            self.unit.move_to(wx, wy)

    def _on_goal_reached(self) -> None:
        """Géré quand on a atteint l'objectif courant.

        Cas:
            - Il reste des zones quantiques cachées -> cibler la suivante.
            - Plus aucune zone cachée -> rentrer à la base (ou stop).
        """
        hidden = self.get_hidden_quantum_polygons()
        if hidden:
            # Encore du travail: choisir une nouvelle zone cachée
            self.current_goal_world = None
            self._plan_to_nearest_hidden(hidden)
        else:
            # Mission terminée -> base ou stop.
            if self.return_to_base_when_done:
                base = self.get_base_pos(getattr(self.unit, "team", "red"))
                self.current_goal_world = base
                logger.info(
                    "ScoutAI: toutes les zones révélées -> retour base %s",
                    base,
                )
                self._plan_path(base)
            else:
                self.unit.stop()
                logger.info(
                    "ScoutAI: toutes les zones révélées -> stop sur place",
                )
                self._clear_path()

    def _ensure_path(self) -> None:
        """S'assure que l'on dispose d'un chemin actif.

        - S'il y a déjà des waypoints, on ne touche à rien.
        - Sinon: cibler la zone quantique cachée la plus proche;
          si aucune n'existe, viser la base.
        """
        if self._path_world:
            return

        hidden = self.get_hidden_quantum_polygons()
        if hidden:
            self._plan_to_nearest_hidden(hidden)
        elif self.return_to_base_when_done:
            base = self.get_base_pos(getattr(self.unit, "team", "red"))
            self._plan_path(base)
        else:
            self.unit.stop()

    def _plan_to_nearest_hidden(
        self, hidden: Sequence[Polygon]
    ) -> None:
        """Sélectionne la zone quantique cachée la plus proche.

        Critère: distance euclidienne entre la position du navire et le
        centroïde du polygone caché. Planifie ensuite un chemin A*.
        """
        ux, uy = self.unit.position
        best_goal: Optional[Vec2] = None
        best_d2: float = float("inf")

        for poly in hidden:
            try:
                c = poly.centroid
                tx = float(c.x)
                ty = float(c.y)
            except Exception:
                # Polygone invalide ou fallback cassé -> on ignore
                continue

            d2 = (tx - ux) ** 2 + (ty - uy) ** 2
            if d2 < best_d2:
                best_d2 = d2
                best_goal = (tx, ty)

        if best_goal is None:
            logger.warning(
                "ScoutAI: aucune zone cachée valide trouvée",
            )
            return

        self.current_goal_world = best_goal
        self._plan_path(best_goal)

    def _plan_path(self, world_goal: Vec2) -> None:
        """Construit un chemin A* jusqu'à world_goal, puis génère
        les waypoints monde (pixels) à suivre.
        """
        start_cell = self.grid.world_to_cell(self.unit.position)
        goal_cell = self.grid.world_to_cell(world_goal)
        path_cells = self.astar.find_path(start_cell, goal_cell)

        if not path_cells:
            logger.warning(
                "ScoutAI: aucun chemin vers %s pour l'instant",
                world_goal,
            )
            self._clear_path()
            return

        # Convertit les cellules du chemin en coordonnées monde.
        self._path_world = [
            self.grid.cell_to_world(c) for c in path_cells
        ]

        # Donne l'ordre de mouvement vers le premier waypoint.
        if self._path_world:
            nx, ny = self._path_world[0]
            self.unit.move_to(nx, ny)
            logger.debug(
                "ScoutAI: chemin planifié (%d étapes), 1er WP=(%.1f,%.1f)",
                len(self._path_world),
                nx,
                ny,
            )

    def _clear_path(self) -> None:
        """Vide complètement la liste des waypoints actuels."""
        self._path_world = []


# ---------------------------------------------------------------------------
# GRILLE DE NAVIGATION (SIMPLEGRID)
# ---------------------------------------------------------------------------
class SimpleGrid:
    """Grille rectangulaire de navigation (walkable + coût).

    Attributs:
        width (int): nombre de cellules en X.
        height (int): nombre de cellules en Y.
        cell_size (int): taille d'une cellule en pixels.
        walkable[x][y] (bool): True si navigable.
        costs[x][y] (float): coût de traversée (>=1).

    Remarque diagonales:
        Pour autoriser une diagonale (x+1, y+1), on exige que les deux
        cases adjacentes cardinales soient walkable. Ça évite de "couper"
        dans un coin d'obstacle.
    """

    def __init__(self, width: int, height: int, cell_size: int = 32) -> None:
        if width <= 0 or height <= 0:
            raise GridAdapterError(
                "SimpleGrid: width/height doivent être > 0",
            )
        if cell_size <= 0:
            raise GridAdapterError(
                "SimpleGrid: cell_size doit être > 0",
            )

        self.width: int = int(width)
        self.height: int = int(height)
        self.cell_size: int = int(cell_size)

        self.walkable: List[List[bool]] = [
            [True for _ in range(self.height)]
            for _ in range(self.width)
        ]
        self.costs: List[List[float]] = [
            [1.0 for _ in range(self.height)]
            for _ in range(self.width)
        ]

    def in_bounds(self, c: Cell) -> bool:
        """Retourne True si la cellule est dans la grille."""
        x, y = c
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, c: Cell) -> bool:
        """Retourne True si la cellule est navigable (eau praticable)."""
        return self.in_bounds(c) and self.walkable[c[0]][c[1]]

    def cost(self, c: Cell) -> float:
        """Retourne le coût de traversée de la cellule."""
        return (
            self.costs[c[0]][c[1]] if self.in_bounds(c)
            else float("inf")
        )

    def neighbors8(self, c: Cell) -> Iterable[Cell]:
        """Génère les voisins 8-directions accessibles.

        Empêche le "corner cutting" : si on veut aller en diagonale,
        les deux cases cardinales adjacentes doivent être libres.
        """
        x, y = c
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue

                nc = (x + dx, y + dy)
                if not self.in_bounds(nc):
                    continue

                # diagonale => pas le droit de traverser un coin fermé
                if dx != 0 and dy != 0:
                    if not (
                        self.is_walkable((x + dx, y))
                        and self.is_walkable((x, y + dy))
                    ):
                        continue

                yield nc

    def world_to_cell(self, p: Vec2) -> Cell:
        """Convertit une coordonnée monde (pixels) en cellule (cx, cy)."""
        x, y = p
        return int(x // self.cell_size), int(y // self.cell_size)

    def cell_to_world(self, c: Cell) -> Vec2:
        """Renvoie le centre monde (pixels) d'une cellule (cx, cy)."""
        cx, cy = c
        return (
            cx * self.cell_size + self.cell_size * 0.5,
            cy * self.cell_size + self.cell_size * 0.5,
        )


def make_grid_adapter_from_simplegrid(grid: SimpleGrid) -> GridAdapter:
    """Construit un GridAdapter prêt pour l'IA à partir d'un SimpleGrid.

    Le GridAdapter est ce que le ScoutAI consomme réellement:
        - conversion monde<->cellule
        - test de navigabilité
        - coût de déplacement
        - voisins 8-directions
    """
    return GridAdapter(
        cell_size=grid.cell_size,
        world_to_cell=grid.world_to_cell,
        cell_to_world=grid.cell_to_world,
        is_walkable=grid.is_walkable,
        cost=grid.cost,
        neighbors=grid.neighbors8,
    )


# ---------------------------------------------------------------------------
# SANITY CHECKS (LANCÉS SI ON EXÉCUTE DIRECTEMENT CE FICHIER)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n[TEST] Démarrage des sanity-checks IA_Eclaireur.py")

    # 1) Construire une grille avec un gros bloc d'obstacles au centre
    grid = SimpleGrid(20, 12, cell_size=32)
    for _x in range(7, 13):
        for _y in range(4, 8):
            grid.walkable[_x][_y] = False

    adapter = make_grid_adapter_from_simplegrid(grid)

    # 2) Vérifier que A* trouve un chemin qui contourne l'obstacle
    astar = AStar(
        adapter.is_walkable,
        adapter.cost,
        adapter.neighbors,
    )
    start = (1, 6)
    goal = (18, 6)
    path = astar.find_path(start, goal)
    assert path, "A*: chemin vide alors qu'il devrait exister"
    assert path[0] == start and path[-1] == goal, (
        "A*: extrémités inattendues"
    )
    print("[OK] A* opérationnel")

    # 3) DummyUnit pour simuler un éclaireur contrôlable
    class DummyUnit:
        def __init__(self, pos: Vec2, team: str = "red") -> None:
            self.position: Vec2 = pos
            self.team: str = team
            self.stopped: bool = False

        def move_to(self, x: float, y: float) -> None:
            """Dans le vrai jeu: commencer un mouvement progressif.

            Ici pour les tests: téléportation immédiate pour accélérer.
            """
            self.position = (float(x), float(y))

        def stop(self) -> None:
            self.stopped = True

    # 4) Simuler une zone quantique cachée (polygone juste avec un centroïde)
    class _Poly:
        def __init__(self, x: float, y: float) -> None:
            class _C:
                def __init__(self, x: float, y: float) -> None:
                    self.x = x
                    self.y = y

            self.centroid = _C(x, y)

    hidden_list: List[Union[Polygon, _Poly]] = [
        _Poly(592.0, 208.0),
    ]

    def get_hidden() -> Sequence[Union[Polygon, _Poly]]:
        return list(hidden_list)

    def get_base(team: str) -> Vec2:
        # base rouge fixe pour le test
        return (48.0, 48.0)

    unit = DummyUnit(pos=(48.0, 208.0), team="red")

    ai = ScoutAI(
        unit=unit,
        grid=adapter,
        get_hidden_quantum_polygons=get_hidden,
        get_base_pos=get_base,
        return_to_base_when_done=True,
        replan_interval=0.1,
        proximity_epsilon=8.0,
    )

    # 5) Tick l'IA pour qu'elle choisisse une zone cachée et planifie un chemin
    for _ in range(50):
        ai.ia_tick(0.05)
        if ai.current_goal_world is not None and ai._path_world:
            break

    assert ai.current_goal_world is not None, (
        "ScoutAI: pas d'objectif après ticks"
    )
    assert ai._path_world, "ScoutAI: aucun chemin planifié"
    print(
        "[OK] ScoutAI choisit une zone cachée et planifie un chemin",
    )

    # 6) Simuler la découverte: plus de zones cachées -> retour à la base
    hidden_list.clear()
    for _ in range(20):
        ai.ia_tick(0.05)
        if ai.current_goal_world == get_base("red"):
            break

    assert (
        ai.current_goal_world == get_base("red")
    ), (
        "ScoutAI: ne retourne pas à la base après découverte"
    )
    print(
        "[OK] ScoutAI retourne à la base quand il n'y a plus de zones cachées",
    )

    print("[TEST] Fin sanity-checks.\n")
