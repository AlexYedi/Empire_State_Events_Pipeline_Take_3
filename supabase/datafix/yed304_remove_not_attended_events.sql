-- YED-304 W4: remove two events Alex did NOT attend from kind='attended'.
-- Alex 2026-11-03: "I did not" attend Agentics (2026-08-19) or Agentic AI in Production (2026-08-20).
-- Convention (supabase/scripts/build_manifests.py): unattended events get NO event row; their research
-- entities stay. So this deletes the 2 event rows and their 11 company edges only. Companies are kept.
-- Pre-checked read-only 2026-11-03: 0 documents, 0 claims, 0 doc_claims reference either event.
-- Notion Event Status for both is already set to not_attending (so a future backfill won't recreate them).
-- APPLY: dashboard SQL editor, The-Prod-Brain, as one paste (single transaction). Aborts unless counts match.

do $$
declare
  ids uuid[] := array['7160a7e8-1d57-4fa8-9166-f7e3a86e792e', 'bee8696e-c87c-421e-adef-5fe37de99d86']::uuid[];
  n_ev int; n_edge int; n_ref int;
begin
  select count(*) into n_ev from public.event where id = any(ids) and kind = 'attended';
  select count(*) into n_edge from public.event_entity where event_id = any(ids);
  select (select count(*) from public.documents where event_id = any(ids))
       + (select count(*) from public.claim where event_id = any(ids))
       + (select count(*) from public.doc_claims where promoted_event_id = any(ids)) into n_ref;
  if n_ev <> 2 or n_edge <> 11 or n_ref <> 0 then
    raise exception 'precondition failed: events=% (want 2) edges=% (want 11) refs=% (want 0)', n_ev, n_edge, n_ref;
  end if;
  delete from public.event_entity where event_id = any(ids);
  delete from public.event where id = any(ids);
  raise notice 'removed 2 events and 11 edges';
end;
$$;

-- Post-check: expect 0
-- select count(*) from public.event where id in ('7160a7e8-1d57-4fa8-9166-f7e3a86e792e','bee8696e-c87c-421e-adef-5fe37de99d86');
