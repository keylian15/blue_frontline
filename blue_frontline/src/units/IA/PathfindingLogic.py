"""
PathfindingLogic.py — Logique de pathfinding A* et gestion de grille.

Ce fichier contient toute la logique algorithmique de pathfinding (A*),
la gestion de grille de navigation, et les utilitaires géométriques.
Il est complètement indépendant de l'IA spécifique de l'Éclaireur.

Contenu:
- A* classique avec limite d'expansions
- Grille rectangulaire avec walkable/costs
- Adaptateur de grille pour l'A*
- File de priorité pour A*
- Heuristique octile
- Fallback Polygon pour tests sans shapely
"""

from __future__ import annotations

import heapq
import math
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Types de base
# ---------------------------------------------------------------------------
Vec2 = tuple[float, float]
Cell = tuple[int, int]


# ---------------------------------------------------------------------------
# Shapely optionnel - Fallback Polygon
# ---------------------------------------------------------------------------
try:
    from shapely.geometry import Polygon  # type: ignore
except Exception:

    class Polygon:  # type: ignore
        """Fallback Polygon minimal pour tests sans shapely."""

        def __init__(self, points: Sequence[Vec2]):
            self._points = list(points)

        @property
        def centroid(self):
            """Calcule le centroïde simple (moyenne des points)."""
            sx = sum(p[0] for p in self._points)
            sy = sum(p[1] for p in self._points)
            n = len(self._points)

            class _Centroid:
                def __init__(self, x: float, y: float):
                    self.x = x
                    self.y = y

            return _Centroid(sx / n, sy / n)


# ---------------------------------------------------------------------------
# File de priorité pour A*
# ---------------------------------------------------------------------------
class _PriorityQueue:
    """File de priorité pour l'algorithme A* avec tie-breaking."""

    def __init__(self) -> None:
        self._pq: list[tuple[float, int, Cell]] = []
        self._tiebreak: int = 0

    def push(self, priority: float, item: Cell) -> None:
        """Ajoute un élément avec une priorité donnée."""
        self._tiebreak += 1
        heapq.heappush(self._pq, (priority, self._tiebreak, item))

    def pop(self) -> Cell:
        """Retire et retourne l'élément de plus haute priorité."""
        return heapq.heappop(self._pq)[2]

    def __bool__(self) -> bool:
        """Retourne True si la file n'est pas vide."""
        return bool(self._pq)


# ---------------------------------------------------------------------------
# Heuristique pour A*
# ---------------------------------------------------------------------------
def octile(a: Cell, b: Cell) -> float:
    """
    Distance octile (heuristique optimale pour grille 8-directions).

    Args:
        a: Cellule de départ
        b: Cellule d'arrivée

    Returns:
        Distance octile estimée
    """
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    return (dx + dy) + (math.sqrt(2.0) - 2.0) * min(dx, dy)


