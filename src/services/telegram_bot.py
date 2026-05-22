import threading
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_alert(image_path: str, caption: str):
    """
    Sends an alert with a photo and caption to Telegram.
    This runs asynchronously in a daemon thread so it doesn't block main execution.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[WARNING] Telegram credentials not configured. Skipping notification.")
        return

    def _send_thread():
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        try:
            print(f"[TELEGRAM] Sending alert photo to chat {TELEGRAM_CHAT_ID}...")
            with open(image_path, "rb") as photo_file:
                files = {"photo": photo_file}
                data = {
                    "chat_id": TELEGRAM_CHAT_ID,
                    "caption": caption,
                    "parse_mode": "HTML"
                }
                
                response = requests.post(url, files=files, data=data, timeout=10)
                if response.status_code == 200:
                    print("[TELEGRAM] Alert sent successfully!")
                else:
                    print(f"[ERROR] Failed to send Telegram alert: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"[ERROR] Exception during Telegram alert: {e}")

    threading.Thread(target=_send_thread, daemon=True).start()

if __name__ == "__main__":
    import time
    print("Testing refactored Telegram alert sender...")
    test_file = "test_tg.jpg"
    with open(test_file, "wb") as f:
        f.write(b"test data")
        
    try:
        send_telegram_alert(test_file, "<b>Test Alert</b>\nThis is a test notification from refactored StepGuard.")
        time.sleep(2)
    finally:
        import os
        if os.path.exists(test_file):
            os.remove(test_file)
