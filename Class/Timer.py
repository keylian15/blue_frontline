import pygame
from Global import TIME_SPEED, TIME_STEP, TIMER_EVENT

class Timer:
    def __init__(self):
        self.count = 0
        self.TIMER_EVENT = TIMER_EVENT
        pygame.time.set_timer(self.TIMER_EVENT, int(TIME_STEP / TIME_SPEED))
        
        
    def handle_event(self, event):
        if event.type == self.TIMER_EVENT:
            self.count += 1
            
    def get_time(self):
        return f"{self.count // 60} : {self.count % 60} "
        
    