-- =============================================================================
-- 0018 — lane_registry: activate the hiring_pulse lane (spec §2 lane 1 / §3.3)
-- Linear: YED-304 lane 1 (PR #271, ats_pulse.py) · Spec: docs/proposals/2026-11-04-market-lens-and-slices.md
--
-- WHAT: flips ONE seeded flag. 0016 seeded all six lanes with active = false (nothing ran yet);
-- the hiring_pulse producer (weekly Action, PR #271) is now built and ledgers each run to prod
-- lane_run; this flag marks the lane live for the freshness layer. No column, grant, RLS or other
-- lane row is touched.
--
-- PRODUCERS CANNOT WRITE THE REGISTRY (ADR-13): lane_registry is write-refused for lane runs by
-- design — activation is a human-applied migration, exactly like this one. The workflow never
-- touches this table.
--
-- STATUS: NOT APPLIED. Alex applies it after a twin rehearsal.
--
-- APPLY ORDER (per the twin-rehearsal rule, CLAUDE.md invariant 2):
--   1. Rehearse on the TWIN first (schema + this file + the VERIFY block below all green, then
--      the ROLLBACK block, then re-apply).
--   2. Then Alex applies it to prod from the dashboard, outside the 07:00–09:00 UTC nightly
--      window. lock_timeout = 5s: a busy table makes the paste fail fast; just re-paste.
--   3. The weekly Action writes its lane_run row to PROD through spine_client's guard (the FK
--      only needs the seeded registry row); this flag is what tells the freshness layer (#269)
--      to start watching that history (freshness_fail_days = 14).
--
-- SAFETY: the update runs inside a DO block that asserts exactly ONE row matched; 0 (the 0016
--   seed is missing) or >1 raises and the whole transaction rolls back. The update does not
--   filter on active, so a second paste matches the same one row again and is a no-op.
-- =============================================================================

begin;
set local lock_timeout = '5s';

do $$
declare
  n integer;
begin
  update public.lane_registry
     set active = true
   where lane = 'hiring_pulse';
  get diagnostics n = row_count;
  if n <> 1 then
    raise exception '0018: expected exactly 1 lane_registry row for hiring_pulse, updated %', n;
  end if;
end
$$;

commit;

-- =============================================================================
-- VERIFY (read-only). Each statement returns one row: <check name> | <t/f>. Every row must be t.
-- The rehearsal harness parses the block between the markers; keep one check per statement, one line each.
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
-- The rehearsal harness parses the block between the markers.
-- =============================================================================
-- ROLLBACK:BEGIN
-- begin;
-- set local lock_timeout = '5s';
-- update public.lane_registry set active = false where lane = 'hiring_pulse';
-- commit;
-- ROLLBACK:END
--
-- lane_run rows already written MAY STAY: they are the run ledger, and the freshness layer
-- (#269) reads history, not just the flag. Delete them only for a clean-slate TWIN rehearsal
-- (deliberately outside the parsed block):
--
--   delete from public.lane_run where lane = 'hiring_pulse';
--
-- No other rollback is needed: this file changes one boolean on one row.
