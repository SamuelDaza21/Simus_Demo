"""
Utilidades de dibujo reutilizables para la interfaz (pygame).
Centraliza botones con esquinas redondeadas y texto con borde/outline.
"""
from __future__ import annotations

import pygame
from core import config


def dibujar_boton_redondeado(
    superficie: pygame.Surface,
    rect: pygame.Rect,
    texto: str,
    fuente: pygame.font.Font,
    color_fondo: tuple,
    color_borde: tuple,
    color_texto: tuple,
    border_radius: int = 15,
    grosor_borde: int = 4,
) -> pygame.Rect:
    """Rectángulo redondeado relleno, borde y texto centrado."""
    pygame.draw.rect(superficie, color_fondo, rect, border_radius=border_radius)
    pygame.draw.rect(
        superficie, color_borde, rect, grosor_borde, border_radius=border_radius
    )
    texto_superficie = config.render_text(texto, fuente, color_texto)
    texto_rect = texto_superficie.get_rect(center=rect.center)
    superficie.blit(texto_superficie, texto_rect)
    return rect


def crear_superficie_texto_borde(
    texto: str,
    fuente: pygame.font.Font,
    color: tuple,
    color_borde: tuple,
    border_width: int = 2,
) -> pygame.Surface:
    """
    Superficie con texto y contorno grueso (outline), estilo tutorial/instrucciones.
    Si border_width <= 0, solo el texto sin borde.
    """
    base = fuente.render(texto, True, color)
    if border_width <= 0:
        return base
    w = base.get_width() + 2 * border_width
    h = base.get_height() + 2 * border_width
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for dx in range(-border_width, border_width + 1):
        for dy in range(-border_width, border_width + 1):
            if dx != 0 or dy != 0:
                surf.blit(
                    fuente.render(texto, True, color_borde),
                    (border_width + dx, border_width + dy),
                )
    surf.blit(base, (border_width, border_width))
    return surf


def blit_texto_borde_ligero(
    superficie: pygame.Surface,
    texto: str,
    fuente: pygame.font.Font,
    color_texto: tuple,
    color_borde: tuple,
    posicion: tuple,
    centrado_horizontal: bool = True,
) -> None:
    """
    Texto con borde en las 4 direcciones cardinales (menú carousel, etiquetas cortas).
    posicion: (x, y) con y como borde superior; si centrado_horizontal, x es el centro.
    """
    base = fuente.render(texto, True, color_texto)
    x = posicion[0] - (base.get_width() // 2 if centrado_horizontal else 0)
    y = posicion[1]
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        borde = fuente.render(texto, True, color_borde)
        superficie.blit(borde, (x + dx, y + dy))
    superficie.blit(base, (x, y))
