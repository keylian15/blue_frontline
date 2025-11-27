import os
import random
import sys
from collections.abc import Iterable

import pygame


def load_tileset(path: str, size: int = 32):
    """
    Charge un spritesheet et le découpe en tuiles.

    Args:
        path (str): Chemin vers le fichier image du tileset

    Returns:
        tiles (list[pygame.Surface]): liste de tuiles découpées
    """
    tile_width = tile_height = size
    image = pygame.image.load(path).convert_alpha()
    tiles = []
    sheet_width, sheet_height = image.get_size()

    for y in range(0, sheet_height, tile_height):
        for x in range(0, sheet_width, tile_width):
            rect = pygame.Rect(x, y, tile_width, tile_height)
            tile = image.subsurface(rect)
            tiles.append(tile)

    return tiles


def resource_path(relative_path: str):
    """Retourne le chemin absolu vers une ressource depuis la racine du projet.

    Args:
        relative_path (str): Chemin relatif vers la ressource.

    Returns:
        (str): Chemin absolu vers la ressource.
    """

    # Si on est dans un EXE PyInstaller
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    return os.path.join(base_path, relative_path)


def user_data_path(filename: str):
    """Retourne le chemin pour les données utilisateur (lecture/écriture).

    Pour les exécutables PyInstaller, vérifie d'abord si le fichier existe dans le package,
    sinon crée un chemin à côté de l'exécutable.

    Args:
        filename (str): Chemin relatif vers la ressource.

    Returns:
        (str): Chemin absolu vers la ressource.
    """
    if hasattr(sys, "_MEIPASS"):  # si exe PyInstaller
        # D'abord, vérifier si le fichier existe dans le package
        packaged_path = os.path.join(sys._MEIPASS, filename)
        if os.path.exists(packaged_path):
            return packaged_path

        # Sinon, utiliser le dossier à côté de l'exe pour l'écriture
        base_path = os.path.dirname(sys.executable)
    else:  # si script normal
        base_path = os.path.dirname(__file__)

    # Remonter jusqu'a blue_frontline
    base_path = os.path.dirname(base_path)  # /src
    base_path = os.path.dirname(base_path)  # /blue_frontline

    # Crée les dossiers nécessaires
    full_path = os.path.join(base_path, filename)
    data_dir = os.path.dirname(full_path)
    os.makedirs(data_dir, exist_ok=True)
    return full_path


def random_point_in_polygon(points: tuple[int, int]):
    """Génère un point aléatoire à l'intérieur d'un polygone défini par ses sommets.

    Args:
        points (tuple[int, int]): Coordonnées des sommets du polygone.

    Returns:
        point (tuple[int, int]): Coordonnées du point généré.
    """
    from shapely.geometry import Point, Polygon

    poly = Polygon(points)
    minx, miny, maxx, maxy = poly.bounds  # bounding box du polygone

    while True:
        # Tirage aléatoire dans le rectangle englobant
        p = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        if poly.contains(p):
            return (p.x, p.y)


def point_in_polygon(polygon_points, test_point):
    """Détermine si un point est à l'intérieur d'un polygone (méthode du ray casting).

    Args:
        polygon_points (list[tuple[float, float]]): Liste des sommets du polygone (x, y).
        test_point (tuple[float, float]): Coordonnées du point à tester (x, y).

    Returns:
        (bool): True si le point est à l'intérieur du polygone, False sinon.
    """

    # Coordonnées du point à tester
    x, y = test_point

    # Booléen indiquant si le point est à l'intérieur du polygone
    inside = False

    # Nombre de sommets du polygone
    n = len(polygon_points)

    # On parcourt tous les segments du polygone (chaque sommet avec le suivant)
    for i in range(n):
        x1, y1 = polygon_points[i]
        x2, y2 = polygon_points[(i + 1) % n]  # relie le dernier au premier sommet

        # Étape 1 : vérifier si le segment traverse la ligne horizontale du point
        # (le point est entre les hauteurs y1 et y2)
        if (y1 > y) != (y2 > y):
            # Étape 2 : calculer la position x du point d'intersection
            # entre le segment et la ligne horizontale passant par le point
            x_intersect = (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1

            # Étape 3 : si le point est à gauche de cette intersection,
            # on considère que le rayon partant vers la droite le croise
            if x < x_intersect:
                inside = not inside  # on inverse l'état

    # Si le nombre d'intersections est impair → le point est dans le polygone
    return inside


def point_in_many_polygons(polygons_points: list[list[tuple]], test_point: tuple):
    """Vérifie si un point est dans plusieurs polygones.

    Args:
        polygons_points (list[list[tuple]]): Liste de listes de tuples
            représentant les coordonnées des sommets des polygones.
        test_point (tuple): Coordonnées du point à tester.

    Returns:
        (bool, Polygon): True si le point est dans un polygone ainsi que son polygon, False sinon.
    """
    for polygon_points in polygons_points:
        if point_in_polygon(polygon_points, test_point):
            return True, polygon_points
    return False


def get_types(obj: any):
    """
    Affiche les types contenus dans obj.
    - Si obj est un dict : affiche les types des clés et des valeurs
    - Si obj est une séquence (tuple, list, set, etc.) : affiche les types des éléments
    - Sinon : affiche le type de obj

    Args:
        obj (Any): l'objet dont on veut afficher les types
    """
    if isinstance(obj, dict):
        print(
            {
                "keys": [type(k).__name__ for k in obj.keys()],
                "values": [type(v).__name__ for v in obj.values()],
            }
        )
    elif isinstance(obj, Iterable) and not isinstance(obj, (str | bytes)):
        print([type(e).__name__ for e in obj])
    else:
        print(type(obj).__name__)


def get_cost(nom: str) -> int:
    """Fonction permettant d'avoir le coût d'une entité

    Args:
        nom (str): Le nom de l'entité.

    Returns:
        coût (int): Le coût de l'entité
    """
    from src.config.units import UNIT_CONFIGS

    return UNIT_CONFIGS[nom]["cost"]
