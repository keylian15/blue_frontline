from Class.units.Unit import Unit
from Global import UNIT_CONFIGS

class SousMarin(Unit):
    """Classe unifiée pour les unités Sous-marin (Rouge et Vert)."""
    
    def __init__(self, game, team):
        # Récupérer la configuration depuis Global.py
        config = UNIT_CONFIGS["sousmarin"]
        
<<<<<<< HEAD
        # Déterminer le chemin de l'image selon l'équipe
        image_path = config["image_paths"][team]
        
=======
>>>>>>> e5f634d (Ajout du système audio spatial)
        # Initialiser avec l'image appropriée et le type d'unité
        super().__init__(game, team=team, unit_type="sousmarin")
        
        # === Spécifications du Sous-marin depuis Global.py ===
        self.cost = config["cost"]
<<<<<<< HEAD
        
=======
>>>>>>> e5f634d (Ajout du système audio spatial)
        self.max_speed = config["max_speed"]
        self.max_health = config["max_health"]
        self.current_health = self.max_health
        self.range = config["range"]
        self.damage = config["damage"]
        self.fire_rate = config["fire_rate"]
        
        # Type d'unité et capacité spéciale
        self.unit_type = config["unit_type"]
        self.unit_name = f"Sous-marin {team.capitalize()}"
        self.special_ability = config.get("special_ability", None)
        
        # Couleur de portée selon l'équipe
        self.range_color = config["range_color"][team]
        
        # État de mouvement
        self.is_moving = False
        self.target_position = None
            
    def update(self, dt=0, combat_system=None, screen=None, camera_offset=(0, 0), all_units=None):
        """Met à jour le sous-marin."""
        # Appeler la mise à jour de la classe parent
        super().update(dt, combat_system, screen, camera_offset, all_units)

        # Dessiner la portée en permanence
        if screen:
            self.draw_range(screen, camera_offset)
    
    def place_mine(self, x, y):
<<<<<<< HEAD
        """Place une mine à la position spécifiée (capacité spéciale du sous-marin)."""
        if self.special_ability == "mines":
            # TODO: Implémenter le système de mines
=======
        """
        Place une mine à la position spécifiée (capacité spéciale du sous-marin).
        NOTE: on ne change pas la logique de jeu ici (le TODO reste).
              On se contente d'ajouter le son "drop_mine.mp3" au moment de la pose.
        """
        if self.special_ability == "mines":
            # TODO: Implémenter le système de mines (création objet Mine, ajout aux groupes, etc.)
            # -- AUDIO : drop mine --
            try:
                if hasattr(self.game, "sound") and self.game.sound:
                    # si plus tard l'objet Mine a un .position, vous pouvez envoyer ça plutôt que (x,y)
                    self.game.sound.on_mine_dropped((x, y))
            except Exception:
                # ne jamais crasher pour du son
                pass
>>>>>>> e5f634d (Ajout du système audio spatial)
            return True
        return False

# Classes d'alias pour la compatibilité avec l'ancien code
class SousMarinRouge(SousMarin):
    def __init__(self, game):
        super().__init__(game, team="red")

class SousMarinVert(SousMarin):
    def __init__(self, game):
<<<<<<< HEAD
        super().__init__(game, team="green")
=======
        super().__init__(game, team="green")
>>>>>>> e5f634d (Ajout du système audio spatial)
