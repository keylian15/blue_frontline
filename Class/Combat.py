import pygame
import math
from Global import *

class Projectile(pygame.sprite.Sprite):
    """Classe pour gérer les projectiles tirés par les unités."""
    
    def __init__(self, x, y, target_x, target_y, damage, speed=200, shooter=None):
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
    
    def update(self, dt):
        """Met à jour le projectile."""
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
        if distance_to_target < 10:  # 10 pixels de tolérance
            self.on_impact()
    
    def on_impact(self):
        """Appelé quand le projectile atteint sa cible."""
        self.destroy()
    
    def destroy(self):
        """Détruit le projectile."""
        self.is_active = False
        self.kill()  # Retire du groupe pygame
    
    def check_collision(self, target):
        """Vérifie la collision avec une cible."""
        if not self.is_active or not target.is_alive:
            return False
            
        # Vérifier si le projectile touche la cible
        if self.rect.colliderect(target.rect):
            # Vérifier que c'est un ennemi
            if self.shooter and target.team != self.shooter.team:
                target.take_damage(self.damage)
                self.destroy()
                return True
        return False


class CombatSystem:
    """Système de gestion du combat et des projectiles."""
    
    def __init__(self):
        self.projectiles = pygame.sprite.Group()
        self.units = pygame.sprite.Group()
    
    def add_unit(self, unit):
        """Ajoute une unité au système de combat."""
        self.units.add(unit)
    
    def remove_unit(self, unit):
        """Retire une unité du système de combat."""
        self.units.remove(unit)
    
    def fire_projectile(self, shooter, target):
        """Crée un projectile tiré par une unité vers une cible."""
        if not shooter.is_alive or not target.is_alive:
            return None
            
        # Créer le projectile
        projectile = Projectile(
            shooter.position[0], 
            shooter.position[1],
            target.position[0], 
            target.position[1],
            shooter.damage,
            speed=300,  # Vitesse des projectiles
            shooter=shooter
        )
        
        self.projectiles.add(projectile)
        return projectile
    
    def update(self, dt):
        """Met à jour tous les projectiles et gère les collisions."""
        # Mettre à jour tous les projectiles
        self.projectiles.update(dt)
        
        # Vérifier les collisions entre projectiles et unités
        for projectile in self.projectiles:
            for unit in self.units:
                if projectile.check_collision(unit):
                    break  # Projectile détruit, passer au suivant
    
    def draw(self, screen):
        """Dessine tous les projectiles."""
        self.projectiles.draw(screen)
    
    def get_projectile_count(self):
        """Retourne le nombre de projectiles actifs."""
        return len(self.projectiles)
    
    def clear_projectiles(self):
        """Supprime tous les projectiles."""
        self.projectiles.empty()