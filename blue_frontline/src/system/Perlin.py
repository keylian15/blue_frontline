from __future__ import annotations

from random import randint
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import IslandSprite

import pygame
from perlin_noise import PerlinNoise
from src.config.mapping import MAPPING, MASK_MAPPING


class Perlin:
    """Générateur de bruit de Perlin pour créer des îles procédurales."""

    def __init__(self, octave: int = 4, seed: int = None):
        """Initialisation du générateur de bruit de Perlin.

        Args:
            octave (int, optional): Nombre d'octaves pour le bruit de Perlin. (La compléxité du bruit) . Defaults to 4.
            seed (int, optional): Seed pour le générateur de bruit. Si None, une seed aléatoire sera générée.. \
                Defaults to None.
        """

        # Si une seed n'est pas fournie, on en génère une aléatoire
        if seed is None:
            seed = randint(0, 10_000)
        self.seed = seed

        # Octave détermine la "complexité" du bruit
        self.noise = PerlinNoise(octaves=octave, seed=seed)

    def generate_island(self, line: int, column: int, scale: float = 30.0):
        """Génère une matrice de hauteur pour une île procédurale.

        Args:
            line (int): Nombre de lignes de la matrice.
            column (int): Nombre de colonnes de la matrice.
            scale (float, optional): Echelle pour le bruit de Perlin, plus la valeur est grande, plus les variations \
                sont douces. Defaults to 30.0.

        Returns:
            (list[list[int]]): Matrice de hauteur (line * column).
        """

        matrice = []
        for y in range(line):
            ligne = []
            for x in range(column):
                # PerlinNoise attend une liste de coordonnées normalisées
                val = self.noise([x / scale, y / scale])

                if val < -0.05:
                    tuile = 0  # Eau profonde
                elif val < 0.1:
                    tuile = 1  # Eau peu profonde
                else:
                    tuile = 2  # Ile

                ligne.append(tuile)
            matrice.append(ligne)
        return matrice

    def get_matrix_value(self, matrice: list[list[int]], y: int, x: int):
        """Retourne la valeur de la matrice aux coordonnées (y, x).
        Si les coordonnées sont hors limites, retourne 1 (eau peu profonde).


        Args:
            matrice (list[list[int]]): Matrice de hauteur (line * column).
            y (int): Coordonnée y.
            x (int): Coordonnée x.

        Returns:
            (int): Valeur de la matrice aux coordonnées (y, x).
        """

        height = len(matrice)
        width = len(matrice[0])

        if y < 0 or y >= height or x < 0 or x >= width:
            return 1
        return matrice[y][x]

    def update_mask(self, matrice: list[list[int]], x: int, y: int, zone_recherche: int) -> int:
        """Fonction permettant de mettre à jour le mask binaire pour la sélection des tuiles.

        Args:
            matrice (list[list[int]]): Matrice de hauteur (line * column).
            x (int): Coordonnée x.
            y (int): Coordonnée y.
            zone_recherche (int): Valeur pour la zone de recherche.

        Returns:
            (int): Mask binaire mis à jour.
        """

        # Voir Global.py pour le MASK_MAPPING.
        mask = 0

        # Initialisation des voisins (booléens)
        voisin_gauche = self.get_matrix_value(matrice, y, x - 1) == zone_recherche
        voisin_droite = self.get_matrix_value(matrice, y, x + 1) == zone_recherche
        voisin_haut = self.get_matrix_value(matrice, y - 1, x) == zone_recherche
        voisin_bas = self.get_matrix_value(matrice, y + 1, x) == zone_recherche
        voisin_haut_gauche = self.get_matrix_value(matrice, y - 1, x - 1) == zone_recherche
        voisin_haut_droite = self.get_matrix_value(matrice, y - 1, x + 1) == zone_recherche
        voisin_bas_gauche = self.get_matrix_value(matrice, y + 1, x - 1) == zone_recherche
        voisin_bas_droite = self.get_matrix_value(matrice, y + 1, x + 1) == zone_recherche

        # Initialisation des masques pour les bits correspondants
        mask_voisin_haut = 1
        mask_voisin_droite = 2
        mask_voisin_bas = 4
        mask_voisin_gauche = 8
        mask_voisin_haut_gauche = 16
        mask_voisin_haut_droite = 32
        mask_voisin_bas_gauche = 64
        mask_voisin_bas_droite = 128

        # Algorithme de mise à jour du mask binaire (Voir tiles_bitmask.xlsx)
        if voisin_haut:
            mask |= mask_voisin_haut

            if voisin_droite:
                mask |= mask_voisin_droite

                if voisin_bas:
                    mask |= mask_voisin_bas

                    if voisin_gauche:
                        mask |= mask_voisin_gauche

                elif voisin_gauche:
                    mask |= mask_voisin_gauche

                elif voisin_bas_gauche:
                    mask |= mask_voisin_bas_gauche

            elif voisin_bas:
                mask |= mask_voisin_bas

                if voisin_gauche:
                    mask |= mask_voisin_gauche

            elif voisin_gauche:
                mask |= mask_voisin_gauche

                if voisin_bas_droite:
                    mask |= mask_voisin_bas_droite

            elif voisin_bas_gauche:
                mask |= mask_voisin_bas_gauche

                if voisin_bas_droite:
                    mask |= mask_voisin_bas_droite

            elif voisin_bas_droite:
                mask |= mask_voisin_bas_droite

        elif voisin_droite:
            mask |= mask_voisin_droite

            if voisin_bas:
                mask |= mask_voisin_bas

                if voisin_gauche:
                    mask |= mask_voisin_gauche

                elif voisin_haut_gauche:
                    mask |= mask_voisin_haut_gauche

            elif voisin_gauche:
                mask |= mask_voisin_gauche

            elif voisin_haut_gauche:
                mask |= mask_voisin_haut_gauche

                if voisin_bas_gauche:
                    mask |= mask_voisin_bas_gauche

            elif voisin_bas_gauche:
                mask |= mask_voisin_bas_gauche

        elif voisin_bas:
            mask |= mask_voisin_bas

            if voisin_gauche:
                mask |= mask_voisin_gauche

                if voisin_haut_droite:
                    mask |= mask_voisin_haut_droite

            elif voisin_haut_gauche:
                mask |= mask_voisin_haut_gauche

                if voisin_haut_droite:
                    mask |= mask_voisin_haut_droite

            elif voisin_haut_droite:
                mask |= mask_voisin_haut_droite

        elif voisin_gauche:
            mask |= mask_voisin_gauche

            if voisin_haut_droite:
                mask |= mask_voisin_haut_droite

                if voisin_bas_droite:
                    mask |= mask_voisin_bas_droite

            elif voisin_bas_droite:
                mask |= mask_voisin_bas_droite

        elif voisin_haut_gauche:
            mask |= mask_voisin_haut_gauche

            if voisin_haut_droite:
                mask |= mask_voisin_haut_droite

                if voisin_bas_gauche:
                    mask |= mask_voisin_bas_gauche

                    if voisin_bas_droite:
                        mask |= mask_voisin_bas_droite

                elif voisin_bas_droite:
                    mask |= mask_voisin_bas_droite

            elif voisin_bas_gauche:
                mask |= mask_voisin_bas_gauche

                if voisin_bas_droite:
                    mask |= mask_voisin_bas_droite

            elif voisin_bas_droite:
                mask |= mask_voisin_bas_droite

        elif voisin_haut_droite:
            mask |= mask_voisin_haut_droite

            if voisin_bas_gauche:
                mask |= mask_voisin_bas_gauche

                if voisin_bas_droite:
                    mask |= mask_voisin_bas_droite

            elif voisin_bas_droite:
                mask |= mask_voisin_bas_droite

        elif voisin_bas_gauche:
            mask |= mask_voisin_bas_gauche

            if voisin_bas_droite:
                mask |= mask_voisin_bas_droite

        elif voisin_bas_droite:
            mask |= mask_voisin_bas_droite

        return mask

    def smooth_map(self, matrice: list[list[int]], tilesets: list):
        """Génère une surface avec transitions (edges, corners, L-shapes).

        Args:
            matrice (list[list[int]]): matrice générée par Perlin.
            tilesets (list): liste de tilesets par biome. ([deep_tileset, shallow_tileset, island_tileset])

        Returns:
            (pygame.Surface): Surface avec les transitions.
        """

        height = len(matrice)
        width = len(matrice[0])
        surface = pygame.Surface((width * 32, height * 32), pygame.SRCALPHA)

        # On parcour toutes les cases de la matrice de Perlin
        for y in range(height):
            for x in range(width):
                # Valeurs possibles : 0 (terre), 1 (eau peu profonde), 2 (île)
                val = matrice[y][x]
                # Les différents tilesets (terre, eau peu profonde, île)
                spritesheet = tilesets[val]

                # Détermine quel type de voisin rechercher pour les transitions
                # Cas spécial : eau peu profonde utilise toujours le centre
                if val == 1:
                    tile_index = MAPPING["full"]
                else:
                    if val == 2:  # île
                        zone_recherche = 1  # recherche l'eau peu profonde autour
                    else:  # val == 0, eau profonde
                        zone_recherche = 1  # recherche l'eau peu profonde autour

                    # On utilise un mask pour du binaire afin de savoir quelle tuile prendre.
                    mask = self.update_mask(matrice, x, y, zone_recherche)

                    # Lors de la séléction du full on a le choix entre plusieurs tuiles
                    if mask == 0:  # Full
                        from random import choice

                        liste_full = [
                            MAPPING["full"],
                            MAPPING["full_1"],
                            MAPPING["full_2"],
                        ]
                        tile_index = choice(liste_full)
                    else:
                        tile_index = MASK_MAPPING.get(mask, MAPPING["full"])
                tile = spritesheet[tile_index]
                surface.blit(tile, (x * 32, y * 32))

        return surface

    @staticmethod
    def get_zone_type(x_pixel: int, y_pixel: int, matrice: list[list[int]], island: IslandSprite) -> int:
        """Retourne le type de zone à partir des coordonnées en pixels.

        Args:
            x_pixel (int): Coordonnée x en pixels.
            y_pixel (int): Coordonnée y en pixels.
            matrice (list[list[int]]): Matrice de valeurs (Perlin).
            island (IslandSprite): La zone quantique.

        Returns:
            (int): Type de zone (0 = eau profonde, 1 = eau peu profonde, 2 = île, 3 = terre).
        """
        # Conversion monde -> local
        local_x = x_pixel - island.rect.x
        local_y = y_pixel - island.rect.y

        tile_x = int(local_x // 32)
        tile_y = int(local_y // 32)

        if 0 <= tile_y < len(matrice) and 0 <= tile_x < len(matrice[0]):
            return matrice[tile_y][tile_x]
        return -1  # en dehors de la map
