from zoneinfo import ZoneInfo

#==== detection.py ==== 
WEIGHTS_DIR = "./model"
MODEL_NAME = "guard.onnx"
MODEL_CONF = 0.7

#==== main.py ==== 
VIDEO_PATH = "./video"
VIDEO_NAME = "/20250815_131147.mp4"
INFER = 15
RTSP = 0
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

def debug_config():
    print(f"[INFO] SNAPSHOT_DIR: {SNAPSHOT_DIR}")
    print(f"[INFO] VIDEO_NAME: {VIDEO_PATH + VIDEO_NAME}")
    print(f"[INFO] INFER: {INFER}")
    print(f"[INFO] RTSP: {RTSP}")
    print(f"[INFO] MARGIN: {MARGIN}")
    print(f"[INFO] PHONE_HOLD_SECONDS: {PHONE_HOLD_SECONDS}")
    print(f"[INFO] ALERT_CLASSES: {ALERT_CLASSES}")
    print(f"[INFO] CROP_FRAME: {CROP_FRAME}")
    print(f"[INFO] COOLDOWN_SEC: {COOLDOWN_SEC}")
    print(f"[INFO] ACTIVE_START: {ACTIVE_START_H}:{ACTIVE_START_M}")
    print(f"[INFO] ACTIVE_END: {ACTIVE_END_H}:{ACTIVE_END_M}")
    print(f"[INFO] TZ: {TZ}")

if __name__ == "__main__":
    debug_config()