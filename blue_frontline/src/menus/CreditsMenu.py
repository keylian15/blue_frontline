import webbrowser

import pygame
from src.config.paths import ANCHOR_PATH
from src.config.visuals import BUTTON_BORDER_RADIUS, LIGHT_BLUE, OCEAN_BLUE, WAVE_COLOR, WHITE


class CreditsMenu:
    """Menu des crédits du jeu."""

    def __init__(self, screen):
        """Initialise le menu des crédits.

        Args:
            screen (pygame.Surface): Surface de dessin du menu.
        """
        self.screen = screen
        self.WIDTH, self.HEIGHT = self.screen.get_size()
        self.font = pygame.font.SysFont(None, 40)
        self.title_font = pygame.font.SysFont(None, 60)
        self.small_font = pygame.font.SysFont(None, 32)

        self.background = (20, 30, 50)

        self.anchor_img = pygame.image.load(ANCHOR_PATH).convert_alpha()
        self.anchor_img = pygame.transform.smoothscale(self.anchor_img, (30, 30))

        self.MARGIN_LEFT = 50
        self.MIN_BUTTON_WIDTH = 250
        self.BUTTON_HEIGHT = 60
        self.VERTICAL_SPACING = 80
        self.BUTTON_PADDING = 80

        # Liste des membres de l'équipe avec leurs informations GitHub
        self.team_members = [
            {
                "prenom": "Keylian",
                "nom": "Turbé",
                "github": "https://github.com/keylian15",
            },
            {
                "prenom": "Romain",
                "nom": "Siame",
                "github": "https://github.com/rommick59",
            },
            {
                "prenom": "Hippolyte",
                "nom": "Le Pallec",
                "github": "https://github.com/Hippolyte-LePallec",
            },
            {
                "prenom": "Antoine",
                "nom": "Arnoult",
                "github": "https://github.com/garniik",
            },
            {
                "prenom": "Thomas",
                "nom": "Champy",
                "github": "https://github.com/tcmy6526512",
            },
            {
                "prenom": "Samy",
                "nom": "Berghol",
                "github": "https://github.com/BERGHOL",
            },
        ]

        # URL de la vidéo (à remplacer par votre lien YouTube ou autre)
        self.video_url = "https://www.youtube.com/watch?v=dcDdPDXefHo"

        # Créer les boutons du menu principal
        self.create_main_menu_buttons()
        self.create_member_buttons()

    def draw_gradient_button(self, rect, hovered=False):
        """Dessine un bouton avec dégradé

        Args:
            rect (pygame.Rect): Le rectangle du bouton.
            hovered (bool): Si le bouton est survolé par la souris.

        Returns:
            button_surf (pygame.Surface): La surface du bouton.
        """
        import math

        button_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)

        color1 = LIGHT_BLUE if hovered else OCEAN_BLUE
        color2 = OCEAN_BLUE if hovered else LIGHT_BLUE

        for i in range(rect.height):
            ratio = i / rect.height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            pygame.draw.rect(button_surf, (r, g, b), (0, i, rect.width, 1))

        wave_height = 5
        wave_points = []
        for i in range(rect.width + 1):
            px = i
            py = int(rect.height - wave_height * (1 + math.sin(i / 18)))
            wave_points.append((px, py))
        pygame.draw.aalines(button_surf, WAVE_COLOR, False, wave_points)

        mask = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(
            mask,
            (255, 255, 255, 255),
            (0, 0, rect.width, rect.height),
            border_radius=BUTTON_BORDER_RADIUS,
        )
        button_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        return button_surf

    def create_member_buttons(self):
        """Crée les boutons cliquables pour chaque membre de l'équipe"""
        start_y = 180
        button_width = 450
        button_height = 50
        spacing = 65
        center_x = self.WIDTH // 2

        self.member_buttons = []
        for i, member in enumerate(self.team_members):
            button_rect = pygame.Rect(
                center_x - button_width // 2,
                start_y + i * spacing,
                button_width,
                button_height,
            )
            self.member_buttons.append(
                {
                    "rect": button_rect,
                    "member": member,
                    "text": f"{member['prenom']} {member['nom']}",
                }
            )

    def create_main_menu_buttons(self):
        """Crée les boutons du menu principal des options"""
        button_width = 300

        self.main_buttons = [
            {
                "text": "Voir la vidéo",
                "rect": pygame.Rect(
                    self.WIDTH // 2 - button_width // 2,
                    self.HEIGHT - 160,
                    button_width,
                    self.BUTTON_HEIGHT,
                ),
                "action": "video",
            },
            {
                "text": "Retour",
                "rect": pygame.Rect(
                    self.MARGIN_LEFT,
                    self.HEIGHT - self.BUTTON_HEIGHT - 20,
                    250,
                    self.BUTTON_HEIGHT,
                ),
                "action": "back",
            },
            {
                "text": "Quitter le jeu",
                "rect": pygame.Rect(
                    self.WIDTH - button_width - self.MARGIN_LEFT,
                    self.HEIGHT - self.BUTTON_HEIGHT - 20,
                    button_width,
                    self.BUTTON_HEIGHT,
                ),
                "action": "quit_game",
            },
        ]

    def draw_main_menu(self):
        """Dessine le menu principal des crédits"""
        self.screen.fill(self.background)

        # Titre
        title = "CRÉDITS"
        title_surf = self.title_font.render(title, True, WHITE)
        title_rect = title_surf.get_rect(midtop=(self.WIDTH // 2, 30))
        self.screen.blit(title_surf, title_rect)

        # Sous-titre
        subtitle = "Équipe de développement - Cliquez pour voir le GitHub"
        subtitle_surf = self.small_font.render(subtitle, True, (150, 200, 255))
        subtitle_rect = subtitle_surf.get_rect(midtop=(self.WIDTH // 2, 110))
        self.screen.blit(subtitle_surf, subtitle_rect)

        # Sous-titre
        subtitle_bis = "Fait avec Pygame et Tiled"
        subtitle_bis_surf = self.small_font.render(subtitle_bis, True, (150, 200, 255))
        subtitle_bis_rect = subtitle_bis_surf.get_rect(midtop=(self.WIDTH // 2, self.HEIGHT - 60))
        self.screen.blit(subtitle_bis_surf, subtitle_bis_rect)

        # Dessiner les boutons des membres de l'équipe
        mouse_pos = pygame.mouse.get_pos()

        for button in self.member_buttons:
            hovered = button["rect"].collidepoint(mouse_pos)

            # Dessiner le bouton
            button_surf = self.draw_gradient_button(button["rect"], hovered)
            self.screen.blit(button_surf, button["rect"])
            pygame.draw.rect(
                self.screen,
                WHITE,
                button["rect"],
                2,
                border_radius=BUTTON_BORDER_RADIUS,
            )

            # Texte du bouton (nom du membre)
            text_surf = self.small_font.render(button["text"], True, WHITE)
            text_rect = text_surf.get_rect(center=button["rect"].center)
            self.screen.blit(text_surf, text_rect)

        # Dessiner les boutons du menu principal
        for button in self.main_buttons:
            hovered = button["rect"].collidepoint(mouse_pos)

            # Dessiner le bouton
            button_surf = self.draw_gradient_button(button["rect"], hovered)
            self.screen.blit(button_surf, button["rect"])
            pygame.draw.rect(
                self.screen,
                WHITE,
                button["rect"],
                3,
                border_radius=BUTTON_BORDER_RADIUS,
            )

            # Icône ancre (sauf pour le bouton vidéo)
            if button["action"] != "video":
                anchor_rect = self.anchor_img.get_rect(midleft=(button["rect"].left + 20, button["rect"].centery))
                self.screen.blit(self.anchor_img, anchor_rect)
                text_x = anchor_rect.right + 15
            else:
                text_x = button["rect"].centerx

            # Texte du bouton
            text_surf = self.font.render(button["text"], True, WHITE)
            if button["action"] == "video":
                text_rect = text_surf.get_rect(center=(text_x, button["rect"].centery))
            else:
                text_rect = text_surf.get_rect(midleft=(text_x, button["rect"].centery))
            self.screen.blit(text_surf, text_rect)

    def run(self):
        """Boucle principale du menu des crédits."""
        running = True
        clock = pygame.time.Clock()
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()

                    if event.button == 1:  # Clic gauche
                        # Vérifier les clics sur les membres de l'équipe
                        for button in self.member_buttons:
                            if button["rect"].collidepoint(mouse_pos):
                                # Ouvrir le profil GitHub dans le navigateur
                                webbrowser.open(button["member"]["github"])
                                break

                        # Vérifier les clics sur les boutons principaux
                        for button in self.main_buttons:
                            if button["rect"].collidepoint(mouse_pos):
                                if button["action"] == "back":
                                    return True
                                elif button["action"] == "quit_game":
                                    pygame.quit()
                                    import sys

                                    sys.exit()
                                elif button["action"] == "video":
                                    # Ouvrir la vidéo dans le navigateur
                                    webbrowser.open(self.video_url)
                                break

            self.draw_main_menu()
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
