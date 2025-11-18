# Fichier des variables globales (Chemin, variables, etc.)
import json
import os
import pygame
from Utils import resource_path, user_data_path

# Chemin du dossier courant
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# === Temps ===
FPS = 60
TIME_STEP = 1000  # en ms => 1 seconde
TIME_MAREE = 180

# === Économie ===
PIECE_PER_KILL = 1
OIL_PER_SECOND = 1

# === Achivements ===
ACHIVEMENTS_PATH = user_data_path("data/achievements.json")

# Vitesses de temps disponibles
TIME_SPEEDS = [1, 2, 4, 8, 10, 20, 0.5]

# === MAP ===
MAP_PATH = resource_path("map.tmx")
ISLAND_TILESET_PATH = resource_path('assets/island/png/island_spritesheet.png')
DEEP_WATER_TILESET_PATH = resource_path(
    'assets/deep_water/png/deep_water_spritesheet.png')
WATER_TILESET_PATH = resource_path('assets/water/png/water_spritesheet.png')

# === HUD ===
PIECE_IMAGE_PATH = resource_path('assets/HUD/piece.png')
PETROLE_IMAGE_PATH = resource_path('assets/HUD/petrole.png')
MAREE_HAUTE_IMAGE_PATH = resource_path('assets/HUD/maree_haute.png')
MAREE_BASSE_IMAGE_PATH = resource_path('assets/HUD/maree_basse.png')

# === EXPLOSIONS ===
EXPLOSION_IMAGE_PATH = resource_path('assets/miscellaneous/png/explosion.png')

# === EVENEMENTS ===
PETROLE_EVENT = pygame.USEREVENT + 1
TIMER_EVENT = pygame.USEREVENT + 2

# === Ile Quantique ===
WATER_PATH = resource_path('assets/water/png/water.png')

# === SONS – système historique ===
# (on remet SOUND sur la musique du jeu pour compatibilité éventuelle)
SOUND = resource_path('blue_frontline_sounds/son_jeu.mp3')
VOLUME_SOUND = 0.5  # Volume du son (0.0 à 1.0)
MASTER_VOL_DEFAULT = 0.5
MASTER_VOL_MAX = 1.0
MASTER_VOL_MIN = 0.0
MASTER_VOL_STEP = 0.1

# === SONS – nouveau système spatial ===
# Musique / beds / one-shots / drops (tout en .mp3)
MUSIC_GAME = resource_path(
    'blue_frontline_sounds/son_jeu.mp3')             # musique de fond
# ambiance îles "normales" (bed)
ISLAND_BED = resource_path('blue_frontline_sounds/son_iles.mp3')
# ambiance mer (bed)
SEA_BED = resource_path('blue_frontline_sounds/sea-waves-169411.mp3')
# son court base (one-shot ~3s)
BASE_BED = resource_path('blue_frontline_sounds/son_base.mp3')
APPARITION_QUANTIQUE = resource_path(
    'blue_frontline_sounds/apparition_ile_quantique.mp3')
DROP_MINE = resource_path('blue_frontline_sounds/drop_mine.mp3')
DROP_COIN = resource_path('blue_frontline_sounds/drop_coin.mp3')
EXPLOSION_MINE = resource_path('blue_frontline_sounds/explosion_mine.mp3')
DROP_ECLAIREURS = resource_path('blue_frontline_sounds/drop_eclaireurs.mp3')

# Drops unités
# (nom d'origine conservé)
DROP_CHALOUPe = resource_path('blue_frontline_sounds/drop_chaloupe.mp3')
# alias propre, pour compatibilité
DROP_CHALOUPE = DROP_CHALOUPe
DROP_BATEAU = resource_path('blue_frontline_sounds/drop_bateau.mp3')
DROP_PAQUEBOT = resource_path('blue_frontline_sounds/drop_paquebot.mp3')
DROP_SOUSMARIN = resource_path('blue_frontline_sounds/drop_sous_marin.mp3')

# Volumes (0.0–1.0)
# volume nominal de la musique (capé par la règle zoom -> 0)
VOL_MUSIC = VOLUME_SOUND
VOL_ISLAND = 0.8
VOL_BASE = 0.8
VOL_SEA = 0.2
VOL_DROPS = 0.8

# === MIXAGE CONTEXTUEL / COMPORTEMENTS ===
# La musique est gérée dans Sound.py pour faire : 0% zoom -> 90% ; 100% zoom -> 0%
# part de mer qui reste quand on est sur une île/base (0.0 = coupée)
SEA_ON_ISLAND_FACTOR = 0.0
# "linear" ou "smooth" (smoothstep) pour la montée/descente de focus
ISLAND_BASE_CURVE = "smooth"

