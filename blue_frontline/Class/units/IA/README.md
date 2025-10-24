# Dossier IA - Intelligence Artificielle des Chaloupes

## Contenu

Ce dossier contient tous les modules liés à l'intelligence artificielle des chaloupes de Blue Frontline.

### Fichiers

#### Modules principaux

- **`ChaloupeQLearning.py`** : Module Q-Learning (apprentissage par renforcement)
  - Classe `QLearningAgent` : Agent d'apprentissage automatique
  - Gestion des états, actions, récompenses
  - Sauvegarde/chargement des Q-tables
  
- **`ChaloupeAI.py`** : Système IA avancé pour les chaloupes
  - Intégration du Q-Learning avec l'IA tactique
  - Modes : Recherche, Positionnement, Attaque éclair, Retraite
  - Gestion des décisions et comportements

#### Tests

- **`test_qlearning.py`** : Tests automatiques du système Q-Learning
  - Test de l'agent Q-Learning
  - Test de discrétisation des états
  - Test de convergence d'apprentissage
  - Test des statistiques
  
  **Usage** :
  ```bash
  # Depuis la racine du projet (blue_frontline/)
  python Class/units/IA/test_qlearning.py
  ```

#### Configuration

- **`__init__.py`** : Configuration du package IA

---

## Architecture

```
IA/
├── ChaloupeQLearning.py   # Apprentissage automatique
├── ChaloupeAI.py          # IA tactique + Q-Learning
├── test_qlearning.py      # Tests unitaires
└── __init__.py            # Package config
```

### Intégration

La classe `Chaloupe` (dans `Class/units/Chaloupe.py`) utilise ces modules :
1. Instancie `ChaloupeAI` qui gère la logique tactique
2. `ChaloupeAI` utilise `QLearningAgent` pour l'apprentissage
3. L'IA hybride combine tactiques prédéfinies + apprentissage

---

## Documentation

- **Guide de test** : `docs/Q-Learning_Test_Guide.md`
- **Guide d'utilisation** : `docs/Q-Learning_Guide.md`
- **Rapport technique** : `Q-Learning_Implementation_Report.md`
- **Commandes debug** : `docs/Q-Learning_Debug_Commands.md`

---

## Tests

Pour valider le bon fonctionnement de l'IA :

```bash
# Test automatique
python Class/units/IA/test_qlearning.py

# Test en jeu
python main.py
# Puis utiliser les touches F1-F5 pour le debug Q-Learning
```

---

**Dernière mise à jour** : Octobre 2025
