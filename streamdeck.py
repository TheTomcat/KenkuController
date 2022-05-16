import serial
import time
import requests

arduino = serial.Serial(port='COM8', baudrate=115200, timeout=0.1)
base_url = "http://127.0.0.1:3333/v1/"

### Define IDs here
ID_BANK = {
    'Corruption':'34567dac-cff2-4f9f-baee-c0e6cb47c90a',
    'Eternal War':'4f46398d-5405-4779-8b9e-9e130db128c6',
    'RyG': '3cde1b56-61b1-4f06-b458-fb11162bb6fb',
    'Diablo Rojo': 'f3c3335b-7a41-4a0d-bc3b-397caea407cd',
    'Hanuman':'12113efa-b1d6-4d48-a156-f2e8c4f4c515',
    'Tavern':'fb86dc01-25a4-4b56-9e8c-d0e48b444eb3',
    'Library':'ea13c936-e7af-459f-ab1e-7d5949035c0f',
    'Ambience':'0da5726a-dd14-4294-81a1-34de737d9e0d',
    'Market':'',
    'Sewer':''
}

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

    @property
    def base_url(self):
        return "http://"+self.url + ":" + str(self.port) + "/v1/"
    def make_url(self, *path):
        return self.base_url + "/".join(path)

    def put(self, path, json_payload=None):
        return requests.put(self.make_url(*path), json=json_payload)
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

    def handle_response(self, response: requests.Response, message=""):
        "Optional response handler. Mostly for debugging"
        if message:
            message = " " + message
        match response.status_code:
            case 200:
                print(f"Success 200{message}: {response.json()}")
            case _:
                print(f"Error   {response.status_code}{message}: {response.json()}")
        return response

    def soundboard_play(self, uuid:str):
        "Play the soundboard element corresponding to `uuid`"
        response = self.put(("soundboard","play"), {'id':uuid})
        return self.handle_response(response)
        
    def soundboard_stop(self, uuid: str):
        "Stop playing the soundboard element corresponding to `uuid`"
        response = self.put(("soundboard","stop"), {'id':uuid})
        return self.handle_response(response)

    def update_soundboard_state(self):
        "Get the state of the soundboard"
        response = self.get(("soundboard","playback"))
        self._soundboard_state = response.json()
        return self.handle_response(response)

    def playlist_play(self, uuid: str):
        "Play the playlist/track corresponding to `uuid`"
        response = self.put(("playlist","play"), {'id':uuid})
        return self.handle_response(response)

    def update_playlist_state(self):
        "Get the state of the playlist"
        response = self.get(("playlist","playback"))
        self._playlist_state = response.json()
        return self.handle_response(response)

    def playlist_unpause(self):
        "Unpause the currently playing track"
        response = self.put(("playlist","playback","play"))
        return self.handle_response(response)
    
    def playlist_pause(self):
        "Pause the currently playing track"
        response = self.put(("playlist","playback","pause"))
        return self.handle_response(response)
    
    def playlist_next(self):
        "Advance to the next track in the playlist"
        response = self.put(("playlist","playback","next"))
        return self.handle_response(response)
    
    def playlist_prev(self):
        "Return to the previous track in the playlist"
        response = self.put(("playlist","playback","previous"))
        return self.handle_response(response)
    
    def playlist_mute(self, mute: bool):
        "Set the mute mode of the player to `mute` (Bool, True or False)"
        response = self.put(("playlist","playback","mute"), {"mute":mute})
        return self.handle_response(response)
    
    def playlist_volume(self, volume: float):
        "Set the volume to `volume`. Value in the range 0-1"
        response = self.put(("playlist","playback","volume"), {"volume":volume})
        return self.handle_response(response)

    def playlist_shuffle(self, shuffle: bool):
        "Set the shuffle mode to `shuffle` (Bool, True or False)"
        response = self.put(("playlist","playback","shuffle"), {"shuffle":shuffle})
        return self.handle_response(response)
    
    def playlist_repeat(self, repeat):
        response = self.put(("playlist","playback","repeat"), {"repeat":repeat})
        return self.handle_response(response)

    def playlist_repeat_rot(self):
        "Rotate through repeat modes (off, playlist, track)"
        cycle = ("off","playlist","track")
        rpt = self.playlist_state['repeat']
        next_rpt = cycle[(cycle.index(rpt)+1)%len(cycle)]
        self.playlist_repeat(next_rpt)
        self._playlist_state['repeat'] = next_rpt
        self._playlist_expiry += self.timeout
    
    def playlist_volume_up(self, inc=0.05):
        "Increase the volume by 5 points"
        volume = self.playlist_state['volume']
        volume = min(1, volume+inc)
        self.playlist_volume(volume)
        self._playlist_state['volume'] = volume
        self._playlist_expiry += self.timeout

    def playlist_volume_down(self, inc=0.05):
        "Decrease the volume by 5 points"
        volume = self.playlist_state['volume']
        volume = max(0, volume-inc)
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
        
    def soundboard_toggle_play(self, uuid: str):
        "Start or stop the element corresponding to `uuid`"
        sounds = self.soundboard_state['sounds']
        is_playing = list(filter(lambda x: x['id']==uuid, sounds))
        if is_playing: # Stop
            self.soundboard_stop(uuid)
        else: # Start
            self.soundboard_play(uuid)
    
    def all_fade_out(self, over=0.2):
        self.is_faded = True
        
        

def handle_instruction(char, kenku:KenkuFM):
    match char:
        case char if char.startswith(b'0'):
            ...
        case char if char.startswith(b'1'):
            kenku.playlist_play(ID_BANK['Corruption'])
            kenku.playlist_repeat('track')
            
        case char if char.startswith(b'2'):
            kenku.playlist_play(ID_BANK['Eternal War'])
            kenku.playlist_repeat('track')
            
        case char if char.startswith(b'3'):
            kenku.playlist_play(ID_BANK['Hanuman'])
            kenku.playlist_repeat('track')

        case char if char.startswith(b'4'):
            kenku.playlist_play(ID_BANK['Diablo Rojo'])
            kenku.playlist_repeat('track')

        case char if char.startswith(b'5'):
            kenku.playlist_play(ID_BANK['Ambience'])
            kenku.playlist_repeat('track')
            ...
        case char if char.startswith(b'6'):
            ...
        case char if char.startswith(b'7'):
            kenku.soundboard_toggle_play(ID_BANK['Library'])

        case char if char.startswith(b'8'):
            kenku.soundboard_toggle_play(ID_BANK['Tavern'])

        case char if char.startswith(b'9'):
            ...
        case char if char.startswith(b'*'):
            ...
        case char if char.startswith(b'#'):
            # Fade all out
            sounds = kenku.soundboard_state['sounds']
            for sound in sounds:
                kenku.soundboard_stop(sound['id'])
            for f in range(20,-1,-1):
                kenku.playlist_volume_down()

        case char if char.startswith(b'+'):
            kenku.playlist_volume_up()
        case char if char.startswith(b'-'):
            kenku.playlist_volume_down()
        case char if char.startswith(b'S'):
            kenku.playlist_toggle_pause()
        case _:
            return
    print(char)
    

def loop():        
    kenku = KenkuFM()
    while True:
        line = arduino.readline()
        if line:
            handle_instruction(line, kenku)
        time.sleep(0.05)

if __name__ == "__main__":
    loop()