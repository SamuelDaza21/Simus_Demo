# ----------------------- PARES MÁGICOS (Juego de memoria) ----------------------
# Internacionalizado

import random
import pygame
from core import config
from core.paths import imagen
from core.Musica import gestor_musica
from api.APICliente import APICliente
from logic.cursor import dibujar_cursor_unificado
from games.base_game import BaseGame

api = APICliente()

def ejecutar_juego_memoria(camara, id_sesion=1):
    game = BaseGame(id_sesion, "Pares mágicos")
    game.enviar_backup_si_existe()

    # Inicialización
    pygame.init()
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    if gestor_musica and not pygame.mixer.music.get_busy():
        gestor_musica.iniciar_musica()

    # Obtener pantalla real (no crear nueva)
    pantalla = pygame.display.get_surface()
    if pantalla is None:
        pantalla = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    ANCHO, ALTO = pantalla.get_size()

    # Esperar a que no haya clic durante ~0.5 segundos
    reloj_espera = pygame.time.Clock()
    frames_sin_clic = 0
    while frames_sin_clic < 15:
        try:
            _, _, clic_activo = camara.obtener_posicion_y_clic()
            if not clic_activo:
                frames_sin_clic += 1
            else:
                frames_sin_clic = 0
        except:
            frames_sin_clic += 1
        reloj_espera.tick(30)

    camara.calibrar()

    # Cargar fondo
    try:
        fondo = pygame.image.load(config.FONDO_PRINCIPAL)
        fondo = pygame.transform.scale(fondo, (ANCHO, ALTO))
    except:
        fondo = pygame.Surface((ANCHO, ALTO))
        fondo.fill(config.COLOR_FONDO)

    # Cargar imágenes de tarjetas
    imagenes = []
    for i in range(1, 7):
        ruta = imagen(f"Pares/tarjeta{i}.png")
        try:
            img = pygame.image.load(ruta)
            img = pygame.transform.scale(img, (186, 186))
            imagenes.append(img)
        except:
            surf = pygame.Surface((186, 186))
            surf.fill(config.HOVER)
            imagenes.append(surf)
    try:
        img_reverso = pygame.image.load(imagen("Botones/vuelta.png"))
        img_reverso = pygame.transform.scale(img_reverso, (186, 186))
    except:
        img_reverso = pygame.Surface((186, 186))
        img_reverso.fill((100, 100, 100))

    # Preparar tarjetas
    imagenes_tarjetas = imagenes * 2
    random.shuffle(imagenes_tarjetas)
    filas, columnas = 4, 3
    ancho_tarjeta, alto_tarjeta = 186, 186
    espacio = 20
    inicio_x = 500
    inicio_y = (ALTO - (filas * alto_tarjeta + (filas - 1) * espacio)) // 2

    tarjetas = []
    for fila in range(filas):
        for col in range(columnas):
            x = inicio_x + col * (ancho_tarjeta + espacio)
            y = inicio_y + fila * (alto_tarjeta + espacio)
            idx = fila * columnas + col
            tarjetas.append({
                "imagen": imagenes_tarjetas[idx],
                "rect": pygame.Rect(x, y, ancho_tarjeta, alto_tarjeta),
                "estado": "vista_previa",
                "angulo": 0,
                "escala": 1.0,
                "color_brillo": None
            })

    # Variables de juego
    estado_juego = "vista_previa"
    temporizador_vista = pygame.time.get_ticks()
    seleccionadas = []
    tiempo_ultima_verificacion = None
    puntaje = 0
    aciertos = 0
    error = 0

    # Botón volver (solo icono, sin texto)
    try:
        btn_img = pygame.image.load(imagen("Botones/Home.png"))
        btn_img = pygame.transform.scale(btn_img, (50, 50))
    except:
        btn_img = pygame.Surface((50, 50))
        btn_img.fill(config.SAVE_BG)
        pygame.draw.rect(btn_img, config.SAVE_BORDER, (0, 0, 50, 50), 3)
    boton_volver = pygame.Rect(ANCHO - 260, ALTO - 100, 200, 50)

    # Confeti
    confeti = []
    tiempo_fin_juego = 0
    mostrando_confeti = False

    reloj = pygame.time.Clock()
    control_clic = False
    ejecutando = True

    while ejecutando:
        # Obtener posición y clic de cámara
        try:
            cursor_x, cursor_y, clic_camara = camara.obtener_posicion_y_clic()
            if clic_camara and not control_clic:
                clic_activo = True
                control_clic = True
            elif not clic_camara:
                control_clic = False
                clic_activo = False
        except:
            cursor_x, cursor_y = ANCHO // 2, ALTO // 2
            clic_activo = False

        # Eventos de pygame (teclado, salir)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    ejecutando = False
                elif evento.key == pygame.K_c:
                    camara.calibrar()

        # Dibujar fondo
        pantalla.blit(fondo, (0, 0))

        # === Manejo de estados y animaciones ===
        ahora = pygame.time.get_ticks()

        if estado_juego == "vista_previa" and ahora - temporizador_vista > 5000:
            for t in tarjetas:
                t["estado"] = "oculta"
            estado_juego = "jugando"

        if estado_juego == "verificando" and tiempo_ultima_verificacion and (ahora - tiempo_ultima_verificacion > 1000):
            idx0, idx1 = seleccionadas[0], seleccionadas[1]
            if tarjetas[idx0]["imagen"] == tarjetas[idx1]["imagen"]:
                tarjetas[idx0]["estado"] = "encontrada"
                tarjetas[idx1]["estado"] = "encontrada"
                puntaje += 1
                aciertos += 1
                if gestor_musica:
                    gestor_musica.reproducir_sonido("sonido_match")
            else:
                tarjetas[idx0]["estado"] = "oculta"
                tarjetas[idx1]["estado"] = "oculta"
                if gestor_musica:
                    gestor_musica.reproducir_sonido("incorrecto")
                error += 1
            seleccionadas.clear()
            estado_juego = "jugando"

        # Detectar victoria
        if not mostrando_confeti and all(t["estado"] == "encontrada" for t in tarjetas):
            if gestor_musica:
                gestor_musica.reproducir_sonido("completado")
            tiempo_fin_juego = ahora
            mostrando_confeti = True

        # Animación de confeti
        if mostrando_confeti:
            if ahora - tiempo_fin_juego > 2000:
                # Reiniciar juego
                random.shuffle(imagenes_tarjetas)
                posiciones = [t["rect"].topleft for t in tarjetas]
                random.shuffle(posiciones)
                for i, t in enumerate(tarjetas):
                    t["imagen"] = imagenes_tarjetas[i]
                    t["rect"].topleft = posiciones[i]
                    t["estado"] = "vista_previa"
                    t["angulo"] = 0
                    t["escala"] = 1.0
                    t["color_brillo"] = None
                seleccionadas.clear()
                estado_juego = "vista_previa"
                temporizador_vista = pygame.time.get_ticks()
                mostrando_confeti = False
                confeti.clear()
            else:
                # Generar confeti
                if random.random() < 0.3:
                    confeti.append({
                        "x": random.randint(0, ANCHO),
                        "y": -10,
                        "color": (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255)),
                        "size": random.randint(5, 15),
                        "speed": random.randint(3, 8),
                        "sway": random.uniform(-1, 1)
                    })
                for c in confeti:
                    pygame.draw.circle(pantalla, c["color"], (int(c["x"]), int(c["y"])), c["size"])
                    c["y"] += c["speed"]
                    c["x"] += c["sway"]
                    if c["y"] > ALTO:
                        confeti.remove(c)

        # Dibujar tarjetas con animaciones de volteo y escala
        for tarjeta in tarjetas:
            if tarjeta["estado"] == "revelada" and tarjeta["angulo"] < 90:
                tarjeta["angulo"] += 18
            elif tarjeta["estado"] == "oculta" and tarjeta["angulo"] > 0:
                tarjeta["angulo"] -= 18
            if tarjeta["estado"] == "encontrada" and tarjeta["escala"] < 1.1:
                tarjeta["escala"] += 0.02
                if tarjeta["color_brillo"] is None:
                    tarjeta["color_brillo"] = (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))

            # Dibujar según ángulo
            if tarjeta["angulo"] == 0 or tarjeta["angulo"] == 90:
                img = tarjeta["imagen"] if tarjeta["estado"] in ["vista_previa", "revelada", "encontrada"] else img_reverso
                if tarjeta["escala"] != 1.0:
                    new_w = int(ancho_tarjeta * tarjeta["escala"])
                    new_h = int(alto_tarjeta * tarjeta["escala"])
                    img = pygame.transform.scale(img, (new_w, new_h))
                    rect = img.get_rect(center=tarjeta["rect"].center)
                    pantalla.blit(img, rect)
                else:
                    pantalla.blit(img, tarjeta["rect"])
            else:
                if tarjeta["angulo"] < 90:
                    escala = 1.0 - (tarjeta["angulo"] / 90)
                    temp = pygame.transform.scale(img_reverso, (int(ancho_tarjeta * escala), alto_tarjeta))
                    rect = temp.get_rect(center=tarjeta["rect"].center)
                    pantalla.blit(temp, rect)
                else:
                    escala = (tarjeta["angulo"] - 90) / 90
                    temp = pygame.transform.scale(tarjeta["imagen"], (int(ancho_tarjeta * escala), alto_tarjeta))
                    rect = temp.get_rect(center=tarjeta["rect"].center)
                    pantalla.blit(temp, rect)

            # Brillo
            if tarjeta["estado"] == "encontrada" and tarjeta["color_brillo"]:
                overlay = pygame.Surface((tarjeta["rect"].width, tarjeta["rect"].height), pygame.SRCALPHA)
                pygame.draw.rect(overlay, (*tarjeta["color_brillo"], 30), (0, 0, tarjeta["rect"].width, tarjeta["rect"].height))
                pantalla.blit(overlay, tarjeta["rect"].topleft)

        # Manejar clics en tarjetas durante juego activo
        if clic_activo and estado_juego == "jugando" and not mostrando_confeti:
            for idx, tarjeta in enumerate(tarjetas):
                if tarjeta["estado"] == "oculta" and tarjeta["rect"].collidepoint(cursor_x, cursor_y):
                    if len(seleccionadas) < 2:
                        tarjeta["estado"] = "revelada"
                        seleccionadas.append(idx)
                        if gestor_musica:
                            gestor_musica.reproducir_sonido("sonido_voltear")
                        if len(seleccionadas) == 2:
                            estado_juego = "verificando"
                            tiempo_ultima_verificacion = pygame.time.get_ticks()
                    break

        # Botón volver (solo icono, sin texto)
        pygame.draw.rect(pantalla, config.SAVE_BORDER, boton_volver, border_radius=10)
        pygame.draw.rect(pantalla, config.SAVE_BG, boton_volver.inflate(-6, -6), border_radius=10)
        if btn_img:
            img_rect = btn_img.get_rect(center=boton_volver.center)
            pantalla.blit(btn_img, img_rect)
        # El texto "Volver" se ha eliminado (solo icono)

        if clic_activo and boton_volver.collidepoint(cursor_x, cursor_y):
            ejecutando = False

        # Puntaje (usando la clave de traducción "Puntaje")
        texto_puntaje = config.render_text(
            config.traductor.t("Puntaje_format").format(puntos=puntaje),
            config.fuente,
            config.COLOR_TEXTO
        )
        pantalla.blit(texto_puntaje, (ANCHO - texto_puntaje.get_width() - 60, 100))

        # Dibujar cursor
        try:
            dibujar_cursor_unificado(pantalla, cursor_x, cursor_y, modo_ocular=True, ancho=ANCHO, alto=ALTO)
        except:
            pygame.draw.circle(pantalla, config.ROJO, (cursor_x, cursor_y), 10, 2)

        pygame.display.flip()
        reloj.tick(60)

    # Al salir, guardar resultados
    game.actualizar_resultados(puntaje=puntaje, aciertos=aciertos, errores=error)
    try:
        api.registrar_resultado(id_sesion, "Pares mágicos", puntaje, aciertos, error)
        print("✅ Resultado enviado.")
    except Exception as e:
        print("❌ Error al enviar resultado:", e)
        game.guardar_backup_local()
    camara.pausar_cursor()
    print("👋 Juego terminado. Retornando al menú...")
    return

# Función wrapper por compatibilidad
def iniciar_memoria(camara, gestor_musica):
    return ejecutar_juego_memoria(camara, 1)

if __name__ == "__main__":
    from core.ManejoCamara import ManejoCamara
    cam = ManejoCamara()
    ejecutar_juego_memoria(cam, 1)