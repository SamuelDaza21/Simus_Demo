<h1 align="center">🎮👁️ SIMUS.MJN — DEMO</h1>

<p align="center"><b>Software educativo de comunicación aumentativa con control por movimientos de cabeza y parpadeos.</b></p>

<p align="center">
  <img src="https://img.shields.io/badge/-Python%203.10--3.12-1b212c?style=flat&logo=python&logoColor=d4a84b&labelColor=1b212c" alt="Python"/>
  <img src="https://img.shields.io/badge/-Windows%2010%2F11-1b212c?style=flat&logo=windows&logoColor=d4a84b&labelColor=1b212c" alt="Windows"/>
  <img src="https://img.shields.io/badge/-Webcam%20requerida-1b212c?style=flat&logo=video&logoColor=d4a84b&labelColor=1b212c" alt="Webcam"/>
  <img src="https://img.shields.io/badge/-Sin%20login%20ni%20licencia-1b212c?style=flat&labelColor=1b212c" alt="Sin login"/>
</p>

<p align="center" style="color:#8b949e">Versión de demostración <b>sin base de datos, sin licencia y sin login</b>: tutorial, menú principal, pantalla de inicio, configuración y <b>5 juegos</b>.</p>

<style>
  @keyframes smFadeUp { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: translateY(0); } }
  .sm-card { background: #161b22; border: 1px solid #21262d; border-radius: 14px; padding: 18px 22px; animation: smFadeUp 0.6s ease both; }
  .sm-title { color: #d4a84b; font-size: 12px; letter-spacing: 3px; text-transform: uppercase; font-weight: 600; }
</style>

---

<div class="sm-card">
  <div class="sm-title">🎬 Mira el trailer</div>
  <p style="margin-top: 10px; color:#e6edf3; font-size:14px">Haz clic en la imagen para ver el trailer <b style="color:#d4a84b">completo, de inicio a fin y con sonido</b> (se abre en YouTube):</p>
  <p align="center" style="margin-top: 12px">
    <a href="https://youtu.be/qKUh0oAfOrM"><img src="https://img.youtube.com/vi/qKUh0oAfOrM/maxresdefault.jpg" width="70%" alt="▶ Ver trailer completo en YouTube"/></a>
  </p>
</div>

<br/>

<div class="sm-card" style="animation-delay: 0.1s">
  <div class="sm-title">🚀 Guía paso a paso para instalarlo (5 minutos)</div>

  <h3>✅ Paso 1 — Descarga el proyecto</h3>
  <p style="color:#e6edf3; font-size:14px">Haz clic en el botón verde <b style="color:#d4a84b">Code → Download ZIP</b> o usa este enlace directo:</p>
  <p><a href="https://github.com/SamuelDaza21/Simus_Demo/archive/refs/heads/main.zip"><img src="https://img.shields.io/badge/-Descargar%20proyecto%20(ZIP)-1b212c?style=for-the-badge&logo=github&logoColor=d4a84b&labelColor=1b212c" alt="Descargar proyecto"/></a></p>
  <p style="color:#e6edf3; font-size:14px">Descomprime el ZIP en una carpeta, por ejemplo <code style="background:#1b212c;padding:2px 6px;border-radius:6px;color:#d4a84b">Escritorio\Simus_Demo</code>.</p>

  <h3>✅ Paso 2 — Instala Python (solo si no lo tienes)</h3>
  <ol style="color:#e6edf3; font-size:14px; line-height:1.9">
    <li>Haz clic en este enlace para <b>descargar el instalador de Python 3.10</b> (el más recomendado para este proyecto):</li>
  </ol>
  <p><a href="https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe"><img src="https://img.shields.io/badge/-Descargar%20Python%203.10-1b212c?style=for-the-badge&logo=python&logoColor=d4a84b&labelColor=1b212c" alt="Descargar Python 3.10"/></a></p>
  <ol start="2" style="color:#e6edf3; font-size:14px; line-height:1.9">
    <li>Abre el archivo <code style="background:#1b212c;padding:2px 6px;border-radius:6px;color:#d4a84b">python-3.10.11-amd64.exe</code> que descargaste.</li>
    <li>⚠️ <b>IMPORTANTE:</b> marca la casilla <b style="color:#d4a84b">"Add python.exe to PATH"</b> (en la parte inferior de la primera ventana):</li>
  </ol>
  <blockquote>✅ <code>[x] Add python.exe to PATH</code></blockquote>
  <ol start="4" style="color:#e6edf3; font-size:14px; line-height:1.9">
    <li>Haz clic en <b>Install Now</b> y espera a que termine.</li>
  </ol>
  <blockquote>¿Tienes otra versión? También sirven <b>Python 3.11 y 3.12</b>. Descarga la que quieras desde <a href="https://www.python.org/downloads/">python.org/downloads</a>. No uses <b>3.13 ni 3.14</b>.</blockquote>

  <h3>✅ Paso 3 — Instala el demo (solo la primera vez)</h3>
  <p style="color:#e6edf3; font-size:14px">Entra a la carpeta <code style="background:#1b212c;padding:2px 6px;border-radius:6px;color:#d4a84b">Simus_Demo</code> que descomprimiste y haz <b>doble clic</b> en:</p>
  <p><a href="https://raw.githubusercontent.com/SamuelDaza21/Simus_Demo/main/Instalar_Demo.bat"><img src="https://img.shields.io/badge/-Instalar_Demo.bat-1b212c?style=for-the-badge&logo=windows&logoColor=d4a84b&labelColor=1b212c" alt="Instalar_Demo.bat"/></a></p>
  <p style="color:#e6edf3; font-size:14px">Este archivo <b style="color:#d4a84b">crea el entorno virtual e instala todas las dependencias automáticamente</b> (busca Python 3.10/3.11/3.12 en tu equipo). Verás algo así:</p>
  <pre style="background:#0d1117; border:1px solid #21262d; border-radius:10px; padding:14px; color:#9da7b3; font-size:12px; line-height:1.6"><code>[DEMO] Buscando Python compatible (3.10 / 3.11 / 3.12)...
[DEMO] Creando entorno virtual con py -3.10...
[DEMO] Instalacion completada. Ejecuta Iniciar_Demo.bat para usar el demo.</code></pre>

  <h3>✅ Paso 4 — ¡A jugar!</h3>
  <p style="color:#e6edf3; font-size:14px">Haz <b>doble clic</b> en:</p>
  <p><a href="https://raw.githubusercontent.com/SamuelDaza21/Simus_Demo/main/Iniciar_Demo.bat"><img src="https://img.shields.io/badge/-Iniciar_Demo.bat-1b212c?style=for-the-badge&logo=windows&logoColor=d4a84b&labelColor=1b212c" alt="Iniciar_Demo.bat"/></a></p>
  <p style="color:#e6edf3; font-size:14px">Se abrirá el demo en pantalla completa. Colócate frente a la cámara y sigue el <b style="color:#d4a84b">tutorial</b>.</p>
</div>

<br/>

<div class="sm-card" style="animation-delay: 0.2s">
  <div class="sm-title">🕹️ Controles</div>
  <table style="margin-top: 10px">
    <thead><tr><th>Acción</th><th>Cómo se hace</th></tr></thead>
    <tbody>
      <tr><td>🎯 Mover el cursor</td><td>Mueve la cabeza</td></tr>
      <tr><td>👁️ Hacer clic</td><td>Parpadea</td></tr>
      <tr><td>🚪 Salir de una pantalla</td><td>Tecla <code>ESC</code></td></tr>
      <tr><td>📷 Recalibrar la cámara</td><td>Tecla <code>C</code></td></tr>
    </tbody>
  </table>
</div>

<br/>

<div class="sm-card" style="animation-delay: 0.3s">
  <div class="sm-title">🎮 Los 5 juegos del demo</div>
  <table style="margin-top: 10px">
    <thead><tr><th>Juego</th><th>Qué es</th></tr></thead>
    <tbody>
      <tr><td>🃏 Pares mágicos</td><td>Juego de memoria con tarjetas</td></tr>
      <tr><td>🦁 Animalia</td><td>Clasifica animales por hábitat</td></tr>
      <tr><td>🧩 Mate-reto</td><td>Laberintos con preguntas de matemáticas</td></tr>
      <tr><td>🔍 Encuentra y aprende</td><td>Busca objetos y aprende su nombre</td></tr>
      <tr><td>🔤 Caza letras</td><td>Encuentra la letra correcta</td></tr>
    </tbody>
  </table>
</div>

<br/>

<div class="sm-card" style="animation-delay: 0.4s">
  <div class="sm-title">🧩 Diferencias con la versión completa</div>
  <table style="margin-top: 10px">
    <thead><tr><th>Aspecto</th><th>Versión completa</th><th>Demo</th></tr></thead>
    <tbody>
      <tr><td>Base de datos</td><td>MySQL (servidor Flask)</td><td>En memoria (sin red)</td></tr>
      <tr><td>Login/sesiones</td><td>Usuarios y sesiones</td><td>Sesión demo automática</td></tr>
      <tr><td>Licencia</td><td>Clave por máquina</td><td>Sin licencia</td></tr>
      <tr><td>Almacenamiento</td><td>Archivos y BD</td><td>Nada (no persiste)</td></tr>
      <tr><td>Panel de info</td><td>Streamlit/ReportLab</td><td>No disponible</td></tr>
    </tbody>
  </table>
</div>

<hr/>

<p align="center" style="color:#8b949e; font-size: 13px">
  Hecho con 💛 para el proyecto educativo <b style="color:#d4a84b">SIMUS.MJN</b>
</p>
