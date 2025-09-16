import pygame

class Petrole:
    def __init__(self):
        self.count = 0

        # On crée un événement unique pour incrémenter le pétrole
        self.PETROLE_EVENT = pygame.USEREVENT + 1
        pygame.time.set_timer(self.PETROLE_EVENT, 1000)  # toutes les 1000 ms (1 sec)

    def handle_event(self, event):
        """À appeler dans la boucle principale pour gérer l'auto-incrément"""
        if event.type == self.PETROLE_EVENT:
            self.count += 1
