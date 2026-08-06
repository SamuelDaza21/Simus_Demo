from core.ManejoCamara import ManejoCamara
import pygame
import math


class CursorIntegral(pygame.sprite.Sprite):
    """
    Cursor integral animado: una estrella brillante giratoria muy atractiva para niños.
    - Animación de rotación continua
    - Efecto de brillo parpadeante
    - Tamaño escalable (por defecto 48x48)
    - Hotspot preciso en el centro
    """
    
    def __init__(self, tamaño=48):
        super().__init__()
        self.tamaño = tamaño
        self.angulo = 0
        self.brillo = 255
        self.direccion_brillo = -5  # Varía el brillo para efecto parpadeante
        self.velocidad_rotacion = 6  # Grados por frame
        self.frame_count = 0
        
        # Generar la imagen de la estrella
        self.image = self._generar_estrella()
        self.rect = self.image.get_rect()
        self.hotspot = (self.tamaño // 2, self.tamaño // 2)  # Centro de la estrella
        
    def _generar_estrella(self):
        """
        Genera una estrella de 5 puntas giratoria con efecto de brillo.
        Colores: gradiente dorado-naranja con efecto de glow blanco.
        """
        # Crear superficie con transparencia
        surface = pygame.Surface((self.tamaño, self.tamaño), pygame.SRCALPHA)
        center_x, center_y = self.tamaño // 2, self.tamaño // 2
        radio_externo = self.tamaño // 2 - 2
        radio_interno = int(radio_externo * 0.4)
        
        # Crear puntos de la estrella de 5 puntas
        puntos = []
        for i in range(10):
            angulo_rad = (i * 36 - 90) * math.pi / 180  # -90 para que apunte hacia arriba
            
            if i % 2 == 0:  # Puntas exteriores
                radio = radio_externo
                color_brillo = (255, 255, 150, int(self.brillo * 0.8))  # Amarillo claro
            else:  # Puntas interiores
                radio = radio_interno
                color_brillo = (255, 200, 0, int(self.brillo * 0.6))  # Dorado
            
            x = center_x + radio * math.cos(angulo_rad)
            y = center_y + radio * math.sin(angulo_rad)
            puntos.append((x, y))
        
        # Dibujar la estrella principal (degradado dorado-naranja)
        pygame.draw.polygon(surface, (255, 165, 0, int(self.brillo * 0.9)), puntos)
        
        # Dibujar contorno brillante
        pygame.draw.polygon(surface, (255, 255, 255, int(self.brillo * 0.5)), puntos, 2)
        
        # Añadir núcleo blanco luminoso en el centro
        pygame.draw.circle(surface, (255, 255, 255, int(self.brillo)), 
                         (center_x, center_y), int(radio_interno * 0.4))
        
        # Añadir aura de brillo suave alrededor
        if self.brillo > 150:
            pygame.draw.circle(surface, (255, 255, 200, int((self.brillo - 100) * 0.3)), 
                             (center_x, center_y), int(radio_externo * 0.7), 3)
        
        return surface
    
    def update(self):
        """Actualiza la animación del cursor."""
        self.frame_count += 1
        
        # Rotación continua
        self.angulo = (self.angulo + self.velocidad_rotacion) % 360
        
        # Efecto de brillo parpadeante
        self.brillo += self.direccion_brillo
        if self.brillo >= 255 or self.brillo <= 150:
            self.direccion_brillo *= -1
        
        # Regenerar la imagen cada frame para que la animación sea suave
        if self.frame_count % 2 == 0:  # Actualizar cada 2 frames para eficiencia
            self.image = self._generar_estrella()
            
            # Rotar la imagen
            imagen_rotada = pygame.transform.rotate(self.image, -self.angulo)
            self.rect = imagen_rotada.get_rect()
            self.image = imagen_rotada
    
    def dibujar(self, surface, x, y):
        """
        Dibuja el cursor en la posición (x, y) con el hotspot preciso.
        Retorna la posición final del cursor (para compatibilidad).
        """
        # Restringir a los límites de pantalla
        ancho_pantalla, alto_pantalla = surface.get_size()
        x_restringido = max(0, min(x, ancho_pantalla - 1))
        y_restringido = max(0, min(y, alto_pantalla - 1))
        
        # Calcular la posición del rect considerando el hotspot
        rect_posicion = (
            x_restringido - self.hotspot[0],
            y_restringido - self.hotspot[1]
        )
        
        # Dibujar
        surface.blit(self.image, rect_posicion)
        
        return x_restringido, y_restringido


class ControladorCursor:
    """Singleton para control de cursor facial centralizado."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, ancho=1620, alto=900, sesion_id=None):
        if getattr(self, '_inicializado', False):
            return

        self._inicializado = True
        self.camara = ManejoCamara(ancho=ancho, alto=alto, modo_ocular=True, sesion_id=sesion_id)

    def obtener_posicion_y_clic(self):
        return self.camara.obtener_posicion_y_clic()

    def dibujar_puntero(self, superficie, x, y):
        return self.camara.dibujar_puntero(superficie, x, y)

    def recalibrar(self):
        if not self.camara.calibrado:
            self.camara.calibrar()

    def calibrar(self):
        self.camara.calibrar()

    def estado_calibrado(self):
        return self.camara.calibrado

    def pausar_cursor(self):
        self.camara.pausar_cursor()

    def reanudar_cursor(self):
        self.camara.reanudar_cursor()

    def ajustar_sensibilidad(self, factor):
        self.camara.ajustar_sensibilidad(factor)

    def liberar_recursos(self):
        self.camara.liberar_recursos()

    def obtener_camara(self):
        return self.camara


def dibujar_cursor_unificado(pantalla, x, y, modo_ocular=True, ancho=1620, alto=900):
    """
    Función unificada para dibujar el cursor facial integral en todas las pantallas.
    ✨ Usa la nueva clase CursorIntegral: una estrella brillante giratoria muy atractiva.
    
    Args:
        pantalla: Superficie pygame donde dibujar
        x, y: Coordenadas del cursor facial
        modo_ocular: Actualmente solo soporta modo ocular (True)
        ancho, alto: Dimensiones de la pantalla
    
    Returns:
        tupla (x_final, y_final): Coordenadas finales del cursor (restringidas a pantalla)
    """
    # Crear cursor integral (única instancia reutilizable)
    if not hasattr(dibujar_cursor_unificado, 'cursor_integral'):
        dibujar_cursor_unificado.cursor_integral = CursorIntegral(tamaño=48)
    
    cursor = dibujar_cursor_unificado.cursor_integral
    cursor.update()  # Actualizar animación
    
    # Dibujar el cursor en la posición proporcionada
    x_final, y_final = cursor.dibujar(pantalla, x, y)
    
    return x_final, y_final
