import pygame
import os
import urllib.request
import io
import numpy as np
from datetime import datetime
import socket # Para comprobar si hay internet
import threading
import subprocess
import time
import requests # Si no lo tienes
from config import *

_fuente_header_big_cache = None
_fuente_header_small_cache = None

HAY_CONEXION = False
BT_CONECTADO = False
TIMER_INICIADO = False

def cargar_fuente(tamano):
    try:
        ruta = os.path.join(os.path.dirname(__file__), 'Chicago.ttf')
        fuente = pygame.font.Font(ruta, tamano)

        if NEGRITA:
            fuente.set_bold(True)

        return fuente
    except FileNotFoundError:
        return pygame.font.SysFont("arial", tamano, bold=True)

def truncar_texto(texto, limite):
    """
    Corta el texto si supera el límite de caracteres
    y añade '...' al final.
    """
    if len(texto) > limite:
        # Cortamos un poco antes del límite para que quepan los puntos
        return texto[:limite-3] + "..."
    return texto

def formato_tiempo(ms):
    """Convierte milisegundos a formato MM:SS"""
    if ms is None: return "00:00"

    total_seconds = int(ms / 1000)
    
    seconds = total_seconds % 60
    minutes = (total_seconds % 3600) // 60
    hours = total_seconds // 3600
    
    if hours > 0:
        # Si hay horas, usamos formato H:MM:SS
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        # Si no, mantenemos el clásico MM:SS
        return f"{minutes:02d}:{seconds:02d}"

def descargar_imagen_url(url):
    """Descarga una imagen de una URL y devuelve los bytes raw"""
    if not url: return None
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.content
    except Exception as e:
        print(f"Error descargando imagen: {e}")
    return None

#######################
# FUNCIONES DE DIBUJO #
#######################

def dibujar_reloj(pantalla, color):

    x_reloj = 5
    y_reloj = ALTURA_HEADER//2

    now = datetime.now()
    time_str = now.strftime("%H:%M") # Formato 24h
    text_time = _fuente_header_small_cache.render(time_str, ANTIALIASING, color)
    rect_time = text_time.get_rect(midleft=(x_reloj, y_reloj))
    pantalla.blit(text_time, rect_time)

def dibujar_icono_bt(pantalla, color):
    
    x = 250
    y = ALTURA_HEADER//2 - 3 #11

    # Patas
    pygame.draw.line(pantalla, color, (x+2, y+1), (x+4, y+3), 1)
    pygame.draw.line(pantalla, color, (x+2, y+5), (x+4, y+3), 1)
    # Triángulos
    pygame.draw.line(pantalla, color, (x+2, y), (x+7, y+5), 1)
    pygame.draw.line(pantalla, color, (x+2, y+6), (x+7, y+1), 1)
    #pygame.draw.line(pantalla, color, (x+4, y+2), (x+7, y+5), 1)
    #pygame.draw.line(pantalla, color, (x+4, y+4), (x+7, y+1), 1)
    pygame.draw.line(pantalla, color, (x+7, y+1), (x+4, y-2), 1)
    pygame.draw.line(pantalla, color, (x+7, y+5), (x+4, y+8), 1)
    # Línea vertical
    pygame.draw.line(pantalla, color, (x+4, y-2), (x+4, y+8), 1)
    # Puntos extra
    pygame.draw.line(pantalla, color, (x+5, y+2), (x+5, y+2), 1)
    pygame.draw.line(pantalla, color, (x+5, y+4), (x+5, y+4), 1)
    pygame.draw.line(pantalla, color, (x+6, y+1), (x+6, y+1), 1)
    pygame.draw.line(pantalla, color, (x+6, y+5), (x+6, y+5), 1)

def dibujar_icono_playpause(pantalla, color, estado_play):

    x_play = 46
    y_play = 9
    x_pause = 46
    y_pause = 9

    if estado_play is True:
        puntos = [(x_play, y_play), (x_play, y_play + 10), (x_play + 10, y_play + 5)]
        pygame.draw.polygon(pantalla, color, puntos)
    elif estado_play is False: # Pause
        pygame.draw.rect(pantalla, color, (x_pause, y_pause, 3, 10))
        pygame.draw.rect(pantalla, color, (x_pause + 6, y_pause, 3, 10))

