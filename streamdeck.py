import serial
from serial.tools import list_ports
from serial.serialutil import SerialException
import time
import requests
from requests.exceptions import ConnectionError
import urllib3
import yaml

class KenkuFM(object):
    def __init__(self, url="127.0.0.1", port=3333, freshness=1):
        """Create bindings to the KenkuFM remote.

        URL and port are pretty self-explanatory.
        freshness determines how often the state of the player needs to be checked. 1s seems appropriate for most uses
        This is important for repeated quick tasks, like turning a knob to increase the volume.
        If freshness is 0 (or less than the response rate of the knob) then each time to increase the volume, the binding will query the player for the current volume level.

        Args:
            url (str, optional): The url of the machine hosting the Kenku player. Defaults to "127.0.0.1".
            port (int, optional): The port on which Kenku FM is listening. Defaults to 3333.
            freshness (int, optional): How quickly does the state go stale (in seconds). Defaults to 1.
        """
        self.url: str = url
        self.port: int = port 
        self._playlist_state=None
        self._soundboard_state=None
        self.timeout=freshness
        self._playlist_expiry=0
        self._soundboard_expiry=0
        # if response_handler is None:
        #     response_handler = lambda *x: None
        # self.handle_response = response_handler

    @property
    def base_url(self):
        return "http://"+self.url + ":" + str(self.port) + "/v1/"
    def make_url(self, *path):
        return self.base_url + "/".join(path)

    def put(self, path, json_payload=None):
        #try:
        return requests.put(self.make_url(*path), json=json_payload)
        #except ConnectionError as e:
            #return 
    def get(self, path):
        return requests.get(self.make_url(*path))
    def post(self, path):
        return requests.post(self.make_url(*path))

    @property
    def playlist_state(self):
        if time.time() > self._playlist_expiry:
            self.update_playlist_state()
            self._playlist_expiry = time.time()+self.timeout
        return self._playlist_state

    @property
    def soundboard_state(self):
        if time.time() > self._soundboard_expiry:
            self.update_soundboard_state()
            self._soundboard_expiry = time.time()+self.timeout
        return self._soundboard_state

    def soundboard_play(self, id:str, **kwargs):
        "Play the soundboard element corresponding to `id`"
        response = self.put(("soundboard","play"), {'id':id})
        return response
        
    def soundboard_stop(self, id: str, **kwargs):
        "Stop playing the soundboard element corresponding to `id`"
        response = self.put(("soundboard","stop"), {'id':id})
        return response

    def update_soundboard_state(self):
        "Get the state of the soundboard"
        response = self.get(("soundboard","playback"))
        self._soundboard_state = response.json()
        return response

    def playlist_play(self, id: str, **kwargs):
        """Play the playlist/track corresponding to `id`. 
        Known issue: if this is called twice with the same id, that music will stop playing, and will be unable to be restarted. Pausing/unpausing has no effect. """
        response = self.put(("playlist","play"), {'id':id})
        return response

    def update_playlist_state(self):
        "Get the state of the playlist"
        response = self.get(("playlist","playback"))
        self._playlist_state = response.json()
        return response

    def playlist_unpause(self):
        "Unpause the currently playing track"
        response = self.put(("playlist","playback","play"))
        return response
    
    def playlist_pause(self):
        "Pause the currently playing track"
        response = self.put(("playlist","playback","pause"))
        return response
    
    def playlist_next(self):
        "Advance to the next track in the playlist"
        response = self.put(("playlist","playback","next"))
        return response
    
    def playlist_prev(self):
        "Return to the previous track in the playlist"
        response = self.put(("playlist","playback","previous"))
        return response
    
    def playlist_mute(self, mute: bool):
        "Set the mute mode of the player to `mute` (Bool, True or False)"
        response = self.put(("playlist","playback","mute"), {"mute":mute})
        return response
    
    def playlist_volume(self, volume: float):
        "Set the volume to `volume`. Value in the range 0-1"
        response = self.put(("playlist","playback","volume"), {"volume":volume})
        return response

    def playlist_shuffle(self, shuffle: bool):
        "Set the shuffle mode to `shuffle` (Bool, True or False)"
        response = self.put(("playlist","playback","shuffle"), {"shuffle":shuffle})
        return response
    
    def playlist_repeat(self, repeat: str):
        response = self.put(("playlist","playback","repeat"), {"repeat":repeat})
        return response

    def playlist_repeat_rot(self):
        "Rotate through repeat modes (off, playlist, track)"
        cycle = ("off","playlist","track")
        rpt = self.playlist_state['repeat']
        next_rpt = cycle[(cycle.index(rpt)+1)%len(cycle)]
        self.playlist_repeat(next_rpt)
        self._playlist_state['repeat'] = next_rpt
        self._playlist_expiry += self.timeout
    
    def playlist_volume_up(self, increment=0.05):
        "Increase the volume by 5 points"
        volume = self.playlist_state['volume']
        volume = min(1, volume+float(increment))
        self.playlist_volume(volume)
        self._playlist_state['volume'] = volume
        self._playlist_expiry += self.timeout

    def playlist_volume_down(self, decrement=0.05):
        "Decrease the volume by 5 points"
        volume = self.playlist_state['volume']
        volume = max(0, volume-float(decrement))
        self.playlist_volume(volume)
        self._playlist_state['volume'] = volume
        self._playlist_expiry += self.timeout
    
    def playlist_toggle_pause(self):
        "Start or stop the playlist"
        playing = self.playlist_state['playing']
        if playing:
            self.playlist_pause()
            self._playlist_state['playing']=False
        else:
            self.playlist_unpause()
            self._playlist_state['playing']=True
        
    def soundboard_toggle_play(self, **kwargs):
        "Start or stop the element corresponding to `id`"
        sounds = self.soundboard_state['sounds']
        is_playing = list(filter(lambda x: x['id']==id, sounds))
        if is_playing: # Stop
            self.soundboard_stop(id)
        else: # Start
            self.soundboard_play(id)
    
    def stop_all(self):
        sounds = self.soundboard_state['sounds']
        for sound in sounds:
            self.soundboard_stop(sound['id'])
        self.playlist_pause()
       
