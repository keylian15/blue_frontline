import pygame
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


if __name__ == "__main__":
    pygame.init()
    tiles = load_tileset(BASE_DIR + "/assets/island/png/island_spritesheet.png")
    print(f"Nombre de tuiles chargées : {len(tiles)}")
    pygame.quit()