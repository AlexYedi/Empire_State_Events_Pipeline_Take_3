-- =====================================================================
-- YED-118 — Document Knowledge Base (RAG) schema
-- Project: Supabase `empire state ai` — ref oicikjyzmxqfomrrqkvf  (NOT any other project)
-- Apply ONCE via the empire state ai SQL Editor (PostgREST cannot run DDL).
-- Vector index for the doc corpus; raw blobs live in Cloudflare R2 (not here).
-- Embedding model: BAAI/bge-small-en-v1.5 → 384 dims. (Fallback bge-base = 768; see PRD §3.)
-- =====================================================================

-- 1. Extension --------------------------------------------------------
create extension if not exists vector;

-- 2. documents (one row per ingested file) ----------------------------
create table if not exists public.documents (
  id              uuid primary key default gen_random_uuid(),
  title           text not null,
  author          text,
  source_type     text not null default 'book'
                    check (source_type in ('book','whitepaper','filing','pdf','other')),
  blob_key        text not null,                 -- Cloudflare R2 object key: {id}/{filename}
  sha256          text not null unique,           -- content dedup key
  word_count      integer,
  embedding_model text not null default 'BAAI/bge-small-en-v1.5',  -- pinned; query side must match
  notion_page_id  text,                           -- optional human-readable mirror
  ingested_at     timestamptz not null default now()
);

-- 3. doc_chunks (one row per chunk; carries the embedding) ------------
create table if not exists public.doc_chunks (
  id           uuid primary key default gen_random_uuid(),
  document_id  uuid not null references public.documents(id) on delete cascade,
  chunk_index  integer not null,
  content      text not null,
  embedding    vector(384) not null,             -- MUST match documents.embedding_model dims
  token_count  integer,
  locator      jsonb,                             -- {chapter, section, page} for citation
  created_at   timestamptz not null default now(),
  unique (document_id, chunk_index)
);

-- 4. ANN index on the embedding (HNSW, cosine) -----------------------
--    HNSW = better recall (PRD pre-mortem risk #1). If the free-tier build
--    is memory-tight, swap to the ivfflat line below and REINDEX.
create index if not exists doc_chunks_embedding_hnsw
  on public.doc_chunks using hnsw (embedding vector_cosine_ops);
-- ivfflat alternative (lighter; needs data present + a lists tuning):
-- create index if not exists doc_chunks_embedding_ivfflat
--   on public.doc_chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);

create index if not exists doc_chunks_document_id_idx
  on public.doc_chunks (document_id);

-- 5. Retrieval RPC (called over REST at query time) ------------------
--    Returns top-N chunks by cosine similarity, newest-model-agnostic.
--    similarity = 1 - cosine_distance  (higher = closer). Optional doc filter.
create or replace function public.match_doc_chunks (
  query_embedding    vector(384),
  match_count        int default 8,
  filter_document_id uuid default null
)
returns table (
  id           uuid,
  document_id  uuid,
  chunk_index  integer,
  content      text,
  locator      jsonb,
  similarity   float
)
language sql stable
as $$
  select
    c.id,
    c.document_id,
    c.chunk_index,
    c.content,
    c.locator,
    1 - (c.embedding <=> query_embedding) as similarity
  from public.doc_chunks c
  where filter_document_id is null or c.document_id = filter_document_id
  order by c.embedding <=> query_embedding
  limit match_count;
$$;

-- 6. Smoke-test helper (optional; run after apply, then delete rows) --
-- insert into public.documents (title, blob_key, sha256, embedding_model)
--   values ('__smoke__', 'x/x', 'smoke-sha', 'BAAI/bge-small-en-v1.5');
-- select id, title from public.documents where sha256 = 'smoke-sha';
-- delete from public.documents where sha256 = 'smoke-sha';   -- cascades to chunks
