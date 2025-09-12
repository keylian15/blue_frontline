# Fichier des variables globales (Chemin, variables, etc.)
import os 

# Chemin du dossier courant
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Chemin de la map
MAP_PATH = "map.tmx"

# === Caméra ===
# Chemin de l'image Bullet
BULLET_IMAGE_PATH = os.path.join(BASE_DIR, 'assets/entity/png/bullet.png')
