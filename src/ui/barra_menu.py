import pygame
from core import config
from core.paths import imagen

class BarraInferior:
    """
    Barra inferior autónoma. Maneja sus propios iconos, traducciones y animaciones.
    Solo necesita: cámara, gestor de música, función para decir texto y ID de sesión.
    """

    def __init__(self, camara=None, gestor_musica=None, decir_texto=None, ID_sesion=None):
        self.camara = camara
        self.gestor_musica = gestor_musica
        self.decir_texto = decir_texto
        self.ID_sesion = ID_sesion
        self.visible = False  # se muestra solo al pasar el cursor por la zona inferior

        # --- Configuración interna de iconos: cada icono tiene su clave de traducción y ruta de imagen ---
        self.iconos_info = [
            {"nombre": "instrucciones", "archivo": "menu/instrucciones.png", "text_key": "Instrucciones"},
            {"nombre": "configuracion", "archivo": "menu/configuraciones.png", "text_key": "Configuración"},
            {"nombre": "salir", "archivo": "menu/salida.png", "text_key": "Salir"},
            {"nombre": "jugar", "archivo": "menu/juegos.png", "text_key": "Jugar"},
            {"nombre": "inicio", "archivo": "menu/inicio.png", "text_key": "Inicio"},
        ]
        self.iconos = {}  # se llenará con las imágenes escaladas
        self.botones = []  # cada botón: rect, text_key, imagen, escala, alpha

        self.velocidad_fade = 15
        self.ultima_pantalla = None  # para recalcular solo cuando cambia el tamaño

    def _cargar_iconos(self, ancho, alto):
        """Carga y escala los iconos según el tamaño actual de pantalla."""
        tamaño_icono = int(min(ancho, alto) * 0.08)  # 8% del lado menor
        for info in self.iconos_info:
            try:
                ruta = imagen(info["archivo"])
                img = pygame.image.load(ruta).convert_alpha()
                img_esc = pygame.transform.scale(img, (tamaño_icono, tamaño_icono))
                self.iconos[info["nombre"]] = {
                    "imagen": img_esc,
                    "text_key": info["text_key"]
                }
            except Exception as e:
                print(f"[BarraInferior] Error cargando {info['nombre']}: {e}")
                # fallback: superficie de color
                surf = pygame.Surface((tamaño_icono, tamaño_icono), pygame.SRCALPHA)
                surf.fill((100, 100, 200))
                self.iconos[info["nombre"]] = {"imagen": surf, "text_key": info["text_key"]}

    def _crear_botones(self, ancho, alto):
        """Crea los rectángulos de los botones según el tamaño actual de pantalla."""
        altura_barra = int(alto * 0.18)
        margen_inferior = 20
        ancho_barra = int(ancho * 0.8)
        x_barra = (ancho - ancho_barra) // 2
        y_barra = alto - altura_barra - margen_inferior
        espaciado = ancho_barra // len(self.iconos_info)

        botones = []
        for i, info in enumerate(self.iconos_info):
            x = x_barra + i * espaciado
            rect = pygame.Rect(x, y_barra, espaciado, altura_barra)
            botones.append({
                "rect": rect,
                "nombre": info["nombre"],
                "text_key": info["text_key"],
                "icono": self.iconos[info["nombre"]]["imagen"],
                "scale": 1.0,
                "alpha": 0
            })
        return botones, (x_barra, y_barra, ancho_barra, altura_barra)

    def actualizar_visibilidad(self, posicion_cursor, alto):
        """Muestra la barra si el cursor está cerca del borde inferior."""
        altura_barra = int(alto * 0.18)
        self.visible = (posicion_cursor[1] > alto - altura_barra)

    def dibujar(self, pantalla, posicion_cursor):
        """Dibuja la barra y sus tooltips, con animaciones."""
        alto = pantalla.get_height()
        ancho = pantalla.get_width()

        # Si la pantalla cambió de tamaño, recargar iconos y botones
        if self.ultima_pantalla != (ancho, alto):
            self._cargar_iconos(ancho, alto)
            self.botones, self.barra_rect = self._crear_botones(ancho, alto)
            self.ultima_pantalla = (ancho, alto)

        if not self.visible:
            return

        # Dibujar fondo de la barra (sombra y barra semitransparente)
        xb, yb, wb, hb = self.barra_rect
        barra_surf = pygame.Surface((wb, hb), pygame.SRCALPHA)
        sombra_surf = pygame.Surface((wb, hb), pygame.SRCALPHA)

        color_madera_trans = (221, 162, 105, 220)
        color_borde_solido = (204, 130, 76, 220)
        color_sombra = (0, 0, 0, 20)

        pygame.draw.rect(sombra_surf, color_sombra, (0, 0, wb, hb), border_radius=25)
        pygame.draw.rect(barra_surf, color_madera_trans, (0, 0, wb, hb), border_radius=25)
        pygame.draw.rect(barra_surf, color_borde_solido, (0, 0, wb, hb), 3, border_radius=25)

        pantalla.blit(sombra_surf, (xb, yb + 5))
        pantalla.blit(barra_surf, (xb, yb))

        # Dibujar botones
        for boton in self.botones:
            hover = boton["rect"].collidepoint(posicion_cursor)

            # Escala
            target_scale = 1.25 if hover else 1.0
            boton["scale"] += (target_scale - boton["scale"]) * 0.15

            # Alpha del tooltip
            target_alpha = 255 if hover else 0
            if boton["alpha"] < target_alpha:
                boton["alpha"] = min(target_alpha, boton["alpha"] + self.velocidad_fade)
            elif boton["alpha"] > target_alpha:
                boton["alpha"] = max(target_alpha, boton["alpha"] - self.velocidad_fade)

            # Icono
            img_orig = boton["icono"]
            new_w = int(img_orig.get_width() * boton["scale"])
            new_h = int(img_orig.get_height() * boton["scale"])
            img = pygame.transform.smoothscale(img_orig, (new_w, new_h))
            img_rect = img.get_rect(center=boton["rect"].center)
            if hover:
                img_rect.centery = boton["rect"].centery - 22
            pantalla.blit(img, img_rect)

            # Tooltip (texto traducido)
            if boton["alpha"] > 0:
                texto = config.traductor.t(boton["text_key"])
                texto_surface = config.render_text(texto, config.fuente_muy_pequena, (50, 50, 50))
                tx_surf = pygame.Surface(texto_surface.get_size(), pygame.SRCALPHA)
                tx_surf.blit(texto_surface, (0, 0))
                tx_surf.set_alpha(boton["alpha"])
                tx_rect = tx_surf.get_rect(centerx=boton["rect"].centerx,
                                           top=boton["rect"].centery + 50)
                pantalla.blit(tx_surf, tx_rect)

    def manejar_clic(self, posicion_cursor, clic_activo):
        """Retorna el estado al que debe navegarse si se hizo clic en un botón."""
        if not self.visible or not clic_activo:
            return None
        for boton in self.botones:
            if boton["rect"].collidepoint(posicion_cursor):
                if self.camara:
                    self.camara.pausar_cursor()
                texto_tts = config.traductor.t(boton["text_key"])
                if self.decir_texto:
                    self.decir_texto(texto_tts)
                print(f"Barra: {boton['nombre']} - sesión {self.ID_sesion}")

                # Mapeo nombre -> estado
                estado = {
                    "instrucciones": "instrucciones",
                    "configuracion": "configuracion",
                    "salir": "menu_principal",
                    "inicio": "menu_principal",
                    "jugar": "juegos"
                }.get(boton["nombre"])
                return estado
        return None