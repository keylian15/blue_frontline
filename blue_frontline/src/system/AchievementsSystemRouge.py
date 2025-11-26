from src.system.AchievementsSystem import AchievementsSystem


class AchievementsSystemRouge(AchievementsSystem):
    """Système de gestion des succès pour l'équipe Rouge."""

    def __init__(self, game=None):
        """Initialise le système de succès pour l'équipe Rouge.

        Args:
            game (Game, optional): Référence au jeu. Par defaut à None.
        """
        super().__init__(game, "Rouge")

    def unlock_test_achievements_rouge(self):
        """Débloque des succès de test spécifiques à l'équipe Rouge."""
        # Simuler quelques statistiques pour l'équipe Rouge
        self.stats["units_created"]["chaloupe"] = 10
        self.stats["units_created"]["bateau"] = 3
        self.stats["games_won"] = 2
        self.stats["total_petrole_spent"] = 500

        # Vérifier et débloquer les succès
        self.check_achievements()
        print(f"Succès débloqués pour l'équipe Rouge: {len(self.unlocked_achievements)}")
