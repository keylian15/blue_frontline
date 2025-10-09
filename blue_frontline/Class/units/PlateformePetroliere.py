import pygame

class PlateformePetroliere(pygame.sprite.Sprite):
    """Classe pour gérer les plateformes pétrolières."""

    def __init__(self, game:"Game", team: str, objTiled: "TiledObject", is_ia : bool = True): # type: ignore
        """Initialise une nouvelle instance de PlateformePetroliere.

        Args:
            game (Game): L'instance du jeu.
            team (str): Équipe de la plateforme.
            objTiled (TiledObject): Objet Tiled correspondant à la plateforme.
            is_ia (bool, optional): Indique si la plateforme est contrôlée par une IA. Par défaut, True.
        """
        super().__init__()
        self.game = game
        self.team = team
        self.objTiled = objTiled
        self.hitbox_polygon = objTiled.points
        
        self.max_health = 1000
        self.current_health = 1000
        self.is_alive = True
        
        # Verifier l'utilité d'ici ===>
        # Calculer les limites du polygone pour le rect
        min_x = min(point[0] for point in self.hitbox_polygon)
        max_x = max(point[0] for point in self.hitbox_polygon)
        min_y = min(point[1] for point in self.hitbox_polygon)
        max_y = max(point[1] for point in self.hitbox_polygon)
        # Position centrale calculée depuis le polygone
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        self.position = [float(center_x), float(center_y)]
        self.width = int(max_x - min_x)
        self.height = int(max_y - min_y)
        rect_x = int(min_x)
        rect_y = int(min_y)
        # <===

        self.unit_type = "plateforme"
        self.is_selected = False
        
        # Image invisible (rectangle transparent) - garde les hitboxes mais invisible
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        color = (0, 0, 0, 0)  # Complètement transparent (invisible)
        self.image.fill(color)
        
        # Le rect englobe la zone de la hitbox
        self.rect = pygame.Rect(rect_x, rect_y, self.width, self.height)
        
        # Pour compatibilité avec la logique d'unités
        self.range = 30
        self.damage = 5
        self.fire_rate = 1  # 1 tir/seconde
        self.last_shot_time = 0
        self.is_platform = True
        
        # On appelle l'initialisation de l'IA si c'est une IA
        self.is_ia = is_ia 
        if self.is_ia : 
            self.init_ia()

    def update(self, dt=0, combat_system=None, screen=None, camera_offset=(0,0), all_units=None):
        """Met à jour la plateforme (tir automatique)."""
        import time
        if not self.is_alive:
            return
        if all_units is None or combat_system is None:
            return
        enemies_in_range = []
        range_pixels = self.range * 32
        for unit in all_units:
            if unit is self:
                continue  
            if hasattr(unit, 'team') and unit.team != self.team and getattr(unit, 'is_alive', False):
                if hasattr(unit, 'rect'):
                    cx, cy = self.position[0], self.position[1]
                    rx, ry, rw, rh = unit.rect.left, unit.rect.top, unit.rect.width, unit.rect.height
                    closest_x = max(rx, min(cx, rx + rw))
                    closest_y = max(ry, min(cy, ry + rh))
                    distance = ((cx - closest_x)**2 + (cy - closest_y)**2) ** 0.5
                else:
                    distance = ((self.position[0] - unit.position[0])**2 + (self.position[1] - unit.position[1])**2) ** 0.5
                if distance <= range_pixels:
                    enemies_in_range.append(unit)
        if enemies_in_range:
            current_time = time.time()
            time_since_last_shot = current_time - self.last_shot_time
            multiplica = self.game.hud.timer.get_speed_multiplier()
            if time_since_last_shot >= (1.0 / (self.fire_rate * multiplica)):
                target = enemies_in_range[0]
                if combat_system:
                    combat_system.fire_projectile(self, target)
                else:
                    if hasattr(target, 'take_damage'):
                        target.take_damage(self.damage, killer=self)
                self.last_shot_time = current_time
        # === Partie IA ===
        if self.is_ia: 
            self.take_choice()
        
    def take_damage(self, damage: int , killer: str = None):
        """Inflige des dégâts à la plateforme.

        Args:
            damage (int): Nombre de dégâts à infliger.
            killer (str, optional): L'équipe attaquante. Defaults to None.
        """
        
        if not self.is_alive:
            return
        self.current_health -= damage
        if self.current_health <= 0:
            self.current_health = 0
            self.is_alive = False
            self.on_destroyed()

    def on_destroyed(self):
        """Appelé quand la plateforme est détruite."""
        
        # Déclencher la victoire si la plateforme a une référence vers le Game
        if hasattr(self, 'game') and self.game:
            self.game.on_platform_destroyed(self)

    def draw_health_bar(self, screen: pygame.Surface, camera_offset: tuple[float, float], zoom: float):
        """Dessine une barre de vie large pour la plateforme.

        Args:
            screen (pygame.Surface): L'ecran de jeu.
            camera_offset (tuple[float, float]): La position de la caméra.
            zoom (float): Le zoom de la caméra.
        """
        
        if not self.is_alive:
            return
        
        # Pour les plateformes, utiliser la position de l'image Tiled plutôt que le centre de la hitbox
        xs = [p.x for p in self.hitbox_polygon]
        ys = [p.y for p in self.hitbox_polygon]
        image_center_x = sum(xs) / len(xs)
        image_center_y = sum(ys) / len(ys)
        
        # Calculer les coordonnées de l'image sur l'écran   
        screen_x = (image_center_x - camera_offset[0]) * zoom
        screen_y = (image_center_y - camera_offset[1]) * zoom
        
        # Barre de vie plus large pour les plateformes, placée en dessous de l'image
        bar_width = int(180 * zoom)  # Largeur fixe adaptée aux plateformes
        bar_height = max(12, int(20 * zoom))
        bar_x = int(screen_x - bar_width // 2)
        # Placer la barre en dessous de l'image de la plateforme (environ 120px en dessous du centre)
        bar_y = int(screen_y + 120 * zoom)
        
        # Fond
        background_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(screen, (80, 80, 80), background_rect)
        
        # Vie
        health_percentage = self.current_health / self.max_health
        health_width = int(bar_width * health_percentage)
        health_rect = pygame.Rect(bar_x, bar_y, health_width, bar_height)
        
        # Couleur de la barre de vie selon le pourcentage
        if health_percentage > 0.6:
            health_color = (0, 255, 0)  # Vert
        elif health_percentage > 0.3:
            health_color = (255, 255, 0)  # Jaune
        else:
            health_color = (255, 0, 0)  # Rouge
            
        pygame.draw.rect(screen, health_color, health_rect)
        
        # Contour
        pygame.draw.rect(screen, (0, 0, 0), background_rect, 2)
        
        # Texte avec la vie actuelle/maximale, placé au-dessus de la barre
        font = pygame.font.Font(None, max(16, int(18 * zoom)))
        health_text = f"{self.current_health}/{self.max_health}"
        text_surface = font.render(health_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(screen_x, bar_y - 20 * zoom))
        screen.blit(text_surface, text_rect)
        
    # === FONCTIONS d'IA ===
    def init_ia(self): 
        """Fonction d'initialisation de l'IA"""
        import random

        # On défini des scénario pour que l'IA adaptera plus tard.
        self.scenarios = {
            "attaque" : 0,
            "defense" : 0,
            "production" : 0,
            "exploration" : 0, 
        }
        
        # On défini des coefficients pour chaque scénario que l'IA adaptera plus tard.
        self.coef = {
            "attaque" : random.randint(1,5),
            "defense" : random.randint(1,5),
            "production" : random.randint(1,5),
            "exploration" : random.randint(1,5),
        }
        
        # On défini des coefficients pour chaque unité qui va attaquer notre base.
        self.coef_unit = {
            "pompe_petroliere" :0,
            "eclaireur" : 0,
            "chaloupe" : 1,
            "sousmarin" : 2,
            "bateau" : 3,
            "paquebot" : 4,
        }
        
        # On récupére le nombre aléatoire.
        self.nb_random = random.randint(0, 100)

    def update_ia(self) :
        """Fonction permettant de mettre les variables à jour pour l'IA"""        
        # On reset les scénarios.
        self.scenarios = {
            "attaque" : 0,
            "defense" : 0,
            "production" : 0,
            "exploration" : 0, 
        }

        # On récupére les unités ennemies et alliées
        self.units = self.game.units
        self.enemie_units, self.ally_units = [], []
        
        if self.units : 
            for unit in self.units : 
                if unit.unit_type != "plateforme" : 
                    if unit.team == self.team : 
                        self.ally_units.append(unit)
                    else :
                        self.enemie_units.append(unit)
                        # On affiche la distance entre l'unité et la plateforme
                    
        # On récupére le nombre d'unités alliées et ennemies
        self.nb_ally = len(self.ally_units)
        self.nb_enemie = len(self.enemie_units)
        
        # On récupére le nombre d'îles quantiques cachées
        if hasattr(self.game, 'quantique_area_hidden'):
            self.nb_island_hidden = len(self.game.quantique_area_hidden)
        else :
            self.nb_island_hidden = 0
            
        # On récupére le nombre de pétrole 
        if hasattr(self.game, 'hud'):
            if self.team == "red":
                self.nb_oil_ennemy = self.game.hud.petrole_green.count
                self.nb_oil_ally = self.game.hud.petrole_red.count
            else :
                self.nb_oil_ennemy = self.game.hud.petrole_red.count
                self.nb_oil_ally = self.game.hud.petrole_green.count
                    
        # On prend un scénario
        return self.take_scenario()
        
    def take_scenario(self) :
        """Fonction permettant de définir un scénario pour l'IA
        On procédera par attribution de point pour définir le meilleur scénario"""
        
        # === SCENARIOS ===
        # Si des îles quantiques sont cachées, on va les explorer
        # 
        # #
        scenarios = self.scenarios
        coef = self.coef
        
        # Si on des îles cachés on va explorer en fonctions du nombre réstant.
        if self.nb_island_hidden > 0 :
            # On explore en fonctions du nombre d'eclaireur a nous présents, en avoir 1 est suffisant.
            compteur = 0 
            for unit in self.ally_units : 
                if unit.unit_type == "eclaireur": 
                    compteur += 1
            if compteur < 1 : 
                scenarios["exploration"] += self.nb_island_hidden * coef["exploration"]

        # Si le nombre d'ennemi est 2 fois supérieur a notre nombre d'ally on défend.
        if self.nb_enemie > 2 * self.nb_ally : 
            scenarios["defense"] += 1 * coef["defense"]
        
        # Si le nombre d'ennemi est 2 fois inférieur a notre nombre d'ally on attaque.
        if self.nb_enemie < 2 * self.nb_ally :
            scenarios["attaque"] += 1 * coef["attaque"]
            
        # Si la distance est proche de la base: 
        # Si distance est inférieur à la range de la plateforme
        import math
        for unit in self.enemie_units : 
            x, y= unit.position[0], unit.position[1]
            distance = math.sqrt((x - self.position[0])**2 + (y - self.position[1])**2)
            # On fais le scénario de défense en prennant en compte la distance et la puissance des unités.
            if distance < self.range * 2 :
                if distance < self.range : # La défense est prioritaire
                    self.scenarios["defense"] += 10 * coef["defense"] * self.coef_unit[unit.unit_type]
                else : 
                    self.scenarios["defense"] += 1 * coef["defense"] * self.coef_unit[unit.unit_type]

        # Si le nombre de pétrole ally est proche de faire la construction d'une pompe on attend pour la construction.
        if self.is_near(self.nb_oil_ally, "pompe_petroliere") : 
            scenarios["production"] += 1 * coef["production"]
            
        return scenarios
            
    def take_choice(self) : 
        """Fonction permettant de prendre une décision pour l'IA"""
        # On met a jour toutes les variables necessaires
        self.update_ia()
        choix = max(self.scenarios, key=self.scenarios.get)
        
        from Global import UNIT_CONFIGS
        if choix == "exploration" : 
            # On spawn un bateau d'exploration 
            self.game.event_handler.spawn_unit("eclaireur", self.team, UNIT_CONFIGS["eclaireur"]["cost"]) 
                
    def give_info(self): 
        """Fonction permettant de donner des informations sur l'IA"""
        # On va afficher le scénario ayant le plus de poids
        self.print_dico(self.coef, "coefficient")
        self.print_dico(self.scenarios, "scénario")
        choix = max(self.scenarios, key=self.scenarios.get)
        
        print(f"Le scénario le plus important est : {choix}")
        print(self.is_near(self.nb_oil_ally, "pompe_petroliere"))
    
    def is_near(self, player_oil : int, objectif : str):
        """Fonction permettant de savoir si un objectif est proche ou non en quantité de pétrole (on se base sur UNIT CONFIGS du global).

        Args:
            player_oil (int): La quantité de pétrole du joueur.
            objectif (str): Le nom de l'objet dans UNIT CONFIGS.

        Returns:
            (bool): True si l'objectif est proche, False sinon.
        """
        from Global import UNIT_CONFIGS
        # Vérification de la présence de l'objectif dans la config
        if objectif not in UNIT_CONFIGS :
            return False

        cost = UNIT_CONFIGS[objectif]["cost"]
        # Si la différence est dans la marge
        return abs(player_oil - cost) <= self.nb_random

    def print_dico(self, dico: dict, nom: str):
        """Fonction permettant d'afficher un dictionnaire de manière lisible.

        Args:
            dico (dict): Le dictionnaire à afficher.
            nom (str): Le nom du dictionnaire.
        """
        print(f"------ Team {self.team} ------\n")
        print(f"Affichage du dictionnaire : {nom}")
        for element in dico:
            print(f"{element} : {dico[element]}")
            
        print("\n\n")
            
class PlateformePetroliereRouge(PlateformePetroliere) :
    def __init__(self, game: "Game", objTiled: "TiledObject") :  # type: ignore
        """Constructeur de la classe PlateformePetroliereRouge.

        Args:
            game (Game): L'instance du jeu.
            objTiled (TiledObject): L'objet Tiled correspondant à la plateforme.
        """ 
        super().__init__(game, "red", objTiled, True )
        
class PlateformePetroliereVerte(PlateformePetroliere) :
    def __init__(self, game: "Game", objTiled: "TiledObject") :  # type: ignore
        """Constructeur de la classe PlateformePetroliereVerte.

        Args:
            game (Game): L'instance du jeu.
            objTiled (TiledObject): L'objet Tiled correspondant à la plateforme.
        """ 
        super().__init__(game, "green", objTiled, True )
