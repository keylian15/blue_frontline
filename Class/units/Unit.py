import pygame
import time
from Global import *
from Utils import load_tileset

class Unit(pygame.sprite.Sprite):
    """Classe de base pour toutes les unités du jeu."""
    
    def __init__(self, x, y, image_path, team="red", unit_type=None):
        super().__init__()
        
        # Position et mouvement
        self.position = [float(x), float(y)]
        self.speed_x = 0  # Vitesse en pixels par seconde sur l'axe X
        self.speed_y = 0  # Vitesse en pixels par seconde sur l'axe Y
        
        # Statistiques de base
        self.max_health = 100
        self.current_health = self.max_health
        self.cost = 0  # Coût en pétrole
        self.team = team  # "red" ou "green"
        
        # Combat
        self.damage = 1  # Dégâts par seconde
        self.range = 1  # Portée en cases (32 pixels par case)
        self.last_shot_time = 0
        self.fire_rate = 1.0  # Tirs par seconde
        
        # Image et sprite
        self.load_sprite_from_tileset(team, unit_type)
        self.rect = self.image.get_rect()
        self.rect.center = (self.position[0], self.position[1])
        
        # État
        self.is_alive = True
        self.target = None
    
    # Chaque unité peut avoir sa propre tuile, pour chaque équipe, et tout est configurable
    def load_sprite_from_tileset(self, team, unit_type):
        """Charge l'image de l'unité depuis le tileset approprié."""
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
        
    def load_image(self, image_path):
        """Charge l'image de l'unité."""
        try:
            self.image = pygame.image.load(image_path).convert_alpha()
        except pygame.error:
            # Image par défaut si l'image n'est pas trouvée
            self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
            self.image.fill((255, 0, 0))  # Rectangle rouge par défaut
    
    def update(self, dt=0, combat_system=None):
        """Met à jour l'unité (mouvement, combat, etc.)."""
        if not self.is_alive:
            return
            
        # Mise à jour de la position
        self.move(dt)
        
        # Mise à jour du combat
        self.combat_update(dt, combat_system)
        
        # Mise à jour du rectangle de collision
        self.rect.center = (int(self.position[0]), int(self.position[1]))
    
    def move(self, dt):
        """Déplace l'unité selon sa vitesse."""
        self.position[0] += self.speed_x * dt
        self.position[1] += self.speed_y * dt
    
    def set_velocity(self, vx, vy):
        """Définit la vitesse de l'unité."""
        self.speed_x = vx
        self.speed_y = vy
    
    def move_to(self, target_x, target_y, speed):
        """Déplace l'unité vers une position cible à une vitesse donnée."""
        dx = target_x - self.position[0]
        dy = target_y - self.position[1]
        distance = (dx**2 + dy**2)**0.5
        
        if distance > 0:
            # Normaliser le vecteur direction et appliquer la vitesse
            self.speed_x = (dx / distance) * speed
            self.speed_y = (dy / distance) * speed
        else:
            self.speed_x = 0
            self.speed_y = 0
    
    def stop(self):
        """Arrête le mouvement de l'unité."""
        self.speed_x = 0
        self.speed_y = 0
    
    def take_damage(self, damage):
        """Inflige des dégâts à l'unité."""
        self.current_health -= damage
        if self.current_health <= 0:
            self.current_health = 0
            self.is_alive = False
            self.die()
    
    def die(self):
        """Gère la mort de l'unité."""
        self.kill()  # Retire l'unité du groupe pygame
    
    def heal(self, amount):
        """Soigne l'unité."""
        self.current_health = min(self.current_health + amount, self.max_health)
    
    def get_health_percentage(self):
        """Retourne le pourcentage de vie restante."""
        return self.current_health / self.max_health if self.max_health > 0 else 0
    
    def distance_to(self, other_unit):
        """Calcule la distance vers une autre unité."""
        dx = self.position[0] - other_unit.position[0]
        dy = self.position[1] - other_unit.position[1]
        return (dx**2 + dy**2)**0.5
    
    def is_in_range(self, other_unit):
        """Vérifie si une autre unité est à portée."""
        distance = self.distance_to(other_unit)
        range_pixels = self.range * 32  # Conversion cases en pixels
        return distance <= range_pixels
    
    def can_attack(self):
        """Vérifie si l'unité peut attaquer (cooldown respecté)."""
        current_time = time.time()
        time_since_last_shot = current_time - self.last_shot_time
        return time_since_last_shot >= (1.0 / self.fire_rate)
    
    def attack(self, target, combat_system=None):
        """Attaque une cible si possible."""
        if not self.can_attack() or not self.is_in_range(target):
            return False
            
        if target.team != self.team and target.is_alive:
            # Si un système de combat est fourni, créer un projectile
            if combat_system:
                combat_system.fire_projectile(self, target)
            else:
                # Attaque directe (sans projectile)
                target.take_damage(self.damage)
            
            self.last_shot_time = time.time()
            return True
        return False
    
    def combat_update(self, dt, combat_system=None):
        """Met à jour la logique de combat."""
        if self.target and self.target.is_alive:
            if self.is_in_range(self.target):
                self.attack(self.target, combat_system)
            else:
                self.target = None
    
    def set_target(self, target):
        """Définit une cible pour l'unité."""
        if target and target.team != self.team:
            self.target = target
    
    def draw_health_bar(self, screen, camera_offset=(0, 0)):
        """Dessine une barre de vie au-dessus de l'unité."""
        if not self.is_alive or self.current_health == self.max_health:
            return
            
        bar_width = 30
        bar_height = 4
        bar_x = self.rect.centerx - bar_width // 2 - camera_offset[0]
        bar_y = self.rect.top - 10 - camera_offset[1]
        
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
