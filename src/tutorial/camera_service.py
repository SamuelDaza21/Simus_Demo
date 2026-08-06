"""
Acceso a captura y análisis facial: delega en ManejoCamara (sin duplicar MediaPipe).
"""
import cv2
import numpy as np


class CameraService:
    def __init__(self, camara):
        self.cam = camara

    def actualizar_seguimiento(self):
        """Una lectura completa: actualiza cursor, EAR, landmarks y último frame."""
        return self.cam.obtener_posicion_y_clic()

    def obtener_frame(self):
        return self.cam.obtener_frame()

    def obtener_bbox(self):
        return self.cam.obtener_bbox_rostro()

    def detectar_parpadeo(self):
        return self.cam.detectar_parpadeo()

    def brillo_promedio(self, frame):
        if frame is None:
            return 0.0
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return float(np.mean(gray))
