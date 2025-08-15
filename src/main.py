import cv2
import time
import os

from detection import load_model, infer , parse_results
from logic import draw_person_status, PhoneHoldTracker
from camera import VideoSource, should_infer
from config import SNAPSHOT_DIR , VIDEO_PATH , VIDEO_NAME

def main():
    model = load_model()
    cam = VideoSource(VIDEO_PATH + VIDEO_NAME)

    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    tracker = PhoneHoldTracker()  

    infer_every_n = 10
    frame_idx = 0
    last_results = []
    
    try:
        while True:
            ok, frame = cam.read()
            if not ok:
                print("Camera read failed")
                break
            frame = cv2.resize(frame, (640, 640))
            if should_infer(frame_idx, infer_every_n):
                yolo_results = infer(model, frame)
                person_results = parse_results(yolo_results)
                last_results = person_results
            else:
                person_results = last_results

            tracker.update(person_results, frame, time.time())
            has_phone = draw_person_status(frame, person_results)
            if has_phone and time.time() - tracker.last_alert_time > tracker.alert_cooldown:
                print("Phone detected")
                tracker.last_alert_time = time.time()
            cv2.imshow("PPE Detection (Per Person)", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            frame_idx += 1

    finally:
        cam.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
