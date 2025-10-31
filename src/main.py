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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
from router import notify_violation

def main():
    try:
        start_scheduler(test_once=False)
        model = load_model()
        os.makedirs(VIDEO_PATH, exist_ok=True)
        os.makedirs(SNAPSHOT_DIR, exist_ok=True)
        cam = VideoSource(RTSP,BACKEND , every_n=INFER)
        # cam = VideoSource(VIDEO_PATH + VIDEO_NAME, every_n=INFER)
        tracker = PhoneHoldTracker()  
        next_clear = next_midnight_bkk()
        last_results = []
        prev_active = None
        total_alerts = 0
        total_normals = 0
    except Exception as e:
        logger.error(f"[ERROR] {e}")
        return
    
    try:
        while True:
            now = datetime.now(TZ)
            if now >= next_clear:
                next_clear = next_midnight_bkk(now)
            ok, frame = cam.read()
            if not ok:
                logger.error("Camera read failed")
                break
            
            for _ in range(5):
                cam.grab()

            frame = cv2.resize(frame, (640, 640))
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
                continue
            
            if prev_active is None or prev_active is False:
                logger.info(f"[INFO {now.time()}] ON-HOURS: resume YOLO")
            if cam.should_infer():
                yolo_results = infer(model, frame)
                person_results = parse_results(yolo_results , margin=MARGIN)
                last_results = person_results
            else:
                person_results = last_results if last_results else []
            if person_results:
                path = tracker.update(person_results, frame, time.time())
                status = draw_person_status(frame, person_results)
                if status["has_alert"] and time.time() - tracker.last_alert_phone_time > tracker.alert_cooldown_phone:
                    logger.info("Phone detected")
                    tracker.last_alert_phone_time = time.time()
                    total_alerts += status["alerts"]
                    if path:
                        notify_violation(path)
                if status["has_normal"] and time.time() - tracker.last_alert_normal_time > tracker.alert_cooldown_normal:
                    logger.info("Normal detected")
                    tracker.last_alert_normal_time = time.time()
                    total_normals += status["normals"]


            # cv2.imshow("Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            prev_active = True
            cam.frame_idx += 1
            
    finally:
        logger.info("Releasing camera")
        logger.info(f"total_normals: {total_normals}")
        logger.info(f"total_alerts: {total_alerts}")
        send_text(
                    f"วันนี้ตรวจจับได้ทั้งหมด {total_alerts + total_normals} ครั้ง\n"
                    f"- มีคนใช้โทรศัพท์ {total_alerts} ครั้ง ({(total_alerts / (total_alerts + total_normals)) * 100 if (total_alerts + total_normals) > 0 else 0:.1f}%)\n"
                    f"- มีคนไม่ใช้โทรศัพท์ {total_normals} ครั้ง ({(total_normals / (total_alerts + total_normals)) * 100 if (total_alerts + total_normals) > 0 else 0:.1f}%)")
        cam.release()
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
