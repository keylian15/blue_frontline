import logging

import pyscroll

LOGGER_AI = logging.getLogger("EclaireurAI")


class GameUpdater:
    """Gestionnaire de mise à jour des systèmes de jeu."""
    
    def __init__(self, game: "Game"):
        """
        Args:
            game (Game): Référence au jeu.
        """
        self.game = game
    
    def update_systems(self, dt: float, game: "Game"):
        """
        Met à jour tous les systèmes du jeu grâce à la partie en cours.

        Args:
            dt (float): La différence de temps entre chaque frame.
            game (Game): Référence au jeu.
        """

        # 1. Sync les refs internes du Game (liste des unités, plateformes, etc.)
        self.game.refresh_all_references(game)

        # 2. Caméra
        self.game.camera.update()

        # 3. Audio (position listener dépend de la caméra donc après update caméra)
        try:
            if hasattr(self.game, "sound") and self.game.sound:
                self.game.sound.update()
        except Exception:
            # on évite qu'un bug son casse la frame
            pass

        # 4. Zoom / renderer si le niveau de zoom a changé
        self.update_renderer_for_zoom()

        # 5. Sync combat_system <-> unités (ajouter nouvelles unités vivantes)
        self.sync_units_with_combat_system()

        # 6. Marée : si elle a changé on doit :
        #    - mettre à jour les collisions
        #    - rebuild la nav_grid_adapter
        #    - recoller cette nouvelle grille dans les IA actives
        if hasattr(self.game.hud, "timer") and self.game.hud.timer.maree_changed:
            # Recalcule obstacles (zones navigables vs zones bloquées)
            self.game.setObstacles()

            # Reconstruit la grille de navigation A*
            self.game.build_nav_grid()

            # IMPORTANT :
            # on met à jour la grid que les IA utilisent,
            # sinon elles continueront à calculer avec l'ancienne carte
            if hasattr(self.game, "nav_grid_adapter"):
                for u in self.game.units:
                    if hasattr(u, "ai") and u.ai is not None:
                        try:
                            u.ai.grid = self.game.nav_grid_adapter
                            # si l'astar interne dépend de grid, on le regénère
                            if hasattr(u.ai, "astar"):
                                u.ai.astar = u.ai._make_astar_from_grid()
                        except Exception as e:
                            LOGGER_AI.warning(
                                "Impossible de réinjecter la nouvelle grille nav dans %s : %s",
                                u, e
                            )

        # 7. Mise à jour des unités + IA
        camera_offset = self.game.camera.get_offset(self.game.screen.get_size())

        for unit in self.game.units:
            # --- UPDATE PHYSIQUE / VISUEL / COLLISIONS / ETC.
            unit.update(
                dt,
                self.game.combat_system,
                self.game.screen,
                camera_offset,
                self.game.units,
            )

            # Marque visuellement l'unité sélectionnée
            if hasattr(unit, "is_selected"):
                unit.is_selected = (unit == self.game.selected_unit)

            # --- IA ---
            # Convention du projet:
            # - unit.ai existe
            # - unit.ai.is_ia == True
            # - unit.ai.ia_tick(dt) doit être appelée CHAQUE frame
            if hasattr(unit, "ai") and unit.ai is not None:
                ai_controller = unit.ai
                if getattr(ai_controller, "is_ia", False):
                    try:
                        ai_controller.ia_tick(dt)
                    except Exception as e:
                        # on log mais on ne casse pas la boucle de jeu
                        try:
                            ux, uy = getattr(unit, "position", (None, None))
                        except Exception:
                            ux, uy = (None, None)

                        LOGGER_AI.error(
                            "Erreur ia_tick sur %s (pos=%s,%s) : %s",
                            unit, ux, uy, e
                        )

        # 8. Combat system (verrouillage / tir / dégâts / mort)
        if hasattr(self.game, "combat_system"):
            self.game.combat_system.update(dt)

        # 9. MAJ du groupe de rendu Pyscroll
        self.game.group.update()
        self.game.group.center(self.game.camera.rect.center)

    def sync_units_with_combat_system(self):
        """Synchronise les unités avec le système de combat."""
        if not hasattr(self.game, 'combat_system'):
            return
            
        # Ajouter toutes les unités vivantes au système de combat si elles n'y sont pas
        for unit in self.game.units:
            is_alive = getattr(unit, "is_alive", True)
            if is_alive and unit not in self.game.combat_system.units:
                self.game.combat_system.add_unit(unit)
    
    def update_renderer_for_zoom(self):
        """Met à jour le renderer pyscroll pour le nouveau niveau de zoom."""
        if self.game.camera.zoom_level != self.game.last_zoom_level:
            # Calculer la nouvelle taille effective de rendu
            effective_width = int(self.game.screen.get_width() / self.game.camera.zoom_level)
            effective_height = int(self.game.screen.get_height() / self.game.camera.zoom_level)
            
            # Recréer le renderer avec la nouvelle taille
            map_data = pyscroll.data.TiledMapData(self.game.tmx_data)
            self.game.map_layer = pyscroll.orthographic.BufferedRenderer(
                map_data,
                (effective_width, effective_height)
            )
            
            # Recréer le groupe avec le nouveau map_layer
            self.game.group = pyscroll.PyscrollGroup(
                map_layer=self.game.map_layer,
                default_layer=3
            )
            
            if hasattr(self.game, 'camera'):
                self.game.group.add(self.game.camera)
            
            # Ajouter toutes les unités existantes au nouveau groupe
            for unit in self.game.units:
                is_alive = getattr(unit, "is_alive", True)
                if is_alive:
                    self.game.group.add(unit)
            
            # Ajouter les îles quantiques visibles à marée haute
            if self.game.hud.timer.maree_haute:
                if hasattr(self.game, 'quantum_islands') and self.game.quantum_islands:
                    for island in self.game.quantum_islands:
                        if island not in self.game.group.sprites():
                            self.game.group.add(island)

            # On met à jour le cache du zoom
            self.game.last_zoom_level = self.game.camera.zoom_level
