import os, time, threading, requests, logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

COOLDOWN_SEC = float(os.getenv("COOLDOWN_SEC", "15"))
last_sent = 0.0  

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

def send_text(text: str):
    token, chat_id = _get_env()
    if not token or not chat_id:
        logging.error("[Notifier] TOKEN/CHAT_ID ว่าง (ตรวจ .env)")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        resp = requests.post(
            url,
            data={"chat_id": chat_id, "text": text})
        if resp.status_code != 200:
            logging.error("[Notifier] ส่งไม่สำเร็จ %s: %s", resp.status_code, resp.text)
        else:
            logging.info("[Notifier] ส่งข้อความเรียบร้อย")
    except Exception as e:
        logging.exception("[Notifier] exception ขณะส่งข้อความ: ",e)
        

def notify_violation(image_path: str, caption: str = "🔥 ตรวจจับคนแอบเล่นมือถือบนบันไดค่ะ! 🚫📱 "):
    global last_sent
    now = time.time()
    if now - last_sent < COOLDOWN_SEC:
        logging.info("[Notifier] อยู่ในคูลดาวน์ ข้ามการส่ง")
        return
    last_sent = now
    threading.Thread(target=send_photo_now, args=(image_path, caption), daemon=True).start()


if __name__ == "__main__":
    print("[INFO] Router")
    # send_photo_now("./snapshots/20250815-161400.jpg", "test")
    # send_text("test")
    total_alerts = 10
    total_normals = 20
    send_text(
    f"วันนี้ตรวจจับได้ทั้งหมด {total_alerts + total_normals} คน\n"
    f"- มีคนใช้โทรศัพท์ {total_alerts} คน ({(total_alerts / (total_alerts + total_normals)) * 100 if (total_alerts + total_normals) > 0 else 0:.1f}%)\n"
    f"- มีคนไม่ใช้โทรศัพท์ {total_normals} คน ({(total_normals / (total_alerts + total_normals)) * 100 if (total_alerts + total_normals) > 0 else 0:.1f}%)"
)