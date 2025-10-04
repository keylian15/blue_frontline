import pygame
import math
from Global import *

class OptionsMenu:
    def __init__(self, screen):
        self.screen = screen
        self.WIDTH, self.HEIGHT = self.screen.get_size()
        self.font = pygame.font.SysFont(None, 40)
        self.title_font = pygame.font.SysFont(None, 60)
        
        self.background = pygame.image.load(MENU_PATH).convert_alpha()
        self.background = pygame.transform.scale(self.background, (self.WIDTH, self.HEIGHT))
        
        self.anchor_img = pygame.image.load(ANCHOR_PATH).convert_alpha()
        self.anchor_img = pygame.transform.smoothscale(self.anchor_img, (30, 30))
        
        self.MARGIN_LEFT = 50
        self.MIN_BUTTON_WIDTH = 180
        self.BUTTON_HEIGHT = 50
        self.ACTION_MARGIN = 220
        self.VERTICAL_SPACING = 60
        self.BUTTON_PADDING = 80

        back_text_width = self.font.render('Retour', True, WHITE).get_width()
        back_button_width = max(self.MIN_BUTTON_WIDTH, back_text_width + self.BUTTON_PADDING)
        
        self.back_button = {
            'text': 'Retour',
            'rect': pygame.Rect(self.MARGIN_LEFT, self.HEIGHT - 70, back_button_width, self.BUTTON_HEIGHT)
        }

        self.waiting_for_key = None
        self.controls = CONTROLS_KEYS.copy()
        
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
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, rect.width, rect.height), 
                        border_radius=BUTTON_BORDER_RADIUS)
        button_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        return button_surf

    def draw_control_button(self, key, rect, action):
        """Dessine un bouton de contrôle stylisé avec largeur adaptée"""
        key_width = self.font.render(key, True, WHITE).get_width()
        button_width = max(self.MIN_BUTTON_WIDTH, key_width + self.BUTTON_PADDING)
        
        adapted_rect = pygame.Rect(rect.x, rect.y, button_width, rect.height)
        
        # Change la couleur si en attente d'une touche
        is_selected = self.waiting_for_key and action == self.waiting_for_key
        button_surf = self.draw_gradient_button(adapted_rect, is_selected)
        
        self.screen.blit(button_surf, adapted_rect)
        pygame.draw.rect(self.screen, LIGHT_BLUE if is_selected else WHITE, 
                        adapted_rect, 2, border_radius=BUTTON_BORDER_RADIUS)
        
        anchor_rect = self.anchor_img.get_rect(midleft=(adapted_rect.x + 20, adapted_rect.centery))
        self.screen.blit(self.anchor_img, anchor_rect)
        
        key_surf = self.font.render(key, True, WHITE)
        key_rect = key_surf.get_rect(midleft=(anchor_rect.right + 10, adapted_rect.centery))
        self.screen.blit(key_surf, key_rect)
        
        action_surf = self.font.render(action, True, WHITE)
        action_rect = action_surf.get_rect(
            midleft=(max(self.ACTION_MARGIN, adapted_rect.right + 40), adapted_rect.centery)
        )
        self.screen.blit(action_surf, action_rect)
        
        return adapted_rect  # Retourne le rectangle pour la détection des clics

    def handle_key_binding(self, event, control_name):
        """Gère l'attribution d'une nouvelle touche"""
        if event.type == pygame.KEYDOWN:
            self.controls[control_name] = event.key
            # Mettre à jour immédiatement la touche dans CONTROLS_KEYS
            CONTROLS_KEYS[control_name]["key"] = event.key
            self.waiting_for_key = None
            return True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.controls[control_name] = event.button
            # Mettre à jour immédiatement la touche dans CONTROLS_KEYS
            CONTROLS_KEYS[control_name]["key"] = event.button
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
                    pygame.BUTTON_WHEELDOWN: "MOLETTE BAS"
                }
                return button_names.get(key_value, str(key_value))
            return pygame.key.name(key_value).upper()
        return str(key_value)

    def draw(self):
        """Dessine le menu des options"""
        # Afficher le fond
        self.screen.blit(self.background, (0, 0))

        # Titre centré
        title = "OPTIONS"
        title_surf = self.title_font.render(title, True, WHITE)
        title_rect = title_surf.get_rect(midtop=(self.WIDTH // 2, 50))
        self.screen.blit(title_surf, title_rect)

        # Sous-titre aligné avec les contrôles
        subtitle = "Contrôles"
        subtitle_surf = self.font.render(subtitle, True, LIGHT_BLUE)
        subtitle_rect = subtitle_surf.get_rect(topleft=(self.MARGIN_LEFT, 120))
        self.screen.blit(subtitle_surf, subtitle_rect)

        # Récupération et affichage des contrôles depuis Global
        y_pos = 180
        control_rects = {}  # Pour stocker les rectangles des contrôles
        
        for control_name, control_info in CONTROLS_KEYS.items():
            key_name = self.get_key_name(self.controls[control_name])
            base_rect = pygame.Rect(
                self.MARGIN_LEFT, 
                y_pos - 5, 
                self.MIN_BUTTON_WIDTH,
                self.BUTTON_HEIGHT
            )
            control_rect = self.draw_control_button(key_name, base_rect, control_info["description"])
            control_rects[control_name] = control_rect
            y_pos += self.VERTICAL_SPACING

        # Dessin du bouton retour
        self._draw_back_button()
        
        return control_rects

    def _draw_back_button(self):
        """Dessine le bouton retour"""
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.back_button['rect'].collidepoint(mouse_pos)
        back_surf = self.draw_gradient_button(self.back_button['rect'], hovered)
        self.screen.blit(back_surf, self.back_button['rect'])
        pygame.draw.rect(self.screen, WHITE, self.back_button['rect'], 4, 
                        border_radius=BUTTON_BORDER_RADIUS)
        
        # Ajout de l'ancre avec l'image
        anchor_rect = self.anchor_img.get_rect(
            midleft=(self.back_button['rect'].left + 20, self.back_button['rect'].centery)
        )
        self.screen.blit(self.anchor_img, anchor_rect)
        
        # Texte du bouton retour
        back_text = self.font.render(self.back_button['text'], True, WHITE)
        back_rect = back_text.get_rect(
            midleft=(anchor_rect.right + 10, self.back_button['rect'].centery)
        )
        self.screen.blit(back_text, back_rect)

    def run(self):
        """Exécute la boucle du menu options"""
        running = True
        while running:
            control_rects = self.draw()
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                    
                if self.waiting_for_key:
                    if self.handle_key_binding(event, self.waiting_for_key):
                        continue
                        
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if not self.waiting_for_key:
                            # Plus besoin de faire un update ici car les changements sont déjà appliqués
                            return True
                            
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Clic gauche
                        mouse_pos = pygame.mouse.get_pos()
                        if self.back_button['rect'].collidepoint(mouse_pos):
                            # Plus besoin de faire un update ici car les changements sont déjà appliqués
                            return True
                            
                        # Vérification des clics sur les contrôles
                        for control_name, rect in control_rects.items():
                            if rect.collidepoint(mouse_pos):
                                self.waiting_for_key = control_name
                                break