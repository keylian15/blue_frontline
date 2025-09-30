import pygame
import math
from Global import *
from Class.Perlin import Perlin

# Importation des modules gestionnaires
from Class.EventHandler import EventHandler
from Class.Renderer import Renderer
from Class.InputManager import InputManager
from Class.GameUpdater import GameUpdater
from Class.GameInitializer import GameInitializer
from Class.Petrole import Petrole
from Class.Piece import Piece
from Class.Timer import Timer

class IslandSprite(pygame.sprite.Sprite):
    """Sprite pour représenter une île générée."""
    
    def __init__(self, surface, x, y):
        super().__init__()
        self.image = surface
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

class Game : 
    """Classe principale du jeu."""

    def __init__(self, screen): 
        """Initialisation du jeu."""
        self.screen = screen
        
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
        
        # Système de combat et projectiles
        self.bullets = []  # Liste des projectiles actifs
        self.selected_unit = None  # Unité actuellement sélectionnée
        
        # Initialiser les gestionnaires après que les composants soient créés
        self.event_handler = EventHandler(self)
        self.renderer = Renderer(self)
        self.input_manager = InputManager(self)
        self.updater = GameUpdater(self)

        # État de pause
        self.paused = False
        
        # État de victoire
        self.game_won = False
        self.winner_team = None
        self.victory_font = pygame.font.Font(None, 72)
        self.button_font = pygame.font.Font(None, 36)
        
        # Obstacles
        self.setObstacles()
        # Zone quantiques
        self.quantique_area_name = []
        self.setQuantiqueArea()

    # --- Utilitaire audio: notification post-quantique (ne change pas la logique de génération) ---
    def _notify_quantum_audio(self):
        """Notifie le moteur audio des îles quantiques présentes, à appeler APRÈS quantique(...)."""
        try:
            if hasattr(self, "sound") and self.sound:
                centers = [(spr.rect.centerx, spr.rect.centery) for spr in getattr(self, "quantum_islands", [])]
                self.sound.set_quantum_islands(centers)
        except Exception:
            # On ne casse jamais la boucle de jeu pour du son
            pass

    def setObstacles(self):
        """Fonction permettant de récupérer les obstacles du jeu."""
        # On récupére les collisions générales.
        self.obstacles = [obj.as_points for obj in self.tmx_data.objects if obj.type == "Collision"]
        
        layer_name = "Collision_Haute" if self.hud.timer.maree_haute else "Collision_Basse"
        layer = next((l for l in self.tmx_data.layers if l.name == layer_name), None)
        if not layer:
            return
        
        for obj in layer:
            if obj.name == "Collision" : # Si l'objet est une collision 
                if hasattr(obj, 'points') :
                    self.obstacles.append(obj.points) 
                elif hasattr(obj, 'as_points') : 
                    self.obstacles.append(obj.as_points)
                    
    def setQuantiqueArea(self):
        """Fonction permettant de récupérer les zones quantique du jeu."""
        self.quantique_area = []
        self.quantique_area_hidden = []
        for obj in self.tmx_data.objects:
            if obj.name.startswith("ile_quantique_"):
                self.quantique_area.append(obj.as_points)
                self.quantique_area_hidden.append(obj.as_points)

    def quantique(self, name: str = None):
        """ Génération de l'île quantique pour toutes les îles quantiques découvertes dans la map.
        name : str Paramètre supplémentaire pour générer qu'une seule île
        """
        # Initialiser la liste des îles si elle n'existe pas
        if not hasattr(self, 'quantum_islands'):
            self.quantum_islands = []
        
        # Nettoyer les anciennes îles
        if not name :
            for old_island in self.quantum_islands:
                if old_island in self.group:
                    self.group.remove(old_island)
            self.quantum_islands.clear()

            # === AUDIO === informer que 0 île quantique est présente (prépare le one-shot 0->N)
            try:
                if hasattr(self, "sound") and self.sound:
                    self.sound.set_quantum_islands([])
            except Exception:
                pass

        # Fonction interne pour créer une île
        def create_island(obj):
            aligned_x = (obj.x // 32) * 32
            aligned_y = (obj.y // 32) * 32
            island_position = (aligned_x, aligned_y)

            island_width_tiles = int(obj.width // 32)
            island_height_tiles = int(obj.height // 32)

            tileset_surface_smooth = [
                self.deep_water_tileset,  # 0: Eau profonde
                self.water_tileset,       # 1: Eau peu profonde
                self.island_tileset       # 2: Île
            ]

            self.perlin = Perlin()
            island_matrix = self.perlin.generate_island(island_height_tiles, island_width_tiles)
            island_surface = self.perlin.smooth_map(island_matrix, tileset_surface_smooth)

            island_sprite = IslandSprite(island_surface, island_position[0], island_position[1])
            self.quantum_islands.append(island_sprite)
            self.group.add(island_sprite)

        # Générer toutes les îles trouvées
        for obj in self.tmx_data.objects:
            if name :
                if obj.name == name:
                    create_island(obj)
            else : 
                if obj.name.startswith("ile_quantique") and obj.name in self.quantique_area_name:
                    create_island(obj)

    def find_unit_at_position(self, world_x, world_y):
        """
        Trouve l'unité (ou plateforme) la plus proche de la position donnée dans le monde.
        Retourne l'unité si elle est dans la zone de tolérance, sinon None.
        """
        click_tolerance = 60 
        closest_unit = None
        min_distance = float('inf')
        
        for unit in self.units:
            if not unit.is_alive:
                continue
                
            # Distance entre le clic et le centre de l'unité
            distance = math.sqrt((unit.position[0] - world_x) ** 2 + (unit.position[1] - world_y) ** 2)
            
            # Ajuster la tolérance selon le type d'unité
            tolerance = 60 if hasattr(unit, 'is_platform') and unit.is_platform else 40
            
            # Si l'unité est dans la zone de tolérance et plus proche que les autres
            if distance <= tolerance and distance < min_distance:
                closest_unit = unit
                min_distance = distance
        
        return closest_unit

    def select_unit(self, unit):
        """Sélectionne une unité et désélectionne les autres."""
        # Désélectionner toutes les unités
        for u in self.units:
            if hasattr(u, 'is_selected'):
                u.is_selected = False
        
        # Sélectionner la nouvelle unité
        if unit and hasattr(unit, 'is_selected'):
            unit.is_selected = True
            self.selected_unit = unit
        else:
            self.selected_unit = None

    def update_bullets(self, dt):
        """Met à jour tous les projectiles."""
        bullets_to_remove = []
        
        for bullet in self.bullets:
            if not bullet.is_alive:
                bullets_to_remove.append(bullet)
                continue
                
            # Mettre à jour le projectile
            bullet.update(dt)
            
            # Vérifier les collisions avec les unités
            for unit in self.units:
                if bullet.check_collision(unit):
                    break  # Le projectile s'est détruit lors de la collision
        
        # Supprimer les projectiles morts
        for bullet in bullets_to_remove:
            self.bullets.remove(bullet)

    def on_platform_destroyed(self, platform):
        """Appelé quand une plateforme pétrolière est détruite."""
        # Déterminer l'équipe gagnante
        if platform.team == "red":
            self.winner_team = "green"
        else:
            self.winner_team = "red"
        
        self.game_won = True
        self.paused = True  # Mettre le jeu en pause
    
    def draw_victory_screen(self):
        """Dessine l'écran de victoire."""
        if not self.game_won:
            return
        
        # Overlay semi-transparent
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Message de victoire
        winner_text = "ÉQUIPE VERTE" if self.winner_team == "green" else "ÉQUIPE ROUGE"
        victory_message = f"{winner_text} A GAGNÉ !"
        victory_surface = self.victory_font.render(victory_message, True, (255, 255, 0))
        victory_rect = victory_surface.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 - 100))
        self.screen.blit(victory_surface, victory_rect)
        
        # Sous-message
        sub_message = "Plateforme pétrolière adverse détruite !"
        sub_surface = self.button_font.render(sub_message, True, (255, 255, 255))
        sub_rect = sub_surface.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 - 50))
        self.screen.blit(sub_surface, sub_rect)
        
        # Position pour les boutons
        mouse_pos = pygame.mouse.get_pos()
        button_width, button_height = 300, 60
        center_x = self.screen.get_width() // 2
        
        # Bouton "Nouvelle partie"
        restart_button_x = center_x - button_width // 2
        restart_button_y = self.screen.get_height() // 2 + 30
        
        mouse_on_restart = (restart_button_x <= mouse_pos[0] <= restart_button_x + button_width and 
                           restart_button_y <= mouse_pos[1] <= restart_button_y + button_height)
        
        restart_color = (100, 200, 100) if mouse_on_restart else (50, 150, 50)
        restart_border = (150, 255, 150) if mouse_on_restart else (100, 200, 100)
        
        restart_rect = pygame.Rect(restart_button_x, restart_button_y, button_width, button_height)
        pygame.draw.rect(self.screen, restart_color, restart_rect)
        pygame.draw.rect(self.screen, restart_border, restart_rect, 3)
        
        restart_text = "Nouvelle Partie"
        restart_surface = self.button_font.render(restart_text, True, (255, 255, 255))
        restart_text_rect = restart_surface.get_rect(center=restart_rect.center)
        self.screen.blit(restart_surface, restart_text_rect)
        
        # Bouton "Retour au menu"
        menu_button_x = center_x - button_width // 2
        menu_button_y = restart_button_y + button_height + 20
        
        mouse_on_menu = (menu_button_x <= mouse_pos[0] <= menu_button_x + button_width and 
                        menu_button_y <= mouse_pos[1] <= menu_button_y + button_height)
        
        menu_color = (200, 100, 100) if mouse_on_menu else (150, 50, 50)
        menu_border = (255, 150, 150) if mouse_on_menu else (200, 100, 100)
        
        menu_rect = pygame.Rect(menu_button_x, menu_button_y, button_width, button_height)
        pygame.draw.rect(self.screen, menu_color, menu_rect)
        pygame.draw.rect(self.screen, menu_border, menu_rect, 3)
        
        menu_text = "Retour au Menu"
        menu_surface = self.button_font.render(menu_text, True, (255, 255, 255))
        menu_text_rect = menu_surface.get_rect(center=menu_rect.center)
        self.screen.blit(menu_surface, menu_text_rect)
        
        # Stocker les positions des boutons pour la détection de clic
        self.restart_button_rect = restart_rect
        self.menu_button_rect = menu_rect
    
    def handle_victory_click(self, mouse_pos):
        """Gère les clics sur l'écran de victoire."""
        if hasattr(self, 'restart_button_rect') and self.restart_button_rect.collidepoint(mouse_pos):
            self.restart_game()
        elif hasattr(self, 'menu_button_rect') and self.menu_button_rect.collidepoint(mouse_pos):
            self.return_to_menu()
    
    def refresh_all_references(self, game):
        """Actualise toutes les références des gestionnaires après reconstruction de la map."""
        # Réinitialiser les gestionnaires pour qu'ils utilisent les nouvelles références
        self.event_handler.game = game
        self.initializer.game = game
        self.updater.game = game
        self.input_manager.game = game
        self.renderer.game = game
        
        # S'assurer que les unités sont dans le nouveau groupe
        if hasattr(self, 'units') and self.units:
            for unit in self.units:
                if unit.is_alive:
                    self.group.add(unit)
                    unit.game = game
                if hasattr(unit, 'refresh_all_references') : 
                    unit.refresh_all_references(game)
        
        # S'assurer que la caméra est dans le nouveau groupe
        if hasattr(self, 'camera') and self.camera not in self.group.sprites():
            self.group.add(self.camera)
    
    def restart_game(self):
        """Redémarre le jeu."""
        # Réinitialiser les variables de victoire
        self.game_won = False
        self.winner_team = None
        self.paused = False
        
        # Vider toutes les listes
        self.units.clear()
        self.bullets.clear()
        if hasattr(self, 'plateformes'):
            self.plateformes.clear()
        
        # Vider le groupe de sprites
        self.group.empty()
        self.combat_system.projectiles.empty()
        self.combat_system.units.empty()
        
        # Réinitialiser les systèmes de jeu
        self.initializer.init_camera()
        self.initializer.init_game_systems()
        
        # Remettre les compteurs à zéro
        self.hud.petrole = Petrole()  # Valeur de départ pétrole
        self.hud.piece = Piece()      # Valeur de départ pièces
        self.hud.timer = Timer()      # Réinstancie le timer
    
    def return_to_menu(self):
        """Retourne au menu principal."""
        self.game_running = False

    def run(self): 
        """Boucle principale du jeu."""
        clock = pygame.time.Clock()
        running = True
        self.game_running = True  # Variable pour contrôler le retour au menu
        
        while running and self.game_running: 
            dt = clock.tick(FPS) / TIME_STEP
            
            # Gestion des événements
            running = self.event_handler.handle_events()
            
            # Gestion des entrées continues
            if not self.paused:
                self.input_manager.handle_continuous_input()
            
                # Mise à jour des systèmes
                self.updater.update_systems(dt, self)
            
            # Rendu
            self.renderer.render()
            
            # Afficher l'écran de victoire si le jeu est gagné
            if self.game_won:
                self.draw_victory_screen()
            
            pygame.display.flip()
        
        if not self.game_running:
            return  # Retourner au menu
        
        pygame.quit()
