class IAInitializer:
    """Gestionnaire d'initialisation des IA du jeu."""

    def __init__(self, game: "Game"):
        """Initialise le gestionnaire d'initialisation avec une référence au jeu.

        Args:
            game (Game): Référence au jeu.
        """

        self.game = game
        
    def init_ia_bateau(self):
        """Initialise les IA des bateaux du jeu. ANTOINE"""
        # Appel de la classe avec self.game en paramétre
        pass