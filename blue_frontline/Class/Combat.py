import pygame, math
from Class.units.Unit import Unit
from Utils import resource_path
from Global import RED_TEAM_PATH, GREEN_TEAM_PATH
from Utils import load_tileset
from Class.ExplosionRenderer import explosion_renderer


class Explosion:
    """Représentation logique d'une explosion (sans affichage).

    L'affichage est géré par `Class.ExplosionRenderer.explosion_renderer`.
    """

    def __init__(self, x: int, y: int, size: int = 64):
        self.position = [float(x), float(y)]
        self.size = size
        self.is_active = True
        self.lifetime = 0.8
        self.elapsed_time = 0

    def update(self, dt: float):
        if not self.is_active:
            return
        self.elapsed_time += dt
        if self.elapsed_time >= self.lifetime:
            self.destroy()

    def destroy(self):
        self.is_active = False


class Projectile(pygame.sprite.Sprite):
    """Classe pour gérer les projectiles tirés par les unités."""
    
    def __init__(self, x: int, y: int, target_x: int, target_y: int, damage: int, speed: int, shooter : Unit):
        """Fonction permettant d'initialiser un projectile.

        Args:
            x (int): La position x du projectile.
            y (int): La position y du projectile.
            target_x (int): La position x de la cible.
            target_y (int): La position y de la cible.
            damage (int): Le dommage infligé par le projectile.
            speed (int): La vitesse du projectile.
            shooter (Unit): L'unité qui a tiré le projectile.
        """
        
        super().__init__()
                
        # Position de départ
        self.position = [float(x), float(y)]
        
        # Cible et dégâts
        self.target_x = target_x
        self.target_y = target_y
        self.damage = damage
        self.shooter = shooter
        
        # Vitesse du projectile
        self.speed = speed
        
        # Calculer la direction
        dx = target_x - x
        dy = target_y - y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            self.velocity_x = (dx / distance) * speed
            self.velocity_y = (dy / distance) * speed
        else:
            self.velocity_x = 0
            self.velocity_y = 0
        
        # Image du projectile
        self.load_image()
        self.rect = self.image.get_rect()
        self.rect.center = (int(self.position[0]), int(self.position[1]))
        
        # État
        self.is_active = True
        self.max_distance = 800  # Distance maximale avant disparition
        self.distance_traveled = 0
    
    def load_image(self):
        """Charge l'image du projectile."""
        try:
            # Essayer de charger l'image bullet.png
            from Utils import resource_path
            self.image = pygame.image.load(resource_path('assets/entity/png/bullet.png')).convert_alpha()
        except (pygame.error, FileNotFoundError):
            # Si l'image n'existe pas, créer un projectile simple
            self.image = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (255, 255, 0), (4, 4), 4)  # Projectile jaune
            pygame.draw.circle(self.image, (255, 165, 0), (4, 4), 2)  # Centre orange
    
    def update(self, dt: float):
        """Fonction permettant de mettre à jour le projectile.

        Args:
            dt (float): La différence de temps entre chaque frame.
        """
        
        if not self.is_active:
            return
        
        # Déplacer le projectile
        old_x, old_y = self.position[0], self.position[1]
        self.position[0] += self.velocity_x * dt
        self.position[1] += self.velocity_y * dt
        
        # Calculer la distance parcourue
        dx = self.position[0] - old_x
        dy = self.position[1] - old_y
        self.distance_traveled += math.sqrt(dx**2 + dy**2)
        
        # Mettre à jour le rectangle
        self.rect.center = (int(self.position[0]), int(self.position[1]))
        
        # Vérifier si le projectile a atteint sa distance maximale
        if self.distance_traveled >= self.max_distance:
            self.destroy()
        
        # Vérifier si le projectile a atteint sa cible (approximativement)
        distance_to_target = math.sqrt((self.position[0] - self.target_x)**2 + 
                                     (self.position[1] - self.target_y)**2)
        if distance_to_target < 15:  # 15 pixels de tolérance
            self.on_impact()
    
    def on_impact(self):
        """Appelé quand le projectile atteint sa cible."""
        
        self.destroy()
    
    def destroy(self):
        """Détruit le projectile."""
        
        self.is_active = False
        self.kill()  # Retire du groupe pygame
    
    def check_collision(self, target: Unit):
        """Vérifie la collision avec une cible.

        Args:
            target (Unit): La cible à vérifier.

        Returns:
            bool: True si il y a collision, False sinon.
        """

        if not self.is_active:
            return False

        if target is self.shooter:
            return False

        # Vérifier que l'unité cible n'est pas de la même équipe (sauf pour les plateformes)
        if self.shooter and hasattr(target, 'team') and target.team == self.shooter.team:
            # Les plateformes peuvent être ciblées par toutes les équipes
            if not (hasattr(target, 'is_platform') and target.is_platform):
                return False
        
        # Vérifier si la cible est encore vivante
        if hasattr(target, 'is_alive') and not target.is_alive:
            return False
        
        # Pour les plateformes avec hitbox polygonale, utiliser la méthode spécialisée
        if hasattr(target, 'is_platform') and target.is_platform and hasattr(target, 'point_in_hitbox'):
            if target.point_in_hitbox(self.position[0], self.position[1]):
                # Inflige les dégâts et passe le tireur comme killer
                if hasattr(target, 'take_damage'):
                    target.take_damage(self.damage, killer=self.shooter)
                self.destroy()
                return True
            return False
        
        # Calculer la distance entre le projectile et l'unité (Méthode classique)
        target_pos = getattr(target, 'position', (0, 0))
        distance = math.sqrt(
            (self.position[0] - target_pos[0])**2 + 
            (self.position[1] - target_pos[1])**2
        )
        
        # Si la distance est suffisamment petite (collision)
        if distance < 25:  # Rayon de collision
            # Inflige les dégâts et passe le tireur comme killer
            if hasattr(target, 'take_damage'):
                target.take_damage(self.damage, killer=self.shooter)
            self.destroy()
            return True
            
        return False


