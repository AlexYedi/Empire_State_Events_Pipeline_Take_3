# YED-96 — Validation handoff (start a fresh session to close the loop)

**Why a fresh session:** the `/post-event-content` command + supporting skills were just edited (full 16-section post-event brief v2). The agent/skill registry is **session-frozen**, so the edits only load in a **new** conversation launched **from this repo, in a terminal** (not the Dock — env inheritance).

## 1. Launch
```
cd "/Users/sameoldexpressions/Documents/GitHub/Empire_State_Events_Pipeline_Take_3"
claude
```

## 2. Paste this prompt to validate + close YED-96
```
Validate and close YED-96 (Post-Event Brief v2). The /post-event-content command + supporting skills were just templatized to the FULL 16-section enhanced post-event brief. Spec + adversarial review = Linear YED-96; evidence = .claude/evals/post-event-brief-template-evidence.md and .claude/evals/ingest-elevenlabs-scorecard.md.

Do an end-to-end validation run on the NYC GTM+AI Masterclass #5 event (06/03/2026):

1. Confirm the edits loaded — read .claude/commands/post-event-content.md and verify the Step 3.7 scaffold now has the 16 sections + the mechanics: keyterms-from-entity-list ingest recipe, content-derived Speaker Map (+ HIGH/MED confidence), web-enrichment pass (bounded/gated/cached), event-page write (## Post-Event Brief) + canonical post_event_brief Content Draft, KG write-back as a search-before-create proposed delta, idempotency marker on the Event page, attribution hard-gate, outreach opt-in.

2. Run /post-event-content for that event using the existing ElevenLabs Scribe v2 transcript already in the folder "Event Content/06 03 26_ NYC GTM+AI Masterclass #5 - NY Tech Week Special". (A prior brief from an earlier manual run exists in that folder — this is the COMMAND-path validation; do not delete it.)

3. Produce: full 16-section post_event_brief → Event page (## Post-Event Brief) + canonical Content Draft; a People/Companies/Topics proposed-delta (search-before-create; human-approve before writing); LinkedIn post(s) + visual brief → Gamma. Outreach: skip unless I name targets.

4. Instrument + report: (a) my review wall-clock for the brief; (b) idempotency — re-run once, confirm no double-write (Event-page marker held); (c) Speaker-Map attribution error vs the transcript; (d) section-fill (which of 16 filled for this masterclass format).

5. If it passes, update YED-96: check the final DoD box (validated end-to-end) and set it Done; otherwise log residual gaps on the issue.

Constraints: Notion/Gmail writes main-thread only; subagents generate/return, parent writes; honor the attribution hard-gate + quote-safety (HIGH/MED) before any public-facing draft.
```

## Context links
- Linear: YED-96 (spec, revised build plan, adversarial review in comment) · related YED-95 (ingest).
- Evidence: `.claude/evals/post-event-brief-template-evidence.md` (n=4 section-fill) · `.claude/evals/ingest-elevenlabs-scorecard.md` (ingest bake-off).
- Edited files: `.claude/commands/post-event-content.md` (primary) · `.claude/skills/content-correspondent/SKILL.md` · `.claude/skills/event-research/SKILL.md` · `.claude/references/notion-schema.md` · `.claude/skills/content-patterns/visual-briefs.md`.
