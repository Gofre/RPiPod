import streamlink
import vlc
import requests
import io
from config import TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN, MORADO_TWITCH
from music.menu_principal import MenuPantalla
from utils import descargar_imagen_url

class TwitchPlayer:
    def __init__(self):
        self.instance = vlc.Instance('--no-video', '--quiet')
        self.player = self.instance.media_player_new()
        
        # Cabeceras para todas las peticiones a Twitch
        self.headers = {
            'Client-ID': TWITCH_CLIENT_ID,
            'Authorization': f'Bearer {TWITCH_ACCESS_TOKEN}'
        }
        
        self.is_playing = False
        self.current_meta = {} # Guardaremos info del canal actual (foto, nombre)

    def get_my_user_id(self):
        """Obtiene tu ID numérico de usuario de Twitch"""
        try:
            r = requests.get('https://api.twitch.tv/helix/users', headers=self.headers)
            if r.status_code == 200:
                data = r.json()
                return data['data'][0]['id']
        except Exception as e:
            print(f"Error obteniendo User ID: {e}")
        return None

    def get_live_followed_streams(self):
        """Devuelve lista de streamers seguidos que están ONLINE"""
        user_id = self.get_my_user_id()
        if not user_id:
            return []

        print(f"Buscando directos para el usuario ID: {user_id}...")
        try:
            url = f'https://api.twitch.tv/helix/streams/followed?user_id={user_id}'
            r = requests.get(url, headers=self.headers)
            
            if r.status_code == 200:
                data = r.json()['data']
                canales = []
                
                # Necesitamos hacer otra llamada para obtener las fotos de perfil
                # (La API de streams no da la foto del usuario, da la miniatura del juego)
                # Recopilamos los user_ids de los streamers
                streamer_ids = [s['user_id'] for s in data]
                profile_pics = self.get_users_profile_pics(streamer_ids)

                for stream in data:
                    s_name = stream['user_name']
                    s_id = stream['user_id']
                    
                    # Buscamos su foto en el diccionario que hemos creado
                    p_pic = profile_pics.get(s_id, None)

                    canales.append({
                        'nombre': s_name,
                        'type': 'twitch_channel',
                        'channel_name': stream['user_login'], # El nombre para la URL (ej: ibai)
                        'is_live': True, # Esto activa el punto rojo
                        'game': stream['game_name'],
                        'viewers': stream['viewer_count'],
                        'profile_image_url': p_pic
                    })
                return canales
            else:
                print(f"Error API Twitch: {r.status_code} - {r.text}")
                
        except Exception as e:
            print(f"Error fetching streams: {e}")
        
        return []

    def get_users_profile_pics(self, user_ids):
        """Dado una lista de IDs, devuelve un diccionario {id: url_foto}"""
        if not user_ids: return {}
        
        # La URL es users?id=1&id=2&id=3...
        query_string = "&id=".join(user_ids)
        url = f'https://api.twitch.tv/helix/users?id={query_string}'
        
        pics = {}
        try:
            r = requests.get(url, headers=self.headers)
            if r.status_code == 200:
                for u in r.json()['data']:
                    pics[u['id']] = u['profile_image_url']
        except:
            pass
        return pics

    def get_menu(self):
        """Genera el menú dinámico"""
        # 1. Obtenemos los LIVE
        live_channels = self.get_live_followed_streams()
        
        if not live_channels:
            live_channels.append({'nombre': '(No live channels)', 'type': 'info_static', 'uri': None})

        return MenuPantalla("Twitch Live", live_channels, color_tema=MORADO_TWITCH)

    def play(self, channel_login):
        self.stop()
        print(f"Twitch: Conectando a {channel_login}...")

        try:
            twitch_url = f"https://www.twitch.tv/{channel_login}"
            streams = streamlink.streams(twitch_url)
            
            if not streams:
                return False

            if 'audio_only' in streams:
                stream_url = streams['audio_only'].url
            elif 'worst' in streams:
                stream_url = streams['worst'].url
            else:
                return False

            media = self.instance.media_new(stream_url)
            self.player.set_media(media)
            self.player.play()
            self.is_playing = True
            return True

        except Exception as e:
            print(f"Error Twitch Play: {e}")
            return False

    def stop(self):
        self.player.stop()
        self.is_playing = False