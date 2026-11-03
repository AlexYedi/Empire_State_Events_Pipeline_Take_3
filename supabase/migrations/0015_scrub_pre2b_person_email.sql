-- 0015_scrub_pre2b_person_email.sql
-- YED-296 (S-04 follow-up): remove the legacy `email` column, and the one value it
-- still holds, from pre2b.person, the parked pre-2B original of the person table.
-- =============================================================================
-- WHY
--   ADR-9 / CLAUDE.md invariant 1: email never enters the Supabase spine. The
--   2026-11-02 post-apply audit of S-04 D1 scanned every non-system schema for
--   forbidden-name columns and found pre2b.person.email with 1 populated row.
--   The Phase-2 backstop (pii-db-check.sql) covers only public.person and
--   canonical_v2.person, so this table was outside its reach. It was not
--   exposed: RLS on with 0 policies, anon has no USAGE on schema pre2b, and
--   pre2b is not an API-exposed schema.
--
-- WHY SCRUB, NOT DROP
--   pre2b is the 2B rollback store (supabase/staging/2b_rollback.sql moves
--   these tables back), and live FK topic_intelligence.topics_cluster_id_fkey
--   references pre2b.topic_cluster. Dropping the schema would destroy the 2B
--   rollback and break that FK. Dropping just this column keeps the rollback
--   intact, and if 2B is ever rolled back, public.person comes back without
--   email, which matches the post-0014 state.
--
-- WHY NULL BEFORE DROP
--   ALTER TABLE ... DROP COLUMN only marks the attribute dropped: the bytes stay
--   in the heap tuples until those rows are rewritten. The UPDATE writes new
--   tuples without the value, the DROP removes the column, and the separate
--   VACUUM FULL (step 2; it cannot run inside a transaction block) rewrites the
--   table so the dead tuples holding the old value are physically gone.
--   Supabase point-in-time backups keep the old value until their retention
--   window expires; nothing in-database can change that.
--
-- SAFETY
--   - 0 dependents on pre2b.person.email (pg_depend, 2026-11-02). No index on it.
--   - pre2b.person has only person_set_updated_at (an updated_at trigger). The
--     UPDATE bumps updated_at on the one row, and nothing reads that.
--   - Idempotent: the block runs only while the column exists, so a re-run is
--     a notice, not an error.
--   - Irreversible by design: the value is not restored. HubSpot is the home
--     for contact detail.
--
-- APPLY (Alex, dashboard SQL editor, The-Prod-Brain), after the twin rehearsal:
--   Step 1: run the DO block below. It is one statement, so one transaction.
--   Step 2: run `vacuum full pre2b.person;` on its own.

-- Guarded so a re-run is a no-op: once the column is gone, the UPDATE itself
-- would error, which the 2026-11-02 twin rehearsal caught on run 2.
do $$
begin
  if exists (
    select 1 from information_schema.columns
    where table_schema = 'pre2b' and table_name = 'person' and column_name = 'email'
  ) then
    update pre2b.person set email = null where email is not null;
    alter table pre2b.person drop column email;
  else
    raise notice 'pre2b.person.email not present: nothing to scrub.';
  end if;
end;
$$;

-- Step 2 (run separately, not inside a transaction):
-- vacuum full pre2b.person;

-- Post-condition:
--   select count(*) from information_schema.columns
--    where lower(column_name) in ('email','e_mail','phone','phone_number','mobile','telephone')
--      and table_schema not in ('auth','storage','pg_catalog','information_schema','realtime',
--        'vault','extensions','graphql','graphql_public','supabase_functions','net','pgsodium',
--        'supabase_migrations','cron');
--   -- expect 0
