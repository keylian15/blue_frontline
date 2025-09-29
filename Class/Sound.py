<<<<<<< HEAD
import pygame
from Global import *

class Sound : 
    
    def __init__(self) :
        pygame.mixer.music.load(SOUND)
        pygame.mixer.music.play(-1)  # -1 pour jouer en boucle
        pygame.mixer.music.set_volume(VOLUME_SOUND)  # Régler le volume
    
    def play_sound(self, sound) :
        """Fonction permettant de jouer un son"""
        pygame.mixer.music.load(sound)
        pygame.mixer.music.play(-1)  # -1 pour jouer en boucle
        
    def stop_sound(self) :
        """Fonction permettant d'arrêter le son"""
        pygame.mixer.music.stop()
    
    def increase_volume(self):
        """Fonction permmettant d'augmenter le volume du son"""
        current_volume = pygame.mixer.music.get_volume()
        new_volume = min(1.0, current_volume + 0.1)  # Augmente de 0.1, max 1.0
        pygame.mixer.music.set_volume(new_volume)
        
    def decrease_volume(self):
        """Fonction permmettant de diminuer le volume du son"""
        current_volume = pygame.mixer.music.get_volume()
        new_volume = max(0.0, current_volume - 0.1)  # Diminue de 0.1, min 0.0
        pygame.mixer.music.set_volume(new_volume)
=======
# Class/Sound.py
import math
import pygame
from Global import (
    # chemins
    MUSIC_GAME, ISLAND_BED, SEA_BED, BASE_BED, APPARITION_QUANTIQUE,
    DROP_CHALOUPE, DROP_CHALOUPE as DROP_CHALOUPe, DROP_BATEAU, DROP_PAQUEBOT, DROP_SOUSMARIN,
    DROP_MINE, DROP_COIN, EXPLOSION_MINE, DROP_ECLAIREURS,
    # volumes / params
    VOL_MUSIC, VOL_ISLAND, VOL_BASE, VOL_SEA, VOL_DROPS,
    SEA_ON_ISLAND_FACTOR, ISLAND_BASE_CURVE,
    FOCUS_RADIUS_MULT, BASE_FOCUS_RADIUS_MULT,
    BASE_TRIGGER_THRESHOLD, BASE_COOLDOWN_MS, BASE_ONE_SHOT_VOL,
)

def clamp(v, lo, hi): return max(lo, min(hi, v))
def lerp(a, b, t):    return a + (b - a) * clamp(t, 0.0, 1.0)

def smoothstep(x):
    x = clamp(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)

