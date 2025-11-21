import pygame


class OverlayMenu:
    """Menu superposé affichable au-dessus du jeu."""

    def __init__(self, screen, game: "Game"):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.show = False  # affichage activé/désactivé
        self.player_team = 'red'
        self.game = game

        # Police
        self.font = pygame.font.Font(None, 32)

        # Système d'améliorations
        self.upgrades = {
            'red': {
                'destruction': {'level': 1, 'values': [1, 2, 3, 4], 'costs': [0, 100, 200, 500]},
                'degat': {'level': 1, 'values': [10, 20, 30, 40], 'costs': [0, 200, 400, 600]},
                'vitesse': {'level': 1, 'values': [1, 2, 3, 4], 'costs': [0, 200, 400, 600]}
            },
            'green': {
                'destruction': {'level': 1, 'values': [1, 2, 3, 4], 'costs': [0, 100, 200, 500]},
                'degat': {'level': 1, 'values': [10, 20, 30, 40], 'costs': [0, 200, 400, 600]},
                'vitesse': {'level': 1, 'values': [1, 2, 3, 4], 'costs': [0, 200, 400, 600]}
            }
        }

        # Définition des boutons
        self.buttons = []
        self.create_button("Destruction", "destruction",
                           "pièce", lambda: self.upgrade("destruction"))
        self.create_button("Dégat", "degat", "% blindage",
                           lambda: self.upgrade("degat"))
        self.create_button("Vitesse", "vitesse", "tirs/4s",
                           lambda: self.upgrade("vitesse"))

        # Positionnement vertical des boutons
        self.position_buttons()

    def create_button(self, label: str, upgrade_name: str, unit: str, action: callable):
        """Crée un bouton et l'ajoute à la liste."""
        button = {
            "label": label,
            "upgrade_name": upgrade_name,
            "unit": unit,
            "rect": pygame.Rect(0, 0, 400, 80),
            "action": action
        }
        self.buttons.append(button)

    def get_button_text(self, btn):
        """Génère le texte à afficher sur un bouton."""
        upgrade = self.upgrades[self.player_team][btn["upgrade_name"]]
        current_level = upgrade['level']
        current_value = upgrade['values'][current_level - 1]

        # Texte de base avec niveau actuel
        text = f"\n{btn['label']} Lvl.{current_level} - {current_value} {btn['unit']}"

        # Si pas au niveau max, afficher le prochain niveau
        if current_level < 4:
            next_value = upgrade['values'][current_level]
            next_cost = upgrade['costs'][current_level]
            text += f"\n-> Lvl.{current_level + 1} - {next_value} {btn['unit']}, coût {next_cost} pièces"
        else:
            text += "\n(MAX)"

        return text

    def upgrade(self, upgrade_name: str):
        """Effectue une amélioration."""
        upgrade = self.upgrades[self.player_team][upgrade_name]
        if upgrade['level'] >= 4:
            return

        cost = upgrade['costs'][upgrade['level']]
        upgrade['level'] += 1
        team = self.player_team
        hud_piece = self.game.hud.piece_red if team == 'red' else self.game.hud.piece_green
        plateforme = self.game.plateformes[team]

        hud_piece.count -= cost
        value = upgrade['values'][upgrade['level'] - 1]

        if upgrade_name == "destruction":
            hud_piece.multiplicateur = value
        elif upgrade_name == "degat":
            from Global import UNIT_CONFIGS
            plateforme.damage = UNIT_CONFIGS["chaloupe"]["max_health"] * value / 100
        elif upgrade_name == "vitesse":
            plateforme.fire_rate = value / 4

    def position_buttons(self):
        """Positionne tous les boutons verticalement."""
        total_height = len(self.buttons) * 100
        start_y = (self.height - total_height) // 2 + \
            50  # Décalé pour le titre
        for i, btn in enumerate(self.buttons):
            btn["rect"].center = (self.width * 0.85, start_y + i * 100)

    def switch(self):
        """Afficher ou cacher le menu."""
        self.show = not self.show

    def handle_event(self, event: any):
        """Gère les clics sur les boutons."""
        if not self.show:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # Vérifier si on clique sur la croix
            if hasattr(self, 'close_button_rect') and self.close_button_rect.collidepoint(mouse_pos):
                self.game.select_unit(None)
                self.switch()
                return

            pieces = self.game.hud.piece_red.count if self.player_team == 'red' else self.game.hud.piece_green.count

            for btn in self.buttons:
                if btn["rect"].collidepoint(mouse_pos):
                    upgrade = self.upgrades[self.player_team][btn["upgrade_name"]]
                    # Vérifie si on peut acheter
                    if upgrade['level'] < 4:
                        next_cost = upgrade['costs'][upgrade['level']]
                        if pieces >= next_cost:
                            btn["action"]()

    def draw(self):
        """Affiche le menu (si activé)."""
        if not self.show:
            return

        # Ajout du titre avec fond
        couleur = "rouge" if self.player_team == 'red' else "verte"
        title_text = f"Améliorations {couleur}"
        title_surface = self.font.render(title_text, True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(self.width * 0.9, 50))

        # Fond du titre
        title_bg = pygame.Rect(title_rect.x - 20, title_rect.y - 10,
                               title_rect.width + 40, title_rect.height + 20)
        pygame.draw.rect(self.screen, (50, 50, 150),
                         title_bg, border_radius=10)
        self.screen.blit(title_surface, title_rect)

        # Bouton croix pour fermer
        close_button_size = 30
        close_button_rect = pygame.Rect(
            title_rect.right + 10,
            title_rect.centery - close_button_size // 2,
            close_button_size,
            close_button_size
        )

        # Fond de la croix
        pygame.draw.rect(self.screen, (180, 50, 50),
                         close_button_rect, border_radius=5)
        pygame.draw.rect(self.screen, (255, 255, 255),
                         close_button_rect, width=2, border_radius=5)

        # Dessiner la croix (X)
        padding = 8
        pygame.draw.line(self.screen, (255, 255, 255),
                         (close_button_rect.left + padding,
                          close_button_rect.top + padding),
                         (close_button_rect.right - padding, close_button_rect.bottom - padding), 3)
        pygame.draw.line(self.screen, (255, 255, 255),
                         (close_button_rect.right - padding,
                          close_button_rect.top + padding),
                         (close_button_rect.left + padding, close_button_rect.bottom - padding), 3)

        # Stocker le rect pour la détection de clic
        self.close_button_rect = close_button_rect

        # Récupère les pièces disponibles
        pieces = self.game.hud.piece_red.count if self.player_team == 'red' else self.game.hud.piece_green.count

        # Dessin des boutons
        for btn in self.buttons:
            # Couleur selon survol et niveau max
            upgrade = self.upgrades[self.player_team][btn["upgrade_name"]]
            is_max = upgrade['level'] >= 4

            # Vérifie si on peut acheter
            can_afford = True
            if not is_max:
                next_cost = upgrade['costs'][upgrade['level']]
                can_afford = pieces >= next_cost

            # Couleur selon l'état
            if is_max:
                color = (50, 150, 50)  # Vert si max
            elif not can_afford:
                color = (180, 50, 50)  # Rouge si pas assez
            else:
                color = (100, 100, 255)  # Bleu normal

            # Ombre du bouton
            shadow_rect = btn["rect"].copy()
            shadow_rect.x += 4
            shadow_rect.y += 4
            pygame.draw.rect(self.screen, (20, 20, 20),
                             shadow_rect, border_radius=10)

            # Bouton principal
            pygame.draw.rect(self.screen, color, btn["rect"], border_radius=10)

            # Bordure
            if not can_afford and not is_max:
                border_color = (200, 100, 100)  # Bordure rouge si pas assez
            else:
                border_color = (150, 150, 200)
            pygame.draw.rect(self.screen, border_color, btn["rect"],
                             width=2, border_radius=10)

            # Texte sur plusieurs lignes
            text = self.get_button_text(btn)
            lines = text.split('\n')

            y_offset = btn["rect"].centery - (len(lines) * 16)
            for i, line in enumerate(lines):
                # Première ligne en gras (titre)
                font_size = 34 if i == 0 else 28
                font = pygame.font.Font(None, font_size)

                text_surface = font.render(line, True, (255, 255, 255))
                text_rect = text_surface.get_rect(
                    center=(btn["rect"].centerx, y_offset))
                self.screen.blit(text_surface, text_rect)
                y_offset += 32

    def switch_team(self):
        """Change l'équipe du joueur."""
        self.player_team = 'green' if self.player_team == 'red' else 'red'
