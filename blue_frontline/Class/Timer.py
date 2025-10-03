import pygame
from Global import TIME_MAREE, TIME_STEP, TIMER_EVENT, TIME_SPEEDS

class Timer:
    """Classe pour gérer le temps et les événements de marée."""

    def __init__(self):
        """Initialise le timer."""

        self.maree_haute = False  # État actuel de la marée (False = basse, True = haute)
        self.maree_changed = False  # Flag pour détecter un changement
        self.count = 0
        self.TIMER_EVENT = TIMER_EVENT
        self.current_speed = TIME_SPEEDS[0]  # Commencer à x1
        self.speed_index = 0  # Index dans TIME_SPEEDS
        pygame.time.set_timer(self.TIMER_EVENT, int(TIME_STEP / self.current_speed))

    def handle_event(self, event: pygame.event):
        """Gère les événements de timer.

        Args:
            event (pygame.event): Événement pygame à traiter.
        """
        
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
        """Retourne le temps écoulé en minutes:secondes.
        
        Returns:
            str: Temps écoulé en minutes:secondes.
        """

        return f"{self.count // 60} : {self.count % 60}"

    def set_speed(self, speed: int):
        """Ajuste la vitesse du timer. Si speed == 0, met en pause (désactive l'événement).

        Args:
            speed (int): Vitesse du timer (en secondes).
        """
        
        # Clamp minimal pour éviter division par zéro
        self.current_speed = speed
        if speed <= 0:
            pygame.time.set_timer(self.TIMER_EVENT, 0)
        else:
            pygame.time.set_timer(self.TIMER_EVENT, int(TIME_STEP / speed))

    def cycle_speed(self):
        """Passe à la vitesse suivante dans le cycle x1 -> x2 -> x4 -> x8 -> x10 -> x20 -> 0.5 -> 1.
        
        Returns:
            int: La nouvelle vitesse.
        """
        
        self.speed_index = (self.speed_index + 1) % len(TIME_SPEEDS)
        self.current_speed = TIME_SPEEDS[self.speed_index]
        self.set_speed(self.current_speed)
        return self.current_speed

    def get_speed_multiplier(self):
        """Retourne le multiplicateur de vitesse actuel.
        
        Returns:
            int: Multiplicateur de vitesse actuel.
        """
        
        return self.current_speed
        
