import pygame
import math
import json
from Global import *

class OptionsMenu:
    def __init__(self, screen):
        self.screen = screen
        self.WIDTH, self.HEIGHT = self.screen.get_size()
        self.font = pygame.font.SysFont(None, 40)
        self.title_font = pygame.font.SysFont(None, 60)

        self.background = (20, 30, 50)

        self.anchor_img = pygame.image.load(ANCHOR_PATH).convert_alpha()
        self.anchor_img = pygame.transform.smoothscale(self.anchor_img, (30, 30))

        self.MARGIN_LEFT = 50
        self.MIN_BUTTON_WIDTH = 180
        self.BUTTON_HEIGHT = 50
        self.ACTION_MARGIN = 220
        self.VERTICAL_SPACING = 60
        self.BUTTON_PADDING = 80

        back_text_width = self.font.render("Retour", True, WHITE).get_width()
        back_button_width = max(
            self.MIN_BUTTON_WIDTH, back_text_width + self.BUTTON_PADDING
        )
        
        # Scroll
        self.scroll_y = 0
        self.scroll_speed = 30
        self.max_scroll = 0
        
        # Position initiale du bouton retour (sera mise à jour dans draw)
        self.back_button_base_y = 0

        self.back_button = {
            "text": "Retour",
            "rect": pygame.Rect(
                self.MARGIN_LEFT,
                0,
                back_button_width,
                self.BUTTON_HEIGHT,
            ),
        }

        self.waiting_for_key = None
        try:
            self.controls = {
                action: get_pygame_key(data.get("key"))
                for action, data in CONTROLS_KEYS.items()
            }
        except Exception:
            self.controls = CONTROLS_KEYS.copy()

    def get_key_string(self, key_value):
        """Convertit une valeur de touche pygame en chaîne pour la sauvegarde JSON."""
        if isinstance(key_value, int):
            for name in dir(pygame):
                if name.startswith("K_") or name.startswith("BUTTON_"):
                    try:
                        if getattr(pygame, name) == key_value:
                            return name
                    except:
                        continue
        return str(key_value)

    def save_keys(self):
        """Sauvegarde les touches de contrôle dans le fichier keys.json."""
        try:
            save_data = {}
            for action, data in CONTROLS_KEYS.items():
                save_data[action] = {
                    "description": data["description"],
                    "key": self.get_key_string(data["key"]),
                }

            with open(KEYS_PATH, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=4, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des touches: {e}")
            return False

    def draw_gradient_button(self, rect, hovered=False):
        """Dessine un bouton avec dégradé comme dans le menu principal"""
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

    def draw_control_button(self, key, rect, action):
        """Dessine un bouton de contrôle stylisé avec largeur adaptée"""
        key_width = self.font.render(key, True, WHITE).get_width()
        button_width = max(self.MIN_BUTTON_WIDTH, key_width + self.BUTTON_PADDING)

        adapted_rect = pygame.Rect(rect.x, rect.y, button_width, rect.height)

        is_selected = self.waiting_for_key and action == self.waiting_for_key
        button_surf = self.draw_gradient_button(adapted_rect, is_selected)

        self.screen.blit(button_surf, adapted_rect)
        pygame.draw.rect(
            self.screen,
            LIGHT_BLUE if is_selected else WHITE,
            adapted_rect,
            2,
            border_radius=BUTTON_BORDER_RADIUS,
        )

        anchor_rect = self.anchor_img.get_rect(
            midleft=(adapted_rect.x + 20, adapted_rect.centery)
        )
        self.screen.blit(self.anchor_img, anchor_rect)

        key_surf = self.font.render(key, True, WHITE)
        key_rect = key_surf.get_rect(
            midleft=(anchor_rect.right + 10, adapted_rect.centery)
        )
        self.screen.blit(key_surf, key_rect)

        action_surf = self.font.render(action, True, WHITE)
        action_rect = action_surf.get_rect(
            midleft=(
                max(self.ACTION_MARGIN, adapted_rect.right + 40),
                adapted_rect.centery,
            )
        )
        self.screen.blit(action_surf, action_rect)

        return adapted_rect

    def handle_key_binding(self, event, control_name):
        """Gère l'attribution d'une nouvelle touche"""
        if event.type == pygame.KEYDOWN:
            self.controls[control_name] = event.key
            CONTROLS_KEYS[control_name]["key"] = event.key
            self.save_keys()
            self.waiting_for_key = None
            return True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.controls[control_name] = event.button
            CONTROLS_KEYS[control_name]["key"] = event.button
            self.save_keys()
            self.waiting_for_key = None
            return True
        return False

    def get_key_name(self, key_value):
        """Convertit une valeur de touche en nom lisible"""
        if isinstance(key_value, int):
            if key_value >= pygame.BUTTON_LEFT and key_value <= pygame.BUTTON_WHEELDOWN:
                button_names = {
                    pygame.BUTTON_LEFT: "CLIC GAUCHE",
                    pygame.BUTTON_RIGHT: "CLIC DROIT",
                    pygame.BUTTON_WHEELUP: "MOLETTE HAUT",
                    pygame.BUTTON_WHEELDOWN: "MOLETTE BAS",
                }
                return button_names.get(key_value, str(key_value))
            return pygame.key.name(key_value).upper()
        return str(key_value)

    def draw(self):
        """Dessine le menu des options"""
        self.screen.fill(self.background)

        # Titre centré (fixe, ne scroll pas)
        title = "OPTIONS"
        title_surf = self.title_font.render(title, True, WHITE)
        title_rect = title_surf.get_rect(midtop=(self.WIDTH // 2, 50))
        self.screen.blit(title_surf, title_rect)

        # Sous-titre (scrollable)
        subtitle_y = 120 - self.scroll_y
        subtitle = "Contrôles"
        subtitle_surf = self.font.render(subtitle, True, LIGHT_BLUE)
        subtitle_rect = subtitle_surf.get_rect(topleft=(self.MARGIN_LEFT, subtitle_y))
        self.screen.blit(subtitle_surf, subtitle_rect)

        # Affichage des contrôles avec scroll
        y_pos = 180
        control_rects = {}

        # Zone limite avant le bouton retour (avec marge de sécurité)
        scrollable_bottom = self.HEIGHT - self.BUTTON_HEIGHT - 40
        
        for control_name, control_info in CONTROLS_KEYS.items():
            # Appliquer le scroll à la position Y
            scrolled_y = y_pos - self.scroll_y
            
            # N'afficher que si visible dans la zone scrollable
            if -self.BUTTON_HEIGHT <= scrolled_y <= scrollable_bottom:
                key_name = self.get_key_name(self.controls[control_name])
                base_rect = pygame.Rect(
                    self.MARGIN_LEFT, scrolled_y, self.MIN_BUTTON_WIDTH, self.BUTTON_HEIGHT
                )
                control_rect = self.draw_control_button(
                    key_name, base_rect, control_info["description"]
                )
                control_rects[control_name] = control_rect
            
            y_pos += self.VERTICAL_SPACING

        # Calculer le scroll maximum
        total_content_height = y_pos
        self.max_scroll = max(0, total_content_height - scrollable_bottom + 20)
        
        # Ligne de séparation (optionnelle)
        separator_y = self.HEIGHT - self.BUTTON_HEIGHT - 30
        pygame.draw.line(self.screen, LIGHT_BLUE, 
                        (self.MARGIN_LEFT, separator_y), 
                        (self.WIDTH - self.MARGIN_LEFT, separator_y), 2)
        
        # Positionner le bouton retour en bas de l'écran (fixe, ne scroll pas)
        self.back_button["rect"].y = self.HEIGHT - self.BUTTON_HEIGHT - 20
        
        self._draw_back_button()

        return control_rects

    def _draw_back_button(self):
        """Dessine le bouton retour"""
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.back_button["rect"].collidepoint(mouse_pos)
        back_surf = self.draw_gradient_button(self.back_button["rect"], hovered)
        self.screen.blit(back_surf, self.back_button["rect"])
        pygame.draw.rect(
            self.screen,
            WHITE,
            self.back_button["rect"],
            4,
            border_radius=BUTTON_BORDER_RADIUS,
        )

        anchor_rect = self.anchor_img.get_rect(
            midleft=(
                self.back_button["rect"].left + 20,
                self.back_button["rect"].centery,
            )
        )
        self.screen.blit(self.anchor_img, anchor_rect)

        back_text = self.font.render(self.back_button["text"], True, WHITE)
        back_rect = back_text.get_rect(
            midleft=(anchor_rect.right + 10, self.back_button["rect"].centery)
        )
        self.screen.blit(back_text, back_rect)
        
    def handle_scroll(self, scroll_direction):
        """Gère le défilement du menu.
        
        Args:
            scroll_direction (int): 1 pour vers le haut, -1 pour vers le bas
        """
        self.scroll_y += scroll_direction * self.scroll_speed
        self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))

    def run(self):
        """Exécute la boucle du menu options"""
        running = True
        clock = pygame.time.Clock()
        
        while running:
            control_rects = self.draw()
            pygame.display.flip()
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False

                if self.waiting_for_key:
                    if self.handle_key_binding(event, self.waiting_for_key):
                        continue

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if not self.waiting_for_key:
                            return True

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Clic gauche
                        mouse_pos = pygame.mouse.get_pos()
                        if self.back_button["rect"].collidepoint(mouse_pos):
                            return True

                        for control_name, rect in control_rects.items():
                            if rect.collidepoint(mouse_pos):
                                self.waiting_for_key = control_name
                                break
                    elif event.button == 4:  # Molette haut
                        self.handle_scroll(-1)  # Scroll vers le haut
                    elif event.button == 5:  # Molette bas
                        self.handle_scroll(1)   # Scroll vers le bas