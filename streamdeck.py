import serial
import time
import requests

arduino = serial.Serial(port='COM8', baudrate=115200, timeout=0.1)
base_url = "http://127.0.0.1:3333/v1/"

### Define IDs here
ID_BANK = {
    'Corruption':'34567dac-cff2-4f9f-baee-c0e6cb47c90a',
    
}

class KenkuFM(object):
    def __init__(self, url="127.0.0.1", port=3333, freshness=1):
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
        if message:
            message = " " + message
        match response.status_code:
            case 200:
                print(f"Success 202{message}: {response.json()}")
            case _:
                print(f"Error   {response.status_code}{message}: {response.json()}")
        return response

    def soundboard_play(self, id:str):
        response = self.put(("soundboard","play"), {'id':id})
        return self.handle_response(response)
        
    def soundboard_stop(self, id):
        response = self.put(("soundboard","stop"), {'id':id})
        return self.handle_response(response)

    def update_soundboard_state(self):
        response = self.get(("soundboard","playback"))
        self._soundboard_state = response.json()
        return self.handle_response(response)

    def playlist_play(self, id):
        response = self.put(("playlist","play"), {'id':id})
        return self.handle_response(response)

    def update_playlist_state(self):
        response = self.get(("playlist","playback"))
        self._playlist_state = response.json()
        return self.handle_response(response)

    def playlist_unpause(self):
        response = self.put(("playlist","playback","play"))
        return self.handle_response(response)
    
    def playlist_pause(self):
        response = self.put(("playlist","playback","pause"))
        return self.handle_response(response)
    
    def playlist_next(self):
        response = self.put(("playlist","playback","next"))
        return self.handle_response(response)
    
    def playlist_prev(self):
        response = self.put(("playlist","playback","previous"))
        return self.handle_response(response)
    
    def playlist_mute(self, mute):
        response = self.put(("playlist","playback","mute"), {"mute":mute})
        return self.handle_response(response)
    
    def playlist_volume(self, volume):
        response = self.put(("playlist","playback","volume"), {"volume":volume})
        return self.handle_response(response)
    
    def playlist_volume_up(self):
        volume = self.playlist_state['volume']
        volume = min(1, volume+0.05)
        self.playlist_volume(volume)
        self._playlist_state['volume'] = volume
        self._playlist_expiry += self.timeout

    def playlist_volume_down(self):
        s = self.playlist_state
        volume = s['volume']
        volume = max(0, volume-0.05)
        self.playlist_volume(volume)
        self._playlist_state['volume'] = volume
        self._playlist_expiry += self.timeout
    
    def playlist_toggle_pause(self):
        playing = self.playlist_state['playing']
        if playing:
            self.playlist_pause()
            self._playlist_state['playing']=False
        else:
            self.playlist_unpause()
            self._playlist_state['playing']=True
        

def handle_instruction(char, kenku:KenkuFM):
    #char = char[0]
    match char:
        case char if char.startswith(b'0'):
            ...
        case char if char.startswith(b'1'):
            ...
        case char if char.startswith(b'2'):
            ...
        case char if char.startswith(b'3'):
            ...
        case char if char.startswith(b'4'):
            ...
        case char if char.startswith(b'5'):
            ...
        case char if char.startswith(b'6'):
            ...
        case char if char.startswith(b'7'):
            ...
        case char if char.startswith(b'8'):
            ...
        case char if char.startswith(b'9'):
            ...
        case char if char.startswith(b'*'):
            ...
        case char if char.startswith(b'#'):
            ...
        case char if char.startswith(b'+'):
            kenku.playlist_volume_up()
        case char if char.startswith(b'-'):
            kenku.playlist_volume_down()
        case char if char.startswith(b'S'):
            kenku.playlist_toggle_pause()
        case _:
            print(f"unaction - {char}")
            return
    print(char)

def loop():        
    kenku = KenkuFM()
    while True:
        line = arduino.readline()

        if line:
            handle_instruction(line, kenku)
            # if line.startswith(b'A'):
            #     p = requests.get(base_url+"playlist/playback")
            #     print(p.json())
            # else:
            #     print(line[0])
        time.sleep(0.05)

if __name__ == "__main__":
    loop()