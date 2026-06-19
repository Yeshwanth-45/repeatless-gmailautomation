-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- USERS TABLE
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  gmail_access_token TEXT,
  gmail_refresh_token TEXT,
  token_expiry TIMESTAMPTZ,
  gmail_history_id TEXT,  -- used for incremental sync
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- THREADS TABLE
CREATE TABLE threads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  gmail_thread_id TEXT NOT NULL,
  subject TEXT,
  participants TEXT[],
  last_message_at TIMESTAMPTZ,
  thread_summary TEXT,
  category TEXT,
  message_count INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, gmail_thread_id)
);

-- EMAILS TABLE
CREATE TABLE emails (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  thread_id UUID REFERENCES threads(id) ON DELETE CASCADE,
  gmail_message_id TEXT UNIQUE NOT NULL,
  gmail_thread_id TEXT NOT NULL,
  subject TEXT,
  sender TEXT,
  sender_email TEXT,
  recipients TEXT[],
  body_text TEXT,
  body_html TEXT,
  snippet TEXT,
  received_at TIMESTAMPTZ,
  labels TEXT[],
  category TEXT,
  summary TEXT,
  in_reply_to TEXT,      -- Gmail thread header
  references_header TEXT, -- Gmail thread header
  is_read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- EMAIL CHUNKS TABLE (for RAG / pgvector)
CREATE TABLE email_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email_id UUID REFERENCES emails(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  chunk_text TEXT NOT NULL,
  chunk_index INT NOT NULL,
  embedding vector(768),  -- Gemini text-embedding-004 outputs 768 dims
  metadata JSONB,  -- stores: sender, sender_email, subject, date, thread_id, gmail_message_id
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- CHAT SESSIONS TABLE
CREATE TABLE chat_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  title TEXT DEFAULT 'New Chat',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- CHAT MESSAGES TABLE
CREATE TABLE chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  sources JSONB,  -- list of {sender, subject, date, gmail_message_id} used
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- INDEXES for performance
CREATE INDEX ON threads(user_id);
CREATE INDEX ON threads(category);
CREATE INDEX ON emails(user_id);
CREATE INDEX ON emails(thread_id);
CREATE INDEX ON emails(category);
CREATE INDEX ON emails(received_at DESC);
CREATE INDEX ON email_chunks(user_id);
CREATE INDEX ON email_chunks(email_id);
CREATE INDEX ON chat_messages(session_id);

-- pgvector index for fast similarity search
CREATE INDEX ON email_chunks 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- FUNCTION for vector similarity search
CREATE OR REPLACE FUNCTION search_email_chunks(
  query_embedding vector(768),
  target_user_id UUID,
  match_count INT DEFAULT 20
)
RETURNS TABLE (
  id UUID,
  email_id UUID,
  chunk_text TEXT,
  chunk_index INT,
  metadata JSONB,
  similarity FLOAT
)
LANGUAGE SQL STABLE
AS $$
  SELECT
    ec.id,
    ec.email_id,
    ec.chunk_text,
    ec.chunk_index,
    ec.metadata,
    1 - (ec.embedding <=> query_embedding) AS similarity
  FROM email_chunks ec
  WHERE ec.user_id = target_user_id
  ORDER BY ec.embedding <=> query_embedding
  LIMIT match_count;
$$;
