import pygame, json, os
from Global import *

class AchievementsSystem:
    """Système de gestion des succès du jeu."""
    
    def __init__(self, game=None):
        """Initialise le système de succès.

        Args:
            game (Game, optional): Référence au jeu. Par defaut à None.
        """
        self.game = game
        self.achievements = self._init_achievements()
        self.unlocked_achievements = set()
        self.pending_notifications = []  # Queue des notifications à afficher
        self.save_file = ACHIVEMENTS_PATH
        
        # Statistiques de jeu
        self.stats = {
            'units_created': {'chaloupe': 0, 'bateau': 0, 'eclaireur': 0, 'paquebot': 0, 'sousmarin': 0},
            'units_killed': {'chaloupe': 0, 'bateau': 0, 'eclaireur': 0, 'paquebot': 0, 'sousmarin': 0},
            'games_won': 0,
            'games_lost': 0,
            'total_petrole_spent': 0,
            'total_coins_earned': 0,
            'platforms_destroyed': 0,
            'bullets_fired': 0,
            'quantum_islands_activated': 0,
            'total_playtime_seconds': 0,
            'units_created_same_game': set(),  # Pour les succès par partie
            'max_units_alive': 0,
            'different_unit_types_created': set(),  # Tous les types créés dans la partie
        }
        
        # Charger les succès précédemment débloqués
        self.load_achievements()
    
    def _init_achievements(self):
        """Initialise la liste des succès avec leurs conditions.
        
        Returns:
            dict: Un dictionnaire des succès avec leurs conditions.
        """
        return {
            # === CONSTRUCTION & ÉCONOMIE ===
            'first_unit': {
                'name': 'Premier Commandement',
                'description': 'Créer votre première unité',
                'hidden_description': 'Succès mystère - Créez quelque chose...',
                'category': 'Construction & Économie',
                'condition': lambda: sum(self.stats['units_created'].values()) >= 1,
                'unlocked': False
            },
            'unit_collector': {
                'name': 'Collectionneur Naval',
                'description': 'Créer au moins une unité de chaque type dans une partie',
                'hidden_description': 'Succès mystère - Diversifiez votre flotte...',
                'category': 'Construction & Économie',
                'condition': lambda: len(self.stats['different_unit_types_created']) >= 5,
                'unlocked': False
            },
            'mass_producer': {
                'name': 'Production de Masse',
                'description': 'Créer 50 unités au total',
                'hidden_description': 'Succès mystère - Construisez en grande quantité...',
                'category': 'Construction & Économie',
                'condition': lambda: sum(self.stats['units_created'].values()) >= 50,
                'unlocked': False
            },
            'naval_architect': {
                'name': 'Architecte Naval',
                'description': 'Créer 10 paquebots',
                'hidden_description': 'Succès mystère - Maîtrisez les gros navires...',
                'category': 'Construction & Économie',
                'condition': lambda: self.stats['units_created']['paquebot'] >= 10,
                'unlocked': False
            },
            'submarine_fleet': {
                'name': 'Flotte Sous-Marine',
                'description': 'Créer 5 sous-marins',
                'hidden_description': 'Succès mystère - Explorez les profondeurs...',
                'category': 'Construction & Économie',
                'condition': lambda: self.stats['units_created']['sousmarin'] >= 5,
                'unlocked': False
            },
            'big_spender': {
                'name': 'Gros Dépensier',
                'description': 'Dépenser 1000 pétrole au total',
                'hidden_description': 'Succès mystère - Investissez vos ressources...',
                'category': 'Construction & Économie',
                'condition': lambda: self.stats['total_petrole_spent'] >= 1000,
                'unlocked': False
            },
            'treasure_hunter': {
                'name': 'Chasseur de Trésors',
                'description': 'Gagner 100 pièces au total',
                'hidden_description': 'Succès mystère - Accumulez des richesses...',
                'category': 'Construction & Économie',
                'condition': lambda: self.stats['total_coins_earned'] >= 100,
                'unlocked': False
            },
            
            # === COMBAT ===
            'first_blood': {
                'name': 'Premier Sang',
                'description': 'Détruire votre première unité ennemie',
                'hidden_description': 'Succès mystère - Engagez le combat...',
                'category': 'Combat',
                'condition': lambda: sum(self.stats['units_killed'].values()) >= 1,
                'unlocked': False
            },
            'destroyer': {
                'name': 'Destructeur',
                'description': 'Détruire 25 unités ennemies',
                'hidden_description': 'Succès mystère - Semez la destruction...',
                'category': 'Combat',
                'condition': lambda: sum(self.stats['units_killed'].values()) >= 25,
                'unlocked': False
            },
            'platform_buster': {
                'name': 'Briseur de Plateformes',
                'description': 'Détruire une plateforme pétrolière ennemie',
                'hidden_description': 'Succès mystère - Visez les infrastructures...',
                'category': 'Combat',
                'condition': lambda: self.stats['platforms_destroyed'] >= 1,
                'unlocked': False
            },
            'trigger_happy': {
                'name': 'Gâchette Facile',
                'description': 'Tirer 500 projectiles',
                'hidden_description': 'Succès mystère - Faites parler la poudre...',
                'category': 'Combat',
                'condition': lambda: self.stats['bullets_fired'] >= 500,
                'unlocked': False
            },
            'ace_commander': {
                'name': 'Commandant d\'Élite',
                'description': 'Gagner 10 parties',
                'hidden_description': 'Succès mystère - Prouvez votre excellence...',
                'category': 'Combat',
                'condition': lambda: self.stats['games_won'] >= 10,
                'unlocked': False
            },
            
            # === STRATÉGIE ===
            'fleet_admiral': {
                'name': 'Amiral de Flotte',
                'description': 'Avoir 20 unités vivantes en même temps',
                'hidden_description': 'Succès mystère - Construisez une armada...',
                'category': 'Stratégie',
                'condition': lambda: self.stats['max_units_alive'] >= 20,
                'unlocked': False
            },
            'quantum_master': {
                'name': 'Maître Quantique',
                'description': 'Activer 10 îles quantiques',
                'hidden_description': 'Succès mystère - Explorez les mystères...',
                'category': 'Stratégie',
                'condition': lambda: self.stats['quantum_islands_activated'] >= 10,
                'unlocked': False
            },
            'survivor': {
                'name': 'Survivant',
                'description': 'Gagner une partie avec moins de 5 unités créées',
                'hidden_description': 'Succès mystère - La qualité avant la quantité...',
                'category': 'Stratégie',
                'condition': self._check_survivor,
                'unlocked': False
            },
            'diversified_fleet': {
                'name': 'Flotte Diversifiée',
                'description': 'Créer au moins 3 de chaque type d\'unité',
                'hidden_description': 'Succès mystère - Équilibrez vos forces...',
                'category': 'Stratégie',
                'condition': lambda: all(count >= 3 for count in self.stats['units_created'].values()),
                'unlocked': False
            },
            
            # === EXPLORATION ===
            'explorer': {
                'name': 'Explorateur',
                'description': 'Jouer pendant 1 heure au total',
                'hidden_description': 'Succès mystère - Passez du temps en mer...',
                'category': 'Exploration',
                'condition': lambda: self.stats['total_playtime_seconds'] >= 3600,
                'unlocked': False
            },
            'veteran': {
                'name': 'Vétéran',
                'description': 'Jouer pendant 5 heures au total',
                'hidden_description': 'Succès mystère - Devenez un loup de mer...',
                'category': 'Exploration',
                'condition': lambda: self.stats['total_playtime_seconds'] >= 18000,
                'unlocked': False
            },
            'dedicated_admiral': {
                'name': 'Amiral Dévoué',
                'description': 'Jouer pendant 10 heures au total',
                'hidden_description': 'Succès mystère - Consacrez-vous aux océans...',
                'category': 'Exploration',
                'condition': lambda: self.stats['total_playtime_seconds'] >= 36000,
                'unlocked': False
            },
            
            # === SUCCÈS SPÉCIAUX ===
            'perfect_victory': {
                'name': 'Victoire Parfaite',
                'description': 'Gagner sans perdre aucune unité',
                'hidden_description': 'Succès mystère - Une stratégie sans faille...',
                'category': 'Succès Spéciaux',
                'condition': self._check_perfect_victory,
                'unlocked': False
            },
            'speed_runner': {
                'name': 'Coureur de Vitesse',
                'description': 'Gagner une partie en moins de 5 minutes',
                'hidden_description': 'Succès mystère - La rapidité avant tout...',
                'category': 'Succès Spéciaux',
                'condition': self._check_speed_runner,
                'unlocked': False
            },
            'persistent': {
                'name': 'Persévérant',
                'description': 'Perdre 5 parties puis en gagner une',
                'hidden_description': 'Succès mystère - Ne jamais abandonner...',
                'category': 'Succès Spéciaux',
                'condition': self._check_persistent,
                'unlocked': False
            },
            'master_tactician': {
                'name': 'Tacticien Maître',
                'description': 'Détruire 5 unités avec une seule chaloupe',
                'hidden_description': 'Succès mystère - Un seul navire, grande victoire...',
                'category': 'Succès Spéciaux',
                'condition': self._check_master_tactician,
                'unlocked': False
            }
        }
    
    def _check_survivor(self):
        """Vérifie le succès 'Survivant'."""
        # Implémenté plus tard avec les événements de fin de partie
        return False
    
    def _check_perfect_victory(self):
        """Vérifie le succès 'Victoire Parfaite'."""
        # Implémenté plus tard avec les événements de fin de partie
        return False
    
    def _check_speed_runner(self):
        """Vérifie le succès 'Coureur de Vitesse'."""
        # Implémenté plus tard avec le temps de partie
        return False
    
    def _check_persistent(self):
        """Vérifie le succès 'Persévérant'."""
        # Implémenté plus tard avec le suivi des défaites consécutives
        return False
    
    def _check_master_tactician(self):
        """Vérifie le succès 'Tacticien Maître'."""
        # Implémenté plus tard avec le suivi des kills par unité
        return False
    
    def track_unit_created(self, unit_type, cost=0):
        """Suit la création d'une unité.
        
        Args:
            unit_type (str): Le type d'unité créé.
            cost (int, optional): Le coût de l'unité. Par defaut à 0.
        """
        if unit_type in self.stats['units_created']:
            self.stats['units_created'][unit_type] += 1
            self.stats['total_petrole_spent'] += cost
            self.stats['units_created_same_game'].add(unit_type)
            self.stats['different_unit_types_created'].add(unit_type)
            
        self.check_achievements()
    
    def track_unit_killed(self, unit_type):
        """Suit la destruction d'une unité.
        
        Args:
            unit_type (str): Le type d'unité détruite.
        """
        if unit_type in self.stats['units_killed']:
            self.stats['units_killed'][unit_type] += 1
        self.check_achievements()
    
    def track_bullet_fired(self):
        """Suit le tir d'un projectile."""
        self.stats['bullets_fired'] += 1
        self.check_achievements()
    
    def track_quantum_island_activated(self):
        """Suit l'activation d'une île quantique."""
        self.stats['quantum_islands_activated'] += 1
        self.check_achievements()
    
    def track_game_won(self):
        """Suit une victoire."""
        self.stats['games_won'] += 1
        self.check_achievements()
    
    def track_game_lost(self):
        """Suit une défaite."""
        self.stats['games_lost'] += 1
        self.check_achievements()
    
    def track_platform_destroyed(self):
        """Suit la destruction d'une plateforme."""
        self.stats['platforms_destroyed'] += 1
        self.check_achievements()
    
    def track_coins_earned(self, amount):
        """Suit les pièces gagnées.
        
        Args:
            amount (int): Le montant de pièces gagnées.
        """
        self.stats['total_coins_earned'] += amount
        self.check_achievements()
    
    def update_max_units_alive(self, current_count):
        """Met à jour le maximum d'unités vivantes simultanément.
        
        Args:
            current_count (int): Le nombre actuel d'unités vivantes.
        """
        if current_count > self.stats['max_units_alive']:
            self.stats['max_units_alive'] = current_count
            self.check_achievements()
    
    def update_playtime(self, delta_seconds):
        """Met à jour le temps de jeu total.
        
        Args:
            delta_seconds (int): Le temps écoulé depuis la dernière mise à jour en secondes.
        """
        self.stats['total_playtime_seconds'] += delta_seconds
        self.check_achievements()
    
    def check_achievements(self):
        """Vérifie tous les succès et débloque ceux qui sont atteints."""
        newly_unlocked = []
        
        for achievement_id, achievement in self.achievements.items():
            if not achievement['unlocked'] and achievement_id not in self.unlocked_achievements:
                try:
                    if achievement['condition']():
                        achievement['unlocked'] = True
                        self.unlocked_achievements.add(achievement_id)
                        newly_unlocked.append(achievement)
                        print(f"[SUCCÈS] Débloqué: {achievement['name']} - {achievement['description']}")
                except Exception as e:
                    print(f"Erreur lors de la vérification du succès {achievement_id}: {e}")
        
        # Ajouter les nouvelles notifications à la queue
        for achievement in newly_unlocked:
            self.pending_notifications.append({
                'achievement': achievement,
                'display_time': 3000,  # 3 secondes en millisecondes
                'created_at': pygame.time.get_ticks()
            })
        
        # Sauvegarder si de nouveaux succès ont été débloqués
        if newly_unlocked:
            self.save_achievements()
    
    def get_achievements_by_category(self):
        """Retourne les succès organisés par catégorie."""
        categories = {}
        for achievement_id, achievement in self.achievements.items():
            category = achievement['category']
            if category not in categories:
                categories[category] = []
            
            achievement_data = achievement.copy()
            achievement_data['id'] = achievement_id
            achievement_data['unlocked'] = achievement_id in self.unlocked_achievements
            categories[category].append(achievement_data)
        
        return categories
    
    def get_completion_percentage(self):
        """Retourne le pourcentage de succès complétés."""
        total = len(self.achievements)
        completed = len(self.unlocked_achievements)
        return (completed / total * 100) if total > 0 else 0
    
    def save_achievements(self):
        """Sauvegarde les succès débloqués dans un fichier JSON."""
        try:
            data = {
                'unlocked_achievements': list(self.unlocked_achievements),
                'stats': self.stats.copy()
            }
            # Convertir les sets en listes pour la sérialisation JSON
            data['stats']['units_created_same_game'] = list(data['stats']['units_created_same_game'])
            data['stats']['different_unit_types_created'] = list(data['stats']['different_unit_types_created'])
            
            with open(self.save_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des succès: {e}")
    
    def load_achievements(self):
        """Charge les succès débloqués depuis un fichier JSON."""
        try:
            if os.path.exists(self.save_file):
                with open(self.save_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.unlocked_achievements = set(data.get('unlocked_achievements', []))
                saved_stats = data.get('stats', {})
                
                # Fusionner les stats sauvegardées avec les stats par défaut
                for key, value in saved_stats.items():
                    if key in ['units_created_same_game', 'different_unit_types_created']:
                        self.stats[key] = set(value)  # Reconvertir en sets
                    elif key in self.stats:
                        self.stats[key] = value
                
                # Mettre à jour le statut des succès
                for achievement_id in self.unlocked_achievements:
                    if achievement_id in self.achievements:
                        self.achievements[achievement_id]['unlocked'] = True
        except Exception as e:
            print(f"Erreur lors du chargement des succès: {e}")
    
    def reset_game_stats(self):
        """Remet à zéro les statistiques de la partie en cours."""
        self.stats['units_created_same_game'] = set()
        self.stats['different_unit_types_created'] = set()
        self.stats['max_units_alive'] = 0
    
    def get_pending_notifications(self):
        """Retourne et supprime les notifications en attente."""
        notifications = self.pending_notifications.copy()
        self.pending_notifications.clear()
        return notifications
    
    def reset_all_achievements(self):
        """Remet à zéro tous les succès et statistiques."""
        # Remettre à zéro les succès débloqués
        self.unlocked_achievements.clear()
        
        # Remettre à zéro toutes les statistiques
        self.stats = {
            'units_created': {'chaloupe': 0, 'bateau': 0, 'eclaireur': 0, 'paquebot': 0, 'sousmarin': 0},
            'units_killed': {'chaloupe': 0, 'bateau': 0, 'eclaireur': 0, 'paquebot': 0, 'sousmarin': 0},
            'games_won': 0,
            'games_lost': 0,
            'total_petrole_spent': 0,
            'total_coins_earned': 0,
            'platforms_destroyed': 0,
            'bullets_fired': 0,
            'quantum_islands_activated': 0,
            'total_playtime_seconds': 0,
            'units_created_same_game': set(),
            'max_units_alive': 0,
            'different_unit_types_created': set(),
        }
        
        # Remettre à zéro le statut des succès
        for achievement in self.achievements.values():
            achievement['unlocked'] = False
        
        # Vider les notifications en attente
        self.pending_notifications.clear()
        
        # Sauvegarder le reset
        self.save_achievements()