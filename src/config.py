from zoneinfo import ZoneInfo
import cv2

#==== detection.py ==== 
WEIGHTS_DIR = "./model"
MODEL_NAME = "guard.onnx"
MODEL_CONF = 0.7

#==== main.py ==== 
VIDEO_PATH = "./video"
VIDEO_NAME = "/20250815_131147.mp4"
INFER = 10
RTSP = "rtsp://root01:12345678@192.168.1.102:554/stream1"
BACKEND = cv2.CAP_FFMPEG
MARGIN = 10

#==== logic.py ==== 
SNAPSHOT_DIR = "./snapshots"  
PHONE_HOLD_SECONDS = 4
ALERT_CLASSES = {"Phone"}
CROP_FRAME = [0.5,0.2]
#==== router.py ==== 
COOLDOWN_SEC = 10

#==== util.py ==== 
ACTIVE_START_H = 6
ACTIVE_START_M = 30

ACTIVE_END_H = 17
ACTIVE_END_M = 30 
TZ = ZoneInfo("Asia/Bangkok")

def debug_config() -> None:
    print(f"[INFO] SNAPSHOT_DIR: {SNAPSHOT_DIR}")
    print(f"[INFO] VIDEO_NAME: {VIDEO_PATH + VIDEO_NAME}")
    print(f"[INFO] INFER: {INFER}")
    value = "" if RTSP is None else str(RTSP).strip()
    if value == "0":
        print("[INFO] RTSP: Webcam")
    elif value.lower().startswith("rtsp"):
        print(f"[INFO] RTSP: {value}")
    else:
        print("#" * 50)
        print(f"[ERROR] Invalid RTSP value: {RTSP} (expected 0 or rtsp://...)")
        print("#" * 50)
    print(f"[INFO] MARGIN: {MARGIN}")
    print(f"[INFO] PHONE_HOLD_SECONDS: {PHONE_HOLD_SECONDS}")
    print(f"[INFO] ALERT_CLASSES: {ALERT_CLASSES}")
    print(f"[INFO] CROP_FRAME: {CROP_FRAME}")
    print(f"[INFO] COOLDOWN_SEC: {COOLDOWN_SEC}")
    print(f"[INFO] ACTIVE_START: {ACTIVE_START_H}:{ACTIVE_START_M}")
    print(f"[INFO] ACTIVE_END: {ACTIVE_END_H}:{ACTIVE_END_M}")
    print(f"[INFO] Timezone: {TZ}")

if __name__ == "__main__":
    debug_config()