# Fichier des variables globales (Chemin, variables, etc.)
import os
import pygame 

# Chemin du dossier courant
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# === Temps === 
FPS = 60
TIME_STEP = 1000 # en ms => 1 seconde
TIME_SPEED = 1 # Vitesse du temps (1 = normal, 2 = x2, 0.5 = x0.5)

# === MAP ===
MAP_PATH = "map.tmx"
ISLAND_TILESET_PATH = os.path.join(BASE_DIR, 'assets/island/png/island_spritesheet.png')
DEEP_WATER_TILESET_PATH = os.path.join(BASE_DIR, 'assets/deep_water/png/deep_water_spritesheet.png')
WATER_TILESET_PATH = os.path.join(BASE_DIR, 'assets/water/png/water_spritesheet.png')

# === HUD === 
PIECE_IMAGE_PATH = os.path.join(BASE_DIR, 'assets/HUD/piece.png')
PETROLE_IMAGE_PATH = os.path.join(BASE_DIR, 'assets/HUD/petrole.png')

# === EVENEMENTS ===
PETROLE_EVENT = pygame.USEREVENT + 1
TIMER_EVENT = pygame.USEREVENT + 2

# === Ile Quantique ===
WATER_PATH = os.path.join(BASE_DIR, 'assets/water/png/water.png')

# === SONS ===
SOUND = os.path.join(BASE_DIR, 'blue_frontline_sounds/sandy-beach-calm-waves-water-nature-sounds-8052.mp3')
VOLUME_SOUND = 0.5  # Volume du son (0.0 à 1.0)

# Les images de mapping font 512 pixels par 512 pixels
# Chaque tuile fait 32 pixels par 32 pixels
# Nous avons laissé de la place pour d'autres tuiles au cas ou.
# Pour le mapping se referer au fichier "tile_bitmask.xlsx"
MAPPING = {    
    "corner_top_left": 0,
    "edge_top": 1,
    "corner_top_right": 2,
    "end_top": 3,
    "d_shape_top_right": 4,
    "center": 5,
    "corner_top_left_l_shape_bottom_right": 6,
    "corner_top_right_l_shape_bottom_left": 7,
    "missing_corner_top_left": 8,
    "missing_corner_top_right": 9,
    # Passage a la ligne 2
    "edge_left": 16,
    "full" : 17,
    "edge_right": 18,
    "edge_vertical": 19,
    "d_shape_top_left": 20,
    "les_avengers": 21,
    "corner_bottom_left_l_shape_top_right": 22,
    "corner_bottom_right_l_shape_top_left": 23,
    "missing_corner_bottom_left": 24,
    "missing_corner_bottom_right": 25,
    # Passage a la ligne 3
    "corner_bottom_left": 32,
    "edge_bottom": 33,
    "corner_bottom_right": 34,
    "end_bottom": 35,
    "end_left": 36,
    "edge_horizontal": 37,
    "end_right": 38,
    # Passage a la ligne 4
    "l_shape_bottom_right": 48,
    "l_shape_bottom_left": 49,
    "t_shape_right": 50,
    "t_shape_bottom": 51,
    "edge_top_corner_bottom_left": 52,
    "edge_right_corner_top_left": 53,
    "edge_left_corner_top_right": 54,
    "edge_top_corner_bottom_right": 55,
    "edge_left_corner": 56,
    "edge_top_corner": 57,
    # Passage a la ligne 5  
    "l_shape_top_right": 64,
    "l_shape_top_left": 65,
    "t_shape_top": 66,
    "t_shape_left": 67,
    "edge_left_corner_bottom_right": 68,
    "edge_bottom_corner_top_right": 69,
    "edge_bottom_corner_top_left": 70,
    "edge_right_corner_bottom_left": 71,
    "edge_bottom_corner": 72,
    "edge_right_corner": 73,
}

