import time
import math
import pygame
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
        self.ia_mode = "attaque"  # Modes possibles: "fuite", "defense_base", "attaque"
        
            
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

    def set_ia_mode(self, mode: str):
        """Change le mode d'IA du sous-marin.
        
        Args:
            mode (str): Le mode à activer ("fuite", "defense_base", "attaque")
        """
        if mode in ["fuite", "defense_base", "attaque"]:
            self.ia_mode = mode
            print(f"🎯 {self.team} sous-marin: Mode IA changé en '{mode}'")
        else:
            print(f"⚠ Mode IA invalide: {mode}. Modes possibles: fuite, defense_base, attaque")
    
    def ia_mode_fuite(self, all_units):
        """Mode fuite: Le sous-marin fuit les ennemis et pose des mines défensives.
        
        Args:
            all_units (list[Unit]): Liste de toutes les unités du jeu
        """
        # TODO: Implémenter la logique de fuite
        pass
    
    def ia_mode_defense_base(self, all_units):
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
        """IA du sous-marin pour se déplacer en ligne droite vers l'avant jusqu'à un obstacle.
        
        Le sous-marin détecte les éclaireurs à proximité, fonce vers eux jusqu'à collision et pose une mine.
        Sinon, il patrouille en ligne droite.
        """
        
        # PRIORITÉ 1 : Chercher des éclaireurs ennemis à proximité (10 cases = 320 pixels)
        nearby_scouts = self.find_nearby_scouts(all_units, detection_range=320)
        
        if nearby_scouts:
            # Si un éclaireur est détecté, le poursuivre
            target_scout = self.get_closest_scout(nearby_scouts)
            
            if target_scout:
                # Calculer la distance avec l'éclaireur
                dx = target_scout.position[0] - self.position[0]
                dy = target_scout.position[1] - self.position[1]
                distance_to_scout = math.sqrt(dx**2 + dy**2)
                
                # Distance de collision augmentée pour mieux détecter la proximité
                collision_distance = 30
                
                print(f"🔍 {self.team} sous-marin: Éclaireur détecté à {int(distance_to_scout)}px (seuil: {collision_distance}px)")
                
                # Si on est en collision ou très très proche, arrêter et poser une mine
                if distance_to_scout <= collision_distance:
                    print(f"⚠️ {self.team} sous-marin: PROCHE de l'éclaireur! Distance: {int(distance_to_scout)}px")
                    
                    # Arrêter le mouvement en cours
                    self.stop()
                    self.is_moving = False
                    self.target_position = None
                    
                    # Poser une mine si le cooldown est passé
                    if self.can_place_mine():
                        print(f"✅ {self.team} sous-marin: Cooldown OK, pose de mine...")
                        mine_placed = self.place_mine(int(self.position[0]), int(self.position[1]))
                        if mine_placed:
                            print(f"💣 {self.team} sous-marin a posé une mine à ({int(self.position[0])}, {int(self.position[1])}) - COLLISION avec éclaireur: {int(distance_to_scout)}px")
                    else:
                        print(f"⏳ {self.team} sous-marin: Cooldown en cours...")
                    return
                
                # Si l'éclaireur est plus loin, arrêter le mouvement actuel et se diriger vers lui
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
                    print(f"🎯 {self.team} sous-marin: Se déplace vers l'éclaireur...")
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
                return
        
        # PRIORITÉ 2 : Comportement normal (patrouille)
        self.patrol_movement()
    
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

