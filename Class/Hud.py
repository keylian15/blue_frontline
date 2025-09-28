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
        self.player_team = 'red'  # Équipe du joueur, 'red' ou 'green'
        
        # Couleur de fond du HUD
        self.hud_color = (198, 198, 198)
        self.show = True
        
        # Charger les images une seule fois
        self.images = self.load_images()
        
        # Police et état du popup d'unités
        self.font = pygame.font.Font(None, 24)
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
        # Clés de config correspondant aux icônes (la plateforme n'a pas de config pour l'instant)
        self.unit_config_keys = [
            'chaloupe', 'bateau', 'paquebot', 'eclaireur', 'sousmarin', None
        ]
                

        # Instance unique de ton compteur de pétrole
        self.petrole_red = Petrole()
        self.piece_red = Piece()
        self.petrole_green = Petrole()
        self.piece_green = Piece()
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

        team_text = "Équipe: " + ("Rouge" if self.player_team == 'red' else "Verte")
        team_color = (255, 0, 0) if self.player_team == 'red' else (0, 255, 0)
        team_surface = self.font.render(team_text, True, team_color)
        screen.blit(team_surface, (self.width * 0.05, self.height * 0.05))
        
        
        
        # Images
        screen.blit(self.images['piece'], (self.width * 0.84, self.height * 0.8))
        screen.blit(self.images['petrole'], (self.width * 0.84, self.height * 0.9))
        
        # Texte compteur pétrole
        font = pygame.font.Font(None, 30)
        text = font.render(str(self.petrole_red.count if self.player_team == 'red' else self.petrole_green.count), True, (0, 0, 0))
        screen.blit(text, (self.width * 0.84 + 90, self.height * 0.9 + 30))
        
        #Texte compteur pièces
        text = font.render(str(self.piece_red.count if self.player_team == 'red' else self.piece_green.count), True, (0, 0, 0))
        screen.blit(text, (self.width * 0.84 + 90, self.height * 0.8 + 30))
        
        #Texte timer avec vitesse
        speed_multiplier = self.timer.get_speed_multiplier()
        timer_text = f"{self.timer.get_time()} (x{speed_multiplier})"
        text = font.render(timer_text, True, (0, 0, 0))
        screen.blit(text, (self.width * 0.5, self.height *0.05))
        
        if self.timer.maree_haute:
            screen.blit(self.images['maree_haute'], (self.width * 0.6, self.height * 0.05))
        else:
            screen.blit(self.images['maree_basse'], (self.width * 0.6, self.height * 0.05))
                
    def load_images(self):
        """Fonction permettant de charger les images du HUD"""
        piece = pygame.image.load(PIECE_IMAGE_PATH).convert_alpha()
        petrole = pygame.image.load(PETROLE_IMAGE_PATH).convert_alpha()
        maree_haute = pygame.image.load(MAREE_HAUTE_IMAGE_PATH).convert_alpha()
        marre_basse = pygame.image.load(MAREE_BASSE_IMAGE_PATH).convert_alpha()
        
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
            'green_platforme': green_platforme,
            'maree_haute': maree_haute,
            'maree_basse': marre_basse
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

        # Affichage d'un panneau de stats pour l'icône actuellement sélectionnée
        self._draw_unit_popup_stats(self.popup_selection, band_x, band_y, band_width)

    def _draw_unit_popup_stats(self, selection_index, band_x, band_y, band_width):
        """Dessine un panneau de stats au-dessus du bandeau pour l'unité sélectionnée dans le popup."""
        # Trouver la clé de config
        if selection_index < 0 or selection_index >= len(self.unit_config_keys):
            return
        config_key = self.unit_config_keys[selection_index]

        # Si pas de config (ex: Plateforme), on affiche un message minimal
        from Global import UNIT_CONFIGS
        config = UNIT_CONFIGS.get(config_key) if config_key else None

        title_font = pygame.font.Font(None, 26)
        text_font = pygame.font.Font(None, 22)

        if config:
            title = self.unit_names[selection_index]
            lines = [
                f"Coût: {config.get('cost', '?')}",
                f"Temps: {config.get('build_time', '?')} s",
                f"PV max: {config.get('max_health', '?')}",
                f"Vitesse: {config.get('max_speed', '?')} px/s",
                f"Portée: {config.get('range', '?')}",
                f"Dégâts: {config.get('damage', '?')}",
                f"Cadence: {config.get('fire_rate', '?')}/s",
            ]
        else:
            title = self.unit_names[selection_index]
            lines = ["Aucune statistique disponible"]

        title_surf = title_font.render(title, True, (255, 255, 255))
        text_surfs = [text_font.render(t, True, (230, 230, 230)) for t in lines]

        padding = 10
        inner_w = max(title_surf.get_width(), max((s.get_width() for s in text_surfs), default=0))
        inner_h = title_surf.get_height() + 6 + sum(s.get_height() for s in text_surfs)
        panel_w = inner_w + padding * 2
        panel_h = inner_h + padding * 2

        # Positionner centré par rapport à la bande, au-dessus
        panel_x = int(band_x + (band_width - panel_w) / 2)
        panel_y = int(band_y - panel_h - 10)
        panel_x = max(6, min(panel_x, self.width - panel_w - 6))
        panel_y = max(6, panel_y)

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 180))
        pygame.draw.rect(panel, (255, 255, 255), panel.get_rect(), 2)

        panel.blit(title_surf, (padding, padding))
        y = padding + title_surf.get_height() + 6
        for s in text_surfs:
            panel.blit(s, (padding, y))
            y += s.get_height()

        self.screen.blit(panel, (panel_x, panel_y))

    def toggle_popup_team(self):
        """Bascule l'équipe affichée dans le popup (rouge <-> vert)."""
        self.popup_team = 'green' if self.popup_team == 'red' else 'red'
        
        
    def switch_team(self):
        """Change l'équipe du joueur"""
        self.player_team = 'green' if self.player_team == 'red' else 'red'
        
