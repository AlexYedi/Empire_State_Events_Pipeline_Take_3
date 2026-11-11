-- =============================================================================
-- 0021 — lane_registry: re-describe the company_signals lane (lane 2) as built
-- Linear: YED-349 · Decision: Alex, 2026-11-08 ("$0 stack + Clay")
-- Evidence: docs/bakeoff/2026-11-05-lane2/README.md (run 1 + run 1b) · design:
-- docs/proposals/2026-11-05-company-signals-lane-stack.md · producer: .claude/scripts/company_signals.py
--
-- WHAT: rewrites schedule and kill_rule on ONE seeded row. 0016 seeded company_signals as
-- "weekly, Monday session (akta MCP); credit cap per run"; the lane is now a weekly GitHub Action
-- (GDELT + HN, + EDGAR once a declared User-Agent exists) plus a Clay research-agent leg every
-- second Monday session, with company RSS left to lane 4 (feeds). consumer ('Q2-Q6; Monday Market
-- Brief'), owner and the freshness thresholds are unchanged. No column, grant, RLS or other lane
-- row is touched.
--
-- NOT ACTIVATED HERE: active stays false. The nightly healthcheck (#284) FAILs an ACTIVE lane
-- with no successful/partial lane_run row, so activation waits for the first good run.
-- FOLLOW-UP (next free migration number; 0022 is taken by the graph phase-1 schema): flip active = true for company_signals (0018's shape) after the first
-- 'success' or 'partial' company_signals lane_run row lands on prod.
--
-- PRODUCERS CANNOT WRITE THE REGISTRY (ADR-13): lane_registry is not in spine_client.ALLOW;
-- every registry change ships as a human-applied migration, like this one.
--
-- APPLY ORDER (twin-rehearsal rule, CLAUDE.md invariant 2):
--   1. Rehearse on the TWIN first (this file + the VERIFY block below all t).
--   2. Alex pastes it on prod, OUTSIDE the 07:00–09:00 UTC nightly window.
-- =============================================================================

begin;

-- 0016 style: a busy table fails the paste after 5s instead of holding the session open.
set local lock_timeout = '5s';

-- The UPDATE runs INSIDE the DO block so GET DIAGNOSTICS sees its row count (0018's lesson: a
-- separate DO after a top-level UPDATE always reads 0). Exactly 1 row must change; 0 means the
-- company_signals seed is missing — raise, and nothing is half-applied. Re-run-safe: a second
-- paste sets the same values again (still 1 row) and passes. Both strings fit the 0016 length
-- checks (schedule <= 200, kill_rule <= 300).
do $$
declare
    changed integer;
begin
    update public.lane_registry
       set schedule  = 'weekly GitHub Action (Sunday): GDELT + HN (+ EDGAR); Clay research agent every 2nd Monday session; company RSS via lane 4',
           kill_rule = 'items_written = 0 for 3 runs -> FAIL; Clay over ~70 credits per run -> pause the Clay leg; <60% watchlist coverage at 90 days -> widen sources before widening the list'
     where lane = 'company_signals';
    get diagnostics changed = row_count;
    if changed <> 1 then
        raise exception '0021: expected exactly 1 lane_registry row to change, got %', changed;
    end if;
end $$;

commit;

-- =============================================================================
-- VERIFY (read-only, 0016 style). Run the VERIFY block with psql in a READ-ONLY session,
-- per the twin-rehearsal runbook. Each statement returns one row: <check name> | <t/f>.
-- Every row must be t.
-- =============================================================================
-- VERIFY:BEGIN
-- select 'company_signals_schedule', (select schedule = 'weekly GitHub Action (Sunday): GDELT + HN (+ EDGAR); Clay research agent every 2nd Monday session; company RSS via lane 4' from public.lane_registry where lane = 'company_signals');
-- select 'company_signals_kill_rule', (select kill_rule = 'items_written = 0 for 3 runs -> FAIL; Clay over ~70 credits per run -> pause the Clay leg; <60% watchlist coverage at 90 days -> widen sources before widening the list' from public.lane_registry where lane = 'company_signals');
-- select 'company_signals_still_inactive', (select not active from public.lane_registry where lane = 'company_signals');
-- select 'company_signals_contract_intact', (select owner = 'alex' and consumer = 'Q2-Q6; Monday Market Brief' and freshness_flag_days = 7 and freshness_fail_days = 14 from public.lane_registry where lane = 'company_signals');
-- select 'other_lanes_untouched', (select schedule = 'weekly GitHub Action (Sunday)' from public.lane_registry where lane = 'hiring_pulse');
-- select 'registry_original_six_present', (select count(*) = 6 from public.lane_registry where lane in ('corpus_mine', 'hiring_pulse', 'company_signals', 'research_frontier', 'feeds', 'segment_enrichment'));  -- names its lanes, so later migrations (0022 adds 4 rows) don't turn this red
-- select 'registry_rls_still_on', (select relrowsecurity from pg_class where oid = 'public.lane_registry'::regclass);
-- select 'registry_no_api_grants', not exists (select 1 from unnest(array['anon', 'authenticated']) r where has_table_privilege(r, 'public.lane_registry', 'select') or has_table_privilege(r, 'public.lane_registry', 'insert') or has_table_privilege(r, 'public.lane_registry', 'update') or has_table_privilege(r, 'public.lane_registry', 'delete'));
-- VERIFY:END

-- =============================================================================
-- ROLLBACK (0016 style — uncomment the block to run). Restores the 0016 seed text for the two
-- columns 0021 changes; nothing else.
--
-- ROLLBACK:BEGIN
-- update public.lane_registry
--    set schedule  = 'weekly, Monday session (akta MCP); credit cap per run',
--        kill_rule = 'over the credit cap Alex set -> pause; <60% watchlist coverage at 90 days -> widen sources before widening the list'
--  where lane = 'company_signals';
-- ROLLBACK:END
-- =============================================================================
