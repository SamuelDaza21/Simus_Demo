import pygame
import sys
import os
import platform
import core.config as config
from core.ManejoCamara import ManejoCamara
from ui.Inicio import SistemaTTS
from api.APICliente import APICliente
from logic.cursor import dibujar_cursor_unificado
from ui.dibujo_ui import dibujar_boton_redondeado
from core.shortcuts import aplicar_atajo_camara, procesar_atajos_globales
from core.paths import imagen
from ui.barra_menu import BarraInferior

api = APICliente()

if not pygame.mixer.get_init():
    try:
        pygame.mixer.init()
        print("[CONFIG] Sonido inicializado")
    except:
        print("[CONFIG] No se pudo inicializar sonido")

# ----------------- Selector de idioma adaptado para clic de cámara -----------------
class LanguageSelector:
    def __init__(self, x, y, w=50, h=50):
        self.rect = pygame.Rect(x, y, w, h)
        self.idiomas = ["es", "en", "fr"]
        self.mapeo_banderas = {
            "es": "espanol.png",
            "en": "ingles.png",
            "fr": "frances.png"
        }
        self.banderas = {}
        self.activo = False
        self.seleccionado = 0
        self.opciones_rects = []
        self.cargar_banderas(w-10, h-10)
        self.cursor_sobre = False

    def cargar_banderas(self, w, h):
        for idioma, archivo in self.mapeo_banderas.items():
            try:
                ruta = imagen(f"Traductor/{archivo}")
                bandera = pygame.image.load(ruta).convert_alpha()
                self.banderas[idioma] = pygame.transform.scale(bandera, (w, h))
            except Exception as e:
                print(f"[WARNING] Bandera {idioma} no cargada: {e}")
                superficie = pygame.Surface((w, h), pygame.SRCALPHA)
                pygame.draw.rect(superficie, (100, 150, 255), (0, 0, w, h))
                self.banderas[idioma] = superficie

    def update(self):
        self.opciones_rects = []
        if self.activo:
            espaciado = self.rect.h + 5
            for i in range(len(self.idiomas)):
                rect_opcion = pygame.Rect(
                    self.rect.x,
                    self.rect.y + i * espaciado,
                    self.rect.w,
                    self.rect.h
                )
                self.opciones_rects.append(rect_opcion)

    def manejar_clic_camara(self, cursor_x, cursor_y, clic_activo):
        if not clic_activo:
            return False
        if self.activo:
            self.update()
            for i, rect in enumerate(self.opciones_rects):
                if rect.collidepoint(cursor_x, cursor_y):
                    self.seleccionado = i
                    config.cambiar_idioma(self.idiomas[i])
                    self.activo = False
                    return True
            self.activo = False
            return True
        else:
            if self.rect.collidepoint(cursor_x, cursor_y):
                self.activo = True
                self.update()
                return True
        return False

    def draw(self, surf):
        pygame.draw.rect(surf, (255, 255, 255), self.rect, border_radius=8)
        pygame.draw.rect(surf, (150, 150, 150), self.rect, 2, border_radius=8)
        idioma_actual = self.idiomas[self.seleccionado]
        if idioma_actual in self.banderas:
            bandera = self.banderas[idioma_actual]
            x = self.rect.x + (self.rect.w - bandera.get_width()) // 2
            y = self.rect.y + (self.rect.h - bandera.get_height()) // 2
            surf.blit(bandera, (x, y))

    def draw_opciones(self, surf):
        if not self.activo:
            return
        if self.opciones_rects:
            total_h = sum(r.h for r in self.opciones_rects) + (len(self.opciones_rects) - 1) * 5
            bg_rect = pygame.Rect(
                self.opciones_rects[0].x - 2,
                self.opciones_rects[0].y - 2,
                self.opciones_rects[0].w + 4,
                total_h + 4
            )
            pygame.draw.rect(surf, (240, 240, 240), bg_rect, border_radius=8)
            pygame.draw.rect(surf, (150, 150, 150), bg_rect, 2, border_radius=8)
        for i, (idioma, rect_opcion) in enumerate(zip(self.idiomas, self.opciones_rects)):
            if i == self.seleccionado:
                pygame.draw.rect(surf, (200, 220, 255), rect_opcion, border_radius=5)
            pygame.draw.rect(surf, (180, 180, 180), rect_opcion, 2, border_radius=5)
            if idioma in self.banderas:
                bandera = self.banderas[idioma]
                x = rect_opcion.x + (rect_opcion.w - bandera.get_width()) // 2
                y = rect_opcion.y + (rect_opcion.h - bandera.get_height()) // 2
                surf.blit(bandera, (x, y))

