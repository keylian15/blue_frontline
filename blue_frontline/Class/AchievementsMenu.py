import pygame, math
from Global import *
from Class.AchievementsSystem import AchievementsSystem

class AchievementsMenu:
    """Menu d'affichage des succès du jeu."""
    
    def __init__(self, screen):
        """Initialise le menu des succès.

        Args:
            screen (pygame.Surface): Surface de dessin du menu.
        """
        self.screen = screen
        self.WIDTH, self.HEIGHT = screen.get_size()
        
        # Polices
        self.title_font = pygame.font.SysFont(None, 60)
        self.category_font = pygame.font.SysFont(None, 40)
        self.achievement_font = pygame.font.SysFont(None, 28)
        self.description_font = pygame.font.SysFont(None, 22)
        self.progress_font = pygame.font.SysFont(None, 24)
        
        # Couleurs
        self.BG_COLOR = (20, 30, 50)
        self.PANEL_COLOR = (40, 50, 70)
        self.COMPLETED_COLOR = (50, 150, 50)
        self.LOCKED_COLOR = (100, 100, 100)
        self.STAR_FILLED_COLOR = (255, 215, 0)  # Or
        self.STAR_EMPTY_COLOR = (80, 80, 80)  # Gris foncé
        
        # Dimensions
        self.MARGIN = 40
        self.ACHIEVEMENT_HEIGHT = 80
        self.ACHIEVEMENT_SPACING = 10
        self.STAR_SIZE = 30
        
        # Bouton retour
        self.back_button = {
            'text': 'Retour',
            'rect': pygame.Rect(self.MARGIN, self.HEIGHT - 80, 150, 50)
        }
        
        # Bouton reset
        self.reset_button = {
            'text': 'Reset Succès',
            'rect': pygame.Rect(self.MARGIN + 170, self.HEIGHT - 80, 150, 50)
        }
        
        # Scroll
        self.scroll_y = 0
        self.scroll_speed = 30
        self.max_scroll = 0
        
        # Référence au système de succès
        self.achievements_system = None
    
    def set_achievements_system(self, achievements_system):
        """Définit le système de succès à utiliser.
        
        Args:
            achievements_system (AchievementsSystem): Le système de succès.
        """
        self.achievements_system = achievements_system
    
    def draw_star(self, surface, x, y, size, filled=False):
        """Dessine une étoile à 5 branches.
        
        Args:
            surface (pygame.Surface): La surface sur laquelle dessiner.
            x (int): La position x du centre de l'étoile.
            y (int): La position y du centre de l'étoile.
            size (int): La taille de l'étoile.
            filled (bool, optional): Si True, l'étoile est pleine, sinon elle est vide. Par defaut à False .
        """
        color = self.STAR_FILLED_COLOR if filled else self.STAR_EMPTY_COLOR
        
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
        
        if filled:
            pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, WHITE if filled else color, points, 2)
    
    def draw_gradient_button(self, surface, rect, hovered=False, completed=False):
        """Dessine un bouton avec dégradé.
        
        Args:
            surface (pygame.Surface): La surface sur laquelle dessiner.
            rect (pygame.Rect): Le rectangle du bouton.
            hovered (bool, optional): Si True, le bouton est survolé. Par defaut à False .
            completed (bool, optional): Si True, le succès est débloqué. Par defaut à False .
        """
        if completed:
            color1 = (30, 80, 30) if not hovered else (40, 100, 40)
            color2 = (60, 120, 60) if not hovered else (80, 140, 80)
        else:
            color1 = OCEAN_BLUE if not hovered else LIGHT_BLUE
            color2 = LIGHT_BLUE if not hovered else OCEAN_BLUE
        
        # Créer le dégradé
        button_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        for i in range(rect.height):
            ratio = i / rect.height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            pygame.draw.rect(button_surf, (r, g, b), (0, i, rect.width, 1))
        
        # Masquer avec des coins arrondis
        mask = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, rect.width, rect.height), border_radius=10)
        button_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        
        surface.blit(button_surf, rect.topleft)
        
        # Contour
        border_color = (100, 255, 100) if completed else WHITE
        pygame.draw.rect(surface, border_color, rect, 3, border_radius=10)
    
    def draw_achievement_item(self, surface, achievement, x, y, width):
        """Dessine un élément de succès.
        
        Args:
            surface (pygame.Surface): La surface sur laquelle dessiner.
            achievement (dict): Le succès à dessiner.
            x (int): La position x de l'élément.
            y (int): La position y de l'élément.
            width (int): La largeur de l'élément.
        """
        # Rectangle principal
        rect = pygame.Rect(x, y, width, self.ACHIEVEMENT_HEIGHT)
        completed = achievement['unlocked']
        
        # Dessiner le fond avec dégradé
        self.draw_gradient_button(surface, rect, completed=completed)
        
        # Nom du succès
        name_color = WHITE if completed else (200, 200, 200)
        name_surface = self.achievement_font.render(achievement['name'], True, name_color)
        surface.blit(name_surface, (x + 15, y + 10))
        
        # Description - cachée ou visible selon le statut
        if completed:
            # Succès débloqué : afficher la vraie description
            description_text = achievement['description']
            desc_color = (220, 220, 220)
        else:
            # Succès verrouillé : afficher la description mystère
            description_text = achievement.get('hidden_description', '???')
            desc_color = (120, 120, 120)
        
        desc_surface = self.description_font.render(description_text, True, desc_color)
        surface.blit(desc_surface, (x + 15, y + 35))
        
        # Étoile à droite
        star_x = x + width - self.STAR_SIZE - 15
        star_y = y + self.ACHIEVEMENT_HEIGHT // 2
        self.draw_star(surface, star_x, star_y, self.STAR_SIZE // 2, filled=completed)
    
    def draw_category_section(self, surface, category_name, achievements, start_y):
        """Dessine une section de catégorie avec ses succès.
        
        Args:
            surface (pygame.Surface): La surface sur laquelle dessiner.
            category_name (str): Le nom de la catégorie.
            achievements (list): La liste des succès de la catégorie.
            start_y (int): La position y de départ de la section.
        
        Returns:
            int: La position y de fin de la section.
        """
        current_y = start_y
        
        # Titre de la catégorie
        category_surface = self.category_font.render(category_name, True, LIGHT_BLUE)
        surface.blit(category_surface, (self.MARGIN, current_y))
        current_y += 50
        
        # Succès de cette catégorie
        achievement_width = self.WIDTH - 2 * self.MARGIN
        for achievement in achievements:
            self.draw_achievement_item(surface, achievement, self.MARGIN, current_y, achievement_width)
            current_y += self.ACHIEVEMENT_HEIGHT + self.ACHIEVEMENT_SPACING
        
        current_y += 20  # Espacement entre catégories
        return current_y
    
    def draw(self):
        """Dessine le menu des succès."""
        # Fond
        self.screen.fill(self.BG_COLOR)
        
        # Calculer la hauteur nécessaire pour le contenu
        estimated_height = self.HEIGHT
        if self.achievements_system:
            categories = self.achievements_system.get_achievements_by_category()
            category_count = len([cat for cat in ['Construction & Économie', 'Combat', 'Stratégie', 'Exploration', 'Succès Spéciaux'] if cat in categories])
            achievement_count = len(self.achievements_system.achievements)
            estimated_height = max(self.HEIGHT, 300 + category_count * 60 + achievement_count * (self.ACHIEVEMENT_HEIGHT + self.ACHIEVEMENT_SPACING))
        
        # Créer une surface pour le contenu scrollable
        content_surface = pygame.Surface((self.WIDTH, estimated_height), pygame.SRCALPHA)
        
        current_y = 50
        
        # Titre principal
        title_surface = self.title_font.render("SUCCÈS", True, WHITE)
        title_rect = title_surface.get_rect(midtop=(self.WIDTH // 2, current_y))
        content_surface.blit(title_surface, title_rect)
        current_y += 80
        
        # Pourcentage de progression
        if self.achievements_system:
            progress = self.achievements_system.get_completion_percentage()
            completed_count = len(self.achievements_system.unlocked_achievements)
            total_count = len(self.achievements_system.achievements)
            
            progress_text = f"Progression: {completed_count}/{total_count} ({progress:.1f}%)"
            progress_surface = self.progress_font.render(progress_text, True, LIGHT_BLUE)
            progress_rect = progress_surface.get_rect(midtop=(self.WIDTH // 2, current_y))
            content_surface.blit(progress_surface, progress_rect)
            current_y += 60
            
            # Barre de progression
            bar_width = 400
            bar_height = 20
            bar_x = (self.WIDTH - bar_width) // 2
            bar_y = current_y
            
            # Fond de la barre
            pygame.draw.rect(content_surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height), border_radius=10)
            
            # Progression
            progress_width = int(bar_width * progress / 100)
            if progress_width > 0:
                pygame.draw.rect(content_surface, LIGHT_BLUE, (bar_x, bar_y, progress_width, bar_height), border_radius=10)
            
            # Contour
            pygame.draw.rect(content_surface, WHITE, (bar_x, bar_y, bar_width, bar_height), 2, border_radius=10)
            current_y += 60
            
            # Dessiner les catégories et succès
            categories = self.achievements_system.get_achievements_by_category()
            for category_name in ['Construction & Économie', 'Combat', 'Stratégie', 'Exploration', 'Succès Spéciaux']:
                if category_name in categories:
                    current_y = self.draw_category_section(content_surface, category_name, categories[category_name], current_y)
        else:
            # Message si pas de système de succès
            no_data_surface = self.achievement_font.render("Système de succès non disponible", True, WHITE)
            no_data_rect = no_data_surface.get_rect(midtop=(self.WIDTH // 2, current_y))
            content_surface.blit(no_data_surface, no_data_rect)
            current_y += 50
        
        # Mettre à jour le scroll maximum
        self.max_scroll = max(0, current_y - self.HEIGHT + 100)
        
        # Appliquer le scroll et dessiner
        # Zone source à copier depuis content_surface (décalée par le scroll)
        source_rect = pygame.Rect(0, self.scroll_y, self.WIDTH, self.HEIGHT - 100)
        # Position de destination sur l'écran
        dest_pos = (0, 0)
        self.screen.blit(content_surface, dest_pos, source_rect)
        
        # Boutons (toujours visibles)
        self.draw_back_button()
        self.draw_reset_button()
    
    def draw_back_button(self):
        """Dessine le bouton retour."""
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.back_button['rect'].collidepoint(mouse_pos)
        
        self.draw_gradient_button(self.screen, self.back_button['rect'], hovered=hovered)
        
        # Texte du bouton
        text_surface = self.achievement_font.render(self.back_button['text'], True, WHITE)
        text_rect = text_surface.get_rect(center=self.back_button['rect'].center)
        self.screen.blit(text_surface, text_rect)
    
    def draw_reset_button(self):
        """Dessine le bouton reset."""
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.reset_button['rect'].collidepoint(mouse_pos)
        
        # Couleur rouge pour le bouton dangereux
        color = (150, 50, 50) if not hovered else (200, 70, 70)
        pygame.draw.rect(self.screen, color, self.reset_button['rect'], border_radius=10)
        pygame.draw.rect(self.screen, WHITE, self.reset_button['rect'], 2, border_radius=10)
        
        # Texte du bouton
        text_surface = self.achievement_font.render(self.reset_button['text'], True, WHITE)
        text_rect = text_surface.get_rect(center=self.reset_button['rect'].center)
        self.screen.blit(text_surface, text_rect)
    
    def handle_scroll(self, scroll_direction):
        """Gère le défilement du menu.
        
        Args:
            scroll_direction (int): La direction du scroll (1 pour vers le bas, -1 pour vers le haut).
        """
        self.scroll_y -= scroll_direction * self.scroll_speed
        self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))
    
    def handle_click(self, mouse_pos):
        """Gère les clics dans le menu.
        
        Args:
            mouse_pos (tuple[int, int]): La position de la souris.
        
        Returns:
            str: 'back' si le bouton retour est cliqué, 'reset' si le bouton reset est cliqué, None sinon.
        """
        if self.back_button['rect'].collidepoint(mouse_pos):
            return 'back'
        elif self.reset_button['rect'].collidepoint(mouse_pos):
            return 'reset'
        return None
    
    def run(self):
        """Boucle principale du menu des succès."""
        running = True
        clock = pygame.time.Clock()
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return True
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Clic gauche
                        result = self.handle_click(pygame.mouse.get_pos())
                        if result == 'back':
                            return True
                        elif result == 'reset':
                            # Demander confirmation avant de reset
                            if self.achievements_system:
                                self.achievements_system.reset_all_achievements()
                    elif event.button == 4:  # Molette haut
                        self.handle_scroll(1)
                    elif event.button == 5:  # Molette bas
                        self.handle_scroll(-1)
            
            self.draw()
            pygame.display.flip()
            clock.tick(60)
        
        return True