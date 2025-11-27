from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    import TiledObject
    from src.core.Game import Game
    from src.units.Unit import Unit


class PlateformePetroliere(pygame.sprite.Sprite):
    """Classe pour gérer les plateformes pétrolières."""

    def __init__(self, game: Game, team: str, objTiled: TiledObject, is_ia: bool = True):  # type: ignore
        """Initialise une nouvelle instance de PlateformePetroliere.

        Args:
            game (Game): L'instance du jeu.
            team (str): Équipe de la plateforme.
            objTiled (TiledObject): Objet Tiled correspondant à la plateforme.
            is_ia (bool, optional): Indique si la plateforme est contrôlée par une IA. Par défaut, True.
        """
        super().__init__()
        self.game = game
        self.team = team
        self.objTiled = objTiled
        self.hitbox_polygon = objTiled.points
        self.name = "BaseRouge" if team == "red" else "BaseVerte"

        self.max_health = 1000
        self.current_health = 1000
        self.is_alive = True

        # Verifier l'utilité d'ici ===>
        # Calculer les limites du polygone pour le rect
        min_x = min(point[0] for point in self.hitbox_polygon)
        max_x = max(point[0] for point in self.hitbox_polygon)
        min_y = min(point[1] for point in self.hitbox_polygon)
        max_y = max(point[1] for point in self.hitbox_polygon)
        # Position centrale calculée depuis le polygone
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        self.position = [float(center_x), float(center_y)]
        self.width = int(max_x - min_x)
        self.height = int(max_y - min_y)
        rect_x = int(min_x)
        rect_y = int(min_y)
        # <===

        self.unit_type = "plateformePetroliere"
        self.is_selected = False

        # Image invisible (rectangle transparent) - garde les hitboxes mais invisible
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        color = (0, 0, 0, 0)  # Complètement transparent (invisible)
        self.image.fill(color)

        # Le rect englobe la zone de la hitbox
        self.rect = pygame.Rect(rect_x, rect_y, self.width, self.height)

        # Pour compatibilité avec la logique d'unités
        from src.config.units import UNIT_CONFIGS

        self.range = 15
        self.damage_pourcentage = 10
        self.damage = UNIT_CONFIGS["chaloupe"]["max_health"] * self.damage_pourcentage / 100
        self.fire_rate = 0.25  # 4 tir/ 4 secondes
        self.last_shot_time = 0
        self.is_platform = True

        # On appelle l'initialisation de l'IA si c'est une IA
        self.is_ia = is_ia
        if self.is_ia:
            self.ia_init()

    def update(
        self,
        dt=0,
        combat_system=None,
        screen=None,
        camera_offset=(0, 0),
        all_units=None,
    ):
        """Met à jour la plateforme (tir automatique).

        Args:
            dt (int, optional): La différence de temps entre chaque frame. Par défaut à 0.
            combat_system (CombatSystem, optional): Le système de combat. Par défaut à None.
            screen (pygame.Surface, optional): L'écran sur lequel afficher. Par défaut à None.
            camera_offset (tuple[float, float], optional): Le décalage de la caméra. Par défaut à (0, 0).
            all_units (list[Unit], optional): La liste de toutes les unités dans le jeu. Par défaut à None.
        """
        import time

        if not self.is_alive:
            return
        if all_units is None or combat_system is None:
            return
        enemies_in_range = []
        range_pixels = self.range * 32
        for unit in all_units:
            if unit is self:
                continue
            if hasattr(unit, "team") and unit.team != self.team and getattr(unit, "is_alive", False):
                if hasattr(unit, "rect"):
                    cx, cy = self.position[0], self.position[1]
                    rx, ry, rw, rh = (
                        unit.rect.left,
                        unit.rect.top,
                        unit.rect.width,
                        unit.rect.height,
                    )
                    closest_x = max(rx, min(cx, rx + rw))
                    closest_y = max(ry, min(cy, ry + rh))
                    distance = ((cx - closest_x) ** 2 + (cy - closest_y) ** 2) ** 0.5
                else:
                    distance = (
                        (self.position[0] - unit.position[0]) ** 2 + (self.position[1] - unit.position[1]) ** 2
                    ) ** 0.5
                if distance <= range_pixels:
                    enemies_in_range.append(unit)
        if enemies_in_range:
            current_time = time.time()
            time_since_last_shot = current_time - self.last_shot_time
            multiplica = self.game.hud.timer.get_speed_multiplier()
            if time_since_last_shot >= (1.0 / (self.fire_rate * multiplica)):
                target = enemies_in_range[0]
                if combat_system:
                    combat_system.fire_projectile(self, target)
                else:
                    if hasattr(target, "take_damage"):
                        target.take_damage(self.damage, killer=self)
                self.last_shot_time = current_time
        # === Partie IA ===
        if self.is_ia:
            self.ia_update()  # On met a jour les données de l'IA
            if self.ia_check_wait():  # Si on doit attendre
                return
            # On note le scénario courant s'il existe.
            if self.current_scenario:
                scenario = self.current_scenario
            else:
                self.ia_scenarios()  # On applique les scenarios de l'IA
                scenario = self.ia_get_scenario()  # On récupére le scénario de l'IA
                self.current_scenario = scenario  # On note le scénario courant

            # On fait le scénario de l'IA
            self.ia_do_scenario(scenario)

            # Si le scénario est terminé ou a échoué, on le remet à None
            if self.wait is False:
                self.current_scenario = None

    def take_damage(self, damage: int, killer: str = None):
        """Inflige des dégâts à la plateforme.

        Args:
            damage (int): Nombre de dégâts à infliger.
            killer (str, optional): L'équipe attaquante. Defaults to None.
        """

        if not self.is_alive:
            return
        self.current_health -= damage
        if self.current_health <= 0:
            self.current_health = 0
            self.is_alive = False
            self.on_destroyed()

    def on_destroyed(self):
        """Appelé quand la plateforme est détruite."""
        if self.is_ia:
            self.ia_save_log(self.team)
        # Déclencher la victoire si la plateforme a une référence vers le Game
        if hasattr(self, Game) and self.game:
            self.game.on_platform_destroyed(self)

    def draw_health_bar(self, screen: pygame.Surface, camera_offset: tuple[float, float], zoom: float):
        """Dessine une barre de vie large pour la plateforme.

        Args:
            screen (pygame.Surface): L'ecran de jeu.
            camera_offset (tuple[float, float]): La position de la caméra.
            zoom (float): Le zoom de la caméra.
        """

        if not self.is_alive:
            return

        # Pour les plateformes, utiliser la position de l'image Tiled plutôt que le centre de la hitbox
        xs = [p.x for p in self.hitbox_polygon]
        ys = [p.y for p in self.hitbox_polygon]
        image_center_x = sum(xs) / len(xs)
        image_center_y = sum(ys) / len(ys)

        # Calculer les coordonnées de l'image sur l'écran
        screen_x = (image_center_x - camera_offset[0]) * zoom
        screen_y = (image_center_y - camera_offset[1]) * zoom

        # Barre de vie plus large pour les plateformes, placée en dessous de l'image
        bar_width = int(180 * zoom)  # Largeur fixe adaptée aux plateformes
        bar_height = max(12, int(20 * zoom))
        bar_x = int(screen_x - bar_width // 2)
        # Placer la barre en dessous de l'image de la plateforme (environ 120px en dessous du centre)
        bar_y = int(screen_y + 120 * zoom)

        # Fond
        background_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(screen, (80, 80, 80), background_rect)

        # Vie
        health_percentage = self.current_health / self.max_health
        health_width = int(bar_width * health_percentage)
        health_rect = pygame.Rect(bar_x, bar_y, health_width, bar_height)

        # Couleur de la barre de vie selon le pourcentage
        if health_percentage > 0.6:
            health_color = (0, 255, 0)  # Vert
        elif health_percentage > 0.3:
            health_color = (255, 255, 0)  # Jaune
        else:
            health_color = (255, 0, 0)  # Rouge

        pygame.draw.rect(screen, health_color, health_rect)

        # Contour
        pygame.draw.rect(screen, (0, 0, 0), background_rect, 2)

        # Texte avec la vie actuelle/maximale, placé au-dessus de la barre
        font = pygame.font.Font(None, max(16, int(18 * zoom)))
        health_text = f"{self.current_health}/{self.max_health}"
        text_surface = font.render(health_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(screen_x, bar_y - 20 * zoom))
        screen.blit(text_surface, text_rect)

    # === FONCTIONS d'IA ===
    def ia_init(self):
        """Fonction d'initialisation de l'IA"""
        from random import randint

        # On défini plusieurs coefficients. L'IA modifira a la fin de partie.
        self.coefficients = {
            "scenarios": {
                "defense": {
                    "simple": 1,
                    "forte": 2,
                },
                "exploration": 1,
                "production": 1,
                "attaque": {
                    "simple": 1,
                    "forte": 2,
                },
            },
        }

        # On défini plusieurs marges. L'IA modifira a la fin de partie.
        self.marges = {
            "oil": randint(1, 30),
        }

        # On défini des seuils pour la quantité d'entité. L'IA modifira au fur et a mesure de la partie.
        self.max_seuil = 10
        self.seuils = {
            "active": {
                "chaloupe": randint(1, self.max_seuil),
                "bateau": randint(1, self.max_seuil),
                "sousmarin": randint(1, self.max_seuil),
                "paquebot": randint(1, self.max_seuil),
            },
            "passive": {
                "eclaireur": 1,
                "pompe_petroliere": randint(1, self.max_seuil),
            },
        }

        # On défini la liste vide
        self.liste = ["chaloupe", "bateau", "sousmarin", "paquebot"]
        self.units = []
        self.last_position = None

        self.wait = False
        self.current_scenario = False

        # On testera toujours si le random est inférieur, si true on prend.
        self.probabilites = {
            # --- Choix de scénario global ---
            "scenario_selection": 0.75,  # 75% : prendre le meilleur scénario
            # --- Cas général d’attaque ---
            "general": 0.5,  # 50% : attaque forte / 50% : attaque simple
            # --- Défense forte ---
            "defense_forte": {
                "no_cost": 0.5,  # 50% : attendre jusqu’à obtention
                "can_spawn": 0.75,  # 75% : spawn une entité
            },
            # --- Attaque simple ---
            "attaque_simple": {
                # Lorsqu’on prend une entité (répartition équitable)
                "entities": {
                    "chaloupe": 0.25,
                    "bateau": 0.25,
                    "sousmarin": 0.25,
                    "paquebot": 0.25,
                }
            },
            # --- Attaque forte ---
            "attaque_forte": {
                "no_cost": 0.75,  # 75% : attendre jusqu’à obtention
                "can_spawn": 0.25,  # 25% : spawn une entité
            },
            # --- Exploration ---
            "exploration": 0.25,  # 25% : attendre si on n’a pas les ressources
            # --- Production ---
            "production": 0.75,  # 75% : attendre si on n’a pas les ressources
        }

        # Système de logs
        self.logs = []

        # Pour les upgrades
        self.max_upgrade = False

    def ia_update(self):
        """Fonction permettant de mettre à jour les données de l'IA, appelé a chaque tick"""
        # On récupére les unités du jeu
        self.units = self.game.units

        if self.units:
            # Définitions des différentes listes
            self.units_ally, self.units_enemy, self.pompe_ally, self.pompe_enemy = (
                [],
                [],
                [],
                [],
            )
            self.units_ally_dico = {
                "chaloupe": 0,
                "bateau": 0,
                "sousmarin": 0,
                "paquebot": 0,
                "eclaireur": 0,
            }
            self.units_enemy_dico = {
                "chaloupe": 0,
                "bateau": 0,
                "sousmarin": 0,
                "paquebot": 0,
                "eclaireur": 0,
            }

            # On récupére les différentes unités dans les 4 listes différentes.
            for unit in self.units:
                # Si c'est une plateforme
                if unit.unit_type == "plateformePetroliere":
                    continue
                # Si c'est une unité alliée
                if unit.team == self.team:
                    # Si c'est une pompe
                    if unit.unit_type == "pompe_petroliere":
                        self.pompe_ally.append(unit)
                    else:
                        self.units_ally.append(unit)
                        # On l'ajoute au dico
                        if self.units_ally_dico.get(unit.unit_type):
                            self.units_ally_dico[unit.unit_type] += 1
                        else:
                            self.units_ally_dico[unit.unit_type] = 1
                # Si c'est une unité ennemie
                else:
                    # Si c'est une pompe
                    if unit.unit_type == "pompe_petroliere":
                        self.pompe_enemy.append(unit)
                    else:
                        self.units_enemy.append(unit)
                        # On l'ajoute au dico
                        if self.units_enemy_dico.get(unit.unit_type):
                            self.units_enemy_dico[unit.unit_type] += 1
                        else:
                            self.units_enemy_dico[unit.unit_type] = 1

            # On récupére le nombre d'unités.
            self.nb_units_ally = len(self.units_ally)
            self.nb_units_enemy = len(self.units_enemy)
            self.nb_pompe_ally = len(self.pompe_ally)
            self.nb_pompe_enemy = len(self.pompe_enemy)

            # On récupére le nombre d'îles quantiques cachées
            if hasattr(self.game, "quantique_area_hidden"):
                self.nb_island_hidden = len(self.game.quantique_area_hidden)

            # On récupére le nombre de pétrole
            if hasattr(self.game, "hud"):
                if self.team == "red":
                    self.nb_oil_enemy = self.game.hud.petrole_green.count
                    self.nb_oil_ally = self.game.hud.petrole_red.count
                else:
                    self.nb_oil_enemy = self.game.hud.petrole_red.count
                    self.nb_oil_ally = self.game.hud.petrole_green.count

            # On récupére le event Handler
            if hasattr(self.game, "event_handler"):
                self.event_handler = self.game.event_handler

            # On fait les améliorations automatiques de la plateforme
            if not self.max_upgrade:
                nom_upgrade = self.ia_get_upgrade()
                if nom_upgrade:
                    self.ia_do_upgrade(nom_upgrade)

    def ia_scenarios(self):
        """Fonction permettant de déterminer les scénarios de l'IA"""
        from random import random

        self.scenarios = {
            "defense": {
                "simple": 0,
                "forte": 0,
            },
            "exploration": 0,
            "production": 0,
            "attaque": {
                "simple": 0,
                "forte": 0,
            },
        }

        # On récupere les coefficients pour plus de facilité.
        coef_def_sim = self.coefficients["scenarios"]["defense"]["simple"]
        coef_def_fort = self.coefficients["scenarios"]["defense"]["forte"]
        coef_exp = self.coefficients["scenarios"]["exploration"]
        coef_prod = self.coefficients["scenarios"]["production"]
        coef_att_sim = self.coefficients["scenarios"]["attaque"]["simple"]
        coef_att_fort = self.coefficients["scenarios"]["attaque"]["forte"]

        # Test 1 : Si la base à moins de 50% de vie => Défense Simple.
        if self.current_health <= (self.max_health * 0.5):
            self.scenarios["defense"]["simple"] += coef_def_sim

        # Test 2 : Si la base à moins de 20% de vie => Défense Forte.
        if self.current_health <= (self.max_health * 0.2):
            self.scenarios["defense"]["forte"] += coef_def_fort

        # On parcours les unités pour le Test 3 et 4 :
        for unit in self.units:
            # Test 3 : Distance d'un enemi présent dans la range de la base => Défense Simple.
            if self.ia_is_near_from_base(unit):
                self.scenarios["defense"]["simple"] += coef_def_sim

            # Test 4 : Distance d'un enemi présent dans la range de la base / 2 (Plus proche) => Défense Forte.
            if self.ia_is_near_from_base(unit, 2):
                self.scenarios["defense"]["forte"] += coef_def_fort

        # Test 5 : S'il existe encore des zones quantiques cachées => Exploration.
        if self.nb_island_hidden > 0:
            self.scenarios["exploration"] += coef_exp
            if self.units_ally_dico["eclaireur"] > 0:
                self.scenarios["exploration"] /= 2

        # Test 6 : Si on est proche d'avoir une pompe pétroliere => Production.
        if self.ia_is_near_oil_goal(self.nb_oil_ally, "pompe_petroliere"):
            self.scenarios["production"] += coef_prod

        # Test 7 : Si l'ennemi a plus de pétrole que nous => Attaque Simple.
        if self.nb_oil_enemy > self.nb_oil_ally:
            self.scenarios["attaque"]["simple"] += coef_att_sim

        # Test 8 : Si l'ennemi a une pompe pétroliere => Attaque Forte.
        if self.nb_pompe_enemy > 0:
            self.scenarios["attaque"]["forte"] += coef_att_fort

        # Test 9 : Si la base ennemi à moins de 50% de vie => Attaque Simple.
        ennemy_team = "red" if self.team == "green" else "green"
        if self.game.plateformes[ennemy_team].current_health <= (self.game.plateformes[ennemy_team].max_health * 0.5):
            self.scenarios["attaque"]["simple"] += coef_att_sim

        # Test 10 : Si la base ennemi à moins de 20% de vie => Attaque Forte.
        if self.game.plateformes[ennemy_team].current_health <= (self.game.plateformes[ennemy_team].max_health * 0.2):
            self.scenarios["attaque"]["forte"] += coef_att_fort

        # Test 11 : Si le nombre d'unités alliées est 2 fois supérieur au nombre d'unités ennemies => Attaque Forte.
        if self.nb_units_ally >= (2 * self.nb_units_enemy):
            self.scenarios["attaque"]["forte"] += coef_att_fort

        # Cas général : Attaque Forte à 50%, Attaque Simple à 50%.
        if random() < self.probabilites["general"]:
            self.scenarios["attaque"]["forte"] += coef_att_fort * 0.5
        else:
            self.scenarios["attaque"]["simple"] += coef_att_sim * 0.5

    def ia_get_scenario(self):
        """Renvoie le meilleur scénario 75% du temps, sinon un scénario aléatoire.

        Returns:
            (tuple): (scénario, sous_scénario, score)
        """
        from random import choice, random

        max_scenario = (None, None, 0)  # (scénario, sous_scenario, score)
        scenarios = list(self.scenarios.items())

        # --- 75% : choisir le meilleur scénario ---
        if random() < self.probabilites["scenario_selection"]:
            for cle, valeur in scenarios:
                if isinstance(valeur, dict):
                    for sous_cle, sous_valeur in valeur.items():
                        if sous_valeur > max_scenario[2]:
                            max_scenario = (cle, sous_cle, sous_valeur)
                else:
                    if valeur > max_scenario[2]:
                        max_scenario = (cle, None, valeur)

        # --- 25% : choisir un scénario aléatoire ---
        else:
            cle, valeur = choice(scenarios)
            if isinstance(valeur, dict):
                sous_cle, sous_valeur = choice(list(valeur.items()))
                max_scenario = (cle, sous_cle, sous_valeur)
            else:
                max_scenario = (cle, None, valeur)
        return max_scenario

    def ia_do_scenario(self, scenario: tuple[str, str | None, int]):
        """Fonction permettant d'executer les scénarios.

        Args:
            scenario (tuple[str, str  |  None, int]): Le scénario demandé

        Returns:
            (bool): -1 si ca ne s'execute pas.
        """
        # On regarde le scénario principal et le secondaire s'il existe.
        match scenario:
            case ("attaque", "simple", _):
                self.ia_do_attack_simple()
            case ("attaque", "forte", _):
                self.ia_do_attack_forte()
            case ("defense", "simple", _):
                self.ia_do_defense_simple()
            case ("defense", "forte", _):
                self.ia_do_defense_forte()
            case ("production", None, _):
                self.ia_do_production()
            case ("exploration", None, _):
                self.ia_do_exploration()
            case _:
                return -1

    def ia_do_defense_simple(self):
        """Fonction permettant de faire le scénario de défense simple.

        Returns :
            (bool): True si le scénario a été effectué, False sinon."""
        from src.utils.Utils import get_cost

        # On vérifie qu'on peux spawn la chaloupe.
        nom = "chaloupe"
        data = nom, self.team, get_cost(nom)
        if self.event_handler.check_cost(data[1], data[2]):
            # On spawn la chaloupe.
            self.event_handler.apply_cost(data[0], data[1], data[2])
            self.event_handler.spawn_unit(data[0], data[1])
            # === Logs ===
            self.ia_log_action("spawn", self.current_scenario, data[2], {"unit": data[0]})
            return True
        return False

    def ia_do_defense_forte(self, indice: int = 0):
        """Fonction permettant de faire le scénario de défense forte.
        Args :
            indice (int): Indice de l'entité à spawn.

        Returns :
            (bool): True si le scénario a été effectué, False sinon."""
        # Si on doit attendre, on ne fait rien.
        if self.wait:
            return False

        # On verifie le seuil pour le changer dans le cas où il est atteint.
        if self.ia_check_seuil():
            self.ia_change_seuil()

        # On parcour la liste dans l'ordre donnée.
        from random import random

        from src.utils.Utils import get_cost

        indice = indice % len(self.liste)
        data = self.liste[indice], self.team, get_cost(self.liste[indice])
        # Si on peux spawn l'unité.
        if self.event_handler.check_cost(data[1], data[2]):
            # Si on est supérieur au seuil on passe a l'indice d'apres, sauf si on a la derniere unité.
            if self.units_ally_dico[data[0]] >= self.seuils["active"][data[0]]:
                if indice < len(self.liste) - 1:
                    # === Logs ===
                    self.ia_log_action(
                        "change_unit",
                        self.current_scenario,
                        0,
                        {"other": ("seuil atteint", data[0])},
                    )
                    self.ia_do_defense_forte(indice + 1)
                else:
                    return False

            # On a 75% de chance de spawn l'unité.
            if random() < self.probabilites["defense_forte"]["can_spawn"]:
                self.event_handler.apply_cost(data[0], data[1], data[2])
                self.event_handler.spawn_unit(data[0], data[1])
                # === Logs ===
                self.ia_log_action("spawn", self.current_scenario, data[2], {"unit": data[0]})
                return True
            else:
                # 25% de chance de passer a l'unité d'apres, si on a pas la derniere unité.
                if indice < len(self.liste) - 1:
                    # === Logs ===
                    self.ia_log_action(
                        "change_unit",
                        self.current_scenario,
                        0,
                        {
                            "other": (
                                "proba",
                                self.probabilites["attaque_forte"]["can_spawn"],
                            )
                        },
                    )
                    self.ia_do_defense_forte(indice + 1)

                else:
                    self.event_handler.apply_cost(data[0], data[1], data[2])
                    self.event_handler.spawn_unit(data[0], data[1])
                    # === Logs ===
                    self.ia_log_action("spawn", self.current_scenario, data[2], {"unit_type": data[0]})
                    return True

        else:
            # On a 50% d'attendre.
            if random() < self.probabilites["defense_forte"]["no_cost"]:
                # On attend pour le faire spawn.
                self.ia_wait_for(data[0])
        return False

    def ia_do_attack_simple(self):
        """Fonction permettant de faire le scénario d'attaque simple.

        Returns:
            (bool): True si le scénario a fonctionné, False sinon.
        """

        from src.utils.Utils import get_cost

        # Les 4 unités ont 25% de chance de spawn.
        nom = self.ia_tirage_pondere(self.probabilites["attaque_simple"]["entities"])
        data = nom, self.team, get_cost(nom)
        # On vérifie qu'on peux spawn l'unité.
        if self.event_handler.check_cost(data[1], data[2]):
            # On spawn l'unité.
            self.event_handler.apply_cost(data[0], data[1], data[2])
            self.event_handler.spawn_unit(data[0], data[1])
            # === Logs ===
            self.ia_log_action("spawn", self.current_scenario, data[2], {"unit": data[0]})
            return True
        return False

    def ia_do_attack_forte(self, indice: int = 0):
        """Fonction permettant de faire le scénario d'attaque forte.
        Args :
            indice (int): Indice de l'entité à spawn.

        Returns :
            (bool): True si le scénario a été effectué, False sinon."""
        # Si on doit attendre, on ne fait rien.
        if self.wait:
            return False

        # On verifie le seuil pour le changer dans le cas où il est atteint.
        if self.ia_check_seuil():
            self.ia_change_seuil()

        # On parcour la liste dans l'ordre donnée.
        from random import random

        from src.utils.Utils import get_cost

        indice = indice % len(self.liste)
        data = self.liste[indice], self.team, get_cost(self.liste[indice])
        # Si on peux spawn l'unité.
        if self.event_handler.check_cost(data[1], data[2]):
            # Si on est supérieur au seuil on passe a l'indice d'apres, sauf si on a la derniere unité.
            if self.units_ally_dico[data[0]] >= self.seuils["active"][data[0]]:
                if indice < len(self.liste) - 1:
                    # === Logs ===
                    self.ia_log_action(
                        "change_unit",
                        self.current_scenario,
                        0,
                        {"other": ("seuil atteint", data[0])},
                    )
                    self.ia_do_attack_forte(indice + 1)
                else:
                    return False

            # On a 25% de chance de spawn l'unité.
            if random() < self.probabilites["attaque_forte"]["can_spawn"]:
                self.event_handler.apply_cost(data[0], data[1], data[2])
                self.event_handler.spawn_unit(data[0], data[1])

                # === Logs ===
                self.ia_log_action("spawn", self.current_scenario, data[2], {"unit_type": data[0]})
                return True
            else:
                # 75% de chance de passer a l'unité d'apres, sauf si on a la derniere unité.
                if indice < len(self.liste) - 1:
                    # === Logs ===
                    self.ia_log_action(
                        "change_unit",
                        self.current_scenario,
                        0,
                        {
                            "other": (
                                "proba",
                                self.probabilites["attaque_forte"]["can_spawn"],
                            )
                        },
                    )

                    self.ia_do_attack_forte(indice + 1)

                else:
                    self.event_handler.apply_cost(data[0], data[1], data[2])
                    self.event_handler.spawn_unit(data[0], data[1])
                    # === Logs ===
                    self.ia_log_action("spawn", self.current_scenario, data[2], {"unit_type": data[0]})
                    return True

        else:
            # On a 75% d'attendre.
            if random() < self.probabilites["attaque_forte"]["no_cost"]:
                # On attend pour le faire spawn.
                self.ia_wait_for(data[0])
        return False

    def ia_do_exploration(self):
        """Fonction permettant de faire le scénario d'exploration.

        Returns:
            (bool): True si le scénario est réalisé, False sinon.
        """
        from src.utils.Utils import get_cost

        data = "eclaireur", self.team, get_cost("eclaireur")
        # On vérifie que l'on peux spawn l'éclaireur.
        if self.event_handler.check_cost(data[1], data[2]):
            # On vérifie qu'on est sous le seuil.
            if self.units_ally_dico[data[0]] < self.seuils["passive"][data[0]]:
                # On spawn l'éclaireur.
                self.event_handler.apply_cost(data[0], data[1], data[2])
                self.event_handler.spawn_unit(data[0], data[1])
                # === Logs ===
                self.ia_log_action("spawn", self.current_scenario, data[2], {"unit_type": data[0]})
                return True
        else:
            from random import random

            # Si on peut pas spawn, on a 25% de chance d'attendre.
            if random() < self.probabilites["exploration"]:
                self.ia_wait_for(data[0])
        return False

    def ia_do_production(self):
        """Fonction permettant de faire le scénario de production.

        Returns:
            (bool): True si le scénario est réalisé, False sinon.
        """

        from src.utils.Utils import get_cost

        data = "pompe_petroliere", self.team, get_cost("pompe_petroliere")
        # On vérifie que l'on peux spawn la pompe.
        if self.event_handler.check_cost(data[1], data[2]):
            # On vérifie qu'on est sous le seuil.
            if self.nb_pompe_ally < self.seuils["passive"][data[0]]:
                # On spawn la pompe.
                self.event_handler.apply_cost(data[0], data[1], data[2])
                self.event_handler.spawn_unit(data[0], data[1])
                # === Logs ===
                self.ia_log_action("spawn", self.current_scenario, data[2], {"unit_type": data[0]})
                return True
        else:
            from random import random

            # Si on peut pas spawn, on a 75% de chance d'attendre.
            if random() < self.probabilites["production"]:
                self.ia_wait_for(data[0])
        return False

    def ia_wait_for(self, type_unit: str):
        """Fonction permettant de définir des variables pour attendre.

        Args:
            type_unit (str): Le type d'unité
        """
        # On passe l'attente a vrai
        self.wait = True
        self.wait_target = type_unit
        # === Logs ===
        from src.utils.Utils import get_cost

        self.ia_log_action(
            "wait",
            self.current_scenario,
            get_cost(self.wait_target),
            {"unit": self.wait_target},
        )

    def ia_check_wait(self, data: tuple[str, str, int] = None):
        """Fonction permettant de vérifier si l'IA attend.

        Args:
            data (tuple[str, str, int], optional): Les données pour le spawn. Defaults to None.

        Returns:
            (bool): True si l'IA attend, False sinon.
        """
        if self.wait:
            from src.utils.Utils import get_cost

            if not data:
                data = self.wait_target, self.team, get_cost(self.wait_target)
            # On vérifie que l'on peux spawn l'entité
            if self.event_handler.check_cost(data[1], data[2]):
                self.wait = False
                self.wait_target = None
                return False
            return True
        else:
            return False

    def ia_check_seuil(self):
        """Fonction permettant de vérifier si le seuil est atteint pour toutes les unités alliées.

        Returns :
            (bool): True si le seuil est atteint pour tous, False sinon."""

        # On parcours toutes les unités alliées.
        for cle, valeur in self.units_ally_dico.items():
            if cle == "eclaireur" or cle == "pompe_petroliere":
                type_dico = "passive"
            else:
                type_dico = "active"
            # Si une unité n'a pas atteint son seuil.
            if valeur < self.seuils[type_dico][cle]:
                return False

        return True

    def ia_change_seuil(self):
        """Fonction permettant de changer le seuil pour toutes les unités alliées."""
        from random import randint

        for cle in self.seuils["active"].keys():
            # Ajoute entre 1 et 5 unités au lieu de doubler
            self.seuils["active"][cle] = self.max_seuil + randint(1, 5)

        self.seuils["passive"]["pompe_petroliere"] = self.max_seuil + randint(1, 5)

        self.max_seuil += randint(1, 5)

        # === Logs ===
        self.ia_log_action("change_seuil", self.current_scenario, 0, {"other": ("seuils", self.seuils)})

    def ia_get_distance(self, unit: Unit, unit2: Unit):
        """Fonction permettant d'avoir la distance entre deux unités

        Args:
            unit (Unit): La premiere unité
            unit2 (Unit): La seconde unité
        Returns :
            (float): La distance entre les deux unités
        """
        import math

        x, y = unit.position[0], unit.position[1]
        x2, y2 = unit2.position[0], unit2.position[1]

        return math.sqrt((x - x2) ** 2 + (y - y2) ** 2)

    def ia_is_near_oil_goal(self, player_oil: int, objectif: str):
        """Fonction permettant de savoir si un objectif est proche ou non en quantité de pétrole
        (on se base sur UNIT CONFIGS du global).

        Args:
            player_oil (int): La quantité de pétrole du joueur.
            objectif (str): Le nom de l'objet dans UNIT CONFIGS.

        Returns:
            (bool): True si l'objectif est proche, False sinon.
        """
        from src.config.units import UNIT_CONFIGS

        # Vérification de la présence de l'objectif dans la config
        if objectif not in UNIT_CONFIGS:
            return False

        # Si la différence est dans la marge
        return abs(player_oil - UNIT_CONFIGS[objectif]["cost"]) <= self.marges["oil"]

    def ia_is_near_from_base(self, unit: Unit, reducteur: int = 1):
        """Fonction permettant de savoir si une unité est proche de la base

        Args:
            unit (Unit): L'entité ciblé
            reducteur (int, optional): Le reducteur de la range. Defaults to 1.

        Returns:
            (bool): True si l'unité est proche de la base, False sinon
        """
        # Si la distance entre la base est l'entité est inférieur à sa range
        if unit.unit_type == "plateformePetroliere":  # Si l'unité est une plateforme pétrolière
            return False
        return self.ia_get_distance(unit, self) < self.range / reducteur

    def ia_tirage_pondere(self, probas: dict[str, float]) -> str:
        """Fonction permettant de faire un tirage pondérer sur les probas.

        Args:
            probas (dict[str, float]): Les probabilités.

        Returns:
            (str): La valeur de la probabilité.
        """
        from random import random

        r = random()
        cumul = 0.0
        for cle, p in probas.items():
            cumul += p
            if r < cumul:
                return cle
        return list(probas.keys())[-1]

    def ia_get_upgrade(self):
        """Détermine quelle amélioration l'IA peut acheter, en choisissant la moins chère.

        Returns:
            (str | None): Nom de l'amélioration la moins chère possible, ou None si toutes sont au max.
        """
        upgrades = self.game.overlay_menu.upgrades[self.team]
        pieces_attr = "piece_red" if self.team == "red" else "piece_green"
        pieces = getattr(self.game.hud, pieces_attr)

        choix = None
        cout_min = float("inf")

        for nom, upgrade in upgrades.items():
            level = upgrade["level"]

            # Si déjà au max, on passe
            # Les niveaux vont de 1 à 4, donc max = 4 (dernière valeur)
            if level >= len(upgrade["values"]):
                continue

            # Coût du prochain niveau (le niveau actuel est "level", donc le coût est à l'index "level")
            cost = upgrade["costs"][level]

            # Si on peut se le payer et que c'est le moins cher jusqu'à présent
            if pieces.count >= cost and cost < cout_min:
                cout_min = cost
                choix = nom

        # Si aucune upgrade possible, on indique qu'on est au max
        if choix is None:
            self.max_upgrade = True

        return choix

    def ia_do_upgrade(self, nom: str):
        """Effectue une amélioration si les ressources sont suffisantes.

        Args:
            nom (str): Nom de l'amélioration.
        """
        upgrade = self.game.overlay_menu.upgrades[self.team][nom]
        level = upgrade["level"]

        # Vérifie qu'on n'est pas déjà au niveau max
        if level >= len(upgrade["values"]):
            return

        cost = upgrade["costs"][level]

        # Sélection des pièces selon l'équipe
        pieces_attr = "piece_red" if self.team == "red" else "piece_green"
        pieces = getattr(self.game.hud, pieces_attr)

        if pieces.count >= cost:
            pieces.count -= cost
            upgrade["level"] += 1

    def ia_log_action(self, action_type: str, scenario: str, cost: int, details: dict = None):
        """Enregistre une action réelle de l'IA.

        Args:
            action_type (str): L'action qu'on log, spawn par exemple
            scenario (str): Le scénario dans lequel cela se produit
            cost (int): Le cout de l'action
            details (dict, optional): Les différents détails. Defaults to None.
        """
        log_entry = {
            "meta": {
                "time": self.game.hud.timer.get_time(),
                "generation": len(self.logs) + 1,
            },
            "decision": {
                "scenario": scenario,
                "reason": details.get("reason") if details else None,
            },
            "action": {
                "type": action_type,
                "unit": details.get("unit") if details else None,
                "cost": cost,
            },
            "context": {
                "oil_ally": int(self.nb_oil_ally + cost),
                "oil_enemy": self.nb_oil_enemy,
                "units_ally": self.units_ally_dico.copy(),
                "units_enemy": self.units_enemy_dico.copy(),
                "nb_units_ally": self.nb_units_ally,
                "nb_units_enemy": self.nb_units_enemy,
                "nb_pompe_ally": self.nb_pompe_ally,
                "nb_pompe_enemy": self.nb_pompe_enemy,
                "nb_island_hidden": self.nb_island_hidden,
            },
            "result": {
                "oil_ally_after": self.nb_oil_ally,
                "nb_units_ally_after": self.nb_units_ally - 1 if action_type == "spawn" else self.nb_units_ally,
            },
            "other": details.get("other") if details else None,
        }

        self.logs.append(log_entry)

    def ia_save_log(self, team: str):
        """Enregistre les actions de l'IA dans un fichier JSON.

        Args:
            team (str): L'équipe de l'IA qui demande les logs.
        """
        import json
        import os

        log_dir = os.path.join(".", "blue_frontline", "Class", "units", "IA")
        os.makedirs(log_dir, exist_ok=True)

        filename = f"logs_ia_{self.team}.json"
        filepath = os.path.join(log_dir, filename)
        info = {
            "time": self.game.hud.timer.get_time(),
            "team": self.team,
            "coefficients": self.coefficients,
            "probabilites": self.probabilites,
            "marges": self.marges,
            "seuil": self.seuils,
            "actions": self.logs,
        }
        if self.team:
            info["winner"] = self.team

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(info, f, indent=2, ensure_ascii=False)


class PlateformePetroliereRouge(PlateformePetroliere):
    def __init__(self, game: Game, objTiled: TiledObject, is_ia: bool = True):  # type: ignore
        """Constructeur de la classe PlateformePetroliereRouge.

        Args:
            game (Game): L'instance du jeu.
            objTiled (TiledObject): L'objet Tiled correspondant à la plateforme.
            is_ia (bool, optional): Indique si la plateforme est contrôlée par l'IA. Par défaut, True.
        """
        super().__init__(game, "red", objTiled, is_ia)


class PlateformePetroliereVerte(PlateformePetroliere):
    def __init__(self, game: Game, objTiled: TiledObject, is_ia: bool = True):  # type: ignore
        """Constructeur de la classe PlateformePetroliereVerte.

        Args:
            game (Game): L'instance du jeu.
            objTiled (TiledObject): L'objet Tiled correspondant à la plateforme.
            is_ia (bool, optional): Indique si la plateforme est contrôlée par l'IA. Par défaut, True.
        """
        super().__init__(game, "green", objTiled, is_ia)
