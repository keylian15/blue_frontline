import pygame
from Global import TIME_SPEED, TIME_STEP

class Timer:
    def __init__(self):
        self.count = 0
        self.TIMER_EVENT = pygame.USEREVENT + 2
        pygame.time.set_timer(self.TIMER_EVENT, int(TIME_STEP / TIME_SPEED))
        
        
    def handle_event(self, event):
        if event.type == self.TIMER_EVENT:
            self.count += 1
            
    def get_time(self):
        if self.count % 60 < 10:
            return f"0{self.count // 60}:0{self.count % 60}"
        return f"0{self.count // 60}:{self.count % 60}"
        
    