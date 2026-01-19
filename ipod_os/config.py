# config.py
import pygame

# Spotify API
CLIENT_ID = ''
CLIENT_SECRET = ''
REDIRECT_URI = 'http://127.0.0.1:8888/callback/spotify'

# Twitch API
TWITCH_CLIENT_ID = ''
TWITCH_ACCESS_TOKEN = ''
# REFRESH_TOKEN = ''

# Rutas
CACHE_PATH = '.spotify_cache'

### INTERFAZ ###
ANCHO = 320
ALTO = 240
FPS = 30

ALTURA_HEADER = 28
INICIO_VERTICAL_LISTA = ALTURA_HEADER + 4 # Altura a la que se empiezan a listar los elementos
ANCHO_SCROLLBAR = 14
ANCHO_SEPARADOR = 2 # Margen negro exterior
GROSOR_CAJA_SCROLL = 2 # Caja verde del scroll
MARGEN_INTERNO_CAJA_SCROLL = 2 # Margen negro interno

# NUEVO: Píxeles totales a añadir al ancho de la letra para el cursor verde.
# Si pones 0, la caja será exactamente del ancho de la letra.
# Si pones 6, añadirá 3px a la izquierda y 3px a la derecha.
EXTRA_ANCHO_CURSOR_BUSQUEDA = 0
# Alto
EXTRA_ALTO_CURSOR_BUSQUEDA = 2

# Truncado de texto
# Ajusta este número entre 20 y 23.
MAX_CARACTERES_MENU = 20

# Texto
TEXT_SMALL = 12
TEXT_BIG = 22
OFFSET_TEXTO_LISTA = 0 # Posición Y del texto
ANTIALIASING = True
NEGRITA = False

# Paleta de Colores
NEGRO = (0, 0, 0)
VERDE_SPOTIFY = (30, 215, 96)
MORADO_TWITCH = (145, 71, 255)
AZUL_LOCAL    = (60, 160, 220)  # Un azul agradable para MP3
NARANJA_RADIO = (255, 140, 0)   # Naranja para Radio
ROJO_ERROR    = (230, 50, 50)
GRIS_OSCURO   = (40, 40, 40)

GRIS_PIXEL = (20, 20, 20)      # Para tramas oscuras
GRIS_TEXTO = (100, 100, 100) # Para títulos de secciones como "ARTISTS", "ALBUMS"
COLOR_HEADER_SECCION = (200, 200, 200) # Para títulos de secciones de la búsqueda