# Zones d'influence (agrandies)
FOCUS_RADIUS_MULT = 1.6     # >1.0 = la "bulle" d'influence des ÎLES est plus large
BASE_FOCUS_RADIUS_MULT = 1.6     # idem pour les BASES

# Déclenchement du one-shot de BASE
# 0..1 : seuil de focus où on déclenche le son de base
BASE_TRIGGER_THRESHOLD = 0.5
BASE_COOLDOWN_MS = 2500    # anti-spam : temps mini entre 2 déclenchements
BASE_ONE_SHOT_VOL = 0.9     # volume de base pour le one-shot (avant pan)

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
    "full": 17,
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
    # Passage a la ligne 6, modification des fulls, full 0 est celui de base
    "full_1": 80,
    "full_2": 81,
    
}

# Utilisation d'un mask binaire pour la séléction de tuiles.
MASK_MAPPING = {
    # Centre (aucun voisin de transition)
    0: MAPPING["full"],
    128: MAPPING["l_shape_bottom_right"],
    64: MAPPING["l_shape_bottom_left"],
    64 + 128: MAPPING["t_shape_bottom"],
    32: MAPPING["l_shape_top_right"],
    32 + 128: MAPPING["t_shape_right"],
    32 + 64: MAPPING["d_shape_top_left"],
    32 + 64 + 128: MAPPING["missing_corner_top_left"],
    16: MAPPING["l_shape_top_left"],
    16 + 128: MAPPING["d_shape_top_right"],
    16 + 64: MAPPING["t_shape_left"],
    16 + 64 + 128: MAPPING["missing_corner_top_right"],
    16 + 32: MAPPING["t_shape_top"],
    16 + 32 + 128: MAPPING["missing_corner_bottom_left"],
    16 + 32 + 64: MAPPING["missing_corner_bottom_right"],
    16 + 32 + 64 + 128: MAPPING["les_avengers"],
    8: MAPPING["edge_left"],
    8 + 128: MAPPING["edge_left_corner_bottom_right"],
    8 + 32: MAPPING["edge_left_corner_top_right"],
    8 + 32 + 128: MAPPING["edge_left_corner"],
    4: MAPPING["edge_bottom"],
    4 + 32: MAPPING["edge_bottom_corner_top_right"],
    4 + 16: MAPPING["edge_bottom_corner_top_left"],
    4 + 16 + 32: MAPPING["edge_bottom_corner"],
    4 + 8: MAPPING["corner_bottom_left"],
    4 + 8 + 32: MAPPING["corner_bottom_left_l_shape_top_right"],
    2: MAPPING["edge_right"],
    2 + 64: MAPPING["edge_right_corner_bottom_left"],
    2 + 16: MAPPING["edge_right_corner_top_left"],
    2 + 16 + 64: MAPPING["edge_right_corner"],
    2 + 8: MAPPING["edge_vertical"],
    2 + 4: MAPPING["corner_bottom_right"],
    2 + 4 + 16: MAPPING["corner_bottom_right_l_shape_top_left"],
    2 + 4 + 8: MAPPING["end_bottom"],
    1: MAPPING["edge_top"],
    1 + 128: MAPPING["edge_top_corner_bottom_right"],
    1 + 64: MAPPING["edge_top_corner_bottom_left"],
    1 + 64 + 128: MAPPING["edge_top_corner"],
    1 + 8: MAPPING["corner_top_left"],
    1 + 8 + 128: MAPPING["corner_top_left_l_shape_bottom_right"],
    1 + 4: MAPPING["edge_horizontal"],
    1 + 4 + 8: MAPPING["end_left"],
    1 + 2: MAPPING["corner_top_right"],
    1 + 2 + 64: MAPPING["corner_top_right_l_shape_bottom_left"],
    1 + 2 + 8: MAPPING["end_top"],
    1 + 2 + 4: MAPPING["end_right"],
    1 + 2 + 4 + 8: MAPPING["center"],
}

# === Unités ===

RED_TEAM_PATH = resource_path('assets/Red_team/png/red_team_spritesheet.png')
GREEN_TEAM_PATH = resource_path(
    'assets/Green_team/png/Green_team_spritesheet.png')

