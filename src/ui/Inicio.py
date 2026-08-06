import pygame
import sys
import os
import subprocess
import platform
import tempfile
import core.config as config
from core.paths import imagen
from ui.barra_menu import BarraInferior
from core.ManejoCamara import ManejoCamara
from core.shortcuts import aplicar_atajo_camara, procesar_atajos_globales
from logic.cursor import dibujar_cursor_unificado

# Intentar importar pyttsx3 y gTTS
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    print("[TTS] pyttsx3 no instalado. Instálalo con: pip install pyttsx3")

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    print("[TTS] gTTS no instalado. Instálalo con: pip install gtts")


class SistemaTTS:
    def __init__(self):
        self.sistema = platform.system()
        self.comando_tts = self.detectar_comando_tts()
        self.lang_map = {
            "es": "es",
            "en": "en",
            "fr": "fr"
        }
        # Inicializar pygame.mixer con un buffer adecuado
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        # No setear volumen aquí, se maneja en GestorMusica
        # Para pyttsx3, cargar voces bajo demanda
        self._engine = None
        self.voice_ids = self._cargar_voces_pyttsx3() if PYTTSX3_AVAILABLE else {}

    def _cargar_voces_pyttsx3(self):
        voice_map = {}
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            for voice in voices:
                name_lower = voice.name.lower()
                if any(k in name_lower for k in ['spanish', 'español', 'mexican']):
                    voice_map['es'] = voice.id
                if any(k in name_lower for k in ['english', 'united states', 'uk', 'british']) and 'spanish' not in name_lower:
                    voice_map['en'] = voice.id
                if any(k in name_lower for k in ['french', 'français']):
                    voice_map['fr'] = voice.id
            engine.stop()
        except Exception as e:
            print(f"[TTS] Error cargando voces: {e}")
        return voice_map

    def detectar_comando_tts(self):
        if self.sistema == "Darwin":
            return "say"
        elif self.sistema == "Linux":
            try:
                subprocess.run(["which", "espeak"], check=True)
                return "espeak"
            except:
                try:
                    subprocess.run(["which", "spd-say"], check=True)
                    return "spd-say"
                except:
                    return None
        elif self.sistema == "Windows":
            return "powershell"
        return None

    def _speak_gtts(self, texto, idioma):
        """Genera audio con gTTS y lo reproduce con pygame.mixer.Sound."""
        if not GTTS_AVAILABLE:
            return False
        try:
            print(f"[TTS] Usando gTTS para '{texto}' en {idioma}")
            tts = gTTS(text=texto, lang=self.lang_map.get(idioma, 'es'), slow=False)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                temp_file = f.name
            tts.save(temp_file)
            # Reproducir con Sound (más fiable que music)
            sound = pygame.mixer.Sound(temp_file)
            sound.set_volume(1.0)
            sound.play()
            # Esperar a que termine
            while pygame.mixer.get_busy():
                pygame.time.delay(100)
            # Eliminar archivo temporal
            os.unlink(temp_file)
            return True
        except Exception as e:
            print(f"[TTS] Error en gTTS: {e}")
            return False

    def _speak_pyttsx3(self, texto, idioma):
        """Usa pyttsx3 offline."""
        if not PYTTSX3_AVAILABLE:
            return False
        try:
            print(f"[TTS] Usando pyttsx3 para '{texto}' en {idioma}")
            if self._engine is None:
                self._engine = pyttsx3.init()
            voice_id = self.voice_ids.get(idioma)
            if voice_id:
                self._engine.setProperty('voice', voice_id)
            self._engine.setProperty('rate', 150)
            self._engine.setProperty('volume', 1.0)
            self._engine.say(texto)
            self._engine.runAndWait()
            return True
        except Exception as e:
            print(f"[TTS] Error en pyttsx3: {e}")
            return False

    def _speak_command(self, texto, idioma):
        """Comandos del sistema (fallback)."""
        if not self.comando_tts:
            return False
        try:
            print(f"[TTS] Usando comando {self.comando_tts}")
            if self.comando_tts == "say":
                subprocess.Popen(["say", texto])
            elif self.comando_tts == "espeak":
                subprocess.Popen(["espeak", "-v", idioma, texto])
            elif self.comando_tts == "spd-say":
                subprocess.Popen(["spd-say", texto])
            elif self.comando_tts == "powershell":
                texto_escapado = texto.replace('"', '`"')
                comando = f'Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak("{texto_escapado}")'
                subprocess.Popen(["powershell", "-Command", comando])
            return True
        except Exception as e:
            print(f"[TTS] Error en comando: {e}")
            return False

    def decir_texto(self, texto):
        """Método público: detecta idioma y decide qué motor usar."""
        idioma = "es"
        try:
            if config.traductor and hasattr(config.traductor, 'get_current_language'):
                idioma = config.traductor.get_current_language()
        except:
            pass

        print(f"[TTS] Solicitado: '{texto}' (idioma: {idioma})")

        # 1. Probar gTTS (online, buena calidad)
        if GTTS_AVAILABLE:
            if self._speak_gtts(texto, idioma):
                return True
        # 2. Probar pyttsx3 (offline)
        if PYTTSX3_AVAILABLE:
            if self._speak_pyttsx3(texto, idioma):
                return True
        # 3. Último recurso: comandos del sistema
        return self._speak_command(texto, idioma)
