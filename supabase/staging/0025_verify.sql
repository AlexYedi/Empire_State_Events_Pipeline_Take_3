-- 0025_verify.sql: rehearsal probes for supabase/migrations/0025_pii_backstop_normalized.sql (YED-392/324 rework).
-- Read-only, except step 4 (VALIDATE, after Alex's go) and the rolled-back transaction in step 5 (twin only).
-- Probe strings use U&'' escapes, so no invisible character sits in this file. Fictional addresses and reserved
-- numbers only (example.com / .test, 555-01xx, Ofcom drama ranges).
--
-- 0. BEFORE apply (read-only; prod or twin, no DDL): the whole probe corpus against v2's expression inline:
--      python3 .claude/scripts/check_pii_corpus.py --emit-sql   -> run the printed SELECT
--    Every row must report ok = true; out_of_contract rows report ok = null (L3 does not promise them).

-- 1. Behaviour after apply: no_contact_pii_v2 keeps its canonical-form contract. Every row: ok = true.
select s, expected_ok, public.no_contact_pii_v2(s) as got, public.no_contact_pii_v2(s) = expected_ok as ok
from (values
  (U&'dana\FF20example.com', false),                      -- NFKC full-width @
  (U&'dana@exa\200Emple.c\200Eom', false),                -- LRM inside the address (review blocker)
  (U&'call 555\200E-123-0100', false),                    -- LRM inside a phone (review blocker)
  (U&'dana@example.c\+0E0041om', false),                  -- tag character U+E0041
  (U&'dana@example.c\034Fom', false),                     -- CGJ
  (U&'dana@example.c\FE0Fom', false),                     -- variation selector
  (U&'dana@example\3002com', false),                      -- UTS-46 ideographic full stop
  (U&'nguy\1EC5n@example.com', false),                    -- Vietnamese local part
  (U&'\0570\0561\0575\056F@example.am', false),           -- Armenian local part
  (U&'\0E2A\0E21\0E0A\0E32\0E22@example.co.th', false),   -- Thai local part
  (U&'\0438\0432\0430\043D@\043F\0440\0438\043C\0435\0440.\0440\0444', false),  -- Cyrillic + IDN TLD
  ('dana&#X0040;example.com', false),
  ('dana&commatexample.com', false),
  ('dana%40example.com', false),
  ('dana[@]example.com', false),
  ('dana (at) example.com', false),
  ('(555)123-0100', false),
  ('555-1230100', false),
  ('+44 20 7946 0958', false),
  ('07700 900123', false),
  ('06 12 34 56 78', false),
  ('wa.me/15551230100', false),
  ('tel:+15551230100', false),
  (U&'555\00B7123\00B70100', false),
  (U&'555\2011123\20110100', false),
  ('{"note": "call\n555-123-0100"}'::jsonb::text, false), -- YED-318: jsonb newline escape before a phone
  ('{"note": "call\t555-123-0100"}'::jsonb::text, false), -- YED-318: jsonb tab escape before a phone
  ('{"555-123-0100": "cell"}'::jsonb::text, false),       -- YED-323: phone as a JSON key
  ('noreply@github.com', true),                           -- allowlist carried into SQL (allow_re)
  ('x.com/@handle', true),
  ('sold 10@3.50', true),
  ('a@b.c1', true),
  ('ISBN 9780134685991', true),
  ('x.com/someone/status/1856212345678901234', true),
  ('linkedin.com/in/x-1234567890', true),
  ('Pets dot com', true),
  (U&'Nguy\1EC5n V\0103n An, CEO', true),
  ('the team at OpenAI', true),
  ('2026-11-20T10:00:00Z', true),
  ('Acme', true),
  (null, true)
) t(s, expected_ok);

-- 2. Catalog: v2 is immutable and service_role-only; the person trigger calls v2; all nine CHECKs exist and are
--    NOT VALID until step 4.
select 'v2_immutable' as check_name,
       (select provolatile = 'i' from pg_proc where oid = 'public.no_contact_pii_v2(text)'::regprocedure) as ok
union all select 'v2_service_role', has_function_privilege('service_role', 'public.no_contact_pii_v2(text)', 'execute')
union all select 'v2_not_anon', not has_function_privilege('anon', 'public.no_contact_pii_v2(text)', 'execute')
union all select 'v2_not_authenticated', not has_function_privilege('authenticated', 'public.no_contact_pii_v2(text)', 'execute')
union all select 'person_trigger_calls_v2',
       pg_get_functiondef('public.assert_no_contact_pii()'::regprocedure) ~ 'no_contact_pii_v2'
union all select 'nine_v2_checks_not_valid',
       (select count(*) = 9 and bool_and(not convalidated) from pg_constraint
        where contype = 'c' and pg_get_constraintdef(oid) ~ 'no_contact_pii_v2'
          and conname in ('claim_text_no_pii', 'claim_quote_no_pii', 'claim_evidence_no_pii_v2',
                          'claim_freshness_reason_no_pii_v2', 'claim_verification_note_no_pii_v2',
                          'claim_verification_source_url_no_pii_v2', 'claim_label_note_no_pii_v2',
                          'entity_alias_alias_no_pii_v2', 'sweep_query_template_no_pii_v2'))
union all select 'v1_kept', to_regprocedure('public.no_contact_pii_v1(text)') is not null;

-- 3. Existing rows: every count must be 0 before step 4 (counts only; never select the text). The person row
--    counts the trigger's columns against v2, i.e. against the new literals.
select 'claim.claim_text' as site, count(*) filter (where not public.no_contact_pii_v2(claim_text)) as violating from public.claim
union all select 'claim.quote', count(*) filter (where not public.no_contact_pii_v2(quote)) from public.claim
union all select 'claim.evidence', count(*) filter (where not public.no_contact_pii_v2(evidence::text)) from public.claim
union all select 'claim.freshness_reason', count(*) filter (where not public.no_contact_pii_v2(freshness_reason)) from public.claim
union all select 'claim_verification.note', count(*) filter (where not public.no_contact_pii_v2(note)) from public.claim_verification
union all select 'claim_verification.source_url', count(*) filter (where not public.no_contact_pii_v2(source_url)) from public.claim_verification
union all select 'claim_label.note', count(*) filter (where not public.no_contact_pii_v2(note)) from public.claim_label
union all select 'entity_alias.alias', count(*) filter (where not public.no_contact_pii_v2(alias)) from public.entity_alias
union all select 'sweep_query.template', count(*) filter (where not public.no_contact_pii_v2(template)) from public.sweep_query
union all select 'person (name, title, bio, role_context, metadata)',
       count(*) filter (where not (public.no_contact_pii_v2(name) and public.no_contact_pii_v2(title)
                                   and public.no_contact_pii_v2(bio) and public.no_contact_pii_v2(role_context)
                                   and public.no_contact_pii_v2(metadata::text)))
from public.person;

-- 4. Only if every step-3 count is 0 (each takes SHARE UPDATE EXCLUSIVE; reads and writes continue):
-- alter table public.claim validate constraint claim_text_no_pii;
-- alter table public.claim validate constraint claim_quote_no_pii;
-- alter table public.claim validate constraint claim_evidence_no_pii_v2;
-- alter table public.claim validate constraint claim_freshness_reason_no_pii_v2;
-- alter table public.claim_verification validate constraint claim_verification_note_no_pii_v2;
-- alter table public.claim_verification validate constraint claim_verification_source_url_no_pii_v2;
-- alter table public.claim_label validate constraint claim_label_note_no_pii_v2;
-- alter table public.entity_alias validate constraint entity_alias_alias_no_pii_v2;
-- alter table public.sweep_query validate constraint sweep_query_template_no_pii_v2;

-- 5. Person trigger: re-run supabase/staging/0017_verify.sql and s04_d1_verify.sql, plus (twin only, rolled back):
-- begin; insert into public.person (id, name, bio) values (gen_random_uuid(), 'probe', U&'dana@exa\200Emple.c\200Eom'); rollback;
--    -> must raise 'ADR-9 tier-2 violation' (an LRM-split email the 0017 body let through).
