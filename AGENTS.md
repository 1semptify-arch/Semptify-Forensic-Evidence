# Agent Guide — app-forensic-evidence

## Scope
Local-first forensic evidence management. Ingests documents, calls, SMS, emails, and carrier records with deduplication, OCR, transcription, and unified search.

## Key paths
- `app/` — source code
- `app/api/server.py` — FastAPI entry point
- `app/ingest/` — file ingestion and extraction
- `app/search/` — query builder and search API
- `app/db.py` — database connection helper
- `data/` — runtime intake folders and case storage
- `start.bat` — Windows startup script

## Working rules
- Never delete original evidence. Duplicates go to `data/quarantine/` for human review.
- No PII or case data in commits.
- Do not commit `data/`, `.env`, credentials, or SQLite/PostgreSQL runtime files.
- Python 3.8+; OCR requires Tesseract and Poppler in PATH.

## Local run
```powershell
python -m app.api.server
```
Or use `start.bat` on Windows.
