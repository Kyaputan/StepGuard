from config import SNAPSHOT_DIR ,TZ , ACTIVE_START_H , ACTIVE_START_M , ACTIVE_END_H , ACTIVE_END_M
import os , time, shutil, logging, atexit
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta    


SNAPSHOT_DIR = os.path.abspath(SNAPSHOT_DIR)

SCHED = None

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
    print(f"[INFO] {datetime.now(TZ)} Cleared snapshots ({deleted} items) @ {SNAPSHOT_DIR}")

def start_scheduler(*, test_once=False):
    global SCHED
    if SCHED and SCHED.running:
        print("[INFO] Scheduler already running.")
        return

    logging.basicConfig()
    logging.getLogger('apscheduler').setLevel(logging.INFO)

    SCHED = BackgroundScheduler(timezone=TZ)

    if not test_once:
        SCHED.add_job(delete_all_snapshots, 'cron', hour=0, minute=0, id="clear_snaps_daily", replace_existing=True, coalesce=True, misfire_grace_time=300)
        print("[INFO] APScheduler started (daily clear @ 00:00 Asia/Bangkok).")
    else:
        run_at = datetime.now(TZ) + timedelta(seconds=10)
        SCHED.add_job(delete_all_snapshots, 'date', run_date=run_at, id="clear_snaps_once", replace_existing=True)
        print(f"[INFO] APScheduler started (one-shot at {run_at})")

    SCHED.start()
    atexit.register(lambda: SCHED.shutdown(wait=False) if SCHED and SCHED.running else None)
    
def next_midnight_bkk(now=None):
    now = now or datetime.now(TZ)
    tomorrow = (now + timedelta(days=1)).date()
    return datetime.combine(tomorrow, datetime.min.time(), tzinfo=TZ)

def is_active_hour(now=None) -> bool:
    now = now or datetime.now(TZ)
    t = (now.hour, now.minute, now.second)
    start = (ACTIVE_START_H, ACTIVE_START_M, 0)
    end   = (ACTIVE_END_H,   ACTIVE_END_M,   0)

    if start <= end:
        return start <= t < end
    else:
        return t >= start or t < end

if __name__ == "__main__":
    print("[DEBUG] Now:", datetime.now(TZ))
    print("[DEBUG] SNAPSHOT_DIR:", SNAPSHOT_DIR)
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    for i in range(3):
        with open(os.path.join(SNAPSHOT_DIR, f"tmp{i}.txt"), "w", encoding="utf-8") as f:
            f.write("test")
    start_scheduler(test_once=True)
    if SCHED: SCHED.print_jobs()
    try:
        time.sleep(20)
    except KeyboardInterrupt:
        pass
