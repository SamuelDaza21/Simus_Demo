import cv2
import mediapipe as mp
import pygame
import math
import sys
import time
import numpy as np
from collections import deque
from google.protobuf import message_factory
from google.protobuf import symbol_database
from core.config import *
from api.APICliente import APICliente

# Ajuste para Protobuf: evita warning sobre GetPrototype en futuras versiones
try:
    db = symbol_database.Default()
    if hasattr(db, 'GetPrototype') and hasattr(message_factory, 'GetMessageClass'):
        db.GetPrototype = message_factory.GetMessageClass
except Exception:
    pass




class ManejoCamara:
    _instancia = None

    def __new__(cls, *args, **kwargs):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
        return cls._instancia

    def __init__(self, ancho=1620, alto=900, modo_ocular=None, sesion_id=None):
        if getattr(self, '_inicializado', False):
            return

        self._inicializado = True
        self.ancho = ancho
        self.alto = alto
        self.modo_ocular = True
        self.clic_sostenido = False
        self.tiempo_inicio_clic = 0
        self.tiempo_ultimo_parpadeo = 0
        self.duracion_clic_sostenido = 0.5  # 500ms de clic sostenido
        self.parpadeo_detectado = False
        self.DPIM = 1.0  # Reducido para mayor estabilidad
        self.DPIO = 1.08
        self.api = APICliente()
        self.sesion_id = sesion_id

        # Para control de cooldown de clics
        self.ultimo_clic_tiempo = 0
        self.cooldown_clic = 0.4  # 400ms entre clics
        self.clic_activo_actual = False

        # Inicializar cámara
        print("[DEBUG] Iniciando cámara...")
        self.camara = self._inicializar_camara()
        print("[DEBUG] Cámara inicializada")

        # Inicializar detección de manos
        print("[DEBUG] Iniciando detección de manos...")
        self.mp_manos = mp.solutions.hands
        self.manos = self.mp_manos.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        print("[DEBUG] Manos inicializadas")

        # Inicializar detección de rostro y ojos
        print("[DEBUG] Iniciando FaceMesh...")
        self.mp_rostro = mp.solutions.face_mesh
        self.rostro = self.mp_rostro.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        print("[DEBUG] FaceMesh inicializado")

        # Variables de estado
        self.cursor_x = self.ancho // 2
        self.cursor_y = self.alto // 2
        self.clic_activo = False
        self.inactividad = 0
        self.umbral_clic = 0.02

        # NUEVO: Para detección de clic alternativo con palma
        self.umbral_distancia_palma = 0.08  # Distancia pulgar-palma para clic
        self.historial_distancia_palma = deque(maxlen=5)  # Para estabilizar detección

        # Para suavizado del movimiento - MEJORADO
        self.suavizado = 0.5
        self.historial_posiciones = deque(maxlen=3)  # Filtro de media móvil

        # Control ocular - EAR (Relación de Aspecto del Ojo)
        self.parpadeo_activo = False
        self.ultimo_parpadeo = 0
        self.UMBRAL_EAR = 0.21
        self.TIEMPO_PARPADEO = 0.5

        # Índices de landmarks para EAR (Relación de Aspecto del Ojo)
        self.INDICES_OJO_IZQUIERDO = [33, 160, 158, 133, 153, 144]
        self.INDICES_OJO_DERECHO = [362, 385, 387, 263, 373, 380]

        # Para estabilización del EAR
        self.historial_ear = deque(maxlen=5)
        self.ear_suavizado = 0

        # Para el área restringida del puntero
        self.area_ancho = self.ancho * 0.8
        self.area_alto = self.alto * 0.8

        # Calibración y sensibilidad - MEJORADO
        self.calibrado = False
        self.rango_cabeza_x = [0.3, 0.7]  # Rango inicial estimado
        self.rango_cabeza_y = [0.3, 0.7]  # Rango inicial estimado
        self.sensibilidadO = 1.04  # Factor de sensibilidad OJOS
        self.sensibilidadM = 1.0  # Reducido para mayor estabilidad MANOS
        self.centro_cabeza = [0.5, 0.5]  # Posición central de la cabeza

        # NUEVO: Para reset automático por inactividad
        self.umbral_inactividad_reset = 30  # ~1 segundo a 30 FPS
        self.tiempo_ultima_deteccion = time.time()

        self._aplicar_calibracion_guardada()

        print("[DEBUG] Ejecutando calibración automática...")
        self.calibrar()
        print("[DEBUG] Calibración automática completada")

        self.cursor_activo = True
        self.seguimiento_pausado = False
        self._ultimo_marco_bgr = None
        self._ultimo_marco_shape = (self.alto, self.ancho)
        self._ultima_landmarks_face = None

    def _aplicar_calibracion_guardada(self):
        """Carga calibration_{sesion_id}.json y aplica sensibilidad, umbral y rangos si existen."""
        if self.sesion_id is None:
            return
        try:
            from tutorial.calibration_service import load_calibration_disk
        except ImportError:
            return
        data = load_calibration_disk(self.sesion_id)
        if not data:
            return
        try:
            if "sensitivity" in data:
                self.sensibilidadO = float(data["sensitivity"])
            if "blink_threshold" in data:
                self.UMBRAL_EAR = float(data["blink_threshold"])
            rx = data.get("rango_cabeza_x")
            ry = data.get("rango_cabeza_y")
            cc = data.get("centro_cabeza")
            if (
                isinstance(rx, (list, tuple))
                and len(rx) == 2
                and isinstance(ry, (list, tuple))
                and len(ry) == 2
                and isinstance(cc, (list, tuple))
                and len(cc) == 2
            ):
                self.rango_cabeza_x = [float(rx[0]), float(rx[1])]
                self.rango_cabeza_y = [float(ry[0]), float(ry[1])]
                self.centro_cabeza = [float(cc[0]), float(cc[1])]
                self.calibrado = True
                print("[CALIBRATION] Parámetros cargados desde archivo para la sesión.")
        except (TypeError, ValueError) as e:
            print(f"[CALIBRATION] No se pudo aplicar archivo de calibración: {e}")

    def _inicializar_camara(self):
        print("[INIT] Searching for available camera...")
        camara = None

        for i in range(5):  # prueba hasta 5 cámaras
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                print(f"[OK] Camera found at index {i}")
                camara = cap
                break
            cap.release()

        if camara is None:
            raise RuntimeError("[ERROR] No available camera found")

        # Configura la resolución
        camara.set(cv2.CAP_PROP_FRAME_WIDTH, self.ancho)
        camara.set(cv2.CAP_PROP_FRAME_HEIGHT, self.alto)

        return camara

    def _detectar_camara_disponible(self, max_camaras=5):
        """Detecta la primera cámara disponible"""
        for i in range(max_camaras):
            camara = cv2.VideoCapture(i)
            if camara.isOpened():
                print(f"[OK] Camera found at index {i}")
                return camara
            camara.release()
        raise RuntimeError("No se encontró ninguna cámara disponible")

    def calibrar(self, duracion=3):
        if self.calibrado:
            print("[OK] Already calibrated, skipping recalibration")
            return

        print("[CALIBRATE] Calibrating... move your head in all directions")

        rangos_x, rangos_y = [], []
        max_frames = int(duracion * 30)

        for _ in range(max_frames):
            ret, marco = self.camara.read()
            if not ret:
                continue

            resultados = self.rostro.process(cv2.cvtColor(marco, cv2.COLOR_BGR2RGB))
            if resultados.multi_face_landmarks:
                nariz = resultados.multi_face_landmarks[0].landmark[1]
                rangos_x.append(nariz.x)
                rangos_y.append(nariz.y)

            # No bloquea el hilo principal: solo continua

        if not rangos_x or not rangos_y:
            print("[WARNING] No face detected during initial calibration. Keeping previous settings.")
            # No forzar calibrado para que siga intentando con valores por defecto.
            return


        # filtra outliers
        rangos_x = np.clip(rangos_x, np.percentile(rangos_x, 10), np.percentile(rangos_x, 90))
        rangos_y = np.clip(rangos_y, np.percentile(rangos_y, 10), np.percentile(rangos_y, 90))

        nuevo_rango_x = [min(rangos_x), max(rangos_x)]
        nuevo_rango_y = [min(rangos_y), max(rangos_y)]

        # asegura un mínimo de amplitud
        min_amp = 0.15
        for r in (nuevo_rango_x, nuevo_rango_y):
            amp = r[1] - r[0]
            if amp < min_amp:
                c = np.mean(r)
                r[0], r[1] = c - min_amp / 2, c + min_amp / 2

        # suaviza con calibraciones previas
        alpha = 0.3
        self.rango_cabeza_x = [
            self.rango_cabeza_x[0] * (1 - alpha) + nuevo_rango_x[0] * alpha,
            self.rango_cabeza_x[1] * (1 - alpha) + nuevo_rango_x[1] * alpha
        ]
        self.rango_cabeza_y = [
            self.rango_cabeza_y[0] * (1 - alpha) + nuevo_rango_y[0] * alpha,
            self.rango_cabeza_y[1] * (1 - alpha) + nuevo_rango_y[1] * alpha
        ]

        self.centro_cabeza = [np.mean(rangos_x), np.mean(rangos_y)]
        self.calibrado = True
        print(f"[OK] Stable calibration. X:{self.rango_cabeza_x}, Y:{self.rango_cabeza_y}")

    def _calcular_ear(self, landmarks, indices):
        """Calcula la Relación de Aspecto del Ojo (EAR) para un ojo"""
        puntos = [landmarks.landmark[i] for i in indices]

        vertical1 = math.sqrt((puntos[1].x - puntos[5].x) ** 2 + (puntos[1].y - puntos[5].y) ** 2)
        vertical2 = math.sqrt((puntos[2].x - puntos[4].x) ** 2 + (puntos[2].y - puntos[4].y) ** 2)

        horizontal = math.sqrt((puntos[0].x - puntos[3].x) ** 2 + (puntos[0].y - puntos[3].y) ** 2)

        if horizontal == 0:
            return 0.0

        ear = (vertical1 + vertical2) / (2.0 * horizontal)
        return ear

    def _detectar_parpadeo_ear(self, landmarks):
        """Detecta parpadeos usando la Relación de Aspecto del Ojo"""
        ear_izquierdo = self._calcular_ear(landmarks, self.INDICES_OJO_IZQUIERDO)
        ear_derecho = self._calcular_ear(landmarks, self.INDICES_OJO_DERECHO)

        ear = (ear_izquierdo + ear_derecho) / 2.0

        self.historial_ear.append(ear)
        self.ear_suavizado = sum(self.historial_ear) / len(self.historial_ear) if self.historial_ear else ear

        tiempo_actual = time.time()
        parpadeo_actual = self.ear_suavizado < self.UMBRAL_EAR

        # Detectar inicio de parpadeo
        if parpadeo_actual and not self.parpadeo_detectado:
            self.parpadeo_detectado = True
            self.tiempo_inicio_clic = tiempo_actual
            self.clic_sostenido = True
            return True

        # Detectar fin de parpadeo
        elif not parpadeo_actual and self.parpadeo_detectado:
            self.parpadeo_detectado = False
            self.tiempo_ultimo_parpadeo = tiempo_actual

            # Mantener clic activo por un tiempo adicional
            tiempo_parpadeo = tiempo_actual - self.tiempo_inicio_clic
            if tiempo_parpadeo < 0.3:  # Parpadeo muy rápido
                self.clic_sostenido = False
            # Para parpadeos normales, el clic se mantiene hasta el tiempo programado

        # Controlar la duración del clic sostenido
        if self.clic_sostenido and (tiempo_actual - self.tiempo_inicio_clic) > self.duracion_clic_sostenido:
            self.clic_sostenido = False

        return self.clic_sostenido

    def _mapear_posicion(self, x, y):
        """Mapea la posición de la cabeza a las coordenadas de la pantalla"""
        if not self.calibrado:
            # Usar valores por defecto si no está calibrado
            rango_x = [0.3, 0.7]
            rango_y = [0.3, 0.7]
            centro_x = 0.5
            centro_y = 0.5
        else:
            rango_x = self.rango_cabeza_x
            rango_y = self.rango_cabeza_y
            centro_x = self.centro_cabeza[0]
            centro_y = self.centro_cabeza[1]

        # Calcular desviación desde el centro (normalizada entre -1 y 1)
        desviacion_x = (x - centro_x) / (rango_x[1] - rango_x[0]) * 2
        desviacion_y = (y - centro_y) / (rango_y[1] - rango_y[0]) * 2

        # Aplicar sensibilidad (SOLO MODO FACIAL)
        desviacion_x *= self.sensibilidadO * self.DPIO
        desviacion_y *= self.sensibilidadO * self.DPIO

        # Mapear a coordenadas de pantalla (INVERTIR EJE X con signo negativo)
        x_virtual = int(self.ancho * 0.5 - desviacion_x * self.ancho * 0.5)  # Cambio aquí: signo negativo
        y_virtual = int(self.alto * 0.5 + desviacion_y * self.alto * 0.5)  # Eje Y sin cambios
        # Limitar a los bordes de la pantalla
        x_virtual = max(0, min(self.ancho, x_virtual))
        y_virtual = max(0, min(self.alto, y_virtual))

        return x_virtual, y_virtual

    def ajustar_dpi(self, factor):
        """Aumenta o disminuye la ganancia (DPI virtual) - SOLO FACIAL"""
        self.DPIO = max(0.0, min(10.0, self.DPIO * factor))
        print(f"[DPI] Adjusted to: {self.DPIO:.2f}")

    def pausar_cursor(self):
        self.cursor_activo = False

    def reanudar_cursor(self):
        self.cursor_activo = True

    def _calcular_distancia_pulgar_palma(self, landmarks):
        """Calcula la distancia entre el pulgar y el centro de la palma - NUEVO MÉTODO ALTERNATIVO"""
        # Landmarks: pulgar (4) y muñeca (0)
        pulgar = landmarks.landmark[4]
        muneca = landmarks.landmark[0]

        # Calcular distancia normalizada
        distancia = math.sqrt((pulgar.x - muneca.x) ** 2 + (pulgar.y - muneca.y) ** 2)
        return distancia

    def _obtener_posicion_manos(self, marco_rgb):
        """Obtiene posición usando las manos - MEJORADO CON NUEVO MÉTODO DE CLIC"""
        resultados = self.manos.process(marco_rgb)
        clic_activo = False

        if resultados.multi_hand_landmarks:
            self.inactividad = 0
            self.tiempo_ultima_deteccion = time.time()

            landmarks = resultados.multi_hand_landmarks[0]
            pulgar = landmarks.landmark[4]
            indice = landmarks.landmark[8]

            # Usa SOLO el pulgar para mover el cursor
            x_virtual, y_virtual = self._mapear_posicion(indice.x, indice.y)

            # --- SUAVIZADO MEJORADO CON FILTRO EXPONENCIAL ---
            suavizado_base = 0.3  # Más suavizado para mayor estabilidad
            zona_muerta = 12  # Zona muerta ligeramente aumentada

            # Diferencia con el cursor actual
            dx = x_virtual - self.cursor_x
            dy = y_virtual - self.cursor_y
            dist = math.hypot(dx, dy)

            # Si el movimiento es muy pequeño → no actualizamos
            if dist < zona_muerta:
                x_virtual = self.cursor_x
                y_virtual = self.cursor_y

            # Filtro exponencial para movimiento más suave
            suavizado = min(1.0, suavizado_base + dist / 150.0)  # Más gradual

            # Aplica el suavizado
            self.cursor_x = int(self.cursor_x * (1 - suavizado) + x_virtual * suavizado)
            self.cursor_y = int(self.cursor_y * (1 - suavizado) + y_virtual * suavizado)

        # --- NUEVO MÉTODO DE CLIC: DISTANCIA PULGAR-ÍNDICE ---
        distancia_pinch = math.sqrt((pulgar.x - indice.x) ** 2 + (pulgar.y - indice.y) ** 2)
        self.historial_distancia_palma.append(distancia_pinch)

        # Requiere que estén muy juntos por varios frames
        if len(self.historial_distancia_palma) >= 4:
            clic_detectado = all(d < 0.04 for d in list(self.historial_distancia_palma)[-4:])
            tiempo_actual = time.time()
            if clic_detectado and (tiempo_actual - self.ultimo_clic_tiempo) >= self.cooldown_clic:
                clic_activo = True
                self.ultimo_clic_tiempo = tiempo_actual
                print("[CLICK] Click detected (thumb-index pinch)")

        else:
            self.inactividad += 1

        return self.cursor_x, self.cursor_y, clic_activo

    def _obtener_posicion_ojos(self, marco_rgb):
        """Obtiene posición usando los ojos - MEJORADO CON COOLDOWN"""
        resultados = self.rostro.process(marco_rgb)

        # Estado de clic por defecto
        clic_activo = False

        if resultados.multi_face_landmarks:
            self.inactividad = 0
            self.tiempo_ultima_deteccion = time.time()

            landmarks = resultados.multi_face_landmarks[0]
            self._ultima_landmarks_face = landmarks
            nariz = landmarks.landmark[1]

            # Mapear la posición de la nariz a coordenadas de pantalla
            x_virtual, y_virtual = self._mapear_posicion(nariz.x, nariz.y)

            # Suavizar el movimiento
            self.cursor_x = int(self.cursor_x * (1 - self.suavizado) + x_virtual * self.suavizado)
            self.cursor_y = int(self.cursor_y * (1 - self.suavizado) + y_virtual * self.suavizado)

            # Detectar parpadeo y aplicar cooldown
            self._detectar_parpadeo_ear(landmarks)

            tiempo_actual = time.time()
            if self.clic_sostenido and (tiempo_actual - self.ultimo_clic_tiempo) >= self.cooldown_clic:
                clic_activo = True
                self.ultimo_clic_tiempo = tiempo_actual

        else:
            self.inactividad += 1
            self._ultima_landmarks_face = None
            # Si no se detecta rostro, desactivar clic sostenido después de un tiempo
            if time.time() - self.tiempo_ultimo_parpadeo > 1.0:
                self.clic_sostenido = False
                self.parpadeo_detectado = False

        return self.cursor_x, self.cursor_y, clic_activo

    def resetear_estado_completo(self):
        """Resetea completamente el estado de clic y buffers - NUEVO MÉTODO"""
        self.clic_sostenido = False
        self.parpadeo_detectado = False
        self.tiempo_inicio_clic = 0
        self.clic_activo_actual = False

        # Resetear buffers de detección
        if hasattr(self, "historial_clic"):
            self.historial_clic.clear()

        self.historial_distancia_palma.clear()
        self.historial_ear.clear()

        print("[RESET] Click state and buffers reset")

    def verificar_reset_por_inactividad(self):
        """Verifica inactividad y resetea estado si es necesario - NUEVO MÉTODO"""
        tiempo_actual = time.time()
        if tiempo_actual - self.tiempo_ultima_deteccion > 1.0:  # 1 segundo de inactividad
            if self.clic_sostenido or self.parpadeo_detectado:
                self.resetear_estado_completo()
                return True
        return False

    def obtener_posicion_y_clic(self):
        """Obtiene la posición del cursor y estado del clic - MEJORADO CON RESET AUTOMÁTICO"""
        # Verificar reset por inactividad
        self.verificar_reset_por_inactividad()

        if getattr(self, "seguimiento_pausado", False):
            return self.cursor_x, self.cursor_y, False

        ret, marco = self.camara.read()
        if not ret:
            return self.cursor_x, self.cursor_y, False

        self._ultimo_marco_bgr = marco
        self._ultimo_marco_shape = (marco.shape[0], marco.shape[1])

        # --- MEJORA DE ILUMINACIÓN ---
        marco_yuv = cv2.cvtColor(marco, cv2.COLOR_BGR2YUV)
        marco_yuv[:, :, 0] = cv2.equalizeHist(marco_yuv[:, :, 0])  # Ecualiza brillo
        marco = cv2.cvtColor(marco_yuv, cv2.COLOR_YUV2BGR)

        marco_rgb = cv2.cvtColor(marco, cv2.COLOR_BGR2RGB)

        # SOLO MODO FACIAL - Eliminado control manual
        x, y, clic = self._obtener_posicion_ojos(marco_rgb)

        return x, y, clic

    def obtener_frame(self):
        """Último fotograma BGR procesado por obtener_posicion_y_clic (o None)."""
        return self._ultimo_marco_bgr

    def obtener_bbox_rostro(self):
        """Bounding box (x, y, w, h) en píxeles del último frame o None."""
        if not self._ultima_landmarks_face:
            return None
        lm = self._ultima_landmarks_face
        fh, fw = self._ultimo_marco_shape[0], self._ultimo_marco_shape[1]
        xs = [pt.x for pt in lm.landmark]
        ys = [pt.y for pt in lm.landmark]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        px = int(min_x * fw)
        py = int(min_y * fh)
        pw = max(1, int((max_x - min_x) * fw))
        ph = max(1, int((max_y - min_y) * fh))
        return px, py, pw, ph

    def detectar_parpadeo(self):
        """True si el EAR actual indica ojos cerrados (parpadeo)."""
        return self.ear_suavizado < self.UMBRAL_EAR

    def alternar_seguimiento_pausado(self):
        self.seguimiento_pausado = not getattr(self, "seguimiento_pausado", False)
        return self.seguimiento_pausado

    def ajustar_sensibilidad(self, factor):
        """Ajusta la sensibilidad del movimiento"""
        if self.modo_ocular:
            self.sensibilidadO = max(0.5, min(10.0, self.sensibilidadO * factor))
            print(f"[SENSITIVITY] Adjusted to: {self.sensibilidadO:.2f}")

    def dibujar_puntero(self, pantalla, x, y):
        """Dibuja el puntero en la pantalla"""
        izquierda = (self.ancho - self.area_ancho) // 2
        derecha = izquierda + self.area_ancho
        arriba = (self.alto - self.area_alto) // 2
        abajo = arriba + self.area_alto

        x_restringido = max(0, min(x, self.ancho))
        y_restringido = max(0, min(y, self.alto))

        color = (0, 255, 255) if self.modo_ocular else (0, 255, 0)
        tamaño = 20
        grosor = 4

        pygame.draw.line(pantalla, color,
                         (x_restringido - tamaño, y_restringido),
                         (x_restringido + tamaño, y_restringido), grosor)
        pygame.draw.line(pantalla, color,
                         (x_restringido, y_restringido - tamaño),
                         (x_restringido, y_restringido + tamaño), grosor)

        pygame.draw.circle(pantalla, color, (x_restringido, y_restringido), tamaño, 2)

        return x_restringido, y_restringido

    def mostrar_estado(self, pantalla, fuente, x, y, clic, inactividad):
        """Muestra información de estado en pantalla"""
        texto_coords = fuente.render(f"X: {x} Y: {y}", True, BLANCO)
        pantalla.blit(texto_coords, (10, 10))

        estado_clic = "CLIC ACTIVADO" if clic else "CLIC INACTIVO"
        color_clic = VERDE if clic else ROJO
        texto_clic = fuente.render(estado_clic, True, color_clic)
        pantalla.blit(texto_clic, (10, 50))

        modo = "OJOS" if self.modo_ocular else "MANOS"
        texto_modo = fuente.render(f"Modo: {modo}", True, (255, 255, 0))
        pantalla.blit(texto_modo, (10, 90))

        texto_inact = fuente.render(f"Inactividad: {inactividad}", True, BLANCO)
        pantalla.blit(texto_inact, (10, 130))

        # SOLO MODO FACIAL
        texto_dpi = fuente.render(f"DPI: {self.DPIO:.2f}", True, BLANCO)
        pantalla.blit(texto_dpi, (10, 290))

        texto_ear = fuente.render(f"EAR: {self.ear_suavizado:.3f}", True, BLANCO)
        pantalla.blit(texto_ear, (10, 170))

        texto_sens = fuente.render(f"Sensibilidad: {self.sensibilidadO:.2f}", True, BLANCO)
        pantalla.blit(texto_sens, (10, 210))

        calibrado = "SI" if self.calibrado else "NO"
        texto_cal = fuente.render(f"Calibrado: {calibrado}", True, BLANCO)
        pantalla.blit(texto_cal, (10, 250))

    def liberar_recursos(self):
        """Libera todos los recursos"""
        if hasattr(self, 'manos') and self.manos:
            self.manos.close()
        if hasattr(self, 'rostro') and self.rostro:
            self.rostro.close()
        if hasattr(self, 'camara') and self.camara.isOpened():
            self.camara.release()


