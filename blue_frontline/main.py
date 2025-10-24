import pygame
from Class.menu import *
import Global

if __name__ == "__main__":
    # supprimer tout les __pycache__ avant de lancer le jeu de manière récursive (pour sous dossiers)
    import shutil
    import os
    for root, dirs, files in os.walk("."):
        for dir_name in dirs:
            if dir_name == "__pycache__":
                shutil.rmtree(os.path.join(root, dir_name))

    pygame.init()
    pygame.display.set_caption("Menu du jeu")
    
    Global.get_controls_keys()    
    menu = Menu()
    menu.run()