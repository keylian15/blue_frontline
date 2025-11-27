import pygame

# === Temps ===
FPS = 60
TIME_STEP = 1000  # en ms => 1 seconde

# Vitesses de temps disponibles
TIME_SPEEDS = [1, 2, 4, 0.5]

# === Événements Pygame ===
PETROLE_EVENT = pygame.USEREVENT + 1
TIMER_EVENT = pygame.USEREVENT + 2
