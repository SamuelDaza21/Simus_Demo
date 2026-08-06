import os

# carpeta src
SRC_DIR = os.path.dirname(os.path.dirname(__file__))

# assets dentro de src
ASSETS = os.path.join(SRC_DIR, "assets")
IMAGES = os.path.join(ASSETS, "imagenes")
FONTS = os.path.join(ASSETS, "fuentes")
SOUNDS = os.path.join(ASSETS, "sonidos")
AUDIO = os.path.join(ASSETS, "audio")


def imagen(ruta):
    return os.path.join(IMAGES, ruta)


def fuentes(ruta):
    return os.path.join(FONTS, ruta)


def sonidos(ruta):
    return os.path.join(SOUNDS, ruta)


def audio(ruta):
    return os.path.join(AUDIO, ruta)