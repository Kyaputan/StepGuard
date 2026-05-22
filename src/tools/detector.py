import cv2
import threading
import time
from datetime import datetime
from pathlib import Path
from ultralytics import YOLO

from config import (
    YOLO_MODEL_PATH,
    SNAPSHOT_DIR,
    MIDDLE_ZONE_TOP,
    MIDDLE_ZONE_BOTTOM
)
from db.database import add_violation
from agent.llm_analyzer import ImageAnalyzer
from services.sound_player import play_alert_sound
from services.telegram_bot import send_telegram_alert
from utils.resizeimg import resizeimg
from utils.blurface import blur_face

class StaircaseDetector:
    def __init__(self):
        print("[INFO] Initializing YOLO Staircase Detector...")
        try:
            self.model = YOLO(YOLO_MODEL_PATH)
            print(f"[INFO] YOLO Model loaded successfully: {YOLO_MODEL_PATH}")
        except Exception as e:
            print(f"[ERROR] Failed to load YOLO Model: {e}. Downloading default yolo26s.pt...")
            self.model = YOLO("yolo26s.pt")
            
        self.analyzer = ImageAnalyzer()
        
        # Tracking states
        self.processed_tracks = set()  # Set of track_ids that have been sent for analysis
        self.active_alerts = {}        # Dict of current active alerts to show in GUI: {track_id: {info}}
        self.alerts_lock = threading.Lock()
        
    def process_frame(self, frame):
        """
        Runs YOLO tracking on the frame.
        Draws bounding boxes and checks middle zone.
        """
        h, w, _ = frame.shape
        top_bound = int(h * MIDDLE_ZONE_TOP)
        bottom_bound = int(h * MIDDLE_ZONE_BOTTOM)
        
        results = self.model.track(frame, persist=True, verbose=False, conf=0.25)
        
        annotated_frame = frame.copy()
        
        # Draw translucent Middle Zone (Horizontal band)
        overlay = annotated_frame.copy()
        cv2.rectangle(overlay, (0, top_bound), (w, bottom_bound), (180, 105, 255), -1)
        cv2.addWeighted(overlay, 0.15, annotated_frame, 0.85, 0, annotated_frame)
        
        # Draw horizontal bounds lines
        cv2.line(annotated_frame, (0, top_bound), (w, top_bound), (180, 105, 255), 2, cv2.LINE_AA)
        cv2.line(annotated_frame, (0, bottom_bound), (w, bottom_bound), (180, 105, 255), 2, cv2.LINE_AA)
        
        # Draw futuristic dashed middle line (----------)
        mid_y = h // 2
        for x in range(0, w, 20):
            cv2.line(annotated_frame, (x, mid_y), (x + 10, mid_y), (180, 105, 255), 2, cv2.LINE_AA)
            
        # Draw middle zone label
        cv2.putText(
            annotated_frame, "DETECTION ZONE", (15, top_bound - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 105, 255), 1, cv2.LINE_AA
        )
        
        # Check detected boxes
        if results and results[0].boxes is not None:
            boxes = results[0].boxes
            for box in boxes:
                cls = int(box.cls[0].item())
                if cls != 0:
                    continue
                
                if box.id is not None:
                    track_id = int(box.id[0].item())
                else:
                    track_id = None
                
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)
                
                # Draw person bbox and ID
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                label = f"Person ID: {track_id}" if track_id is not None else "Person"
                cv2.putText(
                    annotated_frame, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA
                )
                cv2.circle(annotated_frame, (cx, cy), 5, (0, 255, 0), -1)
                
                # Middle Zone Check (แกน Y)
                if track_id is not None and top_bound <= cy <= bottom_bound:
                    if track_id not in self.processed_tracks:
                        self.processed_tracks.add(track_id)
                        self._trigger_background_analysis(frame, track_id, (x1, y1, x2, y2))
                        
        # Clean up expired alerts from GUI (keep them for 5 seconds)
        current_time = time.time()
        with self.alerts_lock:
            expired = [tid for tid, alert in self.active_alerts.items() if current_time - alert["timestamp"] > 5.0]
            for tid in expired:
                del self.active_alerts[tid]
                
        return annotated_frame

    def _trigger_background_analysis(self, frame, track_id, bbox):
        """Helper to crop image and spawn background analyzer thread."""
        x1, y1, x2, y2 = bbox
        h, w, _ = frame.shape
        
        x1_pad = max(0, x1 - 15)
        y1_pad = max(0, y1 - 15)
        x2_pad = min(w, x2 + 15)
        y2_pad = min(h, y2 + 15)
        
        cropped = frame[y1_pad:y2_pad, x1_pad:x2_pad]
        if cropped.size == 0:
            return
            
        # Resize cropped image to 640x640 using user's utility
        resized = resizeimg(cropped, new_shape=(640, 640), color=(26, 26, 26))
            
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"violator_{track_id}_{timestamp_str}.jpg"
        save_path = str(Path(SNAPSHOT_DIR) / filename)
        
        cv2.imwrite(save_path, resized)
        print(f"[DETECTOR] Bounding box cropped, resized to 640x640 and saved for ID {track_id} -> {save_path}")
        
        thread = threading.Thread(
            target=self._analyze_violation_thread,
            args=(save_path, track_id),
            daemon=True
        )
        thread.start()

    def _analyze_violation_thread(self, image_path, track_id):
        """Background thread executing Gemini analysis and alarms."""
        print(f"[ANALYSIS] Starting analysis for track_id {track_id}...")
        result = self.analyzer.analyze_cropped_image(image_path)
        
        print(f"[ANALYSIS] Results for ID {track_id}: Phone={result.is_using_phone}, Gender={result.gender}, Dir={result.direction}, Conf={result.confidence:.2f}")
        
        # Apply face blurring to the saved image to preserve privacy after LLM analysis
        try:
            img = cv2.imread(image_path)
            if img is not None:
                blurred_img = blur_face(img)
                cv2.imwrite(image_path, blurred_img)
                print(f"[PRIVACY] Face blurred successfully in: {image_path}")
            else:
                print(f"[WARNING] Could not read image for face blurring at: {image_path}")
        except Exception as e:
            print(f"[ERROR] Failed to apply face blurring: {e}")

        
        if result.is_using_phone:
            play_alert_sound()
            
            with self.alerts_lock:
                self.active_alerts[track_id] = {
                    "timestamp": time.time(),
                    "gender": result.gender,
                    "direction": result.direction,
                    "explanation": result.explanation,
                    "confidence": result.confidence
                }
            
            db_id = add_violation(
                image_path=image_path,
                gender=result.gender,
                direction=result.direction,
                explanation=result.explanation,
                confidence=result.confidence,
                is_phone_detected=True
            )
            print(f"[DATABASE] Violation logged successfully with DB ID: {db_id}")
            
            caption = (
                f"🚨 <b>StepGuard Alert! Stairway Violation</b> 🚨\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"📱 <b>Phone usage confirmed</b> while walking on stairs!\n\n"
                f"👤 <b>Gender:</b> {result.gender.upper()}\n"
                f"🥾 <b>Direction:</b> {result.direction.upper()}\n"
                f"📈 <b>Confidence:</b> {result.confidence * 100:.1f}%\n"
                f"🕒 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"📝 <b>AI Reasoning:</b> {result.explanation}"
            )
            send_telegram_alert(image_path, caption)
        else:
            add_violation(
                image_path=image_path,
                gender=result.gender,
                direction=result.direction,
                explanation=result.explanation,
                confidence=result.confidence,
                is_phone_detected=False
            )
            print(f"[DATABASE] Logged non-violation event for ID {track_id}")
