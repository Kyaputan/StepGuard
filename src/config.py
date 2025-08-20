from zoneinfo import ZoneInfo

#==== detection.py ==== 
WEIGHTS_DIR = "./model"
MODEL_NAME = "guard.onnx"
MODEL_CONF = 0.7

#==== main.py ==== 
VIDEO_PATH = "./video"
VIDEO_NAME = "/20250815_131147.mp4"
INFER = 15
RTSP = None
MARGIN = 10

#==== logic.py ==== 
SNAPSHOT_DIR = "./snapshots"  
PHONE_HOLD_SECONDS = 4
ALERT_CLASSES = {"Phone"}
CROP_FRAME = [0.5,0.2]
#==== router.py ==== 
COOLDOWN_SEC = 20

#==== util.py ==== 
ACTIVE_START_H = 6
ACTIVE_START_M = 30

ACTIVE_END_H = 17
ACTIVE_END_M = 30 
TZ = ZoneInfo("Asia/Bangkok")


if __name__ == "__main__":
    print("[INFO] SNAPSHOT_DIR:", SNAPSHOT_DIR)
    print("[INFO] VIDEO_NAME:",VIDEO_PATH + VIDEO_NAME)
    print("[INFO] INFER:", INFER)
    print("[INFO] RTSP:", RTSP)
    print("[INFO] MARGIN:", MARGIN)
    print("[INFO] PHONE_HOLD_SECONDS:", PHONE_HOLD_SECONDS)
    print("[INFO] ALERT_CLASSES:", ALERT_CLASSES)
    print("[INFO] CROP_FRAME:", CROP_FRAME)
    print("[INFO] COOLDOWN_SEC:", COOLDOWN_SEC)
    print("[INFO] ACTIVE_START_H:", ACTIVE_START_H)
    print("[INFO] ACTIVE_START_M:", ACTIVE_START_M)
    print("[INFO] ACTIVE_END_H:", ACTIVE_END_H)
    print("[INFO] ACTIVE_END_M:", ACTIVE_END_M)
    print("[INFO] TZ:", TZ)