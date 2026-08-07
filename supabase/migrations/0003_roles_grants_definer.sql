-- 0003_roles_grants_definer.sql
-- MI data-layer consolidation — Increment 1 (YED-130 / ADR-1). WRITE-PATH HARDENING.
-- =============================================================================
-- ADDITIVE ONLY. Creates a scoped `pipeline_writer` role, grants it ONLY what the
-- ingestion pipeline needs on `public`, REVOKES it from the intelligence schemas, and
-- defines the SECURITY DEFINER function pattern as the ONLY write path into
-- topic_intelligence. ZERO DML/DDL against `public` DATA — this migration only touches
-- GRANTS on `public` tables (privileges, not rows/columns) and objects in the two new
-- schemas. `public` table shapes and rows are untouched.
--
-- ############################################################################
-- ## RLS IS NOT A CONTROL AGAINST THE service_role / sb_secret KEY.          ##
-- ##                                                                          ##
-- ## Empire's pipeline currently authenticates as `service_role` via the      ##
-- ## `sb_secret` key, which BYPASSES Row-Level Security entirely. Therefore   ##
-- ## RLS deny-all on topic_intelligence is NOT what keeps the pipeline out of  ##
-- ## the intelligence schema. Enforcement here is ROLES + GRANTS + SECURITY   ##
-- ## DEFINER, not RLS:                                                         ##
-- ##   - a scoped `pipeline_writer` role with grants ONLY on the public tables  ##
-- ##     it must write;                                                        ##
-- ##   - REVOKE ALL on topic_intelligence + signal_read from pipeline_writer;   ##
-- ##   - the ONLY write into topic_intelligence is via SECURITY DEFINER        ##
-- ##     functions owned by a privileged role (EXECUTE granted; direct DML     ##
-- ##     revoked).                                                             ##
-- ##                                                                          ##
-- ## ACTION REQUIRED (ops): the pipeline MUST STOP using the sb_secret          ##
-- ## service key for routine writes and connect as `pipeline_writer` instead.  ##
-- ## While it keeps using sb_secret/service_role, every control below is       ##
-- ## advisory only — service_role bypasses all of it.                          ##
-- ############################################################################
-- =============================================================================

begin;

-- -----------------------------------------------------------------------------
-- 1. Scoped write role. CREATE ROLE has no IF NOT EXISTS -> guard with a DO block.
--    NOLOGIN group role: the pipeline's actual login role is GRANTed pipeline_writer,
--    or (Supabase) a dedicated login user is created out-of-band and granted this role.
-- -----------------------------------------------------------------------------
do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'pipeline_writer') then
    create role pipeline_writer nologin;
  end if;
end
$$;

-- -----------------------------------------------------------------------------
-- 2. Grant ONLY what the ingestion pipeline needs on `public`.
--    Ingestion upserts dimension/hyperedge rows; it does not DELETE. No sequence
--    grants needed (all PKs default gen_random_uuid()).
-- -----------------------------------------------------------------------------
grant usage on schema public to pipeline_writer;
grant select, insert, update on
  public.company,
  public.person,
  public.topic,
  public.event,
  public.event_entity
to pipeline_writer;

-- -----------------------------------------------------------------------------
-- 3. REVOKE the intelligence schemas from pipeline_writer (both schema + objects).
--    pipeline_writer must never touch topic_intelligence or signal_read directly.
-- -----------------------------------------------------------------------------
revoke all on schema topic_intelligence from pipeline_writer;
revoke all on all tables    in schema topic_intelligence from pipeline_writer;
revoke all on all sequences in schema topic_intelligence from pipeline_writer;
revoke all on all functions in schema topic_intelligence from pipeline_writer;

revoke all on schema signal_read from pipeline_writer;
revoke all on all tables    in schema signal_read from pipeline_writer;
revoke all on all functions in schema signal_read from pipeline_writer;

-- Also revoke the PUBLIC pseudo-role's default EXECUTE on new functions in the
-- intelligence schema, so EXECUTE is grant-only (see the definer function below).
alter default privileges in schema topic_intelligence revoke execute on functions from public;

