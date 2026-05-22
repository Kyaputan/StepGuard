import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
else:
    load_dotenv(override=True)  # Fallback to current working directory .env

# Base Directories
SRC_DIR = Path(__file__).resolve().parent
BASE_DIR = SRC_DIR.parent

# Credentials & API Keys
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN") or ""
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID") or ""
API_KEY = os.getenv("API_KEY") or ""

# YOLO Settings
YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")

# Database Path
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "stepguard.db"))

# Directories for output and resources
SNAPSHOT_DIR = Path(os.getenv("SNAPSHOT_DIR", str(BASE_DIR / "snapshots")))
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

# Sound Warning Settings
SOUND_ALERT_PATH = os.getenv("SOUND_ALERT_PATH", str(BASE_DIR / "model" / "stop.wav"))

# Camera Settings
_camera_source_raw = os.getenv("CAMERA_SOURCE") or os.getenv("RTSP") or "0"
if _camera_source_raw.isdigit():
    CAMERA_SOURCE = int(_camera_source_raw)
else:
    # Normalize slashes and resolve relative to BASE_DIR if it's a relative path
    normalized = _camera_source_raw.replace("\\", "/")
    resolved_path = BASE_DIR / normalized
    if resolved_path.exists():
        CAMERA_SOURCE = str(resolved_path)
    else:
        CAMERA_SOURCE = normalized

# Middle Detection Zone (fraction of screen height)
MIDDLE_ZONE_TOP = float(os.getenv("MIDDLE_ZONE_TOP", "0.45"))
MIDDLE_ZONE_BOTTOM = float(os.getenv("MIDDLE_ZONE_BOTTOM", "0.55"))

def print_config():
    """Helper to display active config in a clean manner"""
    print("=" * 40)
    print("       StepGuard Configuration")
    print("=" * 40)
    print(f"Telegram Bot Active: {bool(TELEGRAM_BOT_TOKEN)}")
    print(f"Telegram Chat ID:    {TELEGRAM_CHAT_ID}")
    print(f"API Key Set:         {bool(API_KEY)}")
    print(f"YOLO Model Path:     {YOLO_MODEL_PATH}")
    print(f"Database Path:       {DB_PATH}")
    print(f"Snapshot Directory:  {SNAPSHOT_DIR}")
    print(f"Sound Alert Path:    {SOUND_ALERT_PATH}")
    print(f"Camera Source:       {CAMERA_SOURCE}")
    print(f"Middle Zone Range:   {MIDDLE_ZONE_TOP} to {MIDDLE_ZONE_BOTTOM}")
    print("=" * 40)

if __name__ == "__main__":
    print_config()
