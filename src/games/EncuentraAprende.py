import os
import random
import sys
import json
import atexit

import pygame
import pygame.draw

import core.config as config
from core.paths import IMAGES
from core.ManejoCamara import ManejoCamara
from core.Musica import *
from api.APICliente import APICliente
from logic.cursor import dibujar_cursor_unificado
from games.base_game import BaseGame

api = APICliente()


def ejecutar_encuentra_y_aprende(camara, id_sesion):
    game = BaseGame(id_sesion, "Encuentra y aprende")
    game.enviar_backup_si_existe()

    reloj = pygame.time.Clock()
    frames_sin_clic = 0
    vidas = 3
    fin_juego = False

    while frames_sin_clic < 15:
        try:
            _, _, clic_activo = camara.obtener_posicion_y_clic()
            if not clic_activo:
                frames_sin_clic += 1
            else:
                frames_sin_clic = 0
        except:
            frames_sin_clic += 1
        reloj.tick(30)

    camara.calibrar()
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    if gestor_musica and not pygame.mixer.music.get_busy():
        gestor_musica.iniciar_musica()

    # Obtener la pantalla real (no crear una nueva)
    pantalla = pygame.display.get_surface()
    if pantalla is None:
        print("[ERROR] No se pudo obtener la pantalla en EncuentraAprende")
        return
    ANCHO, ALTO = pantalla.get_size()
    reloj = pygame.time.Clock()

    # Cargar imágenes
    imagenes = {}
    categorias_imagenes = [
        {"nombre": "perro", "archivo": "Encuentra-y-Aprende/perro.png", "categoria": "animales"},
        {"nombre": "gato", "archivo": "Encuentra-y-Aprende/gato.png", "categoria": "animales"},
        {"nombre": "pájaro", "archivo": "Encuentra-y-Aprende/pajaro.png", "categoria": "animales"},
        {"nombre": "pez", "archivo": "Encuentra-y-Aprende/pez.png", "categoria": "animales"},
        {"nombre": "mariposa", "archivo": "Encuentra-y-Aprende/mariposa.png", "categoria": "animales"},
        {"nombre": "manzana", "archivo": "Encuentra-y-Aprende/manzana.png", "categoria": "alimentos"},
        {"nombre": "naranja", "archivo": "Encuentra-y-Aprende/naranja.png", "categoria": "alimentos"},
        {"nombre": "uva", "archivo": "Encuentra-y-Aprende/uva.png", "categoria": "alimentos"},
        {"nombre": "pan", "archivo": "Encuentra-y-Aprende/pan.png", "categoria": "alimentos"},
        {"nombre": "queso", "archivo": "Encuentra-y-Aprende/queso.png", "categoria": "alimentos"},
        {"nombre": "pelota", "archivo": "Encuentra-y-Aprende/pelota.png", "categoria": "objetos"},
        {"nombre": "libro", "archivo": "Encuentra-y-Aprende/libro.png", "categoria": "objetos"},
        {"nombre": "casa", "archivo": "Encuentra-y-Aprende/casa.png", "categoria": "objetos"},
        {"nombre": "auto", "archivo": "Encuentra-y-Aprende/auto.png", "categoria": "objetos"},
        {"nombre": "sol", "archivo": "Encuentra-y-Aprende/sol.png", "categoria": "objetos"},
        {"nombre": "árbol", "archivo": "Encuentra-y-Aprende/arbol.png", "categoria": "naturaleza"},
        {"nombre": "flor", "archivo": "Encuentra-y-Aprende/flor.png", "categoria": "naturaleza"},
        {"nombre": "hoja", "archivo": "Encuentra-y-Aprende/hoja.png", "categoria": "naturaleza"},
        {"nombre": "nube", "archivo": "Encuentra-y-Aprende/nube.png", "categoria": "naturaleza"},
        {"nombre": "luna", "archivo": "Encuentra-y-Aprende/luna.png", "categoria": "naturaleza"},
    ]

    def obtener_ruta_imagen(ruta_relativa):
        ruta_relativa = ruta_relativa.replace('\\', '/').lstrip('/')
        if ruta_relativa.lower().startswith('assets/'):
            ruta_relativa = ruta_relativa.split('/', 1)[1]
        if ruta_relativa.lower().startswith('imagenes/'):
            ruta_relativa = ruta_relativa.split('/', 1)[1]
        return os.path.join(IMAGES, *ruta_relativa.split('/'))

    for img_info in categorias_imagenes:
        try:
            ruta = obtener_ruta_imagen(img_info["archivo"])
            if os.path.exists(ruta):
                imagen = pygame.image.load(ruta)
                if imagen.get_alpha():
                    imagen = imagen.convert_alpha()
                else:
                    imagen = imagen.convert()
                imagenes[img_info["nombre"]] = {
                    "imagen": pygame.transform.scale(imagen, (150, 150)),
                    "categoria": img_info["categoria"]
                }
            else:
                superficie = pygame.Surface((150, 150), pygame.SRCALPHA)
                color = (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200), 200)
                pygame.draw.rect(superficie, color, (0, 0, 150, 150), border_radius=20)
                texto = config.render_text(img_info["nombre"], config.fuente_pequena, config.NEGRO)
                texto_rect = texto.get_rect(center=(75, 75))
                superficie.blit(texto, texto_rect)
                imagenes[img_info["nombre"]] = {
                    "imagen": superficie,
                    "categoria": "placeholder"
                }
        except Exception as e:
            print(f"Error cargando {img_info['nombre']}: {e}")

    # Fuentes (usamos las de config)
    FUENTE = config.fuente
    fuente_texto = config.fuente_pequena
    fuente_puntuacion = config.fuente

    # Estado del juego
    puntuacion = 0
    error = 0
    aciertos = 0
    ronda_actual = 1
    juego_activo = True
    control_clic = False

    tiempo_retroalimentacion = 0
    texto_retroalimentacion = ""
    color_retroalimentacion = config.VERDE
    objetivo_actual = ""
    opciones_actuales = []
    boton_volver = pygame.Rect(50, ALTO - 80, 150, 50)

    def preparar_ronda():
        nonlocal objetivo_actual, opciones_actuales, tiempo_retroalimentacion, texto_retroalimentacion
        if len(imagenes) >= 3:
            objetivo_actual = random.choice(list(imagenes.keys()))
            opciones_posibles = list(imagenes.keys())
            opciones_posibles.remove(objetivo_actual)
            opciones_aleatorias = random.sample(opciones_posibles, 2)
            opciones_actuales = [objetivo_actual] + opciones_aleatorias
            random.shuffle(opciones_actuales)
            tiempo_retroalimentacion = 0
            texto_retroalimentacion = ""

    def mostrar_retroalimentacion(texto, color):
        nonlocal texto_retroalimentacion, color_retroalimentacion, tiempo_retroalimentacion
        texto_retroalimentacion = texto
        color_retroalimentacion = color
        tiempo_retroalimentacion = 90

    def verificar_seleccion(posicion_cursor):
        nonlocal puntuacion, ronda_actual, juego_activo, aciertos, error, vidas, fin_juego
        for i, opcion in enumerate(opciones_actuales):
            rect_opcion = pygame.Rect(200 + i * 300, 250, 200, 200)
            if rect_opcion.collidepoint(posicion_cursor):
                if opcion == objetivo_actual:
                    puntuacion += 10
                    aciertos += 1
                    ronda_actual += 1
                    mostrar_retroalimentacion(config.traductor.t("Correcto_puntos").format(puntos=10), config.VERDE)
                    if gestor_musica:
                        gestor_musica.reproducir_sonido("correcto")
                    pygame.time.delay(800)
                    preparar_ronda()
                else:
                    vidas -= 1
                    puntuacion = max(0, puntuacion - 5)
                    error += 1
                    mostrar_retroalimentacion(config.traductor.t("Incorrecto_puntos").format(puntos=5), config.ROJO)
                    if gestor_musica:
                        gestor_musica.reproducir_sonido("incorrecto")
                    if vidas <= 0:
                        fin_juego = True
                        juego_activo = False
                        return
                    pygame.time.delay(800)
                    preparar_ronda()
                break

    def dibujar_interfaz(posicion_cursor):
        # Fondo
        try:
            fondo_img = pygame.image.load(config.FONDO_PRINCIPAL).convert()
            fondo_img = pygame.transform.scale(fondo_img, (ANCHO, ALTO))
            pantalla.blit(fondo_img, (0, 0))
        except:
            pantalla.fill(config.COLOR_FONDO)

        # Instrucción traducida
        instruccion_texto = config.traductor.t("Encuentra").format(objetivo=objetivo_actual)
        instruccion = config.render_text(instruccion_texto, fuente_texto, config.NEGRO)
        pantalla.blit(instruccion, (ANCHO // 2 - instruccion.get_width() // 2, 120))

        # Opciones
        for i, opcion in enumerate(opciones_actuales):
            x = 200 + i * 300
            y = 250
            rect_opcion = pygame.Rect(x, y, 200, 200)
            color_marco = (221, 162, 105)  # #DDA269
            if rect_opcion.collidepoint(posicion_cursor):
                color_marco = (241, 182, 125)
            sombra_rect = pygame.Rect(x + 5, y + 5, 200, 200)
            pygame.draw.rect(pantalla, (0, 0, 0, 50), sombra_rect, border_radius=20)
            pygame.draw.rect(pantalla, color_marco, rect_opcion, border_radius=20)
            pygame.draw.rect(pantalla, config.NEGRO, rect_opcion, 3, border_radius=20)
            img_data = imagenes[opcion]
            img_rect = img_data["imagen"].get_rect(center=(x + 100, y + 100))
            pantalla.blit(img_data["imagen"], img_rect)

        # Vidas (círculos rojos)
        if juego_activo and not fin_juego:
            for i in range(vidas):
                vida_x = 1450 + i * 55
                vida_y = 70
                pygame.draw.circle(pantalla, config.ROJO, (vida_x, vida_y), 15)
                pygame.draw.circle(pantalla, config.NEGRO, (vida_x, vida_y), 15, 2)

        # Panel de información
        panel_rect = pygame.Rect(20, 20, 200, 120)
        pygame.draw.rect(pantalla, (221, 162, 105, 200), panel_rect, border_radius=15)
        pygame.draw.rect(pantalla, config.NEGRO, panel_rect, 2, border_radius=15)

        # Puntuación
        puntuacion_texto = config.render_text(f"Puntos: {puntuacion}", fuente_texto, config.NEGRO)
        pantalla.blit(puntuacion_texto, (40, 40))

        # Ronda
        ronda_texto = config.render_text(f"Ronda: {ronda_actual}", fuente_texto, config.NEGRO)
        pantalla.blit(ronda_texto, (40, 80))

        # Retroalimentación
        if tiempo_retroalimentacion > 0:
            retro = config.render_text(texto_retroalimentacion, fuente_puntuacion, color_retroalimentacion)
            pantalla.blit(retro, (ANCHO // 2 - retro.get_width() // 2, 500))

        # Botón volver
        pygame.draw.rect(pantalla, (221, 162, 105), boton_volver, border_radius=10)
        pygame.draw.rect(pantalla, config.NEGRO, boton_volver, 2, border_radius=10)
        volver_texto = config.render_text(config.traductor.t("Volver"), fuente_texto, config.NEGRO)
        pantalla.blit(volver_texto, (boton_volver.centerx - volver_texto.get_width() // 2,
                                     boton_volver.centery - volver_texto.get_height() // 2))

        return boton_volver

    def mostrar_resultados():
        overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        pantalla.blit(overlay, (0, 0))

        titulo = config.render_text(config.traductor.t("Juego_Terminado"), FUENTE, config.BLANCO)
        puntos = config.render_text(config.traductor.t("Puntuacion_final").format(puntos=puntuacion), FUENTE, config.BLANCO)
        instruccion = config.render_text(config.traductor.t("Volviendo_menu_juegos"), FUENTE, config.BLANCO)

        pantalla.blit(titulo, (ANCHO // 2 - titulo.get_width() // 2, ALTO // 2 - 150))
        pantalla.blit(puntos, (ANCHO // 2 - puntos.get_width() // 2, ALTO // 2 - 50))
        pantalla.blit(instruccion, (ANCHO // 2 - instruccion.get_width() // 2, ALTO // 2 + 50))

        pygame.display.flip()
        pygame.time.delay(3000)

    preparar_ronda()
    ejecutando = True
    cursor_x, cursor_y = ANCHO // 2, ALTO // 2

    try:
        while ejecutando and juego_activo:
            try:
                cursor_x, cursor_y, clic_camara = camara.obtener_posicion_y_clic()
                if clic_camara and not control_clic:
                    clic_activo = True
                    control_clic = True
                elif not clic_camara:
                    control_clic = False
                    clic_activo = False
            except Exception as e:
                print(f"Error cámara facial: {e}")
                cursor_x, cursor_y = camara.cursor_x, camara.cursor_y
                clic_activo = False

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    camara.pausar_cursor()
                    return
                elif evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        ejecutando = False
                    elif evento.key == pygame.K_c:
                        camara.calibrar()

            boton_volver = dibujar_interfaz((cursor_x, cursor_y))

            if clic_activo:
                if boton_volver.collidepoint(cursor_x, cursor_y):
                    camara.pausar_cursor()
                    ejecutando = False
                else:
                    verificar_seleccion((cursor_x, cursor_y))

            if tiempo_retroalimentacion > 0:
                tiempo_retroalimentacion -= 1

            try:
                dibujar_cursor_unificado(pantalla, cursor_x, cursor_y, modo_ocular=True, ancho=ANCHO, alto=ALTO)
            except:
                pygame.draw.circle(pantalla, config.ROJO, (cursor_x, cursor_y), 15, 3)

            pygame.display.flip()
            reloj.tick(60)

        if fin_juego:
            dibujar_interfaz((cursor_x, cursor_y))
            pygame.display.flip()
            pygame.time.delay(100)
            mostrar_resultados()

    finally:
        game.actualizar_resultados(puntaje=puntuacion, aciertos=aciertos, errores=error)
        try:
            api.registrar_resultado(id_sesion, "Encuentra y aprende", puntuacion, aciertos, error)
            print("✅ Resultado final enviado.")
        except Exception as e:
            print("❌ Error al enviar resultado:", e)
            game.guardar_backup_local()
        camara.pausar_cursor()
        print("👋 Juego cerrado correctamente.")
        return


def iniciar_encuentra_aprende(camara, gestor_musica):
    # Esta función quedó como wrapper por compatibilidad; en realidad recibe id_sesion desde Principal.py
    # Por simplicidad, aquí no se puede ejecutar directamente sin id_sesion.
    # En tu menú de juegos, deberás llamar a ejecutar_encuentra_y_aprende con el id_sesion correcto.
    return ejecutar_encuentra_y_aprende(camara, 1)
    return