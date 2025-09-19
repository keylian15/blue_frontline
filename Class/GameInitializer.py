import pygame
import pytmx
import pyscroll
from Class.Camera import Camera
from Class.Combat import CombatSystem
from Class.Sound import Sound

from Class.units.Chaloupe import ChaloupeRouge, ChaloupeVerte
from Class.units.Bateau import BateauRouge, BateauVert
from Class.units.Eclaireur import EclaireurRouge, EclaireurVert
from Class.units.Paquebot import PaquebotRouge, PaquebotVert
from Class.units.Sousmarin import SousMarinRouge, SousMarinVert
from Class.Hud import Hud
from Global import *
from Utils import *

class GameInitializer:
    """Gestionnaire d'initialisation des composants du jeu."""
    
    def __init__(self, game):
        """Initialise le gestionnaire d'initialisation avec une référence au jeu."""
        self.game = game
    
    def init_display(self):
        """Initialise l'affichage et la fenêtre."""
        self.game.screen = pygame.display.set_mode((0, 0), pygame.NOFRAME)        
        pygame.display.set_caption("Blue Frontline")
    
    def init_map(self):
        """Initialise les données de la map et les tilesets."""
        self.game.tmx_data = pytmx.util_pygame.load_pygame(MAP_PATH)
        
        # Les data de la map
        map_data = pyscroll.data.TiledMapData(self.game.tmx_data)
        self.game.map_layer = pyscroll.orthographic.BufferedRenderer(map_data, self.game.screen.get_size())
        
        # Les data de tilesets
        self.game.island_tileset = load_tileset(ISLAND_TILESET_PATH)
        self.game.deep_water_tileset = load_tileset(DEEP_WATER_TILESET_PATH)
        self.game.water_tileset = load_tileset(WATER_TILESET_PATH)
        
        # Récupérer les dimensions de la map
        self.game.map_width = self.game.tmx_data.width * self.game.tmx_data.tilewidth
        self.game.map_height = self.game.tmx_data.height * self.game.tmx_data.tileheight
        print(f"Dimensions de la map: {self.game.map_width}x{self.game.map_height}")
    
    def init_camera(self):
        """Initialise la caméra et les groupes de sprites."""
        camera_position = self.game.tmx_data.get_object_by_name("spawn")
        self.game.camera = Camera(camera_position.x, camera_position.y, 
                                self.game.screen.get_size(), 
                                (self.game.map_width, self.game.map_height))
        
        # Dessiner le groupe de calques
        self.game.group = pyscroll.PyscrollGroup(map_layer=self.game.map_layer, default_layer=3)
        self.game.group.add(self.game.camera)
    
    def init_game_systems(self):
        """Initialise les systèmes de jeu (combat, unités, etc.)."""
        # Système de combat et unités
        self.game.combat_system = CombatSystem()
        self.game.units = []
        self.game.selected_unit = None
        
        # Positions de spawn des unités
        self.game.green_platform_spawn = (96, 512)
        self.game.red_platform_spawn = (1824, 512)
        self.game.spawn_radius = 80
    
    def init_ui(self):
        """Initialise l'interface utilisateur."""
        # Système de popup pour sélection d'unités
        self.game.show_unit_popup = False
        self.game.unit_classes = [
            ("Chaloupe Rouge", ChaloupeRouge),
            ("Chaloupe Verte", ChaloupeVerte),
            ("Bateau Rouge", BateauRouge),
            ("Bateau Vert", BateauVert),
            ("Éclaireur Rouge", EclaireurRouge),
            ("Éclaireur Vert", EclaireurVert),
            ("Paquebot Rouge", PaquebotRouge),
            ("Paquebot Vert", PaquebotVert),
            ("Sous-Marin Rouge", SousMarinRouge),
            ("Sous-Marin Vert", SousMarinVert)
        ]
        self.game.popup_selection = 0
        
        # Police et HUD
        pygame.font.init()
        self.game.font = pygame.font.Font(None, 24)
        self.game.hud = Hud(self.game.screen)
        
    def init_sound(self):
        """Initialise le système sonore."""
        pygame.mixer.init()
        self.game.sound = Sound()
    
    def switch_layer(self):
        """Fonction permettant de switcher entre les calques de marée haute et basse."""
        if self.game.hud.timer.maree_haute:
            self.toggle_layer("Maree_Haute", True)
            self.toggle_layer("Maree_Basse", False)
        else:
            self.toggle_layer("Maree_Haute", False)
            self.toggle_layer("Maree_Basse", True)
        
        # Marquer la map pour reconstruction au prochain rendu
        self.game.renderer.map_needs_refresh = True        

    def toggle_layer(self, layer_name: str, visible: bool):
        """
        Active ou désactive un calque de la carte par son nom.
        
        :param layer_name: Nom du calque dans Tiled (.tmx)
        :param visible: True pour afficher, False pour cacher
        """
        for layer in self.game.tmx_data.layers:
            if layer.name == layer_name:
                layer.visible = visible
                return