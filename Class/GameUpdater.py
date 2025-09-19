import pyscroll

class GameUpdater:
    """Gestionnaire de mise à jour des systèmes de jeu."""
    
    def __init__(self, game):
        """Initialise le gestionnaire de mise à jour avec une référence au jeu."""
        self.game = game
    
    def update_systems(self, dt):
        """Met à jour tous les systèmes du jeu."""
        # Mettre à jour la caméra
        self.game.camera.update()
        
        # Mettre à jour le renderer si le zoom a changé
        self._update_renderer_for_zoom()
        
        # Mettre à jour les unités
        camera_offset = self.game.camera.get_offset(self.game.screen.get_size())
        for unit in self.game.units:
            unit.update(dt, self.game.combat_system, self.game.screen, camera_offset)
        
        # Mettre à jour le système de combat
        self.game.combat_system.update(dt)
        
        # Mettre à jour les groupes
        self.game.group.update()
        self.game.group.center(self.game.camera.rect.center)
    
    def _update_renderer_for_zoom(self):
        """Met à jour le renderer pyscroll pour le nouveau niveau de zoom."""
        if self.game.camera.zoom_level != self.game.last_zoom_level:
            # Calculer la nouvelle taille effective de rendu
            effective_width = int(self.game.screen.get_width() / self.game.camera.zoom_level)
            effective_height = int(self.game.screen.get_height() / self.game.camera.zoom_level)
            
            # Récréer le renderer avec la nouvelle taille
            map_data = pyscroll.data.TiledMapData(self.game.tmx_data)
            self.game.map_layer = pyscroll.orthographic.BufferedRenderer(map_data, (effective_width, effective_height))
            
            # Recréer le groupe avec le nouveau map_layer
            self.game.group = pyscroll.PyscrollGroup(map_layer=self.game.map_layer, default_layer=3)
            self.game.group.add(self.game.camera)
            
            # Ajouter tous les sprites existants au nouveau groupe
            for unit in self.game.units:
                if unit.is_alive:
                    self.game.group.add(unit)
            
            # Ajouter l'île quantique si elle existe
            if hasattr(self.game, 'island_sprite'):
                self.game.group.add(self.game.island_sprite)
            
            self.game.last_zoom_level = self.game.camera.zoom_level