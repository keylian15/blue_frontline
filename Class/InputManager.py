import pygame
import time

class InputManager:
    """Gestionnaire des entrées continues pour le jeu."""
    
    def __init__(self, game):
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
            self._handle_camera_movement(pressed)
            self._handle_hud_toggle(pressed)

        self._handle_unit_popup(pressed)
        self._handle_unit_popup_navigation(pressed)
        self._handle_shooting(pressed)

    
    def _handle_camera_movement(self, pressed):
        """Gère le déplacement de la caméra avec les touches directionnelles."""
        
        dx, dy = 0, 0
        if pressed[pygame.K_z]:  # Haut
            dy -= self.game.camera.camera_move
        if pressed[pygame.K_s]:  # Bas
            dy += self.game.camera.camera_move
        if pressed[pygame.K_q]:  # Gauche 
            dx -= self.game.camera.camera_move
        if pressed[pygame.K_d]:  # Droite
            dx += self.game.camera.camera_move
        
        # Déplacer la caméra seulement s'il y a un déplacement
        if dx or dy:  
            self.game.camera.move(dx, dy)
    
    def _handle_hud_toggle(self, pressed):
        """Gère l'affichage/masquage du HUD avec cooldown non-bloquant."""
        current_time = pygame.time.get_ticks()
        
        if pressed[pygame.K_h] :
            if current_time - self.last_hud_toggle_time > self.hud_toggle_cooldown:
                self.game.hud.switch()
                self.last_hud_toggle_time = current_time

    def _handle_unit_popup(self, pressed):
        if pressed[pygame.K_j]:
            self.game.hud.toggle_popup_team()
            time.sleep(0.2)
            
    def _handle_unit_popup_navigation(self, pressed):
        if pressed[pygame.K_LEFT]:
            self.game.hud.popup_selection = (self.game.hud.popup_selection - 1) % len(self.game.hud.unit_names)
            time.sleep(0.1)
        if pressed[pygame.K_RIGHT]:
            self.game.hud.popup_selection = (self.game.hud.popup_selection + 1) % len(self.game.hud.unit_names)
            time.sleep(0.1)

    def _handle_shooting(self, pressed):
        """Gère le tir avec la touche T avec cooldown strict de 1 seconde."""
        if pressed[pygame.K_t]:
            current_time = pygame.time.get_ticks()
            # Vérifier le cooldown au niveau de l'InputManager
            if current_time - self.last_shoot_time >= self.shoot_cooldown:
                self._trigger_shooting()
                self.last_shoot_time = current_time
    
    def _trigger_shooting(self):
        """Déclenche le tir si toutes les conditions sont remplies."""
        # Vérifier s'il y a une unité sélectionnée
        if not hasattr(self.game, 'selected_unit') or not self.game.selected_unit:
            print("Aucune unité sélectionnée")
            return
            
        selected_unit = self.game.selected_unit
        
        # Vérifier que l'unité sélectionnée est vivante
        if not selected_unit.is_alive:
            print("L'unité sélectionnée n'est pas vivante")
            return
            
        # Vérifier s'il y a des ennemis dans la portée
        if not hasattr(selected_unit, 'enemies_in_range') or not selected_unit.enemies_in_range:
            print("Aucun ennemi dans la portée")
            return
            
        # Obtenir l'ennemi le plus proche
        target = selected_unit.get_closest_enemy_in_range()
        if not target:
            print("Aucune cible valide trouvée")
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

            

