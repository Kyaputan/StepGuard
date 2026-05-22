import sqlite3
from datetime import datetime
from config import DB_PATH

def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and creates the required tables if they don't exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                image_path TEXT NOT NULL,
                gender TEXT NOT NULL,
                direction TEXT NOT NULL,
                explanation TEXT NOT NULL,
                confidence REAL NOT NULL,
                is_phone_detected INTEGER DEFAULT 1
            )
        """)
        conn.commit()
    print(f"Database initialized at: {DB_PATH}")

def add_violation(image_path: str, gender: str, direction: str, explanation: str, confidence: float, is_phone_detected: bool = True) -> int:
    """
    Saves a violation log to the SQLite database.
    Returns the ID of the newly inserted row.
    """
    timestamp = datetime.now().isoformat()
    is_phone_int = 1 if is_phone_detected else 0
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO violations (timestamp, image_path, gender, direction, explanation, confidence, is_phone_detected)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (timestamp, image_path, gender.lower(), direction.lower(), explanation, confidence, is_phone_int)
        )
        conn.commit()
        return cursor.lastrowid

def get_recent_violations(limit: int = 10):
    """Fetches the most recent violations."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM violations ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]

def get_statistics():
    """Gathers general statistics for violations."""
    stats = {}
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Total violations
        cursor.execute("SELECT COUNT(*) FROM violations WHERE is_phone_detected = 1")
        stats["total_violations"] = cursor.fetchone()[0]
        
        # Gender breakdown
        cursor.execute("SELECT gender, COUNT(*) FROM violations WHERE is_phone_detected = 1 GROUP BY gender")
        stats["gender_breakdown"] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Direction breakdown
        cursor.execute("SELECT direction, COUNT(*) FROM violations WHERE is_phone_detected = 1 GROUP BY direction")
        stats["direction_breakdown"] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Violations by date
        cursor.execute("""
            SELECT date(timestamp) as violation_date, COUNT(*) 
            FROM violations 
            WHERE is_phone_detected = 1
            GROUP BY violation_date 
            ORDER BY violation_date DESC 
            LIMIT 7
        """)
        stats["daily_stats_past_week"] = {row[0]: row[1] for row in cursor.fetchall()}
        
    return stats

if __name__ == "__main__":
    init_db()
    # Test insertion
    test_id = add_violation(
        image_path="test_snapshot.jpg",
        gender="male",
        direction="down",
        explanation="Testing refactored database module.",
        confidence=0.99,
        is_phone_detected=True
    )
    print(f"Inserted test violation with ID: {test_id}")
    print("Recent violations:")
    for v in get_recent_violations():
        print(dict(v))
    print("Stats:")
    print(get_statistics())
