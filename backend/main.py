from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil
import hashlib
import subprocess
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
import json

app = FastAPI(title="Docu Sort API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = Path(__file__).parent.parent
INBOX_DIR = BASE_DIR / "data" / "semptify_inbox"
CASES_DIR = BASE_DIR / "data" / "cases"
QUARANTINE_DIR = BASE_DIR / "data" / "semptify_quarantine"
SECRETS_DIR = BASE_DIR / "secrets"

# Mount static files for frontend
frontend_path = BASE_DIR / "frontend"
app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse(frontend_path / "index.html")

# Database config
DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "semptify"),
    "user": os.getenv("POSTGRES_USER", "semptify"),
    "password": os.getenv("POSTGRES_PASSWORD", "semptify_pass"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# Models
class Document(BaseModel):
    id: int
    title: str
    file_path: str
    file_hash: str
    doc_type: str
    created_at: str
    case_id: int

class Case(BaseModel):
    id: int
    case_number: str
    title: str
    status: str
    court: Optional[str] = None
    opened_at: Optional[str] = None

class DuplicateGroup(BaseModel):
    hash: str
    files: List[str]
    kept: str

class EmailConfig(BaseModel):
    provider: str
    email: str
    password: str

# Endpoints
@app.get("/")
async def root():
    return {"message": "Docu Sort API", "version": "1.0.0"}

@app.get("/api/health")
async def health_check():
    try:
        conn = get_db_connection()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.get("/api/stats")
async def get_stats():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Document counts
        cur.execute("SELECT COUNT(*) as total FROM documents")
        total_docs = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as total FROM cases")
        total_cases = cur.fetchone()['total']
        
        # Storage stats
        inbox_size = sum(f.stat().st_size for f in INBOX_DIR.rglob('*') if f.is_file())
        case_size = sum(f.stat().st_size for f in CASES_DIR.rglob('*') if f.is_file())
        quarantine_size = sum(f.stat().st_size for f in QUARANTINE_DIR.rglob('*') if f.is_file())
        
        return {
            "total_documents": total_docs,
            "total_cases": total_cases,
            "storage": {
                "inbox_bytes": inbox_size,
                "cases_bytes": case_size,
                "quarantine_bytes": quarantine_size
            }
        }
    finally:
        cur.close()
        conn.close()

@app.get("/api/cases", response_model=List[Case])
async def get_cases():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("SELECT * FROM cases ORDER BY opened_at DESC")
        return [Case(**row) for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

@app.post("/api/cases")
async def create_case(case: Case):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            "INSERT INTO cases (case_number, title, status, court, opened_at) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (case.case_number, case.title, case.status, case.court, case.opened_at)
        )
        case_id = cur.fetchone()[0]
        conn.commit()
        return {"id": case_id, "message": "Case created"}
    finally:
        cur.close()
        conn.close()

@app.get("/api/documents", response_model=List[Document])
async def get_documents(case_id: Optional[int] = None, limit: int = 100, offset: int = 0):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        if case_id:
            cur.execute(
                "SELECT * FROM documents WHERE case_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (case_id, limit, offset)
            )
        else:
            cur.execute(
                "SELECT * FROM documents ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (limit, offset)
            )
        return [Document(**row) for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: int):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("SELECT * FROM documents WHERE id = %s", (doc_id,))
        doc = cur.fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get chunks
        cur.execute("SELECT * FROM document_chunks WHERE document_id = %s ORDER BY chunk_index", (doc_id,))
        chunks = cur.fetchall()
        
        return {"document": doc, "chunks": chunks}
    finally:
        cur.close()
        conn.close()

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), case_id: int = 1):
    # Save to inbox
    file_path = INBOX_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"message": "File uploaded to inbox", "path": str(file_path)}

@app.get("/api/quarantine")
async def get_quarantine():
    files = []
    for f in QUARANTINE_DIR.rglob('*'):
        if f.is_file():
            files.append({
                "name": f.name,
                "path": str(f),
                "size": f.stat().st_size
            })
    return {"files": files, "count": len(files)}

@app.delete("/api/quarantine/{filename}")
async def delete_quarantine_file(filename: str):
    file_path = QUARANTINE_DIR / filename
    if file_path.exists():
        file_path.unlink()
        return {"message": "File deleted"}
    raise HTTPException(status_code=404, detail="File not found")

@app.post("/api/dedupe/run")
async def run_dedupe(background_tasks: BackgroundTasks, roots: List[str] = None):
    if roots is None:
        roots = ["C:\\Users\\Brad\\Documents", "C:\\Users\\Brad\\OneDrive"]
    
    script_path = BASE_DIR / "dedupe_quarantine.ps1"
    
    def run_script():
        subprocess.run([
            "powershell",
            "-ExecutionPolicy", "Bypass",
            "-File", str(script_path),
            "-Roots", ",".join(roots),
            "-Quarantine", str(QUARANTINE_DIR)
        ])
    
    background_tasks.add_task(run_script)
    return {"message": "Deduplication started in background"}

@app.get("/api/dedupe/log")
async def get_dedupe_log():
    log_path = QUARANTINE_DIR / "dedupe_log.csv"
    if not log_path.exists():
        return {"log": []}
    
    log = []
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines[1:]:  # Skip header
            parts = line.strip().split(',')
            if len(parts) >= 4:
                log.append({
                    "hash": parts[0],
                    "kept": parts[1],
                    "moved": parts[2],
                    "moved_to": parts[3]
                })
    return {"log": log}

@app.post("/api/email/fetch")
async def fetch_emails(background_tasks: BackgroundTasks):
    script_path = BASE_DIR / "email_fetcher.py"
    
    def run_fetcher():
        subprocess.run(["python", str(script_path)], cwd=str(BASE_DIR))
    
    background_tasks.add_task(run_fetcher)
    return {"message": "Email fetcher started in background"}

@app.post("/api/watcher/start")
async def start_watcher(background_tasks: BackgroundTasks):
    script_path = BASE_DIR / "ingest_watcher.py"
    
    def run_watcher():
        subprocess.run(["python", str(script_path)], cwd=str(BASE_DIR))
    
    background_tasks.add_task(run_watcher)
    return {"message": "Ingest watcher started in background"}

@app.get("/api/search")
async def search_documents(query: str, case_id: Optional[int] = None):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        search_pattern = f"%{query}%"
        if case_id:
            cur.execute(
                """SELECT d.*, dc.content 
                   FROM documents d 
                   LEFT JOIN document_chunks dc ON d.id = dc.document_id 
                   WHERE d.case_id = %s AND (d.title ILIKE %s OR dc.content ILIKE %s)
                   LIMIT 50""",
                (case_id, search_pattern, search_pattern)
            )
        else:
            cur.execute(
                """SELECT d.*, dc.content 
                   FROM documents d 
                   LEFT JOIN document_chunks dc ON d.id = dc.document_id 
                   WHERE d.title ILIKE %s OR dc.content ILIKE %s
                   LIMIT 50""",
                (search_pattern, search_pattern)
            )
        return {"results": cur.fetchall()}
    finally:
        cur.close()
        conn.close()

@app.post("/api/settings/database")
async def update_database_settings(config: dict):
    # Update environment variables or config file
    config_path = SECRETS_DIR / "db_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f)
    return {"message": "Database settings updated"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
