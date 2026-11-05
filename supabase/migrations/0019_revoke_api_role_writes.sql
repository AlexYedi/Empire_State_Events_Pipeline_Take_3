-- =====================================================================
-- 0019 · Revoke API-role write privileges on the MI spine (YED-311)
--
-- NOT APPLIED. Twin rehearsal (supabase/scripts/rehearse_0019.py) + Alex
-- dashboard apply required (CLAUDE.md invariant 2).
--
-- WHY. A read-only audit of prod (2026-11-04 / 11-05) found that `anon` and
-- `authenticated` hold INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER and
-- MAINTAIN (relacl `arwdDxtm`) on nine public tables. The correct tables
-- (e.g. person) carry `anon=r`, SELECT only, and that is the target state here. RLS is enabled on all nine with no policies, so row
-- writes are denied today, but:
--   * TRUNCATE is not governed by RLS at all. Only the privilege check stands
--     between the anon key and an empty table. PostgREST doesn't expose it
--     today, so it isn't reachable through the API, but that's the API surface
--     holding, not the database.
--   * One future permissive policy (e.g. a hub read policy written `FOR ALL`)
--     would silently open writes.
-- Every other public table already grants these roles SELECT only. These nine
-- were created without the explicit revoke the others carry.
--
-- ROOT CAUSE. pg_default_acl in `public` grants anon/authenticated full rights
-- (arwdDxtm) on every new table owned by `postgres`. Part 2 closes that for
-- future tables. The parallel `supabase_admin` default entry can only be
-- altered by supabase_admin and is left as is. Dashboard and migration DDL runs
-- as postgres.
--
-- WHAT IS NOT CHANGED.
--   * SELECT stays exactly as it is (the hub and the healthcheck read probe use
--     the anon key).
--   * service_role and postgres are untouched (spine_client writes as
--     service_role).
--   * The default SELECT grant for new tables stays (an open question for
--     Alex: new tables should arguably start with no API access at all).
--
-- Verified before drafting: no writer in any of the 4 repos uses the anon or
-- authenticated key to write (carry_forward_canonical.py reads with a
-- publishable key from the decommissioned gtm spine and writes with
-- service_role).
--
-- IDEMPOTENT: REVOKE of a privilege not held is a no-op; a re-run is clean.
--
-- PRE-APPLY PROBE (read-only; expect 18 rows = 9 tables x 2 roles, each with
-- write privileges):
--   select table_name, grantee, string_agg(privilege_type, ',' order by 1)
--   from information_schema.role_table_grants
--   where table_schema = 'public' and grantee in ('anon','authenticated')
--     and privilege_type in ('INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER')
--   group by 1, 2 order by 1, 2;
--
-- POST-APPLY PROBE (expect 0 rows from the query above; SELECT still present):
--   select count(*) from information_schema.role_table_grants
--   where table_schema = 'public' and grantee in ('anon','authenticated')
--     and privilege_type = 'SELECT'
--     and table_name in ('artifact_outcome','claim','claim_entity','claim_relation',
--       'claim_usage','doc_chunks','doc_claims','document_entity','documents');
--   -- expect 18
--
-- ROLLBACK (restores the pre-0019 grants exactly; paste only if needed):
--   grant insert, update, delete, truncate, references, trigger, maintain
--     on public.artifact_outcome, public.claim, public.claim_entity,
--        public.claim_relation, public.claim_usage, public.doc_chunks,
--        public.doc_claims, public.document_entity, public.documents
--     to anon, authenticated;
--   alter default privileges for role postgres in schema public
--     grant insert, update, delete, truncate, references, trigger, maintain
--     on tables to anon, authenticated;
-- =====================================================================

-- Part 1 · the nine tables: API roles keep SELECT only.
revoke insert, update, delete, truncate, references, trigger, maintain
  on public.artifact_outcome,
     public.claim,
     public.claim_entity,
     public.claim_relation,
     public.claim_usage,
     public.doc_chunks,
     public.doc_claims,
     public.document_entity,
     public.documents
  from anon, authenticated;

-- Part 2 · future tables created by postgres in public: no write privileges for API roles.
alter default privileges for role postgres in schema public
  revoke insert, update, delete, truncate, references, trigger, maintain
  on tables from anon, authenticated;
