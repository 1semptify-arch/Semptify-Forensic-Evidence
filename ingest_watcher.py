# ingest_watcher.py
import os, time, hashlib, shutil
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import psycopg2
from psycopg2.extras import RealDictCursor

INBOX = Path("data/semptify_inbox")
CASES = Path("data/cases")
CASES.mkdir(parents=True, exist_ok=True)
DEFAULT_CASE = CASES / "velair_lexington"
DEFAULT_CASE.mkdir(parents=True, exist_ok=True)

DB = {
  "dbname": os.getenv("POSTGRES_DB","semptify"),
  "user": os.getenv("POSTGRES_USER","semptify"),
  "password": os.getenv("POSTGRES_PASSWORD","semptify_pass"),
  "host": os.getenv("DB_HOST","localhost"),
  "port": os.getenv("DB_PORT",5432)
}

def get_conn():
    return psycopg2.connect(**DB)

def sha256(path):
    h = hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def extract_text(pdf_path):
    # try pypdf
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        text = ""
        for p in reader.pages:
            text += p.extract_text() or ""
        if text.strip():
            return text
    except Exception:
        pass
    # fallback OCR
    try:
        import pytesseract
        from pdf2image import convert_from_path
        pages = convert_from_path(str(pdf_path))
        text = ""
        for img in pages:
            text += pytesseract.image_to_string(img)
        return text
    except Exception as e:
        print("OCR failed:", e)
        return ""

def store_document(file_path, file_hash, text):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO documents (case_id, doc_type, title, file_path, file_hash) VALUES (%s,%s,%s,%s,%s) RETURNING id",
                (1, 'evidence_raw', os.path.basename(file_path), str(file_path), file_hash))
    doc_id = cur.fetchone()[0]
    conn.commit()
    # chunk text
    chunk_size = 2000
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i+chunk_size]
        cur.execute("INSERT INTO document_chunks (document_id, chunk_index, content) VALUES (%s,%s,%s)",
                    (doc_id, i//chunk_size, chunk))
    conn.commit()
    cur.close()
    conn.close()
    print("Stored document id", doc_id)

class Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        print("New file:", path)
        h = sha256(path)
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM documents WHERE file_hash=%s", (h,))
        if cur.fetchone():
            print("Duplicate detected, moving to quarantine")
            q = Path("data/semptify_quarantine")
            q.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(q / path.name))
            cur.close()
            conn.close()
            return
        # move to default case
        dest = DEFAULT_CASE / path.name
        shutil.move(str(path), str(dest))
        text = extract_text(dest)
        store_document(dest, h, text)
        cur.close()
        conn.close()

if __name__ == "__main__":
    event_handler = Handler()
    observer = Observer()
    observer.schedule(event_handler, str(INBOX), recursive=True)
    observer.start()
    print("Watching", INBOX)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
