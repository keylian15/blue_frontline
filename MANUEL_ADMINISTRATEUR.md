# MANUEL ADMINISTRATEUR
## Blue Frontline - Jeu Naval Stratégique

---

**Version :** 1.0  
**Date :** 30 septembre 2025  
**Auteur :** CHAMPY Thomas 
**Destinataires :** Professeurs, Administrateurs système, DevOps, Développeurs

---

## TABLE DES MATIÈRES

1. [Introduction](#1-introduction)
2. [Description du système](#2-description-du-système)
3. [Installation](#3-installation)
4. [Configuration](#4-configuration)
5. [Exploitation](#5-exploitation)
6. [Maintenance](#6-maintenance)
7. [Annexes](#7-annexes)

---

## 1. INTRODUCTION

### 1.1 Objectif du document
Ce manuel administrateur fournit les procédures techniques nécessaires pour l'installation, la configuration, l'exploitation et la maintenance du jeu **Blue Frontline**, un jeu naval stratégique développé en Python avec Pygame.

### 1.2 Public cible
- Professeurs
- Administrateurs système
- Ingénieurs DevOps
- Développeurs souhaitant déployer ou maintenir l'application
- Exploitants techniques

### 1.3 Prérequis
- Connaissances de base en Python
- Familiarité avec les systèmes Windows/Linux
- Notions de gestion de versions Git

---

## 2. DESCRIPTION DU SYSTÈME

### 2.1 Architecture générale
Blue Frontline est une application standalone Python utilisant l'architecture MVC :

```
blue_frontline/
├── main.py                 # Point d'entrée principal
├── Global.py              # Variables globales et constantes
├── Utils.py               # Utilitaires partagés
├── requirements.txt       # Dépendances Python
├── Class/                 # Classes métier
│   ├── Game.py           # Moteur de jeu principal
│   ├── menu.py           # Interface menu
│   ├── units/            # Unités de combat
│   └── ...
├── assets/               # Ressources graphiques
├── blue_frontline_sounds/ # Ressources audio
└── output/               # Builds compilés
```

### 2.2 Composants principaux
- **Moteur de jeu** : Pygame 2.5.2+
- **Gestion des cartes** : PyTMX pour fichiers Tiled
- **Système de succès** : Persistance JSON
- **Audio** : Mixer Pygame
- **Interface** : Rendu 2D temps réel

### 2.3 Flux de données
```
Utilisateur → Interface Menu → Game Engine → Rendu Pygame → Écran
        ↓
      Système de succès → achievements.json
        ↓
      Chargement dynamique des ressources (assets, sons)
```

---

## 3. INSTALLATION

### 3.1 Prérequis système

**Configuration minimale :**
- OS : Windows 10+ / Linux Ubuntu 18.04+ / macOS 10.14+
- Python : 3.8+
- RAM : 2 GB minimum
- Espace disque : 500 MB
- Résolution : 1024x768 minimum

**Configuration recommandée :**
- Python : 3.10+
- RAM : 4 GB ou plus
### 3.2 Dépendances

**Dépendances Python requises :**
```txt
pygame==2.5.2
pytmx==3.32
pyscroll
perlin-noise
shapely
auto-py-to-exe
pyinstaller
```

### 3.3 Procédure d'installation

#### Étape 1 : Clonage du dépôt
```bash
git clone https://github.com/keylian15/blue_frontline.git
cd blue_frontline
git checkout main  # Branche principale recommandée
```

#### Étape 2 : Environnement virtuel (recommandé)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

#### Étape 3 : Installation des dépendances
```bash
pip install -r docs/requirements.txt  # Chemin recommandé
```

#### Étape 4 : Vérification de l'installation
```bash
python main.py
```

### 3.4 Erreurs courantes d'installation

| Erreur | Cause | Solution |
|--------|-------|----------|
| `ModuleNotFoundError: pygame` | Dépendances manquantes | `pip install pygame` |
| `No module named 'pytmx'` | PyTMX non installé | `pip install pytmx` |
| `Permission denied` | Droits insuffisants | Exécuter en administrateur |

---

## 4. CONFIGURATION

### 4.1 Fichiers de configuration

#### Global.py
Variables de configuration principales :
```python
# Résolution d'écran (configurable dans le menu ou dans le code)
SCREEN_WIDTH = 1366  # Peut être modifié dans le menu ou main.py
SCREEN_HEIGHT = 768

# Couleurs système
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)

# Chemins des assets
ASSETS_PATH = "assets/"
SOUNDS_PATH = "blue_frontline_sounds/"
```

#### map.tmx
Carte de jeu au format Tiled contenant :
- Couches de terrain
- Objets de positionnement des plateformes
- Zones de spawn des unités

### 4.2 Configuration des succès

Le système de succès utilise `achievements.json` :
```json
{
  "unlocked_achievements": ["first_unit", "unit_collector"],
  "stats": {
    "units_created": {"chaloupe": 5, "bateau": 2},
    "units_killed": {"chaloupe": 3},
    "total_petrole_spent": 150,
    "games_won": 2
  }
}
```

### 4.3 Variables d'environnement

Aucune variable d'environnement requise par défaut. Options disponibles :
- `PYGAME_HIDE_SUPPORT_PROMPT=1` : Masque les messages Pygame
- `PYTHONPATH` : Pour imports personnalisés

---

## 5. EXPLOITATION

### 5.1 Lancement de l'application

#### Mode normal
```bash
python main.py
```

#### Mode debug
```bash
python -u main.py  # Sortie non bufferisée
```

### 5.2 Supervision

#### Logs système
Les logs sont affichés dans la console :
```
pygame 2.5.2 (SDL 2.28.3, Python 3.12.6)
Hello from the pygame community.
Plateforme red créée à (144.0, 1488.0)
Plateforme green créée à (3696.0, 1488.0)
[SUCCÈS] Débloqué: Premier Sang - Détruire votre première unité ennemie
```

#### Monitoring des performances
```python
# Dans Game.py - Monitoring FPS
clock = pygame.time.Clock()
fps = clock.get_fps()
```

### 5.3 Arrêt de l'application

- **Normal** : Menu Quitter ou Alt+F4
- **Forcé** : Ctrl+C dans le terminal
- **Urgence** : Gestionnaire des tâches

### 5.4 Fichiers de données

| Fichier | Description | Sauvegarde |
|---------|-------------|------------|
| `achievements.json` | Progression succès | Automatique |
| `map.tmx` | Carte de jeu | Statique |
| `assets/*` | Ressources graphiques | Statique |

---

## 6. MAINTENANCE

### 6.1 Sauvegarde

#### Données utilisateur
```bash
# Sauvegarde progression
cp achievements.json backup/achievements_$(date +%Y%m%d).json

# Sauvegarde complète
tar -czf blue_frontline_backup_$(date +%Y%m%d).tar.gz .
```

#### Restauration
```bash
# Restaurer progression
cp backup/achievements_20250930.json achievements.json
```

### 6.2 Mises à jour

#### Procédure de mise à jour
```bash
# 1. Sauvegarde des données
cp achievements.json achievements_backup.json

# 2. Mise à jour du code
git pull origin main

# 3. Mise à jour des dépendances
pip install -r docs/requirements.txt --upgrade

# 4. Test de fonctionnement
python main.py
```

### 6.3 Sécurité

#### Permissions fichiers
```bash
# Linux/macOS - Sécurisation
chmod 755 *.py
chmod 644 achievements.json
chmod -R 644 assets/
```

#### Vérification d'intégrité
```bash
# Vérification syntaxe Python
python -m py_compile main.py
python -m py_compile Class/*.py
```

### 6.4 Dépannage courant

| Problème | Diagnostic | Solution |
|----------|------------|----------|
| Jeu ne démarre pas | `python main.py` → erreur | Vérifier dépendances |
| Succès non sauvés | `achievements.json` absent | Vérifier droits écriture |
| Sons absents | Erreur mixer | Installer codecs audio |
| Performances lentes | FPS < 30 | Réduire résolution |

---

## 7. ANNEXES

### 7.1 Glossaire

- **PyGame** : Bibliothèque Python pour développement de jeux 2D
- **PyTMX** : Parseur Python pour fichiers Tiled Map Editor
- **Succès** : Système de récompenses basé sur les actions du joueur
- **TMX** : Format de fichier XML pour cartes de jeu Tiled

### 7.2 Scripts utiles

#### Reset complet des succès
```python
import os
if os.path.exists("achievements.json"):
    os.remove("achievements.json")
    print("Succès remis à zéro")
```

#### Vérification dépendances
```bash
pip check
pip list --outdated
```

### 7.3 Références externes

- [Documentation Pygame](https://www.pygame.org/docs/)
- [Tiled Map Editor](https://www.mapeditor.org/)
- [Python.org](https://docs.python.org/3/)
- [ISO/IEC 26514](https://www.iso.org/standard/43073.html)

### 7.4 Structure des logs

```
[TIMESTAMP] [LEVEL] Message
[2025-09-30 14:30:15] [INFO] Jeu démarré
[2025-09-30 14:30:16] [DEBUG] Plateforme créée
[2025-09-30 14:30:20] [SUCCESS] Succès débloqué
[2025-09-30 14:30:25] [ERROR] Erreur de chargement
```

### 7.5 Contact support

**Développeur** : CHAMPY Thomas, TURBE Keylian, SIAME Romain, LE PALLEC Hippolyte, ARNOULT Antoine, BERGHOL Samy
**Repository** : https://github.com/keylian15/blue_frontline  

---

*Ce document respecte les préconisations ISO/IEC 26514 pour la documentation technique.*