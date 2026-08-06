# Api.py
# API REST de SIMUS.MJN en Python (Flask) sobre MySQL.
# Expone los mismos endpoints para que APICliente.py funcione sin cambios.
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Cargar .env desde la raíz del proyecto (DB_*, PORT, API_TOKEN, ...).
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except Exception:
    pass

import mysql.connector
from flask import Flask, request, jsonify, g

# ---------------------- Configuración ----------------------
PORT = int(os.environ.get("PORT", 3000))
# Por defecto escuchamos SOLO en localhost. En Docker se pasa HOST=0.0.0.0 para mapear el puerto.
HOST = os.environ.get("HOST", "127.0.0.1")

# Token opcional: si API_TOKEN está definido, todos los requests deben mandarlo en x-access-token.
API_TOKEN = os.environ.get("API_TOKEN", "")

# Conexión MySQL (misma estructura que el .env histórico).
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 3306)),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "simus_mjn"),
}

# Lista blanca de tablas (misma que la API original)
TABLAS_PERMITIDAS = {
    "usuarios",
    "sesiones",
    "resultados",
    "historial_resultados",
    "configuracion_usuario",
    "juegos",
}

# Lista blanca de columnas POR TABLA: impide inyección SQL por nombres de columna.
COLUMNAS_PERMITIDAS = {
    "usuarios": {"ID_usuario", "ID_grado", "Nickname", "FechaNacimiento"},
    "sesiones": {"ID_sesion", "ID_usuario", "Fecha_Registro"},
    "resultados": {"ID_resultado", "ID_sesion", "ID_juego", "Puntaje", "Aciertos", "Errores", "Fecha"},
    "historial_resultados": {
        "id", "ID_sesion", "Nombre_juego", "puntaje_nuevo", "Nuevo_Acierto",
        "Nuevo_error", "puntaje_antiguo", "Aciertos_antiguo", "Errores_antiguo",
    },
    "configuracion_usuario": {"id_config", "ID_usuario", "idioma", "volumen_musica", "volumen_efectos"},
    "juegos": {
        "ID_juego", "Nombre", "Descripcion", "Nivel_Educativo", "Area_Conocimiento",
        "Objetivos", "Competencias", "Contenidos", "Evaluacion", "Procedimiento",
    },
}

# Mapa de claves primarias
PRIMARY_KEYS = {
    "usuarios": "ID_usuario",
    "sesiones": "ID_sesion",
    "configuracion_usuario": "id_config",
    "juegos": "ID_juego",
    "resultados": "ID_resultado",
    "historial_resultados": "id",
}

