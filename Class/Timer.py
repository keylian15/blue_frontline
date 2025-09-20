import pygame
from Global import TIME_MAREE, TIME_SPEED, TIME_STEP, TIMER_EVENT

class Timer:
    def __init__(self):
        self.maree_haute = False  # État actuel de la marée (False = basse, True = haute)
        self.maree_changed = False  # Flag pour détecter un changement
        self.count = 0
        self.TIMER_EVENT = TIMER_EVENT
        pygame.time.set_timer(self.TIMER_EVENT, int(TIME_STEP / TIME_SPEED))

    def handle_event(self, event):
        if event.type == self.TIMER_EVENT:
            self.count += 1
            
            if self.count % TIME_MAREE == 0:
                # Basculer l'état de la marée
                old_state = self.maree_haute
                self.maree_haute = not self.maree_haute
                
                # Marquer qu'un changement s'est produit
                self.maree_changed = (old_state != self.maree_haute)
            else:
                self.maree_changed = False

    def get_time(self):
        return f"{self.count // 60} : {self.count % 60}"