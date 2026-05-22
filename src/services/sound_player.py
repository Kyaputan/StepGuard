import threading
import time
from pathlib import Path
import pygame
from config import SOUND_ALERT_PATH

try:
    pygame.mixer.init()
    print("[INFO] Pygame mixer successfully initialized.")
except Exception as e:
    print(f"[WARNING] Failed to initialize Pygame mixer: {e}. Audio alerts will be disabled.")

_sound_cache = {}
_cache_lock = threading.Lock()

def _load_sound(sound_path: str):
    """Loads a sound into the cache if not already loaded, with error handling."""
    with _cache_lock:
        if sound_path in _sound_cache:
            return _sound_cache[sound_path]
        
        path = Path(sound_path)
        if not path.exists():
            alternatives = list(path.parent.glob("*.wav")) + list(path.parent.glob("*.mp3"))
            if alternatives:
                print(f"[WARNING] Sound file '{sound_path}' not found. Using alternative: {alternatives[0]}")
                path = alternatives[0]
            else:
                print(f"[WARNING] Sound file '{sound_path}' not found and no alternatives exist.")
                return None
                
        try:
            sound = pygame.mixer.Sound(str(path))
            _sound_cache[sound_path] = sound
            return sound
        except Exception as e:
            print(f"[ERROR] Failed to load sound '{path}': {e}")
            return None

def play_alert_sound(sound_path: str = SOUND_ALERT_PATH):
    """
    Plays the specified alert sound in a separate thread.
    Does not block the calling thread.
    """
    def _play_thread():
        try:
            if not pygame.mixer.get_init():
                return
                
            sound = _load_sound(sound_path)
            if sound:
                print(f"[SOUND] Playing warning alert: {sound_path}")
                channel = sound.play()
                while channel and channel.get_busy():
                    time.sleep(0.1)
        except Exception as e:
            print(f"[ERROR] Exception during sound playback: {e}")

    threading.Thread(target=_play_thread, daemon=True).start()

if __name__ == "__main__":
    print("Testing refactored sound player playback...")
    play_alert_sound()
    time.sleep(3)
    print("Test complete.")
