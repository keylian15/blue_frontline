import pygame
from Class.menu import *


if __name__ == "__main__":
    pygame.init()
    pygame.display.set_caption("Menu du jeu")
    menu = Menu()
    menu.run()