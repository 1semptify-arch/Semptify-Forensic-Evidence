-- init_db.sql - Full forensic evidence database schema
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS vector;

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

CREATE TABLE calls (
  id SERIAL PRIMARY KEY,
  phone_number TEXT,
  direction TEXT,
  started_at TIMESTAMP,
  duration INTEGER,
  file_path TEXT,
  transcript_confidence FLOAT
);

CREATE TABLE call_chunks (
  id SERIAL PRIMARY KEY,
  call_id INTEGER REFERENCES calls(id),
  chunk_index INTEGER,
  content TEXT,
  embedding vector(1536)
);

CREATE TABLE sms_messages (
  id SERIAL PRIMARY KEY,
  phone_number TEXT,
  direction TEXT,
  sent_at TIMESTAMP,
  content TEXT,
  attachment_path TEXT
);

CREATE TABLE phone_numbers (
  id SERIAL PRIMARY KEY,
  number TEXT,
  label TEXT
);

CREATE TABLE phone_links (
  id SERIAL PRIMARY KEY,
  phone_id INTEGER REFERENCES phone_numbers(id),
  source_type TEXT,
  source_id INTEGER
);

CREATE TABLE events (
  id SERIAL PRIMARY KEY,
  case_id INTEGER REFERENCES cases(id),
  event_type TEXT,
  title TEXT,
  description TEXT,
  occurred_at TIMESTAMP
);

CREATE TABLE event_links (
  id SERIAL PRIMARY KEY,
  event_id INTEGER REFERENCES events(id),
  source_type TEXT,
  source_id INTEGER
);

CREATE TABLE costs (
  id SERIAL PRIMARY KEY,
  case_id INTEGER REFERENCES cases(id),
  document_id INTEGER,
  cost_type TEXT,
  amount NUMERIC,
  incurred_at TIMESTAMP
);