class SoundboardInterface(object):
    def __init__(self, path_to_config):
        with open(path_to_config, 'r') as f:
            self.config = yaml.load(f.read(), Loader=yaml.BaseLoader)
        #self.process_config() ## TODO: this will be necessary later
        self._kenku_url = self.config['kenku'].get('url','127.0.0.1')
        self._kenku_port = self.config['kenku'].get('port',3333)
        self._kenku_freshness = self.config['kenku'].get('freshness',1)
        self.kenku = KenkuFM(url=self._kenku_url,
                             port=self._kenku_port,
                             freshness=self._kenku_freshness)
        self._serial_port=self.config['serial'].get('port', 'auto')
        self._serial_baud=self.config['serial'].get('baud',9600)
        self._serial_timeoutt=self.config['serial'].get('timeout',0.1)
        self._serial_opened = False

        self.actions = self.config['keys']
        for action in self.actions:
            for command in self.actions[action]['commands']:

                if not isinstance(self.actions[action]['commands'][command], dict):
                    self.actions[action]['commands'][command] = {}
    
    def process_config(self):
        raise NotImplementedError

    def close_serial(self):
        if self._serial_opened:
            self.serial.close()
    
    def open_serial(self):
        if self._serial_port == 'auto':
            # Attempt to autodetect the serial port
            self.log('Attempting to autodetect serial port: ', end="")
            comports = list_ports.comports()
            for port in comports:
                if ('arduino' in port.description.lower() or
                    'ftdi' in port.description.lower() or
                    'ch340' in port.description.lower()):
                    self.log(f"Found port at {port.name}:{port.description}")
                    self._serial_port = port.name
                    break
            if self._serial_port == 'auto':
                raise ConnectionError(f"invalid port - Unable to automatically detect serial port")
        self.serial = serial.Serial(port=self._serial_port,
                                    baudrate=self._serial_baud,
                                    timeout=self._serial_timeoutt)
        self.log('Connected!')
        self._serial_opened=True
    
    def process_instruction(self, instruction: bytes):
        str_rep = instruction.decode('ascii')[0]
        self.log(f"RCV {str_rep}: ", end="")
        if str_rep in self.actions:
            try:
                commands = self.actions[str_rep]['commands']
                for command in commands:
                    self.log(f"Exec -> {command}->{commands[command]}")
                    self.kenku.__getattribute__(command)(**commands[command])
                
                self.acknowledge()
            except KeyError as e:
                raise e
            except ConnectionError as e:
                self.log("ERR Unable to connect to Kenku FM instance")
        else: 
            self.log(f'{str_rep} not found')

    def acknowledge(self):
        self.log("ACK")
        self.serial.write(b"Y")
    
    def pong(self):
        self.serial.write(b'a')
        self.log("Pong")

    def log(self, *args, **kwargs):
        print(*args, **kwargs)

    def run(self):
        try:
            self.open_serial()
            while True:
                time.sleep(0.01)
                if self.serial.in_waiting:
                    instruction = self.serial.readline()
                    if instruction:
                        if instruction.startswith(b'p'):
                            self.log("Ping->",end="")
                            self.pong()
                            continue
                        self.process_instruction(instruction)
        except SerialException as e:
            self.log(f"ERR Unable to establish a serial connection at {self._serial_port}")
        finally:
            self.log("Closing gracefully...")
            self.close_serial()

if __name__ == "__main__":
    interface = SoundboardInterface('config.yaml')
    interface.run()