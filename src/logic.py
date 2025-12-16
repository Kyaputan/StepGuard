import cv2
from config import  ALERT_CLASSES, SNAPSHOT_DIR, PHONE_HOLD_SECONDS , CROP_FRAME, GPIO_PIN
import os
import time
from typing import List, Dict, Tuple

# Try to import GPIO for LED control
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("[WARN] RPi.GPIO not available - LED control disabled")

def draw_person_status(frame, results):
    alerts = 0
    normals = 0
    has_alert = False
    has_normal = False

    color_map = {
        "Normal": (0, 255, 0),
        "Phone":  (0, 0, 255)
    }

    for i, r in enumerate(results):
        x1, y1, x2, y2 = r["bbox"]
        cls_name = r["class"]

        # เบลอส่วนบน 20% ของกรอบ xyxy
        box_h = y2 - y1
        blur_h = int(box_h * 0.3)
        if blur_h > 0:
            frame[y1:y1+blur_h, x1:x2] = cv2.GaussianBlur(frame[y1:y1 + blur_h, x1:x2], (15, 15), 0)

        color = color_map.get(cls_name, (255, 255, 255))
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f"Person {i+1}: {cls_name}",
                    (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        if cls_name.lower() == "phone":
            alerts += 1
            has_alert = True
        else:
            normals += 1
            has_normal = True

    # ✅ แสดงผลรวมบนภาพ
    cv2.putText(frame, f"Alert: {alerts}",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 0, 255) if alerts > 0 else (0, 255, 0), 2)
    cv2.putText(frame, f"Normal: {normals}",
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 255, 0), 2)

    # ✅ ส่งออกเป็น dict
    return {
        "alerts": alerts,
        "normals": normals,
        "has_alert": has_alert,
        "has_normal": has_normal
    }


def _iou(a: Tuple[int,int,int,int], b: Tuple[int,int,int,int]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    
    iw = max(0, inter_x2 - inter_x1)
    ih = max(0, inter_y2 - inter_y1)
    inter = iw * ih
    
    if inter == 0: 
        return 0.0
    a_area = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    b_area = max(0, bx2 - bx1) * max(0, by2 - by1)
    union = a_area + b_area - inter
    return inter / union if union > 0 else 0.0

class PhoneHoldTracker:
    def __init__(self, hold_seconds: float = PHONE_HOLD_SECONDS,iou_thresh: float = 0.5, lost_tolerance: float = 1.0, alert_cooldown: float = 10.0):
        self.hold_seconds = hold_seconds
        self.iou_thresh = iou_thresh
        self.lost_tolerance = lost_tolerance
        self.tracks = []
        self.last_alert_phone_time = 0.0
        self.last_alert_normal_time = 0.0
        self.alert_cooldown_phone = alert_cooldown
        self.alert_cooldown_normal = alert_cooldown
        self._alert_set = {c.lower() for c in ALERT_CLASSES}
        os.makedirs(SNAPSHOT_DIR, exist_ok=True)

        # Initialize GPIO for LED
        if GPIO_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(GPIO_PIN, GPIO.OUT)
            GPIO.output(GPIO_PIN, GPIO.LOW)  # Start with LED off
            print(f"[INFO] LED initialized on GPIO pin {GPIO_PIN}")
        else:
            print("[WARN] LED control not available")

    def update(self, detections: List[Dict], frame, now: float):
        phone_dets = [d for d in detections if d["class"].lower() in self._alert_set]

        assigned = set()
        for t in self.tracks:
            best_iou, best_j = 0.0, -1
            for j, det in enumerate(phone_dets):
                if j in assigned: 
                    continue
                iou = _iou(t["bbox"], det["bbox"])
                if iou > best_iou:
                    best_iou, best_j = iou, j
            if best_j >= 0 and best_iou >= self.iou_thresh:
                t["bbox"] = phone_dets[best_j]["bbox"]
                t["last"] = now
                assigned.add(best_j)

        for j, det in enumerate(phone_dets):
            if j in assigned: 
                continue
            self.tracks.append({
                "bbox": det["bbox"],
                "start": now,
                "last": now,
                "triggered": False
            })

        h, w = frame.shape[:2]
        for t in self.tracks:
            if not t["triggered"] and (now - t["start"]) >= self.hold_seconds:
                x1, y1, x2, y2 = t["bbox"]
                
                margin_x = int((x2 - x1) * CROP_FRAME[0]) 
                margin_y = int((y2 - y1) * CROP_FRAME[1]) 
                x1 -= margin_x
                y1 -= margin_y
                x2 += margin_x
                y2 += margin_y

                x1 = max(0, min(x1, w-1))
                x2 = max(0, min(x2, w-1))
                y1 = max(0, min(y1, h-1))
                y2 = max(0, min(y2, h-1))

                if x2 > x1 and y2 > y1:
                    x1, y1, x2, y2 = map(int, (x1, y1, x2, y2))
                    crop = frame[y1:y2, x1:x2]
                    crop_h, crop_w = crop.shape[:2]
                    blur_h = int(crop_h * 0.38)
                    
                    if blur_h > 0:
                        crop[:blur_h, :] = cv2.GaussianBlur(crop[:blur_h, :], (25, 25), 0)
                    crop = cv2.rectangle(crop, (x1, y1), (x2, y2), (255,255,255), 2)
                    ts = time.strftime("%Y%m%d-%H%M%S")
                    filename = f"{ts}.jpg"
                    path = os.path.join(SNAPSHOT_DIR, filename)
                    ok = cv2.imwrite(path, crop)
                    if not ok:
                        print(f"[Tracker] บันทึกรูปไม่สำเร็จ: {path}")
                    else:
                        return path
                    t["triggered"] = True

        self.tracks = [t for t in self.tracks if (now - t["last"]) <= self.lost_tolerance]

    def cleanup(self):
        """Cleanup GPIO resources"""
        if GPIO_AVAILABLE:
            GPIO.output(GPIO_PIN, GPIO.LOW)  # Turn off LED
            GPIO.cleanup()
            print("[INFO] GPIO cleanup completed")