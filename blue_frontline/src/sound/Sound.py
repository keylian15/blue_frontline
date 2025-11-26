# Class/Sound.py
from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame
from src.config.audio import (
    APPARITION_QUANTIQUE,
    BASE_BED,
    BASE_COOLDOWN_MS,
    BASE_FOCUS_RADIUS_MULT,
    BASE_ONE_SHOT_VOL,
    BASE_TRIGGER_THRESHOLD,
    DROP_BATEAU,
    DROP_CHALOUPE,
    DROP_COIN,
    DROP_ECLAIREURS,
    DROP_MINE,
    DROP_PAQUEBOT,
    DROP_SOUSMARIN,
    EXPLOSION_MINE,
    FOCUS_RADIUS_MULT,
    ISLAND_BASE_CURVE,
    ISLAND_BED,
    MASTER_VOL_DEFAULT,
    MASTER_VOL_MAX,
    MASTER_VOL_MIN,
    MASTER_VOL_STEP,
    MUSIC_GAME,
    SEA_BED,
    SEA_ON_ISLAND_FACTOR,
    VOL_DROPS,
    VOL_ISLAND,
    VOL_MUSIC,
    VOL_SEA,
)
from src.utils.Utils import resource_path

if TYPE_CHECKING:
    from src.core.Game import Game


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def lerp(a, b, t):
    return a + (b - a) * clamp(t, 0.0, 1.0)


