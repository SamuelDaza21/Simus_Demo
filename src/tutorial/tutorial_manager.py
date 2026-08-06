"""
Máquina de estados del onboarding: valida pasos con la cámara y CalibrationService.
Internacionalización completa.
"""
import pygame
import core.config as config


class TutorialManager:
    STEPS = (
        "iluminacion",
        "rostro",
        "movimiento",
        "parpadeo",
        "calibracion",
    )

    def __init__(self, camera_service, calibration_service, ancho_pantalla, alto_pantalla):
        self.camera = camera_service
        self.calibration = calibration_service
        self.ancho = ancho_pantalla
        self.alto = alto_pantalla
        self.step_index = 0
        self.success_frames = 0
        self.min_success_frames = 14
        self.movement_positions = []
        self.blink_start_ms = None
        self.blink_count = 0
        self._last_blinking = False
        self.feedback_msg = config.traductor.t("Detectando")
        self.feedback_kind = "info"
        self.shake = 0.0
        self._calibracion_guardada = False

    def reset(self):
        self.step_index = 0
        self.success_frames = 0
        self.movement_positions = []
        self.blink_start_ms = None
        self.blink_count = 0
        self._last_blinking = False
        self.feedback_msg = config.traductor.t("Detectando")
        self.feedback_kind = "info"
        self.shake = 0.0
        self._calibracion_guardada = False

    @property
    def done(self) -> bool:
        return self.step_index >= len(self.STEPS)

    def _set_feedback(self, msg, kind="info"):
        self.feedback_msg = msg
        self.feedback_kind = kind

    def _validate_step(self) -> bool:
        step = self.STEPS[self.step_index]
        frame = self.camera.obtener_frame()

        # ---- Paso 1: Iluminación ----
        if step == "iluminacion":
            avg = self.camera.brillo_promedio(frame)
            ok = avg > 100
            estado = config.traductor.t("Correcto") if ok else config.traductor.t("Mejora la luz")
            # Plantilla: "Brillo: {avg:.0f} — {estado}"
            plantilla = config.traductor.t("Brillo_valor")
            msg = plantilla.format(avg=avg, estado=estado)
            self._set_feedback(msg, "ok" if ok else "warn")
            return ok

        # ---- Paso 2: Rostro ----
        if step == "rostro":
            bbox = self.camera.obtener_bbox()
            if not bbox or frame is None:
                self._set_feedback(config.traductor.t("No se detecta rostro"), "warn")
                return False
            x, y, w, h = bbox
            fh, fw = frame.shape[0], frame.shape[1]
            cx, cy = x + w / 2, y + h / 2
            ok = abs(cx - fw / 2) < 0.18 * fw and abs(cy - fh / 2) < 0.22 * fh
            if ok:
                self._set_feedback(config.traductor.t("Rostro centrado"), "ok")
            else:
                self._set_feedback(config.traductor.t("Centra el rostro en el marco"), "warn")
            return ok

        # ---- Paso 3: Movimiento ----
        if step == "movimiento":
            try:
                x, y, _ = self.camera.actualizar_seguimiento()
            except Exception:
                x, y = self.ancho // 2, self.alto // 2
            self.movement_positions.append((x, y))
            if len(self.movement_positions) > 40:
                self.movement_positions.pop(0)
            if len(self.movement_positions) >= 20:
                xs = [p[0] for p in self.movement_positions]
                ys = [p[1] for p in self.movement_positions]
                ok = (max(xs) - min(xs)) > 50 or (max(ys) - min(ys)) > 50
            else:
                ok = False
            if ok:
                self._set_feedback(config.traductor.t("Movimiento detectado"), "ok")
            else:
                self._set_feedback(config.traductor.t("Mueve la cabeza para mover el cursor"), "info")
            return ok

        # ---- Paso 4: Parpadeo ----
        if step == "parpadeo":
            now = pygame.time.get_ticks()
            if self.blink_start_ms is None:
                self.blink_start_ms = now
                self.blink_count = 0
                self._last_blinking = False
            elapsed = (now - self.blink_start_ms) / 1000.0
            blink_now = self.camera.detectar_parpadeo()
            if blink_now and not self._last_blinking:
                self.blink_count += 1
            self._last_blinking = blink_now
            if elapsed >= 5.0:
                ok = self.blink_count >= 3
                if ok:
                    self._set_feedback(config.traductor.t("Parpadeos registrados"), "ok")
                else:
                    self._set_feedback(config.traductor.t("Necesitas al menos 3 parpadeos"), "warn")
                return ok
            # Mensaje dinámico: "Parpadeos: X/3 — Ys"
            plantilla = config.traductor.t("Parpadeos_contador")
            msg = plantilla.format(count=self.blink_count, segundos=int(5 - elapsed))
            self._set_feedback(msg, "info")
            return False

        # ---- Paso 5: Calibración ----
        if step == "calibracion":
            if not self._calibracion_guardada:
                cam = self.camera.cam
                self.calibration.save_calibration(
                    getattr(cam, "sensibilidadO", 1.0),
                    getattr(cam, "UMBRAL_EAR", 0.21),
                    (self.ancho // 2, self.alto // 2),
                    rango_cabeza_x=getattr(cam, "rango_cabeza_x", None),
                    rango_cabeza_y=getattr(cam, "rango_cabeza_y", None),
                    centro_cabeza=getattr(cam, "centro_cabeza", None),
                )
                self._calibracion_guardada = True
            self._set_feedback(config.traductor.t("Configuracion guardada"), "ok")
            return True

        return False

    def update(self, paused: bool):
        """Una iteración de lógica. Devuelve True si se avanzó de paso."""
        if paused or self.done:
            return False

        if self.step_index >= len(self.STEPS):
            return False

        if self.STEPS[self.step_index] != "movimiento":
            self.camera.actualizar_seguimiento()

        ok = self._validate_step()
        if ok:
            self.success_frames += 1
            self.shake = 0.0
        else:
            self.success_frames = 0
            self.shake = min(12.0, self.shake + 0.8)

        need = 1 if self.STEPS[self.step_index] == "calibracion" else self.min_success_frames

        if self.success_frames >= need:
            self.step_index += 1
            self.success_frames = 0
            self.movement_positions = []
            self.blink_start_ms = None
            self.blink_count = 0
            self._last_blinking = False
            return True
        return False