-- -----------------------------------------------------------------------------
-- 4. SECURITY DEFINER write-path PATTERN — the ONLY way pipeline_writer may write
--    into topic_intelligence. Owned by a privileged role (the migration runner /
--    table owner, e.g. postgres). Runs with the owner's rights, so it can INSERT even
--    though pipeline_writer has REVOKE ALL on the schema. `set search_path` pins name
--    resolution (security best practice for SECURITY DEFINER — prevents search_path
--    hijacking). EXECUTE granted to pipeline_writer; direct DML stays revoked.
--
--    This is a representative pattern (one table). Increment 2's live recompute adds
--    sibling definer functions (e.g. reload_topic_pair_metric) following the same mould;
--    the nightly compute is ported here as a definer function, never as direct DML.
-- -----------------------------------------------------------------------------
create or replace function topic_intelligence.upsert_topic_trend(
  p_subject_level          text,
  p_subject_id             uuid,
  p_window_type            text,
  p_as_of_date             date,
  p_event_count            int,
  p_distinct_speaker_count int,
  p_prior_event_count      int,
  p_momentum               numeric,
  p_trend_label            text,
  p_is_low_confidence      boolean,
  p_content_hash           text,
  p_ingestion_run_id       uuid
) returns uuid
language plpgsql
security definer
set search_path = topic_intelligence, pg_temp
as $fn$
declare
  v_trend_id uuid;
begin
  insert into topic_intelligence.topic_trend (
    subject_level, subject_id, window_type, as_of_date,
    event_count, distinct_speaker_count, prior_event_count, momentum,
    trend_label, is_low_confidence, source, content_hash, ingestion_run_id)
  values (
    p_subject_level, p_subject_id, p_window_type, p_as_of_date,
    p_event_count, p_distinct_speaker_count, p_prior_event_count, p_momentum,
    p_trend_label, p_is_low_confidence, 'computed', p_content_hash, p_ingestion_run_id)
  on conflict (subject_level, subject_id, window_type, as_of_date)
  do update set
    event_count            = excluded.event_count,
    distinct_speaker_count = excluded.distinct_speaker_count,
    prior_event_count      = excluded.prior_event_count,
    momentum               = excluded.momentum,
    trend_label            = excluded.trend_label,
    is_low_confidence      = excluded.is_low_confidence,
    content_hash           = excluded.content_hash,
    ingestion_run_id       = excluded.ingestion_run_id
  returning trend_id into v_trend_id;
  return v_trend_id;
end
$fn$;

-- EXECUTE is the ONLY intelligence-schema privilege pipeline_writer receives. It cannot
-- SELECT/INSERT/UPDATE the base tables directly (revoked in step 3); it may only call
-- this vetted definer function, which enforces the write shape.
revoke all on function topic_intelligence.upsert_topic_trend(
  text, uuid, text, date, int, int, int, numeric, text, boolean, text, uuid) from public;
grant execute on function topic_intelligence.upsert_topic_trend(
  text, uuid, text, date, int, int, int, numeric, text, boolean, text, uuid) to pipeline_writer;

commit;

-- =============================================================================
-- CONFIG NOTE (NOT SQL — apply in the Supabase dashboard, in a low-traffic window):
--
--   Data API "Exposed schemas" (Postgres setting `pgrst.db_schemas`) MUST be set to:
--       public, signal_read
--   i.e. ADD `signal_read`, do NOT add `topic_intelligence`.
--
--   - `public`      — Empire's existing surface (unchanged; already exposed).
--   - `signal_read` — the anon-safe, security_invoker, k>=5 views (0002).
--   - topic_intelligence is DELIBERATELY EXCLUDED so there is no direct PostgREST path
--     to the base intelligence tables (defense-in-depth on top of RLS + grants).
--
--   exposed-schemas is a PROJECT-WIDE setting (pre-mortem #5) — changing it touches
--   empire-state-hub's live `public` surface too. Apply in a low-traffic window and run
--   get_advisors on the branch first (APPLY.md steps (d)+(e)).
--
--   TRANSIENT EXCEPTION for the one-time carry-forward load: the Python loader
--   (carry_forward_topic_intelligence.py) writes via PostgREST with
--   `Content-Profile: topic_intelligence`, which requires topic_intelligence to be in
--   the exposed list FOR THE DURATION OF THE LOAD ONLY. Sequence in APPLY.md:
--       expose `public, signal_read, topic_intelligence` -> run loader -> validate ->
--       set final `public, signal_read`.
--   Anon stays safe throughout: even while transiently exposed, anon has no grant on
--   topic_intelligence.topics and RLS/grants restrict the other three to counts via views.
--   (Alternative if you prefer never to expose it: run the loader over psql/COPY instead
--    of PostgREST — see APPLY.md.)
-- =============================================================================

-- Rollback:
--   drop function if exists topic_intelligence.upsert_topic_trend(
--     text, uuid, text, date, int, int, int, numeric, text, boolean, text, uuid);
--   -- revoke the public grants and drop role if unused:
--   revoke all on public.company, public.person, public.topic, public.event,
--     public.event_entity from pipeline_writer;
--   drop role if exists pipeline_writer;   -- only if no login role depends on it
--   -- revert Data API exposed-schemas to `public` (remove signal_read).
