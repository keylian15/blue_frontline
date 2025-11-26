import pygame


class Camera(pygame.sprite.Sprite):
    """Classe pour gérer la caméra."""

    def __init__(self, x: int, y: int, screen_size: tuple[int, int], map_size: tuple[int, int]):
        """Fonction permettant d'initialiser la caméra.

        Args:
            x (int): La position x de la caméra.
            y (int): La position y de la caméra.
            screen_size (tuple[int, int]): La taille de l'écran.
            map_size (tuple[int, int]): La taille de la carte.
        """

        super().__init__()
        # Déplacement de la caméra (en pixels)
        self.camera_move = 8

        # === Limites de la caméra ===
        self.screen_width, self.screen_height = screen_size
        self.map_width, self.map_height = map_size

        # === Système de zoom ===
        self.zoom_level = 1.0  # Niveau de zoom actuel (1.0 = normal)
        self.max_zoom = 2.0  # Zoom maximum
        self.zoom_speed = 0.02  # Vitesse de zoom
        self.default_zoom = 1.0  # Zoom par défaut pour retour normal

        # Calculer le zoom minimum pour voir toute la map
        self.min_zoom = self.calculate_min_zoom_for_full_map()

        # Calculer les limites pour centrer la caméra
        self.update_zoom_limits()

        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        self.rect = self.image.get_rect()

        # Position initiale avec contraintes
        self.position = [
            max(self.min_x, min(self.max_x, x)),
            max(self.min_y, min(self.max_y, y)),
        ]

    def calculate_min_zoom_for_full_map(self):
        """Calcule le niveau de zoom minimum nécessaire pour voir toute la map.

        Returns:
            (float): Le niveau de zoom minimum.
        """

        # Calculer les ratios pour voir toute la map dans chaque dimension
        zoom_x = self.screen_width / self.map_width
        zoom_y = self.screen_height / self.map_height

        # Prendre le plus petit pour que toute la map soit visible
        min_zoom = min(zoom_x, zoom_y)

        # Ajouter une petite marge pour éviter les effets de bord
        min_zoom = min_zoom * 0.95

        return min_zoom

    def update_zoom_limits(self):
        """Met à jour les limites de la caméra en fonction du niveau de zoom."""

        # Calculer les limites en fonction du zoom
        effective_screen_width = self.screen_width / self.zoom_level
        effective_screen_height = self.screen_height / self.zoom_level

        self.min_x = effective_screen_width // 2
        self.max_x = self.map_width - effective_screen_width // 2
        self.min_y = effective_screen_height // 2
        self.max_y = self.map_height - effective_screen_height // 2

        # S'assurer que min <= max
        if self.min_x > self.max_x:
            center_x = self.map_width // 2
            self.min_x = self.max_x = center_x
        if self.min_y > self.max_y:
            center_y = self.map_height // 2
            self.min_y = self.max_y = center_y

    def zoom_in(self):
        """Zoom avant (augmente le niveau de zoom)."""

        if self.zoom_level < self.max_zoom:
            self.zoom_level = min(self.max_zoom, self.zoom_level + self.zoom_speed)
            self.update_zoom_limits()
            # Recalculer la position pour rester dans les limites
            self.position[0] = max(self.min_x, min(self.max_x, self.position[0]))
            self.position[1] = max(self.min_y, min(self.max_y, self.position[1]))

    def zoom_out(self):
        """Zoom arrière (diminue le niveau de zoom)."""

        if self.zoom_level > self.min_zoom:
            self.zoom_level = max(self.min_zoom, self.zoom_level - self.zoom_speed)
            self.update_zoom_limits()
            # Recalculer la position pour rester dans les limites
            self.position[0] = max(self.min_x, min(self.max_x, self.position[0]))
            self.position[1] = max(self.min_y, min(self.max_y, self.position[1]))

    def get_effective_screen_size(self):
        """Retourne la taille effective de l'écran selon le niveau de zoom.

        Returns:
            (tuple[int, int]): La taille effective de l'écran.
        """

        return (
            self.screen_width / self.zoom_level,
            self.screen_height / self.zoom_level,
        )

    def update(self):
        """Met à jour la position du rectangle de la caméra."""

        self.rect.center = self.position

    def move(self, dx: int, dy: int):
        """Déplace la caméra avec contraintes de limites.

        Args:
            dx (int): Déplacement horizontal.
            dy (int): Déplacement vertical.
        """

        # Adapter le déplacement au niveau de zoom
        adjusted_dx = dx / self.zoom_level
        adjusted_dy = dy / self.zoom_level

        # Nouvelle position proposée
        new_x = self.position[0] + adjusted_dx
        new_y = self.position[1] + adjusted_dy

        # Appliquer les contraintes
        self.position[0] = max(self.min_x, min(self.max_x, new_x))
        self.position[1] = max(self.min_y, min(self.max_y, new_y))

    def get_offset(self, screen_size: tuple[int, int]):
        """Calcule l'offset de la caméra pour le rendu.

        Args:
            screen_size (tuple[int, int]): Taille de l'écran.

        Returns:
            tuple[float, float]: Offset de la caméra.
        """

        return (
            self.position[0] - (screen_size[0] // 2) / self.zoom_level,
            self.position[1] - (screen_size[1] // 2) / self.zoom_level,
        )
