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

ISLAND_TILESET_PATH = os.path.join(BASE_DIR, 'assets/island/png/island_spritesheet.png')
DEEP_WATER_TILESET_PATH = os.path.join(BASE_DIR, 'assets/deep_water/png/deep_water_spritesheet.png')
WATER_TILESET_PATH = os.path.join(BASE_DIR, 'assets/water/png/water_spritesheet.png')

ISLAND_MAPPING = {
    "corner_top_left": 0,
    "edge_top": 1,
    "corner_top_right": 2,
    "edge_left": 3,
    "center": 4,
    "edge_right": 5,
    "corner_bottom_left": 6,
    "edge_bottom": 7,
    "corner_bottom_right": 8,
    "l-shape_top_left": 9,
    "l-shape_top_right": 10,
    "l-shape_bottom_left": 11,
    "l-shape_bottom_right": 12,
}
DEEP_WATER_MAPPING = {
    "corner_top_left": 0,
    "edge_top": 1,
    "corner_top_right": 2,
    "edge_left": 3,
    "center": 4,
    "edge_right": 5,
    "corner_bottom_left": 6,
    "edge_bottom": 7,
    "corner_bottom_right": 8,
    "l-shape_top_left": 9,
    "l-shape_top_right": 10,
    "l-shape_bottom_left": 11,
    "l-shape_bottom_right": 12,    
}

MAPPING = {
    "corner_top_left": 0,
    "edge_top": 1,
    "corner_top_right": 2,
    "edge_left": 3,
    "center": 4,
    "edge_right": 5,
    "corner_bottom_left": 6,
    "edge_bottom": 7,
    "corner_bottom_right": 8,
    "l-shape_top_left": 9,
    "l-shape_top_right": 10,
    "l-shape_bottom_left": 11,
    "l-shape_bottom_right": 12,    
}

MASK_MAPPING = {
    # Centre (aucun voisin de transition)
    0: MAPPING["center"],
    
    # Bords simples
    1: MAPPING["edge_top"],        # N
    2: MAPPING["edge_right"],      # E   
    4: MAPPING["edge_bottom"],     # S
    8: MAPPING["edge_left"],       # W
    
    # Coins (deux voisins adjacents)
    1 + 8: MAPPING["corner_top_left"],      # N + W
    1 + 2: MAPPING["corner_top_right"],     # N + E
    2 + 4: MAPPING["corner_bottom_right"],  # E + S
    4 + 8: MAPPING["corner_bottom_left"],   # S + W
    }