import pygame, math
from Class.units.Unit import Unit

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

        if not self.is_active or not target.is_alive:
            return False
            
        # Vérifier que l'unité cible n'est pas de la même équipe
        if self.shooter and target.team == self.shooter.team:
            return False
            
        # Calculer la distance entre le projectile et l'unité
        distance = math.sqrt(
            (self.position[0] - target.position[0])**2 + 
            (self.position[1] - target.position[1])**2
        )
        
        # Si la distance est suffisamment petite (collision)
        if distance < 25:  # Rayon de collision
            # Inflige les dégâts et passe le tireur comme killer
            if hasattr(target, 'take_damage'):
                target.take_damage(self.damage, killer=self.shooter)
            self.destroy()
            return True
            
        return False


class CombatSystem:
    """Système de gestion du combat et des projectiles."""
    
    def __init__(self, game):
        """Fonction permettant d'initialiser le système de combat."""
        
        self.projectiles = pygame.sprite.Group()
        self.units = pygame.sprite.Group()
        self.game = game
    
    def add_unit(self, unit: Unit):
        """Ajoute une unité au système de combat.

        Args:
            unit (Unit): Unité à ajouter.
        """
        
        self.units.add(unit)
    
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
        """Met à jour tous les projectiles et gère les collisions.

        Args:
            dt (float): La différence de temps entre chaque frame.
        """
        
        # Mettre à jour tous les projectiles
        self.projectiles.update(dt)
        
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
    
    def draw(self, screen: pygame.Surface, camera_offset: tuple[float, float], zoom: float):
        """Dessine tous les projectiles en tenant compte du zoom.

        Args:
            screen (pygame.Surface): Surface sur laquelle dessiner les projectiles.
            camera_offset (tuple[float, float]): Décalage de la caméra.
            zoom (float): Zoom de la caméra.
        """        
        
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