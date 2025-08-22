import cv2
import os, time
from detection import load_model, infer , parse_results , debug_detection
from logic import draw_person_status, PhoneHoldTracker
from camera import VideoSource
from config import SNAPSHOT_DIR , VIDEO_PATH , VIDEO_NAME , INFER , TZ , MARGIN , RTSP , BACKEND, debug_config
from util import is_active_hour , start_scheduler , next_midnight_bkk
from datetime import datetime

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
    except Exception as e:
        print(f"[ERROR] {e}")
        return
    
    try:
        while True:
            now = datetime.now(TZ)
            if now >= next_clear:
                next_clear = next_midnight_bkk(now)

            ok, frame = cam.read()
            if not ok:
                print("Camera read failed")
                break
            frame = cv2.resize(frame, (640, 640))
            active = is_active_hour(now)
            
            if not active:
                if prev_active is None or prev_active is True:
                    print(f"[INFO {now.time()}] OFF-HOURS: pause YOLO now")
                    last_results = []
                cv2.imshow("Detection", frame)
                time.sleep(3)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                prev_active = False
                cam.frame_idx += 1
                continue
            
            if prev_active is None or prev_active is False:
                print(f"[INFO {now.time()}] ON-HOURS: resume YOLO")
            if cam.should_infer():
                yolo_results = infer(model, frame)
                person_results = parse_results(yolo_results , margin=MARGIN)
                last_results = person_results
            else:
                person_results = last_results if last_results else []
            if person_results:
                tracker.update(person_results, frame, time.time())
                has_phone = draw_person_status(frame, person_results)
                if has_phone and time.time() - tracker.last_alert_time > tracker.alert_cooldown:
                    print("Phone detected")
                    tracker.last_alert_time = time.time()
            
            cv2.imshow("Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            prev_active = True
            cam.frame_idx += 1
            
    finally:
        cam.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    debug_detection()
    debug_config()
    time.sleep(5)
    print("[INFO] Starting main...")
    time.sleep(3)
    os.system('cls' if os.name == 'nt' else 'clear')
    main()
