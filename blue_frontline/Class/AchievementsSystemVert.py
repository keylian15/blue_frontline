from Class.AchievementsSystem import AchievementsSystem

class AchievementsSystemVert(AchievementsSystem):
    """Système de gestion des succès pour l'équipe Verte."""
    
    def __init__(self, game=None):
        """Initialise le système de succès pour l'équipe Verte.

        Args:
            game (Game, optional): Référence au jeu. Par defaut à None.
        """
        super().__init__(game, "Vert")
    
    def unlock_test_achievements_vert(self):
        """Débloque des succès de test spécifiques à l'équipe Verte."""
        # Simuler des statistiques différentes pour l'équipe Verte
        self.stats['units_created']['chaloupe'] = 15
        self.stats['units_created']['eclaireur'] = 5
        self.stats['units_killed']['chaloupe'] = 8
        self.stats['total_coins_earned'] = 50
        
        # Vérifier et débloquer les succès
        self.check_achievements()
        print(f"Succès débloqués pour l'équipe Verte: {len(self.unlocked_achievements)}")