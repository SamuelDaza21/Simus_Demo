"""
Onboarding interactivo (cámara): delega flujo en TutorialManager y dibujo en TutorialView.
Internacionalización completa.
"""
import pygame
import core.config as config  # Importación modular para i18n dinámico
from core.shortcuts import procesar_atajos_globales
from tutorial.calibration_service import (
    CALIBRATION_FILE,
    TUTORIAL_COMPLETED_FILE,
    CalibrationService,
)
from tutorial.camera_service import CameraService
from tutorial.tutorial_manager import TutorialManager
from ui.tutorial_view import TutorialView


class Instrucciones:
    def __init__(self, camara, gestor_musica, ID_sesion):
        self.pantalla = pygame.display.get_surface()
        self.camara = camara
        self.gestor_musica = gestor_musica
        self.ID_sesion = ID_sesion
        self.ANCHO, self.ALTO = self.pantalla.get_size()

        self.calibration = CalibrationService(ID_sesion)
        self.camera_service = CameraService(camara)
        self.manager = TutorialManager(
            self.camera_service, self.calibration, self.ANCHO, self.ALTO
        )
        self.view = TutorialView(self.pantalla, self.ANCHO, self.ALTO)

        self.ejecutando = True
        self.paused = False
        self.tutorial_completed = self.calibration.is_completed()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.ejecutando = False
            elif event.type == pygame.KEYDOWN:
                acc = procesar_atajos_globales(event, self.camara)
                if acc == "recalibrar":
                    self.recalibrate()
                elif acc == "tutorial":
                    self.restart_tutorial()
                elif acc == "toggle_pausa":
                    self.toggle_pause()
                elif event.key == pygame.K_ESCAPE:
                    self.ejecutando = False

    def recalibrate(self):
        self.calibration.remove_calibration_file()
        try:
            self.camara.calibrado = False
            self.camara.calibrar()
        except Exception:
            pass
        self.restart_tutorial()

    def restart_tutorial(self):
        self.manager.reset()
        self.calibration._calibracion_guardada = False
        self.manager._calibracion_guardada = False

    def toggle_pause(self):
        self.paused = not self.paused
        try:
            self.camara.alternar_seguimiento_pausado()
        except Exception:
            pass

    def _play_step_sound(self, ok: bool):
        if not self.gestor_musica:
            return
        try:
            self.gestor_musica.reproducir_sonido("correcto" if ok else "incorrecto")
        except Exception:
            pass

    def ejecutar(self):
        if not self.camara.calibrado:
            try:
                self.camara.calibrar()
            except Exception:
                pass
        pygame.time.wait(300)

        clock = pygame.time.Clock()
        prev_step = 0

        # Mensajes de los pasos (traducidos dinámicamente)
        # Usamos un diccionario con las claves de traducción
        step_messages = {
            0: ["Iluminación", "Busca un lugar con buena luz."],
            1: ["Detección de rostro", "Centra tu cara en el recuadro."],
            2: ["Mueve la cabeza", "Controla el cursor con el movimiento."],
            3: ["Parpadeo", "Parpadea para hacer clic."],
            4: ["Calibración", "Guardando preferencias…"],
        }

        while self.ejecutando:
            self.handle_events()

            advanced = self.manager.update(self.paused)
            if advanced:
                self._play_step_sound(True)
                # El feedback_msg puede venir del manager; se puede traducir si es necesario
                # (si el manager produce textos fijos, deberías traducirlos allí también)
                if self.manager.feedback_msg.startswith("¡"):
                    pass
            if self.manager.done:
                self.ejecutando = False
                break

            if self.manager.step_index != prev_step:
                prev_step = self.manager.step_index
                # Obtener mensaje traducido según el paso actual
                if self.manager.step_index in step_messages:
                    # Traducir título y texto
                    titulo = config.traductor.t(step_messages[self.manager.step_index][0])
                    texto = config.traductor.t(step_messages[self.manager.step_index][1])
                    self.view.set_assistant([titulo, texto])
                else:
                    # Mensaje por defecto (cuando se sale del rango)
                    titulo = config.traductor.t("¡Genial!")
                    texto = config.traductor.t("Vamos al siguiente paso.")
                    self.view.set_assistant([titulo, texto])

            frame = self.camera_service.obtener_frame()
            cx, cy = self.camara.cursor_x, self.camara.cursor_y

            self.view.tick_transition(self.manager.step_index)
            self.view.draw(
                self.manager,
                frame,
                (cx, cy),
                self.paused,
                min(self.manager.step_index, len(self.manager.STEPS) - 1),
                len(self.manager.STEPS),
            )

            pygame.display.flip()
            clock.tick(30)

        return "menu_principal"

    def check_tutorial_completed(self):
        return self.calibration.is_completed()