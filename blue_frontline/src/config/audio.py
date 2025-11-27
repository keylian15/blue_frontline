from .paths import resource_path

# === Volume principal ===
VOLUME_SOUND = 0.5
MASTER_VOL_DEFAULT = 0.5
MASTER_VOL_MAX = 1.0
MASTER_VOL_MIN = 0.0
MASTER_VOL_STEP = 0.1

# === Musiques et ambiances ===
MUSIC_GAME = resource_path("sounds/son_jeu.mp3")
ISLAND_BED = resource_path("sounds/son_iles.mp3")
SEA_BED = resource_path("sounds/sea-waves-169411.mp3")
BASE_BED = resource_path("sounds/son_base.mp3")
APPARITION_QUANTIQUE = resource_path("sounds/apparition_ile_quantique.mp3")

# === Sons d'actions ===
DROP_MINE = resource_path("sounds/drop_mine.mp3")
DROP_COIN = resource_path("sounds/drop_coin.mp3")
EXPLOSION_MINE = resource_path("sounds/explosion_mine.mp3")
DROP_ECLAIREURS = resource_path("sounds/drop_eclaireurs.mp3")

# === Sons d'unités ===
DROP_CHALOUPE = resource_path("sounds/drop_chaloupe.mp3")
DROP_BATEAU = resource_path("sounds/drop_bateau.mp3")
DROP_PAQUEBOT = resource_path("sounds/drop_paquebot.mp3")
DROP_SOUSMARIN = resource_path("sounds/drop_sous_marin.mp3")

# === Volumes par catégorie ===
VOL_MUSIC = VOLUME_SOUND
VOL_ISLAND = 0.8
VOL_BASE = 0.8
VOL_SEA = 0.2
VOL_DROPS = 0.8

# === Mixage contextuel ===
SEA_ON_ISLAND_FACTOR = 0.0
ISLAND_BASE_CURVE = "smooth"  # "linear" ou "smooth"

# Zones d'influence
FOCUS_RADIUS_MULT = 1.6
BASE_FOCUS_RADIUS_MULT = 1.6

# Déclenchement base
BASE_TRIGGER_THRESHOLD = 0.5
BASE_COOLDOWN_MS = 2500
BASE_ONE_SHOT_VOL = 0.9

# === PARAMÈTRES AUDIO pour OptionsMenu.py ============
AUDIO_SETTINGS = {
    "VOLUME": MASTER_VOL_DEFAULT,  # Volume global (0.0 → 1.0)
    "SOUND_ENABLED": True,  # ON/OFF globale du son
    "MUSIC_ENABLED": True,  # ON/OFF musique de fond uniquement
}


def get_audio_settings():
    """Retourne le dictionnaire centralisé des paramètres audio."""
    return AUDIO_SETTINGS
