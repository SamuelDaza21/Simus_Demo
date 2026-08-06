import json
import os
import atexit
from api.APICliente import APICliente

api = APICliente()


class BaseGame:
    """
    Clase base para todos los juegos del sistema SIMUS.MJN.
    Contiene la lógica común de backup y registro de resultados.

    Atributos:
        id_sesion: ID de la sesión del usuario
        nombre_juego: Nombre del juego para el registro en API
        backup_file: Archivo de backup específico del juego
        resultado_temporal: Diccionario con datos temporales del juego
    """

    def __init__(self, id_sesion, nombre_juego):
        """
        Inicializa la clase base con el ID de sesión y nombre del juego.

        Args:
            id_sesion: ID de la sesión del usuario
            nombre_juego: Nombre del juego (ej: "Caza letras", "Animalia", etc.)
        """
        self.id_sesion = id_sesion
        self.nombre_juego = nombre_juego
        self.backup_file = f"backup_{nombre_juego.lower().replace(' ', '_')}.json"

        # Estructura común de resultados temporales
        self.resultado_temporal = {
            "id_sesion": id_sesion,
            "puntaje": 0,
            "aciertos": 0,
            "errores": 0
        }

        # Registrar el guardado automático al cerrar el programa
        atexit.register(self.guardar_resultado_final)

    def guardar_backup_local(self):
        """
        Guarda el progreso localmente si no se puede enviar a la API.
        """
        try:
            with open(self.backup_file, "w") as f:
                json.dump(self.resultado_temporal, f)
            print("💾 Resultado guardado localmente.")
        except Exception as e:
            print("❌ Error al guardar backup:", e)

    def enviar_backup_si_existe(self):
        """
        Si hay un backup pendiente, intenta enviarlo antes de iniciar el juego.
        """
        if os.path.exists(self.backup_file):
            try:
                with open(self.backup_file, "r") as f:
                    data = json.load(f)
                api.registrar_resultado(
                    data["id_sesion"],
                    self.nombre_juego,
                    data["puntaje"],
                    data["aciertos"],
                    data["errores"]
                )
                os.remove(self.backup_file)
                print("📤 Backup anterior enviado correctamente.")
            except Exception as e:
                print("🌐 No se pudo enviar el backup anterior:", e)

    def guardar_resultado_final(self):
        """
        Envia automáticamente el resultado si el programa se cierra inesperadamente.
        """
        if self.resultado_temporal["id_sesion"] is not None:
            try:
                respuesta = api.registrar_resultado(
                    self.resultado_temporal["id_sesion"],
                    self.nombre_juego,
                    self.resultado_temporal["puntaje"],
                    self.resultado_temporal["aciertos"],
                    self.resultado_temporal["errores"]
                )
                if isinstance(respuesta, dict) and "error" in respuesta:
                    print(f"❌ Falló el envío automático: {respuesta.get('error')}. Se guardará localmente.")
                    self.guardar_backup_local()
                else:
                    print("📡 Resultado final enviado automáticamente.")
            except Exception as e:
                print("❌ Falló el envío automático, se guardará localmente.")
                self.guardar_backup_local()

    def actualizar_resultados(self, puntaje=None, aciertos=None, errores=None):
        """
        Método helper para actualizar los resultados temporales.

        Args:
            puntaje: Nuevo puntaje (opcional)
            aciertos: Nuevos aciertos (opcional)
            errores: Nuevos errores (opcional)
        """
        if puntaje is not None:
            self.resultado_temporal["puntaje"] = puntaje
        if aciertos is not None:
            self.resultado_temporal["aciertos"] = aciertos
        if errores is not None:
            self.resultado_temporal["errores"] = errores