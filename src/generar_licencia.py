# generar_licencia.py
# Genera la clave de activación para SIMUS.MJN.
#
# Uso:
#   python generar_licencia.py               -> detecta el ID de ESTA máquina y activa el programa
#   python generar_licencia.py <ID_MAQUINA>  -> genera la clave para OTRO equipo (la envías al admin)
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from cryptography.fernet import Fernet

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# CLAVE SECRETA (DEBE SER LA MISMA EN EL SOFTWARE)
# Cámbiala por una frase larga y guárdala segura (no la compartas)
SECRET_KEY = "ZLSQ1pqke3G8cq6XAhhclnXVjtJeMw9Z92fLBCgu3vE="
LIC_FILE = Path(__file__).resolve().parent / "licencia.json"


def generar_licencia(id_maquina):
    cipher = Fernet(SECRET_KEY)
    licencia = cipher.encrypt(id_maquina.encode()).decode()
    return licencia


def obtener_id_maquina():
    """Detecta el ID de esta máquina (misma lógica que Principal.py)."""
    try:
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

    try:
        resultado = subprocess.run(["vol", "C:"], capture_output=True, text=True, shell=True)
        match = re.search(r"([A-Z0-9]{4}-[A-Z0-9]{4})", resultado.stdout)
        if match:
            return match.group(1)
    except Exception:
        pass

    import socket
    import uuid as uuid_mod
    mac = format(uuid_mod.getnode(), "x").upper()
    return f"{socket.gethostname()}-{os.getlogin()}-{mac}"


if __name__ == "__main__":
    if len(sys.argv) == 2:
        id_maquina = sys.argv[1]
    else:
        id_maquina = obtener_id_maquina()

    lic = generar_licencia(id_maquina)
    print("\n=== CLAVE DE ACTIVACIÓN ===")
    print(lic)
    print("===========================\n")

    # Si es esta máquina, guardar licencia.json directamente (auto-activación)
    if len(sys.argv) == 1:
        try:
            LIC_FILE.write_text(json.dumps({"licencia": lic}), encoding="utf-8")
            print(f"✅ Licencia guardada en {LIC_FILE}")
            print("   Ya puedes ejecutar: python Principal.py")
        except Exception as e:
            print(f"❌ No se pudo guardar la licencia: {e}")
            print("   Copia la clave de arriba y pégala al iniciar la app.")
    else:
        print(f"👉 Envía esta clave al equipo con ID: {id_maquina}")
