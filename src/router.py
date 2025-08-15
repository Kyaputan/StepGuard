# notifier.py
import os, time, threading, requests, logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

COOLDOWN_SEC = float(os.getenv("COOLDOWN_SEC", "30"))
last_sent = 0.0  # เก็บสถานะไว้ในโมดูลนี้เท่านั้น

def _get_env():
    token = os.getenv("TELEGRAM_TOKEN") or os.getenv("TOKEN")
    chat_id = os.getenv("CHAT_ID")
    return token, chat_id

def send_photo_now(image_path: str, caption: str = "ภาพที่บันทึกจากระบบตรวจจับ 📷"):
    token, chat_id = _get_env()
    if not token or not chat_id:
        logging.error("[Notifier] TOKEN/CHAT_ID ว่าง (ตรวจ .env)")
        return

    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    try:
        with open(image_path, "rb") as f:
            resp = requests.post(
                url,
                data={"chat_id": chat_id, "caption": caption},
                files={"photo": f},
                timeout=15
            )
        if resp.status_code != 200:
            logging.error("[Notifier] ส่งไม่สำเร็จ %s: %s", resp.status_code, resp.text)
        else:
            logging.info("[Notifier] ส่งรูปเรียบร้อย: %s", image_path)
    except Exception as e:
        logging.exception("[Notifier] exception ขณะส่งรูป: %s", e)

def notify_violation(image_path: str, caption: str = "🔥 ตรวจจับคนแอบเล่นมือถือบนบันไดค่ะ! 🚫📱 "):
    global last_sent
    now = time.time()
    if now - last_sent < COOLDOWN_SEC:
        logging.info("[Notifier] อยู่ในคูลดาวน์ ข้ามการส่ง")
        return
    last_sent = now
    threading.Thread(target=send_photo_now, args=(image_path, caption), daemon=True).start()


if __name__ == "__main__":
    send_photo_now("./snapshots/20250815-161400.jpg", "test")