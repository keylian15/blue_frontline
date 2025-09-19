import time
import pygame, pytmx, pyscroll, math, random
from Class.Camera import *
from Class.Combat import CombatSystem
from Class.units.Chaloupe import ChaloupeRouge, ChaloupeVerte
from Class.units.Bateau import BateauRouge, BateauVert
from Class.units.Eclaireur import EclaireurRouge, EclaireurVert
from Class.units.Paquebot import PaquebotRouge, PaquebotVert
from Class.units.Sousmarin import SousMarinRouge, SousMarinVert
from Global import *
from Class.Camera import *
from Class.Perlin import *
from Class.Hud import *
from Class.Petrole import *
from Class.Piece import *
from Class.Timer import *
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
        # Créer le renderer avec la taille initiale, sera mis à jour avec le zoom
        self.map_layer = pyscroll.orthographic.BufferedRenderer(map_data, self.screen.get_size()) 
        
        # Les data de tilesets
        self.island_tileset = load_tileset(ISLAND_TILESET_PATH)
        self.deep_water_tileset = load_tileset(DEEP_WATER_TILESET_PATH)
        self.water_tileset = load_tileset(WATER_TILESET_PATH)
        
        # Créer la caméra
        camera_position = self.tmx_data.get_object_by_name("spawn") # Récupère la position de la caméra depuis Tiled
        self.camera = Camera(camera_position.x, camera_position.y, self.screen.get_size(), (camera_position.x, camera_position.y))
        # Récupérer les dimensions de la map pour limiter la caméra
        self.map_width =self.tmx_data.width *self.tmx_data.tilewidth
        self.map_height =self.tmx_data.height *self.tmx_data.tileheight
        print(f"Dimensions de la map: {self.map_width}x{self.map_height}")
        
        # Créer la caméra avec les limites de la map
        camera_position =self.tmx_data.get_object_by_name("spawn") # Récupère la position de la caméra depuis Tiled
        self.camera = Camera(camera_position.x, camera_position.y, self.screen.get_size(), (self.map_width, self.map_height))
        
        # Dessiner le groupe de calques
        self.group = pyscroll.PyscrollGroup(map_layer=self.map_layer, default_layer=3)
        self.group.add(self.camera)
        
        # === Système de combat et unités ===
        self.combat_system = CombatSystem()
        self.units = []
        self.selected_unit = None
        
        # === Positions de spawn des unités ===
        # Coordonnées approximatives des plateformes sur la map
        self.green_platform_spawn = (96, 512)  # Position plateforme verte
        self.red_platform_spawn = (1824, 512)  # Position plateforme rouge
        self.spawn_radius = 80  # Rayon autour des plateformes pour éviter la superposition
        
        # === Système de popup pour sélection d'unités ===
        self.show_unit_popup = False
        self.unit_classes = [
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
        self.popup_selection = 0
        
        # Police pour le popup
        pygame.font.init()
        self.font = pygame.font.Font(None, 24)

        # HUD
        self.hud = Hud(self.screen)
        
        # Variable pour suivre les changements de zoom
        self.last_zoom_level = self.camera.zoom_level
            
    def update_renderer_for_zoom(self):
        """Met à jour le renderer pyscroll pour le nouveau niveau de zoom."""
        if self.camera.zoom_level != self.last_zoom_level:
            # Calculer la nouvelle taille effective de rendu
            effective_width = int(self.screen.get_width() / self.camera.zoom_level)
            effective_height = int(self.screen.get_height() / self.camera.zoom_level)
            
            # Récréer le renderer avec la nouvelle taille
            map_data = pyscroll.data.TiledMapData(self.tmx_data)
            self.map_layer = pyscroll.orthographic.BufferedRenderer(map_data, (effective_width, effective_height))
            
            # Recréer le groupe avec le nouveau map_layer
            self.group = pyscroll.PyscrollGroup(map_layer=self.map_layer, default_layer=3)
            self.group.add(self.camera)
            
            # Ajouter tous les sprites existants au nouveau groupe
            for unit in self.units:
                if unit.is_alive:
                    self.group.add(unit)
            
            # Ajouter l'île quantique si elle existe
            if hasattr(self, 'island_sprite'):
                self.group.add(self.island_sprite)
            
            self.last_zoom_level = self.camera.zoom_level
            
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
                
    def handle_input(self):
        """Gère les entrées clavier pour déplacer la caméra et gérer le zoom."""
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
            time.sleep(0.2)

        # === Gestion du zoom ===
        if pressed[pygame.K_p]:  # Touche P pour dézoomer
            self.camera.zoom_out()
        if pressed[pygame.K_m]:  # Touche M pour zoomer
            self.camera.zoom_in()

        # On déplace la caméra seulement si il y a un déplacement
        if dx or dy:  
            self.camera.move(dx, dy)
            
    
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
        
        # On crée une horloge pour gérer les fps
        clock = pygame.time.Clock()
        running = True

        while running: 
            dt = clock.tick(FPS) / TIME_STEP  # Delta time en secondes
            
            # Gestion des événements
            for event in pygame.event.get(): 

                if event.type == pygame.QUIT: 
                    running = False

                # Gere la gestion de pétrole
                self.hud.petrole.handle_event(event)
                self.hud.timer.handle_event(event)


                # Clic droit pour générer l'île

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                    self.quantique()            

            
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_e:
                        # Ouvrir/fermer le popup de sélection d'unités
                        self.show_unit_popup = not self.show_unit_popup
                        self.popup_selection = 0
                        print(f"Popup {'ouvert' if self.show_unit_popup else 'fermé'}")

                    elif self.show_unit_popup:
                        # Navigation dans le popup
                        if event.key == pygame.K_UP:
                            self.popup_selection = (self.popup_selection - 1) % len(self.unit_classes)
                            print(f"Sélection précédente: {self.popup_selection}")
                        elif event.key == pygame.K_DOWN:
                            self.popup_selection = (self.popup_selection + 1) % len(self.unit_classes)
                            print(f"Sélection suivante: {self.popup_selection}")
                        elif event.key == pygame.K_RETURN:
                            # Sélectionner l'unité
                            try:
                                unit_name, unit_class = self.unit_classes[self.popup_selection]
                                print(f"Unité sélectionnée: {unit_name}")
                                self.spawn_unit(unit_class)
                                self.show_unit_popup = False
                            except Exception as e:
                                print(f"Erreur lors de la sélection de l'unité: {e}")
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and not self.show_unit_popup:  # Clic gauche
                        mouse_x, mouse_y = pygame.mouse.get_pos()
                        
                        # Conversion screen vers world coordinates avec zoom
                        camera_center = self.camera.rect.center
                        screen_center_x = self.screen.get_width() // 2
                        screen_center_y = self.screen.get_height() // 2
                        
                        # Transformation inverse adaptée au zoom
                        offset_x = (mouse_x - screen_center_x) / self.camera.zoom_level
                        offset_y = (mouse_y - screen_center_y) / self.camera.zoom_level
                        world_x = camera_center[0] + offset_x
                        world_y = camera_center[1] + offset_y
                        
                        # Chercher une unité à cette position
                        clicked_unit = self.find_unit_at_position(world_x, world_y)
                        
                        if clicked_unit:
                            self.selected_unit = clicked_unit
                            print(f"Unité sélectionnée: {clicked_unit.__class__.__name__}")
                        elif self.selected_unit and self.selected_unit.is_alive:
                            # Déplacer l'unité sélectionnée vers la position cliquée
                            if hasattr(self.selected_unit, 'move_to_position'):
                                self.selected_unit.move_to_position(world_x, world_y)
                                print(f"Déplacement de {self.selected_unit.__class__.__name__}")
                        else:
                            self.selected_unit = None
            

            
            
            # Mettre à jour la caméra (CRITIQUE : synchronise rect.center avec position)
            self.camera.update()
            
            # Mettre à jour les unités
            for unit in self.units:
                unit.update(dt, self.combat_system, self.screen, 
                          (self.camera.position[0] - (self.screen.get_width() // 2) / self.camera.zoom_level,
                           self.camera.position[1] - (self.screen.get_height() // 2) / self.camera.zoom_level))
            
            # Mettre à jour le système de combat
            self.combat_system.update(dt)
            
            # On met a jour les groupes
            self.group.update()
            # On centre le groupe sur la caméra
            self.group.center(self.camera.rect.center)
            
            # Rendu avec mise à l'échelle pour le zoom
            if self.camera.zoom_level != 1.0:
                # Créer une surface temporaire à la taille effective
                temp_surface = pygame.Surface((int(self.screen.get_width() / self.camera.zoom_level), 
                                             int(self.screen.get_height() / self.camera.zoom_level)))
                
                # Dessiner le groupe sur la surface temporaire
                self.group.draw(temp_surface)
                
                # Redimensionner et dessiner sur l'écran principal
                scaled_surface = pygame.transform.scale(temp_surface, self.screen.get_size())
                self.screen.blit(scaled_surface, (0, 0))
            else:
                # Rendu normal sans zoom
                self.group.draw(self.screen)
            # On dessine le hud
            if self.hud.show :
                self.hud.draw(self.screen)

            
            # On gère les entrées
            self.handle_input()
            
            # Mettre à jour le renderer si le zoom a changé
            self.update_renderer_for_zoom()
            
            # Dessiner les projectiles
            camera_offset = (self.camera.position[0] - (self.screen.get_width() // 2) / self.camera.zoom_level,
                           self.camera.position[1] - (self.screen.get_height() // 2) / self.camera.zoom_level)
            
            for projectile in self.combat_system.projectiles:
                projectile_screen_x = (projectile.position[0] - camera_offset[0]) * self.camera.zoom_level
                projectile_screen_y = (projectile.position[1] - camera_offset[1]) * self.camera.zoom_level
                
                # Adapter la taille du projectile au zoom
                scaled_image = pygame.transform.scale(
                    projectile.image, 
                    (int(projectile.image.get_width() * self.camera.zoom_level),
                     int(projectile.image.get_height() * self.camera.zoom_level))
                )
                projectile_rect = scaled_image.get_rect(center=(projectile_screen_x, projectile_screen_y))
                self.screen.blit(scaled_image, projectile_rect)
            
            # Dessiner les barres de vie des unités
            for unit in self.units:
                unit.draw_health_bar(self.screen, camera_offset)
            
            # Surligner l'unité sélectionnée avec un cercle jaune qui suit l'unité
            if self.selected_unit and self.selected_unit.is_alive:
                unit_screen_x = (self.selected_unit.position[0] - camera_offset[0]) * self.camera.zoom_level
                unit_screen_y = (self.selected_unit.position[1] - camera_offset[1]) * self.camera.zoom_level
                
                # Vérifier que l'unité est visible à l'écran
                if (-50 <= unit_screen_x <= self.screen.get_width() + 50 and 
                    -50 <= unit_screen_y <= self.screen.get_height() + 50):
                    
                    # Cercle jaune extérieur (plus visible avec animation)
                    import time
                    pulse = abs(math.sin(time.time() * 3)) * 5 + 20  # Animation de pulsation
                    pulse_scaled = pulse * self.camera.zoom_level
                    
                    pygame.draw.circle(self.screen, (255, 255, 0), 
                                     (int(unit_screen_x), int(unit_screen_y)), int(pulse_scaled + 8 * self.camera.zoom_level), 3)
                    
                    # Cercle jaune intérieur (fixe)
                    pygame.draw.circle(self.screen, (255, 255, 0), 
                                     (int(unit_screen_x), int(unit_screen_y)), int(18 * self.camera.zoom_level), 2)
                    
                    # Point central pour bien marquer la position
                    pygame.draw.circle(self.screen, (255, 255, 0), 
                                     (int(unit_screen_x), int(unit_screen_y)), int(3 * self.camera.zoom_level), 0)
            
            # Dessiner le popup de sélection des unités
            self.draw_unit_popup()            
            pygame.display.flip()
            
        pygame.quit()