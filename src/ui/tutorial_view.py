"""
Renderizado del onboarding: layout FIJO (barra arriba, cámara debajo, instrucciones abajo).
Transiciones suaves solo en opacidad del texto; el contenedor de cámara no se mueve.
Internacionalización completa.
"""
import pygame
import cv2
from core.config import (
    FONDO_PRINCIPAL,
    TEXTO,
    BORDE_BOTON,
    FONDO_BOTON,
    HOVER,
    VERDE,
    ROJO,
    SAVE_BG,
    SAVE_BORDER,
)
from core import config  # Para el traductor, render_text, etc.
from ui.dibujo_ui import crear_superficie_texto_borde
from logic.cursor import dibujar_cursor_unificado

# Claves de traducción para los nombres de los pasos (debe coincidir con los JSON)
NOMBRES_PASOS_CLAVES = (
    "Iluminación",
    "Rostro",
    "Movimiento",
    "Parpadeo",
    "Calibración",
)

class TutorialView:
    """Geometría calculada una vez; barra y vista de cámara no cambian de sitio entre pasos."""

    def __init__(self, pantalla, ancho, alto):
        self.pantalla = pantalla
        self.ancho = ancho
        self.alto = alto
        self.font_title = pygame.font.Font(None, int(alto * 0.048))
        self.font_sub = pygame.font.Font(None, int(alto * 0.028))
        self.font_small = pygame.font.Font(None, int(alto * 0.024))
        self._fondo = None
        self._load_fondo()

        self.transition = 1.0
        self.prev_step = 0
        self.progress_smooth = 0.0
        self.assistant_lines = [
            config.traductor.t("¡Bienvenido!"),
            config.traductor.t("Sigue las indicaciones del asistente.")
        ]

        mx = max(28, int(ancho * 0.04))
        self._mx = mx

        # —— Barra de progreso FIJA (parte superior) ——
        self._bar_top = 18
        self._bar_h = 16
        self.bar_rect = pygame.Rect(mx, self._bar_top, ancho - 2 * mx, self._bar_h)
        self._dots_row_y = self.bar_rect.bottom + 16
        self._dot_r_done = 7
        self._dot_r_current = 9
        self._dot_r_todo = 6

        # —— Cuadro de cámara FIJO (tamaño y posición constantes) ——
        self.cam_rect = pygame.Rect(0, 0, 0, 0)
        self._layout_camera()

        # —— Tarjeta de instrucciones FIJA (debajo de la cámara) ——
        card_h = max(100, int(alto * 0.13))
        gap_below_cam = 18
        card_top = self.cam_rect.bottom + gap_below_cam
        self.card_rect = pygame.Rect(mx, card_top, ancho - 2 * mx, card_h)

        # Panel inferior fijo (feedback + atajos)
        self._footer_h = 96
        self.footer_rect = pygame.Rect(
            mx, alto - self._footer_h - 12, ancho - 2 * mx, self._footer_h
        )
        max_card_bottom = self.footer_rect.top - 10
        if self.card_rect.bottom > max_card_bottom:
            self.card_rect.height = max(72, max_card_bottom - self.card_rect.top)

        # Suavizado para tracking facial (opcional)
        self._smooth_face = None

    def _layout_camera(self):
        """Define rect de preview; no depende del paso actual."""
        available_below_dots = self.alto - self._dots_row_y - 24
        # Proporción ~ 4:3 estable
        cam_w = int(min(self.ancho * 0.56, 700))
        cam_h = int(cam_w * 0.72)
        if cam_h > available_below_dots * 0.62:
            cam_h = int(available_below_dots * 0.62)
            cam_w = int(cam_h / 0.72)
        self.cam_rect.width = cam_w
        self.cam_rect.height = cam_h
        self.cam_rect.centerx = self.ancho // 2
        # Top fijo: siempre el mismo offset bajo los dots
        self.cam_rect.top = self._dots_row_y + self._dot_r_current + 18

    def _load_fondo(self):
        try:
            img = pygame.image.load(FONDO_PRINCIPAL)
            self._fondo = pygame.transform.scale(img, (self.ancho, self.alto))
        except Exception:
            self._fondo = None

    def set_assistant(self, lines):
        """Recibe líneas ya traducidas (desde instrucciones.py)."""
        self.assistant_lines = lines[:3]

    def tick_transition(self, step_index: int):
        if step_index != self.prev_step:
            self.transition = 0.0
            self.prev_step = step_index
        self.transition = min(1.0, self.transition + 0.06)

    def _glass_card(self, rect: pygame.Rect, alpha=195):
        surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        surf.fill((22, 32, 48, alpha))
        pygame.draw.rect(surf, (255, 255, 255, 35), surf.get_rect(), width=2, border_radius=18)
        self.pantalla.blit(surf, rect.topleft)

    def _blit_faded(self, surf: pygame.Surface, pos_rect: pygame.Rect):
        """Transición suave solo de opacidad, sin mover layout."""
        if self.transition >= 0.99:
            self.pantalla.blit(surf, pos_rect)
            return
        faded = surf.copy()
        faded.set_alpha(int(max(0, min(255, 255 * self.transition))))
        self.pantalla.blit(faded, pos_rect)

    def _draw_progress_bar(self, manager, step_index: int, total_steps: int):
        bx, by, bw, bh = self.bar_rect.x, self.bar_rect.y, self.bar_rect.w, self.bar_rect.h
        pygame.draw.rect(self.pantalla, SAVE_BG, self.bar_rect, border_radius=10)
        pygame.draw.rect(self.pantalla, SAVE_BORDER, self.bar_rect, 2, border_radius=10)

        target = (
            step_index + (manager.success_frames / max(1, manager.min_success_frames))
        ) / total_steps
        self.progress_smooth += (target - self.progress_smooth) * 0.07
        fw = int(bw * min(1.0, max(0.0, self.progress_smooth)))
        col_fill = (72, 168, 110) if manager.feedback_kind == "ok" else (88, 140, 210)
        if fw > 4:
            inner = pygame.Rect(bx + 3, by + 3, fw - 6, bh - 6)
            pygame.draw.rect(self.pantalla, col_fill, inner, border_radius=7)

        for i in range(total_steps):
            cx = bx + (i + 0.5) * (bw / total_steps)
            cy = self._dots_row_y
            done = i < step_index
            cur = i == step_index
            r = self._dot_r_current if cur else (self._dot_r_done if done else self._dot_r_todo)
            color = VERDE if done else (HOVER if cur else (70, 75, 88))
            pygame.draw.circle(self.pantalla, color, (int(cx), cy), r)
            if cur:
                pygame.draw.circle(self.pantalla, (255, 255, 255), (int(cx), cy), r, 2)
            num = self.font_small.render(str(i + 1), True, (190, 195, 205))
            nr = num.get_rect(midtop=(int(cx), cy + r + 4))
            self.pantalla.blit(num, nr)

    def draw(
        self,
        manager,
        frame,
        cursor_xy,
        paused: bool,
        step_index: int,
        total_steps: int,
    ):
        if self._fondo:
            self.pantalla.blit(self._fondo, (0, 0))
        else:
            self.pantalla.fill((18, 26, 40))

        overlay = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
        overlay.fill((8, 12, 22, 100))
        self.pantalla.blit(overlay, (0, 0))

        # 1) Barra + dots
        self._draw_progress_bar(manager, step_index, total_steps)

        # 2) Cámara
        cr = self.cam_rect
        if frame is not None:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            surf = pygame.surfarray.make_surface(rgb.swapaxes(0, 1))
            surf = pygame.transform.scale(surf, (cr.w, cr.h))
            self.pantalla.blit(surf, cr.topleft)
        else:
            pygame.draw.rect(self.pantalla, (12, 14, 20), cr, border_radius=12)

        # ===== TRACKING CIRCULAR AVANZADO =====
        bbox = manager.camera.obtener_bbox()
        if bbox and frame is not None:
            x, y, w, h = bbox
            fh, fw = frame.shape[0], frame.shape[1]
            if fw > 0 and fh > 0:
                sx = cr.w / fw
                sy = cr.h / fh
                px = cr.x + int(x * sx)
                py = cr.y + int(y * sy)
                pw = max(1, int(w * sx))
                ph = max(1, int(h * sy))
                target_cx = px + pw // 2
                target_cy = py + ph // 2
                target_r = int(min(pw, ph) / 2)

                if self._smooth_face is None:
                    self._smooth_face = [target_cx, target_cy, target_r]

                alpha = 0.15
                self._smooth_face[0] += (target_cx - self._smooth_face[0]) * alpha
                self._smooth_face[1] += (target_cy - self._smooth_face[1]) * alpha
                self._smooth_face[2] += (target_r - self._smooth_face[2]) * alpha

                cx = int(self._smooth_face[0])
                cy = int(self._smooth_face[1])
                rx = int(self._smooth_face[2] * 1.2)
                ry = int(self._smooth_face[2] * 1.5)

                ok = manager.feedback_kind == "ok"
                base_color = (0, 210, 110) if ok else (240, 85, 85)

                t = pygame.time.get_ticks() / 300.0
                pulse = int(3 * (1 + pygame.math.Vector2(1, 0).rotate(t * 60).x))
                rx_pulse = rx + pulse
                ry_pulse = ry + pulse

                ellipse_glow = pygame.Rect(cx - rx_pulse, cy - ry_pulse, rx_pulse*2, ry_pulse*2)
                for i in range(3):
                    glow_rect = ellipse_glow.inflate(i*12, i*12)
                    glow_surf = pygame.Surface((glow_rect.w, glow_rect.h), pygame.SRCALPHA)
                    pygame.draw.ellipse(
                        glow_surf,
                        (*base_color, 40 - i*10),
                        glow_surf.get_rect()
                    )
                    self.pantalla.blit(glow_surf, glow_rect.topleft)

                ellipse_rect = pygame.Rect(cx - rx, cy - ry, rx * 2, ry * 2)
                fill_surf = pygame.Surface((rx * 2, ry * 2), pygame.SRCALPHA)
                pygame.draw.ellipse(fill_surf, (*base_color, 80), fill_surf.get_rect())
                self.pantalla.blit(fill_surf, ellipse_rect.topleft)

                ellipse_pulse = pygame.Rect(cx - rx_pulse, cy - ry_pulse, rx_pulse * 2, ry_pulse * 2)
                pygame.draw.ellipse(self.pantalla, base_color, ellipse_pulse, 3)
                pygame.draw.ellipse(self.pantalla, (255, 255, 255), ellipse_pulse, 1)

        pygame.draw.rect(self.pantalla, BORDE_BOTON, cr, 4, border_radius=14)

        # 3) Tarjeta de instrucciones
        self._glass_card(self.card_rect, alpha=200)
        # Nombre del paso traducido
        if step_index < len(NOMBRES_PASOS_CLAVES):
            nombre_paso = config.traductor.t(NOMBRES_PASOS_CLAVES[step_index])
        else:
            nombre_paso = config.traductor.t("Tutorial")
        title = crear_superficie_texto_borde(nombre_paso, self.font_title, TEXTO, BORDE_BOTON, 2)
        title_pos = title.get_rect(midtop=(self.card_rect.centerx, self.card_rect.y + 14))
        self._blit_faded(title, title_pos)

        sub_texto = config.traductor.t("Alinea tu rostro con la cámara y completa cada paso.")
        sub = crear_superficie_texto_borde(
            sub_texto,
            self.font_sub,
            (228, 230, 238),
            BORDE_BOTON,
            1,
        )
        sub_pos = sub.get_rect(midtop=(self.card_rect.centerx, self.card_rect.y + 52))
        self._blit_faded(sub, sub_pos)

        # 4) Footer fijo
        self._glass_card(self.footer_rect, alpha=205)
        fb = crear_superficie_texto_borde(
            manager.feedback_msg,  # este viene del manager, debería estar traducido o ser dinámico; si no, traducir allí
            self.font_sub,
            FONDO_BOTON if manager.feedback_kind == "warn" else TEXTO,
            BORDE_BOTON,
            1,
        )
        self.pantalla.blit(fb, fb.get_rect(center=(self.footer_rect.centerx, self.footer_rect.centery - 10)))
        hint_texto = config.traductor.t("Ctrl+R recalibrar · Ctrl+T reiniciar · Ctrl+P pausar seguimiento · ESC salir")
        hint = crear_superficie_texto_borde(
            hint_texto,
            self.font_small,
            (160, 168, 180),
            BORDE_BOTON,
            1,
        )
        self.pantalla.blit(hint, hint.get_rect(midbottom=(self.footer_rect.centerx, self.footer_rect.bottom - 8)))

        if paused:
            pv = crear_superficie_texto_borde(config.traductor.t("PAUSADO"), self.font_title, ROJO, BORDE_BOTON, 2)
            self.pantalla.blit(pv, pv.get_rect(center=(self.ancho // 2, self.alto // 2)))

        cx, cy = cursor_xy
        try:
            dibujar_cursor_unificado(
                self.pantalla, cx, cy, modo_ocular=True, ancho=self.ancho, alto=self.alto
            )
        except Exception:
            pygame.draw.circle(self.pantalla, (255, 200, 80), (int(cx), int(cy)), 12, 2)