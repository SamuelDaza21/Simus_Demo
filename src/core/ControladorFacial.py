from logic.cursor import ControladorCursor as ControladorCursorCentral


class ControladorFacial:
    """Compatibilidad retroactiva con el controlador anterior."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, ancho=1620, alto=900, sesion_id=None):
        if getattr(self, '_inicializado', False):
            return

        self._inicializado = True
        self.cursor = ControladorCursorCentral(ancho=ancho, alto=alto, sesion_id=sesion_id)

    def obtener_camara(self):
        return self.cursor.obtener_camara()

    def estado_calibrado(self):
        return self.cursor.estado_calibrado()

    def calibrar(self):
        self.cursor.calibrar()

    def pausar(self):
        self.cursor.pausar_cursor()

    def reanudar(self):
        self.cursor.reanudar_cursor()

    def liberar(self):
        self.cursor.liberar_recursos()

