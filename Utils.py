import sys, pygame, random
from Global import *
from shapely.geometry import Point, Polygon

def load_tileset(path):
    """
    Charge un spritesheet et le découpe en tuiles.
    Args:
        path (str): chemin vers le fichier image du tileset
    Returns:
        list[pygame.Surface]: liste de tuiles découpées
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

def resource_path(relative_path):
    """Retourne le chemin absolu vers une ressource"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)  # exe PyInstaller
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)  # script normal

def random_point_in_polygon(points):
    """
    Génère un point aléatoire à l'intérieur d'un polygone défini par ses sommets.
    points : liste de tuples (x, y)
    """
    poly = Polygon(points)
    minx, miny, maxx, maxy = poly.bounds  # bounding box du polygone

    while True:
        # Tirage aléatoire dans le rectangle englobant
        p = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        if poly.contains(p):
            return (p.x, p.y)

def point_in_polygon(polygon_points:list[tuple], test_point:tuple):
    """
    Vérifie si un point est dans un polygone.
    polygon_points : liste de tuples (x, y)
    test_point : tuple (x, y)
    """
    poly = Polygon(polygon_points)
    point = Point(test_point)
    return poly.contains(point)

def point_in_many_polygons(polygons_points:list[list[tuple]], test_point:tuple) : 
    """
    Vérifie si un point est dans un polygone.
    polygons_points : liste de listes de tuples (x, y)
    test_point : tuple (x, y)
    renvoi un booléen et les points du polygone dans lequel le point est
    """
    for polygon_points in polygons_points:
        if point_in_polygon(polygon_points, test_point):
            return True, polygon_points
    return False