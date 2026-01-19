import socket
import threading
import time
import re
import ssl
from config import *

class TwitchChat:
    def __init__(self):
        self.server = 'irc.chat.twitch.tv'
        self.port = 6697
        self.nickname = 'justinfan12345' # Usuario anónimo de Twitch (siempre funciona)
        self.token = 'oauth:schmoopiie'  # Token genérico para lectura anónima
        
        self.socket = None
        self.running = False
        self.channel = None
        
        # Buffer de mensajes (Guardamos los últimos 10)
        self.messages = [] 
        self.max_messages = 16 # Cuántos caben en pantalla
        
        # Hilo
        self.thread = None

    def connect(self, channel_name):
        """Conecta al chat de un canal"""
        self.disconnect() # Limpieza previa
        
        self.channel = channel_name.lower().strip() # Twitch exige minúsculas
        self.messages = [] # Limpiar chat anterior
        self.running = True
        
        # Iniciar hilo de escucha
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()

    def disconnect(self):
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except: pass
        self.socket = None

    def _listen_loop(self):
        try:
            # Creamos un contexto SSL por defecto
            context = ssl.create_default_context()

            # Creamos el socket normal
            raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            raw_socket.settimeout(10) # Timeout de 10 segundos para conectar

            # Lo "envolvemos" con SSL
            self.socket = context.wrap_socket(raw_socket, server_hostname=self.server)

            # Conectamos
            self.socket.connect((self.server, self.port))

            # Volvemos a modo blocking para escuchar (o settimeout None)
            self.socket.settimeout(None)

            # Protocolo IRC estándar
            self.socket.send(f"PASS {self.token}\n".encode('utf-8'))
            self.socket.send(f"NICK {self.nickname}\n".encode('utf-8'))
            self.socket.send(f"JOIN #{self.channel}\n".encode('utf-8'))
            
            self.add_system_message(f"Connecting to #{self.channel}...")
            
            buffer = ""
            while self.running:
                try:
                    data = self.socket.recv(2048)
                    if not data: break # Conexión cerrada

                    resp = data.decode('utf-8', errors='ignore') # Ignorar caracteres raros
                    buffer += resp

                    # Procesar líneas completas
                    lines = buffer.split('\n')
                    buffer = lines.pop() # Guardar lo incompleto para la siguiente
                
                    for line in lines:
                        if line.startswith('PING'):
                            self.socket.send("PONG\n".encode('utf-8'))
                        else:
                            self._parse_message(line)
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Error lectura socket: {e}")
                    break
                        
        except Exception as e:
            print(f"Chat Error: {e}")
            self.add_system_message("Chat disconnected.")
        finally:
            self.disconnect()

    def _parse_message(self, line):
        """Extrae Usuario y Mensaje del formato IRC crudo"""
        # Formato: :usuario!usuario@... PRIVMSG #canal :Mensaje
        try:
            # Regex simple para capturar usuario y mensaje
            # Busca algo entre dos puntos al principio, luego PRIVMSG, luego el mensaje
            parts = line.split("PRIVMSG", 1)
            if len(parts) > 1:
                prefix = parts[0]
                message = parts[1].split(':', 1)[1].strip()
                
                # Sacar nombre de usuario (está entre : y !)
                username = prefix.split('!')[0].replace(':', '')
                
                self.add_message(username, message)
        except:
            pass

    def add_message(self, user, text):
        """Añade mensaje al buffer y borra los viejos"""
        color = self._get_user_color(user)
        self.messages.append({'user': user, 'text': text, 'color': color})
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

    def add_system_message(self, text):
        self.messages.append({'user': 'SYSTEM', 'text': text, 'color': MORADO_TWITCH})
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
            
    def get_messages(self):
        return self.messages
    
    def _get_user_color(self, username):
        """Genera un color consistente basado en el nombre"""
        # Paleta de colores brillantes (evitamos oscuros que no se ven en negro)
        colores = [
            (255, 80, 80),   # Rojo claro
            (50, 255, 50),   # Verde Matrix
            (80, 160, 255),  # Azul cielo
            (255, 255, 80),  # Amarillo
            (255, 100, 255), # Rosa
            (0, 255, 255),   # Cyan
            (255, 160, 50),  # Naranja
            (200, 200, 200)  # Gris claro
        ]
        # Sumamos los valores ASCII de las letras para elegir un índice
        hash_val = sum(ord(c) for c in username)
        return colores[hash_val % len(colores)]