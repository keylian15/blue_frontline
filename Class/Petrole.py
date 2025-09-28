import pygame
from Global import PETROLE_EVENT, TIME_SPEED, TIME_SPEEDS, TIME_STEP

class Petrole:
    def __init__(self):
        """Fonction permettant d'initialiser le compteur de pétrole"""
        self.count = 0

        # On crée un événement unique pour incrémenter le pétrole
        self.PETROLE_EVENT = PETROLE_EVENT
        self.current_speed = TIME_SPEEDS[0] 
        pygame.time.set_timer(self.PETROLE_EVENT, int(TIME_STEP / self.current_speed))  # On fait le timer en fonction de la vitesse du temps 

    def handle_event(self, event):
        """À appeler dans la boucle principale pour gérer l'auto-incrément"""
        if event.type == self.PETROLE_EVENT:
            self.count += 1

    # Fonction de test.
    def minus_one(self):
        if self.count <= 0:
            return
        else:
            self.count -= 1

    def set_speed(self, speed):
        """Ajuste la vitesse d'auto-incrément. Si speed == 0, met en pause (désactive l'événement)."""
        self.current_speed = speed
        if speed <= 0:
            pygame.time.set_timer(self.PETROLE_EVENT, 0)
        else:
            pygame.time.set_timer(self.PETROLE_EVENT, int(TIME_STEP / speed))

    def pause(self):
        self.set_speed(0)

    def resume(self):
        if self.current_speed <= 0:
            self.current_speed = TIME_SPEED
        self.set_speed(self.current_speed)
    