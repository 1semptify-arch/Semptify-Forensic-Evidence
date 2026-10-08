@echo off
echo Starting Semptify...
echo.

REM Change to project directory (wherever this file lives)
cd /d "%~dp0"

REM Check if Python venv exists
if not exist ".venv" (
    echo Creating Python virtual environment...
    python -m venv .venv
)

REM Activate venv and install dependencies
echo Installing dependencies...
call .venv\Scripts\activate
pip install -r requirements.txt -q

REM Set environment variables
REM For Neon, set DATABASE_URL instead of the individual variables below
REM set DATABASE_URL=postgres://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
set POSTGRES_DB=semptify
set POSTGRES_USER=semptify
set POSTGRES_PASSWORD=semptify_pass
set DB_HOST=localhost
set DB_PORT=5432

REM Start API server
echo.
echo Starting API server on http://localhost:8019
echo Press Ctrl+C to stop
echo.
start http://localhost:8019
python -m app.api.server
