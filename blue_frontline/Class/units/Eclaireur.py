from __future__ import annotations

import pygame
from typing import Tuple, List, Optional

from Class.units.Unit import Unit
from Class.Combat import CombatSystem
from Global import UNIT_CONFIGS
from Class.units.IA.IA_Eclaireur import ScoutAI


class Eclaireur(Unit):
    """
    Classe unifiée pour les unités Éclaireur (Rouge et Vert).

    Rôle gameplay :
        - Navire rapide de reconnaissance.
        - Révèle les zones quantiques cachées (objectif de l'IA).
        - N'a pas d'attaque (pas de dégâts, pas de tir).

    IA :
        - Chaque Éclaireur possède self.ai = ScoutAI(...)
        - ScoutAI gère les déplacements automatiques :
            -> Va vers les zones quantiques cachées.
            -> Quand tout est révélé, retourne à la base de son équipe.
        - GameUpdater appelle self.ai.ia_tick(dt) si disponible.

    Affichage :
        - L'Éclaireur dessine sa portée (draw_range) en permanence
          pour feedback visuel.
    """

    def __init__(self, game: "Game", team: str) -> None:
        """
        Initialise l'unité Éclaireur.

        Args:
            game (Game): Instance du jeu en cours (contient nav_grid_adapter,
                         systèmes globaux, plateformes, etc.).
            team (str): Équipe de l'unité. Généralement "red" ou "green".
        """
        # Initialisation de la classe parente
        # NOTE : Dans ton engine, Unit.__init__ prend (game, team, unit_type).
        # On garde ça tel quel pour ne rien casser dans le reste du projet.
        super().__init__(game, team=team, unit_type="eclaireur")

        # ------------------------------------------------------------
        # Chargement des stats depuis Global.py > UNIT_CONFIGS["eclaireur"]
        # ------------------------------------------------------------
        config = UNIT_CONFIGS["eclaireur"]

        # Coût de recrutement / construction
        self.cost: int = config["cost"]

        # Vitesse
        self.max_speed: float = config["max_speed"]
        self.reducte_speed: float = self.max_speed // 2  # vitesse réduite
        self.speed: float = self.max_speed               # vitesse courante

        # Points de vie
        self.max_health: int = config["max_health"]
        self.current_health: int = self.max_health

        # Combat (l'éclaireur ne tire pas, conformément au GDD)
        self.range: int = 0
        self.damage: int = 0
        self.fire_rate: float = 0.0

        # Type d'unité (utilisé ailleurs dans l'UI/HUD/logique)
        self.unit_type: str = config["unit_type"]
        self.unit_name: str = f"Éclaireur {team.capitalize()}"

        # Couleur d'affichage de la portée par équipe
        # Exemple: {'red': (255,0,0,80), 'green': (0,255,0,80)}
        self.range_color: Tuple[int, int, int, int] = config["range_color"][team]

        # État runtime
        self.is_moving: bool = False
        self.target_position: Optional[Tuple[float, float]] = None

        # Sélection HUD (le GameUpdater gère self.is_selected)
        self.is_selected: bool = False

        # ------------------------------------------------------------
        # IA : création du cerveau ScoutAI
        # ------------------------------------------------------------
        #
        # /!\ IMPORTANT :
        # On suppose que le Game a déjà :
        #   - self.nav_grid_adapter (créé via game.build_nav_grid())
        #   - def get_hidden_quantum_polygons(self)
        #   - def get_base_position(self, team)
        #
        # ScoutAI respecte les conventions du chef de groupe :
        #   - ai.is_ia == True
        #   - ai.ia_tick(dt) est appelée par GameUpdater
        #
        self.ai: ScoutAI = ScoutAI(
            unit=self,
            grid=game.nav_grid_adapter,
            get_hidden_quantum_polygons=game.get_hidden_quantum_polygons,
            get_base_pos=game.get_base_position,
            return_to_base_when_done=True,   # Après la révélation de tout -> rentrer base
            replan_interval=2.0,             # Replanifier périodiquement
            proximity_epsilon=4.0,           # Distance pour considérer waypoint atteint
        )

    # ------------------------------------------------------------------
    # MISE À JOUR PAR FRAME
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
        Met à jour l'état de l'unité (déplacements, collisions, etc.).
        Appelée à chaque frame par GameUpdater AVANT l'appel IA.

        Args:
            dt (float): Delta time entre les frames.
            combat_system (CombatSystem): Système de combat global.
            screen (pygame.Surface): Surface d'affichage principale.
            camera_offset (tuple[float, float]): Décalage caméra.
            all_units (list[Unit]): Liste des unités actives dans la partie.
        """
        # Laisse la classe parent gérer le mouvement, la révèlation des
        # zones quantiques, les ralentissements éventuels selon l'eau,
        # etc. (ton Unit.update() gère déjà tout ça dans ton projet).
        super().update(dt, combat_system, screen, camera_offset, all_units)

        # Dessiner la portée de détection / zone d'intérêt
        if screen:
            self.draw_range(screen, camera_offset)

    # ------------------------------------------------------------------
    # UTILITAIRES DE GAMEPLAY
    # ------------------------------------------------------------------
    def take_damage(self, amount: float) -> None:
        """
        Inflige des dégâts à l'unité.

        Args:
            amount (float): Dégâts reçus.
        """
        if amount <= 0:
            return

        self.current_health -= amount
        if self.current_health <= 0:
            self.current_health = 0
            self.destroy()

    def destroy(self) -> None:
        """
        Détruit l'unité (PV <= 0).
        Retire l'unité de la liste du jeu si elle y est encore.
        """
        try:
            self.game.units.remove(self)
        except ValueError:
            pass
        # TODO : si Unit ou Game gère déjà un flag "alive" ou un effet d'explosion,
        # appelle-le ici (ex: super().destroy()).

    def can_fire(self) -> bool:
        """
        Retourne False : L'Éclaireur ne tire pas.
        """
        return False

    def get_attack_target(self, units: List["Unit"]) -> None:
        """
        L'Éclaireur ne choisit pas de cible offensive.
        Toujours None.
        """
        return None


# ----------------------------------------------------------------------
# Alias pour compatibilité avec l'ancien code (spawn par couleur)
# ----------------------------------------------------------------------
class EclaireurRouge(Eclaireur):
    """
    Version spécialisée Éclaireur Rouge.
    Conserve l'ancienne signature EclaireurRouge(game).
    """

    def __init__(self, game: "Game") -> None:
        """
        Args:
            game (Game): L'instance du jeu en cours.
        """
        super().__init__(game, team="red")


class EclaireurVert(Eclaireur):
    """
    Version spécialisée Éclaireur Vert.
    Conserve l'ancienne signature EclaireurVert(game).
    """

    def __init__(self, game: "Game") -> None:
        """
        Args:
            game (Game): L'instance du jeu en cours.
        """
        super().__init__(game, team="green")
