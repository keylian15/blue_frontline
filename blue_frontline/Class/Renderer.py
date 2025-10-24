import pygame, pyscroll, time, math


from Global import get_pygame_key
import Global

class Renderer:
    """Gestionnaire de rendu pour le jeu."""
    
    def __init__(self, game: "Game"):
        """Initialise le gestionnaire de rendu avec une référence au jeu.

        Args:
            game (Game): Référence au jeu.
        """
        
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
        
        # Créer un nouveau PyscrollGroup avec le bon layer par défaut
        self.game.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=3)
        
        if hasattr(self.game, 'camera'):
            self.game.group.add(self.game.camera)
        
        # Ajouter toutes les unités vivantes au groupe
        if hasattr(self.game, 'units') and self.game.units:
            for unit in self.game.units:
                if unit.is_alive:
                    # S'assurer que l'unité n'est pas déjà dans le groupe
                    if unit not in self.game.group.sprites():
                        self.game.group.add(unit)
                    
        # Remettre les îles quantiques si en marée haute
        if self.game.hud.timer.maree_haute:
            self.restore_quantum_islands()
        
        # Marquer comme terminé
        self.map_needs_refresh = False
        
        # Actualiser les références
        self.game.refresh_all_references(self.game)

    def restore_quantum_islands(self):
        """Réstaure les iles quantiques."""
        if hasattr(self.game, 'quantum_islands'):
            for island in self.game.quantum_islands:
                if island not in self.game.group.sprites():
                    self.game.group.add(island)

    def render(self):
        """Effectue tout le rendu du jeu."""

        # Rendu de la map avec zoom
        self.render_map()
        
        # HUD
        if self.game.hud.show:
            self.game.hud.draw(self.game.screen)
        
        # Projectiles
        self.render_projectiles()
        
        # Barres de vie des unités
        self.render_unit_health_bars()
        
        # Unité sélectionnée
        self.render_selected_unit_highlight()
        
        # Notifications de succès
        if hasattr(self.game, 'notification_manager'):
            self.game.notification_manager.draw()
        
    def render_map(self):
        """Rend la map avec gestion du zoom et reconstruction si nécessaire."""
        
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

    def render_projectiles(self):
        """Rend tous les projectiles."""
        
        if hasattr(self.game, 'combat_system'):
            camera_offset = self.game.camera.get_offset(self.game.screen.get_size())
            zoom = self.game.camera.zoom_level
            self.game.combat_system.draw(self.game.screen, camera_offset, zoom)
    
    def render_unit_health_bars(self):
        """Rend les barres de vie des unités."""
        
        camera_offset = self.game.camera.get_offset(self.game.screen.get_size())
        zoom = self.game.camera.zoom_level
        for unit in self.game.units:
            unit.draw_health_bar(self.game.screen, camera_offset, zoom)
    
    def render_selected_unit_highlight(self):
        """Rend la surbrillance de l'unité sélectionnée et son cercle de portée."""
        
        if not (self.game.selected_unit and self.game.selected_unit.is_alive):
            return
        
        # Ne pas afficher les cercles et la portée pour les plateformes
        if hasattr(self.game.selected_unit, 'is_platform') and self.game.selected_unit.is_platform:
            return
        
        camera_offset = self.game.camera.get_offset(self.game.screen.get_size())
        unit_screen_x = (self.game.selected_unit.position[0] - camera_offset[0]) * self.game.camera.zoom_level
        unit_screen_y = (self.game.selected_unit.position[1] - camera_offset[1]) * self.game.camera.zoom_level
        
        # Vérifier que l'unité est visible à l'écran
        if (-50 <= unit_screen_x <= self.game.screen.get_width() + 50 and 
            -50 <= unit_screen_y <= self.game.screen.get_height() + 50):
            
            # Cercle de portée rouge 
            range_radius = self.game.selected_unit.range * 32 * self.game.camera.zoom_level  # Portée en pixels avec zoom
            
            # Surface semi-transparente pour le cercle de portée
            range_surface = pygame.Surface((range_radius * 2, range_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(range_surface, (255, 0, 0, 30), (range_radius, range_radius), range_radius)
            self.game.screen.blit(range_surface, (unit_screen_x - range_radius, unit_screen_y - range_radius))
            
            # Contour rouge pour la portée
            pygame.draw.circle(self.game.screen, (255, 0, 0), 
                             (int(unit_screen_x), int(unit_screen_y)), 
                             int(range_radius), 2)
            
            # Animation de pulsation pour la sélection
            pulse = abs(math.sin(time.time() * 3)) * 5 + 20
            pulse_scaled = pulse * self.game.camera.zoom_level
            
            # Cercles de sélection jaunes
            pygame.draw.circle(self.game.screen, (255, 255, 0), 
                             (int(unit_screen_x), int(unit_screen_y)), 
                             int(pulse_scaled + 8 * self.game.camera.zoom_level), 3)
            pygame.draw.circle(self.game.screen, (255, 255, 0), 
                             (int(unit_screen_x), int(unit_screen_y)), 
                             int(18 * self.game.camera.zoom_level), 2)
            pygame.draw.circle(self.game.screen, (255, 255, 0), 
                             (int(unit_screen_x), int(unit_screen_y)), 
                             int(3 * self.game.camera.zoom_level), 0)
            
            # Affichage du message de tir si des ennemis sont dans la portée
            if hasattr(self.game.selected_unit, 'enemies_in_range') and self.game.selected_unit.enemies_in_range:
                font = pygame.font.Font(None, 32)
                controls_keys = Global.get_controls_keys()  # S'assurer que les contrôles sont chargés
                shoot_key = controls_keys.get("SHOOT", {}).get("key") # Touche pygame
                if shoot_key:
                    num_key = get_pygame_key(shoot_key)
                    key_name = pygame.key.name(num_key).upper()  
                else:
                    key_name = "T"  # Valeur par défaut
                
                message = f"Ennemis en vue: {len(self.game.selected_unit.enemies_in_range)} - Appuyez sur {key_name} pour tirer"
                text_surface = font.render(message, True, (255, 255, 255))
                
                # Position du texte au-dessus du cercle de portée
                text_x = int(unit_screen_x - text_surface.get_width() // 2)
                text_y = int(unit_screen_y - range_radius - 50)
                
                # Fond semi-transparent pour le texte
                text_bg = pygame.Surface((text_surface.get_width() + 20, text_surface.get_height() + 10), pygame.SRCALPHA)
                text_bg.fill((0, 0, 0, 180))
                self.game.screen.blit(text_bg, (text_x - 10, text_y - 5))
                self.game.screen.blit(text_surface, (text_x, text_y))