import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


class APICliente:
    """
    Versión DEMO de APICliente: funciona 100% en memoria, sin servidor,
    sin MySQL y sin red. Mantiene las mismas firmas de método que el
    APICliente real para que los juegos y pantallas no se rompan.
    """

    def __init__(self, base_url=None, max_reintentos=3, espera_reintento=1):
        self.base_url = base_url or "demo://localhost:3000/api"
        self.token = None
        self.sesion_actual = None
        self.archivo_config = "config_api.json"
        self.max_reintentos = max_reintentos
        self.espera_reintento = espera_reintento

        self._usuarios = [
            {"ID_usuario": 1, "Nickname": "Invitado Demo", "FechaNacimiento": "2015-01-01"},
        ]
        self._sesiones = [
            {"ID_sesion": 1, "ID_usuario": 1, "Fecha_Registro": "2026-01-01"},
        ]
        self._configuraciones = []
        self._resultados = []
        self._contadores = {"usuarios": 2, "sesiones": 2, "resultados": 1}
        self._juegos = [
            {"ID_juego": 1, "Nombre": "Pares mágicos"},
            {"ID_juego": 2, "Nombre": "Animalia"},
            {"ID_juego": 3, "Nombre": "Mate-reto"},
            {"ID_juego": 4, "Nombre": "Encuentra y aprende"},
            {"ID_juego": 5, "Nombre": "Caza letras"},
        ]

    # -------------------- OPERACIONES BÁSICAS (en memoria) --------------------
    def crear_registro(self, tabla, datos):
        if tabla == "usuarios":
            nuevo = dict(datos)
            nuevo["ID_usuario"] = self._contadores["usuarios"]
            self._contadores["usuarios"] += 1
            self._usuarios.append(nuevo)
            return {"id": nuevo["ID_usuario"], **nuevo}
        if tabla == "sesiones":
            nuevo = dict(datos)
            nuevo["ID_sesion"] = self._contadores["sesiones"]
            self._contadores["sesiones"] += 1
            nuevo["Fecha_Registro"] = "2026-01-01"
            self._sesiones.append(nuevo)
            return {"id": nuevo["ID_sesion"], **nuevo}
        if tabla == "resultados":
            nuevo = dict(datos)
            nuevo["ID_resultado"] = self._contadores["resultados"]
            self._contadores["resultados"] += 1
            self._resultados.append(nuevo)
            return {"id": nuevo["ID_resultado"], **nuevo}
        if tabla == "configuracion_usuario":
            nuevo = dict(datos)
            nuevo["id_config"] = len(self._configuraciones) + 1
            self._configuraciones.append(nuevo)
            return {"id": nuevo["id_config"], **nuevo}
        if tabla == "juegos":
            nuevo = dict(datos)
            nuevo["ID_juego"] = len(self._juegos) + 1
            self._juegos.append(nuevo)
            return {"id": nuevo["ID_juego"], **nuevo}
        return {"error": "tabla_desconocida"}

    def obtener_registros(self, tabla):
        return {
            "usuarios": self._usuarios,
            "sesiones": self._sesiones,
            "resultados": self._resultados,
            "juegos": self._juegos,
            "configuracion_usuario": self._configuraciones,
            "historial_resultados": self._resultados,
        }.get(tabla, [])

    def obtener_registro_por_id(self, tabla, id_registro):
        for reg in self.obtener_registros(tabla):
            pk = "ID_usuario" if tabla == "usuarios" else (
                "ID_sesion" if tabla == "sesiones" else (
                    "ID_resultado" if tabla == "resultados" else (
                        "id_config" if tabla == "configuracion_usuario" else "ID_juego")))
            if str(reg.get(pk)) == str(id_registro):
                return reg
        return None

    def actualizar_registro(self, tabla, id_registro, datos):
        reg = self.obtener_registro_por_id(tabla, id_registro)
        if reg is None:
            return {"error": "no_encontrado"}
        reg.update(datos)
        return reg

    def eliminar_registro(self, tabla, id_registro):
        pk = "ID_usuario" if tabla == "usuarios" else (
            "ID_sesion" if tabla == "sesiones" else (
                "ID_resultado" if tabla == "resultados" else (
                    "id_config" if tabla == "configuracion_usuario" else "ID_juego")))
        lista = self.obtener_registros(tabla)
        for i, reg in enumerate(lista):
            if str(reg.get(pk)) == str(id_registro):
                del lista[i]
                return {"ok": True}
        return None

    # -------------------- FUNCIONES ESPECÍFICAS --------------------
    def obtener_todos_usuarios(self):
        return self._usuarios

    def obtener_todas_sesiones(self):
        return self._sesiones

    def eliminar_sesion(self, id_sesion):
        return self.eliminar_registro("sesiones", id_sesion)

    def eliminar_usuario(self, id_usuario):
        return self.eliminar_registro("usuarios", id_usuario)

    def crear_usuario(self, nombre, FechaNacimiento=0):
        return self.crear_registro("usuarios", {"Nickname": nombre, "FechaNacimiento": FechaNacimiento})

    def actualizar_usuario(self, id_usuario, nombre, FechaNacimiento):
        return self.actualizar_registro("usuarios", id_usuario, {"Nickname": nombre, "FechaNacimiento": FechaNacimiento})

    def crear_sesion(self, usuario_id):
        for sesion in self._sesiones:
            if str(sesion.get("ID_usuario")) == str(usuario_id):
                return sesion.get("ID_sesion")
        resultado = self.crear_registro("sesiones", {"ID_usuario": usuario_id})
        if resultado and "id" in resultado:
            return resultado["id"]
        return None

    def registrar_resultado(self, sesion_id, Nombre_juego, puntaje, aciertos, errores):
        id_juego = self.obtenerID_juego(Nombre_juego)
        if not id_juego:
            return {"error": f"no se encontro el juego {Nombre_juego}"}
        for reg in self._resultados:
            if str(reg.get("ID_sesion")) == str(sesion_id) and reg.get("ID_juego") == id_juego:
                return self.actualizar_registro("resultados", reg["ID_resultado"], {
                    "Puntaje": puntaje, "Aciertos": aciertos, "Errores": errores})
        return self.crear_registro("resultados", {
            "ID_sesion": sesion_id, "ID_juego": id_juego,
            "Puntaje": puntaje, "Aciertos": aciertos, "Errores": errores})

    def obtener_historial_resultados(self, sesion_id=None):
        resultado = self._resultados
        if sesion_id:
            resultado = [r for r in resultado if str(r.get("ID_sesion")) == str(sesion_id)]
        return resultado

    def obtenerID_juego(self, nombre_juego):
        for juego in self._juegos:
            if juego.get("Nombre") == nombre_juego:
                return juego.get("ID_juego")
        return None

    def obtenerID_usuario(self, id_Sesion):
        for sesion in self._sesiones:
            try:
                if str(sesion.get("ID_sesion")) == str(id_Sesion):
                    return int(sesion.get("ID_usuario"))
            except Exception:
                continue
        return None

    def Obterner_Usuario(self, id_usuario):
        for u in self._usuarios:
            try:
                if str(u.get("ID_usuario")) == str(id_usuario):
                    return str(u.get("Nickname"))
            except Exception:
                continue
        return None

    def obtener_id_usuario(self, Nickname):
        for u in self._usuarios:
            if u.get("Nickname") == Nickname:
                return int(u.get("ID_usuario"))
        return None

    def cargar_sesion_usuario(self, Nickname):
        usuario_id = self.obtener_id_usuario(Nickname)
        if usuario_id is None:
            return None
        for sesion in self._sesiones:
            if sesion.get("ID_usuario") == usuario_id:
                return sesion.get("ID_sesion")
        return None

    def obtener_sesion_por_id(self, id_sesion):
        return self.obtener_registro_por_id("sesiones", id_sesion)

    def obtener_resultados_por_sesion(self, id_sesion):
        return [r for r in self._resultados if str(r.get("ID_sesion")) == str(id_sesion)]

    def obtener_historial_completo(self, id_sesion):
        resultado = []
        for r in self.obtener_resultados_por_sesion(id_sesion):
            juego_info = self.obtener_juego_por_id(r.get("ID_juego")) or {}
            resultado.append({**r, "nombre_juego": juego_info.get("Nombre", "Juego"), "juego_info": juego_info})
        return resultado

    def obtener_juego_por_id(self, id_juego):
        return self.obtener_registro_por_id("juegos", id_juego)

    # -------------------- CONFIGURACIÓN LOCAL (sin escritura en disco) --------------------
    def cargar_config_local(self):
        return None

    def guardar_config_local(self, datos_config):
        return True

    def cargar_ultima_sesion(self):
        if self.sesion_actual:
            return self.sesion_actual
        if self._sesiones:
            self.sesion_actual = self._sesiones[-1]["ID_sesion"]
            return self.sesion_actual
        return None

    def crear_perfil_completo(self, nombre_usuario):
        usuario_existente = self.obtener_id_usuario(nombre_usuario)
        if usuario_existente:
            sesion_existente = self.cargar_sesion_usuario(nombre_usuario)
            if sesion_existente:
                self.sesion_actual = sesion_existente
                return sesion_existente
        resultado_usuario = self.crear_usuario(nombre_usuario)
        if not resultado_usuario:
            return None
        usuario_id = resultado_usuario.get("id")
        if not usuario_id:
            return None
        resultado_sesion = self.crear_sesion(usuario_id)
        if not resultado_sesion:
            return None
        self.sesion_actual = resultado_sesion
        return resultado_sesion

    def diagnosticar_conexion(self):
        print("🔍 [DEMO] Diagnóstico de API (en memoria) OK.")
        return True

    # -------------------- CONFIGURACIÓN DE USUARIO --------------------
    def obtener_configuracion_usuario(self, id_usuario):
        for config in self._configuraciones:
            if str(config.get("ID_usuario")) == str(id_usuario):
                return config
        return None

    def guardar_configuracion_usuario(self, id_usuario, idioma=None, volumen_musica=None, volumen_efectos=None):
        config_actual = self.obtener_configuracion_usuario(id_usuario)
        datos = {
            "ID_usuario": id_usuario,
            "idioma": idioma if idioma is not None else (config_actual.get("idioma") if config_actual else "es"),
            "volumen_musica": volumen_musica if volumen_musica is not None else (
                config_actual.get("volumen_musica") if config_actual else 50),
            "volumen_efectos": volumen_efectos if volumen_efectos is not None else (
                config_actual.get("volumen_efectos") if config_actual else 80),
        }
        if config_actual:
            return self.actualizar_registro("configuracion_usuario", config_actual["id_config"], datos)
        return self.crear_registro("configuracion_usuario", datos)

    def obtener_id_usuario_desde_sesion(self, id_sesion):
        sesion = self.obtener_sesion_por_id(id_sesion)
        if sesion:
            return sesion.get("ID_usuario")
        return None
