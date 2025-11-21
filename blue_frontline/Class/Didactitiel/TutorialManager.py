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
    Indique comment zommer la caméra (molette)
    Indique comment sélectionner une unité dans l'HUD (Fléche directionnelle et clic gauche)
    Indique comment faire apparaître l'entité
    Indique comment déplacer une unité (clic gauche)
    Indique comment attaquer une unité ennemie (Touche T préssée)
    Indique comment poser une mine (Touche T préssée)
    Indique comment améliorer la base

    Indique la pompe pétrolière
    """

    def __init__(self, game):
        self.step = -3
        self.active = True
        self.message = ""
        self.phase = 1  # Affichage = 1, actions = 2
        self.game = game
        self.screen = game.screen
        self.width = self.game.screen.get_width()
        self.height = self.game.screen.get_height()
        self.orientation = "hg"
        self.arrow = True
        self.sub_text = None
        self.count = 0
        self.zoom_is_done = False
        self.alien_symbols = [
            # Math / logique
            "∑", "∆", "√", "≠", "≤", "≥",

            # Grec
            "Ω", "Ψ", "Φ", "Θ", "Λ", "Σ", "ξ", "δ", "π", "η", "ζ",

            # Divers
            "¤", "§", "¶", "‡", "†", "※", "‰"
        ]

    def update(self):
        """Appelée chaque frame depuis ta boucle principale"""
        if not self.active:
            return

        if self.step == -3:
            self.message = "Bienvenue dans le didactitiel de Blue Frontline ! Je suis le Commandant Capitaine, votre guide pour vous préparez a cette guerre navale. Je vais vous expliquer comment jouer."
            self.anchor_pos = (self.width * 0.4, self.height * 0.4)
            self.arrow = False
            self.sub_text = None

        if self.step == -2:
            self.message = "Commençons par les bases ! Vous pouvez quitter le didactitiel à tout moment en appuyant sur la touche Echap."
            self.anchor_pos = (self.width * 0.4, self.height * 0.4)
            self.arrow = False
            self.sub_text = None

        if self.step == -1:
            self.message = "Dans ce jeu, plusieurs modes de jeu sont disponibles. Vous pouvez jouer en solo contre l'IA, en multijoueur local (en utilisant la touche J pour changer d'équipe) ou même IA contre IA. Tout est possible ! Je vous laisserais jetter un oeil aux paramétres plus tard."
            self.anchor_pos = (self.width * 0.4, self.height * 0.4)
            self.arrow = False
            self.sub_text = None

        if self.step == 0:
            self.message = "Voici le timer, il vous guide à travers le temps passé dans le jeu."
            self.anchor_pos = (self.width * 0.5, self.height * 0.05)
            self.orientation = "hg"
            self.arrow = True

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
            if self.move_to_base("red"):
                self.message = "Voici votre base, protégez-la à tout prix !"
                self.anchor_pos = (self.width * 0.1, self.height * 0.5)
                self.orientation = "bg"

        if self.step == 5:
            if self.move_to_base("green"):
                self.message = "Voici la base ennemie, détruisez la pour remporter cette guerre !"
                self.anchor_pos = (self.width * 0.9, self.height * 0.5)
                self.orientation = "bd"

        if self.step == 6:
            self.message = "Voici l'indicateur de votre équipe"
            self.anchor_pos = (self.width * 0.05, self.height * 0.05)
            self.orientation = "hg"

        if self.step == 7:
            self.message = "Voici la quantité de pétrole dont vous disposez, elle vous permetra de poser des troupes."
            self.anchor_pos = (self.width * 0.84, self.height * 0.9)
            self.orientation = "bd"
            self.arrow = True

        if self.step == 8:
            self.message = "Voici la quantité de pièces dont vous disposez, elle vous permetra d'améliorer le plateforme pétroliére."
            self.anchor_pos = (self.width * 0.84, self.height * 0.8)
            self.orientation = "bd"
            self.arrow = True

        if self.step == 9:
            self.phase = 2
            self.message = "Utilisez les touches ZQSD pour déplacer la caméra."
            self.anchor_pos = (self.width * 0.4, self.height * 0.4)
            self.arrow = False
            self.count_max = 10
            self.sub_text = "Appuyez sur une touche de déplacement pour continuer..."

        if self.step == 10:
            self.message = "Vous pouvez zoomer et dézoomer la caméra avec la molette de la souris."
            self.anchor_pos = (self.width * 0.4, self.height * 0.4)
            self.arrow = False
            self.count_max = 30
            self.sub_text = "Zoomer pour continuer..."

        if self.step == 11:
            self.message = "Utilisez les flèches directionnelles pour sélectionner une unité dans l'HUD."
            self.anchor_pos = (self.width * 0.4, self.height * 0.4)
            self.arrow = False
            self.count_max = 5
            self.sub_text = "Appuyez sur une touche de déplacement pour continuer..."

        if self.step == 12:
            self.message = "Vous pouvez également cliquer sur une unité dans l'HUD pour la sélectionner."
            self.anchor_pos = (self.width * 0.4, self.height * 0.4)
            self.arrow = False
            self.sub_text = "Cliquez sur la chaloupe dans l'HUD pour continuer..."

        if self.step == 13:
            self.move_to_base("red")
            self.zoom_in()
            self.game.hud.petrole_red.count = 20
            self.message = "Utilisez la touche entrée pour faire apparaître l'unité sélectionnée."
            self.anchor_pos = (self.width * 0.4, self.height * 0.4)
            self.arrow = False
            self.sub_text = "Appuyez sur la touche entrée pour continuer..."

        if self.step == 14:
            self.game.selected_unit = self.game.units[-1]
            self.message = "Utilisez le clic gauche pour séléctionner puis déplacer une unité sur la carte."
            self.anchor_pos = (self.width * 0.4, self.height * 0.4)
            self.arrow = False
            self.sub_text = "Utilisez le clic gauche pour déplacer une unité sur la carte."

        if self.step == 15:
            if self.game.selected_unit.is_moving == False and len(self.game.units) == 3:
                self.game.event_handler.spawn_unit("chaloupe", "green")
                self.game.units[-1].position = self.game.selected_unit.position[0] + \
                    20, self.game.selected_unit.position[1]
                self.message = "Utilisez la touche T pour attaquer une unité ennemie."
                self.anchor_pos = (self.width * 0.4, self.height * 0.4)
                self.arrow = False
                self.sub_text = "Utilisez la touche T pour attaquer une unité ennemie."

        if self.step == 16:
            self.message = "Vous infligez des dégâts à l'unité ennemie ! Les dégâts dépendent de l'unité utilisée."
            self.anchor_pos = (self.width * 0.4, self.height * 0.4)
            self.arrow = False
            self.sub_text = None

        if self.step == 17:

            if len(self.game.units) == 2:
                self.game.event_handler.spawn_unit("sousmarin", "red")
                self.game.selected_unit = self.game.units[-1]
            elif len(self.game.units) != 3:
                self.game.selected_unit.die()
                self.game.units[-1].die()
            self.message = "Avec le sous marin vous ne pouvez pas tirer, mais vous pouvez placer des mines."
            self.anchor_pos = (self.width * 0.4, self.height * 0.4)
            self.arrow = False
            self.sub_text = "Utilisez la barre espace pour poser une mine."

        if self.step == 18:
            self.message = "Les mines explosent au contact d'une unité ennemie, utilisez-les judicieusement."
            self.anchor_pos = (self.width * 0.6, self.height * 0.6)
            self.arrow = False
            self.sub_text = None

        if self.step == 19:
            if len(self.game.units) == 3:
                self.game.selected_unit.die()
                self.game.selected_unit = None
            self.message = "Cliquez sur la plateforme pétroliére augmenter vos capacités de défense."
            self.anchor_pos = (self.width * 0.4, self.height * 0.4)
            self.arrow = False
            self.sub_text = "Cliquez sur la plateforme pétroliére pour continuer."

        if self.step == 20:
            self.message = "Différentes améliorations sont disponibles, améliorez votre plateforme pétroliére pour gagner en défense."
            self.anchor_pos = (self.width * 0.4, self.height * 0.4)
            self.arrow = False
            self.sub_text = None

        if self.step == 21:
            self.message = "Les améliorations vous coûtent des pièces, assurez-vous de tuer suffisamment d'unités ennemies pour en obtenir."
            self.anchor_pos = (self.width * 0.4, self.height * 0.4)
            self.arrow = False
            self.sub_text = None

        if self.step == 22:
            self.game.selected_unit = None
            self.message = "Des parties de la map sont sous le brouillard, on les appelle les zones quantiques."
            self.move_cam_to((self.width * 1.2, self.height * 0.5))
            self.anchor_pos = (self.width * 0.4, self.height * 0.4)
            self.arrow = False
            self.sub_text = None

        if self.step == 23:
            self.message = "Explorez ces zones pour découvrir ce qui s'y cache !"
            self.anchor_pos = (self.width * 0.4, self.height * 0.4)
            self.arrow = False
            self.sub_text = None

        if self.step == 24:
            from random import choice
            self.message = " ".join(choice(self.alien_symbols) for _ in range(50))
            self.sub_text = " ".join(choice(self.alien_symbols) for _ in range(20))
            
        if self.step == 25:
            from random import choice
            self.message = "Rentrez mes enfants, venez à Moi... le Grand Océan vous appelle... JE VOUS APPPELLE..."
            self.sub_text = " ".join(choice(self.alien_symbols) for _ in range(20))

        if self.step == 26:
            from random import choice
            self.message = " ".join(choice(self.alien_symbols) for _ in range(50))
            self.sub_text = " ".join(choice(self.alien_symbols) for _ in range(20))
            
        if self.step == 27:
            from random import choice
            self.message = "Un dernier conseil : gardez un oeil sur la marée, "
            self.message += " ".join(choice(self.alien_symbols) for _ in range(15))
            self.message += "    et les récifs."
            self.sub_text = None
            
        if self.step == 28:
            self.message = "Maintenant, vous savez tout. Allez, allez, allez ! Vous pouvez maintenant vous aventurer dans le monde de Blue Frontline !"
            self.sub_text = None
            
        if self.step == 29:
            from Class.menu import Menu
            menu = Menu()
            menu.run()


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
        if self.sub_text:
            sub_surf = font_sub.render(
                self.sub_text, True, sub_text_color)
        else:
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
        # blink = (time.time() % 0.6) < 0.3  # ON 300ms / OFF 300ms
        # border_color = (255, 0, 0, 255) if blink else (255, 0, 0, 0)

        # pygame.draw.rect(
        #     popup,
        #     border_color,
        #     (0, 0, width, height),
        #     width=10,               # épaisseur du contour
        #     border_radius=border_radius
        # )

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
        if self.arrow:
            pos = self.anchor_pos[0] + padding, self.anchor_pos[1] + padding
            self.draw_arrow_towards((x, y), (width, height), pos)

    def count_to_next_step(self):
        """"""
        if self.count == self.count_max:
            self.next_step()
            self.count = 0
        else:
            self.count += 1

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

    def move_to_base(self, team: str = "red"):
        """Déplace la caméra vers la base spécifiée.

        Returns:
            True si la cible est visible à l'écran, False sinon
        """
        cam_x, cam_y = self.game.camera.position
        target_x, target_y = self.game.get_base_position(team)

        if team == "red":
            target_x -= 100
        else:
            target_x += 100

        # 1. Calculer les limites visibles de l'écran
        # camera.position = coin supérieur-gauche de la caméra
        screen_w, screen_h = self.game.screen.get_size()
        zoom = self.game.camera.zoom_level

        half_w = screen_w / (2 * zoom)
        half_h = screen_h / (2 * zoom)

        left = (cam_x - half_w) * zoom
        right = (cam_x + half_w) * zoom
        top = (cam_y - half_h) * zoom
        bottom = (cam_y + half_h) * zoom

        # 2. Vérifier si la cible est visible avec une marge de sécurité
        if left <= target_x <= right and top <= target_y <= bottom:
            return True

        # 3. Calculer la distance à la cible
        distance_x = target_x - cam_x
        distance_y = target_y - cam_y
        distance = (distance_x**2 + distance_y**2)**0.5

        # 4. Déplacer la caméra progressivement
        dx = distance_x * 0.05
        dy = distance_y * 0.05

        # Vitesse minimale pour éviter de stagner
        min_speed = 1.0
        if abs(dx) < min_speed and distance_x != 0:
            dx = min_speed if dx > 0 else -min_speed
        if abs(dy) < min_speed and distance_y != 0:
            dy = min_speed if dy > 0 else -min_speed

        self.game.camera.move(dx, dy)

        return False

    def zoom_in(self):
        """Zoom avant de la caméra."""
        if self.zoom_is_done:
            return
        for _ in range(10):
            self.game.camera.zoom_in()
            self.zoom_is_done = True

    def zoom_out(self):
        """Zoom arrière de la caméra."""
        if not self.zoom_is_done:
            return
        for _ in range(10):
            self.game.camera.zoom_out()
            self.zoom_is_done = True
