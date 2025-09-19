import pygame
import math
import random
from Global import *
from Class.Perlin import Perlin

# Importation des modules gestionnaires
from Class.EventHandler import EventHandler
from Class.Renderer import Renderer
from Class.InputManager import InputManager
from Class.GameUpdater import GameUpdater
from Class.GameInitializer import GameInitializer

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
        
        # Initialiser les gestionnaires
        self.initializer = GameInitializer(self)
        
        # Initialiser les composants principaux
        self.initializer.init_display()
        self.initializer.init_map()
        self.initializer.init_camera()
        self.initializer.init_game_systems()
        self.initializer.init_ui()
        self.initializer.init_sound()

        # Variable pour suivre les changements de zoom
        self.last_zoom_level = self.camera.zoom_level
        
        # Initialiser les gestionnaires après que les composants soient créés
        self.event_handler = EventHandler(self)
        self.renderer = Renderer(self)
        self.input_manager = InputManager(self)
        self.updater = GameUpdater(self)
            
    def quantique(self):
        """ Génération de l'île quantique pour toutes les îles quantique dans la map."""
        # Générer l'île avec Perlin
        island_position = None
        for obj in self.tmx_data.objects:
            if obj.name.startswith("ile_quantique")  :                         
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
                    self.island_sprite = IslandSprite(island_surface, island_position[0], island_position[1])
                else:
                    self.island_sprite = IslandSprite(island_surface, 100, 100)
                    
                self.group.add(self.island_sprite)
    
    def spawn_unit(self, unit_class):
        """Fait apparaître une unité près de la plateforme correspondant à son équipe."""
        try:
            print(f"Tentative de création de l'unité: {unit_class.__name__}")
            
            # Déterminer l'équipe de l'unité à partir du nom de la classe
            if "Rouge" in unit_class.__name__:
                team = "red"
                base_spawn = self.red_platform_spawn
                print(f"Unité rouge -> plateforme rouge à {base_spawn}")
            else :
                team = "green"
                base_spawn = self.green_platform_spawn
                print(f"Unité verte -> plateforme verte à {base_spawn}")
            
            # Essayer plusieurs positions jusqu'à en trouver une libre
            max_attempts = 20
            for attempt in range(max_attempts):
                # Angle aléatoire en radians
                angle = random.uniform(0, 2 * math.pi)
                # Distance aléatoire entre 60 et 120 pixels de la plateforme
                distance = random.uniform(60, 120)
                
                # Calculer les coordonnées avec trigonométrie correcte
                spawn_x = base_spawn[0] + distance * math.cos(angle)
                spawn_y = base_spawn[1] + distance * math.sin(angle)
                
                # Vérifier que la position est libre (pas de collision avec d'autres unités)
                position_libre = True
                for existing_unit in self.units:
                    if existing_unit.is_alive:
                        dist_to_unit = math.sqrt((spawn_x - existing_unit.position[0])**2 + 
                                               (spawn_y - existing_unit.position[1])**2)
                        if dist_to_unit < 40:  # Distance minimale entre unités
                            position_libre = False
                            break
                
                # Vérifier que l'unité n'est pas trop proche de la plateforme
                dist_to_platform = math.sqrt((spawn_x - base_spawn[0])**2 + (spawn_y - base_spawn[1])**2)
                if dist_to_platform < self.spawn_radius:  # Utilisation de spawn_radius
                    position_libre = False
            else:
                # Si aucune position libre n'a été trouvée, utiliser la dernière calculée
                print("Aucune position libre trouvée, utilisation de la dernière position calculée")
            
            # Créer l'unité à la position de spawn calculée
            unit = unit_class(spawn_x, spawn_y)
            print(f"Unité créée avec succès: {unit} à la position ({spawn_x:.1f}, {spawn_y:.1f})")

            # Ajouter au système de combat et au groupe de sprites
            self.combat_system.add_unit(unit)
            self.units.append(unit)
            self.group.add(unit)

            return unit
        #Gestion erreurs
        except Exception as e:
            print(f"Erreur lors de la création de l'unité: {e}")
            import traceback
            traceback.print_exc()
            return None

    def draw_unit_popup(self):
        """Dessine le popup de sélection des unités."""
        if not self.show_unit_popup:
            return
        
        # Dimensions du popup
        popup_width = 300
        popup_height = len(self.unit_classes) * 30 + 40
        popup_x = (self.screen.get_width() - popup_width) // 2
        popup_y = (self.screen.get_height() - popup_height) // 2
        
        # Fond du popup
        popup_surface = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
        popup_surface.fill((0, 0, 0, 180))  # Fond noir semi-transparent
        pygame.draw.rect(popup_surface, (255, 255, 255), popup_surface.get_rect(), 2)
        
        # Titre
        title_text = self.font.render("Sélectionner une unité (E pour fermer)", True, (255, 255, 255))
        popup_surface.blit(title_text, (10, 10))
        
        # Liste des unités
        for i, (unit_name, unit_class) in enumerate(self.unit_classes):
            y_pos = 40 + i * 30
            color = (255, 255, 0) if i == self.popup_selection else (255, 255, 255)
            
            # Flèche pour l'unité sélectionnée
            if i == self.popup_selection:
                arrow_text = self.font.render(">", True, color)
                popup_surface.blit(arrow_text, (10, y_pos))
            
            # Nom de l'unité
            unit_text = self.font.render(unit_name, True, color)
            popup_surface.blit(unit_text, (25, y_pos))
        
        # Instructions
        instructions = [
            "Flèches: Naviguer",
            "Entrée: Sélectionner",
            "E: Fermer"
        ]
        for i, instruction in enumerate(instructions):
            inst_text = self.font.render(instruction, True, (200, 200, 200))
            popup_surface.blit(inst_text, (10, popup_height - 60 + i * 20))
        
        # Afficher le popup
        self.screen.blit(popup_surface, (popup_x, popup_y))

    def find_unit_at_position(self, world_x, world_y):
        """
        Trouve l'unité la plus proche de la position donnée dans le monde.
        Retourne l'unité si elle est dans la zone de tolérance, sinon None.
        """
        click_tolerance = 40  # Tolérance raisonnable maintenant que les coordonnées sont fixes
        closest_unit = None
        min_distance = float('inf')
        
        for unit in self.units:
            if not unit.is_alive:
                continue
                
            # Distance entre le clic et le centre de l'unité
            distance = math.sqrt((unit.position[0] - world_x) ** 2 + (unit.position[1] - world_y) ** 2)
            
            # Si l'unité est dans la zone de tolérance et plus proche que les autres
            if distance <= click_tolerance and distance < min_distance:
                closest_unit = unit
                min_distance = distance
        
        return closest_unit

    def run(self): 
        """Boucle principale du jeu."""
        clock = pygame.time.Clock()
        running = True
        
        while running: 
            dt = clock.tick(FPS) / TIME_STEP
            
            # Gestion des événements
            running = self.event_handler.handle_events()
            
            # Gestion des entrées continues
            self.input_manager.handle_continuous_input()
            
            # Mise à jour des systèmes
            self.updater.update_systems(dt)
            
            # Rendu
            self.renderer.render()
            
            pygame.display.flip()
        
        pygame.quit()