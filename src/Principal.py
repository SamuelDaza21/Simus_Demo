# main.py
import os
import pygame, sys, os, time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

print("[IMPORT] Iniciando imports...")

from ui.sesion import login
print("[IMPORT] sesion importado")

from ui.Menu_Principal import MenuPrincipal
from ui.Inicio import Inicio
from ui.instrucciones import Instrucciones
from ui.Configuracion import Configuracion
from ui.juegos import MenuJuegos
from ui.informacion_streamlit import StreamlitInfoLauncher
from logic.cursor import ControladorCursor
print("[IMPORT] ControladorCursor importado")

from core.Musica import gestor_musica
print("[IMPORT] gestor_musica importado")

from api.Servidor import Servidor
print("[IMPORT] Servidor importado")

print("[IMPORT] Todos los módulos importados")
import os
import json
import subprocess
import platform
from cryptography.fernet import Fernet

SECRET_KEY = "ZLSQ1pqke3G8cq6XAhhclnXVjtJeMw9Z92fLBCgu3vE="
LIC_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "licencia.json")


def obtener_id_maquina():
    """
    Devuelve un ID único y estable de la máquina (funciona en Windows).
    Prioriza el UUID de la placa base (más fiable que la MAC).
    """
    sistema = platform.system()

    if sistema == "Windows":
        try:
            # 1. Intentar obtener UUID del hardware (válido incluso sin admin)
            resultado = subprocess.run(
                ["wmic", "csproduct", "get", "uuid"],
                capture_output=True, text=True, shell=True
            )
            lineas = resultado.stdout.strip().splitlines()
            if len(lineas) >= 2:
                uuid_val = lineas[1].strip()
                if uuid_val and uuid_val != "UUID":
                    return uuid_val
        except Exception:
            pass

        # 2. Fallback: volumen de la unidad C: (número de serie)
        try:
            resultado = subprocess.run(
                ["vol", "C:"],
                capture_output=True, text=True, shell=True
            )
            # La salida tiene algo como "Número de serie del volumen: 1234-5678"
            import re
            match = re.search(r"([A-Z0-9]{4}-[A-Z0-9]{4})", resultado.stdout)
            if match:
                return match.group(1)
        except Exception:
            pass

    # 3. Último recurso: combinar nombre de host + usuario + MAC
    import socket
    import uuid
    try:
        mac = uuid.getnode()
        mac_str = format(mac, 'x').upper()
        nombre_host = socket.gethostname()
        usuario = os.getlogin()
        return f"{nombre_host}-{usuario}-{mac_str}"
    except:
        return "ID_GENERICO_FALLBACK"


def verificar_licencia():
    """Devuelve True si la licencia es válida, False en caso contrario."""
    id_maquina = obtener_id_maquina()

    # Si el archivo no existe, pedir activación
    if not os.path.exists(LIC_FILE):
        print("\n" + "=" * 60)
        print("🔐 ACTIVACIÓN DEL SOFTWARE - SIMUS.MJN")
        print("=" * 60)
        print(f"ID de esta máquina:\n{id_maquina}\n")
        print("👉 Envía este ID al administrador para obtener tu clave de activación.")
        clave = input("✏️  Clave de activación: ").strip()

        if not clave:
            print("❌ No se ingresó clave. El programa no puede continuar.")
            return False

        # Guardar la licencia (aunque aún no sabemos si es válida)
        with open(LIC_FILE, "w") as f:
            json.dump({"licencia": clave}, f)

        # Verificar la clave
        cipher = Fernet(SECRET_KEY)
        try:
            id_decodificado = cipher.decrypt(clave.encode()).decode()
            if id_decodificado == id_maquina:
                print("✅ Licencia activada correctamente. ¡Bienvenido!")
                return True
            else:
                print("❌ Error: La clave no corresponde a esta máquina.")
                os.remove(LIC_FILE)  # Eliminar archivo inválido
                return False
        except Exception as e:
            print(f"❌ Clave inválida o corrupta: {e}")
            os.remove(LIC_FILE)
            return False

    # Si el archivo existe, validar su contenido
    try:
        with open(LIC_FILE, "r") as f:
            data = json.load(f)
            clave = data.get("licencia", "")
        if not clave:
            print("❌ Archivo de licencia corrupto (clave vacía).")
            os.remove(LIC_FILE)
            return False

        cipher = Fernet(SECRET_KEY)
        id_decodificado = cipher.decrypt(clave.encode()).decode()
        if id_decodificado == id_maquina:
            print("✅ Licencia válida. Continuando...")
            return True
        else:
            print("❌ Licencia inválida: esta clave pertenece a otro equipo.")
            print("   Eliminando archivo de licencia...")
            os.remove(LIC_FILE)
            return False
    except json.JSONDecodeError:
        print("❌ Archivo de licencia corrupto (formato JSON inválido). Eliminando...")
        os.remove(LIC_FILE)
        return False
    except Exception as e:
        print(f"❌ Error al verificar licencia: {e}")
        # No eliminamos automáticamente para no borrar accidentalmente, pero retornamos False
        return False
