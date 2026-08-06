import pygame
import os
import sys
from core.config import *
import core.config as config
from games.Juego_memoria import ejecutar_juego_memoria
from games.juegolaberinto import ejecutar_juego_laberinto
from games.juego_puzzle import ejecutar_puzzle_animales
from games.EncuentraAprende import ejecutar_encuentra_y_aprende
from games.cazaletras import ejecutar_juego_ahorcado
from ui.barra_menu import BarraInferior
from api.APICliente import APICliente
from core.paths import imagen
from logic.cursor import dibujar_cursor_unificado
from ui.dibujo_ui import blit_texto_borde_ligero
from core.shortcuts import aplicar_atajo_camara, procesar_atajos_globales
from ui.Inicio import SistemaTTS   # para el TTS

api = APICliente()


class MenuJuegos:
    def __init__(self, camara, gestor_musica, ID_sesion):
        self.camara = camara
        self.gestor_musica = gestor_musica
        self.ID_sesion = ID_sesion

        # Configurar pantalla
        self.pantalla = pygame.display.get_surface()
        if not self.pantalla:
            self.pantalla = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

        self.ANCHO, self.ALTO = self.pantalla.get_size()

        # Cargar fondo
        try:
            self.fondo = pygame.image.load(FONDO_PRINCIPAL)
            self.fondo = pygame.transform.scale(self.fondo, (self.ANCHO, self.ALTO))
        except Exception as e:
            print("⚠️ No se pudo cargar la imagen de fondo del menú de juegos", e)
            self.fondo = pygame.Surface((self.ANCHO, self.ALTO))
            self.fondo.fill(COLOR_FONDO)

        # Configuración de botones
        self.carpeta_img = imagen("Juegos")

        # Definir juegos disponibles
        self.juegos = [
            {"nombre": "Pares mágicos", "imagen": "pares_magicos.jpg", "accion": ejecutar_juego_memoria},
            {"nombre": "Animalia", "imagen": "animalia.jpg", "accion": ejecutar_puzzle_animales},
            {"nombre": "Mate-reto", "imagen": "mate-reto.jpg", "accion": ejecutar_juego_laberinto},
            {"nombre": "Encuentra y aprende", "imagen": "encuentra.jpg", "accion": ejecutar_encuentra_y_aprende},
            {"nombre": "Caza letras", "imagen": "caza_letras.jpg", "accion": ejecutar_juego_ahorcado},
        ]

        # Configuración de carrusel
        self.start_index = 0
        self.vista_count = min(3, len(self.juegos))
        self.tamaño_miniaturas = (290, 280)

        # Cargar imágenes de los juegos
        self.cargar_imagenes_juegos()

        # ========== BARRA INFERIOR AUTÓNOMA ==========
        self.tts = SistemaTTS()
        self.barra = BarraInferior(
            camara=self.camara,
            gestor_musica=self.gestor_musica,
            decir_texto=self.tts.decir_texto,
            ID_sesion=self.ID_sesion
        )

        self.ejecutando = False

    def cargar_imagenes_juegos(self):
        """Cargar las imágenes de los juegos disponibles"""
        self.imagenes_juegos = []

        for juego in self.juegos:
            ruta = os.path.join(self.carpeta_img, juego["imagen"])
            try:
                imagen = pygame.image.load(ruta)
            except Exception as ex:
                print(f"⚠️ No se pudo cargar la imagen: {ruta} -> {ex}")
                imagen = pygame.Surface(self.tamaño_miniaturas)
                imagen.fill((150, 150, 150))

            juego["superficie"] = imagen
            self.imagenes_juegos.append(imagen)

        self.miniaturas = [pygame.transform.scale(juego["superficie"], self.tamaño_miniaturas) for juego in self.juegos]
        self.rect_miniaturas = []

        for _ in range(self.vista_count):
            self.rect_miniaturas.append(pygame.Rect(0, 0, *self.tamaño_miniaturas))

    def dibujar(self, cursor_x, cursor_y):
        """Dibujar todo el menú de juegos con diseño mejorado"""
        self.pantalla.blit(self.fondo, (0, 0))

        # Geometría del carrusel
        separacion_x = int(self.ANCHO * 0.05)
        total_visible = min(self.vista_count, len(self.juegos))
        ancho_fotos = total_visible * self.tamaño_miniaturas[0] + (total_visible - 1) * separacion_x
        inicio_x = (self.ANCHO - ancho_fotos) // 2
        y_fotos = int(self.ALTO * 0.25)

        # Flechas de navegación
        centro_y_fotos = y_fotos + (self.tamaño_miniaturas[1] // 2)
        self.rect_izquierda = pygame.Rect(inicio_x - 100, centro_y_fotos - 40, 60, 80)
        self.rect_derecha = pygame.Rect(inicio_x + ancho_fotos + 40, centro_y_fotos - 40, 60, 80)

        for rect, direccion in [(self.rect_izquierda, "izq"), (self.rect_derecha, "der")]:
            color_flecha = HOVER if rect.collidepoint(cursor_x, cursor_y) else SAVE_BG
            pygame.draw.rect(self.pantalla, color_flecha, rect, border_radius=15)
            puntos = []
            if direccion == "izq":
                puntos = [(rect.centerx + 10, rect.centery - 20), (rect.centerx - 10, rect.centery),
                          (rect.centerx + 10, rect.centery + 20)]
            else:
                puntos = [(rect.centerx - 10, rect.centery - 20), (rect.centerx + 10, rect.centery),
                          (rect.centerx - 10, rect.centery + 20)]
            pygame.draw.polygon(self.pantalla, BLANCO, puntos)

        # Dibujar miniaturas
        self.rect_miniaturas = []
        for i in range(total_visible):
            index_visual = (self.start_index + i) % len(self.juegos)
            x = inicio_x + i * (self.tamaño_miniaturas[0] + separacion_x)
            rect = pygame.Rect(x, y_fotos, *self.tamaño_miniaturas)
            self.rect_miniaturas.append(rect)

            if rect.collidepoint(cursor_x, cursor_y):
                ancho_h = int(self.tamaño_miniaturas[0] * 1.1)
                alto_h = int(self.tamaño_miniaturas[1] * 1.1)
                img_hover = pygame.transform.scale(self.miniaturas[index_visual], (ancho_h, alto_h))
                rect_hover = img_hover.get_rect(center=rect.center)
                self.pantalla.blit(img_hover, rect_hover)
                pygame.draw.rect(self.pantalla, BLANCO, rect_hover, 12, border_radius=0)
                nombre = self.juegos[index_visual]["nombre"]
                blit_texto_borde_ligero(self.pantalla, nombre, config.fuente, SAVE_BG, NEGRO,
                                        (rect.centerx, rect.bottom + 40))
            else:
                self.pantalla.blit(self.miniaturas[index_visual], rect)
                pygame.draw.rect(self.pantalla, SAVE_BORDER, rect, 12, border_radius=0)
                nombre = self.juegos[index_visual]["nombre"]
                blit_texto_borde_ligero(self.pantalla, nombre, config.fuente, BLANCO, HOVER,
                                        (rect.centerx, rect.bottom + 30))

    def manejar_interaccion(self, cursor_x, cursor_y, clic_activo):
        """Manejar las interacciones del usuario (flechas y clic en juegos)"""
        if not clic_activo:
            return False

        if hasattr(self, "rect_izquierda") and self.rect_izquierda.collidepoint(cursor_x, cursor_y):
            self.start_index = (self.start_index - 1) % len(self.juegos)
            return True

        if hasattr(self, "rect_derecha") and self.rect_derecha.collidepoint(cursor_x, cursor_y):
            self.start_index = (self.start_index + 1) % len(self.juegos)
            return True

        for i, rect in enumerate(self.rect_miniaturas):
            if rect.collidepoint(cursor_x, cursor_y):
                index_visual = (self.start_index + i) % len(self.juegos)
                self.iniciar_juego(index_visual)
                return True

        return False

    def iniciar_juego(self, indice_juego):
        """Iniciar el juego seleccionado"""
        if indice_juego < 0 or indice_juego >= len(self.juegos):
            print(f"⚠️ Índice de juego inválido: {indice_juego}")
            return

        juego = self.juegos[indice_juego]
        print(f"🎮 Iniciando '{juego['nombre']}' (índice {indice_juego})")

        self.camara.pausar_cursor()
        try:
            juego['accion'](self.camara, self.ID_sesion)
        except Exception as e:
            print(f"Error al iniciar {juego['nombre']}: {e}")

    def ejecutar(self):
        """Ejecutar el menú de juegos"""
        self.ejecutando = True
        self.control_clic = False
        self.camara.reanudar_cursor()
        pygame.time.delay(800)

        try:
            for _ in range(10):
                _, _, clic_activo = self.camara.obtener_posicion_y_clic()
                if clic_activo:
                    pygame.time.delay(100)
        except:
            pass

        self.camara.calibrar()
        reloj = pygame.time.Clock()

        while self.ejecutando:
            try:
                cursor_x, cursor_y, clic_activo = self.camara.obtener_posicion_y_clic()
            except Exception as e:
                cursor_x, cursor_y = pygame.mouse.get_pos()
                clic_activo = pygame.mouse.get_pressed()[0]

            # Detección de flanco: un clic por parpadeo (igual que el menú principal)
            if clic_activo and not self.control_clic:
                clic_activo_edge = True
                self.control_clic = True
            elif not clic_activo:
                self.control_clic = False
                clic_activo_edge = False
            else:
                clic_activo_edge = False

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    self.ejecutando = False
                elif evento.type == pygame.KEYDOWN:
                    acc = procesar_atajos_globales(evento, self.camara)
                    if acc == "tutorial":
                        self.camara.pausar_cursor()
                        return "instrucciones"
                    if acc == "recalibrar":
                        aplicar_atajo_camara("recalibrar", self.camara)
                    elif acc == "toggle_pausa":
                        aplicar_atajo_camara("toggle_pausa", self.camara)
                    elif evento.key == pygame.K_ESCAPE:
                        self.ejecutando = False
                    elif evento.key == pygame.K_c:
                        self.camara.calibrar()

            self.dibujar(cursor_x, cursor_y)
            self.manejar_interaccion(cursor_x, cursor_y, clic_activo_edge)

            # ========== BARRA INFERIOR AUTÓNOMA ==========
            self.barra.actualizar_visibilidad((cursor_x, cursor_y), self.ALTO)
            self.barra.dibujar(self.pantalla, (cursor_x, cursor_y))
            destino = self.barra.manejar_clic((cursor_x, cursor_y), clic_activo_edge)
            if destino == "juegos":
                destino = None  # ya estamos en el menú de juegos; no recargar
            if destino:
                self.camara.pausar_cursor()
                self.ejecutando = False
                return destino

            try:
                dibujar_cursor_unificado(self.pantalla, cursor_x, cursor_y, modo_ocular=True,
                                         ancho=self.ANCHO, alto=self.ALTO)
            except Exception as e:
                pygame.draw.circle(self.pantalla, (255, 0, 0), (cursor_x, cursor_y), 10, 2)

            pygame.display.flip()
            reloj.tick(30)

        return "menu_principal"