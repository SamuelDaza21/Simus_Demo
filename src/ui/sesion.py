import pygame
import sys
import os
import calendar
from datetime import date, datetime, timedelta
from api.APICliente import APICliente
from api.Servidor import Servidor
from core.ManejoCamara import ManejoCamara
from core import config
from core.Musica import gestor_musica
from core.paths import imagen
from ui.common import render_text, Button, InputBox

# ------------------ CONFIG ------------------
pygame.init()
pygame.display.set_caption("Sistema de Sesión")
ANCHO, ALTO = 1920, 1080
if config.traductor is None:
    config.setup_traductor("es")

# --- CONFIGURACIÓN GLOBAL DE ICONOS ---
TAM_ICONO = (24, 24)
try:
    ICONO_EDITAR = pygame.transform.smoothscale(pygame.image.load(imagen("General/editar.png")), TAM_ICONO)
    ICONO_BORRAR = pygame.transform.smoothscale(pygame.image.load(imagen("General/borrar.png")), TAM_ICONO)
except Exception as e:
    print(f"[WARNING] Error cargando iconos: {e}")
    ICONO_EDITAR = pygame.Surface(TAM_ICONO, pygame.SRCALPHA)
    ICONO_BORRAR = pygame.Surface(TAM_ICONO, pygame.SRCALPHA)
    pygame.draw.rect(ICONO_EDITAR, (0, 0, 255), (0,0,24,24))

fondo = None
cliente = APICliente()
sesion_existente = None


def render_text(text, font, color, antialias=True):
    if config.traductor and config.traductor.get_direction() == "rtl":
        text = text[::-1]
    return font.render(text, antialias, color)

def wp(px): return int(ANCHO * px)
def hp(px): return int(ALTO * px)

# ------------------ VALIDACIONES ------------------
def validar_nickname(nickname):
    if not nickname or not nickname.strip():
        return False, "El nickname no puede estar vacío"
    if len(nickname) > 25:
        return False, "El nickname no puede tener más de 25 caracteres"
    caracteres_permitidos = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 áéíóúÁÉÍÓÚñÑ"
    for char in nickname:
        if char not in caracteres_permitidos:
            return False, "Solo se permiten letras, números, espacios y tildes"
    return True, "Nickname válido"

def parsear_fecha(fecha_texto):
    if not fecha_texto:
        return None
    fecha_texto = fecha_texto.replace('-', '/')
    partes = fecha_texto.split('/')
    if len(partes) != 3:
        return None
    try:
        dia, mes, anio = partes
        dia = dia.zfill(2)
        mes = mes.zfill(2)
        if len(anio) == 2:
            anio = '20' + anio
        fecha_nac = date(int(anio), int(mes), int(dia))
        return f"{anio}-{mes}-{dia}"
    except:
        return None

def calcular_edad(fecha_iso):
    try:
        fecha_nac = date.fromisoformat(fecha_iso)
        hoy = date.today()
        edad = hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
        return edad
    except:
        return None

def validar_datos_usuario(nickname, grado, fecha_iso):
    errores = []
    nick_valido, msg_nick = validar_nickname(nickname)
    if not nick_valido:
        errores.append(msg_nick)
    if not fecha_iso:
        errores.append("La fecha de nacimiento es requerida")
    else:
        try:
            fecha_nac = date.fromisoformat(fecha_iso)
            hoy = date.today()
            edad = hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
            if fecha_nac > hoy:
                errores.append("La fecha no puede ser en el futuro.")
            elif edad < 5:
                errores.append("Debes tener al menos 5 años para registrarte.")
            elif edad > 12:
                errores.append("¡Lo sentimos! Esta plataforma es exclusiva para niños de hasta 12 años.")
        except ValueError:
            errores.append("Fecha inválida")
    return len(errores) == 0, errores

