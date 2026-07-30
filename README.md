# Semptify - Forensic Evidence System

Local-first forensic evidence management system for Lexington Flats / Velair legal cases. Ingests documents, calls, SMS, emails, and carrier records with deduplication, OCR, transcription, and unified search.

## Project Structure

```
C:\REPOs\PPPP\
├── app/
│   ├── db.py                      # Database connection helper
│   ├── ingest/
│   │   ├── watcher.py             # File system watcher
│   │   ├── classify.py            # File type classifier
│   │   ├── pdf_extractor.py       # PDF text extraction
│   │   ├── image_extractor.py     # Image OCR
│   │   ├── email_extractor.py     # Email parsing
│   │   ├── audio_extractor.py     # Audio/call handling
│   │   ├── csv_extractor.py       # Carrier call log parsing
│   │   ├── sms_importer.py        # SMS export parsing
│   │   └── phone_number_extractor.py  # Phone number extraction
│   ├── embeddings/
│   │   └── embed_client.py        # Embedding generation (HF/local)
│   ├── search/
│   │   ├── query_builder.py       # SQL query builder
│   │   └── search_api.py          # Search API functions
│   ├── api/
│   │   └── server.py              # FastAPI REST server
│   └── ui/
│       └── web/
│           └── index.html         # Web UI
├── db/
│   └── init_db.sql               # PostgreSQL schema
├── data/
│   ├── inbox/                    # Intake folder
│   ├── quarantine/               # Duplicates
│   └── cases/                    # Canonical storage
├── scripts/
│   ├── email_fetcher.py          # Gmail/Hotmail IMAP
│   └── dedupe_scan.ps1           # PowerShell deduplication
├── secrets/                      # Encrypted credentials
├── docker-compose.yml            # PostgreSQL container
├── requirements.txt              # Python dependencies
└── start.bat                     # Windows startup script
```

## Prerequisites

- Python 3.8+
- PostgreSQL 16+ (or Neon serverless)
- Tesseract OCR (for PDF/image OCR)
- Poppler (for pdf2image)
- Docker (optional, for local PostgreSQL)

### Install Tesseract OCR (Windows)

1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to `C:\Program Files\Tesseract-OCR`
3. Add to PATH or set `TESSDATA_PREFIX` environment variable

### Install Poppler (Windows)

1. Download from: http://blog.alivate.com.au/poppler-windows/
2. Extract and add `bin` folder to PATH

## Quick Start

### Option 1: Neon Serverless (Recommended)

1. Create a free Neon account at https://neon.tech
2. Create a new project and copy the connection string
3. Set the DATABASE_URL environment variable:

```powershell
# Change to project directory
cd C:\REPOs\PPPP

# Set Neon connection string
$env:DATABASE_URL="postgres://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require"

# Create virtual environment and install dependencies
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Run schema (first time only)
psql $env:DATABASE_URL -f db/init_db.sql

# Insert default case
psql $env:DATABASE_URL -c "INSERT INTO cases (case_number, title, status, opened_at) VALUES ('VEL-001', 'Lexington Flats / Velair', 'active', NOW());"

# Start API server
python -m app.api.server
```

### Option 2: Docker (Local)

```powershell
# Change to project directory
cd C:\REPOs\PPPP

# Start PostgreSQL
docker-compose up -d

# Create virtual environment and install dependencies
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
$env:POSTGRES_DB="semptify"
$env:POSTGRES_USER="semptify"
$env:POSTGRES_PASSWORD="semptify_pass"
$env:DB_HOST="localhost"

# Run schema (first time only)
psql -h localhost -U semptify -d semptify -f db/init_db.sql

# Insert default case
psql -h localhost -U semptify -d semptify -c "INSERT INTO cases (case_number, title, status, opened_at) VALUES ('VEL-001', 'Lexington Flats / Velair', 'active', NOW());"

# Start API server
python -m app.api.server
```

### Option 2: Local PostgreSQL

```powershell
# Change to project directory
cd C:\REPOs\PPPP

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Create database
createdb semptify

# Run schema
psql -d semptify -f db/init_db.sql

# Insert default case
psql -d semptify -c "INSERT INTO cases (case_number, title, status, opened_at) VALUES ('VEL-001', 'Lexington Flats / Velair', 'active', NOW());"

# Start API server
python -m app.api.server
```

### Option 3: Using start.bat

```powershell
# Edit start.bat to set your database credentials
# Then run:
start.bat
```

## Running the System

### 1. Start the API Server

```powershell
python -m app.api.server
```

The web UI will be available at `http://localhost:8000`

### 2. Start the Ingest Watcher (Separate Terminal)

```powershell
python -m app.ingest.watcher
```

