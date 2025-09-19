import pygame 
from Class.Petrole import Petrole
from Global import * 
from Class.Piece import Piece
from Class.Timer import Timer
from Utils import *
class Hud:
    """Classe pour gérer le HUD du jeu."""
    
    def __init__(self, screen):
        """Fonction permettant d'initialiser le HUD"""
        # Dimensions de l'écran
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.screen = screen
        
        # Couleur de fond du HUD
        self.hud_color = (198, 198, 198)
        self.show = True
        
        # Charger les images une seule fois
        self.images = self.load_images()
        
        # Police et état du popup d'unités
        self.font = pygame.font.Font(None, 24)
        self.show_unit_popup = True
        self.popup_selection = 0  # index sélectionné, 0..5
        self.popup_team = 'red'  # équipe affichée: 'red' ou 'green'
        # Noms correspondant à l'ordre d'affichage des icônes rouges
        self.unit_names = [
            "Chaloupe",
            "Bateau",
            "Paquebot",
            "Éclaireur",
            "Sous-marin",
            "Plateforme"
        ]
                

        # Instance unique de ton compteur de pétrole
        self.petrole = Petrole()
        self.piece = Piece()
        self.timer = Timer()

    def switch(self):
        """Fonction permettant d'afficher ou de cacher le HUD"""
        self.show = not self.show
            
    def draw(self, screen):
        """Fonction permettant de déssiener le HUD sur le screen"""
        
        # On vérifie si le HUD doit être affiché
        if not self.show:
            return
        
        #affichage de la selection des troupes
        # Popup aligné aux icônes
        self.draw_unit_popup()
        # screen.blit(self.images['green_chaloupe'], (self.width * 0.7, self.height * 0.9))
        # screen.blit(self.images['green_bateau'], (self.width * 0.8, self.height * 0.9))
        # screen.blit(self.images['green_paquebot'], (self.width * 0.9, self.height * 0.9))
        # screen.blit(self.images['green_eclaireur'], (self.width * 0.1, self.height * 0.9))
        # screen.blit(self.images['green_sousmarin'], (self.width * 0.2, self.height * 0.9))
        # screen.blit(self.images['green_platforme'], (self.width * 0.3, self.height * 0.9))
        
        
        
        # Images
        screen.blit(self.images['piece'], (self.width * 0.84, self.height * 0.8))
        screen.blit(self.images['petrole'], (self.width * 0.84, self.height * 0.9))
        
        # Texte compteur pétrole
        font = pygame.font.Font(None, 30)
        text = font.render(str(self.petrole.count), True, (0, 0, 0))
        screen.blit(text, (self.width * 0.84 + 90, self.height * 0.9 + 30))
        
        #Texte compteur pièces
        text = font.render(str(self.piece.count), True, (0, 0, 0))
        screen.blit(text, (self.width * 0.84 + 90, self.height * 0.8 + 30))
        
        #Texte timer
        text = font.render(str(self.timer.get_time()), True, (0, 0, 0))
        screen.blit(text, (self.width * 0.5, self.height *0.05))

    def load_images(self):
        """Fonction permettant de charger les images du HUD"""
        piece = pygame.image.load(PIECE_IMAGE_PATH).convert_alpha()
        petrole = pygame.image.load(PETROLE_IMAGE_PATH).convert_alpha()
        
        red_team = load_tileset(RED_TEAM_PATH)
        green_team = load_tileset(GREEN_TEAM_PATH)
        
        
        red_chaloupe = pygame.transform.scale(red_team[0], (80, 80))
        red_bateau = pygame.transform.scale(red_team[1], (80, 80))
        red_paquebot = pygame.transform.scale(red_team[2], (80, 80))
        red_eclaireur = pygame.transform.scale(red_team[3], (80, 80))
        red_sousmarin = pygame.transform.scale(red_team[4], (80, 80))
        red_platforme = pygame.transform.scale(red_team[6], (80, 80))
        
        green_chaloupe = pygame.transform.scale(green_team[0], (80, 80))
        green_bateau = pygame.transform.scale(green_team[1], (80, 80))
        green_paquebot = pygame.transform.scale(green_team[2], (80, 80))
        green_eclaireur = pygame.transform.scale(green_team[3], (80, 80))
        green_sousmarin = pygame.transform.scale(green_team[4], (80, 80))
        green_platforme = pygame.transform.scale(green_team[6], (80, 80))
        
        piece = pygame.transform.scale(piece, (80, 80))
        petrole = pygame.transform.scale(petrole, (80, 80))
        
        images = {
            'piece': piece,
            'petrole': petrole,
            'red_chaloupe': red_chaloupe,
            'red_bateau': red_bateau,
            'red_paquebot': red_paquebot,
            'red_eclaireur': red_eclaireur,
            'red_sousmarin': red_sousmarin,
            'red_platforme': red_platforme,
            'green_chaloupe': green_chaloupe,
            'green_bateau': green_bateau,
            'green_paquebot': green_paquebot,
            'green_eclaireur': green_eclaireur,
            'green_sousmarin': green_sousmarin,
            'green_platforme': green_platforme
        }
        return images
    
    def draw_unit_popup(self):
        """Dessine un popup horizontal aligné au-dessus des icônes du HUD."""
        # Toujours affiché
        
        # Paramètres d'alignement des icônes
        icon_size = 80
        icon_y = self.height * 0.875
        x_factors = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35]
        icon_positions = [
            (self.width * xf, icon_y)
            for xf in x_factors
        ]
        first_x = icon_positions[0][0]
        last_x = icon_positions[-1][0]
        band_margin = 8
        band_height = 80
        popup_drop = 130  # décale le popup vers le bas pour conserver la position apparente
        band_width = (last_x - first_x) + icon_size
        band_x = first_x - band_margin
        band_y = icon_y - band_height - band_margin + popup_drop
        band_width += band_margin * 2
        
        # Bande semi-transparente au-dessus des icônes
        band_surface = pygame.Surface((int(band_width), int(band_height)), pygame.SRCALPHA)
        band_surface.fill((0, 0, 0, 160))
        pygame.draw.rect(band_surface, (255, 255, 255), band_surface.get_rect(), 2)

        # Icônes miniatures centrées au-dessus de chaque grande icône
        popup_icon_size = 40
        popup_icon_margin_top = 10
        if self.popup_team == 'red':
            image_keys = [
                'red_chaloupe',
                'red_bateau',
                'red_paquebot',
                'red_eclaireur',
                'red_sousmarin',
                'red_platforme'
            ]
        else:
            image_keys = [
                'green_chaloupe',
                'green_bateau',
                'green_paquebot',
                'green_eclaireur',
                'green_sousmarin',
                'green_platforme'
            ]
        for i, key in enumerate(image_keys):
            icon_x = icon_positions[i][0]
            base_image = self.images[key]
            mini_image = pygame.transform.smoothscale(base_image, (popup_icon_size, popup_icon_size))
            mini_rect = mini_image.get_rect()
            mini_rect.midtop = (int(icon_x + icon_size / 2 - band_x), popup_icon_margin_top)
            band_surface.blit(mini_image, mini_rect)

            # Indication de sélection: cadre jaune autour de l'icône sélectionnée
            if i == self.popup_selection:
                pygame.draw.rect(
                    band_surface,
                    (255, 215, 0),
                    mini_rect.inflate(8, 8),
                    2
                )
        
        # Affichage de la bande
        self.screen.blit(band_surface, (int(band_x), int(band_y)))

    def toggle_popup_team(self):
        """Bascule l'équipe affichée dans le popup (rouge <-> vert)."""
        self.popup_team = 'green' if self.popup_team == 'red' else 'red'