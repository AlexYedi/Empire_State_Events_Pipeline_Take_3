-- 0023 PREFLIGHT for the Supabase SQL editor (project oicikjyzmxqfomrrqkvf, The-Prod-Brain).
-- GENERATED from supabase/migrations/0023_graph_v2_l1_freshness.sql by rehearse_0023.py --emit-dashboard;
-- the rehearsal fails if this file drifts. READ-ONLY. APPLY 0022 FIRST, then run this, then 0023.
-- Expect: prereq_0022 = true, no_0023_columns = true, no_0023_tables = true. Note the two
-- baseline_* rows: VERIFY's info_claim_rows must equal baseline_claim_rows after the paste.
-- Any false: STOP. prereq_0022 false = 0022 is not applied; a no_0023_* false = a partial or
-- earlier 0023 is already there (run 0023_verify_dashboard.sql to see which part).
select 'prereq_0022' as check_name, (to_regprocedure('public.no_contact_pii_v1(text)') is not null and to_regclass('public.entity_alias') is not null)::text as detail
union all
select 'no_0023_columns', (not exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'claim' and column_name in ('evidence', 'judge_verdict', 'judge_model', 'judge_prompt_hash', 'judged_at', 'rank', 'review_flag', 'valid_from', 'valid_to', 'freshness_class', 'freshness_conf', 'freshness_reason', 'next_check_at', 'visibility')))::text
union all
select 'no_0023_tables', (to_regclass('public.claim_verification') is null and to_regclass('public.claim_label') is null and to_regclass('public.judge_audit') is null and to_regclass('public.claim_current') is null)::text
union all
select 'baseline_claim_rows', (select count(*) from public.claim)::text
union all
select 'baseline_claim_by_status', (select string_agg(status || '=' || n, ',' order by status) from (select status, count(*) n from public.claim group by status) s);
