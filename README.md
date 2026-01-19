# RPiPod
Requirements and dependencies
- Raspberry Pi Zero 2W
- Raspberry Pi OS Lite (64-bit)
- Raspotify
- Spotipy
- pygame
- NumPy
- VLC
- Mutagen
- Streamlink

First steps:

**Actualizar lista de paquetes**

`sudo apt update`

**Actualizar el sistema completo**

`sudo apt full-upgrade -y`

**Eliminar paquetes obsoletos que ya no sirvan**

`sudo apt autoremove -y`

**Limpiar caché para liberar espacio en la SD**

`sudo apt clean`

**Install Git and Python**

`sudo apt install git python3-pip python3-venv -y`

### Raspotify

It is needed to install [Raspotify](https://github.com/dtcooper/raspotify) so the Raspberry can play music itself as a Spotify Connect device.

`sudo apt-get -y install curl && curl -sL https://dtcooper.github.io/raspotify/install.sh | sh`

### Spotipy

Spotify API Python library: [Spotipy](https://spotipy.readthedocs.io/)

`pip3 install spotipy --break-system-packages`

### pygame

Open-source Python library for creating graphics: [pygame](https://www.pygame.org/)

`sudo apt install python3-pygame -y`

### NumPy

Python library for mathematical operations. [Numpy](https://numpy.org/) is used to draw the albums cover in green pixel art.

`sudo apt install python3-numpy`

### VLC

VLC Player with Python library to reproduce online radio.

`sudo apt-get install vlc`

`sudo apt install python-vlc`

### Bluetooth

`sudo apt-get install pulseaudio pulseaudio-module-bluetooth`

`sudo usermod -a -G bluetooth [user]`

`pulseaudio -k`

`pulseaudio --start`

`sudo systemctl restart bluetooth`

### Mutagen

Python module to handle audio metadata. [Mutagen](https://github.com/quodlibet/mutagen)

`sudo apt-get install python3-mutagen`

### Streamlink

[Streamlink](https://streamlink.github.io/index.html) pipes streams from various services into a player, such as VLC.

`sudo apt install python3-streamlink`
