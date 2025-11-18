import os
import pygame
from Utils import resource_path


class ExplosionRenderer:
    """Gère le chargement et le rendu de l'image d'explosion (singleton-like).

    Appel:
        from Class.ExplosionRenderer import explosion_renderer
        explosion_renderer.render(explosion, screen, camera_offset, zoom)
    """

    def __init__(self):
        self.base_image = None
        self._load_base_image()

    def _load_base_image(self):
        # 1) Essayer le chemin absolu depuis le fichier actuel
        try:
            # Depuis Class/ExplosionRenderer.py -> blue_frontline/ -> assets/
            repo_explosion = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'assets', 'miscellaneous', 'png', 'explosion.png'
            )
            if os.path.exists(repo_explosion):
                self.base_image = pygame.image.load(repo_explosion)
                print(f"[ExplosionRenderer] Image chargée: {repo_explosion}")
                return
        except Exception as e:
            print(f"[ExplosionRenderer] Tentative 1 échouée: {e}")

        # 2) Essayer avec resource_path
        try:
            path = resource_path('assets/miscellaneous/png/explosion.png')
            self.base_image = pygame.image.load(path)
            print(f"[ExplosionRenderer] Image chargée via resource_path: {path}")
            return
        except Exception as e:
            print(f"[ExplosionRenderer] Tentative 2 échouée: {e}")

        # 3) Fallback : créer une image procédurale
        print("[ExplosionRenderer] Utilisation du fallback procédural")
        fallback = pygame.Surface((64, 64), pygame.SRCALPHA)
        pygame.draw.circle(fallback, (255, 150, 0), (32, 32), 32)
        pygame.draw.circle(fallback, (255, 255, 0), (32, 32), 16)
        self.base_image = fallback



    def render(self, explosion, screen: pygame.Surface, camera_offset: tuple[float, float], zoom: float):
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

        try:
            if self.base_image:
                scaled = pygame.transform.scale(self.base_image, (img_w, img_h))
            else:
                raise Exception('No base image')
        except Exception:
            # Créer une petite surface fallback
            scaled = pygame.Surface((img_w, img_h), pygame.SRCALPHA)
            pygame.draw.circle(scaled, (255, 150, 0), (img_w // 2, img_h // 2), img_w // 2)
            pygame.draw.circle(scaled, (255, 255, 0), (img_w // 2, img_h // 2), img_w // 3)

        screen.blit(scaled, (screen_x - scaled.get_width() // 2, screen_y - scaled.get_height() // 2))


# Exporter une instance prête à l'emploi
explosion_renderer = ExplosionRenderer()
