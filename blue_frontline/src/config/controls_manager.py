import json
import os
import shutil

import pygame

from .paths import KEYS_PATH
from src.utils.Utils import resource_path

# Cache des contrôles
CONTROLS_KEYS = None


def load_keys(path):
    """Charge le fichier keys.json.

    Args:
        path (str): Chemin vers le fichier keys.json.
    Returns:
        (dict): Dictionnaire des contrôles.
    """
    # Si le fichier n'existe pas, copier le fichier par défaut
    if not os.path.exists(path):
        default_keys_path = resource_path("data/keys.json")
        if os.path.exists(default_keys_path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            shutil.copy(default_keys_path, path)
    
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_pygame_key(key_str):
    """Convertit une chaîne en constante pygame.
    Args:
        key_str (str): Chaîne à convertir.
    Returns:
        (int): Constante pygame.
    """
    if isinstance(key_str, int):
        return key_str
    if isinstance(key_str, str):
        if key_str.startswith("K_") or key_str.startswith("BUTTON_"):
            return getattr(pygame, key_str, key_str)
    return key_str


def load_controls_runtime():
    """Charge et convertit les contrôles.
    Returns:
        (dict): Dictionnaire des contrôles avec touches pygame.
    """
    raw = load_keys(KEYS_PATH)
    return {
        action: {
            "description": data["description"],
            "key": get_pygame_key(data["key"]),
        }
        for action, data in raw.items()
    }


def get_action_key(action):
    """Retourne la touche pygame pour une action.
    Args:
        action (str): Nom de l'action.
    Returns:
        (int): Touche pygame.
    """
    try:
        raw = load_keys(KEYS_PATH)
        data = raw.get(action)
        if data and "key" in data:
            return get_pygame_key(data["key"])
    except Exception as e:
        print(f"Erreur lors du chargement de la touche pour '{action}': {e}")
    return None


def get_controls_keys():
    """Retourne le dictionnaire des contrôles (avec cache).
    Returns:
        (dict): Dictionnaire des contrôles.
    """
    global CONTROLS_KEYS
    if CONTROLS_KEYS is None:
        try:
            CONTROLS_KEYS = load_controls_runtime()
        except Exception as e:
            print(f"Erreur lors du chargement des contrôles: {e}")
            CONTROLS_KEYS = {}
    return CONTROLS_KEYS
