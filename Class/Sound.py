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