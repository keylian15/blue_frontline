import pygame, math
from Global import *

class AchievementNotification:
    """Notification popup pour les succès débloqués."""
    
    def __init__(self, achievement, screen_width, screen_height):
        self.achievement = achievement
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Dimensions de la notification
        self.width = 350
        self.height = 100
        self.margin = 20
        
        # Position (en bas à droite)
        self.target_x = screen_width - self.width - self.margin
        self.target_y = screen_height - self.height - self.margin
        
        # Animation
        self.current_x = screen_width  # Commence hors écran
        self.current_y = self.target_y
        self.animation_speed = 8
        
        # Timing
        self.display_duration = 3000  # 3 secondes en millisecondes
        self.created_time = pygame.time.get_ticks()
        self.fade_start_time = self.created_time + self.display_duration - 500  # Fade 500ms avant la fin
        
        # État
        self.is_visible = True
        self.alpha = 255
        
        # Polices
        self.title_font = pygame.font.SysFont(None, 28)
        self.desc_font = pygame.font.SysFont(None, 20)
        
        # Couleurs
        self.bg_color = (30, 50, 70)
        self.border_color = (255, 215, 0)  # Or
        self.title_color = (255, 255, 255)
        self.desc_color = (200, 200, 200)
        self.success_color = (50, 255, 50)
    
    def update(self, dt):
        """Met à jour l'animation et l'état de la notification."""
        current_time = pygame.time.get_ticks()
        
        # Animation d'entrée
        if self.current_x > self.target_x:
            self.current_x -= self.animation_speed
            if self.current_x < self.target_x:
                self.current_x = self.target_x
        
        # Gestion de l'alpha pour le fade out
        if current_time > self.fade_start_time:
            fade_progress = (current_time - self.fade_start_time) / 500  # 500ms de fade
            self.alpha = max(0, int(255 * (1 - fade_progress)))
        
        # Vérifier si la notification doit disparaître
        if current_time > self.created_time + self.display_duration:
            self.is_visible = False
    
    def draw_star(self, surface, x, y, size, filled=True):
        """Dessine une étoile à 5 branches."""
        color = (255, 215, 0) if filled else (80, 80, 80)  # Or ou gris
        
        # Points pour une étoile à 5 branches
        points = []
        for i in range(10):
            angle = i * math.pi / 5 - math.pi / 2
            if i % 2 == 0:
                # Points extérieurs
                radius = size
            else:
                # Points intérieurs
                radius = size * 0.4
            
            px = x + radius * math.cos(angle)
            py = y + radius * math.sin(angle)
            points.append((px, py))
        
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, self.border_color, points, 2)
    
    def draw(self, screen):
        """Dessine la notification."""
        if not self.is_visible or self.alpha <= 0:
            return
        
        # Créer une surface avec alpha pour le fade
        notification_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Fond avec gradient
        for i in range(self.height):
            ratio = i / self.height
            r = int(self.bg_color[0] * (1.2 - ratio * 0.4))
            g = int(self.bg_color[1] * (1.2 - ratio * 0.4))
            b = int(self.bg_color[2] * (1.2 - ratio * 0.4))
            color_with_alpha = (r, g, b, self.alpha)
            pygame.draw.rect(notification_surface, color_with_alpha, (0, i, self.width, 1))
        
        # Contour doré
        border_color_alpha = (*self.border_color, self.alpha)
        pygame.draw.rect(notification_surface, border_color_alpha, (0, 0, self.width, self.height), 3, border_radius=10)
        
        # Icône étoile
        star_x = 25
        star_y = self.height // 2
        star_size = 15
        
        # Créer une surface temporaire pour l'étoile avec alpha
        star_surface = pygame.Surface((star_size * 2 + 10, star_size * 2 + 10), pygame.SRCALPHA)
        self.draw_star(star_surface, star_size + 5, star_size + 5, star_size, filled=True)
        star_surface.set_alpha(self.alpha)
        notification_surface.blit(star_surface, (star_x - star_size - 5, star_y - star_size - 5))
        
        # Texte \"SUCCÈS DÉBLOQUÉ\"
        success_text = "SUCCÈS DÉBLOQUÉ !"
        success_surface = self.desc_font.render(success_text, True, (*self.success_color, self.alpha))
        success_rect = success_surface.get_rect(topleft=(star_x + star_size + 15, 10))
        success_surface.set_alpha(self.alpha)
        notification_surface.blit(success_surface, success_rect)
        
        # Nom du succès
        title_surface = self.title_font.render(self.achievement['name'], True, (*self.title_color, self.alpha))
        title_rect = title_surface.get_rect(topleft=(star_x + star_size + 15, 30))
        title_surface.set_alpha(self.alpha)
        notification_surface.blit(title_surface, title_rect)
        
        # Description (tronquée si trop longue)
        description = self.achievement['description']
        if len(description) > 35:
            description = description[:32] + "..."
        
        desc_surface = self.desc_font.render(description, True, (*self.desc_color, self.alpha))
        desc_rect = desc_surface.get_rect(topleft=(star_x + star_size + 15, 55))
        desc_surface.set_alpha(self.alpha)
        notification_surface.blit(desc_surface, desc_rect)
        
        # Dessiner la notification sur l'écran
        notification_surface.set_alpha(self.alpha)
        screen.blit(notification_surface, (int(self.current_x), int(self.current_y)))

class AchievementNotificationManager:
    """Gestionnaire des notifications de succès."""
    
    def __init__(self, screen):
        self.screen = screen
        self.WIDTH, self.HEIGHT = screen.get_size()
        self.active_notifications = []
        self.max_notifications = 3  # Maximum de notifications simultanées
        
    def add_notification(self, achievement):
        """Ajoute une nouvelle notification."""
        # Limiter le nombre de notifications simultanées
        if len(self.active_notifications) >= self.max_notifications:
            # Supprimer la plus ancienne
            self.active_notifications.pop(0)
        
        # Calculer la position Y en tenant compte des notifications existantes
        notification_height = 100
        margin = 20
        spacing = 10
        
        y_offset = 0
        for i, notification in enumerate(self.active_notifications):
            y_offset = (notification_height + spacing) * (i + 1)
        
        notification = AchievementNotification(achievement, self.WIDTH, self.HEIGHT)
        # Ajuster la position Y pour éviter les superpositions
        notification.target_y -= y_offset
        notification.current_y = notification.target_y
        
        self.active_notifications.append(notification)
    
    def update(self, dt):
        """Met à jour toutes les notifications actives."""
        # Mettre à jour les notifications existantes
        for notification in self.active_notifications[:]:
            notification.update(dt)
            if not notification.is_visible:
                self.active_notifications.remove(notification)
        
        # Réorganiser les positions des notifications restantes
        notification_height = 100
        spacing = 10
        base_y = self.HEIGHT - notification_height - 20
        
        for i, notification in enumerate(self.active_notifications):
            target_y = base_y - (notification_height + spacing) * i
            # Animation douce vers la nouvelle position
            if notification.target_y != target_y:
                notification.target_y = target_y
                if abs(notification.current_y - target_y) > 2:
                    notification.current_y += (target_y - notification.current_y) * 0.1
                else:
                    notification.current_y = target_y
    
    def draw(self):
        """Dessine toutes les notifications actives."""
        for notification in self.active_notifications:
            notification.draw(self.screen)
    
    def clear_all(self):
        """Supprime toutes les notifications actives."""
        self.active_notifications.clear()