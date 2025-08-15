from zoneinfo import ZoneInfo
#==== detection.py ==== 
WEIGHTS_DIR = "./model"
MODEL_NAME = "guard.onnx"
MODEL_CONF = 0.7
TZ = ZoneInfo("Asia/Bangkok")
ALERT_CLASSES = {"Phone"}

VIDEO_PATH = "./video"
VIDEO_NAME = "/20250815_131147.mp4"

SNAPSHOT_DIR = "./snapshots"  
PHONE_HOLD_SECONDS = 4

alert_cooldown = 5

INFER = 10

COOLDOWN_SEC = 15

# ====== Time Detect ======
ACTIVE_START_H = 6
ACTIVE_START_M = 30

ACTIVE_END_H = 17
ACTIVE_END_M = 30 