# Función principal de prueba (actualizada para usar nuevos métodos)
def ejecutar_prueba():
    pygame.init()

    ANCHO, ALTO = 1620, 900
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Control por Gestos - Seguimiento de Manos/Ojos MEJORADO")

    fuente = pygame.font.SysFont(None, 36)

    try:
        manejador = ManejoCamara(ancho=ANCHO, alto=ALTO, modo_ocular=False)
        print("[OK] Camera and detection initialized correctly")
    except Exception as e:
        print(f"[ERROR] Initialization error: {e}")
        pygame.quit()
        sys.exit()

    reloj = pygame.time.Clock()
    ejecutando = True

    print("[READY] Enhanced gesture control activated. Press ESC to exit.")
    print("[HAND] Move your hand in front of the camera or your head for eye mode")
    print("[CLICK] Bring thumb close to palm for click or blink in eye mode")
    print("M: Cambiar entre modos")
    print("C: Calibrar modo ocular")
    print("+/-: Ajustar sensibilidad")
    print("R: Reset manual del estado de clic")

    while ejecutando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    ejecutando = False
                elif evento.key == pygame.K_m:
                    manejador.cambiar_modo()
                elif evento.key == pygame.K_c:
                    manejador.calibrar()
                elif evento.key == pygame.K_PLUS or evento.key == pygame.K_KP_PLUS:
                    manejador.ajustar_sensibilidad(1.2)
                elif evento.key == pygame.K_MINUS or evento.key == pygame.K_KP_MINUS:
                    manejador.ajustar_sensibilidad(0.8)
                elif evento.key == pygame.K_d:  # Aumentar DPI
                    manejador.ajustar_dpi(1.5)
                elif evento.key == pygame.K_s:  # Disminuir DPI
                    manejador.ajustar_dpi(0.7)
                elif evento.key == pygame.K_r:  # Reset manual
                    manejador.resetear_estado_completo()
                    print("[RESET] Manual reset executed")

        pantalla.fill((50, 50, 50))

        try:
            x, y, clic = manejador.obtener_posicion_y_clic()
            x_final, y_final = manejador.dibujar_puntero(pantalla, x, y)
            manejador.mostrar_estado(pantalla, fuente, x_final, y_final, clic, manejador.inactividad)

        except Exception as e:
            print(f"Error durante la ejecucion: {e}")

        pygame.display.flip()
        reloj.tick(30)

    manejador.liberar_recursos()
    pygame.quit()
    print("[EXIT] Program terminated correctly")
