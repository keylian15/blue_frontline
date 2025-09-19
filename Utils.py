import sys, pygame
from Global import *
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
