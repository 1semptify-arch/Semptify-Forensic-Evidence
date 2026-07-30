from pathlib import Path
import csv
import sys
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent))
from db import get_conn

def handle_csv(path: Path):
    """Parse carrier call log CSV and insert into calls table."""
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Adjust column names based on actual carrier format
                phone_number = row.get('Phone Number') or row.get('Number') or row.get('phone') or 'unknown'
                direction = row.get('Direction') or row.get('Type') or 'unknown'
                started_at_str = row.get('Date') or row.get('Timestamp') or row.get('date')
                duration_str = row.get('Duration') or row.get('duration') or '0'
                
                # Parse datetime
                started_at = datetime.now()
                if started_at_str:
                    try:
                        started_at = datetime.fromisoformat(started_at_str.replace('T', ' '))
                    except:
                        pass
                
                # Parse duration
                duration = 0
                try:
                    duration = int(duration_str)
                except:
                    pass
                
                cur.execute(
                    "INSERT INTO calls (phone_number, direction, started_at, duration, file_path) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (phone_number, direction, started_at, duration, str(path)),
                )
        
        conn.commit()
        print(f"Processed CSV call log: {path}")
    except Exception as e:
        print(f"Error processing CSV: {e}")
    finally:
        cur.close()
        conn.close()
