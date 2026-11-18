-- 0025_verify.sql: rehearsal probes for supabase/migrations/0025_pii_backstop_normalized.sql (YED-392/324).
-- Read-only. Run on the twin AFTER applying 0025 there, then read-only on prod before the dashboard apply.
-- Every row must return ok = true. Probe strings use U&'' escapes so no invisible character sits in this file;
-- the same 22 verdicts are pinned against pii_normalize.has_pii() by the generator, and the inline twin of this
-- probe returned 22/22 on prod (read-only, PG 17.6) on 2026-11-18.

-- 1. Behaviour: no_contact_pii_v2 agrees with the client guard.
select s, expected_ok, public.no_contact_pii_v2(s) as got, public.no_contact_pii_v2(s) = expected_ok as ok
from (values
  ('reach dana [at] example [dot] com', false),
  ('DANA AT EXAMPLE DOT COM', false),
  (U&'dana\FF20example.com', false),
  ('dana&#64;example.com', false),
  ('dana%40example.com', false),
  (U&'da\200Bna@exa\200Bmple.com', false),
  (U&'\0438\0432\0430\043D@\043F\0440\0438\043C\0435\0440.\0440\0444', false),
  (U&'call 555\2011123\20110100', false),
  (U&'call 555\2013123\20130100', false),
  (U&'call \FF15\FF15\FF15-\FF11\FF12\FF13-\FF10\FF11\FF10\FF10', false),
  ('call 5551230100', false),
  ('jane @ fakeco . test', false),
  ('raised $5M in 2026, 3x growth', true),
  ('Q3 2026: 1,200,000 users', true),
  ('see https://x.com/a/status/1856212345678901234', true),
  ('id aaaaaaaa000000000000000000000001', true),
  ('2026-11-04 12:30:45', true),
  (U&'\0418\0432\0430\043D \041F\0435\0442\0440\043E\0432, CEO', true),
  ('x.com/@handle', true),
  ('end. Next sentence', true),
  ('meet at noon', true),
  ('Acme', true),
  (null, true)
) t(s, expected_ok);

-- 2. Catalog: v2 is immutable, service_role-only; the two CHECKs exist (NOT VALID until step 4).
select 'v2_immutable', (select provolatile = 'i' from pg_proc where oid = 'public.no_contact_pii_v2(text)'::regprocedure)
union all select 'v2_service_role', has_function_privilege('service_role', 'public.no_contact_pii_v2(text)', 'execute')
union all select 'v2_not_anon', not has_function_privilege('anon', 'public.no_contact_pii_v2(text)', 'execute')
union all select 'v2_not_authenticated', not has_function_privilege('authenticated', 'public.no_contact_pii_v2(text)', 'execute')
union all select 'claim_text_check', exists (select 1 from pg_constraint where conrelid = 'public.claim'::regclass
                                             and conname = 'claim_text_no_pii')
union all select 'claim_quote_check', exists (select 1 from pg_constraint where conrelid = 'public.claim'::regclass
                                              and conname = 'claim_quote_no_pii');

-- 3. Existing rows: expect 0 before validating (counts only; never select the text).
select count(*) as violating_claims from public.claim
where not public.no_contact_pii_v2(claim_text) or not public.no_contact_pii_v2(quote);

-- 4. Only if step 3 returned 0:
-- alter table public.claim validate constraint claim_text_no_pii;
-- alter table public.claim validate constraint claim_quote_no_pii;

-- 5. Person trigger still refuses the 0017 / s04_d1 shapes and now a Cyrillic email: re-run
--    supabase/staging/0017_verify.sql and s04_d1_verify.sql, plus (twin only, inside a rolled-back txn):
-- begin; insert into public.person (id, name, bio) values (gen_random_uuid(), 'probe', U&'\0438\0432\0430\043D@\043F\0440\0438\043C\0435\0440.\0440\0444'); rollback;
--    -> must raise 'ADR-9 tier-2 violation'.
