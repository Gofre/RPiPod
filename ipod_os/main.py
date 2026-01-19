import pygame
import spotipy
import os
import threading
from spotipy.oauth2 import SpotifyOAuth

# Importamos nuestros modulos propios
from config import *
from utils import comprobar_bluetooth_loop
from music.menu_principal import MenuPantalla
from music.now_playing import PantallaNowPlaying
from music.search import SearchScreen
from radio.radio_app import RadioApp
from music.local_player import LocalPlayer
from twitch.twitch_app import TwitchPlayer

# --- CONFIGURACION INICIAL ---
pygame.init()
pygame.mouse.set_visible(False)
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("WafflePod")

# --- INICIALIZAR API ---
def iniciar_spotify():
    scope = "user-library-read user-read-playback-state user-modify-playback-state user-follow-read"
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=scope,
        open_browser=False,
        cache_path=CACHE_PATH
    ))

# Iniciar Spotify
print("Conectando a Spotify...")
sp = iniciar_spotify()

# Iniciar Reproductor local
app_local_player = LocalPlayer()

# Iniciar Radio
radio = RadioApp()

# Iniciar Twitch
twitch = TwitchPlayer()

# --- ESTADO GLOBAL ---
global_is_playing = False # Estado inicial
last_global_check = 0
GLOBAL_CHECK_INTERVAL = 3000 # Comprobar estado cada 3 seg (menos agresivo)

# --- DEFINICION DE PANTALLAS ---
# Se crean las instancias de las pantallas de Spotify
now_playing = PantallaNowPlaying(sp)
search = SearchScreen(sp)
menu_artistas = MenuPantalla("Artists", [], sp, 'artistas')
menu_albums   = MenuPantalla("Albums", [], sp, 'albums')
menu_playlists = MenuPantalla("Playlists", [], sp, 'playlists')
menu_releases = MenuPantalla("New Releases", [], sp, 'new_releases')
menu_shows = MenuPantalla("Shows", [], sp, 'shows')
menu_settings = MenuPantalla("Settings", [], sp, 'settings')

# Menu de Spotify
spotify_opts = [
    {'nombre': 'Artists', 'destino': menu_artistas},
    {'nombre': 'Albums', 'destino': menu_albums},
    {'nombre': 'Playlists', 'destino': menu_playlists},
    {'nombre': 'New Releases', 'destino': menu_releases},
    {'nombre': 'Shows', 'destino': menu_shows},
    {'nombre': 'Search', 'destino': search},
    {'nombre': 'Now Playing', 'destino': now_playing},
    {'nombre': 'Settings', 'destino': menu_settings}
]
menu_spotify = MenuPantalla("iSpod", spotify_opts)

# Menu del reproductor local
menu_local_player = app_local_player.get_menu_artistas()

# Menu de Radio
menu_radio = radio.get_menu()

# Menu de Twitch
menu_twitch = twitch.get_menu()

# Menu Settings
menu_settings = MenuPantalla("Settings", [], sp, 'settings')

# Menu principal (LAUNCHER)
launcher_opts = [
    {'nombre': 'Spotify', 'destino': menu_spotify}, # Entra a la carpeta de Spotify
    {'nombre': 'Local player', 'destino': menu_local_player},
    {'nombre': 'Radio', 'destino': menu_radio}, # Entra a la Radio
    {'nombre': 'Twitch', 'destino': menu_twitch},
    {'nombre': 'Now Playing', 'destino': now_playing},
    {'nombre': 'Settings', 'destino': menu_settings} # Ajustes globales
]
launcher = MenuPantalla("iPod OS", launcher_opts)

# Pila de navegacion (Stack)
stack = [launcher]

# --- BUCLE PRINCIPAL ---
clock = pygame.time.Clock()
running = True

hilo_bt = threading.Thread(target=comprobar_bluetooth_loop, daemon=True)
hilo_bt.start()
print("Monitor de Bluetooth iniciado en segundo plano.")

