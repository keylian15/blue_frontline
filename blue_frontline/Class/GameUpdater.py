import pyscroll

class GameUpdater:
    """Gestionnaire de mise à jour des systèmes de jeu."""
    
    def __init__(self, game: "Game"):
        """Initialise le gestionnaire de mise à jour avec une référence au jeu.

        Args:
            game (Game): Référence au jeu.
        """

        self.game = game
    
    def update_systems(self, dt: float, game: "Game"):
        """Met à jour tous les systèmes du jeu grâce à la partie en cours.

        Args:
            dt (float): La différence de temps entre chaque frame.
            game (Game): Référence au jeu.
        """

        # Met à jour la game (références internes: listes d'unités, plateformes, etc.)
        self.game.refresh_all_references(game)

        # Mettre à jour la caméra (position, zoom, rect, etc.)
        self.game.camera.update()

        # === AUDIO ===
        # Mettre à jour le moteur sonore (spatialisation, ducking musique...)
        # On fait ça après la MAJ caméra pour avoir la bonne position d'écoute.
        try:
            if hasattr(self.game, "sound") and self.game.sound:
                self.game.sound.update()
        except Exception:
            # On évite de faire crasher la boucle de jeu si un son manque, etc.
            pass

        # Mettre à jour le renderer si le zoom a changé
        self.update_renderer_for_zoom()

        # S'assurer que toutes les unités sont dans le système de combat
        self.sync_units_with_combat_system()

        # --- Gestion dynamique de la marée ---
        # Si la marée a changé, on recalcule les collisions et la grille de nav IA
        if hasattr(self.game.hud, "timer") and self.game.hud.timer.maree_changed:
            # Met à jour les zones d'obstacles / zones navigables selon la marée
            self.game.setObstacles()

            # Reconstruit la grille de navigation A* pour l'IA (walkable + coûts)
            # et met à jour self.game.nav_grid_adapter
            self.game.build_nav_grid()

        # Mettre à jour les unités
        camera_offset = self.game.camera.get_offset(self.game.screen.get_size())

        for unit in self.game.units:
            # Mettre à jour l'unité (physique, tir, collision, etc.)
            unit.update(
                dt,
                self.game.combat_system,
                self.game.screen,
                camera_offset,
                self.game.units,
            )

            # Marquer l'unité comme sélectionnée si c'est l'unité active
            if hasattr(unit, "is_selected"):
                unit.is_selected = (unit == self.game.selected_unit)

            # === IA SCOUT / IA BATEAU ===
            # Convention d'équipe:
            # - l'objet IA est dans unit.ai
            # - il expose is_ia: bool = True
            # - il expose ia_tick(dt)
            if hasattr(unit, "ai") and unit.ai is not None:
                ai_controller = unit.ai
                if getattr(ai_controller, "is_ia", False):
                    try:
                        ai_controller.ia_tick(dt)
                    except Exception as e:
                        # On log pour debug mais on ne stoppe pas le jeu
                        # (évite qu'une erreur IA fasse planter toute la frame)
                        import logging
                        logging.getLogger("EclaireurAI").error(
                            "Erreur ia_tick sur %s : %s", unit, e
                        )

        # Mettre à jour le système de combat (détection de portée, tirs, etc.)
        if hasattr(self.game, "combat_system"):
            self.game.combat_system.update(dt)

        # Mettre à jour les groupes (pour le rendu groupé sur la minimap/affichage)
        self.game.group.update()
        self.game.group.center(self.game.camera.rect.center)

    def sync_units_with_combat_system(self):
        """Synchronise les unités avec le système de combat."""
        
        if not hasattr(self.game, 'combat_system'):
            return
            
        # Ajouter toutes les unités vivantes au système de combat si elles n'y sont pas
        for unit in self.game.units:
            if unit.is_alive and unit not in self.game.combat_system.units:
                self.game.combat_system.add_unit(unit)
    
    def update_renderer_for_zoom(self):
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
            
            if hasattr(self.game, 'camera'):
                self.game.group.add(self.game.camera)
            
            # Ajouter toutes les unités existantes au nouveau groupe
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
            self.game.last_zoom_level = self.game.camera.zoom_level