import cv2
import sys
import time
from datetime import datetime
from config import CAMERA_SOURCE, print_config
from db.database import init_db
from tools.detector import StaircaseDetector
from utils.resizeimg import resizeimg

def draw_futuristic_dashboard(frame, detector):
    """
    Draws a highly aesthetic, premium HUD / dashboard overlay on the frame
    to showcase a professional and state-of-the-art AI solution.
    """
    h, w, _ = frame.shape
    
    hud_height = 50
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, hud_height), (20, 10, 30), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    
    cv2.putText(
        frame, "★ STEPGUARD SYSTEM ACTIVE", (15, hud_height - 18),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA
    )
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(
        frame, timestamp, (w - 200, hud_height - 18),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA
    )
    
    with detector.alerts_lock:
        if detector.active_alerts:
            recent_id = list(detector.active_alerts.keys())[-1]
            alert = detector.active_alerts[recent_id]
            
            banner_w = min(460, w - 40)
            banner_h = 100
            bx1 = int((w - banner_w) / 2)
            bx2 = bx1 + banner_w
            by1 = hud_height + 15
            by2 = by1 + banner_h
            
            card_overlay = frame.copy()
            cv2.rectangle(card_overlay, (bx1, by1), (bx2, by2), (30, 20, 60), -1)
            cv2.rectangle(card_overlay, (bx1, by1), (bx2, by2), (0, 0, 255), 2)
            cv2.addWeighted(card_overlay, 0.85, frame, 0.15, 0, frame)
            
            cv2.putText(
                frame, "⚠️ VIOLATION: PHONE DETECTED ON STAIRS", (bx1 + 15, by1 + 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2, cv2.LINE_AA
            )
            
            details_line1 = f"ID: {recent_id} | Gender: {alert['gender'].upper()} | Dir: {alert['direction'].upper()}"
            cv2.putText(
                frame, details_line1, (bx1 + 15, by1 + 52),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA
            )
            
            explanation_snipped = alert['explanation']
            if len(explanation_snipped) > 55:
                explanation_snipped = explanation_snipped[:52] + "..."
            cv2.putText(
                frame, f"AI: {explanation_snipped}", (bx1 + 15, by1 + 78),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1, cv2.LINE_AA
            )
            
def main():
    print_config()
    
    print("[INIT] Initializing DB schema...")
    init_db()
    
    print(f"[CAMERA] Attempting to open video source: {CAMERA_SOURCE}...")

    cap = cv2.VideoCapture(CAMERA_SOURCE)
    
    if not cap.isOpened():
        print(f"[ERROR] Could not open video source {CAMERA_SOURCE}.")
        print("Please check your .env camera source or ensure webcam is connected.")
        sys.exit(1)
        
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"[CAMERA] Successfully opened! Resolution: {width}x{height} @ {fps or 'Unknown'} FPS")
    
    detector = StaircaseDetector()
    
    window_name = "StepGuard AI Staircase Phone Usage Monitor"
    # cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    # cv2.resizeWindow(window_name, 960, 540)
    
    print("\n" + "=" * 50)
    print("      StepGuard Monitoring Active")
    print("      Press 'q' inside OpenCV window to quit")
    print("=" * 50 + "\n")
    
    frame_count = 0
    start_time = time.time()
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                if isinstance(CAMERA_SOURCE, str) and CAMERA_SOURCE != "0":
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    print("[CAMERA] Stream ended or frame could not be read.")
                    break
            
            frame_count += 1
            
            processed_frame = detector.process_frame(frame)
            draw_futuristic_dashboard(processed_frame, detector)
            
            elapsed = time.time() - start_time
            if elapsed > 0:
                current_fps = frame_count / elapsed
                cv2.putText(
                    processed_frame, f"FPS: {current_fps:.1f}", (processed_frame.shape[1] - 80, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1, cv2.LINE_AA
                )
            processed_frame = resizeimg(processed_frame, new_shape=(640, 640))
            cv2.imshow(window_name, processed_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("[SYSTEM] Exit requested by user.")
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("[SYSTEM] Resources released. StepGuard terminated cleanly. สวัสดีค่ะ! 🌸")

if __name__ == "__main__":
    main()
