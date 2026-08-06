import pygame
import random
import os
from core.paths import audio, sonidos
class GestorMusica:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GestorMusica, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            pygame.mixer.init()
            self.volumen_musica = 1.0
            self.volumen_efectos = 1.0
            self.musica_pausada = False
            self.cancion_actual = None
            self.canciones = self._cargar_canciones_validas()
            self.sonidos = self._cargar_sonidos_validos()  # Nueva línea
            self._initialized = True

    def _cargar_canciones_validas(self):
        """Carga solo las canciones que existen"""
        canciones_posibles = {
            "Spc80s": os.path.join(audio("Spc80s.mp3")),
            "SpcBeach": os.path.join(audio("SpcBeach.mp3")),
            "SpcDefault": os.path.join(audio("SpcDefault.mp3")),
            "SpcMain": os.path.join(audio("SpcMain.mp3")),
            "SpcPlayground": os.path.join(audio("SpcPlayground.mp3")),
            "SpcRoom": os.path.join(audio("SpcRoom.mp3")),
            "SpcSky": os.path.join(audio("SpcSky.mp3")),
            "SpcStar": os.path.join(audio("SpcStar.mp3")),
            "SpcWhy": os.path.join(audio("SpcWhy.mp3"))
        }

        canciones_validas = {}
        for nombre, ruta in canciones_posibles.items():
            if os.path.exists(ruta):
                canciones_validas[nombre] = ruta
            else:
                print(f"⚠️ No se encuentra: {ruta}")

        return canciones_validas

    def _cargar_sonidos_validos(self):
        """Carga los efectos de sonido válidos"""
        sonidos_posibles = {
            "correcto": os.path.join(sonidos("completado.mp3")),
            "incorrecto": os.path.join(sonidos("incorrecto.wav")),
            "clic": os.path.join(sonidos("clic.mp3")),
            "completado": os.path.join(sonidos("completado.mp3")),
            "globo": os.path.join(sonidos("globo_desinflandose.mp3")),
            "sonido_match":os.path.join(sonidos("sonido_match.wav")),
            "sonido_voltear": os.path.join(sonidos("sonido_voltear.wav")),
            "sonido_ganar": os.path.join(sonidos("correcto.wav"))
        }

        sonidos_validos = {}
        for nombre, ruta in sonidos_posibles.items():
            if os.path.exists(ruta):
                try:
                    sonidos_validos[nombre] = pygame.mixer.Sound(ruta)
                    print(f"[OK] Sonido cargado: {nombre}")
                except pygame.error as e:
                    print(f"[ERROR] Error cargando sonido {nombre}: {e}")
            else:
                print(f"[WARNING] Sonido no encontrado: {ruta}")

        return sonidos_validos

    def reproducir_sonido(self, nombre_sonido):
        """Reproduce un efecto de sonido"""
        if nombre_sonido in self.sonidos:
            try:
                self.sonidos[nombre_sonido].set_volume(self.volumen_efectos)
                self.sonidos[nombre_sonido].play()
            except pygame.error as e:
                print(f"[ERROR] Error reproduciendo sonido {nombre_sonido}: {e}")
        else:
            print(f"[WARNING] Sonido no disponible: {nombre_sonido}")

    def iniciar_musica(self, cancion=None):
        """Inicia la música con una canción aleatoria o específica"""
        if not self.canciones:
            print("[WARNING] No hay canciones disponibles")
            return

        if cancion is None:
            nueva_cancion = random.choice(list(self.canciones.keys()))
        else:
            nueva_cancion = cancion

        # Si ya está reproduciendo la misma canción, solo actualizar volumen
        if pygame.mixer.music.get_busy() and self.cancion_actual == nueva_cancion:
            pygame.mixer.music.set_volume(self.volumen_musica)
            print(f"[MUSIC] Volumen actualizado para: {nueva_cancion}")
            return

        self.cancion_actual = nueva_cancion

        if self.cancion_actual in self.canciones:
            try:
                pygame.mixer.music.load(self.canciones[self.cancion_actual])
                pygame.mixer.music.play(-1)  # -1 para reproducir en loop
                pygame.mixer.music.set_volume(self.volumen_musica)
                self.musica_pausada = False
                print(f"[MUSIC] Reproduciendo: {self.cancion_actual}")
            except pygame.error as e:
                print(f"[ERROR] Error al cargar cancion: {e}")

    def cambiar_cancion(self, nombre_cancion):
        """Cambia a una canción específica"""
        if nombre_cancion in self.canciones:
            self.iniciar_musica(nombre_cancion)

    def pausar_musica(self):
        """Pausa la música"""
        if pygame.mixer.music.get_busy() and not self.musica_pausada:
            pygame.mixer.music.pause()
            self.musica_pausada = True

    def reanudar_musica(self):
        """Reanuda la música"""
        if self.musica_pausada:
            pygame.mixer.music.unpause()
            self.musica_pausada = False

    def establecer_volumen_musica(self, volumen):
        """Establece el volumen de la música"""
        self.volumen_musica = max(0.0, min(1.0, volumen))
        pygame.mixer.music.set_volume(self.volumen_musica)

    def establecer_volumen_efectos(self, volumen):
        """Establece el volumen de los efectos"""
        self.volumen_efectos = max(0.0, min(1.0, volumen))
        # Actualizar volumen de todos los sonidos cargados
        for sonido in self.sonidos.values():
            sonido.set_volume(self.volumen_efectos)


# Instancia global del gestor de música
gestor_musica = GestorMusica()