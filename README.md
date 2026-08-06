<h1 align="center">🎮👁️ SIMUS.MJN — DEMO</h1>

<p align="center"><b>Software educativo de comunicación aumentativa con control por movimientos de cabeza y parpadeos.</b></p>

<p align="center">
  <img src="https://img.shields.io/badge/-Python%203.10--3.12-1b212c?style=flat&logo=python&logoColor=d4a84b&labelColor=1b212c&color=1b212c" alt="Python"/>
  <img src="https://img.shields.io/badge/-Windows%2010%2F11-1b212c?style=flat&logo=windows&logoColor=d4a84b&labelColor=1b212c&color=1b212c" alt="Windows"/>
  <img src="https://img.shields.io/badge/-Webcam%20requerida-1b212c?style=flat&logo=video&logoColor=d4a84b&labelColor=1b212c&color=1b212c" alt="Webcam"/>
  <img src="https://img.shields.io/badge/-Sin%20login%20ni%20licencia-1b212c?style=flat&labelColor=1b212c&color=1b212c" alt="Sin login"/>
</p>

<p align="center">Versión de demostración **sin base de datos, sin licencia y sin login**: tutorial, menú principal, pantalla de inicio, configuración y **5 juegos**.</p>

---

## 🎬 Mira el trailer

Haz clic en la imagen para ver el trailer **completo, de inicio a fin y con sonido** (se abre en YouTube):

<p align="center">
  <a href="https://youtu.be/qKUh0oAfOrM"><img src="https://img.youtube.com/vi/qKUh0oAfOrM/maxresdefault.jpg" width="70%" alt="▶ Ver trailer completo en YouTube"/></a>
</p>

---

## 🚀 Guía paso a paso para instalarlo (5 minutos)

### ✅ Paso 1 — Descarga el proyecto

Haz clic en el botón verde **Code → Download ZIP** o usa este enlace directo:

<p>
  <a href="https://github.com/SamuelDaza21/Simus_Demo/archive/refs/heads/main.zip"><img src="https://img.shields.io/badge/-Descargar%20proyecto%20(ZIP)-d4a84b?style=flat-square&logo=github&logoColor=0d1117&labelColor=d4a84b&color=d4a84b" alt="Descargar proyecto"/></a>
</p>

Descomprime el ZIP en una carpeta, por ejemplo `Escritorio\Simus_Demo`.

---

### ✅ Paso 2 — Instala Python (solo si no lo tienes)

1. Haz clic en este enlace para **descargar el instalador de Python 3.10** (el más recomendado para este proyecto):

   <p>
     <a href="https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe"><img src="https://img.shields.io/badge/-Descargar%20Python%203.10-1b212c?style=flat-square&logo=python&logoColor=d4a84b&labelColor=1b212c&color=1b212c" alt="Descargar Python 3.10"/></a>
   </p>

2. Abre el archivo `python-3.10.11-amd64.exe` que descargaste.
3. ⚠️ **IMPORTANTE:** marca la casilla **"Add python.exe to PATH"** (en la parte inferior de la primera ventana):

   > ✅ `[x] Add python.exe to PATH`

4. Haz clic en **Install Now** y espera a que termine.

> ¿Tienes otra versión? También sirven **Python 3.11 y 3.12**. Descarga la que quieras desde [python.org/downloads](https://www.python.org/downloads/). No uses **3.13 ni 3.14**.

---

### ✅ Paso 3 — Instala el demo (solo la primera vez)

Entra a la carpeta `Simus_Demo` que descomprimiste y haz **doble clic** en:

<p>
  <a href="https://raw.githubusercontent.com/SamuelDaza21/Simus_Demo/main/Instalar_Demo.bat"><img src="https://img.shields.io/badge/-Instalar_Demo.bat-1b212c?style=flat-square&logo=windows&logoColor=d4a84b&labelColor=1b212c&color=1b212c" alt="Instalar_Demo.bat"/></a>
</p>

Este archivo **crea el entorno virtual e instala todas las dependencias automáticamente** (busca Python 3.10/3.11/3.12 en tu equipo). Verás algo así:

```
[DEMO] Buscando Python compatible (3.10 / 3.11 / 3.12)...
[DEMO] Creando entorno virtual con py -3.10...
[DEMO] Instalacion completada. Ejecuta Iniciar_Demo.bat para usar el demo.
```

---

### ✅ Paso 4 — ¡A jugar!

Haz **doble clic** en:

<p>
  <a href="https://raw.githubusercontent.com/SamuelDaza21/Simus_Demo/main/Iniciar_Demo.bat"><img src="https://img.shields.io/badge/-Iniciar_Demo.bat-1b212c?style=flat-square&logo=windows&logoColor=d4a84b&labelColor=1b212c&color=1b212c" alt="Iniciar_Demo.bat"/></a>
</p>

Se abrirá el demo en pantalla completa. Colócate frente a la cámara y sigue el **tutorial**.

---

## 🕹️ Controles

| Acción | Cómo se hace |
|--------|--------------|
| 🎯 Mover el cursor | Mueve la cabeza |
| 👁️ Hacer clic | Parpadea |
| 🚪 Salir de una pantalla | Tecla `ESC` |
| 📷 Recalibrar la cámara | Tecla `C` |

---

## 🎮 Los 5 juegos del demo

| Juego | Qué es |
|-------|--------|
| 🃏 Pares mágicos | Juego de memoria con tarjetas |
| 🦁 Animalia | Clasifica animales por hábitat |
| 🧩 Mate-reto | Laberintos con preguntas de matemáticas |
| 🔍 Encuentra y aprende | Busca objetos y aprende su nombre |
| 🔤 Caza letras | Encuentra la letra correcta |

---

## 🧩 Diferencias con la versión completa

| Aspecto        | Versión completa       | Demo                     |
|----------------|------------------------|--------------------------|
| Base de datos  | MySQL (servidor Flask) | En memoria (sin red)     |
| Login/sesiones | Usuarios y sesiones    | Sesión demo automática   |
| Licencia       | Clave por máquina      | Sin licencia             |
| Almacenamiento | Archivos y BD          | Nada (no persiste)       |
| Panel de info  | Streamlit/ReportLab    | No disponible            |

---

<p align="center">Hecho con 💛 para el proyecto educativo **SIMUS.MJN**</p>
