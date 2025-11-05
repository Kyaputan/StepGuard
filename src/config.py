from zoneinfo import ZoneInfo
import cv2
import logging
import dotenv
import os
dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
#==== detection.py ==== 
WEIGHTS_DIR = "./model"
MODEL_NAME = "guard.onnx"
MODEL_CONF = 0.3

#==== main.py ==== 
VIDEO_PATH = "./src/utils/save/"
VIDEO_NAME = "recorded_video.avi"
INFER = 1
RTSP = os.getenv("RTSP", "").strip() or "0"
BACKEND = cv2.CAP_FFMPEG
MARGIN = 10

#==== logic.py ==== 
SNAPSHOT_DIR = "./snapshots"  
PHONE_HOLD_SECONDS = 4
ALERT_CLASSES = {"Phone"}
CROP_FRAME = [0.7,0.5]
LOST_TOLERANCE = 5.0  # เพิ่มเพื่อ clear tracks ที่ inactive เร็วขึ้น
#==== router.py ====
COOLDOWN_SEC = 10

#==== util.py ==== 
ACTIVE_START_H = 6
ACTIVE_START_M = 30

ACTIVE_END_H = 17
ACTIVE_END_M = 10

TZ = ZoneInfo("Asia/Bangkok")

def debug_config() -> None:
    logger.info(f"SNAPSHOT_DIR: {SNAPSHOT_DIR}")
    logger.info(f"VIDEO_NAME: {VIDEO_PATH + VIDEO_NAME}")
    logger.info(f"INFER: {INFER}")
    value = "" if RTSP is None else str(RTSP).strip()
    if value == "0":
        logger.info("RTSP: Webcam")
    elif value.lower().startswith("rtsp"):
        logger.info(f"RTSP: {value}")
    else:
        logger.error("#" * 50)
        logger.error(f"[ERROR] Invalid RTSP value: {RTSP} (expected 0 or rtsp://...)")
        logger.error("#" * 50)
    logger.info(f"MARGIN: {MARGIN}")
    logger.info(f"PHONE_HOLD_SECONDS: {PHONE_HOLD_SECONDS}")
    logger.info(f"ALERT_CLASSES: {ALERT_CLASSES}")
    logger.info(f"CROP_FRAME: {CROP_FRAME}")
    logger.info(f"COOLDOWN_SEC: {COOLDOWN_SEC}")
    logger.info(f"ACTIVE_START: {ACTIVE_START_H}:{ACTIVE_START_M}")
    logger.info(f"ACTIVE_END: {ACTIVE_END_H}:{ACTIVE_END_M}")
    logger.info(f"Timezone: {TZ}")

if __name__ == "__main__":
    debug_config()