This watches `data/inbox/` for new files and processes them automatically.

### 3. Upload Files

- Use the web UI upload tab
- Or manually copy files to `data/inbox/`

### 4. Run Phone Number Extraction

```powershell
python -m app.ingest.phone_number_extractor
```

Or trigger from the web UI Quarantine tab.

## Web UI Features

- **Dashboard**: System statistics and storage overview
- **Search**: Unified search across documents, calls, and SMS with filters
- **Upload**: Drag-and-drop file upload
- **Timeline**: Chronological view of events
- **Phone Numbers**: View all phone numbers and linked evidence
- **Quarantine**: Review and manage duplicate files

## Database Schema

The system uses PostgreSQL with the following tables:

- `cases` - Legal case information
- `documents` - File metadata (PDFs, images, emails)
- `document_chunks` - Text chunks with optional embeddings
- `calls` - Call records and recordings
- `call_chunks` - Transcribed call audio
- `sms_messages` - SMS/MMS messages
- `phone_numbers` - Normalized phone numbers with labels
- `phone_links` - Links between phone numbers and evidence
- `events` - Timeline events
- `event_links` - Links between events and evidence
- `costs` - Financial records

## Supported File Types

- **PDF**: Text extraction via pypdf, OCR fallback
- **Images**: OCR via Tesseract
- **Email**: .eml parsing, attachment handling
- **Audio**: Call recordings (transcription placeholder)
- **CSV**: Carrier call logs (Xfinity, T-Mobile)
- **XML/CSV**: SMS exports

## Environment Variables

```powershell
$env:POSTGRES_DB="semptify"
$env:POSTGRES_USER="semptify"
$env:POSTGRES_PASSWORD="semptify_pass"
$env:DB_HOST="localhost"
$env:DB_PORT="5432"
$env:HUGGINGFACE_API_KEY="your_hf_key"  # Optional, for embeddings
$env:LOCAL_EMBEDDING_ENDPOINT="http://localhost:11434/api/embeddings"  # Optional, Ollama
```

## API Endpoints

- `GET /` - Web UI
- `POST /api/search` - Search across all data
- `GET /api/document/{id}` - Get document details
- `GET /api/call/{id}` - Get call details
- `GET /api/sms/{id}` - Get SMS details
- `GET /api/phone/{number}` - Get phone number context
- `GET /api/cases` - List cases
- `POST /api/cases` - Create case
- `GET /api/events` - List events
- `POST /api/events` - Create event
- `GET /api/phone-numbers` - List phone numbers
- `POST /api/upload` - Upload file to inbox
- `GET /api/quarantine` - List quarantined files
- `DELETE /api/quarantine/{filename}` - Delete quarantined file
- `POST /api/extract-phone-numbers` - Trigger phone extraction
- `GET /api/stats` - System statistics

## Importing Carrier Data

### Xfinity Mobile

1. Log into Xfinity portal
2. Download call logs as CSV
3. Download voicemails as audio
4. Drop into `data/inbox/`

### T-Mobile

1. Log into T-Mobile account
2. Export call logs as CSV/PDF
3. Drop into `data/inbox/`

### SMS Exports

1. Export SMS from Android (SMS Backup & Restore) or iPhone
2. Drop XML/CSV into `data/inbox/`

## Email Import

```powershell
python scripts/email_fetcher.py
```

Supports Gmail and Hotmail via IMAP. Credentials encrypted and stored in `secrets/`.

## Deduplication

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\dedupe_scan.ps1 -Roots @("C:\Users\Brad\Documents","C:\Users\Brad\OneDrive") -Quarantine "data\quarantine"
```

Duplicates are moved to quarantine for review, not deleted automatically.

## Safety Rules

1. **No automatic deletion** - Duplicates quarantined for review
2. **Keep originals** - Never permanently remove until verified
3. **Human sign-off** - Any assembled filing must be reviewed
4. **Protect credentials** - Encrypted storage for sensitive data
5. **Review OCR** - Low-confidence pages may need manual correction

## Troubleshooting

### PostgreSQL connection failed

```powershell
# Test connection
psql -h localhost -U semptify -d semptify

# If using Docker, check container status
docker ps
docker logs semptify-postgres-1
```

### Tesseract not found

```powershell
# Add to PATH
$env:PATH += ";C:\Program Files\Tesseract-OCR"

# Or set TESSDATA_PREFIX
$env:TESSDATA_PREFIX="C:\Program Files\Tesseract-OCR"
```

### Watcher not processing files

- Ensure files are in `data/inbox/` not subdirectories
- Check console output for errors
- Verify database connection

## License

Local-first forensic evidence system for personal legal case management.
