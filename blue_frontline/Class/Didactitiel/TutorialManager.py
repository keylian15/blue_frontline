from Global import get_action_key


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
        self.step = 0
        self.active = True
        self.phase = 1  # Affichage = 1, actions = 2
        self.game = game
        self.screen = game.screen
        self.width = self.game.screen.get_width()
        self.height = self.game.screen.get_height()
        self.count = 0
        self.zoom_is_done = False
        self.do_function = False
        self.alien_symbols = [
            # Math / logique
            "∑", "∆", "√", "≠", "≤", "≥",

            # Grec
            "Ω", "Ψ", "Φ", "Θ", "Λ", "Σ", "ξ", "δ", "π", "η", "ζ",

            # Divers
            "¤", "§", "¶", "‡", "†", "※", "‰"
        ]

        default_sub_text = "Clic gauche pour continuer..."
        pos_center = (self.width * 0.4, self.height * 0.5)
        self.current_indice = -3
        self.messages = [
            {
                "message": "Bienvenue dans le didactitiel de Blue Frontline ! Je suis le Commandant Capitaine, votre guide pour vous préparez a cette guerre navale. Je vais vous expliquer comment jouer.",
                "sub_text": default_sub_text,
                "anchor_pos": pos_center,
                "orientation": "hg",
                "arrow": False,
                "phase": 1,
                "count": 0
            },
            {
                "message": "Commençons par les bases ! Vous pouvez quitter le didactitiel à tout moment en appuyant sur la touche Echap.",
                "sub_text": default_sub_text,
                "anchor_pos": pos_center,
                "orientation": "hg",
                "arrow": False,
                "phase": 1,
                "count": 0
            },
            {
                "message": "Dans ce jeu, plusieurs modes de jeu sont disponibles. Vous pouvez jouer en solo contre l'IA, en multijoueur local (en utilisant la touche J pour changer d'équipe) ou même IA contre IA. Tout est possible ! Je vous laisserais jetter un oeil aux paramétres plus tard.",
                "sub_text": default_sub_text,
                "anchor_pos": pos_center,
                "orientation": "hg",
                "arrow": False,
                "phase": 1,
                "count": 0
            },
            {
                "message": "Voici le timer, il vous guide à travers le temps passé dans le jeu.",
                "sub_text": default_sub_text,
                "anchor_pos": (self.width * 0.5, self.height * 0.05),
                "orientation": "hg",
                "arrow": True,
                "phase": 1,
                "count": 0
            },
            {
                "message": "Voici l'îcone de marée, elle vous sera très utile, gardez un oeil dessus.",
                "sub_text": default_sub_text,
                "anchor_pos": (self.width * 0.6, self.height * 0.05),
                "orientation": "hg",
                "arrow": True,
                "phase": 1,
                "count": 0
            },
            {
                "message": "Voici la zone de sélection d'unité, vous pouvez y sélectionner vos unités.",
                "sub_text": default_sub_text,
                "anchor_pos": (self.width * 0.2, self.height * 0.93),
                "orientation": "bg",
                "arrow": True,
                "phase": 1,
                "count": 0
            },
            {
                "message": "Ici, c'est le détail de chacune de vos unités sélectionnées.",
                "sub_text": default_sub_text,
                "anchor_pos": (self.width * 0, self.height * 0.85),
                "orientation": "bg",
                "arrow": True,
                "phase": 1,
                "count": 0
            },
            {
                "message": "Voici votre base, protégez-la à tout prix !",
                "sub_text": default_sub_text,
                "anchor_pos": (self.width * 0.1, self.height * 0.5),
                "orientation": "bg",
                "arrow": True,
                "phase": 1,
                "count": 0,
                "function": [{"name": self.move_to_base, "args": ("red",)}]
            },
            {
                "message": "Et la base ennemie, détruisez la pour remporter cette guerre !",
                "sub_text": default_sub_text,
                "anchor_pos": (self.width * 0.9, self.height * 0.5),
                "orientation": "bd",
                "arrow": True,
                "phase": 1,
                "count": 0,
                "function": [{"name": self.move_to_base, "args": ("green",)}]
            },
            {
                "message": "La c'est l'indicateur de votre équipe",
                "sub_text": default_sub_text,
                "anchor_pos": (self.width * 0.05, self.height * 0.05),
                "orientation": "hg",
                "arrow": True,
                "phase": 1,
                "count": 0
            },
            {
                "message": "Par la c'est pétrole dont vous disposez, elle vous permettra de poser des troupes.",
                "sub_text": default_sub_text,
                "anchor_pos": (self.width * 0.84, self.height * 0.9),
                "orientation": "bd",
                "arrow": True,
                "phase": 1,
                "count": 0
            },
            {
                "message": "Et ici les pièces obtenues par les morts, elle vous permettra d'améliorer le plateforme pétroliére.",
                "sub_text": default_sub_text,
                "anchor_pos": (self.width * 0.84, self.height * 0.8),
                "orientation": "bd",
                "arrow": True,
                "phase": 1,
                "count": 0
            },
            {
                "message": "Navigons un peu plus loin, utilisez ZQSD.",
                "sub_text": "Utilisez les touches de déplacement pour continuer...",
                "anchor_pos": pos_center,
                "orientation": "hg",
                "arrow": False,
                "phase": 2,
                "count": 10,
                "restriction": {"name": "zqsd", "keys": [get_action_key("CAMERA_UP"), get_action_key("CAMERA_DOWN"),
                                                         get_action_key("CAMERA_LEFT"), get_action_key("CAMERA_RIGHT")]}
            },
            {
                "message": "Et si on se rapprochait un peu ?",
                "sub_text": "Utilisez le zoom pour continuer...",
                "anchor_pos": pos_center,
                "orientation": "hg",
                "arrow": False,
                "phase": 2,
                "count": 20,
                "restriction": {"name": "zoom", "keys": [get_action_key("ZOOM_IN"), get_action_key("ZOOM_OUT")]}
            },
            {
                "message": "Changer de troupe via les flèches directionnelles dans l'HUD.",
                "sub_text": "Appuyez sur une touche de navigation pour continuer...",
                "anchor_pos": pos_center,
                "orientation": "hg",
                "arrow": False,
                "phase": 2,
                "count": 5,
                "restriction": {"name": "navigation", "keys": [get_action_key("HUD_LEFT"), get_action_key("HUD_RIGHT")]}
            },
            {
                "message": "Les touches c'est bien mais le clic c'est mieux.",
                "sub_text": "Cliquez sur la chaloupe pour continuer...",
                "anchor_pos": pos_center,
                "orientation": "hg",
                "arrow": False,
                "phase": 2,
                "count": 0,
                "restriction": {"name": "select_chaloupe", "keys": [get_action_key("SELECT_MOVE")]}
            },
            {
                "message": "A l'attaque ! Faites apparaîte l'unité.",
                "sub_text": "Appuyez sur la touche entrée pour continuer...",
                "anchor_pos": pos_center,
                "orientation": "hg",
                "arrow": False,
                "phase": 2,
                "count": 0,
                "function": [{"name": self.move_to_base, "args": ("red",)}, {"name": self.zoom_in, "args": None}, {"name": self.set_oil_tuto, "args": ("20",)}],
                "restriction": {"name": "spawn_chaloupe", "keys": [get_action_key("CREATE_UNIT")]},
            },
            {
                "message": "Il faut se bouger ! Clic gauche pour séléctionner et pour la déplacer.",
                "sub_text": default_sub_text,
                "anchor_pos": pos_center,
                "orientation": "hg",
                "arrow": False,
                "phase": 2,
                "count": 0,
                "restriction": {"name": "move_chaloupe", "keys": [get_action_key("SELECT_MOVE")]}
            },
            {
                "message": "Utilisez la touche T pour attaquer une unité ennemie.",
                "sub_text": "Appuyez sur la touche T pour continuer...",
                "anchor_pos": pos_center,
                "orientation": "hg",
                "arrow": False,
                "phase": 2,
                "count": 0,
                "function": [{"name": self.do_seq_fire, "args": None}],
                "restriction": {"name": "fire_chaloupe", "keys": [get_action_key("SHOOT")]}
            },
            {
                "message": "Vous infligez des dégâts à l'unité ennemie ! Les dégâts dépendent de l'unité utilisée.",
                "sub_text": default_sub_text,
                "anchor_pos": pos_center,
                "orientation": "hg",
                "arrow": False,
                "phase": 2,
                "count": 0
            },
            {
                "message": "Les gros dégats c'est avec de gros moyens, utilisez les mines de sous marins !",
                "sub_text": "Utilisez la barre espace pour continuer...",
                "anchor_pos": pos_center,
                "orientation": "hg",
                "arrow": False,
                "phase": 2,
                "count": 0,
                "function": [{"name": self.do_seq_submarin, "args": None}, {"name": self.set_oil_tuto, "args": ("180",)}],
                "restriction": {"name": "fire_mine", "keys": [get_action_key("MINE")]}
            },
            {
                "message": "Les mines explosent au contact d'une unité ennemie, utilisez-les bien.",
                "sub_text": default_sub_text,
                "anchor_pos": pos_center,
                "orientation": "hg",
                "arrow": False,
                "phase": 2,
                "count": 0
            },
            {
                "message": "Jetons un oeil à la défense, cliquez sur la Plateforme Pétroliére",
                "sub_text": "Cliquez sur la plateforme pétroliére pour continuer...",
                "anchor_pos": pos_center,
                "orientation": "hg",
                "arrow": False,
                "phase": 2,
                "count": 0,
                "restriction": {"name": "select_base", "keys": [get_action_key("SELECT_MOVE")]}
            },
            {
                "message": "Différentes améliorations sont disponibles, améliorez les pour avoir plus de défense.",
                "sub_text": default_sub_text,
                "anchor_pos": pos_center,
                "orientation": "hg",
                "arrow": False,
                "phase": 2,
                "count": 0
            },
            {
                "message": "Les pièces ont les voles qu'aux morts, tuez le plus d'énnemies pour en avoir.",
                "sub_text": default_sub_text,
                "anchor_pos": pos_center,
                "orientation": "hg",
                "arrow": False,
                "phase": 2,
                "count": 0
            },
            {
                "message": "Le brouillard ? C'est... Explorer le vous verez. ",
                "sub_text": "Vous hesitez a cliquer pour continuer...",
                "anchor_pos": pos_center,
                "orientation": "hg",
                "arrow": False,
                "phase": 2,
                "count": 0,
                "function": [{"name": self.move_cam_to, "args": ((self.width * 1.2, self.height * 0.5),)}, {"name": self.unselect_unit, "args": None}]
            },
            {
                "message": "Des zones quantiques, mais c'est une longue histoire, ne me refaites pas me souvenir de ca...",
                "sub_text": "Je veux en savoir plus....",
                "anchor_pos": pos_center,
                "orientation": "hg",
                "arrow": False,
                "phase": 2,
                "count": 0
            },
            {
                "message": "{ALIEN}",
                "sub_text": "{ALIEN}",
                "anchor_pos": pos_center,
                "orientation": "hg",
                "arrow": False,
                "phase": 2,
                "count": 0,
                "function": [{"name": "alien", "args": (50, 20)}]
            },
            {
                "message": "Rentrez mes enfants, venez à Moi... le Grand Océan vous appelle... JE VOUS APPPELLE...",
                "sub_text": "{ALIEN}",
                "anchor_pos": pos_center,
                "orientation": "hg",
                "arrow": False,
                "phase": 2,
                "count": 0,
                "function": [{"name": "alien", "args": (20,)}]
            },
            {
                "message": "{ALIEN}",
                "sub_text": "{ALIEN}",
                "anchor_pos": pos_center,
                "orientation": "hg",
                "arrow": False,
                "phase": 2,
                "count": 0,
                "function": [{"name": "alien", "args": (50, 20)}]
            },
            {
                "message": "Un dernier conseil : gardez un oeil sur la marée, {ALIEN} et les récifs.",
                "sub_text": default_sub_text,
                "anchor_pos": pos_center,
                "orientation": "hg",
                "arrow": False,
                "phase": 2,
                "count": 0,
                "function": [{"name": "alien", "args": (20,)}]
            },
            {
                "message": "Maintenant, vous savez tout. Allez, allez, allez ! Vous pouvez maintenant vous aventurer dans le monde de Blue Frontline !",
                "sub_text": "Se lancer dans l'aventure...",
                "anchor_pos": pos_center,
                "orientation": "hg",
                "arrow": False,
                "phase": 2,
                "count": 0
            },

        ]

    def update(self):
        """Permettant d'afficher le didacticiel a chaque frame."""
        if not self.active:
            return
        if self.step > len(self.messages) - 1:
            from Class.menu import Menu
            menu = Menu()
            menu.run()
            self.active = False
            return
        self.message = self.messages[self.step]["message"]
        self.sub_text = self.messages[self.step]["sub_text"]
        self.anchor_pos = self.messages[self.step]["anchor_pos"]
        self.arrow = self.messages[self.step]["arrow"]
        self.orientation = self.messages[self.step]["orientation"]
        self.phase = self.messages[self.step]["phase"]
        self.count_max = self.messages[self.step]["count"]

        if self.do_function and "function" in self.messages[self.step]:
            for function in self.messages[self.step]["function"]:
                fn = function["name"]
                if fn == "alien":
                    args = function.get("args", ())
                    alien = self.get_alien_message(args[0])
                    self.message = self.messages[self.step]["message"].replace(
                        "{ALIEN}", alien)
                    self.sub_text = self.messages[self.step]["sub_text"].replace(
                        "{ALIEN}", alien)
                    if len(args) == 2:
                        alien = self.get_alien_message(args[1])
                        self.sub_text = self.messages[self.step]["sub_text"].replace(
                            "{ALIEN}", alien)

                else:
                    if function.get("done", False):
                        self.zoom_is_done = True
                        return
                    self.zoom_is_done = False
                        
                    args = function.get("args", ())
                    if args is None:
                        if fn():
                            self.do_function = False
                    else:
                        if fn(*args):
                            self.do_function = False

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

        # 4. Déplacer la caméra progressivement
        dx = distance_x * 0.03
        dy = distance_y * 0.03

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

    def select_last_unit(self):
        """Sélectionne la dernière unité créée."""
        self.game.selected_unit = self.game.units[-1]

    def do_seq_fire(self):
        """Exécute les actions de la séquence.
        Spawn une chaloupe verte a coté de la chaloupe rouge"""
        if self.game.selected_unit.is_moving == False and len(self.game.units) == 3:
            self.game.event_handler.spawn_unit("chaloupe", "green")
            self.game.units[-1].position = self.game.selected_unit.position[0] + \
                20, self.game.selected_unit.position[1]
            return True
        return False

    def do_seq_submarin(self):
        """Exécute les actions de la séquence.
        Spawn un sous-marin rouge pour placer une mine"""
        if len(self.game.units) == 2:
            self.game.event_handler.spawn_unit("sousmarin", "red")
            self.game.units[-1].position = self.game.get_base_position("red")
            self.game.units[-1].position = self.game.units[-1].position[0] + \
                100, self.game.units[-1].position[1]
            self.select_last_unit()
            return True
        elif len(self.game.units) != 3:
            self.game.selected_unit.die()
            self.game.units[-1].die()
            return False

    def do_seq_plateforme(self):
        """Exécute les actions de la séquence.
        Voit les améliorations de la plateforme."""
        if len(self.game.units) == 3:
            self.game.selected_unit.die()
            self.game.selected_unit = None
            return True
        return False

    def get_alien_message(self, nb: int):
        """Renvoie le message à afficher avec le nombre de caractéres"""
        from random import choice
        return " ".join(choice(self.alien_symbols) for _ in range(nb))

    def set_oil_tuto(self, nb: int | str):
        """Met le pétrole pour le tuto"""
        self.game.hud.petrole_red.count = int(nb)

    def unselect_unit(self):
        """Désélectionne l'unité"""
        self.game.selected_unit = None
