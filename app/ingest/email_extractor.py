from pathlib import Path
import email
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from db import get_conn

def handle_email(path: Path, file_hash: str):
    """Parse email and store in database."""
    raw = path.read_bytes()
    msg = email.message_from_bytes(raw)
    
    subject = msg.get("Subject", "")
    from_addr = msg.get("From", "")
    to_addr = msg.get("To", "")
    date = msg.get("Date", "")
    
    # Extract body
    body = ""
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            body += part.get_payload(decode=True).decode(errors="ignore")
    
    # Insert document
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO documents (case_id, doc_type, title, file_path, file_hash) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (1, "email", subject[:200] if subject else "No Subject", str(path), file_hash),
        )
        doc_id = cur.fetchone()[0]
        conn.commit()
        
        # Chunk and insert body
        chunk_size = 2000
        for i in range(0, len(body), chunk_size):
            chunk = body[i:i+chunk_size]
            cur.execute(
                "INSERT INTO document_chunks (document_id, chunk_index, content) "
                "VALUES (%s, %s, %s)",
                (doc_id, i//chunk_size, chunk),
            )
        conn.commit()
        print(f"Stored email document {doc_id}")
        
        # Handle attachments
        for part in msg.walk():
            if part.get_content_disposition() and part.get_filename():
                attachment_name = part.get_filename()
                attachment_data = part.get_payload(decode=True)
                # Save attachment and re-route through watcher
                # This would be implemented in a full version
    finally:
        cur.close()
        conn.close()
