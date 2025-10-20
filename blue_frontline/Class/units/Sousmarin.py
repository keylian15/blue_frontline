import time
import math
import pygame
import threading
from Class.units.Unit import Unit
from Class.Combat import CombatSystem, Mine
from math import * 
from Global import UNIT_CONFIGS
from Utils import point_in_many_polygons

class SousMarin(Unit):

    """Classe unifiée pour les unités Sous-marin (Rouge et Vert)."""
    
    def __init__(self, game, team: str):
        """Initialise une instance de SousMarin.

        Args:
            game: Instance du jeu.
            team (str): Équipe de l'unité.
        """
        # Récupérer la configuration depuis Global.py
        config = UNIT_CONFIGS["sousmarin"]
        
        # Initialiser avec l'image appropriée et le type d'unité
        super().__init__(game, team=team, unit_type="sousmarin")
        
        # === Spécifications du Sous-marin depuis Global.py ===
        self.cost = config["cost"]
        
        self.max_speed = config["max_speed"]
        self.reducte_speed = self.max_speed // 2
        self.speed = self.max_speed # Par défaut speed = speed max
        self.max_health = config["max_health"]
        self.current_health = self.max_health
        self.range = 0  # Les sous-marins ne tirent pas
        self.damage = 0
        self.fire_rate = 0
        
        # Type d'unité et capacité spéciale
        self.unit_type = config["unit_type"]
        self.unit_name = f"Sous-marin {team.capitalize()}"
        self.special_ability = config.get("special_ability", None)
        
        # Couleur de portée selon l'équipe
        self.range_color = config["range_color"][team]
        
        # État de mouvement
        self.is_moving = False
        self.target_position = None

        # Variables opérationnelles (minage/manual control)
        # Pas d'IA automatique dans cette classe ; le minage peut être déclenché manuellement
        self.mines_placed = 0
        self.max_mines = None  # None = pas de limite par défaut
        
        # Variables pour la stratégie d'encerclement
        self.current_target_scout = None  # L'éclaireur actuellement ciblé
        self.mine_positions_around_target = []  # Positions où poser des mines autour de la cible
        self.current_mine_index = 0  # Index de la prochaine position de mine
        
        # Modes d'IA
        self.ia_mode = "patrol"  # Modes possibles: "patrol", "attack", "return_to_platform"
        self.previous_mode = "patrol"  # Pour suivre le mode précédent
        self.platform_position = None  # Position de la plateforme pétrolière de l'équipe
        
        # Variables pour A* pathfinding (spécifiques au sous-marin)
        self.current_path = []  # Chemin A* actuel
        self.path_index = 0  # Index dans le chemin actuel
        self.is_computing_path = False  # Flag indiquant qu'un calcul est en cours
        
            
    def update(self, dt: int = 0, combat_system: CombatSystem = None, screen: pygame.Surface = None, camera_offset: tuple[float, float] =(0, 0), all_units: list[Unit] = None):
        """Met à jour l'unité en fonction de son état actuel.

        Args:
            dt (int, optional): La différence de temps entre chaque frame. Defaults to 0.
            combat_system (CombatSystem, optional): Le systeme de combat. Defaults to None.
            screen (pygame.Surface, optional): L'écran sur lequel affiché. Defaults to None.
            camera_offset (tuple[float, float], optional): La position de la caméra. Defaults to (0, 0).
            all_units (list[Unit], optional): Liste des unités. Defaults to None.
        """

        # Appeler l'IA de déplacement automatique
        if all_units:
            self.ia_mouvement(all_units)
        
        # Appeler la mise à jour de la classe parent
        super().update(dt, combat_system, screen, camera_offset, all_units)

        # Dessiner la portée en permanence
        if screen:
            self.draw_range(screen, camera_offset)


    def can_place_mine(self):
        """Vérifie si le sous-marin peut poser une mine (cooldown respecté, mais fire_rate ignoré)."""
        current_time = time.time()
        time_since_last_shot = current_time - self.last_shot_time
        multiplica = self.game.hud.timer.get_speed_multiplier() if hasattr(self.game, 'hud') and hasattr(self.game.hud, 'timer') else 1
        # Cooldown d'une seconde par défaut
        return time_since_last_shot >= (1.0 / multiplica)
    
    def place_mine(self, x: int, y: int):
        """Place une mine à la position spécifiée (capacité spéciale du sous-marin).

        Args:
            x (int): La position x de la mine.
            y (int): La position y de la mine.

        Returns:
            bool : True si la mine a été placée, False sinon.
        """
        if self.special_ability == "mines":
            # Créer la mine à la position exacte du sous-marin
            mine = Mine(x, y, self.team, damage=18)
            if hasattr(self.game, 'combat_system') and self.game.combat_system:
                self.game.combat_system.add_mine(mine)
                self.last_shot_time = time.time()
                self.mines_placed += 1
                print(f"✓ Mine #{self.mines_placed} posée par {self.team} sous-marin à ({x}, {y})")
            # -- AUDIO : drop mine --
            try:
                if hasattr(self.game, "sound") and self.game.sound:
                    self.game.sound.on_mine_dropped((x, y))
            except Exception:
                # ne jamais crasher pour du son
                pass
            return True
        else:
            print(f"⚠ Sous-marin {self.team} n'a pas la capacité 'mines' (actual: {self.special_ability})")
        return False
    
    
    
    def is_position_valid(self, x, y):
        """Vérifie si une position est valide (pas dans un obstacle)."""
        world_pos = (x, y)
        
        # Vérifier si la position est dans les limites de la carte avec une marge
        margin = 50  # Marge de sécurité pour éviter les bords
        if x < margin or y < margin or x >= (self.game.map_width - margin) or y >= (self.game.map_height - margin):
            return False
        
        # Vérifier si la position est dans un obstacle (île) avec une zone de sécurité
        if hasattr(self.game, 'obstacles') and self.game.obstacles:
            if point_in_many_polygons(self.game.obstacles, world_pos):
                return False
                
        # Vérifier les zones quantiques cachées (obstacles pour le sous-marin)
        if hasattr(self.game, 'quantique_area_hidden') and self.game.quantique_area_hidden:
            if point_in_many_polygons(self.game.quantique_area_hidden, world_pos):
                return False
        
        # Vérifier s'il y a une autre unité mobile à cette position (ignorer les plateformes)
        unit_at_pos = self.game.find_unit_at_position(x, y, self)
        if unit_at_pos:
            # Ignorer les plateformes pétrolières (is_platform) et les bases
            if not hasattr(unit_at_pos, 'is_platform') or not unit_at_pos.is_platform:
                return False
            
        return True
    
    def is_path_clear(self, target_x, target_y, num_checks=10):
        """Vérifie si le chemin vers la position cible est dégagé (pas d'obstacles sur la trajectoire).
        
        Args:
            target_x (float): Position x de la cible
            target_y (float): Position y de la cible
            num_checks (int): Nombre de points à vérifier le long du trajet
            
        Returns:
            bool: True si le chemin est dégagé, False sinon
        """
        # Vérifier plusieurs points le long de la trajectoire
        for i in range(1, num_checks + 1):
            # Interpolation linéaire entre la position actuelle et la cible
            ratio = i / num_checks
            check_x = self.position[0] + (target_x - self.position[0]) * ratio
            check_y = self.position[1] + (target_y - self.position[1]) * ratio
            
            # Si un point du trajet n'est pas valide, le chemin est bloqué
            if not self.is_position_valid(check_x, check_y):
                return False
        
        return True
    
    def find_nearby_scouts(self, all_units, detection_range=320):
        """Trouve les éclaireurs ennemis à proximité.
        
        Args:
            all_units (list[Unit]): Liste de toutes les unités du jeu
            detection_range (int): Rayon de détection en pixels (10 cases * 32 pixels = 320)
            
        Returns:
            list[Unit]: Liste des éclaireurs ennemis détectés
        """
        nearby_scouts = []
        
        for unit in all_units:
            # Vérifier si c'est un ennemi vivant
            if not unit.is_alive or unit.team == self.team:
                continue
            
            # Vérifier si c'est un éclaireur
            if hasattr(unit, 'unit_type') and unit.unit_type == "eclaireur":
                # Calculer la distance
                dx = unit.position[0] - self.position[0]
                dy = unit.position[1] - self.position[1]
                distance = math.sqrt(dx**2 + dy**2)
                
                # Si dans le rayon de détection
                if distance <= detection_range:
                    nearby_scouts.append(unit)
        
        return nearby_scouts
    
    def find_nearby_paquebots(self, all_units, detection_range=600):
        """Trouve les paquebots ennemis à proximité.
        
        Args:
            all_units (list[Unit]): Liste de toutes les unités du jeu
            detection_range (int): Rayon de détection en pixels (par défaut 600px)
            
        Returns:
            list[Unit]: Liste des paquebots ennemis détectés
        """
        nearby_paquebots = []
        
        for unit in all_units:
            # Vérifier si c'est un ennemi vivant
            if not unit.is_alive or unit.team == self.team:
                continue
            
            # Vérifier si c'est un paquebot
            if hasattr(unit, 'unit_type') and unit.unit_type == "paquebot":
                # Calculer la distance
                dx = unit.position[0] - self.position[0]
                dy = unit.position[1] - self.position[1]
                distance = math.sqrt(dx**2 + dy**2)
                
                # Si dans le rayon de détection
                if distance <= detection_range:
                    nearby_paquebots.append(unit)
        
        return nearby_paquebots
    
    def find_nearby_chaloupes(self, all_units, detection_range=500):
        """Trouve les chaloupes ennemies à proximité.
        
        Args:
            all_units (list[Unit]): Liste de toutes les unités du jeu
            detection_range (int): Rayon de détection en pixels (par défaut 500px)
            
        Returns:
            list[Unit]: Liste des chaloupes ennemies détectées
        """
        nearby_chaloupes = []
        
        for unit in all_units:
            # Vérifier si c'est un ennemi vivant
            if not unit.is_alive or unit.team == self.team:
                continue
            
            # Vérifier si c'est une chaloupe
            if hasattr(unit, 'unit_type') and unit.unit_type == "chaloupe":
                # Calculer la distance
                dx = unit.position[0] - self.position[0]
                dy = unit.position[1] - self.position[1]
                distance = math.sqrt(dx**2 + dy**2)
                
                # Si dans le rayon de détection
                if distance <= detection_range:
                    nearby_chaloupes.append(unit)
        
        return nearby_chaloupes
    
    def get_closest_scout(self, scouts):
        """Trouve l'éclaireur le plus proche parmi une liste.
        
        Args:
            scouts (list[Unit]): Liste des éclaireurs
            
        Returns:
            Unit: L'éclaireur le plus proche, ou None si la liste est vide
        """
        if not scouts:
            return None
        
        closest_scout = None
        min_distance = float('inf')
        
        for scout in scouts:
            dx = scout.position[0] - self.position[0]
            dy = scout.position[1] - self.position[1]
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < min_distance:
                min_distance = distance
                closest_scout = scout
        
        return closest_scout

    def a_star_search(self, start, goal):
        """Implémentation A* sur grille 32x32 pixels.

        Args:
            start (tuple): (x, y) position départ
            goal (tuple): (x, y) position but

        Returns:
            list de (x,y): chemin en pixels (centre des tuiles) ou None
        """
        def pos_to_grid(pos):
            return (int(pos[0] // 32), int(pos[1] // 32))

        def grid_to_pos(grid):
            return (grid[0] * 32 + 16, grid[1] * 32 + 16)

        start_grid = pos_to_grid(start)
        goal_grid = pos_to_grid(goal)

        # Construire l'ensemble des obstacles sur la grille
        obstacles = set()
        if hasattr(self.game, 'obstacles') and self.game.obstacles:
            for poly in self.game.obstacles:
                min_x = min(p[0] for p in poly) // 32
                max_x = max(p[0] for p in poly) // 32
                min_y = min(p[1] for p in poly) // 32
                max_y = max(p[1] for p in poly) // 32
                for x in range(int(min_x), int(max_x)+1):
                    for y in range(int(min_y), int(max_y)+1):
                        obstacles.add((x, y))
        
        # Ajouter les zones quantiques cachées comme obstacles
        if hasattr(self.game, 'quantique_area_hidden') and self.game.quantique_area_hidden:
            for poly in self.game.quantique_area_hidden:
                min_x = min(p[0] for p in poly) // 32
                max_x = max(p[0] for p in poly) // 32
                min_y = min(p[1] for p in poly) // 32
                max_y = max(p[1] for p in poly) // 32
                for x in range(int(min_x), int(max_x)+1):
                    for y in range(int(min_y), int(max_y)+1):
                        obstacles.add((x, y))

        # Directions de déplacement (4 directions: haut, bas, gauche, droite)
        neighbors = [(0, 1), (1, 0), (0, -1), (-1, 0)]

        # Ensembles pour A*
        open_set = set([start_grid])
        came_from = {}

        g_score = {start_grid: 0}
        f_score = {start_grid: self.heuristic(start_grid, goal_grid)}

        while open_set:
            # Trouver le nœud avec le plus petit f_score
            current = min(open_set, key=lambda x: f_score.get(x, float('inf')))
            
            # Si on a atteint le but
            if current == goal_grid:
                path = []
                while current in came_from:
                    path.append(grid_to_pos(current))
                    current = came_from[current]
                path.append(grid_to_pos(start_grid))
                path.reverse()
                return path

            open_set.remove(current)

            # Explorer les voisins
            for dx, dy in neighbors:
                neighbor = (current[0] + dx, current[1] + dy)
                
                # Ignorer les obstacles
                if neighbor in obstacles:
                    continue
                
                # Vérifier les limites de la carte
                if neighbor[0] < 0 or neighbor[1] < 0:
                    continue
                if neighbor[0] >= (self.game.map_width // 32) or neighbor[1] >= (self.game.map_height // 32):
                    continue
                
                tentative_g_score = g_score[current] + 1
                
                if tentative_g_score < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal_grid)
                    open_set.add(neighbor)

        # Aucun chemin trouvé
        return None

    def heuristic(self, a, b):
        """Distance de Manhattan."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def recalculate_path(self):
        """Signale qu'il faut recalculer le chemin.
        """
        if not self.need_recalculate_path:
            self.need_recalculate_path = True
            self.current_path = []
            self.path_index = 0
    
    def compute_path(self):
        """Calcule le chemin A* vers la plateforme en arrière-plan (appelé dans un thread)."""
        start = self.position
        goal = self.platform_position
        
        if not start or not goal:
            self.is_computing_path = False
            return

        # Calculer le chemin avec A*
        path = self.a_star_search(start, goal)
        
        if path:
            self.new_path = path
            self.path_found = True
            print(f"🧵 {self.team} sous-marin: Chemin calculé en thread ({len(path)} points)")
        else:
            self.new_path = None
            self.path_found = False
            print(f"⚠️ {self.team} sous-marin: Aucun chemin trouvé en thread")
        
        self.is_computing_path = False
    
    def update_path_from_thread(self):
        """Met à jour le chemin depuis le résultat du thread."""
        if self.path_found and self.new_path:
            self.current_path = self.new_path
            self.path_index = 0
            self.need_recalculate_path = False
            self.path_found = False
            self.new_path = None
            print(f"✅ {self.team} sous-marin: Chemin mis à jour depuis le thread")
            return True
        return False

    def follow_path(self):
        """Suit le chemin A* calculé."""
        if not self.current_path or self.path_index >= len(self.current_path):
            return False
        
        # Obtenir la prochaine position dans le chemin
        next_pos = self.current_path[self.path_index]
        
        # Calculer la distance à la prochaine position
        dx = next_pos[0] - self.position[0]
        dy = next_pos[1] - self.position[1]
        distance = math.sqrt(dx**2 + dy**2)
        
        # Si on est proche de la prochaine position (moins de 20 pixels), passer à la suivante
        if distance < 20:
            self.path_index += 1
            if self.path_index >= len(self.current_path):
                # Fin du chemin
                return False
            next_pos = self.current_path[self.path_index]
        
        # Se déplacer vers la prochaine position
        if not self.is_moving or self.target_position != next_pos:
            # Calculer l'angle vers la prochaine position
            angle_to_next = math.degrees(math.atan2(-dy, dx)) - 90
            self.angle = angle_to_next % 360
            self.image = pygame.transform.rotate(self.image_original, self.angle)
            self.rect = self.image.get_rect(center=self.rect.center)
            
            # Se déplacer vers la prochaine position
            self.move_to_position(next_pos)
        
        return True

    def find_base_position(self, all_units):
        """Trouve la position d'une plateforme pétrolière de l'équipe.
        
        Args:
            all_units (list[Unit]): Liste de toutes les unités du jeu
            
        Returns:
            tuple: Position (x, y) de la plateforme ou None si non trouvée
        """
        print(f"🔍 {self.team} sous-marin: Recherche d'une plateforme pétrolière...")
        
        for unit in all_units:
            # Vérifier si c'est une plateforme de la même équipe
            if hasattr(unit, 'team') and unit.team == self.team:
                # Vérifier plusieurs possibilités pour identifier une plateforme pétrolière
                is_platform = False
                
                if hasattr(unit, 'is_platform') and unit.is_platform:
                    is_platform = True
                    print(f"✅ {self.team} sous-marin: Plateforme trouvée via is_platform flag")
                
                if hasattr(unit, 'unit_type'):
                    # Vérifier si c'est une plateforme par le type
                    if unit.unit_type in ["plateforme", "platform", "plateforme_petroliere", "PlateformePetroliere"]:
                        is_platform = True
                        print(f"✅ {self.team} sous-marin: Plateforme trouvée via unit_type: {unit.unit_type}")
                
                # Vérifier par le nom de classe
                class_name = unit.__class__.__name__.lower()
                if 'plateforme' in class_name or 'platform' in class_name:
                    is_platform = True
                    print(f"✅ {self.team} sous-marin: Plateforme trouvée via class name: {unit.__class__.__name__}")
                
                if is_platform:
                    print(f"🛢️ {self.team} sous-marin: Plateforme pétrolière trouvée à position {unit.position}")
                    return unit.position
        
        print(f"❌ {self.team} sous-marin: Aucune plateforme pétrolière trouvée!")
        return None

    def handle_platform_collision(self, all_units):
        """Détecte si le sous-marin est en collision avec sa plateforme et force
        un retournement de 180° dans tous les cas.

        Ce handler est appelé à chaque tick IA pour garantir que le sous-marin
        tourne systématiquement s'il entre en contact physique avec la
        plateforme (indépendamment du mode IA courant).
        """
        # Chercher la plateforme la plus proche de la même équipe
        platform_unit = None
        for unit in all_units:
            if not hasattr(unit, 'team') or unit.team != self.team:
                continue
            # Reconnaître une plateforme via plusieurs marqueurs possibles
            is_platform = False
            if hasattr(unit, 'is_platform') and unit.is_platform:
                is_platform = True
            if hasattr(unit, 'unit_type') and unit.unit_type in ["plateforme", "platform", "plateforme_petroliere", "PlateformePetroliere"]:
                is_platform = True
            class_name = unit.__class__.__name__.lower()
            if 'plateforme' in class_name or 'platform' in class_name:
                is_platform = True

            if is_platform:
                platform_unit = unit
                break

        if not platform_unit:
            return

        # Collision physique simple: utiliser la distance centre-à-centre
        # ou si la plateforme expose un rect, faire une intersection cercle/rect.
        sub_x, sub_y = self.position
        # Rayon approximatif du sous-marin
        sub_radius = 25

        plat_rect = getattr(platform_unit, 'rect', None)
        if plat_rect:
            # Trouver le point le plus proche sur le rect
            closest_x = max(plat_rect.left, min(sub_x, plat_rect.right))
            closest_y = max(plat_rect.top, min(sub_y, plat_rect.bottom))
            dx = closest_x - sub_x
            dy = closest_y - sub_y
            dist_sq = dx*dx + dy*dy
            if dist_sq <= (sub_radius * sub_radius):
                # Collision détectée
                self.stop()
                self.is_moving = False
                self.target_position = None
                self.current_path = []
                self.path_index = 0
                # Tourner de 180°
                self.angle = (self.angle + 180) % 360
                self.image = pygame.transform.rotate(self.image_original, self.angle)
                self.rect = self.image.get_rect(center=self.rect.center)
                # Forcer repasse en patrol
                self.ia_mode = "patrol"
                self.platform_position = None
                print(f"🔁 {self.team} sous-marin: Collision plateforme détectée → rotation 180° (angle={int(self.angle)})")
                return
        else:
            # Pas de rect disponible: fallback distance simple vers la position déclarée
            if hasattr(platform_unit, 'position') and platform_unit.position:
                dx = platform_unit.position[0] - sub_x
                dy = platform_unit.position[1] - sub_y
                distance = math.sqrt(dx*dx + dy*dy)
                # Seuil conservateur (approx. taille plateforme + sous-marin)
                if distance <= 50:
                    self.stop()
                    self.is_moving = False
                    self.target_position = None
                    self.current_path = []
                    self.path_index = 0
                    self.angle = (self.angle + 180) % 360
                    self.image = pygame.transform.rotate(self.image_original, self.angle)
                    self.rect = self.image.get_rect(center=self.rect.center)
                    self.ia_mode = "patrol"
                    self.platform_position = None
                    print(f"🔁 {self.team} sous-marin: Collision plateforme (distance) → rotation 180° (angle={int(self.angle)})")
                    return
    
    def return_to_base(self, all_units):
        """Fait retourner le sous-marin à une plateforme pétrolière de son équipe en utilisant A*.
        
        Args:
            all_units (list[Unit]): Liste de toutes les unités du jeu
        """
        # Trouver la plateforme si on ne l'a pas encore
        if self.platform_position is None:
            self.platform_position = self.find_base_position(all_units)
            self.need_recalculate_path = True  # Forcer le recalcul du chemin
        
        if self.platform_position:
            # Calculer la distance à la plateforme
            dx = self.platform_position[0] - self.position[0]
            dy = self.platform_position[1] - self.position[1]
            distance_to_platform = math.sqrt(dx**2 + dy**2)
            
            # Si on est proche de la plateforme (moins de 50 pixels), on arrête et on tourne le bateau
            if distance_to_platform < 50:
                print(f"🛢️ {self.team} sous-marin: Arrivé à la plateforme pétrolière!")
                self.stop()
                self.is_moving = False
                self.target_position = None
                self.current_path = []
                self.path_index = 0
                
                # Faire tourner le bateau de 180 degrés pour repartir dans l'autre direction
                self.angle = (self.angle + 180) % 360
                self.image = pygame.transform.rotate(self.image_original, self.angle)
                self.rect = self.image.get_rect(center=self.rect.center)
                print(f"🔄 {self.team} sous-marin: Bateau tourné de 180° (nouvel angle: {int(self.angle)}°)")
                
                # Passer en mode patrol
                self.ia_mode = "patrol"
                self.platform_position = None  # Réinitialiser pour chercher une nouvelle plateforme la prochaine fois
                print(f"✅ {self.team} sous-marin: Retour en mode PATROL!")
                return
            
            # Calculer ou suivre le chemin A* en utilisant le thread centralisé
            # 1) Si un chemin a été trouvé par le thread, l'appliquer
            if self.update_path_from_thread():
                # Le chemin a été mis à jour, on peut continuer pour le suivre
                pass
            # 2) Si on doit recalculer ou s'il n'y a pas de chemin, démarrer/attendre le thread
            elif self.need_recalculate_path or not self.current_path:
                # Si aucun thread n'est en cours, en lancer un
                if not getattr(self, 'path_thread', None) or not self.path_thread.is_alive():
                    print(f"🧵 {self.team} sous-marin: Lancement du calcul A* en thread...")
                    # Démarrer la computation en arrière-plan via l'utilitaire Unit
                    # (start_pathfinding_thread stocke le Thread dans self.path_thread)
                    try:
                        # Utiliser la méthode fournie par Unit
                        self.start_pathfinding_thread(self.compute_path)
                    except Exception:
                        # En cas de problème avec le threading, retomber sur le calcul synchrone
                        print(f"⚠️ {self.team} sous-marin: Échec du lancement du thread, calcul synchrone A*...")
                        path = self.a_star_search(self.position, self.platform_position)
                        if path:
                            self.current_path = path
                            self.path_index = 0
                            self.need_recalculate_path = False
                            print(f"✅ {self.team} sous-marin: Chemin A* trouvé ({len(path)} points)")
                        else:
                            print(f"⚠️ {self.team} sous-marin: A* a échoué, utilisation du chemin direct")
                            if self.is_path_clear(self.platform_position[0], self.platform_position[1]):
                                self.move_to_position(self.platform_position)
                            else:
                                self.find_alternative_path_to_target(self.platform_position[0], self.platform_position[1])
                        return

                # Si le thread est terminé mais n'a pas trouvé de chemin, retomber sur la méthode directe
                if getattr(self, 'path_thread', None) and not self.path_thread.is_alive() and not self.path_found and not self.current_path:
                    print(f"⚠️ {self.team} sous-marin: A* a échoué en thread, utilisation du chemin direct")
                    if self.is_path_clear(self.platform_position[0], self.platform_position[1]):
                        self.move_to_position(self.platform_position)
                    else:
                        self.find_alternative_path_to_target(self.platform_position[0], self.platform_position[1])
                    # Réinitialiser la demande de recalcul
                    self.need_recalculate_path = False
                    return

            # Suivre le chemin A*
            if not self.follow_path():
                # Le chemin est terminé mais on n'est pas encore arrivé, recalculer
                self.need_recalculate_path = True
        else:
            # Si on ne trouve pas de plateforme, retour en mode patrol
            print(f"⚠️ {self.team} sous-marin: Plateforme non trouvée, retour en mode PATROL")
            self.ia_mode = "patrol"
            self.current_path = []
            self.path_index = 0
            self.patrol_movement()
    
    def set_ia_mode(self, mode: str):
        """Change le mode d'IA du sous-marin.
        
        Args:
            mode (str): Le mode à activer ("fuite", "defense_base", "attaque", "normal")
        """
        if mode in ["fuite", "defense_base", "attaque", "normal"]:
            self.previous_mode = self.ia_mode  # Sauvegarder le mode précédent
            self.ia_mode = mode
            print(f"🎯 {self.team} sous-marin: Mode IA changé de '{self.previous_mode}' en '{mode}'")
        else:
            print(f"⚠ Mode IA invalide: {mode}. Modes possibles: fuite, defense_base, attaque, normal")
    

        """Mode défense base: Le sous-marin patrouille autour de sa base et la protège.
        
        Args:
            all_units (list[Unit]): Liste de toutes les unités du jeu
        """
        # TODO: Implémenter la logique de défense de base
        pass
    
    def ia_mode_attaque(self, all_units):
        """Mode attaque: Le sous-marin poursuit activement les ennemis (éclaireurs).
        
        Activé automatiquement quand un éclaireur est à proximité.
        Dans ce mode, le sous-marin s'approche jusqu'à collision et pose une mine.
        
        Args:
            all_units (list[Unit]): Liste de toutes les unités du jeu
        """
        # Chercher l'éclaireur le plus proche
        nearby_scouts = self.find_nearby_scouts(all_units, detection_range=60)
        
        if nearby_scouts:
            target_scout = self.get_closest_scout(nearby_scouts)
            
            if target_scout:
                # Calculer la distance avec l'éclaireur
                dx = target_scout.position[0] - self.position[0]
                dy = target_scout.position[1] - self.position[1]
                distance_to_scout = math.sqrt(dx**2 + dy**2)
                # Distance de collision très proche (environ la taille d'une unité, ~25 pixels)
                collision_distance = 25
                
                # Si on est en collision ou très très proche, arrêter et poser une mine
                if distance_to_scout <= collision_distance:
                    # Arrêter le mouvement en cours
                    self.stop()
                    self.is_moving = False
                    self.target_position = None
                    
                    # Poser une mine si le cooldown est passé
                    if self.can_place_mine():
                        mine_placed = self.place_mine(int(self.position[0]), int(self.position[1]))
                        if mine_placed:
                            print(f"💣 [MODE ATTAQUE] {self.team} sous-marin a posé une mine à ({int(self.position[0])}, {int(self.position[1])}) - COLLISION avec éclaireur: {int(distance_to_scout)}px")
                else:
                    # Continuer à poursuivre l'éclaireur
                    if not self.is_moving:
                        # Calculer l'angle vers l'éclaireur
                        angle_to_scout = math.degrees(math.atan2(-dy, dx)) - 90
                        self.angle = angle_to_scout % 360
                        self.image = pygame.transform.rotate(self.image_original, self.angle)
                        self.rect = self.image.get_rect(center=self.rect.center)
                        
                        # Se déplacer vers l'éclaireur si le chemin est dégagé
                        if self.is_path_clear(target_scout.position[0], target_scout.position[1]):
                            self.move_to_position(target_scout.position)
                        else:
                            # Si le chemin direct est bloqué, chercher une route alternative
                            self.find_alternative_path_to_target(target_scout.position[0], target_scout.position[1])
        else:
            # Plus d'éclaireur à proximité, reprendre la patrouille
            self.patrol_movement()
    
    def ia_mouvement(self, all_units):
        """IA du sous-marin avec trois modes distincts : patrol, attack, return_to_platform.
        
        Flux:
        1. PATROL → Patrouille normale jusqu'à détecter un éclaireur
        2. ATTACK → Poursuite et pose de mine
        3. RETURN_TO_PLATFORM → Retour à la plateforme pétrolière
        4. Retour en PATROL
        """
        
        # Avant tout: gérer la collision avec la plateforme (toujours faire 180° si on se cogne)
        self.handle_platform_collision(all_units)

        # MODE 1: PATROL - Patrouille normale
        if self.ia_mode == "patrol":
            self.behavior_patrol(all_units)
        
        # MODE 2: ATTACK - Attaque d'un éclaireur
        elif self.ia_mode == "attack":
            self.behavior_attack(all_units)
        
        # MODE 3: RETURN_TO_PLATFORM - Retour à la plateforme
        elif self.ia_mode == "return_to_platform":
            self.behavior_return_to_platform(all_units)
    
    def behavior_patrol(self, all_units):
        """Comportement de patrouille normale.
        
        Cherche des chaloupes ennemies à 500px ou moins → passe en mode return_to_platform.
        Cherche des paquebots ennemis à 300px ou moins → passe en mode return_to_platform.
        Cherche des éclaireurs ennemis à 320px → passe en mode attack.
        Sinon, patrouille en ligne droite.
        """
        # PRIORITÉ 1: Chercher des chaloupes ennemies à proximité (500 pixels)
        nearby_chaloupes = self.find_nearby_chaloupes(all_units, detection_range=500)
        
        if nearby_chaloupes:
            # Chaloupe détectée → retourner à la plateforme immédiatement
            print(f"⛵ {self.team} sous-marin: CHALOUPE DÉTECTÉE à 500px ou moins → Passage en mode RETURN_TO_PLATFORM")
            self.ia_mode = "return_to_platform"
            return
        
        # PRIORITÉ 2: Chercher des paquebots ennemis à proximité (300 pixels)
        nearby_paquebots = self.find_nearby_paquebots(all_units, detection_range=300)
        
        if nearby_paquebots:
            # Paquebot détecté → retourner à la plateforme immédiatement
            print(f"🚢 {self.team} sous-marin: PAQUEBOT DÉTECTÉ à 300px ou moins → Passage en mode RETURN_TO_PLATFORM")
            self.ia_mode = "return_to_platform"
            return
        
        # PRIORITÉ 3: Chercher des éclaireurs ennemis à proximité (10 cases = 320 pixels)
        nearby_scouts = self.find_nearby_scouts(all_units, detection_range=320)
        
        if nearby_scouts:
            # Éclaireur détecté → passer en mode attaque
            print(f"⚔️ {self.team} sous-marin: ÉCLAIREUR DÉTECTÉ → Passage en mode ATTACK")
            self.ia_mode = "attack"
            return
        
        # Pas de menace → patrouille normale
        self.patrol_movement()
    
    def behavior_attack(self, all_units):
        """Comportement d'attaque d'un éclaireur.
        
        PRIORITÉ: Si chaloupe détectée à 500px → passe en mode return_to_platform.
        PRIORITÉ: Si paquebot détecté à 300px → passe en mode return_to_platform.
        Poursuit l'éclaireur et pose une mine à proximité.
        Si plus d'éclaireur → passe en mode return_to_platform.
        """
        # PRIORITÉ 1: Vérifier la présence de chaloupes à proximité (500 pixels)
        nearby_chaloupes = self.find_nearby_chaloupes(all_units, detection_range=500)
        
        if nearby_chaloupes:
            # Chaloupe détectée → annuler l'attaque et retourner à la plateforme
            print(f"⛵ {self.team} sous-marin: CHALOUPE DÉTECTÉE pendant l'attaque → Annulation, passage en mode RETURN_TO_PLATFORM")
            self.ia_mode = "return_to_platform"
            return
        
        # PRIORITÉ 2: Vérifier la présence de paquebots à proximité (300 pixels)
        nearby_paquebots = self.find_nearby_paquebots(all_units, detection_range=300)
        
        if nearby_paquebots:
            # Paquebot détecté → annuler l'attaque et retourner à la plateforme
            print(f"🚢 {self.team} sous-marin: PAQUEBOT DÉTECTÉ pendant l'attaque → Annulation, passage en mode RETURN_TO_PLATFORM")
            self.ia_mode = "return_to_platform"
            return
        
        # PRIORITÉ 3: Chercher des éclaireurs ennemis à proximité
        nearby_scouts = self.find_nearby_scouts(all_units, detection_range=320)
        
        if not nearby_scouts:
            # Plus d'éclaireur → passer en mode retour à la plateforme
            print(f"🛢️ {self.team} sous-marin: PLUS D'ÉCLAIREUR → Passage en mode RETURN_TO_PLATFORM")
            self.ia_mode = "return_to_platform"
            return
        
        # Éclaireur détecté, le poursuivre
        target_scout = self.get_closest_scout(nearby_scouts)
        
        if target_scout:
            # Calculer la distance avec l'éclaireur
            dx = target_scout.position[0] - self.position[0]
            dy = target_scout.position[1] - self.position[1]
            distance_to_scout = math.sqrt(dx**2 + dy**2)
            
            # Distance de collision
            collision_distance = 30
            
            print(f"🔍 {self.team} sous-marin: Éclaireur à {int(distance_to_scout)}px (seuil: {collision_distance}px)")
            
            # Si on est en collision ou très proche, poser une mine
            if distance_to_scout <= collision_distance:
                print(f"⚠️ {self.team} sous-marin: COLLISION! Distance: {int(distance_to_scout)}px")
                
                # Arrêter le mouvement
                self.stop()
                self.is_moving = False
                self.target_position = None
                
                # Poser une mine si le cooldown est passé
                if self.can_place_mine():
                    print(f"✅ {self.team} sous-marin: Cooldown OK, pose de mine...")
                    mine_placed = self.place_mine(int(self.position[0]), int(self.position[1]))
                    if mine_placed:
                        print(f"💣 {self.team} sous-marin a posé une mine - Distance éclaireur: {int(distance_to_scout)}px")
                else:
                    print(f"⏳ {self.team} sous-marin: Cooldown en cours...")
                return
            
            # Si l'éclaireur est plus loin, ajuster la trajectoire si nécessaire
            if self.is_moving and self.target_position:
                # Vérifier si on se dirige déjà vers l'éclaireur (tolérance de 30 degrés)
                current_target_dx = self.target_position[0] - self.position[0]
                current_target_dy = self.target_position[1] - self.position[1]
                current_angle = math.degrees(math.atan2(-current_target_dy, current_target_dx)) - 90
                scout_angle = math.degrees(math.atan2(-dy, dx)) - 90
                angle_diff = abs((scout_angle - current_angle + 180) % 360 - 180)
                
                # Si on ne se dirige pas vers l'éclaireur, changer de direction
                if angle_diff > 30:
                    self.stop()
                    self.is_moving = False
                    self.target_position = None
            
            # Se déplacer vers l'éclaireur
            if not self.is_moving:
                print(f"🎯 {self.team} sous-marin: Poursuite de l'éclaireur...")
                # Calculer l'angle vers l'éclaireur
                angle_to_scout = math.degrees(math.atan2(-dy, dx)) - 90
                self.angle = angle_to_scout % 360
                self.image = pygame.transform.rotate(self.image_original, self.angle)
                self.rect = self.image.get_rect(center=self.rect.center)
                
                # Se déplacer vers l'éclaireur si le chemin est dégagé
                if self.is_path_clear(target_scout.position[0], target_scout.position[1]):
                    self.move_to_position(target_scout.position)
                else:
                    # Si le chemin direct est bloqué, chercher une route alternative
                    self.find_alternative_path_to_target(target_scout.position[0], target_scout.position[1])
    
    def behavior_return_to_platform(self, all_units):
        """Comportement de retour à la plateforme pétrolière.
        
        Retourne à une plateforme pétrolière alliée.
        Arrivé à destination → tourne de 180° et repasse en mode patrol.
        """
        # PRIORITÉ 1: Vérifier la présence de chaloupes et paquebots (ne pas interrompre le retour)
        nearby_chaloupes = self.find_nearby_chaloupes(all_units, detection_range=500)
        nearby_paquebots = self.find_nearby_paquebots(all_units, detection_range=300)
        
        if nearby_chaloupes or nearby_paquebots:
            # Une menace est toujours présente, continuer le retour
            menace_type = "Chaloupe" if nearby_chaloupes else "Paquebot"
            print(f"🚢 {self.team} sous-marin: {menace_type} toujours détecté(e), continuation du retour à la plateforme")
        
        # PRIORITÉ 2: Si un éclaireur est détecté ET qu'il n'y a ni chaloupe ni paquebot, annuler le retour
        if not nearby_chaloupes and not nearby_paquebots:
            nearby_scouts = self.find_nearby_scouts(all_units, detection_range=320)
            if nearby_scouts:
                print(f"⚔️ {self.team} sous-marin: ÉCLAIREUR DÉTECTÉ (pas de menace majeure) → Annulation du retour, passage en mode ATTACK")
                self.ia_mode = "attack"
                self.platform_position = None  # Réinitialiser la position de la plateforme
                return
        
        # Continuer le retour à la plateforme
        self.return_to_base(all_units)
    
    def patrol_movement(self):
        """Effectue un mouvement de patrouille (avancer tout droit)."""
        # Si le sous-marin est déjà en mouvement, ne rien faire
        if self.is_moving:
            return
        
        # Calculer la prochaine position en avançant tout droit
        # On utilise l'angle actuel du sous-marin pour déterminer la direction
        distance_check = 150  # Distance à vérifier devant le sous-marin
        
        # Convertir l'angle en radians et calculer la direction
        angle_rad = math.radians(self.angle + 90)  # +90 car l'angle 0 pointe vers le haut
        
        # Calculer la position cible en avançant tout droit
        target_x = self.position[0] + math.cos(angle_rad) * distance_check
        target_y = self.position[1] - math.sin(angle_rad) * distance_check
        
        # Vérifier si le chemin vers la position cible est dégagé (pas seulement le point final)
        if self.is_path_clear(target_x, target_y):
            # Si le chemin est dégagé, se déplacer vers cette position
            self.move_to_position((target_x, target_y))
        else:
            # Si le chemin n'est pas dégagé, chercher une direction alternative
            self.find_alternative_direction(distance_check)
    
    def find_alternative_direction(self, distance_check):
        """Cherche une direction alternative quand le chemin est bloqué.
        
        Args:
            distance_check (int): Distance à vérifier pour chaque direction
        """
        direction_found = False
        
        # Liste d'angles à tester (de plus en plus grand)
        angles_to_test = [20, -20, 40, -40, 60, -60, 80, -80, 100, -100, 120, -120, 140, -140, 160, -160, 180]
        
        # D'abord essayer avec la distance normale
        for angle_offset in angles_to_test:
            test_angle = math.radians(self.angle + 90 + angle_offset)
            test_x = self.position[0] + math.cos(test_angle) * distance_check
            test_y = self.position[1] - math.sin(test_angle) * distance_check
            
            # Vérifier tout le chemin, pas seulement la destination
            if self.is_path_clear(test_x, test_y):
                # Mettre à jour l'angle du sous-marin
                self.angle = (self.angle + angle_offset) % 360
                self.image = pygame.transform.rotate(self.image_original, self.angle)
                self.rect = self.image.get_rect(center=self.rect.center)
                # Se déplacer vers cette nouvelle position
                self.move_to_position((test_x, test_y))
                direction_found = True
                break
        
        # Si aucune direction n'a été trouvée, essayer avec une distance plus courte
        if not direction_found:
            shorter_distance = distance_check // 2  # 75 pixels
            for angle_offset in angles_to_test:
                test_angle = math.radians(self.angle + 90 + angle_offset)
                test_x = self.position[0] + math.cos(test_angle) * shorter_distance
                test_y = self.position[1] - math.sin(test_angle) * shorter_distance
                
                # Vérifier tout le chemin, pas seulement la destination
                if self.is_path_clear(test_x, test_y):
                    # Mettre à jour l'angle du sous-marin
                    self.angle = (self.angle + angle_offset) % 360
                    self.image = pygame.transform.rotate(self.image_original, self.angle)
                    self.rect = self.image.get_rect(center=self.rect.center)
                    # Se déplacer vers cette nouvelle position
                    self.move_to_position((test_x, test_y))
                    direction_found = True
                    break
    
    def find_alternative_path_to_target(self, target_x, target_y):
        """Cherche un chemin alternatif vers une cible spécifique.
        
        Args:
            target_x (float): Position x de la cible
            target_y (float): Position y de la cible
        """
        # Calculer l'angle vers la cible
        dx = target_x - self.position[0]
        dy = target_y - self.position[1]
        base_angle = math.degrees(math.atan2(-dy, dx)) - 90
        
        # Tester des angles autour de la direction de la cible
        angles_to_test = [0, 15, -15, 30, -30, 45, -45, 60, -60, 90, -90]
        distance_check = 100
        
        for angle_offset in angles_to_test:
            test_angle_deg = (base_angle + angle_offset) % 360
            test_angle_rad = math.radians(test_angle_deg + 90)
            
            test_x = self.position[0] + math.cos(test_angle_rad) * distance_check
            test_y = self.position[1] - math.sin(test_angle_rad) * distance_check
            
            if self.is_path_clear(test_x, test_y):
                self.angle = test_angle_deg
                self.image = pygame.transform.rotate(self.image_original, self.angle)
                self.rect = self.image.get_rect(center=self.rect.center)
                self.move_to_position((test_x, test_y))
                break
    



# Classes d'alias pour la compatibilité avec l'ancien code
class SousMarinRouge(SousMarin):
    def __init__(self, game):
        """Constructeur de SousMarinRouge.

        Args:
            game: L'instance de la classe Game.
        """
        super().__init__(game, team="red")

class SousMarinVert(SousMarin):
    def __init__(self, game):
        """Constructeur de SousMarinVert.

        Args:
            game: L'instance de la classe Game.
        """
        super().__init__(game, team="green")

