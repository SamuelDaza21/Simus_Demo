# SIMUS.MJN - DEMO

Versión de demostración del software educativo SIMUS.MJN. Incluye el
recorrido completo de la aplicación **sin base de datos, sin licencia, sin
login y sin almacenamiento**: tutorial, menú principal, pantalla de inicio,
configuración y los 5 juegos.

## Requisitos

- Windows 10/11
- Python 3.10, 3.11 o 3.12 (no uses 3.13 ni 3.14; mediapipe no tiene ruedas)
  - Descárgalo desde https://www.python.org/downloads/ y marca
    **"Add python.exe to PATH"** al instalarlo.
- Webcam (el control se hace con movimientos de cabeza y parpadeos)

## Cómo descargar y ejecutar

1. Descarga el código: botón verde **Code → Download ZIP** (o `git clone`).
2. Descomprime la carpeta.
3. **Instalación (solo la primera vez):** doble clic en `Instalar_Demo.bat`.
   Crea el entorno virtual e instala las dependencias mínimas automáticamente.
   (Busca Python 3.10/3.11/3.12 en tu equipo; si no lo encuentra te avisa.)
4. **Iniciar:** doble clic en `Iniciar_Demo.bat`.

También se puede ejecutar a mano:

```bash
.venv\Scripts\python src\Demo.py
```

## Controles

- Mueve la cabeza para mover el cursor.
- Parpadea para hacer clic.
- `ESC` para salir de las pantallas.
- `C` para recalibrar la cámara.

## Qué hace el demo

- Salta la licencia, el login y el servidor MySQL (los datos de juegos y
  configuración viven solo en memoria durante la sesión).
- Muestra el tutorial de la cámara al iniciar.
- Menús navegables con cursor facial: Inicio, Juegos, Instrucciones,
  Configuración y Salir.
- Al finalizar no se guarda ningún archivo de calibración, usuarios ni
  resultados.

## Diferencias con la versión completa

| Aspecto          | Versión completa       | Demo                     |
|------------------|------------------------|--------------------------|
| Base de datos    | MySQL (servidor Flask) | En memoria (sin red)     |
| Login/sesiones   | Usuarios y sesiones    | Sesión demo automática   |
| Licencia         | Clave por máquina      | Sin licencia             |
| Almacenamiento   | Archivos y BD          | Nada (no persiste)       |
| Panel de info    | Streamlit/ReportLab    | No disponible            |
