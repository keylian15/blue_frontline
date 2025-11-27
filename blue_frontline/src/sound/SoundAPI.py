# Class/SoundAPI.py
# import pygame
# from src.sound.Sound import SpatialAudioManager
from src.config.audio import get_audio_settings


# ===================================================================
# === FONCTIONS GLOBALES DU MODULE POUR LE MENU OPTIONS (CORRIGÉ) ===
# ===================================================================

_current_audio_manager = None


def register_audio_manager(manager):
    """
    Enregistre l'instance globale du gestionnaire audio pour le menu Options.
    """
    global _current_audio_manager
    _current_audio_manager = manager
    print("[SoundAPI] Gestionnaire audio enregistré :", manager)


def apply_audio_settings_from_global():
    """
    Lit Global.AUDIO_SETTINGS et applique :
      - volume maître
      - mute global
      - mute musique
    """
    global _current_audio_manager
    if _current_audio_manager is None:
        print("[SoundAPI] Aucun manager audio trouvé.")
        return

    settings = get_audio_settings()

    volume = settings.get("VOLUME", 0.5)
    sound_enabled = settings.get("SOUND_ENABLED", True)
    music_enabled = settings.get("MUSIC_ENABLED", True)

    # Ces trois méthodes doivent exister dans Sound.py
    if hasattr(_current_audio_manager, "set_master_volume"):
        _current_audio_manager.set_master_volume(volume)

    if hasattr(_current_audio_manager, "set_global_mute"):
        _current_audio_manager.set_global_mute(not sound_enabled)

    if hasattr(_current_audio_manager, "set_music_mute"):
        _current_audio_manager.set_music_mute(not music_enabled)

    print("[SoundAPI] Paramètres audio appliqués :", settings)