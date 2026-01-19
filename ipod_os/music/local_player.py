import os
import vlc
from config import AZUL_LOCAL
from mutagen import File
from music.menu_principal import MenuPantalla

class LocalPlayer:
    def __init__(self, ruta_musica="songs"):
        self.ruta_musica = ruta_musica
        
        # Base de datos en memoria
        self.biblioteca = {}
        
        # VLC se traga FLAC, WAV, ALAC sin problemas
        self.instance = vlc.Instance('--no-video', '--quiet')
        self.player = self.instance.media_player_new()
        
        self.is_playing = False
        
        # Extensiones permitidas (puedes añadir más si quieres)
        self.valid_extensions = ('.mp3', '.flac', '.wav', '.m4a', '.ogg')
        
        self.scan_library()

    def scan_library(self):
        """Escanea recursivamente buscando audio y leyendo metadatos unificados"""
        print("Escaneando biblioteca local (FLAC/MP3/WAV)...")
        self.biblioteca = {}
        
        if not os.path.exists(self.ruta_musica):
            os.makedirs(self.ruta_musica)
            return

        for root, dirs, files in os.walk(self.ruta_musica):
            for file in files:
                # Comprobamos si termina en alguna de las extensiones validas
                if file.lower().endswith(self.valid_extensions):
                    path = os.path.join(root, file)
                    try:
                        # --- MAGIA DE MUTAGEN ---
                        # File(path, easy=True) detecta si es FLAC o MP3 y nos da
                        # una interfaz común (diccionario) para leer los datos.
                        audio = File(path, easy=True)
                        
                        # Valores por defecto por si el archivo no tiene etiquetas
                        # OJO: Los WAV suelen venir sin etiquetas (serán None)
                        if audio:
                            artista = audio.get('artist', ['Unknown Artist'])[0]
                            album = audio.get('album', ['Unknown Album'])[0]
                            titulo = audio.get('title', [file])[0]
                            track_no = audio.get('tracknumber', ['0'])[0]
                        else:
                            # Si mutagen no entiende el archivo o no tiene tags (ej: WAV básico)
                            artista = "Unknown Artist"
                            album = "Unknown Album"
                            titulo = file # Usamos nombre de archivo
                            track_no = "0"
                        
                        # Insertar en la biblioteca
                        if artista not in self.biblioteca:
                            self.biblioteca[artista] = {}
                        if album not in self.biblioteca[artista]:
                            self.biblioteca[artista][album] = []
                            
                        self.biblioteca[artista][album].append({
                            'titulo': titulo,
                            'ruta': path,
                            'track_no': track_no
                        })
                        
                    except Exception as e:
                        print(f"Error leyendo {file}: {e}")

        # Ordenar artistas alfabéticamente
        self.biblioteca = dict(sorted(self.biblioteca.items()))

    # Añade esto dentro de la clase LocalPlayer, al final
    
    def get_caratula(self, ruta_archivo):
        """
        Intenta extraer la imagen incrustada (ID3 APIC o FLAC Picture).
        Devuelve bytes de imagen o None si falla.
        """
        try:
            f = File(ruta_archivo)
            
            # 1. CASO FLAC
            # Los FLAC guardan las imagenes en f.pictures
            if hasattr(f, 'pictures') and f.pictures:
                # Solemos querer la primera imagen
                return f.pictures[0].data
                
            # 2. CASO ID3 (MP3)
            # Buscamos etiquetas que empiecen por APIC: (Attached Picture)
            if hasattr(f, 'tags'):
                for key in f.tags.keys():
                    if key.startswith('APIC:'):
                        return f.tags[key].data
                        
            return None # No se encontró imagen
        except Exception as e:
            print(f"Error extrayendo carátula: {e}")
            return None
    
    # --- MENÚS (Igual que antes) ---

    def get_menu_artistas(self):
        opciones = []
        for artista in self.biblioteca.keys():
            opciones.append({
                'nombre': artista,
                'type': 'local_artist',
                'artist_name': artista
            })
        if not opciones:
            opciones.append({'nombre': '(No songs found)', 'type': 'info_static', 'uri': None})
            
        return MenuPantalla("Local Music", opciones, color_tema=AZUL_LOCAL)

    def get_menu_albums(self, artista):
        opciones = []
        if artista in self.biblioteca:
            albums = self.biblioteca[artista].keys()
            for alb in albums:
                opciones.append({
                    'nombre': alb,
                    'type': 'local_album',
                    'artist_name': artista,
                    'album_name': alb
                })
        return MenuPantalla(artista, opciones, color_tema=AZUL_LOCAL)

    def get_menu_tracks(self, artista, album):
        opciones = []
        if artista in self.biblioteca and album in self.biblioteca[artista]:
            tracks = self.biblioteca[artista][album]
            
            # Ordenar por número de pista si es posible
            # (Intenta convertir track_no a int, si falla usa 0)
            tracks.sort(key=lambda x: int(x['track_no'].split('/')[0]) if x['track_no'].replace('/','').isdigit() else 0)

            for t in tracks:
                opciones.append({
                    'nombre': t['titulo'],
                    'type': 'local_track',
                    'uri': t['ruta'],
                    'is_local': True,
                    'artist_name': artista,
                    'album_name': album
                })
        return MenuPantalla(album, opciones, color_tema=AZUL_LOCAL)

    # --- REPRODUCCIÓN ---

    def play(self, ruta_archivo):
        self.stop()
        print(f"Reproduciendo: {ruta_archivo}")
        media = self.instance.media_new(ruta_archivo)
        self.player.set_media(media)
        self.player.play()
        self.is_playing = True

    def stop(self):
        self.player.stop()
        self.is_playing = False