import Global
import pygame
from Class.menu import *

if __name__ == "__main__":
    load_gameplay_settings()
    pygame.init()
    pygame.display.set_caption("Menu du jeu")
    
    Global.get_controls_keys()
    menu = Menu()
    menu.run()