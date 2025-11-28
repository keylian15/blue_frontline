import json
import os
import shutil

from .paths import SETTINGS_PATH
from src.utils.Utils import resource_path

# Variables globales en cache
GAMEPLAY_SETTINGS = None
TIME_MAREE = None
OIL_PER_SECOND = None
PIECE_PER_KILL = None


def load_gameplay_settings():
    """Charge les settings depuis le JSON au lancement."""
    global GAMEPLAY_SETTINGS, TIME_MAREE, OIL_PER_SECOND, PIECE_PER_KILL

    # Si le fichier n'existe pas, copier le fichier par défaut
    if not os.path.exists(SETTINGS_PATH):
        default_settings_path = resource_path("data/gameplay_settings.json")
        if os.path.exists(default_settings_path):
            os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
            shutil.copy(default_settings_path, SETTINGS_PATH)

    with open(SETTINGS_PATH) as f:
        GAMEPLAY_SETTINGS = json.load(f)

    # Mise en cache
    TIME_MAREE = GAMEPLAY_SETTINGS["TIME_MAREE"]
    OIL_PER_SECOND = GAMEPLAY_SETTINGS["OIL_PER_SECOND"]
    PIECE_PER_KILL = GAMEPLAY_SETTINGS["PIECE_PER_KILL"]


def get_gameplay_settings():
    """Retourne les settings actuels.
    Returns:
        (dict): Dictionnaire des settings.
    """
    return GAMEPLAY_SETTINGS


def set_gameplay_setting(new_settings):
    """Met à jour les settings et sauvegarde.
    Args:
        new_settings (dict): Nouveau dictionnaire des settings.
    """
    global GAMEPLAY_SETTINGS, TIME_MAREE, OIL_PER_SECOND, PIECE_PER_KILL

    GAMEPLAY_SETTINGS = new_settings

    # Mise à jour du cache
    TIME_MAREE = GAMEPLAY_SETTINGS["TIME_MAREE"]
    OIL_PER_SECOND = GAMEPLAY_SETTINGS["OIL_PER_SECOND"]
    PIECE_PER_KILL = GAMEPLAY_SETTINGS["PIECE_PER_KILL"]

    # Sauvegarde
    with open(SETTINGS_PATH, "w") as f:
        json.dump(GAMEPLAY_SETTINGS, f, indent=4)
