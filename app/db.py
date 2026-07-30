import os
import psycopg2

def get_conn():
    """Get PostgreSQL connection using environment variables or DATABASE_URL."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg2.connect(database_url)
    
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "semptify"),
        user=os.getenv("POSTGRES_USER", "semptify"),
        password=os.getenv("POSTGRES_PASSWORD", "semptify_pass"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
    )
