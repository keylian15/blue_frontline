from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pyscroll
from src.units.IA.IA_Eclaireur import update_all_scout_ai

LOGGER_AI = logging.getLogger("EclaireurAI")

if TYPE_CHECKING:
    from src.core.Game import Game


class GameUpdater:
    """Gestionnaire de mise à jour des systèmes de jeu."""

    def __init__(self, game: Game):
        """
        Args:
            game (Game): Référence au jeu.
        """
        self.game = game

    def update_systems(self, dt: float):
        """
        Met à jour tous les systèmes du jeu grâce à la partie en cours.

        Args:
            dt (float): Delta time frame.
            game (Game): Référence au jeu.
        """
        # 1. Caméra
        self.game.camera.update()

        # 2. Audio (listener = caméra donc après update caméra)
        try:
            if hasattr(self.game, "sound") and self.game.sound:
                self.game.sound.update()
        except Exception:
            # on évite qu'un bug son casse la frame
            pass

        # 3. Zoom / renderer si le niveau de zoom a changé
        self.update_renderer_for_zoom()

        # 4. Sync combat_system <-> unités (ajouter nouvelles unités vivantes)
        self.sync_units_with_combat_system()

        # 5. Mettre à jour les unités (déplacement, tir, collisions, HUD...)
        camera_offset = self.game.camera.get_offset(self.game.screen.get_size())
        from src.config.settings_manager import get_gameplay_settings

        settings = get_gameplay_settings()

        for unit in self.game.units:
            # On vérifie si l'unité a l'attribut is_ia
            if hasattr(unit, "is_ia"):
                # Si l'unité est une IA, on met à jour si elle est ia
                # On récuperera la valeur depuis les paramètres de gameplay
                unit.is_ia = settings["AI_ACTIVATION"].get(unit.name, False)

            # Mettre à jour l'unité avec toutes les informations nécessaires
            unit.update(
                dt,
                self.game.combat_system,
                self.game.screen,
                camera_offset,
                self.game.units,
            )

            # Marquer l'unité comme sélectionnée si c'est l'unité active
            if hasattr(unit, "is_selected"):
                unit.is_selected = unit == self.game.selected_unit

        # 6. Mettre à jour l'IA des éclaireurs UNIQUEMENT
        # (gère aussi le rebuild nav_grid en cas de marée)
        update_all_scout_ai(self.game, dt)

        # 7. Combat system (verrouillage / tir / dégâts / mort)
        if hasattr(self.game, "combat_system"):
            self.game.combat_system.update(dt)

        # 8. MAJ du groupe de rendu Pyscroll
        self.game.group.update()
        self.game.group.center(self.game.camera.rect.center)

    def sync_units_with_combat_system(self):
        """Synchronise les unités avec le système de combat."""
        if not hasattr(self.game, "combat_system"):
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
            self.game.map_layer = pyscroll.orthographic.BufferedRenderer(map_data, (effective_width, effective_height))

            # Recréer le groupe avec le nouveau map_layer
            self.game.group = pyscroll.PyscrollGroup(map_layer=self.game.map_layer, default_layer=3)

            if hasattr(self.game, "camera"):
                self.game.group.add(self.game.camera)

            # Ajouter toutes les unités existantes au nouveau groupe
            for unit in self.game.units:
                is_alive = getattr(unit, "is_alive", True)
                if is_alive:
                    self.game.group.add(unit)

            # Ajouter les îles quantiques visibles à marée haute
            if self.game.hud.timer.maree_haute:
                if hasattr(self.game, "quantum_islands") and self.game.quantum_islands:
                    for island in self.game.quantum_islands:
                        if island not in self.game.group.sprites():
                            self.game.group.add(island)

            # On met à jour le cache du zoom
            self.game.last_zoom_level = self.game.camera.zoom_level