while running:

    # 1. ACTUALIZAR ESTADO GLOBAL (PLAY/PAUSE)
    tiempo_actual = pygame.time.get_ticks()
    if tiempo_actual - last_global_check > GLOBAL_CHECK_INTERVAL:
        try:
            # Hacemos una llamada ligera solo para ver si suena
            pb = sp.current_playback()
            if pb:
                global_is_playing = pb['is_playing']
            else:
                global_is_playing = False
        except:
            pass # Si falla (internet, etc), mantenemos el último estado conocido
        last_global_check = tiempo_actual

    # 2. Gestion de Eventos
    for e in pygame.event.get():

        if e.type == pygame.QUIT: 
            running = False
        
        if e.type == pygame.KEYDOWN:

            # TECLAS DE NAVEGACION
            curr = stack[-1] # Pantalla actual
            
            # --- 1. MENU ---
            if isinstance(curr, MenuPantalla):
                if e.key == pygame.K_UP: curr.mover_arriba()
                if e.key == pygame.K_DOWN: curr.mover_abajo()
                if e.key == pygame.K_ESCAPE:
                    if len(stack) > 1: stack.pop()
                
                # TECLA ENTER (Seleccionar)
                if e.key == pygame.K_RETURN:
                    sel = curr.obtener_seleccion()
                    
                    if not sel: continue # Seguridad por si está vacío

                    # 1. Extraemos datos básicos
                    tipo = sel.get('type')
                    uri = sel.get('uri') # Usamos .get() para que no falle si no existe
                    nombre = sel.get('nombre')

                    print(f"DEBUG: Enter en -> {tipo}")

                    # --- PRIORIDAD 1: ACCIONES DE SISTEMA (No requieren URI) ---
                    
                    # A. Cambiar Dispositivo (Tu problema actual)
                    if tipo == 'device_action':
                        print(f"Intentando cambiar al ID: {sel['id']}")
                        try:
                            sp.transfer_playback(device_id=sel['id'], force_play=True)
                            stack.pop() # Volver atrás
                        except Exception as e:
                            print(f"Error cambiando dispositivo: {e}")

                    # B. Abrir lista de dispositivos
                    elif tipo == 'menu_devices_list':
                        stack.append(MenuPantalla("Devices", [], sp, 'devices_list'))

                    # C. Toggle de Settings (Shuffle)
                    elif tipo == 'setting_toggle':
                        if sel.get('setting_key') == 'shuffle':
                            nuevo_estado = not sel['current_val']
                            try:
                                sp.shuffle(nuevo_estado)
                                # Actualización visual inmediata
                                txt = "Shuffle: ON" if nuevo_estado else "Shuffle: OFF"
                                curr.opciones[curr.seleccionado]['nombre'] = txt
                                curr.opciones[curr.seleccionado]['current_val'] = nuevo_estado
                            except Exception as e:
                                print(f"Error Shuffle: {e}")

                    # D. Abrir Settings Menu
                    elif tipo == 'menu_settings':
                        stack.append(MenuPantalla(nombre, [], sp, 'settings'))
                    
                    # A. Apagar / Reiniciar
                    elif tipo == 'system_action':
                        action = sel.get('action')
                        if action == 'shutdown':
                            print("Apagando sistema...")
                            # Dibujamos algo en pantalla antes de morir
                            pantalla.fill((0,0,0))
                            # Podrías poner un texto "Bye Bye..." aquí
                            pygame.display.flip()
                            os.system("sudo shutdown -h now")
                            running = False # Salir del bucle
                            
                        elif action == 'reboot':
                            print("Reiniciando...")
                            os.system("sudo reboot")
                            running = False

                    # --- PRIORIDAD 2: NAVEGACIÓN DE MENÚS PROPIOS ---
                    elif isinstance(sel, dict) and sel.get('destino'):
                        stack.append(sel['destino'])

                    # --- NAVEGACIÓN REPRODUCTOR LOCAL ---
                    # 1. Has pulsado en un Artista -> Mostrar Álbumes
                    elif tipo == 'local_artist':
                        artista = sel['artist_name']
                        # Pedimos a la app local que genere el menú
                        nuevo_menu = app_local_player.get_menu_albums(artista)
                        stack.append(nuevo_menu)

                    # 2. Has pulsado en un Álbum -> Mostrar Canciones
                    elif tipo == 'local_album':
                        artista = sel['artist_name']
                        album = sel['album_name']
                        nuevo_menu = app_local_player.get_menu_tracks(artista, album)
                        stack.append(nuevo_menu)
                    
                    # -> TWITCH CHANNEL
                    elif tipo == 'twitch_channel':
                        canal = sel['channel_name']
                        nombre = sel['nombre']
                        game = sel.get('game', '')
                        url_foto = sel.get('profile_image_url')
                        print(f"Intentando reproducir Twitch: {canal}")
                        
                        # 1. Parar otros audios
                        radio.stop()
                        app_local_player.stop()
                        
                        # 2. Dibujar pantalla de carga rápida (Streamlink tarda 2-3 segs)
                        # Como es proceso bloqueante, pintamos algo antes
                        pantalla.fill((0,0,0))
                        #dibujar_header(pantalla, "Twitch", False)
                        msg = curr.font_item.render("Connecting to", True, MORADO_TWITCH)
                        pantalla.blit(msg, (20, 92))
                        ch = curr.font_item.render(f"{canal}", True, MORADO_TWITCH)
                        pantalla.blit(ch, (20, 120))
                        pygame.display.flip()
                        
                        # 1. Descargar imagen de perfil (si hay URL)
                        # Lo hacemos aquí antes de reproducir para pasársela a la pantalla
                        foto_bytes = None
                        if url_foto:
                            from utils import descargar_imagen_url # Import local
                            foto_bytes = descargar_imagen_url(url_foto)

                        # 2. Intentar reproducir
                        exito = twitch.play(canal)
                        
                        if exito:
                            now_playing.set_mode_twitch(
                                channel_name=nombre,
                                game_name=game,
                                cover_bytes=foto_bytes
                            )
                            stack.append(now_playing)
                        else:
                            print("El canal está offline o error")

                    # --- PRIORIDAD 3: CONTENIDO SPOTIFY (Requiere URI) ---
                    elif uri: 
                        # -> ARTISTA
                        if tipo == 'artist':
                            stack.append(MenuPantalla(nombre, [], sp, 'artist_albums', id_padre=uri))
                        
                        # -> ALBUM
                        elif tipo == 'album':
                            stack.append(MenuPantalla(nombre, [], sp, 'album_tracks', id_padre=uri))
                            
                        # -> PLAYLIST
                        elif tipo == 'playlist':
                            stack.append(MenuPantalla(nombre, [], sp, 'playlist_tracks', id_padre=uri))
                        
                        # -> SHOW (Podcast)
                        elif tipo == 'show':
                            # OJO: Aquí usamos el ID que guardaste en menu_principal, no solo URI
                            el_id = sel.get('id', uri) 
                            stack.append(MenuPantalla(nombre, [], sp, 'show_episodes', id_padre=el_id))

                        # -> REPRODUCIR (Track o Episode)
                        elif tipo == 'track' or tipo == 'episode':
                            print(f"Reproduciendo: {nombre}")
                            try:
                                radio.stop()
                                app_local_player.stop()
                                twitch.stop()
                                sp.start_playback(uris=[uri])
                                stack.append(now_playing)
                            except Exception as err:
                                print(f"Error Playback: {err}")
                        
                        # -> RADIO STATION
                        elif tipo == 'radio_station':
                            print(f"Sintonizando radio: {nombre}")
                            
                            # 1. IMPORTANTÍSIMO: Detener Spotify si está sonando
                            # Aunque sea cuenta free y no puedas pausar remoto,
                            # intentamos dejar de pintar la UI de spotify.
                            # (Si tuvieras premium haríamos sp.pause_playback())
                            app_local_player.stop()
                            twitch.stop()
                            
                            # 2. Reproducir Radio
                            radio.play(uri)
                            
                            # 3. (Opcional) Ir a una pantalla de "Now Playing Radio"
                            # Por ahora nos quedamos en la lista o vamos a una pantalla simple.
                            # stack.append(pantalla_radio_now_playing
                            now_playing.set_mode_radio(nombre)
                            stack.append(now_playing)
                        
                        # 3. Has pulsado en una Canción -> Reproducir
                        elif tipo == 'local_track':
                            print(f"Reproduciendo local: {nombre}")
                            
                            # DETENER OTROS REPRODUCTORES
                            # Si tuvieras premium: sp.pause_playback()
                            radio.stop()
                            twitch.stop()
                            
                            # REPRODUCIR
                            app_local_player.play(uri) # 'uri' aquí es la ruta del archivo (/home/...)

                            cover_data = app_local_player.get_caratula(uri)
                            
                            # IR A NOW PLAYING (Opcional, de momento nos quedamos en la lista)
                            # stack.append(now_playing) # Esto requeriría adaptar now_playing para local
                            art = sel.get('artist_name', "Local Artist") # Necesitas pasar esto en el menú tracks
                            alb = sel.get('album_name', "Local Album")

                            now_playing.set_mode_local(
                                titulo=nombre,
                                artista=menu_local_player.titulo if not art else art, # Fallback
                                album=alb,
                                cover_bytes=cover_data
                            )
                            stack.append(now_playing)
                        
            
            # --- 2. SEARCH ---
            elif isinstance(curr, SearchScreen):
                if e.key == pygame.K_UP:
                    curr.mover_arriba()
                if e.key == pygame.K_DOWN:
                    curr.mover_abajo()
                if e.key == pygame.K_RIGHT:
                    curr.avanzar_caracter()
                if e.key == pygame.K_LEFT:
                    curr.borrar_caracter()
                if e.key == pygame.K_ESCAPE:
                    if curr.retroceder(): stack.pop()
                if e.key == pygame.K_RETURN:
                    res = curr.pulsar_enter()
                    if res and res['tipo'] == 'item':

                        # Lógica idéntica al menú principal para navegar/reproducir
                        uri = res['uri']
                        tipo = res['subtipo']
                        nombre = res['nombre']

                        if tipo == 'track':
                            try:
                                sp.start_playback(uris=[uri])
                                stack.append(now_playing)
                            except: print("Error Playback Search")
                        elif tipo == 'artist':
                            stack.append(MenuPantalla(nombre, [], sp, 'artist_albums', id_padre=uri))
                        elif tipo == 'album':
                            stack.append(MenuPantalla(nombre, [], sp, 'album_tracks', id_padre=uri))
                        elif tipo == 'playlist':
                            stack.append(MenuPantalla(nombre, [], sp, 'playlist_tracks', id_padre=uri))
                        elif tipo == 'show':
                            stack.append(MenuPantalla(nombre, [], sp, 'show_episodes', id_padre=uri))
                        elif tipo == 'show':
                            # Usamos res['id'] porque show_episodes requiere el ID, no la URI
                            # (Asegúrate de haber guardado 'id' en menu_search.py como hablamos antes)
                            stack.append(MenuPantalla(nombre, [], sp, 'show_episodes', id_padre=res['id']))
                        elif tipo == 'episode':
                            try:
                                sp.start_playback(uris=[uri])
                                stack.append(now_playing)
                            except: print("Error Playback Episode")
        
            # --- 3. NOW PLAYING ---
            elif isinstance(curr, PantallaNowPlaying):
                if e.key == pygame.K_ESCAPE:
                    stack.pop()
                
                if e.key == pygame.K_RETURN:
                    curr.cambiar_vista()
                # Aquí añadiremos controles de pausa/next en el futuro
                        
            # Si estamos en Now Playing, Enter o Clickwheel central podria pausar (futuro)

    # 3. Dibujar
    stack[-1].dibujar(pantalla, global_is_playing)
    
    # 3. Refrescar
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()