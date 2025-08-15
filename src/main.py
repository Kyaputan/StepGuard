import cv2
import time
import os

from detection import load_model, infer , parse_results
from logic import draw_person_status, PhoneHoldTracker
from camera import VideoSource, should_infer
from drawing import draw_alerts
from config import SNAPSHOT_DIR , VIDEO_PATH , VIDEO_NAME

# --- ถ้ายังไม่มี parse_results ให้ใช้ฟังก์ชันนี้ ---


def main():
    model = load_model()
    cam = VideoSource(VIDEO_PATH + VIDEO_NAME)

    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    tracker = PhoneHoldTracker()  

    infer_every_n = 5
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

            # อัปเดต tracker เพื่อตรวจจับถือโทรศัพท์เกิน 5 วิแล้วครอป
            tracker.update(person_results, frame, time.time())

            # วาด overlay
            draw_person_status(frame, person_results)

            cv2.imshow("PPE Detection (Per Person)", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            frame_idx += 1

    finally:
        cam.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