# Utilisation d'un mask binaire pour la séléction de tuiles.
MASK_MAPPING = {
    # Centre (aucun voisin de transition)
    0: MAPPING["full"],
    128 : MAPPING["l_shape_bottom_right"],
    64 : MAPPING["l_shape_bottom_left"],
    64 + 128 : MAPPING["t_shape_bottom"],
    32 : MAPPING["l_shape_top_right"],
    32 + 128 : MAPPING["t_shape_right"],
    32 + 64 : MAPPING["d_shape_top_left"],
    32 + 64 + 128 : MAPPING["missing_corner_bottom_left"],
    16 : MAPPING["l_shape_top_left"],
    16 + 128 : MAPPING["d_shape_top_right"],
    16 + 64 : MAPPING["t_shape_left"],
    16 + 64 + 128 : MAPPING["missing_corner_top_right"],
    16 + 32 : MAPPING["t_shape_top"],
    16 + 32 + 128 : MAPPING["missing_corner_bottom_left"],
    16 + 32 + 64 : MAPPING["missing_corner_bottom_right"],
    16 + 32 + 64 + 128 : MAPPING["les_avengers"],
    8: MAPPING["edge_left"],
    8 + 128 : MAPPING["edge_left_corner_bottom_right"],
    8 + 32 : MAPPING["edge_left_corner_top_right"],
    8 + 32 + 128 : MAPPING["edge_left_corner"],
    4: MAPPING["edge_bottom"],
    4 + 32 : MAPPING["edge_bottom_corner_top_right"],
    4 + 16 : MAPPING["edge_bottom_corner_top_left"],
    4 + 16 + 32 : MAPPING["edge_bottom_corner"],
    4 + 8 : MAPPING["corner_bottom_left"],
    4 + 8 + 32 : MAPPING["corner_bottom_left_l_shape_top_right"],
    2: MAPPING["edge_right"],
    2 + 64 : MAPPING["edge_right_corner_bottom_left"],
    2 + 16 : MAPPING["edge_right_corner_top_left"],
    2 + 16 + 64 : MAPPING["edge_right_corner"],
    2 + 8 : MAPPING["edge_vertical"],
    2 + 4 : MAPPING["corner_bottom_right"],
    2 + 4 + 16 : MAPPING["corner_bottom_right_l_shape_top_left"],
    2 + 4 + 8 : MAPPING["end_bottom"],
    1: MAPPING["edge_top"],
    1 + 128 : MAPPING["edge_top_corner_bottom_right"],
    1 + 64 : MAPPING["edge_top_corner_bottom_left"],
    1 + 64 + 128 : MAPPING["edge_top_corner"],
    1 + 8: MAPPING["corner_top_left"],
    1 + 8 + 128: MAPPING["corner_top_left_l_shape_bottom_right"],
    1 + 4 : MAPPING["edge_horizontal"],
    1 + 4 + 8 : MAPPING["end_left"],
    1 + 2 : MAPPING["corner_top_right"],
    1 + 2 + 64 : MAPPING["corner_top_right_l_shape_bottom_left"],
    1 + 2 + 8 : MAPPING["end_top"],
    1 + 2 + 4 : MAPPING["end_right"],
    1 + 2 + 4 + 8 : MAPPING["center"],
    }

# === Unités ===
RED_TEAM_PATH = os.path.join(BASE_DIR, 'assets/Red_team/png/red_team_spritesheet.png')
GREEN_TEAM_PATH = os.path.join(BASE_DIR, 'assets/Green_team/png/Green_team_spritesheet.png')

