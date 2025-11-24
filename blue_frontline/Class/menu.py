import pygame, sys, math
from Global import *
from Class.Game import Game
from Class.OptionsMenu import OptionsMenu
from Class.AchievementsMenu import AchievementsMenu
from Class.AchievementsSystem import AchievementsSystem
from Class.AchievementsSystemRouge import AchievementsSystemRouge
from Class.AchievementsSystemVert import AchievementsSystemVert

class Menu:
    """Classe pour gérer le menu principal du jeu."""
    
    def __init__(self):
        """Fonction d'initialisation du menu principal."""
        self.screen = pygame.display.set_mode((0, 0), pygame.NOFRAME)
        pygame.display.set_caption("Blue Frontline")
        self.WIDTH, self.HEIGHT = self.screen.get_size()

        self.background = pygame.image.load(MENU_PATH).convert_alpha()
        self.background = pygame.transform.scale(self.background, (self.WIDTH, self.HEIGHT))

        self.font = pygame.font.SysFont(None, 60)

        # Ajout : chargement de l'image d'ancre
        self.anchor_img = pygame.image.load(ANCHOR_PATH).convert_alpha()
        self.anchor_img = pygame.transform.smoothscale(self.anchor_img, (40, 40))

        # Boutons
        start_x = BUTTON_MARGIN_LEFT
        start_y = self.HEIGHT - (5 * BUTTON_HEIGHT + 3 * BUTTON_SPACING) - BUTTON_MARGIN_BOTTOM
        self.buttons = [
            ("Jouer",   start_x, start_y, BUTTON_WIDTH, BUTTON_HEIGHT),
            ("Tuto",  start_x, start_y + (BUTTON_HEIGHT + BUTTON_SPACING) * 1, BUTTON_WIDTH, BUTTON_HEIGHT),
            ("Options", start_x, start_y + (BUTTON_HEIGHT + BUTTON_SPACING) * 2, BUTTON_WIDTH, BUTTON_HEIGHT),
            ("Succès", start_x, start_y + (BUTTON_HEIGHT + BUTTON_SPACING) * 3, BUTTON_WIDTH, BUTTON_HEIGHT),
            ("Quitter", start_x, start_y + (BUTTON_HEIGHT + BUTTON_SPACING) * 4, BUTTON_WIDTH, BUTTON_HEIGHT),
        ]
        
        
        self.achievements_system_rouge = AchievementsSystemRouge()
        self.achievements_system_vert = AchievementsSystemVert()
        
        # Système par défaut (Rouge) pour compatibilité
        self.achievements_system = self.achievements_system_rouge

    def draw_button(self, text: str, x: int, y: int, w: int, h: int, hovered: bool):
        """Fonction pour dessiner un bouton avec un texte et une bordure.

        Args:
            text (str): Texte à afficher sur le bouton.
            x (int): Position x du bouton.
            y (int): Position y du bouton.
            w (int): Largeur du bouton.
            h (int): Hauteur du bouton.
            hovered (bool): Indique si le bouton est survolé.
        """
        
        BORDER_COLOR = WHITE

        button_surf = pygame.Surface((w, h), pygame.SRCALPHA)

        color1 = LIGHT_BLUE if hovered else OCEAN_BLUE
        color2 = OCEAN_BLUE if hovered else LIGHT_BLUE
        for i in range(h):
            ratio = i / h
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            pygame.draw.rect(button_surf, (r, g, b), (0, i, w, 1))

        wave_height = 10
        wave_points = []
        for i in range(w + 1):
            px = i
            py = int(h - wave_height * (1 + math.sin(i / 18)))
            wave_points.append((px, py))
        pygame.draw.aalines(button_surf, WAVE_COLOR, False, wave_points)

        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=BUTTON_BORDER_RADIUS)
        button_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        self.screen.blit(button_surf, (x, y))

        pygame.draw.rect(self.screen, BORDER_COLOR, (x, y, w, h), 4, border_radius=BUTTON_BORDER_RADIUS)

        # Utilisation de l'image d'ancre
        anchor_rect = self.anchor_img.get_rect(midleft=(x + 30, y + h // 2))
        self.screen.blit(self.anchor_img, anchor_rect)

        # Texte centré à droite de l'ancre
        txt = self.font.render(text, True, WHITE)
        txt_rect = txt.get_rect(midleft=(anchor_rect.right + 20, y + h // 2))
        self.screen.blit(txt, txt_rect)

    def choose_game_mode(self):
        """Affiche un sous-menu pour choisir le mode de jeu et retourne le choix."""
        modes = [
            ("Joueur vs Joueur", "PVP"),
            ("Joueur vs IA", "PVE"),
            ("IA vs IA", "EVE")
        ]

        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()
            mouse_click = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F4 and (pygame.key.get_mods() & pygame.KMOD_ALT):
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_click = True

            self.screen.blit(self.background, (0, 0))

            # Affichage des boutons
            start_y = self.HEIGHT // 3
            for idx, (text, mode) in enumerate(modes):
                w, h = 500, 70
                x = self.WIDTH // 2 - w // 2
                y = start_y + idx * (h + 20)
                hovered = x <= mouse_pos[0] <= x + w and y <= mouse_pos[1] <= y + h
                self.draw_button(text, x, y, w, h, hovered)

                if hovered and mouse_click:
                    return mode  # Retourne le mode choisi
            # Bouton retour
            back_button_rect = pygame.Rect(50, self.HEIGHT - 80, 250, 60)
            self.draw_button("Retour", back_button_rect.x, back_button_rect.y, back_button_rect.width, back_button_rect.height, back_button_rect.collidepoint(mouse_pos))

            if back_button_rect.collidepoint(mouse_pos) and mouse_click:
                return "menu"
            
            pygame.display.flip()

    def run(self):
        """Boucle principale du menu."""
        menu = True
        try:
            while menu:
                mouse_pos = pygame.mouse.get_pos()
                mouse_click = False

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_F4 and (pygame.key.get_mods() & pygame.KMOD_ALT):
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mouse_click = True

                self.screen.blit(self.background, (0, 0))

                for idx, (text, x, y, w, h) in enumerate(self.buttons):
                    hovered = x <= mouse_pos[0] <= x + w and y <= mouse_pos[1] <= y + h
                    self.draw_button(text, x, y, w, h, hovered)

                    if hovered and mouse_click:
                        if text == "Quitter":
                            pygame.quit()
                            sys.exit()
                        elif text == "Jouer":
                            mode = self.choose_game_mode()  
                            if mode == "menu": 
                                continue
                            else : 
                                game = Game(self.screen, mode)
                                # Le système de succès sera assigné dans Game.run() selon l'équipe du joueur
                                game.achievements_system_rouge = self.achievements_system_rouge
                                game.achievements_system_vert = self.achievements_system_vert
                                game.run()
                        elif text == "Succès":
                            achievements_menu = AchievementsMenu(self.screen)
                            achievements_menu.set_achievements_systems(None)  # Pas besoin de game dans le menu
                            achievements_menu.run()
                        elif text == "Options":
                            options_menu = OptionsMenu(self.screen)
                            retour = options_menu.run()
                            if type(retour) == tuple and len(retour) == 2:
                                changed, new_gameplay_settings = retour
                                if changed:
                                    # Appliquer les nouveaux paramètres de gameplay au jeu
                                    from Global import set_gameplay_setting
                                    set_gameplay_setting(new_gameplay_settings)
                        elif text == "Tuto":
                            game = Game(self.screen, "tuto")
                            game.achievements_system = self.achievements_system
                            game.run()
                            

                pygame.display.flip()

        except SystemExit:
            # Empêche un traceback en console quand on quitte avec Alt+F4
            pass
        except pygame.error:
            # Cas où la fenêtre est déjà fermée
            pass

