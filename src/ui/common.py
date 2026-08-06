import pygame
from core import config

def render_text(text, font, color, antialias=True):
    return font.render(text, antialias, color)

class Button:
    def __init__(self, text_key, x, y, w, h):
        """Crea un botón con traducción dinámica.
        text_key: clave de traducción (ej: 'Iniciar Sesión')
        """
        self.rect = pygame.Rect(x, y, w, h)
        self.text_key = text_key  # Guardamos la clave, no el texto

    def draw(self, surf, hover=False):
        texto_actual = config.traductor.t(self.text_key)
        sombra = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        sombra.fill((0, 0, 0, 40))
        surf.blit(sombra, (self.rect.x + 4, self.rect.y + 6))
        color = (min(255, config.FONDO_BOTON[0] + (30 if hover else 0)),
                 min(255, config.FONDO_BOTON[1] + (30 if hover else 0)),
                 min(255, config.FONDO_BOTON[2] + (30 if hover else 0)))
        pygame.draw.rect(surf, color, self.rect)
        pygame.draw.rect(surf, config.BORDE_BOTON, self.rect, 3)
        txt = render_text(texto_actual, config.fuente, config.COLOR_TEXTO)
        surf.blit(txt, (self.rect.centerx - txt.get_width() // 2,
                        self.rect.centery - txt.get_height() // 2))

    def collidepoint(self, pos):
        return self.rect.collidepoint(pos)

class InputBox:
    def __init__(self, x, y, w, h, texto='', placeholder_key='', max_caracteres=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = config.COLOR_INPUT
        self.color_error = (255, 100, 100)
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
                    if self.max_caracteres and len(self.texto + texto_pegar) > self.max_caracteres:
                        texto_pegar = texto_pegar[:self.max_caracteres - len(self.texto)]
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
            self.cursor_counter += 1
            if self.cursor_counter % 30 == 0:
                self.cursor_visible = not self.cursor_visible
        else:
            self.cursor_visible = False
            self.cursor_counter = 0

    def draw(self, surf):
        panel = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (255, 255, 255, 240), (0, 0, self.rect.w, self.rect.h))
        surf.blit(panel, (self.rect.x, self.rect.y))

        texto_mostrar = self.texto
        if self.texto:
            txt_temp = render_text(self.texto, config.fuente_pequena, config.COLOR_TEXTO)
            while txt_temp.get_width() > self.rect.w - 30 and len(texto_mostrar) > 1:
                texto_mostrar = texto_mostrar[1:]
                txt_temp = render_text("..." + texto_mostrar, config.fuente_pequena, config.COLOR_TEXTO)
            if len(texto_mostrar) < len(self.texto):
                texto_mostrar = "..." + texto_mostrar

        if self.texto:
            txt_s = render_text(texto_mostrar, config.fuente_pequena, config.COLOR_TEXTO)
        else:
            placeholder_texto = config.traductor.t(self.placeholder_key) if self.placeholder_key else ""
            txt_s = render_text(placeholder_texto, config.fuente, (150, 150, 150))

        surf.blit(txt_s, (self.rect.x + 14, self.rect.y + (self.rect.h - txt_s.get_height()) // 2))

        if self.active and self.cursor_visible:
            cursor_x = self.rect.x + 14 + txt_s.get_width()
            pygame.draw.line(surf, config.COLOR_TEXTO, (cursor_x, self.rect.y + 10),
                             (cursor_x, self.rect.y + self.rect.h - 10), 2)

        border_color = self.color_error if self.mostrar_error else (config.BORDE_BOTON if self.active else self.color)
        pygame.draw.rect(surf, border_color, self.rect, 3)