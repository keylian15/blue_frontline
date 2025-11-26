import pygame
from src.config.paths import EXPLOSION_IMAGE_PATH


class ExplosionRenderer:
    """Gère le chargement et le rendu de l'image d'explosion (singleton-like).

    Appel:
        from src.ExplosionRenderer import explosion_renderer
        explosion_renderer.render(explosion, screen, camera_offset, zoom)
    """

    def __init__(self):
        self.base_image = None
        self.load_base_image()

    def load_base_image(self):
        try:
            self.base_image = pygame.image.load(EXPLOSION_IMAGE_PATH)
        except Exception as e:
            # Fallback procédural si le chargement échoue (normalement ne devrait pas arriver)
            fallback = pygame.Surface((64, 64), pygame.SRCALPHA)
            pygame.draw.circle(fallback, (255, 150, 0), (32, 32), 32)
            pygame.draw.circle(fallback, (255, 255, 0), (32, 32), 16)
            self.base_image = fallback
            print(f"[ExplosionRenderer] Erreur: {e}, utilisation du fallback")

    def render(
        self,
        explosion,
        screen: pygame.Surface,
        camera_offset: tuple[float, float],
        zoom: float,
    ):
        """Rend une explosion donnée à l'écran.

        Args:
            explosion: objet ayant `position` (x,y), `size` (pixels), et `is_active`.
            screen: surface Pygame.
            camera_offset: tuple (x,y).
            zoom: float du zoom.
        """
        if not explosion.is_active:
            return

        # Position monde -> écran
        screen_x = (explosion.position[0] - camera_offset[0]) * zoom
        screen_y = (explosion.position[1] - camera_offset[1]) * zoom

        # Taille adaptée au zoom
        img_w = max(1, int(explosion.size * zoom))
        img_h = img_w

        scaled = None
        try:
            if self.base_image:
                scaled = pygame.transform.scale(self.base_image, (img_w, img_h))
            else:
                raise Exception("No base image")
        except Exception:
            # Fallback visuel
            scaled = pygame.Surface((img_w, img_h), pygame.SRCALPHA)
            pygame.draw.circle(scaled, (255, 150, 0), (img_w // 2, img_h // 2), img_w // 2)
            pygame.draw.circle(scaled, (255, 255, 0), (img_w // 2, img_h // 2), img_w // 3)

        if scaled:
            screen.blit(
                scaled,
                (
                    screen_x - scaled.get_width() // 2,
                    screen_y - scaled.get_height() // 2,
                ),
            )
