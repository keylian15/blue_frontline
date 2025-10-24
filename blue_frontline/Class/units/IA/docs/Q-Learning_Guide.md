# Guide d'utilisation du Q-Learning pour les Chaloupes - Blue Frontline

## Vue d'ensemble

Le système Q-Learning a été intégré dans l'IA des chaloupes pour permettre un apprentissage automatique et une amélioration continue des tactiques de combat. Ce guide explique comment utiliser et configurer cette fonctionnalité.

## Fonctionnement du Q-Learning

### Principe
Le Q-Learning permet aux chaloupes d'apprendre les meilleures actions à effectuer selon l'état du jeu (position des ennemis, santé, etc.). Au fil du temps, elles deviennent plus efficaces dans leurs attaques éclairs.

### États analysés
- Position de la chaloupe (discrétisée par zones)
- Santé de la chaloupe (élevée/moyenne/faible)  
- Distance à l'ennemi (très proche/proche/moyen/loin/très loin)
- Type d'ennemi (paquebot, bateau, chaloupe, etc.)
- Position relative de l'ennemi (nord/sud/est/ouest)
- Présence d'obstacles
- Mode IA actuel (recherche/positionnement/attaque/retraite)

### Actions possibles
- `move_to_enemy` : Se déplacer vers la cible
- `retreat` : Se déplacer hors de portée
- `orbit` : Orbiter autour de la cible
- `attack` : Attaquer la cible
- `change_angle` : Changer d'angle d'approche
- `hide` : Se cacher derrière un obstacle
- `wait` : Attendre/observer

### Système de récompenses
- **+10** : Toucher un ennemi
- **+5** : Éviter des dégâts
- **+3** : Se rapprocher pour attaquer
- **+2** : Rester en vie, maintenir distance sécurisée
- **+1** : Comportement tactique (orbite)
- **-3** : S'approcher dangereusement
- **-5** : Perdre de la santé
- **-10** : Être détruit

## Commandes de contrôle

### Touches de debug en jeu
- **F1** : Active/désactive le Q-Learning pour toutes les chaloupes
- **F2** : Sauvegarde le progrès Q-Learning de toutes les chaloupes
- **F3** : Affiche les statistiques Q-Learning dans la console
- **F4** : Reset le Q-Learning (efface la Q-table)

### Informations à l'écran
Quand une chaloupe est sélectionnée, les informations Q-Learning s'affichent :
- Action Q-Learning actuelle
- Dernière récompense (verte si positive, rouge si négative)
- Taux d'exploration (epsilon)
- Lignes colorées vers la cible selon l'action (rouge=attaque, cyan=retraite, magenta=orbite)

## Configuration avancée

### Paramètres Q-Learning modifiables
Dans `ChaloupeQLearning.py` :
```python
alpha=0.1      # Taux d'apprentissage (0-1)
gamma=0.9      # Facteur de remise (0-1)
epsilon=0.2    # Taux d'exploration initial (0-1)
```

### Fréquence de mise à jour
Dans `ChaloupeAI.py` :
```python
qlearning_update_interval = 0.5  # Secondes entre les mises à jour
```

## Sauvegarde et persistance

### Fichiers de sauvegarde
- `data/qlearning/chaloupe_red_qtable.pkl` : Q-table pour les chaloupes rouges
- `data/qlearning/chaloupe_green_qtable.pkl` : Q-table pour les chaloupes vertes

### Sauvegarde automatique
- Sauvegarde automatique tous les 100 épisodes
- Sauvegarde manuelle avec **F2**
- Chargement automatique au démarrage du jeu

## Statistiques et monitoring

### Métriques disponibles
- **total_episodes** : Nombre d'épisodes d'apprentissage
- **total_rewards** : Récompenses cumulées
- **avg_reward** : Récompense moyenne par épisode
- **epsilon** : Taux d'exploration actuel
- **q_table_size** : Nombre d'états appris
- **last_reward** : Dernière récompense reçue

### Interprétation
- Un `avg_reward` qui augmente indique un apprentissage réussi
- Un `epsilon` qui diminue montre que l'IA explore moins et exploite plus
- Une `q_table_size` qui croît indique la découverte de nouveaux états

## Optimisation des performances

### Réglages recommandés
- **Début d'apprentissage** : `epsilon=0.3` (exploration élevée)
- **Apprentissage avancé** : `epsilon=0.1` (plus d'exploitation)
- **Production** : `epsilon=0.05` (exploitation maximale)

### Vitesse d'apprentissage
- `alpha=0.1` : Apprentissage lent mais stable
- `alpha=0.3` : Apprentissage rapide mais instable
- `alpha=0.05` : Apprentissage très lent mais précis

## Dépannage

### Problèmes courants
1. **L'IA ne semble pas apprendre**
   - Vérifier que le Q-Learning est activé (F1)
   - Augmenter le taux d'apprentissage (alpha)
   - Reset la Q-table (F4) si corrompue

2. **Comportement erratique**
   - Taux d'exploration trop élevé
   - Réduire epsilon ou laisser plus de temps

3. **Pas de sauvegarde**
   - Vérifier que le dossier `data/qlearning/` existe
   - Permissions d'écriture sur le dossier

### Messages de debug
Les messages Q-Learning apparaissent dans la console avec le préfixe `[Q-Learning]`.

## Développement et extension

### Ajouter de nouveaux états
Modifier la méthode `get_state()` dans `ChaloupeQLearning.py`.

### Ajouter de nouvelles actions
1. Ajouter l'action dans `CHALOUPE_ACTIONS`
2. Implémenter l'action dans `_apply_qlearning_action()`

### Modifier les récompenses
Ajuster la méthode `calculate_reward()` selon les comportements souhaités.

## Intégration avec l'IA existante

Le Q-Learning fonctionne en complément de l'IA tactique existante :
- L'IA tactique gère les mouvements précis et la logique de combat
- Le Q-Learning influence les décisions stratégiques de haut niveau
- Fallback automatique vers l'IA standard si Q-Learning désactivé

Cette approche hybride garantit des performances robustes tout en permettant l'apprentissage continu.