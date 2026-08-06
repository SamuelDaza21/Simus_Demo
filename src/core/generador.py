from __future__ import annotations

import argparse
import os
import random
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import mysql.connector

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parents[1]


def config_mysql() -> dict:
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": int(os.environ.get("DB_PORT", 3306)),
        "user": os.environ.get("DB_USER", "root"),
        "password": os.environ.get("DB_PASSWORD", ""),
        "database": os.environ.get("DB_NAME", "simus_mjn"),
    }


def conectar_bd() -> mysql.connector.MySQLConnection:
    """Abre la conexión MySQL del proyecto (autocommit desactivado para batch)."""
    conexion = mysql.connector.connect(**config_mysql())
    conexion.autocommit = False
    return conexion


def obtener_sesiones_validas(cursor: mysql.connector.cursor.MySQLCursor) -> list[int]:
    """Retorna las sesiones disponibles para asociar los datos generados."""
    cursor.execute("SELECT ID_sesion FROM sesiones ORDER BY ID_sesion")
    filas = cursor.fetchall()
    return [int(fila[0]) for fila in filas]


def obtener_juegos_validos(cursor: mysql.connector.cursor.MySQLCursor) -> list[str]:
    """Lee los nombres de juego definidos en la base de datos."""
    cursor.execute("SELECT Nombre FROM juegos ORDER BY ID_juego")
    filas = cursor.fetchall()
    return [str(fila[0]) for fila in filas if fila[0]]


def resolver_sesion_objetivo(sesiones: list[int], sesion_preferida: int | None) -> int:
    """Selecciona una sesión existente para no romper claves foráneas ni filtros de UI."""
    if not sesiones:
        raise ValueError("No hay sesiones registradas en la base de datos. Cree primero un usuario/sesión.")

    if sesion_preferida is not None:
        if sesion_preferida not in sesiones:
            raise ValueError(f"La sesión {sesion_preferida} no existe. Sesiones disponibles: {sesiones}")
        return sesion_preferida

    return sesiones[-1]


def construir_registros_juego(
    sesion_id: int,
    nombre_juego: str,
    repeticiones: int,
    variacion: int,
) -> list[tuple[int, str, int, int, int, int, int, int]]:
    """Genera una secuencia con tendencia positiva para que las gráficas sean legibles."""
    registros = []
    puntaje_anterior = random.randint(28, 52)
    aciertos_previos = max(2, min(10, round(puntaje_anterior / 12)))
    errores_previos = max(0, 10 - aciertos_previos + random.randint(0, 2))

    for indice in range(repeticiones):
        mejora = random.randint(3, variacion) + indice
        puntaje_nuevo = max(15, min(100, puntaje_anterior + mejora + random.randint(-4, 5)))
        aciertos_nuevos = max(1, min(10, round(puntaje_nuevo / 10) + random.randint(-1, 1)))
        errores_nuevos = max(0, min(6, 10 - aciertos_nuevos + random.randint(0, 1)))

        registros.append(
            (
                sesion_id,
                nombre_juego,
                puntaje_nuevo,
                aciertos_nuevos,
                errores_nuevos,
                puntaje_anterior,
                aciertos_previos,
                errores_previos,
            )
        )

        puntaje_anterior = puntaje_nuevo
        aciertos_previos = aciertos_nuevos
        errores_previos = errores_nuevos

    return registros


