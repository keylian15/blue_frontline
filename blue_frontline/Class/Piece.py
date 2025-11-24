class Piece:
    """Classe pour gérer les pièces."""

    def __init__(self):
        """Initialise les pièces."""
        self.count = 0
        self.multiplicateur = 1
        
    def add_piece(self):
        """Ajoute des pièces."""
        from Global import get_gameplay_settings
        self.count += get_gameplay_settings()["PIECE_PER_KILL"] * self.multiplicateur