-- =====================================================================
-- YED-157 — Doc-KB Phase B, story B1 (ADDITIVE ONLY)
-- Project: Supabase `empire state ai` — ref oicikjyzmxqfomrrqkvf  (NOT any other project)
-- Apply ONCE via the empire state ai SQL Editor, AFTER doc-kb-migration-a5.sql.
--
-- Adds: the 'reference' event kind, and the doc_claims STAGING table.
-- Staging is the core design move: extracted claims are candidates — private,
-- reversible, and invisible to the graph until Alex approves them at the
-- /doc-digest gate. Only approved claims are promoted to `event`.
-- =====================================================================

-- 1. allow kind='reference' -------------------------------------------
--    The live constraint `event_kind_enum` currently allows exactly these 8
--    (verified empirically 2026-09-11 by probing each value). This ADDS one;
--    widening a CHECK re-validates existing rows, so it fails loudly if wrong.
--    NOTE: this constraint exists in the live DB but was missing from
--    .claude/references/market-intel-schema.sql — drift, now documented.
alter table public.event drop constraint if exists event_kind_enum;
alter table public.event add constraint event_kind_enum check (kind in (
  'attended', 'market', 'funding', 'launch', 'exec_move',
  'role_posted', 'application', 'interview',
  'reference'                                    -- NEW: doc-derived, secondhand
));

-- 2. doc_claims — the staging table ------------------------------------
create table if not exists public.doc_claims (
  id                 uuid primary key default gen_random_uuid(),
  document_sha256    text not null,          -- keyed on sha256, NOT documents.id, so an
                                             -- A.5 second-profile copy extracts nothing new
  claim_key          text not null,          -- sha256(normalized claim text)
  claim_text         text not null,
  claim_type         text,                   -- thesis | definition | statistic | practice | prediction
  locator            jsonb,                  -- {section|page} — the citation
  quote              text,                   -- <= 25 words (licensing guard)
  proposed_entities  jsonb default '[]',     -- [{type:topic|company, name, existing_id|null}]
  confidence         numeric,                -- extractor self-score; capped at 0.6 on promotion
  extractor          text not null default 'gemini',   -- gemini | manual | claude
  extractor_model    text,
  lane               text,                   -- A graph | B content | C glossary | D recommend
  status             text not null default 'candidate'
                       check (status in ('candidate', 'approved', 'rejected')),
  promoted_event_id  uuid references public.event(id) on delete set null,
  created_at         timestamptz not null default now(),
  reviewed_at        timestamptz,
  unique (document_sha256, claim_key)        -- extraction is upsert-ignore => idempotent
);
create index if not exists doc_claims_status_idx   on public.doc_claims (status);
create index if not exists doc_claims_sha_idx      on public.doc_claims (document_sha256);

-- 3. promotion idempotency: one event per claim ------------------------
create unique index if not exists event_claim_key_uq
  on public.event ((metadata->>'claim_key'))
  where metadata ? 'claim_key';

-- 4. security: service-key only (matches the doc-KB tables) ------------
alter table public.doc_claims enable row level security;

-- 5. Verify (optional) -------------------------------------------------
-- select count(*) from public.doc_claims;                                  -- expect 0
-- select conname from pg_constraint where conname = 'event_kind_enum';     -- expect 1 row
