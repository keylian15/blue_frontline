import time
import pygame
from Class.units.Unit import Unit
from Class.Combat import CombatSystem, Mine
from math import * 
from Global import UNIT_CONFIGS
from Utils import point_in_many_polygons, random_point_in_polygon

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
        
        # Variables pour l'IA en arc de cercle
        self.own_base_position = None
        self.circle_radius = 200  # Rayon du cercle autour de la base
        self.current_angle = 0  # Angle actuel sur le cercle
        self.angle_step = 30  # Pas d'angle en degrés entre chaque mine
        self.circle_center = None
        self.target_position_on_circle = None
        self.mines_placed = 0
        self.max_mines = 12  # Nombre maximum de mines à placer en cercle
        
            
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

        # Dessiner la portée en permanence
        if screen:
            self.draw_range(screen, camera_offset)

        self.ia_action(all_units)

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
            # -- AUDIO : drop mine --
            try:
                if hasattr(self.game, "sound") and self.game.sound:
                    self.game.sound.on_mine_dropped((x, y))
            except Exception:
                # ne jamais crasher pour du son
                pass
            return True
        return False
    
    def get_own_base_position(self):
        """Récupère la position de sa propre base."""
        if self.own_base_position is None:
            print(f"Sous-marin {self.team}: Recherche de sa propre base...")
            
            if self.team == "red":
                # Notre base = base rouge
                base_zone = getattr(self.game, 'red_platform_zone', None)
                print(f"Base zone rouge trouvée: {base_zone is not None}")
            else:
                # Notre base = base verte  
                base_zone = getattr(self.game, 'green_platform_zone', None)
                print(f"Base zone verte trouvée: {base_zone is not None}")
                
            if base_zone:
                # Prendre le centre approximatif de la zone de la base
                self.own_base_position = random_point_in_polygon(base_zone)
                print(f"Position de notre base: {self.own_base_position}")
            else:
                # Fallback: utiliser des positions fixes approximatives
                print(f"Zones de base non trouvées, utilisation de positions par défaut")
                # Rechercher les unités de notre base comme alternative
                own_units = [unit for unit in getattr(self.game, 'all_units', []) 
                              if hasattr(unit, 'team') and unit.team == self.team and 
                              hasattr(unit, 'unit_type') and 'base' in str(unit.unit_type).lower()]
                
                if own_units:
                    # Utiliser la position de la première unité de base trouvée
                    self.own_base_position = own_units[0].position
                    print(f"Notre base trouvée via unités: {self.own_base_position}")
                else:
                    # Dernière option: centre de la carte
                    map_center_x = getattr(self.game, 'map_width', 1600) // 2
                    map_center_y = getattr(self.game, 'map_height', 1200) // 2
                    if self.team == "red":
                        # Base rouge : côté gauche-bas  
                        self.own_base_position = (map_center_x - 300, map_center_y + 300)
                    else:
                        # Base verte : côté droit-haut
                        self.own_base_position = (map_center_x + 300, map_center_y - 300)
                    print(f"Position de fallback (centre carte): {self.own_base_position}")
        
        return self.own_base_position
    
    def get_circle_position(self, angle_degrees):
        """Calcule la position sur le cercle autour de notre base."""
        if not self.circle_center:
            return None
            
        angle_rad = radians(angle_degrees)
        x = self.circle_center[0] + self.circle_radius * cos(angle_rad)
        y = self.circle_center[1] + self.circle_radius * sin(angle_rad)
        return (x, y)
    
    def find_safe_circle_position(self, target_angle):
        """Trouve une position sûre sur le cercle, en évitant les obstacles."""
        # Essayer l'angle cible d'abord
        pos = self.get_circle_position(target_angle)
        if pos and self.is_position_valid(pos[0], pos[1]):
            return pos, target_angle
        
        # Si la position n'est pas valide, essayer des angles proches
        for offset in range(5, 46, 5):  # Essayer par pas de 5 degrés jusqu'à 45°
            for sign in [1, -1]:
                test_angle = target_angle + (offset * sign)
                pos = self.get_circle_position(test_angle)
                if pos and self.is_position_valid(pos[0], pos[1]):
                    return pos, test_angle
        
        return None, target_angle
    
    def move_to_circle_position(self):
        """Déplace le sous-marin vers la prochaine position sur le cercle."""
        if not self.circle_center:
            print(f"Sous-marin {self.team}: Pas de centre de cercle défini")
            return False
        
        # Calculer la position cible sur le cercle
        target_pos, actual_angle = self.find_safe_circle_position(self.current_angle)
        if not target_pos:
            # Si aucune position valide, passer au suivant
            print(f"Sous-marin {self.team}: Aucune position valide trouvée à l'angle {self.current_angle}°, passage au suivant")
            self.current_angle = (self.current_angle + self.angle_step) % 360
            return False
        
        self.target_position_on_circle = target_pos
        
        # Se déplacer vers cette position
        distance = sqrt((self.position[0] - target_pos[0])**2 + (self.position[1] - target_pos[1])**2)
        
        if distance < 30:  # Arrivé à la position
            # Placer une mine
            if self.can_place_mine() and self.mines_placed < self.max_mines:
                self.place_mine(int(self.position[0]), int(self.position[1]))
                self.mines_placed += 1
                print(f"Sous-marin {self.team}: Mine défensive {self.mines_placed} placée à l'angle {actual_angle}° (position {self.position})")
            
            # Passer à la position suivante sur le cercle
            self.current_angle = (self.current_angle + self.angle_step) % 360
            print(f"Sous-marin {self.team}: Passage à l'angle suivant: {self.current_angle}°")
            return True
        else:
            # Se déplacer vers la position cible
            if not hasattr(self, 'last_move_debug') or time.time() - self.last_move_debug > 5.0:
                print(f"Sous-marin {self.team}: Mouvement vers {target_pos}, distance: {distance:.1f}")
                self.last_move_debug = time.time()
            self.move_to(target_pos[0], target_pos[1])
            self.is_moving = True
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
        
        # Vérifier s'il y a une autre unité à cette position
        if self.game.find_unit_at_position(x, y, self):
            return False
            
        return True

    
    def ia_action(self, all_units):
        """IA du sous-marin pour créer un arc de cercle de mines autour de sa propre base."""
        # Obtenir la position de notre base
        own_base = self.get_own_base_position()
        if not own_base:
            print(f"Sous-marin {self.team}: Impossible de trouver sa propre base")
            return
        
        # Initialiser le centre du cercle si ce n'est pas fait
        if not self.circle_center:
            self.circle_center = own_base
            print(f"Sous-marin {self.team}: Initialisation du cercle défensif autour de sa base à {own_base}")
            print(f"Position actuelle du sous-marin: {self.position}")
        
        # Si toutes les mines ont été placées, rester en position
        if self.mines_placed >= self.max_mines:
            if not hasattr(self, 'completed_message_shown'):
                print(f"Sous-marin {self.team}: Toutes les mines défensives ont été placées ({self.mines_placed}/{self.max_mines})")
                self.completed_message_shown = True
            return
        
        # Se déplacer en arc de cercle autour de la base
        moved = self.move_to_circle_position()
        
        # Debug: afficher la progression
        if not hasattr(self, 'last_debug_time'):
            self.last_debug_time = time.time()
            
        if time.time() - self.last_debug_time > 3.0:  # Debug toutes les 3 secondes
            distance_to_target = 0
            if self.target_position_on_circle:
                distance_to_target = sqrt(
                    (self.position[0] - self.target_position_on_circle[0])**2 + 
                    (self.position[1] - self.target_position_on_circle[1])**2
                )
            print(f"Sous-marin {self.team}: Position {self.position}, Angle {self.current_angle}°, Mines défensives {self.mines_placed}/{self.max_mines}, Distance cible: {distance_to_target:.1f}, Moving: {self.is_moving}")
            self.last_debug_time = time.time()


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
