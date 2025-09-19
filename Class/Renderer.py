import pygame, pyscroll, time, math

class Renderer:
    """Gestionnaire de rendu pour le jeu."""
    
    def __init__(self, game):
        """Initialise le gestionnaire de rendu avec une référence au jeu."""
        self.game = game
        self.map_needs_refresh = False
                
    def refresh_map(self):
        """Force la reconstruction de la surface de map avec les calques actuels."""
        
        # Recréer le map_data avec les calques actuellement visibles
        map_data = pyscroll.data.TiledMapData(self.game.tmx_data)
        
        # Recréer le BufferedRenderer
        map_layer = pyscroll.BufferedRenderer(map_data, self.game.screen.get_size())
        
        # Conserver le niveau de zoom actuel
        if hasattr(self.game.camera, 'zoom_level'):
            map_layer.zoom = self.game.camera.zoom_level
        
        # Remplacer l'ancien renderer dans le groupe
        if hasattr(self.game.group, 'map_layer'):
            self.game.group.map_layer = map_layer
        elif hasattr(self.game, 'map_layer'):
            self.game.map_layer = map_layer
        
        # Reconstruire le PyscrollGroup avec le nouveau map_layer
        # Sauvegarder les sprites existants
        existing_sprites = list(self.game.group.sprites())

        # Créer un nouveau PyscrollGroup
        self.game.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=1)

        # Remettre tous les sprites
        for sprite in existing_sprites:
            if not hasattr(sprite, '__dict__') or 'map_layer' not in str(type(sprite)):
                self.game.group.add(sprite)

    
    def render(self):
        """Effectue tout le rendu du jeu."""
        # Vérifier si la map doit être reconstruite
        if self.map_needs_refresh:
            self.refresh_map()
            self.map_needs_refresh = False

        # Rendu de la map avec zoom
        self._render_map()
        
        # HUD
        if self.game.hud.show:
            self.game.hud.draw(self.game.screen)
        
        # Projectiles
        self._render_projectiles()
        
        # Barres de vie des unités
        self._render_unit_health_bars()
        
        # Unité sélectionnée
        self._render_selected_unit_highlight()
        
        # Popup d'unités
        self.game.draw_unit_popup()
        
    def _render_map(self):
        """Rend la map avec gestion du zoom et reconstruction si nécessaire."""
        
        # Vérifier si la map doit être reconstruite
        if self.map_needs_refresh:
            self.refresh_map()
            self.map_needs_refresh = False

        if self.game.camera.zoom_level != 1.0:
            # Rendu avec zoom
            temp_surface = pygame.Surface((
                int(self.game.screen.get_width() / self.game.camera.zoom_level), 
                int(self.game.screen.get_height() / self.game.camera.zoom_level)
            ))
            self.game.group.draw(temp_surface)
            scaled_surface = pygame.transform.scale(temp_surface, self.game.screen.get_size())
            self.game.screen.blit(scaled_surface, (0, 0))
        else:
            # Rendu normal sans zoom
            self.game.group.draw(self.game.screen)

    def _render_projectiles(self):
        """Rend tous les projectiles."""
        camera_offset = self.game.camera.get_offset(self.game.screen.get_size())
        
        for projectile in self.game.combat_system.projectiles:
            projectile_screen_x = (projectile.position[0] - camera_offset[0]) * self.game.camera.zoom_level
            projectile_screen_y = (projectile.position[1] - camera_offset[1]) * self.game.camera.zoom_level
            
            # Adapter la taille du projectile au zoom
            scaled_image = pygame.transform.scale(
                projectile.image, 
                (int(projectile.image.get_width() * self.game.camera.zoom_level),
                 int(projectile.image.get_height() * self.game.camera.zoom_level))
            )
            projectile_rect = scaled_image.get_rect(center=(projectile_screen_x, projectile_screen_y))
            self.game.screen.blit(scaled_image, projectile_rect)
    
    def _render_unit_health_bars(self):
        """Rend les barres de vie des unités."""
        camera_offset = self.game.camera.get_offset(self.game.screen.get_size())
        for unit in self.game.units:
            unit.draw_health_bar(self.game.screen, camera_offset)
    
    def _render_selected_unit_highlight(self):
        """Rend la surbrillance de l'unité sélectionnée."""
        if not (self.game.selected_unit and self.game.selected_unit.is_alive):
            return
        
        camera_offset = self.game.camera.get_offset(self.game.screen.get_size())
        unit_screen_x = (self.game.selected_unit.position[0] - camera_offset[0]) * self.game.camera.zoom_level
        unit_screen_y = (self.game.selected_unit.position[1] - camera_offset[1]) * self.game.camera.zoom_level
        
        # Vérifier que l'unité est visible à l'écran
        if (-50 <= unit_screen_x <= self.game.screen.get_width() + 50 and 
            -50 <= unit_screen_y <= self.game.screen.get_height() + 50):
            
            # Animation de pulsation
            pulse = abs(math.sin(time.time() * 3)) * 5 + 20
            pulse_scaled = pulse * self.game.camera.zoom_level
            
            # Cercles de sélection
            pygame.draw.circle(self.game.screen, (255, 255, 0), 
                             (int(unit_screen_x), int(unit_screen_y)), 
                             int(pulse_scaled + 8 * self.game.camera.zoom_level), 3)
            pygame.draw.circle(self.game.screen, (255, 255, 0), 
                             (int(unit_screen_x), int(unit_screen_y)), 
                             int(18 * self.game.camera.zoom_level), 2)
            pygame.draw.circle(self.game.screen, (255, 255, 0), 
                             (int(unit_screen_x), int(unit_screen_y)), 
                             int(3 * self.game.camera.zoom_level), 0)