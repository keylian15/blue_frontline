# Guide de Test Complet - Q-Learning pour Chaloupes

## Vue d'ensemble

Ce guide vous permet de tester toutes les fonctionnalités du système Q-Learning implémenté dans Blue Frontline pour l'unité Chaloupe. Suivez les étapes dans l'ordre pour valider le bon fonctionnement du système d'apprentissage automatique des chaloupes.

---

## Table des Matières

1. [Prérequis et Installation](#1-prérequis-et-installation)
2. [Commandes de Debug](#2-commandes-de-debug)
3. [Phase 1 : Vérification de l'Installation](#phase-1--vérification-de-linstallation)
4. [Phase 2 : Test des Commandes de Base](#phase-2--test-des-commandes-de-base)
5. [Phase 3 : Activation et Fonctionnement](#phase-3--activation-et-fonctionnement)
6. [Phase 4 : Test de Sauvegarde](#phase-4--test-de-sauvegarde)
7. [Phase 5 : Observation de l'Apprentissage](#phase-5--observation-de-lapprentissage)
8. [Phase 6 : Test de Persistance](#phase-6--test-de-persistance)
9. [Phase 7 : Tests Automatiques](#phase-7--tests-automatiques)
10. [Dépannage](#dépannage)

---

## 1. Prérequis et Installation

### Vérifications avant de commencer

- ✅ Python 3.8 ou supérieur installé
- ✅ Toutes les dépendances installées (`pip install -r requirements.txt`)
- ✅ Le jeu Blue Frontline se lance sans erreur
- ✅ Le dossier `data/qlearning/` existe (créé automatiquement au premier lancement)

### Structure des fichiers

Vérifiez que ces fichiers existent :
```
blue_frontline/
├── Class/units/
│   ├── Chaloupe.py            # Classe principale chaloupe
│   └── IA/
│       ├── ChaloupeQLearning.py  # Module Q-Learning principal
│       ├── ChaloupeAI.py          # IA intégrée
│       └── test_qlearning.py      # Tests automatiques
├── data/qlearning/            # Sauvegardes Q-tables
└── docs/
    └── Q-Learning_Test_Guide.md  # Ce guide
```

---

## 2. Commandes de Debug

### Touches Clavier (en jeu)

| Touche | Action | Description |
|--------|--------|-------------|
| **F1** | Toggle Q-Learning | Active/désactive le Q-Learning pour toutes les chaloupes |
| **F2** | Toggle Debug Visuel | Affiche/masque les informations visuelles au-dessus des chaloupes |
| **F3** | Statistiques | Affiche les statistiques Q-Learning dans la console |
| **F4** | Reset Q-Learning | Efface toutes les Q-tables et recommence l'apprentissage |
| **F5** | Sauvegarde Manuelle | Force la sauvegarde de toutes les Q-tables |

### Messages Console Attendus

**Messages importants conservés** :
- `[Q-Learning Debug] Q-Learning activé/désactivé pour X chaloupes` (F1)
- `[Visual Debug] Debug visuel activé/désactivé pour X chaloupes` (F2)
- `=== STATISTIQUES Q-LEARNING ===` (F3)
- `[Q-Learning Debug] Q-Learning reset pour X chaloupes` (F4)
- `[ChaloupeAI] Q-Learning activé pour chaloupe {team}` (démarrage)
- `[Q-Learning] Q-table chargée: X états, Y épisodes` (démarrage)

**Messages de spam supprimés** (pour alléger le terminal) :
- `[Q-Learning] Update: ...`
- `[Q-Learning] Exploitation: ...`
- `[Q-Learning] Q-table sauvegardée: ...`

---

## Phase 1 : Vérification de l'Installation

### Étape 1.1 : Lancement du jeu

```bash
cd blue_frontline
python main.py
```

**Résultat attendu** :
- Le jeu se lance sans erreur
- Le menu principal s'affiche

### Étape 1.2 : Vérification des messages de démarrage

**Observez la console au démarrage** :

✅ **Messages attendus** :
```
Chaloupe red : IA avancée activée
[ChaloupeAI] Q-Learning activé pour chaloupe red
[Q-Learning] Q-table chargée: X états, Y épisodes
```

❌ **Messages d'erreur à éviter** :
```
Module Q-Learning non disponible, utilisation de l'IA standard
ImportError: Cannot import ChaloupeQLearning
```

**Si erreur** : Vérifiez que `ChaloupeQLearning.py` existe dans `Class/units/IA/`

### Étape 1.3 : Démarrage d'une partie

1. Cliquez sur "Jouer"
2. Sélectionnez le mode de jeu
3. Attendez le chargement complet
4. Observez les chaloupes à l'écran

**Résultat attendu** :
- Les chaloupes apparaissent et se déplacent normalement
- Pas de crash ou de ralentissement

✅ **Phase 1 réussie si** : Le jeu fonctionne normalement avec Q-Learning actif en arrière-plan

---

## Phase 2 : Test des Commandes de Base

### Étape 2.1 : Test F1 (Toggle Q-Learning)

**Action** : Appuyez sur **F1** pendant la partie

**Résultats attendus** :
```
[Q-Learning Debug] Q-Learning désactivé pour X chaloupes
```

**Action** : Appuyez à nouveau sur **F1**

**Résultats attendus** :
```
[Q-Learning Debug] Q-Learning activé pour X chaloupes
```

✅ **Test réussi si** : Le message s'affiche à chaque pression, alternant entre activé/désactivé

### Étape 2.2 : Test F2 (Toggle Debug Visuel)

**Action** : Appuyez sur **F2** pendant la partie

**Résultats attendus** :
```
[Visual Debug] Debug visuel activé pour X chaloupes
```

**Observation visuelle** :
- Recherchez les chaloupes à l'écran
- Des informations textuelles devraient apparaître au-dessus d'elles :
  - État IA (Recherche/Position/Attaque/Retraite)
  - Action Q-Learning (si Q-Learning activé)
  - Récompense (R: +2.0)
  - Epsilon (ε: 0.150)

**Note** : Si vous ne voyez pas les informations visuelles, ce n'est pas bloquant. Le Q-Learning fonctionne en arrière-plan. Passez à l'étape suivante.

### Étape 2.3 : Test F3 (Statistiques)

**Action** : Appuyez sur **F3** pendant la partie

**Résultats attendus dans la console** :
```
=== STATISTIQUES Q-LEARNING ===
Chaloupe red #1:
  - Épisodes: 0
  - Récompenses totales: 150.5
  - Récompense moyenne: 150.50
  - Epsilon (exploration): 0.180
  - Taille Q-table: 45 états
  - Dernière récompense: 2.0
Chaloupe red #2:
  [...]
=================================
```

**Vérifications** :
- ✅ Chaque chaloupe vivante apparaît dans la liste
- ✅ Les récompenses totales sont positives et augmentent
- ✅ L'epsilon diminue progressivement (exploration → exploitation)
- ✅ La taille de la Q-table augmente (nouveaux états découverts)

### Étape 2.4 : Test F4 (Reset)

**Action** : Appuyez sur **F4** pendant la partie

**Résultats attendus** :
```
[Q-Learning Debug] Q-Learning reset pour X chaloupes
```

**Vérification** : Appuyez sur **F3** pour voir les statistiques
- ✅ Récompenses totales = 0 ou très faible
- ✅ Epsilon remis à 0.2
- ✅ Taille Q-table réduite ou vidée

### Étape 2.5 : Test F5 (Sauvegarde Manuelle)

**Action** : Appuyez sur **F5** pendant la partie

**Résultats attendus** :
- Pas de message console (spam supprimé)
- Les fichiers dans `data/qlearning/` sont mis à jour

**Vérification** :
```bash
ls data/qlearning/
```

**Fichiers attendus** :
- `chaloupe_red_qtable.pkl`
- `chaloupe_green_qtable.pkl`

✅ **Phase 2 réussie si** : Toutes les commandes F1-F5 fonctionnent correctement

---

## Phase 3 : Activation et Fonctionnement

### Étape 3.1 : Observer le Q-Learning en action

**Préparation** :
1. Démarrez une nouvelle partie
2. Assurez-vous que Q-Learning est activé (F1 si nécessaire)
3. Appuyez sur F3 pour voir l'état initial

**Observation initiale (temps T=0)** :
```
Chaloupe red #1:
  - Récompenses totales: ~50-100
  - Epsilon: ~0.15-0.20 (exploration moyenne)
  - Taille Q-table: ~10-30 états
```

**Attendez 2-3 minutes de jeu...**

**Observation après 2-3 min (temps T=3min)** :
Appuyez sur F3 à nouveau

**Résultats attendus** :
- ✅ **Récompenses totales** : Augmentation de 100-300 points
- ✅ **Epsilon** : Diminution vers 0.01-0.05
- ✅ **Taille Q-table** : Augmentation de 20-50 nouveaux états

### Étape 3.2 : Comprendre les actions Q-Learning

**Actions possibles** observables (via logs ou debug visuel) :
- `move_to_enemy` : Se déplacer vers la cible
- `retreat` : Se replier hors de portée
- `orbit` : Orbiter autour de la cible
- `attack` : Attaquer la cible
- `change_angle` : Changer d'angle d'approche
- `hide` : Se cacher derrière obstacle
- `wait` : Attendre/observer

**Comportement attendu** :
- Début : Actions variées (exploration)
- Après quelques minutes : Actions plus cohérentes (exploitation)

### Étape 3.3 : Système de récompenses

**Observez les dernières récompenses** (via F3) :

**Récompenses positives attendues** :
- `+10.0` : Toucher un ennemi (rare)
- `+3.0` : Se rapprocher pour attaquer
- `+2.0` : Rester en vie (fréquent)
- `+1.0` : Comportement tactique

**Récompenses négatives attendues** :
- `-10.0` : Être détruit (rare)
- `-5.0` : Perdre de la santé
- `-3.0` : Position dangereuse

✅ **Phase 3 réussie si** : 
- Récompenses augmentent progressivement
- Epsilon diminue au fil du temps
- Q-table s'enrichit de nouveaux états

---

## Phase 4 : Test de Sauvegarde

### Étape 4.1 : Sauvegarde automatique

**Le système sauvegarde automatiquement :**
- Toutes les 0.5 secondes pendant le jeu (sauvegarde silencieuse)
- À la destruction d'une chaloupe
- À la fin d'une partie

**Vérification** :
1. Jouez pendant 2-3 minutes
2. Appuyez sur F3 pour noter les statistiques actuelles
3. Quittez le jeu proprement (menu → quitter)

### Étape 4.2 : Sauvegarde manuelle

**Test de sauvegarde forcée** :
1. Pendant une partie active
2. Appuyez sur **F5**
3. Vérifiez l'horodatage des fichiers :

```bash
ls -l data/qlearning/
```

**Résultat attendu** :
- Les fichiers `.pkl` ont été modifiés récemment

### Étape 4.3 : Vérification de l'intégrité

**Ouvrez le fichier de sauvegarde avec Python** :

```python
import pickle

with open('data/qlearning/chaloupe_red_qtable.pkl', 'rb') as f:
    data = pickle.load(f)
    print(f"Q-table: {len(data['q_table'])} états")
    print(f"Récompenses: {data['total_rewards']}")
    print(f"Epsilon: {data['epsilon']}")
```

**Résultat attendu** :
- Données cohérentes avec les statistiques F3
- Pas d'erreur de chargement

✅ **Phase 4 réussie si** : Les sauvegardes fonctionnent automatiquement et manuellement

---

## Phase 5 : Observation de l'Apprentissage

### Étape 5.1 : Test d'apprentissage court terme (5 minutes)

**Protocole** :
1. Réinitialisez le Q-Learning : Appuyez sur **F4**
2. Notez les statistiques initiales : Appuyez sur **F3**
3. Jouez pendant **5 minutes** sans interruption
4. Notez les statistiques finales : Appuyez sur **F3**

**Exemple de résultats attendus** :

**T=0 min** :
```
Chaloupe red #1:
  - Récompenses totales: 0.0
  - Epsilon: 0.200
  - Taille Q-table: 0 états
```

**T=5 min** :
```
Chaloupe red #1:
  - Récompenses totales: 500-800
  - Epsilon: 0.010-0.050
  - Taille Q-table: 100-200 états
```

**Indicateurs de succès** :
- ✅ Augmentation des récompenses (≥400 points)
- ✅ Diminution epsilon (≤0.05)
- ✅ Croissance Q-table (≥80 états)

### Étape 5.2 : Test d'apprentissage long terme (10 minutes)

**Protocole** :
1. Continuez la partie précédente (ou démarrez une nouvelle)
2. Jouez pendant **10 minutes** au total
3. Relevez les statistiques toutes les **2 minutes** :

**Tableau de suivi** :

| Temps | Récompenses | Epsilon | Q-table | Dernière Récompense |
|-------|-------------|---------|---------|---------------------|
| 0 min | ~0-100      | ~0.20   | ~10-20  | Variable            |
| 2 min | ~300-500    | ~0.10   | ~50-100 | +2.0 typique        |
| 4 min | ~600-900    | ~0.05   | ~100-150| +2.0 typique        |
| 6 min | ~900-1300   | ~0.02   | ~150-200| +2.0 typique        |
| 8 min | ~1200-1700  | ~0.01   | ~180-250| +2.0 typique        |
| 10 min| ~1500-2100  | ~0.01   | ~200-300| +2.0 typique        |

**Observations attendues** :
- **Courbe de récompenses** : Croissance continue puis stabilisation
- **Epsilon** : Décroissance rapide puis plateau à ~0.01
- **Q-table** : Croissance puis stabilisation (tous les états courants découverts)

### Étape 5.3 : Comparaison Rouge vs Vert

**Appuyez sur F3 après 10 minutes** :

**Résultats typiques** :
- **Chaloupes Rouges** : Récompenses ~1800-2100 (performance supérieure)
- **Chaloupes Vertes** : Récompenses ~1400-1900 (apprentissage plus lent)

**Explication** : Les deux équipes apprennent indépendamment selon leurs expériences

✅ **Phase 5 réussie si** :
- Augmentation continue des récompenses
- Epsilon converge vers 0.01
- Q-table se stabilise vers 200-300 états
- Comportement des chaloupes devient plus cohérent

---

## Phase 6 : Test de Persistance

### Étape 6.1 : Sauvegarde de l'état d'apprentissage

**Après la Phase 5 (10+ minutes de jeu)** :
1. Appuyez sur **F3** pour noter les statistiques finales
2. Appuyez sur **F5** pour forcer la sauvegarde
3. Notez les valeurs importantes :
   - Récompenses totales de chaque chaloupe
   - Epsilon final
   - Taille Q-table

**Exemple de notes** :
```
Chaloupe red #1:
  - Récompenses: 2066.5
  - Epsilon: 0.010
  - Q-table: 249 états
```

### Étape 6.2 : Redémarrage et vérification du chargement

**Protocole** :
1. **Fermez complètement le jeu** (ne pas juste quitter la partie)
2. **Attendez 5 secondes**
3. **Relancez le jeu** : `python main.py`
4. **Observez la console au démarrage**

**Messages attendus au lancement** :
```
Chaloupe red : IA avancée activée
[ChaloupeAI] Q-Learning activé pour chaloupe red
[Q-Learning] Q-table chargée: 249 états, 0 épisodes
```

**Vérification importante** :
- ✅ Nombre d'états chargés correspond aux notes précédentes
- ✅ Pas d'erreur de chargement

### Étape 6.3 : Validation des données rechargées

**Démarrez une nouvelle partie et immédiatement appuyez sur F3** :

**Résultats attendus** :
```
=== STATISTIQUES Q-LEARNING ===
Chaloupe red #1:
  - Épisodes: 0
  - Récompenses totales: 2066.5 (ou valeur proche)
  - Epsilon: 0.010 (ou valeur proche)
  - Taille Q-table: 249 états (ou valeur proche)
  - Dernière récompense: 0.0 (normal au démarrage)
```

**Vérifications critiques** :
- ✅ Récompenses totales = valeur sauvegardée (±10 points)
- ✅ Epsilon = valeur sauvegardée (±0.005)
- ✅ Q-table = taille sauvegardée (±5 états)
- ⚠️ Dernière récompense = 0.0 (normal, aucune action encore)

### Étape 6.4 : Test de continuité d'apprentissage

**Après chargement, jouez encore 2-3 minutes** :

**Appuyez sur F3 et observez** :
- ✅ Récompenses continuent d'augmenter depuis la valeur rechargée
- ✅ Epsilon reste stable (~0.01)
- ✅ Q-table peut encore croître légèrement (nouveaux états)

**Exemple** :
```
Avant (rechargé): 2066.5 récompenses
Après 3 min:     2200.0 récompenses (+133.5)
```

✅ **Phase 6 réussie si** :
- Toutes les données sont rechargées correctement
- L'apprentissage continue depuis le point de sauvegarde
- Pas de perte de progression

---

## Phase 7 : Tests Automatiques

### Étape 7.1 : Exécution des tests unitaires

**Lancez le script de test** :
```bash
# Depuis la racine du projet blue_frontline/
python Class/units/IA/test_qlearning.py
```

**Ou depuis le dossier IA** :
```bash
cd Class/units/IA
python test_qlearning.py
```

**Tests exécutés** :
1. **Test agent Q-Learning** : Création, actions, mise à jour
2. **Test discrétisation** : Position, distance, santé
3. **Test convergence** : Apprentissage sur scénario contrôlé
4. **Test statistiques** : Métriques et monitoring

**Résultat attendu** :
```
=== TEST AGENT Q-LEARNING ===
✓ Agent créé avec 7 actions
✓ Action choisie: move_to_enemy
✓ Q-table mise à jour avec récompense 5.0
✓ Q-table contient 2 états
✓ Récompense calculée: 2.0
✓ Q-table sauvegardée
✓ Q-table chargée dans nouvel agent
✓ Intégrité des données vérifiée
✓ Test agent Q-Learning RÉUSSI

=== TEST DISCRÉTISATION ===
✓ Position discrétisée: (2, 3)
✓ Distances discrétisées correctement
✓ Santé discrétisée correctement
✓ Test discrétisation RÉUSSI

=== TEST CONVERGENCE APPRENTISSAGE ===
✓ Meilleure action pour état favorable: attack
✓ Valeur 'wait' vs 'attack' en état défavorable: 2.00 vs -2.00
✓ Apprentissage effectué sur 2 états
✓ Test convergence RÉUSSI

=== TEST STATISTIQUES ===
✓ Statistiques: {...}
✓ Test statistiques RÉUSSI

🎉 TOUS LES TESTS RÉUSSIS en X.XXs
```

### Étape 7.2 : Interprétation des résultats

**Si tous les tests passent** :
- ✅ Module Q-Learning fonctionnel
- ✅ Algorithmes d'apprentissage corrects
- ✅ Sauvegarde/chargement opérationnels
- ✅ Statistiques précises

**Si un test échoue** :
- ❌ Vérifier les messages d'erreur
- ❌ Consulter la section [Dépannage](#dépannage)

✅ **Phase 7 réussie si** : Tous les tests automatiques passent avec succès

---

## Dépannage

### Problème 1 : Q-Learning ne semble pas apprendre

**Symptômes** :
- Récompenses n'augmentent pas
- Epsilon ne diminue pas
- Q-table reste petite

**Vérifications** :
1. **Q-Learning activé ?** Appuyez sur F1 et vérifiez le message
2. **Chaloupes survivent ?** Si détruites trop vite, pas d'apprentissage
3. **Assez de temps ?** Attendez au moins 5-10 minutes

**Solutions** :
```python
# Dans ChaloupeQLearning.py, augmentez le taux d'apprentissage
alpha = 0.2  # Au lieu de 0.1
```

### Problème 2 : Comportement erratique des chaloupes

**Symptômes** :
- Mouvements incohérents
- Actions aléatoires persistantes
- Performance décroissante

**Cause probable** : Exploration trop élevée

**Solution** :
```python
# Dans ChaloupeQLearning.py
epsilon = 0.05  # Réduire l'exploration initiale
```

Ou appuyez sur **F1** pour désactiver temporairement Q-Learning

### Problème 3 : Erreurs de sauvegarde

**Symptômes** :
```
[Q-Learning] Erreur sauvegarde: Permission denied
[Q-Learning] Erreur sauvegarde: File not found
```

**Solutions** :
1. **Créez le dossier manuellement** :
```bash
mkdir -p data/qlearning
```

2. **Vérifiez les permissions** :
```bash
chmod 755 data/qlearning
```

### Problème 4 : Données ne se chargent pas

**Symptômes** :
```
[Q-Learning] Fichier chaloupe_red_qtable.pkl non trouvé
```

**Vérification** :
```bash
ls data/qlearning/
```

**Si fichiers manquants** :
- Normal pour la première exécution
- Jouez 5-10 minutes pour générer des données
- Appuyez sur F5 pour forcer la sauvegarde

### Problème 5 : Tests automatiques échouent

**Si `Class/units/IA/test_qlearning.py` échoue** :

1. **Vérifiez l'environnement** :
```bash
python --version  # Python 3.8+
pip list | grep numpy  # Vérifiez numpy installé
```

2. **Réinstallez les dépendances** :
```bash
pip install -r requirements.txt --force-reinstall
```

3. **Vérifiez les imports** :
```python
# Test manuel depuis la racine du projet
python -c "from Class.units.IA.ChaloupeQLearning import QLearningAgent; print('OK')"
```

4. **Exécutez depuis le bon répertoire** :
```bash
# Assurez-vous d'être dans blue_frontline/
cd c:\Users\thoma\OneDrive\Bureau\Blue_frontline\blue_frontline\blue_frontline
python Class/units/IA/test_qlearning.py
```

### Problème 6 : Console spam de messages

**Si trop de messages Q-Learning** :

**Solution** : Les messages de spam ont été supprimés dans la dernière version.

**Vérification** :
- Vous devriez voir SEULEMENT les messages F1-F5
- PAS de messages `[Q-Learning] Update: ...`
- PAS de messages `[Q-Learning] Exploitation: ...`

**Si spam persiste** :
```python
# Dans ChaloupeQLearning.py, ligne ~45
self.debug_enabled = False  # Assurer que c'est False
```

---

## Récapitulatif des Phases de Test

| Phase | Objectif | Durée | Succès si... |
|-------|----------|-------|--------------|
| **Phase 1** | Installation | 5 min | Jeu lance sans erreur, Q-Learning détecté |
| **Phase 2** | Commandes | 10 min | F1-F5 fonctionnent toutes correctement |
| **Phase 3** | Fonctionnement | 5 min | Récompenses augmentent, epsilon diminue |
| **Phase 4** | Sauvegarde | 5 min | Fichiers .pkl créés et à jour |
| **Phase 5** | Apprentissage | 10 min | Performance s'améliore progressivement |
| **Phase 6** | Persistance | 5 min | Données rechargées correctement |
| **Phase 7** | Tests auto | 2 min | Tous les tests passent |
| **Total** | - | **~42 min** | Toutes les phases validées |

---

## Indicateurs de Succès Global

### ✅ Q-Learning Complètement Fonctionnel

**Vous avez réussi si** :

1. **Installation** :
   - ✅ Jeu se lance sans erreur
   - ✅ Messages Q-Learning au démarrage

2. **Commandes** :
   - ✅ F1-F5 répondent correctement
   - ✅ Messages appropriés dans la console

3. **Apprentissage** :
   - ✅ Récompenses augmentent de 0 → 2000+ en 10 min
   - ✅ Epsilon diminue de 0.20 → 0.01
   - ✅ Q-table croît de 0 → 200+ états

4. **Persistance** :
   - ✅ Données sauvegardées automatiquement
   - ✅ Données rechargées au redémarrage
   - ✅ Apprentissage continue après redémarrage

5. **Tests** :
   - ✅ Tests automatiques passent tous

6. **Performance** :
   - ✅ Pas de ralentissement du jeu
   - ✅ Console propre (pas de spam)
   - ✅ Comportement des chaloupes cohérent

---

## Paramètres Avancés

### Modifier les paramètres d'apprentissage

**Fichier** : `Class/units/IA/ChaloupeQLearning.py`

```python
class QLearningAgent:
    def __init__(self, actions, alpha=0.1, gamma=0.9, epsilon=0.2):
        # alpha: Taux d'apprentissage (0.01-0.5)
        #   0.01 = lent mais stable
        #   0.3  = rapide mais instable
        
        # gamma: Facteur de remise (0.8-0.99)
        #   0.8  = privilégie récompenses immédiates
        #   0.99 = privilégie récompenses futures
        
        # epsilon: Exploration initiale (0.1-0.5)
        #   0.1  = peu d'exploration
        #   0.5  = beaucoup d'exploration
        
        self.epsilon_decay = 0.995  # Vitesse de décroissance
        self.epsilon_min = 0.01     # Exploration minimale
```

### Modifier les récompenses

**Fichier** : `Class/units/IA/ChaloupeQLearning.py`, méthode `calculate_reward()`

```python
# Récompenses actuelles
hit_enemy = 10.0         # Toucher un ennemi
survive = 2.0            # Rester en vie
take_damage = -5.0       # Perdre de la santé
destroyed = -10.0        # Être détruit
tactical_behavior = 1.0  # Bon comportement tactique
```

### Modifier la fréquence de mise à jour

**Fichier** : `Class/units/IA/ChaloupeAI.py`

```python
# Ligne ~70
self.qlearning_update_interval = 0.5  # En secondes
# 0.5 = 2 mises à jour par seconde (défaut)
# 1.0 = 1 mise à jour par seconde (plus lent)
# 0.2 = 5 mises à jour par seconde (plus rapide)
```

---

## Conclusion

Ce guide vous a permis de tester systématiquement toutes les fonctionnalités du système Q-Learning. Si toutes les phases sont validées, le Q-Learning est **complètement opérationnel** dans Blue Frontline.

### Prochaines étapes possibles

1. **Optimisation** : Ajuster les paramètres selon vos préférences
2. **Extension** : Ajouter de nouveaux états ou actions
3. **Analyse** : Étudier les Q-tables pour comprendre les stratégies apprises
4. **Tournois** : Comparer différentes configurations Q-Learning

### Ressources supplémentaires

- `docs/Q-Learning_Guide.md` : Guide d'utilisation détaillé
- `Q-Learning_Implementation_Report.md` : Documentation technique
- `docs/Q-Learning_Debug_Commands.md` : Référence des commandes
- `Class/units/IA/test_qlearning.py` : Tests automatiques avec code source

---

**Bon test et bon apprentissage automatique ! 🚀🤖**
