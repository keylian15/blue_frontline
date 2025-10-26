import math  # <-- pour build_nav_grid

import pygame
import pyscroll
import pytmx
from Class.Camera import Camera
from Class.Combat import CombatSystem
from Class.Hud import Hud
from Class.PlateformePetroliere import PlateformePetroliere
from Class.SoundAPI import Sound  # <-- API publique son
from Class.units.Bateau import BateauRouge, BateauVert
from Class.units.Chaloupe import ChaloupeRouge, ChaloupeVerte
from Class.units.Eclaireur import EclaireurRouge, EclaireurVert
# On importe les outils de navmesh IA
from Class.units.IA.IA_Eclaireur import (SimpleGrid,
                                         make_grid_adapter_from_simplegrid)
from Class.units.Paquebot import PaquebotRouge, PaquebotVert
from Class.units.Sousmarin import SousMarinRouge, SousMarinVert
from Class.Hud import Hud
from Class.OverlayMenu import OverlayMenu
from Global import *
from Utils import *

class GameInitializer:
    """Gestionnaire d'initialisation des composants du jeu.
    
    Ce module est responsable de:
        - Charger la carte Tiled
        - Initialiser la caméra
        - Instancier les plateformes pétrolières / systèmes du jeu
        - Initialiser HUD + Son
        - Construire la grille de navigation (pathfinding IA)
    """

    def __init__(self, game: "Game"):
        """Initialise le gestionnaire d'initialisation avec une référence au jeu.

        Args:
            game (Game): Référence au jeu.
        """
        self.game = game

    def init_map(self):
        """Initialise les données de la map et les tilesets.

        Charge la TMX, crée le renderer pyscroll, enregistre les dimensions
        du monde, et prépare les tilesets nécessaires.
        """
        # Charger la carte Tiled (.tmx)
        self.game.tmx_data = pytmx.util_pygame.load_pygame(MAP_PATH)

        # Les data de la map pour pyscroll
        map_data = pyscroll.data.TiledMapData(self.game.tmx_data)
        self.game.map_layer = pyscroll.orthographic.BufferedRenderer(
            map_data,
            self.game.screen.get_size()
        )

        # Charger les tilesets utilisés pour afficher les différentes zones
        self.game.island_tileset = load_tileset(ISLAND_TILESET_PATH)
        self.game.deep_water_tileset = load_tileset(DEEP_WATER_TILESET_PATH)
        self.game.water_tileset = load_tileset(WATER_TILESET_PATH)

        # Dimensions du monde en pixels
        self.game.map_width = self.game.tmx_data.width * self.game.tmx_data.tilewidth
        self.game.map_height = self.game.tmx_data.height * self.game.tmx_data.tileheight

    def init_camera(self):
        """Initialise la caméra et le groupe de rendu pyscroll."""
        # On récupère l'objet "spawn" défini dans Tiled comme position de base
        camera_position = self.game.tmx_data.get_object_by_name("spawn")

        # Caméra qui suit le monde
        self.game.camera = Camera(
            camera_position.x,
            camera_position.y,
            self.game.screen.get_size(),
            (self.game.map_width, self.game.map_height),
        )

        # Groupe pyscroll qui dessine la map + tous les sprites
        self.game.group = pyscroll.PyscrollGroup(
            map_layer=self.game.map_layer,
            default_layer=3
        )
        self.game.group.add(self.game.camera)

    def init_game_systems(self):
        """Initialise les systèmes de jeu (combat, unités, plateformes, etc.)."""

        # Système de combat
        self.game.combat_system = CombatSystem(self.game)

        # Liste des unités présentes dans la partie
        self.game.units = []

        # Compteurs d'économie
        self.game.nbPompePetroliereRouge = 0
        self.game.nbPompePetroliereVert = 0

        # Aucune unité sélectionnée au départ
        self.game.selected_unit = None

        # On va récupérer les infos de base (plateformes, zones de spawn)
        red_platform_obj = None
        green_platform_obj = None

        # Pour info:
        #   - "Base_rouge" / "Base_verte" = vraies plateformes pétrolières
        #   - "Spawn_base_rouge" / "Spawn_base_verte" = zones (polygones) de déploiement
        #
        # On parcourt tous les objets définis dans Tiled
        for obj in self.game.tmx_data.objects:
            if obj.name == "Base_verte":
                green_platform_obj = obj
                self.game.green_platform_spawn = obj.points  # contour ?
            elif obj.name == "Base_rouge":
                red_platform_obj = obj
                self.game.red_platform_spawn = obj.points
            elif obj.name == "Spawn_base_verte":
                self.game.green_platform_zone = obj.points
            elif obj.name == "Spawn_base_rouge":
                self.game.red_platform_zone = obj.points  # Récupérer les points du polygone
            elif obj.name == "Spawn_base_verte_pompe" : 
                self.game.green_pompe_zone = obj.as_points
            elif obj.name == "Spawn_base_rouge_pompe" : 
                self.game.red_pompe_zone = obj.as_points
        
        # Créer les plateformes à partir des positions Tiled
        from Class.units.PlateformePetroliere import PlateformePetroliereRouge, PlateformePetroliereVerte
        plateforme_rouge = PlateformePetroliereRouge(self.game, red_platform_obj)
        plateforme_verte = PlateformePetroliereVerte(self.game, green_platform_obj)

        # Stocker les plateformes
        self.game.plateformes = {"red": plateforme_rouge, "green": plateforme_verte}
        
        # Ajouter les plateformes à la liste des unités pour la détection/tir/dégâts
        self.game.units.append(plateforme_rouge)
        self.game.units.append(plateforme_verte)

        # Ajouter au système de combat
        self.game.combat_system.add_unit(plateforme_rouge)
        self.game.combat_system.add_unit(plateforme_verte)

        # Ajouter au groupe de rendu
        self.game.group.add(plateforme_rouge)
        self.game.group.add(plateforme_verte)
        
        # === Positions ponctuelles pour l'audio (bases) ===
        # On fournit explicitement des tuples (x,y) au moteur audio
        # self.game.red_platform_spawn   = (platform_rouge_x, platform_rouge_y)
        # self.game.green_platform_spawn = (platform_verte_x, platform_verte_y)

        # === Construire la grille de navigation (pathfinding IA) ===
        #
        # IMPORTANT : L'IA de l'Éclaireur (ScoutAI) a besoin que
        # self.game.nav_grid_adapter existe AVANT le spawn des unités.
        #
        self.build_nav_grid()

    def init_ui(self):
        """Initialise l'interface utilisateur (HUD, popup unités, police)."""

        # Liste des unités constructibles pour la popup de sélection
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
            ("Sous-Marin Vert", SousMarinVert),
        ]
        self.game.popup_selection = 0

        # Police pour le HUD
        pygame.font.init()
        self.game.font = pygame.font.Font(None, 24)

        # Interface HUD (timer marée, vie bases, etc.)
        self.game.hud = Hud(self.game.screen)
        self.game.overlay_menu = OverlayMenu(self.game.screen, self.game)
        
    def init_sound(self):
        """Initialise le système sonore (via l'API publique Sound)."""
        # Sound va gérer l'init du mixer et les canaux
        self.game.sound = Sound(self.game)

    def switch_layer(self):
        """Active le bon calque de marée (haute ou basse) dans Tiled
        et prévient le renderer qu'il doit se mettre à jour.
        """
        if self.game.hud.timer.maree_haute:
            self.toggle_layer("Maree_Haute", True)
            self.toggle_layer("Maree_Basse", False)
        else:
            self.toggle_layer("Maree_Haute", False)
            self.toggle_layer("Maree_Basse", True)

        # Indiquer au renderer que les calques ont changé
        self.game.renderer.map_needs_refresh = True

    def toggle_layer(self, layer_name: str, visible: bool):
        """Change la visibilité d'un calque Tiled.

        Args:
            layer_name (str): Nom du calque.
            visible (bool): True pour rendre visible, False pour cacher.

        Returns:
            None
        """
        for layer in self.game.tmx_data.layers:
            if layer.name == layer_name:
                layer.visible = visible
                return

    # ------------------------------------------------------------------
    # NAVIGATION GRID (PATHFINDING POUR L'IA)
    # ------------------------------------------------------------------
    def build_nav_grid(self):
        """Construit la grille de navigation (pathfinding) pour l'IA.

        Produit / met à jour :
            self.game.nav_grid_raw        -> SimpleGrid brut
            self.game.nav_grid_adapter    -> GridAdapter pour l'IA

        Pour l'instant : on considère toute la carte comme navigable.
        Ensuite on pourra:
          - marquer comme bloquées les cellules qui correspondent à des rochers,
            terre à marée basse, quai, etc.
          - ajuster le coût (self.game.nav_grid_raw.costs[x][y]) pour simuler
            zones risquées / peu profondes / zone d'artillerie ennemie etc.
        """

        # Taille en pixels d'une case de pathfinding
        cell_size = 32  # DOIT rester cohérent avec SimpleGrid

        # Calculer le nombre de cellules nécessaires pour couvrir toute la map
        grid_w = math.ceil(self.game.map_width / cell_size)
        grid_h = math.ceil(self.game.map_height / cell_size)

        # 1) Construire une SimpleGrid initialement toute navigable
        nav_grid = SimpleGrid(grid_w, grid_h, cell_size=cell_size)

        # 2) (Option FUTURE) Analyser la TMX pour poser des obstacles.
        # Exemple d'idées pour plus tard :
        #   - Parcourir les layers "Maree_Basse"/"Maree_Haute" et marquer
        #     les tuiles de terre comme NON walkable.
        #   - Lire un calque d'objets genre "Rochers" et faire
        #     nav_grid.walkable[cx][cy] = False
        #
        # Pour l'instant : on laisse tout navigable pour éviter le crash
        # et permettre aux éclaireurs de bouger.

        # 3) Convertir SimpleGrid -> GridAdapter utilisable par A*
        self.game.nav_grid_raw = nav_grid
        self.game.nav_grid_adapter = make_grid_adapter_from_simplegrid(nav_grid)