# ---------------------- Esquema MySQL ----------------------
SCHEMA = [
    """CREATE TABLE IF NOT EXISTS grados (
      ID_grado        INT NOT NULL AUTO_INCREMENT,
      grado_academico VARCHAR(25) DEFAULT NULL,
      Descripcion     VARCHAR(20) DEFAULT NULL,
      PRIMARY KEY (ID_grado)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci""",
    """CREATE TABLE IF NOT EXISTS juegos (
      ID_juego          INT NOT NULL AUTO_INCREMENT,
      Nombre            VARCHAR(100) NOT NULL,
      Descripcion       TEXT NULL,
      Nivel_Educativo   VARCHAR(50) NULL,
      Area_Conocimiento VARCHAR(50) NULL,
      Objetivos         TEXT NULL,
      Competencias      TEXT NULL,
      Contenidos        TEXT NULL,
      Evaluacion        TEXT NULL,
      Procedimiento     TEXT NULL,
      PRIMARY KEY (ID_juego),
      UNIQUE KEY uq_juegos_nombre (Nombre)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci""",
    """CREATE TABLE IF NOT EXISTS usuarios (
      ID_usuario      INT NOT NULL AUTO_INCREMENT,
      ID_grado        INT NULL,
      Nickname        VARCHAR(25) NULL,
      FechaNacimiento DATE NOT NULL,
      PRIMARY KEY (ID_usuario),
      KEY idx_usuarios_grado (ID_grado),
      CONSTRAINT fk_usuarios_grado FOREIGN KEY (ID_grado)
        REFERENCES grados (ID_grado) ON UPDATE CASCADE ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci""",
    """CREATE TABLE IF NOT EXISTS sesiones (
      ID_sesion      INT NOT NULL AUTO_INCREMENT,
      ID_usuario     INT NOT NULL,
      Fecha_Registro DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (ID_sesion),
      KEY idx_sesiones_usuario (ID_usuario),
      CONSTRAINT fk_sesiones_usuario FOREIGN KEY (ID_usuario)
        REFERENCES usuarios (ID_usuario) ON UPDATE CASCADE ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci""",
    """CREATE TABLE IF NOT EXISTS resultados (
      ID_resultado INT NOT NULL AUTO_INCREMENT,
      ID_sesion    INT NOT NULL,
      ID_juego     INT NOT NULL,
      Puntaje      SMALLINT NULL,
      Aciertos     SMALLINT NULL,
      Errores      SMALLINT NULL,
      Fecha        DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (ID_resultado),
      KEY idx_resultados_sesion (ID_sesion),
      KEY idx_resultados_juego (ID_juego),
      CONSTRAINT fk_resultados_sesion FOREIGN KEY (ID_sesion)
        REFERENCES sesiones (ID_sesion) ON UPDATE CASCADE ON DELETE CASCADE,
      CONSTRAINT fk_resultados_juego FOREIGN KEY (ID_juego)
        REFERENCES juegos (ID_juego) ON UPDATE CASCADE ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci""",
    # historial_resultados: Nombre_juego es un snapshot de auditoría (desnormalización
    # intencional en una tabla histórica, evita joins masivos y cambios de catálogo).
    """CREATE TABLE IF NOT EXISTS historial_resultados (
      id               INT NOT NULL AUTO_INCREMENT,
      ID_sesion        INT NULL,
      Nombre_juego     VARCHAR(100) NULL,
      puntaje_nuevo    SMALLINT NULL,
      Nuevo_Acierto    SMALLINT NULL,
      Nuevo_error      SMALLINT NULL,
      puntaje_antiguo  SMALLINT NULL,
      Aciertos_antiguo SMALLINT NULL,
      Errores_antiguo  SMALLINT NULL,
      PRIMARY KEY (id),
      KEY idx_historial_sesion (ID_sesion),
      CONSTRAINT fk_historial_sesion FOREIGN KEY (ID_sesion)
        REFERENCES sesiones (ID_sesion) ON UPDATE CASCADE ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci""",
    """CREATE TABLE IF NOT EXISTS configuracion_usuario (
      id_config       INT NOT NULL AUTO_INCREMENT,
      ID_usuario      INT NOT NULL,
      idioma          VARCHAR(20) DEFAULT 'es',
      volumen_musica  INT DEFAULT 100,
      volumen_efectos INT DEFAULT 100,
      PRIMARY KEY (id_config),
      UNIQUE KEY uq_config_usuario (ID_usuario),
      CONSTRAINT fk_config_usuario FOREIGN KEY (ID_usuario)
        REFERENCES usuarios (ID_usuario) ON UPDATE CASCADE ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci""",
]

GRADOS_SEMILLA = [
    (1, "Primero", "Primaria"),
    (2, "Segundo", "Primaria"),
    (3, "Tercero", "Primaria"),
    (4, "Cuarto", "Primaria"),
    (5, "Quinto", "Primaria"),
]