# === BASE ===
RED_BASE_TEAM_PATH = resource_path('assets/Red_team/png/red_base.png')
GREEN_BASE_TEAM_PATH = resource_path('assets/Green_team/png/Green_base.png')

# Dictionnaire centralisé contenant toutes les statistiques des unités
UNIT_CONFIGS = {
    "chaloupe": {
        "cost": 20,
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
        "max_speed": 100,
        "max_health": 15,
        "range": 0,
        "damage": 0,
        "fire_rate": 0,
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
        "max_speed": 65,
        "max_health": 35,
        "range": 0,
        "damage": 12,
        "fire_rate": 1,
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
    },
    "pompe_petroliere": {
        "cost": 500,
        "max_speed": 0,
        "max_health": 100,
        "range": 0,
        "damage": 0,
        "fire_rate": 1,
        "unit_type": "pompe_petroliere",
        "tile_index": {
            "red": 6,    # Index de la tuile pour équipe rouge
            "green": 6   # Index de la tuile pour équipe verte
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

# === IMAGES ===
MENU_PATH = resource_path('assets/menu/menu.png')
ANCHOR_PATH = resource_path('assets/menu/NotoV1Anchor.png')

# === Contrôles du jeu ===
# Utilisation de user_data_path comme pour les achievements
KEYS_PATH = user_data_path("data/keys.json")


def load_keys(path):
    """Charge le fichier keys.json depuis le chemin donné."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_pygame_key(key_str):
    """Convertit la chaîne en constante pygame (ex: "K_e" -> pygame.K_e) ou retourne directement si c'est déjà un entier"""
    # Si c'est déjà un entier (constante pygame), le retourner directement
    if isinstance(key_str, int):
        return key_str
    # Si c'est une chaîne, la convertir
    if isinstance(key_str, str):
        if key_str.startswith("K_"):
            return getattr(pygame, key_str)
        if key_str.startswith("BUTTON_"):
            return getattr(pygame, key_str)
    return key_str  # Pour les boutons souris ou autres


def load_controls_runtime():
    """Charge les contrôles depuis keys.json à chaque appel et retourne un dict
    avec les valeurs des touches converties en constantes pygame."""
    raw = load_keys(KEYS_PATH)
    return {
        action: {
            "description": data["description"],
            "key": get_pygame_key(data["key"]),
        }
        for action, data in raw.items()
    }


def get_action_key(action):
    """Retourne la valeur pygame de la touche pour une action en lisant keys.json.
    En cas d'erreur, retourne None."""
    try:
        raw = load_keys(KEYS_PATH)
        data = raw.get(action)
        if data and "key" in data:
            return get_pygame_key(data["key"])
    except Exception as e:
        print(f"Erreur lors du chargement de la touche pour '{action}': {e}")
        return None


# Variable CONTROLS_KEYS - initialisée à None, sera chargée au premier appel
CONTROLS_KEYS = None


def get_controls_keys():
    """Retourne le dictionnaire CONTROLS_KEYS, en le chargeant si nécessaire."""
    global CONTROLS_KEYS
    if CONTROLS_KEYS is None:
        try:
            CONTROLS_KEYS = load_controls_runtime()
        except Exception as e:
            print(f"Erreur lors du chargement des contrôles: {e}")
            CONTROLS_KEYS = {}
    return CONTROLS_KEYS


GAMEPLAY_SETTINGS = {
    "AI_ACTIVATION": {
        "BaseRouge": True,
        "BaseVerte": True,
        "ChaloupeRouge": True,
        "ChaloupeVerte": True,
        "BateauRouge": True,
        "BateauVert": True,
        "PaquebotRouge": True,
        "PaquebotVert": True,
        "EclaireurRouge": True,
        "EclaireurVert": True,
        "SousmarinRouge": True,
        "SousmarinVert": True,
    },
    "TIME_MAREE": TIME_MAREE,
    "OIL_PER_SECOND": OIL_PER_SECOND,
    "PIECE_PER_KILL": PIECE_PER_KILL
}


def get_gameplay_settings():
    return GAMEPLAY_SETTINGS


def set_gameplay_setting(dico_settings):
    global GAMEPLAY_SETTINGS, TIME_MAREE, OIL_PER_SECOND, PIECE_PER_KILL

    GAMEPLAY_SETTINGS = dico_settings
    TIME_MAREE = dico_settings["TIME_MAREE"]
    OIL_PER_SECOND = dico_settings["OIL_PER_SECOND"]
    PIECE_PER_KILL = dico_settings["PIECE_PER_KILL"]
