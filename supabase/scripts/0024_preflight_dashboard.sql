-- 0024 PREFLIGHT for the Supabase SQL editor (project oicikjyzmxqfomrrqkvf, The-Prod-Brain).
-- GENERATED from supabase/migrations/0024_readers_on_claim_current.sql by rehearse_0024.py --emit-dashboard;
-- the rehearsal fails if this file drifts. READ-ONLY. APPLY 0023 FIRST, then run this, then 0024.
-- Expect: prereq_0023 = true, old_match_claims_shape = true, nothing_retired_yet = true. Note the
-- three baseline_* rows: after the paste VERIFY's info_mi_fact_claim_rows, info_mi_fact_rows and
-- info_live_claims must equal baseline_mi_fact_claim_rows, baseline_mi_fact_rows, baseline_live_claims.
-- Any false: STOP. prereq_0023 false = 0023 is not applied; old_match_claims_shape false = 0024 (or
-- part of it) is already there (run 0024_verify_dashboard.sql); nothing_retired_yet false = a writer
-- already retired a claim, so the *_at_apply rows will not hold: ask before pasting.
select 'prereq_0023' as check_name, (to_regclass('public.claim_current') is not null and exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'claim' and column_name = 'rank'))::text as detail
union all
select 'old_match_claims_shape', (to_regprocedure('public.match_claims_hybrid(vector,text,integer,integer,integer,uuid[],text[],text[])') is not null and to_regprocedure('public.match_claims_hybrid(vector,text,integer,integer,integer,uuid[],text[],text[],text[])') is null)::text
union all
select 'nothing_retired_yet', (not exists (select 1 from public.claim c where c.rank = 'deprecated' or (c.valid_to is not null and c.valid_to <= now())) and not exists (select 1 from public.claim_verification where outcome = 'contradicted'))::text
union all
select 'baseline_mi_fact_claim_rows', (select count(*) from mi.fact where fact_type = 'claim')::text
union all
select 'baseline_mi_fact_rows', (select count(*) from mi.fact)::text
union all
select 'baseline_live_claims', (select count(*) from public.claim where status in ('approved', 'candidate'))::text;
