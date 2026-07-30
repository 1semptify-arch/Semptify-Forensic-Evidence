-- init_db.sql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS vector; -- if pgvector installed

CREATE TABLE cases (
  id SERIAL PRIMARY KEY,
  case_number TEXT,
  title TEXT,
  status TEXT,
  court TEXT,
  opened_at TIMESTAMP,
  closed_at TIMESTAMP
);

CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  case_id INTEGER REFERENCES cases(id),
  doc_type TEXT,
  title TEXT,
  version INTEGER DEFAULT 1,
  file_path TEXT,
  file_hash TEXT,
  created_at TIMESTAMP DEFAULT now(),
  uploaded_at TIMESTAMP DEFAULT now()
);

CREATE TABLE document_chunks (
  id SERIAL PRIMARY KEY,
  document_id INTEGER REFERENCES documents(id),
  chunk_index INTEGER,
  content TEXT,
  embedding vector(1536)
);

CREATE TABLE events (
  id SERIAL PRIMARY KEY,
  case_id INTEGER REFERENCES cases(id),
  event_type TEXT,
  title TEXT,
  description TEXT,
  occurred_at TIMESTAMP,
  location TEXT
);

CREATE TABLE event_links (
  id SERIAL PRIMARY KEY,
  event_id INTEGER REFERENCES events(id),
  document_id INTEGER REFERENCES documents(id)
);

CREATE TABLE signatures (
  id SERIAL PRIMARY KEY,
  document_id INTEGER REFERENCES documents(id),
  signed_by TEXT,
  signed_at TIMESTAMP,
  signature_type TEXT
);

CREATE TABLE costs (
  id SERIAL PRIMARY KEY,
  case_id INTEGER REFERENCES cases(id),
  document_id INTEGER,
  cost_type TEXT,
  amount NUMERIC,
  incurred_at TIMESTAMP
);
