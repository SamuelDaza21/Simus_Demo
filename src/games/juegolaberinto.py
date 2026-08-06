import os
import random
import math
import json
import pygame
import pygame.mask
import pygame.draw

import core.config as config
from core.Musica import *
from core.paths import IMAGES
from logic.cursor import ControladorCursor
from core.ManejoCamara import *
from api.APICliente import APICliente
from logic.cursor import dibujar_cursor_unificado
from games.base_game import BaseGame

api = APICliente()

def obtener_preguntas_segun_idioma():
    idioma = "es"
    try:
        idioma = config.traductor.get_current_language()
    except:
        pass

    # Ruta corregida: src/core/Locales/preguntas_*.json
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # sube a src/
    ruta_json = os.path.join(base_dir, "core", "Locales", f"preguntas_{idioma}.json")

    print(f"[LABERINTO] Cargando preguntas desde: {ruta_json}")
    try:
        with open(ruta_json, "r", encoding="utf-8") as f:
            preguntas = json.load(f)
            if not isinstance(preguntas, list):
                print("[ERROR] El archivo de preguntas no contiene un array")
                return []
            return preguntas
    except FileNotFoundError:
        print(f"[ERROR] No se encontró el archivo para {idioma} en {ruta_json}")
        ruta_es = os.path.join(base_dir, "core", "Locales", "preguntas_es.json")
        try:
            with open(ruta_es, "r", encoding="utf-8") as f:
                preguntas = json.load(f)
                print("[INFO] Cargadas preguntas en español como fallback")
                return preguntas
        except:
            print("[ERROR] No se encontró el archivo de preguntas (ni siquiera en español).")
            return []
    except Exception as e:
        print(f"[ERROR] Error cargando preguntas: {e}")
        return []

