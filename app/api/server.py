from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict
from pathlib import Path
import sys
import os
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))
from db import get_conn
from search.search_api import search_all, get_document_detail, get_call_detail, get_sms_detail, get_phone_number_context
from ingest.phone_number_extractor import extract_phone_numbers

app = FastAPI(title="Semptify API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
FRONTEND_DIR = BASE_DIR / "app" / "ui" / "web"
INBOX_DIR = BASE_DIR / "data" / "inbox"
QUARANTINE_DIR = BASE_DIR / "data" / "quarantine"

# Mount static files
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
async def serve_frontend():
    if (FRONTEND_DIR / "index.html").exists():
        return FileResponse(FRONTEND_DIR / "index.html")
    return {"message": "Semptify API", "version": "2.0.0"}

@app.get("/USER_GUIDE.md")
async def serve_user_guide():
    guide_path = BASE_DIR / "USER_GUIDE.md"
    if guide_path.exists():
        return FileResponse(guide_path)
    return {"error": "User guide not found"}

# Models
class SearchRequest(BaseModel):
    keywords: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    sources: Optional[List[str]] = None
    types: Optional[List[str]] = None
    phone_numbers: Optional[List[str]] = None
    case_id: Optional[int] = None
    confidence: Optional[float] = None

class EventCreate(BaseModel):
    case_id: int
    event_type: str
    title: str
    description: Optional[str] = None
    occurred_at: str

# Endpoints
@app.get("/api/health")
async def health_check():
    try:
        conn = get_conn()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.post("/api/search")
async def search(request: SearchRequest):
    """Search across documents, calls, and SMS."""
    params = request.dict(exclude_none=True)
    results = search_all(params)
    return results

@app.get("/api/document/{doc_id}")
async def get_document(doc_id: int):
    """Get document details with chunks."""
    doc = get_document_detail(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@app.get("/api/call/{call_id}")
async def get_call(call_id: int):
    """Get call details with transcript."""
    call = get_call_detail(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call

@app.get("/api/sms/{sms_id}")
async def get_sms(sms_id: int):
    """Get SMS message details."""
    sms = get_sms_detail(sms_id)
    if not sms:
        raise HTTPException(status_code=404, detail="SMS not found")
    return sms

@app.get("/api/phone/{phone_number}")
async def get_phone_context(phone_number: str):
    """Get all evidence linked to a phone number."""
    return get_phone_number_context(phone_number)

@app.get("/api/cases")
async def get_cases():
    """Get all cases."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM cases ORDER BY opened_at DESC")
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

@app.post("/api/cases")
async def create_case(case: dict):
    """Create a new case."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO cases (case_number, title, status, court, opened_at) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (case.get('case_number'), case.get('title'), case.get('status', 'active'), 
             case.get('court'), case.get('opened_at'))
        )
        case_id = cur.fetchone()[0]
        conn.commit()
        return {"id": case_id, "message": "Case created"}
    finally:
        cur.close()
        conn.close()

@app.get("/api/events")
async def get_events(case_id: Optional[int] = None):
    """Get events, optionally filtered by case."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        if case_id:
            cur.execute("SELECT * FROM events WHERE case_id = %s ORDER BY occurred_at DESC", (case_id,))
        else:
            cur.execute("SELECT * FROM events ORDER BY occurred_at DESC")
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

@app.post("/api/events")
async def create_event(event: EventCreate):
    """Create a new event."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO events (case_id, event_type, title, description, occurred_at) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (event.case_id, event.event_type, event.title, event.description, event.occurred_at)
        )
        event_id = cur.fetchone()[0]
        conn.commit()
        return {"id": event_id, "message": "Event created"}
    finally:
        cur.close()
        conn.close()

@app.get("/api/phone-numbers")
async def get_phone_numbers():
    """Get all phone numbers with labels."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM phone_numbers ORDER BY number")
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

@app.post("/api/phone-numbers/{phone_id}/label")
async def update_phone_label(phone_id: int, label: str):
    """Update phone number label."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE phone_numbers SET label = %s WHERE id = %s", (label, phone_id))
        conn.commit()
        return {"message": "Label updated"}
    finally:
        cur.close()
        conn.close()

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), case_id: int = 1):
    """Upload file to inbox for processing."""
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    file_path = INBOX_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"message": "File uploaded to inbox", "path": str(file_path)}

@app.get("/api/quarantine")
async def get_quarantine():
    """List quarantined files."""
    files = []
    if QUARANTINE_DIR.exists():
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
    """Delete file from quarantine."""
    file_path = QUARANTINE_DIR / filename
    if file_path.exists():
        file_path.unlink()
        return {"message": "File deleted"}
    raise HTTPException(status_code=404, detail="File not found")

@app.post("/api/extract-phone-numbers")
async def trigger_phone_extraction(background_tasks: BackgroundTasks):
    """Trigger phone number extraction job."""
    background_tasks.add_task(extract_phone_numbers)
    return {"message": "Phone number extraction started in background"}

@app.get("/api/stats")
async def get_stats():
    """Get system statistics."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        stats = {}
        
        # Document counts
        cur.execute("SELECT COUNT(*) FROM documents")
        stats['total_documents'] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM calls")
        stats['total_calls'] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM sms_messages")
        stats['total_sms'] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM cases")
        stats['total_cases'] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM phone_numbers")
        stats['total_phone_numbers'] = cur.fetchone()[0]
        
        # Storage stats
        inbox_size = sum(f.stat().st_size for f in INBOX_DIR.rglob('*') if f.is_file()) if INBOX_DIR.exists() else 0
        quarantine_size = sum(f.stat().st_size for f in QUARANTINE_DIR.rglob('*') if f.is_file()) if QUARANTINE_DIR.exists() else 0
        
        stats['storage'] = {
            'inbox_bytes': inbox_size,
            'quarantine_bytes': quarantine_size
        }
        
        return stats
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8019)
