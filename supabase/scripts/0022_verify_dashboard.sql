-- 0022 VERIFY for the Supabase SQL editor (project oicikjyzmxqfomrrqkvf, The-Prod-Brain).
-- GENERATED from the migration's VERIFY block by rehearse_0022.py --emit-dashboard (drift fails the
-- rehearsal). READ-ONLY. Run AFTER the 0022 paste. Expect 43 rows; every row NOT starting with info_
-- must read true. info_claim_usage_rows >= 1282, info_lane_registry_rows = 10.
select 'event_kind_researched' as check_name, ((select pg_get_constraintdef(oid) = 'CHECK ((kind = ANY (ARRAY[''attended''::text, ''market''::text, ''funding''::text, ''launch''::text, ''exec_move''::text, ''role_posted''::text, ''application''::text, ''interview''::text, ''reference''::text, ''published''::text, ''researched''::text])))' from pg_constraint where conrelid = 'public.event'::regclass and conname = 'event_kind_enum'))::text as ok
union all
select 'lens_of_researched_null' as check_name, (mi.lens_of('researched', null, null) is null and mi.lens_of('researched', 'substrate:research', null) is null and mi.lens_of('researched', 'substrate:research', 'research') = 'research' and coalesce(mi.lens_of('researched', null, 'A'), '') <> 'attended')::text as ok
union all
select 'keep_lens_of_0016_truth_table' as check_name, (mi.lens_of('attended', null, null) = 'attended' and mi.lens_of('attended', null, 'research') = 'research' and mi.lens_of('role_posted', 'substrate:research', 'research') = 'job' and mi.lens_of('funding', 'akta', null) = 'market' and mi.lens_of(null, 'substrate:research', null) = 'research' and mi.lens_of('published', null, null) is null and mi.lens_of(null, null, 'A') is null)::text as ok
union all
select 'keep_lens_of_immutable_no_api_exec' as check_name, ((select provolatile = 'i' from pg_proc where oid = 'mi.lens_of(text,text,text)'::regprocedure) and not has_function_privilege('anon', 'mi.lens_of(text,text,text)', 'execute'))::text as ok
union all
select 'use_count_trigger_present' as check_name, (exists (select 1 from pg_trigger t where t.tgrelid = 'public.claim_usage'::regclass and t.tgname = 'claim_usage_sync_use_count' and t.tgenabled = 'O' and t.tgfoid = 'public.claim_usage_sync_use_count()'::regprocedure and (t.tgtype & 1) = 1 and (t.tgtype & 2) = 0 and (t.tgtype & 4) = 4 and (t.tgtype & 8) = 8 and (t.tgtype & 16) = 16 and (select array_agg(a.attname::text order by a.attname) from pg_attribute a where a.attrelid = t.tgrelid and a.attnum = any(t.tgattr::int2[])) = array['claim_id', 'used_at']))::text as ok
union all
select 'use_count_fn_invoker_no_api_exec' as check_name, ((select not prosecdef and proconfig = array['search_path=pg_catalog, pg_temp'] from pg_proc where oid = 'public.claim_usage_sync_use_count()'::regprocedure) and not has_function_privilege('anon', 'public.claim_usage_sync_use_count()', 'execute') and not has_function_privilege('authenticated', 'public.claim_usage_sync_use_count()', 'execute'))::text as ok
union all
select 'use_count_fn_locks_rows' as check_name, ((select prosrc ~ 'perform 1 from public\.claim where id = any\(ids\) order by id for update;' from pg_proc where oid = 'public.claim_usage_sync_use_count()'::regprocedure))::text as ok
union all
select 'use_count_matches_usage' as check_name, ((select count(*) > 0 from public.claim_usage) and not exists (select 1 from public.claim c left join (select claim_id, count(*) as n, max(used_at) as l from public.claim_usage group by claim_id) u on u.claim_id = c.id where c.use_count <> coalesce(u.n, 0) or c.last_used_at is distinct from u.l))::text as ok
union all
select 'claim_usage_consumer_vocab' as check_name, ((select pg_get_constraintdef(oid) = 'CHECK ((consumer = ANY (ARRAY[''event''::text, ''content''::text, ''job''::text, ''ideation''::text, ''dev''::text, ''brief''::text, ''published''::text])))' from pg_constraint where conrelid = 'public.claim_usage'::regclass and conname = 'claim_usage_consumer_check'))::text as ok
union all
select 'documents_source_type_vocab' as check_name, ((select pg_get_constraintdef(oid) = 'CHECK ((source_type = ANY (ARRAY[''book''::text, ''whitepaper''::text, ''filing''::text, ''pdf''::text, ''other''::text, ''research_brief''::text, ''deep_read''::text, ''prior_context_pack''::text, ''post_event_brief''::text, ''transcript''::text, ''linkedin_post''::text, ''carousel''::text, ''connection_note''::text, ''dossier''::text, ''project_idea''::text, ''scan_digest''::text, ''build_retro''::text, ''note''::text, ''glossary''::text, ''email''::text, ''meeting_note''::text, ''notion_comment''::text])))' from pg_constraint where conrelid = 'public.documents'::regclass and conname = 'documents_source_type_check'))::text as ok
union all
select 'claim_relation_method_vocab' as check_name, ((select pg_get_constraintdef(oid) = 'CHECK ((method = ANY (ARRAY[''human''::text, ''embedding''::text, ''rule''::text, ''llm''::text])))' from pg_constraint where conrelid = 'public.claim_relation'::regclass and conname = 'claim_relation_method_check'))::text as ok
union all
select 'norm_fns_behaviour' as check_name, ((select bool_and(provolatile = 'i') from pg_proc where oid in ('public.norm_name_v1(text)'::regprocedure, 'public.norm_plain_v1(text)'::regprocedure)) and public.norm_name_v1('Acme, Inc.') = 'acme' and public.norm_name_v1('LangChain Inc') = 'langchain' and public.norm_name_v1('Co-Marketing Labs') = 'co marketing labs' and public.norm_name_v1('AG-UI') = 'ag ui' and public.norm_name_v1('  Zed (AI) ') = 'zed ai' and public.norm_name_v1('Inc.') is null and public.norm_plain_v1('Agents Inc') = 'agents inc' and public.norm_plain_v1('AI-Agents') = 'ai agents' and public.norm_plain_v1('!!!') is null)::text as ok
union all
select 'norm_fns_exec_service_role_only' as check_name, (has_function_privilege('service_role', 'public.norm_name_v1(text)', 'execute') and has_function_privilege('service_role', 'public.norm_plain_v1(text)', 'execute') and not has_function_privilege('anon', 'public.norm_name_v1(text)', 'execute') and not has_function_privilege('authenticated', 'public.norm_name_v1(text)', 'execute') and not has_function_privilege('anon', 'public.norm_plain_v1(text)', 'execute') and not has_function_privilege('authenticated', 'public.norm_plain_v1(text)', 'execute'))::text as ok
union all
select 'no_contact_pii_behaviour' as check_name, ((select provolatile = 'i' from pg_proc where oid = 'public.no_contact_pii_v1(text)'::regprocedure) and not public.no_contact_pii_v1('jane.doe@example.com') and not public.no_contact_pii_v1('call +44 20 7946 0958') and not public.no_contact_pii_v1('555-123-4567') and public.no_contact_pii_v1('Acme') and public.no_contact_pii_v1('https://x.com/@handle') and public.no_contact_pii_v1('2026-11-04 12:30:45') and public.no_contact_pii_v1(null) and has_function_privilege('service_role', 'public.no_contact_pii_v1(text)', 'execute') and not has_function_privilege('anon', 'public.no_contact_pii_v1(text)', 'execute') and not has_function_privilege('authenticated', 'public.no_contact_pii_v1(text)', 'execute'))::text as ok
union all
select 'company_name_norm_unique' as check_name, (exists (select 1 from pg_indexes where schemaname = 'public' and tablename = 'company' and indexname = 'company_name_norm_uq' and indexdef = 'CREATE UNIQUE INDEX company_name_norm_uq ON public.company USING btree (norm_name_v1(name))'))::text as ok
union all
select 'topic_name_norm_unique' as check_name, (exists (select 1 from pg_indexes where schemaname = 'public' and tablename = 'topic' and indexname = 'topic_name_norm_uq' and indexdef = 'CREATE UNIQUE INDEX topic_name_norm_uq ON public.topic USING btree (norm_plain_v1(name))'))::text as ok
union all
select 'person_name_norm_nonunique' as check_name, (exists (select 1 from pg_indexes where schemaname = 'public' and tablename = 'person' and indexname = 'person_name_norm_company_idx' and indexdef = 'CREATE INDEX person_name_norm_company_idx ON public.person USING btree (norm_plain_v1(name), company_id)'))::text as ok
union all
select 'keep_lower_name_indexes' as check_name, ((select count(*) = 2 from pg_indexes where schemaname = 'public' and indexname in ('company_lower_idx', 'topic_lower_idx')))::text as ok
union all
select 'entity_alias_columns' as check_name, ((select string_agg(column_name, ',' order by ordinal_position) = 'id,entity_type,entity_id,alias,alias_norm,source,confidence,created_at' from information_schema.columns where table_schema = 'public' and table_name = 'entity_alias'))::text as ok
union all
select 'entity_alias_norm_generated' as check_name, ((select is_generated = 'ALWAYS' and generation_expression ~ 'norm_name_v1\(alias\)' and generation_expression ~ 'norm_plain_v1\(alias\)' from information_schema.columns where table_schema = 'public' and table_name = 'entity_alias' and column_name = 'alias_norm'))::text as ok
union all
select 'entity_alias_unique_norm' as check_name, (exists (select 1 from pg_indexes where schemaname = 'public' and indexname = 'entity_alias_type_norm_uq' and indexdef = 'CREATE UNIQUE INDEX entity_alias_type_norm_uq ON public.entity_alias USING btree (entity_type, alias_norm)'))::text as ok
union all
select 'entity_alias_pii_check' as check_name, ((select pg_get_constraintdef(oid) = 'CHECK (no_contact_pii_v1(alias))' from pg_constraint where conrelid = 'public.entity_alias'::regclass and conname = 'entity_alias_alias_no_pii'))::text as ok
union all
select 'entity_alias_rls_on' as check_name, ((select relrowsecurity from pg_class where oid = 'public.entity_alias'::regclass))::text as ok
union all
select 'entity_alias_no_policies' as check_name, (to_regclass('public.entity_alias') is not null and not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'entity_alias'))::text as ok
union all
select 'entity_alias_no_api_grants' as check_name, (not exists (select 1 from unnest(array['anon', 'authenticated']) r where has_table_privilege(r, 'public.entity_alias', 'select') or has_table_privilege(r, 'public.entity_alias', 'insert') or has_table_privilege(r, 'public.entity_alias', 'update') or has_table_privilege(r, 'public.entity_alias', 'delete') or has_table_privilege(r, 'public.entity_alias', 'truncate') or has_table_privilege(r, 'public.entity_alias', 'references') or has_table_privilege(r, 'public.entity_alias', 'trigger') or has_table_privilege(r, 'public.entity_alias', 'maintain')))::text as ok
union all
select 'entity_alias_service_role_rw' as check_name, (has_table_privilege('service_role', 'public.entity_alias', 'select') and has_table_privilege('service_role', 'public.entity_alias', 'insert') and has_table_privilege('service_role', 'public.entity_alias', 'update') and has_table_privilege('service_role', 'public.entity_alias', 'delete'))::text as ok
union all
select 'sweep_query_columns' as check_name, ((select string_agg(column_name, ',' order by ordinal_position) = 'query_id,kind,theme_id,template,seed_event_id,seed_claim_id,iso_week,lane_run_id,status,items_returned,items_written,items_used,searches,created_at,last_run_at' from information_schema.columns where table_schema = 'public' and table_name = 'sweep_query'))::text as ok
union all
select 'sweep_query_kind_vocab' as check_name, ((select pg_get_constraintdef(oid) = 'CHECK ((kind = ANY (ARRAY[''velocity''::text, ''gap''::text, ''event''::text, ''entity''::text, ''room_topic''::text, ''room_entity''::text, ''open_question''::text, ''room_vs_market''::text])))' from pg_constraint where conrelid = 'public.sweep_query'::regclass and conname = 'sweep_query_kind_check'))::text as ok
union all
select 'sweep_query_issue_unique' as check_name, ((select pg_get_constraintdef(oid) = 'UNIQUE NULLS NOT DISTINCT (kind, theme_id, template, iso_week)' from pg_constraint where conrelid = 'public.sweep_query'::regclass and conname = 'sweep_query_issue_uq'))::text as ok
union all
select 'sweep_query_pii_check' as check_name, ((select pg_get_constraintdef(oid) = 'CHECK (no_contact_pii_v1(template))' from pg_constraint where conrelid = 'public.sweep_query'::regclass and conname = 'sweep_query_template_no_pii'))::text as ok
union all
select 'sweep_query_fks' as check_name, ((select count(*) = 4 from pg_constraint where conrelid = 'public.sweep_query'::regclass and contype = 'f' and confdeltype = 'n'))::text as ok
union all
select 'sweep_query_rls_on' as check_name, ((select relrowsecurity from pg_class where oid = 'public.sweep_query'::regclass))::text as ok
union all
select 'sweep_query_no_policies' as check_name, (to_regclass('public.sweep_query') is not null and not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'sweep_query'))::text as ok
union all
select 'sweep_query_no_api_grants' as check_name, (not exists (select 1 from unnest(array['anon', 'authenticated']) r where has_table_privilege(r, 'public.sweep_query', 'select') or has_table_privilege(r, 'public.sweep_query', 'insert') or has_table_privilege(r, 'public.sweep_query', 'update') or has_table_privilege(r, 'public.sweep_query', 'delete') or has_table_privilege(r, 'public.sweep_query', 'truncate') or has_table_privilege(r, 'public.sweep_query', 'references') or has_table_privilege(r, 'public.sweep_query', 'trigger') or has_table_privilege(r, 'public.sweep_query', 'maintain')))::text as ok
union all
select 'sweep_query_service_role_rw' as check_name, (has_table_privilege('service_role', 'public.sweep_query', 'select') and has_table_privilege('service_role', 'public.sweep_query', 'insert') and has_table_privilege('service_role', 'public.sweep_query', 'update') and has_table_privilege('service_role', 'public.sweep_query', 'delete'))::text as ok
union all
select 'new_tables_no_pii_columns' as check_name, (to_regclass('public.entity_alias') is not null and to_regclass('public.sweep_query') is not null and not exists (select 1 from information_schema.columns where table_schema = 'public' and table_name in ('entity_alias', 'sweep_query') and column_name ~* '(e_?mail|phone|mobile|telephone|contact|address|linkedin)'))::text as ok
union all
select 'lanes_0022_seeded_inactive' as check_name, ((select count(*) = 4 from public.lane_registry where not active and owner = 'alex' and ((lane = 'theme_sweep' and freshness_flag_days = 2 and freshness_fail_days = 4 and schedule like 'daily 05:30 ET%') or (lane = 'claim_review' and freshness_flag_days = 2 and freshness_fail_days = 4 and schedule like 'nightly sweep%') or (lane = 'notion_prior' and freshness_flag_days = 10 and freshness_fail_days = 21 and schedule like 'weekly Sunday%') or (lane = 'reconcile' and freshness_flag_days = 2 and freshness_fail_days = 4 and schedule like 'nightly on the Mac mini%'))))::text as ok
union all
select 'keep_lanes_0016_present' as check_name, ((select count(*) = 6 from public.lane_registry where lane in ('corpus_mine', 'hiring_pulse', 'company_signals', 'research_frontier', 'feeds', 'segment_enrichment')))::text as ok
union all
select 'keep_registry_no_api_grants' as check_name, (not exists (select 1 from unnest(array['anon', 'authenticated']) r where has_table_privilege(r, 'public.lane_registry', 'select') or has_table_privilege(r, 'public.lane_registry', 'insert') or has_table_privilege(r, 'public.lane_registry', 'update') or has_table_privilege(r, 'public.lane_registry', 'delete')))::text as ok
union all
select 'info_claim_usage_rows' as check_name, ((select count(*) from public.claim_usage)::text)::text as ok
union all
select 'info_claims_with_use_count' as check_name, ((select count(*) from public.claim where use_count > 0)::text)::text as ok
union all
select 'info_lane_registry_rows' as check_name, ((select count(*) from public.lane_registry)::text)::text as ok
union all
select 'info_null_lane_claims_under_events' as check_name, ((select count(*) from public.claim where lane is null and event_id is not null)::text)::text as ok;