# ==================== JUEGO LABERINTO ====================
def ejecutar_juego_laberinto(camara, id_sesion):
    game = BaseGame(id_sesion, "Mate-reto")
    game.enviar_backup_si_existe()

    pantalla = pygame.display.get_surface()
    if pantalla is None:
        print("[ERROR] No se pudo obtener la pantalla en Laberinto")
        return
    ANCHO_PANTALLA, ALTO_PANTALLA = pantalla.get_size()
    reloj = pygame.time.Clock()

    camara.reanudar_cursor()
    pygame.time.delay(800)
    try:
        for _ in range(10):
            _, _, clic_activo = camara.obtener_posicion_y_clic()
            if clic_activo:
                pygame.time.delay(100)
    except:
        pass
    camara.calibrar()
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    if gestor_musica and not pygame.mixer.music.get_busy():
        gestor_musica.iniciar_musica()

    # === NIVELES (5 niveles completos) ===
    niveles = [
        {
            "fondo": "assets/imagenes/Mate-Reto/laberinto1.png",
            "pos_circulo_inicial": (ANCHO_PANTALLA - 860, ALTO_PANTALLA // 8),
            "pos_meta": (ANCHO_PANTALLA - 808, ALTO_PANTALLA - 185),
            "estrellas": [
                (ANCHO_PANTALLA - 1032, ALTO_PANTALLA - 637),
                (ANCHO_PANTALLA - 785, ALTO_PANTALLA - 465),
                (ANCHO_PANTALLA - 600, ALTO_PANTALLA - 332)
            ],
            "img_completado": "assets/imagenes/Mate-Reto/siguiente_laberinto.png",
            "tamaño_circulo": (30, 30),
            "tamaño_estrella": (40, 40)
        },
        {
            "fondo": "assets/imagenes/Mate-Reto/laberinto2.png",
            "pos_circulo_inicial": (ANCHO_PANTALLA - 1000, ALTO_PANTALLA // 8),
            "pos_meta": (ANCHO_PANTALLA - 630, ALTO_PANTALLA - 425),
            "estrellas": [
                (ANCHO_PANTALLA - 1115, ALTO_PANTALLA - 295),
                (ANCHO_PANTALLA - 915, ALTO_PANTALLA - 325),
                (ANCHO_PANTALLA - 775, ALTO_PANTALLA - 300),
                (ANCHO_PANTALLA - 590, ALTO_PANTALLA - 250)
            ],
            "img_completado": "assets/imagenes/Mate-Reto/siguiente_laberinto.png",
            "tamaño_circulo": (30, 30),
            "tamaño_estrella": (40, 40)
        },
        {
            "fondo": "assets/imagenes/Mate-Reto/laberinto3.png",
            "pos_circulo_inicial": (ANCHO_PANTALLA - 770, ALTO_PANTALLA - 710),
            "pos_meta": (ANCHO_PANTALLA - 825, ALTO_PANTALLA - 495),
            "estrellas": [
                (ANCHO_PANTALLA - 1020, ALTO_PANTALLA - 500),
                (ANCHO_PANTALLA - 835, ALTO_PANTALLA - 330),
                (ANCHO_PANTALLA - 700, ALTO_PANTALLA - 285),
                (ANCHO_PANTALLA - 620, ALTO_PANTALLA - 585)
            ],
            "img_completado": "assets/imagenes/Mate-Reto/siguiente_laberinto.png",
            "tamaño_circulo": (30, 30),
            "tamaño_estrella": (40, 40)
        },
        {
            "fondo": "assets/imagenes/Mate-Reto/laberinto4.png",
            "pos_circulo_inicial": (ANCHO_PANTALLA - 785, ALTO_PANTALLA - 778),
            "pos_meta": (ANCHO_PANTALLA - 825, ALTO_PANTALLA - 532),
            "estrellas": [
                (ANCHO_PANTALLA - 830, ALTO_PANTALLA - 735),
                (ANCHO_PANTALLA - 820, ALTO_PANTALLA - 605),
                (ANCHO_PANTALLA - 642, ALTO_PANTALLA - 422),
                (ANCHO_PANTALLA - 870, ALTO_PANTALLA - 420)
            ],
            "img_completado": "assets/imagenes/Mate-Reto/siguiente_laberinto.png",
            "tamaño_circulo": (15, 15),
            "tamaño_estrella": (25, 25)
        },
        {
            "fondo": "assets/imagenes/Mate-Reto/laberinto5.png",
            "pos_circulo_inicial": (ANCHO_PANTALLA - 1000, ALTO_PANTALLA - 700),
            "pos_meta": (ANCHO_PANTALLA - 975, ALTO_PANTALLA - 225),
            "estrellas": [
                (ANCHO_PANTALLA - 1160, ALTO_PANTALLA - 645),
                (ANCHO_PANTALLA - 1160, ALTO_PANTALLA - 400),
                (ANCHO_PANTALLA - 1105, ALTO_PANTALLA - 345),
                (ANCHO_PANTALLA - 905, ALTO_PANTALLA - 595),
                (ANCHO_PANTALLA - 950, ALTO_PANTALLA - 345)
            ],
            "img_completado": "assets/imagenes/Mate-Reto/siguiente_laberinto.png",
            "tamaño_circulo": (25, 25),
            "tamaño_estrella": (40, 40)
        }
    ]
    nivel_actual = 0

    # === PREGUNTAS según idioma ===
    preguntas_base = obtener_preguntas_segun_idioma()
    if not preguntas_base:
        print("[ERROR] No se pudieron cargar preguntas. Saliendo del juego.")
        return

    preguntas_restantes = preguntas_base.copy()
    preguntas_utilizadas = []

    velocidad_actual = [0, 0]
    FUENTE = config.fuente

    # === Variables globales del juego ===
    fondo = None
    muro = None
    masc_laberinto = None
    imagen_circulo = None
    imagen_estrella = None
    mascara_circulo = None
    pos_circulo = None
    pos_meta = pygame.Rect(0,0,50,50)
    pos_estrella_inicio = []
    pos_estrella = []
    n_estrellas = 0
    puntaje = 0
    acierto = 0
    aciertos = 0
    errores = 0
    error = 0

    # === FUNCIONES AUXILIARES ===
    def resolver_ruta(ruta_relativa):
        ruta = ruta_relativa.replace('\\', '/').lstrip('/')
        if ruta.lower().startswith('assets/'):
            ruta = ruta.split('/', 1)[1]
        if ruta.lower().startswith('imagenes/'):
            ruta = ruta.split('/', 1)[1]
        return os.path.join(IMAGES, *ruta.split('/'))

    def verificar_colision(x, y):
        offset = (int(x - pos_circulo.width // 2), int(y - pos_circulo.height // 2))
        return masc_laberinto.overlap(mascara_circulo, offset) is not None

    def mover_circulo_avanzado(obj_x, obj_y):
        nonlocal pos_circulo, velocidad_actual
        actu_x, actu_y = pos_circulo.center
        dir_deseada_x = obj_x - actu_x
        dir_deseada_y = obj_y - actu_y
        distancia = math.hypot(dir_deseada_x, dir_deseada_y)
        if distancia < 5:
            velocidad_actual = [0, 0]
            return
        dir_deseada_x /= distancia
        dir_deseada_y /= distancia
        velocidad_actual[0] = velocidad_actual[0] * 0.9 + dir_deseada_x * 0.1
        velocidad_actual[1] = velocidad_actual[1] * 0.9 + dir_deseada_y * 0.1
        velo_magnitud = math.hypot(velocidad_actual[0], velocidad_actual[1])
        if velo_magnitud > 0:
            velocidad_actual[0] /= velo_magnitud
            velocidad_actual[1] /= velo_magnitud
        velocidad = min(5, distancia * 0.1)
        mov_x = velocidad_actual[0] * velocidad
        mov_y = velocidad_actual[1] * velocidad
        pasos = 3
        movimiento_exitoso = False
        for paso in range(pasos):
            frac = (paso + 1) / pasos
            test_x = actu_x + mov_x * frac
            test_y = actu_y + mov_y * frac
            if not verificar_colision(test_x, test_y):
                pos_circulo.center = (test_x, test_y)
                movimiento_exitoso = True
            else:
                if paso == 0:
                    correcciones = [(mov_x*0.3, mov_y*0.3), (mov_x*0.2, 0), (0, mov_y*0.2), (mov_x*0.1, mov_y*0.1)]
                    for corr_x, corr_y in correcciones:
                        test_x_corr = actu_x + corr_x
                        test_y_corr = actu_y + corr_y
                        if not verificar_colision(test_x_corr, test_y_corr):
                            pos_circulo.center = (test_x_corr, test_y_corr)
                            if corr_x != 0 or corr_y != 0:
                                magnitud = math.hypot(corr_x, corr_y)
                                velocidad_actual[0] = corr_x / magnitud
                                velocidad_actual[1] = corr_y / magnitud
                            movimiento_exitoso = True
                            break
                if not movimiento_exitoso:
                    break
        if not movimiento_exitoso:
            velocidad_actual = [0, 0]

    def ajustar_texto(texto, color, max_width, max_height):
        if '\n' in texto:
            lineas = [l for l in texto.split('\n') if l.strip()]
            for tamaño in range(28, 12, -2):
                fuente_temp = pygame.font.Font(None, tamaño)
                todas_caben = all(fuente_temp.size(linea)[0] <= max_width - 10 for linea in lineas)
                if not todas_caben:
                    continue
                altura_total = len(lineas) * fuente_temp.get_linesize()
                if altura_total <= max_height - 10:
                    surf = pygame.Surface((max_width, max_height), pygame.SRCALPHA)
                    y_offset = (max_height - altura_total)//2
                    for linea in lineas:
                        tsurf = fuente_temp.render(linea, True, color)
                        x_pos = (max_width - tsurf.get_width())//2
                        surf.blit(tsurf, (x_pos, y_offset))
                        y_offset += fuente_temp.get_linesize()
                    return surf
            surf = pygame.Surface((max_width, max_height), pygame.SRCALPHA)
            fuente_temp = pygame.font.Font(None, 12)
            y_offset = (max_height - len(lineas)*15)//2
            for linea in lineas:
                tsurf = fuente_temp.render(linea, True, color)
                x_pos = (max_width - tsurf.get_width())//2
                surf.blit(tsurf, (x_pos, y_offset))
                y_offset += 15
            return surf
        else:
            for tamaño in range(28, 12, -2):
                fuente_temp = pygame.font.Font(None, tamaño)
                palabras = texto.split()
                lineas = []
                linea_actual = []
                for palabra in palabras:
                    if fuente_temp.size(palabra)[0] > max_width - 10:
                        parte = ""
                        for letra in palabra:
                            if fuente_temp.size(parte+letra)[0] <= max_width - 10:
                                parte += letra
                            else:
                                if parte:
                                    if fuente_temp.size(' '.join(linea_actual + [palabra]))[0] <= max_width - 10:
                                        linea_actual.append(palabra)
                                    else:
                                        if linea_actual:
                                            lineas.append(' '.join(linea_actual))
                                        linea_actual = [parte]
                                parte = letra
                        if parte:
                            if fuente_temp.size(' '.join(linea_actual + [parte]))[0] <= max_width - 10:
                                linea_actual.append(parte)
                            else:
                                if linea_actual:
                                    lineas.append(' '.join(linea_actual))
                                linea_actual = [parte]
                    else:
                        prueba_linea = ' '.join(linea_actual + [palabra])
                        if fuente_temp.size(prueba_linea)[0] <= max_width - 10:
                            linea_actual.append(palabra)
                        else:
                            if linea_actual:
                                lineas.append(' '.join(linea_actual))
                            linea_actual = [palabra]
                if linea_actual:
                    lineas.append(' '.join(linea_actual))
                if not lineas:
                    continue
                altura_total = len(lineas) * fuente_temp.get_linesize()
                if altura_total <= max_height - 10:
                    surf = pygame.Surface((max_width, max_height), pygame.SRCALPHA)
                    y_offset = (max_height - altura_total)//2
                    for linea in lineas:
                        tsurf = fuente_temp.render(linea, True, color)
                        x_pos = (max_width - tsurf.get_width())//2
                        surf.blit(tsurf, (x_pos, y_offset))
                        y_offset += fuente_temp.get_linesize()
                    return surf
            surf = pygame.Surface((max_width, max_height), pygame.SRCALPHA)
            fuente_temp = pygame.font.Font(None, 12)
            texto_trunc = texto[:15] + "..." if len(texto) > 15 else texto
            tsurf = fuente_temp.render(texto_trunc, True, color)
            x_pos = (max_width - tsurf.get_width())//2
            y_pos = (max_height - tsurf.get_height())//2
            surf.blit(tsurf, (x_pos, y_pos))
            return surf

    def reinicio_estrellas():
        nonlocal n_estrellas, pos_estrella
        pos_estrella.clear()
        for p in pos_estrella_inicio:
            r = imagen_estrella.get_rect()
            r.center = p
            pos_estrella.append(r)
        n_estrellas = 0
        return 0

    def carga_de_nivel(nivel):
        nonlocal fondo, muro, masc_laberinto, pos_circulo, pos_meta, pos_estrella_inicio, nivel_actual, imagen_circulo, imagen_estrella, mascara_circulo
        nivel_actual = nivel
        cfg = niveles[nivel_actual]
        try:
            ruta_fondo = resolver_ruta(cfg["fondo"])
            fondo = pygame.image.load(ruta_fondo).convert_alpha()
            fondo = pygame.transform.scale(fondo, (ANCHO_PANTALLA, ALTO_PANTALLA))
        except:
            fondo = pygame.Surface((ANCHO_PANTALLA, ALTO_PANTALLA))
            fondo.fill((100,100,100))
        try:
            tamaño = cfg["tamaño_circulo"]
            img = pygame.image.load(resolver_ruta("Mate-Reto/circulo_laberinto.png")).convert_alpha()
            imagen_circulo = pygame.transform.scale(img, tamaño)
        except:
            tamaño = cfg["tamaño_circulo"]
            imagen_circulo = pygame.Surface(tamaño, pygame.SRCALPHA)
            pygame.draw.circle(imagen_circulo, (255,0,0), (tamaño[0]//2, tamaño[1]//2), min(tamaño)//2-5)
        try:
            tamaño_e = cfg["tamaño_estrella"]
            img = pygame.image.load(resolver_ruta("Mate-Reto/Estrella.png")).convert_alpha()
            imagen_estrella = pygame.transform.scale(img, tamaño_e)
        except:
            tamaño_e = cfg["tamaño_estrella"]
            imagen_estrella = pygame.Surface(tamaño_e, pygame.SRCALPHA)
            pygame.draw.rect(imagen_estrella, (255,255,0), (tamaño_e[0]//4, tamaño_e[1]//4), tamaño_e[0]//2, tamaño_e[1]//2)
        mascara_circulo = pygame.mask.from_surface(imagen_circulo)
        pos_circulo = imagen_circulo.get_rect()
        pos_circulo.center = cfg["pos_circulo_inicial"]
        muro = pygame.Surface((ANCHO_PANTALLA, ALTO_PANTALLA), pygame.SRCALPHA)
        for x in range(ANCHO_PANTALLA):
            for y in range(ALTO_PANTALLA):
                a,b,c,*_ = fondo.get_at((x,y))
                if (a<50 and b<50 and c<50) or (a==221 and b==162 and c==105):
                    muro.set_at((x,y), (255,255,255,255))
                else:
                    muro.set_at((x,y), (0,0,0,0))
        masc_laberinto = pygame.mask.from_surface(muro)
        pos_meta.x, pos_meta.y = cfg["pos_meta"]
        pos_estrella_inicio = cfg["estrellas"]
        reinicio_estrellas()

    # === Cargar recursos UI ===
    try:
        ruta_tab = resolver_ruta("Mate-Reto/Barra de preguntas.png")
        tab_pregunta = pygame.image.load(ruta_tab).convert_alpha()
        tab_pregunta = pygame.transform.scale(tab_pregunta, (1600, 900))
    except:
        tab_pregunta = pygame.Surface((1600,900), pygame.SRCALPHA)
        tab_pregunta.fill((200,200,200))
    try:
        ruta_marco = resolver_ruta("Mate-Reto/cuadro_respuestas.png")
        marco_rta = pygame.image.load(ruta_marco).convert_alpha()
        marco_rta = pygame.transform.scale(marco_rta, (200,140))
    except:
        marco_rta = pygame.Surface((200,140), pygame.SRCALPHA)
        pygame.draw.rect(marco_rta, (255,255,0), (0,0,200,140), 2)
    try:
        ruta_home = resolver_ruta("Botones/Home.png")
        boton_volver_img = pygame.image.load(ruta_home).convert_alpha()
        boton_volver_img = pygame.transform.scale(boton_volver_img, (50,50))
    except:
        boton_volver_img = pygame.Surface((50,50))
        boton_volver_img.fill(config.SAVE_BG)
        pygame.draw.rect(boton_volver_img, config.SAVE_BORDER, (0,0,50,50), 3)
    boton_volver = pygame.Rect(ANCHO_PANTALLA - 260, ALTO_PANTALLA - 100, 200, 50)

    carga_de_nivel(nivel_actual)
    circulo_sigue = False
    fin = False
    mostrar_pregunta = False
    clic_pres = False
    estrella_actu_ref = None
    preg_actual = None
    rta_actual = []

    def mostrar_mensaje_final():
        try:
            img_fin = pygame.image.load(resolver_ruta("Mate-Reto/laberintos_completados.png")).convert_alpha()
            img_fin = pygame.transform.scale(img_fin, (ANCHO_PANTALLA, ALTO_PANTALLA))
        except:
            img_fin = pygame.Surface((ANCHO_PANTALLA, ALTO_PANTALLA))
            img_fin.fill((200,200,200))
        overlay = pygame.Surface((ANCHO_PANTALLA, ALTO_PANTALLA), pygame.SRCALPHA)
        overlay.fill((0,0,0,150))
        pantalla.blit(overlay, (0,0))
        img_rect = img_fin.get_rect(center=(ANCHO_PANTALLA//2, ALTO_PANTALLA//2))
        pantalla.blit(img_fin, img_rect)
        mensaje = config.render_text(config.traductor.t("Volviendo_menu_juegos"), config.fuente, config.NEGRO)
        pantalla.blit(mensaje, (ANCHO_PANTALLA//2 - mensaje.get_width()//2, ALTO_PANTALLA//2+100))
        if gestor_musica:
            gestor_musica.reproducir_sonido("correcto")
        pygame.display.flip()
        t0 = pygame.time.get_ticks()
        while pygame.time.get_ticks() - t0 < 5000:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return
            reloj.tick(60)

    # === BUCLE PRINCIPAL ===
    ejecucion = True
    try:
        while ejecucion:
            datos = camara.obtener_posicion_y_clic()
            if datos:
                cx, cy, clic = datos
            else:
                cx, cy, clic = ANCHO_PANTALLA//2, ALTO_PANTALLA//2, False

            if fondo:
                pantalla.blit(fondo, (0,0))
            else:
                pantalla.fill((0,0,0))

            if clic and not clic_pres:
                if not circulo_sigue and pos_circulo.collidepoint(cx, cy):
                    circulo_sigue = True
            clic_pres = clic

            if circulo_sigue and not fin and not mostrar_pregunta:
                mover_circulo_avanzado(cx, cy)
                for estrella in pos_estrella[:]:
                    if pos_circulo.colliderect(estrella):
                        mostrar_pregunta = True
                        if not preguntas_restantes:
                            preguntas_restantes = preguntas_base.copy()
                            preguntas_utilizadas = []
                        preg_actual = random.choice(preguntas_restantes)
                        preguntas_restantes.remove(preg_actual)
                        preguntas_utilizadas.append(preg_actual)
                        rta_actual = random.sample(preg_actual["respuestas"], len(preg_actual["respuestas"]))
                        estrella_actu_ref = estrella
                        break

            if not fin and pos_circulo.colliderect(pos_meta):
                fin = True
                circulo_sigue = False
                sig = nivel_actual + 1
                if sig < len(niveles):
                    carga_de_nivel(sig)
                    fin = False
                else:
                    ejecucion = False
                    mostrar_mensaje_final()
                    return

            if not fin:
                pygame.draw.rect(pantalla, (0,255,0), pos_meta, 3)
            pantalla.blit(imagen_circulo, pos_circulo)
            for e in pos_estrella:
                pantalla.blit(imagen_estrella, e)
            for i in range(n_estrellas):
                x = ANCHO_PANTALLA - 330 + i*40
                y = 160
                pantalla.blit(imagen_estrella, (x,y))

            if mostrar_pregunta and preg_actual:
                pantalla.blit(tab_pregunta, (0,0))
                pregunta_txt = preg_actual["pregunta"]
                if len(pregunta_txt) > 30:
                    fp = pygame.font.Font(None,28)
                elif len(pregunta_txt) > 20:
                    fp = pygame.font.Font(None,32)
                else:
                    fp = FUENTE
                pantalla.blit(fp.render(pregunta_txt, True, (0,0,0)), (80,600))

                if "secuencia" in preg_actual:
                    seq = preg_actual["secuencia"]
                    x_seq = 600
                    y_seq = 600
                    esp = 30
                    for idx, e in enumerate(seq):
                        x_act = x_seq + idx*esp
                        if isinstance(e, str) and e.lower().endswith(".png"):
                            try:
                                im = pygame.image.load(resolver_ruta(e)).convert_alpha()
                                an, al = im.get_size()
                                esc = min(80/an, 80/al)
                                nw, nh = int(an*esc), int(al*esc)
                                im = pygame.transform.scale(im, (nw,nh))
                                offx = (80-nw)//2
                                offy = (80-nh)//2
                                pantalla.blit(im, (x_act+offx, y_seq+offy))
                            except:
                                pass
                        else:
                            if len(e) > 10:
                                fs = pygame.font.Font(None,20)
                            else:
                                fs = pygame.font.Font(None,28)
                            pantalla.blit(fs.render(e, True, (0,0,0)), (x_act+(80-fs.size(e)[0])//2, y_seq+(80-fs.size(e)[1])//2))
                        x_seq += 120

                x = 200
                y = 700
                rects_resp = []
                for ans in rta_actual:
                    pantalla.blit(marco_rta, (x, y))
                    if ans.lower().endswith(".png"):
                        try:
                            im = pygame.image.load(resolver_ruta(ans)).convert_alpha()
                            an, al = im.get_size()
                            esc = min(100/an, 80/al)
                            nw, nh = int(an*esc), int(al*esc)
                            im = pygame.transform.scale(im, (nw,nh))
                            offx = (marco_rta.get_width()-nw)//2
                            offy = (marco_rta.get_height()-nh)//2
                            pantalla.blit(im, (x+offx, y+offy))
                        except:
                            pass
                    else:
                        surf_text = ajustar_texto(ans, (0,0,0), marco_rta.get_width(), marco_rta.get_height())
                        pantalla.blit(surf_text, (x+(marco_rta.get_width()-surf_text.get_width())//2, y+(marco_rta.get_height()-surf_text.get_height())//2))
                    rect_op = pygame.Rect(x, y, marco_rta.get_width(), marco_rta.get_height())
                    rects_resp.append((rect_op, ans))
                    x += 190

                if clic_pres:
                    for rect_op, ans in rects_resp:
                        if rect_op.collidepoint(cx, cy):
                            if ans == preg_actual["correcto"]:
                                n_estrellas += 1
                                pos_estrella.remove(estrella_actu_ref)
                                if gestor_musica:
                                    gestor_musica.reproducir_sonido("correcto")
                                acierto += 1
                            else:
                                pos_circulo.center = niveles[nivel_actual]["pos_circulo_inicial"]
                                if gestor_musica:
                                    gestor_musica.reproducir_sonido("incorrecto")
                                n_estrellas = reinicio_estrellas()
                                error += 1
                            mostrar_pregunta = False
                            preg_actual = None
                            estrella_actu_ref = None
                            break
                puntaje = n_estrellas
                aciertos = acierto
                errores = error

            # Botón volver
            pygame.draw.rect(pantalla, config.SAVE_BORDER, boton_volver, border_radius=10)
            pygame.draw.rect(pantalla, config.SAVE_BG, boton_volver.inflate(-6,-6), border_radius=10)
            pantalla.blit(boton_volver_img, boton_volver_img.get_rect(center=boton_volver.center))
            if clic_pres and boton_volver.collidepoint(cx, cy):
                camara.pausar_cursor()
                return

            texto_estrellas = config.render_text(config.traductor.t("Estrellas_format").format(n=n_estrellas), config.fuente, (255,255,255))
            pantalla.blit(texto_estrellas, (ANCHO_PANTALLA - texto_estrellas.get_width() - 180, 100))
            dibujar_cursor_unificado(pantalla, cx, cy, modo_ocular=True, ancho=ANCHO_PANTALLA, alto=ALTO_PANTALLA)

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    ejecucion = False
                elif ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        ejecucion = False
                    elif ev.key == pygame.K_c:
                        camara.calibrar()
            pygame.display.flip()
            reloj.tick(60)

    finally:
        game.actualizar_resultados(puntaje=puntaje, aciertos=aciertos, errores=error)
        try:
            api.registrar_resultado(id_sesion, "Mate-reto", puntaje, aciertos, error)
            print("✅ Resultado final enviado.")
        except Exception as e:
            print("❌ Error al enviar resultado:", e)
            game.guardar_backup_local()
        camara.pausar_cursor()
        print("👋 Juego Laberinto cerrado correctamente.")