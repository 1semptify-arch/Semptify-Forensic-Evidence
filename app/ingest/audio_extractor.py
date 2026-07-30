from pathlib import Path
import sys
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent))
from db import get_conn

def handle_audio(path: Path, file_hash: str = None):
    """Insert audio file as call record (transcript to be added later)."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO calls (phone_number, direction, started_at, duration, file_path) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            ("unknown", "unknown", datetime.now(), 0, str(path)),
        )
        call_id = cur.fetchone()[0]
        conn.commit()
        print(f"Stored audio call {call_id}")
        # Transcript will be added later via ASR integration
    finally:
        cur.close()
        conn.close()
