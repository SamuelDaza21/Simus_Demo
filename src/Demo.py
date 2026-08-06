# Demo.py - Lanzador DEMO de SIMUS.MJN
# Recorrido completo SIN licencia, SIN login, SIN servidor MySQL y SIN almacenamiento:
#   tutorial (cámara) -> menú principal -> inicio / juegos / configuración / instrucciones
import os
import sys

# El modo demo se activa ANTES de importar cualquier módulo del proyecto.
os.environ["DEMO_MODE"] = "true"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SRC = os.path.dirname(os.path.abspath(__file__))
if SRC not in sys.path:
    sys.path.insert(0, SRC)

print("[DEMO] ==========================================")
print("[DEMO]  SIMUS.MJN - MODO DEMOSTRACIÓN (sin BD)")
print("[DEMO]  Tutorial + Menú + Inicio + Juegos")
print("[DEMO] ==========================================")

import pygame

import core.config as core_config
from ui.Menu_Principal import MenuPrincipal
from ui.Inicio import Inicio
from ui.instrucciones import Instrucciones
from ui.Configuracion import Configuracion
from ui.juegos import MenuJuegos
from logic.cursor import ControladorCursor
from core.Musica import gestor_musica


def main():
    print("[DEMO] Inicializando pygame...")
    pygame.init()
    try:
        pygame.mixer.init()
    except pygame.error:
        print("[DEMO] Sin dispositivo de audio; modo silencioso.")
    pygame.font.init()

    # En la app real esto lo hace la pantalla de login; en el demo se hace aquí.
    if core_config.traductor is None:
        core_config.setup_traductor("es")

    pantalla = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.RESIZABLE)
    ANCHO, ALTO = pantalla.get_size()
    pygame.display.set_caption("SIMUS.MJN - Demo")

    # Sesión de demostración (sin usuarios ni registro en disco)
    sesion_id = 1
    print("[DEMO] Sesión demo: %s" % sesion_id)

    print("[DEMO] Creando controlador de cámara...")
    controlador_cursor = ControladorCursor(ancho=ANCHO, alto=ALTO, sesion_id=sesion_id)
    camara = controlador_cursor.obtener_camara()

    # Tutorial automático (se muestra siempre en el demo; no se guarda estado)
    print("[DEMO] Iniciando tutorial...")
    tutorial = Instrucciones(camara, gestor_musica, sesion_id)
    estado = tutorial.ejecutar()  # devuelve "menu_principal"
    print("[DEMO] Tutorial finalizado -> %s" % estado)

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
        elif estado == "instrucciones":
            instr = Instrucciones(camara, gestor_musica, sesion_id)
            estado = instr.ejecutar()
        elif estado == "juegos":
            juego = MenuJuegos(camara, gestor_musica, sesion_id)
            estado = juego.ejecutar()
        elif estado == "informacion":
            print("[DEMO] Panel de información no disponible en modo demo.")
            estado = "menu_principal"
        elif estado == "salir":
            print("[DEMO] Saliendo del demo...")
            camara.liberar_recursos()
            pygame.quit()
            sys.exit()


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print("[DEMO] Error: %s" % e)
        print("[DEMO] El demo requiere una cámara web. Conéctala y vuelve a intentar.")
        input("Presiona Enter para salir...")
    except Exception as e:
        import traceback
        print("[DEMO] Error inesperado:")
        traceback.print_exc()
        input("Presiona Enter para salir...")
