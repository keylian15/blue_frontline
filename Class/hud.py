import pygame 
from Class.Petrole import Petrole
from Global import * 
from Class.Piece import Piece

class Hud:
    """Classe pour gérer le HUD du jeu."""
    
    def __init__(self, screen):
        """Fonction permettant d'initialiser le HUD"""
        # Dimensions de l'écran
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Couleur de fond du HUD
        self.hud_color = (198, 198, 198)
        self.show = True
        
        # Charger les images une seule fois
        self.images = self.load_images()
                
        # Build du HUD
        self.build_surface = pygame.Surface((self.width * 0.15, self.height * 0.25), pygame.SRCALPHA)
        
        # Select HUD
        self.select_surface = pygame.Surface((self.width * 0.3, self.height * 0.2), pygame.SRCALPHA)

        # Instance unique de ton compteur de pétrole
        self.petrole = Petrole()
        self.piece = Piece()

    def switch(self):
        """Fonction permettant d'afficher ou de cacher le HUD"""
        self.show = not self.show
            
    def draw(self, screen):
        """Fonction permettant de déssiener le HUD sur le screen"""
        
        # On vérifie si le HUD doit être affiché
        if not self.show:
            return

        # Build hud
        screen.blit(self.build_surface, (self.width * 0.84, self.height * 0.74))
            
        # Select hud
        screen.blit(self.select_surface, (self.width * 0.35, self.height * 0.79))

        # Images
        screen.blit(self.images['piece'], (self.width * 0.84, self.height * 0.74))
        screen.blit(self.images['petrole'], (self.width * 0.84, self.height * 0.84))
        
        # Texte compteur pétrole
        font = pygame.font.Font(None, 30)
        text = font.render(str(self.petrole.count), True, (0, 0, 0))
        screen.blit(text, (self.width * 0.84 + 90, self.height * 0.84 + 30))
        
        #Texte compteur pièces
        text = font.render(str(self.piece.count), True, (0, 0, 0))
        screen.blit(text, (self.width * 0.84 + 90, self.height * 0.74 + 30))

    def load_images(self):
        """Fonction permettant de charger les images du HUD"""
        piece = pygame.image.load(PIECE_IMAGE_PATH).convert_alpha()
        petrole = pygame.image.load(PETROLE_IMAGE_PATH).convert_alpha()
        
        piece = pygame.transform.scale(piece, (80, 80))
        petrole = pygame.transform.scale(petrole, (80, 80))
        
        images = {
            'piece': piece,
            'petrole': petrole
        }
        return images
    
    