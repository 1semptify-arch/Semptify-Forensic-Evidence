import time
import hashlib
import shutil
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from db import get_conn
from case_config import CASES_DIR, DEFAULT_CASE_DIR

INBOX = Path("data/inbox")
QUARANTINE = Path("data/quarantine")
CASES = Path(CASES_DIR)
DEFAULT_CASE = Path(DEFAULT_CASE_DIR)

for p in (INBOX, QUARANTINE, DEFAULT_CASE):
    p.mkdir(parents=True, exist_ok=True)

def sha256(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def is_duplicate(file_hash: str) -> bool:
    """Check if file hash exists in documents or calls."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT 1 FROM documents WHERE file_hash=%s LIMIT 1", (file_hash,))
        doc_dup = cur.fetchone()
        cur.execute("SELECT 1 FROM calls WHERE file_path LIKE %s LIMIT 1", (f"%{file_hash}%",))
        call_dup = cur.fetchone()
        return bool(doc_dup or call_dup)
    finally:
        cur.close()
        conn.close()

def classify_and_process(path: Path, file_hash: str):
    """Route file to appropriate extractor based on type."""
    from .classify import classify_file
    extractor_type = classify_file(path)
    
    if extractor_type == "pdf":
        from .pdf_extractor import handle_pdf
        handle_pdf(path, file_hash)
    elif extractor_type == "image":
        from .image_extractor import handle_image
        handle_image(path, file_hash)
    elif extractor_type == "email":
        from .email_extractor import handle_email
        handle_email(path, file_hash)
    elif extractor_type == "audio":
        from .audio_extractor import handle_audio
        handle_audio(path, file_hash)
    elif extractor_type == "csv":
        from .csv_extractor import handle_csv
        handle_csv(path)
    elif extractor_type == "sms":
        from .sms_importer import handle_sms
        handle_sms(path)
    else:
        print(f"Unhandled file type: {path}")

class IngestHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        print(f"New file detected: {path}")
        
        # Wait for file to be fully written
        time.sleep(1)
        
        file_hash = sha256(path)
        
        if is_duplicate(file_hash):
            dest = QUARANTINE / path.name
            counter = 1
            while dest.exists():
                stem = path.stem
                suffix = path.suffix
                dest = QUARANTINE / f"{stem}_{counter}{suffix}"
                counter += 1
            shutil.move(str(path), str(dest))
            print(f"Duplicate detected → moved to quarantine: {dest}")
            return
        
        # Move to default case folder
        dest = DEFAULT_CASE / path.name
        counter = 1
        while dest.exists():
            stem = path.stem
            suffix = path.suffix
            dest = DEFAULT_CASE / f"{stem}_{counter}{suffix}"
            counter += 1
        shutil.move(str(path), str(dest))
        path = dest
        
        # Process file
        classify_and_process(path, file_hash)

if __name__ == "__main__":
    observer = Observer()
    observer.schedule(IngestHandler(), str(INBOX), recursive=True)
    observer.start()
    print(f"Watching inbox: {INBOX}")
    print("Press Ctrl+C to stop...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
