-- =============================================================================
-- 0018 — lane_registry: activate the hiring_pulse lane (spec §2 lane 1 / §3.3)
-- Linear: YED-304 lane 1 (PR #271, ats_pulse.py) · Spec: docs/proposals/2026-11-04-market-lens-and-slices.md
--
-- WHAT: flips ONE seeded flag. 0016 seeded all six lanes with active = false (nothing ran yet);
-- the hiring_pulse producer (weekly Action, PR #271) is now built and its lane_run ledger rows
-- (PII-free, spine-guarded) go live with this flag. No column, grant, RLS or other lane row is
-- touched.
--
-- PRODUCERS CANNOT WRITE THE REGISTRY (ADR-13): lane_registry is write-refused for lane runs by
-- design — activation is a human-applied migration, exactly like this one. The workflow never
-- touches this table.
--
-- APPLY ORDER (per the twin-rehearsal rule, CLAUDE.md invariant 2):
--   1. Rehearse on the TWIN first (schema + this file + the VERIFY block below all green).
--   2. Then Alex applies it to prod from the dashboard.
--   3. Only after prod has the flag does the first scheduled Action run post a lane_run row to
--      prod that the freshness layer (#269) will watch for (freshness_fail_days = 14).
-- =============================================================================

begin;

-- 0016 style: a busy table fails the paste after 5s instead of holding the session open
-- (the paste retries cleanly — nothing has been written yet).
set local lock_timeout = '5s';

update public.lane_registry
   set active = true
 where lane = 'hiring_pulse';

-- In-transaction check: exactly 1 row must change. 0 means the hiring_pulse lane row is
-- missing (0016 not applied or seeded differently) — raise, and the transaction aborts with
-- nothing half-applied. A re-run after a successful apply still changes the row (UPDATE
-- counts it), so the check is re-run-safe.
do $$
declare
    changed integer;
begin
    get diagnostics changed = row_count;
    if changed <> 1 then
        raise exception '0018: expected exactly 1 lane_registry row to change, got %', changed;
    end if;
end $$;

commit;

-- =============================================================================
-- VERIFY (read-only, 0016 style). Run the VERIFY block with psql in a READ-ONLY session,
-- per the twin-rehearsal runbook. Each statement returns one row: <check name> | <t/f>.
-- Every row must be t.
-- =============================================================================
-- VERIFY:BEGIN
-- select 'hiring_pulse_active', (select active from public.lane_registry where lane = 'hiring_pulse');
-- select 'exactly_one_lane_active', (select count(*) = 1 from public.lane_registry where active);
-- select 'other_lanes_unchanged', not exists (select 1 from public.lane_registry where lane <> 'hiring_pulse' and active);
-- select 'registry_rowcount_unchanged', (select count(*) = 6 from public.lane_registry);
-- select 'hiring_pulse_contract_intact', (select schedule = 'weekly GitHub Action (Sunday)' and owner = 'alex' and consumer like 'Q2%' and freshness_flag_days = 7 and freshness_fail_days = 14 from public.lane_registry where lane = 'hiring_pulse');
-- select 'registry_rls_still_on', (select relrowsecurity from pg_class where oid = 'public.lane_registry'::regclass);
-- select 'registry_no_api_grants', not exists (select 1 from unnest(array['anon', 'authenticated']) r where has_table_privilege(r, 'public.lane_registry', 'select') or has_table_privilege(r, 'public.lane_registry', 'insert') or has_table_privilege(r, 'public.lane_registry', 'update') or has_table_privilege(r, 'public.lane_registry', 'delete'));
-- select 'lane_run_ledger_ready', (select count(*) = 10 from information_schema.columns where table_schema = 'public' and table_name = 'lane_run');
-- VERIFY:END

-- =============================================================================
-- ROLLBACK (0016 style — uncomment the block to run). Drops only what 0018 changes: the flag.
--
-- lane_run rows already written while the lane was active MAY STAY — they are the run ledger,
-- and the freshness layer (#269) reads history, not just the flag. Delete them only for a
-- clean-slate rehearsal.
--
-- ROLLBACK:BEGIN
-- update public.lane_registry set active = false where lane = 'hiring_pulse';
-- -- clean-slate rehearsal only (optional):
-- -- delete from public.lane_run where lane = 'hiring_pulse';
-- ROLLBACK:END
-- =============================================================================
