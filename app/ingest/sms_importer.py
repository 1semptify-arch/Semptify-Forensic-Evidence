from pathlib import Path
import csv
import xml.etree.ElementTree as ET
import sys
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent))
from db import get_conn

def handle_sms(path: Path):
    """Parse SMS export (XML or CSV) and insert into sms_messages table."""
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        if path.suffix.lower() == '.xml':
            # Parse XML format (Android SMS backup)
            tree = ET.parse(path)
            root = tree.getroot()
            for sms in root.findall('sms'):
                phone_number = sms.get('address', 'unknown')
                direction = 'incoming' if sms.get('type') == '1' else 'outgoing'
                sent_at = datetime.fromtimestamp(int(sms.get('date', '0')) / 1000)
                content = sms.get('body', '')
                
                cur.execute(
                    "INSERT INTO sms_messages (phone_number, direction, sent_at, content) "
                    "VALUES (%s, %s, %s, %s)",
                    (phone_number, direction, sent_at, content),
                )
        
        elif path.suffix.lower() == '.csv':
            # Parse CSV format
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    phone_number = row.get('Phone') or row.get('Number') or row.get('phone') or 'unknown'
                    direction = row.get('Direction') or row.get('Type') or 'unknown'
                    sent_at_str = row.get('Date') or row.get('Timestamp') or row.get('date')
                    content = row.get('Message') or row.get('Body') or row.get('message') or ''
                    
                    sent_at = datetime.now()
                    if sent_at_str:
                        try:
                            sent_at = datetime.fromisoformat(sent_at_str.replace('T', ' '))
                        except:
                            pass
                    
                    cur.execute(
                        "INSERT INTO sms_messages (phone_number, direction, sent_at, content) "
                        "VALUES (%s, %s, %s, %s)",
                        (phone_number, direction, sent_at, content),
                    )
        
        conn.commit()
        print(f"Processed SMS export: {path}")
    except Exception as e:
        print(f"Error processing SMS: {e}")
    finally:
        cur.close()
        conn.close()
