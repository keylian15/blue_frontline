import pygame
from src.config.controls_manager import get_controls_keys
from src.config.settings_manager import load_gameplay_settings

if __name__ == "__main__":
    load_gameplay_settings()
    pygame.init()
    pygame.display.set_caption("Menu du jeu")

    get_controls_keys()
    from src.menus.Menu import Menu

    menu = Menu()
    menu.run()
