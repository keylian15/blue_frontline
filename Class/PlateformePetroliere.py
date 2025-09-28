import pygame

class PlateformePetroliere(pygame.sprite.Sprite):
    def __init__(self, x, y, team="red", max_health=1000):
        super().__init__()
        self.team = team
        self.max_health = max_health
        self.current_health = max_health
        self.is_alive = True
        self.position = [float(x), float(y)]  # Position centrale de la plateforme
        self.width = 160   # Rectangle beaucoup plus grand et carré (invisible mais actif)
        self.height = 160  # Rectangle beaucoup plus grand et carré (invisible mais actif)
        self.unit_type = "plateforme"
        self.is_selected = False
        
        # Image invisible (rectangle transparent) - garde les hitboxes mais invisible
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        color = (0, 0, 0, 0)  # Complètement transparent (invisible)
        self.image.fill(color)
        
        # Le rect utilise la position (x, y) comme centre
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        
        # Pour compatibilité avec la logique d'unités
        self.range = 0
        self.damage = 0
        self.is_platform = True
        
    def take_damage(self, damage, killer=None):
        """Inflige des dégâts à la plateforme."""
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

    def draw_health_bar(self, screen, camera_offset=(0, 0), zoom=1.0):
        """Dessine une barre de vie large pour la plateforme."""
        if not self.is_alive:
            return
        screen_x = (self.position[0] - camera_offset[0]) * zoom
        screen_y = (self.position[1] - camera_offset[1]) * zoom
        
        # Barre de vie plus large pour les plateformes, placée en dessous de l'image
        bar_width = int(180 * zoom)  # Largeur fixe adaptée aux plateformes
        bar_height = max(12, int(20 * zoom))
        bar_x = int(screen_x - bar_width // 2)
        # Placer la barre en dessous de l'image de la plateforme (environ 80px en dessous du centre)
        bar_y = int(screen_y + 80 * zoom)
        
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