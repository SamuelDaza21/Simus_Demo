# -------------------------ANIMALIA----------------------------
import random
import math
import sys
import pygame
import core.config as config
from core.paths import imagen
from api.APICliente import APICliente
from logic.cursor import dibujar_cursor_unificado
from games.base_game import BaseGame
from core.Musica import gestor_musica

api = APICliente()


# ----------------------------------------JUEGO DE PUZZLE-------------------------------------------
def ejecutar_puzzle_animales(camara, id_sesion):
    game = BaseGame(id_sesion, "Animalia")
    game.enviar_backup_si_existe()

    # Obtener la pantalla existente (no crear una nueva)
    pantalla = pygame.display.get_surface()
    if pantalla is None:
        print("[ERROR] No se pudo obtener la pantalla en Animalia")
        return

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

    ANCHO, ALTO = pantalla.get_size()
    reloj = pygame.time.Clock()

    # --- Configuración Visual ---
    # Usar colores de config
    COLOR_TEXTO = config.NEGRO  # negro real (0,0,0) definido en config
    try:
        fondo = pygame.image.load(config.FONDO_PRINCIPAL)
        fondo = pygame.transform.scale(fondo, (ANCHO, ALTO))
    except Exception:
        fondo = pygame.Surface((ANCHO, ALTO))
        fondo.fill(config.COLOR_FONDO)

    img_home = pygame.image.load(imagen("Botones/Home.png"))
    img_home = pygame.transform.scale(img_home, (60, 60))

    # --- Base de Datos Maestra de 20 Animales ---
    DATA_MAESTRA = {
        "tigre": "jungla", "elefante": "sabana", "tiburon": "oceano",
        "camello": "desierto", "oso": "bosque", "lobo": "montana",
        "vaca": "granja", "pulpo": "oceano", "zorro": "bosque",
        "aguila": "montana", "jirafa": "sabana", "canguro": "pradera",
        "buho": "bosque", "foca": "hielo", "cocodrilo": "pantano",
        "ardilla": "bosque", "tucan": "jungla", "cerdo": "granja",
        "orca": "oceano", "rinoceronte": "sabana"
    }

    # Traducción de nombres de hábitats (se usan solo internamente para emparejar,
    # pero no se muestran directamente. Los hábitats visuales son imágenes fijas.
    # No se traducen porque son imágenes.

    TAMANO_ANIMAL = (ANCHO // 8, ANCHO // 8)
    TAMANO_HABITAT = (ANCHO // 5, ALTO // 5)

    def preparar_ronda():
        seleccion_nombres = random.sample(list(DATA_MAESTRA.keys()), 4)
        animales_ronda = {}
        habitats_necesarios = list(set(DATA_MAESTRA[name] for name in seleccion_nombres))
        todos_los_habitats = ["jungla", "sabana", "oceano", "desierto", "bosque", "montana", "granja", "pradera",
                              "pantano", "hielo"]
        while len(habitats_necesarios) < 4:
            extra = random.choice(todos_los_habitats)
            if extra not in habitats_necesarios:
                habitats_necesarios.append(extra)
        habitats_visuales_nombres = random.sample(habitats_necesarios, 4)
        habitats_ronda = {}

        for nombre in seleccion_nombres:
            img = pygame.image.load(imagen(f"Animalia/animal_{nombre}.png"))
            animales_ronda[nombre] = {
                "imagen": pygame.transform.scale(img, TAMANO_ANIMAL),
                "habitat": DATA_MAESTRA[nombre]
            }

        for h_nombre in habitats_visuales_nombres:
            img_h = pygame.image.load(imagen(f"Animalia/habitat_{h_nombre}.jpg"))
            habitats_ronda[h_nombre] = {
                "imagen": pygame.transform.scale(img_h, TAMANO_HABITAT),
                "rect": None
            }
        return animales_ronda, habitats_ronda

    def posicionar_elementos(animales_dict, habitats_dict):
        margen_h = ANCHO // 12
        espacio_h = (ANCHO - 2 * margen_h - 4 * TAMANO_HABITAT[0]) // 5
        for i, (nombre, data) in enumerate(habitats_dict.items()):
            x = margen_h + i * (TAMANO_HABITAT[0] + espacio_h)
            y = ALTO - TAMANO_HABITAT[1] - 150
            habitats_dict[nombre]["rect"] = pygame.Rect(x, y, TAMANO_HABITAT[0], TAMANO_HABITAT[1])

        posiciones_base = []
        altura_fija = ALTO // 3
        espacio_a = (ANCHO - 4 * TAMANO_ANIMAL[0]) // 5
        for i in range(4):
            posiciones_base.append((espacio_a + i * (TAMANO_ANIMAL[0] + espacio_a), altura_fija))
        random.shuffle(posiciones_base)
        activos = []
        for i, (nombre, data) in enumerate(animales_dict.items()):
            x, y = posiciones_base[i]
            activos.append({
                "tipo": nombre,
                "imagen": data["imagen"],
                "rect": pygame.Rect(x, y, TAMANO_ANIMAL[0], TAMANO_ANIMAL[1]),
                "arrastrando": False,
                "pos_original": (x, y)
            })
        return activos

    # Inicialización de la primera ronda
    animales_ronda, habitats_ronda = preparar_ronda()
    animales_activos = posicionar_elementos(animales_ronda, habitats_ronda)

    # UI estática con textos traducidos
    titulo_texto = config.render_text(
        config.traductor.t("Ayuda_a_cada_animal"),
        config.fuente, COLOR_TEXTO
    )
    # Calcular tamaño del rectángulo del título
    titulo_rect = pygame.Rect(
        ANCHO // 2 - (titulo_texto.get_width() + 60) // 2,
        30,
        titulo_texto.get_width() + 60,
        80
    )
    boton_menu = pygame.Rect(50, ALTO - 100, 70, 70)

    # Estado del juego
    puntaje, vidas, error, aciertos = 0, 3, 0, 0
    animal_arrastrado = None
    feedback_positivo = None
    feedback_tiempo = 0
    clic_anterior = False
    ejecutando = True

    try:
        while ejecutando:
            datos_mano = camara.obtener_posicion_y_clic()
            if datos_mano:
                cursor_x, cursor_y, clic = datos_mano
            else:
                cursor_x, cursor_y, clic = ANCHO // 2, ALTO // 2, False

            clic_nuevo = clic and not clic_anterior
            clic_anterior = clic

            # Dibujar fondo
            pantalla.blit(fondo, (0, 0))

            # Título con fondo
            pygame.draw.rect(pantalla, config.SAVE_BG, titulo_rect, border_radius=15)
            pantalla.blit(titulo_texto, (titulo_rect.centerx - titulo_texto.get_width() // 2,
                                         titulo_rect.centery - titulo_texto.get_height() // 2))

            # Dibujar hábitats
            for h in habitats_ronda.values():
                pantalla.blit(h["imagen"], h["rect"])

            # Dibujar animales
            for animal in animales_activos:
                if animal["arrastrando"]:
                    animal["rect"].center = (cursor_x, cursor_y)
                pantalla.blit(animal["imagen"], animal["rect"])

            # Manejo de clics
            if clic_nuevo:
                if animal_arrastrado is None:
                    # Intentar agarrar un animal
                    for animal in animales_activos:
                        if animal["rect"].collidepoint(cursor_x, cursor_y):
                            gestor_musica.reproducir_sonido("sonido_voltear")
                            animal["arrastrando"] = True
                            animal_arrastrado = animal
                            break
                    # Botón de volver
                    if boton_menu.collidepoint(cursor_x, cursor_y):
                        ejecutando = False
                        break
                else:
                    # Soltar animal
                    animal_arrastrado["arrastrando"] = False
                    emparejado = False
                    for h_nombre, h_data in habitats_ronda.items():
                        if h_data["rect"].collidepoint(cursor_x, cursor_y):
                            if animales_ronda[animal_arrastrado["tipo"]]["habitat"] == h_nombre:
                                # Éxito
                                puntaje += 10
                                aciertos += 1
                                gestor_musica.reproducir_sonido("correcto")
                                feedback_positivo = config.traductor.t("Correcto")
                                feedback_tiempo = pygame.time.get_ticks()
                                animales_activos.remove(animal_arrastrado)
                                emparejado = True
                                break
                            else:
                                # Error
                                puntaje = max(0, puntaje - 5)
                                vidas -= 1
                                error += 1
                                gestor_musica.reproducir_sonido("incorrecto")
                                feedback_positivo = config.traductor.t("Intenta_de_nuevo")
                                feedback_tiempo = pygame.time.get_ticks()
                                if vidas <= 0:
                                    ejecutando = False
                                    break
                                break
                    if not emparejado and animal_arrastrado is not None:
                        animal_arrastrado["rect"].topleft = animal_arrastrado["pos_original"]
                    animal_arrastrado = None

                    # Si se acabaron los animales, pasar a siguiente ronda
                    if not animales_activos and ejecutando:
                        pygame.display.flip()
                        pygame.time.delay(1000)
                        animales_ronda, habitats_ronda = preparar_ronda()
                        animales_activos = posicionar_elementos(animales_ronda, habitats_ronda)

            # Mostrar feedback (positivo o negativo)
            if feedback_positivo and pygame.time.get_ticks() - feedback_tiempo < 1000:
                f_txt = config.render_text(feedback_positivo, config.fuente, COLOR_TEXTO)
                pantalla.blit(f_txt, (ANCHO // 2 - f_txt.get_width() // 2, ALTO // 2))

            # Mostrar vidas y puntaje con formas traducidas
            # Vidas
            vidas_rect = pygame.Rect(ANCHO - 240, ALTO - 140, 220, 60)
            texto_vidas = config.traductor.t("Vidas_formato").format(vidas=vidas, max_vidas=3)
            txt_vidas = config.render_text(texto_vidas, config.fuente, COLOR_TEXTO)
            pygame.draw.rect(pantalla, config.SAVE_BG, vidas_rect, border_radius=15)
            pantalla.blit(txt_vidas, (vidas_rect.centerx - txt_vidas.get_width() // 2,
                                      vidas_rect.centery - txt_vidas.get_height() // 2))

            # Puntaje
            puntaje_rect = pygame.Rect(ANCHO - 240, ALTO - 70, 220, 60)
            texto_puntaje = config.traductor.t("Puntaje_format").format(puntos=puntaje)
            txt_puntaje = config.render_text(texto_puntaje, config.fuente, COLOR_TEXTO)
            pygame.draw.rect(pantalla, config.SAVE_BG, puntaje_rect, border_radius=15)
            pantalla.blit(txt_puntaje, (puntaje_rect.centerx - txt_puntaje.get_width() // 2,
                                        puntaje_rect.centery - txt_puntaje.get_height() // 2))

            # Botón home
            pantalla.blit(img_home, (boton_menu.centerx - 30, boton_menu.centery - 30))

            # Cursor
            try:
                dibujar_cursor_unificado(pantalla, cursor_x, cursor_y, modo_ocular=True,
                                         ancho=ANCHO, alto=ALTO)
            except:
                pygame.draw.circle(pantalla, config.ROJO, (int(cursor_x), int(cursor_y)), 10, 2)

            # Eventos de sistema
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    ejecutando = False
                elif evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        ejecutando = False
                    elif evento.key == pygame.K_c:
                        camara.calibrar()

            pygame.display.flip()
            reloj.tick(60)

    finally:
        # Guardar resultados
        game.actualizar_resultados(puntaje=puntaje, aciertos=aciertos, errores=error)
        try:
            api.registrar_resultado(id_sesion, "Animalia", puntaje, aciertos, error)
            print("✅ Resultado de Animalia enviado correctamente.")
        except Exception as e:
            print("❌ Error al enviar resultado de Animalia:", e)
            game.guardar_backup_local()

        camara.pausar_cursor()
        print("👋 Juego Animalia terminado. Retornando al menú...")