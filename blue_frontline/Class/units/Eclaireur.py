from __future__ import annotations

from typing import List, Optional, Tuple

import pygame
from Class.Combat import CombatSystem
from Class.units.IA.IA_Eclaireur import ScoutAI
from Class.units.Unit import Unit
from Global import UNIT_CONFIGS


class Eclaireur(Unit):
    """
    Classe unifiée pour les unités Éclaireur (Rouge et Vert).

    Rôle gameplay :
        - Bateau rapide de reco.
        - Révèle les zones quantiques cachées en naviguant dessus.
        - Ne tire pas.

    IA :
        - self.ai = ScoutAI(...)
        - GameUpdater appelle self.ai.ia_tick(dt) si présent.

    Affichage :
        - L'éclaireur peut dessiner sa portée (draw_range) comme les autres unités.
    """

    def __init__(self, game: "Game", team: str, is_ia:bool = True) -> None:
        """
        Args:
            game (Game): instance du jeu.
            team (str): "red" ou "green".
        """
        # IMPORTANT :
        # On laisse Unit faire tout le boulot d'initialisation :
        # - position spawn aléatoire dans la zone de la base
        # - sprite / rect
        # - vitesses, états, etc.
        super().__init__(game, team=team, unit_type="eclaireur")

        # Récupère les stats depuis la config globale
        config = UNIT_CONFIGS["eclaireur"]

        # Coût en pièces
        self.cost: int = config["cost"]

        # Vitesse
        self.max_speed: float = config["max_speed"]
        self.reducte_speed: float = self.max_speed // 2
        self.speed: float = self.max_speed  # vitesse actuelle (Unit.move_to() utilise self.speed)

        # Santé
        self.max_health: int = config["max_health"]
        self.current_health: int = self.max_health

        # Tir / combat (éclaireur ne tire pas)
        self.range: int = 0          # pas de portée d'attaque
        self.damage: int = 0
        self.fire_rate: float = 0.0  # pas de cadence de tir

        # Métadonnées type/unité (utile pour HUD / récompenses à la mort)
        self.unit_type: str = config["unit_type"]          # "eclaireur"
        self.unit_name: str = f"Éclaireur {team.capitalize()}"

        # Couleur de zone (transparente) pour l'affichage de portée
        # Global.UNIT_CONFIGS["eclaireur"]["range_color"]["red"/"green"]
        self.range_color: Tuple[int, int, int, int] = config["range_color"][team]

        # États runtime
        self.is_moving: bool = False
        self.target_position: Optional[Tuple[float, float]] = None

        # sélection HUD (GameUpdater met à jour self.is_selected)
        self.is_selected: bool = False

        # === CRÉATION DU CONTROLEUR IA ===
        # On suppose que le Game a déjà construit la grille de navigation :
        #   game.build_nav_grid() -> game.nav_grid_adapter
        #
        # Et qu'il expose :
        #   - game.get_hidden_quantum_polygons() -> liste de polygones cachés
        #   - game.get_base_position(team) -> (x,y) base alliée
        #
        # ScoutAI respecte la convention d'équipe:
        #   ai.is_ia == True
        #   ai.ia_tick(dt) sera appelée dans GameUpdater
        #
        self.ai: ScoutAI = ScoutAI(
            unit=self,
            grid=game.nav_grid_adapter,
            get_hidden_quantum_polygons=game.get_hidden_quantum_polygons,
            get_base_pos=game.get_base_position,
            return_to_base_when_done=True,
            replan_interval=0.5,      # l'IA recalcule son plan régulièrement
            proximity_epsilon=8.0,    # distance considérée "waypoint atteint"
        )

    # ------------------------------------------------------------------
    # UPDATE PAR FRAME
    # ------------------------------------------------------------------
    def update(
        self,
        dt: float = 0.0,
        combat_system: Optional[CombatSystem] = None,
        screen: Optional[pygame.Surface] = None,
        camera_offset: Tuple[float, float] = (0.0, 0.0),
        all_units: Optional[List[Unit]] = None,
    ) -> None:
        """
        Mise à jour par frame.

        On délègue l'essentiel à Unit.update(), qui gère :
        - le déplacement réel (move / check_area),
        - la collision avec îles / eau peu profonde,
        - la révélation des zones quantiques,
        - le combat de base (même si ici il tire pas),
        - le rect.center.

        Et on rajoute juste l'affichage spécifique si besoin.
        """
        super().update(dt, combat_system, screen, camera_offset, all_units)

        # Pour l'éclaireur, on veut toujours afficher sa zone d'influence
        # (même s'il n'est pas sélectionné) ? ou seulement s'il est sélectionné ?
        #
        # -> Actuellement, Unit.draw_range() ne dessine que si self.is_selected.
        # L'éclaireur n'a pas de portée de tir donc ça ne sert pas à grand-chose
        # en combat. On n'en rajoute pas plus ici pour ne pas surcharger l'écran.
        #
        # Si tu veux l'afficher toujours, tu peux décommenter :
        #
        # if screen:
        #     self.draw_range(screen, camera_offset)

    # ------------------------------------------------------------------
    # OVERRIDES COMBAT / DEGATS
    # ------------------------------------------------------------------
    def take_damage(self, amount: float) -> None:
        """Inflige des dégâts à l'éclaireur."""
        if amount <= 0:
            return

        self.current_health -= amount
        if self.current_health <= 0:
            self.current_health = 0
            self.destroy()

    def destroy(self) -> None:
        """Destruction du bateau (PV <= 0)."""
        # Le jeu principal garde self.game.units comme liste d'unités actives.
        try:
            self.game.units.remove(self)
        except ValueError:
            pass

        # On marque l'unité comme morte pour éviter update() / IA_tick()
        self.is_alive = False
        self.kill()  # retire aussi du groupe pygame

    def can_fire(self) -> bool:
        """L'éclaireur ne tire pas."""
        return False

    def get_attack_target(self, units: List["Unit"]) -> None:
        """Pas d'attaque ciblée pour l'éclaireur -> toujours None."""
        return None


# ----------------------------------------------------------------------
# VARIANTES ROUGE / VERTE POUR RESTER COMPATIBLE AVEC LE RESTE DU CODE
# (le EventHandler spawn encore en appelant EclaireurRouge(game) par ex.)
# ----------------------------------------------------------------------

class EclaireurRouge(Eclaireur):
    def __init__(self, game: "Game", is_ia: bool = True) -> None:
        super().__init__(game, team="red", is_ia=is_ia)


class EclaireurVert(Eclaireur):
    def __init__(self, game: "Game", is_ia: bool = True) -> None:
        super().__init__(game, team="green", is_ia=is_ia)
