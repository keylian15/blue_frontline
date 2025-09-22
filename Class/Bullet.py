import pygame
import math
from Utils import resource_path

class Bullet(pygame.sprite.Sprite):
    """Classe pour gérer les projectiles du jeu."""
    
    def __init__(self, start_x, start_y, target_x, target_y, damage, speed=300, team="red"):
        super().__init__()
        
        # Charger l'image du projectile
        try:
            self.image = pygame.image.load(resource_path('Class/bullet.png')).convert_alpha()
        except pygame.error:
            # Si l'image n'existe pas, créer un cercle simple
            self.image = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (255, 255, 0), (4, 4), 4)
        
        self.rect = self.image.get_rect()
        
        # Position de départ
        self.position = [float(start_x), float(start_y)]
        self.rect.center = (int(start_x), int(start_y))
        
        # Calculer la direction vers la cible
        dx = target_x - start_x
        dy = target_y - start_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 0:
            # Normaliser la direction
            self.velocity_x = (dx / distance) * speed
            self.velocity_y = (dy / distance) * speed
        else:
            self.velocity_x = 0
            self.velocity_y = 0
        
        # Propriétés du projectile
        self.damage = damage
        self.speed = speed
        self.team = team
        self.is_alive = True
        self.max_range = 500  # Distance maximale avant destruction automatique
        self.traveled_distance = 0
        
    def update(self, dt):
        """Met à jour la position du projectile."""
        if not self.is_alive:
            return
            
        # Calculer le déplacement
        dx = self.velocity_x * dt
        dy = self.velocity_y * dt
        
        # Mettre à jour la position
        self.position[0] += dx
        self.position[1] += dy
        self.rect.center = (int(self.position[0]), int(self.position[1]))
        
        # Suivre la distance parcourue
        self.traveled_distance += math.sqrt(dx*dx + dy*dy)
        
        # Détruire le projectile s'il a parcouru trop de distance
        if self.traveled_distance > self.max_range:
            self.destroy()
    
    def check_collision(self, target_unit):
        """Vérifie la collision avec une unité cible."""
        if not self.is_alive or not target_unit.is_alive:
            return False
            
        # Vérifier que l'unité cible n'est pas de la même équipe
        if target_unit.team == self.team:
            return False
            
        # Calculer la distance entre le projectile et l'unité
        distance = math.sqrt(
            (self.position[0] - target_unit.position[0])**2 + 
            (self.position[1] - target_unit.position[1])**2
        )
        
        # Si la distance est suffisamment petite (collision)
        if distance < 25:  # Rayon de collision agrandi pour être plus facile à toucher
            target_unit.take_damage(self.damage)
            self.destroy()
            return True
            
        return False
    
    def destroy(self):
        """Détruit le projectile."""
        self.is_alive = False
        self.kill()  # Retire le sprite du groupe
    
    def draw(self, screen, camera_offset=(0, 0)):
        """Dessine le projectile à l'écran."""
        if not self.is_alive:
            return
            
        # Position avec décalage de caméra
        screen_x = int(self.position[0] - camera_offset[0])
        screen_y = int(self.position[1] - camera_offset[1])
        
        # Dessiner le projectile
        screen.blit(self.image, (screen_x - self.rect.width//2, screen_y - self.rect.height//2))