# ----------------- Clase Configuracion -----------------
class Configuracion:
    def __init__(self, camara_existente=None, gestor_musica=None, ID_Sesion=None):
        self.gestor_musica = gestor_musica
        self.ID_Sesion = ID_Sesion
        self.voz = SistemaTTS()
        if camara_existente:
            self.camara = camara_existente
        else:
            self.camara = ManejoCamara(ancho=800, alto=600, modo_ocular=True)
        self.fondo = None
        self.pantalla = None
        self.ancho = 800
        self.alto = 600
        self.barra = None

    def dibujar_boton(self, pantalla, rect, texto, color_fondo=config.FONDO_BOTON, color_borde=config.BORDE_BOTON):
        return dibujar_boton_redondeado(
            pantalla, rect, texto, config.fuente_pequena, color_fondo, color_borde, config.COLOR_TEXTO,
            border_radius=10, grosor_borde=4
        )

    def barra_volumen(self, pantalla, rect, valor, cursor_x, cursor_y, clic, relleno=config.BARRA):
        pygame.draw.rect(pantalla, (200, 200, 200), rect, border_radius=5)
        ancho_relleno = int(rect.width * valor)
        rect_relleno = pygame.Rect(rect.x, rect.y, ancho_relleno, rect.height)
        pygame.draw.rect(pantalla, relleno, rect_relleno, border_radius=5)
        pygame.draw.rect(pantalla, config.BORDE_BOTON, rect, 2, border_radius=5)
        porcentaje = int(valor * 100)
        texto = config.render_text(f"{porcentaje}%", config.fuente_pequena, config.COLOR_TEXTO)
        texto_rect = texto.get_rect(center=rect.center)
        pantalla.blit(texto, texto_rect)
        if rect.collidepoint(cursor_x, cursor_y) and clic:
            nuevo_valor = (cursor_x - rect.x) / rect.width
            return max(0.0, min(1.0, nuevo_valor))
        return valor

    def _truncar_texto(self, texto, fuente, max_ancho):
        texto_original = texto
        if fuente.render(texto_original, True, config.COLOR_TEXTO).get_width() <= max_ancho:
            return texto_original
        while len(texto_original) > 3:
            texto_original = texto_original[:-1]
            if fuente.render(texto_original + "...", True, config.COLOR_TEXTO).get_width() <= max_ancho:
                return texto_original + "..."
        return texto[:5] + "..."

    def ejecutar_configuracion(self):
        self.pantalla = pygame.display.get_surface()
        if self.pantalla is None:
            print("[ERROR] No se pudo obtener pantalla en Configuracion")
            return "menu_principal"
        self.ancho, self.alto = self.pantalla.get_size()

        # Obtener ID de usuario a partir de la sesión actual
        id_usuario = None
        if self.ID_Sesion:
            id_usuario = api.obtener_id_usuario_desde_sesion(self.ID_Sesion)
            print(f"[CONFIG] ID_usuario obtenido: {id_usuario}")

        # Cargar configuración guardada si existe
        config_guardada = None
        if id_usuario:
            config_guardada = api.obtener_configuracion_usuario(id_usuario)
            if config_guardada:
                print(f"[CONFIG] Configuración cargada: {config_guardada}")
                # Aplicar idioma
                idioma_guardado = config_guardada.get("idioma", "es")
                if idioma_guardado != config.traductor.get_current_language():
                    config.cambiar_idioma(idioma_guardado)
                # Aplicar volúmenes (BD almacena 0-100, gestor usa 0.0-1.0)
                vol_mus = config_guardada.get("volumen_musica", 50) / 100.0
                vol_ef = config_guardada.get("volumen_efectos", 80) / 100.0
                if self.gestor_musica:
                    self.gestor_musica.volumen_musica = vol_mus
                    self.gestor_musica.volumen_efectos = vol_ef
                    self.gestor_musica.establecer_volumen_musica(vol_mus)
                    self.gestor_musica.establecer_volumen_efectos(vol_ef)
            else:
                # Si no hay configuración, guardar los valores actuales por defecto
                vol_mus_actual = self.gestor_musica.volumen_musica if self.gestor_musica else 0.5
                vol_ef_actual = self.gestor_musica.volumen_efectos if self.gestor_musica else 0.8
                api.guardar_configuracion_usuario(
                    id_usuario,
                    idioma=config.traductor.get_current_language(),
                    volumen_musica=int(vol_mus_actual * 100),
                    volumen_efectos=int(vol_ef_actual * 100)
                )

        try:
            fondo_img = pygame.image.load(imagen("General/Configuracion.png"))
            self.fondo = pygame.transform.scale(fondo_img, (self.ancho, self.alto))
        except:
            self.fondo = None
            print("[CONFIG] Fondo no encontrado, usando color sólido")

        # Selector de idioma (con margen desde la esquina)
        selector_margen = 20
        selector_idioma = LanguageSelector(self.ancho - 70, selector_margen)
        # Sincronizar el selector con el idioma actual
        idioma_actual = config.traductor.get_current_language()
        if idioma_actual in selector_idioma.idiomas:
            selector_idioma.seleccionado = selector_idioma.idiomas.index(idioma_actual)

        # Crear la barra inferior autónoma
        self.barra = BarraInferior(
            camara=self.camara,
            gestor_musica=self.gestor_musica,
            decir_texto=self.voz.decir_texto,
            ID_sesion=self.ID_Sesion
        )

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

        ejecutando = True
        control_clic = False
        reloj = pygame.time.Clock()
        menu_abierto = False

        barra_musica = pygame.Rect(self.ancho // 2 - 150, int(self.alto * 0.35), 300, 30)
        barra_efectos = pygame.Rect(self.ancho // 2 - 150, int(self.alto * 0.45), 300, 30)
        boton_menu = pygame.Rect(self.ancho // 2 - 150, int(self.alto * 0.55), 300, 50)

        cursor_x, cursor_y = self.ancho // 2, self.alto // 2
        clic_activo = False

        while ejecutando:
            try:
                cursor_x, cursor_y, clic_camara = self.camara.obtener_posicion_y_clic()
                if clic_camara and not control_clic:
                    clic_activo = True
                    control_clic = True
                elif not clic_camara:
                    control_clic = False
                    clic_activo = False
            except Exception as e:
                cursor_x, cursor_y = pygame.mouse.get_pos()
                clic_activo = pygame.mouse.get_pressed()[0] and not control_clic
                control_clic = pygame.mouse.get_pressed()[0]

            # Manejo del selector de idioma (con cámara)
            if clic_activo:
                if selector_idioma.activo:
                    selector_idioma.update()
                    clic_consumido = False
                    for i, rect in enumerate(selector_idioma.opciones_rects):
                        if rect.collidepoint(cursor_x, cursor_y):
                            selector_idioma.seleccionado = i
                            nuevo_idioma = selector_idioma.idiomas[i]
                            config.cambiar_idioma(nuevo_idioma)
                            # Guardar en BD
                            if id_usuario:
                                api.guardar_configuracion_usuario(id_usuario, idioma=nuevo_idioma)
                            selector_idioma.activo = False
                            clic_consumido = True
                            break
                    if not clic_consumido:
                        selector_idioma.activo = False
                    clic_activo = False
                else:
                    if selector_idioma.rect.collidepoint(cursor_x, cursor_y):
                        selector_idioma.activo = True
                        selector_idioma.update()
                        clic_activo = False

            # Eventos de pygame
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    ejecutando = False
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
                        ejecutando = False
                    elif evento.key == pygame.K_c:
                        self.camara.calibrar()
                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    if selector_idioma.rect.collidepoint(evento.pos):
                        selector_idioma.activo = not selector_idioma.activo
                        if selector_idioma.activo:
                            selector_idioma.update()
                    elif selector_idioma.activo:
                        selector_idioma.update()
                        for i, rect in enumerate(selector_idioma.opciones_rects):
                            if rect.collidepoint(evento.pos):
                                selector_idioma.seleccionado = i
                                nuevo_idioma = selector_idioma.idiomas[i]
                                config.cambiar_idioma(nuevo_idioma)
                                if id_usuario:
                                    api.guardar_configuracion_usuario(id_usuario, idioma=nuevo_idioma)
                                selector_idioma.activo = False
                                break
                        else:
                            selector_idioma.activo = False

            # Dibujar fondo
            if self.fondo:
                self.pantalla.blit(self.fondo, (0, 0))
            else:
                self.pantalla.fill((50, 50, 50))

            # Textos de volumen (usando fuente grande para los títulos)
            txt_musica = config.render_text(config.traductor.t("VOLUMEN MÚSICA"), config.fuente, config.COLOR_TEXTO)
            self.pantalla.blit(txt_musica, (self.ancho // 2 - txt_musica.get_width() // 2, int(self.alto * 0.3)))
            txt_efectos = config.render_text(config.traductor.t("VOLUMEN EFECTOS"), config.fuente, config.COLOR_TEXTO)
            self.pantalla.blit(txt_efectos, (self.ancho // 2 - txt_efectos.get_width() // 2, int(self.alto * 0.4)))

            # Barras de volumen y guardado en BD al cambiar
            nuevo_vol_mus = self.barra_volumen(
                self.pantalla, barra_musica, self.gestor_musica.volumen_musica,
                cursor_x, cursor_y, clic_activo
            )
            if nuevo_vol_mus != self.gestor_musica.volumen_musica:
                self.gestor_musica.volumen_musica = nuevo_vol_mus
                self.gestor_musica.establecer_volumen_musica(nuevo_vol_mus)
                if id_usuario:
                    api.guardar_configuracion_usuario(id_usuario, volumen_musica=int(nuevo_vol_mus * 100))

            nuevo_vol_ef = self.barra_volumen(
                self.pantalla, barra_efectos, self.gestor_musica.volumen_efectos,
                cursor_x, cursor_y, clic_activo
            )
            if nuevo_vol_ef != self.gestor_musica.volumen_efectos:
                self.gestor_musica.volumen_efectos = nuevo_vol_ef
                self.gestor_musica.establecer_volumen_efectos(nuevo_vol_ef)
                if id_usuario:
                    api.guardar_configuracion_usuario(id_usuario, volumen_efectos=int(nuevo_vol_ef * 100))

            # Texto del botón de cambio de canción
            cancion_actual = self.gestor_musica.cancion_actual or config.traductor.t("Sin música")
            texto_boton = config.traductor.t("Pista") + f": {cancion_actual}"
            max_ancho_boton = boton_menu.width - 20
            texto_truncado = self._truncar_texto(texto_boton, config.fuente, max_ancho_boton)
            self.dibujar_boton(self.pantalla, boton_menu, texto_truncado)

            # Menú desplegable de canciones
            if boton_menu.collidepoint(cursor_x, cursor_y) and clic_activo:
                menu_abierto = not menu_abierto
                pygame.time.delay(200)
                clic_activo = False

            if menu_abierto and self.gestor_musica.canciones:
                alto_opcion = 40
                for i, nombre_cancion in enumerate(self.gestor_musica.canciones.keys()):
                    rect_opcion = pygame.Rect(boton_menu.x, boton_menu.y + (i + 1) * alto_opcion,
                                              boton_menu.width, alto_opcion)
                    color = (180, 220, 255) if nombre_cancion == self.gestor_musica.cancion_actual else config.FONDO_BOTON
                    pygame.draw.rect(self.pantalla, color, rect_opcion, border_radius=5)
                    pygame.draw.rect(self.pantalla, config.BORDE_BOTON, rect_opcion, 1, border_radius=5)
                    texto = config.fuente_muy_pequena.render(nombre_cancion, True, config.COLOR_TEXTO)
                    texto_rect = texto.get_rect(center=rect_opcion.center)
                    self.pantalla.blit(texto, texto_rect)
                    if rect_opcion.collidepoint(cursor_x, cursor_y) and clic_activo:
                        self.gestor_musica.cambiar_cancion(nombre_cancion)
                        clic_activo = False
                        menu_abierto = False

            # Dibujar selector de idioma
            selector_idioma.update()
            selector_idioma.draw(self.pantalla)
            selector_idioma.draw_opciones(self.pantalla)

            # Barra inferior
            self.barra.actualizar_visibilidad((cursor_x, cursor_y), self.alto)
            self.barra.dibujar(self.pantalla, (cursor_x, cursor_y))
            destino = self.barra.manejar_clic((cursor_x, cursor_y), clic_activo)
            if destino:
                self.camara.pausar_cursor()
                return destino

            # Dibujar cursor
            try:
                dibujar_cursor_unificado(self.pantalla, cursor_x, cursor_y, modo_ocular=True,
                                         ancho=self.ancho, alto=self.alto)
            except Exception as e:
                pygame.draw.circle(self.pantalla, config.ROJO, (cursor_x, cursor_y), 10, 2)
                pygame.draw.line(self.pantalla, config.ROJO, (cursor_x - 15, cursor_y), (cursor_x + 15, cursor_y), 2)
                pygame.draw.line(self.pantalla, config.ROJO, (cursor_x, cursor_y - 15), (cursor_x, cursor_y + 15), 2)

            pygame.display.flip()
            reloj.tick(30)

        self.camara.pausar_cursor()
        return "menu_principal"