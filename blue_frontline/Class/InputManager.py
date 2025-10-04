import pygame
from Global import get_action_key

class InputManager:
    """Gestionnaire des entrées continues pour le jeu."""
    
    def __init__(self, game: "Game"):
        """Initialise le gestionnaire d'entrées avec une référence au jeu."""
        self.game = game
        self.last_hud_toggle_time = 0
        self.hud_toggle_cooldown = 200  # 200ms de cooldown
        self.last_shoot_time = 0  # Cooldown pour la touche T
        self.shoot_cooldown = 1000  # 1 seconde de cooldown pour la touche T
    
    def handle_continuous_input(self):
        """Gère les entrées continues (touches maintenues)."""
        
        pressed = pygame.key.get_pressed()
        if not self.game.paused:
            self.handle_camera_movement(pressed)
            self.handle_hud_toggle(pressed)

        self._handle_shooting(pressed)

    
    def handle_camera_movement(self, pressed: tuple[bool]):
        """Gère le déplacement de la caméra avec les touches directionnelles.

        Args:
            pressed (tuple[bool]): Un tuple de booléens indiquant si les touches sont enfoncées.
        """
        
        dx, dy = 0, 0
        if pressed[get_action_key("MOVE_UP")]:  # Haut
            dy -= self.game.camera.camera_move
        if pressed[get_action_key("MOVE_DOWN")]:  # Bas
            dy += self.game.camera.camera_move
        if pressed[get_action_key("MOVE_LEFT")]:  # Gauche
            dx -= self.game.camera.camera_move
        if pressed[get_action_key("MOVE_RIGHT")]:  # Droite
            dx += self.game.camera.camera_move
        
        # Déplacer la caméra seulement s'il y a un déplacement
        if dx or dy:  
            self.game.camera.move(dx, dy)
    
    def handle_hud_toggle(self, pressed: tuple[bool]):
        """Gère l'affichage/masquage du HUD avec cooldown non-bloquant.

        Args:
            pressed (tuple[bool]): Un tuple de booléens indiquant si les touches sont enfoncées.
        """
        
        current_time = pygame.time.get_ticks()

        if pressed[get_action_key("TOGGLE_HUD")]:
            if current_time - self.last_hud_toggle_time > self.hud_toggle_cooldown:
                self.game.hud.switch()
                self.last_hud_toggle_time = current_time

    def _handle_shooting(self, pressed: tuple[bool]):
        """Gère le tir avec la touche T avec cooldown strict de 1 seconde

        Args:
            pressed (tuple[bool]): Un tuple de booléens indiquant si les touches sont enfoncées.
        """
        
        if pressed[get_action_key("SHOOT")]:
            self.trigger_shooting()
    
    def trigger_shooting(self):
        """Déclenche le tir si toutes les conditions sont remplies."""
        
        # Vérifier s'il y a une unité sélectionnée
        if not hasattr(self.game, 'selected_unit') or not self.game.selected_unit:
            return
            
        selected_unit = self.game.selected_unit
        
        # Vérifier que l'unité sélectionnée est vivante
        if not selected_unit.is_alive:
            return
            
        # Vérifier s'il y a des ennemis dans la portée
        if not hasattr(selected_unit, 'enemies_in_range') or not selected_unit.enemies_in_range:
            return
            
        # Obtenir l'ennemi le plus proche
        target = selected_unit.get_closest_enemy_in_range()
        if not target:
            return
            
        # Vérifier le cooldown de tir
        current_time = pygame.time.get_ticks()
        if not selected_unit.can_shoot(current_time):
            return
        
        # Mettre à jour immédiatement le temps du dernier tir pour empêcher le spam
        selected_unit.last_shot_time = current_time
            
        # Tirer sur la cible en utilisant le système de combat
        if hasattr(self.game, 'combat_system'):
            projectile = self.game.combat_system.fire_projectile(selected_unit, target)