# ---------------------------------------------------------------------------
# A* Pathfinding
# ---------------------------------------------------------------------------
class AStar:
    """
    A* classique sur grille 8 directions.
    Limitation d'expansions pour éviter de freeze le jeu.

    Attributes:
        is_walkable: Fonction qui détermine si une cellule est marchable
        cost: Fonction qui retourne le coût d'une cellule
        neighbors: Fonction qui retourne les voisins d'une cellule
        heuristic: Fonction heuristique (par défaut: octile)
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
    ) -> list[Cell]:
        """
        Trouve un chemin de start à goal en utilisant A*.

        Args:
            start: Cellule de départ
            goal: Cellule d'arrivée
            max_expansions: Nombre maximum de cellules à explorer

        Returns:
            Liste de cellules formant le chemin, ou liste vide si pas de chemin
        """
        if not self.is_walkable(start) or not self.is_walkable(goal):
            return []

        frontier = _PriorityQueue()
        frontier.push(0.0, start)

        came_from: dict[Cell, Cell | None] = {start: None}
        g_cost: dict[Cell, float] = {start: 0.0}

        expansions = 0

        while frontier:
            current = frontier.pop()
            if current == goal:
                break

            expansions += 1
            if expansions > max_expansions:
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

        # Reconstruction du chemin
        path: list[Cell] = []
        cur: Cell | None = goal
        while cur is not None:
            path.append(cur)
            cur = came_from[cur]
        path.reverse()
        return path


# ---------------------------------------------------------------------------
# Grille de navigation
# ---------------------------------------------------------------------------
@dataclass
class GridAdapter:
    """
    Adaptateur pour connecter une grille à l'algorithme A*.

    Attributes:
        cell_size: Taille d'une cellule en pixels
        world_to_cell: Convertit coordonnées monde -> cellule
        cell_to_world: Convertit cellule -> coordonnées monde
        is_walkable: Détermine si une cellule est marchable
        cost: Retourne le coût d'une cellule
        neighbors: Retourne les voisins d'une cellule
    """

    cell_size: int
    world_to_cell: Callable[[Vec2], Cell]
    cell_to_world: Callable[[Cell], Vec2]
    is_walkable: Callable[[Cell], bool]
    cost: Callable[[Cell], float]
    neighbors: Callable[[Cell], Iterable[Cell]]


class SimpleGrid:
    """
    Grille rectangulaire avec walkable + coûts.
    Le système neighbors8 empêche de traverser un coin bloqué en diagonale.

    Attributes:
        width: Largeur de la grille en cellules
        height: Hauteur de la grille en cellules
        cell_size: Taille d'une cellule en pixels
        walkable: Matrice de cellules marchables
        costs: Matrice des coûts de déplacement
    """

    def __init__(self, width: int, height: int, cell_size: int = 32) -> None:
        self.width = int(width)
        self.height = int(height)
        self.cell_size = int(cell_size)

        self.walkable: list[list[bool]] = [[True for _ in range(self.height)] for _ in range(self.width)]
        self.costs: list[list[float]] = [[1.0 for _ in range(self.height)] for _ in range(self.width)]

    def in_bounds(self, c: Cell) -> bool:
        """Vérifie si une cellule est dans les limites de la grille."""
        x, y = c
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, c: Cell) -> bool:
        """Détermine si une cellule est marchable."""
        x, y = c
        return self.in_bounds(c) and self.walkable[x][y]

    def cost(self, c: Cell) -> float:
        """Retourne le coût de déplacement d'une cellule."""
        x, y = c
        if not self.in_bounds(c):
            return float("inf")
        return self.costs[x][y]

    def neighbors8(self, c: Cell) -> Iterable[Cell]:
        """
        Retourne les 8 voisins d'une cellule (incluant diagonales).
        Empêche de traverser un coin bloqué en diagonale (corner cutting).

        Args:
            c: Cellule dont on veut les voisins

        Yields:
            Cellules voisines valides
        """
        x, y = c
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue

                nc = (x + dx, y + dy)
                if not self.in_bounds(nc):
                    continue

                # Anti "corner cut": empêche traversée diagonale si les côtés sont bloqués
                if dx != 0 and dy != 0:
                    if not (self.is_walkable((x + dx, y)) and self.is_walkable((x, y + dy))):
                        continue

                yield nc

    def world_to_cell(self, p: Vec2) -> Cell:
        """
        Convertit une position monde en coordonnées de cellule.

        Args:
            p: Position monde (x, y) en pixels

        Returns:
            Coordonnées de cellule (cx, cy)
        """
        x, y = p
        return int(x // self.cell_size), int(y // self.cell_size)

    def cell_to_world(self, c: Cell) -> Vec2:
        """
        Convertit des coordonnées de cellule en position monde (centre de la cellule).

        Args:
            c: Coordonnées de cellule (cx, cy)

        Returns:
            Position monde (x, y) au centre de la cellule
        """
        cx, cy = c
        return (
            cx * self.cell_size + self.cell_size * 0.5,
            cy * self.cell_size + self.cell_size * 0.5,
        )


# ---------------------------------------------------------------------------
# Fonction utilitaire
# ---------------------------------------------------------------------------
def make_grid_adapter_from_simplegrid(grid: SimpleGrid) -> GridAdapter:
    """
    Crée un GridAdapter à partir d'une SimpleGrid.

    Args:
        grid: Instance de SimpleGrid

    Returns:
        GridAdapter configuré pour utiliser avec A*
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
# Test rapide
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("[TEST] PathfindingLogic - Tests de base")

    # Créer une petite grille
    grid = SimpleGrid(20, 20, cell_size=32)

    # Bloquer quelques cellules pour former un obstacle
    for x in range(8, 12):
        for y in range(8, 12):
            grid.walkable[x][y] = False

    # Créer l'A*
    astar = AStar(
        is_walkable=grid.is_walkable,
        cost=grid.cost,
        neighbors=grid.neighbors8,
    )

    # Trouver un chemin
    start = (2, 2)
    goal = (15, 15)
    path = astar.find_path(start, goal, max_expansions=500)

    if path:
        print(f"✅ Chemin trouvé: {len(path)} cellules")
        print(f"   Départ: {start}, Arrivée: {goal}")
        print(f"   Premiers points: {path[:5]}...")
    else:
        print("❌ Aucun chemin trouvé")

    # Test conversion monde <-> cellule
    world_pos = (512.0, 768.0)
    cell = grid.world_to_cell(world_pos)
    world_back = grid.cell_to_world(cell)
    print(f"\n✅ Conversion: {world_pos} -> {cell} -> {world_back}")

    print("\n✅ Tous les tests passés!")
