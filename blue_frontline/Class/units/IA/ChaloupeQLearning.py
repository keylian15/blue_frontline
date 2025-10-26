import random
import pickle
import math
import time
import os
from typing import List, Dict, Tuple, Optional, Any

class QLearningAgent:
    """
    Agent Q-Learning pour l'IA de la chaloupe.
    Apprend à choisir les meilleures actions selon l'état du jeu.
    """
    
    def __init__(self, actions: List[str], alpha: float = 0.1, gamma: float = 0.9, epsilon: float = 0.2):
        """
        Initialise l'agent Q-Learning.
        
        Args:
            actions: Liste des actions possibles
            alpha: Taux d'apprentissage (0-1)
            gamma: Facteur de remise (0-1) 
            epsilon: Taux d'exploration (0-1)
        """
        self.q_table = {}  # {(state): {action: value}}
        self.actions = actions
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = 0.995  # Décroissance de l'exploration
        self.epsilon_min = 0.01     # Exploration minimale
        
        # Statistiques d'apprentissage
        self.total_episodes = 0
        self.total_rewards = 0
        self.last_reward = 0
        self.state_history = []
        self.action_history = []
        self.reward_history = []
        
        # Debug
        self.debug_enabled = True
        
    def discretize_position(self, x: float, y: float, grid_size: int = 64) -> Tuple[int, int]:
        """Discrétise les positions pour réduire l'espace d'états."""
        return (int(x // grid_size), int(y // grid_size))
    
    def discretize_distance(self, distance: float) -> str:
        """Discrétise les distances en catégories."""
        if distance < 100:
            return "very_close"
        elif distance < 200:
            return "close"
        elif distance < 400:
            return "medium"
        elif distance < 600:
            return "far"
        else:
            return "very_far"
    
    def discretize_health(self, health: float, max_health: float) -> str:
        """Discrétise la santé en catégories."""
        ratio = health / max_health if max_health > 0 else 0
        if ratio > 0.7:
            return "high"
        elif ratio > 0.3:
            return "medium"
        else:
            return "low"

    def get_state(self, chaloupe, all_units: List = None) -> Tuple:
        """
        Encode l'état courant en tuple discret.
        
        Args:
            chaloupe: L'unité chaloupe
            all_units: Liste de toutes les unités
        Returns:
            Tuple représentant l'état discret
        """
        # Position discrétisée de la chaloupe
        chaloupe_pos = self.discretize_position(chaloupe.position[0], chaloupe.position[1])
        
        # Santé discrétisée
        health_state = self.discretize_health(chaloupe.current_health, chaloupe.max_health)
        
        # État de l'ennemi le plus proche
        enemy_distance = "none"
        enemy_type = "none"
        enemy_health = "none"
        relative_position = "none"
        
        if all_units:
            closest_enemy = self._find_closest_enemy(chaloupe, all_units)
            if closest_enemy:
                distance = math.sqrt((chaloupe.position[0] - closest_enemy.position[0])**2 + (chaloupe.position[1] - closest_enemy.position[1])**2)
                enemy_distance = self.discretize_distance(distance)
                enemy_type = closest_enemy.unit_type
                enemy_health = self.discretize_health(closest_enemy.current_health, closest_enemy.max_health)
                
                # Position relative de l'ennemi
                dx = closest_enemy.position[0] - chaloupe.position[0]
                dy = closest_enemy.position[1] - chaloupe.position[1]
                if abs(dx) > abs(dy):
                    relative_position = "east" if dx > 0 else "west"
                else:
                    relative_position = "south" if dy > 0 else "north"
        
        # Présence d'obstacles
        obstacle_nearby = self._obstacle_near(chaloupe)
        
        # Mode actuel (si disponible via l'IA existante)
        current_mode = "searching"
        if hasattr(chaloupe, 'ai_system') and chaloupe.ai_system:
            current_mode = chaloupe.ai_system.state.value.lower()
        
        state = (
            chaloupe_pos,
            health_state,
            enemy_distance,
            enemy_type,
            enemy_health,
            relative_position,
            obstacle_nearby,
            current_mode
        )
        
        return state

    def choose_action(self, state: Tuple) -> str:
        """
        Choisit une action selon la politique epsilon-greedy.
        
        Args:
            state: État courant
            
        Returns:
            Action choisie
        """
        # Exploration vs exploitation
        if random.random() < self.epsilon or state not in self.q_table:
            action = random.choice(self.actions)
        else:
            # Choisir la meilleure action
            action = max(self.q_table[state], key=self.q_table[state].get)
        
        return action

    def update_q_table(self, state: Tuple, action: str, reward: float, next_state: Tuple):
        """
        Met à jour la Q-table selon l'équation de Bellman.
        
        Args:
            state: État précédent
            action: Action effectuée
            reward: Récompense reçue
            next_state: Nouvel état
        """
        # Initialisation si nécessaire
        if state not in self.q_table:
            self.q_table[state] = {a: 0.0 for a in self.actions}
        if next_state not in self.q_table:
            self.q_table[next_state] = {a: 0.0 for a in self.actions}
        
        # Mise à jour Q-Learning
        old_value = self.q_table[state][action]
        next_max = max(self.q_table[next_state].values()) if self.q_table[next_state] else 0.0
        new_value = old_value + self.alpha * (reward + self.gamma * next_max - old_value)
        self.q_table[state][action] = new_value
        
        # Statistiques
        self.total_rewards += reward
        self.last_reward = reward
                
        # Décroissance de epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def calculate_reward(self, chaloupe, previous_state: Tuple, action: str, current_state: Tuple, all_units: List = None) -> float:
        """
        Calcule la récompense basée sur l'action et l'état résultant.
        
        Args:
            chaloupe: L'unité chaloupe
            previous_state: État précédent
            action: Action effectuée
            current_state: État courant
            all_units: Liste de toutes les unités
            
        Returns:
            Valeur de récompense
        """
        reward = 0.0
        
        # Récompense de base pour rester en vie
        if chaloupe.is_alive:
            reward += 2.0
        else:
            reward -= 10.0  # Pénalité pour mourir
            return reward
        
        # Analyse des changements d'état
        prev_health = previous_state[1] if len(previous_state) > 1 else "high"
        curr_health = current_state[1] if len(current_state) > 1 else "high"
        
        # Récompenses liées à la santé
        if curr_health != prev_health:
            if curr_health == "low" and prev_health != "low":
                reward -= 5.0  # Pénalité pour perdre de la santé
            elif curr_health == "high" and prev_health == "low":
                reward += 3.0  # Récompense pour récupérer
        
        # Récompenses liées aux ennemis
        if all_units:
            enemy_before = previous_state[2] if len(previous_state) > 2 else "none"
            enemy_after = current_state[2] if len(current_state) > 2 else "none"
            
            # Récompense pour se rapprocher d'un ennemi (phase d'attaque)
            if action in ["move_to_enemy", "attack"] and enemy_after in ["close", "very_close"]:
                reward += 3.0
            
            # Récompense pour rester à distance sécurisée
            if action in ["retreat", "orbit"] and enemy_after in ["medium", "far"]:
                reward += 2.0
            
            # Bonus pour attaquer quand l'ennemi est proche
            if action == "attack" and enemy_after == "very_close":
                reward += 10.0
            
            # Pénalité pour s'approcher trop quand l'ennemi est dangereux
            if enemy_after == "very_close" and action not in ["attack", "retreat"]:
                reward -= 3.0
        
        # Récompenses spécifiques aux actions
        action_rewards = {
            "wait": -0.5,        # Légère pénalité pour attendre
            "orbit": 1.0,        # Récompense pour orbiter (comportement tactique)
            "change_angle": 0.5, # Récompense pour changer d'angle
            "hide": 2.0          # Récompense pour se cacher
        }
        
        if action in action_rewards:
            reward += action_rewards[action]
        
        return reward

    def save_q_table(self, filename: str = "chaloupe_qtable.pkl"):
        """Sauvegarde la Q-table dans un fichier."""
        try:
            # Créer le dossier data/qlearning s'il n'existe pas
            os.makedirs("data/qlearning", exist_ok=True)
            filepath = os.path.join("data/qlearning", filename)
            
            save_data = {
                'q_table': self.q_table,
                'total_episodes': self.total_episodes,
                'total_rewards': self.total_rewards,
                'epsilon': self.epsilon
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(save_data, f)
            # Message de sauvegarde supprimé pour réduire le spam
        except Exception as e:
            print(f"[Q-Learning] Erreur sauvegarde: {e}")

    def load_q_table(self, filename: str = "chaloupe_qtable.pkl"):
        """Charge la Q-table depuis un fichier."""
        try:
            filepath = os.path.join("data/qlearning", filename)
            with open(filepath, 'rb') as f:
                save_data = pickle.load(f)
                
            self.q_table = save_data.get('q_table', {})
            self.total_episodes = save_data.get('total_episodes', 0)
            self.total_rewards = save_data.get('total_rewards', 0)
            self.epsilon = save_data.get('epsilon', self.epsilon)
            
            print(f"[Q-Learning] Q-table chargée: {len(self.q_table)} états, {self.total_episodes} épisodes")
        except FileNotFoundError:
            print(f"[Q-Learning] Fichier {filename} non trouvé, nouvelle Q-table créée")
            self.q_table = {}
        except Exception as e:
            print(f"[Q-Learning] Erreur chargement: {e}")

    def _find_closest_enemy(self, chaloupe, all_units: List) -> Optional[Any]:
        """Trouve l'ennemi le plus proche."""
        closest_enemy = None
        min_distance = float('inf')
        
        for unit in all_units:
            if unit.team != chaloupe.team and unit.is_alive:
                distance = math.sqrt((chaloupe.position[0] - unit.position[0])**2 + (chaloupe.position[1] - unit.position[1])**2)
                if distance < min_distance:
                    min_distance = distance
                    closest_enemy = unit
        
        return closest_enemy

    def _obstacle_near(self, chaloupe) -> bool:
        """Détecte s'il y a un obstacle proche (simplifié pour l'instant)."""
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'apprentissage."""
        return {
            'total_episodes': self.total_episodes,
            'total_rewards': self.total_rewards,
            'avg_reward': self.total_rewards / max(1, self.total_episodes),
            'epsilon': self.epsilon,
            'q_table_size': len(self.q_table),
            'last_reward': self.last_reward
        }

# Actions possibles pour la chaloupe
CHALOUPE_ACTIONS = [
    "move_to_enemy",    # Se déplacer vers la cible
    "retreat",          # Se déplacer hors de portée  
    "orbit",            # Orbiter autour de la cible
    "attack",           # Attaquer
    "change_angle",     # Changer d'angle d'approche
    "hide",             # Se cacher derrière un obstacle
    "wait"              # Attendre/observer
]

# Exemple d'utilisation et tests
if __name__ == "__main__":
    print("=== Test Q-Learning pour Chaloupe ===")
    
    # Créer l'agent
    agent = QLearningAgent(CHALOUPE_ACTIONS, alpha=0.1, gamma=0.9, epsilon=0.3)
    
    # Test avec des états fictifs
    test_state1 = (
        (10, 15),      # Position chaloupe
        "high",        # Santé
        "medium",      # Distance ennemi
        "paquebot",    # Type ennemi
        "high",        # Santé ennemi
        "north",       # Position relative
        False,         # Obstacle
        "searching"    # Mode actuel
    )
    
    test_state2 = (
        (11, 15),      # Position chaloupe (bougé)
        "high",        # Santé
        "close",       # Distance ennemi (rapprochée)
        "paquebot",    # Type ennemi
        "medium",      # Santé ennemi
        "north",       # Position relative
        False,         # Obstacle
        "positioning"  # Mode actuel
    )
    
    # Test de choix d'action
    action1 = agent.choose_action(test_state1)
    print(f"Action choisie pour état 1: {action1}")
    
    # Simuler une récompense
    reward = 5.0
    agent.update_q_table(test_state1, action1, reward, test_state2)
    
    action2 = agent.choose_action(test_state2)
    print(f"Action choisie pour état 2: {action2}")
    
    # Afficher les statistiques
    stats = agent.get_stats()
    print(f"Statistiques: {stats}")
    
    # Test de sauvegarde/chargement
    agent.save_q_table("test_chaloupe_qtable.pkl")
    agent.load_q_table("test_chaloupe_qtable.pkl")
    
    print("=== Test terminé ===")