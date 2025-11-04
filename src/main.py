import cv2
import os
import time
from detection import load_model, infer , parse_results , debug_detection
from logic import draw_person_status, PhoneHoldTracker
from camera import VideoSource
from config import SNAPSHOT_DIR , VIDEO_PATH , VIDEO_NAME , INFER , TZ , MARGIN , RTSP , BACKEND, debug_config
from util import is_active_hour , start_scheduler , next_midnight_bkk
from datetime import datetime
from router import send_text
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
from router import notify_violation
import gc, torch
import psutil
import os

def main():
    try:
        start_scheduler(test_once=False)
        model = load_model()
        os.makedirs(VIDEO_PATH, exist_ok=True)
        os.makedirs(SNAPSHOT_DIR, exist_ok=True)
        cam = VideoSource(VIDEO_PATH + VIDEO_NAME,BACKEND , every_n=INFER)
        # cam = VideoSource(RTSP,BACKEND , every_n=INFER)
        tracker = PhoneHoldTracker()  
        next_clear = next_midnight_bkk()
        last_results = []
        prev_active = None
        total_alerts = 0
        total_normals = 0
        frame_count = 0
        process = psutil.Process(os.getpid())
    except Exception as e:
        logger.error(f"[ERROR] Initialization failed: {e}")
        return
    
    try:
        while True:
            now = datetime.now(TZ)
            if now >= next_clear:
                next_clear = next_midnight_bkk(now)
            ok, frame = cam.read()
            if not ok:
                logger.error("Camera read failed")
                time.sleep(1)  # เพิ่ม sleep เพื่อป้องกัน loop เร็วเกินไป
                continue
            logger.debug(f"[Camera] Read frame {frame_count}, shape: {frame.shape}")

            for _ in range(5):
                cam.grab()
            logger.debug(f"[Camera] Grabbed 5 frames")

            frame = cv2.resize(frame, (640, 640))
            logger.debug(f"[Processing] Resized frame to {frame.shape}")
            active = is_active_hour(now)

            if not active:
                if prev_active is None or prev_active is True:
                    logger.info(f"[INFO {now.time()}] OFF-HOURS: pause YOLO now")
                    send_text(
                    f"วันนี้ตรวจจับได้ทั้งหมด {total_alerts + total_normals} ครั้ง\n"
                    f"- มีคนใช้โทรศัพท์ {total_alerts} ครั้ง ({(total_alerts / (total_alerts + total_normals)) * 100 if (total_alerts + total_normals) > 0 else 0:.1f}%)\n"
                    f"- มีคนไม่ใช้โทรศัพท์ {total_normals} ครั้ง ({(total_normals / (total_alerts + total_normals)) * 100 if (total_alerts + total_normals) > 0 else 0:.1f}%)")
                    time.sleep(1)
                    last_results = []
                    total_alerts = 0
                    total_normals = 0
                # cv2.imshow("Detection", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                prev_active = False
                cam.frame_idx += 1
                time.sleep(0.1)  # เพิ่ม sleep เล็กน้อยเพื่อลด CPU usage
                continue

            if prev_active is None or prev_active is False:
                logger.info(f"[INFO {now.time()}] ON-HOURS: resume YOLO")
            if cam.should_infer():
                try:
                    logger.debug(f"[Inference] Starting inference on frame {frame_count}")
                    yolo_results = infer(model, frame)
                    person_results = parse_results(yolo_results , margin=MARGIN)
                    del yolo_results
                    last_results = person_results
                    logger.debug(f"[Inference] Detected {len(person_results)} persons")
                except Exception as e:
                    logger.error(f"[ERROR] Inference failed: {e}")
                    person_results = last_results if last_results else []
            else:
                person_results = last_results if last_results else []
            if person_results:
                try:
                    logger.debug(f"[Processing] Updating tracker with {len(person_results)} detections")
                    path = tracker.update(person_results, frame, time.time())
                    status = draw_person_status(frame, person_results)
                    if status["has_alert"] and time.time() - tracker.last_alert_phone_time > tracker.alert_cooldown_phone:
                        logger.info("Phone detected")
                        tracker.last_alert_phone_time = time.time()
                        total_alerts += status["alerts"]
                        if path:
                            logger.debug(f"[Alert] Sending violation notification for {path}")
                            notify_violation(path)
                    if status["has_normal"] and time.time() - tracker.last_alert_normal_time > tracker.alert_cooldown_normal:
                        logger.info("Normal detected")
                        tracker.last_alert_normal_time = time.time()
                        total_normals += status["normals"]
                except Exception as e:
                    logger.error(f"[ERROR] Processing results failed: {e}")


            # cv2.imshow("Detection", frame)
            frame_count += 1
            if frame_count % 100 == 0:
                mem_info = process.memory_info()
                logger.info(f"[DEBUG] Frame {frame_count}: RAM usage: {mem_info.rss / 1024 / 1024:.2f} MB")
            if frame_count % 200 == 0:
                gc.collect()
            if cv2.waitKey(1) & 0xFF == ord('q'):
                logger.info("[INFO] Exit")
                break
            prev_active = True
            cam.frame_idx += 1
            time.sleep(0.01)  # เพิ่ม sleep เล็กน้อยเพื่อลด CPU usage
            
    finally:
        logger.info("Releasing camera")
        logger.info(f"total_normals: {total_normals}")
        logger.info(f"total_alerts: {total_alerts}")
        try:
            send_text(
                        f"วันนี้ตรวจจับได้ทั้งหมด {total_alerts + total_normals} ครั้ง\n"
                        f"- มีคนใช้โทรศัพท์ {total_alerts} ครั้ง ({(total_alerts / (total_alerts + total_normals)) * 100 if (total_alerts + total_normals) > 0 else 0:.1f}%)\n"
                        f"- มีคนไม่ใช้โทรศัพท์ {total_normals} ครั้ง ({(total_normals / (total_alerts + total_normals)) * 100 if (total_alerts + total_normals) > 0 else 0:.1f}%)")
        except Exception as e:
            logger.error(f"[ERROR] Failed to send final report: {e}")
        try:
            cam.release()
        except Exception as e:
            logger.error(f"[ERROR] Failed to release camera: {e}")
        cv2.destroyAllWindows()

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    debug_detection()
    debug_config()
    time.sleep(5)
    logger.info("Starting main...")
    time.sleep(3)
    os.system('cls' if os.name == 'nt' else 'clear')
    main()
