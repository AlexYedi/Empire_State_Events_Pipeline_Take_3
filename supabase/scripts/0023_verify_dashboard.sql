-- 0023 VERIFY for the Supabase SQL editor (project oicikjyzmxqfomrrqkvf, The-Prod-Brain).
-- GENERATED from the migration's VERIFY block by rehearse_0023.py --emit-dashboard (drift fails the
-- rehearsal). READ-ONLY. Run AFTER the 0023 paste. Expect 23 rows; every row NOT starting with info_
-- must read true. info_claim_rows = the preflight baseline_claim_rows. A false row: re-paste 0023
-- once (it is re-runnable), re-run this; still false = stop and run the ROLLBACK block.
select 'claim_new_columns' as check_name, ((select count(*) = 14 from information_schema.columns where table_schema = 'public' and table_name = 'claim' and column_name in ('evidence', 'judge_verdict', 'judge_model', 'judge_prompt_hash', 'judged_at', 'rank', 'review_flag', 'valid_from', 'valid_to', 'freshness_class', 'freshness_conf', 'freshness_reason', 'next_check_at', 'visibility')))::text as ok
union all
select 'claim_rank_visibility_defaults' as check_name, ((select bool_and(case column_name when 'rank' then column_default = '''normal''::text' and is_nullable = 'NO' when 'visibility' then column_default = '''private''::text' and is_nullable = 'NO' end) from information_schema.columns where table_schema = 'public' and table_name = 'claim' and column_name in ('rank', 'visibility')))::text as ok
union all
select 'claim_new_checks' as check_name, ((select count(*) = 12 from pg_constraint where conrelid = 'public.claim'::regclass and contype = 'c' and convalidated and conname in ('claim_evidence_shape', 'claim_evidence_no_pii', 'claim_judge_verdict_vocab', 'claim_judge_record_complete', 'claim_judge_prompt_hash_hex', 'claim_rank_vocab', 'claim_review_flag_vocab', 'claim_valid_window', 'claim_freshness_class_vocab', 'claim_freshness_conf_range', 'claim_freshness_reason_no_pii', 'claim_visibility_vocab')))::text as ok
union all
select 'claim_all_rows_neutral_at_apply' as check_name, (not exists (select 1 from public.claim where rank <> 'normal' or review_flag is not null or visibility <> 'private' or evidence is not null or judge_verdict is not null))::text as ok
union all
select 'keep_claim_status_vocab' as check_name, ((select pg_get_constraintdef(oid) = 'CHECK ((status = ANY (ARRAY[''candidate''::text, ''approved''::text, ''rejected''::text])))' from pg_constraint where conrelid = 'public.claim'::regclass and conname = 'claim_status_check'))::text as ok
union all
select 'evidence_fn_behaviour' as check_name, ((select provolatile = 'i' from pg_proc where oid = 'public.claim_evidence_ok_v1(jsonb)'::regprocedure) and public.claim_evidence_ok_v1(null) and public.claim_evidence_ok_v1('[{"para_idx": 3, "quote": "Acme raised a Series B"}]') and public.claim_evidence_ok_v1('[{"para_idx": 0, "quote": "a"}, {"para_idx": 12, "quote": "b c"}]') and not public.claim_evidence_ok_v1('[]') and not public.claim_evidence_ok_v1('{"para_idx": 1, "quote": "x"}') and not public.claim_evidence_ok_v1('[{"para_idx": -1, "quote": "x"}]') and not public.claim_evidence_ok_v1('[{"para_idx": 1.5, "quote": "x"}]') and not public.claim_evidence_ok_v1('[{"para_idx": "1", "quote": "x"}]') and not public.claim_evidence_ok_v1('[{"para_idx": 1, "quote": "  "}]') and not public.claim_evidence_ok_v1('[{"para_idx": 1, "quote": "x", "extra": 1}]') and not public.claim_evidence_ok_v1('[{"quote": "x"}]') and not public.claim_evidence_ok_v1('["x"]') and not public.claim_evidence_ok_v1('"x"') and not public.claim_evidence_ok_v1('[{"para_idx": 1, "quote": "x"}, 7]') and public.claim_evidence_ok_v1(jsonb_build_array(jsonb_build_object('para_idx', 1, 'quote', array_to_string(array_fill('w'::text, array[25]), ' ')))) and not public.claim_evidence_ok_v1(jsonb_build_array(jsonb_build_object('para_idx', 1, 'quote', array_to_string(array_fill('w'::text, array[26]), ' ')))))::text as ok
union all
select 'evidence_fn_exec_service_role_only' as check_name, (has_function_privilege('service_role', 'public.claim_evidence_ok_v1(jsonb)', 'execute') and not has_function_privilege('anon', 'public.claim_evidence_ok_v1(jsonb)', 'execute') and not has_function_privilege('authenticated', 'public.claim_evidence_ok_v1(jsonb)', 'execute'))::text as ok
union all
select 'claim_verification_columns' as check_name, ((select string_agg(column_name, ',' order by ordinal_position) = 'id,claim_id,outcome,method,source_url,source_document_id,checker_model,run_id,note,checked_at' from information_schema.columns where table_schema = 'public' and table_name = 'claim_verification'))::text as ok
union all
select 'claim_verification_append_only_trigger' as check_name, (exists (select 1 from pg_trigger t where t.tgrelid = 'public.claim_verification'::regclass and t.tgname = 'claim_verification_append_only' and t.tgenabled = 'O' and t.tgfoid = 'public.claim_verification_append_only()'::regprocedure and (t.tgtype & 2) = 2 and (t.tgtype & 16) = 16 and (t.tgtype & 4) = 0 and (t.tgtype & 8) = 0))::text as ok
union all
select 'claim_label_columns' as check_name, ((select string_agg(column_name, ',' order by ordinal_position) = 'id,claim_id,sample_run,stratum,inclusion_prob,label,useful,labeler,note,labelled_at' from information_schema.columns where table_schema = 'public' and table_name = 'claim_label'))::text as ok
union all
select 'claim_label_one_per_run' as check_name, (exists (select 1 from pg_constraint where conrelid = 'public.claim_label'::regclass and contype = 'u' and pg_get_constraintdef(oid) = 'UNIQUE (claim_id, sample_run)'))::text as ok
union all
select 'judge_audit_columns' as check_name, ((select string_agg(column_name, ',' order by ordinal_position) = 'id,run_date,part,n,hits,bound,threshold,passed,judge_model,judge_prompt_hash,batch,confirms_audit_id,created_at' from information_schema.columns where table_schema = 'public' and table_name = 'judge_audit'))::text as ok
union all
select 'pii_checks_on_new_text' as check_name, ((select count(*) = 5 from pg_constraint where contype = 'c' and pg_get_constraintdef(oid) ~ 'no_contact_pii_v1' and conrelid in ('public.claim'::regclass, 'public.claim_verification'::regclass, 'public.claim_label'::regclass) and conname in ('claim_evidence_no_pii', 'claim_freshness_reason_no_pii', 'claim_verification_note_no_pii', 'claim_verification_source_url_no_pii', 'claim_label_note_no_pii')))::text as ok
union all
select 'new_tables_rls_on_no_policies' as check_name, ((select bool_and(relrowsecurity) from pg_class where oid in ('public.claim_verification'::regclass, 'public.claim_label'::regclass, 'public.judge_audit'::regclass)) and not exists (select 1 from pg_policies where schemaname = 'public' and tablename in ('claim_verification', 'claim_label', 'judge_audit')))::text as ok
union all
select 'new_relations_no_api_grants' as check_name, (not exists (select 1 from unnest(array['anon', 'authenticated']) r, unnest(array['public.claim_verification', 'public.claim_label', 'public.judge_audit', 'public.claim_current']) rel, unnest(array['select', 'insert', 'update', 'delete', 'truncate', 'references', 'trigger']) p where has_table_privilege(r, rel, p)))::text as ok
union all
select 'new_tables_service_role_rw' as check_name, ((select bool_and(has_table_privilege('service_role', rel, 'select') and has_table_privilege('service_role', rel, 'insert') and has_table_privilege('service_role', rel, 'update') and has_table_privilege('service_role', rel, 'delete')) from unnest(array['public.claim_verification', 'public.claim_label', 'public.judge_audit']) rel) and has_table_privilege('service_role', 'public.claim_current', 'select'))::text as ok
union all
select 'new_tables_no_pii_columns' as check_name, ((select count(*) = 3 from pg_class where oid in (to_regclass('public.claim_verification'), to_regclass('public.claim_label'), to_regclass('public.judge_audit'))) and not exists (select 1 from information_schema.columns where table_schema = 'public' and table_name in ('claim_verification', 'claim_label', 'judge_audit') and column_name ~* '(e_?mail|phone|mobile|telephone|contact|address|linkedin)'))::text as ok
union all
select 'claim_current_invoker' as check_name, ((select coalesce('security_invoker=on' = any(reloptions), false) from pg_class where oid = 'public.claim_current'::regclass))::text as ok
union all
select 'claim_current_matches_claim_at_apply' as check_name, ((select count(*) from public.claim_current) = (select count(*) from public.claim) and (select count(*) filter (where is_current) from public.claim_current) = (select count(*) from public.claim where status <> 'rejected'))::text as ok
union all
select 'keep_match_claims_present' as check_name, (to_regprocedure('public.match_claims_hybrid(vector,text,integer,integer,integer,uuid[],text[],text[])') is not null)::text as ok
union all
select 'keep_mi_fact_present' as check_name, (to_regclass('mi.fact') is not null or exists (select 1 from pg_proc where proname = 'fact' and pronamespace = 'mi'::regnamespace))::text as ok
union all
select 'info_claim_rows' as check_name, ((select count(*) from public.claim)::text)::text as ok
union all
select 'info_claim_current_is_current' as check_name, ((select count(*) filter (where is_current) from public.claim_current)::text)::text as ok;
