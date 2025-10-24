import pygame
from Global import PETROLE_EVENT, TIME_SPEEDS, TIME_STEP

class Petrole:
    """Classe permettant de gérer le compteur de pétrole"""

    def __init__(self):
        """Fonction permettant d'initialiser le compteur de pétrole"""
    
        self.count = 1000000

        # On crée un événement unique pour incrémenter le pétrole
        self.PETROLE_EVENT = PETROLE_EVENT
        self.current_speed = TIME_SPEEDS[0] 
        pygame.time.set_timer(self.PETROLE_EVENT, int(TIME_STEP / self.current_speed))  # On fait le timer en fonction de la vitesse du temps 

    def handle_event(self, event: pygame.event, nbPompe: int):
        """À appeler dans la boucle principale pour gérer l'auto-incrément

        Args:
            event (pygame.event): L'événement à traiter
            nbPompe (int): Le nombre de pompe à pétrole
        """
        
        if event.type == self.PETROLE_EVENT:
            from Global import OIL_PER_SECOND
            self.count += OIL_PER_SECOND + nbPompe

    def set_speed(self, speed: int):
        """Ajuste la vitesse d'auto-incrément. Si speed == 0, met en pause (désactive l'événement).

        Args:
            speed (int): La vitesse à appliquer
        """
        
        self.current_speed = speed
        if speed <= 0:
            pygame.time.set_timer(self.PETROLE_EVENT, 0)
        else:
            pygame.time.set_timer(self.PETROLE_EVENT, int(TIME_STEP / speed))