import pygame, pytmx, pyscroll
from Class.Camera import *
from Class.Perlin import *
from Global import *
from Utils import *

class IslandSprite(pygame.sprite.Sprite):
    """Sprite pour représenter une île générée."""
    
    def __init__(self, surface, x, y):
        super().__init__()
        self.image = surface
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

class Game : 
    """Classe principale du jeu."""

    def __init__(self): 
        """Initialisation du jeu."""
        
        # Créer la fenêtre
        self.screen = pygame.display.set_mode((0, 0), pygame.NOFRAME)        
        pygame.display.set_caption("Blue Frontline")
        self.tmx_data = pytmx.util_pygame.load_pygame(MAP_PATH)
        
        # Les data de la map
        map_data = pyscroll.data.TiledMapData(self.tmx_data)
        map_layer = pyscroll.orthographic.BufferedRenderer(map_data, self.screen.get_size()) 
        
        # Les data de tilesets
        self.island_tileset = load_tileset(ISLAND_TILESET_PATH)
        self.deep_water_tileset = load_tileset(DEEP_WATER_TILESET_PATH)
        self.water_tileset = load_tileset(WATER_TILESET_PATH)
        
        # Créer la caméra
        camera_position = self.tmx_data.get_object_by_name("spawn") # Récupère la position de la caméra depuis Tiled
        self.camera = Camera(camera_position.x, camera_position.y)
        
        # Dessiner le groupe de calques
        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=3)
        self.group.add(self.camera)
            
    def quantique(self):
        """ Génération de l'île quantique"""
        # Générer l'île avec Perlin
        island_position = None
        for obj in self.tmx_data.objects:
            if obj.name == "ile_quantique" :                         
                # On récupère la position et on l'aligne à la grille      
                aligned_x = (obj.x // 32) * 32
                aligned_y = (obj.y // 32) * 32
                island_position = (aligned_x, aligned_y)

                # On récupère la taille en nombre de tuiles
                island_width_tiles = int(obj.width // 32) 
                island_height_tiles = int(obj.height // 32)
                        
                # Créer le tileset final avec les tuiles centrales
                tileset_surface_smooth = [
                        self.deep_water_tileset,# Index 0: Eau profonde (centre du tileset)
                        self.water_tileset,     # Index 1: Eau peu profonde (le png en lui même)
                        self.island_tileset     # Index 2: Île (centre du tileset)
                    ]
        
                # Générer et créer le sprite de l'île
                self.perlin = Perlin()
                island_matrix = self.perlin.generate_island(island_height_tiles, island_width_tiles)
                island_surface = self.perlin.smooth_map(island_matrix, tileset_surface_smooth)
                
                # Créer le sprite et l'ajouter au groupe
                if island_position:
                    island_sprite = IslandSprite(island_surface, island_position[0], island_position[1])
                else:
                    island_sprite = IslandSprite(island_surface, 100, 100)
                    
                self.group.add(island_sprite)
                
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
                    
                # Clic gauche pour générer l'île
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.quantique()            
            # On gère les entrées
            self.handle_input()
            # On met a jour les groupes
            self.group.update()
            # On centre le groupe sur la caméra
            self.group.center(self.camera.rect.center)
            # On dessine le groupe
            self.group.draw(self.screen)
            
            pygame.display.flip()
            
            clock.tick(60)
        pygame.quit()