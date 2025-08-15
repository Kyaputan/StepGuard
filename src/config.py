#==== detection.py ==== 
WEIGHTS_DIR = "./model"
MODEL_NAME = "guard.pt"
MODEL_CONF = 0.7

ALERT_CLASSES = {"Phone"}

VIDEO_PATH = "./video"
VIDEO_NAME = "/20250815_131147.mp4"

SNAPSHOT_DIR = "./snapshots"  
PHONE_HOLD_SECONDS = 4

alert_cooldown = 5

INFER = 10

COOLDOWN_SEC = 15  