# ------------------ UI ------------------
class Button:
    def __init__(self, text_key, x, y, w, h):
        self.rect = pygame.Rect(x,y,w,h)
        self.text_key = text_key
    def draw(self, surf, hover=False):
        texto_actual = config.traductor.t(self.text_key)
        sombra = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        sombra.fill((0,0,0,40))
        surf.blit(sombra, (self.rect.x+4, self.rect.y+6))
        color = (min(255, config.FONDO_BOTON[0]+(30 if hover else 0)),
                 min(255, config.FONDO_BOTON[1]+(30 if hover else 0)),
                 min(255, config.FONDO_BOTON[2]+(30 if hover else 0)))
        pygame.draw.rect(surf, color, self.rect)
        pygame.draw.rect(surf, config.BORDE_BOTON, self.rect,3)
        txt = render_text(texto_actual, config.fuente_pequena, config.COLOR_TEXTO)
        surf.blit(txt, (self.rect.centerx-txt.get_width()//2, self.rect.centery-txt.get_height()//2))
    def collidepoint(self, pos):
        return self.rect.collidepoint(pos)

class ButtonImage:
    def __init__(self, imagen_path, x, y, w, h):
        self.rect = pygame.Rect(x,y,w,h)
        try:
            ruta_imagen = imagen(imagen_path)
            self.imagen = pygame.image.load(ruta_imagen).convert_alpha()
            self.imagen = pygame.transform.scale(self.imagen, (w,h))
        except Exception as e:
            print(f"error cargando imagen {imagen_path}: {e}")
            self.imagen = pygame.Surface((w,h))
            self.imagen.fill(config.FONDO_BOTON)
            pygame.draw.rect(self.imagen, config.BORDE_BOTON, (0,0,w,h),3)
    def draw(self, surf, hover=False):
        sombra = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        sombra.fill((0,0,0,10))
        surf.blit(sombra, (self.rect.x+4, self.rect.y+6))
        surf.blit(self.imagen, self.rect)
        if hover:
            overlay = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
            overlay.fill((255,255,255,60))
            surf.blit(overlay, self.rect)
    def collidepoint(self, pos):
        return self.rect.collidepoint(pos)

class InputBox:
    def __init__(self, x, y, w, h, texto='', placeholder_key='', max_caracteres=None):
        self.rect = pygame.Rect(x,y,w,h)
        self.color = config.COLOR_INPUT
        self.color_error = (255,100,100)
        self.texto = texto
        self.placeholder_key = placeholder_key
        self.active = False
        self.cursor_visible = True
        self.cursor_counter = 0
        self.max_caracteres = max_caracteres
        self.mostrar_error = False
    def manejar_evento(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.mostrar_error = False
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return self.texto
            elif event.key == pygame.K_BACKSPACE:
                self.texto = self.texto[:-1]
            elif event.key == pygame.K_v and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                try:
                    import pyperclip
                    texto_pegar = pyperclip.paste()
                    if self.max_caracteres and len(self.texto+texto_pegar) > self.max_caracteres:
                        texto_pegar = texto_pegar[:self.max_caracteres-len(self.texto)]
                    self.texto += texto_pegar
                except:
                    pass
            else:
                if event.unicode:
                    if self.max_caracteres is None or len(self.texto) < self.max_caracteres:
                        self.texto += event.unicode
        return None
    def update(self):
        if self.active:
            self.cursor_counter +=1
            if self.cursor_counter %30 ==0:
                self.cursor_visible = not self.cursor_visible
        else:
            self.cursor_visible = False
            self.cursor_counter = 0
    def draw(self, surf):
        panel = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (255,255,255,240), (0,0,self.rect.w,self.rect.h))
        surf.blit(panel, (self.rect.x, self.rect.y))
        texto_mostrar = self.texto
        if self.texto:
            txt_temp = render_text(self.texto, config.fuente_muy_pequena, config.COLOR_TEXTO)
            while txt_temp.get_width() > self.rect.w-30 and len(texto_mostrar)>1:
                texto_mostrar = texto_mostrar[1:]
                txt_temp = render_text("..."+texto_mostrar, config.fuente_pequena, config.COLOR_TEXTO)
            if len(texto_mostrar) < len(self.texto):
                texto_mostrar = "..."+texto_mostrar
        if self.texto:
            txt_s = render_text(texto_mostrar, config.fuente_muy_pequena, config.COLOR_TEXTO)
        else:
            placeholder_texto = config.traductor.t(self.placeholder_key) if self.placeholder_key else ""
            txt_s = render_text(placeholder_texto, config.fuente_muy_pequena, (150,150,150))
        surf.blit(txt_s, (self.rect.x+14, self.rect.y+(self.rect.h-txt_s.get_height())//2))
        if self.active and self.cursor_visible:
            cursor_x = self.rect.x+14+txt_s.get_width()
            pygame.draw.line(surf, config.COLOR_TEXTO, (cursor_x, self.rect.y+10), (cursor_x, self.rect.y+self.rect.h-10),2)
        border_color = self.color_error if self.mostrar_error else (config.BORDE_BOTON if self.active else self.color)
        pygame.draw.rect(surf, border_color, self.rect,3)

class Dropdown:
    def __init__(self, x, y, w, h, opciones, placeholder='Seleccione'):
        self.rect = pygame.Rect(x,y,w,h)
        self.opciones = opciones
        self.seleccionado = None
        self.placeholder = placeholder
        self.activo = False
        self.color = config.COLOR_INPUT
        self.color_error = (255,100,100)
        self.mostrar_error = False
        self.rect_opciones = []
    def manejar_evento(self, event, elementos_superpuestos=None, dropdowns_activos=None):
        if elementos_superpuestos is None: elementos_superpuestos=[]
        if dropdowns_activos is None: dropdowns_activos=[]
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            if self.activo:
                for i, rect in enumerate(self.rect_opciones):
                    if rect.collidepoint(mouse_pos):
                        self.seleccionado = self.opciones[i]
                        self.activo = False
                        self.mostrar_error = False
                        return True
            if self.rect.collidepoint(mouse_pos):
                for dropdown in dropdowns_activos:
                    if dropdown != self and hasattr(dropdown,'activo'):
                        dropdown.activo = False
                self.activo = not self.activo
                self.mostrar_error = False
                return True
            for elemento in elementos_superpuestos:
                if hasattr(elemento,'collidepoint') and elemento.collidepoint(mouse_pos):
                    self.activo = False
                    return False
            if self.activo:
                self.activo = False
                return False
        return False
    def update(self):
        self.rect_opciones = []
        if self.activo:
            for i in range(len(self.opciones)):
                rect_opcion = pygame.Rect(self.rect.x, self.rect.y+(i+1)*self.rect.h, self.rect.w, self.rect.h)
                self.rect_opciones.append(rect_opcion)
    def draw(self, surf):
        color_borde = self.color_error if self.mostrar_error else (config.BORDE_BOTON if self.activo else self.color)
        pygame.draw.rect(surf, (255,255,255), self.rect)
        pygame.draw.rect(surf, color_borde, self.rect,3)
        texto = self.seleccionado if self.seleccionado else self.placeholder
        color_temp = config.COLOR_TEXTO if self.seleccionado else (150,150,150)
        txt_s = render_text(texto, config.fuente, color_temp)
        texto_mostrar = texto
        if txt_s.get_width() > self.rect.w-50:
            while txt_s.get_width() > self.rect.w-50 and len(texto_mostrar)>1:
                texto_mostrar = texto_mostrar[:-1]
                txt_s = render_text(texto_mostrar+"...", config.fuente, color_temp)
        surf.blit(txt_s, (self.rect.x+14, self.rect.y+(self.rect.h-txt_s.get_height())//2))
        arrow_size=8
        arrow_x=self.rect.right-25
        arrow_y=self.rect.centery
        if self.activo:
            pygame.draw.polygon(surf, color_borde, [(arrow_x, arrow_y-arrow_size//2), (arrow_x-arrow_size, arrow_y+arrow_size//2), (arrow_x+arrow_size, arrow_y+arrow_size//2)])
        else:
            pygame.draw.polygon(surf, color_borde, [(arrow_x, arrow_y+arrow_size//2), (arrow_x-arrow_size, arrow_y-arrow_size//2), (arrow_x+arrow_size, arrow_y-arrow_size//2)])
    def draw_opciones(self, surf):
        if not self.activo: return
        sombra_surf = pygame.Surface((self.rect.w, len(self.opciones)*self.rect.h), pygame.SRCALPHA)
        sombra_surf.fill((0,0,0,30))
        surf.blit(sombra_surf, (self.rect.x+2, self.rect.y+self.rect.h+2))
        for i, (opcion, rect_opcion) in enumerate(zip(self.opciones, self.rect_opciones)):
            color_fondo = (230,240,255) if opcion==self.seleccionado else (255,255,255)
            color_borde_opcion = (100,150,255) if opcion==self.seleccionado else (200,200,200)
            pygame.draw.rect(surf, color_fondo, rect_opcion)
            pygame.draw.rect(surf, color_borde_opcion, rect_opcion,2)
            txt_opcion = render_text(opcion, config.fuente_pequena, config.COLOR_TEXTO)
            texto_opcion_mostrar = opcion
            if txt_opcion.get_width() > rect_opcion.w-20:
                while txt_opcion.get_width() > rect_opcion.w-20 and len(texto_opcion_mostrar)>1:
                    texto_opcion_mostrar = texto_opcion_mostrar[:-1]
                    txt_opcion = render_text(texto_opcion_mostrar+"...", config.fuente_pequena, config.COLOR_TEXTO)
            surf.blit(txt_opcion, (rect_opcion.x+10, rect_opcion.y+(rect_opcion.h-txt_opcion.get_height())//2))

class DateDropdown:
    def __init__(self, x, y, w, h, fecha_texto=''):
        self.rect = pygame.Rect(x,y,w,h)
        self.color = config.COLOR_INPUT
        self.color_error = (255,100,100)
        self.mostrar_error = False
        dia_inicial, mes_inicial, anio_inicial = self._parsear_fecha(fecha_texto)
        dias = [str(i).zfill(2) for i in range(1,32)]
        meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
        anio_actual = datetime.now().year
        anios = [str(i) for i in range(anio_actual-12, anio_actual-4)]
        dropdown_w = (w-20)//3
        self.dropdown_dia = Dropdown(x, y, dropdown_w, h, dias, 'Día')
        self.dropdown_mes = Dropdown(x+dropdown_w+10, y, dropdown_w, h, meses, 'Mes')
        self.dropdown_anio = Dropdown(x+2*(dropdown_w+10), y, dropdown_w, h, anios, 'Año')
        if dia_inicial: self.dropdown_dia.seleccionado = dia_inicial
        if mes_inicial: self.dropdown_mes.seleccionado = meses[int(mes_inicial)-1] if mes_inicial.isdigit() and 1<=int(mes_inicial)<=12 else None
        if anio_inicial: self.dropdown_anio.seleccionado = anio_inicial
    def _parsear_fecha(self, fecha_texto):
        if not fecha_texto: return None,None,None
        try:
            if '/' in fecha_texto:
                partes = fecha_texto.split('/')
                if len(partes)==3: return partes[0], partes[1], partes[2]
            elif '-' in fecha_texto:
                partes = fecha_texto.split('-')
                if len(partes)==3: return partes[2], partes[1], partes[0]
        except: pass
        return None,None,None
    def manejar_evento(self, event, elementos_bloqueados=None, dropdowns_activos=None):
        if elementos_bloqueados is None: elementos_bloqueados=[]
        if dropdowns_activos is None: dropdowns_activos=[]
        if event.type == pygame.MOUSEBUTTONDOWN:
            todos_dropdowns_fecha = [self.dropdown_dia, self.dropdown_mes, self.dropdown_anio]
            manejado_dia = self.dropdown_dia.manejar_evento(event, elementos_bloqueados, todos_dropdowns_fecha+dropdowns_activos)
            manejado_mes = self.dropdown_mes.manejar_evento(event, elementos_bloqueados, todos_dropdowns_fecha+dropdowns_activos)
            manejado_anio = self.dropdown_anio.manejar_evento(event, elementos_bloqueados, todos_dropdowns_fecha+dropdowns_activos)
            return manejado_dia or manejado_mes or manejado_anio
        return False
    def update(self):
        self.dropdown_dia.update()
        self.dropdown_mes.update()
        self.dropdown_anio.update()
    def draw(self, surf):
        self.dropdown_dia.draw(surf)
        self.dropdown_mes.draw(surf)
        self.dropdown_anio.draw(surf)
        separador_x1 = self.dropdown_dia.rect.right+5
        separador_x2 = self.dropdown_mes.rect.right+5
        pygame.draw.line(surf, (200,200,200), (separador_x1, self.rect.y+10), (separador_x1, self.rect.y+self.rect.h-10),1)
        pygame.draw.line(surf, (200,200,200), (separador_x2, self.rect.y+10), (separador_x2, self.rect.y+self.rect.h-10),1)
    def draw_opciones(self, surf):
        self.dropdown_dia.draw_opciones(surf)
        self.dropdown_mes.draw_opciones(surf)
        self.dropdown_anio.draw_opciones(surf)
    def obtener_fecha_iso(self):
        if self.dropdown_dia.seleccionado and self.dropdown_mes.seleccionado and self.dropdown_anio.seleccionado:
            try:
                meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
                mes_numero = str(meses.index(self.dropdown_mes.seleccionado)+1).zfill(2)
                return f"{self.dropdown_anio.seleccionado}-{mes_numero}-{self.dropdown_dia.seleccionado}"
            except: return None
        return None
    def obtener_fecha_formateada(self):
        if self.dropdown_dia.seleccionado and self.dropdown_mes.seleccionado and self.dropdown_anio.seleccionado:
            try:
                meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
                mes_numero = str(meses.index(self.dropdown_mes.seleccionado)+1).zfill(2)
                return f"{self.dropdown_dia.seleccionado}/{mes_numero}/{self.dropdown_anio.seleccionado}"
            except: return ""
        return ""
    @property
    def dia(self): return self.dropdown_dia.seleccionado
    @property
    def mes(self):
        if self.dropdown_mes.seleccionado:
            meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
            return str(meses.index(self.dropdown_mes.seleccionado)+1)
        return None
    @property
    def anio(self): return self.dropdown_anio.seleccionado

class LanguageSelector:
    def __init__(self, x, y, w=50, h=50):
        self.rect = pygame.Rect(x,y,w,h)
        self.idiomas = ["es", "en", "fr"]
        self.mapeo_banderas = {
            "es": "espanol.png",
            "en": "ingles.png",
            "fr": "frances.png"
        }
        self.banderas = {}
        self.activo = False
        self.seleccionado = 0
        self.opciones_rects = []
        self.cargar_banderas(w-10, h-10)
    def cargar_banderas(self, w, h):
        for idioma, archivo in self.mapeo_banderas.items():
            try:
                ruta = imagen(f"Traductor/{archivo}")
                bandera = pygame.image.load(ruta).convert_alpha()
                self.banderas[idioma] = pygame.transform.scale(bandera, (w,h))
            except Exception as e:
                print(f"[WARNING] No se pudo cargar bandera {idioma}: {e}")
                superficie = pygame.Surface((w,h), pygame.SRCALPHA)
                pygame.draw.rect(superficie, (100,150,255), (0,0,w,h))
                pygame.draw.line(superficie, (255,255,255), (0,0), (w,h),2)
                self.banderas[idioma] = superficie
    def manejar_evento(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            if self.activo:
                self.update()
                for i, rect in enumerate(self.opciones_rects):
                    if rect.collidepoint(mouse_pos):
                        self.seleccionado = i
                        config.cambiar_idioma(self.idiomas[i])
                        self.activo = False
                        return True
                if not self.rect.collidepoint(mouse_pos):
                    self.activo = False
                    return True
            if self.rect.collidepoint(mouse_pos):
                self.activo = not self.activo
                if self.activo:
                    self.update()
                return True
        return False
    def update(self):
        self.opciones_rects = []
        if self.activo:
            for i in range(len(self.idiomas)):
                rect_opcion = pygame.Rect(
                    self.rect.x,
                    self.rect.y + (i * (self.rect.h + 5)),
                    self.rect.w,
                    self.rect.h
                )
                self.opciones_rects.append(rect_opcion)
    def draw(self, surf):
        pygame.draw.rect(surf, (255,255,255), self.rect, border_radius=8)
        pygame.draw.rect(surf, (150,150,150), self.rect, 2, border_radius=8)
        idioma_actual = self.idiomas[self.seleccionado]
        if idioma_actual in self.banderas:
            bandera = self.banderas[idioma_actual]
            x = self.rect.x + (self.rect.w - bandera.get_width())//2
            y = self.rect.y + (self.rect.h - bandera.get_height())//2
            surf.blit(bandera, (x,y))
    def draw_opciones(self, surf):
        if not self.activo: return
        if self.opciones_rects:
            total_h = sum(r.h for r in self.opciones_rects) + (len(self.opciones_rects)-1)*5
            bg_rect = pygame.Rect(
                self.opciones_rects[0].x - 2,
                self.opciones_rects[0].y - 2,
                self.opciones_rects[0].w + 4,
                total_h + 4
            )
            pygame.draw.rect(surf, (240,240,240), bg_rect, border_radius=8)
            pygame.draw.rect(surf, (150,150,150), bg_rect, 2, border_radius=8)
        for i, (idioma, rect_opcion) in enumerate(zip(self.idiomas, self.opciones_rects)):
            if i == self.seleccionado:
                pygame.draw.rect(surf, (200,220,255), rect_opcion, border_radius=5)
            pygame.draw.rect(surf, (180,180,180), rect_opcion, 2, border_radius=5)
            if idioma in self.banderas:
                bandera = self.banderas[idioma]
                x = rect_opcion.x + (rect_opcion.w - bandera.get_width())//2
                y = rect_opcion.y + (rect_opcion.h - bandera.get_height())//2
                surf.blit(bandera, (x,y))

def mostrar_confirmacion_salir(pantalla=None):
    if pantalla is None: pantalla = pygame.display.get_surface()
    modal_w, modal_h = 400,400
    modal_x = (ANCHO-modal_w)//2
    modal_y = (ALTO-modal_h)//2
    try:
        fuente_modal = pygame.font.Font(None,24)
        fuente_botones = pygame.font.Font(None,20)
    except:
        fuente_modal = pygame.font.Font(None,24)
        fuente_botones = pygame.font.Font(None,20)
    mensaje = "¿Estás seguro de que quieres salir?"
    boton_si = pygame.Rect(modal_x+modal_w-170, modal_y+modal_h-60,70,40)
    boton_no = pygame.Rect(modal_x+modal_w-90, modal_y+modal_h-60,70,40)
    esperando = True
    reloj = pygame.time.Clock()
    while esperando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if evento.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = evento.pos
                if boton_si.collidepoint(mouse_pos): return True
                if boton_no.collidepoint(mouse_pos): return False
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                return False
        shadow_rect = pygame.Rect(modal_x+4, modal_y+4, modal_w, modal_h)
        pygame.draw.rect(pantalla, (0,0,0,50), shadow_rect, border_radius=15)
        modal_rect = pygame.Rect(modal_x, modal_y, modal_w, modal_h)
        pygame.draw.rect(pantalla, (255,255,255), modal_rect, border_radius=15)
        pygame.draw.rect(pantalla, config.BORDE_BOTON, modal_rect, 3, border_radius=15)
        texto = fuente_modal.render(mensaje, True, config.COLOR_TEXTO)
        texto_rect = texto.get_rect(center=(modal_x+modal_w//2, modal_y+modal_h//2-20))
        pantalla.blit(texto, texto_rect)
        pygame.draw.rect(pantalla, config.FONDO_BOTON, boton_si, border_radius=8)
        pygame.draw.rect(pantalla, config.BORDE_BOTON, boton_si, 2, border_radius=8)
        texto_si = fuente_botones.render("Sí", True, config.COLOR_TEXTO)
        pantalla.blit(texto_si, (boton_si.centerx - texto_si.get_width()//2, boton_si.centery - texto_si.get_height()//2))
        pygame.draw.rect(pantalla, config.FONDO_BOTON, boton_no, border_radius=8)
        pygame.draw.rect(pantalla, config.BORDE_BOTON, boton_no, 2, border_radius=8)
        texto_no = fuente_botones.render("No", True, config.COLOR_TEXTO)
        pantalla.blit(texto_no, (boton_no.centerx - texto_no.get_width()//2, boton_no.centery - texto_no.get_height()//2))
        pygame.display.flip()
        reloj.tick(30)
    return False

def fade_out(pantalla=None):
    if pantalla is None: pantalla = pygame.display.get_surface()
    fade = pygame.Surface((ANCHO, ALTO))
    fade.fill((0,0,0))
    for alpha in range(0,255,15):
        fade.set_alpha(alpha)
        pantalla.blit(fade,(0,0))
        pygame.display.update()
        pygame.time.delay(10)

# ------------------ REGISTRO/EDICIÓN ------------------
def formulario_usuario(usuario_editar=None, pantalla=None):
    if pantalla is None: pantalla = pygame.display.get_surface()
    panel_w, panel_h = int(ANCHO*0.45), int(ALTO*0.6)
    panel_x, panel_y = (ANCHO-panel_w)//2, (ALTO-panel_h)//2
    field_w, field_h = int(panel_w*0.6), 56
    gap = 20
    sx, sy = panel_x+(panel_w-field_w)//2, panel_y+90
    if usuario_editar:
        nombre_inicial = usuario_editar.get("Nickname","")
        fecha_db = usuario_editar.get("FechaNacimiento","")
        if fecha_db:
            Fecha = fecha_db.split("T")[0]
            try:
                partes = Fecha.split("-")
                fecha_inicial = f"{partes[2]}/{partes[1]}/{partes[0]}"
            except IndexError:
                fecha_inicial = Fecha
        else: fecha_inicial=""
    else:
        nombre_inicial=""
        fecha_inicial=""
    input_nombre = InputBox(sx,sy,field_w,field_h, nombre_inicial, 'Nick Name', max_caracteres=25)
    placeholder_fecha = config.traductor.get_date_format()
    input_fecha = InputBox(sx, sy+(field_h+gap), field_w, field_h, fecha_inicial, placeholder_fecha)
    boton_guardar = Button("Editar" if usuario_editar else "Registrar", sx, sy+(field_h+gap)*2+20, field_w, 56)
    boton_cerrar = Button("X", panel_x+panel_w-50, panel_y+10, 40,40)
    clock = pygame.time.Clock()
    mensaje = ""
    mensaje_tipo = "error"
    while True:
        mouse_pos = pygame.mouse.get_pos()
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            evento_manejado = False
            if not evento_manejado:
                input_nombre.manejar_evento(evento)
                input_fecha.manejar_evento(evento)
            if evento.type == pygame.MOUSEBUTTONDOWN and not evento_manejado:
                if boton_cerrar.collidepoint(evento.pos):
                    return False
                if boton_guardar.collidepoint(evento.pos):
                    nombre = input_nombre.texto.strip()
                    fecha_texto = input_fecha.texto.strip()
                    fecha_iso = parsear_fecha(fecha_texto)
                    if fecha_iso:
                        es_valido, errores = validar_datos_usuario(nombre, "", fecha_iso)
                        if not es_valido:
                            mensaje = " • "+"\n • ".join(errores)
                            mensaje_tipo = "error"
                            input_nombre.mostrar_error = not validar_nickname(nombre)[0]
                            input_fecha.mostrar_error = True
                        else:
                            if usuario_editar:
                                resultado = cliente.actualizar_usuario(usuario_editar["ID_usuario"], nombre, fecha_iso)
                                if resultado:
                                    if resultado.get("error")=="database_locked":
                                        mensaje = "❌ La base de datos está ocupada.\n¡Inténtalo de nuevo en unos segundos!"
                                        mensaje_tipo = "error"
                                    else:
                                        mensaje = "[OK] Usuario actualizado correctamente"
                                        mensaje_tipo = "exito"
                                        pygame.time.delay(1500)
                                        return True
                                else:
                                    mensaje = "[ERROR] Error al actualizar usuario"
                                    mensaje_tipo = "error"
                            else:
                                nuevo_usuario = cliente.crear_usuario(nombre, fecha_iso)
                                if nuevo_usuario:
                                    if nuevo_usuario.get("error")=="database_locked":
                                        mensaje = "❌ La base de datos está ocupada.\n¡Inténtalo de nuevo en unos segundos!"
                                        mensaje_tipo = "error"
                                    elif nuevo_usuario.get("error"):
                                        mensaje = f"❌ Error al registrar: {nuevo_usuario.get('error')}"
                                        mensaje_tipo = "error"
                                    else:
                                        mensaje = "[OK] Usuario creado correctamente"
                                        mensaje_tipo = "exito"
                                        input_nombre.texto = ""
                                        input_fecha.texto = ""
                                        input_nombre.mostrar_error = False
                                        input_fecha.mostrar_error = False
                                        pygame.time.delay(2000)
                                        fade_out(pantalla)
                                        return True
                                else:
                                    mensaje = "[ERROR] Error al registrar usuario"
                                    mensaje_tipo = "error"
                    else:
                        mensaje = " • Formato de fecha inválido. Use DD/MM/AAAA"
                        mensaje_tipo = "error"
                        input_fecha.mostrar_error = True
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                if mostrar_confirmacion_salir(pantalla):
                    pygame.quit(); sys.exit()
                return False
        input_nombre.update()
        input_fecha.update()
        pantalla.blit(fondo,(0,0))
        shadow = pygame.Surface((panel_w,panel_h), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0,0,0,40), (0,0,panel_w,panel_h))
        pantalla.blit(shadow, (panel_x+6, panel_y+8))
        panel = pygame.Surface((panel_w,panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (255,255,255,220), (0,0,panel_w,panel_h))
        pygame.draw.rect(panel, (230,230,230,200), (0,0,panel_w,panel_h),3)
        pantalla.blit(panel, (panel_x,panel_y))
        titulo = render_text(config.traductor.t("Editar Usuario") if usuario_editar else config.traductor.t("Registro de Usuario"), config.fuente, config.COLOR_TEXTO)
        pantalla.blit(titulo, (panel_x+(panel_w-titulo.get_width())//2, panel_y+20))
        label_font = config.fuente_pequena
        lbl = label_font.render(config.traductor.t("Nick Name")+":", True, config.COLOR_TEXTO)
        pantalla.blit(lbl, (input_nombre.rect.x-140, input_nombre.rect.y+14))
        input_nombre.draw(pantalla)
        lbl2 = label_font.render(config.traductor.t("Fecha Nac.")+":", True, config.COLOR_TEXTO)
        pantalla.blit(lbl2, (input_fecha.rect.x-140, input_fecha.rect.y+14))
        input_fecha.draw(pantalla)
        boton_guardar.draw(pantalla, hover=boton_guardar.rect.collidepoint(mouse_pos))
        boton_cerrar.draw(pantalla, hover=boton_cerrar.rect.collidepoint(mouse_pos))
        if mensaje:
            color_mensaje = (100,255,100) if mensaje_tipo=="exito" else (255,100,100)
            lineas = mensaje.split('\n')
            for i, linea in enumerate(lineas):
                msg_surface = render_text(linea, config.fuente_pequena, color_mensaje)
                pantalla.blit(msg_surface, (panel_x+(panel_w-msg_surface.get_width())//2, panel_y+panel_h-40 - (len(lineas)-1-i)*25))
        pygame.display.flip()
        clock.tick(30)

def registrar_usuario(pantalla=None):
    return formulario_usuario(pantalla=pantalla)
def editar_usuario(usuario, pantalla=None):
    return formulario_usuario(usuario_editar=usuario, pantalla=pantalla)

# ------------------ MODAL USUARIOS ------------------
def compute_modal_info(lista):
    modal_w, modal_h = 600,420
    mx, my = (ANCHO-modal_w)//2, (ALTO-modal_h)//2
    modal_rect = pygame.Rect(mx,my,modal_w,modal_h)
    close_rect = pygame.Rect(mx+modal_w-50, my+16,30,30)
    botones = []
    scroll_y = my+70
    for u in lista:
        card_rect = pygame.Rect(mx+30, scroll_y, modal_w-60,70)
        user_select_rect = pygame.Rect(card_rect.x, card_rect.y, card_rect.w-100, card_rect.h)
        btn_edit_rect = pygame.Rect(card_rect.right-95, card_rect.y+12,36,36)
        btn_del_rect = pygame.Rect(card_rect.right-50, card_rect.y+12,36,36)
        botones.append({"edit":btn_edit_rect,"del":btn_del_rect,"user":u,"card":card_rect,"select_rect":user_select_rect})
        scroll_y+=80
    return {"modal_rect":modal_rect,"close_rect":close_rect,"botones":botones,"mx":mx,"my":my,"modal_w":modal_w}

def draw_modal_from_info(info, pantalla=None):
    if pantalla is None: pantalla = pygame.display.get_surface()
    overlay = pygame.Surface((ANCHO,ALTO), pygame.SRCALPHA)
    overlay.fill((0,0,0,150))
    pantalla.blit(overlay,(0,0))
    mx,my = info["mx"], info["my"]
    modal_w, modal_h = info["modal_w"], info["modal_rect"].h
    shadow = pygame.Surface((modal_w,modal_h), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0,0,0,40), (0,0,modal_w,modal_h), border_radius=15)
    pantalla.blit(shadow, (mx+6, my+6))
    modal_surf = pygame.Surface((modal_w,modal_h), pygame.SRCALPHA)
    pygame.draw.rect(modal_surf, (255,255,255,250), (0,0,modal_w,modal_h), border_radius=15)
    pygame.draw.rect(modal_surf, config.BORDE_BOTON, (0,0,modal_w,modal_h),3, border_radius=15)
    txt_titulo = render_text(config.traductor.t("Usuarios Registrados"), config.fuente, config.COLOR_TEXTO)
    modal_surf.blit(txt_titulo, ((modal_w-txt_titulo.get_width())//2, 20))
    txt_inst = render_text(config.traductor.t("Selecciona un perfil para jugar"), config.fuente_muy_pequena, (120,120,120))
    modal_surf.blit(txt_inst, ((modal_w-txt_inst.get_width())//2, 55))
    mouse_pos = pygame.mouse.get_pos()
    close_rect = info["close_rect"]
    close_local = close_rect.move(-mx,-my)
    color_x = (255,100,100) if close_rect.collidepoint(mouse_pos) else (150,150,150)
    pygame.draw.circle(modal_surf, (240,240,240), close_local.center, 15)
    pygame.draw.line(modal_surf, color_x, (close_local.x+8, close_local.y+8), (close_local.x+22, close_local.y+22),3)
    pygame.draw.line(modal_surf, color_x, (close_local.x+22, close_local.y+8), (close_local.x+8, close_local.y+22),3)
    start_y = 100
    spacing = 75
    for i,b in enumerate(info["botones"]):
        card = b["card"]
        card.y = my + start_y + i*spacing
        card_local = card.move(-mx,-my)
        hover_card = b["select_rect"].collidepoint(mouse_pos)
        color_card = (235,245,255) if hover_card else (250,250,250)
        border_card = (100,150,255) if hover_card else (210,210,210)
        pygame.draw.rect(modal_surf, color_card, card_local, border_radius=10)
        pygame.draw.rect(modal_surf, border_card, card_local, 2, border_radius=10)
        nombre_txt = config.fuente_pequena.render(b["user"].get("Nickname","Invitado"), True, config.COLOR_TEXTO)
        modal_surf.blit(nombre_txt, (card_local.x+20, card_local.centery - nombre_txt.get_height()//2))
        rect_edit = b["edit"]
        rect_edit.y = card.y + (card.height//2)-18
        rect_edit_local = rect_edit.move(-mx,-my)
        hover_edit = rect_edit.collidepoint(mouse_pos)
        bg_edit = (210,230,255) if hover_edit else (240,245,255)
        pygame.draw.circle(modal_surf, bg_edit, rect_edit_local.center, 18)
        modal_surf.blit(ICONO_EDITAR, ICONO_EDITAR.get_rect(center=rect_edit_local.center))
        rect_del = b["del"]
        rect_del.y = card.y + (card.height//2)-18
        rect_del_local = rect_del.move(-mx,-my)
        hover_del = rect_del.collidepoint(mouse_pos)
        bg_del = (255,210,210) if hover_del else (255,240,240)
        pygame.draw.circle(modal_surf, bg_del, rect_del_local.center, 18)
        modal_surf.blit(ICONO_BORRAR, ICONO_BORRAR.get_rect(center=rect_del_local.center))
    pantalla.blit(modal_surf, (mx,my))

# ------------------ LOGIN ------------------
def login(pantalla=None):
    global ANCHO, ALTO, fondo
    print("[LOGIN] Iniciando login...")
    if pantalla is None:
        pantalla = config.init_pantalla()
    else:
        config.PANTALLA = pantalla
        config.ANCHO, config.ALTO = pantalla.get_size()
    ANCHO, ALTO = pantalla.get_size()
    print(f"[LOGIN] Dimensiones: {ANCHO}x{ALTO}")
    try:
        fondo_img = pygame.image.load(imagen("General/fondo.png"))
        fondo = pygame.transform.scale(fondo_img, (ANCHO, ALTO))
    except Exception as e:
        print(f"[WARNING] No se pudo cargar fondo: {e}")
        fondo = pygame.Surface((ANCHO, ALTO))
        fondo.fill((30,30,40))
    print("[LOGIN] Creando componentes UI...")
    panel_w, panel_h = int(ANCHO*0.45), int(ALTO*0.5)
    panel_x, panel_y = (ANCHO-panel_w)//2, (ALTO-panel_h)//2
    field_w, field_h = int(panel_w*0.6), 56
    sx, sy = panel_x+(panel_w-field_w)//2, panel_y+100
    input_usuario = InputBox(sx,sy,field_w,field_h,'','Usuario',25)
    boton_login = Button("Iniciar Sesión", sx, sy+field_h+40, field_w,56)
    boton_registro = Button("Registrar", sx, sy+field_h+120, field_w,56)
    boton_ver = Button("Ver Usuarios", sx, sy+field_h+200, field_w,56)
    icono_w,icono_h = 56,56
    icono_x = sx+200
    icono_y = sy+field_h+315
    boton_salir = ButtonImage("Botones/cerrar-programa.png", icono_x, icono_y, icono_w, icono_h)
    print("[LOGIN] Creando selector de idioma...")
    language_selector = LanguageSelector(ANCHO-60,10)
    print("[LOGIN] Componentes UI creados. Iniciando bucle...")
    mostrando_lista = False
    lista_usuarios = []
    modal_info = None
    mensaje = ""
    clock = pygame.time.Clock()
    saliendo = False
    frame_quit = 0
    while True:
        if saliendo:
            frame_quit+=1
            if frame_quit>10:
                if mostrar_confirmacion_salir():
                    pygame.quit(); sys.exit()
                else:
                    saliendo=False
                    frame_quit=0
                    pygame.event.clear()
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                saliendo=True
                continue
            input_usuario.manejar_evento(evento)
            language_selector.manejar_evento(evento)
            if evento.type == pygame.MOUSEBUTTONDOWN:
                mpos = evento.pos
                if mostrando_lista and modal_info:
                    if modal_info["close_rect"].collidepoint(mpos):
                        mostrando_lista=False
                        modal_info=None
                        continue
                    if not modal_info["modal_rect"].collidepoint(mpos):
                        mostrando_lista=False
                        modal_info=None
                        continue
                    manejado = False
                    for b in modal_info["botones"]:
                        if b["del"].collidepoint(mpos):
                            try:
                                cliente.eliminar_usuario(b["user"]["ID_usuario"])
                                lista_usuarios = cliente.obtener_todos_usuarios() or []
                                modal_info = compute_modal_info(lista_usuarios)
                            except Exception as ex:
                                print("Error eliminando usuario:", ex)
                            manejado = True
                            break
                        elif b["edit"].collidepoint(mpos):
                            fade_out(pantalla)
                            resultado = editar_usuario(b["user"], pantalla=pantalla)
                            if resultado:
                                lista_usuarios = cliente.obtener_todos_usuarios() or []
                                modal_info = compute_modal_info(lista_usuarios)
                            manejado = True
                            break
                        elif b["select_rect"].collidepoint(mpos):
                            usuario_seleccionado = b["user"]
                            global sesion_existente
                            sesion_existente = cliente.cargar_sesion_usuario(usuario_seleccionado["Nickname"])
                            if sesion_existente:
                                # Obtener ID de usuario a partir de la sesión existente
                                id_usuario = cliente.obtener_id_usuario_desde_sesion(sesion_existente)
                                if id_usuario:
                                    config_user = cliente.obtener_configuracion_usuario(id_usuario)
                                    if config_user:
                                        # Aplicar idioma
                                        idioma_guardado = config_user.get("idioma", "es")
                                        config.cambiar_idioma(idioma_guardado)
                                        # Aplicar volúmenes (convertir a float 0-1)
                                        vol_mus = config_user.get("volumen_musica", 50) / 100.0
                                        vol_ef = config_user.get("volumen_efectos", 80) / 100.0
                                        gestor_musica.volumen_musica = vol_mus
                                        gestor_musica.volumen_efectos = vol_ef
                                        gestor_musica.establecer_volumen_musica(vol_mus)
                                        gestor_musica.establecer_volumen_efectos(vol_ef)
                                fade_out(pantalla)
                                return sesion_existente
                            else:
                                # Crear nueva sesión y luego guardar configuración por defecto si se desea
                                nueva_sesion = cliente.crear_sesion(usuario_seleccionado["ID_usuario"])
                                if nueva_sesion:
                                    # Opcional: guardar configuración inicial (valores actuales)
                                    id_usuario = usuario_seleccionado["ID_usuario"]
                                    config_user = cliente.obtener_configuracion_usuario(id_usuario)
                                    if not config_user:
                                        # Guardar valores por defecto (idioma actual y volúmenes actuales)
                                        vol_mus_actual = gestor_musica.volumen_musica if gestor_musica else 0.5
                                        vol_ef_actual = gestor_musica.volumen_efectos if gestor_musica else 0.8
                                        cliente.guardar_configuracion_usuario(
                                            id_usuario,
                                            idioma=config.traductor.get_current_language(),
                                            volumen_musica=int(vol_mus_actual * 100),
                                            volumen_efectos=int(vol_ef_actual * 100)
                                        )
                                    fade_out(pantalla)
                                    return nueva_sesion
                                else:
                                    mensaje = "❌ Error al crear sesión"
                            manejado = True
                            break
                    if manejado: continue
                if boton_login.collidepoint(mpos):
                    usuario_nombre = input_usuario.texto.strip()
                    if not usuario_nombre:
                        mensaje = "Ingrese su nombre de usuario"
                    else:
                        usuarios = cliente.obtener_todos_usuarios() or []
                        usuario = next((u for u in usuarios if str(u.get("Nickname","")).lower() == usuario_nombre.lower()), None)
                        if usuario:
                            s = cliente.cargar_sesion_usuario(usuario_nombre)
                            if s is None:
                                sesion = cliente.crear_sesion(usuario["ID_usuario"])
                                if sesion:
                                    # Guardar configuración por defecto si no existe
                                    id_usuario = usuario["ID_usuario"]
                                    config_user = cliente.obtener_configuracion_usuario(id_usuario)
                                    if not config_user:
                                        vol_mus_actual = gestor_musica.volumen_musica if gestor_musica else 0.5
                                        vol_ef_actual = gestor_musica.volumen_efectos if gestor_musica else 0.8
                                        cliente.guardar_configuracion_usuario(
                                            id_usuario,
                                            idioma=config.traductor.get_current_language(),
                                            volumen_musica=int(vol_mus_actual * 100),
                                            volumen_efectos=int(vol_ef_actual * 100)
                                        )
                                    fade_out(pantalla)
                                    return sesion
                                else:
                                    mensaje = "❌ Error al crear sesión"
                            else:
                                # Cargar configuración de la sesión existente
                                id_usuario = cliente.obtener_id_usuario_desde_sesion(s)
                                if id_usuario:
                                    config_user = cliente.obtener_configuracion_usuario(id_usuario)
                                    if config_user:
                                        config.cambiar_idioma(config_user.get("idioma", "es"))
                                        vol_mus = config_user.get("volumen_musica", 50) / 100.0
                                        vol_ef = config_user.get("volumen_efectos", 80) / 100.0
                                        gestor_musica.volumen_musica = vol_mus
                                        gestor_musica.volumen_efectos = vol_ef
                                        gestor_musica.establecer_volumen_musica(vol_mus)
                                        gestor_musica.establecer_volumen_efectos(vol_ef)
                                fade_out(pantalla)
                                return s
                        else:
                            mensaje = "[ERROR] Usuario no encontrado"
                elif boton_registro.collidepoint(mpos):
                    fade_out(pantalla)
                    resultado = registrar_usuario(pantalla=pantalla)
                    if resultado:
                        mensaje = ""
                elif boton_ver.collidepoint(mpos):
                    lista_usuarios = cliente.obtener_todos_usuarios() or []
                    mostrando_lista = True
                    modal_info = compute_modal_info(lista_usuarios)
                if boton_salir.collidepoint(mpos):
                    if mostrar_confirmacion_salir(pantalla):
                        pygame.quit(); sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    if mostrar_confirmacion_salir(pantalla):
                        pygame.quit(); sys.exit()
        input_usuario.update()
        language_selector.update()
        pantalla.blit(fondo,(0,0))
        shadow = pygame.Surface((panel_w,panel_h), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0,0,0,40), (0,0,panel_w,panel_h))
        pantalla.blit(shadow, (panel_x+6, panel_y+6))
        panel = pygame.Surface((panel_w,panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (255,255,255,230), (0,0,panel_w,panel_h))
        pygame.draw.rect(panel, (230,230,230,200), (0,0,panel_w,panel_h),3)
        pantalla.blit(panel, (panel_x,panel_y))
        titulo_surface = render_text(config.traductor.t("Iniciar Sesión").upper(), config.fuente, config.COLOR_TEXTO)
        pantalla.blit(titulo_surface, (panel_x+(panel_w-titulo_surface.get_width())//2, panel_y+30))
        input_usuario.draw(pantalla)
        boton_login.draw(pantalla, hover=boton_login.rect.collidepoint(pygame.mouse.get_pos()))
        boton_registro.draw(pantalla, hover=boton_registro.rect.collidepoint(pygame.mouse.get_pos()))
        boton_ver.draw(pantalla, hover=boton_ver.rect.collidepoint(pygame.mouse.get_pos()))
        boton_salir.draw(pantalla, hover=boton_salir.rect.collidepoint(pygame.mouse.get_pos()))
        if mensaje:
            msg_surface = render_text(mensaje, config.fuente_pequena, config.COLOR_TEXTO)
            pantalla.blit(msg_surface, (panel_x+(panel_w-msg_surface.get_width())//2, panel_y+panel_h-40))
        language_selector.draw(pantalla)
        language_selector.draw_opciones(pantalla)
        if mostrando_lista and modal_info:
            draw_modal_from_info(modal_info, pantalla)
        pygame.display.flip()
        clock.tick(30)

if __name__ == "__main__":
    login()