---
description: "Workflow C (SCAFFOLD — not yet wired) — weekly synthesis of all events, content, and outreach activity. Builds 'The Upcoming Week' Sunday LinkedIn post, runs pattern-synthesis if ≥2 briefs have opposing theses, polishes via voice-pass. Designed for Sunday evening cadence."
argument-hint: "[optional: ISO week date, defaults to this week]"
---

# /weekly-recap — Workflow C (SCAFFOLD)

> **Status:** Skeleton only. Will be useful after 3-5 events have been put through Workflow A. Not yet wired.
> **Why scaffolded:** Workflow C operates on a week's worth of briefs. Building it now without that data would be premature.

---

## Trigger

Run when Alex:
- Says "weekly recap" / "wrap the week" / "build the Sunday post"
- It's Sunday evening (manual cadence — not yet automated; future hook candidate)
- Asks "what events do I have this week?" before content sprint

## Required inputs

- **None required** — pulls everything from Notion automatically
- **(Optional) Date range override** — for backfilling or future-week previews

## Planned agent flow (NOT YET BUILT)

```
1. Query Notion (this conversation):
   - Events DB: events with Event Date in the upcoming 7 days OR past 7 days
   - Content Drafts DB: drafts created in past 7 days, status ≠ archived
   ↓
2. Group: upcoming events vs. attended events vs. drafts in flight
   ↓
3. For UPCOMING events (next 7 days):
   - Build "The Upcoming Week" LinkedIn post via pre-event-content skill (existing)
   - Format: roundup of events Alex is attending, framing per documentarian angle from each brief
   ↓
4. For ATTENDED events (past 7 days):
   - Detect: do ≥2 briefs have opposing theses?
     - YES → invoke pattern-synthesis skill → drafts linkedin_post_synthesis
     - NO → no synthesis post this week (cadence rule: max 1 synthesis post/week, format fatigues)
   ↓
5. Run /voice-pass over all drafts produced this week (Workflow D)
   ↓
6. Write everything to Notion Content Drafts with status = needs_review
   ↓
7. Summary report to Alex:
   - Posts ready for review (with Notion links)
   - Events upcoming (count + dates)
   - Drafts still in flight from prior weeks
   - Anti-signals fired across the week's events (if any retros captured them)
```

## What to do today (until wired)

If Alex tries to run `/weekly-recap` before this is built:
1. Acknowledge scaffolded
2. Manually do the steps:
   - Query Events DB for upcoming week
   - Invoke `pre-event-content` skill for the Upcoming Week roundup
   - Check if pattern-synthesis applies (review past 7 days of briefs together)
   - Suggest /voice-pass if/when it's wired

## Wiring TODO (for the build session)

- [ ] **Steering — two-touch** (`.claude/skills/steering-interview/SKILL.md`): run **Touch 1 (Aim)**
  at the top (what to foreground for the week, audience), and **Touch 2 (Sharpen)** after the event
  set is assembled and before drafting — ≤3 genuine forks derived from the week's shape (which
  through-line, which events lead), never generic. Persist to `## Author Steer` (Sharpen). Skippable.

- [ ] Decide pattern-synthesis trigger automation — programmatic detection of "opposing theses" is hard; might just surface candidate pairs to Alex and let him decide
- [ ] Cadence rule enforcement: store last synthesis post date somewhere, refuse if <7 days
- [ ] Anti-signal aggregation: requires Step 7 retros to be consistently filled in — depend on Workflow B running reliably first
- [ ] Decide whether to run Workflow C as a series of inline calls (simpler) or with a recap-orchestrator agent (cleaner separation)
- [ ] Format spec for the Sunday post — define template, length, voice — pull from .claude/references/content-style-guide.md

## Future automation (deferred — Alex chose commands first, automation later)

When ready, this becomes a candidate for:
- A scheduled task (anthropic-skills:schedule) that fires Sunday 6pm
- A SessionStart hook that nudges Alex if it's Sunday and the recap hasn't run

## Ground truth references

- `.claude/skills/pre-event-content/SKILL.md` — existing skill that builds The Upcoming Week
- `.claude/skills/pattern-synthesis/SKILL.md` — existing two-thesis synthesis
- `.claude/skills/content-patterns/two-thesis-synthesis.md` — pattern definition (per CLAUDE.md)
- `.claude/references/content-style-guide.md` — voice + audience · `.claude/references/audience-north-star.md` — top-level ethos (mission, persona, three floors, Learn-More Set)
- CLAUDE.md § Phase 2 cadence rules (max 1 synthesis post/week)
