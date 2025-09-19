import pygame
import sys
import math
from Global import *
from Class.Game import Game

class Menu:
    def __init__(self):
        self.screen = pygame.display.set_mode((0, 0), pygame.NOFRAME)
        pygame.display.set_caption("Blue Frontline")
        self.WIDTH, self.HEIGHT = self.screen.get_size()

        self.background = pygame.image.load("./assets/menu/menu.png")
        self.background = pygame.transform.scale(self.background, (self.WIDTH, self.HEIGHT))

        self.font = pygame.font.SysFont(None, 60)

        # Boutons
        start_x = BUTTON_MARGIN_LEFT
        start_y = self.HEIGHT - (3 * BUTTON_HEIGHT + 2 * BUTTON_SPACING) - BUTTON_MARGIN_BOTTOM
        self.buttons = [
            ("Jouer",   start_x, start_y, BUTTON_WIDTH, BUTTON_HEIGHT),
            ("Succès",  start_x, start_y + BUTTON_HEIGHT + BUTTON_SPACING, BUTTON_WIDTH, BUTTON_HEIGHT),
            ("Options", start_x, start_y + BUTTON_HEIGHT + BUTTON_SPACING, BUTTON_WIDTH, BUTTON_HEIGHT),
            ("Quitter", start_x, start_y + 2 * (BUTTON_HEIGHT + BUTTON_SPACING), BUTTON_WIDTH, BUTTON_HEIGHT),
        ]

    def draw_button(self, text, x, y, w, h, hovered):
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

        anchor = "⚓"
        try:
            anchor_font = pygame.font.SysFont("DejaVu Sans", 50)
        except:
            anchor_font = pygame.font.SysFont(None, 50)
        anchor_surf = anchor_font.render(anchor, True, WHITE)
        anchor_rect = anchor_surf.get_rect(midleft=(x + 30, y + h // 2))
        self.screen.blit(anchor_surf, anchor_rect)

        txt = self.font.render(text, True, WHITE)
        txt_rect = txt.get_rect(midleft=(anchor_rect.right + 20, y + h // 2))
        self.screen.blit(txt, txt_rect)

    def run(self):
        menu = True
        while menu:
            mouse_pos = pygame.mouse.get_pos()
            mouse_click = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
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
                        pygame.init()
                        game = Game()
                        game.run()
                        menu = False
                    elif text == "Succès":
                        print("Menu succès...")
                    elif text == "Options":
                        print("Menu options...")

            pygame.display.flip()


