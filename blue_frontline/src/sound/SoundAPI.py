# Class/SoundAPI.py
import pygame
from Sound import SpatialAudioManager
from src.config.audio import get_audio_settings


class Sound:
    """
    API publique simple pour piloter l'audio depuis le jeu.
    Toute la logique est implémentée dans SpatialAudioManager.
    """

    def __init__(self, game):
        self._engine = SpatialAudioManager(game)

    # --- boucle par frame ---
    def update(self):
        self._engine.update()

    # --- volume maître ---
    def increase_master_volume(self):
        self._engine.adjust_master_volume(+1)

    def decrease_master_volume(self):
        self._engine.adjust_master_volume(-1)

    def set_master_volume(self, value_0_1: float):
        self._engine.set_master_volume(value_0_1)

    def get_master_volume(self) -> float:
        return self._engine.get_master_volume()

    # --- événements de gameplay (one-shots) ---
    def on_unit_dropped(self, unit_class_name: str, pos=None):
        self._engine.play_drop_for_unit(unit_class_name, pos=pos)

    def on_eclaireur_dropped(self, pos):
        self._engine.play_one_shot_named("DROP_ECLAIREURS", world_pos=pos)

    def on_mine_dropped(self, pos):
        self._engine.play_one_shot_named("DROP_MINE", world_pos=pos)

    def on_mine_explosion(self, pos):
        self._engine.play_one_shot_named("EXPLOSION_MINE", world_pos=pos)

    def on_coin_drop(self, pos):
        self._engine.play_one_shot_named("DROP_COIN", world_pos=pos)

    def on_unit_shot(self, unit_class_name: str, pos=None):
        """À appeler quand une unité tire."""
        self._engine.play_shot_for_unit(unit_class_name, pos=pos)

    def on_victory(self):
        self._engine.play_victory()

    def on_defeat(self):
        self._engine.play_defeat()

    # --- îles quantiques ---
    def set_quantum_islands(self, centers):
        self._engine.set_quantum_islands(centers)

    # --- configuration audio ---
    def set_vertical_attenuation(self, range_float: float):
        try:
            self._engine.vertical_attenuation_range = float(range_float)
        except Exception:
            pass

    def enable_audio_debug(self, flag: bool = True):
        try:
            self._engine.debug_audio = bool(flag)
        except Exception:
            pass

    # Alias rétro-compatibles pour EventHandler
    def increase_volume(self):
        self._engine.adjust_master_volume(+1)

    def decrease_volume(self):
        self._engine.adjust_master_volume(-1)

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