def main():
    #TOKEN INICIAL
    es_docker = os.environ.get('DOCKER_MODE') == 'true'
    # En Docker (API headless) no hay licencia física; se salta la validación.
    if not es_docker and not verificar_licencia():
        print("No se pudo validar la licencia. El programa terminará.")
        input("Presiona Enter para salir...")  # Pequeña pausa para leer el mensaje
        return
    # 1. ESTO SE QUEDA IGUAL (Preparación)
    print("[DEBUG] Iniciando pygame...")
    pygame.init()
    pygame.mixer.init()
    pygame.font.init()
    print("[DEBUG] Pygame inicializado")

    print("[DEBUG] Creando servidor...")
    servidor = Servidor()
    print("[DEBUG] Iniciando servidor...")
    servidor.iniciar()
    print("[DEBUG] Servidor iniciado correctamente")

    # 2. EL FILTRO INTELIGENTE
    if es_docker:
        print("[INFO] Modo Docker detectado. API activa y escuchando...")
        # Bloqueamos el proceso aquí para que NO siga hacia la interfaz
        try:
            while True:
                time.sleep(3600)  # Dormir una hora y repetir (mantiene el server vivo)
        except KeyboardInterrupt:
            print("[INFO] Deteniendo servidor...")
            servidor.detener()
            return  # Finaliza aquí en Docker

    # 3. TODO LO QUE SIGUE SOLO SE EJECUTA SI NO ES DOCKER (Windows Local)
    print("[INFO] Iniciando interfaz gráfica (Modo Local)...")
    pantalla = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.RESIZABLE)
    ANCHO, ALTO = pantalla.get_size()

    print("[DEBUG] Servidor iniciado, iniciando login...")
    sesion_id = login(pantalla)
    print(f"[DEBUG] Login completado, sesion_id: {sesion_id}")
    print("[DEBUG] Creando ControladorCursor...")
    controlador_cursor = ControladorCursor(ancho=ANCHO, alto=ALTO, sesion_id=sesion_id)
    print("[DEBUG] ControladorCursor creado")
    camara = controlador_cursor.obtener_camara()
    print("[DEBUG] Cámara obtenida")
    info_launcher = StreamlitInfoLauncher()  # Comentado: requiere seaborn, pandas, streamlit
    print("[DEBUG] Verificando calibración...")
    if not controlador_cursor.estado_calibrado():
        print("[DEBUG] Ejecutando calibración...")
        controlador_cursor.calibrar()
        print("[DEBUG] Calibración completada")

    # Tutorial automático solo si no está completado
    print("[DEBUG] Creando Instrucciones...")
    tutorial = Instrucciones(camara, gestor_musica, sesion_id)
    print("[DEBUG] Instrucciones creadas")
    if not tutorial.tutorial_completed:
        print("[DEBUG] Ejecutando tutorial...")
        estado = tutorial.ejecutar()  # devuelve "menu_principal"
        print(f"[DEBUG] Tutorial completado, estado: {estado}")
    else:
        estado = "menu_principal"
        print("[DEBUG] Tutorial ya completado, yendo al menú")

    while True:
        if estado == "menu_principal":
            menu = MenuPrincipal(sesion_id, camara)
            estado = menu.ejecutar()
        elif estado == "configuracion":
            config = Configuracion(camara_existente=camara, gestor_musica=gestor_musica, ID_Sesion=sesion_id)
            estado = config.ejecutar_configuracion()
        elif estado == "inicio":
            inicio = Inicio(camara=camara, gestor_musica=gestor_musica, ID_sesion=sesion_id)
            estado = inicio.ejecutar()
        elif estado == "salir":
            info_launcher.stop()  # Comentado: requiere seaborn, pandas, streamlit
            camara.liberar_recursos()
            # No detener la API aquí: los juegos registran un atexit (guardar_resultado_final)
            # que envía el resultado por HTTP. Si se detiene antes de sys.exit(), ese envío
            # falla con "No se pudo conectar al servidor API". El hilo de la API es daemon
            # y el puerto 3000 se libera solo al terminar el proceso.
            pygame.quit()
            sys.exit()
        elif estado == "instrucciones":
            # Reentrada manual desde el menú
            instr = Instrucciones(camara, gestor_musica, sesion_id)
            estado = instr.ejecutar()
        elif estado == "juegos":
            juego = MenuJuegos(camara, gestor_musica, sesion_id)
            estado = juego.ejecutar()
        elif estado == "informacion":
            try:
               os.environ["SIMUS_SESSION_ID"] = str(sesion_id)
               info_launcher.open_dashboard(session_id=sesion_id)  # Comentado: requiere seaborn, pandas, streamlit
               estado = "menu_principal"
            except Exception as error:
                print(f"No fue posible abrir el dashboard web: {error}")
                estado = "menu_principal"

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Esta joda se jodio antes de iniciar")
        print(e)
        input("Vaya y arregle eso rapido no joda")