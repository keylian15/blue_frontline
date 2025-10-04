import sys, pygame, random, os
from shapely.geometry import Point, Polygon

def load_tileset(path: str):
    """
    Charge un spritesheet et le découpe en tuiles.
    
    Args:
        path (str): Chemin vers le fichier image du tileset
    
    Returns:
        tiles (list[pygame.Surface]): liste de tuiles découpées
    """
    tile_width  = tile_height = 32
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
    """Retourne le chemin absolu vers une ressource/

    Args:
        relative_path (str): Chemin relatif vers la ressource.

    Returns:
        path (str): Chemin absolu vers la ressource.
    """
    
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)  # exe PyInstaller
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)  # script normal

def user_data_path(filename: str):
    """Retourne le chemin pour les sauvegardes (lecture/écriture).
    
    Args:
        filename (str): Chemin relatif vers la ressource.

    Returns:
        path (str): Chemin absolu vers la ressource.
    """
    if hasattr(sys, '_MEIPASS'):  # si exe
        base_path = os.path.dirname(sys.executable)  # dossier du .exe
    else:  # si script normal
        base_path = os.path.dirname(__file__)
    
    # Crée un sous-dossier "data" à côté de l'exe
    data_dir = os.path.join(base_path, "data")
    os.makedirs(data_dir, exist_ok=True)

    return os.path.join(base_path, filename)

def random_point_in_polygon(points: tuple[int, int]):
    """Génère un point aléatoire à l'intérieur d'un polygone défini par ses sommets.

    Args:
        points (tuple[int, int]): Coordonnées des sommets du polygone.

    Returns:
        point (tuple[int, int]): Coordonnées du point généré.
    """
    
    poly = Polygon(points)
    minx, miny, maxx, maxy = poly.bounds  # bounding box du polygone

    while True:
        # Tirage aléatoire dans le rectangle englobant
        p = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        if poly.contains(p):
            return (p.x, p.y)

def point_in_polygon(polygon_points:list[tuple], test_point:tuple):
    """Vérifie si un point est dans un polygone.

    Args:
        polygon_points (list[tuple]): Liste de tuples représentant les coordonnées des sommets du polygone.
        test_point (tuple): Coordonnées du point à tester.

    Returns:
        Bool: True si le point est dans le polygone, False sinon.
    """
    poly = Polygon(polygon_points)
    point = Point(test_point)
    return poly.contains(point)

def point_in_many_polygons(polygons_points:list[list[tuple]], test_point:tuple) : 
    """Vérifie si un point est dans plusieurs polygones.

    Args:
        polygons_points (list[list[tuple]]): Liste de listes de tuples représentant les coordonnées des sommets des polygones.
        test_point (tuple): Coordonnées du point à tester.

    Returns:
        bool, Polygon: True si le point est dans un polygone ainsi que son polygon, False sinon.
    """
    for polygon_points in polygons_points:
        if point_in_polygon(polygon_points, test_point):
            return True, polygon_points
    return False

from collections.abc import Iterable

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
        print({
            "keys": [type(k).__name__ for k in obj.keys()],
            "values": [type(v).__name__ for v in obj.values()]
        })
    elif isinstance(obj, Iterable) and not isinstance(obj, (str, bytes)):
        print([type(e).__name__ for e in obj])
    else:
        print(type(obj).__name__)
