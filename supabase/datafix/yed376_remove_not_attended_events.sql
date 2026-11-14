-- YED-376: remove two events Alex did NOT attend from kind='attended'.
-- 1. "Software Is the New Media" (2026-04-28): Alex 2026-11-09, he did not attend. Notion status not_attending.
-- 2. "AI Builders NYC: Agent Observability + Evals" (2026-05-14): Notion title is "[TEST EVENT — DELETE ME]", status not_attending.
-- Convention (supabase/scripts/build_manifests.py, yed304 datafix): unattended events get NO event row; research entities stay.
-- This deletes the 2 event rows and their 16 event_entity edges only. Companies, people and topics are kept.
-- Pre-checked read-only 2026-11-09: 0 documents, 0 claims, 0 doc_claims reference either event.
-- APPLY: dashboard SQL editor, The-Prod-Brain, as one paste (single transaction). Aborts unless counts match.

do $$
declare
  ids uuid[] := array['5683da50-e714-470f-91af-2a27f790f533', 'bca7b046-9272-484d-ad18-af2f6ab6bd8b']::uuid[];
  n_ev int; n_edge int; n_ref int;
begin
  select count(*) into n_ev from public.event where id = any(ids) and kind = 'attended';
  select count(*) into n_edge from public.event_entity where event_id = any(ids);
  select (select count(*) from public.documents where event_id = any(ids))
       + (select count(*) from public.claim where event_id = any(ids))
       + (select count(*) from public.doc_claims where promoted_event_id = any(ids)) into n_ref;
  if n_ev <> 2 or n_edge <> 16 or n_ref <> 0 then
    raise exception 'precondition failed: events=% (want 2) edges=% (want 16) refs=% (want 0)', n_ev, n_edge, n_ref;
  end if;
  delete from public.event_entity where event_id = any(ids);
  delete from public.event where id = any(ids);
  raise notice 'removed 2 events and 16 edges';
end;
$$;

-- Post-check: expect 0
-- select count(*) from public.event where id in ('5683da50-e714-470f-91af-2a27f790f533','bca7b046-9272-484d-ad18-af2f6ab6bd8b');
