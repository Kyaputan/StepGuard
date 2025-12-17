import cv2
import os
import time
from detection import load_model, infer , parse_results , debug_detection
from logic import draw_person_status, PhoneHoldTracker
from camera import VideoSource
from config import SNAPSHOT_DIR , VIDEO_PATH , VIDEO_NAME , INFER , TZ , MARGIN , RTSP , BACKEND, debug_config, GPIO_PIN
from util import is_active_hour , start_scheduler , next_midnight_bkk
from datetime import datetime
from router import send_text
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
from router import notify_violation
from sound_manager import Alert
import tkinter as tk
from PIL import Image, ImageTk
from collections import deque
import numpy as np

try:
    import RPi.GPIO as GPIO
    import threading
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("[WARN] RPi.GPIO not available - LED control disabled")

class Dashboard:
    def __init__(self, delay_seconds=3):
        self.root = tk.Tk()
        self.root.title("StepGuard Detection Dashboard")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # กำหนดสีธีม - โทนสีขาวนวลมินิมอล
        self.bg_color = '#F8F9FA'  # สีขาวนวล
        self.panel_bg = '#FFFFFF'  # สีขาวบริสุทธิ์
        self.text_color = '#2C3E50'  # สีเทาเข้มอ่อน
        self.accent_color = '#3498DB'  # สีน้ำเงินอ่อนสำหรับ accent
        self.border_color = '#E0E0E0'  # สีเทาอ่อนสำหรับเส้นขอบ
        
        # ตั้งพื้นหลังหน้าต่างหลัก
        self.root.configure(bg=self.bg_color)
        
        # เก็บ frame ที่ผ่านมาตามจำนวนวินาที (ประมาณ 1 frame ต่อ loop)
        self.delay_frames = delay_seconds
        self.frame_buffer = deque(maxlen=self.delay_frames)
        
        # สร้าง Frame หลักแบ่ง 2 ส่วน
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # ส่วนซ้าย: ภาพ delay 3 วินาที (ขนาดเล็กกว่า)
        left_frame = tk.Frame(main_frame, bg=self.panel_bg, relief=tk.FLAT, bd=1)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 4))
        
        # จำกัดขนาดของ left_frame
        left_frame.configure(width=400)
        left_frame.pack_propagate(False)
        
        # Header สำหรับส่วนซ้าย
        left_header = tk.Frame(left_frame, bg=self.panel_bg)
        left_header.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        left_label = tk.Label(left_header, text="🎥 Live Detection",
                             fg=self.text_color, bg=self.panel_bg,
                             font=('Segoe UI', 16, 'bold'))
        left_label.pack(anchor='w')
        
        # Divider line
        left_divider = tk.Frame(left_frame, bg=self.border_color, height=1)
        left_divider.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        # Panel สำหรับแสดงภาพ
        panel_container_left = tk.Frame(left_frame, bg=self.panel_bg)
        panel_container_left.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.left_panel = tk.Label(panel_container_left, bg='#FAFAFA',
                                   relief=tk.FLAT, bd=0)
        self.left_panel.pack(fill=tk.BOTH, expand=True)
        
        # ส่วนขวา: ภาพ crop คนใช้โทรศัพท์ (ขนาดใหญ่กว่า - เด่นกว่า)
        right_frame = tk.Frame(main_frame, bg=self.panel_bg, relief=tk.FLAT, bd=1)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(4, 8))
        
        # ขนาดของ right_frame จะใหญ่กว่าเพราะใช้ expand=True แบบเต็ม
        
        # Header สำหรับส่วนขวา
        right_header = tk.Frame(right_frame, bg=self.panel_bg)
        right_header.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        right_label = tk.Label(right_header, text="📱 Phone User Detection",
                              fg='#E74C3C', bg=self.panel_bg,
                              font=('Segoe UI', 18, 'bold'))
        right_label.pack(anchor='w')
        
        # Divider line
        right_divider = tk.Frame(right_frame, bg=self.border_color, height=1)
        right_divider.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        # Panel สำหรับแสดงภาพ
        panel_container_right = tk.Frame(right_frame, bg=self.panel_bg)
        panel_container_right.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.right_panel = tk.Label(panel_container_right, bg='#FAFAFA',
                                    relief=tk.FLAT, bd=0)
        self.right_panel.pack(fill=tk.BOTH, expand=True)
        
        self.is_running = True
        self.cropped_image = None
        
    def update_frames(self, current_frame, cropped_frame=None):
        """อัปเดตภาพทั้งสองส่วน"""
        if not self.is_running:
            return
            
        # เพิ่ม frame ปัจจุบันเข้า buffer
        self.frame_buffer.append(current_frame.copy())
        
        # แสดงภาพด้านซ้าย (delay)
        # ใช้ภาพเก่าที่สุดใน buffer (FIFO)
        delayed_frame = self.frame_buffer[0] if len(self.frame_buffer) > 0 else current_frame
            
        self._display_image(delayed_frame, self.left_panel)
        
        # แสดงภาพด้านขวา (cropped) - ใช้ขนาดคงที่เพื่อไม่ให้กระโดด
        if cropped_frame is not None:
            self.cropped_image = cropped_frame
            self._display_image_fixed(cropped_frame, self.right_panel)
        elif self.cropped_image is not None:
            # แสดงภาพ cropped ล่าสุด
            self._display_image_fixed(self.cropped_image, self.right_panel)
        else:
            # ถ้ายังไม่มีภาพ cropped ให้แสดงข้อความ
            self._show_placeholder(self.right_panel, "No phone user detected")
    
    def _display_image(self, frame, panel):
        """แสดงภาพใน panel"""
        try:
            # แปลง BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # ปรับขนาดให้พอดีกับ panel (รักษาอัตราส่วน)
            panel_width = panel.winfo_width() if panel.winfo_width() > 1 else 640
            panel_height = panel.winfo_height() if panel.winfo_height() > 1 else 640
            
            h, w = frame_rgb.shape[:2]
            scale = min(panel_width / w, panel_height / h)
            new_w, new_h = int(w * scale), int(h * scale)
            
            if new_w > 0 and new_h > 0:
                resized = cv2.resize(frame_rgb, (new_w, new_h))
                
                # แปลงเป็น ImageTk
                img = Image.fromarray(resized)
                imgtk = ImageTk.PhotoImage(image=img)
                
                panel.imgtk = imgtk
                panel.configure(image=imgtk)
        except Exception as e:
            logger.error(f"Error displaying image: {e}")
    
    def _display_image_fixed(self, frame, panel, target_size=(640, 640)):
        """แสดงภาพใน panel ด้วยขนาดคงที่ (letterbox) - ป้องกันการกระโดดของเฟรม"""
        try:
            # แปลง BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # กำหนดขนาดเป้าหมาย
            target_w, target_h = target_size
            
            # คำนวณ scale เพื่อรักษาอัตราส่วน
            h, w = frame_rgb.shape[:2]
            scale = min(target_w / w, target_h / h)
            new_w, new_h = int(w * scale), int(h * scale)
            
            if new_w > 0 and new_h > 0:
                # Resize ภาพ
                resized = cv2.resize(frame_rgb, (new_w, new_h))
                
                # สร้าง canvas ขนาดคงที่พื้นหลังสีเทาอ่อน
                canvas = np.full((target_h, target_w, 3), 250, dtype=np.uint8)
                
                # คำนวณตำแหน่งกึ่งกลาง
                x_offset = (target_w - new_w) // 2
                y_offset = (target_h - new_h) // 2
                
                # วางภาพลงใน canvas
                canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
                
                # แปลงเป็น ImageTk
                img = Image.fromarray(canvas)
                imgtk = ImageTk.PhotoImage(image=img)
                
                panel.imgtk = imgtk
                panel.configure(image=imgtk)
        except Exception as e:
            logger.error(f"Error displaying fixed image: {e}")
    
    def _show_placeholder(self, panel, text):
        placeholder = np.full((400, 400, 3), 250, dtype=np.uint8)

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        color = (100, 100, 100)  # สีเทา

        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        text_x = (400 - text_size[0]) // 2
        text_y = (400 + text_size[1]) // 2
        
        cv2.putText(placeholder, text, (text_x, text_y),
                   font, font_scale, color, thickness, cv2.LINE_AA)
        self._display_image(placeholder, panel)
    
    def on_closing(self):
        """จัดการเมื่อปิดหน้าต่าง"""
        self.is_running = False
        self.root.quit()
        
    def update(self):
        """อัปเดต GUI"""
        if self.is_running:
            self.root.update_idletasks()
            self.root.update()

