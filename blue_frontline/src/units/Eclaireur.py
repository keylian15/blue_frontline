from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.Game import Game


import pygame
from src.config.units import UNIT_CONFIGS
from src.system.Combat import CombatSystem
from src.units.IA.IA_Eclaireur import ScoutAI
from src.units.Unit import Unit


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

    def __init__(self, game: Game, team: str, is_ia: bool = True) -> None:
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
        self.range: int = 0  # pas de portée d'attaque
        self.damage: int = 0
        self.fire_rate: float = 0.0  # pas de cadence de tir

        # Métadonnées type/unité (utile pour HUD / récompenses à la mort)
        self.unit_type: str = config["unit_type"]  # "eclaireur"
        self.unit_name: str = f"Éclaireur {team.capitalize()}"

        # Couleur de zone (transparente) pour l'affichage de portée
        self.range_color: tuple[int, int, int, int] = config["range_color"][team]

        # États runtime
        self.is_moving: bool = False
        self.target_position: tuple[float, float] | None = None

        # sélection HUD (GameUpdater met à jour self.is_selected)
        self.is_selected: bool = False

        # === GESTION DE L'IA ===
        # Conserver le même comportement que les autres unités :
        # - stocker `self.is_ia` à partir du paramètre `is_ia`
        # - n'instancier le contrôleur ScoutAI que si `is_ia` est True
        # - laisser le runtime (update) créer/détruire l'IA si le flag change
        self.is_ia = is_ia

        self.ai: ScoutAI | None = None
        if self.is_ia:
            self.init_ai(game)

    def init_ai(self, game: Game) -> None:
        """Initialise le contrôleur ScoutAI si possible."""
        try:
            self.ai = ScoutAI(
                unit=self,
                grid=game.nav_grid_adapter,
                get_hidden_quantum_polygons=game.get_hidden_quantum_polygons,
                get_base_pos=game.get_base_position,
                return_to_base_when_done=True,
                replan_interval=0.5,
                proximity_epsilon=8.0,
            )
        except Exception:
            # Ne jamais planter l'initialisation de l'unité si l'IA échoue
            self.ai = None

    # ------------------------------------------------------------------
    # UPDATE PAR FRAME
    # ------------------------------------------------------------------
    def update(
        self,
        dt: float = 0.0,
        combat_system: CombatSystem | None = None,
        screen: pygame.Surface | None = None,
        camera_offset: tuple[float, float] = (0.0, 0.0),
        all_units: list[Unit] | None = None,
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

        # Synchroniser l'existence du contrôleur IA avec le flag `is_ia`.
        # `GameUpdater` peut changer `unit.is_ia` à chaque frame selon `GAMEPLAY_SETTINGS`.
        if getattr(self, "is_ia", False):
            if self.ai is None:
                try:
                    self.init_ai(self.game)
                except Exception:
                    pass
        else:
            # Si l'IA est désactivée en runtime, libérer le contrôleur
            if self.ai is not None:
                try:
                    if hasattr(self.ai, "shutdown"):
                        try:
                            self.ai.shutdown()
                        except Exception:
                            pass
                finally:
                    self.ai = None

        # Pour l'éclaireur, on veut toujours afficher sa zone d'influence
        # (même s'il n'est pas sélectionné) ? ou seulement s'il est sélectionné ?
        #
        # -> Actuellement, Unit.draw_range() ne dessine que si self.is_selected.
        # L'éclaireur n'a pas de portée de tir donc ça ne sert pas à grand-chose
        # en combat. On n'en rajoute pas plus ici pour ne pas surcharger l'écran.
        #
        # Pour l'afficher, on peut décommenter :
        #
        # if screen:
        #     self.draw_range(screen, camera_offset)

    # ------------------------------------------------------------------
    # OVERRIDES COMBAT / DEGATS
    # ------------------------------------------------------------------
    def destroy(self) -> None:
        """Destruction du bateau (PV <= 0)."""
        # Le jeu principal garde self.game.units comme liste d'unités actives.
        try:
            self.game.units.remove(self)
        except ValueError:
            pass

        # On marque l'unité comme morte pour éviter update() / IA_tick()
        self.is_alive = False
        self.kill()

    def can_fire(self) -> bool:
        """L'éclaireur ne tire pas."""
        return False

    def get_attack_target(self, units: list[Unit]) -> None:
        """Pas d'attaque ciblée pour l'éclaireur -> toujours None."""
        return None


# ----------------------------------------------------------------------
# VARIANTES ROUGE / VERTE POUR RESTER COMPATIBLE AVEC LE RESTE DU CODE
# (le EventHandler spawn encore en appelant EclaireurRouge(game) par ex.)
# ----------------------------------------------------------------------


class EclaireurRouge(Eclaireur):
    def __init__(self, game: Game, is_ia: bool = True) -> None:
        super().__init__(game, team="red", is_ia=is_ia)


class EclaireurVert(Eclaireur):
    def __init__(self, game: Game, is_ia: bool = True) -> None:
        super().__init__(game, team="green", is_ia=is_ia)