def dibujar_icono_wifi(pantalla, color):
    
    x = 265
    y = ALTURA_HEADER//2 + 4

    color_wifi = color if HAY_CONEXION else (100, 100, 100)

    # Punto base
    pygame.draw.circle(pantalla, color_wifi, (x+6, y), 1)
    # Arco pequeño
    pygame.draw.arc(pantalla, color_wifi, (x+2, y-5, 9, 9), 1.57, 2.6, 2)
    pygame.draw.arc(pantalla, color_wifi, (x+3, y-5, 9, 9), 0.729, 1.57, 2)
    pygame.draw.line(pantalla, (0, 0, 0), (x+9, y-3), (x+9, y-3), 1)
    # Arco grande
    pygame.draw.arc(pantalla, color_wifi, (x-1, y-9, 14, 14), 1.57, 2.6, 2)
    pygame.draw.arc(pantalla, color_wifi, (x, y-9, 14, 14), 0.729, 1.57, 2)
    pygame.draw.line(pantalla, color_wifi, (x+11, y-8), (x+11, y-8), 1)
    pygame.draw.line(pantalla, color_wifi, (x+9, y-9), (x+9, y-9), 1)

def dibujar_bateria(pantalla, color_tema):

    x = ANCHO - 5
    y = ALTURA_HEADER // 2

    # Placeholder: 100% (Más adelante leeremos el sistema real)
    bateria_pct = "100%" 
    text_bat = _fuente_header_small_cache.render(bateria_pct, ANTIALIASING, color_tema)
    rect_bat = text_bat.get_rect(midright=(x, y))
    pantalla.blit(text_bat, rect_bat)