def generar_registros_muestra(
    juegos: list[str],
    sesion_id: int,
    total: int,
) -> list[tuple[int, str, int, int, int, int, int, int]]:
    """Distribuye registros entre juegos para poblar las gráficas con datos variados."""
    if not juegos:
        raise ValueError("No hay juegos registrados en la base de datos.")

    cantidad_por_juego = max(4, total // len(juegos))
    registros: list[tuple[int, str, int, int, int, int, int, int]] = []

    for nombre_juego in juegos:
        registros.extend(
            construir_registros_juego(
                sesion_id=sesion_id,
                nombre_juego=nombre_juego,
                repeticiones=cantidad_por_juego,
                variacion=random.randint(6, 12),
            )
        )

    while len(registros) < total:
        juego_extra = random.choice(juegos)
        registros.extend(
            construir_registros_juego(
                sesion_id=sesion_id,
                nombre_juego=juego_extra,
                repeticiones=1,
                variacion=random.randint(4, 10),
            )
        )

    random.shuffle(registros)
    return registros[:total]


def limpiar_historial_sesion(cursor: mysql.connector.cursor.MySQLCursor, sesion_id: int) -> int:
    """Elimina registros previos de una sesión si el usuario quiere regenerarlos."""
    cursor.execute(
        "DELETE FROM historial_resultados WHERE ID_sesion = %s",
        (sesion_id,),
    )
    return int(cursor.rowcount or 0)


def insertar_registros(
    cursor: mysql.connector.cursor.MySQLCursor,
    registros: list[tuple[int, str, int, int, int, int, int, int]],
) -> int:
    """Inserta registros de historial compatibles con la UI de progreso."""
    cursor.executemany(
        """
        INSERT INTO historial_resultados (
            ID_sesion,
            Nombre_juego,
            puntaje_nuevo,
            Nuevo_Acierto,
            Nuevo_error,
            puntaje_antiguo,
            Aciertos_antiguo,
            Errores_antiguo
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        registros,
    )
    return len(registros)


def mostrar_resumen(cursor: mysql.connector.cursor.MySQLCursor, sesion_id: int) -> None:
    """Imprime un resumen útil para validar que las gráficas tendrán datos."""
    cursor.execute(
        "SELECT COUNT(*) FROM historial_resultados WHERE ID_sesion = %s",
        (sesion_id,),
    )
    total = cursor.fetchone()[0]

    print(f"📊 Total de registros para la sesión {sesion_id}: {total}")

    cursor.execute(
        """
        SELECT Nombre_juego, COUNT(*), MIN(puntaje_nuevo), MAX(puntaje_nuevo)
        FROM historial_resultados
        WHERE ID_sesion = %s
        GROUP BY Nombre_juego
        ORDER BY Nombre_juego
        """,
        (sesion_id,),
    )
    resumen = cursor.fetchall()

    print("\n📈 Resumen por juego:")
    for nombre_juego, cantidad, minimo, maximo in resumen:
        print(f"  - {nombre_juego}: {cantidad} registros | rango {minimo}% - {maximo}%")

    cursor.execute(
        """
        SELECT id, ID_sesion, Nombre_juego, puntaje_nuevo, Nuevo_Acierto, Nuevo_error
        FROM historial_resultados
        WHERE ID_sesion = %s
        ORDER BY id DESC
        LIMIT 10
        """,
        (sesion_id,),
    )
    muestra = cursor.fetchall()

    print("\n📋 Últimos 10 registros insertados:")
    for fila in muestra:
        print(f"  {fila}")


def crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Genera datos aleatorios en historial_resultados para mostrar gráficas en SIMUS.MJN."
    )
    parser.add_argument("--cantidad", type=int, default=60, help="Cantidad total de registros a insertar.")
    parser.add_argument("--sesion", type=int, default=None, help="ID_sesion destino. Si no se indica, usa la última.")
    parser.add_argument("--seed", type=int, default=None, help="Semilla para resultados reproducibles.")
    parser.add_argument(
        "--limpiar",
        action="store_true",
        help="Borra antes el historial de la sesión seleccionada.",
    )
    return parser


def main() -> int:
    args = crear_parser().parse_args()
    if args.cantidad <= 0:
        print("❌ La cantidad debe ser mayor que cero.")
        return 1

    if args.seed is not None:
        random.seed(args.seed)

    conexion = None
    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()
        sesiones = obtener_sesiones_validas(cursor)
        juegos = obtener_juegos_validos(cursor)
        sesion_id = resolver_sesion_objetivo(sesiones, args.sesion)

        print(f"🗂️ Base de datos: {config_mysql()['host']}:{config_mysql()['port']}/{config_mysql()['database']}")
        print(f"🎯 Sesión objetivo: {sesion_id}")
        print(f"🎮 Juegos detectados: {', '.join(juegos)}")

        if args.limpiar:
            eliminados = limpiar_historial_sesion(cursor, sesion_id)
            print(f"🧹 Registros eliminados de la sesión {sesion_id}: {eliminados}")

        registros = generar_registros_muestra(juegos=juegos, sesion_id=sesion_id, total=args.cantidad)
        insertados = insertar_registros(cursor, registros)
        conexion.commit()

        print(f"✅ Registros insertados correctamente: {insertados}")
        mostrar_resumen(cursor, sesion_id)
        return 0

    except (mysql.connector.Error, ValueError) as error:
        if conexion is not None:
            try:
                conexion.rollback()
            except Exception:
                pass
        print(f"❌ Error al generar datos de muestra: {error}")
        return 1
    finally:
        if conexion is not None:
            conexion.close()


if __name__ == "__main__":
    raise SystemExit(main())
