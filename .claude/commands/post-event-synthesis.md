---
description: "Workflow B (SCAFFOLD — not yet wired) — turns raw post-event material (Granola transcripts, voice notes, observations) into structured intel + content drafts. Chains transcript-analysis → objection-mining → commercial-insight-generator → content-correspondent → pattern-synthesis → voice-pass."
argument-hint: "[paste transcript or notes, or reference event name to pull from Notion]"
---

# /post-event-synthesis — Workflow B (SCAFFOLD)

> **Status:** Skeleton only. Triggers, inputs, and agent flow are documented. Not yet wired for end-to-end execution.
> **Why scaffolded:** Alex doesn't yet have a Granola transcript queued for the current week's content sprint. Wiring + first run happens after Workflow A produces briefs and an event has been attended.

---

## Trigger

Run when Alex:
- Just got back from an event ("just left PMF x AI", "back from Field Notation", "wrapped up the founders dinner")
- Has Granola / Wispr / voice notes to process
- Says "post-event content for [event]" / "synthesize last night" / "turn my notes into content"
- Pastes a transcript / notes block

## Required inputs (one or more)

1. **Raw material** — Granola transcript, Wispr voice notes, freeform recap, photos with captions
2. **Event name** — to pull the original research brief from Notion Content Drafts (filter: Content Type = research_brief, Event Name = X)
3. **(Optional) Contact list** — names Alex met / talked to that should get DMs

## Planned agent flow (NOT YET BUILT — do not invoke today)

```
1. Pull research brief from Notion (this conversation)
   ↓
2. transcript-analysis skill (.claude/skills/transcript-intelligence/transcript-analysis/)
   → extracts: action items, themes, quotes, objections, surprise moments
   ↓
3. objection-mining skill (.claude/skills/transcript-intelligence/objection-mining/)
   → surfaces friction signals: what would block someone from engaging with Alex's POV / project / role search
   ↓
4. commercial-insight-generator agent (.claude/agents/sales-methodology/)
   → finds the documentarian thesis: what's the Reframe across the room's conversation
   ↓
5. content-correspondent skill (existing)
   → bucket-sorts contacts (A/B/C), drafts DMs per bucket, drafts Tier 1 comments + Tier 2 post
   ↓
6. pattern-synthesis skill (existing) — IF ≥2 briefs in last 7 days have opposing theses
   → drafts the two-thesis synthesis post (linkedin_post_synthesis)
   ↓
7. voice-pass command (Workflow D) — over all generated drafts before they hit Notion
   ↓
8. Write to Notion Content Drafts (this conversation) — one Content Draft per output, all with Event Phase = post_event, Content Status = needs_review
```

## What to do today (until wired)

If Alex tries to run `/post-event-synthesis` before this is built:
1. Acknowledge the workflow is scaffolded but not yet wired
2. Default to invoking `content-correspondent` skill directly (existing path)
3. Note that adding `transcript-analysis` + `objection-mining` + `commercial-insight-generator` upfront would deepen the output
4. Offer to wire the full chain "next session" or in a dedicated build session

## Wiring TODO (for the build session)

- [ ] Decide: orchestrator agent for B (similar to event-research-orchestrator) or inline orchestration in this command file?
- [ ] Define the handoff schema between transcript-analysis and content-correspondent (what does transcript-analysis output that content-correspondent consumes?)
- [ ] Decide whether commercial-insight-generator runs always, or only when post-event material has enough scope (single-DM follow-up doesn't need a Reframe — full event recap does)
- [ ] Pattern-synthesis trigger logic: detect ≥2 briefs in 7 days with opposing theses programmatically, or ask Alex
- [ ] Confirm Content Drafts schema accepts all output types (research_brief / linkedin_dm_speaker / linkedin_dm_host / linkedin_post_post / prepared_questions / linkedin_post_synthesis — ✅ confirmed in CLAUDE.md)

## Ground truth references

- `.claude/skills/content-correspondent/SKILL.md` — current post-event content path
- `.claude/skills/transcript-intelligence/transcript-analysis/SKILL.md` — imported, ready to call
- `.claude/skills/transcript-intelligence/objection-mining/SKILL.md` — imported, ready to call
- `.claude/agents/sales-methodology/commercial-insight-generator.md` — imported, ready to call
- `.claude/skills/pattern-synthesis/SKILL.md` — existing
- CLAUDE.md § Project Architecture for Content Drafts schema
