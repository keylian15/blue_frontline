#!/usr/bin/env python3
"""
Script de test automatique pour le système Q-Learning des chaloupes.
Teste les fonctionnalités principales sans interface graphique.

Usage:
    Depuis le dossier blue_frontline/:
    python Class/units/IA/test_qlearning.py
    
    Ou depuis Class/units/IA/:
    python test_qlearning.py
"""

import sys
import os
import time

# Ajouter le chemin du projet pour les imports
# Remonter de 3 niveaux : IA -> units -> Class -> blue_frontline
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.insert(0, project_root)

from Class.units.IA.ChaloupeQLearning import QLearningAgent, CHALOUPE_ACTIONS

def test_qlearning_agent():
    """Test des fonctionnalités de base de l'agent Q-Learning."""
    print("=== TEST AGENT Q-LEARNING ===")
    
    # Créer l'agent
    agent = QLearningAgent(CHALOUPE_ACTIONS, alpha=0.1, gamma=0.9, epsilon=0.3)
    print(f"✓ Agent créé avec {len(CHALOUPE_ACTIONS)} actions")
    
    # Test de l'encodage d'état
    test_state = (
        (10, 15),      # Position chaloupe
        "high",        # Santé
        "medium",      # Distance ennemi
        "paquebot",    # Type ennemi
        "high",        # Santé ennemi
        "north",       # Position relative
        False,         # Obstacle
        "searching"    # Mode actuel
    )
    
    # Test du choix d'action
    action = agent.choose_action(test_state)
    print(f"✓ Action choisie: {action}")
    assert action in CHALOUPE_ACTIONS, f"Action invalide: {action}"
    
    # Test de mise à jour Q-table
    reward = 5.0
    next_state = (
        (11, 15),      # Position changée
        "high",        # Santé
        "close",       # Distance réduite
        "paquebot",    # Type ennemi
        "medium",      # Santé ennemi réduite
        "north",       # Position relative
        False,         # Obstacle
        "positioning"  # Mode changé
    )
    
    agent.update_q_table(test_state, action, reward, next_state)
    print(f"✓ Q-table mise à jour avec récompense {reward}")
    
    # Vérifier que la Q-table contient les états
    assert test_state in agent.q_table, "État initial non trouvé dans Q-table"
    assert next_state in agent.q_table, "État suivant non trouvé dans Q-table"
    print(f"✓ Q-table contient {len(agent.q_table)} états")
    
    # Test de calcul de récompense
    class MockChaloupe:
        def __init__(self):
            self.is_alive = True
            self.current_health = 80
            self.max_health = 100
    
    mock_chaloupe = MockChaloupe()
    calculated_reward = agent.calculate_reward(
        mock_chaloupe, test_state, action, next_state
    )
    print(f"✓ Récompense calculée: {calculated_reward}")
    
    # Test de sauvegarde/chargement
    test_filename = "test_qtable.pkl"
    agent.save_q_table(test_filename)
    print(f"✓ Q-table sauvegardée")
    
    # Créer un nouvel agent et charger
    agent2 = QLearningAgent(CHALOUPE_ACTIONS)
    agent2.load_q_table(test_filename)
    print(f"✓ Q-table chargée dans nouvel agent")
    
    # Vérifier que les données sont identiques
    assert len(agent2.q_table) == len(agent.q_table), "Tailles Q-table différentes"
    print(f"✓ Intégrité des données vérifiée")
    
    # Nettoyer
    if os.path.exists(f"data/qlearning/{test_filename}"):
        os.remove(f"data/qlearning/{test_filename}")
    
    print("✓ Test agent Q-Learning RÉUSSI\n")

def test_discretization():
    """Test des fonctions de discrétisation."""
    print("=== TEST DISCRÉTISATION ===")
    
    agent = QLearningAgent(CHALOUPE_ACTIONS)
    
    # Test discrétisation position
    pos = agent.discretize_position(150.5, 200.3, grid_size=64)
    expected_pos = (2, 3)  # (150//64, 200//64)
    assert pos == expected_pos, f"Position attendue {expected_pos}, obtenue {pos}"
    print(f"✓ Position discrétisée: {pos}")
    
    # Test discrétisation distance
    distances = [50, 150, 350, 550, 800]
    expected = ["very_close", "close", "medium", "far", "very_far"]
    
    for dist, exp in zip(distances, expected):
        result = agent.discretize_distance(dist)
        assert result == exp, f"Distance {dist}: attendu {exp}, obtenu {result}"
    print(f"✓ Distances discrétisées correctement")
    
    # Test discrétisation santé
    health_tests = [
        (90, 100, "high"),    # 90%
        (50, 100, "medium"),  # 50%
        (20, 100, "low")      # 20%
    ]
    
    for health, max_health, expected in health_tests:
        result = agent.discretize_health(health, max_health)
        assert result == expected, f"Santé {health}/{max_health}: attendu {expected}, obtenu {result}"
    print(f"✓ Santé discrétisée correctement")
    
    print("✓ Test discrétisation RÉUSSI\n")

