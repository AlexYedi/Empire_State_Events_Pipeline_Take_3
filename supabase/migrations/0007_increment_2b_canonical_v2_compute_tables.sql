-- 0007 — Increment 2b, part 3: canonical_v2 compute OUTPUT tables
-- Spec: supabase/specs/2b_relations_to_event_entity_mapping.md (§4) · Linear: YED-130
--
-- WHAT: the tables the rewritten compute writes into — ingestion_run (run bookkeeping),
--   topic_trend (theme trajectory), topic_pair_metric (theme-pair co-occurrence + bridges).
--   Structure copied verbatim (LIKE ... INCLUDING ALL) from the Increment-1 snapshot in
--   topic_intelligence, so grain / unique indexes / checks / content_hash discipline are
--   byte-identical to what signal_read already consumes — the atomic swap just repoints the
--   views from topic_intelligence.* to canonical_v2.*.
--
-- ⚠️ GATED: canonical_v2 only. Phantom Test Case DB rehearsal, then prod at cutover. RLS deny-all.

begin;

-- run bookkeeping (compute inserts a 'running' row, flips to 'success')
create table if not exists canonical_v2.ingestion_run
  (like topic_intelligence.ingestion_run including all);
alter table canonical_v2.ingestion_run enable row level security;

-- theme trajectory (one (subject, window, as_of_date) snapshot)
create table if not exists canonical_v2.topic_trend
  (like topic_intelligence.topic_trend including all);
alter table canonical_v2.topic_trend enable row level security;

-- theme-pair co-occurrence (shared events) + bridges (shared speakers)
create table if not exists canonical_v2.topic_pair_metric
  (like topic_intelligence.topic_pair_metric including all);
alter table canonical_v2.topic_pair_metric enable row level security;

commit;

-- Rollback (pre-swap): drop schema canonical_v2 cascade;  (public untouched by construction)
