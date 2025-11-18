import pygame
import math
import json
from Global import *
import Global


class OptionsMenu:
    def __init__(self, screen):
        self.screen = screen
        self.WIDTH, self.HEIGHT = self.screen.get_size()
        self.font = pygame.font.SysFont(None, 40)
        self.title_font = pygame.font.SysFont(None, 60)

        self.background = (20, 30, 50)

        self.anchor_img = pygame.image.load(ANCHOR_PATH).convert_alpha()
        self.anchor_img = pygame.transform.smoothscale(
            self.anchor_img, (30, 30))

        self.MARGIN_LEFT = 50
        self.MIN_BUTTON_WIDTH = 250
        self.BUTTON_HEIGHT = 60
        self.VERTICAL_SPACING = 80
        self.BUTTON_PADDING = 80

        # État actuel : 'main' ou 'controls'
        self.current_view = 'main'

        # Pour la vue controls
        self.waiting_for_key = None
        self.scroll_y = 0
        self.scroll_speed = 30
        self.max_scroll = 0

        # Charger les contrôles
        self.load_keys_from_file()
        try:
            controls_keys = Global.get_controls_keys()
            self.controls = {}
            for action, data in controls_keys.items():
                key = data.get("key")
                if isinstance(key, int):
                    self.controls[action] = key
                else:
                    self.controls[action] = get_pygame_key(key)
        except Exception as e:
            print(f"Erreur lors du chargement des contrôles: {e}")
            controls_keys = Global.get_controls_keys()
            self.controls = {action: get_pygame_key(
                data.get("key")) for action, data in controls_keys.items()}

        self.dragging_slider = TIME_MAREE
        self.active_input = None

        # Créer les boutons du menu principal
        self.create_main_menu_buttons()

    def create_main_menu_buttons(self):
        """Crée les boutons du menu principal des options"""
        start_y = 300
        button_width = 300
        center_x = self.WIDTH // 2

        self.main_buttons = [
            {
                "text": "Contrôles",
                "rect": pygame.Rect(
                    center_x - button_width // 2,
                    start_y,
                    button_width,
                    self.BUTTON_HEIGHT
                ),
                "action": "controls"
            },
            {
                "text": "Gameplay",
                "rect": pygame.Rect(
                    center_x - button_width // 2,
                    start_y + self.VERTICAL_SPACING,
                    button_width,
                    self.BUTTON_HEIGHT
                ),
                "action": "gameplay"
            },
            {
                "text": "Audio",
                "rect": pygame.Rect(
                    center_x - button_width // 2,
                    start_y + self.VERTICAL_SPACING * 2,
                    button_width,
                    self.BUTTON_HEIGHT
                ),
                "action": "audio"
            },
            {
                "text": "Quitter le jeu",
                "rect": pygame.Rect(
                    self.WIDTH - button_width - self.MARGIN_LEFT,
                    self.HEIGHT - self.BUTTON_HEIGHT - 20,
                    button_width,
                    self.BUTTON_HEIGHT
                ),
                "action": "quit_game"
            },
            {
                "text": "Retour",
                "rect": pygame.Rect(
                    self.MARGIN_LEFT,
                    self.HEIGHT - self.BUTTON_HEIGHT - 20,
                    250,
                    self.BUTTON_HEIGHT
                ),
                "action": "back"
            }
        ]

    def load_keys_from_file(self):
        """Recharge CONTROLS_KEYS depuis le fichier JSON."""
        try:
            with open(KEYS_PATH, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
                controls_keys = Global.get_controls_keys()
                for action, data in loaded_data.items():
                    if action in controls_keys:
                        controls_keys[action]["key"] = data["key"]
        except Exception as e:
            print(f"Erreur lors du chargement du fichier keys.json: {e}")

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
            controls_keys = Global.get_controls_keys()
            save_data = {}
            for action, data in controls_keys.items():
                save_data[action] = {
                    "description": data["description"],
                    "key": self.get_key_string(self.controls[action]),
                }

            with open(KEYS_PATH, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=4, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des touches: {e}")
            return False

    def draw_gradient_button(self, rect, hovered=False):
        """Dessine un bouton avec dégradé"""
        button_surf = pygame.Surface(
            (rect.width, rect.height), pygame.SRCALPHA)

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

    def draw_main_menu(self):
        """Dessine le menu principal des options"""
        self.screen.fill(self.background)

        # Titre
        title = "OPTIONS"
        title_surf = self.title_font.render(title, True, WHITE)
        title_rect = title_surf.get_rect(midtop=(self.WIDTH // 2, 50))
        self.screen.blit(title_surf, title_rect)

        # Dessiner les boutons
        mouse_pos = pygame.mouse.get_pos()

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

            # Icône ancre
            anchor_rect = self.anchor_img.get_rect(
                midleft=(button["rect"].left + 20, button["rect"].centery)
            )
            self.screen.blit(self.anchor_img, anchor_rect)

            # Texte du bouton
            text_surf = self.font.render(button["text"], True, WHITE)
            text_rect = text_surf.get_rect(
                midleft=(anchor_rect.right + 15, button["rect"].centery)
            )
            self.screen.blit(text_surf, text_rect)

    def draw_control_button(self, key, rect, action):
        """Dessine un bouton de contrôle stylisé"""
        key_width = self.font.render(key, True, WHITE).get_width()
        button_width = max(self.MIN_BUTTON_WIDTH,
                           key_width + self.BUTTON_PADDING)
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
            midleft=(max(220, adapted_rect.right + 40), adapted_rect.centery)
        )
        self.screen.blit(action_surf, action_rect)

        return adapted_rect

    def draw_controls_menu(self):
        """Dessine le menu des contrôles"""
        self.screen.fill(self.background)

        # Titre
        title = "CONTRÔLES"
        title_surf = self.title_font.render(title, True, WHITE)
        title_rect = title_surf.get_rect(midtop=(self.WIDTH // 2, 50))
        self.screen.blit(title_surf, title_rect)

        # Affichage des contrôles avec scroll
        y_pos = 150
        control_rects = {}
        scrollable_bottom = self.HEIGHT - self.BUTTON_HEIGHT - 40

        controls_keys = Global.get_controls_keys()
        for control_name, control_info in controls_keys.items():
            scrolled_y = y_pos - self.scroll_y

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

        # Ligne de séparation
        separator_y = self.HEIGHT - self.BUTTON_HEIGHT - 30
        pygame.draw.line(self.screen, LIGHT_BLUE,
                         (self.MARGIN_LEFT, separator_y),
                         (self.WIDTH - self.MARGIN_LEFT, separator_y), 2)

        # Bouton retour
        back_button_rect = pygame.Rect(
            self.MARGIN_LEFT,
            self.HEIGHT - self.BUTTON_HEIGHT - 20,
            250,
            self.BUTTON_HEIGHT
        )
        mouse_pos = pygame.mouse.get_pos()
        hovered = back_button_rect.collidepoint(mouse_pos)

        back_surf = self.draw_gradient_button(back_button_rect, hovered)
        self.screen.blit(back_surf, back_button_rect)
        pygame.draw.rect(self.screen, WHITE, back_button_rect,
                         3, border_radius=BUTTON_BORDER_RADIUS)

        anchor_rect = self.anchor_img.get_rect(
            midleft=(back_button_rect.left + 20, back_button_rect.centery)
        )
        self.screen.blit(self.anchor_img, anchor_rect)

        back_text = self.font.render("Retour", True, WHITE)
        back_rect = back_text.get_rect(
            midleft=(anchor_rect.right + 10, back_button_rect.centery)
        )
        self.screen.blit(back_text, back_rect)

        return control_rects, back_button_rect

    def draw_gameplay_menu(self):
        """Dessine le menu Gameplay en grille responsive et retourne les zones interactives"""
        self.screen.fill(self.background)

        title = "GAMEPLAY"
        title_surf = self.title_font.render(title, True, WHITE)
        title_rect = title_surf.get_rect(midtop=(self.WIDTH // 2, 50))
        self.screen.blit(title_surf, title_rect)

        gameplay_settings = Global.get_gameplay_settings()
        interactive_rects = {}

        # === Layout ===
        margin = self.MARGIN_LEFT
        spacing_x = 40
        spacing_y = 40
        button_height = self.BUTTON_HEIGHT
        button_width = 250
        start_y = 150

        # === 1. IA ===
        ia_settings = gameplay_settings["AI_ACTIVATION"]
        ia_x = margin
        ia_y = start_y
        ia_width = 425 * 2  # Largeur * 2 Colonnes
        ia_rect_height = (len(ia_settings) * (button_height + 10) + 20) / 2
        ia_rect = pygame.Rect(ia_x - 20, ia_y - 10, ia_width, ia_rect_height)
        pygame.draw.rect(self.screen, LIGHT_BLUE, ia_rect, 2, border_radius=10)

        for i, (unit, active) in enumerate(ia_settings.items()):
            # Détermine la position
            if i % 2 == 0:
                # Colonne de gauche
                x = ia_x
                y = ia_y + (i // 2) * (button_height + 10)
            else:
                # Colonne de droite
                x = ia_x + ia_width // 2 + 20  # décale à droite
                y = ia_y + (i // 2) * (button_height + 10)

            # Texte
            text_color = WHITE
            # # Si l'unité commence par Eclaireur
            # if unit.startswith("Eclaireur"):
            #     text_color = (120, 120, 120)
            #     active = True

            text_surf = self.font.render(f"{unit}", True, text_color)
            self.screen.blit(text_surf, (x, y + button_height //
                             2 - text_surf.get_height() // 2))

            # Bouton ON/OFF
            button_rect = pygame.Rect(x + 250, y, 120, button_height)
            hovered = button_rect.collidepoint(pygame.mouse.get_pos())
            button_surf = self.draw_gradient_button(button_rect, hovered)
            self.screen.blit(button_surf, button_rect)
            pygame.draw.rect(self.screen, WHITE, button_rect,
                             2, border_radius=BUTTON_BORDER_RADIUS)

            # Texte ON/OFF centré
            state_text = "ON" if active else "OFF"
            state_surf = self.font.render(state_text, True, WHITE)
            state_rect = state_surf.get_rect(center=button_rect.center)
            self.screen.blit(state_surf, state_rect)

            # Interaction
            interactive_rects[f"IA_{unit}"] = button_rect

        # === 2. Autres paramètres ===
        param_x = ia_x + ia_width + spacing_x
        param_y = start_y
        max_width = self.WIDTH - margin

        # --- Temps Marée (slider) ---
        slider_width = 300
        slider_height = 20
        slider_x = param_x
        slider_y = param_y + button_height // 2 - slider_height // 2

        # Track
        track_rect = pygame.Rect(
            slider_x, slider_y, slider_width, slider_height)
        pygame.draw.rect(self.screen, OCEAN_BLUE, track_rect, border_radius=10)

        # Curseur
        time_val = gameplay_settings['TIME_MAREE']
        time_min = 30
        time_max = 360
        cursor_pos = int(slider_x + ((time_val - time_min) /
                         (time_max - time_min)) * slider_width)
        cursor_rect = pygame.Rect(
            cursor_pos - 10, slider_y - 5, 20, slider_height + 10)
        pygame.draw.rect(self.screen, LIGHT_BLUE, cursor_rect, border_radius=5)

        # Texte
        text_surf = self.font.render(f"Temps Marée: {time_val}s", True, WHITE)
        self.screen.blit(text_surf, (slider_x, slider_y - 30))
        interactive_rects["TIME_MAREE"] = track_rect
        interactive_rects["TIME_MAREE_CURSOR"] = cursor_rect

        # Avancer x et y pour la grille
        param_y += button_height + 2 * spacing_y
        param_x_start = param_x

        # --- Pétrole / sec (input) ---
        rect = pygame.Rect(param_x, param_y, button_width, button_height)
        pygame.draw.rect(self.screen, OCEAN_BLUE, rect, border_radius=10)
        pygame.draw.rect(self.screen, WHITE, rect, 3,
                         border_radius=BUTTON_BORDER_RADIUS)
        value_str = str(gameplay_settings['OIL_PER_SECOND'])
        text_surf = self.font.render(
            f"Pétrole / sec: {value_str}", True, WHITE)
        self.screen.blit(
            text_surf, (rect.x + 10, rect.centery - text_surf.get_height()//2))
        interactive_rects["OIL_PER_SECOND"] = rect

        # --- Pièces / kill (input) ---
        param_x += button_width + spacing_x
        if param_x + button_width > max_width:
            param_x = param_x_start
            param_y += button_height + spacing_y
        rect = pygame.Rect(param_x, param_y, button_width, button_height)
        pygame.draw.rect(self.screen, OCEAN_BLUE, rect, border_radius=10)
        pygame.draw.rect(self.screen, WHITE, rect, 3,
                         border_radius=BUTTON_BORDER_RADIUS)
        value_str = str(gameplay_settings['PIECE_PER_KILL'])
        text_surf = self.font.render(
            f"Pièces / Kill: {value_str}", True, WHITE)
        self.screen.blit(
            text_surf, (rect.x + 10, rect.centery - text_surf.get_height()//2))
        interactive_rects["PIECE_PER_KILL"] = rect

        # Bouton Appliquer
        apply_rect = pygame.Rect(
            self.WIDTH - 270, self.HEIGHT - self.BUTTON_HEIGHT - 20, 250, self.BUTTON_HEIGHT)
        hovered = apply_rect.collidepoint(pygame.mouse.get_pos())
        apply_surf = self.draw_gradient_button(apply_rect, hovered)
        self.screen.blit(apply_surf, apply_rect)
        pygame.draw.rect(self.screen, WHITE, apply_rect, 3,
                         border_radius=BUTTON_BORDER_RADIUS)
        apply_text = self.font.render("Appliquer", True, WHITE)
        self.screen.blit(apply_text, (apply_rect.x + 20,
                         apply_rect.centery - apply_text.get_height() // 2))
        interactive_rects["apply"] = apply_rect

        # --- Bouton retour ---
        back_rect = pygame.Rect(margin, self.HEIGHT -
                                button_height - 20, 250, button_height)
        hovered = back_rect.collidepoint(pygame.mouse.get_pos())
        back_surf = self.draw_gradient_button(back_rect, hovered)
        self.screen.blit(back_surf, back_rect)
        pygame.draw.rect(self.screen, WHITE, back_rect, 3,
                         border_radius=BUTTON_BORDER_RADIUS)
        back_text = self.font.render("Retour", True, WHITE)
        self.screen.blit(back_text, (back_rect.x + 20,
                         back_rect.centery - back_text.get_height() // 2))
        interactive_rects["back"] = back_rect

        return interactive_rects

    def handle_key_binding(self, event, control_name):
        """Gère l'attribution d'une nouvelle touche"""
        if event.type == pygame.KEYDOWN:
            self.controls[control_name] = event.key
            self.save_keys()
            self.waiting_for_key = None
            return True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.controls[control_name] = event.button
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

    def handle_scroll(self, scroll_direction):
        """Gère le défilement du menu"""
        self.scroll_y += scroll_direction * self.scroll_speed
        self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))

    def run(self):
        """Exécute la boucle du menu options"""
        running = True
        clock = pygame.time.Clock()

        while running:
            # Dessiner la vue appropriée
            if self.current_view == 'main':
                self.draw_main_menu()
                interactive_rects = None
            elif self.current_view == 'controls':
                control_rects, back_button_rect = self.draw_controls_menu()
                interactive_rects = None
            elif self.current_view == 'gameplay':
                interactive_rects = self.draw_gameplay_menu()

            pygame.display.flip()
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False

                # Gestion des touches dans le menu contrôles
                if self.current_view == 'controls' and self.waiting_for_key:
                    if self.handle_key_binding(event, self.waiting_for_key):
                        continue

                elif event.type == pygame.KEYDOWN:

                    if self.active_input:
                        gameplay_settings = Global.get_gameplay_settings()
                        val_str = str(gameplay_settings[self.active_input])

                        if event.key == pygame.K_BACKSPACE:
                            val_str = val_str[:-1]
                        elif event.unicode.isdigit():  # on n'ajoute que les chiffres
                            val_str += event.unicode
                        elif event.key == pygame.K_RETURN:
                            self.active_input = None  # fin de saisie

                        # Mettre à jour la valeur numérique
                        if val_str.isdigit():
                            gameplay_settings[self.active_input] = int(val_str)
                        else:
                            gameplay_settings[self.active_input] = 0

                    if event.key == pygame.K_ESCAPE:
                        if self.current_view == 'main':
                            return True
                        elif self.current_view in ['controls', 'gameplay'] and not self.waiting_for_key:
                            self.current_view = 'main'
                            self.scroll_y = 0

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()

                    if event.button == 1:  # Clic gauche
                        if self.current_view == 'main':
                            for button in self.main_buttons:
                                if button["rect"].collidepoint(mouse_pos):
                                    if button["action"] == "back":
                                        return True
                                    elif button["action"] == "controls":
                                        self.current_view = 'controls'
                                    elif button["action"] == "gameplay":
                                        self.current_view = 'gameplay'
                                    elif button["action"] == "audio":
                                        print("Menu Audio à implémenter")
                                    elif button["action"] == "quit_game":
                                        pygame.quit()
                                        import sys
                                        sys.exit()
                                    break

                        elif self.current_view == 'controls':
                            if back_button_rect.collidepoint(mouse_pos):
                                self.current_view = 'main'
                                self.scroll_y = 0
                            else:
                                for control_name, rect in control_rects.items():
                                    if rect.collidepoint(mouse_pos):
                                        self.waiting_for_key = control_name
                                        break

                        elif self.current_view == 'gameplay' and interactive_rects:
                            for key, rect in interactive_rects.items():
                                if rect.collidepoint(mouse_pos):
                                    gameplay_settings = Global.get_gameplay_settings()
                                    if key.startswith("IA_"):
                                        unit = key[3:]
                                        gameplay_settings["AI_ACTIVATION"][unit] = not gameplay_settings["AI_ACTIVATION"][unit]
                                    elif key == "TIME_MAREE":
                                        self.dragging_slider = "TIME_MAREE"
                                    elif key in ["OIL_PER_SECOND", "PIECE_PER_KILL"]:
                                        self.active_input = key
                                    elif key == "back":
                                        self.current_view = 'main'
                                    elif key == "apply":
                                        # Appliquer les changements au moteur de jeu
                                        return True, GAMEPLAY_SETTINGS
                                    break

                    elif event.button == 4 and self.current_view == 'controls':  # Molette haut
                        self.handle_scroll(-1)
                    elif event.button == 5 and self.current_view == 'controls':  # Molette bas
                        self.handle_scroll(1)

                elif event.type == pygame.MOUSEBUTTONUP:
                    # Relâchement de la souris
                    if self.dragging_slider == "TIME_MAREE":
                        self.dragging_slider = None

                elif event.type == pygame.MOUSEMOTION:
                    # Déplacement du curseur
                    if self.dragging_slider == "TIME_MAREE" and interactive_rects:
                        mouse_x = pygame.mouse.get_pos()[0]
                        slider_x = interactive_rects["TIME_MAREE"].x
                        slider_width = interactive_rects["TIME_MAREE"].width
                        # Limiter à la track
                        mouse_x = max(slider_x, min(
                            slider_x + slider_width, mouse_x))
                        # Calculer la valeur proportionnelle
                        time_min = 30
                        time_max = 360
                        proportion = (mouse_x - slider_x) / slider_width
                        gameplay_settings = Global.get_gameplay_settings()
                        gameplay_settings["TIME_MAREE"] = int(
                            time_min + proportion * (time_max - time_min))

        return True
