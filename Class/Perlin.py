from random import randint
from perlin_noise import PerlinNoise
import pygame

class Perlin:
    """Générateur de bruit de Perlin pour créer des îles procédurales."""
    
    def __init__(self, octave = 4, seed = None):
        """Initialisation du générateur de bruit de Perlin.
        octave : Nombre d'octaves pour le bruit de Perlin. (La compléxité du bruit)
        seed : Seed pour le générateur de bruit. Si None, une seed aléatoire sera générée.
        """

        # Si une seed n'est pas fournie, on en génère une aléatoire        
        if seed is None:
            seed = randint(0, 10_000)
        self.seed = seed

        # Octave détermine la "complexité" du bruit
        self.noise = PerlinNoise(octaves=octave, seed=seed)

    def generate_island(self, line, column, scale=30.0):
        """Génère une matrice représentant une île.
        line : Nombre de lignes de la matrice.
        column : Nombre de colonnes de la matrice.
        scale : Échelle pour le bruit de Perlin. Plus la valeur est grande, plus les variations sont douces.
        Retourne une matrice 2D où chaque élément est :
            0 : Eau profonde
            1 : Eau peu profonde
            2 : Ile
        """
        matrice = []
        for y in range(line):
            ligne = []
            for x in range(column):
                # PerlinNoise attend une liste de coordonnées normalisées
                val = self.noise([x/scale, y/scale])

                if val < -0.05:
                    tuile = 0  # Eau profonde
                elif val < 0.1:
                    tuile = 1  # Eau peu profonde
                else:
                    tuile = 2  # Ile

                ligne.append(tuile)
            matrice.append(ligne)
        return matrice

    def show_matrix(self, matrice):
        """Affiche la matrice dans la console pour visualiser l'île."""
        mapping = {
            0: "x",  # Eau profonde
            1: "░",  # Eau peu profonde
            2: "▓",  # Ile
        }
        for ligne in matrice:
            print("".join(mapping[val] for val in ligne))

    def render_matrix(self, matrice, tileset, tile_size, mapping):
        """
        Transforme une matrice de tuiles en surface Pygame. (Ile Brute)
        Args:
            matrice (list[list[int]]): matrice générée par Perlin
            tileset (list[pygame.Surface]): liste de tuiles
            tile_size (int): taille d'une tuile en pixels
            mapping (dict): association {val_matrice: index_tileset}
        Returns:
            pygame.Surface: surface représentant la carte
        """
        height = len(matrice)
        width = len(matrice[0])
        surface = pygame.Surface((width * tile_size, height * tile_size), pygame.SRCALPHA)

        for y in range(height):
            for x in range(width):
                val = matrice[y][x]
                tile_index = mapping[val]
                tile = tileset[tile_index]
                surface.blit(tile, (x * tile_size, y * tile_size))

        return surface

    def smooth_map(self, matrice, surface):
        """Méthode pour lisser la carte."""
        """
        2  3  4
        1  x  5
        8  7  6
        Algorithme de lissage simple :
            Pour chaque cellule, on regarde ses 8 voisins.
            
        
        
        """

if __name__ == "__main__":
    perlin = Perlin()
    perlin.show_matrix(perlin.generate_island(20, 50))