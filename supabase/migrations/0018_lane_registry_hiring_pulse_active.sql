-- =============================================================================
-- 0018 — lane_registry: activate the hiring_pulse lane (spec §2 lane 1 / §3.3)
-- Linear: YED-304 lane 1 (PR #271, ats_pulse.py) · Spec: docs/proposals/2026-11-04-market-lens-and-slices.md
--
-- WHAT: flips ONE seeded flag. 0016 seeded all six lanes with active = false (nothing ran yet);
-- the hiring_pulse producer (weekly Action, PR #271) is now built and its lane_run ledger writes
-- go live with this flag. No column, grant, RLS or other lane row is touched.
--
-- PRODUCERS CANNOT WRITE THE REGISTRY (ADR-13): lane_registry is write-refused for lane runs by
-- design — activation is a human-applied migration, exactly like this one. The workflow never
-- touches this table.
--
-- APPLY ORDER (per the twin-rehearsal rule, CLAUDE.md invariant 2):
--   1. Rehearse on the TWIN first (schema + this file + the VERIFY block below all green).
--   2. Then Alex applies it to prod from the dashboard.
--   3. Only after prod has the flag does the first scheduled Action run post a lane_run row to
--      the twin that the freshness layer (#269) will watch for (freshness_fail_days = 14).
-- =============================================================================

begin;

update public.lane_registry
   set active = true
 where lane = 'hiring_pulse';

commit;

-- =============================================================================
-- VERIFY (read-only). Each statement returns one row: <check name> | <t/f>. Every row must be t.
-- One check per statement, one line each.
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
-- ROLLBACK (the twin-rehearsal leg, or any post-prod reversal): re-deactivate the lane.
--
--   update public.lane_registry set active = false where lane = 'hiring_pulse';
--
-- lane_run rows already written while the lane was active MAY STAY — they are the run ledger,
-- and the freshness layer (#269) reads history, not just the flag. Delete them only for a
-- clean-slate rehearsal:
--
--   delete from public.lane_run where lane = 'hiring_pulse';
--
-- No other rollback is needed: this file changes one boolean on one row.
-- =============================================================================
