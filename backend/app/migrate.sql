-- Run once after DB is up:
-- psql -h localhost -U rag -d rag -f app/migrate.sql

CREATE EXTENSION IF NOT EXISTS vector;

-- FTS support: generated tsvector
ALTER TABLE chunks
ADD COLUMN IF NOT EXISTS fts tsvector
GENERATED ALWAYS AS (to_tsvector('turkish', coalesce(chunk_text,''))) STORED;

CREATE INDEX IF NOT EXISTS ix_chunks_fts ON chunks USING GIN (fts);

-- Embeddings (pgvector)
ALTER TABLE chunks
ADD COLUMN IF NOT EXISTS embedding vector(1536);

CREATE INDEX IF NOT EXISTS ix_chunks_embedding
ON chunks USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);
