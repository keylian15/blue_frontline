import json

import pygame

from .paths import KEYS_PATH

# Cache des contrôles
CONTROLS_KEYS = None


def load_keys(path):
    """Charge le fichier keys.json."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_pygame_key(key_str):
    """Convertit une chaîne en constante pygame."""
    if isinstance(key_str, int):
        return key_str
    if isinstance(key_str, str):
        if key_str.startswith("K_") or key_str.startswith("BUTTON_"):
            return getattr(pygame, key_str, key_str)
    return key_str


def load_controls_runtime():
    """Charge et convertit les contrôles."""
    raw = load_keys(KEYS_PATH)
    return {
        action: {
            "description": data["description"],
            "key": get_pygame_key(data["key"]),
        }
        for action, data in raw.items()
    }


def get_action_key(action):
    """Retourne la touche pygame pour une action."""
    try:
        raw = load_keys(KEYS_PATH)
        data = raw.get(action)
        if data and "key" in data:
            return get_pygame_key(data["key"])
    except Exception as e:
        print(f"Erreur lors du chargement de la touche pour '{action}': {e}")
    return None


def get_controls_keys():
    """Retourne le dictionnaire des contrôles (avec cache)."""
    global CONTROLS_KEYS
    if CONTROLS_KEYS is None:
        try:
            CONTROLS_KEYS = load_controls_runtime()
        except Exception as e:
            print(f"Erreur lors du chargement des contrôles: {e}")
            CONTROLS_KEYS = {}
    return CONTROLS_KEYS
