import pygame, math
from Global import *
from Class.Perlin import Perlin

# Importation des modules gestionnaires
from Class.EventHandler import EventHandler
from Class.Renderer import Renderer
from Class.GameUpdater import GameUpdater
from Class.GameInitializer import GameInitializer
from Class.Petrole import Petrole
from Class.Piece import Piece
from Class.Timer import Timer
from Class.units import Unit
from Class.AchievementNotification import AchievementNotificationManager
from Class.units.IA.IA_Eclaireur import SimpleGrid, make_grid_adapter_from_simplegrid
from Class.units import PlateformePetroliere
from Class.AchievementsSystemRouge import AchievementsSystemRouge
from Class.AchievementsSystemVert import AchievementsSystemVert


class IslandSprite(pygame.sprite.Sprite):
    """Sprite pour représenter une île générée."""
    
    def __init__(self, name: str, surface: pygame.Surface, x: int, y: int):
        """Fonction permettant d'initialiser un sprite d'île.

        Args:
            name (str): Le nom de l'île.
            surface (pygame.Surface): La surface de l'île.
            x (int): La position x de l'île.
            y (int): La position y de l'île.
        """
        super().__init__()
        self.image = surface
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.name = name

class Game : 
    """Classe principale du jeu."""

    def __init__(self, screen: pygame.surface, mode: str = "normal"): 
        """Fonction permettant d'initialiser le jeu.

        Args:
            screen (pygame.surface): La surface d'affichage du jeu.
            mode (str, optional): Le mode de jeu ("normal", "tuto", etc.). Defaults to "normal".
        """
        # Variables de base
        self.mode = mode
        self.screen = screen
    
        # Systèmes de succès (seront assignés par le menu)
        self.achievements_system = None
        self.achievements_system_rouge = None
        self.achievements_system_vert = None
        
        # Gestionnaire de notifications de succès
        self.notification_manager = AchievementNotificationManager(screen)
            
        # La liste des iles quantiques GRAPHIQUES
        self.quantum_islands = [] 
        
        # Initialiser les gestionnaires
        self.initializer = GameInitializer(self)
        
        # Variable pour suivre les changements de zoom
        self.last_zoom_level = self.camera.zoom_level
        
        # Système de combat et projectiles
        self.bullets = []  # Liste des projectiles actifs
        self.selected_unit = None  # Unité actuellement sélectionnée
        
        # Initialiser les gestionnaires après que les composants soient créés
        self.event_handler = EventHandler(self)
        self.renderer = Renderer(self)
        self.updater = GameUpdater(self)

        # État de pause
        self.paused = False
        
        # État de victoire
        self.game_won = False
        self.winner_team = None
        self.victory_font = pygame.font.Font(None, 72)
        self.button_font = pygame.font.Font(None, 36)
        
        # Statistiques de jeu pour les succès
        self.game_start_time = pygame.time.get_ticks()
        self.units_created_this_game = set()
        self.units_lost_this_game = 0

        # Obstacles
        self.setObstacles()
        # Zone quantiques
        self.quantique_area_name = []
        self.setQuantiqueArea()
        self.build_nav_grid()
        
        if self.mode == "tuto":
            # Activer le didacticiel
            from Class.Didactitiel.TutorialManager import TutorialManager
            self.tutorial = TutorialManager(self)
        elif self.mode == "PVP": 
            # Ici on désactive les IA
            self.set_ia_setting(False, "green")
            self.set_ia_setting(False, "red")
        elif self.mode == "PVE":
            # On active l'IA pour la team Verte
            self.set_ia_setting(True, "green")
            self.set_ia_setting(False, "red")
            
        elif self.mode == "EVE":
            # On active l'IA pour la team Verte et la team Red
            self.set_ia_setting(True, "green")
            self.set_ia_setting(True, "red")
                
        # Système de succès (sera assigné par le menu)
        self.achievements_system = None
        
        # Gestionnaire de notifications de succès
        self.notification_manager = AchievementNotificationManager(screen)
        
    def set_ia_setting(self, ia_setting: bool, team: str):
        """
        Définit les paramètres IA pour l'équipe demandée.
        """
        settings = get_gameplay_settings()

        for key in settings["AI_ACTIVATION"]:
            if team == "red":
                if key.endswith("Rouge"):
                    settings["AI_ACTIVATION"][key] = ia_setting  
            else:
                if not key.endswith("Rouge"):
                    settings["AI_ACTIVATION"][key] = ia_setting
        
        set_gameplay_setting(settings)

    # --- Utilitaire audio: notification post-quantique (ne change pas la logique de génération) ---
    def notify_quantum_audio(self):
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
        self.obstacles = []
        for obj in self.tmx_data.objects:
            if obj.type == "Collision":
                if hasattr(obj, 'points'):
                    self.obstacles.append(obj.points)
                elif hasattr(obj, "as_points"):
                    self.obstacles.append(obj.as_points)
        self.eau_peu_profondes = []
        
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
            if obj.name == "Eau_peu_profonde" : 
                if hasattr(obj, 'points') :
                    self.eau_peu_profondes.append(obj.points)
                elif hasattr(obj, 'as_points') : 
                    self.eau_peu_profondes.append(obj.as_points)
                    
    def setQuantiqueArea(self):
        """Fonction permettant de récupérer les zones quantique du jeu."""
        self.quantique_area = [] # La liste des zones quantique
        self.quantique_area_hidden = [] # La liste des zones quantique cachées
        for obj in self.tmx_data.objects:
            if obj.name.startswith("ile_quantique_"):
                self.quantique_area.append(obj.as_points)
                self.quantique_area_hidden.append(obj.as_points)

    def quantique(self, name: str = None):
        """Génération de l'île quantique pour toutes les îles quantiques découvertes dans la map.

        Args:
            name (str, optional): Le nom d'une île si on veut en générer qu'une seule. Defaults to None.
        """        
        # Suivre les statistiques pour les succès (îles quantiques) - global pour les deux équipes
        if hasattr(self, 'achievements_system_rouge') and self.achievements_system_rouge:
            self.achievements_system_rouge.track_quantum_island_activated()
        if hasattr(self, 'achievements_system_vert') and self.achievements_system_vert:
            self.achievements_system_vert.track_quantum_island_activated()
        
        # Nettoyer les anciennes îles
        if not name :
            for old_island in self.quantum_islands:
                if old_island in self.group:
                    self.group.remove(old_island)
            self.quantum_islands.clear()

        # Fonction interne pour créer une île
        def create_island(obj: "tmx.TiledObject" ):
            """Fonction interne pour créer une île quantique.

            Args:
                obj (tmx.TiledObject): L'objet
            """
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
            from Global import get_gameplay_settings
            self.perlin = Perlin(get_gameplay_settings()["OCTAVES"])
            island_matrix = self.perlin.generate_island(island_height_tiles, island_width_tiles)
            island_surface = self.perlin.smooth_map(island_matrix, tileset_surface_smooth)

            island_sprite = IslandSprite(obj.name, island_surface, island_position[0], island_position[1])
            island_sprite.matrix = island_matrix # On stocke la matrice de l'île pour les collisions
            self.quantum_islands.append(island_sprite)
            self.group.add(island_sprite)

        # Générer toutes les îles trouvées
        for obj in self.tmx_data.objects:
            if name :
                if obj.name == name:
                    create_island(obj)
                    
                    # On joue le son 
                    self.notify_quantum_audio()
            else : 
                if obj.name.startswith("ile_quantique") and obj.name in self.quantique_area_name:
                    create_island(obj)
                    
                    # On joue le son 
                    self.notify_quantum_audio()

    def find_unit_at_position(self, world_x: float, world_y: float, exclude_unit=None):
        """Trouve l'unité (ou plateforme) la plus proche de la position donnée dans le monde,
        en ignorant une unité spécifique si elle est fournie.

        Args:
            world_x (float): Coordonnée x de la position dans le monde.
            world_y (float): Coordonnée y de la position dans le monde.
            exclude_unit (Unit, optional): Unité à ignorer lors de la recherche.

        Returns:
            Unit | None: L'unité la plus proche de la position donnée, ou None si aucune n'est trouvée.
        """

        closest_unit = None
        min_distance = float('inf')
        
        for unit in self.units:
            # Ignorer l'unité exclue ou les unités mortes
            if unit == exclude_unit or not unit.is_alive:
                continue

            # Distance entre le point et le centre de l'unité
            distance = math.sqrt((unit.position[0] - world_x) ** 2 + (unit.position[1] - world_y) ** 2)

            # Tolérance différente si c’est une plateforme
            tolerance = 60 if getattr(unit, 'is_platform', False) else 40

            # Vérifie si l'unité est dans la zone de tolérance et plus proche
            if distance <= tolerance and distance < min_distance:
                closest_unit = unit
                min_distance = distance

        return closest_unit

    def select_unit(self, unit: Unit):
        """Sélectionne une unité et désélectionne les autres.

        Args:
            unit (Unit): L'unité à sélectionner.
        """
        # Désélectionner toutes les unités
        for u in self.units:
            if hasattr(u, 'is_selected'):
                u.is_selected = False

        # Sélectionner la nouvelle unité
        if unit and hasattr(unit, 'is_selected'):
            if unit.unit_type != "pompe_petroliere":  # Ne pas sélectionner la pompe pétrolière
                unit.is_selected = True
                self.selected_unit = unit
                self.hud.update_selected_unit(unit)
        else:
            self.selected_unit = None

    def build_nav_grid(self):
        """
        Construit/actualise la grille de navigation IA (A*).
        
        Remplit:
            self.nav_grid_raw      : SimpleGrid (walkable + coûts)
            self.nav_grid_adapter  : GridAdapter prêt pour ScoutAI
        
        OPTIMISATION : Utilise des bounding boxes au lieu de point_in_polygon
        sur chaque cellule, ce qui réduit drastiquement le temps de calcul.
        """
        import time
        start_time = time.time()
        
        tile_size = 32  # Taille d'une cellule en pixels
        width_in_cells = self.map_width // tile_size
        height_in_cells = self.map_height // tile_size

        # Créer la grille vide (tout est navigable par défaut)
        grid = SimpleGrid(width_in_cells, height_in_cells, cell_size=tile_size)

        # ========================================================================
        # ÉTAPE 1 : Marquer les OBSTACLES (îles, rochers, etc.)
        # ========================================================================
        obstacle_count = 0
        for obstacle_poly in self.obstacles:
            if not obstacle_poly or len(obstacle_poly) == 0:
                continue
            
            # Calculer la bounding box du polygone
            try:
                min_x = int(min(p[0] for p in obstacle_poly) // tile_size)
                max_x = int(max(p[0] for p in obstacle_poly) // tile_size)
                min_y = int(min(p[1] for p in obstacle_poly) // tile_size)
                max_y = int(max(p[1] for p in obstacle_poly) // tile_size)
            except (ValueError, TypeError):
                continue  # Polygone invalide, on skip
            
            # Clamper aux limites de la grille
            min_x = max(0, min_x)
            max_x = min(width_in_cells - 1, max_x)
            min_y = max(0, min_y)
            max_y = min(height_in_cells - 1, max_y)
            
            # Marquer toutes les cellules dans la bounding box comme non-navigables
            for cx in range(min_x, max_x + 1):
                for cy in range(min_y, max_y + 1):
                    grid.walkable[cx][cy] = False
                    grid.costs[cx][cy] = float('inf')
            
            obstacle_count += 1

        # ========================================================================
        # ÉTAPE 2 : Marquer les EAUX PEU PROFONDES (navigable mais lent)
        # ========================================================================
        shallow_count = 0
        for eau_poly in self.eau_peu_profondes:
            if not eau_poly or len(eau_poly) == 0:
                continue
            
            try:
                min_x = int(min(p[0] for p in eau_poly) // tile_size)
                max_x = int(max(p[0] for p in eau_poly) // tile_size)
                min_y = int(min(p[1] for p in eau_poly) // tile_size)
                max_y = int(max(p[1] for p in eau_poly) // tile_size)
            except (ValueError, TypeError):
                continue
            
            min_x = max(0, min_x)
            max_x = min(width_in_cells - 1, max_x)
            min_y = max(0, min_y)
            max_y = min(height_in_cells - 1, max_y)
            
            for cx in range(min_x, max_x + 1):
                for cy in range(min_y, max_y + 1):
                    # Seulement si la cellule n'est pas déjà bloquée par un obstacle
                    if grid.walkable[cx][cy]:
                        grid.costs[cx][cy] = 2.0  # Coût élevé (ralentissement)
            
            shallow_count += 1

        # ========================================================================
        # ÉTAPE 3 : Marquer les ZONES QUANTIQUES CACHÉES (prioritaires pour l'IA)
        # ========================================================================
        quantum_count = 0
        for quant_poly in self.quantique_area_hidden:
            if not quant_poly or len(quant_poly) == 0:
                continue
            
            try:
                min_x = int(min(p[0] for p in quant_poly) // tile_size)
                max_x = int(max(p[0] for p in quant_poly) // tile_size)
                min_y = int(min(p[1] for p in quant_poly) // tile_size)
                max_y = int(max(p[1] for p in quant_poly) // tile_size)
            except (ValueError, TypeError):
                continue
            
            min_x = max(0, min_x)
            max_x = min(width_in_cells - 1, max_x)
            min_y = max(0, min_y)
            max_y = min(height_in_cells - 1, max_y)
            
            for cx in range(min_x, max_x + 1):
                for cy in range(min_y, max_y + 1):
                    # Seulement si navigable
                    if grid.walkable[cx][cy]:
                        grid.costs[cx][cy] = 0.5  # Coût faible (encourage l'exploration)
            
            quantum_count += 1

        # ========================================================================
        # FINALISATION
        # ========================================================================
        self.nav_grid_raw = grid
        self.nav_grid_adapter = make_grid_adapter_from_simplegrid(grid)

    def get_hidden_quantum_polygons(self):
        """
        Renvoie les polygones des zones quantiques NON révélées.
        -> Ça correspond à ce que l'Éclaireur doit aller découvrir.
        """
        return self.quantique_area_hidden

    def get_base_position(self, team: str):
        """
        Renvoie la position vers laquelle l'unité doit rentrer à la fin.
        On utilise les plateformes pétrolières comme 'base'.

        team : "red" ou "green"
        """
        # Les plateformes sont construites dans GameInitializer.init_game_systems()
        # et stockées dans self.plateformes = {"red": plateforme_rouge, "green": plateforme_verte}
        plateforme = self.plateformes.get(team)
        if plateforme is None:
            # fallback : si jamais l'équipe n'existe pas, on renvoie juste la rouge
            plateforme = self.plateformes.get("red")

        # PlateformePetroliere a déjà self.position = [x, y]
        return (plateforme.position[0], plateforme.position[1])


    def on_platform_destroyed(self, platform: PlateformePetroliere):
        """Appelé quand une plateforme pétrolière est détruite.

        Args:
            platform (PlateformePetroliere): La plateforme détruite.
        """

        # Déterminer l'équipe gagnante
        if platform.team == "red":
            self.winner_team = "green"
        else:
            self.winner_team = "red"
        
        # Suivre les statistiques pour les succès de l'équipe gagnante
        if self.winner_team == "red" and hasattr(self, 'achievements_system_rouge') and self.achievements_system_rouge:
            self.achievements_system_rouge.track_platform_destroyed()
            self.achievements_system_rouge.track_game_won()
        elif self.winner_team == "green" and hasattr(self, 'achievements_system_vert') and self.achievements_system_vert:
            self.achievements_system_vert.track_platform_destroyed()
            self.achievements_system_vert.track_game_won()
        
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
    
    def handle_victory_click(self, mouse_pos:tuple[float, float]):
        """Gère les clics sur l'écran de victoire.

        Args:
            mouse_pos (tuple[float, float]): La position du clic de la souris.
        """
        
        if hasattr(self, 'restart_button_rect') and self.restart_button_rect.collidepoint(mouse_pos):
            self.restart_game()
        elif hasattr(self, 'menu_button_rect') and self.menu_button_rect.collidepoint(mouse_pos):
            self.return_to_menu()
    
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
        self.hud.petrole_red = Petrole()  # Valeur de départ pétrole
        self.hud.petrole_green = Petrole()  # Valeur de départ pétrole
        self.hud.piece_red = Piece()      # Valeur de départ pièces
        self.hud.piece_green = Piece()      # Valeur de départ pièces
        self.hud.timer = Timer()      # Réinstancie le timer
    
    def return_to_menu(self):
        """Retourne au menu principal."""
        
        self.game_running = False

    def run(self):
        """
        Boucle principale du jeu.
        """
        clock = pygame.time.Clock()
        running = True
        self.game_running = True

        # Mode tuto : désactiver les IA
        if self.mode == "tuto":
            self.paused = True
            from Global import get_gameplay_settings
            settings = get_gameplay_settings()
            for key in settings["AI_ACTIVATION"] :
                settings["AI_ACTIVATION"][key] = False
        else : 
            # Initialiser les systèmes de succès pour les deux équipes si ils ne sont pas déjà assignés
            if not hasattr(self, 'achievements_system_rouge') or not self.achievements_system_rouge:
                self.achievements_system_rouge = AchievementsSystemRouge(self)
                self.achievements_system_vert = AchievementsSystemVert(self)
            
            # Sélectionner le bon système de succès selon l'équipe du joueur pour l'affichage
            if self.hud.player_team == 'red':
                self.achievements_system = self.achievements_system_rouge
            else:
                self.achievements_system = self.achievements_system_vert
            
            # Réinitialiser les statistiques de jeu pour les succès des deux équipes
            if self.achievements_system_rouge:
                self.achievements_system_rouge.reset_game_stats()
            
            if self.achievements_system_vert:
                self.achievements_system_vert.reset_game_stats()

        while running and self.game_running:
            dt = clock.tick(FPS) / TIME_STEP

            # Gestion des événements si pas en pause
            if self.mode == "tuto":
                running = self.event_handler.handle_events_tuto()
                self.event_handler.handle_continuous_input_tuto()
                
            else:
                running = self.event_handler.handle_events()
                self.event_handler.handle_continuous_input()

            # Mise à jour des systèmes de jeu
            self.updater.update_systems(dt, self)

            # Gestion achievements et notifications
            if self.mode != "tuto" and self.achievements_system:
                # Mettre à jour le temps de jeu pour les succès des deux équipes
                if hasattr(self, 'achievements_system_rouge') and self.achievements_system_rouge:
                    self.achievements_system_rouge.update_playtime(dt / 1000)  # Convertir en secondes
                if hasattr(self, 'achievements_system_vert') and self.achievements_system_vert:
                    self.achievements_system_vert.update_playtime(dt / 1000)  # Convertir en secondes
                    
                # Vérifier s'il y a de nouvelles notifications de succès pour les DEUX équipes
                if self.achievements_system_rouge:
                    new_notifications = self.achievements_system_rouge.get_pending_notifications()
                    for notification in new_notifications:
                        self.notification_manager.add_notification(notification['achievement'])
                
                if self.achievements_system_vert:
                    new_notifications = self.achievements_system_vert.get_pending_notifications()
                    for notification in new_notifications:
                        self.notification_manager.add_notification(notification['achievement'])
                
                # Mettre à jour le gestionnaire de notifications
                self.notification_manager.update(dt)

            # Rendu
            self.renderer.render()

            # Tutoriel
            if self.mode == "tuto":
                self.tutorial.update()
                self.tutorial.draw()

            # Écran de victoire
            if self.game_won:
                self.draw_victory_screen()

            pygame.display.flip()

        # Quitter ou retourner au menu
        if not self.game_running:
            return
        pygame.quit()
