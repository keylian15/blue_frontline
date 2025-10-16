import pygame
from Class.units.Unit import Unit
from Class.Combat import CombatSystem
from Global import UNIT_CONFIGS
from Utils import point_in_many_polygons


class Bateau(Unit):
    """Classe unifiée pour les unités Bateau (Rouge et Vert)."""
    
    def __init__(self, game: "Game", team: str, ia: bool = True):
        """Fonction d'initialisation de la classe Bateau.

        Args:
            game (Game): L'instance du jeu.
            team (str): L'équipe de l'unité.
            ia (bool): Si True, l'unité est contrôlée par l'IA.
        """
        
        # Récupérer la configuration depuis Global.py
        config = UNIT_CONFIGS["bateau"]
        
        # Initialiser avec l'image appropriée et le type d'unité
        super().__init__(game, team=team, unit_type="bateau")
        
        # === Spécifications du Bateau depuis Global.py ===
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
        self.unit_name = f"Bateau {team.capitalize()}"
        
        # Couleur de portée selon l'équipe
        self.range_color = config["range_color"][team]
        
        # État de mouvement
        self.is_moving = False
        self.target_position = None
        
        # === Configuration IA ===
        self.ia = ia
        self.current_goal = None
        self.path = []
        self._pi = 0
        self.enemie_base = self.get_enemy_base()
        self.ally_base = self.get_ally_base()
        
        # État de contournement pour éviter les oscillations gauche/droite
        self._detour_side = None  # +1 ou -1, None = non défini
        self._last_goal_position = None
        
        # Détection de blocage
        self._last_position = tuple(self.position)
        self._stuck_timer = 0
        self._stuck_threshold = 60  # frames avant de considérer bloqué
        
        # État de l'IA (pour le diagramme)
        self.current_state = "chercher_but"  # États possibles: chercher_but, suivre_eclaireur, attaquer, avancer
        
        # Éclaireur allié
        self._ally_scout = None
        self._scout_check_cooldown = 0
        self._scout_check_interval = 30  # Vérifier toutes les 30 frames

    def update(self, dt: int = 0, combat_system: CombatSystem = None, screen: pygame.Surface = None, 
               camera_offset: tuple[float, float] = (0, 0), all_units: list[Unit] = None):
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
        
        # Dessiner la portée en permanence
        if screen:
            self.draw_range(screen, camera_offset)
        
        if self.ia and all_units:
            self.execute_ia_logic(combat_system, all_units)

    def execute_ia_logic(self, combat_system: CombatSystem, all_units: list[Unit]):
        """Exécute la logique de l'IA selon le diagramme."""
        
        # Étape 1: Chercher un ennemi proche (dans la portée étendue pour la détection)
        enemy = self.get_closest_enemy_in_range()
        
        if enemy:
            # Calculer la distance réelle à l'ennemi
            dx = enemy.position[0] - self.position[0]
            dy = enemy.position[1] - self.position[1]
            distance_to_enemy = (dx*dx + dy*dy) ** 0.5
            
            # Ennemi proche détecté
            health_percentage = self.current_health / self.max_health
            
            if health_percentage > 0.5:
                # PV > 50%
                if self.is_paquebot(enemy):
                    # C'est un paquebot -> Attaquer
                    self.current_state = "fuite"
                    self.flee_to_ally_base()
                else:
                    # Pas un paquebot -> Attaquer normalement
                    self.current_state = "attaquer"
                    self.attack_enemy(enemy, combat_system)
            else:
                # PV <= 50% -> Vérifier éclaireur allié
                ally_scout = self.find_ally_scout(all_units)
                
                if ally_scout:
                    # BUT = suivre éclaireur allié
                    self.current_state = "suivre_eclaireur"
                    self.follow_scout(ally_scout)
                else:
                    # BUT = base ennemie (fuir vers base alliée)
                    self.current_state = "fuite"
                    self.flee_to_ally_base()
        else:
            # Pas d'ennemi proche -> BUT = base ennemie (ou fuite si besoin)
            health_percentage = self.current_health / self.max_health
            
            if health_percentage <= 0.5:
                ally_scout = self.find_ally_scout(all_units)
                if ally_scout:
                    self.current_state = "suivre_eclaireur"
                    self.follow_scout(ally_scout)
                else:
                    self.current_state = "fuite"
                    self.flee_to_ally_base()
            else:
                self.current_state = "avancer"
                self.advance_to_enemy_base()
        
        # Étape 2: Avancer vers le but (avec gestion de blocage)
        if self.current_state in ["avancer", "fuite", "suivre_eclaireur"]:
            self.move_towards_goal()

    def attack_enemy(self, enemy: Unit, combat_system: CombatSystem):
        """Attaque un ennemi si à portée, sinon avance vers lui."""
        
        dx = enemy.position[0] - self.position[0]
        dy = enemy.position[1] - self.position[1]
        distance_to_enemy = (dx*dx + dy*dy) ** 0.5
        
        if distance_to_enemy <= self.range:
            # À portée de tir -> Tirer
            self.attack(enemy, combat_system)
        else:
            # Pas à portée -> Se rapprocher
            self.set_goal(tuple(enemy.position))
            self.move_towards_goal()

    def find_ally_scout(self, all_units: list[Unit]):
        """Trouve l'éclaireur allié le plus proche (si disponible)."""
        
        # Cooldown pour éviter de chercher trop souvent
        self._scout_check_cooldown -= 1
        if self._scout_check_cooldown > 0 and self._ally_scout:
            # Vérifier que l'éclaireur existe encore
            if self._ally_scout in all_units:
                return self._ally_scout
        
        self._scout_check_cooldown = self._scout_check_interval
        
        # Chercher un éclaireur allié
        closest_scout = None
        min_distance = float('inf')
        
        for unit in all_units:
            # Vérifier si c'est un éclaireur allié
            if (unit.team == self.team and 
                unit != self and 
                hasattr(unit, 'unit_type') and 
                unit.unit_type == "eclaireur"):
                
                dx = unit.position[0] - self.position[0]
                dy = unit.position[1] - self.position[1]
                distance = (dx*dx + dy*dy) ** 0.5
                
                if distance < min_distance:
                    min_distance = distance
                    closest_scout = unit
        
        self._ally_scout = closest_scout
        return closest_scout

    def follow_scout(self, scout: Unit):
        """Suit un éclaireur allié."""
        if scout and hasattr(scout, 'position'):
            self.set_goal(tuple(scout.position))

    def flee_to_ally_base(self):
        """Fuit vers la base alliée."""
        if self.ally_base:
            self.set_goal(tuple(self.ally_base.position))

    def advance_to_enemy_base(self):
        """Avance vers la base ennemie."""
        if self.enemie_base:
            self.set_goal(tuple(self.enemie_base.position))

    def is_paquebot(self, unit: Unit) -> bool:
        """Vérifie si une unité est un paquebot."""
        return getattr(unit, 'type', None) == "Paquebot" or getattr(unit, 'unit_type', None) == "paquebot"

    def set_goal(self, new_goal: tuple):
        """Définit un nouveau but seulement si nécessaire."""
        if new_goal != self._last_goal_position:
            self._detour_side = None
            self.current_goal = new_goal
            self._last_goal_position = new_goal
            self.path = self.create_path(self.position, self.current_goal)
            self._pi = 0

    def move_towards_goal(self):
        """Se déplace vers le but actuel avec détection de blocage."""
        
        if not self.current_goal:
            return

        # Détecter si le bateau est bloqué
        current_pos = tuple(self.position)
        distance_moved = ((current_pos[0] - self._last_position[0])**2 + 
                         (current_pos[1] - self._last_position[1])**2) ** 0.5
        
        if distance_moved < 0.5:  # Presque pas de mouvement
            self._stuck_timer += 1
        else:
            self._stuck_timer = 0
            
        self._last_position = current_pos
        
        # Si bloqué trop longtemps, forcer la recalculation
        if self._stuck_timer > self._stuck_threshold:
            self._detour_side = None
            self.path = self.create_path(self.position, self.current_goal)
            self._pi = 0
            self._stuck_timer = 0
            return

        # Vérifier la distance jusqu'au goal final
        goal_dx = self.current_goal[0] - self.position[0]
        goal_dy = self.current_goal[1] - self.position[1]
        goal_dist = (goal_dx*goal_dx + goal_dy*goal_dy) ** 0.5
        
        # Si on est proche du goal final
        if goal_dist < self.range:
            self.move_to_position(self.current_goal)
            return

        if self._pi >= len(self.path):
            # Se diriger directement vers le goal
            self.move_to_position(self.current_goal)
            return

        target = self.path[self._pi]
        dx = target[0] - self.position[0]
        dy = target[1] - self.position[1]
        dist = (dx*dx + dy*dy) ** 0.5

        if dist < 5:
            self._pi += 1
            if self._pi < len(self.path):
                target = self.path[self._pi]
                self.move_to_position(target)
            else:
                self.move_to_position(self.current_goal)
            return

        # Continuer vers le waypoint courant
        self.move_to_position(target)

    def get_enemy_base(self):
        """Renvoie la base ennemie."""
        for p in self.game.plateformes.values():
            if p.team != self.team:
                return p
        return None
    
    def get_ally_base(self):
        """Renvoie la base alliée."""
        for p in self.game.plateformes.values():
            if p.team == self.team:
                return p
        return None
    
    def create_path(self, depart, goal, depth: int = 0, max_depth: int = 3):
        """Crée un chemin avec contournement d'obstacles."""
        
        if not depart or not goal or depart == goal:
            return []

        x0, y0 = depart
        x1, y1 = goal
        dx = x1 - x0
        dy = y1 - y0
        dist = (dx*dx + dy*dy) ** 0.5
        if dist == 0:
            return []

        # Paramètres
        step = 16          
        back_margin = 32
        detour_distance = 64
        max_detour_distance = 512        
        dir_x = dx / dist
        dir_y = dy / dist
        perp_x = -dir_y
        perp_y = dir_x

        steps = max(1, int(dist // step))
        path = []
        hit_obstacle = None

        # Échantillonnage sur la ligne directe
        for i in range(1, steps + 1):
            t = i / steps
            px = x0 + dx * t
            py = y0 + dy * t
            if point_in_many_polygons(self.game.obstacles, (px, py)) or point_in_many_polygons(self.game.quantique_area_hidden, (px, py)):
                hit_obstacle = (px, py)
                break
            path.append((px, py))

        # Pas d'obstacle: chemin direct
        if not hit_obstacle:
            return path

        # Profondeur max atteinte
        if depth >= max_depth:
            return path

        # Point pivot avant l'obstacle
        pivot_x = hit_obstacle[0] - dir_x * back_margin
        pivot_y = hit_obstacle[1] - dir_y * back_margin

        # Déterminer l'ordre de préférence des côtés
        preferred_sides = (+1, -1) if self._detour_side is None else (self._detour_side, -self._detour_side)

        # Essayer le côté préféré en augmentant progressivement la distance
        for sign in preferred_sides:
            current_detour = detour_distance
            while current_detour <= max_detour_distance:
                detour_x = pivot_x + perp_x * current_detour * sign
                detour_y = pivot_y + perp_y * current_detour * sign

                # Le détour ne doit pas tomber dans un obstacle
                if point_in_many_polygons(self.game.obstacles, (detour_x, detour_y)) or point_in_many_polygons(self.game.quantique_area_hidden, (detour_x, detour_y)):
                    current_detour *= 1.5
                    continue

                # Vérifier que le segment depart -> détour est dégagé
                seg_dx = detour_x - depart[0]
                seg_dy = detour_y - depart[1]
                seg_dist = (seg_dx*seg_dx + seg_dy*seg_dy) ** 0.5
                seg_steps = max(1, int(seg_dist // step))
                blocked = False
                for j in range(1, seg_steps + 1):
                    tj = j / seg_steps
                    sx = depart[0] + seg_dx * tj
                    sy = depart[1] + seg_dy * tj
                    if point_in_many_polygons(self.game.obstacles, (sx, sy)) or point_in_many_polygons(self.game.quantique_area_hidden, (sx, sy)):
                        blocked = True
                        break
                if blocked:
                    current_detour *= 1.5
                    continue

                # Construire le chemin avec récursion
                self._detour_side = sign
                segment1 = self.create_path(depart, (detour_x, detour_y), depth + 1, max_depth)
                if not segment1:
                    current_detour *= 1.5
                    continue
                segment2 = self.create_path((detour_x, detour_y), goal, depth + 1, max_depth)
                if not segment2:
                    current_detour *= 1.5
                    continue

                return segment1 + segment2

        # Aucun détour viable
        self._detour_side = None
        return path


# Classes d'alias pour la compatibilité avec l'ancien code
class BateauRouge(Bateau):
    def __init__(self, game: "Game"):
        """Fonction d'initialisation de la classe BateauRouge.

        Args:
            game (Game): L'instance de la classe Game.
        """
        super().__init__(game, team="red")

class BateauVert(Bateau):
    def __init__(self, game: "Game"):
        """Fonction d'initialisation de la classe BateauVert.

        Args:
            game (Game): L'instance de la classe Game.
        """
        super().__init__(game, team="green")