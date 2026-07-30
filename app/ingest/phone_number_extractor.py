import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from db import get_conn

# Phone number regex patterns
PHONE_PATTERNS = [
    r'\+?1?[-.\s]?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US format
    r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',  # International
]

def normalize_phone_number(number: str) -> str:
    """Normalize phone number to E.164 format."""
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', number)
    
    # If starts with +1 (US), keep as is
    if cleaned.startswith('+1'):
        return cleaned
    
    # If 10 digits, assume US and add +1
    if len(cleaned) == 10 and cleaned.isdigit():
        return f'+1{cleaned}'
    
    # If starts with 1 and has 11 digits, add +
    if len(cleaned) == 11 and cleaned.startswith('1'):
        return f'+{cleaned}'
    
    # Otherwise return as-is with + if missing
    if not cleaned.startswith('+'):
        return f'+{cleaned}'
    
    return cleaned

def extract_phone_numbers():
    """Scan all text content for phone numbers and link them."""
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        # Scan document_chunks
        cur.execute("SELECT id, content FROM document_chunks")
        for chunk_id, content in cur.fetchall():
            for pattern in PHONE_PATTERNS:
                matches = re.findall(pattern, content)
                for match in matches:
                    normalized = normalize_phone_number(match)
                    # Insert phone number if new
                    cur.execute(
                        "INSERT INTO phone_numbers (number) VALUES (%s) ON CONFLICT DO NOTHING RETURNING id",
                        (normalized,)
                    )
                    result = cur.fetchone()
                    if result:
                        phone_id = result[0]
                    else:
                        cur.execute("SELECT id FROM phone_numbers WHERE number = %s", (normalized,))
                        phone_id = cur.fetchone()[0]
                    
                    # Link to document
                    cur.execute(
                        "INSERT INTO phone_links (phone_id, source_type, source_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                        (phone_id, 'document_chunk', chunk_id)
                    )
        
        # Scan call_chunks
        cur.execute("SELECT id, content FROM call_chunks")
        for chunk_id, content in cur.fetchall():
            for pattern in PHONE_PATTERNS:
                matches = re.findall(pattern, content)
                for match in matches:
                    normalized = normalize_phone_number(match)
                    cur.execute(
                        "INSERT INTO phone_numbers (number) VALUES (%s) ON CONFLICT DO NOTHING RETURNING id",
                        (normalized,)
                    )
                    result = cur.fetchone()
                    if result:
                        phone_id = result[0]
                    else:
                        cur.execute("SELECT id FROM phone_numbers WHERE number = %s", (normalized,))
                        phone_id = cur.fetchone()[0]
                    
                    cur.execute(
                        "INSERT INTO phone_links (phone_id, source_type, source_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                        (phone_id, 'call_chunk', chunk_id)
                    )
        
        # Scan sms_messages
        cur.execute("SELECT id, content FROM sms_messages")
        for sms_id, content in cur.fetchall():
            for pattern in PHONE_PATTERNS:
                matches = re.findall(pattern, content)
                for match in matches:
                    normalized = normalize_phone_number(match)
                    cur.execute(
                        "INSERT INTO phone_numbers (number) VALUES (%s) ON CONFLICT DO NOTHING RETURNING id",
                        (normalized,)
                    )
                    result = cur.fetchone()
                    if result:
                        phone_id = result[0]
                    else:
                        cur.execute("SELECT id FROM phone_numbers WHERE number = %s", (normalized,))
                        phone_id = cur.fetchone()[0]
                    
                    cur.execute(
                        "INSERT INTO phone_links (phone_id, source_type, source_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                        (phone_id, 'sms', sms_id)
                    )
        
        conn.commit()
        print("Phone number extraction complete")
    except Exception as e:
        print(f"Error extracting phone numbers: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    extract_phone_numbers()
