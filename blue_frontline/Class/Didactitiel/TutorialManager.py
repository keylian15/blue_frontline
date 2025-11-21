class TutorialManager:
    """
    Le tutoriel guide le joueur à travers les étapes de base du jeu.
    Il suit la progression du joueur et affiche des messages contextuels.
    Il se déroule sur plusieurs étapes, chacune correspondant à une action clé que le joueur doit accomplir.

    -- Indications des zones d'affichage --
    Indique le Timer
    Indique l'icon de marée
    Indique la zone de sélection d'unité
    Indique la zone de detail d'unité
    Indique la base
    Indique la quantité de pétrole
    Indique la quantité de piece

    -- Indications des actions --
    Indique comment déplacer la caméra (ZQSD)
    Indique comment sélectionner une unité dans l'HUD (Fléche directionnelle et clic gauche)
    Indique comment déplacer une unité (clic gauche)
    Indique comment attaquer une unité ennemie (Touche T préssée)
    Indique comment poser une bombe (Touche T préssée)
    Indique comment construire une pompe pétrolière
    Indique comment améliorer la base
    """

    def __init__(self, game):
        self.step = 0
        self.active = True
        self.message = ""
        self.phase = 1  # Affichage = 1, actions = 2
        self.game = game
        self.screen = game.screen
        self.width = self.game.screen.get_width()
        self.height = self.game.screen.get_height()
        self.orientation = "hg"

    def update(self):
        """Appelée chaque frame depuis ta boucle principale"""
        if not self.active:
            return

        if self.step == 0:
            self.message = "Voici le timer, il vous guide à travers le temps passé dans le jeu."
            self.anchor_pos = (self.width * 0.5, self.height * 0.05)
            self.orientation = "hg"

        if self.step == 1:
            self.message = "Voici l'îcone de marée, il vous sera très utile, gardez un oeil dessus."
            self.anchor_pos = (self.width * 0.6, self.height * 0.05)
            self.orientation = "hg"

        if self.step == 2:
            self.message = "Voici la zone de sélection d'unité, vous pouvez y sélectionner vos unités."
            self.anchor_pos = (250, 800)
            self.orientation = "bg"
            
        if self.step == 3:
            self.message = "Ici, c'est le détail de chacune de vos unités sélectionnées."
            self.anchor_pos = (0, 735)
            self.orientation = "bg"
        
        if self.step == 4:
            target_x, target_y = 768.0, 1425.0
            pos = self.game.camera.position

            # Distance restante
            dx = (target_x - pos[0]) * 0.05
            dy = (target_y - pos[1]) * 0.05


            if abs(dx) < 0.5: dx = 0.5 if dx > 0 else -0.5
            if abs(dy) < 0.5: dy = 0.5 if dy > 0 else -0.5

            if abs(pos[0] - target_x) > 1 or abs(pos[1] - target_y) > 1:
                self.game.camera.move(dx, dy)
                pos = self.game.camera.position
                
            else : 
                self.message = "Voici votre base, protégez-la à tout prix !"
                self.anchor_pos = (self.width * 0.1, self.height * 0.5)
                self.orientation = "bg"

        if self.step == 5:        
            target_x, target_y = 3072.0, 1488.0
            pos = self.game.camera.position

            # Distance restante
            dx = (target_x - pos[0]) * 0.05
            dy = (target_y - pos[1]) * 0.05


            if abs(dx) < 0.5: dx = 0.5 if dx > 0 else -0.5
            if abs(dy) < 0.5: dy = 0.5 if dy > 0 else -0.5

            if abs(pos[0] - target_x) > 1 or abs(pos[1] - target_y) > 1:
                self.game.camera.move(dx, dy)
                pos = self.game.camera.position
                
            else : 
                self.message = "Voici la base ennemie, détruisez la pour remporter cette guerre !"
                self.anchor_pos = (self.width * 0.9, self.height * 0.5)
                self.orientation = "bd"

    def draw_arrow_towards(self, pop_up, pop_up_size, target_pos, color=(255, 255, 255)):
        import pygame
        import math

        # ----- ORIGINE DE LA FLÈCHE -----
        if self.orientation == "bg":  # bas gauche
            start_x = pop_up[0]
            start_y = pop_up[1] + pop_up_size[1]  # bas de la popup
        elif self.orientation == "bd":  # bas droite
            start_x = pop_up[0] + pop_up_size[0]  # droite de la popup
            start_y = pop_up[1] + pop_up_size[1]  # bas de la popup
        else:  # haut gauche par défaut
            start_x = pop_up[0]
            start_y = pop_up[1]

        tx, ty = target_pos

        # Direction
        dx = tx - start_x
        dy = ty - start_y
        angle = math.atan2(dy, dx)

        # Position de la pointe de la flèche (vers la cible)
        arrow_length = 40
        end_x = start_x + math.cos(angle) * arrow_length
        end_y = start_y + math.sin(angle) * arrow_length

        # Triangle de la flèche
        size = 12  # taille du triangle au bout

        p1 = (end_x, end_y)
        p2 = (end_x - math.cos(angle - 0.4) * size,
              end_y - math.sin(angle - 0.4) * size)
        p3 = (end_x - math.cos(angle + 0.4) * size,
              end_y - math.sin(angle + 0.4) * size)

        # Ligne reliant popup → flèche
        pygame.draw.line(self.screen, color,
                         (start_x, start_y), (end_x, end_y), 3)

        # Pointe
        pygame.draw.polygon(self.screen, color, [p1, p2, p3])

    def draw(self):
        """Affiche un message de tutoriel dans une popup responsive avec wrap du texte."""
        if not self.active:
            return

        import pygame

        # --- Styles ---
        font_main = pygame.font.Font(None, 28)
        font_sub = pygame.font.Font(None, 18)

        main_text_color = (255, 255, 255)
        sub_text_color = (220, 220, 220)
        bg_color = (0, 0, 0, 180)

        padding = 12
        spacing = 4
        border_radius = 8

        max_width = 260  # largeur max avant retour à la ligne

        # --- Fonction wrap du texte ---
        def wrap_text(text, font, max_width):
            words = text.split(" ")
            lines = []
            current_line = ""

            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                if font.size(test_line)[0] <= max_width:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word

            if current_line:
                lines.append(current_line)

            return lines

        # --- Préparation des lignes de texte ---
        wrapped_main = wrap_text(self.message, font_main, max_width)

        # Surface du texte principal (plusieurs lignes)
        main_surfaces = [font_main.render(
            line, True, main_text_color) for line in wrapped_main]

        # Sous-texte fixe
        sub_surf = font_sub.render(
            "clic gauche pour continuer...", True, sub_text_color)

        # --- Dimensions de la popup ---
        text_width = max(
            max(s.get_width() for s in main_surfaces),
            sub_surf.get_width()
        )

        text_height = sum(s.get_height()
                          for s in main_surfaces) + spacing + sub_surf.get_height()

        width = text_width + padding * 2
        height = text_height + padding * 2

        # --- Placement intelligent de la popup selon la position de l'objet ---
        object_x, object_y = self.anchor_pos
        screen_w, screen_h = self.screen.get_size()

        # Gros padding
        pad_x = 60
        pad_y = 60

        # Position par défaut : popup à droite et au-dessus
        if self.orientation == "bg":
            x = object_x + (pad_x * 2)
            y = object_y - (pad_y * 2)
        else:
            x = object_x + pad_x
            y = object_y - pad_y

        # --- Si l'objet est trop haut, placer en-dessous ---
        if object_y < pad_y + height:
            y = object_y + pad_y

        # --- Si la popup dépasse à droite, placer à gauche ---
        if x + width > screen_w:
            x = object_x - width - pad_x

        # --- Si la popup dépasse à gauche (sécurité), mettre un minimum ---
        if x < 0:
            x = 10

        # --- Si la popup dépasse en bas, mettre un minimum ---
        if y + height > screen_h:
            y = screen_h - height - 10

        # --- Si la popup dépasse en haut, placer en dessous ---
        if y < 0:
            y = object_y + pad_y

        # --- Surface popup ---
        popup = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(popup, bg_color, (0, 0, width, height),
                         border_radius=border_radius)
        
        import time
        blink = (time.time() % 0.6) < 0.3 # ON 300ms / OFF 300ms
        # blink = (time.time() % 0.1) < 0.05
        border_color = (255, 0, 0, 255) if blink else (255, 0, 0, 0)

        pygame.draw.rect(
            popup,
            border_color,
            (0, 0, width, height),
            width=10,               # épaisseur du contour
            border_radius=border_radius
        )


        # --- Blit des lignes ---
        offset_y = padding
        for line_surf in main_surfaces:
            popup.blit(line_surf, (padding, offset_y))
            offset_y += line_surf.get_height()

        # --- Blit du sous-texte ---
        popup.blit(sub_surf, (padding, offset_y + spacing))

        # --- Affichage ---
        self.screen.blit(popup, (x, y))

        # --- Affichage de la fléche ---
        pos = self.anchor_pos[0] + padding, self.anchor_pos[1] + padding
        self.draw_arrow_towards((x, y), (width, height), pos)

    def next_step(self):
        """Passe à l'étape suivante du tutoriel."""
        self.step += 1

    def previous_step(self):
        """Retourne à l'étape précédente du tutoriel."""
        if self.step > 0:
            self.step -= 1

    def move_cam_to(self, pos):
        """Déplace la caméra vers la position spécifiée."""
        self.game.camera.position[0] = pos[0]
        self.game.camera.position[1] = pos[1]