def smoothstep(x):
    x = clamp(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


# Vertical attenuation default range (1.0 = full falloff to screen edge)
DEFAULT_VERTICAL_ATTEN_RANGE = 1.0


class SpatialAudioManager:
    """
    Moteur audio:
      - volume maître (increase/decrease)
      - musique de fond (duck vs zoom réel)
      - beds: îles (spatial), mer (crossfade)
      - base: one-shot à l'entrée de zone (cooldown)
      - îles quantiques: one-shot d’apparition
      - drops: unités + événements (mine, coin, explosion, éclaireurs)
      - tirs: chaloupe / bateau / paquebot
      - victoire / défaite / klaxon de bateau
    """

    def __init__(self, game: Game):
        self.game = game

        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        self._load_sounds()

        # --- volume maître (0..1) ---
        self._master = clamp(MASTER_VOL_DEFAULT, MASTER_VOL_MIN, MASTER_VOL_MAX)

        # musique de fond
        try:
            pygame.mixer.music.load(MUSIC_GAME)
            pygame.mixer.music.set_volume(clamp(VOL_MUSIC * self._master, 0.0, 1.0))
            pygame.mixer.music.play(-1)
        except Exception:
            pass

        # canaux dédiés
        self.chan_island = pygame.mixer.Channel(1)
        self.chan_sea = pygame.mixer.Channel(2)
        self.chan_base = pygame.mixer.Channel(3)  # one-shot base
        self.chan_fx = pygame.mixer.Channel(4)  # one-shots gameplay (tir, drop, etc.)

        # états
        self.static_islands = None
        self.quantum_islands = []
        self._last_base_trigger_time = 0

        # paramètres d'audio locaux
        self.vertical_attenuation_range = DEFAULT_VERTICAL_ATTEN_RANGE
        self.debug_audio = False

        # init des beds
        self._ensure_beds_started()

        # init détection d'îles statiques
        self._init_static_islands_from_tmx()

    # ---- API volume maître ----
    def set_master_volume(self, value_0_1: float):
        self._master = clamp(value_0_1, MASTER_VOL_MIN, MASTER_VOL_MAX)
        # l'update() recalcule à chaque frame; nudge pour prise en compte immédiate:
        cur = pygame.mixer.music.get_volume()
        pygame.mixer.music.set_volume(clamp(cur, 0.0, 1.0))

    def adjust_master_volume(self, direction: int):
        """direction: +1 (increase) / -1 (decrease)"""
        step = MASTER_VOL_STEP * (1 if direction >= 0 else -1)
        self.set_master_volume(self._master + step)

    def get_master_volume(self) -> float:
        return self._master

    # ---- chargement sons ----
    def _load_sounds(self):
        # beds
        try:
            self.sfx_island = pygame.mixer.Sound(ISLAND_BED)
        except Exception:
            self.sfx_island = None
        try:
            self.sfx_sea = pygame.mixer.Sound(SEA_BED)
        except Exception:
            self.sfx_sea = None
        try:
            self.sfx_base = pygame.mixer.Sound(BASE_BED)
        except Exception:
            self.sfx_base = None
        try:
            self.sfx_quantum = pygame.mixer.Sound(APPARITION_QUANTIQUE)
        except Exception:
            self.sfx_quantum = None

        # drops
        self.sfx_drop = {}

        def _safe_load(name, path):
            try:
                self.sfx_drop[name] = pygame.mixer.Sound(path)
            except Exception:
                self.sfx_drop[name] = None

        _safe_load("chaloupe", DROP_CHALOUPE)
        _safe_load("bateau", DROP_BATEAU)
        _safe_load("paquebot", DROP_PAQUEBOT)
        _safe_load("sousmarin", DROP_SOUSMARIN)
        _safe_load("DROP_MINE", DROP_MINE)
        _safe_load("DROP_COIN", DROP_COIN)
        _safe_load("EXPLOSION_MINE", EXPLOSION_MINE)
        _safe_load("DROP_ECLAIREURS", DROP_ECLAIREURS)

        # tirs (tir_chaloupe / tir_bateau / tir_paquebot)
        self.sfx_shot = {}

        def _safe_load_shot(key, filename):
            try:
                path = resource_path(f"blue_frontline_sounds/{filename}")
                self.sfx_shot[key] = pygame.mixer.Sound(path)
            except Exception:
                self.sfx_shot[key] = None

        _safe_load_shot("chaloupe", "tir_chaloupe.mp3")
        _safe_load_shot("bateau", "tir_bateau.mp3")
        _safe_load_shot("paquebot", "tir_paquebot.mp3")

        # victoire / défaite
        try:
            self.sfx_victory = pygame.mixer.Sound(resource_path("blue_frontline_sounds/victoire.mp3"))
        except Exception:
            self.sfx_victory = None

        try:
            self.sfx_defeat = pygame.mixer.Sound(resource_path("blue_frontline_sounds/son_defaite.mp3"))
        except Exception:
            self.sfx_defeat = None

        # klaxon / corne de bateau
        try:
            self.sfx_horn = pygame.mixer.Sound(
                resource_path("blue_frontline_sounds/staten-island-ferry-horn-close-85120.mp3")
            )
        except Exception:
            self.sfx_horn = None

    def _ensure_beds_started(self):
        if self.sfx_island and not self.chan_island.get_busy():
            self.chan_island.play(self.sfx_island, loops=-1)
            self.chan_island.set_volume(0, 0)
        if self.sfx_sea and not self.chan_sea.get_busy():
            self.chan_sea.play(self.sfx_sea, loops=-1)
            self.chan_sea.set_volume(0, 0)

    # --- îles statiques depuis TMX ---
    def _init_static_islands_from_tmx(self):
        tmx = self.game.tmx_data
        centers = []

        for obj in getattr(tmx, "objects", []):
            n = getattr(obj, "name", "")
            t = getattr(obj, "type", "")
            if n == "Collision" or t == "Collision":
                cx = obj.x + (getattr(obj, "width", 0) or 0) / 2
                cy = obj.y + (getattr(obj, "height", 0) or 0) / 2
                centers.append((cx, cy))

        for layer in getattr(tmx, "layers", []):
            lname = getattr(layer, "name", "")
            if lname in ("Collision_Basse", "Collision_Haute"):
                for obj in layer:
                    n = getattr(obj, "name", "")
                    t = getattr(obj, "type", "")
                    if n == "Collision" or t == "Collision":
                        cx = obj.x + (getattr(obj, "width", 0) or 0) / 2
                        cy = obj.y + (getattr(obj, "height", 0) or 0) / 2
                        centers.append((cx, cy))

        if not centers:
            try:
                mw, mh = self.game.map_width, self.game.map_height
                centers = [(mw / 2, mh / 2)]
            except Exception:
                centers = [(0, 0)]
        self.static_islands = centers

    # --- API interne (déclenchées par l'API publique) ---
    def set_quantum_islands(self, centers):
        had = len(self.quantum_islands) > 0
        self.quantum_islands = list(centers or [])
        have_now = len(self.quantum_islands) > 0
        if not had and have_now and self.sfx_quantum:
            self.chan_fx.play(self.sfx_quantum)

    def play_drop_for_unit(self, unit_class_name: str, pos=None):
        key = None
        low = (unit_class_name or "").lower()
        if "chaloupe" in low:
            key = "chaloupe"
        elif "paquebot" in low:
            key = "paquebot"
        elif "sous" in low:
            key = "sousmarin"
        elif "eclaireur" in low:
            self.play_one_shot_named("DROP_ECLAIREURS", world_pos=pos)
            return
        else:
            key = "bateau"
        sfx = self.sfx_drop.get(key)
        if sfx:
            self._play_spatial_one_shot(sfx, world_pos=pos, base_vol=VOL_DROPS)

    def play_one_shot_named(self, const_name: str, world_pos=None):
        sfx = self.sfx_drop.get(const_name)
        if sfx:
            self._play_spatial_one_shot(sfx, world_pos=world_pos, base_vol=VOL_DROPS)

    def play_shot_for_unit(self, unit_class_name: str, pos=None):
        """
        Joue le son de tir associé à l'unité (chaloupe / bateau / paquebot).
        """
        low = (unit_class_name or "").lower()
        if "chaloupe" in low:
            key = "chaloupe"
        elif "paquebot" in low:
            key = "paquebot"
        else:
            key = "bateau"

        sfx = self.sfx_shot.get(key)
        if sfx:
            self._play_spatial_one_shot(sfx, world_pos=pos, base_vol=VOL_DROPS)

    def play_victory(self):
        """Joue le son de victoire (non-spatial, centré)."""
        if not self.sfx_victory:
            return
        vol = clamp(self._master, 0.0, 1.0)
        self.chan_fx.set_volume(vol, vol)
        self.chan_fx.play(self.sfx_victory)

    def play_defeat(self):
        """Joue le son de défaite (non-spatial, centré)."""
        if not self.sfx_defeat:
            return
        vol = clamp(self._master, 0.0, 1.0)
        self.chan_fx.set_volume(vol, vol)
        self.chan_fx.play(self.sfx_defeat)

    def play_ship_horn(self, pos=None):
        """
        Joue le klaxon / corne de bateau.
        - si pos est fourni → spatial
        - sinon → centré
        """
        if not self.sfx_horn:
            return
        if pos is None:
            vol = clamp(self._master, 0.0, 1.0)
            self.chan_fx.set_volume(vol, vol)
            self.chan_fx.play(self.sfx_horn)
        else:
            self._play_spatial_one_shot(self.sfx_horn, world_pos=pos, base_vol=VOL_DROPS)

    # --- update frame ---
    def update(self):
        self._ensure_beds_started()
        cam = getattr(self.game, "camera", None)
        screen = getattr(self.game, "screen", None)
        if not cam or not screen:
            return

        # Normalise le zoom entre [0..1] où 0 = min_zoom, 1 = max_zoom
        try:
            zmin = getattr(cam, "min_zoom", None)
            zmax = getattr(cam, "max_zoom", None)
            zcur = getattr(cam, "zoom_level", None)
            if zmin is None or zmax is None or zcur is None or zmax <= zmin:
                zoom_norm = clamp((cam.zoom_level - 1.0) / 3.0, 0.0, 1.0)  # fallback (1..4)
            else:
                zoom_norm = clamp((zcur - zmin) / (zmax - zmin), 0.0, 1.0)
        except Exception:
            zoom_norm = 0.0

        # musique : 0 => 0.9 ; 1 => 0.0 puis * master
        music_vol = lerp(0.9, 0.0, zoom_norm) * self._master
        pygame.mixer.music.set_volume(clamp(music_vol, 0.0, 1.0))

        # focus île/base
        island_focus, island_pan = self._best_focus_pan(self._all_island_centers(), cam, screen, FOCUS_RADIUS_MULT)
        base_focus, base_pan = self._base_focus_pan(cam, screen)

        # island bed (spatial)
        if self.sfx_island:
            il_raw = smoothstep(island_focus) if ISLAND_BASE_CURVE == "smooth" else island_focus
            il_vol = clamp(il_raw * VOL_ISLAND * self._master, 0.0, 1.0)
            left, right = self._pan_to_lr(il_vol, island_pan)
            self.chan_island.set_volume(left, right)

        # mer — crossfade avec le focus le plus fort (île OU base)
        if self.sfx_sea:
            focus_all = max(island_focus, base_focus)
            sea_scale = (1.0 - focus_all) + SEA_ON_ISLAND_FACTOR * focus_all
            sea_vol = clamp(VOL_SEA * sea_scale * self._master, 0.0, 1.0)
            self.chan_sea.set_volume(sea_vol, sea_vol)

        # base one-shot
        self._maybe_trigger_base_oneshot(base_focus, base_pan)

    # --- helpers spatialisation ---
    def _world_to_screen(self, wx, wy, cam, screen):
        ox, oy = cam.get_offset(screen.get_size())
        sx = (wx - ox) / cam.zoom_level
        sy = (wy - oy) / cam.zoom_level
        return sx, sy

    def _pan_from_screen_x(self, sx, screen):
        w = max(1, screen.get_width())
        x = clamp(sx / w, 0.0, 1.0)
        return (x * 2.0) - 1.0  # -1..+1

    def _pan_to_lr(self, vol, pan):
        left = vol * (1.0 - clamp((pan + 1.0) / 2.0, 0.0, 1.0))
        right = vol * (1.0 - clamp((-pan + 1.0) / 2.0, 0.0, 1.0))
        return left, right

    def _dist_focus(self, wx, wy, cam, screen, radius_mult):
        sx, sy = self._world_to_screen(wx, wy, cam, screen)
        cx, cy = screen.get_width() / 2, screen.get_height() / 2
        dx, dy = (sx - cx), (sy - cy)
        d = math.hypot(dx, dy)
        base_radius = min(screen.get_width(), screen.get_height()) * 0.45
        r = base_radius * clamp(radius_mult, 0.5, 3.0)
        return clamp(1.0 - (d / r), 0.0, 1.0)

    def _best_focus_pan(self, centers, cam, screen, radius_mult):
        best = 0.0
        best_pan = 0.0
        for wx, wy in centers:
            f = self._dist_focus(wx, wy, cam, screen, radius_mult)
            if f > best:
                sx, _ = self._world_to_screen(wx, wy, cam, screen)
                best_pan = self._pan_from_screen_x(sx, screen)
                best = f
        return best, best_pan

    def _all_island_centers(self):
        out = []
        if self.static_islands:
            out.extend(self.static_islands)
        if self.quantum_islands:
            out.extend(self.quantum_islands)
        return out

    def _base_focus_pan(self, cam, screen):
        centers = []
        rp = getattr(self.game, "red_platform_spawn", None)
        gp = getattr(self.game, "green_platform_spawn", None)
        if isinstance(rp, tuple) and len(rp) == 2:
            centers.append(rp)
        if isinstance(gp, tuple) and len(gp) == 2:
            centers.append(gp)
        if not centers:
            return 0.0, 0.0
        f, pan = self._best_focus_pan(centers, cam, screen, BASE_FOCUS_RADIUS_MULT)
        return f, pan

    def _maybe_trigger_base_oneshot(self, base_focus, base_pan):
        if not self.sfx_base:
            return
        now = pygame.time.get_ticks()
        if base_focus >= BASE_TRIGGER_THRESHOLD and (now - self._last_base_trigger_time) >= BASE_COOLDOWN_MS:
            vol = clamp(BASE_ONE_SHOT_VOL * base_focus * self._master, 0.0, 1.0)
            left, right = self._pan_to_lr(vol, base_pan)
            self.chan_base.set_volume(left, right)
            self.chan_base.play(self.sfx_base)
            self._last_base_trigger_time = now

    def _play_spatial_one_shot(self, sfx, world_pos=None, base_vol=1.0):
        if not sfx:
            return
        cam = getattr(self.game, "camera", None)
        screen = getattr(self.game, "screen", None)
        vol = clamp(base_vol * self._master, 0.0, 1.0)
        if not cam or not screen or not world_pos:
            self.chan_fx.set_volume(vol, vol)
            self.chan_fx.play(sfx)
            return
        sx, sy = self._world_to_screen(world_pos[0], world_pos[1], cam, screen)
        # Atténuation verticale (simule qu'une source trop haut/bas devient plus faible)
        try:
            cy = float(screen.get_height()) / 2.0
            vertical_distance = abs(sy - cy) / max(1.0, cy)
            vertical_factor = clamp(1.0 - vertical_distance * float(self.vertical_attenuation_range), 0.0, 1.0)
            vol = clamp(vol * vertical_factor, 0.0, 1.0)
        except Exception:
            # en cas de souci, ne pas changer le volume
            pass
        pan = self._pan_from_screen_x(sx, screen)
        left, right = self._pan_to_lr(vol, pan)
        self.chan_fx.set_volume(left, right)
        self.chan_fx.play(sfx)

        # Debug optionnel pour vérifier panning/volumes
        try:
            if getattr(self, "debug_audio", False) or getattr(self.game, "debug_audio", False):
                print(
                    f"[AUDIO DEBUG] world_pos={world_pos} sx={sx:.1f} sy={sy:.1f} "
                    f"pan={pan:.2f} vol={vol:.3f} L={left:.3f} R={right:.3f}"
                )
        except Exception:
            pass


# ------------- WRAPPER PUBLIC (rétro-compat) -------------
class Sound:
    """
    Wrapper public pour rester compatible avec l'ancien code:
      - increase_volume() / decrease_volume() (anciens noms)
      - increase_master_volume() / decrease_master_volume() (nouveaux noms)
    Et expose aussi les callbacks gameplay (drop, coins, mines, quantique).
    """

    def __init__(self, game):
        self._engine = SpatialAudioManager(game)

    def update(self):
        self._engine.update()

    # --- anciens noms (compat EventHandler) ---
    def increase_volume(self):
        self._engine.adjust_master_volume(+1)

    def decrease_volume(self):
        self._engine.adjust_master_volume(-1)

    # --- nouveaux noms (si vous préférez) ---
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
        """À appeler quand une unité tire (joue tir_chaloupe / tir_bateau / tir_paquebot)."""
        self._engine.play_shot_for_unit(unit_class_name, pos=pos)

    def on_victory(self):
        """À appeler sur écran de victoire."""
        self._engine.play_victory()

    def on_defeat(self):
        """À appeler quand le joueur perd."""
        self._engine.play_defeat()

    # --- îles quantiques ---
    def set_quantum_islands(self, centers):
        self._engine.set_quantum_islands(centers)

    # --- configuration audio ---
    def set_vertical_attenuation(self, range_float: float):
        """Range: 0.0 = no vertical attenuation, 1.0 = full falloff to screen edge"""
        try:
            self._engine.vertical_attenuation_range = float(range_float)
        except Exception:
            pass

    def enable_audio_debug(self, flag: bool = True):
        """Active des logs diagnostics pour l'audio (print)."""
        try:
            self._engine.debug_audio = bool(flag)
        except Exception:
            pass