class Mine(pygame.sprite.Sprite):
    """Classe pour gérer les mines posées par les sous-marins."""

    def __init__(self, x: int, y: int, team: str, damage: int = 18, combat_system=None):
        """Initialise une mine.

        Args:
            x (int): Position x de la mine.
            y (int): Position y de la mine.
            team (str): Équipe qui a posé la mine ("red" ou "green").
            damage (int): Dégâts infligés par la mine. Defaults to 18.
            combat_system: Référence au système de combat pour créer l'explosion.
        """
        super().__init__()

        # Position et propriétés
        self.position = [float(x), float(y)]
        self.team = team
        self.damage = damage
        self.is_active = True
        self.combat_system = combat_system

        # Charger l'image de la mine
        self.load_image()
        self.rect = self.image.get_rect()
        self.rect.center = (int(self.position[0]), int(self.position[1]))

        # Rayon de détection de collision
        self.collision_radius = 30

    def load_image(self):
        """Charge l'image de la mine."""
        try:
            # Charger le spritesheet de l'équipe appropriée
            if self.team == "red":
                team_spritesheet = load_tileset(RED_TEAM_PATH)
                mine_image = team_spritesheet[5]  # Utiliser l'index 5 pour la mine
            else:
                team_spritesheet = load_tileset(GREEN_TEAM_PATH)
                mine_image = team_spritesheet[5]  # Utiliser l'index 5 pour la mine

            # Redimensionner l'image
            self.image = pygame.transform.scale(mine_image, (20, 20))

        except (pygame.error, IndexError):
            # Fallback : créer une mine simple
            self.image = pygame.Surface((20, 20))
            color = (200, 0, 0) if self.team == "red" else (0, 200, 0)
            pygame.draw.circle(self.image, color, (10, 10), 8)
            pygame.draw.circle(self.image, (50, 50, 50), (10, 10), 8, 2)
            self.image.set_colorkey((0, 0, 0))

    def update(self, dt: int = 0):
        """Met à jour la mine.

        Args:
            dt (int): Delta time en millisecondes.
        """
        # Les mines sont statiques, pas besoin de mise à jour particulière
        pass

    def check_collision(self, unit):
        """Vérifie la collision avec une unité et inflige des dégâts si c'est un ennemi.

        Args:
            unit: L'unité à vérifier.

        Returns:
            bool: True si la mine a explosé, False sinon.
        """
        if not self.is_active or not unit.is_alive:
            return False

        # Vérifier si l'unité est ennemie
        if unit.team == self.team:
            return False

        # Calculer la distance
        dx = unit.position[0] - self.position[0]
        dy = unit.position[1] - self.position[1]
        distance = math.sqrt(dx**2 + dy**2)

        # Si la distance est suffisamment petite (collision)
        if distance < self.collision_radius:
            # Infliger les dégâts
            if hasattr(unit, 'take_damage'):
                unit.take_damage(self.damage)

            # Désactiver la mine (elle explose)
            self.explode()
            return True

        return False

    def explode(self):
        """Fait exploser la mine."""
        # Créer une explosion visuelle si le combat_system est disponible
        if self.combat_system and hasattr(self.combat_system, 'add_explosion'):
            explosion = Explosion(int(self.position[0]), int(self.position[1]), size=48)
            self.combat_system.add_explosion(explosion)
        
        self.is_active = False
        self.kill()  # Retire la mine du groupe de sprites

    def draw(self, screen: pygame.Surface, camera_offset: tuple[float, float] = (0, 0)):
        """Dessine la mine sur l'écran.

        Args:
            screen (pygame.Surface): Surface sur laquelle dessiner.
            camera_offset (tuple[float, float]): Décalage de la caméra.
        """
        if self.is_active:
            draw_x = int(self.position[0] - camera_offset[0])
            draw_y = int(self.position[1] - camera_offset[1])
            screen.blit(self.image, (draw_x - self.image.get_width()//2,
                                   draw_y - self.image.get_height()//2))


class CombatSystem:
    """Système de gestion du combat, des projectiles et des mines."""

    def __init__(self, game: "Game"):
        """Fonction permettant d'initialiser le système de combat.

        Args:
            game (Game): L'instance du jeu.
        """

        self.projectiles = pygame.sprite.Group()
        self.units = pygame.sprite.Group()
        self.mines = pygame.sprite.Group()
        self.explosions = []  # Liste simple car Explosion n'est plus un Sprite
        self.game = game
    
    def add_unit(self, unit: Unit):
        """Ajoute une unité au système de combat.

        Args:
            unit (Unit): Unité à ajouter.
        """

        self.units.add(unit)

    def add_mine(self, mine: "Mine"):
        """Ajoute une mine au système de combat.

        Args:
            mine (Mine): Mine à ajouter.
        """

        self.mines.add(mine)
    
    def add_explosion(self, explosion: "Explosion"):
        """Ajoute une explosion au système de combat.
        
        Args:
            explosion (Explosion): Explosion à ajouter.
        """
        self.explosions.append(explosion)
    
    def fire_projectile(self, shooter: Unit, target: Unit):
        """Crée un projectile tiré par une unité vers une cible.

        Args:
            shooter (Unit): Unité qui tire.
            target (Unit): Unité cible.

        Returns:
            Projectile: Projectile créé.
        """

        if not shooter.is_alive or not target.is_alive:
            return None
        
        # Suivre le tir pour les succès
        if hasattr(shooter, 'game') and hasattr(shooter.game, 'achievements_system') and shooter.game.achievements_system:
            shooter.game.achievements_system.track_bullet_fired()

            
        # Créer le projectile
        projectile = Projectile(
            shooter.position[0], 
            shooter.position[1],
            target.position[0], 
            target.position[1],
            shooter.damage,
            300,
            shooter
        )
        
        self.projectiles.add(projectile)
        return projectile
    
    def update(self, dt: float):
        """Met à jour tous les projectiles, mines, explosions et gère les collisions.

        Args:
            dt (float): La différence de temps entre chaque frame.
        """

        # Mettre à jour tous les projectiles
        self.projectiles.update(dt)

        # Mettre à jour toutes les mines
        self.mines.update(dt)
        
        # Mettre à jour toutes les explosions
        for explosion in self.explosions:
            explosion.update(dt)
        
        # Nettoyer les explosions inactives
        self.explosions = [exp for exp in self.explosions if exp.is_active]

        # Vérifier les collisions entre projectiles et unités
        for projectile in self.projectiles:
            if not projectile.is_active:
                continue

            # NOTE: on parcourt les unités; check_collision() doit gérer dégâts + désactivation proj
            for unit in self.units:
                if projectile.check_collision(unit):
                    # === AUDIO: drop coin si l'unité vient de mourir suite à l'impact ===
                    try:
                        # Certaines implémentations mettent à jour is_alive dans check_collision()
                        if (hasattr(unit, "is_alive") and not unit.is_alive
                                and hasattr(unit, "position")
                                and hasattr(self, "game") and hasattr(self.game, "sound") and self.game.sound):
                            # On joue le son au centre de l'unité détruite
                            pos = (unit.position[0], unit.position[1])
                            self.game.sound.on_coin_drop(pos)
                    except Exception:
                        # On ne casse jamais la boucle de jeu à cause de l'audio
                        pass

                    break  # Projectile détruit, passer au suivant

        # Vérifier les collisions entre mines et unités
        for mine in self.mines:
            if not mine.is_active:
                continue

            for unit in self.units:
                if mine.check_collision(unit):
                    # === AUDIO: explosion de mine ===
                    try:
                        if (hasattr(unit, "is_alive") and not unit.is_alive
                                and hasattr(unit, "position")
                                and hasattr(self, "game") and hasattr(self.game, "sound") and self.game.sound):
                            # On joue le son au centre de l'unité détruite
                            pos = (unit.position[0], unit.position[1])
                            self.game.sound.on_coin_drop(pos)
                    except Exception:
                        # On ne casse jamais la boucle de jeu à cause de l'audio
                        pass
                    break  # Mine explosée, passer à la suivante
    
    def draw(self, screen: pygame.Surface, camera_offset: tuple[float, float], zoom: float):
        """Dessine tous les projectiles et mines en tenant compte du zoom.

        Args:
            screen (pygame.Surface): Surface sur laquelle dessiner les projectiles et mines.
            camera_offset (tuple[float, float]): Décalage de la caméra.
            zoom (float): Zoom de la caméra.
        """

        # Dessiner les projectiles
        for projectile in self.projectiles:
            if projectile.is_active:
                # Position avec décalage de caméra et zoom
                screen_x = (projectile.position[0] - camera_offset[0]) * zoom
                screen_y = (projectile.position[1] - camera_offset[1]) * zoom
                # Adapter la taille du projectile au zoom
                if zoom != 1.0:
                    scaled_image = pygame.transform.scale(
                        projectile.image,
                        (max(1, int(projectile.image.get_width() * zoom)), max(1, int(projectile.image.get_height() * zoom)))
                    )
                else:
                    scaled_image = projectile.image
                screen.blit(scaled_image, (screen_x - scaled_image.get_width()//2, screen_y - scaled_image.get_height()//2))

        # Dessiner les mines
        for mine in self.mines:
            if mine.is_active:
                # Position avec décalage de caméra et zoom
                screen_x = (mine.position[0] - camera_offset[0]) * zoom
                screen_y = (mine.position[1] - camera_offset[1]) * zoom
                # Adapter la taille de la mine au zoom
                if zoom != 1.0:
                    scaled_image = pygame.transform.scale(
                        mine.image,
                        (max(1, int(mine.image.get_width() * zoom)), max(1, int(mine.image.get_height() * zoom)))
                    )
                else:
                    scaled_image = mine.image
                screen.blit(scaled_image, (screen_x - scaled_image.get_width()//2, screen_y - scaled_image.get_height()//2))
        
        # Dessiner les explosions via le renderer dédié
        for explosion in self.explosions:
            if explosion.is_active:
                try:
                    explosion_renderer.render(explosion, screen, camera_offset, zoom)
                except Exception:
                    # Never break the main loop for rendering errors
                    pass