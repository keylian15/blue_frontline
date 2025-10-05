import pygame, time, math
from Global import *
from Utils import load_tileset, point_in_many_polygons, random_point_in_polygon
from Class.Perlin import Perlin

class Unit(pygame.sprite.Sprite):
    """Classe de base pour toutes les unités du jeu."""
    
    def __init__(self, game: "Game", team: str, unit_type: str):
        """Initialise une unité.

        Args:
            game (Game): L'instance de la classe Game.
            team (str): L'équipe de l'unité.
            unit_type (str): Le nom du type d'unité.
        """
        super().__init__()
        # La game 
        self.game = game
        
        # Type et team
        self.type = unit_type
        self.team = team
        
        # Position et mouvement
        base_spawn = self.game.red_platform_zone if team == "red" else self.game.green_platform_zone
            
        self.position = random_point_in_polygon(base_spawn)
        self.speed_x = 0  # Vitesse en pixels par seconde sur l'axe X
        self.speed_y = 0  # Vitesse en pixels par seconde sur l'axe Y
        
        # Combat
        self.last_shot_time = 0
        
        # Image et sprite
        self.load_sprite_from_tileset(team, unit_type)
        self.rect = self.image.get_rect()
        self.rect.center = (self.position[0], self.position[1])
        self.angle = 0 
        
        
        # État
        self.is_alive = True
        self.target = None
        
        # État de combat et sélection
        self.is_selected = False
        self.last_shot_time = 0  # Pour gérer le cooldown des tirs (en millisecondes)
        self.enemies_in_range = []  # Liste des ennemis dans la portée
        
        # Couleur de portée selon l'équipe (défaut si pas dans config)
        if unit_type and unit_type in UNIT_CONFIGS:
            config = UNIT_CONFIGS[unit_type]
            self.range_color = config.get("range_color", {}).get(team, (255, 0, 0, 50))
        else:
            self.range_color = (255, 0, 0, 50) if team == "red" else (0, 255, 0, 50)

    # Chaque unité peut avoir sa propre tuile, pour chaque équipe, et tout est configurable
    def load_sprite_from_tileset(self, team: str, unit_type: str):
        """Charge l'image de l'unité depuis le tileset approprié.

        Args:
            team (str): Équipe de l'unité.
            unit_type (str): Nom du type de l'unité.
        """
        
        if unit_type and unit_type in UNIT_CONFIGS:
            config = UNIT_CONFIGS[unit_type]
            tileset_path = config["tileset_paths"][team]
            tile_index = config["tile_index"][team]
            
            # Charger le tileset et sélectionner la bonne tuile
            self.tileset = load_tileset(tileset_path)
            if tile_index < len(self.tileset):
                self.image = self.tileset[tile_index]
            else:
                # Si l'index est invalide, utiliser la première tuile
                self.image = self.tileset[0]
            
        else:
            # Fallback vers l'ancien système si unit_type n'est pas fourni
            self.tileset = load_tileset(RED_TEAM_PATH if team == "red" else GREEN_TEAM_PATH)
            self.image = self.tileset[0]
        self.image_original = self.image
             

        
    
    def update(self, dt: int = 0, combat_system: "CombatSystem" = None, screen: pygame.Surface = None, camera_offset: tuple[float, float] =(0, 0), all_units: list["Unit"] = None):
        """Met à jour l'unité en fonction de son état actuel.

        Args:
            dt (int, optional): La différence de temps entre chaque frame. Defaults to 0.
            combat_system (CombatSystem, optional): Le systeme de combat. Defaults to None.
            screen (pygame.Surface, optional): L'écran sur lequel affiché. Defaults to None.
            camera_offset (tuple[float, float], optional): La position de la caméra. Defaults to (0, 0).
            all_units (list[Unit], optional): Liste des unités. Defaults to None.
        """

        if not self.is_alive:
            return
            
        # Mise à jour de la position
        self.move(dt)
        
        # Mettre à jour la liste des ennemis dans la portée
        if all_units:
            self.update_enemies_in_range(all_units)
        
        # Mise à jour du combat
        self.combat_update(combat_system)
        
        # Dessiner la portée uniquement si l'unité est sélectionnée
        if screen and self.is_selected:
            self.draw_range(screen, camera_offset)
        
        # Mise à jour du rectangle de collision
        self.rect.center = (int(self.position[0]), int(self.position[1]))
        
        
    
    def check_area(self, dt: int):
        """Fonction permettant de verifier la zone dans laquelle l'unité veut aller.

        Args:
            dt (int): La différence de temps entre chaque frame.
        """

        # === RAPPELS ===
        # quantum_islands = Zone quantique Graphique 
        # quantique_area = Zone quantique Tiled
        # quantique_area_hidden = Zone quantique Tiled cachée
        # quantique_area_name = Nom des iles quantiques
        # === RAPPELS ===
        
        if not self.is_moving:
            return
        
        # On prend la prochaine position et ses valeurs 
        self.speed = self.max_speed
        next_position = (
            self.position[0] + self.speed_x * dt, 
            self.position[1] + self.speed_y * dt
        )
        
        # Si la prochaine position est la position d'une entité autre que la notre, on arrête le mouvement
        if self.game.find_unit_at_position(next_position[0], next_position[1], self):
            self.stop()
            self.is_moving = False
            self.target_position = None
            return
        
        # Si la prochaine position est dans une ile, on arrête le mouvement
        if point_in_many_polygons(self.game.obstacles, next_position):
            self.stop()
            self.is_moving = False
            self.target_position = None
            return
        
        # On vérifie si le prochaine position est dans une zone quantique non découverte
        result = point_in_many_polygons(self.game.quantique_area_hidden, next_position)
        if result:
            if self.type == "eclaireur":
                # Récupérer l'index de self.game.quantique_area correspondant à l'île
                index = self.game.quantique_area.index(result[1])
                if index == 0:  # L'ile quantique n°4 est l'index 0 car la plus haute sur Tiled.
                    index = 4
                
                self.game.initializer.toggle_layer('fog' + str(index), False)  # On enléve le calque de brouillard
                self.game.quantique_area_hidden.remove(result[1])  # On enlève l'ile de la liste des iles cachées
                self.game.quantique_area_name.append('ile_quantique_' + str(index))  # On ajoute le nom de l'ile dans la liste des iles quantiques
                
                self.game.renderer.refresh_map()  # On rafraichit le rendu
                self.game.refresh_all_references(self.game)  # On met a jour la map
                self.game.quantique('ile_quantique_' + str(index))  # On appel la fonction quantique du jeu pour activer le changement
            else:
                self.stop()  # Seul l'eclaireur peut découvrir la zone
                self.is_moving = False
                self.target_position = None
                return
        
        # On vérifie si la prochaine position est dans une zone quantique découverte (Il suffit juste de regarder l'ensemble des zones)
        result = point_in_many_polygons(self.game.quantique_area, next_position)
        if result:
            # Récupérer l'index de self.game.quantique_area correspondant à l'île
            index = self.game.quantique_area.index(result[1])

            # On parcours les îles graphiques pour retrouver la bonne île
            for island in self.game.quantum_islands:
                # On vérifie qu'on a le bon index et le bon nom
                if index == int(island.name[-1]):
                    # On récupére la matrice de Perlin
                    matrice = island.matrix
                    
                    # On vérifie qu'on est pas dans une zone 3 (ile)
                    num = Perlin.get_zone_type(next_position[0], next_position[1], matrice, island)
                    
                    # Gesion de la collision 
                    if num == 2:  # Ile 
                        self.stop()
                        self.is_moving = False
                        self.target_position = None
                    elif num == 1:  # Eau peu profonde
                        if self.speed != self.reducte_speed:
                            # Gestion du rallenti
                            self.speed = self.reducte_speed
        
        # On vérifie si la prochaine position est dans une zone d'eau peu profonde
        result = point_in_many_polygons(self.game.eau_peu_profondes, next_position)
        if result:
            # Gestion du rallentissement
            self.speed = self.reducte_speed
        
        # On met a jour la vitesse de l'unité, speed est la valeur de déplacement, move_to va redefinir la vitesse de déplacement jusqu'a la cible
        if self.is_moving : 
            self.move_to(self.target_position[0], self.target_position[1])
            self.position = next_position

    def move(self, dt: int):
        """Déplace l'unité selon sa vitesse. Appelé a chaque tick.

        Args:
            dt (int): La différence de temps entre chaque frame.
        """
        
        if not (self.is_moving and self.target_position):
            return
        
        # Temps de jeu rapide : 
        if self.game.hud.timer.get_speed_multiplier() >= 10:
            # On prend un vecteur avant le déplacement
            to_target_before = (
                self.target_position[0] - self.position[0],
                self.target_position[1] - self.position[1]
            )

            # Verifier le prochain déplacement.
            self.check_area(dt)
            
            if self.is_moving:
                
                # On prend un vecteur après le déplacement
                to_target_after = (
                    self.target_position[0] - self.position[0],
                    self.target_position[1] - self.position[1]
                )

                # Produit scalaire : si le signe change, c'est qu'on a dépassé la cible
                if (to_target_before[0] * to_target_after[0] + 
                    to_target_before[1] * to_target_after[1]) <= 0:
                    self.stop()
                    self.is_moving = False
                    self.target_position = None
        else:
            # Vérifier si on a atteint la destination
            dx = self.position[0] - self.target_position[0]
            dy = self.position[1] - self.target_position[1]
            distance_to_target = (dx**2 + dy**2)**0.5
            
            # Si on est proche de la destination (moins de 5 pixels)
            if distance_to_target < 5:
                self.stop()
                self.is_moving = False
                self.target_position = None
            
            self.check_area(dt)

    def move_to(self, target_x: int, target_y: int):
        """Fonction permettant de mettre a jour la vitesse pour les déplacements.

        Args:
            target_x (int): Coordonnée x de la cible.
            target_y (int): Coordonnée y de la cible.
        """
        
        dx = target_x - self.position[0]
        dy = target_y - self.position[1]
        distance = (dx**2 + dy**2)**0.5
        
        if distance > 0:
            # Normaliser le vecteur direction et appliquer la vitesse
            self.angle = math.degrees(math.atan2(-dy, dx)) - 90
            self.angle %= 360
            self.image = pygame.transform.rotate(self.image_original, self.angle)
            self.rect = self.image.get_rect(center=self.rect.center)

            multiplica = self.game.hud.timer.get_speed_multiplier()
            self.speed_x = (dx / distance) * self.speed * multiplica
            self.speed_y = (dy / distance) * self.speed * multiplica
        else:
            self.stop()

    def move_to_position(self, target: tuple):
        """Fonction permettant de mettre les mécanismes de déplacements.

        Args:
            target (tuple): Coordonnées x et y de la cible.
        """
        self.target_position = target       # On défini la position cible
        self.move_to(target[0], target[1])  # On va initialiser les déplacements de l'unité
        self.is_moving = True               # On indique que l'unité est en train de bouger
        
    def stop(self):
        """Arrête le mouvement de l'unité."""
        
        self.speed_x = 0
        self.speed_y = 0
    
    def take_damage(self, damage: int, killer: "Unit"=None):
        """Inflige des dégâts à l'unité. killer = unité qui inflige le coup fatal (pour récompense).

        Args:
            damage (int): Dégâts infligés.
            killer (Unit, optional): L'entité attaquante. Defaults to None.
        """
        
        self.current_health -= damage
        if self.current_health <= 0:
            self.current_health = 0
            self.is_alive = False
            self.die(killer=killer)
    
    def die(self, killer: "Unit"=None):
        """Gère la mort de l'unité et attribue des pièces à l'ennemi si applicable.

        Args:
            killer (Unit, optional): L'entité attaquante. Defaults to None.
        """
        
        # Attribution des pièces uniquement si tué par un ennemi
        if killer and hasattr(killer, 'team') and killer.team != self.team and hasattr(self, 'game') and hasattr(self.game, 'hud'):
            # Détermination du type d'unité pour la récompense
            unit_type = getattr(self, 'unit_type', None)

            if self.team == "red" : 
                self.game.hud.piece_green.count += 1
            else :
                self.game.hud.piece_red.count += 1
        self.kill()  # Retire l'unité du groupe pygame
        
    def get_health_percentage(self):
        """Retourne le pourcentage de vie restante."""
        
        return self.current_health / self.max_health if self.max_health > 0 else 0
    
    def distance_to(self, other_unit: "Unit"):
        """Calcule la distance vers une autre unité.

        Args:
            other_unit (Unit): Autre unité.

        Returns:
            distance (float): Distance entre les deux unités.
        """
        
        dx = self.position[0] - other_unit.position[0]
        dy = self.position[1] - other_unit.position[1]
        return (dx**2 + dy**2)**0.5
    
    def is_in_range(self, other_unit: "Unit"):
        """Vérifie si une autre unité est à portée.

        Args:
            other_unit (Unit): Autre unité.

        Returns:
            bool: True si l'autre unité est à portée, False sinon.
        """
        
        distance = self.distance_to(other_unit)
        range_pixels = self.range * 32  # Conversion cases en pixels
        return distance <= range_pixels
    
    def can_attack(self):
        """Vérifie si l'unité peut attaquer (cooldown respecté)."""
        if not hasattr(self, 'fire_rate') or self.fire_rate == 0:
            return False
        current_time = time.time()
        time_since_last_shot = current_time - self.last_shot_time
        multiplica = self.game.hud.timer.get_speed_multiplier()
        return time_since_last_shot >= (1.0 / (self.fire_rate * multiplica))
    
    def attack(self, target: "Unit", combat_system: "CombatSystem" = None):
        """Attaque une cible si possible. Si un système de combat est fourni, créer un projectile.

        Args:
            target (Unit): Cible de l'attaque.
            combat_system (CombatSystem, optional): Le systeme de combat. Defaults to None.

        Returns:
            Bool: True si l'attaque a été effectuée, False sinon.
        """
        
        if not self.can_attack() or not self.is_in_range(target):
            return False
            
        if target.team != self.team and target.is_alive:
            # Si un système de combat est fourni, créer un projectile
            if combat_system:
                combat_system.fire_projectile(self, target)
            else:
                # Attaque directe (sans projectile)
                target.take_damage(self.damage, killer=self)
            
            self.last_shot_time = time.time()
            return True
        return False
    
    def combat_update(self, combat_system: "CombatSysteme" = None):
        """Met à jour la logique de combat. Si une cible est définie, essaie d'attaquer la cible.

        Args:
            combat_system (CombatSysteme, optional): Le systeme de combat. Defaults to None.
        """
        
        if self.target and self.target.is_alive:
            if self.is_in_range(self.target):
                self.attack(self.target, combat_system)
            else:
                self.target = None
        
    def draw_health_bar(self, screen: pygame.Surface, camera_offset: tuple[int, int]=(0, 0), zoom: float=1.0):
        """Dessine une barre de vie au-dessus de l'unité, qui suit le zoom et la caméra.

        Args:
            screen (pygame.Surface): Surface sur laquelle dessiner la barre de vie.
            camera_offset (tuple[int, int], optional): La postition de la caméra. Defaults to (0, 0).
            zoom (float, optional): Le niveau de zoom. Defaults to 1.0.
        """
        
        if not self.is_alive or self.current_health == self.max_health:
            return
        # Position monde -> écran avec zoom
        screen_x = (self.position[0] - camera_offset[0]) * zoom
        screen_y = (self.position[1] - camera_offset[1]) * zoom
        # Adapter la largeur/hauteur de la barre au zoom
        bar_width = int(30 * zoom)
        bar_height = max(2, int(4 * zoom))
        bar_x = int(screen_x - bar_width // 2)
        bar_y = int(screen_y - 30 * zoom)  # 30 pixels au-dessus du centre du sprite
        # Barre de fond (rouge)
        background_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(screen, (255, 0, 0), background_rect)
        # Barre de vie (verte)
        health_percentage = self.get_health_percentage()
        health_width = int(bar_width * health_percentage)
        health_rect = pygame.Rect(bar_x, bar_y, health_width, bar_height)
        pygame.draw.rect(screen, (0, 255, 0), health_rect)
        # Contour
        pygame.draw.rect(screen, (0, 0, 0), background_rect, 1)

    def draw_range(self, screen: pygame.Surface, camera_offset: list[int, int]=(0, 0)):
        """Dessine une zone de portée de tir autour de l'unité.

        Args:
            screen (pygame.Surface): Surface sur laquelle dessiner.
            camera_offset (list[int, int], optional): Position de la caméra. Defaults to (0, 0).
        """
        
        if not self.is_alive or not self.is_selected:
            return

        # Calculer le rayon en pixels (range en cases * 32 pixels par case)
        range_radius = self.range * 32

        # Position de l'unité avec décalage de la caméra
        center_x = int(self.position[0] - camera_offset[0])
        center_y = int(self.position[1] - camera_offset[1])

        # Vérifier que l'unité est visible à l'écran
        if (-range_radius <= center_x <= screen.get_width() + range_radius and 
            -range_radius <= center_y <= screen.get_height() + range_radius):
        
            # Dessiner un cercle semi-transparent pour la portée avec la couleur de l'équipe
            surface = pygame.Surface((range_radius * 2, range_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(surface, self.range_color, (range_radius, range_radius), range_radius)
            screen.blit(surface, (center_x - range_radius, center_y - range_radius))
            
            # Dessiner un contour plus visible
            pygame.draw.circle(screen, self.range_color[:3], (center_x, center_y), range_radius, 3)
            
            # Afficher le nombre d'ennemis en portée
            if self.enemies_in_range:
                font = pygame.font.Font(None, 24)
                text = font.render(f"Ennemis: {len(self.enemies_in_range)} - Appuyez sur 'T'", True, (255, 255, 255))
                text_rect = text.get_rect(center=(center_x, center_y - range_radius - 30))
                
                # Fond pour le texte
                bg_surface = pygame.Surface((text.get_width() + 10, text.get_height() + 4), pygame.SRCALPHA)
                bg_surface.fill((0, 0, 0, 150))
                screen.blit(bg_surface, (text_rect.x - 5, text_rect.y - 2))
                screen.blit(text, text_rect)

    def update_enemies_in_range(self, all_units: list["Unit"]):
        """Met à jour la liste des ennemis dans la portée de tir (collision cercle-rectangle pour plateformes).

        Args:
            all_units (list[&quot;Unit&quot;]): Liste de toutes les unités du jeu.
        """
        
        self.enemies_in_range = []
        range_pixels = self.range * 32  # Rayon du cercle de portée

        for unit in all_units:
            if not unit.is_alive or unit.team == self.team:
                continue

            # Si la cible a un rect (plateforme ou autre sprite), on fait une collision cercle-rectangle
            if hasattr(unit, 'rect'):
                # Centre du cercle
                cx, cy = self.position[0], self.position[1]
                # Rectangle cible
                rx, ry, rw, rh = unit.rect.left, unit.rect.top, unit.rect.width, unit.rect.height

                # Trouver le point du rectangle le plus proche du centre du cercle
                closest_x = max(rx, min(cx, rx + rw))
                closest_y = max(ry, min(cy, ry + rh))
                # Calculer la distance entre ce point et le centre du cercle
                distance = math.hypot(cx - closest_x, cy - closest_y)
                if distance <= range_pixels:
                    self.enemies_in_range.append(unit)
            else:
                # Fallback : distance centre-centre
                distance = math.sqrt(
                    (self.position[0] - unit.position[0])**2 + 
                    (self.position[1] - unit.position[1])**2
                )
                if distance <= range_pixels:
                    self.enemies_in_range.append(unit)
    
    def can_shoot(self, current_time: int):
        """Vérifie si l'unité peut tirer (cooldown de 1 seconde).

        Args:
            current_time (int): Temps actuel en millisecondes.

        Returns:
            bool: True si l'unité peut tirer, False sinon.
        """
        
        multiplica = self.game.hud.timer.get_speed_multiplier()
        cooldown = 1000 / multiplica # Cooldown d'1 seconde entre chaque tir
        return current_time - self.last_shot_time >= cooldown
    
    def get_closest_enemy_in_range(self):
        """Retourne l'ennemi le plus proche dans la portée."""
        
        if not self.enemies_in_range:
            return None
            
        closest_enemy = None
        min_distance = float('inf')
        
        for enemy in self.enemies_in_range:
            if not enemy.is_alive:
                continue
                
            distance = math.sqrt(
                (self.position[0] - enemy.position[0])**2 + 
                (self.position[1] - enemy.position[1])**2
            )
            
            if distance < min_distance:
                min_distance = distance
                closest_enemy = enemy
                
        return closest_enemy