# Sembrado de los 5 juegos (mismo contenido pedagógico que siempre)
JUEGOS_SEMILLA = [
    (1, "Pares mágicos", "En este juego se tienen 12 tarjetas, entre ellas salen 6 pares que deben ser encontrados, las tarjetas se ubicarán al azar.", "Primaria", "Matemática", "Trabajar memoria y capacidad de asociación.", "Reconocer las figuras y sus posiciones para asociarlas en las respectivas parejas; desarrollo de competencias cognitivas.", "Reconocimiento de elementos básicos (frutas), trabajo en memoria, concentración y destrezas motrices.", "Número de pares hallados y puntos acumulados; también actitudes y persistencia durante el juego.", "Se muestran 12 tarjetas al azar, el usuario debe encontrar los 6 pares."),
    (2, "Encuentra y aprende", "Se presentan 3 imágenes y un recuadro con un sustantivo; el usuario debe escoger la imagen que coincide con el nombre mostrado.", "Primaria", "Lenguaje", "Comprender vocabulario y asociar palabras con imágenes.", "Reconocimiento y comprensión de palabras básicas; memoria y capacidad de asociación con imágenes.", "Vocabulario básico; asociación palabra-imagen.", "Número de aciertos y desaciertos, tiempo de respuesta y motivación.", "El usuario observa un sustantivo y selecciona la imagen correcta entre 3 opciones."),
    (3, "Caza letras", "Juego tipo ahorcado con imágenes; se deben completar los nombres de sustantivos escogiendo letras entre opciones que aparecen cada 5 segundos; el jugador tiene 3 vidas representadas en globos.", "Primaria", "Lenguaje", "Comprender vocabulario y asociar palabras con imágenes completando nombres de sustantivos.", "Reconocimiento y escritura adecuada de palabras; toma de decisiones bajo tiempo limitado.", "Vocabulario y ortografía; asociación imagen-palabra.", "Número de aciertos y errores, tiempo de respuesta, motivación y vidas restantes.", "Se muestra una imagen y espacios en blanco; cada 5 segundos aparecen 5 letras, el jugador selecciona la correcta; al completar la palabra se avanza de nivel."),
    (4, "Animalia", "Juego tipo puzzle en el que 4 animales deben ser ubicados en su respectivo hábitat arrastrándolos y soltándolos en pantalla.", "Primaria", "Biología", "Fortalecer saberes básicos de biología en ecosistemas y especies.", "Atención, memoria, toma de decisiones; reforzar conocimiento de animales y clasificación según hábitat.", "Hábitats y biodiversidad básica; clasificación de animales.", "Número de aciertos y errores en la ubicación de animales, rapidez y precisión en la clasificación.", "Se muestran 4 animales y 4 hábitats; el jugador arrastra cada animal a su hábitat correcto; si se falla se pierde una vida de 3 posibles."),
    (5, "Mate-reto", "Se presentan 5 laberintos que el jugador debe recorrer; en el trayecto se encuentran estrellas que presentan preguntas de matemáticas o secuencias para resolver y avanzar.", "Primaria", "Matemática", "Fortalecer habilidades en resolución de conceptos matemáticos básicos mediante ejercicios y problemas.", "Razonamiento lógico, aplicación básica en matemáticas, atención, memoria de trabajo y toma de decisiones.", "Suma, resta, secuencias de imágenes; pensamiento lógico-matemático.", "Número de aciertos, reintentos en caso de errores, método estratégico, actitud y motivación frente al reto.", "El jugador recorre laberintos con estrellas que presentan preguntas; si responde mal debe reiniciar el laberinto en curso."),
]


def _conectar(database=True):
    config = dict(DB_CONFIG)
    if not database:
        config.pop("database", None)
    conn = mysql.connector.connect(**config)
    conn.autocommit = False
    return conn


def get_db():
    """Conexión MySQL por request (una conexión por petición, sin compartir hilos)."""
    if "db" not in g:
        try:
            g.db = _conectar()
        except mysql.connector.Error:
            # La BD aún no existe: la creamos (mismo comportamiento que el esquema
            # SQLite que se autocreaba).
            admin = _conectar(database=False)
            cur = admin.cursor()
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci"
            )
            admin.commit()
            cur.close()
            admin.close()
            g.db = _conectar()
            _crear_esquema_y_seed(g.db)
    return g.db


def cerrar_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        try:
            db.close()
        except Exception:
            pass


