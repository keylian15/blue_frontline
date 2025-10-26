import pygame

class PlateformePetroliere(pygame.sprite.Sprite):
    """Classe pour gérer les plateformes pétrolières."""

    def __init__(self, x: int, y: int, team: str, max_health: int, objTiled):
        """Initialise une nouvelle instance de PlateformePetroliere.

        Args:
            x (int): Coordonnée x de la plateforme.
            y (int): Coordonnée y de la plateforme.
            team (str): Équipe de la plateforme.
            max_health (int): Santé maximale de la plateforme.
            hitbox_polygon (list["Point", "Point", "Point", "Point"]): Liste des points formant la hitbox de la plateforme.
        """

        super().__init__()
        self.team = team
        self.max_health = max_health
        self.current_health = max_health
        self.is_alive = True
        self.hitbox_polygon = objTiled.points
        self.objTiled = objTiled
        
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
        self.range = 5
        self.damage = 5
        self.fire_rate = 1  # 1 tir/seconde
        self.last_shot_time = 0
        self.is_platform = True

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
            self.ia_update()                    # On met a jour les données de l'IA
            if self.ia_check_wait():            # Si on doit attendre
                return
            # On note le scénario courant s'il existe.
            if self.current_scenario:
                scenario = self.current_scenario
            else:
                self.ia_scenarios()                 # On applique les scenarios de l'IA
                scenario = self.ia_get_scenario()   # On récupére le scénario de l'IA
                self.current_scenario = scenario    # On note le scénario courant

            # On fait le scénario de l'IA
            self.ia_do_scenario(scenario)

            # Si le scénario est terminé ou a échoué, on le remet à None
            if self.wait is False:
                self.current_scenario = None
        
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