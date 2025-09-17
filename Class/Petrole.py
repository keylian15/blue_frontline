import pygame
from Global import PETROLE_EVENT, TIME_SPEED, TIME_STEP

class Petrole:
    def __init__(self):
        """Fonction permettant d'initialiser le compteur de pétrole"""
        self.count = 0

        # On crée un événement unique pour incrémenter le pétrole
        self.PETROLE_EVENT = PETROLE_EVENT
        pygame.time.set_timer(self.PETROLE_EVENT, int(TIME_STEP / TIME_SPEED))  # On fait le timer en fonction de la vitesse du temps 

    def handle_event(self, event):
        """À appeler dans la boucle principale pour gérer l'auto-incrément"""
        if event.type == self.PETROLE_EVENT:
            self.count += 1
            
            print(event.type, event)

    # Fonction de test.
    def minus_one(self):
        if self.count <= 0:
            return
        else:
            self.count -= 1
    