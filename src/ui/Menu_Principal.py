import pygame
import sys
from ui.Configuracion import Configuracion
from ui.Inicio import SistemaTTS
import core.config as config  # Importa el módulo, no los nombres sueltos
from core.ManejoCamara import ManejoCamara
from core.Musica import *
from api.Servidor import Servidor
from logic.cursor import dibujar_cursor_unificado
from ui.dibujo_ui import dibujar_boton_redondeado
from core.shortcuts import aplicar_atajo_camara, procesar_atajos_globales

servidor = Servidor()

class MenuPrincipal:
    def __init__(self, ID_sesion, camara):
        self.camara = camara
        self.gestor_musica = gestor_musica
        self.ID_sesion = ID_sesion

        if not pygame.mixer.get_init():
            pygame.mixer.init()
        if not pygame.mixer.music.get_busy():
            self.gestor_musica.iniciar_musica()
        self.voz = SistemaTTS()
        self.fondo = None

        # Opciones del menú (text_key debe coincidir con claves en JSON)
        self.opciones = [
            {"text_key": "Inicio", "estado": "inicio", "voz": "Inicio"},
            {"text_key": "Juegos", "estado": "juegos", "voz": "Juegos"},
            {"text_key": "Instrucciones", "estado": "instrucciones", "voz": "Instrucciones"},
            {"text_key": "Configuracion", "estado": "configuracion", "voz": "Configuracion"},
            {"text_key": "Salir", "estado": "salir", "voz": "Salir"},
        ]
        self.ejecutando = True
        self.control_clic = False
        self.cartel_estado = "oculto"
        self.cartel_x = 0

    def dibujar_texto_centrado(self, pantalla, texto, y, fuente, color=None):
        if color is None:
            color = config.COLOR_TEXTO
        texto_superficie = config.render_text(texto, fuente, color)
        ancho = pantalla.get_width()
        x = ancho // 2 - texto_superficie.get_width() // 2
        pantalla.blit(texto_superficie, (x, y))
        return pygame.Rect(x, y, texto_superficie.get_width(), texto_superficie.get_height())

    def dibujar_boton(self, pantalla, rect, texto, fuente, color_fondo=None, color_borde=None):
        if color_fondo is None:
            color_fondo = config.FONDO_BOTON
        if color_borde is None:
            color_borde = config.BORDE_BOTON
        return dibujar_boton_redondeado(
            pantalla, rect, texto, fuente, color_fondo, color_borde, config.COLOR_TEXTO,
            border_radius=15, grosor_borde=4,
        )

    def mostrar_mensaje_ayuda(self, pantalla, mano_detectada):
        pass

    def ejecutar(self):
        pantalla = pygame.display.get_surface()
        if pantalla is None:
            print("[ERROR] No se pudo obtener la superficie de pantalla en MenuPrincipal")
            return "salir"

        ancho, alto = pantalla.get_size()
        self.cartel_x = ancho

        try:
            fondo_img = pygame.image.load(config.FONDO_PRINCIPAL)
            self.fondo = pygame.transform.scale(fondo_img, (ancho, alto))
        except Exception as e:
            print("⚠️ No se pudo cargar la imagen de fondo del menú", e)
            self.fondo = None

        print("🚀 Entrando a MenuPrincipal")
        reloj = pygame.time.Clock()
        self.camara.reanudar_cursor()

        if not self.camara.calibrado:
            self.camara.calibrar()

        while self.ejecutando:
            try:
                cursor_x, cursor_y, clic_camara = self.camara.obtener_posicion_y_clic()
                if clic_camara and not self.control_clic:
                    clic_activo = True
                    self.control_clic = True
                elif not clic_camara:
                    self.control_clic = False
                    clic_activo = False
            except Exception as e:
                cursor_x, cursor_y = pygame.mouse.get_pos()
                clic_activo = pygame.mouse.get_pressed()[0] and not self.control_clic
                self.control_clic = pygame.mouse.get_pressed()[0]

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

            if self.fondo:
                pantalla.blit(self.fondo, (0, 0))
            else:
                pantalla.fill(config.FONDO)

            # Dibujar botones usando config.traductor y config.fuente
            for i, opcion in enumerate(self.opciones):
                ancho_boton = ancho * 0.4
                alto_boton = alto * 0.08
                espacio_vertical = alto * 0.12

                rect = pygame.Rect(ancho // 2 - ancho_boton // 2,
                                   int(alto * 0.3 + i * espacio_vertical),
                                   int(ancho_boton), int(alto_boton))
                color_fondo = config.HOVER if rect.collidepoint(cursor_x, cursor_y) else config.FONDO_BOTON
                texto_traducido = config.traductor.t(opcion["text_key"])
                rect_boton = self.dibujar_boton(pantalla, rect, texto_traducido, config.fuente, color_fondo)

                if rect.collidepoint(cursor_x, cursor_y) and clic_activo:
                    texto_traducido = config.traductor.t(opcion["text_key"])
                    self.camara.pausar_cursor()
                    pygame.time.delay(200)
                    self.voz.decir_texto(texto_traducido)
                    return opcion["estado"]

            mano_detectada = self.camara.inactividad < 30
            self.mostrar_mensaje_ayuda(pantalla, mano_detectada)

            try:
                dibujar_cursor_unificado(pantalla, cursor_x, cursor_y, modo_ocular=True, ancho=ancho, alto=alto)
            except Exception as e:
                pygame.draw.circle(pantalla, config.ROJO, (cursor_x, cursor_y), 10, 2)
                pygame.draw.line(pantalla, config.ROJO, (cursor_x - 15, cursor_y), (cursor_x + 15, cursor_y), 2)
                pygame.draw.line(pantalla, config.ROJO, (cursor_x, cursor_y - 15), (cursor_x, cursor_y + 15), 2)

            pygame.display.flip()
            reloj.tick(30)

        return "salir"


if __name__ == "__main__":
    test_pantalla = pygame.display.set_mode((800, 600))
    c = ManejoCamara(ancho=800, alto=600, modo_ocular=True)
    menu = MenuPrincipal(1, c)
    menu.ejecutar()
    pygame.quit()
    sys.exit()