def _crear_esquema_y_seed(db):
    """Crea tablas si no existen y siembra grados + juegos (idempotente)."""
    cur = db.cursor()
    try:
        for stmt in SCHEMA:
            cur.execute(stmt)
        db.commit()

        cur.execute("SELECT COUNT(*) FROM grados")
        if cur.fetchone()[0] == 0:
            cur.executemany(
                "INSERT INTO grados (ID_grado, grado_academico, Descripcion) VALUES (%s, %s, %s)",
                GRADOS_SEMILLA,
            )
            db.commit()
            print("✅ Tabla grados sembrada con 5 grados")

        cur.execute("SELECT COUNT(*) FROM juegos")
        if cur.fetchone()[0] == 0:
            cur.executemany(
                """INSERT INTO juegos (ID_juego, Nombre, Descripcion, Nivel_Educativo, Area_Conocimiento,
                    Objetivos, Competencias, Contenidos, Evaluacion, Procedimiento)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                JUEGOS_SEMILLA,
            )
            db.commit()
            print("✅ Tabla juegos sembrada con 5 juegos")
    finally:
        cur.close()


def inicializar_bd():
    """Garantiza que la BD y el esquema existan (usado por Servidor.py)."""
    db = _conectar()
    _crear_esquema_y_seed(db)
    db.close()


def validar_tabla(tabla):
    return tabla in TABLAS_PERMITIDAS


def filtrar_columnas(tabla, datos):
    """Devuelve solo las columnas permitidas del esquema (evita inyección SQL)."""
    permitidas = COLUMNAS_PERMITIDAS.get(tabla, set())
    return {k: v for k, v in datos.items() if k in permitidas}


# ---------------------- Aplicación Flask ----------------------
def create_app():
    app = Flask(__name__)
    app.config["JSON_AS_ASCII"] = False

    app.teardown_appcontext(cerrar_db)

    # CORS: solo navegador desde localhost (la app Python no usa CORS, usa requests).
    @app.after_request
    def aplicar_cors(response):
        origin = request.headers.get("Origin")
        if origin and (origin == "null" or origin.startswith("http://localhost") or origin.startswith("http://127.0.0.1")):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, x-access-token"
        return response

    @app.before_request
    def verificar_token():
        if request.method == "OPTIONS":
            return ""
        if API_TOKEN and request.headers.get("x-access-token") != API_TOKEN:
            return jsonify({"error": "Token no autorizado"}), 401

    # --- Rutas ---
    @app.get("/")
    def raiz():
        return jsonify({"mensaje": "¡API MySQL funcionando!"})

    @app.get("/api/<tabla>")
    def obtener_todos(tabla):
        if not validar_tabla(tabla):
            return jsonify({"error": "Tabla no permitida"}), 400
        cur = get_db().cursor(dictionary=True)
        try:
            cur.execute(f"SELECT * FROM `{tabla}`")
            return jsonify(cur.fetchall())
        finally:
            cur.close()

    @app.get("/api/<tabla>/<int:id_registro>")
    def obtener_uno(tabla, id_registro):
        if not validar_tabla(tabla):
            return jsonify({"error": "Tabla no permitida"}), 400
        pk = PRIMARY_KEYS.get(tabla, "id")
        cur = get_db().cursor(dictionary=True)
        try:
            cur.execute(f"SELECT * FROM `{tabla}` WHERE `{pk}` = %s", (id_registro,))
            fila = cur.fetchone()
        finally:
            cur.close()
        if fila is None:
            return jsonify({"mensaje": "Registro no encontrado"}), 404
        return jsonify(fila)

    @app.post("/api/<tabla>")
    def crear(tabla):
        if not validar_tabla(tabla):
            return jsonify({"error": "Tabla no permitida"}), 400
        datos = request.get_json(silent=True) or {}
        db = get_db()

        # Caso especial para "sesiones": reutiliza la sesión existente del usuario.
        if tabla == "sesiones":
            id_usuario = datos.get("ID_usuario")
            if not id_usuario:
                return jsonify({"error": "Falta ID_usuario"}), 400
            cur = db.cursor(dictionary=True)
            try:
                cur.execute("SELECT * FROM sesiones WHERE ID_usuario = %s", (id_usuario,))
                existente = cur.fetchone()
            finally:
                cur.close()
            if existente is not None:
                return jsonify({"mensaje": "Sesión ya existente", "id": existente["ID_sesion"]})

        datos = filtrar_columnas(tabla, datos)
        if not datos:
            return jsonify({"error": "No hay columnas válidas para insertar"}), 400

        # FechaNacimiento NOT NULL en MySQL: 0/vacío -> fecha por defecto.
        if tabla == "usuarios" and "FechaNacimiento" in datos:
            if datos["FechaNacimiento"] in (0, "", None, "0"):
                datos["FechaNacimiento"] = "2000-01-01"

        campos = ", ".join(f"`{k}`" for k in datos.keys())
        placeholders = ", ".join("%s" for _ in datos)
        cur = db.cursor()
        try:
            cur.execute(
                f"INSERT INTO `{tabla}` ({campos}) VALUES ({placeholders})", list(datos.values())
            )
            db.commit()
            return jsonify({"mensaje": "Registro creado exitosamente", "id": cur.lastrowid})
        except mysql.connector.Error as e:
            db.rollback()
            raise e
        finally:
            cur.close()

    @app.put("/api/<tabla>/<int:id_registro>")
    def actualizar(tabla, id_registro):
        if not validar_tabla(tabla):
            return jsonify({"error": "Tabla no permitida"}), 400
        datos = request.get_json(silent=True) or {}
        datos = filtrar_columnas(tabla, datos)
        if not datos:
            return jsonify({"error": "No hay columnas válidas para actualizar"}), 400

        pk = PRIMARY_KEYS.get(tabla, "id")
        asignaciones = ", ".join(f"`{c}` = %s" for c in datos.keys())
        cur = get_db().cursor()
        try:
            cur.execute(
                f"UPDATE `{tabla}` SET {asignaciones} WHERE `{pk}` = %s",
                list(datos.values()) + [id_registro],
            )
            get_db().commit()
        except mysql.connector.Error as e:
            get_db().rollback()
            raise e
        finally:
            cur.close()
        if cur.rowcount == 0:
            return jsonify({"mensaje": "Registro no encontrado"}), 404
        return jsonify({"mensaje": "Registro actualizado exitosamente"})

    @app.delete("/api/<tabla>/<int:id_registro>")
    def eliminar(tabla, id_registro):
        if not validar_tabla(tabla):
            return jsonify({"error": "Tabla no permitida"}), 400
        pk = PRIMARY_KEYS.get(tabla, "id")
        cur = get_db().cursor()
        try:
            cur.execute(f"DELETE FROM `{tabla}` WHERE `{pk}` = %s", (id_registro,))
            get_db().commit()
        except mysql.connector.Error as e:
            get_db().rollback()
            raise e
        finally:
            cur.close()
        if cur.rowcount == 0:
            return jsonify({"mensaje": "Registro no encontrado"}), 404
        return jsonify({"mensaje": "Registro eliminado exitosamente"})

    # Errores
    @app.errorhandler(404)
    def no_encontrada(e):
        return jsonify({"error": "Ruta no encontrada"}), 404

    @app.errorhandler(500)
    def error_servidor(e):
        print("❌ Error del servidor:", e)
        return jsonify({"error": "Algo salió mal en el servidor"}), 500

    @app.errorhandler(Exception)
    def error_general(e):
        print("❌ Error inesperado:", e)
        return jsonify({"error": str(e)}), 500

    return app


def iniciar_api():
    """Crea la app y garantiza que la BD/esquema existan (usado por Servidor.py)."""
    inicializar_bd()
    return create_app()


if __name__ == "__main__":
    print(f"🚀 API MySQL en http://{HOST}:{PORT}")
    iniciar_api().run(host=HOST, port=PORT, threaded=True)
