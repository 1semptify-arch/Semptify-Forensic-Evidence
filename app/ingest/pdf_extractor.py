from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from db import get_conn

def handle_pdf(path: Path, file_hash: str):
    """Extract text from PDF and store in database."""
    text = ""
    
    # Try pypdf first
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        for page in reader.pages:
            text += page.extract_text() or ""
    except Exception as e:
        print(f"pypdf failed: {e}")
    
    # Fallback to OCR if text is empty
    if not text.strip():
        try:
            from pdf2image import convert_from_path
            import pytesseract
            pages = convert_from_path(str(path))
            for img in pages:
                text += pytesseract.image_to_string(img)
        except Exception as e:
            print(f"OCR failed: {e}")
    
    # Insert document
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO documents (case_id, doc_type, title, file_path, file_hash) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (1, "pdf", path.name, str(path), file_hash),
        )
        doc_id = cur.fetchone()[0]
        conn.commit()
        
        # Chunk and insert text
        chunk_size = 2000
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i+chunk_size]
            cur.execute(
                "INSERT INTO document_chunks (document_id, chunk_index, content) "
                "VALUES (%s, %s, %s)",
                (doc_id, i//chunk_size, chunk),
            )
        conn.commit()
        print(f"Stored PDF document {doc_id}")
    finally:
        cur.close()
        conn.close()