def dibujar_header(pantalla, contenido, estado_play, color_tema):
    """
    Dibuja la barra superior, iconos y el contenido central.
    'contenido' puede ser:
       - str: Texto simple (se renderiza en verde).
       - pygame.Surface: Una imagen ya renderizada (se centra automáticamente).
    """
    global _fuente_header_big_cache
    global _fuente_header_small_cache

    if _fuente_header_big_cache is None:
        _fuente_header_big_cache = cargar_fuente(TEXT_BIG)

    if _fuente_header_small_cache is None:
        _fuente_header_small_cache = cargar_fuente(TEXT_SMALL)

    global TIMER_INICIADO
    if not TIMER_INICIADO:
        comprobar_internet() # Primera comprobación
        TIMER_INICIADO = True
    
    # FONDO Y LÍNEA
    pygame.draw.rect(pantalla, NEGRO, (0, 0, ANCHO, ALTURA_HEADER))
    pygame.draw.line(pantalla, color_tema, (0, ALTURA_HEADER), (ANCHO, ALTURA_HEADER), 2)
    
    # RELOJ (Izquierda)
    dibujar_reloj(pantalla, color_tema)

    # PLAY/PAUSE (Izquierda)
    dibujar_icono_playpause(pantalla, color_tema, estado_play)

    # CONTENIDO CENTRAL (Texto o Surface)
    if isinstance(contenido, str):
        # Es texto normal
        surf = _fuente_header_big_cache.render(contenido, ANTIALIASING, color_tema)
    else:
        # Es una Surface (imagen) personalizada (ej: búsqueda con colores)
        surf = contenido
    
    rect_titulo = surf.get_rect(center=(ANCHO//2, ALTURA_HEADER//2))
    pantalla.blit(surf, rect_titulo)
    
    # Icono Bluetooth (esquina superior derecha)
    if BT_CONECTADO:
        dibujar_icono_bt(pantalla, color_tema)

    # WIFI (Derecha)
    dibujar_icono_wifi(pantalla, color_tema)

    # BATERÍA (Derecha) - Porcentaje
    dibujar_bateria(pantalla, color_tema)
    
def dibujar_lista_elementos(pantalla, opciones, seleccion, inicio_scroll, items_visibles, fuente, tiene_foco=True, color_tema=VERDE_SPOTIFY):
    """
    Dibuja una lista estándar estilo iPod.
    - pantalla: Surface destino.
    - opciones: Lista de diccionarios (con 'nombre', 'tipo'...) o strings.
    - seleccion: Índice del elemento seleccionado.
    - inicio_scroll: Índice del primer elemento visible.
    - items_visibles: Cuántos caben en pantalla.
    - fuente: La fuente a usar (grande o pequeña).
    - tiene_foco: Si False, el elemento seleccionado se pinta en gris/verde oscuro (no activo).
    """
    
    # 1. Cálculos de zona
    total_items = len(opciones)
    hay_scroll = total_items > items_visibles
    
    # Si hay scroll, restamos el ancho de la barra y el separador
    ancho_zona = ANCHO - (ANCHO_SCROLLBAR + ANCHO_SEPARADOR) if hay_scroll else ANCHO
    
    # 2. Slice de elementos visibles
    vista = opciones[inicio_scroll : inicio_scroll + items_visibles]
    
    for i, op in enumerate(vista):
        pos_y = INICIO_VERTICAL_LISTA + (i * ALTURA_HEADER)
        idx_real = i + inicio_scroll
        
        # Normalizar datos: puede ser un dict (Search) o un str (Menu simple)
        if isinstance(op, dict):
            nombre = op['nombre']
            es_header = op.get('tipo') == 'header'
        else:
            nombre = str(op)
            es_header = False
        
        # A) CASO HEADER (Títulos de sección)
        if es_header:
            texto_render = fuente.render(nombre, ANTIALIASING, COLOR_HEADER_SECCION)
            # Usamos OFFSET_TEXTO_LISTA para el ajuste vertical fino
            pantalla.blit(texto_render, (10, pos_y + OFFSET_TEXTO_LISTA))
            
        # B) CASO ÍTEM NORMAL
        else:
            # Truncamos según el ancho disponible (ajuste manual o global)
            # Si usamos fuente grande, caben menos caracteres (aprox 18). Si es pequeña, config global.
            #limite_chars = 18 if fuente.get_height() > 20 else MAX_CARACTERES_MENU
            limite_chars = MAX_CARACTERES_MENU
            txt_mostrar = truncar_texto(nombre, limite_chars)
            
            es_seleccionado = (idx_real == seleccion)
            
            if es_seleccionado and tiene_foco:
                # Fondo Verde
                pygame.draw.rect(pantalla, color_tema, (0, pos_y, ancho_zona, ALTURA_HEADER))
                # Texto Negro
                r = fuente.render(txt_mostrar, ANTIALIASING, NEGRO)
                # Flechita '>'
                flecha = fuente.render(">", ANTIALIASING, NEGRO)
                pantalla.blit(flecha, (ancho_zona - 15, pos_y + OFFSET_TEXTO_LISTA))
            else:
                # Texto Verde (o Gris si no tiene foco y es el seleccionado "fantasma")
                color = color_tema
                if es_seleccionado and not tiene_foco:
                    color = (0, 100, 0) # Verde oscuro para indicar "última posición" sin foco
                elif not tiene_foco:
                    color = GRIS_TEXTO # Ítems inactivos
                
                r = fuente.render(txt_mostrar, ANTIALIASING, color)
            
            pantalla.blit(r, (10, pos_y + OFFSET_TEXTO_LISTA))

            if op.get('is_live'):
                
                # Dibujamos el círculo rojo
                # (pantalla, color, (x, y), radio)
                pygame.draw.circle(pantalla, (235, 4, 0), (ancho_zona - 25, pos_y + OFFSET_TEXTO_LISTA + 14), 4)
    
    # 3. Dibujar Scrollbar
    dibujar_scrollbar(pantalla, total_items, items_visibles, inicio_scroll, color_tema)

def dibujar_scrollbar(pantalla, total_items, visibles, indice_inicio, color_tema=VERDE_SPOTIFY):
    """
    Dibuja la barra de scroll a la derecha si es necesario.
    Usa las constantes de config para posición y estilo.
    """
    if total_items <= visibles:
        return # No hace falta scroll

    # Coordenadas
    sb_x = ANCHO - ANCHO_SCROLLBAR
    sb_y = ALTURA_HEADER
    sb_h = ALTO - ALTURA_HEADER
    
    # A) Marco (Caja)
    pygame.draw.rect(pantalla, color_tema, (sb_x, sb_y, ANCHO_SCROLLBAR, sb_h), GROSOR_CAJA_SCROLL)
    
    # B) Thumb (Barra interior)
    margen_interno = GROSOR_CAJA_SCROLL + MARGEN_INTERNO_CAJA_SCROLL
    ancho_thumb = ANCHO_SCROLLBAR - (margen_interno * 2)
    altura_util = sb_h - (margen_interno * 2)

    # Evitar errores si los márgenes son tan grandes que el thumb desaparece
    if ancho_thumb < 1: ancho_thumb = 1
    if altura_util < 1: altura_util = 1
    
    # Cálculo proporcional
    thumb_height = max(10, int((visibles / total_items) * altura_util))
    max_scroll = total_items - visibles
    scroll_ratio = indice_inicio / max_scroll
    espacio_recorrido = altura_util - thumb_height
    pos_y_thumb = sb_y + margen_interno + int(scroll_ratio * espacio_recorrido)

    # Dibujar Thumb
    pygame.draw.rect(pantalla, color_tema, 
                     (sb_x + margen_interno, pos_y_thumb, ancho_thumb, thumb_height))

def procesar_caratula_retro(surface_original, color_tema=VERDE_SPOTIFY):
    """
    Convierte una Surface a un estilo retro de 4 tonos (2-bit dithering).
    """
    # 1. Definir la paleta de 4 colores (Simulación LCD)
    # Nivel 0: Negro
    c0 = np.array([0, 0, 0])
    # Nivel 1: Verde muy oscuro (sombra)
    c1 = np.array([10, 55, 25])
    # Nivel 2: Verde Spotify (medio)
    c2 = np.array([30, 215, 96])
    # Nivel 3: Verde muy claro / Blanco verdoso (brillo)
    c3 = np.array([210, 255, 220])
    
    if color_tema == MORADO_TWITCH:
        c1 = np.array([48, 24, 85])
        c2 = np.array([145, 71, 255]) # Original
        c3 = np.array([210, 190, 255])
    elif color_tema == AZUL_LOCAL:
        c1 = np.array([20, 53, 73])
        c2 = np.array([60, 160, 220]) # Original
        c3 = np.array([233, 247, 247])
    
    palette_colors = np.array([c0, c1, c2, c3])

    # 2. Reducir tamaño
    tamano_pixel = (64, 64) # Resolución interna pixelada
    small = pygame.transform.scale(surface_original, tamano_pixel)
    
    # 3. Obtener píxeles como array de floats para cálculos
    pixels = pygame.surfarray.pixels3d(small).astype(np.float32)
    ancho, alto, _ = pixels.shape
    
    # 4. Convertir a Escala de Grises (Luminancia)
    # Usamos la fórmula de luminancia perceptiva: 0.299R + 0.587G + 0.114B
    grayscale = pixels[:, :, 0] * 0.299 + pixels[:, :, 1] * 0.587 + pixels[:, :, 2] * 0.114
    
    # Preparamos el array de salida (3 canales RGB)
    output = np.zeros((ancho, alto, 3), dtype=np.uint8)

    # 5. Algoritmo Floyd-Steinberg ajustado a 4 niveles
    # Los niveles de gris objetivo son: 0, 85, 170, 255
    
    for y in range(alto):
        for x in range(ancho):
            old_pixel = grayscale[x, y]
            
            # Cuantizar: Encontrar el nivel más cercano (0, 1, 2, 3)
            # Normalizamos 0-255 a 0-3
            level = np.round(old_pixel / 85.0)
            level = np.clip(level, 0, 3)
            
            # Asignar el nuevo valor de gris cuantizado (para calcular el error)
            new_pixel_val = level * 85.0
            
            # Guardamos el COLOR correspondiente en la imagen final
            output[x, y] = palette_colors[int(level)]
            
            # Calcular el error (diferencia de brillo)
            error = old_pixel - new_pixel_val
            
            # Difundir el error a los vecinos (solo en el mapa de grises)
            if x + 1 < ancho:
                grayscale[x+1, y] += error * 0.5 # Derecha
            if y + 1 < alto:
                grayscale[x, y+1] += error * 0.5 # Abajo
                
            # Nota: He simplificado la difusión a solo 2 vecinos (Derecha y Abajo)
            # con factor 0.5 para que sea más rápido y el patrón sea más limpio
            # estilo "Bayer" o ordenado, que queda mejor en pixelart.

    # 6. Crear superficie final
    surface_final = pygame.surfarray.make_surface(output)
    
    return pygame.transform.scale(surface_final, (128, 128))

#########################
# FUNCIONES DEL SISTEMA #
#########################
def obtener_ip():
    """Devuelve la IP local de la Raspberry Pi."""

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # No necesita conectarse realmente, solo ver qué interfaz usa para salir a internet
        s.connect(('8.8.8.8', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP

def comprobar_internet():
    """Devuelve True si hay conexión a internet, False si no."""

    global HAY_CONEXION
    
    try:
        # Intenta conectar a Google DNS (esto es lo que podría bloquear)
        socket.setdefaulttimeout(1)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        HAY_CONEXION = True
    except:
        HAY_CONEXION = False
    
    # IMPORTANTE: Se programa a sí misma para volver a ejecutarse en 10 segundos
    # Esto es el 'threading.Timer'
    t = threading.Timer(10.0, comprobar_internet)
    t.daemon = True # Para que se cierre si apagas el programa
    t.start()

def comprobar_bluetooth_loop():
    """
    Se ejecuta en segundo plano. Comprueba cada 5s si hay algún dispositivo
    Bluetooth con estado 'Connected: yes'.
    """
    global BT_CONECTADO
    while True:
        try:
            # Preguntamos a bluetoothctl info sobre los dispositivos emparejados
            # Si alguno dice "Connected: yes", es que tenemos audio.
            resultado = subprocess.check_output("bluetoothctl info | grep 'Connected: yes'", shell=True)
            if resultado:
                BT_CONECTADO = True
            else:
                BT_CONECTADO = False
        except subprocess.CalledProcessError:
            # grep devuelve error (exit code 1) si no encuentra nada, así que es normal
            BT_CONECTADO = False
        except Exception as e:
            print(f"Error check BT: {e}")
            BT_CONECTADO = False
            
        time.sleep(5) # Descansar 5 segundos