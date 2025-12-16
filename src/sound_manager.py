import pygame
import os
import time
from config import WEIGHTS_DIR, MODEL_NAME

pygame.mixer.init()
sound_path = os.path.join(WEIGHTS_DIR, "Hello.wav")
try:
    alert_sound = pygame.mixer.Sound(sound_path) 
    print("✅ Audio System Ready: Sound loaded.")
except FileNotFoundError:
    print("❌ Error: ไม่พบไฟล์ warning.wav กรุณาตรวจสอบ Path")
    alert_sound = None

def Alert():
    if alert_sound:
        alert_sound.play()
    else:
        print("Alert triggered (No sound file loaded)")
        

if __name__ == "__main__":
    print("🚀 System Started...")
    
    counter = 0
    
    try:
        while True:
            counter += 1
            if counter % 50 == 0:
                print(f"[{counter}] ⚠️ DETECTED! Calling Alert...")
                Alert() 
            time.sleep(0.1) 
            
    except KeyboardInterrupt:
        print("\nStopping System...")