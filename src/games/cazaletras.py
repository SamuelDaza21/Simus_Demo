# -------------------------CAZA LETRAS (INTERNACIONALIZADO)-------------------------
import pygame
import random
import os
import sys
import core.config as config
from core.init_pygame import *
from logic.cursor import ControladorCursor
from core.ManejoCamara import ManejoCamara
from core.Musica import *
from api.APICliente import APICliente
from logic.cursor import dibujar_cursor_unificado
from games.base_game import BaseGame

api = APICliente()


class CazaLetras(BaseGame):
    def __init__(self, id_sesion):
        super().__init__(id_sesion, "Caza letras")

    # ---------- MÉTODOS DE LÓGICA ----------
    def preparar_juego(self):
        """Selecciona una palabra aleatoria según el idioma actual."""
        # Obtener idioma actual
        try:
            idioma = config.traductor.get_current_language()
        except:
            idioma = "es"

        # Diccionario de palabras por idioma para cada concepto (imagen)
        # La clave del diccionario es el nombre base de la imagen (en español original)
        self.palabras_por_idioma = {
            "perro": {"es": "perro", "en": "dog", "fr": "chien"},
            "gato": {"es": "gato", "en": "cat", "fr": "chat"},
            "pájaro": {"es": "pájaro", "en": "bird", "fr": "oiseau"},
            "pez": {"es": "pez", "en": "fish", "fr": "poisson"},
            "mariposa": {"es": "mariposa", "en": "butterfly", "fr": "papillon"},
            "manzana": {"es": "manzana", "en": "apple", "fr": "pomme"},
            "naranja": {"es": "naranja", "en": "orange", "fr": "orange"},
            "uva": {"es": "uva", "en": "grape", "fr": "raisin"},
            "pan": {"es": "pan", "en": "bread", "fr": "pain"},
            "queso": {"es": "queso", "en": "cheese", "fr": "fromage"},
            "pelota": {"es": "pelota", "en": "ball", "fr": "balle"},
            "libro": {"es": "libro", "en": "book", "fr": "livre"},
            "casa": {"es": "casa", "en": "house", "fr": "maison"},
            "auto": {"es": "auto", "en": "car", "fr": "voiture"},
            "sol": {"es": "sol", "en": "sun", "fr": "soleil"},
            "árbol": {"es": "árbol", "en": "tree", "fr": "arbre"},
            "flor": {"es": "flor", "en": "flower", "fr": "fleur"},
            "hoja": {"es": "hoja", "en": "leaf", "fr": "feuille"},
            "nube": {"es": "nube", "en": "cloud", "fr": "nuage"},
            "luna": {"es": "luna", "en": "moon", "fr": "lune"},
        }

        # Filtrar conceptos que tienen imagen cargada
        conceptos_disponibles = [c for c in self.palabras_por_idioma.keys() if c in self.imagenes_cargadas]
        if not conceptos_disponibles:
            return

        # Elegir un concepto aleatorio
        self.concepto_actual = random.choice(conceptos_disponibles)
        # Obtener la palabra en el idioma actual
        self.palabra_actual = self.palabras_por_idioma[self.concepto_actual].get(idioma, self.concepto_actual)
        # Crear palabra oculta con guiones
        self.palabra_oculta = ["_" for _ in self.palabra_actual]
        # Reiniciar listas de letras
        self.letras_correctas = []
        self.letras_incorrectas = []
        # Generar letras disponibles
        self.generar_letras_disponibles()
        # Reiniciar temporizador
        self.tiempo_ultimo_cambio = pygame.time.get_ticks()

    def generar_letras_disponibles(self):
        # Abecedario básico (sin ñ, pero se puede añadir)
        abecedario = "abcdefghijklmnopqrstuvwxyz"
        # Letras únicas de la palabra actual
        letras_palabra = list(set(self.palabra_actual))
        letras_sin_adivinar = [l for l in letras_palabra if l not in self.palabra_oculta]
        if not letras_sin_adivinar:
            letras_sin_adivinar = letras_palabra

        # Asegurar al menos 2 letras correctas (si hay suficientes)
        num_correctas = min(2, len(letras_sin_adivinar))
        correctas_lista = random.sample(letras_sin_adivinar, num_correctas) if num_correctas > 0 else []
        # Seleccionar letras incorrectas (que no están en la palabra)
        letras_incorrectas_lista = [l for l in abecedario if l not in letras_palabra]
        num_incorrectas = 6 - num_correctas
        if num_incorrectas > 0 and letras_incorrectas_lista:
            incorrectas_lista = random.sample(letras_incorrectas_lista, min(num_incorrectas, len(letras_incorrectas_lista)))
        else:
            incorrectas_lista = []
        # Combinar y mezclar
        self.letras_disponibles = correctas_lista + incorrectas_lista
        random.shuffle(self.letras_disponibles)

        # Asignar posiciones fijas a las letras
        self.letras_posiciones = {}
        for i, letra in enumerate(self.letras_disponibles):
            if i < len(self.posiciones_fijas):
                self.letras_posiciones[letra] = self.posiciones_fijas[i]

    def actualizar_letras_disponibles(self):
        if pygame.time.get_ticks() - self.tiempo_ultimo_cambio > self.intervalo_cambio:
            self.generar_letras_disponibles()
            self.tiempo_ultimo_cambio = pygame.time.get_ticks()

    def verificar_letra(self, letra):
        if letra in self.palabra_actual:
            self.letra_animando = letra
            self.animacion_progreso = 0
            self.aciertos += 1
            # Posición objetivo (primer índice donde aparece la letra)
            indices = [i for i, ch in enumerate(self.palabra_actual) if ch == letra]
            self.posicion_objetivo = (400 + indices[0] * 70, 250)
            self.posicion_inicial = self.letras_posiciones[letra]
        else:
            self.dibujo_globo = self.vidas - 1
            self.globo_progreso = 0
            if self.gestor_musica:
                self.gestor_musica.reproducir_sonido("globo")
            if letra in self.letras_disponibles:
                self.letras_disponibles.remove(letra)
            if letra in self.letras_posiciones:
                del self.letras_posiciones[letra]
            self.letras_incorrectas.append(letra)
            self.vidas -= 1
            self.error += 1

    def actualizar_animacion(self):
        if self.letra_animando and self.animacion_progreso < self.animacion_duracion:
            self.animacion_progreso += 1
            prog = self.animacion_progreso / self.animacion_duracion
            x = self.posicion_inicial[0] + (self.posicion_objetivo[0] - self.posicion_inicial[0]) * prog
            y = self.posicion_inicial[1] + (self.posicion_objetivo[1] - self.posicion_inicial[1]) * prog
            self.letras_posiciones[self.letra_animando] = (x, y)
            if self.animacion_progreso >= self.animacion_duracion:
                for i, ch in enumerate(self.palabra_actual):
                    if ch == self.letra_animando:
                        self.palabra_oculta[i] = ch
                if self.letra_animando in self.letras_disponibles:
                    self.letras_disponibles.remove(self.letra_animando)
                if self.letra_animando in self.letras_posiciones:
                    del self.letras_posiciones[self.letra_animando]
                if "_" not in self.palabra_oculta:
                    ronda = (self.vidas * 10) + (len(self.letras_correctas) * 5)
                    self.puntaje_total += ronda
                    self.rondas_completas += 1
                    self.mensaje_final = config.traductor.t("Felicidades_puntos").format(puntos=ronda)
                    self.juego_activo = False
                    if self.gestor_musica:
                        self.gestor_musica.reproducir_sonido("correcto")
                    self.siguiente_ronda = pygame.time.get_ticks()
                    self.esperar_siguiente_ronda = True
                self.letra_animando = None

        if self.dibujo_globo is not None and self.globo_progreso < self.globo_duracion:
            self.globo_progreso += 1
            if self.globo_progreso >= self.globo_duracion:
                self.dibujo_globo = None
                if self.vidas <= 0:
                    self.mensaje_final = config.traductor.t("Game_over_palabra").format(palabra=self.palabra_actual)
                    self.juego_activo = False
                    if self.gestor_musica:
                        self.gestor_musica.reproducir_sonido("incorrecto")

        if self.esperar_siguiente_ronda and pygame.time.get_ticks() - self.siguiente_ronda > 3000:
            self.preparar_siguiente_ronda()

    def preparar_siguiente_ronda(self):
        self.esperar_siguiente_ronda = False
        self.juego_activo = True
        self.dibujo_globo = None
        self.preparar_juego()

    # ---------- DIBUJO DE INTERFAZ ----------
    def dibujar_interfaz(self, cursor_pos):
        self.pantalla.blit(self.fondo, (0, 0))
        # Recuadro imagen
        rect_img = pygame.Rect(50, 100, 300, 300)
        pygame.draw.rect(self.pantalla, self.COLOR_FONDO_B, rect_img, border_radius=20)
        pygame.draw.rect(self.pantalla, config.NEGRO, rect_img, 3, border_radius=20)
        if self.concepto_actual in self.imagenes_cargadas:
            img_data = self.imagenes_cargadas[self.concepto_actual]
            img_rect = img_data["imagen"].get_rect(center=rect_img.center)
            self.pantalla.blit(img_data["imagen"], img_rect)

        # Palabra oculta
        for i, letra in enumerate(self.palabra_oculta):
            x = 400 + i * 70
            y = 150
            rect = pygame.Rect(x, y, 60, 60)
            pygame.draw.rect(self.pantalla, config.FONDO_BOTON, rect, border_radius=10)
            pygame.draw.rect(self.pantalla, config.NEGRO, rect, 2, border_radius=10)
            if letra != "_":
                surf = config.render_text(letra, config.fuente, config.COLOR_TEXTO)
                self.pantalla.blit(surf, (x + 30 - surf.get_width()//2, y + 30 - surf.get_height()//2))

        # Letras disponibles
        for letra in self.letras_disponibles:
            if letra != self.letra_animando and letra in self.letras_posiciones:
                x, y = self.letras_posiciones[letra]
                rect = pygame.Rect(x - 40, y - 40, 80, 80)
                color = config.FONDO_BOTON
                if rect.collidepoint(cursor_pos):
                    color = config.HOVER
                sombra = pygame.Rect(x - 35, y - 35, 80, 80)
                pygame.draw.rect(self.pantalla, (0, 0, 0, 50), sombra, border_radius=15)
                pygame.draw.rect(self.pantalla, color, rect, border_radius=15)
                pygame.draw.rect(self.pantalla, config.NEGRO, rect, 3, border_radius=15)
                surf = config.render_text(letra, config.fuente, config.COLOR_TEXTO)
                self.pantalla.blit(surf, (x - surf.get_width()//2, y - surf.get_height()//2))

        # Letra animada
        if self.letra_animando and self.letra_animando in self.letras_posiciones and self.animacion_progreso < self.animacion_duracion:
            x, y = self.letras_posiciones[self.letra_animando]
            rect = pygame.Rect(x - 40, y - 40, 80, 80)
            pygame.draw.rect(self.pantalla, config.FONDO_BOTON, rect, border_radius=15)
            pygame.draw.rect(self.pantalla, config.NEGRO, rect, 3, border_radius=15)
            surf = config.render_text(self.letra_animando, config.fuente, config.COLOR_TEXTO)
            self.pantalla.blit(surf, (x - surf.get_width()//2, y - surf.get_height()//2))

        # Vidas (globos)
        for i in range(self.vidas):
            px = self.ancho - 220 - i * 70
            py = 500
            self.pantalla.blit(self.img_globo, (px, py))

        # Temporizador
        resto = (self.intervalo_cambio - (pygame.time.get_ticks() - self.tiempo_ultimo_cambio)) // 1000
        if resto < 0:
            resto = 0
        texto = config.traductor.t("Cambio_en_segundos").format(segundos=resto)
        surf = config.render_text(texto, config.fuente, config.COLOR_TEXTO)
        self.pantalla.blit(surf, (self.ancho - 350, 150))

        # Puntaje
        txt = config.traductor.t("Puntaje").format(puntos=self.puntaje_total)
        surf = config.render_text(txt, config.fuente, config.COLOR_TEXTO)
        self.pantalla.blit(surf, (self.ancho - 350, 100))

        # Rondas
        txt = config.traductor.t("Rondas").format(rondas=self.rondas_completas)
        surf = config.render_text(txt, config.fuente, config.COLOR_TEXTO)
        self.pantalla.blit(surf, (self.ancho - 350, 200))

        # Botón volver
        pygame.draw.rect(self.pantalla, config.FONDO_BOTON, self.boton_volver, border_radius=10)
        pygame.draw.rect(self.pantalla, config.NEGRO, self.boton_volver, 2, border_radius=10)
        txt = config.render_text(config.traductor.t("Volver"), config.fuente, config.COLOR_TEXTO)
        self.pantalla.blit(txt, (self.boton_volver.centerx - txt.get_width()//2,
                                 self.boton_volver.centery - txt.get_height()//2))

        # Animación de globo reventando
        for i in range(3):
            px = self.ancho - 220 - i * 70
            py = 500
            if i < self.vidas:
                self.pantalla.blit(self.img_globo, (px, py))
            elif i == self.dibujo_globo:
                t = 60 * (1 - self.globo_progreso / self.globo_duracion)
                if t > 0:
                    anim = pygame.transform.scale(self.img_globo, (int(t), int(t * 1.33)))
                    self.pantalla.blit(anim, (px + (60 - t)/2, py + (80 - t*1.33)/2))

        return self.boton_volver

    def mostrar_mensaje_final(self):
        overlay = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.pantalla.blit(overlay, (0, 0))
        msg = config.render_text(self.mensaje_final, config.fuente, config.BLANCO)
        self.pantalla.blit(msg, (self.ancho//2 - msg.get_width()//2, self.alto//2 - 50))
        pts = config.render_text(config.traductor.t("Puntaje_final").format(puntos=self.puntaje_total),
                                 config.fuente, config.BLANCO)
        self.pantalla.blit(pts, (self.ancho//2 - pts.get_width()//2, self.alto//2 + 20))
        inst = config.render_text(config.traductor.t("Volviendo_menu_juegos"), config.fuente, config.BLANCO)
        self.pantalla.blit(inst, (self.ancho//2 - inst.get_width()//2, self.alto//2 + 100))
        pygame.display.flip()
        pygame.time.delay(5000)

    # ---------- EJECUCIÓN PRINCIPAL ----------
    def ejecutar(self, camara, gestor_musica):
        self.enviar_backup_si_existe()
        self.camara = camara
        self.gestor_musica = gestor_musica
        self.resultado_temporal["id_sesion"] = self.id_sesion

        self.camara.reanudar_cursor()
        pygame.time.delay(800)
        try:
            for _ in range(10):
                _, _, clic = self.camara.obtener_posicion_y_clic()
                if clic:
                    pygame.time.delay(100)
        except:
            pass
        self.camara.calibrar()

        if not pygame.mixer.get_init():
            pygame.mixer.init()
        if self.gestor_musica and not pygame.mixer.music.get_busy():
            self.gestor_musica.iniciar_musica()

        # Obtener pantalla real
        self.pantalla = pygame.display.get_surface()
        if self.pantalla is None:
            print("[ERROR] No se pudo obtener pantalla en CazaLetras")
            return "menu_principal"
        self.ancho, self.alto = self.pantalla.get_size()
        self.reloj = pygame.time.Clock()

        self.COLOR_FONDO_B = (204, 130, 76)

        # Cargar fondo
        try:
            from core.paths import IMAGES
            ruta_fondo = os.path.join(IMAGES, "General", "fondo.png")
            img = pygame.image.load(ruta_fondo).convert()
            self.fondo = pygame.transform.scale(img, (self.ancho, self.alto))
        except:
            self.fondo = pygame.Surface((self.ancho, self.alto))
            self.fondo.fill((255, 255, 255))

        # Cargar imágenes de palabras (por concepto)
        self.imagenes_cargadas = {}
        conceptos = [
            "perro", "gato", "pájaro", "pez", "mariposa",
            "manzana", "naranja", "uva", "pan", "queso",
            "pelota", "libro", "casa", "auto", "sol",
            "árbol", "flor", "hoja", "nube", "luna"
        ]
        carpeta = IMAGES
        for concepto in conceptos:
            archivo = f"Encuentra-y-Aprende/{concepto}.png"
            ruta = os.path.join(carpeta, archivo)
            try:
                if os.path.exists(ruta):
                    img = pygame.image.load(ruta)
                    if img.get_alpha():
                        img = img.convert_alpha()
                    else:
                        img = img.convert()
                    self.imagenes_cargadas[concepto] = {
                        "imagen": pygame.transform.scale(img, (250, 250)),
                        "categoria": "general"
                    }
                else:
                    # Placeholder
                    surf = pygame.Surface((250, 250), pygame.SRCALPHA)
                    pygame.draw.rect(surf, (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200), 200),
                                     (0, 0, 250, 250), border_radius=20)
                    txt = config.render_text(concepto, config.fuente, config.NEGRO)
                    txt_rect = txt.get_rect(center=(125, 125))
                    surf.blit(txt, txt_rect)
                    self.imagenes_cargadas[concepto] = {"imagen": surf, "categoria": "placeholder"}
            except Exception as e:
                print(f"Error cargando imagen {concepto}: {e}")

        # Globo
        try:
            ruta_globo = os.path.join(carpeta, "Encuentra-y-Aprende", "globo.png")
            self.img_globo = pygame.image.load(ruta_globo).convert_alpha()
            self.img_globo = pygame.transform.scale(self.img_globo, (200, 250))
        except:
            self.img_globo = pygame.Surface((200, 250), pygame.SRCALPHA)
            pygame.draw.circle(self.img_globo, (255, 255, 255), (100, 100), 30)
            pygame.draw.rect(self.img_globo, (255, 255, 255), (88, 55, 4, 25))

        # Estado inicial
        self.vidas = 3
        self.palabra_actual = ""
        self.palabra_oculta = []
        self.letras_correctas = []
        self.letras_incorrectas = []
        self.letras_disponibles = []
        self.letras_posiciones = {}
        self.tiempo_ultimo_cambio = 0
        self.intervalo_cambio = 10000
        self.juego_activo = True
        self.mensaje_final = ""
        self.letra_animando = None
        self.animacion_progreso = 0
        self.animacion_duracion = 30
        self.globo_progreso = 0
        self.globo_duracion = 20
        self.dibujo_globo = None
        self.esperar_siguiente_ronda = False
        self.siguiente_ronda = 0
        self.puntaje_total = 0
        self.aciertos = 0
        self.error = 0
        self.rondas_completas = 0
        self.posicion_inicial = (0, 0)
        self.posicion_objetivo = (0, 0)

        # Posiciones fijas de letras
        self.posiciones_fijas = []
        espacio = 100
        inicio_x = (self.ancho - 6 * espacio) // 2
        y = self.alto - 250
        for i in range(6):
            self.posiciones_fijas.append((inicio_x + i * espacio, y))

        self.boton_volver = pygame.Rect(50, self.alto - 80, 150, 50)
        self.preparar_juego()

        ejecutando = True
        control_clic = False

        try:
            while ejecutando:
                datos = self.camara.obtener_posicion_y_clic()
                if datos:
                    cx, cy, clic_cam = datos
                else:
                    cx, cy, clic_cam = self.ancho // 2, self.alto // 2, False

                if clic_cam and not control_clic:
                    clic_activo = True
                    control_clic = True
                elif not clic_cam:
                    control_clic = False
                    clic_activo = False

                for evento in pygame.event.get():
                    if evento.type == pygame.QUIT:
                        ejecutando = False
                    elif evento.type == pygame.KEYDOWN:
                        if evento.key == pygame.K_ESCAPE:
                            ejecutando = False
                        elif evento.key == pygame.K_c:
                            self.camara.calibrar()

                self.actualizar_animacion()

                if self.juego_activo and not self.esperar_siguiente_ronda:
                    self.actualizar_letras_disponibles()
                    self.dibujar_interfaz((cx, cy))
                    if clic_activo and not self.letra_animando:
                        if self.boton_volver.collidepoint(cx, cy):
                            self.camara.pausar_cursor()
                            ejecutando = False
                        else:
                            for letra in self.letras_disponibles:
                                if letra in self.letras_posiciones:
                                    lx, ly = self.letras_posiciones[letra]
                                    rect = pygame.Rect(lx - 40, ly - 40, 80, 80)
                                    if rect.collidepoint(cx, cy):
                                        self.verificar_letra(letra)
                                        break
                else:
                    self.dibujar_interfaz((cx, cy))
                    if not self.juego_activo and not self.esperar_siguiente_ronda and "Game Over" in self.mensaje_final and self.dibujo_globo is None:
                        self.mostrar_mensaje_final()
                        ejecutando = False
                    if clic_activo and self.boton_volver.collidepoint(cx, cy):
                        ejecutando = False

                dibujar_cursor_unificado(self.pantalla, cx, cy, modo_ocular=True, ancho=self.ancho, alto=self.alto)
                pygame.display.flip()
                self.reloj.tick(60)

        finally:
            self.resultado_temporal["puntaje"] = self.puntaje_total
            self.resultado_temporal["aciertos"] = self.aciertos
            self.resultado_temporal["errores"] = self.error
            self.guardar_resultado_final()
            print("👋 Juego terminado. Retornando al menú...")


# Funciones wrapper para compatibilidad
def ejecutar_juego_ahorcado(camara, id_sesion):
    juego = CazaLetras(id_sesion)
    return juego.ejecutar(camara, gestor_musica)


def iniciar_ahorcado(camara, music_manager):
    return ejecutar_juego_ahorcado(camara, 1)


if __name__ == "__main__":
    controlador = ControladorCursor()
    camara = controlador.obtener_camara()
    ejecutar_juego_ahorcado(camara, 23)
    controlador.pausar_cursor()