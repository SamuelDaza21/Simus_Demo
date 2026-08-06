# Servidor.py (versión DEMO)
# Stub inofensivo: en el demo NO se levanta ningún servidor HTTP ni MySQL.
# Todas las operaciones de datos son atendidas por APICliente en memoria.
import os


class Servidor:
    _server = None
    _thread = None

    def __init__(self, ruta_api=None):
        self.ruta_api = ruta_api

    def iniciar(self):
        print("[DEMO] Servidor API desactivado (modo demo sin MySQL).")

    def detener(self):
        pass
