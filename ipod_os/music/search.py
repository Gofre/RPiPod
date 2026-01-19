import pygame
from config import *
from utils import cargar_fuente, dibujar_header, truncar_texto, dibujar_scrollbar, dibujar_lista_elementos

class SearchScreen:
    def __init__(self, sp_client):
        self.sp = sp_client
        self.font_small = cargar_fuente(TEXT_SMALL)
        self.font_big = cargar_fuente(TEXT_BIG)
        
        # Caracteres disponibles para rotar
        self.caracteres = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        
        self.items_visibles = 7

        self.reset_state()
        self.buscar()

    def reset_state(self):
        """Reinicia la pantalla a su estado original (Letra A, sin query)"""
        self.char_idx = 1 # Empezamos en la 'A'
        self.query = ""
        self.modo_foco = 'busqueda'
        self.resultados = []
        self.idx_res = 0
        self.scroll_inicio = 0

    def buscar(self):
        # Concatenamos la query confirmada + el caracter actual para buscar en tiempo real
        busqueda_actual = self.query + self.caracteres[self.char_idx]
        if not busqueda_actual.strip():
            self.resultados = []
            return
        
        try:
            # Buscamos por categorias como hace dupontgu
            res = self.sp.search(q=busqueda_actual, limit=10, type='track,artist,album,playlist,show')
            self.resultados = []
            
            categorias = [
                ('artists', 'ARTISTS'), 
                ('tracks', 'SONGS'), 
                ('albums', 'ALBUMS'), 
                ('playlists', 'PLAYLISTS'), 
                ('shows', 'PODCASTS'), 
                ('episodes', 'EPISODES')
            ]

            # Categorias
            for cat_key, label in categorias:
                items = res.get(cat_key, {}).get('items', [])
                if items:
                    self.resultados.append({'tipo': 'header', 'nombre': label})
                    for i in items:
                        if not i: continue

                        nombre = i['name']
                        if cat_key == 'tracks': nombre += f" - {i['artists'][0]['name']}"
                        self.resultados.append({
                            'tipo': 'item',
                            'nombre': nombre,
                            'uri': i['uri'],
                            'id': i['id'],
                            'subtipo': cat_key[:-1]
                        })
            self.idx_res = 0
            self.scroll_inicio = 0
        except:
            pass

    def mover_arriba(self):
        if self.modo_foco == 'busqueda':
            self.char_idx = (self.char_idx - 1) % len(self.caracteres)
            self.buscar()
        else:
            # Lógica para la LISTA: Buscar el anterior ítem que NO sea header
            nuevo_idx = self.idx_res - 1
            
            # Retrocedemos mientras sea un header (saltar headers hacia arriba)
            while nuevo_idx >= 0 and self.resultados[nuevo_idx]['tipo'] == 'header':
                nuevo_idx -= 1
            
            # Si encontramos un índice válido (>=0) y distinto del actual
            if nuevo_idx >= 0:
                self.idx_res = nuevo_idx
                
                # Ajustar scroll si nos salimos por arriba
                if self.idx_res < self.scroll_inicio:
                    self.scroll_inicio = self.idx_res

            else:
                # Si estamos intentando subir más allá del primer elemento,
                # significa que estamos en el tope. Forzamos scroll a 0
                # para que se vea el Header (ej: "ARTISTS")
                self.scroll_inicio = 0

    def mover_abajo(self):
        if self.modo_foco == 'busqueda':
            self.char_idx = (self.char_idx + 1) % len(self.caracteres)
            self.buscar()
        else:
            # Lógica para la LISTA: Buscar el siguiente ítem que NO sea header
            nuevo_idx = self.idx_res + 1
            total = len(self.resultados)
            
            # Avanzamos mientras sea un header (saltar headers hacia abajo)
            while nuevo_idx < total and self.resultados[nuevo_idx]['tipo'] == 'header':
                nuevo_idx += 1
            
            # Si encontramos un índice válido dentro del rango
            if nuevo_idx < total:
                self.idx_res = nuevo_idx
                
                # Ajustar scroll si nos salimos por abajo
                # Si el índice seleccionado está más allá de lo visible...
                if self.idx_res >= self.scroll_inicio + self.items_visibles:
                    # Movemos el inicio para que el nuevo ítem sea el último visible
                    self.scroll_inicio = self.idx_res - self.items_visibles + 1

    def avanzar_caracter(self):
        """Confirmar letra actual y pasar a la siguiente (Flecha Derecha)"""
        if self.modo_foco == 'busqueda':
            self.query += self.caracteres[self.char_idx]
            self.char_idx = 1 # Volver a la 'A' para la siguiente posición
            self.buscar()

    def borrar_caracter(self):
        """Borrar última letra confirmada (Flecha Izquierda)"""
        if self.modo_foco == 'busqueda' and len(self.query) > 0:
            self.query = self.query[:-1]
            self.buscar()

    def pulsar_enter(self):
        if self.modo_foco == 'busqueda':
            if self.resultados:
                # Cambiar foco a lista
                self.modo_foco = 'lista'
                
                # Buscar el PRIMER ítem válido (no header)
                self.idx_res = 0
                while self.idx_res < len(self.resultados) and self.resultados[self.idx_res]['tipo'] == 'header':
                    self.idx_res += 1
                
                # Si por lo que sea todo son headers (raro), volvemos a 0 o manejamos error
                if self.idx_res >= len(self.resultados): 
                    self.idx_res = 0 # Fallback
            return None
        else:
            return self.resultados[self.idx_res]

    def retroceder(self):
        """
        Gestiona el botón ESCAPE/MENU.
        """
        if self.modo_foco == 'lista':
            self.modo_foco = 'busqueda'
            return False # Se queda en Search pero sube al texto
        else:
            # Si vamos a salir de la pantalla, la reseteamos para la próxima vez
            self.reset_state()
            self.buscar() # Buscamos la 'A' por defecto para dejarlo listo
            return True
        return True # Sale al menú anterior

    def dibujar(self, pantalla, estado_play):
        pantalla.fill(NEGRO)
        
        # --- 1. PREPARAR EL TEXTO PERSONALIZADO ---
        # Creamos una superficie temporal para montar nuestro texto bicolor
        font = self.font_big
        char_actual = self.caracteres[self.char_idx]

        # Renderizamos las partes
        surf_query = font.render(self.query, ANTIALIASING, VERDE_SPOTIFY)

        if self.modo_foco == 'busqueda':
            surf_char = font.render(char_actual, ANTIALIASING, NEGRO)
        else:
            surf_char = font.render(char_actual, ANTIALIASING, VERDE_SPOTIFY)

        # Calculamos tamaño total de la etiqueta
        w_total = surf_query.get_width() + surf_char.get_width()
        h_total = max(surf_query.get_height(), surf_char.get_height())

        # Creamos la superficie (transparente por defecto o rellena de negro)
        # Usamos flags=pygame.SRCALPHA para transparencia si hiciera falta, 
        # pero con fondo negro (NEGRO) va bien.
        header_surf = pygame.Surface((w_total, h_total))
        header_surf.fill(NEGRO)

        # Pintamos la query
        header_surf.blit(surf_query, (0, 0))

        # Pintamos el carácter (con fondo verde si toca)
        dest_char_x = surf_query.get_width()

        if self.modo_foco == 'busqueda':
            # 1. Creamos el rectángulo base con el tamaño exacto de la letra
            bg_rect = pygame.Rect(dest_char_x, 0, surf_char.get_width(), h_total)
            
            # 2. USAMOS LAS VARIABLES DE CONFIGURACIÓN para "inflarlo"
            # inflate(x, y) añade x/2 a cada lado y y/2 arriba/abajo
            bg_rect = bg_rect.inflate(EXTRA_ANCHO_CURSOR_BUSQUEDA, EXTRA_ALTO_CURSOR_BUSQUEDA)
            
            # 3. Recentramos el rectángulo inflado sobre la posición original de la letra
            bg_rect.center = (dest_char_x + surf_char.get_width()//2, h_total//2)
            
            pygame.draw.rect(header_surf, VERDE_SPOTIFY, bg_rect)
            
        # Pintamos la letra
        header_surf.blit(surf_char, (dest_char_x, 0))
        
        # --- 2. LLAMAR AL HEADER COMÚN ---
        # Le pasamos nuestra imagen 'header_surf' y él pone los iconos y centra
        dibujar_header(pantalla, header_surf, estado_play)

        # --- 3. RESULTADOS ---
        if not self.resultados:
            msg = self.font_small.render("Rotate to search...", ANTIALIASING, GRIS_TEXTO)
            pantalla.blit(msg, (ANCHO//2 - msg.get_width()//2, 60))
        else:
            # Determinamos si la lista tiene el foco visual
            lista_activa = (self.modo_foco == 'lista')
            
            dibujar_lista_elementos(
                pantalla=pantalla,
                opciones=self.resultados,
                seleccion=self.idx_res,
                inicio_scroll=self.scroll_inicio,
                items_visibles=self.items_visibles,
                fuente=self.font_big,  # Usamos la FUENTE GRANDE como pediste
                tiene_foco=lista_activa
            )