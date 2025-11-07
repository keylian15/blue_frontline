import pygame, math, time, threading
from Class.units.Unit import Unit
from Class.Combat import CombatSystem
from Global import UNIT_CONFIGS
from Utils import point_in_many_polygons

# Import de l'IA séparée
try:
    from Class.units.IA.ChaloupeAI import ChaloupeAI
    AI_AVAILABLE = True
except ImportError:
    print("IA ChaloupeAI non disponible, utilisation du comportement de base")
    AI_AVAILABLE = False

class Chaloupe(Unit):
    """Classe unifiée pour les unités Chaloupe (Rouge et Verte)."""
    
    def __init__(self, game: "Game", team: str, is_ia: bool = True):
        """Initialise une instance de Chaloupe.

        Args:
            game (Game): Instance du jeu.
            team (str): Équipe de l'unité.
            is_ia (bool): Active ou désactive l'IA pour cette chaloupe.
        """
        # Récupérer la configuration depuis Global.py
        config = UNIT_CONFIGS["chaloupe"]
        
        # Initialiser avec l'image appropriée et le type d'unité
        super().__init__(game, team=team, unit_type="chaloupe")
        
        # === Spécifications de la Chaloupe depuis Global.py ===
        self.cost = config["cost"]
        
        self.max_speed = config["max_speed"]
        self.reducte_speed = self.max_speed // 2
        self.speed = self.max_speed # Par défaut speed = speed max
        self.max_health = config["max_health"]
        self.current_health = self.max_health
        self.range = config["range"]
        self.damage = config["damage"]
        self.fire_rate = config["fire_rate"]
        
        # Type d'unité
        self.unit_type = config["unit_type"]
        self.unit_name = f"Chaloupe {team.capitalize()}"
        
        # Couleur de portée selon l'équipe
        self.range_color = config["range_color"][team]
        
        # État de mouvement
        self.is_moving = False
        self.target_position = None

        self.path_to_follow = []
        self.current_path_index = 0

        # Pour détection blocage
        self._last_positions = []
        self._block_check_interval = 1.0
        self._last_block_check_time = time.time()

        # Gestion prise en main manuelle (désactive IA)
        self.manual_override = False

        # Multithreading pour pathfinding
        self.path_thread = None
        self.path_found = False
        self.new_path = []
        self.need_recalculate_path = False

        # IA activée par défaut
        self.ia_enabled = True
        
        # Paramètre pour activer/désactiver l'IA
        self.is_ia = is_ia
        
        # Cible ennemie actuelle
        self.target_enemy = None
        self.last_enemy_check = 0
        self.enemy_check_interval = 0.1  # Vérifier les ennemis 10 fois par seconde pour réactivité
        
        # Suivi direct de la cible
        self.target_last_position = None
        self.direct_follow_mode = False  # Mode suivi direct sans pathfinding
        self.last_pathfinding_time = 0
        self.pathfinding_cooldown = 0.5  # Pathfinding maximum 2 fois par seconde (réduit de 1.0 à 0.5)

        # Debug path
        self.debug_path = False

        # === SYSTÈME D'IA AVANCÉE ===
        # Initialiser l'IA d'attaque éclair si disponible et si l'IA est activée
        if AI_AVAILABLE and self.is_ia:
            self.ai_system = ChaloupeAI(self)
            self.use_advanced_ai = True
            self.visual_debug_enabled = True  # Debug visuel activé par défaut
            print(f"Chaloupe {self.team} : IA avancée activée")
        else:
            self.ai_system = None
            self.use_advanced_ai = False
            self.visual_debug_enabled = False
            if not self.is_ia:
                print(f"Chaloupe {self.team} : IA désactivée")
        
    def update(self, dt: int = 0, combat_system: CombatSystem = None, screen: pygame.Surface = None, camera_offset: tuple[float, float] =(0, 0), all_units: list[Unit] = None):
        """Met à jour l'unité en fonction de son état actuel.

        Args:
            dt (int, optional): La différence de temps entre chaque frame. Defaults to 0.
            combat_system (CombatSystem, optional): Le systeme de combat. Defaults to None.
            screen (pygame.Surface, optional): L'écran sur lequel affiché. Defaults to None.
            camera_offset (tuple[float, float], optional): La position de la caméra. Defaults to (0, 0).
            all_units (list[Unit], optional): Liste des unités. Defaults to None.
        """

        # Appeler la mise à jour de la classe parent
        super().update(dt, combat_system, screen, camera_offset, all_units)

        # Logique IA uniquement si activée
        if self.is_ia:
            # Vérification périodique des unités ennemies
            now = time.time()
            if now - self.last_enemy_check > self.enemy_check_interval:
                self.last_enemy_check = now
                # === SYSTÈME D'IA AVANCÉE ===
                if self.use_advanced_ai and self.ai_system:
                    # Utiliser l'IA avancée d'attaque éclair
                    self.ai_system.update(dt, all_units)
                else:
                    # Utiliser le système de base
                    self.check_for_enemies(all_units)

            # === COMPORTEMENT DE BASE === (utilisé si IA avancée désactivée)
            if not self.use_advanced_ai:
                # Suivi direct de la cible (chaque frame pour fluidité maximale)
                if self.target_enemy and self.target_enemy.is_alive:
                    self.direct_follow_target()

        # Suivi du chemin pathfinding dans le thread
        if self.path_thread and self.path_thread.is_alive():
            # Le thread calcule encore, on attend
            pass
        else:
            # Si nouveau chemin calculé, on le charge
            if self.path_found:
                self.path_to_follow = self.new_path
                self.current_path_index = 0
                if self.path_to_follow:
                    self.move_to_position(self.path_to_follow[0])
                self.path_found = False

        # Suivi du déplacement sur chemin
        if self.path_to_follow and not self.manual_override:
            if not self.is_moving:
                self.current_path_index += 1
                if self.current_path_index < len(self.path_to_follow):
                    self.move_to_position(self.path_to_follow[self.current_path_index])
                else:
                    self.path_to_follow = []
                    self.current_path_index = 0

        # Reprise après déplacement manuel
        if self.manual_override and not self.is_moving:
            self.manual_override = False
            if self.target_enemy:
                self.aller_vers_unite_ennemie(self.target_enemy)
            else:
                self.aller_vers_base_ennemie_avec_pathfinding()

        # Détection blocage simple
        now = time.time()
        if now - self._last_block_check_time > self._block_check_interval:
            self._last_block_check_time = now
            self._last_positions.append(self.position)
            if len(self._last_positions) > 5:
                self._last_positions.pop(0)
            if len(self._last_positions) == 5:
                dist_moved = math.sqrt(
                    (self._last_positions[-1][0] - self._last_positions[0][0]) ** 2 +
                    (self._last_positions[-1][1] - self._last_positions[0][1]) ** 2
                )
                if dist_moved < 5:
                    # Blocage détecté, recalculer chemin dans un thread
                    if not self.need_recalculate_path:
                        self.need_recalculate_path = True
                        if self.target_enemy:
                            self.start_pathfinding_thread(lambda: self.compute_path_to_target(self.target_enemy.position))
                        else:
                            self.start_pathfinding_thread(self.compute_path)

        # Dessiner la portée en permanence
        if screen:
            self.draw_range(screen, camera_offset)
            # Dessiner les informations d'IA si disponible et si debug activé
            if self.use_advanced_ai and self.ai_system and getattr(self, 'visual_debug_enabled', False):
                self.draw_ai_debug(screen, camera_offset)
        
        # Dessiner le chemin de pathfinding si en mode debug
        if screen and hasattr(self, 'debug_path') and self.debug_path:
            self.draw_path(screen, camera_offset)

    def pos_base_ennemie(self):
        """Retourne la position de la base ennemie."""
        if self.team == "red":
            return self.game.plateformes["green"].position
        elif self.team == "green":
            return self.game.plateformes["red"].position
        return None

    def pos_cible_ennemie(self, all_units):
        """Trouve la position de l'unité ennemie la plus proche.
        
        Args:
            all_units (list[Unit]): Liste de toutes les unités
            
        Returns:
            tuple: Position (x, y) de l'unité ennemie la plus proche ou None
        """
        if not all_units:
            return None
            
        closest_enemy = None
        min_distance = float('inf')
        
        for unit in all_units:
            # Ignorer les unités de la même équipe, les unités mortes et les plateformes
            if (unit.team == self.team or 
                not unit.is_alive or 
                getattr(unit, 'is_platform', False)):
                continue
                
            # Calculer la distance
            distance = math.sqrt(
                (unit.position[0] - self.position[0]) ** 2 + 
                (unit.position[1] - self.position[1]) ** 2
            )
            
            # Garder l'unité la plus proche
            if distance < min_distance:
                min_distance = distance
                closest_enemy = unit
        
        return closest_enemy.position if closest_enemy else None

    def direct_follow_target(self):
        """Suit directement la cible sans pathfinding constant.
        Utilise le mouvement direct avec vérification d'obstacles occasionnelle.
        """
        if not self.target_enemy or not self.target_enemy.is_alive:
            return
            
        current_target_position = self.target_enemy.position
        current_time = time.time()
        
        # Distance à la cible
        distance_to_target = math.sqrt(
            (current_target_position[0] - self.position[0]) ** 2 + 
            (current_target_position[1] - self.position[1]) ** 2
        )
        
        # Si on est proche de la cible (rayon d'attaque), ne pas bouger
        attack_range = getattr(self, 'range', 100)
        if distance_to_target <= attack_range * 1.2:  # 120% de la portée d'attaque
            self.stop()
            self.is_moving = False
            return
        
        # Vérifier s'il faut utiliser le pathfinding (obstacles bloquants)
        need_pathfinding = self.need_pathfinding_to_target(current_target_position)
        
        if need_pathfinding and (current_time - self.last_pathfinding_time > self.pathfinding_cooldown):
            # Pathfinding seulement si obstacles ET cooldown écoulé
            print(f"Obstacle détecté - Pathfinding vers {self.target_enemy.unit_type}")
            self.last_pathfinding_time = current_time
            self.direct_follow_mode = False
            self.start_pathfinding_thread(lambda: self.compute_path_to_target(current_target_position))
            return  # Arrêter ici, ne PAS continuer avec le mouvement direct!
        elif need_pathfinding:
            # Il y a des obstacles mais le cooldown n'est pas écoulé - ne pas bouger directement !
            return
        else:
            # Mouvement direct vers la cible
            self.direct_follow_mode = True
            self.move_directly_to_target(current_target_position)

    def need_pathfinding_to_target(self, target_position):
        """Vérifie s'il y a des obstacles entre la Chaloupe et sa cible."""
        # Ligne droite entre position actuelle et cible
        start_x, start_y = self.position
        end_x, end_y = target_position
        
        # Vérifier plusieurs points sur la ligne (augmenté pour mieux détecter les îles quantiques)
        steps = 10  # Augmenté de 5 à 10 pour plus de précision
        for i in range(1, steps):
            t = i / steps
            check_x = start_x + (end_x - start_x) * t
            check_y = start_y + (end_y - start_y) * t
            
            # Vérifier si ce point est dans un obstacle
            from Utils import point_in_many_polygons
            if point_in_many_polygons(self.game.obstacles, (check_x, check_y)):
                return True
            
            # Vérifier si ce point est dans une zone de brouillard
            if self.is_point_in_fog(check_x, check_y):
                return True
            
            # Vérifier si ce point est dans une île quantique
            if self.is_point_in_quantum_island(check_x, check_y):
                return True
                
        return False

    def is_point_in_quantum_island(self, x, y):
        """Vérifie si un point est dans une île quantique.
        
        Args:
            x (float): Coordonnée X en pixels
            y (float): Coordonnée Y en pixels
            
        Returns:
            bool: True si le point est dans une île quantique, False sinon
        """
        if not hasattr(self.game, 'quantum_islands'):
            return False
            
        for island in self.game.quantum_islands:
            if hasattr(island, 'matrix') and hasattr(island, 'rect'):
                # Vérifier si le point est dans les limites de l'île
                if (island.rect.x <= x < island.rect.right and 
                    island.rect.y <= y < island.rect.bottom):
                    
                    # Convertir en coordonnées locales de l'île
                    local_x = int(x - island.rect.x)
                    local_y = int(y - island.rect.y)
                    
                    # Convertir en coordonnées de grille (32x32 pixels par cellule)
                    grid_x = local_x // 32
                    grid_y = local_y // 32
                    
                    # Vérifier les limites de la matrice
                    if (0 <= grid_y < len(island.matrix) and 
                        0 <= grid_x < len(island.matrix[grid_y])):
                        # Type 2 = île solide, Type 1 = eau peu profonde
                        # On considère les deux comme obstacles pour la chaloupe
                        cell_type = island.matrix[grid_y][grid_x]
                        if cell_type >= 1:  # 1 = eau peu profonde, 2 = île
                            return True
        
        return False

    def is_point_in_fog(self, x, y):
        """Vérifie si un point est dans une zone de brouillard.
        
        Args:
            x (float): Coordonnée X en pixels
            y (float): Coordonnée Y en pixels
            
        Returns:
            bool: True si le point est dans le brouillard, False sinon
        """
        # Utiliser les zones de brouillard cachées du jeu (polygones TMX)
        if not hasattr(self.game, 'quantique_area_hidden'):
            return False
        
        # Vérifier si le point est dans une zone de brouillard encore cachée
        result = point_in_many_polygons(self.game.quantique_area_hidden, (x, y))
        # point_in_many_polygons retourne (True, polygon) si trouvé, False sinon
        is_in_fog = result is not False
        
        return is_in_fog

    def move_directly_to_target(self, target_position):
        """Mouvement direct vers la cible sans pathfinding."""
        # Arrêter le pathfinding actuel
        self.path_to_follow = []
        self.current_path_index = 0
        
        # Mouvement direct vers la cible
        self.move_to_position(target_position)

    def check_for_enemies(self, all_units):
        """Vérifie s'il y a des unités ennemies à proximité et met à jour la cible.
        Priorité aux gros navires (bateau, paquebot).
        
        Args:
            all_units (list[Unit]): Liste de toutes les unités
        """
        if not all_units or not self.ia_enabled:
            return
            
        # Types d'unités prioritaires pour les Chaloupes (gros navires)
        priority_targets = ["bateau", "paquebot"]
        
        best_target = None
        min_priority_distance = float('inf')
        min_other_distance = float('inf')
        closest_other = None
        
        detection_range = 800  # Portée de détection étendue pour chercher activement
        
        for unit in all_units:
            # Ignorer les unités de la même équipe, les unités mortes et les plateformes
            if (unit.team == self.team or 
                not unit.is_alive or 
                getattr(unit, 'is_platform', False)):
                continue
                
            # Calculer la distance
            distance = math.sqrt(
                (unit.position[0] - self.position[0]) ** 2 + 
                (unit.position[1] - self.position[1]) ** 2
            )
            
            # Vérifier le type d'unité
            unit_type = getattr(unit, 'unit_type', '')
            
            # Si c'est une cible prioritaire (gros navire)
            if unit_type in priority_targets and distance <= detection_range:
                if distance < min_priority_distance:
                    min_priority_distance = distance
                    best_target = unit
            # Sinon, garder comme cible secondaire
            elif distance <= detection_range and distance < min_other_distance:
                min_other_distance = distance
                closest_other = unit
        
        # Prioriser les gros navires, sinon prendre la cible la plus proche
        new_target = best_target if best_target else closest_other
        
        # Mettre à jour la cible
        if new_target != self.target_enemy:
            self.target_enemy = new_target
            if new_target:
                # Aller vers la nouvelle cible
                self.aller_vers_unite_ennemie(new_target)
                print(f"Chaloupe {self.team} cible maintenant: {new_target.unit_type}")
            else:
                # Plus d'ennemis dans la zone, patrouiller sans aller vers la base
                self.patrol_area()

    def patrol_area(self):
        """Fait patrouiller la Chaloupe dans une zone pour chercher des ennemis."""
        if not hasattr(self, '_patrol_points') or not self._patrol_points:
            # Créer des points de patrouille autour de la position de spawn
            spawn_x, spawn_y = self.position
            patrol_radius = 400
            
            self._patrol_points = [
                (spawn_x + patrol_radius, spawn_y),
                (spawn_x, spawn_y + patrol_radius),
                (spawn_x - patrol_radius, spawn_y),
                (spawn_x, spawn_y - patrol_radius),
                (spawn_x + patrol_radius//2, spawn_y + patrol_radius//2),
                (spawn_x - patrol_radius//2, spawn_y + patrol_radius//2),
                (spawn_x - patrol_radius//2, spawn_y - patrol_radius//2),
                (spawn_x + patrol_radius//2, spawn_y - patrol_radius//2)
            ]
            self._current_patrol_index = 0
        
        # Si on n'est pas en mouvement, aller au prochain point de patrouille
        if not self.is_moving:
            target_point = self._patrol_points[self._current_patrol_index]
            self.start_pathfinding_thread(lambda: self.compute_path_to_target(target_point))
            self._current_patrol_index = (self._current_patrol_index + 1) % len(self._patrol_points)

    def move_to_position(self, target_position):
        """Déplace l'unité vers une position cible en utilisant le système de la classe parent.
        
        Args:
            target_position (tuple): Position cible (x, y)
        """
        if not target_position:
            return
        
        # Utiliser le système de mouvement de la classe parent
        super().move_to_position(target_position)

    def move_to_click(self, target_position):
        """Méthode pour déplacer l'unité vers une position cliquée par le joueur.
        Utilise le pathfinding pour contourner les obstacles.
        
        Args:
            target_position (tuple): Position cible (x, y)
        """
        self.manual_override = True
        self.target_enemy = None  # Annuler la cible ennemie lors d'un clic manuel
        
        # Lancer le pathfinding vers la position cliquée
        self.start_pathfinding_thread(lambda: self.compute_path_to_target(target_position))

    def aller_vers_base_ennemie(self):
        """Déplacement direct vers la base ennemie sans pathfinding."""
        position_base_ennemie = self.pos_base_ennemie()
        if position_base_ennemie:
            self.move_to_position(position_base_ennemie)

    def aller_vers_unite_ennemie(self, enemy_unit):
        """Démarre le calcul du chemin vers une unité ennemie spécifique.
        
        Args:
            enemy_unit (Unit): L'unité ennemie à cibler
        """
        if not enemy_unit or not enemy_unit.is_alive:
            self.target_enemy = None
            self.target_last_position = None
            self.patrol_area()
            return
            
        # Passer en mode suivi direct
        self.target_last_position = enemy_unit.position
        self.direct_follow_mode = True
        
        # Commencer immédiatement le mouvement direct
        self.move_directly_to_target(enemy_unit.position)

    def aller_vers_base_ennemie_avec_pathfinding(self):
        """Démarre le calcul du chemin vers la base ennemie dans un thread."""
        if self.path_thread and self.path_thread.is_alive():
            return  # Un calcul est déjà en cours
        self.need_recalculate_path = False
        self.start_pathfinding_thread(self.compute_path)

    def start_pathfinding_thread(self, target_function):
        """Démarre un thread pour calculer le pathfinding.
        
        Args:
            target_function: Fonction à exécuter dans le thread
        """
        if self.path_thread and self.path_thread.is_alive():
            return  # Un calcul est déjà en cours, ne pas perturber
        
        self.path_thread = threading.Thread(target=target_function)
        self.path_thread.daemon = True  # Thread daemon pour éviter les blocages
        self.path_thread.start()

    def compute_path(self):
        """Calcule le chemin vers la base ennemie."""
        start = self.position
        goal = self.pos_base_ennemie()
        if not start or not goal:
            return

        path = self.a_star_search(start, goal)
        if path:
            self.new_path = path
            self.path_found = True

    def compute_path_to_target(self, target_position):
        """Calcule le chemin vers une position cible spécifique.
        
        Args:
            target_position (tuple): Position cible (x, y)
        """
        start = self.position
        if not start or not target_position:
            return

        path = self.a_star_search(start, target_position)
        if path:
            self.new_path = path
            self.path_found = True

    def a_star_search(self, start, goal):
        """Implémentation A* améliorée sur grille 32x32 pixels avec mouvements diagonaux.
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

        def is_valid_position(grid_pos):
            """Vérifie si une position de grille est valide (pas dans un obstacle)."""
            return grid_pos not in obstacles

        start_grid = pos_to_grid(start)
        goal_grid = pos_to_grid(goal)

        # Construire l'ensemble des obstacles à partir des polygones
        obstacles = set()
        
        # Obstacles principaux (îles, récifs)
        for poly in self.game.obstacles:
            min_x = min(p[0] for p in poly) // 32
            max_x = max(p[0] for p in poly) // 32
            min_y = min(p[1] for p in poly) // 32
            max_y = max(p[1] for p in poly) // 32
            for x in range(int(min_x), int(max_x) + 1):
                for y in range(int(min_y), int(max_y) + 1):
                    obstacles.add((x, y))
        
        # Ajouter les îles quantiques comme obstacles
        if hasattr(self.game, 'quantum_islands'):
            for island in self.game.quantum_islands:
                if hasattr(island, 'matrix') and hasattr(island, 'rect'):
                    # Utiliser la matrice de l'île pour déterminer les obstacles
                    start_x = int(island.rect.x // 32)
                    start_y = int(island.rect.y // 32)
                    
                    quantum_obstacles_per_island = 0
                    
                    # Parcourir toute la matrice de l'île
                    for y, row in enumerate(island.matrix):
                        for x, cell in enumerate(row):
                            # Type 2 = île solide, Type 1 = eau peu profonde (peut aussi être obstacle selon config)
                            if cell == 2:  # Cellule d'île (obstacle)
                                grid_x = start_x + x
                                grid_y = start_y + y
                                obstacles.add((grid_x, grid_y))
                                quantum_obstacles_per_island += 1

        # Ajouter les zones de brouillard comme obstacles pour les Chaloupes
        # Utiliser les zones de brouillard cachées (quantique_area_hidden)
        if hasattr(self.game, 'quantique_area_hidden'):
            from Utils import point_in_many_polygons
            
            fog_obstacles = 0
            
            # Pour chaque zone de brouillard cachée, ajouter les cellules comme obstacles
            for fog_polygon in self.game.quantique_area_hidden:
                # Obtenir les limites du polygone de brouillard
                min_x = min(point[0] for point in fog_polygon) // 32
                max_x = max(point[0] for point in fog_polygon) // 32
                min_y = min(point[1] for point in fog_polygon) // 32
                max_y = max(point[1] for point in fog_polygon) // 32
                
                # Ajouter toutes les cellules dans cette zone comme obstacles
                for x in range(int(min_x), int(max_x) + 1):
                    for y in range(int(min_y), int(max_y) + 1):
                        # Vérifier si le centre de la cellule est dans le polygone
                        cell_center_x = x * 32 + 16
                        cell_center_y = y * 32 + 16
                        result = point_in_many_polygons([fog_polygon], (cell_center_x, cell_center_y))
                        if result is not False:  # Trouvé dans un polygone
                            obstacles.add((x, y))
                            fog_obstacles += 1

        # Mouvements possibles : 4 directions cardinales + 4 diagonales
        neighbors = [
            (0, 1, 1),   # Nord
            (1, 0, 1),   # Est  
            (0, -1, 1),  # Sud
            (-1, 0, 1),  # Ouest
            (1, 1, 1.4), # Nord-Est (coût diagonal)
            (1, -1, 1.4), # Sud-Est
            (-1, -1, 1.4), # Sud-Ouest
            (-1, 1, 1.4)  # Nord-Ouest
        ]

        # Structures de données pour A*
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

            # Examiner tous les voisins
            for dx, dy, cost in neighbors:
                neighbor = (current[0] + dx, current[1] + dy)
                
                # Vérifier si le voisin est valide
                if neighbor in obstacles:
                    continue
                
                # Pour les mouvements diagonaux, vérifier que les côtés adjacents sont libres
                if abs(dx) == 1 and abs(dy) == 1:
                    if (current[0] + dx, current[1]) in obstacles or (current[0], current[1] + dy) in obstacles:
                        continue
                
                # Calculer le nouveau g_score
                tentative_g_score = g_score[current] + cost
                
                # Si ce chemin vers le voisin est meilleur
                if tentative_g_score < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal_grid)
                    open_set.add(neighbor)

        return None  # Aucun chemin trouvé

    def heuristic(self, a, b):
        """Heuristique euclidienne pour A* (meilleure que Manhattan pour les mouvements diagonaux)."""
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        return math.sqrt(dx * dx + dy * dy)

    def ia(self):
        """Méthode d'IA principale pour la Chaloupe."""
        if not self.ia_enabled:
            return
            
        # Si on a une cible ennemie valide, ne jamais l'abandonner
        if self.target_enemy and self.target_enemy.is_alive:
            # Continuer à poursuivre la cible peu importe la distance
            self.aller_vers_unite_ennemie(self.target_enemy)
        else:
            # Pas de cible valide, chercher activement ou patrouiller
            self.target_enemy = None
            self.patrol_area()

    def patrol_area(self):
        """Fait patrouiller la Chaloupe dans une zone pour chercher des ennemis."""
        if not hasattr(self, '_patrol_points') or not self._patrol_points:
            # Créer des points de patrouille autour de la position de spawn
            spawn_x, spawn_y = self.position
            patrol_radius = 400
            
            self._patrol_points = [
                (spawn_x + patrol_radius, spawn_y),
                (spawn_x, spawn_y + patrol_radius),
                (spawn_x - patrol_radius, spawn_y),
                (spawn_x, spawn_y - patrol_radius),
                (spawn_x + patrol_radius//2, spawn_y + patrol_radius//2),
                (spawn_x - patrol_radius//2, spawn_y + patrol_radius//2),
                (spawn_x - patrol_radius//2, spawn_y - patrol_radius//2),
                (spawn_x + patrol_radius//2, spawn_y - patrol_radius//2)
            ]
            self._current_patrol_index = 0
        
        # Si on n'est pas en mouvement, aller au prochain point de patrouille
        if not self.is_moving:
            target_point = self._patrol_points[self._current_patrol_index]
            self.start_pathfinding_thread(lambda: self.compute_path_to_target(target_point))
            self._current_patrol_index = (self._current_patrol_index + 1) % len(self._patrol_points)

    def set_manual_target(self, target_position):
        """Définit une cible manuelle pour l'unité (utilisé lors des clics).
        
        Args:
            target_position (tuple): Position cible (x, y)
        """
        self.move_to_click(target_position)

    def draw_path(self, screen, camera_offset):
        """Dessine le chemin de pathfinding pour le débogage.
        
        Args:
            screen (pygame.Surface): Surface d'affichage
            camera_offset (tuple): Décalage de la caméra
        """
        if not self.path_to_follow or len(self.path_to_follow) < 2:
            return
            
        # Convertir les positions du chemin en coordonnées écran
        screen_points = []
        for point in self.path_to_follow:
            screen_x = point[0] - camera_offset[0]
            screen_y = point[1] - camera_offset[1]
            screen_points.append((screen_x, screen_y))
        
        # Dessiner le chemin en lignes vertes
        if len(screen_points) > 1:
            pygame.draw.lines(screen, (0, 255, 0), False, screen_points, 2)
        
        # Dessiner les points du chemin
        for i, point in enumerate(screen_points):
            color = (255, 0, 0) if i == self.current_path_index else (0, 255, 0)
            pygame.draw.circle(screen, color, (int(point[0]), int(point[1])), 4)

    def enable_debug_path(self):
        """Active l'affichage du chemin de débogage."""
        self.debug_path = True
        
    def disable_debug_path(self):
        """Désactive l'affichage du chemin de débogage."""
        self.debug_path = False

    def draw_ai_debug(self, screen, camera_offset):
        """Dessine les informations de debug pour l'IA d'attaque éclair."""
        if not self.ai_system:
            return
            
        try:
            debug_info = self.ai_system.get_debug_info()
            
            # Vérification que debug_info n'est pas None
            if not debug_info:
                return
            
            # Position à l'écran
            screen_x = int(self.position[0] - camera_offset[0])
            screen_y = int(self.position[1] - camera_offset[1]) - 50
            
            # Vérifier que la position est dans l'écran
            if screen_x < -100 or screen_x > screen.get_width() + 100 or screen_y < -100 or screen_y > screen.get_height() + 100:
                return
            
            # Font pour le texte
            font = pygame.font.Font(None, 16)
            small_font = pygame.font.Font(None, 14)
            
            # === INFORMATIONS IA STANDARD ===
            y_offset = 0
            
            # État actuel avec couleur selon l'état
            state_colors = {
                "Recherche": (128, 128, 128),    # Gris
                "Position": (255, 255, 0),       # Jaune
                "Attaque": (255, 0, 0),          # Rouge
                "Retraite": (0, 255, 0)          # Vert
            }
            color = state_colors.get(debug_info.get("state", ""), (255, 255, 255))
            
            state_text = f"IA: {debug_info.get('state', 'Unknown')}"
            text_surface = font.render(state_text, True, color)
            screen.blit(text_surface, (screen_x, screen_y + y_offset))
            y_offset += 18
            
            # === INFORMATIONS Q-LEARNING ===
            qlearning_info = debug_info.get('qlearning', {})
            
            if qlearning_info.get('enabled', False):
                # Action Q-Learning
                action_text = f"Q-Action: {qlearning_info.get('last_action', 'None')[:8]}"
                text_surface = small_font.render(action_text, True, (255, 255, 0))
                screen.blit(text_surface, (screen_x, screen_y + y_offset))
                y_offset += 15
                
                # Récompense avec couleur
                last_reward = float(qlearning_info.get('last_reward', '0'))
                reward_color = (0, 255, 0) if last_reward > 0 else (255, 100, 100) if last_reward < 0 else (200, 200, 200)
                reward_text = f"R: {last_reward:.1f}"
                text_surface = small_font.render(reward_text, True, reward_color)
                screen.blit(text_surface, (screen_x, screen_y + y_offset))
                y_offset += 15
                
                # Exploration (epsilon)
                epsilon_text = f"ε: {qlearning_info.get('epsilon', '0.000')}"
                text_surface = small_font.render(epsilon_text, True, (200, 200, 200))
                screen.blit(text_surface, (screen_x, screen_y + y_offset))
                y_offset += 15
                
            else:
                # Q-Learning désactivé
                ql_disabled = small_font.render("Q-Learning: OFF", True, (100, 100, 100))
                screen.blit(ql_disabled, (screen_x, screen_y + y_offset))
            
            # === VISUALISATIONS GÉOMÉTRIQUES ===
            if hasattr(self.ai_system, 'target') and self.ai_system.target:
                target_screen_x = int(self.ai_system.target.position[0] - camera_offset[0])
                target_screen_y = int(self.ai_system.target.position[1] - camera_offset[1])
                
                # Vérifier que la cible est dans l'écran
                if (0 <= target_screen_x <= screen.get_width() and 
                    0 <= target_screen_y <= screen.get_height()):
                    
                    # Ligne vers la cible (couleur selon l'action Q-Learning)
                    line_color = (255, 255, 0)  # Jaune par défaut
                    
                    if qlearning_info.get('enabled', False):
                        last_action = qlearning_info.get('last_action', '')
                        if 'attack' in last_action:
                            line_color = (255, 0, 0)  # Rouge pour attaque
                        elif 'retreat' in last_action:
                            line_color = (0, 255, 255)  # Cyan pour retraite
                        elif 'orbit' in last_action:
                            line_color = (255, 0, 255)  # Magenta pour orbite
                    
                    pygame.draw.line(screen, line_color, 
                                   (screen_x + 20, screen_y + 20),
                                   (target_screen_x, target_screen_y), 2)
                    
                    # Zone de sécurité (jaune)
                    safe_distance = min(debug_info.get("safe_distance", 100), 300)  # Limiter la taille
                    pygame.draw.circle(screen, (255, 255, 0), 
                                     (target_screen_x, target_screen_y), safe_distance, 1)
                    
                    # Portée d'attaque de l'ennemi (rouge clair)
                    enemy_range = min(self.ai_system._get_enemy_range(), 250)  # Limiter la taille
                    pygame.draw.circle(screen, (255, 100, 100), 
                                     (target_screen_x, target_screen_y), enemy_range, 1)
        
        except Exception as e:
            # En cas d'erreur, ne pas crasher le jeu
            print(f"Erreur debug IA: {e}")
            pass
            
            # === INFORMATIONS Q-LEARNING ===
            qlearning_info = debug_info.get('qlearning', {})
            
            if qlearning_info.get('enabled', False):
                # Action Q-Learning
                action_text = f"Q-Action: {qlearning_info.get('last_action', 'None')[:8]}"
                text_surface = small_font.render(action_text, True, (255, 255, 0))
                screen.blit(text_surface, (screen_x, screen_y + y_offset))
                y_offset += 15
                
                # Récompense avec couleur
                last_reward = float(qlearning_info.get('last_reward', '0'))
                reward_color = (0, 255, 0) if last_reward > 0 else (255, 100, 100) if last_reward < 0 else (200, 200, 200)
                reward_text = f"R: {last_reward:.1f}"
                text_surface = small_font.render(reward_text, True, reward_color)
                screen.blit(text_surface, (screen_x, screen_y + y_offset))
                y_offset += 15
                
                # Exploration (epsilon)
                epsilon_text = f"ε: {qlearning_info.get('epsilon', '0.000')}"
                text_surface = small_font.render(epsilon_text, True, (200, 200, 200))
                screen.blit(text_surface, (screen_x, screen_y + y_offset))
                y_offset += 15
                
            else:
                # Q-Learning désactivé
                ql_disabled = small_font.render("Q-Learning: OFF", True, (100, 100, 100))
                screen.blit(ql_disabled, (screen_x, screen_y + y_offset))
            
            # === VISUALISATIONS GÉOMÉTRIQUES ===
            if hasattr(self.ai_system, 'target') and self.ai_system.target:
                target_screen_x = int(self.ai_system.target.position[0] - camera_offset[0])
                target_screen_y = int(self.ai_system.target.position[1] - camera_offset[1])
                
                # Vérifier que la cible est dans l'écran
                if (0 <= target_screen_x <= screen.get_width() and 
                    0 <= target_screen_y <= screen.get_height()):
                    
                    # Ligne vers la cible (couleur selon l'action Q-Learning)
                    line_color = (255, 255, 0)  # Jaune par défaut
                    
                    if qlearning_info.get('enabled', False):
                        last_action = qlearning_info.get('last_action', '')
                        if 'attack' in last_action:
                            line_color = (255, 0, 0)  # Rouge pour attaque
                        elif 'retreat' in last_action:
                            line_color = (0, 255, 255)  # Cyan pour retraite
                        elif 'orbit' in last_action:
                            line_color = (255, 0, 255)  # Magenta pour orbite
                    
                    pygame.draw.line(screen, line_color, 
                                   (screen_x + 20, screen_y + 20),
                                   (target_screen_x, target_screen_y), 2)
                    
                    # Zone de sécurité (jaune)
                    safe_distance = min(debug_info.get("safe_distance", 100), 300)  # Limiter la taille
                    pygame.draw.circle(screen, (255, 255, 0), 
                                     (target_screen_x, target_screen_y), safe_distance, 1)
                    
                    # Portée d'attaque de l'ennemi (rouge clair)
                    enemy_range = min(self.ai_system._get_enemy_range(), 250)  # Limiter la taille
                    pygame.draw.circle(screen, (255, 100, 100), 
                                     (target_screen_x, target_screen_y), enemy_range, 1)
        
        except Exception as e:
            print(f"Erreur debug IA: {e}")
            pass
    
    # ==========================================
    # MÉTHODES Q-LEARNING
    # ==========================================
    
    def get_qlearning_stats(self):
        """Retourne les statistiques Q-Learning de l'IA."""
        if self.use_advanced_ai and self.ai_system:
            return self.ai_system.get_qlearning_stats()
        return None
    
    def save_qlearning_progress(self):
        """Sauvegarde le progrès Q-Learning."""
        if self.use_advanced_ai and self.ai_system:
            self.ai_system.save_qlearning_progress()
    
    def toggle_qlearning(self, enabled: bool):
        """Active/désactive le Q-Learning."""
        if self.use_advanced_ai and self.ai_system:
            self.ai_system.toggle_qlearning(enabled)
    
    def is_qlearning_enabled(self):
        """Vérifie si le Q-Learning est activé."""
        if self.use_advanced_ai and self.ai_system:
            return getattr(self.ai_system, 'qlearning_enabled', False)
        return False

class ChaloupeRouge(Chaloupe):
    def __init__(self, game, is_ia: bool = True):
        super().__init__(game, team="red", is_ia=is_ia)

class ChaloupeVerte(Chaloupe):
    def __init__(self, game, is_ia: bool = True):
        super().__init__(game, team="green", is_ia=is_ia)