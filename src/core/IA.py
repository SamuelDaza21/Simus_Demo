import re
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from groq import Groq
from api.APICliente import *
from collections import defaultdict
from deep_translator import GoogleTranslator

import core.config as config

_GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
Cliente_IA = Groq(api_key=_GROQ_API_KEY) if _GROQ_API_KEY else None


class AI:
    def Obtener_Datos(self, sesion_id):
        registros = APICliente().obtener_historial_resultados(sesion_id)
        return registros

    def agrupar_datos(self, registros):
        juegos = defaultdict(list)
        for r in registros:
            juegos[r["Nombre_juego"]].append(r)
        return juegos

    def analizar_progreso(self, juegos):
        resumen = ""
        for juego, datos in juegos.items():
            primero = datos[0]["puntaje_nuevo"]
            ultimo = datos[-1]["puntaje_nuevo"]
            diferencia = ultimo - primero
            resumen += f"""
            juego:{juego}
            Inicio:{primero}
            Final:{ultimo}
            Cambio:{diferencia}
            --------------------
            """
        return resumen

    def _get_idioma(self, idioma=None):
        if idioma:
            return idioma
        try:
            return config.traductor.get_current_language()
        except:
            return "es"

    # ---------- Genera análisis en español (con marcadores) ----------
    def _generar_analisis_es(self, registros, sesion_id, tipo="normal"):
        """Genera el análisis en español (sin traducción)."""
        self.Usuario = APICliente().Obterner_Usuario(APICliente().obtenerID_usuario(sesion_id))
        U = self.Usuario
        resumen = self.analizar_progreso(self.agrupar_datos(registros))

        if tipo == "pdf":
            prompt = f"""Eres un analista de rendimiento en videojuegos educativos. 
Debes responder SIEMPRE en ESPAÑOL, usando exactamente los siguientes títulos de sección:

### RESUMEN EJECUTIVO
(contenido breve)

### ANÁLISIS
(análisis detallado, sin incluir resumen ejecutivo ni conclusiones)

### CONCLUSIONES
(conclusiones claras)

### RECOMENDACIONES
(recomendaciones prácticas)

Nombre del usuario: {U}

Datos de rendimiento:
{resumen}

IMPORTANTE:
- No inventes datos médicos.
- Basarte solo en la información dada.
- Sé claro, profesional y motivador.
- No incluyas otros títulos ni texto adicional fuera de estas cuatro secciones.
- No uses inglés. Responde únicamente en español.
"""
        else:
            prompt = f"""Historial de rendimiento del Usuario:

Eres un analista de rendimiento cognitivo. Debes responder SIEMPRE en ESPAÑOL.
Analiza el rendimiento y progreso del usuario basado en los siguientes registros:
Nombre: {U}
Registros: {resumen}
Genera un análisis general del progreso del Usuario, destacando mejoras, debilidades y recomendaciones.
            Tarea:
            -Analiza el progreso del Usuario
            -Indica si ha mejorado o empeorado
            -Detecta debilidades (errores)
            -Da recomendaciones claras para mejorar, teniendo en cuenta que es un paciente de patologia de Neurodegeneracion asociada al Pantotenato quinasa
            Responde de forma:
            -Clara
            -Motivadora
            -Analiza y compara todos los datos del Usuario para llegar a un resumen completo y general de los resultados del Usuario
            -Personalizada usando el nombre del usuario
            -no des diagnosticos medicos
            -no se califique si esta bien o mal (todos los resultados son buenos, solo hay que fortalecer habilidades)
IMPORTANTE:
-Detecta mejoras reales
-Detecta caidas fuertes de rendimiento
-Explica posibles causas (fatiga, falta de concentracion, etc.)
-Brinda recomendaciones claras
NO HAGAS UN ANALISIS SUPERFICIAL
Responde únicamente en español."""

        try:
            if Cliente_IA is None:
                return config.traductor.t("Error_analisis_ia")
            contacto_ia = Cliente_IA.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )
            analisis = contacto_ia.choices[0].message.content
            analisis = re.sub(r"<think>.*?</think>", "", analisis, flags=re.DOTALL)
            analisis = analisis.replace(".", ".\n")
            carpeta = "../reportes"
            os.makedirs(carpeta, exist_ok=True)
            ruta = os.path.join(carpeta, f"analisis_{U}_{tipo}.txt")
            with open(ruta, "w", encoding="utf-8") as archivo:
                archivo.write(analisis)
            return analisis
        except Exception as e:
            try:
                return config.traductor.t("Error_analisis_ia")
            except:
                return f"Error al generar analisis: {e}"

    # ---------- Limpieza de marcadores internos ----------
    def _limpiar_marcadores(self, texto):
        """Elimina líneas que contengan '###' o títulos de sección repetidos."""
        # Eliminar líneas que empiecen por ### (con o sin espacios)
        texto = re.sub(r'^\s*###.*$', '', texto, flags=re.MULTILINE)
        # Eliminar títulos de sección comunes (en español e inglés) que puedan quedar sueltos
        texto = re.sub(
            r'^\s*(RESUMEN EJECUTIVO|EXECUTIVE SUMMARY|ANÁLISIS|ANALYSIS|CONCLUSIONES|CONCLUSIONS|RECOMENDACIONES|RECOMMENDATIONS)\s*:?\s*$',
            '', texto, flags=re.MULTILINE | re.IGNORECASE)
        # Reemplazar múltiples saltos de línea por dos
        texto = re.sub(r'\n\s*\n', '\n\n', texto)
        # Convertir saltos de línea a <br/> para que ReportLab los muestre
        texto = texto.replace('\n', '<br/>')
        return texto.strip()

    def dividir_secciones(self, analisis_texto):
        """
        Recibe el análisis (puede ser en español o inglés) y devuelve un diccionario
        con las cuatro secciones: resumen, analisis, conclusiones, recomendaciones.
        Busca tanto títulos en español como en inglés.
        """
        # Patrones flexibles (español e inglés)
        patrones = {
            "resumen": r"###\s*(RESUMEN EJECUTIVO|EXECUTIVE SUMMARY)\s*(.*?)(?=###\s*(ANÁLISIS|ANALYSIS|---|$))",
            "analisis": r"###\s*(ANÁLISIS|ANALYSIS|ANÁLISIS DETALLADO|DETAILED ANALYSIS)\s*(.*?)(?=###\s*(CONCLUSIONES|CONCLUSIONS|---|$))",
            "conclusiones": r"###\s*(CONCLUSIONES|CONCLUSIONS)\s*(.*?)(?=###\s*(RECOMENDACIONES|RECOMMENDATIONS|---|$))",
            "recomendaciones": r"###\s*(RECOMENDACIONES|RECOMMENDATIONS)\s*(.*?)$"
        }
        contenido = {k: "" for k in patrones}

        # Buscar cada sección con expresión regular (modo DOTALL)
        for key, patron in patrones.items():
            match = re.search(patron, analisis_texto, re.DOTALL | re.IGNORECASE)
            if match:
                # El grupo 2 es el contenido (el grupo 1 es el título)
                texto_seccion = match.group(2).strip() if len(match.groups()) >= 2 else ""
                texto_seccion = self._limpiar_marcadores(texto_seccion)
                contenido[key] = texto_seccion

        # Si alguna sección quedó vacía, intentar recuperar del texto crudo (fallback)
        if not contenido["resumen"]:
            contenido["resumen"] = config.traductor.t("Analisis_generado_ia") if hasattr(config,
                                                                                         'traductor') else "Análisis generado por IA"
        if not contenido["analisis"]:
            # Si no se encontró la sección análisis, tomar todo el texto (pero sin los títulos)
            texto_restante = re.sub(r'###.*$', '', analisis_texto, flags=re.MULTILINE).strip()
            contenido["analisis"] = self._limpiar_marcadores(texto_restante) if texto_restante else analisis_texto
        if not contenido["conclusiones"]:
            contenido["conclusiones"] = config.traductor.t("Revisar_analisis") if hasattr(config,
                                                                                          'traductor') else "Revisar el análisis completo"
        if not contenido["recomendaciones"]:
            contenido["recomendaciones"] = config.traductor.t("Basado_datos_usuario") if hasattr(config,
                                                                                                 'traductor') else "Basado en datos de usuario"

        return contenido

    # ---------- Métodos públicos ----------
    def Resultados(self, sesion_id, idioma=None):
        idioma_destino = self._get_idioma(idioma)
        analisis_es = self._generar_analisis_es(self.Obtener_Datos(sesion_id), sesion_id, tipo="normal")
        if idioma_destino == "es":
            return analisis_es
        try:
            traductor = GoogleTranslator(source='es', target=idioma_destino)
            analisis_trad = traductor.translate(analisis_es)
            return analisis_trad
        except Exception as e:
            print(f"Error traduciendo análisis: {e}")
            return analisis_es

    def ResultadosPDF(self, sesion_id, idioma=None):
        """
        Genera el diccionario con resumen, análisis, conclusiones, recomendaciones.
        Primero obtiene el análisis (forzado a español), lo divide, y luego traduce cada campo si es necesario.
        """
        idioma_destino = self._get_idioma(idioma)
        # 1. Obtener análisis completo en español (con marcadores)
        analisis_es = self._generar_analisis_es(self.Obtener_Datos(sesion_id), sesion_id, tipo="pdf")
        # 2. Dividir secciones (funciona incluso si la IA respondió en inglés, gracias a los patrones bilingües)
        secciones = self.dividir_secciones(analisis_es)

        # Si el idioma destino es español, devolver directamente
        if idioma_destino == "es":
            return secciones

        # 3. Traducir cada sección por separado
        try:
            traductor = GoogleTranslator(source='es', target=idioma_destino)
            secciones_trad = {}
            for key in ["resumen", "analisis", "conclusiones", "recomendaciones"]:
                texto = secciones.get(key, "")
                if texto and texto not in ["Análisis generado por IA", "Revisar el análisis completo",
                                           "Basado en datos de usuario"]:
                    secciones_trad[key] = traductor.translate(texto)
                else:
                    secciones_trad[key] = texto
            return secciones_trad
        except Exception as e:
            print(f"Error traduciendo secciones del PDF: {e}")
            return secciones