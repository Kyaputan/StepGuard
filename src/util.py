from config import SNAPSHOT_DIR , TZ , ACTIVE_START_H , ACTIVE_START_M , ACTIVE_END_H , ACTIVE_END_M
import os
import shutil
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta    

def delete_all_snapshots():
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    deleted = 0
    for name in os.listdir(SNAPSHOT_DIR):
        p = os.path.join(SNAPSHOT_DIR, name)
        try:
            if os.path.isfile(p) or os.path.islink(p):
                os.remove(p); deleted += 1
            elif os.path.isdir(p):
                shutil.rmtree(p); deleted += 1
        except Exception as e:
            print(f"[WARN] Delete failed: {p} -> {e}")
    print(f"[INFO] {datetime.now(TZ)} Cleared snapshots ({deleted} items).")
    

def start_scheduler():
    scheduler = BackgroundScheduler(timezone=TZ)
    scheduler.add_job(delete_all_snapshots, "cron", hour=0, minute=0, id="clear_snaps_daily")
    scheduler.start()
    print("[INFO] APScheduler started (daily clear @ 00:00 Asia/Bangkok).")
    
def next_midnight_bkk(now=None):
    now = now or datetime.now(TZ)
    tomorrow = (now + timedelta(days=1)).date()
    return datetime.combine(tomorrow, datetime.min.time(), tzinfo=TZ)

def is_active_hour():
    now = datetime.now(TZ)
    return ACTIVE_START_H <= now.hour < ACTIVE_END_H

def is_active_hour(now=None) -> bool:
    """
    เปิดทำงานแบบช่วงเวลา [START, END) คือรวม START และไม่รวม END
    รองรับระดับวินาที และรองรับช่วงที่ข้ามเที่ยงคืนได้ด้วย
    """
    now = now or datetime.now(TZ)
    t = (now.hour, now.minute, now.second)
    start = (ACTIVE_START_H, ACTIVE_START_M, 0)
    end   = (ACTIVE_END_H,   ACTIVE_END_M,   0)

    if start <= end:
        return start <= t < end
    else:
        return t >= start or t < end

if __name__ == "__main__":
    print(is_active_hour())