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
        
        # Créer la caméra
        camera_position = self.tmx_data.get_object_by_name("spawn") # Récupère la position de la caméra depuis Tiled
        self.camera = Camera(camera_position.x, camera_position.y)
        
        # Dessiner le groupe de calques
        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=3)
        self.group.add(self.camera)
        
    def quantique(self):
        # Générer l'île avec Perlin
        island_position = None
        for obj in self.tmx_data.objects:
            if obj.name == "ile_quantique":               
                aligned_x = (obj.x // 32) * 32
                aligned_y = (obj.y // 32) * 32
                island_position = (aligned_x, aligned_y)

                island_width_tiles = int(obj.width // 32) + 1
                island_height_tiles = int(obj.height // 32) + 1
                break

        eau_profonde = pygame.image.load(DEEP_WATER_PATH).convert_alpha()
        eau_peu_profonde = pygame.image.load(WATER_PATH).convert_alpha()
        terre = pygame.image.load(ISLAND_PATH).convert_alpha()
        tileset = [eau_profonde, eau_peu_profonde, terre]
        # tileset = load_tileset(TILESET_PATH)
        mapping = {0: 0, 1: 1, 2: 2}

        # Générer et créer le sprite de l'île
        self.perlin = Perlin()
        island_matrix = self.perlin.generate_island(island_height_tiles, island_width_tiles)
        island_surface = self.perlin.render_matrix(island_matrix, tileset, 32, mapping)
        
        # Créer le sprite et l'ajouter au groupe
        if island_position:
            island_sprite = IslandSprite(island_surface, island_position[0], island_position[1])
        else:
            # Position par défaut si pas d'objet "ile_quantique" trouvé
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