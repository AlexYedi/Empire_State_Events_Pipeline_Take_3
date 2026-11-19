-- 0024 VERIFY for the Supabase SQL editor (project oicikjyzmxqfomrrqkvf, The-Prod-Brain).
-- GENERATED from the migration's VERIFY block by rehearse_0024.py --emit-dashboard (drift fails the
-- rehearsal). READ-ONLY. Run AFTER the 0024 paste. Expect 17 rows; every row NOT starting with info_
-- must read true. info_* rows = the preflight baseline_* rows. A false row: re-paste 0024 once (it is
-- re-runnable), re-run this; still false = stop and run the ROLLBACK block.
select 'claim_current_is_retired_col' as check_name, ((select string_agg(column_name, ',' order by ordinal_position) from information_schema.columns where table_schema = 'public' and table_name = 'claim_current' and ordinal_position > (select count(*) from information_schema.columns where table_schema = 'public' and table_name = 'claim')) = 'last_check_outcome,last_checked_at,is_current,is_overdue,is_retired')::text as ok
union all
select 'keep_claim_current_invoker_no_api' as check_name, ((select coalesce('security_invoker=on' = any(reloptions), false) from pg_class where oid = 'public.claim_current'::regclass) and not has_table_privilege('anon', 'public.claim_current', 'select') and not has_table_privilege('authenticated', 'public.claim_current', 'select') and has_table_privilege('service_role', 'public.claim_current', 'select'))::text as ok
union all
select 'match_claims_new_shape_only' as check_name, (to_regprocedure('public.match_claims_hybrid(vector,text,integer,integer,integer,uuid[],text[],text[],text[])') is not null and to_regprocedure('public.match_claims_hybrid(vector,text,integer,integer,integer,uuid[],text[],text[])') is null)::text as ok
union all
select 'match_claims_reads_claim_current' as check_name, ((select prosrc ~ 'from public\.claim_current c' and prosrc ~ 'not c\.is_retired' and prosrc ~ 'filter_visibility is null or c\.visibility = any\(filter_visibility\)' and prosrc !~ 'from public\.claim c' from pg_proc where oid = to_regprocedure('public.match_claims_hybrid(vector,text,integer,integer,integer,uuid[],text[],text[],text[])')))::text as ok
union all
select 'match_claims_out_columns' as check_name, ((select array_to_string(proargnames[array_length(proargnames, 1) - 3:array_length(proargnames, 1)], ',') = 'review_flag,last_check_outcome,is_overdue,visibility' from pg_proc where oid = to_regprocedure('public.match_claims_hybrid(vector,text,integer,integer,integer,uuid[],text[],text[],text[])')))::text as ok
union all
select 'entity_neighborhood_reads_claim_current' as check_name, ((select prosrc ~ 'from public\.claim_current c' and prosrc ~ 'not c\.is_retired' and prosrc ~ 'c\.review_flag, c\.last_check_outcome, c\.is_overdue, c\.visibility' and prosrc !~ 'from public\.claim c' from pg_proc where oid = to_regprocedure('public.entity_neighborhood(uuid[],timestamp with time zone,integer,integer,integer)')))::text as ok
union all
select 'functions_exec_service_role_only' as check_name, ((select bool_and(has_function_privilege('service_role', f, 'execute') and not has_function_privilege('anon', f, 'execute') and not has_function_privilege('authenticated', f, 'execute')) from unnest(array['public.match_claims_hybrid(vector,text,integer,integer,integer,uuid[],text[],text[],text[])', 'public.entity_neighborhood(uuid[],timestamp with time zone,integer,integer,integer)']) f))::text as ok
union all
select 'functions_invoker_search_path' as check_name, ((select count(*) = 2 and bool_and(not prosecdef and proconfig is not distinct from array['search_path=public']) from pg_proc where oid in (to_regprocedure('public.match_claims_hybrid(vector,text,integer,integer,integer,uuid[],text[],text[],text[])'), to_regprocedure('public.entity_neighborhood(uuid[],timestamp with time zone,integer,integer,integer)'))))::text as ok
union all
select 'mi_fact_reads_claim_current' as check_name, ((select pg_get_viewdef('mi.fact'::regclass, true) ~ 'FROM claim_current c' and pg_get_viewdef('mi.fact'::regclass, true) ~ 'NOT c\.is_retired'))::text as ok
union all
select 'keep_mi_fact_invoker' as check_name, ((select coalesce('security_invoker=on' = any(reloptions), false) from pg_class where oid = 'mi.fact'::regclass))::text as ok
union all
select 'keep_mi_fact_columns' as check_name, ((select string_agg(attname, ',' order by attnum) = 'fact_type,fact_id,occasion_event_id,lens,kind,signal_type,lane,source_system,source_ref,provenance_tier,asserted_at,asserted_week,observed_at' from pg_attribute where attrelid = 'mi.fact'::regclass and attnum > 0 and not attisdropped))::text as ok
union all
select 'keep_mi_dependents' as check_name, (to_regclass('mi.fact_company') is not null and to_regclass('mi.fact_topic') is not null)::text as ok
union all
select 'keep_mi_fact_claims_unchanged_at_apply' as check_name, ((select count(*) from mi.fact where fact_type = 'claim') = (select count(*) from public.claim where status <> 'rejected'))::text as ok
union all
select 'nothing_retired_at_apply' as check_name, (not exists (select 1 from public.claim_current where is_retired))::text as ok
union all
select 'info_mi_fact_claim_rows' as check_name, ((select count(*) from mi.fact where fact_type = 'claim')::text)::text as ok
union all
select 'info_mi_fact_rows' as check_name, ((select count(*) from mi.fact)::text)::text as ok
union all
select 'info_live_claims' as check_name, ((select count(*) from public.claim_current where status in ('approved', 'candidate') and not is_retired)::text)::text as ok;
