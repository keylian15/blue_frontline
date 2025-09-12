import pygame 
from Global import * 

class Hud:
    
    def __init__ (self, width, height):
        
        self.width = width
        self.height = height
        
        self.hud_color = (198, 198, 198)
        self.show = True
        
        # Build du HUD
        self.build_surface = pygame.Surface((width * 0.15, height * 0.25), pygame.SRCALPHA)
        self.build_surface.fill(self.hud_color)
        
        #select HUD
        self.select_surface = pygame.Surface((width * 0.3, height * 0.2), pygame.SRCALPHA)
        self.select_surface.fill(self.hud_color)
        
    def switch(self):
        self.show = not self.show
            
    def draw(self, screen):

            
        #build hud
        screen.blit(self.build_surface, (self.width * 0.84, self.height * 0.74))
            
        #select hud
        screen.blit(self.select_surface, (self.width * 0.35, self.height * 0.79))