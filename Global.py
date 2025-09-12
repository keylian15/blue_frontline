# Fichier des variables globales (Chemin, variables, etc.)
import os 

# Chemin du dossier courant
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Chemin de la map
MAP_PATH = "map.tmx"

# === Caméra ===
# Chemin de l'image Bullet
BULLET_IMAGE_PATH = os.path.join(BASE_DIR, 'assets/entity/png/bullet.png')

# === Ile Quantique ===
WATER_PATH = os.path.join(BASE_DIR, 'assets/water/png/water.png')
DEEP_WATER_PATH = os.path.join(BASE_DIR, 'assets/deep_water/png/deep_water_tile.png')
ISLAND_PATH = os.path.join(BASE_DIR, 'assets/island/png/island_tile.png')

ISLAND_TILESET_PATH = os.path.join(BASE_DIR, 'assets/island/png/island_spritesheet.png')
DEEP_WATER_TILESET_PATH = os.path.join(BASE_DIR, 'assets/deep_water/png/deep_water_spritesheet.png')

ISLAND_MAPPING = {
    "corner_top_left": 0,
    "edge_top": 1,
    "coner_top_right": 2,
    "edge_left": 3,
    "center": 4,
    "edge_right": 5,
    "coner_bottom_left": 6,
    "edge_bottom": 7,
    "coner_bottom_right": 8,
    "l-shape_top_left": 9,
    "l-shape_top_right": 10,
    "l-shape_bottom_left": 11,
    "l-shape_bottom_right": 12,
}
WATER_MAPPING = {
    "corner_top_left": 0,
    "edge_top": 1,
    "coner_top_right": 2,
    "edge_left": 3,
    "center": 4,
    "edge_right": 5,
    "coner_bottom_left": 6,
    "edge_bottom": 7,
    "coner_bottom_right": 8,
    "l-shape_top_left": 9,
    "l-shape_top_right": 10,
    "l-shape_bottom_left": 11,
    "l-shape_bottom_right": 12,    
}