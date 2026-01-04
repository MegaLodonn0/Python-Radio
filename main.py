import os
import sys
import vlc
import yt_dlp
import json
import threading

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, BackgroundTasks
from ytmusicapi import YTMusic

# ------Basic Config------
yt = YTMusic()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
MUSIC_PATH = "Musics"

if not os.path.exists(MUSIC_PATH): os.makedirs(MUSIC_PATH)


class radio:
    def __init__(self):
        # -----VSL Config------
        self.instance = vlc.Instance("--no-xlib", "--quiet")
        self.player = self.instance.media_player_new()

        # -----Current Situation-----
        self.isPlaying = False
        self.curentVideoId = None

        # -----Basic List Params-----
        self.history = []
        self.historyIndex = -1
        self.songCache = {}
        self.playerHistory = []
        #self.musicMap = {os.path.splitext(f)[0]: f for f in os.listdir(MUSIC_PATH) if os.path.isfile(os.path.join(MUSIC_PATH, f))}

        self.lock = threading.RLock()

    @property
    def musicMap(self):
        return {os.path.splitext(f)[0]: os.path.join(MUSIC_PATH, f) for f in os.listdir(MUSIC_PATH) if os.path.isfile(os.path.join(MUSIC_PATH, f))} 



    def download(self, videoId: str, quality: str="bestaudio/best"):
        if videoId in self.musicMap:
            print("File Faund!")
            return {"path": self.musicMap[videoId]}

        else:
            url= f"https://www.youtube.com/watch?v={videoId}"
            path= os.path.join(MUSIC_PATH, f"{videoId}.webm")

            # ---Progress Bar---
            def progressHook(d):
                if d["status"] == 'downloading':
                    try:
                        p = d.get('_percent_str', 'N/A').replace('%','')
                        speed = d.get('_speed_str', 'N/A')
                        eta = d.get('_eta_str', 'N/A')
                        sys.stdout.write(f"\r⬇️ Downloading: %{p} | Speed: {speed} | Remaining: {eta}   ")
                        sys.stdout.flush()
                    except: pass
                elif d["status"] == "finished":
                    sys.stdout.write(f"\n✅ Download complete: {videoId}\n")
                    sys.stdout.flush()

            ytdlpOpts= {
                "format": quality,
                "no_warnings": True,
                "quiet": True,
                "outtmpl": path,
                "progressHook":[progressHook],
                }

            try:
                print("Video Downloading ...")
                with yt_dlp.YoutubeDL(ytdlpOpts) as ydl:
                    return {"path": path}
            except Exception as e:
                print(f"Error: {e}")
                return {"Error": e}

    def playMusic(self, videoId):
        with self.lock:
            path = self.musicMap.get(videoId)
            if not path:
                self.download(videoId)
                path = self.musicMap.get(videoId)
                
                if not path: return {"status": "Error", "mgs": "Downloading Failed"}

            self.curentVideoId = videoId
            media = self.instance.media_new(path)
            self.player.set_media(media)
            self.player.play()
            self.isPlaying = True
            print(f"▶️ Playing: {videoId}")
            return {"Status": f"{videoId} Is Playing"}
            
        if self.curentVideoId in self.playerHistory: self.playerHistory.remove(videoId)

        self.playerHistory.append(videoId)

    def stopMusic(self):
        self.player.stop()
        self.isPlaying = False

    # ---Pause/Resume Music---
    def pauseMusic(self, pause):
        self.player.set_pause(pause)

    # defult return length = 5
    # costum return example: /getSuggestion/<videoId>?limit=10
    def getSuggestion(self, videoId: str, length: int= 5):
        if not self.songCache:
            firstSongEntry = [{
                    "id": videoId,
                    "title": "N/A",
                    "url": f"https://img.youtube.com/vi/{videoId}/mqdefault.jpg", 
                    "length": "N/A"
                    }]
            self.songCache.update({item["id"]: item for item in firstSongEntry})
            self.history.extend([item["id"] for item in firstSongEntry])

        playlist = yt.get_watch_playlist(videoId= videoId, limit= length)
        cleanPlaylist = [
            {
                "title": i["title"],
                "length": i["length"],
                "id": i["videoId"],
                "url": f"https://img.youtube.com/vi/{i['videoId']}/mqdefault.jpg",
                "views": i.get("views", "0")
            }
            for i in playlist["tracks"][:length]
        ]
        self.songCache.update({item["id"]: item for item in cleanPlaylist})
        self.history.extend([item["id"] for item in cleanPlaylist])
        print(self.history)

    def nextMusic(self):
        with self.lock:
            if self.historyIndex < len(self.history)-1:
                self.historyIndex += 1
                nextId = self.history[self.historyIndex]
                self.playMusic(nextId)
                return {"Status": "Playing In history", "id": nextId}

            else:
                currentSeed = self.curentVideoId or (self.history[-1] if self.history else None)
                if not currentSeed: return {"status": "error", "msg": "No Reference"}

                try:
                    self.getSuggestion(currentSeed, length= 10)
                    if self.historyIndex < len(self.history)-1:
                        self.historyIndex += 1
                        nextId = self.history[self.historyIndex]

                    else: return {"status": "Error", "msg": "No New Song"}

                except Exception as e:
                    print(f"API Error: {e}")
                    return {"status": "Error", "msg": str(e)}
                
                self.playMusic(nextId)
                return {"status": "Playing New Song", "id": nextId}


    def prevMusic(self):
        with self.lock:
            if self.historyIndex > 0:
                self.historyIndex -= 1
                prev = self.history[self.historyIndex]
                self.playMusic(prev)
                return {"status": "ok", "id": prev}
            return{"status": "Error", "msg": "Beginning of the History"}

    def manageMemory(self):
        if len(history):
            pass







import time
rd = radio()
#rd.download("TDl79ZlS9tg")
#rd.playMusic("TDl79ZlS9tg")
#time.sleep(5)
#rd.pauseMusic(True)
#time.sleep(3)
#rd.pauseMusic(False)
#time.sleep(3)
#rd.stopMusic()
rd.getSuggestion("TDl79ZlS9tg")
rd.nextMusic()
rd.nextMusic()
print(rd.playerHistory)





"""
@app.get("/seyHello")
def seyHello():
    return {"message": "Hello"}



@app.post("/getSuggestion/{videoId}")

@app.post("/download/{videoId}")
def download(videoId: str, qualty: str= "bestaudio/best"):


@app.get("play/{videoId}")
def play(videoId: str, )


"""
