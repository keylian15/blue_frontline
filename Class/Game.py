import time
import pygame, pytmx, pyscroll
from Class.Camera import *
from Global import *
from Class.hud import *

class Game : 
    """Classe principale du jeu."""

    def __init__(self): 
        """Initialisation du jeu."""
        
        # Créer la fenêtre
        self.screen = pygame.display.set_mode((0, 0), pygame.NOFRAME)        
        pygame.display.set_caption("Blue Frontline")
        tmx_data = pytmx.util_pygame.load_pygame(MAP_PATH)
        
        # Les data de la map
        map_data = pyscroll.data.TiledMapData(tmx_data)
        map_layer = pyscroll.orthographic.BufferedRenderer(map_data, self.screen.get_size()) 
        
        # Créer la caméra
        camera_position = tmx_data.get_object_by_name("spawn") # Récupère la position de la caméra depuis Tiled
        self.camera = Camera(camera_position.x, camera_position.y)
        
        # Dessiner le groupe de calques
        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=3)
        self.group.add(self.camera)
        
        # le HUD
        self.hud = Hud (self.screen.get_width(), self.screen.get_height())

    def handle_input(self):
        """Gère les entrées clavier pour déplacer la caméra."""
        # On récupère les touches appuyées
        pressed = pygame.key.get_pressed()

        dx, dy = 0, 0
        if pressed[pygame.K_UP]: # Haut
            dy -= self.camera.camera_move
        if pressed[pygame.K_DOWN]: # Bas
            dy += self.camera.camera_move
        if pressed[pygame.K_LEFT]: # Gauche 
            dx -= self.camera.camera_move
        if pressed[pygame.K_RIGHT]: # Droite
            dx += self.camera.camera_move
            
        if pressed[pygame.K_h]:
            self.hud.switch()
            time.sleep(0.1)

        # On déplace la caméra seulement si il y a un déplacement
        if dx or dy:  
            self.camera.move(dx, dy)
            

    def run(self): 
        
        # On crée une horloge pour gérer les fps
        clock = pygame.time.Clock()
        running = True
    
        while running: 
            
            # Gestion des événements
            for event in pygame.event.get(): 

                if event.type == pygame.QUIT: 
                    running = False
            
            # On gère les entrées
            self.handle_input()
            # On met a jour les groupes
            self.group.update()
            # On centre le groupe sur la caméra
            self.group.center(self.camera.rect.center)
            # On dessine le groupe
            self.group.draw(self.screen)
            #on dessine le hud
            if self.hud.show:
                self.hud.draw(self.screen)
            
            pygame.display.flip()
            clock.tick(60)
        pygame.quit()