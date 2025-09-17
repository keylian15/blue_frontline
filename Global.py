# Fichier des variables globales (Chemin, variables, etc.)
import os 

# Chemin du dossier courant
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Chemin de la map
MAP_PATH = "map.tmx"

# === Caméra ===
# Chemin de l'image Bullet
BULLET_IMAGE_PATH = os.path.join(BASE_DIR, 'assets/entity/png/bullet.png')

# === Unités ===
# Chaloupes
RED_CHALOUPE_IMAGE_PATH = os.path.join(BASE_DIR, 'assets/boat/png/red_chaloupe.png')
GREEN_CHALOUPE_IMAGE_PATH = os.path.join(BASE_DIR, 'assets/boat/png/green_chaloupe.png')

# Bâteaux 
RED_SHIP_IMAGE_PATH = os.path.join(BASE_DIR, 'assets/boat/png/red_ship.png')
GREEN_SHIP_IMAGE_PATH = os.path.join(BASE_DIR, 'assets/boat/png/green_ship.png')

#Paquebots
RED_PAQUEBOT_IMAGE_PATH = os.path.join(BASE_DIR, 'assets/boat/png/red_paquebot.png')
GREEN_PAQUEBOT_IMAGE_PATH = os.path.join(BASE_DIR, 'assets/boat/png/green_paquebot.png')

# Éclaireurs
RED_ECLAIREUR_IMAGE_PATH = os.path.join(BASE_DIR, 'assets/boat/png/red_eclaireur.png')
GREEN_ECLAIREUR_IMAGE_PATH = os.path.join(BASE_DIR, 'assets/boat/png/green_eclaireur.png')

# Sous-marins
RED_SUBMARINE_IMAGE_PATH = os.path.join(BASE_DIR, 'assets/boat/png/red_submarine.png')
GREEN_SUBMARINE_IMAGE_PATH = os.path.join(BASE_DIR, 'assets/boat/png/green_submarine.png')
