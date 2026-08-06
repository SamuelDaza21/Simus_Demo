"""
Módulo de inicialización centralizada de Pygame para SIMUS.MJN.
Este módulo asegura que pygame se inicialice UNA sola vez en todo el proyecto.
"""

import pygame

# Inicialización centralizada de pygame
pygame.init()
pygame.mixer.init()
pygame.font.init()

print("[INIT] Pygame inicializado correctamente en init_pygame.py")