import vlc
import time
from config import NARANJA_RADIO
from music.menu_principal import MenuPantalla 

class RadioApp:
    def __init__(self):
        # --- MOTOR VLC ---
        # Creamos una instancia básica de VLC
        self.instance = vlc.Instance('--no-video', '--aout=alsa', '--quiet')
        self.player = self.instance.media_player_new()
        
        # --- LISTA DE EMISORAS ---
        # Puedes buscar URLs de streaming en internet (formato mp3 o aac)
        self.emisoras = [
            {
                'nombre': 'RNE 3',
                'uri': 'https://rtvelivestream.rtve.es/rtvesec/rne/rne_r5_madrid_main.m3u8?idasset=1712404' 
            },
            {
                'nombre': 'RNE Radio 3',
                'uri': 'https://ztnr.rtve.es/ztnr/2795617.m3u8'
            },
            {
                'nombre': '[VLL] RNE Radio 5',
                'uri': 'https://dispatcher.rndfnk.com/crtve/rne5/vll/mp3/high'
            },
            {
                'nombre': 'RNE Radio Clásica',
                'uri': 'https://rtvelivestream.rtve.es/rtvesec/rne/rne_r2_main.m3u8?idasset=1712494'
            },
            {
                'nombre': '[CYL] RNE Nacional',
                # URL HLS moderna (funciona mejor) o MP3 directo
                'uri': 'https://dispatcher.rndfnk.com/crtve/rne1/cyl/mp3/high' 
            },
            {
                'nombre': 'Cadena 100',
                # URL HLS moderna (funciona mejor) o MP3 directo
                'uri': 'https://cadena100-streamers-mp3.flumotion.com/cope/cadena100.mp3' 
            },
            {
                'nombre': 'Los 40 Classic',
                'uri': 'http://playerservices.streamtheworld.com/api/livestream-redirect/LOS40_CLASSIC.mp3'
            },
            {
                'nombre': 'Los 40',
                # Las de PRISA (Los 40, Cadena SER) suelen usar estos dominios ahora
                'uri': 'https://25633.live.streamtheworld.com/LOS40_SC'
            },
            {
                'nombre': 'Rock FM',
                'uri': 'https://icecast-streaming.nice264.com/rockfm'
            },
            {
                'nombre': 'Kiss FM',
                'uri': 'http://kissfm.kissfmradio.cires21.com/kissfm.mp3'
            },
            {
                'nombre': 'Ibiza Global',
                'uri': 'http://ibizaglobalradio.streaming-pro.com:8024/;'
            }
        ]
        
        self.is_playing = False

    def get_menu(self):
        """
        Devuelve un objeto MenuPantalla con las emisoras listas para usar en main.py
        """
        opciones = []
        for emi in self.emisoras:
            opciones.append({
                'nombre': emi['nombre'],
                'type': 'radio_station', # Tipo nuevo para main.py
                'uri': emi['uri']
            })
            
        return MenuPantalla("Radio", opciones, color_tema=NARANJA_RADIO)

    def play(self, url):
        """Reproduce una URL"""

        if self.is_playing:
            self.stop()

        print(f"Sintonizando {url}...")
        
        # 1. Cargar el medio
        media = self.instance.media_new(url)
        # 2. Asignarlo al reproductor
        self.player.set_media(media)
        # 3. Play
        self.player.play()
        self.is_playing = True

        # Pequeño truco: VLC a veces necesita un empujón de volumen al iniciar
        time.sleep(0.5)
        self.player.audio_set_volume(100)

    def stop(self):
        """Detiene la radio"""
        print("Radio: Stop")
        self.player.stop()
        self.is_playing = False

    def get_info(self):
        """Devuelve info para la pantalla (placeholder)"""
        if self.is_playing:
            return "Radio Playing..."
        return "Radio Stopped"