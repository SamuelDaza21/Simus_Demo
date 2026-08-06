from __future__ import annotations

import io
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

import mysql.connector

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from streamlit_option_menu import option_menu

from core.IA import AI
import core.config as config
from core.Traductor import Traductor

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = BASE_DIR / "config_api.json"
REPORTS_DIR = BASE_DIR / "reportes"

COLOR_PRIMARY = "#2C3E50"
COLOR_SECONDARY = "#34495E"
COLOR_ACCENT = "#2980B9"
COLOR_SURFACE = "#ECF0F1"
COLOR_TEXT = "#1F2D3D"
PALETTE = ["#2C3E50", "#2980B9", "#16A085", "#8E44AD", "#C0392B"]


# ----------------------------------------------------------------------
# Funciones para asegurar el traductor en modo standalone (Streamlit)
# ----------------------------------------------------------------------
def ensure_translator():
    """Inicializa el traductor si no está listo, usando español por defecto o el idioma guardado."""
    if config.traductor is not None:
        return
    idioma = "es"  # fallback
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "idioma" in data:
                    idioma = data["idioma"]
        except:
            pass
    config.traductor = Traductor(idioma)
    print(f"[Dashboard] Traductor inicializado con idioma: {idioma}")


def t(key: str, **kwargs) -> str:
    """Helper para obtener textos traducidos, asegurando que el traductor esté listo."""
    ensure_translator()
    text = config.traductor.t(key)
    if kwargs:
        return text.format(**kwargs)
    return text