def main():
    try:
        start_scheduler(test_once=False)
        model = load_model()
        os.makedirs(VIDEO_PATH, exist_ok=True)
        os.makedirs(SNAPSHOT_DIR, exist_ok=True)
        # cam = VideoSource(RTSP,BACKEND , every_n=INFER)
        cam = VideoSource(VIDEO_PATH + VIDEO_NAME, every_n=INFER)
        tracker = PhoneHoldTracker()
        next_clear = next_midnight_bkk()
        last_results = []
        prev_active = None
        total_alerts = 0
        total_normals = 0
        
        # สร้าง Dashboard (delay 3 วินาที)
        dashboard = Dashboard(delay_seconds=3)
        
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
                continue
            
            for _ in range(5):
                cam.grab()

            frame = cv2.resize(frame, (640, 640))
            active = is_active_hour(now)

            if not active:
                if prev_active is None or prev_active is True:
                    logger.info(f"[INFO {now.time()}] OFF-HOURS: pause YOLO now")
                    send_text("หมดเวลาทำการ")
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
                send_text("เริ่มเวลาทำการ ระบบจะเริ่มทำการตรวจจับ")
            if cam.should_infer():
                yolo_results = infer(model, frame)
                person_results = parse_results(yolo_results , margin=MARGIN)
                last_results = person_results
            else:
                person_results = last_results if last_results else []
            cropped_phone_user = None
            if person_results:
                path = tracker.update(person_results, frame, time.time())
                status = draw_person_status(frame, person_results)
                
                # หาคนที่ใช้โทรศัพท์และ crop ภาพ
                for person in person_results:
                    if person.get("class") == "Phone":
                        # Crop ภาพคนที่ใช้โทรศัพท์
                        x1, y1, x2, y2 = person["bbox"]
                        cropped_phone_user = frame[y1:y2, x1:x2].copy()
                        break  # เอาคนแรกที่เจอ
                
                if status["has_alert"] and time.time() - tracker.last_alert_phone_time > tracker.alert_cooldown_phone:
                    logger.info("Phone detected")
                    tracker.last_alert_phone_time = time.time()
                    total_alerts += status["alerts"]
                    Alert()
                    if path:
                        notify_violation(path)
                        # !---------------------------------------------------------
                    if GPIO_AVAILABLE:
                        GPIO.output(GPIO_PIN, GPIO.HIGH)
                        def turn_off_led():
                            time.sleep(5)
                            GPIO.output(GPIO_PIN, GPIO.LOW)
                        threading.Thread(target=turn_off_led, daemon=True).start()
                        # !---------------------------------------------------------
                if status["has_normal"] and time.time() - tracker.last_alert_normal_time > tracker.alert_cooldown_normal:
                    logger.info("Normal detected")
                    tracker.last_alert_normal_time = time.time()
                    total_normals += status["normals"]

            # อัปเดต Dashboard แทน cv2.imshow
            dashboard.update_frames(frame, cropped_phone_user)
            dashboard.update()
            
            if not dashboard.is_running:
                logger.info("[INFO] Exit")
                break
            prev_active = True
            cam.frame_idx += 1
            
    finally:
        logger.info("Releasing camera")
        logger.info(f"total_normals: {total_normals}")
        logger.info(f"total_alerts: {total_alerts}")
        send_text(
                    f"ระบบถูกขัดจังหวะการทำงาน \n"
                    f"ก่อนหยุดการทำงานทำการตรวจจับได้ทั้งหมด {total_alerts + total_normals} ครั้ง\n"
                    f"- มีคนใช้โทรศัพท์ {total_alerts} ครั้ง ({(total_alerts / (total_alerts + total_normals)) * 100 if (total_alerts + total_normals) > 0 else 0:.1f}%)\n"
                    f"- มีคนไม่ใช้โทรศัพท์ {total_normals} ครั้ง ({(total_normals / (total_alerts + total_normals)) * 100 if (total_alerts + total_normals) > 0 else 0:.1f}%)")
        cam.release()
        # ปิด Dashboard
        try:
            dashboard.root.destroy()
        except:
            pass
        # Cleanup GPIO
        tracker.cleanup()

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    debug_detection()
    debug_config()
    time.sleep(3)
    logger.info("Starting main...")
    time.sleep(1)
    os.system('cls' if os.name == 'nt' else 'clear')
    main()
