-- YED-376: two events Alex did NOT attend are stored as kind='attended'. Re-label them kind='researched'.
-- 1. "Software Is the New Media" (2026-04-28): Alex 2026-11-09, he did not attend. Notion status not_attending.
-- 2. "AI Builders NYC: Agent Observability + Evals" (2026-05-14): Notion title is "[TEST EVENT — DELETE ME]", status not_attending.
--
-- Why re-label, not delete (changed 2026-11-20): the 11/12 research-lane staging (substrate.py stage-research) linked each
-- event's pre-event research brief to its row by Notion page id: 2 documents + 51 approved research claims (18 + 33).
-- Since migration 0022, research for an event Alex did not attend lives on a kind='researched' row (53 such events,
-- 4,760 claims), which is exactly what these two are. Deleting would orphan the briefs and claims; 'researched' keeps
-- them and stops anything from counting these as attended. substrate.py only promotes researched -> attended, never back,
-- so this is a one-off datafix. Edges (16), documents and claims are untouched.
-- Pre-checked read-only 2026-11-20: events=2 (attended), edges=16, documents=2, claims=51, doc_claims=0.
-- APPLY: dashboard SQL editor, The-Prod-Brain, as one paste (single transaction). Aborts unless counts match.

do $$
declare
  ids uuid[] := array['5683da50-e714-470f-91af-2a27f790f533', 'bca7b046-9272-484d-ad18-af2f6ab6bd8b']::uuid[];
  n_ev int; n_done int;
begin
  select count(*) into n_ev from public.event where id = any(ids) and kind = 'attended';
  if n_ev <> 2 then
    raise exception 'precondition failed: attended events=% (want 2)', n_ev;
  end if;
  update public.event
     set kind = 'researched',
         metadata = coalesce(metadata, '{}'::jsonb)
                    || jsonb_build_object('relabelled_from', 'attended', 'relabelled_at', now(), 'relabel_reason', 'YED-376: not attended')
   where id = any(ids) and kind = 'attended';
  get diagnostics n_done = row_count;
  if n_done <> 2 then
    raise exception 'expected 2 rows updated, got %', n_done;
  end if;
  raise notice 're-labelled 2 events attended -> researched';
end;
$$;

-- Post-check: expect 2 rows, both kind = researched
-- select id, title, kind from public.event where id in ('5683da50-e714-470f-91af-2a27f790f533','bca7b046-9272-484d-ad18-af2f6ab6bd8b');
-- Revert: update public.event set kind = 'attended', metadata = metadata - 'relabelled_from' - 'relabelled_at' - 'relabel_reason'
--         where id in ('5683da50-e714-470f-91af-2a27f790f533','bca7b046-9272-484d-ad18-af2f6ab6bd8b') and kind = 'researched';
