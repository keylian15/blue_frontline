# Class/SoundAPI.py
import pygame
from Class.Sound import SpatialAudioManager

class Sound:
    """
    API publique simple pour piloter l'audio depuis le jeu.
    On garde ici une surface minimale; toute la logique est dans SpatialAudioManager.
    """
    def __init__(self, game: "Game"):
        self.game = game
        # le moteur initialise mixer + charge les sons
        self._engine = SpatialAudioManager(game)

    # --- boucle par frame ---
    def update(self):
        self._engine.update()

    # --- événements de gameplay (one-shots) ---
    def on_unit_dropped(self, unit_class_name: str, pos=None):
        """Drop générique des unités : chaloupe, bateau, paquebot, sous-marin, etc."""
        self._engine.play_drop_for_unit(unit_class_name, pos=pos)

    def on_eclaireur_dropped(self, pos):
        self._engine.play_one_shot_named("DROP_ECLAIREURS", world_pos=pos)

    def on_mine_dropped(self, pos):
        self._engine.play_one_shot_named("DROP_MINE", world_pos=pos)

    def on_mine_explosion(self, pos):
        self._engine.play_one_shot_named("EXPLOSION_MINE", world_pos=pos)

    def on_coin_drop(self, pos):
        """Quand un ennemi (bateau) est détruit et qu'on spawn une pièce."""
        self._engine.play_one_shot_named("DROP_COIN", world_pos=pos)

    # --- îles quantiques ---
    def set_quantum_islands(self, centers):
        """
        Informe le moteur des centres d'îles quantiques actuellement présentes.
        Déclenche apparition_ile_quantique si on passe de 0 -> >=1.
        """
        self._engine.set_quantum_islands(centers)

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