-- =====================================================================
-- S1a VERIFY — behavioural assertions for 0009_substrate_s1a_additive.sql
--
-- One DO block = one transaction. It inserts probe rows, asserts what must
-- succeed AND what must be REJECTED, deletes the probes, and checks that
-- pre-existing row counts are unchanged. Any miss RAISEs, which rolls back
-- every probe automatically. Success prints: NOTICE  S1a VERIFY: PASS (n checks)
--
-- Why behavioural (review finding 1d): reading a constraint definition proves
-- what was ADDED, never what failed to be REMOVED. A stray second CHECK that
-- still rejects 'published' only shows up when you actually insert 'published'.
-- =====================================================================
do $verify$
declare
  n            int := 0;
  c            int;
  ev_before    bigint;  doc_before bigint;  ent_before bigint;
  probe_event  uuid;
  probe_doc1   uuid;    probe_doc2 uuid;
  cl1          uuid;    cl2        uuid;
  ts1          timestamptz;
  probe_ref    text := '__s1a_probe__' || gen_random_uuid()::text;
begin
  select count(*) into ev_before  from public.event;
  select count(*) into doc_before from public.documents;
  select count(*) into ent_before from public.event_entity;

  -- ---------- structure: exactly-one checks (catches a leftover constraint) ----------
  select count(*) into c from pg_constraint
   where conrelid = 'public.event'::regclass and contype = 'c'
     and pg_get_constraintdef(oid) ilike '%kind%';
  if c <> 1 then raise exception 'FAIL: expected 1 CHECK on event.kind, found %', c; end if;
  n := n + 1;

  select count(*) into c from pg_constraint
   where conrelid = 'public.documents'::regclass and contype = 'c'
     and pg_get_constraintdef(oid) ilike '%source_type%';
  if c <> 1 then raise exception 'FAIL: expected 1 CHECK on documents.source_type, found %', c; end if;
  n := n + 1;

  select count(*) into c from information_schema.tables
   where table_schema = 'public'
     and table_name in ('claim','claim_entity','claim_relation','document_entity','artifact_outcome','claim_usage');
  if c <> 6 then raise exception 'FAIL: expected 6 new tables, found %', c; end if;
  n := n + 1;

  select count(*) into c from pg_class
   where relkind = 'r' and relrowsecurity
     and oid in ('public.claim'::regclass, 'public.claim_entity'::regclass, 'public.claim_relation'::regclass,
                 'public.document_entity'::regclass, 'public.artifact_outcome'::regclass, 'public.claim_usage'::regclass);
  if c <> 6 then raise exception 'FAIL: RLS must be ON for all 6 new tables, found %', c; end if;
  n := n + 1;

  select count(*) into c from pg_trigger
   where tgrelid = 'public.artifact_outcome'::regclass and tgname = 'artifact_outcome_set_updated_at';
  if c <> 1 then raise exception 'FAIL: expected exactly 1 updated_at trigger, found %', c; end if;
  n := n + 1;

  select count(*) into c from pg_indexes where schemaname = 'public' and indexname = 'claim_embedding_hnsw';
  if c <> 1 then raise exception 'FAIL: claim_embedding_hnsw missing'; end if;
  n := n + 1;

  -- ---------- event kinds ----------
  insert into public.event (title, kind, source, metadata)
  values ('__s1a_probe__', 'published', 's1a_verify', '{"probe":true}') returning id into probe_event;
  n := n + 1;

  begin
    insert into public.event (title, kind, source) values ('__s1a_probe__', 'observed', 's1a_verify');
    raise exception 'FAIL: kind=observed was ACCEPTED (ADR-10 decision 3 says it must not exist)';
  exception when check_violation then null; end;
  n := n + 1;

  -- ---------- documents: our artifacts ----------
  insert into public.documents (title, source_type, sha256, blob_key, external_ref, version, event_id, doc_date)
  values ('__s1a_probe__ v1', 'research_brief', 'probe-' || gen_random_uuid(), null, probe_ref, 1, probe_event, now())
  returning id into probe_doc1;
  n := n + 1;   -- null blob_key + new source_type accepted

  begin
    insert into public.documents (title, source_type, sha256, external_ref, version)
    values ('dup', 'research_brief', 'probe-' || gen_random_uuid(), probe_ref, 1);
    raise exception 'FAIL: duplicate (external_ref, version) was ACCEPTED';
  exception when unique_violation then null; end;
  n := n + 1;

  begin
    insert into public.documents (title, source_type, sha256, external_ref, version, is_current)
    values ('second current', 'research_brief', 'probe-' || gen_random_uuid(), probe_ref, 2, true);
    raise exception 'FAIL: a second is_current row for one external_ref was ACCEPTED';
  exception when unique_violation then null; end;
  n := n + 1;

  update public.documents set is_current = false where id = probe_doc1;
  insert into public.documents (title, source_type, sha256, external_ref, version, supersedes_id)
  values ('__s1a_probe__ v2', 'research_brief', 'probe-' || gen_random_uuid(), probe_ref, 2, probe_doc1)
  returning id into probe_doc2;
  n := n + 1;   -- supersession path works

  begin
    insert into public.documents (title, source_type, sha256, visibility)
    values ('bad vis', 'note', 'probe-' || gen_random_uuid(), 'public');
    raise exception 'FAIL: visibility=public was ACCEPTED';
  exception when check_violation then null; end;
  n := n + 1;

  -- ---------- claims ----------
  insert into public.claim (source_key, claim_key, claim_text, claim_type, document_id, event_id,
                            provenance_tier, confidence, asserted_at, status, extractor)
  values ('probe-src', 'k1', 'Probe claim one about agent autonomy.', 'thesis', probe_doc2, probe_event,
          'first_hand', 0.8, now() - interval '30 days', 'approved', 'parse')
  returning id into cl1;
  insert into public.claim (source_key, claim_key, claim_text, provenance_tier, asserted_at)
  values ('probe-src', 'k2', 'Probe claim two, contradicting one.', 'web_verified', now())
  returning id into cl2;
  n := n + 1;

  begin
    insert into public.claim (source_key, claim_key, claim_text) values ('probe-src', 'k1', 'dup');
    raise exception 'FAIL: duplicate (source_key, claim_key) was ACCEPTED — extraction would not be idempotent';
  exception when unique_violation then null; end;
  n := n + 1;

  begin
    insert into public.claim (source_key, claim_key, claim_text, confidence) values ('probe-src', 'k3', 'x', 1.5);
    raise exception 'FAIL: confidence 1.5 was ACCEPTED';
  exception when check_violation then null; end;
  n := n + 1;

  begin
    insert into public.claim (source_key, claim_key, claim_text, provenance_tier) values ('probe-src', 'k4', 'x', 'rumor');
    raise exception 'FAIL: provenance_tier=rumor was ACCEPTED';
  exception when check_violation then null; end;
  n := n + 1;

  select count(*) into c from public.claim where id = cl1 and tsv @@ plainto_tsquery('english', 'autonomy');
  if c <> 1 then raise exception 'FAIL: generated tsv does not match claim_text'; end if;
  n := n + 1;

  -- ---------- claim_entity / claim_relation ----------
  insert into public.claim_entity (claim_id, entity_type, entity_id, role)
  values (cl1, 'person', gen_random_uuid(), 'asserted_by'),
         (cl1, 'topic',  gen_random_uuid(), 'about');
  n := n + 1;

  insert into public.claim_relation (from_claim_id, to_claim_id, relation, method, confidence)
  values (cl2, cl1, 'contradicts', 'human', 0.9);
  n := n + 1;

  begin
    insert into public.claim_relation (from_claim_id, to_claim_id, relation) values (cl1, cl1, 'refines');
    raise exception 'FAIL: a self-relation was ACCEPTED';
  exception when check_violation then null; end;
  n := n + 1;

  begin
    insert into public.claim_relation (from_claim_id, to_claim_id, relation) values (cl1, cl2, 'agrees');
    raise exception 'FAIL: relation=agrees was ACCEPTED';
  exception when check_violation then null; end;
  n := n + 1;

  -- ---------- document_entity / outcomes / usage ----------
  insert into public.document_entity (document_id, entity_type, entity_id, role)
  values (probe_doc2, 'company', gen_random_uuid(), 'about');
  n := n + 1;

  insert into public.artifact_outcome (document_id, goal, outcome) values (probe_doc2, 'engagement', 'pending')
  returning updated_at into ts1;
  perform pg_sleep(0.01);
  update public.artifact_outcome set outcome = 'hit' where document_id = probe_doc2;
  select count(*) into c from public.artifact_outcome where document_id = probe_doc2 and updated_at > ts1;
  if c <> 1 then raise exception 'FAIL: updated_at trigger did not fire'; end if;
  n := n + 1;

  insert into public.claim_usage (claim_id, document_id, consumer) values (cl1, probe_doc2, 'content');
  begin
    insert into public.claim_usage (claim_id, document_id, consumer) values (cl2, probe_doc2, 'marketing');
    raise exception 'FAIL: consumer=marketing was ACCEPTED';
  exception when check_violation then null; end;
  n := n + 1;

  -- ---------- cleanup (cascades clear entity/relation/usage/outcome rows) ----------
  delete from public.claim     where source_key = 'probe-src';
  delete from public.documents where external_ref = probe_ref;
  delete from public.event     where id = probe_event;

  select count(*) into c from public.claim_entity   where claim_id in (cl1, cl2);
  if c <> 0 then raise exception 'FAIL: claim_entity rows survived their claim (cascade broken)'; end if;
  select count(*) into c from public.claim_relation where from_claim_id in (cl1, cl2) or to_claim_id in (cl1, cl2);
  if c <> 0 then raise exception 'FAIL: claim_relation rows survived their claims (cascade broken)'; end if;
  n := n + 1;

  if (select count(*) from public.event)        <> ev_before  then raise exception 'FAIL: event count changed';        end if;
  if (select count(*) from public.documents)    <> doc_before then raise exception 'FAIL: documents count changed';    end if;
  if (select count(*) from public.event_entity) <> ent_before then raise exception 'FAIL: event_entity count changed'; end if;
  n := n + 1;

  raise notice 'S1a VERIFY: PASS (% checks)', n;
end
$verify$;
