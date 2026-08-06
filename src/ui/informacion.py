# InformacionJugador.py
import io
import os
import random
from datetime import datetime
import pygame
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import seaborn as sns
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import core.config as config
from core.ManejoCamara import ManejoCamara
from core.paths import SRC_DIR, fuentes, imagen
from api.APICliente import APICliente
from ui.barra_menu import BarraInferior
from logic.cursor import dibujar_cursor_unificado
from core.shortcuts import aplicar_atajo_camara, procesar_atajos_globales
from core.IA import AI


class InformacionJugador:
    def __init__(self, camara=None, gestor_musica=None, ID_sesion=None):
        # Obtener la pantalla existente (no crear una nueva)
        pantalla = pygame.display.get_surface()
        if pantalla is None:
            pantalla = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.ANCHO, self.ALTO = pantalla.get_size()
        self.pantalla = pantalla
        pygame.display.set_caption("SIMUS.MJN - Tu Progreso")

        self.ID_sesion = ID_sesion
        self.camara = camara if camara else ManejoCamara(ancho=self.ANCHO, alto=self.ALTO, modo_ocular=True)
        self.gestor_musica = gestor_musica
        self.control_clic = False

        # Paleta de colores (no se traduce)
        self.COLOR_FONDO = (236, 240, 241)
        self.COLOR_PRIMARIO = (44, 62, 80)
        self.COLOR_SECUNDARIO = (52, 73, 94)
        self.COLOR_TERCIARIO = (41, 128, 185)
        self.COLOR_CUATERNARIO = (22, 160, 133)
        self.COLOR_QUINTENARIO = (142, 68, 173)
        self.COLOR_SEXTENARIO = (192, 57, 43)
        self.COLOR_TEXTO = (31, 45, 61)
        self.COLOR_TEXTO_CLARO = (107, 122, 137)
        self.COLOR_BORDE = (213, 220, 227)

        # Fuentes (se mantienen personalizadas, pero se usarán con config.render_text)
        try:
            ruta_fuente = fuentes("Karina.ttf")
            self.fuente_titulo = pygame.font.Font(ruta_fuente, 42)
            self.fuente_subtitulo = pygame.font.Font(ruta_fuente, 28)
            self.fuente_texto = pygame.font.Font(ruta_fuente, 20)
            self.fuente_pequena = pygame.font.Font(ruta_fuente, 16)
        except:
            self.fuente_titulo = pygame.font.SysFont("Arial", 42, bold=True)
            self.fuente_subtitulo = pygame.font.SysFont("Arial", 28, bold=True)
            self.fuente_texto = pygame.font.SysFont("Arial", 20)
            self.fuente_pequena = pygame.font.SysFont("Arial", 16)

        # Cargar fondo
        try:
            self.fondo_original = pygame.image.load(imagen("General/fondo.png"))
            self.fondo_original = pygame.transform.scale(self.fondo_original, (self.ANCHO, self.ALTO))
            self.fondo = self.crear_fondo_difuminado()
        except:
            self.fondo = None

        # Inicializar API cliente
        self.api = APICliente()
        print("=== INICIANDO DIAGNÓSTICO DE API ===")
        self.api.diagnosticar_conexion()

        print("=== CONFIGURANDO SESIÓN ===")
        if not self.api.sesion_actual:
            ultima_sesion = self.api.cargar_ultima_sesion()
            if not ultima_sesion:
                print("⚠️ No hay sesión guardada. Creando sesión de prueba...")
                usuario_prueba_id = self.api.obtener_id_usuario("UsuarioPrueba")
                if usuario_prueba_id:
                    print(f"✅ Usuario de prueba encontrado: {usuario_prueba_id}")
                    sesion_id = self.api.crear_sesion(usuario_prueba_id)
                    if sesion_id:
                        self.api.sesion_actual = sesion_id
                        self.api.guardar_config_local({"sesion_id": sesion_id})
                        print(f"✅ Sesión creada: {sesion_id}")
                    else:
                        print("❌ No se pudo crear sesión")
                else:
                    print("ℹ️ No hay usuario de prueba. Los datos se mostrarán cuando haya partidas jugadas.")
            else:
                print(f"✅ Sesión cargada: {self.api.sesion_actual}")
        else:
            print(f"✅ Sesión ya está activa: {self.api.sesion_actual}")

        # Configurar elementos de UI
        self.desplazamiento = 0
        self.altura_total_contenido = 0
        self.velocidad_scroll = 40
        self.chart_dpi = 320
        self.directorio_reportes = os.path.join(SRC_DIR, "reportes")
        self.botones_accion = []
        self.estado_ui = {"mensaje": "", "tipo": "info", "expira": 0}
        self.filas_historial_visibles = 14

        # Crear elementos visuales
        self.actualizar_datos_vista()

        # Barra inferior
        tamaño_icono = int(min(self.ANCHO, self.ALTO) * 0.08)
        self.iconos = {
            "inicio": {"imagen": pygame.transform.scale(pygame.image.load(imagen("menu/inicio.png")),
                                                        (tamaño_icono, tamaño_icono)), "texto": config.traductor.t("Inicio")},
            "instrucciones": {"imagen": pygame.transform.scale(pygame.image.load(imagen("menu/instrucciones.png")),
                                                               (tamaño_icono, tamaño_icono)), "texto": config.traductor.t("Instrucciones")},
            "configuracion": {"imagen": pygame.transform.scale(pygame.image.load(imagen("menu/configuraciones.png")),
                                                               (tamaño_icono, tamaño_icono)), "texto": config.traductor.t("Configuración")},
            "salir": {"imagen": pygame.transform.scale(pygame.image.load(imagen("menu/salida.png")),
                                                       (tamaño_icono, tamaño_icono)), "texto": config.traductor.t("Salir")},
            "info": {"imagen": pygame.transform.scale(pygame.image.load(imagen("menu/informacion.png")),
                                                      (tamaño_icono, tamaño_icono)), "texto": config.traductor.t("Información")},
            "jugar": {"imagen": pygame.transform.scale(pygame.image.load(imagen("menu/juegos.png")),
                                                       (tamaño_icono, tamaño_icono)), "texto": config.traductor.t("Jugar")}
        }

        from ui.Inicio import SistemaTTS
        voz = SistemaTTS()

        self.barra = BarraInferior(
            self.ANCHO,
            self.ALTO,
            {"instrucciones": self.iconos["instrucciones"],
             "configuracion": self.iconos["configuracion"],
             "salir": self.iconos["salir"],
             "info": self.iconos["info"],
             "jugar": self.iconos["jugar"],
             "inicio": self.iconos["inicio"]},
            camara=self.camara,
            gestor_musica=self.gestor_musica,
            decir_texto=voz.decir_texto,
            ID_Sesion=self.ID_sesion
        )

    def crear_fondo_difuminado(self):
        """Crea una versión más clara del fondo para mejor legibilidad"""
        fondo = self.fondo_original.copy()
        overlay = pygame.Surface((self.ANCHO, self.ALTO), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 180))
        fondo.blit(overlay, (0, 0))
        return fondo

    def dibujar_panel_base(self, superficie, rect, color=(255, 255, 255), borde=None,
                           radio=18, sombra=True, brillo_superior=False):
        if sombra:
            sombra_superficie = pygame.Surface((rect.width + 16, rect.height + 16), pygame.SRCALPHA)
            pygame.draw.rect(sombra_superficie, (34, 53, 69, 28), sombra_superficie.get_rect(), border_radius=radio + 6)
            superficie.blit(sombra_superficie, (rect.x - 2, rect.y + 8))

        pygame.draw.rect(superficie, color, rect, border_radius=radio)
        pygame.draw.rect(superficie, borde or self.COLOR_BORDE, rect, 2, border_radius=radio)

        if brillo_superior:
            overlay = pygame.Surface((rect.width, max(44, rect.height // 3)), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 40))
            superficie.blit(overlay, (rect.x, rect.y))

    def dibujar_titulo_seccion(self, superficie, texto, y_offset, subtitulo=None):
        titulo_surf = config.render_text(texto, self.fuente_subtitulo, self.COLOR_TEXTO)
        superficie.blit(titulo_surf, (50, y_offset))
        pygame.draw.line(
            superficie,
            self.COLOR_PRIMARIO,
            (50, y_offset + titulo_surf.get_height() + 10),
            (50 + min(180, titulo_surf.get_width() + 24), y_offset + titulo_surf.get_height() + 10),
            3
        )

        if subtitulo:
            texto_sub = config.render_text(subtitulo, self.fuente_pequena, self.COLOR_TEXTO_CLARO)
            superficie.blit(texto_sub, (50, y_offset + titulo_surf.get_height() + 18))
            return y_offset + titulo_surf.get_height() + 42

        return y_offset + titulo_surf.get_height() + 22

    def actualizar_datos_vista(self):
        self.usuario = self.obtener_datos_usuario()
        print(f"🔍 Usuario obtenido: {self.usuario}")
        self.historial = self.obtener_historial_usuario()
        print(f"📊 Historial obtenido: {len(self.historial)} juegos con datos")
        for juego, datos in self.historial.items():
            print(f"   {juego}: {len(datos)} registros")

        self.graficas = self.crear_graficas_modernas()
        self.tarjetas_estadisticas = self.crear_tarjetas_estadisticas()
        self.grafica_global = self.crear_grafica_global()
        self.recalcular_altura_contenido()
        self.desplazamiento = min(self.desplazamiento, max(0, self.altura_total_contenido - self.ALTO))

    def recalcular_altura_contenido(self):
        altura_base = 228 + 176
        if self.tarjetas_estadisticas:
            filas_tarjetas = (len(self.tarjetas_estadisticas) + 2) // 3
            altura_base += 50 + filas_tarjetas * 110
        else:
            altura_base += 120
        altura_base += 320 if self.grafica_global else 170
        if self.graficas:
            filas_graficas = (len(self.graficas) + 1) // 2
            altura_base += 50 + filas_graficas * 280 + 20
        else:
            altura_base += 180
        altura_base += 470
        altura_base += 390
        altura_base += 254
        self.altura_total_contenido = altura_base
        print(f"📏 Altura total del contenido: {self.altura_total_contenido}")

    def configurar_tema_graficas(self):
        sns.set_theme(style="whitegrid", context="talk")
        plt.rcParams.update({
            "figure.dpi": self.chart_dpi,
            "savefig.dpi": self.chart_dpi,
            "axes.titlesize": 16,
            "axes.labelsize": 11,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "axes.facecolor": "white",
            "figure.facecolor": "white",
            "grid.color": "#E6ECF2",
            "grid.alpha": 0.8,
        })

    def obtener_color_juego(self, juego):
        colores = {
            'Pares mágicos': self.COLOR_PRIMARIO,
            'Animalia': self.COLOR_TERCIARIO,
            'Encuentra y aprende': self.COLOR_CUATERNARIO,
            'Caza letras': self.COLOR_SEXTENARIO,
            'Mate-reto': self.COLOR_QUINTENARIO
        }
        return colores.get(juego, self.COLOR_PRIMARIO)

    def color_a_hex(self, color):
        return '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])

    def crear_superficie_grafica(self, fig, size):
        buffer = io.BytesIO()
        fig.savefig(
            buffer,
            format="png",
            dpi=self.chart_dpi,
            bbox_inches="tight",
            facecolor=fig.get_facecolor(),
            edgecolor="none"
        )
        buffer.seek(0)
        superficie = pygame.image.load(buffer, "grafica.png").convert_alpha()
        buffer.close()
        return pygame.transform.smoothscale(superficie, size)

    def configurar_ejes_grafica(self, ax, titulo, xlabel, ylabel):
        self.configurar_tema_graficas()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('#D5DCE3')
        ax.set_facecolor('white')
        ax.tick_params(colors='#607080', labelsize=10)
        ax.set_title(titulo, fontsize=17, fontweight='bold', color='#2C3E50', pad=18, loc='left')
        ax.set_xlabel(xlabel, fontsize=11, color='#34495E')
        ax.set_ylabel(ylabel, fontsize=11, color='#34495E')
        ax.set_ylim(0, 100)
        ax.grid(axis='y', alpha=0.8, color='#E6ECF2', linewidth=0.8)
        ax.grid(axis='x', visible=False)

    def crear_figura_juego(self, juego, registros, figsize=(10, 5)):
        if not registros:
            return None

        registros_ordenados = sorted(registros, key=lambda x: x["fecha"])
        puntajes = [r["puntaje"] for r in registros_ordenados]
        sesiones = list(range(1, len(registros_ordenados) + 1))
        color = self.obtener_color_juego(juego)
        color_hex = self.color_a_hex(color)

        self.configurar_tema_graficas()
        fig, ax = plt.subplots(figsize=figsize, dpi=self.chart_dpi, facecolor='white')

        if len(registros_ordenados) == 1:
            ax.pie(
                [puntajes[0], max(100 - puntajes[0], 0)],
                colors=[color_hex, '#E8F4FD'],
                startangle=90,
                wedgeprops={'width': 0.58, 'edgecolor': 'white', 'linewidth': 2}
            )
            ax.text(0, 0.05, f'{puntajes[0]}%', ha='center', va='center', fontsize=24,
                    fontweight='bold', color=color_hex)
            ax.text(0, -0.18, config.traductor.t("Primer registro"), ha='center', va='center', fontsize=11, color='#34495E')
            ax.set_title(juego, fontsize=16, fontweight='bold', color='#2C3E50', pad=18)
        else:
            ax.fill_between(sesiones, puntajes, alpha=0.22, color=color_hex)
            ax.plot(
                sesiones,
                puntajes,
                'o-',
                color=color_hex,
                linewidth=3,
                markersize=7,
                markerfacecolor='white',
                markeredgewidth=2
            )
            ax.scatter(sesiones[-1], puntajes[-1], s=110, color=color_hex, zorder=3)
            ax.annotate(
                config.traductor.t("Actual").format(puntaje=puntajes[-1]),
                (sesiones[-1], puntajes[-1]),
                xytext=(-20, 18),
                textcoords='offset points',
                fontsize=10,
                color='#2C3E50',
                bbox={'boxstyle': 'round,pad=0.3', 'fc': 'white', 'ec': '#D1D9E6'}
            )
            self.configurar_ejes_grafica(ax, juego, config.traductor.t("Sesiones"), config.traductor.t("Puntuacion"))
            ax.margins(x=0.05, y=0.12)

        fig.tight_layout(pad=1.2)
        return fig

    def crear_figura_global_mpl(self, figsize=(12, 6)):
        if not self.historial:
            print("⚠️  No hay historial para gráfica global")
            return None

        todas_fechas = []
        todos_puntajes = []
        todos_juegos = []

        for juego, registros in self.historial.items():
            for registro in registros:
                todas_fechas.append(registro["fecha"])
                todos_puntajes.append(registro["puntaje"])
                todos_juegos.append(juego)

        if not todas_fechas:
            print("⚠️  No hay fechas para gráfica global")
            return None

        datos_ordenados = sorted(zip(todas_fechas, todos_puntajes, todos_juegos), key=lambda x: x[0])
        puntajes_ordenados = [d[1] for d in datos_ordenados]
        sesiones = list(range(1, len(todas_fechas) + 1))

        self.configurar_tema_graficas()
        fig, ax = plt.subplots(figsize=figsize, dpi=self.chart_dpi, facecolor='white')
        color_hex = self.color_a_hex(self.COLOR_PRIMARIO)
        tendencia_color = self.color_a_hex(self.COLOR_TERCIARIO)

        ax.fill_between(sesiones, puntajes_ordenados, alpha=0.25, color=color_hex)
        ax.plot(
            sesiones,
            puntajes_ordenados,
            'o-',
            color=color_hex,
            linewidth=3,
            markersize=7,
            markerfacecolor='white',
            markeredgewidth=2,
            label=config.traductor.t("Puntaje")
        )

        if len(sesiones) > 1:
            z = np.polyfit(sesiones, puntajes_ordenados, 1)
            p = np.poly1d(z)
            ax.plot(sesiones, p(sesiones), '--', color=tendencia_color, linewidth=2, alpha=0.85, label=config.traductor.t("Tendencia"))
            ax.legend(frameon=False, loc='upper left')

        self.configurar_ejes_grafica(ax, config.traductor.t("Progreso_Global"), config.traductor.t("Sesiones_Totales"), config.traductor.t("Puntuacion"))
        ax.margins(x=0.03, y=0.12)
        fig.tight_layout(pad=1.2)
        return fig

    def obtener_nombre_archivo_seguro(self, texto):
        texto = (texto or "reporte").strip().replace(' ', '_')
        permitido = []
        for caracter in texto:
            if caracter.isalnum() or caracter in ('_', '-'):
                permitido.append(caracter)
        return ''.join(permitido) or 'reporte'

    def establecer_estado_ui(self, mensaje, tipo='info', duracion=4500):
        self.estado_ui = {
            'mensaje': mensaje,
            'tipo': tipo,
            'expira': pygame.time.get_ticks() + duracion
        }

    def dibujar_estado_ui(self, superficie):
        if not self.estado_ui.get('mensaje'):
            return

        if pygame.time.get_ticks() > self.estado_ui.get('expira', 0):
            self.estado_ui = {'mensaje': '', 'tipo': 'info', 'expira': 0}
            return

        colores = {
            'info': ((237, 246, 249), (64, 145, 108)),
            'success': ((230, 250, 235), (47, 128, 89)),
            'warning': ((255, 247, 230), (194, 124, 12)),
            'error': ((255, 236, 236), (186, 74, 74))
        }
        fondo, borde = colores.get(self.estado_ui['tipo'], colores['info'])
        rect = pygame.Rect(self.ANCHO - 430, 74, 380, 44)
        pygame.draw.rect(superficie, fondo, rect, border_radius=12)
        pygame.draw.rect(superficie, borde, rect, 2, border_radius=12)
        texto = config.render_text(self.estado_ui['mensaje'], self.fuente_pequena, borde)
        superficie.blit(texto, (rect.x + 14, rect.y + 13))

    def dibujar_panel_acciones(self, superficie, cursor_pos):
        definiciones = [
            ('exportar_pdf', config.traductor.t("Exportar PDF"), 'E'),
            ('datos_demo', config.traductor.t("Datos demo"), 'D'),
            ('recargar', config.traductor.t("Actualizar"), 'R')
        ]
        ancho_boton = max(140, min(180, int(self.ANCHO * 0.14)))
        alto_boton = 42
        separacion = 12
        total = len(definiciones) * ancho_boton + (len(definiciones) - 1) * separacion
        x_inicial = self.ANCHO - total - 36
        y = 20
        self.botones_accion = []

        for indice, (identificador, texto, atajo) in enumerate(definiciones):
            x = x_inicial + indice * (ancho_boton + separacion)
            rect = pygame.Rect(x, y, ancho_boton, alto_boton)
            hover = rect.collidepoint(cursor_pos)
            color_fondo = (255, 255, 255) if not hover else (249, 242, 234)
            color_borde = self.COLOR_PRIMARIO if hover else self.COLOR_BORDE
            pygame.draw.rect(superficie, color_fondo, rect, border_radius=14)
            pygame.draw.rect(superficie, color_borde, rect, 2, border_radius=14)

            etiqueta = config.render_text(texto, self.fuente_texto, self.COLOR_TEXTO)
            pista = config.render_text(atajo, self.fuente_pequena, self.COLOR_TEXTO_CLARO)
            superficie.blit(etiqueta, (rect.x + 14, rect.y + 9))
            superficie.blit(pista, (rect.right - pista.get_width() - 12, rect.y + 12))
            self.botones_accion.append({'id': identificador, 'rect': rect})

    def manejar_acciones_ui(self, cursor_pos, clic_activo):
        if not clic_activo:
            return False

        for boton in self.botones_accion:
            if boton['rect'].collidepoint(cursor_pos):
                if boton['id'] == 'exportar_pdf':
                    self.exportar_reporte_pdf()
                elif boton['id'] == 'datos_demo':
                    self.generar_datos_muestra()
                elif boton['id'] == 'recargar':
                    self.actualizar_datos_vista()
                    self.establecer_estado_ui(config.traductor.t("Vista_actualizada"), 'success')
                return True
        return False

    def construir_filas_datos(self):
        filas = []
        for juego, registros in self.historial.items():
            for indice, registro in enumerate(sorted(registros, key=lambda x: x['fecha']), start=1):
                filas.append([
                    juego,
                    str(indice),
                    str(registro.get('fecha', '')),
                    f"{registro.get('puntaje', 0)}%",
                    str(registro.get('aciertos', 0)),
                    str(registro.get('errores', 0))
                ])
        return filas

    def construir_resumen_juegos(self):
        resumen = []
        for juego, registros in self.historial.items():
            if not registros:
                continue
            puntajes = [registro["puntaje"] for registro in registros]
            mejoras = [registro["puntaje"] - registro.get("puntaje_antiguo", 0) for registro in registros]
            resumen.append({
                "juego": juego,
                "sesiones": len(registros),
                "promedio": round(float(np.mean(puntajes)), 1),
                "maximo": max(puntajes),
                "mejora": round(float(np.mean(mejoras)), 1),
            })
        resumen.sort(key=lambda item: item["promedio"], reverse=True)
        return resumen

    def generar_parrafos_reporte(self):
        total_registros = sum(len(registros) for registros in self.historial.values())
        resumen = self.construir_resumen_juegos()
        mejor_juego = resumen[0]["juego"] if resumen else "Sin datos"
        promedio_global = round(float(np.mean([r["puntaje"] for regs in self.historial.values() for r in regs])), 1) if self.historial else 0
        mejora_global = round(float(np.mean([
            r["puntaje"] - r.get("puntaje_antiguo", 0)
            for regs in self.historial.values() for r in regs
        ])), 1) if self.historial else 0
        nombre = self.usuario["Nickname"] if self.usuario else "Sin identificar"

        return {
            "resumen": config.traductor.t("Reporte_resumen").format(
                nombre=nombre,
                total_registros=total_registros,
                juegos=len(self.historial),
                promedio=promedio_global,
                mejora=mejora_global
            ),
            "analisis": config.traductor.t("Reporte_analisis").format(mejor_juego=mejor_juego),
            "conclusiones": config.traductor.t("Reporte_conclusiones").format(mejor_juego=mejor_juego),
        }

    def crear_estilos_pdf(self):
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name="ReportTitlePygame",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#2C3E50"),
            alignment=TA_LEFT,
            spaceAfter=10,
        ))
        styles.add(ParagraphStyle(
            name="SectionHeadingPygame",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#34495E"),
            spaceAfter=8,
            spaceBefore=8,
        ))
        styles.add(ParagraphStyle(
            name="BodyTextPygame",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.4,
            leading=15,
            alignment=TA_JUSTIFY,
            textColor=colors.HexColor("#1F2D3D"),
            spaceAfter=8,
        ))
        styles.add(ParagraphStyle(
            name="FooterMetaPygame",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#6B7A89"),
            alignment=TA_CENTER,
        ))
        return styles

    def crear_tabla_reportlab(self, filas, encabezado_color="#2C3E50"):
        tabla = Table(filas, repeatRows=1)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(encabezado_color)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D6DBDF")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("FONTSIZE", (0, 0), (-1, -1), 8.8),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        return tabla

    def crear_figura_resumen_pdf(self):
        fig = plt.figure(figsize=(11.69, 8.27), dpi=self.chart_dpi, facecolor='white')
        fig.text(0.06, 0.93, config.traductor.t("Resumen_Ejecutivo"), fontsize=22, fontweight='bold', color='#22313F')
        fig.text(0.06, 0.89, config.traductor.t("Metricas_Consolidadas"), fontsize=11, color='#4C5B68')

        metricas = self.tarjetas_estadisticas or [
            {'titulo': config.traductor.t("Sesiones_Totales"), 'valor': 0},
            {'titulo': config.traductor.t("Puntuacion_Promedio"), 'valor': '0%'},
            {'titulo': config.traductor.t("Mejor_Puntuacion"), 'valor': '0%'},
            {'titulo': config.traductor.t("Tasa_Mejora"), 'valor': '0.0%'},
            {'titulo': config.traductor.t("Juegos_Jugados"), 'valor': 0},
            {'titulo': config.traductor.t("Dias_Activos"), 'valor': 0}
        ]

        for indice, metrica in enumerate(metricas[:6]):
            columna = indice % 3
            fila = indice // 3
            x = 0.06 + columna * 0.29
            y = 0.70 - fila * 0.17
            rect = Rectangle((x, y), 0.25, 0.12, facecolor='#F8FAFC', edgecolor='#D1D9E6', linewidth=1.4,
                             transform=fig.transFigure)
            fig.add_artist(rect)
            fig.text(x + 0.02, y + 0.075, metrica['titulo'], fontsize=9, color='#6B7D8C', fontweight='bold')
            fig.text(x + 0.02, y + 0.03, str(metrica['valor']), fontsize=18, color='#22313F', fontweight='bold')

        filas = self.construir_filas_datos()
        ax_tabla = fig.add_axes([0.06, 0.08, 0.88, 0.38])
        ax_tabla.axis('off')
        vista_previa = filas[:10] if filas else [['Sin datos', '-', '-', '-', '-', '-']]
        tabla = ax_tabla.table(
            cellText=vista_previa,
            colLabels=[config.traductor.t("Juego"), config.traductor.t("Sesion"), config.traductor.t("Fecha"),
                       config.traductor.t("Puntaje"), config.traductor.t("Aciertos"), config.traductor.t("Errores")],
            loc='center',
            cellLoc='center'
        )
        tabla.auto_set_font_size(False)
        tabla.set_fontsize(9)
        tabla.scale(1, 1.5)
        for (fila, columna), celda in tabla.get_celld().items():
            celda.set_edgecolor('#D1D9E6')
            if fila == 0:
                celda.set_facecolor('#EAF2F8')
                celda.set_text_props(color='#22313F', weight='bold')
            else:
                celda.set_facecolor('white')
        return fig

    def crear_figuras_tablas_pdf(self):
        filas = self.construir_filas_datos()
        if not filas:
            return []

        figuras = []
        filas_por_pagina = 18
        columnas = [config.traductor.t("Juego"), config.traductor.t("Sesion"), config.traductor.t("Fecha"),
                    config.traductor.t("Puntaje"), config.traductor.t("Aciertos"), config.traductor.t("Errores")]

        for inicio in range(0, len(filas), filas_por_pagina):
            pagina = filas[inicio:inicio + filas_por_pagina]
            indice_pagina = inicio // filas_por_pagina + 1
            fig, ax = plt.subplots(figsize=(11.69, 8.27), dpi=self.chart_dpi)
            fig.patch.set_facecolor('white')
            ax.axis('off')
            ax.set_title(config.traductor.t("Detalle_Resultados_Pagina").format(pagina=indice_pagina), loc='left',
                         fontsize=18, fontweight='bold', color='#22313F', pad=20)
            tabla = ax.table(cellText=pagina, colLabels=columnas, loc='center', cellLoc='center')
            tabla.auto_set_font_size(False)
            tabla.set_fontsize(9)
            tabla.scale(1, 1.6)
            for (fila, columna), celda in tabla.get_celld().items():
                celda.set_edgecolor('#D1D9E6')
                if fila == 0:
                    celda.set_facecolor('#EEF4F7')
                    celda.set_text_props(weight='bold', color='#22313F')
                else:
                    celda.set_facecolor('#FFFFFF' if fila % 2 else '#FAFCFD')
            figuras.append(fig)

        return figuras

    def exportar_reporte_pdf(self):
        try:
            os.makedirs(self.directorio_reportes, exist_ok=True)
            nombre_usuario = self.usuario['Nickname'] if self.usuario else 'sin_usuario'
            nombre_archivo = self.obtener_nombre_archivo_seguro(nombre_usuario)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ruta_pdf = os.path.join(self.directorio_reportes, f'reporte_progreso_{nombre_archivo}_{timestamp}.pdf')

            doc = SimpleDocTemplate(
                ruta_pdf,
                pagesize=A4,
                leftMargin=1.8 * cm,
                rightMargin=1.8 * cm,
                topMargin=1.6 * cm,
                bottomMargin=1.5 * cm,
            )
            styles = self.crear_estilos_pdf()
            textos = self.generar_parrafos_reporte()
            story = []

            story.append(Paragraph(config.traductor.t("Titulo_Informe"), styles["ReportTitlePygame"]))
            story.append(Paragraph(
                config.traductor.t("Subtitulo_Informe").format(nombre=nombre_usuario, fecha=datetime.now().strftime('%Y-%m-%d %H:%M')),
                styles["BodyTextPygame"],
            ))

            story.append(Paragraph(config.traductor.t("Resumen_Ejecutivo"), styles["SectionHeadingPygame"]))
            story.append(Paragraph(textos["resumen"], styles["BodyTextPygame"]))

            story.append(Paragraph(config.traductor.t("Analisis"), styles["SectionHeadingPygame"]))
            story.append(Paragraph(textos["analisis"], styles["BodyTextPygame"]))

            story.append(Paragraph(config.traductor.t("Estadisticas"), styles["SectionHeadingPygame"]))
            filas_resumen = [[config.traductor.t("Indicador"), config.traductor.t("Valor")]]
            for tarjeta in self.tarjetas_estadisticas:
                filas_resumen.append([tarjeta["titulo"].replace("_", " "), str(tarjeta["valor"])])
            story.append(self.crear_tabla_reportlab(filas_resumen))
            story.append(Spacer(1, 0.35 * cm))

            story.append(Paragraph(config.traductor.t("Graficas"), styles["SectionHeadingPygame"]))
            figura_global = self.crear_figura_global_mpl(figsize=(11.4, 5.8))
            if figura_global is not None:
                buffer_global = io.BytesIO()
                figura_global.savefig(buffer_global, format="png", dpi=self.chart_dpi, bbox_inches="tight", facecolor="white")
                buffer_global.seek(0)
                story.append(Image(buffer_global, width=17.2 * cm, height=8.3 * cm))
                plt.close(figura_global)

            for juego, registros in self.historial.items():
                figura_juego = self.crear_figura_juego(juego, registros, figsize=(11.0, 5.3))
                if figura_juego is not None:
                    story.append(PageBreak())
                    story.append(Paragraph(config.traductor.t("Grafica_por_Juego").format(juego=juego), styles["SectionHeadingPygame"]))
                    buffer_juego = io.BytesIO()
                    figura_juego.savefig(buffer_juego, format="png", dpi=self.chart_dpi, bbox_inches="tight", facecolor="white")
                    buffer_juego.seek(0)
                    story.append(Image(buffer_juego, width=17.2 * cm, height=8.0 * cm))
                    plt.close(figura_juego)

            if self.ID_sesion is None:
                story.append(Paragraph(config.traductor.t("No_sesion_IA"), styles["BodyTextPygame"]))
            else:
                try:
                    ia = AI()
                    analisis_ia_dict = ia.ResultadosPDF(self.ID_sesion)
                    story.append(PageBreak())
                    story.append(Paragraph(config.traductor.t("Analisis_IA"), styles["SectionHeadingPygame"]))
                    story.append(Paragraph(config.traductor.t("Resumen_IA"), styles["SectionHeadingPygame"]))
                    story.append(Paragraph(analisis_ia_dict.get("resumen", ""), styles["BodyTextPygame"]))
                    story.append(Paragraph(config.traductor.t("Analisis_IA_Heading"), styles["SectionHeadingPygame"]))
                    story.append(Paragraph(analisis_ia_dict.get("analisis", ""), styles["BodyTextPygame"]))
                    story.append(Paragraph(config.traductor.t("Conclusiones_IA"), styles["SectionHeadingPygame"]))
                    story.append(Paragraph(analisis_ia_dict.get("conclusiones", ""), styles["BodyTextPygame"]))
                    story.append(Paragraph(config.traductor.t("Recomendaciones_IA"), styles["SectionHeadingPygame"]))
                    story.append(Paragraph(analisis_ia_dict.get("recomendaciones", ""), styles["BodyTextPygame"]))
                except Exception as e:
                    print(f"🔴 [IA] ERROR: {type(e).__name__}: {e}")
                    story.append(Paragraph(config.traductor.t("Error_IA"), styles["BodyTextPygame"]))

            story.append(PageBreak())
            story.append(Paragraph(config.traductor.t("Detalle_Resultados"), styles["SectionHeadingPygame"]))
            filas_detalle = [[config.traductor.t("Juego"), config.traductor.t("Sesion"), config.traductor.t("Fecha"),
                              config.traductor.t("Puntaje"), config.traductor.t("Aciertos"), config.traductor.t("Errores")]] + self.construir_filas_datos()[:30]
            story.append(self.crear_tabla_reportlab(filas_detalle, encabezado_color="#34495E"))
            story.append(Spacer(1, 0.35 * cm))

            story.append(Paragraph(config.traductor.t("Conclusiones"), styles["SectionHeadingPygame"]))
            story.append(Paragraph(textos["conclusiones"], styles["BodyTextPygame"]))
            story.append(Spacer(1, 0.4 * cm))
            story.append(Paragraph(config.traductor.t("Pie_Informe"), styles["FooterMetaPygame"]))

            doc.build(story)

            self.establecer_estado_ui(config.traductor.t("PDF_exportado").format(ruta=ruta_pdf), 'success')
            print(f'✅ Reporte PDF exportado: {ruta_pdf}')
            return ruta_pdf
        except Exception as e:
            print(f'❌ Error exportando PDF: {e}')
            self.establecer_estado_ui(config.traductor.t("Error_PDF"), 'error')
            return None

    def generar_datos_muestra(self, iteraciones=6):
        try:
            sesion_id = getattr(self.api, 'sesion_actual', None) or self.ID_sesion
            nombre_usuario = self.usuario['Nickname'] if self.usuario else 'UsuarioDemo'

            if not sesion_id:
                sesion_id = self.api.crear_perfil_completo(nombre_usuario)
                self.ID_sesion = sesion_id

            if not sesion_id:
                self.establecer_estado_ui(config.traductor.t("Error_sesion_demo"), 'error')
                return False

            juegos = self.api.obtener_registros('juegos')
            if not juegos:
                juegos = [
                    {'Nombre': 'Pares mágicos'},
                    {'Nombre': 'Animalia'},
                    {'Nombre': 'Encuentra y aprende'},
                    {'Nombre': 'Caza letras'},
                    {'Nombre': 'Mate-reto'}
                ]

            for juego in juegos:
                nombre_juego = juego.get('Nombre') or juego.get('nombre')
                if not nombre_juego:
                    continue

                puntaje_base = random.randint(35, 60)
                for indice in range(iteraciones):
                    puntaje = max(15, min(100, puntaje_base + indice * random.randint(4, 9) + random.randint(-6, 6)))
                    aciertos = max(1, min(10, int(round(puntaje / 10)) + random.randint(0, 2)))
                    errores = max(0, 10 - aciertos + random.randint(0, 2))
                    resultado = self.api.registrar_resultado(sesion_id, nombre_juego, puntaje, aciertos, errores)
                    if isinstance(resultado, dict) and resultado.get('error'):
                        raise ValueError(resultado.get('error'))

            self.api.sesion_actual = sesion_id
            self.ID_sesion = sesion_id
            if hasattr(self, 'barra'):
                self.barra.ID_Sesion = sesion_id
            self.actualizar_datos_vista()
            self.establecer_estado_ui(config.traductor.t("Datos_demo_cargados"), 'success')
            print(f'✅ Datos demo generados para la sesión {sesion_id}')
            return True
        except Exception as e:
            print(f'❌ Error generando datos demo: {e}')
            self.establecer_estado_ui(config.traductor.t("Error_demo"), 'error')
            return False

    def crear_graficas_modernas(self):
        graficas = {}
        print(f"🔍 Creando gráficas para {len(self.historial)} juegos")

        for juego, registros in self.historial.items():
            print(f"📈 Procesando juego: {juego} con {len(registros)} registros")
            if len(registros) < 1:
                print(f"   ⚠️  Saltando {juego}: menos de 1 registro")
                continue

            try:
                fig = self.crear_figura_juego(juego, registros, figsize=(10, 5))
                if fig is None:
                    continue

                superficie = self.crear_superficie_grafica(fig, (max(180, (self.ANCHO - 120) // 2 - 40), 190))
                graficas[juego] = {
                    "surface": superficie,
                    "registros": sorted(registros, key=lambda x: x["fecha"])
                }
                plt.close(fig)
                print(f"   ✅ Gráfica creada para {juego}")

            except Exception as e:
                print(f"   ❌ Error creando gráfica para {juego}: {e}")
                continue

        print(f"📊 Total de gráficas creadas: {len(graficas)}")
        return graficas

    def crear_grafica_global(self):
        try:
            fig = self.crear_figura_global_mpl(figsize=(12, 6))
            if fig is None:
                return None

            superficie = self.crear_superficie_grafica(fig, (self.ANCHO - 140, 240))
            plt.close(fig)
            print("✅ Gráfica global creada exitosamente")
            return {"surface": superficie}

        except Exception as e:
            print(f"❌ Error creando gráfica global: {e}")
            return None

    def crear_tarjetas_estadisticas(self):
        tarjetas = []
        if not self.historial:
            return tarjetas

        total_puntajes = []
        total_sesiones = 0
        for juego, registros in self.historial.items():
            total_puntajes.extend([r["puntaje"] for r in registros])
            total_sesiones += len(registros)

        if total_puntajes:
            promedio = int(np.mean(total_puntajes)) if total_puntajes else 0
            mejora = self.calcular_tendencia(total_puntajes) * 100 if len(total_puntajes) > 1 else 0

            tarjetas.extend([
                {"titulo": config.traductor.t("Sesiones_Totales"), "valor": total_sesiones, "color": self.COLOR_PRIMARIO},
                {"titulo": config.traductor.t("Puntuacion_Promedio"), "valor": f"{promedio}%", "color": self.COLOR_SECUNDARIO},
                {"titulo": config.traductor.t("Mejor_Puntuacion"), "valor": f"{max(total_puntajes) if total_puntajes else 0}%", "color": self.COLOR_TERCIARIO},
                {"titulo": config.traductor.t("Tasa_Mejora"), "valor": f"{mejora:+.1f}%", "color": self.COLOR_CUATERNARIO},
                {"titulo": config.traductor.t("Juegos_Jugados"), "valor": len(self.historial), "color": self.COLOR_QUINTENARIO},
                {"titulo": config.traductor.t("Dias_Activos"), "valor": len(set([r["fecha"] for regs in self.historial.values() for r in regs])), "color": self.COLOR_SEXTENARIO}
            ])

        return tarjetas

    def dibujar_tarjeta_estadistica(self, superficie, tarjeta, x, y, ancho, alto):
        rect_principal = pygame.Rect(x, y, ancho, alto)
        self.dibujar_panel_base(superficie, rect_principal, radio=18, brillo_superior=True)

        franja = pygame.Rect(x + 12, y + 12, 10, alto - 24)
        pygame.draw.rect(superficie, tarjeta["color"], franja, border_radius=8)

        globo = pygame.Rect(x + ancho - 56, y + 14, 34, 34)
        pygame.draw.ellipse(superficie, (*tarjeta["color"], 35), globo)

        titulo = config.render_text(tarjeta["titulo"], self.fuente_pequena, self.COLOR_TEXTO_CLARO)
        superficie.blit(titulo, (x + 34, y + 15))

        valor = config.render_text(str(tarjeta["valor"]), self.fuente_subtitulo, tarjeta["color"])
        superficie.blit(valor, (x + 34, y + 40))

        if config.traductor.t("Tasa_Mejora") in tarjeta["titulo"]:
            valor_num = float(str(tarjeta["valor"]).replace("%", "").replace("+", ""))
            color_flecha = self.COLOR_TERCIARIO if valor_num > 0 else self.COLOR_QUINTENARIO
            flecha = "▲" if valor_num > 0 else "▼" if valor_num < 0 else "●"
            indicador = config.render_text(flecha, self.fuente_pequena, color_flecha)
            superficie.blit(indicador, (x + ancho - 43, y + 22))

    def dibujar_cabecera_profesional(self, superficie, y_offset):
        rect_cabecera = pygame.Rect(28, y_offset + 18, self.ANCHO - 56, 190)
        self.dibujar_panel_base(superficie, rect_cabecera, color=(248, 243, 238), borde=(221, 195, 172), radio=28)

        banda = pygame.Rect(rect_cabecera.x, rect_cabecera.y, rect_cabecera.width, 74)
        pygame.draw.rect(superficie, self.COLOR_PRIMARIO, banda, border_top_left_radius=28, border_top_right_radius=28)

        adorno = pygame.Surface((rect_cabecera.width, 74), pygame.SRCALPHA)
        pygame.draw.circle(adorno, (255, 255, 255, 24), (rect_cabecera.width - 90, 24), 52)
        pygame.draw.circle(adorno, (255, 255, 255, 20), (rect_cabecera.width - 180, 60), 38)
        superficie.blit(adorno, (rect_cabecera.x, rect_cabecera.y))

        titulo = config.render_text("SIMUS.MJN", self.fuente_titulo, (255, 255, 255))
        subtitulo = config.render_text(config.traductor.t("Panel_progreso"), self.fuente_texto, (255, 255, 255))
        descripcion = config.render_text(config.traductor.t("Descripcion_panel"), self.fuente_pequena, self.COLOR_TEXTO_CLARO)

        superficie.blit(titulo, (rect_cabecera.x + 28, rect_cabecera.y + 14))
        superficie.blit(subtitulo, (rect_cabecera.x + 240, rect_cabecera.y + 26))
        superficie.blit(descripcion, (rect_cabecera.x + 30, rect_cabecera.y + 102))

        total_sesiones = sum(len(registros) for registros in self.historial.values())
        resumenes = [
            (config.traductor.t("Jugador"), self.usuario['Nickname'] if self.usuario else "Sin datos"),
            (config.traductor.t("Sesiones_Totales"), str(total_sesiones)),
            (config.traductor.t("Reportes"), config.traductor.t("PDF_graficas"))
        ]

        base_x = rect_cabecera.x + 26
        base_y = rect_cabecera.y + 128
        ancho_chip = (rect_cabecera.width - 72) // 3
        for indice, (etiqueta, valor) in enumerate(resumenes):
            chip = pygame.Rect(base_x + indice * (ancho_chip + 10), base_y, ancho_chip, 44)
            pygame.draw.rect(superficie, (255, 255, 255), chip, border_radius=14)
            pygame.draw.rect(superficie, (232, 221, 212), chip, 2, border_radius=14)
            texto_etiqueta = config.render_text(etiqueta.upper(), self.fuente_pequena, self.COLOR_TEXTO_CLARO)
            texto_valor = config.render_text(valor, self.fuente_texto, self.COLOR_TEXTO)
            superficie.blit(texto_etiqueta, (chip.x + 14, chip.y + 5))
            superficie.blit(texto_valor, (chip.x + 14, chip.y + 20))

        return y_offset + 228

    def dibujar_datos_usuario(self, superficie, y_offset):
        if not self.usuario:
            rect_usuario = pygame.Rect(50, y_offset, self.ANCHO - 100, 80)
            self.dibujar_panel_base(superficie, rect_usuario)
            mensaje = config.render_text(config.traductor.t("No_datos_usuario"), self.fuente_texto, self.COLOR_TEXTO_CLARO)
            superficie.blit(mensaje, (rect_usuario.centerx - mensaje.get_width() // 2,
                                      rect_usuario.centery - mensaje.get_height() // 2))
            return y_offset + 100

        fecha = self.usuario.get("FechaNacimiento")
        edad = config.traductor.t("N/A")
        if fecha:
            try:
                fecha_n = datetime.strptime(fecha.split("T")[0], "%Y-%m-%d")
                hoy = datetime.now()
                edad = hoy.year - fecha_n.year - ((hoy.month, hoy.day) < (fecha_n.month, fecha_n.day))
                edad = str(edad) + " " + config.traductor.t("anios")
            except:
                edad = config.traductor.t("N/A")

        rect_usuario = pygame.Rect(50, y_offset, self.ANCHO - 100, 156)
        self.dibujar_panel_base(superficie, rect_usuario, radio=20, brillo_superior=True)

        cabecera = pygame.Rect(rect_usuario.x + 16, rect_usuario.y + 16, rect_usuario.width - 32, 40)
        pygame.draw.rect(superficie, (246, 236, 228), cabecera, border_radius=14)
        etiqueta = config.render_text(config.traductor.t("Perfil_Jugador"), self.fuente_pequena, self.COLOR_PRIMARIO)
        superficie.blit(etiqueta, (cabecera.x + 14, cabecera.y + 11))

        avatar = pygame.Rect(rect_usuario.x + 22, rect_usuario.y + 72, 82, 62)
        pygame.draw.rect(superficie, (250, 244, 239), avatar, border_radius=18)
        pygame.draw.rect(superficie, self.COLOR_SECUNDARIO, avatar, 2, border_radius=18)
        inicial = (self.usuario['Nickname'][:1] if self.usuario.get('Nickname') else '?').upper()
        letra = config.render_text(inicial, self.fuente_titulo, self.COLOR_PRIMARIO)
        superficie.blit(letra, (avatar.centerx - letra.get_width() // 2, avatar.centery - letra.get_height() // 2 - 2))

        total_sesiones = sum(len(registros) for registros in self.historial.values())
        items = [
            (config.traductor.t("Nombre"), self.usuario['Nickname']),
            (config.traductor.t("Edad"), edad),
            (config.traductor.t("Sesiones"), str(total_sesiones)),
            (config.traductor.t("Juegos"), str(len(self.historial)))
        ]
        posiciones = [
            (rect_usuario.x + 128, rect_usuario.y + 74),
            (rect_usuario.x + 128, rect_usuario.y + 106),
            (rect_usuario.x + rect_usuario.width // 2 + 10, rect_usuario.y + 74),
            (rect_usuario.x + rect_usuario.width // 2 + 10, rect_usuario.y + 106)
        ]

        for (titulo_item, valor), (pos_x, pos_y) in zip(items, posiciones):
            etiqueta_item = config.render_text(titulo_item.upper(), self.fuente_pequena, self.COLOR_TEXTO_CLARO)
            valor_item = config.render_text(str(valor), self.fuente_texto, self.COLOR_TEXTO)
            superficie.blit(etiqueta_item, (pos_x, pos_y))
            superficie.blit(valor_item, (pos_x, pos_y + 14))

        return y_offset + 176

    def dibujar_estadisticas_globales(self, superficie, y_offset):
        if not self.tarjetas_estadisticas:
            rect_mensaje = pygame.Rect(50, y_offset, self.ANCHO - 100, 100)
            self.dibujar_panel_base(superficie, rect_mensaje)
            mensaje = config.render_text(config.traductor.t("No_datos_estadisticas"), self.fuente_texto, self.COLOR_TEXTO_CLARO)
            superficie.blit(mensaje, (rect_mensaje.centerx - mensaje.get_width() // 2,
                                      rect_mensaje.centery - mensaje.get_height() // 2))
            return y_offset + 120

        y_offset = self.dibujar_titulo_seccion(
            superficie,
            config.traductor.t("Metricas_Globales"),
            y_offset,
            config.traductor.t("Subtitulo_Metricas")
        )

        ancho_tarjeta = (self.ANCHO - 140) // 3
        alto_tarjeta = 104

        for i, tarjeta in enumerate(self.tarjetas_estadisticas):
            fila = i // 3
            columna = i % 3
            x = 50 + columna * (ancho_tarjeta + 20)
            y = y_offset + fila * (alto_tarjeta + 15)

            self.dibujar_tarjeta_estadistica(superficie, tarjeta, x, y, ancho_tarjeta, alto_tarjeta)

        filas_totales = (len(self.tarjetas_estadisticas) + 2) // 3
        return y_offset + filas_totales * (alto_tarjeta + 20)

    def dibujar_grafica_global(self, superficie, y_offset):
        if not self.grafica_global:
            rect_mensaje = pygame.Rect(50, y_offset, self.ANCHO - 100, 150)
            self.dibujar_panel_base(superficie, rect_mensaje)
            mensaje = config.render_text(config.traductor.t("No_datos_grafica_global"), self.fuente_texto, self.COLOR_TEXTO_CLARO)
            superficie.blit(mensaje, (rect_mensaje.centerx - mensaje.get_width() // 2,
                                      rect_mensaje.centery - mensaje.get_height() // 2))
            return y_offset + 170

        y_offset = self.dibujar_titulo_seccion(
            superficie,
            config.traductor.t("Progreso_General"),
            y_offset,
            config.traductor.t("Subtitulo_Progreso")
        )

        rect_grafica = pygame.Rect(50, y_offset, self.ANCHO - 100, 300)
        self.dibujar_panel_base(superficie, rect_grafica, radio=20)

        etiqueta = config.render_text(config.traductor.t("Evolucion_Global"), self.fuente_pequena, self.COLOR_TEXTO_CLARO)
        superficie.blit(etiqueta, (rect_grafica.x + 22, rect_grafica.y + 14))

        surf_grafica = self.grafica_global["surface"]
        superficie.blit(surf_grafica, (rect_grafica.x + 20, rect_grafica.y + 44))

        return y_offset + 320

    def dibujar_graficas_por_juego(self, superficie, y_offset):
        if not self.graficas:
            rect_mensaje = pygame.Rect(50, y_offset, self.ANCHO - 100, 150)
            self.dibujar_panel_base(superficie, rect_mensaje)
            mensaje = config.render_text(config.traductor.t("Mensaje_inicio_juegos"), self.fuente_subtitulo, self.COLOR_TEXTO_CLARO)
            instruccion = config.render_text(config.traductor.t("Mensaje_espera_datos"), self.fuente_texto, self.COLOR_TEXTO_CLARO)
            superficie.blit(mensaje, (rect_mensaje.centerx - mensaje.get_width() // 2, rect_mensaje.centery - 20))
            superficie.blit(instruccion, (rect_mensaje.centerx - instruccion.get_width() // 2, rect_mensaje.centery + 20))
            return y_offset + 180

        y_offset = self.dibujar_titulo_seccion(
            superficie,
            config.traductor.t("Progreso_por_Juego"),
            y_offset,
            config.traductor.t("Subtitulo_Comparativa")
        )

        juegos_lista = list(self.graficas.keys())
        for i, juego in enumerate(juegos_lista):
            fila = i // 2
            columna = i % 2

            x = 50 + columna * ((self.ANCHO - 120) // 2)
            y = y_offset + fila * 280

            rect_grafica = pygame.Rect(x, y, (self.ANCHO - 120) // 2, 250)
            self.dibujar_panel_base(superficie, rect_grafica, radio=18)

            chip = pygame.Rect(x + 16, y + 12, 122, 24)
            pygame.draw.rect(superficie, (246, 236, 228), chip, border_radius=12)
            pygame.draw.rect(superficie, self.obtener_color_juego(juego), chip, 2, border_radius=12)

            surf_grafica = self.graficas[juego]["surface"]
            superficie.blit(surf_grafica, (x + 20, y + 50))

            titulo_juego = config.render_text(juego, self.fuente_texto, self.COLOR_TEXTO)
            superficie.blit(titulo_juego, (x + 152, y + 13))

            if juego in self.historial and self.historial[juego]:
                ultimo_puntaje = self.historial[juego][-1]["puntaje"]
                sesiones = len(self.historial[juego])
                stats = config.render_text(config.traductor.t("Ultimo_sesion").format(ultimo=ultimo_puntaje, sesiones=sesiones), self.fuente_pequena, self.COLOR_TEXTO_CLARO)
                superficie.blit(stats, (x + 20, y + 220))

            texto_chip = config.render_text(config.traductor.t("JUEGO"), self.fuente_pequena, self.obtener_color_juego(juego))
            superficie.blit(texto_chip, (chip.x + 34, chip.y + 4))

        filas_totales = (len(juegos_lista) + 1) // 2
        return y_offset + filas_totales * 280 + 20

    def dibujar_analisis_categorias(self, superficie, y_offset):
        y_offset = self.dibujar_titulo_seccion(
            superficie,
            config.traductor.t("Analisis_Competencias"),
            y_offset,
            config.traductor.t("Subtitulo_Competencias")
        )

        rect_analisis = pygame.Rect(50, y_offset, self.ANCHO - 100, 400)
        self.dibujar_panel_base(superficie, rect_analisis, radio=20)

        categorias = [
            {"nombre": config.traductor.t("Movilidad_motriz_fina"), "juegos": ["Pares mágicos", "Animalia"], "color": self.COLOR_PRIMARIO},
            {"nombre": config.traductor.t("Lenguaje"), "juegos": ["Encuentra y aprende", "Caza letras"], "color": self.COLOR_TERCIARIO},
            {"nombre": config.traductor.t("Cognitivo_matematico"), "juegos": ["Mate-reto"], "color": self.COLOR_CUATERNARIO}
        ]

        for i, categoria in enumerate(categorias):
            columna = i % 2
            fila = i // 2

            x = rect_analisis.x + 20 + columna * ((rect_analisis.width - 40) // 2)
            y = rect_analisis.y + 20 + fila * 90

            rect_categoria = pygame.Rect(x, y, (rect_analisis.width - 40) // 2 - 10, 80)
            self.dibujar_panel_base(superficie, rect_categoria, color=(252, 252, 252), borde=categoria["color"], radio=14, sombra=False)
            barra = pygame.Rect(rect_categoria.x + 10, rect_categoria.y + 10, 8, rect_categoria.height - 20)
            pygame.draw.rect(superficie, categoria["color"], barra, border_radius=8)

            nombre = config.render_text(categoria["nombre"], self.fuente_texto, self.COLOR_TEXTO)
            superficie.blit(nombre, (x + 28, y + 10))

            juegos_texto = config.render_text(", ".join(categoria["juegos"]), self.fuente_pequena, self.COLOR_TEXTO_CLARO)
            superficie.blit(juegos_texto, (x + 28, y + 35))

            tendencia = self.analizar_tendencia_categoria(categoria["juegos"])
            analisis_texto = config.render_text(tendencia, self.fuente_pequena, self.COLOR_TEXTO)
            superficie.blit(analisis_texto, (x + 28, y + 55))

        try:
            ia = AI()
            analisis_IA = ia.Resultados(self.ID_sesion)

            y_analisis = rect_analisis.y + 200
            cinta = pygame.Rect(rect_analisis.x + 20, y_analisis - 4, rect_analisis.width - 40, 34)
            pygame.draw.rect(superficie, (246, 236, 228), cinta, border_radius=12)
            recomendacion_titulo = config.render_text(config.traductor.t("Recomendaciones_personalizadas"), self.fuente_texto, self.COLOR_PRIMARIO)
            superficie.blit(recomendacion_titulo, (rect_analisis.x + 34, y_analisis + 1))

            palabras = analisis_IA.split(' ')
            lineas = []
            linea_actual = ""
            ancho_maximo = rect_analisis.width - 40

            for palabra in palabras:
                prueba_linea = f"{linea_actual} {palabra}".strip()
                if self.fuente_texto.size(prueba_linea)[0] < ancho_maximo:
                    linea_actual = prueba_linea
                else:
                    lineas.append(linea_actual)
                    linea_actual = palabra

            if linea_actual:
                lineas.append(linea_actual)

            for i, linea in enumerate(lineas):
                if i < 8:
                    texto = config.render_text(linea, self.fuente_texto, self.COLOR_TEXTO)
                    superficie.blit(texto, (rect_analisis.x + 24, y_analisis + 44 + i * 25))

        except Exception as e:
            mensaje_error = config.render_text(config.traductor.t("Error_IA_temporal"), self.fuente_pequena, (150, 50, 50))
            superficie.blit(mensaje_error, (rect_analisis.x + 34, y_analisis + 44))
            print(f"Error en IA: {e}")
        return y_offset + 430

    def dibujar_historial_resumido(self, superficie, y_offset):
        y_offset = self.dibujar_titulo_seccion(
            superficie,
            config.traductor.t("Historial_Completo"),
            y_offset,
            config.traductor.t("Subtitulo_Historial")
        )

        rect_historial = pygame.Rect(50, y_offset, self.ANCHO - 100, 350)
        self.dibujar_panel_base(superficie, rect_historial, radio=20)

        columnas = [
            (config.traductor.t("Juego"), rect_historial.x + 18),
            (config.traductor.t("Sesion"), rect_historial.x + 290),
            (config.traductor.t("Actual"), rect_historial.x + 400),
            (config.traductor.t("Mejora"), rect_historial.x + 520),
            (config.traductor.t("Aciertos"), rect_historial.x + 650),
            (config.traductor.t("Errores"), rect_historial.x + 790),
        ]

        header = pygame.Rect(rect_historial.x + 14, rect_historial.y + 16, rect_historial.width - 28, 34)
        pygame.draw.rect(superficie, (246, 248, 250), header, border_radius=12)
        for titulo, posicion in columnas:
            texto = config.render_text(titulo.upper(), self.fuente_pequena, self.COLOR_SECUNDARIO)
            superficie.blit(texto, (posicion, header.y + 9))

        filas = []
        for juego, registros in self.historial.items():
            for indice, registro in enumerate(sorted(registros, key=lambda x: x["fecha"], reverse=True), start=1):
                filas.append({
                    "juego": juego,
                    "sesion": indice,
                    "actual": registro["puntaje"],
                    "mejora": registro["puntaje"] - registro.get("puntaje_antiguo", 0),
                    "aciertos": registro.get("aciertos", 0),
                    "errores": registro.get("errores", 0),
                })

        filas = filas[:self.filas_historial_visibles]
        for indice, fila in enumerate(filas):
            y_fila = header.y + 42 + indice * 20
            if indice % 2 == 0:
                banda = pygame.Rect(rect_historial.x + 14, y_fila - 2, rect_historial.width - 28, 20)
                pygame.draw.rect(superficie, (248, 250, 252), banda, border_radius=8)

            celdas = [
                (fila["juego"], columnas[0][1]),
                (str(fila["sesion"]), columnas[1][1]),
                (f"{fila['actual']}%", columnas[2][1]),
                (f"{fila['mejora']:+d}", columnas[3][1]),
                (str(fila["aciertos"]), columnas[4][1]),
                (str(fila["errores"]), columnas[5][1]),
            ]

            for valor, posicion in celdas:
                texto = config.render_text(valor, self.fuente_pequena, self.COLOR_TEXTO)
                superficie.blit(texto, (posicion, y_fila))

        resumen_juegos = self.construir_resumen_juegos()[:5]
        y_stats = rect_historial.y + 210
        subtitulo = config.render_text(config.traductor.t("Estadisticas_Resumidas"), self.fuente_texto, self.COLOR_PRIMARIO)
        superficie.blit(subtitulo, (rect_historial.x + 18, y_stats))

        for indice, fila in enumerate(resumen_juegos):
            card_y = y_stats + 34 + indice * 20
            texto = config.render_text(
                f"{fila['juego']}  |  {config.traductor.t('promedio')} {fila['promedio']}%  |  {config.traductor.t('max')} {fila['maximo']}%  |  {config.traductor.t('mejora')} {fila['mejora']:+.1f}",
                self.fuente_pequena,
                self.COLOR_TEXTO,
            )
            superficie.blit(texto, (rect_historial.x + 18, card_y))

        pie = config.render_text(
            config.traductor.t("Mostrando_registros").format(mostrados=len(filas)),
            self.fuente_pequena,
            self.COLOR_TEXTO_CLARO,
        )
        superficie.blit(pie, (rect_historial.x + 18, rect_historial.bottom - 24))

        return y_offset + 372

    def analizar_tendencia_categoria(self, juegos_categoria):
        puntajes = []
        for juego in juegos_categoria:
            if juego in self.historial:
                puntajes.extend([r["puntaje"] for r in self.historial[juego]])

        if len(puntajes) < 2:
            return config.traductor.t("Datos_insuficientes")

        tendencia = self.calcular_tendencia(puntajes)

        if tendencia > 0.1:
            return config.traductor.t("Tendencia_positiva")
        elif tendencia < -0.1:
            return config.traductor.t("Necesita_atencion")
        else:
            return config.traductor.t("Estabilidad")

    def generar_analisis_mejorado(self):
        if not self.historial:
            return config.traductor.t("No_datos_juego_inicio")
        total_registros = sum(len(registros) for registros in self.historial.values())
        if total_registros == 0:
            return config.traductor.t("Bienvenido_comienza_jugar")
        if total_registros < 3:
            return config.traductor.t("Pocas_sesiones").format(sesiones=total_registros)

        categorias = self.categorizar_juegos()
        analisis = []

        for categoria, juegos in categorias.items():
            if not juegos:
                continue

            puntajes_categoria = []
            for juego in juegos:
                if juego in self.historial:
                    ultimos_puntajes = [r["puntaje"] for r in self.historial[juego][-3:]]
                    puntajes_categoria.extend(ultimos_puntajes)

            if not puntajes_categoria:
                continue

            tendencia = self.calcular_tendencia(puntajes_categoria)

            # Usar traducciones dinámicas
            if categoria == config.traductor.t("Movilidad_motriz_fina"):
                if tendencia > 0.1:
                    analisis.append(config.traductor.t("Analisis_motriz_mejora").format(juego_cat=categoria, juegos=", ".join(juegos), nombre=self.usuario['Nickname']))
                elif tendencia < -0.1:
                    analisis.append(config.traductor.t("Analisis_motriz_baja").format(juego_cat=categoria))
                else:
                    analisis.append(config.traductor.t("Analisis_motriz_estable").format(juego_cat=categoria))
            elif categoria in (config.traductor.t("Lenguaje"), "Lenguaje"):
                if tendencia > 0.1:
                    analisis.append(config.traductor.t("Analisis_lenguaje_mejora").format(juego_cat=categoria, juegos=", ".join(juegos), nombre=self.usuario['Nickname']))
                elif tendencia < -0.1:
                    analisis.append(config.traductor.t("Analisis_lenguaje_baja").format(juego_cat=categoria))
                else:
                    analisis.append(config.traductor.t("Analisis_lenguaje_estable").format(juego_cat=categoria))
            elif categoria in (config.traductor.t("Cognitivo_matematico"), "Cognitivo-matemático"):
                if tendencia > 0.1:
                    analisis.append(config.traductor.t("Analisis_cognitivo_mejora").format(juego_cat=categoria, juegos=", ".join(juegos)))
                elif tendencia < -0.1:
                    analisis.append(config.traductor.t("Analisis_cognitivo_baja").format(juego_cat=categoria))
                else:
                    analisis.append(config.traductor.t("Analisis_cognitivo_estable").format(juego_cat=categoria))
            elif categoria == config.traductor.t("Creativo_artistico"):
                if tendencia > 0.1:
                    analisis.append(config.traductor.t("Analisis_creativo_mejora").format(juego_cat=categoria, juegos=", ".join(juegos), nombre=self.usuario['Nickname']))
                elif tendencia < -0.1:
                    analisis.append(config.traductor.t("Analisis_creativo_baja").format(juego_cat=categoria))
                else:
                    analisis.append(config.traductor.t("Analisis_creativo_estable").format(juego_cat=categoria))

        if analisis:
            total_puntajes = []
            for juego_registros in self.historial.values():
                total_puntajes.extend([r["puntaje"] for r in juego_registros])

            if total_puntajes:
                tendencia_general = self.calcular_tendencia(total_puntajes)
                if tendencia_general > 0.15:
                    analisis.append(config.traductor.t("Recomendacion_progreso_muy_positivo"))
                elif tendencia_general > 0:
                    analisis.append(config.traductor.t("Recomendacion_avance_constante"))
                elif tendencia_general < -0.1:
                    analisis.append(config.traductor.t("Recomendacion_disminucion"))
                else:
                    analisis.append(config.traductor.t("Recomendacion_estable"))

        return " ".join(analisis) if analisis else config.traductor.t("Analisis_datos_insuficientes")

    def categorizar_juegos(self):
        categorias = {
            config.traductor.t("Movilidad_motriz_fina"): ["Pares mágicos", "Animalia"],
            config.traductor.t("Lenguaje"): ["Encuentra y aprende", "Caza letras"],
            config.traductor.t("Cognitivo_matematico"): ["Mate-reto"]
        }

        juegos_categorizados = {categoria: [] for categoria in categorias}
        for juego in self.historial.keys():
            for categoria, juegos in categorias.items():
                if juego in juegos:
                    juegos_categorizados[categoria].append(juego)
                    break
            else:
                juegos_categorizados[config.traductor.t("Otros")] = juegos_categorizados.get(config.traductor.t("Otros"), []) + [juego]

        return juegos_categorizados

    def calcular_tendencia(self, datos):
        if len(datos) < 2:
            return 0
        x = np.arange(len(datos))
        y = np.array(datos)
        coeficiente = np.polyfit(x, y, 1)[0]
        promedio = np.mean(y)
        if promedio == 0:
            return 0
        return coeficiente / promedio

    def obtener_datos_usuario(self):
        id_sesion = getattr(self, "ID_sesion", None) or getattr(self.api, "sesion_actual", None)
        if not id_sesion:
            print("⚠️ No se pudo determinar el ID de sesión actual.")
            return None

        usuario_id = self.api.obtenerID_usuario(id_sesion)
        if not usuario_id:
            print(f"⚠️ No se encontró usuario asociado a la sesión {id_sesion}")
            return None

        usuarios = self.api.obtener_registros("usuarios")
        usuario = next((u for u in usuarios if int(u.get("ID_usuario")) == int(usuario_id)), None)
        if not usuario:
            print(f"⚠️ No se encontraron datos para el usuario {usuario_id}")
            return None

        datos_usuario = {
            "ID_usuario": usuario.get("ID_usuario"),
            "Nickname": usuario.get("Nickname"),
            "FechaNacimiento": usuario.get("FechaNacimiento"),
        }
        print(f"✅ Usuario obtenido correctamente: {datos_usuario}")
        return datos_usuario

    def obtener_historial_usuario(self):
        if not self.usuario:
            return {}

        usuario_id = self.usuario["ID_usuario"]
        historial_completo = self.api.obtener_historial_resultados()
        historial_organizado = {}

        for registro in historial_completo:
            sesion_id = registro.get("ID_sesion")
            if sesion_id:
                sesion_usuario = self.api.obtenerID_usuario(sesion_id)
                if sesion_usuario == usuario_id:
                    nombre_juego = (
                            registro.get("Nombre_juego")
                            or registro.get("nombre_juego")
                            or "Desconocido"
                    )

                    if nombre_juego not in historial_organizado:
                        historial_organizado[nombre_juego] = []

                    historial_organizado[nombre_juego].append({
                        "fecha": registro.get("Fecha", datetime.now().strftime("%Y-%m-%d")),
                        "puntaje": registro.get("puntaje_nuevo", 0),
                        "aciertos": registro.get("Nuevo_Acierto", 0),
                        "errores": registro.get("Nuevo_error", 0),
                        "puntaje_antiguo": registro.get("puntaje_antiguo", 0),
                        "aciertos_antiguo": registro.get("Aciertos_antiguo", 0),
                        "errores_antiguo": registro.get("Errores_antiguo", 0)
                    })

        print(f"🧩 Registros totales recibidos: {len(historial_completo)}")
        print(f"🧩 Registros filtrados para el usuario {usuario_id}: {sum(len(v) for v in historial_organizado.values())}")
        return historial_organizado

    def obtener_nombre_juego(self, juego_id):
        juegos = self.api.obtener_registros("juegos")
        for juego in juegos:
            if juego.get("ID_juego") == juego_id:
                return juego.get("Nombre", f"Juego {juego_id}")
        return f"Juego {juego_id}"

    def dibujar_pie_historico(self, superficie, y_offset):
        tamaño_fuente_pie = max(14, int(self.ALTO * 0.018))
        fuente_pie = pygame.font.SysFont("Arial", tamaño_fuente_pie)

        historia = config.traductor.t("Historia_proyecto").split('|')  # Suponemos que la clave da el texto con saltos de línea o separadores
        # Para simplificar, usaremos una lista fija de párrafos con claves de traducción
        lineas_historia = [
            config.traductor.t("Historia_linea1"),
            config.traductor.t("Historia_linea2"),
            config.traductor.t("Historia_linea3"),
            config.traductor.t("Historia_linea4"),
            config.traductor.t("Historia_linea5"),
            config.traductor.t("Historia_linea6"),
            config.traductor.t("Historia_linea7"),
            config.traductor.t("Historia_linea8")
        ]

        rect_pie = pygame.Rect(50, y_offset, self.ANCHO - 100, 214)
        self.dibujar_panel_base(superficie, rect_pie, color=(242, 235, 229), borde=(216, 188, 164), radio=20)

        cinta = pygame.Rect(rect_pie.x, rect_pie.y, rect_pie.width, 46)
        pygame.draw.rect(superficie, self.COLOR_PRIMARIO, cinta, border_top_left_radius=20, border_top_right_radius=20)
        titulo = config.render_text(config.traductor.t("Historia_proyecto_titulo"), self.fuente_texto, (255, 255, 255))
        superficie.blit(titulo, (rect_pie.x + 20, rect_pie.y + 10))

        for i, linea in enumerate(lineas_historia):
            texto = fuente_pie.render(linea, True, self.COLOR_TEXTO)
            superficie.blit(texto, (rect_pie.x + 20, rect_pie.y + 62 + i * 18))

        version_final = fuente_pie.render(config.traductor.t("Version_final"), True, self.COLOR_PRIMARIO)
        superficie.blit(version_final, (rect_pie.centerx - version_final.get_width() // 2, rect_pie.y + 184))

        return y_offset + 234

    def ejecutar(self):
        reloj = pygame.time.Clock()
        ejecutando = True

        # Obtener la pantalla real (puede haber cambiado de tamaño en otra pantalla)
        self.pantalla = pygame.display.get_surface()
        if self.pantalla is None:
            self.pantalla = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.ANCHO, self.ALTO = self.pantalla.get_size()

        if self.camara:
            self.camara.reanudar_cursor()
            pygame.time.delay(500)

        while ejecutando:
            # Obtener entrada
            try:
                if self.camara:
                    cursor_x, cursor_y, clic_camara = self.camara.obtener_posicion_y_clic()
                    clic_activo = clic_camara and not self.control_clic
                    self.control_clic = clic_camara
                else:
                    cursor_x, cursor_y = pygame.mouse.get_pos()
                    clic_mouse = pygame.mouse.get_pressed()[0]
                    clic_activo = clic_mouse and not self.control_clic
                    self.control_clic = clic_mouse
            except:
                cursor_x, cursor_y = pygame.mouse.get_pos()
                clic_mouse = pygame.mouse.get_pressed()[0]
                clic_activo = clic_mouse and not self.control_clic
                self.control_clic = clic_mouse

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    ejecutando = False
                elif evento.type == pygame.KEYDOWN:
                    acc = procesar_atajos_globales(evento, self.camara)
                    if acc == "tutorial":
                        self.camara.pausar_cursor()
                        return "instrucciones"
                    if acc == "recalibrar":
                        aplicar_atajo_camara("recalibrar", self.camara)
                    elif acc == "toggle_pausa":
                        aplicar_atajo_camara("toggle_pausa", self.camara)
                    elif evento.key == pygame.K_ESCAPE:
                        ejecutando = False
                    elif evento.key == pygame.K_DOWN:
                        self.desplazamiento = min(self.desplazamiento + self.velocidad_scroll,
                                                  max(0, self.altura_total_contenido - self.ALTO))
                    elif evento.key == pygame.K_UP:
                        self.desplazamiento = max(0, self.desplazamiento - self.velocidad_scroll)
                    elif evento.key == pygame.K_c:
                        if self.camara:
                            self.camara.calibrar()
                    elif evento.key == pygame.K_e:
                        self.exportar_reporte_pdf()
                    elif evento.key == pygame.K_d:
                        self.generar_datos_muestra()
                    elif evento.key == pygame.K_r:
                        self.actualizar_datos_vista()
                        self.establecer_estado_ui(config.traductor.t("Vista_actualizada"), 'success')
                elif evento.type == pygame.MOUSEWHEEL:
                    self.desplazamiento = max(0, min(self.desplazamiento - evento.y * self.velocidad_scroll,
                                                     max(0, self.altura_total_contenido - self.ALTO)))

            # Dibujar fondo
            if self.fondo:
                self.pantalla.blit(self.fondo, (0, 0))
            else:
                self.pantalla.fill(self.COLOR_FONDO)

            # Crear superficie contenido
            superficie_contenido = pygame.Surface((self.ANCHO, self.altura_total_contenido))
            superficie_contenido.fill(self.COLOR_FONDO)

            y_actual = 0
            y_actual = self.dibujar_cabecera_profesional(superficie_contenido, y_actual)
            y_actual = self.dibujar_datos_usuario(superficie_contenido, y_actual)
            y_actual = self.dibujar_estadisticas_globales(superficie_contenido, y_actual)
            y_actual = self.dibujar_grafica_global(superficie_contenido, y_actual)
            y_actual = self.dibujar_graficas_por_juego(superficie_contenido, y_actual)
            y_actual = self.dibujar_analisis_categorias(superficie_contenido, y_actual)
            y_actual = self.dibujar_historial_resumido(superficie_contenido, y_actual)
            y_actual = self.dibujar_pie_historico(superficie_contenido, y_actual)

            if self.desplazamiento > self.altura_total_contenido - self.ALTO:
                self.desplazamiento = max(0, self.altura_total_contenido - self.ALTO)
            area_visible = pygame.Rect(0, int(self.desplazamiento), self.ANCHO, self.ALTO)
            self.pantalla.blit(superficie_contenido, (0, 0), area_visible)

            self.dibujar_panel_acciones(self.pantalla, (cursor_x, cursor_y))
            accion_consumida = self.manejar_acciones_ui((cursor_x, cursor_y), clic_activo)
            self.dibujar_estado_ui(self.pantalla)

            if self.altura_total_contenido > self.ALTO:
                altura_barra = int((self.ALTO / self.altura_total_contenido) * self.ALTO * 0.8)
                posicion_barra = int((self.desplazamiento / self.altura_total_contenido) * self.ALTO * 0.8)
                rect_barra = pygame.Rect(self.ANCHO - 20, 50 + posicion_barra, 10, altura_barra)
                pygame.draw.rect(self.pantalla, self.COLOR_PRIMARIO, rect_barra, border_radius=5)

            self.barra.actualizar_visibilidad((cursor_x, cursor_y), self.ALTO)
            self.barra.dibujar(self.pantalla, (cursor_x, cursor_y))
            destino = self.barra.manejar_clic((cursor_x, cursor_y), clic_activo and not accion_consumida)

            if destino:
                if self.camara:
                    self.camara.pausar_cursor()
                return destino

            try:
                if self.camara:
                    dibujar_cursor_unificado(self.pantalla, cursor_x, cursor_y, modo_ocular=True, ancho=self.ANCHO, alto=self.ALTO)
                else:
                    dibujar_cursor_unificado(self.pantalla, cursor_x, cursor_y, modo_ocular=True, ancho=self.ANCHO, alto=self.ALTO)
            except Exception as e:
                print(f"Error dibujando cursor: {e}")
                pygame.draw.circle(self.pantalla, (255, 0, 0), (cursor_x, cursor_y), 10, 2)

            pygame.display.flip()
            reloj.tick(60)

        if self.camara:
            self.camara.pausar_cursor()
        return "menu_principal"


if __name__ == "__main__":
    pygame.init()
    info = InformacionJugador()
    info.ejecutar()
    pygame.quit()