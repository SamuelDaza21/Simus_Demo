import os
import pygame
from core.paths import imagen, fuentes
from core.Traductor import Traductor
import json
from pathlib import Path

# Cargar variables de entorno desde simus_mjn/.env (GROQ_API_KEY, API_URL, ...).
# Sin esto, solo Node leia el .env y las claves no llegaban a Python.
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parents[2] / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass

# Inicializar pygame y audio (una sola vez)
pygame.init()
try:
    pygame.mixer.init()
    print("Sonido inicializado correctamente.")
except pygame.error:
    print("Advertencia: No se detectó dispositivo de audio. Continuando en modo silencioso...")
pygame.font.init()

# Dimensiones y pantalla (se actualizarán después de crear la pantalla real)
PANTALLA = None
ANCHO, ALTO = 800, 600  # valores temporales

# Colores globales
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
AMARILLO = (255, 215, 0)
GRIS_OSCURO = (40, 40, 40)
BLANCO_TRANSPARENTE = (255, 255, 255, 180)
AMARILLO_SUAVE = (255, 255, 150)
CELESTE = (173, 216, 230)
COLOR_FONDO = (135, 206, 235)
COLOR_FONDO_B = (204, 130, 76)
COLOR_BORDE = (221, 162, 105)
FONDO_BOTON = COLOR_FONDO_B
BORDE_BOTON = COLOR_BORDE
AZUL = (100, 149, 237)
CAMBIO_COLOR_SOBRE_DE = (230, 160, 100)
COLORES = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 105, 180), (0, 255, 255), (0, 0, 0)]
BARRA = (100, 200, 100)
SOMBRA = (180, 180, 220)
VERDE = (0, 255, 0)
ROJO = (255, 0, 0)
HOVER = COLOR_BORDE
COLOR_TEXTO = NEGRO
TEXTO = COLOR_TEXTO  # Alias para compatibilidad
COLOR_INPUT = (80, 50, 30)
SAVE_BG = FONDO_BOTON
SAVE_BORDER = BORDE_BOTON

# Fuentes específicas por idioma (rutas de los archivos .ttf)
FUENTES_IDIOMAS = {
    "es": fuentes("ESPAÑOL.ttf"),
    "en": fuentes("INGLES.ttf"),
    "fr": fuentes("FRANCES.ttf"),
}

# Fuentes globales que se actualizarán dinámicamente
fuente = None
fuente_pequena = None
fuente_muy_pequena = None
FUENTE = None  # Alias uppercase para compatibilidad
FUENTE_PEQUENA = None  # Alias uppercase para compatibilidad

# Traductor global
traductor = None


def cargar_fuentes_para_idioma(idioma):
    """Carga las tres fuentes según el idioma, con fallback a fuentes del sistema si el archivo TTF no existe."""
    global fuente, fuente_pequena, fuente_muy_pequena, FUENTE, FUENTE_PEQUENA

    # Fallback para Windows (fuentes del sistema que soportan cada idioma)
    fallback_windows = {
        "es": "Arial",
        "en": "Arial",
        "fr": "Arial"
    }

    # 1. Intentar cargar desde archivo TTF personalizado
    ruta_ttf = FUENTES_IDIOMAS.get(idioma)
    if ruta_ttf and os.path.exists(ruta_ttf):
        try:
            fuente = pygame.font.Font(ruta_ttf, 36)
            fuente_pequena = pygame.font.Font(ruta_ttf, 28)
            fuente_muy_pequena = pygame.font.Font(ruta_ttf, 20)
            FUENTE = fuente
            FUENTE_PEQUENA = fuente_pequena
            print(f"Fuentes cargadas correctamente para {idioma} desde {ruta_ttf}")
            return
        except Exception as e:
            print(f"Error cargando fuente {ruta_ttf}: {e}. Usando fallback del sistema.")

    # 2. Fallback a fuentes del sistema (si el idioma está en el diccionario)
    if idioma in fallback_windows:
        nombre_fuente = fallback_windows[idioma]
        try:
            fuente = pygame.font.SysFont(nombre_fuente, 36)
            fuente_pequena = pygame.font.SysFont(nombre_fuente, 27)
            fuente_muy_pequena = pygame.font.SysFont(nombre_fuente, 20)
            FUENTE = fuente
            FUENTE_PEQUENA = fuente_pequena
            print(f"Fuentes del sistema usadas para {idioma}: {nombre_fuente}")
            return
        except Exception as e:
            print(f"Error con fuente del sistema {nombre_fuente}: {e}")

    # 3. Último fallback: fuente por defecto de pygame
    print(f"Advertencia: No se pudo cargar fuente para {idioma}, usando fuente por defecto.")
    fuente = pygame.font.Font(None, 36)
    fuente_pequena = pygame.font.Font(None, 28)
    fuente_muy_pequena = pygame.font.Font(None, 20)
    FUENTE = fuente
    FUENTE_PEQUENA = fuente_pequena


def setup_traductor(idioma="es"):
    global traductor
    traductor = Traductor(idioma)
    cargar_fuentes_para_idioma(idioma)


def cambiar_idioma(idioma):
    global traductor
    if traductor:
        traductor = Traductor(idioma)
    else:
        setup_traductor(idioma)
    cargar_fuentes_para_idioma(idioma)
    print(f"[IDIOMA] Cambiado a {idioma}")
    if os.environ.get("DEMO_MODE") == "true":
        return
    # Guardar idioma en archivo de configuración para que lo lean otros procesos (Streamlit)
    CONFIG_PATH = Path(__file__).resolve().parents[1] / "config_api.json"
    try:
        with open(CONFIG_PATH, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data["idioma"] = idioma
            f.seek(0)
            json.dump(data, f)
            f.truncate()
    except Exception as e:
        print(f"No se pudo guardar el idioma en config_api.json: {e}")


def init_pantalla():
    """Crea la pantalla fullscreen y actualiza ANCHO, ALTO"""
    global PANTALLA, ANCHO, ALTO
    PANTALLA = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.RESIZABLE)
    ANCHO, ALTO = PANTALLA.get_size()
    return PANTALLA


def render_text(text, font, color, antialias=True):
    return font.render(text, antialias, color)


# Alias para compatibilidad con otros módulos
FONDO_PRINCIPAL = imagen("General/fondo.png")
FONDO_JUEGOS = imagen("Juegos/juegos_menu.png")
FONDO_BOTONES = imagen("General/fondo.png")
URL_API = "http://LOCALHOST:3000"
FONDO = FONDO_PRINCIPAL
CARPETA_IMG = imagen("Botones")