class SpatialAudioManager:
    """
    Moteur audio:
      - musique de fond (duck vs zoom)
      - beds: îles (spatial), mer (crossfade)
      - base: one-shot à l'entrée de zone (cooldown)
      - îles quantiques: one-shot d’apparition
      - drops: unités + événements (mine, coin, explosion, éclaireurs)
    """
    def __init__(self, game):
        self.game = game

        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        self._load_sounds()

        # musique de fond
        try:
            pygame.mixer.music.load(MUSIC_GAME)
            pygame.mixer.music.set_volume(clamp(VOL_MUSIC, 0.0, 1.0))
            pygame.mixer.music.play(-1)
        except Exception:
            pass

        # canaux dédiés (réutilisés)
        self.chan_island = pygame.mixer.Channel(1)
        self.chan_sea    = pygame.mixer.Channel(2)
        self.chan_base   = pygame.mixer.Channel(3)  # one-shot base
        self.chan_fx     = pygame.mixer.Channel(4)  # one-shots gameplay (drop, coin, mine, etc.)

        # états
        self.static_islands = None
        self.quantum_islands = []
        self.had_quantum = False

        self._last_base_trigger_time = 0

        # init des beds
        self._ensure_beds_started()

        # init détection d'îles statiques (meilleure couverture)
        self._init_static_islands_from_tmx()

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

        # drops unités connus
        self.sfx_drop = {}
        def _safe_load(name, path):
            try:
                self.sfx_drop[name] = pygame.mixer.Sound(path)
            except Exception:
                self.sfx_drop[name] = None

        _safe_load("chaloupe", DROP_CHALOUPE)
        _safe_load("bateau",   DROP_BATEAU)
        _safe_load("paquebot", DROP_PAQUEBOT)
        _safe_load("sousmarin",DROP_SOUSMARIN)

        # nouveaux événements
        _safe_load("DROP_MINE",       DROP_MINE)
        _safe_load("DROP_COIN",       DROP_COIN)
        _safe_load("EXPLOSION_MINE",  EXPLOSION_MINE)
        _safe_load("DROP_ECLAIREURS", DROP_ECLAIREURS)

    def _ensure_beds_started(self):
        if self.sfx_island and not self.chan_island.get_busy():
            self.chan_island.play(self.sfx_island, loops=-1)
            self.chan_island.set_volume(0, 0)
        if self.sfx_sea and not self.chan_sea.get_busy():
            self.chan_sea.play(self.sfx_sea, loops=-1)
            self.chan_sea.set_volume(0, 0)

    # --- îles statiques depuis TMX (détection élargie) ---
    def _init_static_islands_from_tmx(self):
        tmx = self.game.tmx_data
        centers = []

        # 1) objets globaux
        for obj in getattr(tmx, "objects", []):
            n = getattr(obj, "name", "")
            t = getattr(obj, "type", "")
            if n == "Collision" or t == "Collision":
                cx = obj.x + (getattr(obj, "width", 0) or 0) / 2
                cy = obj.y + (getattr(obj, "height", 0) or 0) / 2
                centers.append((cx, cy))

        # 2) calques Collision_*
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

        # fallback
        if not centers:
            try:
                mw, mh = self.game.map_width, self.game.map_height
                centers = [(mw/2, mh/2)]
            except Exception:
                centers = [(0, 0)]

        self.static_islands = centers

    # --- API interne utilisées par SoundAPI ---
    def set_quantum_islands(self, centers):
        had = len(self.quantum_islands) > 0
        self.quantum_islands = list(centers or [])
        have_now = len(self.quantum_islands) > 0
        if not had and have_now and self.sfx_quantum:
            self.chan_fx.play(self.sfx_quantum)

    def play_drop_for_unit(self, unit_class_name: str, pos=None):
        """Mappe nombres/classes vers un nom générique ('chaloupe', 'bateau', 'paquebot', 'sousmarin')."""
        key = None
        low = unit_class_name.lower()
        if "chaloupe" in low:
            key = "chaloupe"
        elif "paquebot" in low:
            key = "paquebot"
        elif "sous" in low:
            key = "sousmarin"
        elif "eclaireur" in low:
            # pour compat historique: si le code existant appelle on_unit_dropped pour l'éclaireur
            self.play_one_shot_named("DROP_ECLAIREURS", world_pos=pos)
            return
        else:
            # par défaut on le traite comme "bateau"
            key = "bateau"

        sfx = self.sfx_drop.get(key)
        if sfx:
            self._play_spatial_one_shot(sfx, world_pos=pos, base_vol=VOL_DROPS)

    def play_one_shot_named(self, const_name: str, world_pos=None):
        sfx = self.sfx_drop.get(const_name)
        if sfx:
            self._play_spatial_one_shot(sfx, world_pos=world_pos, base_vol=VOL_DROPS)

    # --- rendu / update par frame ---
    def update(self):
        self._ensure_beds_started()
        cam = getattr(self.game, "camera", None)
        screen = getattr(self.game, "screen", None)
        if not cam or not screen:
            return

        # 1) musique vs zoom: 0% zoom -> 90% ; 100% -> 0%
        zoom = clamp(cam.zoom_level, 0.01, 10.0)
        zoom_t = clamp((zoom - 1.0) / (4.0 - 1.0), 0.0, 1.0)  # suppose zoom 1..4
        music_vol = lerp(0.9, 0.0, zoom_t)
        pygame.mixer.music.set_volume(clamp(music_vol, 0.0, 1.0))

        # 2) focus island/base
        island_focus, island_pan = self._best_focus_pan(self._all_island_centers(), cam, screen, FOCUS_RADIUS_MULT)
        base_focus,   base_pan   = self._base_focus_pan(cam, screen)

        focus_val = island_focus
        pan_val   = island_pan

        # 3) island bed (spatial)
        if self.sfx_island:
            il_vol = (smoothstep(focus_val) if ISLAND_BASE_CURVE == "smooth" else focus_val) * VOL_ISLAND
            left, right = self._pan_to_lr(il_vol, pan_val)
            self.chan_island.set_volume(left, right)

        # 4) mer — crossfade avec le focus le plus fort (île OU base)
        if self.sfx_sea:
            focus_all = max(island_focus, base_focus)
            sea_scale = (1.0 - focus_all) + SEA_ON_ISLAND_FACTOR * focus_all
            sea_vol = clamp(VOL_SEA * sea_scale, 0.0, 1.0)
            self.chan_sea.set_volume(sea_vol, sea_vol)

        # 5) base one-shot: déclenche à l'entrée (seuil + cooldown)
        self._maybe_trigger_base_oneshot(base_focus, base_pan)

    # --- helpers spatialisation ---
    def _world_to_screen(self, wx, wy, cam, screen):
        # position monde -> position écran estimée (cam.rect est centré)
        ox, oy = cam.get_offset(screen.get_size())
        sx = (wx - ox) / cam.zoom_level
        sy = (wy - oy) / cam.zoom_level
        return sx, sy

    def _pan_from_screen_x(self, sx, screen):
        w = max(1, screen.get_width())
        x = clamp(sx / w, 0.0, 1.0)
        # L= -1 .. R= +1
        return (x * 2.0) - 1.0

    def _pan_to_lr(self, vol, pan):
        # pan -1..+1 -> balance G/D
        left  = vol * (1.0 - clamp(( pan + 1.0) / 2.0, 0.0, 1.0))
        right = vol * (1.0 - clamp((-pan + 1.0) / 2.0, 0.0, 1.0))
        return left, right

    def _dist_focus(self, wx, wy, cam, screen, radius_mult):
        sx, sy = self._world_to_screen(wx, wy, cam, screen)
        cx, cy = screen.get_width()/2, screen.get_height()/2
        dx, dy = (sx - cx), (sy - cy)
        d = math.hypot(dx, dy)
        # rayon d'influence dépend de l'écran et du zoom
        base_radius = min(screen.get_width(), screen.get_height()) * 0.45
        r = base_radius * clamp(radius_mult, 0.5, 3.0)
        return clamp(1.0 - (d / r), 0.0, 1.0)

    def _best_focus_pan(self, centers, cam, screen, radius_mult):
        best = 0.0
        best_pan = 0.0
        for (wx, wy) in centers:
            f = self._dist_focus(wx, wy, cam, screen, radius_mult)
            if f > best:
                sx, _ = self._world_to_screen(wx, wy, cam, screen)
                best_pan = self._pan_from_screen_x(sx, screen)
                best = f
        return best, best_pan

    def _all_island_centers(self):
        # static + quantum
        out = []
        if self.static_islands:
            out.extend(self.static_islands)
        if self.quantum_islands:
            out.extend(self.quantum_islands)
        return out

    def _base_focus_pan(self, cam, screen):
        # positions des bases depuis game
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
            vol = clamp(BASE_ONE_SHOT_VOL * base_focus, 0.0, 1.0)
            left, right = self._pan_to_lr(vol, base_pan)
            self.chan_base.set_volume(left, right)
            self.chan_base.play(self.sfx_base)
            self._last_base_trigger_time = now

    def _play_spatial_one_shot(self, sfx, world_pos=None, base_vol=1.0):
        if not sfx:
            return
        cam = getattr(self.game, "camera", None)
        screen = getattr(self.game, "screen", None)
        if not cam or not screen or not world_pos:
            # sans position -> mono centré
            self.chan_fx.set_volume(base_vol, base_vol)
            self.chan_fx.play(sfx)
            return
        sx, _ = self._world_to_screen(world_pos[0], world_pos[1], cam, screen)
        pan = self._pan_from_screen_x(sx, screen)
        left, right = self._pan_to_lr(base_vol, pan)
        self.chan_fx.set_volume(left, right)
        self.chan_fx.play(sfx)
>>>>>>> e5f634d (Ajout du système audio spatial)
