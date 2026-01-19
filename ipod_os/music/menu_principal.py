import pygame
from config import *
from utils import cargar_fuente, dibujar_header, truncar_texto, dibujar_scrollbar, dibujar_lista_elementos, obtener_ip

class MenuPantalla:
    def __init__(self, titulo, opciones, sp_client=None, tipo_carga=None, id_padre=None, color_tema=VERDE_SPOTIFY):
        self.titulo = titulo
        self.opciones = opciones 
        self.sp = sp_client
        self.tipo_carga = tipo_carga # 'artistas', 'playlists'
        self.id_padre = id_padre
        self.color_tema = color_tema

        self.datos_cargados = False
        self.seleccionado = 0
        self.indice_inicio = 0 # Scroll
        self.items_visibles = 7
        self.font_item = cargar_fuente(TEXT_BIG)

    def cargar_datos(self):
        # Evitamos cargar si ya tenemos datos o no hay cliente Spotify
        if self.datos_cargados or not self.sp: return
        
        try:
            nuevas = []
            
            # --- FAV ARTISTS ---
            if self.tipo_carga == 'artistas':
                print("Descargando artistas...")
                res = self.sp.current_user_followed_artists(limit=50)
                nuevas = [{'nombre': i['name'], 'uri': i['uri'], 'type': 'artist'} for i in res['artists']['items']]
            
            # --- FAV ALBUMS ---
            elif self.tipo_carga == 'albums':
                print("Descargando albumes guardados...")
                res = self.sp.current_user_saved_albums(limit=50)
                # OJO: Aqui la estructura es item['album']['name']
                nuevas = [{'nombre': i['album']['name'], 'uri': i['album']['uri'], 'type': 'album'} for i in res['items']]

            # --- MY PLAYLISTS ---
            elif self.tipo_carga == 'playlists':
                print("Descargando playlists...")
                res = self.sp.current_user_playlists(limit=50)
                nuevas = [{'nombre': i['name'], 'uri': i['uri'], 'type': 'playlist'} for i in res['items']]
            
            # --- NEW RELEASES ---
            elif self.tipo_carga == 'new_releases':
                print("Descargando novedades...")
                res = self.sp.new_releases(limit=50)
                # Aqui la estructura es res['albums']['items']
                nuevas = [{'nombre': i['name'], 'uri': i['uri'], 'type': 'album'} for i in res['albums']['items']]
            
            # --- ALBUMS (ARTIST) ---
            elif self.tipo_carga == 'artist_albums' and self.id_padre:
                print(f"Cargando albumes del artista {self.id_padre}...")
                # include_groups='album,single' para filtrar un poco
                res = self.sp.artist_albums(self.id_padre, limit=50, country="ES", include_groups='album,single')
                nuevas = [{'nombre': i['name'], 'uri': i['uri'], 'type': 'album'} for i in res['items']]

            # --- SONGS (ALBUM) ---
            elif self.tipo_carga == 'album_tracks' and self.id_padre:
                print(f"Cargando canciones del album {self.id_padre}...")
                res = self.sp.album_tracks(self.id_padre, limit=50)
                # Las canciones son 'track', listas para reproducir
                nuevas = [{'nombre': i['name'], 'uri': i['uri'], 'type': 'track'} for i in res['items']]

            # --- SONGS (PLAYLIST) ---
            elif self.tipo_carga == 'playlist_tracks' and self.id_padre:
                print(f"Cargando canciones de playlist {self.id_padre}...")
                res = self.sp.playlist_items(self.id_padre, limit=50)
                # En playlist, la cancion esta dentro de 'track'
                nuevas = []
                for item in res['items']:
                    if item.get('track'): # Verificacion de seguridad # A veces hay items vacios
                        t = item['track']
                        nuevas.append({'nombre': t['name'], 'uri': t['uri'], 'type': 'track'})
            
            # --- SHOWS ---
            elif self.tipo_carga == 'shows':
                print("Descargando shows...")
                res = self.sp.current_user_saved_shows(limit=20)
                nuevas = []
                for item in res['items']:
                    show_obj = item['show']
                    nuevas.append({'nombre': show_obj['name'], 'uri': show_obj['uri'], 'id': show_obj['id'], 'type': 'show'})
            
            # --- EPISODES ---
            elif self.tipo_carga == 'show_episodes':
                print(f"Cargando episodios del show {self.id_padre}...")
                # self.id_padre aquí será el ID del show
                results = self.sp.show_episodes(show_id=self.id_padre, limit=20)
                nuevas = []
                for episode in results['items']:
                    nuevas.append({
                        'type': 'episode',    # Etiqueta para reproducir
                        'nombre': episode['name'], 
                        'uri': episode['uri'],
                        'subtype': 'podcast'
                    })
            
            # --- SETTINGS ---
            elif self.tipo_carga == 'settings':
                nuevas = []
                
                # 1. Mostrar IP (Información)
                mi_ip = obtener_ip() # Función importada de ipod_utils
                nuevas.append({
                    'nombre': f"IP: {mi_ip}",
                    'type': 'info_static', # Tipo especial que no hace nada al clickar
                    'uri': None
                })

                # 2. Selección de dispositivo
                nuevas.append({
                    'nombre': "Spotify Connect",
                    'type': 'menu_devices_list', # Tipo para main.py
                    'uri': None
                })

                # 3. Toggle Shuffle
                # Obtenemos estado actual (esto puede tardar un poco, idealmente se cachea)
                try:
                    pb = self.sp.current_playback()
                    if pb:
                        shuffle_state = pb['shuffle_state']
                    else:
                        # Si no hay playback, asumimos False, pero avisamos
                        print("No hay dispositivo activo para leer Shuffle")
                        shuffle_state = False
                    txt_shuffle = "Shuffle: ON" if shuffle_state else "Shuffle: OFF"
                except:
                    shuffle_state = False
                    txt_shuffle = "Shuffle: ?"

                nuevas.append({
                    'nombre': txt_shuffle,
                    'type': 'setting_toggle',
                    'setting_key': 'shuffle',
                    'current_val': shuffle_state
                })
                
                # 3. Toggle Device (Ejemplo futuro)
                """
                nuevas.append({
                    'nombre': "Device: Raspberry Pi",
                    'type': 'info_static',
                    'uri': None
                })
                """

                # 4. SEPARADOR (Opcional, para que quede bonito)
                nuevas.append({'nombre': "------------------", 'type': 'info_static', 'uri': None})

                # 5. APAGAR SISTEMA
                nuevas.append({
                    'nombre': "Shut Down",
                    'type': 'system_action', # Nuevo tipo para main.py
                    'action': 'shutdown',
                    'uri': None
                })

                # 6. REINICIAR (Opcional, pero muy útil)
                nuevas.append({
                    'nombre': "Reboot",
                    'type': 'system_action',
                    'action': 'reboot',
                    'uri': None
                })
            
            # --- NUEVO BLOQUE: LISTA DE DISPOSITIVOS ---
            elif self.tipo_carga == 'devices_list':
                print("Buscando dispositivos...")
                try:
                    devices = self.sp.devices()
                    nuevas = []
                    
                    for d in devices['devices']:
                        # Marcamos visualmente el activo
                        nombre = d['name']
                        if d['is_active']:
                            nombre = f"* {nombre}" # Asterisco para el activo
                        
                        nuevas.append({
                            'nombre': nombre,
                            'id': d['id'],
                            'type': 'device_action', # Tipo para main.py
                            'is_active': d['is_active']
                        })
                    
                    if not nuevas:
                        nuevas.append({'nombre': "No devices found", 'type': 'info_static'})
                    
                except Exception as e:
                    print(f"Error devices: {e}")
                    nuevas = [{'nombre': "Error loading", 'type': 'info_static'}]

            if nuevas:
                self.opciones = nuevas
            else:
                self.opciones = ["Vacío"] # Para saber si cargo pero no habia nada
        
        except Exception as e:
            print(f"Error cargando {self.tipo_carga}: {e}")
            self.opciones = ["Error de conexion"]
            
        self.datos_cargados = True

    def mover_arriba(self):
        if self.seleccionado > 0:
            self.seleccionado -= 1
            if self.seleccionado < self.indice_inicio:
                self.indice_inicio = self.seleccionado

    def mover_abajo(self):
        if self.seleccionado < len(self.opciones) - 1:
            self.seleccionado += 1
            if self.seleccionado >= self.indice_inicio + self.items_visibles:
                self.indice_inicio += 1

    def obtener_seleccion(self):
        if not self.opciones: return None
        return self.opciones[self.seleccionado]

    def dibujar(self, pantalla, estado_play):
        
        # Si es un menu dinamico y esta vacio, cargamos
        
        if self.tipo_carga and not self.datos_cargados:
            pantalla.fill(NEGRO)
            dibujar_header(pantalla, truncar_texto(self.titulo, 20), estado_play, self.color_tema)
            t = self.font_item.render("Loading...", ANTIALIASING, self.color_tema)
            pantalla.blit(t, (100, 100))
            pygame.display.flip() # Forzamos refresco para que se vea el "Loading"
            self.cargar_datos()
        
        #if not self.datos_cargados and self.sp:
        #    self.cargar_datos()
        
        pantalla.fill(NEGRO)

        # Header
        dibujar_header(pantalla, truncar_texto(self.titulo, 20), estado_play, self.color_tema)
        
        # --- DIBUJADO DE LISTA UNIFICADO ---
        dibujar_lista_elementos(
            pantalla=pantalla,
            opciones=self.opciones,
            seleccion=self.seleccionado,
            inicio_scroll=self.indice_inicio,
            items_visibles=self.items_visibles,
            fuente=self.font_item, # Pasamos la fuente configurada en __init__
            tiene_foco=True,       # El menú siempre tiene el foco
            color_tema=self.color_tema
        )