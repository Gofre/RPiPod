import pygame
import threading
import time
import requests
import io
import traceback
import numpy as np
from config import *
from utils import cargar_fuente, dibujar_header, truncar_texto, formato_tiempo, procesar_caratula_retro, descargar_imagen_url
from twitch.twitch_chat import TwitchChat

class PantallaNowPlaying:
    def __init__(self, sp_client):
        self.sp = sp_client
        self.font_big = cargar_fuente(TEXT_BIG)
        self.font_small = cargar_fuente(TEXT_SMALL)
        
        self.theme_color = VERDE_SPOTIFY
        self.source_mode = 'spotify'

        # Datos de la canción
        self.track = "Loading..."
        self.artist = ""
        self.album = ""       # NUEVO
        self.track_no = 0     # NUEVO
        self.total_tracks = 0 # NUEVO
        
        self.cover_img = None
        self.cover_url = ""
        self.duration = 0
        self.progress = 0
        self.is_playing = False
        
        # Control de actualización (solo para Spotify)
        self.last_update = 0
        self.update_interval = 1000
        
        # MODO DE VISTA: 0 = Carátula, 1 = Texto Detallado (Estilo iPod Clásico)
        self.modo_vista = 0

        # Imagen por defecto (puedes crear un placeholder.png si quieres)
        self.default_cover = pygame.Surface((128, 128))
        self.default_cover.fill(GRIS_OSCURO) # Gris oscuro

        # CHAT CLIENT
        self.chat = TwitchChat()
        self.show_chat = True # Flag por si quieres ocultarlo con algún botón
        
        # Fuente MUY pequeña para el chat (necesitamos que quepan cosas)
        # Si Chicago.ttf escala mal, usaremos SysFont
        self.font_chat = cargar_fuente(12)

    ##################################
    # FUNCIONES PARA CAMBIAR DE MODO #
    ##################################

    def set_mode_spotify(self):
        self.chat.disconnect()
        self.source_mode = 'spotify'
        self.theme_color = VERDE_SPOTIFY
        self.update() # Forzar actualización inmediata
    
    def set_mode_twitch(self, channel_name, game_name, cover_bytes=None):
        self.chat.disconnect()
        self.source_mode = 'twitch'
        self.theme_color = MORADO_TWITCH
        self.track = channel_name
        self.artist = "Live Stream"
        self.album = game_name if game_name else ""
        self.duration = 0
        self.progress = 0
        self.is_playing = True
        self.cargar_caratula(data_bytes=cover_bytes)
        self.chat.connect(channel_name)

    def set_mode_radio(self, station_name):
        self.chat.disconnect()
        self.source_mode = 'radio'
        self.theme_color = NARANJA_RADIO
        self.track = station_name
        self.artist = "Live Radio"
        self.album = "FM Stream"
        self.duration = 0
        self.progress = 0
        self.is_playing = True
        self.cover_img = None # O podrías poner un icono de radio
    
    def set_mode_local(self, titulo, artista, album, cover_bytes=None):
        self.chat.disconnect()
        self.source_mode = 'local'
        self.theme_color = AZUL_LOCAL
        self.track = titulo
        self.artist = artista
        self.album = album
        self.duration = 0 # VLC no siempre da la duración fácil, por ahora 0
        self.progress = 0
        self.is_playing = True
        self.cargar_caratula(data_bytes=cover_bytes)
    
    def cambiar_vista(self):
        """Alterna entre ver la carátula o ver el texto detallado"""
        self.modo_vista = 1 if self.modo_vista == 0 else 0

    ##################
    # SPOTIFY UPDATE #
    ##################

    def update(self):

        if self.source_mode != 'spotify': return

        current_time = pygame.time.get_ticks()
        if current_time - self.last_update > self.update_interval:
            self.last_update = current_time
            try:
                pb = self.sp.current_playback(additional_types='track,episode')
                if pb and pb.get('item'):
                    item = pb['item']
                    self.is_playing = pb['is_playing']
                    self.progress = pb['progress_ms']
                    self.duration = item['duration_ms']
                    
                    item_type = item.get('type') # track/episode

                    if item_type == 'track':

                        self.track = item['name']
                        self.artist = item['artists'][0]['name']
                        self.album = item['album']['name']
                        self.track_no = item['track_number']
                        self.total_tracks = item['album']['total_tracks']
                        images = item['album']['images']
                        
                    elif item_type == 'episode':
                        self.track = item['name']
                        self.artist = item['show']['publisher']
                        self.album = item['show']['name']
                        images = item['images'] # A veces están en el root del item
                        if not images:
                            images = item['show']['images'] # A veces en el show
                        
                        self.track_no = 0 # No suelen tener número de pista fiable
                        self.total_tracks = 0
                    
                    # Carátula (Solo descargamos si cambia)
                    url = images[0]['url'] if images else None
                    if url and url != self.cover_url:
                        self.cover_url = url
                        self.cargar_caratula(url=url)
                else:
                    self.is_playing = False
                    
            except Exception as e:
                print(f"Error update: {e}")

    def cargar_caratula(self, url=None, data_bytes=None):
        """
        Método inteligente:
        - Si recibe data_bytes: Procesa al instante (Local/Twitch).
        - Si recibe url: Lanza un hilo para no bloquear (Spotify).
        """
        # CASO 1: Bytes directos (Local o Twitch pre-descargado)
        if data_bytes:
            self._procesar_bytes_imagen(data_bytes)
            return

        # CASO 2: URL (Spotify) -> Threading
        if url:
            def _thread_download():
                # Usamos la función de utils que ya tienes
                bytes_descargados = descargar_imagen_url(url)
                if bytes_descargados:
                    self._procesar_bytes_imagen(bytes_descargados)
            
            threading.Thread(target=_thread_download, daemon=True).start()
            return
            
        # CASO 3: Nada
        self.cover_img = None

    def _procesar_bytes_imagen(self, data):
        """Convierte bytes -> Imagen Pygame -> Filtro Retro"""
        if not data: 
            self.cover_img = None
            return
        try:
            img = pygame.image.load(io.BytesIO(data))
            self.cover_img = procesar_caratula_retro(img, color_tema=self.theme_color)
        except Exception as e:
            print(f"Error procesando imagen: {e}")
            self.cover_img = None

    ############
    # DIBUJADO #
    ############

    def dibujar_barra_progreso(self, pantalla, y_pos, ancho_barra=ANCHO-40):
        altura_barra = 11
        radio_borde = 3
        grosor_outline = 1 # Grosor de la línea de la caja

        x_pos = (ANCHO - ancho_barra) // 2
        # Rectángulo total que ocupará la barra
        rect_contenedor = (x_pos, y_pos, ancho_barra, altura_barra)
        
        # --- 1. DIBUJAR EL RELLENO (Primero, y cuadrado) ---
        if self.duration > 0 and self.progress > 0:
            pct = self.progress / self.duration
            ancho_relleno = int(ancho_barra * pct)
            
            # Para que quede perfecto, el relleno rectangular debe dibujarse 
            # ligeramente por dentro del outline.
            # Desplazamos X e Y por el grosor, y reducimos ancho y alto por el doble del grosor.
            rect_relleno = (
                x_pos + grosor_outline, 
                y_pos + grosor_outline,
                max(0, ancho_relleno - (grosor_outline * 2)), # Asegurar que no sea negativo
                altura_barra - (grosor_outline * 2)
            )

            # Dibujamos solo si tiene anchura válida.
            # border_radius=0 (por defecto) asegura esquinas rectas.
            if rect_relleno[2] > 0:
                pygame.draw.rect(pantalla, self.theme_color, rect_relleno)

        # --- 2. DIBUJAR LA CAJA OUTLINE (Encima, y redondeada) ---
        # Usamos 'width=grosor_outline' para que sea hueca
        # Al dibujarla después, "recorta" visualmente las esquinas del relleno.
        pygame.draw.rect(pantalla, self.theme_color, rect_contenedor, width=grosor_outline, border_radius=radio_borde)
            
        # --- TIEMPOS (IGUAL QUE ANTES) ---
        alineado_y = 15 # Un poco más abajo de la barra
        
        # Tiempo actual
        txt_actual = formato_tiempo(self.progress)
        s_actual = self.font_big.render(txt_actual, ANTIALIASING, self.theme_color)
        pantalla.blit(s_actual, (x_pos, y_pos + alineado_y))
        
        # Tiempo restante
        restante = self.duration - self.progress
        txt_restante = "-" + formato_tiempo(restante)
        s_restante = self.font_big.render(txt_restante, ANTIALIASING, self.theme_color)
        pantalla.blit(s_restante, (x_pos + ancho_barra - s_restante.get_width(), y_pos + alineado_y))

    def dibujar(self, pantalla, estado_play):
        self.update()
        pantalla.fill(NEGRO)
        
        # Título Contexto (Header)
        # En el iPod original solía poner el nombre del Album o "Now Playing"
        # Usaremos el nombre del Álbum si cabe, o "Now Playing"
        #titulo_header = self.album if len(self.album) < 20 else "Now Playing"
        titulo_header = "Now Playing"
        dibujar_header(pantalla, titulo_header, self.is_playing, self.theme_color)

        # --- VISTA 0: CARÁTULA (Tu diseño anterior) ---
        if self.modo_vista == 0:

            if self.source_mode == 'twitch' and self.show_chat:
                # Ocupamos todo el espacio debajo del header
                y_inicio = ALTURA_HEADER 
                alto_chat = ALTO - ALTURA_HEADER
                
                # Llamamos a dibujar chat ocupando todo el resto de la pantalla
                self._dibujar_chat(pantalla, 0, y_inicio, ANCHO, alto_chat)
                
                # IMPORTANTE: Hacemos return aquí para que NO dibuje nada más
                # (ni carátula, ni títulos, ni barras de progreso)
                return

            if self.source_mode == 'radio':
                self._dibujar_radio_placeholder(pantalla, 75, 120)
                pygame.draw.rect(pantalla, GRIS_PIXEL, (10, 58, 128, 128), 1)

            elif self.cover_img:
                pantalla.blit(self.cover_img, (10, 58))
                pygame.draw.rect(pantalla, self.theme_color, (10, 58, 128, 128), 1)
            else:
                pygame.draw.rect(pantalla, GRIS_PIXEL, (10, 58, 128, 128), 1)
            
            # Textos laterales
            t_track = truncar_texto(self.track, 13)
            t_artist = truncar_texto(self.artist, 13)
            t_album = truncar_texto(self.album, 13)
            pantalla.blit(self.font_big.render(t_track, ANTIALIASING, self.theme_color), (150, 75))
            pantalla.blit(self.font_big.render(t_artist, ANTIALIASING, self.theme_color), (150, 75 + 32))
            pantalla.blit(self.font_big.render(t_album, ANTIALIASING, self.theme_color), (150, 75 + 32 + 32))
            
            # Barra simple
            """
            if self.duration > 0: pct = self.progress / self.duration
            else: pct = 0
            pygame.draw.rect(pantalla, GRIS_PIXEL, (160, 155, 140, 8))
            pygame.draw.rect(pantalla, self.theme_color, (160, 155, int(140*pct), 8))
            """

        # --- VISTA 1: DETALLE TEXTO (Estilo iPod Foto adjunta) ---
        elif self.modo_vista == 1:
            
            # Información Central (Título, Artista, Álbum)
            center_x = ANCHO // 2

            # Coordenadas equidistantes
            # Tenemos espacio entre Y=60 y Y=160 (aprox 100px)
            y_cancion = 80
            y_artista = y_cancion + 32  # +32px
            y_album   = y_artista + 32 # +32px

            start_y = 65 # Altura inicial

            # Limite caracteres más estricto por ser fuente grande
            limite_chars = 24
            
            # Título (Grande y Brillante)
            lbl_title = truncar_texto(self.track, limite_chars) # Un poco más de margen al no haber foto
            s_title = self.font_big.render(lbl_title, ANTIALIASING, self.theme_color)
            r_title = s_title.get_rect(center=(center_x, y_cancion))
            pantalla.blit(s_title, r_title)
            
            # Artista (Pequeño)
            lbl_artist = truncar_texto(self.artist, limite_chars)
            s_artist = self.font_big.render(lbl_artist, ANTIALIASING, self.theme_color)
            r_artist = s_artist.get_rect(center=(center_x, y_artista))
            pantalla.blit(s_artist, r_artist)
            
            # Álbum (Pequeño)
            lbl_album = truncar_texto(self.album, limite_chars)
            s_album = self.font_big.render(lbl_album, ANTIALIASING, self.theme_color) # Gris para diferenciar
            r_album = s_album.get_rect(center=(center_x, y_album))
            pantalla.blit(s_album, r_album)
        
        # Contador de Pista (Esquina superior izquierda)
        # "1 of 53"
        txt_counter = f"{self.track_no} of {self.total_tracks}"
        s_counter = self.font_small.render(txt_counter, ANTIALIASING, self.theme_color)
        pantalla.blit(s_counter, (10, ALTURA_HEADER + 10))

        # Barra de Progreso y Tiempos
        # La ponemos abajo, estilo iPod classic
        if self.source_mode == 'spotify':
            self.dibujar_barra_progreso(pantalla, y_pos=195, ancho_barra=290)
    
    def _dibujar_radio_placeholder(self, pantalla, x, y):
        """Dibuja un icono de radio retro procedimentalmente"""
        # Caja principal (Cuerpo radio)
        rect_body = pygame.Rect(0, 0, 100, 60)
        rect_body.center = (x, y + 10)
        pygame.draw.rect(pantalla, self.theme_color, rect_body, 2) # Borde
        
        # Asa de transporte
        pygame.draw.line(pantalla, self.theme_color, (rect_body.left + 10, rect_body.top), (rect_body.left + 10, rect_body.top - 15), 2)
        pygame.draw.line(pantalla, self.theme_color, (rect_body.right - 10, rect_body.top), (rect_body.right - 10, rect_body.top - 15), 2)
        pygame.draw.line(pantalla, self.theme_color, (rect_body.left + 10, rect_body.top - 15), (rect_body.right - 10, rect_body.top - 15), 2)
        
        # Antena
        pygame.draw.line(pantalla, self.theme_color, (rect_body.right - 20, rect_body.top), (rect_body.right - 10, rect_body.top - 30), 2)
        
        # Altavoz (Círculo izquierdo)
        pygame.draw.circle(pantalla, self.theme_color, (rect_body.left + 30, rect_body.centery), 18, 2)
        # Rejilla altavoz (puntos)
        pygame.draw.circle(pantalla, self.theme_color, (rect_body.left + 30, rect_body.centery), 2)
        
        # Dial (Rectángulo derecho)
        pygame.draw.rect(pantalla, self.theme_color, (rect_body.left + 60, rect_body.top + 10, 30, 40), 1)
        # Linea dial
        pygame.draw.line(pantalla, ROJO_ERROR, (rect_body.left + 60, rect_body.top + 25), (rect_body.left + 89, rect_body.top + 25), 2)
    
    def _dibujar_chat2(self, pantalla, x, y, w, h):
        """Dibuja el overlay del chat"""
        # 1. Fondo semitransparente (Negro al 70%)
        #s = pygame.Surface((w, h))
        #s.set_alpha(180) 
        #s.fill((0,0,0))
        #pantalla.blit(s, (x, y))
        
        # 2. Obtener mensajes
        msgs = self.chat.get_messages()
        
        line_height = 12 # Altura de cada línea de texto
        margen_izq = 5
        start_y = y + h - (len(msgs) * line_height) - 5 # Empezar desde abajo
        
        for msg in msgs:
            # Formato: "User: Mensaje"
            
            # Dibujar Usuario (en color del tema o negrita)
            user_surf = self.font_chat.render(f"{msg['user']}: ", True, self.theme_color)
            pantalla.blit(user_surf, (x + margen_izq, start_y))
            
            # Dibujar Mensaje (Blanco)
            # Calculamos offset X para que el mensaje empiece después del usuario
            user_width = user_surf.get_width()
            
            # Truncamos mensaje si es muy largo para que no se salga
            # (Una solución simple, lo ideal sería word-wrap pero es costoso)
            chars_max = int((w - user_width - 10) / 6) 
            msg_clean = truncar_texto(msg['text'], chars_max)

            msg_surf = self.font_chat.render(msg_clean, True, (255, 255, 255))
            pantalla.blit(msg_surf, (x + margen_izq + user_width, start_y))
            
            start_y += line_height
    
    # En now_playing.py

    def _dibujar_chat(self, pantalla, x, y, w, h):
        msgs = self.chat.get_messages()
        
        line_height = 12 # Altura por línea de texto
        margen_izq = 6
        ancho_util = w - (margen_izq * 2) # Margen a ambos lados
        
        # Empezamos a dibujar desde abajo del todo
        current_y = y + h - line_height - 5
        
        # Recorremos mensajes del más NUEVO al más VIEJO (reversed)
        for msg in reversed(msgs):
            if current_y < y: break # Si nos salimos por arriba, paramos
            
            # 1. Preparar Usuario
            user_str = f"{msg['user']}: "
            user_surf = self.font_chat.render(user_str, True, msg['color']) # Usamos el color guardado
            user_width = user_surf.get_width()
            
            # 2. Calcular espacio restante en la primera línea para el texto
            ancho_para_texto_linea1 = ancho_util - user_width
            
            # 3. Dividir el mensaje en líneas
            # OJO: La primera línea tiene menos espacio porque está el usuario
            # Las siguientes líneas tienen todo el ancho
            
            todas_las_lineas = []
            palabras = msg['text'].split(' ')
            linea_actual = []
            es_primera_linea = True
            
            for palabra in palabras:
                ancho_limite = ancho_para_texto_linea1 if es_primera_linea else ancho_util
                prueba = ' '.join(linea_actual + [palabra])
                
                if self.font_chat.size(prueba)[0] <= ancho_limite:
                    linea_actual.append(palabra)
                else:
                    todas_las_lineas.append(' '.join(linea_actual))
                    linea_actual = [palabra]
                    es_primera_linea = False # A partir de aquí tenemos todo el ancho
            
            if linea_actual:
                todas_las_lineas.append(' '.join(linea_actual))
            
            # 4. Dibujar de abajo a arriba
            # Invertimos las líneas del mensaje para dibujar primero la última parte (que va más abajo)
            for i, linea_txt in enumerate(reversed(todas_las_lineas)):
                if current_y < y: break
                
                txt_surf = self.font_chat.render(linea_txt, True, (255, 255, 255))
                
                # Si es la primera línea del mensaje (que aquí es la última en procesarse por el reversed)
                # Dibujamos usuario + texto
                if i == len(todas_las_lineas) - 1:
                    pantalla.blit(user_surf, (x + margen_izq, current_y))
                    pantalla.blit(txt_surf, (x + margen_izq + user_width, current_y))
                else:
                    # Es una línea de continuación -> Dibujamos con un pequeño sangrado
                    pantalla.blit(txt_surf, (x + margen_izq, current_y))
                
                current_y -= line_height # Subimos una línea
            
            # Un pequeño espacio extra entre mensajes distintos
            current_y -= 4

    def _dividir_texto_en_lineas(self, texto, fuente, max_ancho):
        """
        Divide un texto en varias líneas para que quepan en max_ancho.
        Devuelve una lista de strings.
        """
        palabras = texto.split(' ')
        lineas = []
        linea_actual = []
        
        for palabra in palabras:
            # Probamos a añadir la palabra a la línea actual
            linea_test = ' '.join(linea_actual + [palabra])
            ancho_test = fuente.size(linea_test)[0]
            
            if ancho_test <= max_ancho:
                linea_actual.append(palabra)
            else:
                # Si la línea ya tenía algo, la guardamos y empezamos nueva
                if linea_actual:
                    lineas.append(' '.join(linea_actual))
                    linea_actual = [palabra]
                else:
                    # Si la palabra sola ya es más ancha que la pantalla (muy raro),
                    # la metemos igual para no perderla (o la cortaríamos)
                    lineas.append(palabra)
                    linea_actual = []
        
        # Añadir la última línea pendiente
        if linea_actual:
            lineas.append(' '.join(linea_actual))
            
        return lineas