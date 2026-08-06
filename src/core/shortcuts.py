"""
Atajos globales (Ctrl+R / Ctrl+T / Ctrl+P) para pantallas con bucle pygame.
Devuelve un string de destino o None si no aplica.
"""
import pygame


def procesar_atajos_globales(event, camara):
    """
    Procesa un evento KEYDOWN. Requiere modificador Ctrl.
    Retorna: None | "recalibrar" | "tutorial" | "toggle_pausa"
    """
    if event.type != pygame.KEYDOWN:
        return None
    if not (event.mod & pygame.KMOD_CTRL):
        return None
    if event.key == pygame.K_r:
        return "recalibrar"
    if event.key == pygame.K_t:
        return "tutorial"
    if event.key == pygame.K_p:
        return "toggle_pausa"
    return None


def aplicar_atajo_camara(accion, camara):
    """Ejecuta efecto en ManejoCamara (recalibrar / pausa de seguimiento)."""
    if accion == "recalibrar":
        try:
            camara.calibrado = False
            camara.calibrar()
        except Exception:
            pass
        return
    if accion == "toggle_pausa":
        try:
            camara.alternar_seguimiento_pausado()
        except Exception:
            pass
