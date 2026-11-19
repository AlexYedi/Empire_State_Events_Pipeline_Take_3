-- =====================================================================
-- 0020 · public.feed_items — lane 4 raw-feed staging (YED-304 Phase C, lanes DDL)
--
-- NOT APPLIED. Twin rehearsal (supabase/scripts/rehearse_0020.py) + Alex
-- dashboard apply required (CLAUDE.md invariant 2). Merge gate for PRs #270/#272.
--
-- WHY. Lane 4 (company feeds, market-lens design #268 §6 lane 4) has its producer
-- built (feeds.py fetch CLI + Action, PR #272) and its classifier contract built
-- (feed_classifier.py JSON schema + validator, PR #270) — but no table to stage
-- into: `spine_client.ALLOW['feed_items']` names columns for a table that does not
-- exist, and feeds.py holds its write until this migration lands. This file creates
-- public.feed_items and nothing else.
--
-- ROW CONTRACT = feeds.py `to_row()` / `stage_rows()` (PR #272), which stages
-- exactly the columns `spine_client.ALLOW['feed_items']` allows:
--   source_key          sha256 of the canonical item URL (feeds.py item_key) — the
--                       dedup key; weekly reruns upsert on_conflict=source_key.
--   company             registry company name (link-to-existing; never a free-form entity).
--   feed_url / url / title / summary   the item fields as the producer redacted them:
--                       every string value passes spine's EMAIL_RE/PHONE_RE (feeds.py
--                       redact()); the summary additionally passes substrate.redact_body
--                       (to_row, PR #272). The spine guard re-checks per row and
--                       quarantines failures by sha256 key. The DB performs NO PII
--                       validation on this table: the DB-side backstop
--                       (docs/adr/proposals/pii-db-check.sql, its regexes pinned to
--                       the spine's by check_pii_regex_parity.py) is person-only by
--                       scope; extending it to feed_items is Alex's call.
--   published           item publish time (ISO-8601 from the feed), nullable.
--   kind                the staged item's kind per the ADOPTED #270 matrix (Alex,
--                       2026-11-05, adopted as-is): launch | market — feeds.py classify()
--                       (#272 head 30f327b). launch-flavored items (product/GA announcements)
--                       stage kind=launch with a NULL signal_type_guess; market items stage
--                       kind=market with a required signal_type_guess. The feed FORMAT
--                       (rss/atom/youtube) is NOT kind — it lives in metadata.source_format.
--                       Classified launch/market *events* are separate `event` rows (0009).
--   signal_type_guess   feeds.py's deterministic keyword guess — one of the five market
--                       signals, or NULL for launch-flavored items, per the ADOPTED
--                       mapping (Alex, 2026-11-05): kind=launch ⇒ signal_type null;
--                       kind=market ⇒ signal_type required. The guess is a hint only —
--                       the schema-validated classifier (#270, EVENT_CANDIDATE_FLOOR
--                       = 0.6) stays authoritative in the Monday session.
--   fetched_at          when the Action fetched the batch.
--   metadata            jsonb, free-form provenance ({canonical_url, source_format} today —
--                       source_format is the feed format the item was parsed from).
--
-- NOTHING SEEDED. The table ships empty; the first fetch run stages the first rows.
--
-- SECURITY MODEL (0016 pattern): `public`, RLS enabled, no policies, all privileges
-- revoked from public/anon/authenticated. The REVOKE is the SELECT control on this
-- table: 0019 revoked WRITES only and deliberately left the default SELECT grant for
-- new tables in place (0019 "WHAT IS NOT CHANGED" — an open question for Alex), so
-- WITHOUT this REVOKE anon/authenticated could read the table. It is idempotent, so
-- re-pasting is safe. RLS deny-by-default (no policies) backs it up for direct SQL;
-- the service-role REST path through spine_client — which bypasses RLS and keeps its
-- grants — is the only writer.
--
-- RE-RUNNABLE: every DDL statement is guarded (if not exists / no-op REVOKE); a second
-- paste is a no-op.
--
-- APPLY (Alex, prod dashboard): paste OUTSIDE the 07:00–09:00 UTC nightly window
-- (relevance recompute + MI health check). lock_timeout is set inside the transaction,
-- so a busy table fails the paste in 5s instead of queueing — just re-paste.
-- VERIFY (Alex, after apply): run the VERIFY block with psql in a READ-ONLY session,
-- per the twin-rehearsal runbook (the dashboard SQL editor shows only the last
-- statement's result). Every row must be t.
-- =====================================================================

begin;
set local lock_timeout = '5s';

-- ---------------------------------------------------------------------
-- 1. The table. uuid PK per repo convention (0009/0016); producers never
--    set item_id — source_key is the dedup key.
-- ---------------------------------------------------------------------
create table if not exists public.feed_items (
  item_id           uuid primary key default gen_random_uuid(),
  source_key        text not null unique
                      check (source_key ~ '^[0-9a-f]{64}$'),
  company           text not null,
  feed_url          text not null,
  url               text not null,
  title             text not null default '',
  published         timestamptz,
  summary           text not null default '',
  kind              text not null
                      check (kind in ('launch', 'market')),
  signal_type_guess text
                      check (signal_type_guess is null or
                             signal_type_guess in
                             ('news', 'partnership', 'layoff', 'paper', 'model_release')),
  fetched_at        timestamptz not null,
  metadata          jsonb not null default '{}'::jsonb,
  created_at        timestamptz not null default now(),
  -- Table-level (it references two columns — a column constraint would lie about
  -- scope): the ADOPTED #270 matrix, enforced at the DB.
  constraint feed_items_signal_mapping_check
  check ((kind = 'launch' and signal_type_guess is null) or
         (kind = 'market' and signal_type_guess is not null))
);

comment on table public.feed_items is
  'YED-304 lane 4: raw (redacted) company-feed items staged by the weekly feeds.py Action, '
  'deduped on source_key = sha256(canonical item url). Staging only: the Monday-session '
  'classifier (#270) turns candidates into schema-validated launch/market event rows; '
  'signal_type_guess is a keyword hint, never authoritative. PII was scrubbed before staging '
  '(spine dialect); this table must never hold contact PII (ADR-9).';

comment on column public.feed_items.signal_type_guess is
  'Keyword guess over the five market signals (news/partnership/layoff/paper/model_release); '
  'NULL for launch-flavored items — adopted mapping 2026-11-05: launch ⇒ signal_type null, '
  'market ⇒ signal_type required. Authoritative classification happens in the Monday session.';

-- Dedup upserts (on_conflict=source_key) and the two read shapes the lane needs:
-- per-company digest (Monday brief) and freshness windows (lane health).
create index if not exists feed_items_company_idx on public.feed_items (company);
create index if not exists feed_items_fetched_at_idx on public.feed_items (fetched_at desc);

-- ---------------------------------------------------------------------
-- 2. Security: RLS on, no policies, no API-role or PUBLIC grants
--    (0016 pattern; idempotent — a REVOKE of an unheld privilege is a no-op).
-- ---------------------------------------------------------------------
alter table public.feed_items enable row level security;

revoke all on public.feed_items from public, anon, authenticated;

commit;

-- =====================================================================
-- VERIFY (read-only, 0016 style). Run the VERIFY block with psql in a READ-ONLY session,
-- per the twin-rehearsal runbook. Each statement returns one row: <check name> | <t/f>.
-- Every row must be t.
-- =====================================================================
-- VERIFY:BEGIN
-- select 'feed_items_exists', to_regclass('public.feed_items') is not null;
-- select 'feed_items_no_rows', (select count(*) = 0 from public.feed_items);
-- select 'feed_items_column_order', (select string_agg(column_name, ',' order by ordinal_position) = 'item_id,source_key,company,feed_url,url,title,published,summary,kind,signal_type_guess,fetched_at,metadata,created_at' from information_schema.columns where table_schema = 'public' and table_name = 'feed_items');
-- select 'feed_items_source_key_64hex', (select pg_get_constraintdef(oid) = 'CHECK ((source_key ~ ''^[0-9a-f]{64}$''::text))' from pg_constraint where conrelid = 'public.feed_items'::regclass and contype = 'c' and conname = 'feed_items_source_key_check');
-- select 'feed_items_source_key_unique', exists (select 1 from pg_indexes where schemaname = 'public' and tablename = 'feed_items' and indexdef ~* 'unique.*source_key');
-- select 'feed_items_kind_vocab', (select pg_get_constraintdef(oid) = 'CHECK ((kind = ANY (ARRAY[''launch''::text, ''market''::text])))' from pg_constraint where conrelid = 'public.feed_items'::regclass and contype = 'c' and conname = 'feed_items_kind_check');
-- select 'feed_items_signal_vocab', (select pg_get_constraintdef(oid) = 'CHECK (((signal_type_guess IS NULL) OR (signal_type_guess = ANY (ARRAY[''news''::text, ''partnership''::text, ''layoff''::text, ''paper''::text, ''model_release''::text]))))' from pg_constraint where conrelid = 'public.feed_items'::regclass and contype = 'c' and conname = 'feed_items_signal_type_guess_check');
-- select 'feed_items_signal_mapping', (select pg_get_constraintdef(oid) = 'CHECK ((((kind = ''launch''::text) AND (signal_type_guess IS NULL)) OR ((kind = ''market''::text) AND (signal_type_guess IS NOT NULL))))' from pg_constraint where conrelid = 'public.feed_items'::regclass and contype = 'c' and conname = 'feed_items_signal_mapping_check');
-- select 'feed_items_service_role_rw', (select has_table_privilege('service_role', 'public.feed_items', 'select') and has_table_privilege('service_role', 'public.feed_items', 'insert') and has_table_privilege('service_role', 'public.feed_items', 'update') and has_table_privilege('service_role', 'public.feed_items', 'delete'));
-- select 'feed_items_guess_nullable_launch_null', (select is_nullable = 'YES' from information_schema.columns where table_schema = 'public' and table_name = 'feed_items' and column_name = 'signal_type_guess');
-- select 'feed_items_rls_on', (select relrowsecurity from pg_class where oid = 'public.feed_items'::regclass);
-- select 'feed_items_no_policies', not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'feed_items');
-- select 'feed_items_no_api_grants', not exists (select 1 from unnest(array['anon', 'authenticated']) r where has_table_privilege(r, 'public.feed_items', 'select') or has_table_privilege(r, 'public.feed_items', 'insert') or has_table_privilege(r, 'public.feed_items', 'update') or has_table_privilege(r, 'public.feed_items', 'delete') or has_table_privilege(r, 'public.feed_items', 'truncate') or has_table_privilege(r, 'public.feed_items', 'references') or has_table_privilege(r, 'public.feed_items', 'trigger') or has_table_privilege(r, 'public.feed_items', 'maintain'));
-- select 'feed_items_no_pii_columns', not exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'feed_items' and column_name ~* '(e_?mail|phone|mobile|telephone|contact|address|linkedin)');
-- VERIFY:END
--
-- =====================================================================
-- ROLLBACK (uncomment to run). Drops only what 0020 creates: the table
-- (its three indexes go with it). No other object is touched.
--
-- ROLLBACK:BEGIN
-- drop table if exists public.feed_items;
-- ROLLBACK:END
-- =====================================================================
