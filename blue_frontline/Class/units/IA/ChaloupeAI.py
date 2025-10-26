"""
Module IA pour Chaloupe - Blue Frontline
Implémente le comportement "Attaque Éclair" avec machine à états + Q-Learning.
États : SEARCHING, POSITIONING, STRIKE, RETREAT
"""

import math
import time
from enum import Enum

# Import du module Q-Learning
try:
    from Class.units.IA.ChaloupeQLearning import QLearningAgent, CHALOUPE_ACTIONS
    QLEARNING_AVAILABLE = True
except ImportError:
    print("Module Q-Learning non disponible, utilisation de l'IA standard")
    QLEARNING_AVAILABLE = False


class ChaloupeState(Enum):
    """États possibles de la chaloupe IA pour l'attaque éclair."""
    SEARCHING = "Recherche"      # Cherche des ennemis
    POSITIONING = "Position"     # Se positionne à distance de sécurité
    STRIKE = "Attaque"          # Fonce vers la cible et tire
    RETREAT = "Retraite"        # Bat en retraite hors de portée


class ChaloupeAI:
    """
    Intelligence Artificielle pour la Chaloupe avec comportement Attaque Éclair.
    
    Comportement :
    1. Chercher une cible ennemie prioritaire
    2. Se positionner à distance de sécurité autour de la cible
    3. Attendre l'opportunité puis foncer pour attaquer
    4. Battre en retraite immédiatement après l'attaque
    5. Répéter le cycle jusqu'à destruction de la cible
    """
    
    def __init__(self, chaloupe_unit):
        """
        Initialise l'IA pour une chaloupe.
        
        Args:
            chaloupe_unit: Instance de la classe Chaloupe
        """
        self.unit = chaloupe_unit
        self.state = ChaloupeState.SEARCHING
        self.target = None
        self.last_state_change = time.time()
        
        # État de combat et timing
        self.last_strike_time = 0
        self.strike_cooldown = 3.0          # Attendre 3s entre les attaques
        self.retreat_position = None
        self.retreat_start_time = 0
        self.min_retreat_duration = 1.5    # Retraite minimum 1.5s
        
        # === Q-LEARNING INTEGRATION ===
        self.qlearning_enabled = False  # DÉSACTIVÉ PAR DÉFAUT - Activer avec F1
        self.qlearning_agent = None
        self.current_state = None
        self.previous_state = None
        self.current_action = None
        self.last_qlearning_update = time.time()
        self.qlearning_update_interval = 2.0  # Mise à jour Q-Learning toutes les 2s
        
        # Système de positionnement dynamique
        self.current_orbit_angle = 0        # Angle actuel autour de la cible
        self.orbit_direction = 1            # 1 = horaire, -1 = anti-horaire
        self.orbit_speed = 0.05             # Vitesse de rotation autour de la cible
        self.last_enemy_position = None     # Dernière position de l'ennemi
        
        # Portées de tir des unités ennemies (depuis Global.py, en pixels)
        self.enemy_ranges = {
            "paquebot": 8 * 32,   # 8 tiles = 256 pixels
            "bateau": 6 * 32,     # 6 tiles = 192 pixels  
            "chaloupe": 2 * 32,   # 2 tiles = 64 pixels
            "eclaireur": 0,       # Pas d'attaque
            "sousmarin": 0,       # À vérifier dans Global.py
            "default": 6 * 32     # Portée par défaut (bateau)
        }
        
        # Distances tactiques
        self.safe_distance_multiplier = 1.5  # 50% plus loin que la portée ennemie  
        self.orbit_radius = 120              # Rayon d'orbite autour de la cible (augmenté)
        
        # Paramètres de recherche  
        self.detection_range = 800  # Portée de détection étendue
        
        # Debug et logs
        self.debug_enabled = False  # Désactivé pour éviter le spam de logs
        self.decision_log = []
    
    def log_decision(self, message: str):
        """Enregistre une décision pour le debug."""
        if self.debug_enabled:
            timestamp = time.time()
            log_entry = f"[Chaloupe {self.unit.team}] {self.state.value}: {message}"
            self.decision_log.append(log_entry)
            print(log_entry)  # Debug console
            
            # Limiter la taille du log
            if len(self.decision_log) > 30:
                self.decision_log.pop(0)
    
    def update(self, dt: int, all_units):
        """
        Mise à jour principale de l'IA (appelée chaque tick).
        
        Args:
            dt: Delta time en millisecondes
            all_units: Liste de toutes les unités du jeu
        """
        if not self.unit.is_alive:
            return
        
        # === Q-LEARNING INTEGRATION ===
        if self.qlearning_enabled and self.qlearning_agent:
            self._update_qlearning(all_units)
        
        # Vérifier si la cible actuelle est toujours valide
        if self.target and not self.target.is_alive:
            self.target = None
            self._change_state(ChaloupeState.SEARCHING, "Cible détruite")
        
        # Machine à états (peut être influencée par Q-Learning)
        if self.state == ChaloupeState.SEARCHING:
            self._handle_searching(all_units)
        elif self.state == ChaloupeState.POSITIONING:
            self._handle_positioning()
        elif self.state == ChaloupeState.STRIKE:
            self._handle_strike()
        elif self.state == ChaloupeState.RETREAT:
            self._handle_retreat()
    
    def _change_state(self, new_state: ChaloupeState, reason: str = ""):
        """Change l'état de l'IA et log la transition."""
        if new_state != self.state:
            old_state = self.state
            self.state = new_state
            self.last_state_change = time.time()
            self.log_decision(f"Transition {old_state.value} -> {new_state.value} ({reason})")
    
    def _handle_searching(self, all_units):
        """Gère l'état SEARCHING : recherche de cible prioritaire."""
        # Chercher une cible prioritaire
        best_target = self._find_best_target(all_units)
        
        if best_target:
            self.target = best_target
            # Mettre à jour la cible dans l'unité aussi
            self.unit.target_enemy = best_target
            distance = self._calculate_distance(self.unit.position, best_target.position)
            
            # IMPORTANT: Toujours passer par POSITIONING d'abord (pas d'attaque directe)
            self._change_state(ChaloupeState.POSITIONING, 
                             f"Cible trouvée: {best_target.unit_type} à {int(distance)}px")
                             
            # Choisir un angle d'approche aléatoire pour varier les attaques
            import random
            self.current_orbit_angle = random.uniform(0, 2 * math.pi)
            self.orbit_direction = random.choice([1, -1])  # Direction aléatoire
        else:
            # Aucune cible trouvée, patrouiller
            if not hasattr(self, '_last_patrol_time') or time.time() - self._last_patrol_time > 2.0:
                self.unit.patrol_area()
                self._last_patrol_time = time.time()
    
    def _handle_positioning(self):
        """Gère l'état POSITIONING : positionnement tactique autour de la cible."""
        if not self.target:
            self._change_state(ChaloupeState.SEARCHING, "Cible perdue")
            return
        
        current_distance = self._calculate_distance(self.unit.position, self.target.position)
        safe_distance = self._get_safe_distance()
        
        # Détecter si l'ennemi nous poursuit (se rapproche)
        enemy_is_approaching = self._is_enemy_approaching()
        
        if enemy_is_approaching:
            self.log_decision(f"ENNEMI APPROCHE! Évasion active à {int(current_distance)}px")
            self._evasive_positioning()
            return
        
        # Vérifier si on est à distance de sécurité
        if self._is_at_safe_distance():
            self.log_decision(f"En position sécurisée ({int(current_distance)}px >= {int(safe_distance)}px)")
            
            # Vérifier s'il faut attaquer
            if self._should_trigger_strike():
                # Changer d'angle avant l'attaque pour surprendre
                self._rotate_orbit_angle()
                self._change_state(ChaloupeState.STRIKE, "Opportunité d'attaque détectée")
            else:
                # Continuer à orbiter en changeant constamment de position
                self._dynamic_orbit()
        else:
            # Pas encore à distance de sécurité, s'y rendre rapidement
            self.log_decision(f"Approche sécurisée ({int(current_distance)}px -> {int(safe_distance)}px)")
            self._move_to_safe_position()
    
    def _handle_strike(self):
        """Gère l'état STRIKE : attaque éclair rapide."""
        if not self.target:
            self._change_state(ChaloupeState.SEARCHING, "Cible perdue")
            return
        
        current_distance = self._calculate_distance(self.unit.position, self.target.position)
        
        # Vérifier si on peut attaquer la cible
        if self._can_attack_target():
            # Attaquer immédiatement !
            self.log_decision(f"ATTAQUE ÉCLAIR sur {self.target.unit_type} à {int(current_distance)}px!")
            
            # Forcer l'attaque même si Unit.is_in_range() dit non (pour cibles mobiles)
            if hasattr(self.unit.game, 'combat_system'):
                try:
                    # Forcer l'attaque en utilisant directement le système de combat
                    projectile = self.unit.game.combat_system.fire_projectile(self.unit, self.target)
                    if projectile:
                        self.log_decision(f"PROJECTILE TIRÉ avec succès!")
                    else:
                        self.log_decision(f"Attaque échouée - projectile non créé")
                        
                    # Marquer le temps d'attaque pour le cooldown
                    self.unit.last_shot_time = time.time()
                except Exception as e:
                    self.log_decision(f"Erreur attaque: {e}")
            else:
                self.log_decision("Système de combat non disponible")
            
            self.last_strike_time = time.time()
            
            # Calculer la position de retraite et commencer la retraite
            self.retreat_position = self._calculate_retreat_position()
            self.retreat_start_time = time.time()
            self._change_state(ChaloupeState.RETREAT, "Attaque effectuée")
        else:
            # Continuer à foncer vers la cible
            attack_range = self.unit.range * 32  # Portée en pixels
            self.log_decision(f"Fonce vers cible ({int(current_distance)}px -> {attack_range}px)")
            self._move_directly_to_target()
    
    def _handle_retreat(self):
        """Gère l'état RETREAT : retraite tactique hors de portée."""
        if not self.target:
            self._change_state(ChaloupeState.SEARCHING, "Aucune cible pour la retraite")
            return
        
        current_time = time.time()
        retreat_duration = current_time - self.retreat_start_time
        current_distance = self._calculate_distance(self.unit.position, self.target.position)
        
        # Toujours maintenir la distance de sécurité pendant la retraite
        if not self._is_at_safe_distance():
            self.log_decision(f"RETRAITE ACTIVE! Distance: {int(current_distance)}px")
            self._dynamic_retreat()
            return
        
        # Vérifier si la retraite est terminée
        if retreat_duration >= self.min_retreat_duration:
            # Retraite terminée, changer d'angle d'attaque et retour au positionnement
            self._rotate_orbit_angle(large_rotation=True)  # Grand changement d'angle
            self.retreat_position = None
            self.log_decision("Retraite terminée - Nouveau positionnement")
            self._change_state(ChaloupeState.POSITIONING, "Retraite terminée")
        else:
            # Continuer la retraite en mouvement
            self.log_decision(f"Retraite en cours ({retreat_duration:.1f}s)")
            self._dynamic_retreat()
    

    # === MÉTHODES UTILITAIRES ===
    def _find_best_target(self, all_units):
        """Trouve la meilleure cible ennemie selon les priorités."""
        if not all_units:
            return None
        
        # Types d'unités prioritaires pour les Chaloupes
        priority_targets = ["paquebot", "bateau"]
        
        best_priority_target = None
        best_other_target = None
        min_priority_distance = float('inf')
        min_other_distance = float('inf')
        
        for unit in all_units:
            # Ignorer les unités de la même équipe, mortes ou plateformes
            if (unit.team == self.unit.team or 
                not unit.is_alive or 
                getattr(unit, 'is_platform', False)):
                continue
            
            distance = self._calculate_distance(self.unit.position, unit.position)
            
            if distance > self.detection_range:
                continue
            
            unit_type = getattr(unit, 'unit_type', '')
            
            # Cible prioritaire
            if unit_type in priority_targets and distance < min_priority_distance:
                min_priority_distance = distance
                best_priority_target = unit
            # Cible secondaire
            elif distance < min_other_distance:
                min_other_distance = distance
                best_other_target = unit
        
        return best_priority_target if best_priority_target else best_other_target
    
    def _calculate_distance(self, pos1, pos2):
        """Calcule la distance entre deux positions."""
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def _get_enemy_range(self):
        """Retourne la portée de tir de la cible actuelle."""
        if not self.target:
            return self.enemy_ranges["default"]
        
        unit_type = getattr(self.target, 'unit_type', 'default')
        return self.enemy_ranges.get(unit_type, self.enemy_ranges["default"])
    
    def _get_safe_distance(self):
        """Retourne la distance de sécurité par rapport à la cible."""
        enemy_range = self._get_enemy_range()
        return enemy_range * self.safe_distance_multiplier
    
    def _is_at_safe_distance(self):
        """Vérifie si la chaloupe est à distance de sécurité."""
        if not self.target:
            return True
        
        distance = self._calculate_distance(self.unit.position, self.target.position)
        safe_dist = self._get_safe_distance()
        return distance >= safe_dist
    
    def _can_attack_target(self):
        """Vérifie si la chaloupe peut attaquer la cible."""
        if not self.target:
            return False
        
        distance = self._calculate_distance(self.unit.position, self.target.position)
        # Utiliser la portée en pixels (range * 32) avec une marge pour compenser le mouvement
        attack_range = self.unit.range * 32 + 30  # 2 * 32 + 30 = 94 pixels (marge pour cibles mobiles)
        can_attack = distance <= attack_range
        
        if can_attack:
            self.log_decision(f"Distance à cible: {distance:.0f}px, Portée chaloupe: {attack_range}px, Peut attaquer: {can_attack}")
            
        return can_attack
    
    def _should_trigger_strike(self):
        """Détermine s'il faut déclencher une attaque éclair."""
        current_time = time.time()
        
        # Vérifier le cooldown
        if current_time - self.last_strike_time < self.strike_cooldown:
            self.log_decision(f"Cooldown actif: {self.strike_cooldown - (current_time - self.last_strike_time):.1f}s restant")
            return False
        
        # Attendre au moins 2 secondes en position avant d'attaquer
        if current_time - self.last_state_change < 2.0:
            self.log_decision("Positionnement en cours...")
            return False
        
        # Vérifier si la cible bouge (opportunité d'attaque)
        if hasattr(self.target, 'is_moving') and self.target.is_moving:
            self.log_decision("Cible en mouvement - ATTAQUE!")
            return True
        
        # Ou si on attend depuis longtemps (8 secondes au lieu de 5)
        if current_time - self.last_state_change > 8.0:
            self.log_decision("Attaque par timeout")
            return True
        
        self.log_decision("Attente d'opportunité...")
        return False
    
    def _calculate_orbit_position(self, angle_override=None):
        """Calcule une position d'orbite autour de la cible."""
        if not self.target:
            return self.unit.position
        
        safe_dist = self._get_safe_distance()
        target_pos = self.target.position
        
        # Utiliser l'angle spécifié ou l'angle actuel
        angle = angle_override if angle_override is not None else self.current_orbit_angle
        
        # Calculer la position d'orbite
        orbit_x = target_pos[0] + safe_dist * math.cos(angle)
        orbit_y = target_pos[1] + safe_dist * math.sin(angle)
        
        return (orbit_x, orbit_y)
    
    def _is_enemy_approaching(self):
        """Détecte si l'ennemi se rapproche de nous."""
        if not self.target or not self.last_enemy_position:
            self.last_enemy_position = self.target.position if self.target else None
            return False
        
        # Distance précédente entre ennemi et nous
        old_distance = self._calculate_distance(self.unit.position, self.last_enemy_position)
        # Distance actuelle
        current_distance = self._calculate_distance(self.unit.position, self.target.position)
        
        # Mettre à jour la position de l'ennemi
        self.last_enemy_position = self.target.position
        
        # Si l'ennemi se rapproche de plus de 10px
        return current_distance < old_distance - 10
    
    def _evasive_positioning(self):
        """Positionnement évasif quand l'ennemi nous poursuit."""
        if not self.target:
            return
        
        if self._is_unit_busy_with_pathfinding():
            return  # Attendre que le mouvement actuel se termine
        
        # Changer rapidement d'angle pour éviter l'ennemi
        self.current_orbit_angle += self.orbit_direction * self.orbit_speed * 3  # 3x plus rapide
        
        # Calculer position évasive avec distance de sécurité augmentée
        enemy_pos = self.target.position
        safe_dist = self._get_safe_distance() * 1.2  # 20% plus loin quand poursuivi
        
        evasive_x = enemy_pos[0] + safe_dist * math.cos(self.current_orbit_angle)
        evasive_y = enemy_pos[1] + safe_dist * math.sin(self.current_orbit_angle)
        
        evasive_pos = (evasive_x, evasive_y)
        self.log_decision(f"Évasion -> ({int(evasive_x)}, {int(evasive_y)})")
        
        # Respecter le cooldown pour éviter les recalculs constants
        if self.unit.need_pathfinding_to_target(evasive_pos):
            current_time = time.time()
            if current_time - self.unit.last_pathfinding_time > self.unit.pathfinding_cooldown:
                self.log_decision("Pathfinding nécessaire pour évasion")
                self.unit.last_pathfinding_time = current_time
                self.unit.start_pathfinding_thread(
                    lambda: self.unit.compute_path_to_target(evasive_pos)
                )
        else:
            self.unit.move_directly_to_target(evasive_pos)
    
    def _dynamic_orbit(self):
        """Orbite dynamique qui change constamment de position."""
        if self._is_unit_busy_with_pathfinding():
            return  # Attendre que le mouvement actuel se termine
        
        # Faire tourner l'angle d'orbite
        self.current_orbit_angle += self.orbit_direction * self.orbit_speed
        
        # Changer de direction de temps en temps pour imprévisibilité
        if abs(self.current_orbit_angle) > 2 * math.pi:
            self.current_orbit_angle = 0
            self.orbit_direction *= -1  # Inverser la direction
        
        orbit_pos = self._calculate_orbit_position()
        self.log_decision(f"Orbite dynamique -> ({int(orbit_pos[0])}, {int(orbit_pos[1])})")
        
        # Respecter le cooldown pour éviter les recalculs constants
        if self.unit.need_pathfinding_to_target(orbit_pos):
            current_time = time.time()
            if current_time - self.unit.last_pathfinding_time > self.unit.pathfinding_cooldown:
                self.log_decision("Pathfinding nécessaire pour orbite")
                self.unit.last_pathfinding_time = current_time
                self.unit.start_pathfinding_thread(
                    lambda: self.unit.compute_path_to_target(orbit_pos)
                )
        else:
            self.unit.move_directly_to_target(orbit_pos)
    
    def _rotate_orbit_angle(self, large_rotation=False):
        """Change l'angle d'orbite pour varier les angles d'attaque."""
        import random
        if large_rotation:
            # Grand changement d'angle (60-180 degrés)
            angle_change = random.uniform(math.pi/3, math.pi)
        else:
            # Petit changement d'angle (30-90 degrés)
            angle_change = random.uniform(math.pi/6, math.pi/2)
        
        self.current_orbit_angle += angle_change * self.orbit_direction
        self.log_decision(f"Nouvel angle d'attaque: {int(math.degrees(self.current_orbit_angle))}°")
    
    def _dynamic_retreat(self):
        """Retraite dynamique qui maintient la distance de sécurité."""
        if not self.target:
            return
        
        if self._is_unit_busy_with_pathfinding():
            return  # Attendre que le mouvement actuel se termine
        
        # Calculer direction de fuite (opposée à l'ennemi)
        enemy_pos = self.target.position
        current_pos = self.unit.position
        
        dx = current_pos[0] - enemy_pos[0]
        dy = current_pos[1] - enemy_pos[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 0:
            # Normaliser
            dx /= distance
            dy /= distance
            
            # Position de retraite à distance de sécurité + marge
            safe_dist = self._get_safe_distance() * 1.1  # 10% plus loin
            retreat_x = enemy_pos[0] + dx * safe_dist
            retreat_y = enemy_pos[1] + dy * safe_dist
            
            retreat_pos = (retreat_x, retreat_y)
            self.log_decision(f"Retraite dynamique -> ({int(retreat_x)}, {int(retreat_y)})")
            
            # Respecter le cooldown pour éviter les recalculs constants
            if self.unit.need_pathfinding_to_target(retreat_pos):
                current_time = time.time()
                if current_time - self.unit.last_pathfinding_time > self.unit.pathfinding_cooldown:
                    self.log_decision("Pathfinding nécessaire pour retraite")
                    self.unit.last_pathfinding_time = current_time
                    self.unit.start_pathfinding_thread(
                        lambda: self.unit.compute_path_to_target(retreat_pos)
                    )
            else:
                self.unit.move_directly_to_target(retreat_pos)
    
    def _calculate_retreat_position(self):
        """Calcule la position de retraite optimale."""
        if not self.target:
            return self.unit.position
        
        enemy_pos = self.target.position
        current_pos = self.unit.position
        
        # Vecteur de direction opposée à l'ennemi
        dx = current_pos[0] - enemy_pos[0]
        dy = current_pos[1] - enemy_pos[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 0:
            # Normaliser le vecteur
            dx /= distance
            dy /= distance
            
            # Position de retraite à distance de sécurité
            safe_dist = self._get_safe_distance()
            retreat_x = enemy_pos[0] + dx * safe_dist
            retreat_y = enemy_pos[1] + dy * safe_dist
            
            return (retreat_x, retreat_y)
        
        return current_pos
    
    def _orbit_around_target(self):
        """Fait orbiter légèrement la chaloupe autour de la cible.""" 
        # Utiliser la nouvelle orbite dynamique
        self._dynamic_orbit()
    
    def _move_to_safe_position(self):
        """Se déplace vers une position de sécurité."""
        if self._is_unit_busy_with_pathfinding():
            return  # Attendre que le mouvement actuel se termine
        
        safe_pos = self._calculate_orbit_position()
        self.log_decision(f"Mouvement sécurisé -> ({int(safe_pos[0])}, {int(safe_pos[1])})")
        
        # Vérifier si pathfinding nécessaire
        # Respecter le cooldown pour éviter les recalculs constants
        if self.unit.need_pathfinding_to_target(safe_pos):
            current_time = time.time()
            if current_time - self.unit.last_pathfinding_time > self.unit.pathfinding_cooldown:
                self.log_decision("Pathfinding nécessaire pour position sécurisée")
                self.unit.last_pathfinding_time = current_time
                self.unit.start_pathfinding_thread(
                    lambda: self.unit.compute_path_to_target(safe_pos)
                )
        else:
            self.unit.move_directly_to_target(safe_pos)
    
    def _move_directly_to_target(self):
        """Fonce directement vers la cible pour l'attaque."""
        if not self.target:
            return
        
        if self._is_unit_busy_with_pathfinding():
            return  # Attendre que le mouvement actuel se termine
        
        target_pos = self.target.position
        self.log_decision(f"Fonce vers {self.target.unit_type} -> ({int(target_pos[0])}, {int(target_pos[1])})")
        
        # Si une île quantique bloque le chemin, la contourner
        # Respecter le cooldown pour éviter les recalculs constants
        if self.unit.need_pathfinding_to_target(target_pos):
            current_time = time.time()
            if current_time - self.unit.last_pathfinding_time > self.unit.pathfinding_cooldown:
                self.log_decision("OBSTACLE DÉTECTÉ - Pathfinding pour attaque")
                self.unit.last_pathfinding_time = current_time
                self.unit.start_pathfinding_thread(
                    lambda: self.unit.compute_path_to_target(target_pos)
                )
        else:
            # Mouvement direct si chemin libre
            self.unit.move_directly_to_target(target_pos)
    
    def _flee_from_target(self):
        """Fuit dans la direction opposée à la cible."""
        # Utiliser la retraite dynamique plutôt que statique
        self._dynamic_retreat()
    
    def _is_unit_busy_with_pathfinding(self):
        """Vérifie si l'unité est occupée avec un pathfinding ou suit un chemin.
        
        Returns:
            bool: True si l'unité est occupée, False sinon
        """
        # Vérifier si un thread de pathfinding est en cours
        if self.unit.path_thread and self.unit.path_thread.is_alive():
            return True
        
        # Vérifier si l'unité suit un chemin existant
        if self.unit.path_to_follow and len(self.unit.path_to_follow) > 0:
            return True
        
        # Vérifier si l'unité est en mouvement vers une destination
        if self.unit.is_moving:
            return True
        
        return False
    
    def get_debug_info(self):
        """Retourne les informations de debug de l'IA."""
        try:
            debug_info = {
                "state": self.state.value if self.state else "Unknown",
                "target": self.target.unit_type if self.target and hasattr(self.target, 'unit_type') else "Aucune",
                "distance_to_target": int(self._calculate_distance(self.unit.position, self.target.position)) if self.target and hasattr(self.target, 'position') else 0,
                "safe_distance": int(self._get_safe_distance()) if self.target else 0,
                "can_attack": self._can_attack_target() if self.target else False,
                "at_safe_distance": self._is_at_safe_distance() if self.target else True,
                "last_decisions": self.decision_log[-3:] if self.decision_log else []
            }
            
            # Ajouter les infos Q-Learning si disponible
            if self.qlearning_enabled and self.qlearning_agent:
                qlearning_stats = self.qlearning_agent.get_stats()
                debug_info["qlearning"] = {
                    "enabled": True,
                    "epsilon": f"{qlearning_stats['epsilon']:.3f}",
                    "last_action": self.current_action if self.current_action else "None",
                    "last_reward": f"{qlearning_stats['last_reward']:.1f}",
                    "total_rewards": f"{qlearning_stats['total_rewards']:.1f}",
                    "q_table_size": qlearning_stats['q_table_size']
                }
            else:
                debug_info["qlearning"] = {"enabled": False}
            
            return debug_info
            
        except Exception as e:
            # En cas d'erreur, retourner un debug info minimal
            print(f"Erreur get_debug_info: {e}")
            return {
                "state": "Error",
                "target": "Unknown",
                "distance_to_target": 0,
                "safe_distance": 0,
                "can_attack": False,
                "at_safe_distance": True,
                "last_decisions": [],
                "qlearning": {"enabled": False}
            }
    
    # ==========================================
    # MÉTHODES Q-LEARNING
    # ==========================================
    
    def _update_qlearning(self, all_units):
        """Met à jour le système Q-Learning."""
        current_time = time.time()
        
        # Mise à jour périodique pour éviter la surcharge
        if current_time - self.last_qlearning_update < self.qlearning_update_interval:
            return
        
        self.last_qlearning_update = current_time
        
        # Obtenir l'état courant
        self.current_state = self.qlearning_agent.get_state(self.unit, all_units)
        
        # Si on a un état précédent, calculer la récompense et mettre à jour Q-table
        if self.previous_state is not None and self.current_action is not None:
            reward = self.qlearning_agent.calculate_reward(
                self.unit, self.previous_state, self.current_action, self.current_state, all_units
            )
            
            self.qlearning_agent.update_q_table(
                self.previous_state, self.current_action, reward, self.current_state
            )
        
        # Choisir la prochaine action avec Q-Learning
        suggested_action = self.qlearning_agent.choose_action(self.current_state)
        
        # Appliquer l'action suggérée par Q-Learning
        self._apply_qlearning_action(suggested_action, all_units)
        
        # Sauvegarder l'état pour la prochaine mise à jour
        self.previous_state = self.current_state
        self.current_action = suggested_action
        
        # Sauvegarde périodique de la Q-table
        if self.qlearning_agent.total_episodes % 100 == 0:
            qtable_filename = f"chaloupe_{self.unit.team}_qtable.pkl"
            self.qlearning_agent.save_q_table(qtable_filename)
    
    def _apply_qlearning_action(self, action: str, all_units):
        """Applique l'action suggérée par Q-Learning."""
        try:
            if self.state in [ChaloupeState.STRIKE, ChaloupeState.RETREAT]:
                self.log_decision(f"Q-Learning: Action {action} ignorée (état {self.state.value} prioritaire)")
                return
            
            if action == "move_to_enemy":
                if self.target and self.state == ChaloupeState.SEARCHING:
                    self._change_state(ChaloupeState.POSITIONING, f"Q-Learning: {action}")
                    
            elif action == "retreat":
                if self.state == ChaloupeState.POSITIONING:
                    self._change_state(ChaloupeState.RETREAT, f"Q-Learning: {action}")
                
            elif action == "orbit":
                if self.target and self.state == ChaloupeState.POSITIONING:
                    self._dynamic_orbit()
                    self.log_decision(f"Q-Learning: Orbite dynamique appliquée")
                    
            elif action == "attack":
                if self.target and self._can_attack_target() and self.state == ChaloupeState.POSITIONING:
                    self._change_state(ChaloupeState.STRIKE, f"Q-Learning: {action}")
                elif self.target and self.state == ChaloupeState.SEARCHING:
                    # Si on ne peut pas attaquer, se positionner d'abord
                    self._change_state(ChaloupeState.POSITIONING, f"Q-Learning: Positionnement pour attaque")
                    
            elif action == "change_angle":
                if self.state == ChaloupeState.POSITIONING:
                    self._rotate_orbit_angle()
                    self.log_decision(f"Q-Learning: Changement d'angle appliqué")
                
            elif action == "hide":
                # Pour l'instant, considérer comme une retraite vers un obstacle
                if self.state == ChaloupeState.POSITIONING:
                    self._change_state(ChaloupeState.RETREAT, f"Q-Learning: Se cacher (retraite)")
                
            elif action == "wait":
                # Maintenir la position actuelle, pas de changement d'état
                self.log_decision(f"Q-Learning: Attendre en position")
                
        except Exception as e:
            self.log_decision(f"Erreur application action Q-Learning {action}: {e}")
    
    def get_qlearning_stats(self):
        """Retourne les statistiques Q-Learning."""
        if self.qlearning_enabled and self.qlearning_agent:
            return self.qlearning_agent.get_stats()
        return None
    
    def save_qlearning_progress(self):
        """Sauvegarde manuellement le progrès Q-Learning."""
        if self.qlearning_enabled and self.qlearning_agent:
            qtable_filename = f"chaloupe_{self.unit.team}_qtable.pkl"
            self.qlearning_agent.save_q_table(qtable_filename)
            print(f"[ChaloupeAI] Progrès Q-Learning sauvegardé pour {self.unit.team}")
    
    def toggle_qlearning(self, enabled: bool):
        """Active/désactive le Q-Learning."""
        if QLEARNING_AVAILABLE:
            self.qlearning_enabled = enabled
            if enabled and not self.qlearning_agent:
                # Initialiser l'agent Q-Learning
                self.qlearning_agent = QLearningAgent(
                    actions=CHALOUPE_ACTIONS,
                    alpha=0.1,      # Taux d'apprentissage
                    gamma=0.9,      # Facteur de remise  
                    epsilon=0.2     # Exploration initiale
                )
                qtable_filename = f"chaloupe_{self.unit.team}_qtable.pkl"
                self.qlearning_agent.load_q_table(qtable_filename)
            print(f"[ChaloupeAI] Q-Learning {'activé' if enabled else 'désactivé'} pour {self.unit.team}")
        else:
            print(f"[ChaloupeAI] Q-Learning non disponible")