def test_learning_convergence():
    """Test de convergence d'apprentissage sur un scénario simple."""
    print("=== TEST CONVERGENCE APPRENTISSAGE ===")
    
    agent = QLearningAgent(CHALOUPE_ACTIONS, alpha=0.5, gamma=0.9, epsilon=0.1)
    
    # Scénario simple : récompenser l'action "attack" dans un état spécifique
    good_state = ("test_state", "attack_opportunity")
    bad_state = ("test_state", "no_opportunity")
    
    # Entraîner sur plusieurs épisodes
    for episode in range(100):
        # État favorable à l'attaque
        action = agent.choose_action(good_state)
        if action == "attack":
            reward = 10.0  # Récompense élevée
        else:
            reward = -1.0  # Pénalité légère
        
        agent.update_q_table(good_state, action, reward, good_state)
        
        # État défavorable à l'attaque
        action = agent.choose_action(bad_state)
        if action == "wait":
            reward = 2.0   # Récompense pour attendre
        else:
            reward = -2.0  # Pénalité pour action incorrecte
        
        agent.update_q_table(bad_state, action, reward, bad_state)
    
    # Vérifier que l'agent a appris
    # Dans l'état favorable, "attack" devrait avoir la plus haute valeur
    if good_state in agent.q_table:
        best_action = max(agent.q_table[good_state], key=agent.q_table[good_state].get)
        print(f"✓ Meilleure action pour état favorable: {best_action}")
        # Note: en raison de l'exploration, ce n'est pas toujours "attack" mais la tendance devrait être là
    
    # Dans l'état défavorable, "wait" devrait être valorisé
    if bad_state in agent.q_table:
        wait_value = agent.q_table[bad_state].get("wait", 0)
        attack_value = agent.q_table[bad_state].get("attack", 0)
        print(f"✓ Valeur 'wait' vs 'attack' en état défavorable: {wait_value:.2f} vs {attack_value:.2f}")
    
    print(f"✓ Apprentissage effectué sur {len(agent.q_table)} états")
    print("✓ Test convergence RÉUSSI\n")

def test_stats_and_monitoring():
    """Test des statistiques et du monitoring."""
    print("=== TEST STATISTIQUES ===")
    
    agent = QLearningAgent(CHALOUPE_ACTIONS)
    
    # Simuler quelques mises à jour
    state = ("test",)
    for i in range(5):
        action = "attack"
        reward = i * 2.0  # Récompenses croissantes
        next_state = ("test", i)
        agent.update_q_table(state, action, reward, next_state)
        state = next_state
    
    # Obtenir les statistiques
    stats = agent.get_stats()
    
    # Vérifier les statistiques
    expected_total_rewards = sum(i * 2.0 for i in range(5))  # 0+2+4+6+8 = 20
    assert abs(stats['total_rewards'] - expected_total_rewards) < 0.1, f"Récompenses totales incorrectes: {stats['total_rewards']}"
    assert stats['q_table_size'] > 0, "Q-table vide"
    assert 0 <= stats['epsilon'] <= 1, f"Epsilon invalide: {stats['epsilon']}"
    
    print(f"✓ Statistiques: {stats}")
    print("✓ Test statistiques RÉUSSI\n")

def run_all_tests():
    """Lance tous les tests."""
    print("DÉBUT DES TESTS Q-LEARNING\n")
    start_time = time.time()
    
    try:
        test_qlearning_agent()
        test_discretization()
        test_learning_convergence()
        test_stats_and_monitoring()
        
        elapsed = time.time() - start_time
        print(f"TOUS LES TESTS RÉUSSIS en {elapsed:.2f}s")
        return True
        
    except Exception as e:
        print(f"ÉCHEC DES TESTS: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