class Inicio:
    def __init__(self, camara=None, gestor_musica=None, ID_sesion=None):
        self.ID_sesion = ID_sesion
        self.camara = camara
        self.gestor_musica = gestor_musica
        self.control_clic = False
        self.tts_sistema = SistemaTTS()

        # Colores de cuadros
        self.COLOR_SOCIALES = (255, 200, 200)
        self.COLOR_NECESIDADES = (200, 255, 200)
        self.COLOR_EMOCIONES = (200, 200, 255)
        self.COLOR_CONTROL = (255, 255, 200)
        self.COLOR_PERSONAS = (255, 200, 255)
        self.COLOR_ACTIVIDADES = (200, 255, 255)
        self.COLOR_AZUL = (0, 0, 255)
        self.COLOR_FONDO = (240, 240, 240)

        self.ancho = None
        self.alto = None
        self.pantalla = None
        self.cuadros = []
        self.iconos = {}
        self.botones_comunicacion = []
        self.barra_inferior = None

    def decir_texto(self, texto):
        self.tts_sistema.decir_texto(texto)

    def cargar_iconos(self):
        """Carga todos los iconos de comunicación y los de la barra (aunque la barra ya no los usa aquí)."""
        tamaño_icono = int(min(self.ancho, self.alto) * 0.1)
        self.iconos = {}
        iconos_info = [
            # Iconos de la barra (ya no se usan para la barra, pero se mantienen por si acaso)
            {"nombre": "instrucciones", "archivo": "menu/instrucciones.png", "text_key": "Instrucciones"},
            {"nombre": "configuracion", "archivo": "menu/configuraciones.png", "text_key": "Configuración"},
            {"nombre": "salir", "archivo": "menu/salida.png", "text_key": "Salir"},
            {"nombre": "jugar", "archivo": "menu/juegos.png", "text_key": "Jugar"},
            {"nombre": "inicio", "archivo": "menu/inicio.png", "text_key": "Inicio"},
            # Iconos de comunicación (sociales)
            {"nombre": "hola", "archivo": "Inicio/hola.png", "text_key": "HOLA"},
            {"nombre": "adios", "archivo": "Inicio/adios.png", "text_key": "ADIÓS"},
            {"nombre": "gracias", "archivo": "Inicio/gracias.png", "text_key": "GRACIAS"},
            {"nombre": "porfavor", "archivo": "Inicio/porfavor.png", "text_key": "POR FAVOR"},
            {"nombre": "si", "archivo": "Inicio/si.png", "text_key": "SÍ"},
            {"nombre": "no", "archivo": "Inicio/no.png", "text_key": "NO"},
            # Necesidades
            {"nombre": "hambre", "archivo": "Inicio/hambre.png", "text_key": "HAMBRE"},
            {"nombre": "incomodo", "archivo": "Inicio/incomodo.png", "text_key": "INCÓMODO"},
            {"nombre": "bano", "archivo": "Inicio/bano.png", "text_key": "BAÑO"},
            {"nombre": "sed", "archivo": "Inicio/sed.png", "text_key": "SED"},
            {"nombre": "cansado", "archivo": "Inicio/cansado.png", "text_key": "CANSADO"},
            {"nombre": "dolor", "archivo": "Inicio/dolor.png", "text_key": "DOLOR"},
            # Emociones
            {"nombre": "feliz", "archivo": "Inicio/feliz.png", "text_key": "FELIZ"},
            {"nombre": "triste", "archivo": "Inicio/triste.png", "text_key": "TRISTE"},
            {"nombre": "enojado", "archivo": "Inicio/enojado.png", "text_key": "ENOJADO"},
            {"nombre": "miedo", "archivo": "Inicio/miedo.png", "text_key": "MIEDO"},
            {"nombre": "nervioso", "archivo": "Inicio/nervioso.png", "text_key": "NERVIOSO"},
            {"nombre": "calma", "archivo": "Inicio/calma.png", "text_key": "CALMA"},
            # Control
            {"nombre": "ayuda", "archivo": "Inicio/ayuda.png", "text_key": "AYUDA"},
            {"nombre": "no-quiero", "archivo": "Inicio/noquiero.png", "text_key": "NO QUIERO"},
            {"nombre": "mas", "archivo": "Inicio/mas.png", "text_key": "MÁS"},
            {"nombre": "quiero", "archivo": "Inicio/quiero.png", "text_key": "QUIERO"},
            {"nombre": "basta", "archivo": "Inicio/basta.png", "text_key": "BASTA"},
            {"nombre": "espera", "archivo": "Inicio/espera.png", "text_key": "ESPERA"},
            # Personas
            {"nombre": "mama", "archivo": "Inicio/mama.png", "text_key": "MAMÁ"},
            {"nombre": "enfermera", "archivo": "Inicio/enfermera.png", "text_key": "ENFERMERA"},
            {"nombre": "hermano", "archivo": "Inicio/hermano.png", "text_key": "HERMANO"},
            {"nombre": "papa", "archivo": "Inicio/papa.png", "text_key": "PAPÁ"},
            {"nombre": "maestra", "archivo": "Inicio/maestra.png", "text_key": "MAESTRA"},
            {"nombre": "amigo", "archivo": "Inicio/amigo.png", "text_key": "AMIGO"},
            # Actividades
            {"nombre": "jugar-act", "archivo": "Inicio/jugar.png", "text_key": "JUGAR"},
            {"nombre": "salir-act", "archivo": "Inicio/salir.png", "text_key": "SALIR"},
            {"nombre": "musica", "archivo": "Inicio/musica.png", "text_key": "MÚSICA"},
            {"nombre": "television", "archivo": "Inicio/television.png", "text_key": "TELEVISIÓN"},
            {"nombre": "dormir", "archivo": "Inicio/dormir.png", "text_key": "DORMIR"},
            {"nombre": "libro", "archivo": "Inicio/libro.png", "text_key": "LIBRO"},
        ]

        for icono_info in iconos_info:
            try:
                ruta = imagen(icono_info["archivo"])
                if os.path.exists(ruta):
                    img = pygame.image.load(ruta)
                    self.iconos[icono_info["nombre"]] = {
                        "imagen": pygame.transform.scale(img, (tamaño_icono, tamaño_icono)),
                        "text_key": icono_info["text_key"]
                    }
                else:
                    superficie = pygame.Surface((tamaño_icono, tamaño_icono), pygame.SRCALPHA)
                    pygame.draw.circle(superficie, (100, 100, 200), (tamaño_icono // 2, tamaño_icono // 2),
                                       tamaño_icono // 2 - 5)
                    self.iconos[icono_info["nombre"]] = {
                        "imagen": superficie,
                        "text_key": icono_info["text_key"]
                    }
            except Exception as e:
                print(f"Error cargando icono {icono_info['nombre']}: {e}")

    def crear_cuadros(self):
        area = pygame.Rect(0, 0, self.ancho, self.alto)
        margen_x = int(area.width * 0.02)
        margen_y = int(area.height * 0.02)
        columnas = 3
        filas = 2
        ancho_cuadro = (area.width - (columnas + 1) * margen_x) // columnas
        alto_cuadro = (area.height - (filas + 1) * margen_y) // filas

        cuadros = [
            {"rect": pygame.Rect(area.x + margen_x, area.y + margen_y, ancho_cuadro, alto_cuadro),
             "color": self.COLOR_SOCIALES, "title_key": "SOCIALES"},
            {"rect": pygame.Rect(area.x + 2*margen_x + ancho_cuadro, area.y + margen_y, ancho_cuadro, alto_cuadro),
             "color": self.COLOR_NECESIDADES, "title_key": "NECESIDADES"},
            {"rect": pygame.Rect(area.x + 3*margen_x + 2*ancho_cuadro, area.y + margen_y, ancho_cuadro, alto_cuadro),
             "color": self.COLOR_EMOCIONES, "title_key": "EMOCIONES"},
            {"rect": pygame.Rect(area.x + margen_x, area.y + 2*margen_y + alto_cuadro, ancho_cuadro, alto_cuadro),
             "color": self.COLOR_CONTROL, "title_key": "CONTROL"},
            {"rect": pygame.Rect(area.x + 2*margen_x + ancho_cuadro, area.y + 2*margen_y + alto_cuadro, ancho_cuadro, alto_cuadro),
             "color": self.COLOR_PERSONAS, "title_key": "PERSONAS"},
            {"rect": pygame.Rect(area.x + 3*margen_x + 2*ancho_cuadro, area.y + 2*margen_y + alto_cuadro, ancho_cuadro, alto_cuadro),
             "color": self.COLOR_ACTIVIDADES, "title_key": "ACTIVIDADES"}
        ]
        return cuadros

    def crear_botones_comunicacion(self):
        botones = []
        tamaño_icono = int(min(self.ancho, self.alto) * 0.1)
        espacio_vertical = int(tamaño_icono * 0.2)
        espacio_horizontal = int(tamaño_icono * 0.1)

        categorias = [
            {"nombre": "sociales", "posicion": self.cuadros[0]["rect"].topleft,
             "botones": ["hola", "adios", "gracias", "porfavor", "si", "no"]},
            {"nombre": "necesidades", "posicion": self.cuadros[1]["rect"].topleft,
             "botones": ["hambre", "incomodo", "bano", "sed", "cansado", "dolor"]},
            {"nombre": "emociones", "posicion": self.cuadros[2]["rect"].topleft,
             "botones": ["feliz", "triste", "enojado", "miedo", "nervioso", "calma"]},
            {"nombre": "control", "posicion": self.cuadros[3]["rect"].topleft,
             "botones": ["ayuda", "no-quiero", "mas", "quiero", "basta", "espera"]},
            {"nombre": "personas", "posicion": self.cuadros[4]["rect"].topleft,
             "botones": ["mama", "enfermera", "hermano", "papa", "maestra", "amigo"]},
            {"nombre": "actividades", "posicion": self.cuadros[5]["rect"].topleft,
             "botones": ["jugar-act", "salir-act", "musica", "television", "dormir", "libro"]}
        ]

        for categoria in categorias:
            base_x, base_y = categoria["posicion"]
            botones_categoria = categoria["botones"]
            ancho_cuadro = self.cuadros[0]["rect"].width
            alto_cuadro = self.cuadros[0]["rect"].height
            espacio_disponible_x = ancho_cuadro - 2 * espacio_horizontal
            espacio_disponible_y = alto_cuadro - 2 * espacio_vertical - 50
            celda_ancho = espacio_disponible_x // 3
            celda_alto = espacio_disponible_y // 2
            for i, nombre_icono in enumerate(botones_categoria):
                fila = i // 3
                columna = i % 3
                x = base_x + espacio_horizontal + columna * celda_ancho
                y = base_y + espacio_vertical + 50 + fila * celda_alto
                icono_ancho = celda_ancho - 20
                icono_alto = celda_alto - 40
                tam_icono = min(icono_ancho, icono_alto)
                rect_x = x + (celda_ancho - tam_icono) // 2
                rect_y = y
                rect = pygame.Rect(rect_x, rect_y, tam_icono, tam_icono)
                if nombre_icono in self.iconos:
                    botones.append({
                        "rect": rect,
                        "icono": nombre_icono,
                        "text_key": self.iconos[nombre_icono]["text_key"],
                        "texto_pos": (x + celda_ancho // 2, rect_y + tam_icono + 20)
                    })
        return botones

    def dibujar_cuadro(self, cuadro):
        pygame.draw.rect(self.pantalla, cuadro["color"], cuadro["rect"], border_radius=20)
        pygame.draw.rect(self.pantalla, self.COLOR_AZUL, cuadro["rect"], width=3, border_radius=20)
        if "title_key" in cuadro:
            texto = config.render_text(config.traductor.t(cuadro["title_key"]), config.fuente, config.NEGRO)
            # Ajuste de posición para que no se salga del cuadro
            texto_rect = texto.get_rect(center=(cuadro["rect"].centerx, cuadro["rect"].y + 30))
            self.pantalla.blit(texto, texto_rect)

    def dibujar_boton_comunicacion(self, boton_info, mouse_pos):
        boton_rect = boton_info["rect"]
        icono_data = self.iconos.get(boton_info["icono"])
        if not icono_data:
            return
        color_fondo = (221, 162, 105)
        if boton_rect.collidepoint(mouse_pos):
            color_fondo = (200, 150, 100)
        sombra_rect = pygame.Rect(boton_rect.x + 3, boton_rect.y + 3, boton_rect.width, boton_rect.height)
        pygame.draw.rect(self.pantalla, (0, 0, 0, 80), sombra_rect, border_radius=15)
        pygame.draw.rect(self.pantalla, color_fondo, boton_rect, border_radius=15)
        pygame.draw.rect(self.pantalla, (0, 0, 0, 100), boton_rect, width=2, border_radius=15)
        icono_rect = icono_data["imagen"].get_rect(center=boton_rect.center)
        self.pantalla.blit(icono_data["imagen"], icono_rect)

        texto_traducido = config.traductor.t(boton_info["text_key"])
        texto_surface = config.render_text(texto_traducido, config.fuente_muy_pequena, config.NEGRO)
        if "texto_pos" in boton_info:
            texto_rect = texto_surface.get_rect(center=boton_info["texto_pos"])
        else:
            texto_rect = texto_surface.get_rect(center=(boton_rect.centerx, boton_rect.bottom + 15))
        self.pantalla.blit(texto_surface, texto_rect)

    def ejecutar(self):
        self.pantalla = pygame.display.get_surface()
        if self.pantalla is None:
            print("[ERROR] No se pudo obtener la pantalla en Inicio")
            return "menu_principal"

        self.ancho, self.alto = self.pantalla.get_size()
        if self.camara is None:
            self.camara = ManejoCamara(ancho=self.ancho, alto=self.alto, modo_ocular=True)

        self.cargar_iconos()
        self.cuadros = self.crear_cuadros()
        self.botones_comunicacion = self.crear_botones_comunicacion()

        # Barra inferior autónoma
        self.barra_inferior = BarraInferior(
            camara=self.camara,
            gestor_musica=self.gestor_musica,
            decir_texto=self.decir_texto,
            ID_sesion=self.ID_sesion
        )

        reloj = pygame.time.Clock()
        ejecutando = True
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

        while ejecutando:
            try:
                cursor_x, cursor_y, clic_camara = self.camara.obtener_posicion_y_clic()
                clic_activo = clic_camara and not self.control_clic
                self.control_clic = clic_camara
            except Exception as e:
                cursor_x, cursor_y = pygame.mouse.get_pos()
                clic_activo = pygame.mouse.get_pressed()[0]

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

            self.barra_inferior.actualizar_visibilidad((cursor_x, cursor_y), self.alto)

            self.pantalla.fill(self.COLOR_FONDO)

            for cuadro in self.cuadros:
                self.dibujar_cuadro(cuadro)

            for boton in self.botones_comunicacion:
                self.dibujar_boton_comunicacion(boton, (cursor_x, cursor_y))
                if boton["rect"].collidepoint(cursor_x, cursor_y) and clic_activo:
                    texto_tts = config.traductor.t(boton["text_key"])
                    self.decir_texto(texto_tts)
                    pygame.time.delay(200)

            self.barra_inferior.dibujar(self.pantalla, (cursor_x, cursor_y))
            destino = self.barra_inferior.manejar_clic((cursor_x, cursor_y), clic_activo)
            if destino:
                self.camara.pausar_cursor()
                return destino

            try:
                dibujar_cursor_unificado(self.pantalla, cursor_x, cursor_y, modo_ocular=True,
                                         ancho=self.ancho, alto=self.alto)
            except Exception as e:
                pygame.draw.circle(self.pantalla, config.ROJO, (cursor_x, cursor_y), 10, 2)

            pygame.display.flip()
            reloj.tick(60)

        self.camara.pausar_cursor()
        return "menu_principal"