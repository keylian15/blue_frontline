import time
import math
import pygame
import threading
import random
from Class.units.Unit import Unit
from Class.Combat import CombatSystem, Mine
from math import *
from Global import UNIT_CONFIGS
from Utils import point_in_many_polygons


class SousMarin(Unit):

    """Classe unifiée pour les unités Sous-marin (Rouge et Vert)."""

    def __init__(self, game, team: str, is_ia: bool = True):
        """Initialise une instance de SousMarin.

        Args:
            game: Instance du jeu.
            team (str): Équipe de l'unité.
            is_ia (bool): Indique si l'unité est contrôlée par l'IA. Défaut à True.
        """
        # Récupérer la configuration depuis Global.py
        config = UNIT_CONFIGS["sousmarin"]

        # Initialiser avec l'image appropriée et le type d'unité
        super().__init__(game, team=team, unit_type="sousmarin")

        # === Spécifications du Sous-marin depuis Global.py ===
        self.cost = config["cost"]

        self.max_speed = config["max_speed"]
        self.reducte_speed = self.max_speed // 2
        self.speed = self.max_speed  # Par défaut speed = speed max
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
        # Positions où poser des mines autour de la cible
        self.mine_positions_around_target = []
        self.current_mine_index = 0  # Index de la prochaine position de mine

        # Modes d'IA
        # Nouvel état par défaut : défense de base
        # Modes possibles: "defense_base", "patrol", "attack", "return_to_platform"
        self.ia_mode = "defense_base"
        self.previous_mode = "patrol"  # Pour suivre le mode précédent
        self.is_ia = is_ia
        self.platform_position = None  # Position de la plateforme pétrolière de l'équipe

        # ===== Défense de base =====
        # Rayon pour poser les mines autour de la plateforme (300px)
        self.defense_square_radius = 300
        # Rayon pour compter les mines existantes (400px)
        self.defense_count_radius = 400
        self.defense_max_mines = 30
        # espacement entre emplacements de mines (approx)
        self.defense_grid_spacing = 60
        self.defense_mine_positions = []  # positions planifiées pour poser des mines
        self.defense_current_mine_index = 0
        self.defense_positions_generated = False

        # Variables pour A* pathfinding (spécifiques au sous-marin)
        self.current_path = []  # Chemin A* actuel
        self.path_index = 0  # Index dans le chemin actuel
        self.is_computing_path = False  # Flag indiquant qu'un calcul est en cours
        # ===== Variables pour la logique de groupe (IA coordonnée) =====
        # Identifiant du groupe auquel appartient ce sous-marin (None si isolé)
        self.group_id = None
        # Booléen indiquant si cette unité est le leader du groupe
        self.is_leader = False
        # Slot de formation (index) pour positionner les suiveurs autour du leader
        self.formation_slot = None
        # Distance voulue entre leader et suiveur en formation (px)
        self.formation_distance = 80
        # Référence à la cible actuelle du groupe (unité ennemi)
        self.group_target_unit = None
        # Délai interne pour éviter de reformer un groupe trop souvent
        self._last_group_formed_time = 0
        # Pour pathfinding générique vers une cible (attaques)
        self.path_goal = None
        self.new_path = None
        self.path_found = False
        self.need_recalculate_path = False

    def update(self, dt: int = 0, combat_system: CombatSystem = None, screen: pygame.Surface = None, camera_offset: tuple[float, float] = (0, 0), all_units: list[Unit] = None):
        """Met à jour l'unité en fonction de son état actuel.

        Args:
            dt (int, optional): La différence de temps entre chaque frame. Defaults to 0.
            combat_system (CombatSystem, optional): Le systeme de combat. Defaults to None.
            screen (pygame.Surface, optional): L'écran sur lequel affiché. Defaults to None.
            camera_offset (tuple[float, float], optional): La position de la caméra. Defaults to (0, 0).
            all_units (list[Unit], optional): Liste des unités. Defaults to None.
        """

        # Appeler l'IA de déplacement automatique
        if all_units and getattr(self, 'is_ia', True):
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
        multiplica = self.game.hud.timer.get_speed_multiplier() if hasattr(
            self.game, 'hud') and hasattr(self.game.hud, 'timer') else 1
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
            # -- AUDIO : drop mine --
            try:
                if hasattr(self.game, "sound") and self.game.sound:
                    self.game.sound.on_mine_dropped((x, y))
            except Exception:
                # ne jamais crasher pour du son
                pass
            return True
        else:
            pass
        return False

    def is_position_valid(self, x, y, treat_platform_as_obstacle: bool = False):
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

        # Vérifier les obstacles dans les îles quantiques DÉCOUVERTES
        if hasattr(self.game, 'quantique_area') and self.game.quantique_area:
            result = point_in_many_polygons(self.game.quantique_area, world_pos)
            if result:
                # On a trouvé une île quantique, vérifier si elle est découverte
                try:
                    index = self.game.quantique_area.index(result[1])
                    # Correction par rapport au nom des îles quantiques
                    if index == 0:
                        index = 4
                    
                    # Parcourir les îles graphiques pour retrouver la bonne île
                    if hasattr(self.game, 'quantum_islands') and self.game.quantum_islands:
                        for island in self.game.quantum_islands:
                            # Vérifier qu'on a le bon index et le bon nom
                            if hasattr(island, 'name') and island.name and index == int(island.name[-1]):
                                # On récupère la matrice de Perlin
                                if hasattr(island, 'matrix') and island.matrix:
                                    from Class.Perlin import Perlin
                                    num = Perlin.get_zone_type(x, y, island.matrix, island)
                                    
                                    # Si c'est une zone d'île (valeur 2), c'est un obstacle
                                    if num == 2:
                                        return False
                                break
                except (ValueError, IndexError, AttributeError):
                    # En cas d'erreur, ignorer cette vérification
                    pass

        # Vérifier s'il y a une autre unité mobile à cette position
        unit_at_pos = self.game.find_unit_at_position(x, y, self)
        if unit_at_pos:
            # Si on considère les plateformes comme obstacles, rejeter toute position occupée
            if treat_platform_as_obstacle:
                return False
            # Sinon, autoriser la plateforme mais bloquer les autres unités
            if not hasattr(unit_at_pos, 'is_platform') or not unit_at_pos.is_platform:
                return False

        return True

    def is_path_clear(self, target_x, target_y, num_checks=10, treat_platform_as_obstacle: bool = False):
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
            if not self.is_position_valid(check_x, check_y, treat_platform_as_obstacle=treat_platform_as_obstacle):
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

    # ------------------ LOGIQUE DE GROUPE ------------------
    def form_attack_group(self, all_units, detected_target=None, radius=600, min_members=2):
        """Forme un groupe d'attaque autour de ce sous-marin.

        Si suffisamment d'alliés sont proches (< radius), on choisit un leader
        et on assigne group_id + ia_mode='group_attack' aux membres.

        Args:
            all_units (list[Unit]): Liste de toutes les unités.
            detected_target (Unit|None): La cible initiale détectée (éventuellement None).
            radius (int): Rayon de recherche d'alliés en pixels.
            min_members (int): Nombre minimum de membres pour former un groupe (inclut le détecteur).
        """
        # Vérifier cooldown anti-reformation
        now = time.time()
        if now - getattr(self, '_last_group_formed_time', 0) < 1.0:
            return False

        # Trouver alliés sous-marins vivants de la même équipe.
        # Accepte les instances de SousMarin OU les unités avec unit_type == 'sousmarin'
        allies = []
        for u in all_units:
            if u is self:
                continue
            if not getattr(u, 'is_alive', False):
                continue
            if getattr(u, 'team', None) != self.team:
                continue
            # Ne considérer que les alliés contrôlés par l'IA
            if not getattr(u, 'is_ia', True):
                continue
            if isinstance(u, SousMarin) or getattr(u, 'unit_type', None) == 'sousmarin':
                allies.append(u)

        # Exclure soi-même pour le calcul mais on l'ajoutera
        # Utiliser <= radius pour inclure la frontière
        nearby = [a for a in allies if a != self and math.hypot(
            a.position[0]-self.position[0], a.position[1]-self.position[1]) <= radius]

        # inclure soi-même
        nearby_with_self = [self] + nearby

        # debug: afficher les comptes pour diagnostic
        
        if len(nearby_with_self) >= min_members:
            # Créer un id de groupe unique
            group_id = random.randint(1000, 9999)
            # Choisir un leader: le plus proche de la cible si fournie, sinon le détecteur
            leader = self
            if detected_target:
                # choisir l'allié le plus proche de la cible
                best = None
                bestd = float('inf')
                for a in nearby_with_self:
                    dx = a.position[0] - detected_target.position[0]
                    dy = a.position[1] - detected_target.position[1]
                    d = math.hypot(dx, dy)
                    if d < bestd:
                        best = a
                        bestd = d
                if best:
                    leader = best

            # Assignation des membres
            slot = 0
            for a in nearby_with_self:
                a.group_id = group_id
                a.group_target_unit = detected_target
                a.is_leader = (a == leader)
                a.formation_slot = slot if not a.is_leader else 0
                if getattr(a, 'is_ia', True):
                    a.ia_mode = 'group_attack'
                slot += 1

            leader.is_leader = True
            leader.group_id = group_id
            leader.group_target_unit = detected_target
            if getattr(leader, 'is_ia', True):
                leader.ia_mode = 'group_attack'

            self._last_group_formed_time = now

            return True


        return False

    def broadcast_attack_signal(self, all_units):
        """Le leader envoie un signal d'attaque à tous les alliés de son groupe."""
        if not self.is_leader or not self.group_id:
            return
        for ally in all_units:
            if getattr(ally, 'group_id', None) == self.group_id:
                # Transmettre la cible
                ally.group_target_unit = self.group_target_unit
                # Autoriser l'attaque (changer de mode interne si besoin) uniquement si c'est une IA
                if getattr(ally, 'is_ia', True):
                    ally.ia_mode = 'group_attack'
                    # Demander une attaque immédiate (pour synchroniser)
                    try:
                        ally.attack_target(self.group_target_unit)
                    except Exception:
                        # ne pas faire planter si une unité n'implémente pas attack_target
                        pass

    def attack_target(self, target_unit):
        """Effectue l'attaque vers la target sans redétection (logique similaire à behavior_attack)."""
        if not target_unit or not target_unit.is_alive:
            return

        dx = target_unit.position[0] - self.position[0]
        dy = target_unit.position[1] - self.position[1]
        distance = math.hypot(dx, dy)
        collision_distance = 35

        # Si proche, poser une mine
        if distance <= collision_distance:
            self.stop()
            self.is_moving = False
            self.target_position = None
            if self.can_place_mine():
                placed = self.place_mine(
                    int(self.position[0]), int(self.position[1]))
            return

        # sinon, utiliser A* pour atteindre la cible (thread si possible)
        goal = (target_unit.position[0], target_unit.position[1])
        # Si la goal a changé, demander un nouveau chemin
        if self.path_goal != goal:
            self.path_goal = goal
            # lancer le thread de pathfinding si possible
            try:
                if not getattr(self, 'path_thread', None) or not self.path_thread.is_alive():
                    self.start_pathfinding_thread(self.compute_path_to_goal)
            except Exception:
                # retomber sur calcul synchrone
                path = self.a_star_search(self.position, goal)
                if path:
                    self.current_path = path
                    self.path_index = 0
                    self.need_recalculate_path = False

        # appliquer tout chemin disponible
        if self.update_path_from_thread() or self.current_path:
            # suivre le chemin A*
            followed = self.follow_path()
            if followed:
                return

        # fallback: si A* impossible, essayer le mouvement direct
        if self.is_path_clear(target_unit.position[0], target_unit.position[1]):
            self.move_to_position(target_unit.position)
        else:
            self.find_alternative_path_to_target(
                target_unit.position[0], target_unit.position[1])

    def coordinate_retreat(self, all_units):
        """Ordre de retraite coordonnée: envoie tous les membres du groupe en 'return_to_platform'."""
        if not self.group_id:
            return
        for ally in all_units:
            if getattr(ally, 'group_id', None) == self.group_id:
                if getattr(ally, 'is_ia', True):
                    ally.ia_mode = 'return_to_platform'
                # réinitialiser certains flags de groupe
                ally.group_id = None
                ally.is_leader = False
                ally.formation_slot = None
                ally.group_target_unit = None

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

    def find_nearby_bateaux(self, all_units, detection_range=400):
        """Trouve les bateaux ennemis à proximité.

        Args:
            all_units (list[Unit]): Liste de toutes les unités du jeu
            detection_range (int): Rayon de détection en pixels (par défaut 400px)

        Returns:
            list[Unit]: Liste des bateaux ennemis détectés
        """
        nearby_bateaux = []

        for unit in all_units:
            # Vérifier si c'est un ennemi vivant
            if not unit.is_alive or unit.team == self.team:
                continue

            # Vérifier si c'est un bateau
            if hasattr(unit, 'unit_type') and unit.unit_type == "bateau":
                # Calculer la distance
                dx = unit.position[0] - self.position[0]
                dy = unit.position[1] - self.position[1]
                distance = math.sqrt(dx**2 + dy**2)

                # Si dans le rayon de détection
                if distance <= detection_range:
                    nearby_bateaux.append(unit)

        return nearby_bateaux

    def get_nearby_allied_submarines(self, all_units, radius=600):
        """Renvoie la liste des sous-marins alliés (vivants) dans un rayon donné (exclut self)."""
        allies = []
        for u in all_units:
            if u is self:
                continue
            if not getattr(u, 'is_alive', False):
                continue
            if isinstance(u, SousMarin) and u.team == self.team:
                dx = u.position[0] - self.position[0]
                dy = u.position[1] - self.position[1]
                if math.hypot(dx, dy) <= radius:
                    allies.append(u)
        return allies

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
        
        Esquive toutes les îles quantiques (découvertes ou non).

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
        
        # Ajouter les obstacles normaux (îles principales)
        if hasattr(self.game, 'obstacles') and self.game.obstacles:
            for poly in self.game.obstacles:
                min_x = min(p[0] for p in poly) // 32
                max_x = max(p[0] for p in poly) // 32
                min_y = min(p[1] for p in poly) // 32
                max_y = max(p[1] for p in poly) // 32
                for x in range(int(min_x), int(max_x)+1):
                    for y in range(int(min_y), int(max_y)+1):
                        obstacles.add((x, y))

        # Ajouter les zones quantiques CACHÉES comme obstacles complets
        if hasattr(self.game, 'quantique_area_hidden') and self.game.quantique_area_hidden:
            for poly in self.game.quantique_area_hidden:
                min_x = min(p[0] for p in poly) // 32
                max_x = max(p[0] for p in poly) // 32
                min_y = min(p[1] for p in poly) // 32
                max_y = max(p[1] for p in poly) // 32
                for x in range(int(min_x), int(max_x)+1):
                    for y in range(int(min_y), int(max_y)+1):
                        obstacles.add((x, y))
        
        # Ajouter les obstacles réels (parties terrestres) des îles quantiques DÉCOUVERTES
        if hasattr(self.game, 'quantique_area') and self.game.quantique_area:
            if hasattr(self.game, 'quantum_islands') and self.game.quantum_islands:
                from Class.Perlin import Perlin
                for island in self.game.quantum_islands:
                    if hasattr(island, 'matrix') and island.matrix and hasattr(island, 'rect'):
                        # Parcourir la zone de l'île découverte
                        island_x_start = island.rect.x // 32
                        island_y_start = island.rect.y // 32
                        island_width = island.rect.width // 32
                        island_height = island.rect.height // 32
                        
                        for gx in range(island_x_start, island_x_start + island_width + 1):
                            for gy in range(island_y_start, island_y_start + island_height + 1):
                                # Convertir en coordonnées monde
                                world_x = gx * 32 + 16
                                world_y = gy * 32 + 16
                                
                                # Vérifier le type de zone via la matrice de Perlin
                                try:
                                    zone_type = Perlin.get_zone_type(world_x, world_y, island.matrix, island)
                                    # Si c'est une zone d'île (valeur 2), ajouter comme obstacle
                                    if zone_type == 2:
                                        obstacles.add((gx, gy))
                                except:
                                    # En cas d'erreur, ignorer cette tuile
                                    pass

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
                    f_score[neighbor] = tentative_g_score + \
                        self.heuristic(neighbor, goal_grid)
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
        else:
            self.new_path = None
            self.path_found = False

        self.is_computing_path = False

    def compute_path_to_goal(self):
        """Calcule le chemin A* vers `self.path_goal` en arrière-plan (thread)."""
        goal = self.path_goal
        start = self.position
        if not start or not goal:
            self.is_computing_path = False
            return

        path = self.a_star_search(start, goal)
        if path:
            self.new_path = path
            self.path_found = True
        else:
            self.new_path = None
            self.path_found = False

        self.is_computing_path = False

    def update_path_from_thread(self):
        """Met à jour le chemin depuis le résultat du thread."""
        if self.path_found and self.new_path:
            self.current_path = self.new_path
            self.path_index = 0
            self.need_recalculate_path = False
            self.path_found = False
            self.new_path = None
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
            self.image = pygame.transform.rotate(
                self.image_original, self.angle)
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

        for unit in all_units:
            # Vérifier si c'est une plateforme de la même équipe
            if hasattr(unit, 'team') and unit.team == self.team:
                # Vérifier plusieurs possibilités pour identifier une plateforme pétrolière
                is_platform = False

                if hasattr(unit, 'is_platform') and unit.is_platform:
                    is_platform = True
                if hasattr(unit, 'unit_type'):
                    # Vérifier si c'est une plateforme par le type
                    if unit.unit_type in ["plateforme", "platform", "plateforme_petroliere", "PlateformePetroliere"]:
                        is_platform = True

                # Vérifier par le nom de classe
                class_name = unit.__class__.__name__.lower()
                if 'plateforme' in class_name or 'platform' in class_name:
                    is_platform = True

                if is_platform:
                    return unit.position

        return None

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

            # Si on est proche de la plateforme (moins de 80 pixels), on arrête SANS faire de virage
            if distance_to_platform < 80:
                self.stop()
                self.is_moving = False
                self.target_position = None
                self.current_path = []
                self.path_index = 0

                # NE PAS faire tourner le bateau - le garder dans sa direction actuelle
                # Le sous-marin garde son cap au lieu de faire un virage à 180°


                # Passer en mode patrol
                self.ia_mode = "patrol"
                # Réinitialiser pour chercher une nouvelle plateforme la prochaine fois
                self.platform_position = None
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
                    # Démarrer la computation en arrière-plan via l'utilitaire Unit
                    # (start_pathfinding_thread stocke le Thread dans self.path_thread)
                    try:
                        # Utiliser la méthode fournie par Unit
                        self.start_pathfinding_thread(self.compute_path)
                    except Exception:
                        # En cas de problème avec le threading, retomber sur le calcul synchrone
                        path = self.a_star_search(
                            self.position, self.platform_position)
                        if path:
                            self.current_path = path
                            self.path_index = 0
                            self.need_recalculate_path = False
                        else:
                            if self.is_path_clear(self.platform_position[0], self.platform_position[1]):
                                self.move_to_position(self.platform_position)
                            else:
                                self.find_alternative_path_to_target(
                                    self.platform_position[0], self.platform_position[1])
                        return

                # Si le thread est terminé mais n'a pas trouvé de chemin, retomber sur la méthode directe
                if getattr(self, 'path_thread', None) and not self.path_thread.is_alive() and not self.path_found and not self.current_path:
                    if self.is_path_clear(self.platform_position[0], self.platform_position[1]):
                        self.move_to_position(self.platform_position)
                    else:
                        self.find_alternative_path_to_target(
                            self.platform_position[0], self.platform_position[1])
                    # Réinitialiser la demande de recalcul
                    self.need_recalculate_path = False
                    return

            # Suivre le chemin A*
            if not self.follow_path():
                # Le chemin est terminé mais on n'est pas encore arrivé, recalculer
                self.need_recalculate_path = True
        else:
            # Si on ne trouve pas de plateforme, retour en mode patrol
            self.ia_mode = "patrol"
            self.current_path = []
            self.path_index = 0
            self.patrol_movement()

    def count_mines_around_platform(self, all_units):
        """Compte le nombre de mines autour de la plateforme pétrolière de l'équipe.
        
        Args:
            all_units (list[Unit]): Liste de toutes les unités du jeu
            
        Returns:
            int: Nombre de mines autour de la plateforme
        """
        # Trouver la plateforme si on ne l'a pas encore
        if self.platform_position is None:
            self.platform_position = self.find_base_position(all_units)
        
        if not self.platform_position:
            return 0
            
        mine_count = 0
        platform_x, platform_y = self.platform_position
        
        # Vérifier s'il y a un système de combat avec des mines
        if hasattr(self.game, 'combat_system') and self.game.combat_system:
            if hasattr(self.game.combat_system, 'mines'):
                for mine in self.game.combat_system.mines:
                    # Vérifier si la mine appartient à notre équipe
                    if hasattr(mine, 'team') and mine.team == self.team:
                        # Calculer la distance entre la mine et la plateforme
                        dx = mine.position[0] - platform_x
                        dy = mine.position[1] - platform_y
                        distance = math.sqrt(dx**2 + dy**2)
                        
                        # Si la mine est dans le rayon de comptage, la compter
                        if distance <= self.defense_count_radius:
                            mine_count += 1
        
        return mine_count

    def ia_mouvement(self, all_units):
        """IA du sous-marin avec trois modes distincts : patrol, attack, return_to_platform.

        Flux:
        1. PATROL → Patrouille normale jusqu'à détecter un éclaireur
        2. ATTACK → Poursuite et pose de mine
        3. RETURN_TO_PLATFORM → Retour à la plateforme pétrolière
        4. Retour en PATROL
        """

        # MODE 0: DEFENSE_BASE - patrouille minière autour de la plateforme (activé au spawn)
        if self.ia_mode == "defense_base":
            self.ia_behavior_defense_base(all_units)
            return

        # MODE 1: PATROL - Patrouille normale
        if self.ia_mode == "patrol":
            self.ia_behavior_patrol(all_units)

        # MODE 2: ATTACK - Attaque d'un éclaireur
        elif self.ia_mode == "attack":
            self.ia_behavior_attack(all_units)

        # MODE 2b: GROUP_ATTACK - Attaque coordonnée
        elif self.ia_mode == "group_attack":
            self.ia_behavior_group_attack(all_units)

        # MODE 3: RETURN_TO_PLATFORM - Retour à la plateforme
        elif self.ia_mode == "return_to_platform":
            self.ia_behavior_return_to_platform(all_units)

    def ia_behavior_patrol(self, all_units):
        """Comportement de patrouille normale.

        Cherche des chaloupes ennemies à 500px ou moins → passe en mode return_to_platform.
        Cherche des bateaux ennemis à 450px ou moins → passe en mode return_to_platform.
        Cherche des paquebots ennemis à 300px ou moins → passe en mode return_to_platform.
        Cherche des éclaireurs ennemis à 320px → passe en mode attack.
        Détecte la plateforme alliée à 100px → fait un virage à 180°.
        Sinon, patrouille en ligne droite.
        """
        # PRIORITÉ 1: Vérifier si moins de 15 mines autour de la plateforme
        mine_count = self.count_mines_around_platform(all_units)
        if mine_count < 15:
            self.ia_mode = "defense_base"
            return
        
        # PRIORITÉ 2: Chercher des chaloupes ennemies à proximité (500 pixels)
        nearby_chaloupes = self.find_nearby_chaloupes(
            all_units, detection_range=500)

        if nearby_chaloupes:
            # Chaloupe détectée → tenter formation de groupe avant de fuir
            allies = self.get_nearby_allied_submarines(all_units, radius=600)
            if len(allies) >= 2:
                formed = self.form_attack_group(
                    all_units, detected_target=nearby_chaloupes[0], radius=600, min_members=3)
                if formed:
                    self.ia_mode = 'group_attack'
                    return
            # Sinon, comportement original: fuir vers la plateforme
            self.ia_mode = "return_to_platform"
            return

        # PRIORITÉ 2: Chercher des bateaux ennemis à proximité (450 pixels)
        nearby_bateaux = self.find_nearby_bateaux(
            all_units, detection_range=450)

        if nearby_bateaux:
            # Bateau détecté → tenter formation de groupe avant de fuir
            allies = self.get_nearby_allied_submarines(all_units, radius=600)
            if len(allies) >= 2:
                formed = self.form_attack_group(
                    all_units, detected_target=nearby_bateaux[0], radius=600, min_members=3)
                if formed:
                    self.ia_mode = 'group_attack'
                    return
            self.ia_mode = "return_to_platform"
            return

        # PRIORITÉ 3: Chercher des paquebots ennemis à proximité (300 pixels)
        nearby_paquebots = self.find_nearby_paquebots(
            all_units, detection_range=300)

        if nearby_paquebots:
            # Paquebot détecté → tenter formation de groupe avant de fuir
            allies = self.get_nearby_allied_submarines(all_units, radius=600)
            if len(allies) >= 2:
                formed = self.form_attack_group(
                    all_units, detected_target=nearby_paquebots[0], radius=600, min_members=3)
                if formed:
                    self.ia_mode = 'group_attack'
                    return
            self.ia_mode = "return_to_platform"
            return

        # PRIORITÉ 4: Chercher des éclaireurs ennemis à proximité (10 cases = 320 pixels)
        nearby_scouts = self.find_nearby_scouts(all_units, detection_range=320)

        if nearby_scouts:
            # Éclaireur détecté → tenter de former un groupe d'attaque
            target = self.get_closest_scout(nearby_scouts)
            formed = self.form_attack_group(
                all_units, detected_target=target, radius=600, min_members=2)
            if formed:
                self.ia_mode = 'group_attack'
            else:
                self.ia_mode = "attack"
            return

        # Pas de menace → patrouille normale
        self.patrol_movement()

    def generate_defense_mine_positions(self, all_units):
        """Génère une liste d'emplacements valides pour poser des mines dans un carré autour de la plateforme.

        Utilise `is_position_valid` pour filtrer et tente de contourner les obstacles en cherchant
        une position proche si un point de la grille est invalide.
        """
        # Trouver la plateforme si nécessaire
        if self.platform_position is None:
            self.platform_position = self.find_base_position(all_units)

        if not self.platform_position:
            # Pas de plateforme trouvée : ne rien générer
            return

        cx, cy = self.platform_position
        half = self.defense_square_radius
        spacing = max(32, int(self.defense_grid_spacing))

        positions = []
        # Définir les bornes du carré centré sur la plateforme
        x_start = int(cx - half)
        x_end = int(cx + half)
        y_start = int(cy - half)
        y_end = int(cy + half)

        # Générer des points le long des 4 côtés (périmètre) avec un espacement donné
        # Top et bottom edges
        x = x_start
        while x <= x_end and len(positions) < self.defense_max_mines:
            for y in (y_start, y_end):
                if len(positions) >= self.defense_max_mines:
                    break
                if self.is_position_valid(x, y, treat_platform_as_obstacle=True):
                    positions.append((x, y))
                else:
                    # tenter de trouver une position proche le long de la normale extérieure
                    found = False
                    for r in (20, 40, 60, 80):
                        for angle in range(0, 360, 30):
                            rx = x + int(math.cos(math.radians(angle)) * r)
                            ry = y + int(math.sin(math.radians(angle)) * r)
                            if self.is_position_valid(rx, ry, treat_platform_as_obstacle=True):
                                positions.append((rx, ry))
                                found = True
                                break
                        if found:
                            break
            x += spacing

        # Left and right edges (avoid duplicating corners)
        y = y_start + spacing
        while y <= y_end - spacing and len(positions) < self.defense_max_mines:
            for x in (x_start, x_end):
                if len(positions) >= self.defense_max_mines:
                    break
                if self.is_position_valid(x, y, treat_platform_as_obstacle=True):
                    if (x, y) not in positions:
                        positions.append((x, y))
                else:
                    found = False
                    for r in (20, 40, 60, 80):
                        for angle in range(0, 360, 30):
                            rx = x + int(math.cos(math.radians(angle)) * r)
                            ry = y + int(math.sin(math.radians(angle)) * r)
                            if self.is_position_valid(rx, ry, treat_platform_as_obstacle=True):
                                if (rx, ry) not in positions:
                                    positions.append((rx, ry))
                                found = True
                                break
                        if found:
                            break
            y += spacing

        # Si insuffisant, tenter d'ajouter points intermédiaires le long du périmètre avec pas réduit
        if len(positions) < self.defense_max_mines:
            small_step = max(16, spacing // 2)
            # parcours top/bottom
            x = x_start
            while x <= x_end and len(positions) < self.defense_max_mines:
                for y in (y_start, y_end):
                    if len(positions) >= self.defense_max_mines:
                        break
                    if (x, y) not in positions and self.is_position_valid(x, y, treat_platform_as_obstacle=True):
                        positions.append((x, y))
                x += small_step
            # parcours left/right
            y = y_start + small_step
            while y <= y_end - small_step and len(positions) < self.defense_max_mines:
                for x in (x_start, x_end):
                    if len(positions) >= self.defense_max_mines:
                        break
                    if (x, y) not in positions and self.is_position_valid(x, y, treat_platform_as_obstacle=True):
                        positions.append((x, y))
                y += small_step

        # Enfin tailler la liste à la taille demandée
        self.defense_mine_positions = positions[:self.defense_max_mines]
        self.defense_current_mine_index = 0
        self.defense_positions_generated = True

    def ia_behavior_group_attack(self, all_units):
        """Comportement pour les sous-marins en mode 'group_attack'.

        - Le leader calcule la route vers la cible (A* ou direct) et la suit.
        - Les suiveurs gardent une position en formation relative au leader.
        - Quand le leader est à portée suffisante, il broadcast le signal d'attaque.
        """
        # PRIORITÉ 1: Vérifier si moins de 15 mines autour de la plateforme
        mine_count = self.count_mines_around_platform(all_units)
        if mine_count < 15:
            self.ia_mode = "defense_base"
            return
        
        # Récupérer les membres du groupe
        if not self.group_id:
            # Pas de groupe, revenir en patrol
            self.ia_mode = 'patrol'
            return

        members = [u for u in all_units if getattr(
            u, 'group_id', None) == self.group_id and u.is_alive]
        if not members:
            self.group_id = None
            self.ia_mode = 'patrol'
            return

        # Trouver le leader
        leader = None
        for m in members:
            if getattr(m, 'is_leader', False):
                leader = m
                break

        if leader is None:
            # Si aucun leader, élire le premier membre comme leader
            leader = members[0]
            leader.is_leader = True

        # Vérifier si la cible est toujours valide
        target = self.group_target_unit
        if not target or not target.is_alive:
            # cible perdue -> fin du groupe
            for m in members:
                m.group_id = None
                m.is_leader = False
                m.ia_mode = 'patrol'
            return

        # Calculer la distance à la cible pour tous les membres
        dx_target = target.position[0] - self.position[0]
        dy_target = target.position[1] - self.position[1]
        dist_to_target = math.hypot(dx_target, dy_target)

        
        collision_distance = 35
        if dist_to_target <= collision_distance:
            self.stop()
            self.is_moving = False
            self.target_position = None
            if self.can_place_mine():
                placed = self.place_mine(
                    int(self.position[0]), int(self.position[1]))
            return

        # Si je suis leader, je vais gérer la route/attaque
        if self.is_leader:
            # Leader: suivre la cible comme en attaque (A* si nécessaire)
            # Si le leader est proche de la cible, envoyer le signal d'attaque
            attack_range = 180 if getattr(
                target, 'unit_type', None) == 'paquebot' else 120
            if dist_to_target <= attack_range:
                # le signal d'attaque
                self.broadcast_attack_signal(all_units)

            # Se déplacer vers la cible en utilisant A* (thread si possible)
            goal = (target.position[0], target.position[1])
            if self.path_goal != goal:
                self.path_goal = goal
                try:
                    if not getattr(self, 'path_thread', None) or not self.path_thread.is_alive():
                        self.start_pathfinding_thread(self.compute_path_to_goal)
                except Exception:
                    path = self.a_star_search(self.position, goal)
                    if path:
                        self.current_path = path
                        self.path_index = 0
                        self.need_recalculate_path = False

            if self.update_path_from_thread() or self.current_path:
                if self.follow_path():
                    return

            # fallback direct
            if self.is_path_clear(target.position[0], target.position[1]):
                self.move_to_position(target.position)
            else:
                self.find_alternative_path_to_target(
                    target.position[0], target.position[1])

        else:
            # Si je suis suiveur, je dois suivre une position relative au leader
            if leader is None:
                return

            # Vérifier d'abord si je suis proche de la cible pour attaquer
            # (distance déjà calculée plus haut : dist_to_target)
            attack_distance = 140 if getattr(
                target, 'unit_type', None) == 'paquebot' else 80
            if dist_to_target <= attack_distance:
                # Je suis assez proche, me diriger vers la cible pour attaquer
                if not self.is_moving or self.target_position != target.position:
                    if self.is_path_clear(target.position[0], target.position[1]):
                        self.move_to_position(target.position)
                    else:
                        self.find_alternative_path_to_target(
                            target.position[0], target.position[1])
                return

            # Sinon, maintenir la formation autour du leader
            # Définir un angle de formation en V selon mon slot
            slot = getattr(self, 'formation_slot', 0) or 0
            # base_angle est l'angle du leader (cap)
            base_angle = leader.angle
            # décaler l'angle pour former un V centré
            offset_angle = base_angle + (slot * 20 - 40)
            fx = leader.position[0] - \
                math.cos(math.radians(offset_angle)) * self.formation_distance
            fy = leader.position[1] - \
                math.sin(math.radians(offset_angle)) * self.formation_distance

            # Se déplacer vers la position de formation
            if not self.is_moving:
                # tourner vers la position de formation
                dx = fx - self.position[0]
                dy = fy - self.position[1]
                angle_to = math.degrees(math.atan2(-dy, dx)) - 90
                self.angle = angle_to % 360
                self.image = pygame.transform.rotate(
                    self.image_original, self.angle)
                self.rect = self.image.get_rect(center=self.rect.center)

                if self.is_path_clear(fx, fy):
                    self.move_to_position((fx, fy))
                else:
                    # essayer un point proche
                    self.find_alternative_path_to_target(fx, fy)

    def ia_behavior_defense_base(self, all_units):
        """Patrouille minière autour de la plateforme : pose jusqu'à `defense_max_mines` mines.

        Comportement :
        - Si menace lourde (chaloupe/bateau/paquebot) détectée, basculer en `return_to_platform` (sécurité).
        - Générer positions de mines (une fois).
        - Se déplacer vers la position suivante et poser une mine si possible (respect cooldown).
        - Si toutes les mines posées, repasser en `patrol`.
        """
        # Priorités de sécurité (identiques à patrol)
        nearby_chaloupes = self.find_nearby_chaloupes(
            all_units, detection_range=500)
        if nearby_chaloupes:
            # Chaloupe détectée en défense -> tenter formation de groupe
            allies = self.get_nearby_allied_submarines(all_units, radius=600)
            if len(allies) >= 2:
                formed = self.form_attack_group(
                    all_units, detected_target=nearby_chaloupes[0], radius=600, min_members=3)
                if formed:
                    self.ia_mode = 'group_attack'
                    return
            self.ia_mode = "return_to_platform"
            return

        nearby_bateaux = self.find_nearby_bateaux(
            all_units, detection_range=450)
        if nearby_bateaux:
            allies = self.get_nearby_allied_submarines(all_units, radius=600)
            if len(allies) >= 2:
                formed = self.form_attack_group(
                    all_units, detected_target=nearby_bateaux[0], radius=600, min_members=3)
                if formed:
                    self.ia_mode = 'group_attack'
                    return
            self.ia_mode = "return_to_platform"
            return

        nearby_paquebots = self.find_nearby_paquebots(
            all_units, detection_range=300)
        if nearby_paquebots:
            allies = self.get_nearby_allied_submarines(all_units, radius=600)
            if len(allies) >= 2:
                formed = self.form_attack_group(
                    all_units, detected_target=nearby_paquebots[0], radius=600, min_members=3)
                if formed:
                    self.ia_mode = 'group_attack'
                    return
            self.ia_mode = "return_to_platform"
            return

        # Trouver la plateforme et générer positions si nécessaire
        if not self.defense_positions_generated:
            self.generate_defense_mine_positions(all_units)

        # Si aucune position générée -> fallback en patrol
        if not self.defense_mine_positions:
            self.ia_mode = "patrol"
            return

        # Vérifier le nombre réel de mines autour de la plateforme
        current_mine_count = self.count_mines_around_platform(all_units)
        if current_mine_count >= self.defense_max_mines:
            # On a assez de mines défensives, passer en patrol
            self.ia_mode = "patrol"
            return

        # Aller poser la mine suivante
        idx = self.defense_current_mine_index
        if idx >= len(self.defense_mine_positions):
            # toutes les positions assignées mais pas forcément posées (peut arriver si invalidées)
            # réessayer de régénérer
            self.defense_positions_generated = False
            self.generate_defense_mine_positions(all_units)
            idx = self.defense_current_mine_index

        target_pos = self.defense_mine_positions[idx]

        # Si on est proche, poser la mine
        dx = target_pos[0] - self.position[0]
        dy = target_pos[1] - self.position[1]
        dist = math.hypot(dx, dy)

        if dist <= 20:
            # Arrêter et poser la mine si possible
            self.stop()
            self.is_moving = False
            self.target_position = None
            if self.can_place_mine():
                placed = self.place_mine(
                    int(self.position[0]), int(self.position[1]))
                    # Avancer à la position suivante
                self.defense_current_mine_index += 1
            else:
                # attendre cooldown
                pass
            return

        # Sinon, se déplacer vers la cible
        if not self.is_moving:
            # tourner et tenter le déplacement direct ou alternatif
            angle_to_target = math.degrees(math.atan2(-dy, dx)) - 90
            self.angle = angle_to_target % 360
            self.image = pygame.transform.rotate(
                self.image_original, self.angle)
            self.rect = self.image.get_rect(center=self.rect.center)

            if self.is_path_clear(target_pos[0], target_pos[1], treat_platform_as_obstacle=True):
                self.move_to_position(target_pos)
            else:
                # tenter un chemin alternatif qui évite explicitement la plateforme
                self.find_alternative_path_to_target(
                    target_pos[0], target_pos[1], avoid_platform=True)

    def ia_behavior_attack(self, all_units):
        """Comportement d'attaque d'un éclaireur.

        PRIORITÉ: Si chaloupe détectée à 500px → passe en mode return_to_platform.
        PRIORITÉ: Si bateau détecté à 400px → passe en mode return_to_platform.
        PRIORITÉ: Si paquebot détecté à 300px → passe en mode return_to_platform.
        Poursuit l'éclaireur et pose une mine à proximité.
        Si plus d'éclaireur → passe en mode return_to_platform.
        """
        # PRIORITÉ 1: Vérifier si moins de 15 mines autour de la plateforme
        mine_count = self.count_mines_around_platform(all_units)
        if mine_count < 15:
            self.ia_mode = "defense_base"
            return
        
        # PRIORITÉ 2: Vérifier la présence de chaloupes à proximité (500 pixels)
        nearby_chaloupes = self.find_nearby_chaloupes(
            all_units, detection_range=500)

        if nearby_chaloupes:
            # Chaloupe détectée → tenter formation de groupe avant de fuir
            allies = self.get_nearby_allied_submarines(all_units, radius=600)
            if len(allies) >= 2:
                formed = self.form_attack_group(
                    all_units, detected_target=nearby_chaloupes[0], radius=600, min_members=3)
                if formed:
                    self.ia_mode = 'group_attack'
                    return
            self.ia_mode = "return_to_platform"
            return

        # PRIORITÉ 2: Vérifier la présence de bateaux à proximité (450 pixels)
        nearby_bateaux = self.find_nearby_bateaux(
            all_units, detection_range=400)

        if nearby_bateaux:
            allies = self.get_nearby_allied_submarines(all_units, radius=600)
            if len(allies) >= 2:
                formed = self.form_attack_group(
                    all_units, detected_target=nearby_bateaux[0], radius=600, min_members=3)
                if formed:
                    self.ia_mode = 'group_attack'
                    return
            self.ia_mode = "return_to_platform"
            return

        # PRIORITÉ 3: Vérifier la présence de paquebots à proximité (300 pixels)
        nearby_paquebots = self.find_nearby_paquebots(
            all_units, detection_range=300)

        if nearby_paquebots:
            allies = self.get_nearby_allied_submarines(all_units, radius=600)
            if len(allies) >= 2:
                formed = self.form_attack_group(
                    all_units, detected_target=nearby_paquebots[0], radius=600, min_members=3)
                if formed:
                    self.ia_mode = 'group_attack'
                    return
            self.ia_mode = "return_to_platform"
            return

        # PRIORITÉ 4: Chercher des éclaireurs ennemis à proximité
        nearby_scouts = self.find_nearby_scouts(all_units, detection_range=320)

        if not nearby_scouts:
            # Plus d'éclaireur → passer en mode retour à la plateforme
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


            # Si on est en collision ou très proche, poser une mine
            if distance_to_scout <= collision_distance:

                # Arrêter le mouvement
                self.stop()
                self.is_moving = False
                self.target_position = None

                # Poser une mine si le cooldown est passé
                if self.can_place_mine():
                    mine_placed = self.place_mine(
                        int(self.position[0]), int(self.position[1]))
                else:
                    # attendre cooldown
                    pass
                return

            # Si l'éclaireur est plus loin, ajuster la trajectoire si nécessaire
            if self.is_moving and self.target_position:
                # Vérifier si on se dirige déjà vers l'éclaireur (tolérance de 30 degrés)
                current_target_dx = self.target_position[0] - self.position[0]
                current_target_dy = self.target_position[1] - self.position[1]
                current_angle = math.degrees(
                    math.atan2(-current_target_dy, current_target_dx)) - 90
                scout_angle = math.degrees(math.atan2(-dy, dx)) - 90
                angle_diff = abs(
                    (scout_angle - current_angle + 180) % 360 - 180)

                # Si on ne se dirige pas vers l'éclaireur, changer de direction
                if angle_diff > 30:
                    self.stop()
                    self.is_moving = False
                    self.target_position = None

            # Se déplacer vers l'éclaireur
            if not self.is_moving:
                # Calculer l'angle vers l'éclaireur
                angle_to_scout = math.degrees(math.atan2(-dy, dx)) - 90
                self.angle = angle_to_scout % 360
                self.image = pygame.transform.rotate(
                    self.image_original, self.angle)
                self.rect = self.image.get_rect(center=self.rect.center)

                # Se déplacer vers l'éclaireur si le chemin est dégagé
                # Utiliser A* pour atteindre l'éclaireur (thread si possible)
                goal = (target_scout.position[0], target_scout.position[1])
                if self.path_goal != goal:
                    self.path_goal = goal
                    try:
                        if not getattr(self, 'path_thread', None) or not self.path_thread.is_alive():
                            self.start_pathfinding_thread(self.compute_path_to_goal)
                    except Exception:
                        path = self.a_star_search(self.position, goal)
                        if path:
                            self.current_path = path
                            self.path_index = 0
                            self.need_recalculate_path = False

                if self.update_path_from_thread() or self.current_path:
                    if self.follow_path():
                        return

                # fallback
                if self.is_path_clear(target_scout.position[0], target_scout.position[1]):
                    self.move_to_position(target_scout.position)
                else:
                    self.find_alternative_path_to_target(
                        target_scout.position[0], target_scout.position[1])

    def ia_behavior_return_to_platform(self, all_units):
        """Comportement de retour à la plateforme pétrolière.

        Retourne à une plateforme pétrolière alliée.
        Arrivé à destination → tourne de 180° et repasse en mode patrol.
        """
        # PRIORITÉ 1: Vérifier si moins de 15 mines autour de la plateforme
        mine_count = self.count_mines_around_platform(all_units)
        if mine_count < 15:
            self.ia_mode = "defense_base"
            return
        
        # PRIORITÉ 2: Vérifier la présence de chaloupes, bateaux et paquebots (ne pas interrompre le retour)
        nearby_chaloupes = self.find_nearby_chaloupes(
            all_units, detection_range=500)
        nearby_bateaux = self.find_nearby_bateaux(
            all_units, detection_range=450)
        nearby_paquebots = self.find_nearby_paquebots(
            all_units, detection_range=300)

        if nearby_chaloupes or nearby_bateaux or nearby_paquebots:
            # Une menace est toujours présente, continuer le retour
            menace_type = "Chaloupe" if nearby_chaloupes else (
                "Bateau" if nearby_bateaux else "Paquebot")


        # PRIORITÉ 2: Si un éclaireur est détecté ET qu'il n'y a ni chaloupe, ni bateau, ni paquebot, annuler le retour
        if not nearby_chaloupes and not nearby_bateaux and not nearby_paquebots:
            nearby_scouts = self.find_nearby_scouts(
                all_units, detection_range=320)
            if nearby_scouts:
                # Il y a seulement des éclaireurs -> annuler le retour et attaquer
                self.ia_mode = "attack"
                self.platform_position = None  # Réinitialiser la position de la plateforme
                return
            else:
                # Plus aucune menace lourde ni éclaireur -> revenir en PATROL immédiatement
                self.ia_mode = "patrol"
                self.platform_position = None
                # Réinitialiser le chemin si un calcul était en cours
                self.current_path = []
                self.path_index = 0
                self.need_recalculate_path = False
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
        # +90 car l'angle 0 pointe vers le haut
        angle_rad = math.radians(self.angle + 90)

        # Calculer la position cible en avançant tout droit
        target_x = self.position[0] + math.cos(angle_rad) * distance_check
        target_y = self.position[1] - math.sin(angle_rad) * distance_check

        # Vérifier si le chemin vers la position cible est dégagé (pas seulement le point final)
        if self.is_path_clear(target_x, target_y, treat_platform_as_obstacle=True):
            # Si le chemin est dégagé, se déplacer vers cette position
            self.move_to_position((target_x, target_y))
        else:
            # Si le chemin n'est pas dégagé, chercher une direction alternative
            self.find_alternative_direction(
                distance_check, avoid_platform=True)

    def find_alternative_direction(self, distance_check, avoid_platform: bool = False):
        """Cherche une direction alternative quand le chemin est bloqué.

        Args:
            distance_check (int): Distance à vérifier pour chaque direction
        """
        direction_found = False

        # Liste d'angles à tester (de plus en plus grand)
        angles_to_test = [20, -20, 40, -40, 60, -60, 80, -80,
                          100, -100, 120, -120, 140, -140, 160, -160, 180]

        # D'abord essayer avec la distance normale
        for angle_offset in angles_to_test:
            test_angle = math.radians(self.angle + 90 + angle_offset)
            test_x = self.position[0] + math.cos(test_angle) * distance_check
            test_y = self.position[1] - math.sin(test_angle) * distance_check

            # Vérifier tout le chemin, pas seulement la destination
            if self.is_path_clear(test_x, test_y, treat_platform_as_obstacle=avoid_platform):
                # Mettre à jour l'angle du sous-marin
                self.angle = (self.angle + angle_offset) % 360
                self.image = pygame.transform.rotate(
                    self.image_original, self.angle)
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
                test_x = self.position[0] + \
                    math.cos(test_angle) * shorter_distance
                test_y = self.position[1] - \
                    math.sin(test_angle) * shorter_distance

                # Vérifier tout le chemin, pas seulement la destination
                if self.is_path_clear(test_x, test_y, treat_platform_as_obstacle=avoid_platform):
                    # Mettre à jour l'angle du sous-marin
                    self.angle = (self.angle + angle_offset) % 360
                    self.image = pygame.transform.rotate(
                        self.image_original, self.angle)
                    self.rect = self.image.get_rect(center=self.rect.center)
                    # Se déplacer vers cette nouvelle position
                    self.move_to_position((test_x, test_y))
                    direction_found = True
                    break

    def find_alternative_path_to_target(self, target_x, target_y, avoid_platform: bool = False):
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

            test_x = self.position[0] + \
                math.cos(test_angle_rad) * distance_check
            test_y = self.position[1] - \
                math.sin(test_angle_rad) * distance_check

            if self.is_path_clear(test_x, test_y, treat_platform_as_obstacle=avoid_platform):
                self.angle = test_angle_deg
                self.image = pygame.transform.rotate(
                    self.image_original, self.angle)
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
