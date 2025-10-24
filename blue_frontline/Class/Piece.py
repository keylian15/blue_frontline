class Piece:
    """Classe pour gérer les pièces."""

    def __init__(self):
        """Initialise les pièces."""
        self.count = 0
        self.multiplicateur = 1
        
    def add_piece(self):
        """Ajoute des pièces."""
        from Global import PIECE_PER_KILL
        self.count += PIECE_PER_KILL * self.multiplicateur