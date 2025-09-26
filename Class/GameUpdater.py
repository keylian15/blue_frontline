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
        
        # S'assurer que toutes les unités sont dans le système de combat
        self._sync_units_with_combat_system()
        
        # Mettre à jour les unités
        camera_offset = self.game.camera.get_offset(self.game.screen.get_size())
        self.game.setObstacles()
        for unit in self.game.units:
            # Met a jour les obstacles 
            if type(unit).__name__ != "PlateformePetroliere" : 
                unit.updateObstacle(self.game.obstacles)
            # Mettre à jour l'unité avec toutes les informations nécessaires
            unit.update(dt, self.game.combat_system, self.game.screen, camera_offset, self.game.units)
            
            # Marquer l'unité comme sélectionnée si c'est l'unité active
            if hasattr(unit, 'is_selected'):
                unit.is_selected = (unit == self.game.selected_unit)
        
        # Mettre à jour le système de combat
        
        if hasattr(self.game, 'combat_system'):
            self.game.combat_system.update(dt)
        
        # Mettre à jour les projectiles
        if hasattr(self.game, 'update_bullets'):
            self.game.update_bullets(dt)
        
        # Mettre à jour les groupes
        self.game.group.update()
        self.game.group.center(self.game.camera.rect.center)

    def _sync_units_with_combat_system(self):
        """Synchronise les unités avec le système de combat."""
        if not hasattr(self.game, 'combat_system'):
            return
            
        # Ajouter toutes les unités vivantes au système de combat si elles n'y sont pas
        for unit in self.game.units:
            if unit.is_alive and unit not in self.game.combat_system.units:
                self.game.combat_system.add_unit(unit)
    
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
            
            # Ajouter les îles quantiques si elles existent
            if self.game.hud.timer.maree_haute:
                if hasattr(self.game, 'quantum_islands') and self.game.quantum_islands:
                    for island in self.game.quantum_islands:
                        if island not in self.game.group.sprites():
                            self.game.group.add(island)

            # Actualiser toutes les références des gestionnaires
            self.game.refresh_all_references()
            self.game.last_zoom_level = self.game.camera.zoom_level