# ----------------------------------------------------------------------
# StreamlitInfoLauncher (sin cambios importantes)
# ----------------------------------------------------------------------
class StreamlitInfoLauncher:
    """Lanza y reutiliza el dashboard Streamlit desde el flujo principal de pygame."""

    def __init__(self, script_path: Path | None = None, port: int = 8502):
        self.script_path = script_path or Path(__file__).resolve()
        self.port = port
        self.url = f"http://127.0.0.1:{port}"
        self.process: subprocess.Popen[str] | None = None
        # No accedemos a config.traductor aquí porque podría ser None

    def _is_port_open(self) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            return sock.connect_ex(("127.0.0.1", self.port)) == 0

    def _build_command(self) -> list[str]:
        if getattr(sys, "frozen", False):
            streamlit_executable = shutil.which("streamlit")
            if not streamlit_executable:
                raise RuntimeError("No se encontró el ejecutable de Streamlit en el sistema.")
            return [
                streamlit_executable,
                "run",
                str(self.script_path),
                "--server.headless=true",
                f"--server.port={self.port}",
                "--browser.gatherUsageStats=false",
            ]

        return [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(self.script_path),
            "--server.headless=true",
            f"--server.port={self.port}",
            "--browser.gatherUsageStats=false",
        ]

    def _persist_session(self, session_id: int | None) -> None:
        if session_id is None:
            return
        payload = {}
        if CONFIG_PATH.exists():
            try:
                payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                payload = {}
        payload["sesion_id"] = int(session_id)
        CONFIG_PATH.write_text(json.dumps(payload), encoding="utf-8")

    def start(self, session_id: int | None = None) -> str:
        self._persist_session(session_id)

        if self.process and self.process.poll() is None and self._is_port_open():
            return self.url

        if not self._is_port_open():
            command = self._build_command()
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=str(BASE_DIR),
            )

            started = False
            for _ in range(40):
                if self._is_port_open():
                    started = True
                    break
                time.sleep(0.25)

            if not started:
                self.stop()
                raise RuntimeError("No fue posible iniciar el dashboard Streamlit.")

        return self.url

    def open_dashboard(self, session_id: int | None = None) -> str:
        url = self.start(session_id=session_id)
        webbrowser.open(url)
        return url

    def stop(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None


# ----------------------------------------------------------------------
# Configuración de página
# ----------------------------------------------------------------------
def configurar_pagina() -> None:
    st.set_page_config(
        page_title=t("page_title"),
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.markdown(
        f"""
        <style>
            :root {{
                --primary: {COLOR_PRIMARY};
                --secondary: {COLOR_SECONDARY};
                --accent: {COLOR_ACCENT};
                --surface: {COLOR_SURFACE};
                --text: {COLOR_TEXT};
            }}

            [data-testid="stSidebar"] {{display: none;}}
            [data-testid="collapsedControl"] {{display: none;}}
            #MainMenu {{visibility: hidden;}}
            footer {{visibility: hidden;}}
            header {{visibility: hidden;}}

            html, body, [class*="css"] {{
                font-family: "Segoe UI", Helvetica, Arial, sans-serif;
                color: var(--text);
                background: linear-gradient(180deg, #F8FAFC 0%, #EEF3F7 100%);
            }}

            ::-webkit-scrollbar {{width: 6px; height: 6px;}}
            ::-webkit-scrollbar-track {{background: transparent;}}
            ::-webkit-scrollbar-thumb {{background: #BDC3C7; border-radius: 999px;}}
            ::-webkit-scrollbar-thumb:hover {{background: #AAB7B8;}}

            .block-container {{padding-top: 1.2rem; padding-bottom: 2rem;}}

            .hero-card {{
                background: linear-gradient(135deg, rgba(44,62,80,0.98), rgba(52,73,94,0.95));
                padding: 1.8rem 2rem;
                border-radius: 24px;
                color: white;
                box-shadow: 0 22px 48px rgba(44,62,80,0.18);
                margin-bottom: 1.25rem;
            }}

            .hero-title {{font-size: 2.1rem; font-weight: 700; margin-bottom: 0.35rem;}}
            .hero-subtitle {{font-size: 1rem; opacity: 0.88; margin-bottom: 1rem;}}
            .hero-meta {{display: flex; gap: 0.75rem; flex-wrap: wrap;}}
            .hero-pill {{
                background: rgba(236,240,241,0.12);
                border: 1px solid rgba(236,240,241,0.18);
                padding: 0.55rem 0.85rem;
                border-radius: 999px;
                font-size: 0.92rem;
            }}

            .metric-card {{
                background: rgba(255,255,255,0.95);
                border: 1px solid rgba(44,62,80,0.08);
                border-radius: 20px;
                padding: 1rem 1.05rem;
                box-shadow: 0 14px 30px rgba(44,62,80,0.06);
                min-height: 120px;
            }}

            .metric-label {{font-size: 0.82rem; color: #6B7A89; text-transform: uppercase; letter-spacing: 0.08em;}}
            .metric-value {{font-size: 1.85rem; font-weight: 700; color: var(--primary); margin-top: 0.35rem;}}
            .metric-note {{font-size: 0.9rem; color: #5D6D7E; margin-top: 0.3rem;}}

            .section-card {{
                background: rgba(255,255,255,0.96);
                border: 1px solid rgba(52,73,94,0.08);
                border-radius: 22px;
                padding: 1.15rem 1.2rem;
                box-shadow: 0 12px 30px rgba(44,62,80,0.05);
                margin-bottom: 1rem;
            }}

            .footer-actions {{
                background: rgba(255,255,255,0.96);
                border: 1px solid rgba(52,73,94,0.08);
                border-radius: 20px;
                padding: 1rem 1.2rem;
                margin-top: 1rem;
            }}

            div[data-testid="stButton"] > button,
            div[data-testid="stDownloadButton"] > button {{
                border-radius: 14px;
                border: 1px solid rgba(41,128,185,0.2);
                background: linear-gradient(135deg, #FFFFFF 0%, #F7FAFC 100%);
                color: var(--primary);
                font-weight: 600;
                transition: all 0.25s ease;
                box-shadow: 0 8px 18px rgba(44,62,80,0.06);
            }}

            div[data-testid="stButton"] > button:hover,
            div[data-testid="stDownloadButton"] > button:hover {{
                border-color: rgba(41,128,185,0.45);
                color: var(--accent);
                transform: translateY(-1px);
                box-shadow: 0 12px 22px rgba(41,128,185,0.12);
            }}

            div[data-testid="stExpander"] {{
                border: 1px solid rgba(52,73,94,0.08);
                border-radius: 18px;
                overflow: hidden;
            }}

            .small-muted {{font-size: 0.92rem; color: #6B7A89;}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_db_connection() -> mysql.connector.MySQLConnection:
    """Abre conexión MySQL (mismos parámetros del .env que la API)."""
    try:
        from dotenv import load_dotenv
        load_dotenv(BASE_DIR / ".." / ".env")
    except Exception:
        pass
    connection = mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", 3306)),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "simus_mjn"),
    )
    return connection


def get_session_id() -> int | None:
    env_session = os.environ.get("SIMUS_SESSION_ID")
    if env_session:
        try:
            return int(env_session)
        except:
            pass

    if CONFIG_PATH.exists():
        try:
            config_data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            session_id = config_data.get("sesion_id")
            return int(session_id) if session_id is not None else None
        except (ValueError, json.JSONDecodeError, OSError):
            return None
    return None


@st.cache_data(show_spinner=False)
def load_dashboard_data(session_id: int | None = None) -> dict[str, object]:
    with get_db_connection() as connection:
        sessions_df = pd.read_sql_query("SELECT ID_sesion, ID_usuario FROM sesiones ORDER BY ID_sesion", connection)
        if sessions_df.empty:
            return {
                "session_id": None,
                "user": None,
                "history": pd.DataFrame(),
                "summary": {},
                "user_sessions": pd.DataFrame(),
            }

        if session_id is None:
            session_id = int(sessions_df["ID_sesion"].iloc[-1])

        selected = sessions_df[sessions_df["ID_sesion"] == session_id]
        if selected.empty:
            session_id = int(sessions_df["ID_sesion"].iloc[-1])
            selected = sessions_df[sessions_df["ID_sesion"] == session_id]

        user_id = int(selected["ID_usuario"].iloc[0])
        user_sessions = sessions_df[sessions_df["ID_usuario"] == user_id].copy()

        users_df = pd.read_sql_query(
            "SELECT ID_usuario, Nickname, FechaNacimiento FROM usuarios WHERE ID_usuario = ?",
            connection,
            params=[user_id],
        )
        user = users_df.iloc[0].to_dict() if not users_df.empty else None

        placeholders = ",".join(["?"] * len(user_sessions))
        history_df = pd.read_sql_query(
            f"""
                SELECT id, ID_sesion, Nombre_juego, puntaje_nuevo, Nuevo_Acierto, Nuevo_error,
                       puntaje_antiguo, Aciertos_antiguo, Errores_antiguo
                FROM historial_resultados
                WHERE ID_sesion IN ({placeholders})
                ORDER BY id ASC
                """,
            connection,
            params=user_sessions["ID_sesion"].tolist(),
        )

    if history_df.empty:
        return {
            "session_id": session_id,
            "user": user,
            "history": history_df,
            "summary": {},
            "user_sessions": user_sessions,
        }

    history_df["sesion_orden"] = history_df.groupby("Nombre_juego").cumcount() + 1
    history_df["mejora"] = history_df["puntaje_nuevo"] - history_df["puntaje_antiguo"]
    history_df["eficiencia"] = history_df["Nuevo_Acierto"] - history_df["Nuevo_error"]
    history_df["registro"] = history_df.index + 1

    score_mean = float(history_df["puntaje_nuevo"].mean())
    score_max = int(history_df["puntaje_nuevo"].max())
    improvement = float(history_df["mejora"].mean())
    total_sessions = int(len(history_df))
    games_count = int(history_df["Nombre_juego"].nunique())
    best_game_series = history_df.groupby("Nombre_juego")["puntaje_nuevo"].mean().sort_values(ascending=False)
    best_game = str(best_game_series.index[0]) if not best_game_series.empty else t("Sin_datos")

    summary = {
        "puntaje_promedio": round(score_mean, 1),
        "mejor_puntaje": score_max,
        "mejora_promedio": round(improvement, 1),
        "sesiones_totales": total_sessions,
        "juegos_jugados": games_count,
        "mejor_juego": best_game,
    }

    return {
        "session_id": session_id,
        "user": user,
        "history": history_df,
        "summary": summary,
        "user_sessions": user_sessions,
    }


def configure_chart_style() -> None:
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams.update(
        {
            "figure.dpi": 320,
            "savefig.dpi": 320,
            "axes.titlesize": 18,
            "axes.labelsize": 12,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "axes.edgecolor": "#D5DCE3",
            "grid.color": "#E6ECF2",
            "grid.alpha": 0.75,
            "axes.facecolor": "white",
            "figure.facecolor": "white",
        }
    )


def finalize_axis(ax: plt.Axes, title: str, xlabel: str, ylabel: str) -> None:
    ax.set_title(title, loc="left", fontweight="bold", color=COLOR_PRIMARY, pad=14)
    ax.set_xlabel(xlabel, color=COLOR_SECONDARY)
    ax.set_ylabel(ylabel, color=COLOR_SECONDARY)
    ax.grid(axis="y", linestyle="-", linewidth=0.8)
    ax.grid(axis="x", visible=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#D5DCE3")
    ax.tick_params(colors="#607080")


def build_global_chart(history_df: pd.DataFrame) -> plt.Figure:
    configure_chart_style()
    fig, ax = plt.subplots(figsize=(12, 5.8))
    global_series = history_df.reset_index(drop=True).copy()
    global_series["paso"] = global_series.index + 1

    sns.lineplot(
        data=global_series,
        x="paso",
        y="puntaje_nuevo",
        marker="o",
        linewidth=2.8,
        markersize=7,
        color=COLOR_ACCENT,
        ax=ax,
    )
    ax.fill_between(global_series["paso"], global_series["puntaje_nuevo"], color="#AED6F1", alpha=0.25)
    ax.set_ylim(0, max(100, int(global_series["puntaje_nuevo"].max()) + 5))
    finalize_axis(ax, t("Progreso_global"), t("Registro"), t("Puntaje"))
    fig.tight_layout()
    return fig


def build_game_chart(history_df: pd.DataFrame, game_name: str) -> plt.Figure:
    configure_chart_style()
    game_df = history_df[history_df["Nombre_juego"] == game_name].copy()
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    color = PALETTE[abs(hash(game_name)) % len(PALETTE)]

    sns.lineplot(
        data=game_df,
        x="sesion_orden",
        y="puntaje_nuevo",
        marker="o",
        linewidth=2.6,
        markersize=6,
        color=color,
        ax=ax,
    )
    ax.fill_between(game_df["sesion_orden"], game_df["puntaje_nuevo"], color=color, alpha=0.16)
    ax.set_ylim(0, max(100, int(game_df["puntaje_nuevo"].max()) + 5))
    finalize_axis(ax, t("Evolucion_de").format(game=game_name), t("Sesion"), t("Puntaje"))
    fig.tight_layout()
    return fig


def build_bar_chart(history_df: pd.DataFrame) -> plt.Figure:
    configure_chart_style()
    stats_df = (
        history_df.groupby("Nombre_juego", as_index=False)["puntaje_nuevo"]
        .mean()
        .sort_values("puntaje_nuevo", ascending=False)
    )
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    sns.barplot(
        data=stats_df,
        x="puntaje_nuevo",
        y="Nombre_juego",
        hue="Nombre_juego",
        palette=PALETTE,
        dodge=False,
        legend=False,
        ax=ax,
    )
    finalize_axis(ax, t("Promedio_por_juego"), t("Puntaje_promedio"), t("Juego"))
    ax.set_xlim(0, max(100, int(stats_df["puntaje_nuevo"].max()) + 5))
    fig.tight_layout()
    return fig


def fig_to_png_buffer(fig: plt.Figure) -> io.BytesIO:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=320, bbox_inches="tight", facecolor="white")
    buffer.seek(0)
    return buffer


def build_pdf_report(data: dict[str, object]) -> bytes:

    history_df: pd.DataFrame = data["history"]
    user = data["user"] or {}
    summary = data["summary"] or {}
    report_buffer = io.BytesIO()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        report_buffer,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor(COLOR_PRIMARY),
            alignment=TA_LEFT,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor(COLOR_SECONDARY),
            spaceAfter=8,
            spaceBefore=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyTextPro",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.4,
            leading=15,
            alignment=TA_JUSTIFY,
            textColor=colors.HexColor(COLOR_TEXT),
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallMeta",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#6B7A89"),
            alignment=TA_CENTER,
        )
    )

    try:
        idioma_pdf = "es"
        try:
            ensure_translator()
            if hasattr(config.traductor, 'get_current_language'):
                idioma_pdf = config.traductor.get_current_language()
        except:
            pass
    except Exception:
        idioma_pdf = "es"

    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        # Fuente del idioma actual (es/en/fr)
        font_path = config.FUENTES_IDIOMAS.get(idioma_pdf)
        if font_path and os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('UniFont', font_path))
            # Aplicar a todos los estilos que usaremos
            for style_name in ['ReportTitle', 'SectionHeading', 'BodyTextPro', 'SmallMeta']:
                if style_name in styles:
                    styles[style_name].fontName = 'UniFont'
            print("[PDF] Fuente registrada:", font_path)
        else:
            print("[PDF] No se encontró fuente para el idioma, usando Helvetica")
    except Exception as e:
        print(f"[PDF] Error registrando fuente: {e}")

    story = []
    player_name = user.get("Nickname", t("Sin_identificar"))
    story.append(Paragraph(t("Titulo_Informe"), styles["ReportTitle"]))
    story.append(
        Paragraph(
            t("Subtitulo_Informe").format(player_name=player_name, session_id=data['session_id']),
            styles["BodyTextPro"],
        )
    )
    idioma_actual = "es"
    try:
        ensure_translator()
        if hasattr(config.traductor, 'get_current_language'):
            idioma_actual = config.traductor.get_current_language()
    except:
        pass
    ia = AI()
    session_id = data.get("session_id")
    analisis_ia_dict = ia.ResultadosPDF(session_id, idioma_actual)

    story.append(Paragraph(t("Resumen_Ejecutivo"), styles["SectionHeading"]))
    story.append(Paragraph(analisis_ia_dict.get("resumen", t("Sin_datos")), styles["BodyTextPro"]))#ACA DEBE IR SOLO EL RESUMEN EJECUTIVO DADO POR LA IA

    story.append(Paragraph(t("Analisis"), styles["SectionHeading"]))
    story.append(Paragraph(analisis_ia_dict.get("analisis", t("Sin_datos")), styles["BodyTextPro"]))#ACA DEBE IR SOLO EL ANALISIS GENERAL DADO POR LA IA (NO DEBE IR RESUMEN GENERAL, NI CONCLUSIONES, NI RECOMENDACIONES)

    story.append(Paragraph(t("Estadisticas"), styles["SectionHeading"]))
    summary_rows = [
        [t("Indicador"), t("Valor")],
        [t("Sesiones_analizadas"), str(summary.get("sesiones_totales", 0))],
        [t("Juegos_evaluados"), str(summary.get("juegos_jugados", 0))],
        [t("Puntaje_promedio"), f"{summary.get('puntaje_promedio', 0)}%"],
        [t("Mejor_puntaje"), f"{summary.get('mejor_puntaje', 0)}%"],
        [t("Mejora_promedio"), f"{summary.get('mejora_promedio', 0)} pts"],
        [t("Juego_destacado"), str(summary.get("mejor_juego", t("Sin_datos")))],
    ]
    summary_table = Table(summary_rows, colWidths=[6.8 * cm, 8.0 * cm])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLOR_PRIMARY)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), "UniFont"),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D6DBDF")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 0.35 * cm))

    story.append(Paragraph(t("Graficas"), styles["SectionHeading"]))
    global_fig = build_global_chart(history_df)
    global_image = Image(fig_to_png_buffer(global_fig), width=17.2 * cm, height=8.3 * cm)
    story.append(global_image)
    plt.close(global_fig)
    story.append(Spacer(1, 0.35 * cm))

    bar_fig = build_bar_chart(history_df)
    bar_image = Image(fig_to_png_buffer(bar_fig), width=17.2 * cm, height=8.2 * cm)
    story.append(bar_image)
    plt.close(bar_fig)

    for game_name in history_df["Nombre_juego"].drop_duplicates().tolist():
        story.append(PageBreak())
        story.append(Paragraph(t("Grafica_por_juego").format(game=game_name), styles["SectionHeading"]))
        game_fig = build_game_chart(history_df, game_name)
        story.append(Image(fig_to_png_buffer(game_fig), width=17.2 * cm, height=8.2 * cm))
        plt.close(game_fig)

        game_stats = history_df[history_df["Nombre_juego"] == game_name][
            ["ID_sesion", "puntaje_antiguo", "puntaje_nuevo", "mejora", "Nuevo_Acierto", "Nuevo_error"]
        ].copy()
        game_stats.columns = [t("Sesion"), t("Puntaje_previo"), t("Puntaje_actual"), t("Mejora"), t("Aciertos"), t("Errores")]
        table_rows = [game_stats.columns.tolist()] + game_stats.astype(str).values.tolist()[:12]
        detail_table = Table(table_rows, repeatRows=1)
        detail_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLOR_SECONDARY)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, -1), "UniFont"),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D6DBDF")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.6),
                ]
            )
        )
        story.append(Spacer(1, 0.25 * cm))
        story.append(detail_table)

    story.append(PageBreak())

    story.append(Paragraph(t("Conclusiones"), styles["SectionHeading"]))
    story.append(Paragraph(analisis_ia_dict.get("conclusiones", t("Sin_datos")), styles["BodyTextPro"]))#ACA DEBE IR SOLO LAS CONCLUSIONES QUE DA LA IA

    story.append(Paragraph(t("Recomendaciones"), styles["SectionHeading"]))
    story.append(Paragraph(analisis_ia_dict.get("recomendaciones", t("Sin_datos")), styles["BodyTextPro"]))#ACA DEBE IR SOLO LAS RECOMENDACIONES DADAS POR LA IA

    story.append(PageBreak())
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(t("Pie_Informe"), styles["SmallMeta"]))

    doc.build(story)
    return report_buffer.getvalue()


def render_metric_cards(summary: dict[str, object]) -> None:
    cards = [
        (t("Sesiones_analizadas"), summary.get("sesiones_totales", 0), t("Card_note_sesiones")),
        (t("Puntaje_promedio"), f"{summary.get('puntaje_promedio', 0)}%", t("Card_note_promedio")),
        (t("Mejor_puntaje"), f"{summary.get('mejor_puntaje', 0)}%", t("Card_note_mejor")),
        (t("Mejora_promedio"), f"{summary.get('mejora_promedio', 0)} pts", t("Card_note_mejora")),
    ]
    columns = st.columns(4)
    for column, (label, value, note) in zip(columns, cards):
        with column:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-note">{note}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_home(data: dict[str, object], pdf_bytes: bytes) -> None:
    user = data["user"] or {}
    summary = data["summary"] or {}

    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-title">{t("hero_title")}</div>
            <div class="hero-subtitle">{t("hero_subtitle")}</div>
            <div class="hero-meta">
                <div class="hero-pill">{t("Jugador_info")}: {user.get('Nickname', t('Sin_identificar'))}</div>
                <div class="hero-pill">{t("Sesion_base")}: {data.get('session_id') or 'N/D'}</div>
                <div class="hero-pill">{t("Mejor_juego")}: {summary.get('mejor_juego', t('Sin_datos'))}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_metric_cards(summary)
    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    overview_col, actions_col = st.columns([1.8, 1])
    with overview_col:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader(t("Resumen_desempeno"))
        st.write(t("Resumen_texto"))
        st.markdown("</div>", unsafe_allow_html=True)
    with actions_col:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader(t("Acciones_rapidas"))
        st.download_button(
            label=t("Descargar_PDF"),
            data=pdf_bytes,
            file_name=f"{t('reporte_prefix')}_{user.get('Nickname', 'usuario').replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="download_home"
        )
        if st.button(t("Actualizar_datos"), use_container_width=True):
            load_dashboard_data.clear()
            st.rerun()
        st.markdown(f"<p class='small-muted'>{t('Menu_info')}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


def render_information(data: dict[str, object]) -> None:
    history_df: pd.DataFrame = data["history"]
    summary = data["summary"] or {}

    render_metric_cards(summary)
    st.markdown("<div style='height:0.9rem'></div>", unsafe_allow_html=True)

    chart_left, chart_right = st.columns([1.4, 1])
    with chart_left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader(t("Tendencia_global"))
        st.pyplot(build_global_chart(history_df), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with chart_right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader(t("Promedio_por_juego"))
        st.pyplot(build_bar_chart(history_df), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader(t("Graficas_por_juego"))
    game_columns = st.columns(2)
    for index, game_name in enumerate(history_df["Nombre_juego"].drop_duplicates().tolist()):
        with game_columns[index % 2]:
            with st.expander(game_name, expanded=True):
                st.pyplot(build_game_chart(history_df, game_name), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    details_col, analysis_col = st.columns([1.5, 1])
    with details_col:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader(t("Historial_completo"))
        table_df = history_df[
            [
                "id",
                "ID_sesion",
                "Nombre_juego",
                "puntaje_antiguo",
                "puntaje_nuevo",
                "mejora",
                "Nuevo_Acierto",
                "Nuevo_error",
            ]
        ].copy()
        table_df.columns = [
            "ID",
            t("Sesion"),
            t("Juego"),
            t("Puntaje_previo"),
            t("Puntaje_actual"),
            t("Mejora"),
            t("Aciertos"),
            t("Errores"),
        ]
        height = min(35 * (len(table_df) + 1), 900)
        st.dataframe(table_df, use_container_width=True, hide_index=True, height=height)
        st.markdown("</div>", unsafe_allow_html=True)

    with analysis_col:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader(t("Estadisticas_resumidas"))
        stats_df = (
            history_df.groupby("Nombre_juego", as_index=False)
            .agg(
                sesiones=("id", "count"),
                puntaje_promedio=("puntaje_nuevo", "mean"),
                mejor_resultado=("puntaje_nuevo", "max"),
                mejora_promedio=("mejora", "mean"),
            )
            .sort_values("puntaje_promedio", ascending=False)
        )
        stats_df["puntaje_promedio"] = stats_df["puntaje_promedio"].round(1)
        stats_df["mejora_promedio"] = stats_df["mejora_promedio"].round(1)
        stats_df.columns = [t("Juego"), t("Sesiones"), t("Promedio"), t("Mejor"), t("Mejora_media")]
        st.dataframe(stats_df, use_container_width=True, hide_index=True, height=310)

    with st.expander(t("Analisis_redactado"), expanded=True):
        idioma_actual = "es"
        try:
            ensure_translator()
            if hasattr(config.traductor, 'get_current_language'):
                idioma_actual = config.traductor.get_current_language()
        except:
            pass
        ia = AI()
        session_id = data.get("session_id")
        st.write(ia.Resultados(session_id, idioma_actual))
    st.markdown("</div>", unsafe_allow_html=True)


def render_download(data: dict[str, object], pdf_bytes: bytes) -> None:
    user = data["user"] or {}
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader(t("Descargar_PDF_pro"))
    st.write(t("Descripcion_PDF"))
    st.download_button(
        label=t("Descargar_informe_PDF"),
        data=pdf_bytes,
        file_name=f"{t('reporte_prefix')}_{user.get('Nickname', 'usuario').replace(' ', '_')}.pdf",
        mime="application/pdf",
        use_container_width=True,
        key="download_footer"
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_exit() -> None:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader(t("Salir"))
    st.info(t("Salir_info"))
    st.markdown("</div>", unsafe_allow_html=True)


def render_footer(pdf_bytes: bytes, nickname: str) -> None:
    st.markdown('<div class="footer-actions">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1.3, 1, 1])
    with col1:
        st.markdown("**" + t("Acciones_finales") + "**")
        st.markdown(f"<p class='small-muted'>{t('Footer_texto')}</p>", unsafe_allow_html=True)
    with col2:
        st.download_button(
            t("Descargar_PDF"),
            data=pdf_bytes,
            file_name=f"{t('reporte_prefix')}_{nickname.replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="download_footer_pdf"  # ← Cambia a un nombre único
        )

    with col3:
        if st.button(t("Salir"), use_container_width=True):
            st.info(t("Salir_info_cierre"))
    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    configurar_pagina()
    session_id = get_session_id()

    try:
        data = load_dashboard_data(session_id)
    except FileNotFoundError as error:
        st.error(str(error))
        return

    history_df: pd.DataFrame = data["history"]
    if history_df.empty:
        st.warning(t("No_datos_disponibles"))
        return

    selected = option_menu(
        menu_title=None,
        options=[t("Inicio"), t("Informacion"), t("Descargar_PDF"), t("Salir")],
        icons=["house", "bar-chart", "download", "box-arrow-right"],
        menu_icon="cast",
        default_index=1,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "transparent", "margin-bottom": "0.85rem"},
            "icon": {"color": COLOR_ACCENT, "font-size": "16px"},
            "nav-link": {
                "font-size": "15px",
                "font-weight": "600",
                "text-align": "center",
                "margin": "0px 8px 0px 0px",
                "padding": "12px 18px",
                "border-radius": "14px",
                "background-color": "#FFFFFF",
                "color": COLOR_PRIMARY,
                "border": "1px solid rgba(44, 62, 80, 0.08)",
            },
            "nav-link-selected": {
                "background-color": COLOR_PRIMARY,
                "color": "white",
                "border": f"1px solid {COLOR_PRIMARY}",
            },
        },
    )

    pdf_bytes = build_pdf_report(data)
    nickname = (data["user"] or {}).get("Nickname", "usuario")

    if selected == t("Inicio"):
        render_home(data, pdf_bytes)
    elif selected == t("Informacion"):
        render_information(data)
    elif selected == t("Descargar_PDF"):
        render_download(data, pdf_bytes)
    elif selected == t("Salir"):
        render_exit()

    render_footer(pdf_bytes, nickname)


if __name__ == "__main__":
    main()