# Dictionnaire centralisé contenant toutes les statistiques des unités
UNIT_CONFIGS = {
    "chaloupe": {
        "cost": 20,
        "build_time": 20,
        "max_speed": 80,
        "max_health": 20,
        "range": 2,
        "damage": 2,
        "fire_rate": 1.0,
        "unit_type": "chaloupe",
        "tile_index": {
            "red": 0,    # Index de la tuile pour équipe rouge
            "green": 0   # Index de la tuile pour équipe verte
        },
        "tileset_paths": {
            "red": RED_TEAM_PATH,
            "green": GREEN_TEAM_PATH
        },
        "image_paths": {
            "red": RED_TEAM_PATH,
            "green": GREEN_TEAM_PATH
        },
        "range_color": {
            "red": (255, 0, 0, 50),    # Rouge semi-transparent
            "green": (0, 255, 0, 50)   # Vert semi-transparent
        }
    },
    "bateau": {
        "cost": 60,
        "build_time": 60,
        "max_speed": 70,
        "max_health": 30,
        "range": 6,
        "damage": 6,
        "fire_rate": 1.0,
        "unit_type": "bateau",
        "tile_index": {
            "red": 1,    # Index de la tuile pour équipe rouge
            "green": 1   # Index de la tuile pour équipe verte
        },
        "tileset_paths": {
            "red": RED_TEAM_PATH,
            "green": GREEN_TEAM_PATH
        },
        "image_paths": {
            "red": RED_TEAM_PATH,
            "green": GREEN_TEAM_PATH
        },
        "range_color": {
            "red": (255, 0, 0, 50),
            "green": (0, 255, 0, 50)
        }
    },
    "eclaireur": {
        "cost": 40,
        "build_time": 40,
        "max_speed": 100,
        "max_health": 15,
        "range": 4,
        "damage": 3,
        "fire_rate": 1.5,
        "unit_type": "eclaireur",
        "tile_index": {
            "red": 3,    # Index de la tuile pour équipe rouge
            "green": 3   # Index de la tuile pour équipe verte
        },
        "tileset_paths": {
            "red": RED_TEAM_PATH,
            "green": GREEN_TEAM_PATH
        },
        "image_paths": {
            "red": RED_TEAM_PATH,
            "green": GREEN_TEAM_PATH
        },
        "range_color": {
            "red": (255, 0, 0, 50),
            "green": (0, 255, 0, 50)
        }
    },
    "paquebot": {
        "cost": 120,
        "build_time": 120,
        "max_speed": 60,
        "max_health": 50,
        "range": 8,
        "damage": 10,
        "fire_rate": 0.8,
        "unit_type": "paquebot",
        "tile_index": {
            "red": 2,    # Index de la tuile pour équipe rouge
            "green": 2   # Index de la tuile pour équipe verte
        },
        "tileset_paths": {
            "red": RED_TEAM_PATH,
            "green": GREEN_TEAM_PATH
        },
        "image_paths": {
            "red": RED_TEAM_PATH,
            "green": GREEN_TEAM_PATH
        },
        "range_color": {
            "red": (255, 0, 0, 50),
            "green": (0, 255, 0, 50)
        }
    },
    "sousmarin": {
        "cost": 180,
        "build_time": 180,
        "max_speed": 65,
        "max_health": 35,
        "range": 5,
        "damage": 18,
        "fire_rate": 0.5,
        "unit_type": "sousmarin",
        "special_ability": "mines",  # Capacité spéciale
        "tile_index": {
            "red": 4,    # Index de la tuile pour équipe rouge
            "green": 4   # Index de la tuile pour équipe verte
        },
        "tileset_paths": {
            "red": RED_TEAM_PATH,
            "green": GREEN_TEAM_PATH
        },
        "image_paths": {
            "red": RED_TEAM_PATH,
            "green": GREEN_TEAM_PATH
        },
        "range_color": {
            "red": (255, 0, 0, 50),
            "green": (0, 255, 0, 50)
        }
    }
}


# === Couleurs marines et interface ===
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
BLUE = (0, 120, 215)
OCEAN_BLUE = (0, 70, 140)
LIGHT_BLUE = (0, 150, 255)
WAVE_COLOR = (173, 216, 230)

# === Boutons menu ===
BUTTON_WIDTH = 300
BUTTON_HEIGHT = 70
BUTTON_SPACING = 20
BUTTON_BORDER_RADIUS = 15
BUTTON_MARGIN_LEFT = 40
BUTTON_MARGIN_BOTTOM = 40

