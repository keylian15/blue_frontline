import os

from src.utils.Utils import resource_path, user_data_path

# Chemin de base
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# === Données utilisateur ===
ACHIVEMENTS_PATH = user_data_path("achievements.json")
SETTINGS_PATH = user_data_path("gameplay_settings.json")
KEYS_PATH = user_data_path("keys.json")

# === Map ===
MAP_PATH = resource_path("src/utils/map.tmx")

# === Tilesets ===
ISLAND_TILESET_PATH = resource_path("assets/island/png/island_spritesheet.png")
DEEP_WATER_TILESET_PATH = resource_path("assets/deep_water/png/deep_water_spritesheet.png")
WATER_TILESET_PATH = resource_path("assets/water/png/water_spritesheet.png")
WATER_PATH = resource_path("assets/water/png/water.png")

# === HUD ===
PIECE_IMAGE_PATH = resource_path("assets/HUD/piece.png")
PETROLE_IMAGE_PATH = resource_path("assets/HUD/petrole.png")
MAREE_HAUTE_IMAGE_PATH = resource_path("assets/HUD/maree_haute.png")
MAREE_BASSE_IMAGE_PATH = resource_path("assets/HUD/maree_basse.png")

# === Effets ===
EXPLOSION_IMAGE_PATH = resource_path("assets/miscellaneous/png/explosion.png")

# === Équipes ===
RED_TEAM_PATH = resource_path("assets/Red_team/png/red_team_spritesheet.png")
GREEN_TEAM_PATH = resource_path("assets/Green_team/png/Green_team_spritesheet.png")
RED_TEAM_PATH_BIG = resource_path("assets/Red_team/png/red_team_spritesheet_big.png")
GREEN_TEAM_PATH_BIG = resource_path("assets/Green_team/png/Green_team_spritesheet_big.png")

# === Bases ===
RED_BASE_TEAM_PATH = resource_path("assets/Red_team/png/red_base.png")
GREEN_BASE_TEAM_PATH = resource_path("assets/Green_team/png/Green_base.png")

# === Menu ===
MENU_PATH = resource_path("assets/menu/menu.png")
ANCHOR_PATH = resource_path("assets/menu/NotoV1Anchor.png")
LOGO_PATH = resource_path("assets/logo/png/logo.png")
