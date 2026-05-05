---
description: "Workflow D (SCAFFOLD — not yet wired) — runs voice-editor agent over Content Drafts in needs_review status, outputs voice deltas + before/after suggestions. Polish layer for any drafts produced by Workflow A/B/C."
argument-hint: "[optional: specific Content Draft ID or 'all' to process the entire needs_review queue]"
---

# /voice-pass — Workflow D (SCAFFOLD)

> **Status:** Skeleton only. Alex explicitly deferred polish — this gets built after Workflow A is producing volume.
> **Why scaffolded:** Polish that runs over content that doesn't exist yet is premature. Will land when there's a queue worth polishing.

---

## Trigger

Run when Alex:
- Says "voice pass" / "polish my drafts" / "run voice-editor"
- Has Content Drafts sitting in `needs_review` status that need a quality pass before approval
- Specifically asks to apply voice-guidelines

## Required inputs

- **None required** — defaults to scanning all Content Drafts with status = needs_review
- **(Optional) Specific Content Draft URL or ID** — to run on just one
- **(Optional) Scope filter** — by Content Type (e.g., "voice-pass on all linkedin_post_pre drafts this week")

## Planned agent flow (NOT YET BUILT)

```
1. Query Notion Content Drafts (this conversation):
   - Filter: Content Status = needs_review
   - Optional filter: by Content Type, by date range
   ↓
2. For each draft, invoke voice-editor agent (.claude/agents/content/voice-editor.md):
   - Pass the draft body content
   - Pass .claude/references/content-style-guide.md as the voice spec
   - Pass .claude/references/content-anti-patterns.md as the negative spec
   ↓
3. voice-editor returns per-draft:
   - Severity rating (clean / minor / moderate / major)
   - Specific before/after fixes
   - Voice / tone / terminology / anti-pattern flags
   ↓
4. Present to Alex grouped by severity:
   - Drafts that pass clean → no action
   - Drafts with minor issues → list inline, let Alex accept-all or pick
   - Drafts with moderate/major issues → walk through one by one
   ↓
5. For each accepted change, update the Notion Content Draft (this conversation):
   - Apply edits to body
   - Optionally bump status to approved if Alex approves the polish wholesale
```

## What to do today (until wired)

If Alex tries to run `/voice-pass` before this is built:
1. Acknowledge scaffolded
2. Default behavior: invoke voice-editor agent inline on whatever draft Alex hands over (paste content)
3. Don't try to query Notion in batch — just process one at a time the manual way

## Wiring TODO (for the build session)

- [ ] Decide whether voice-editor takes content + style-guide every time, or whether style-guide should live inside the agent definition (probably the former — keeps style-guide as a single source of truth, agent stays generic)
- [ ] Severity rubric: define what "minor / moderate / major" mean in concrete terms
- [ ] Update flow to Notion: how to apply edits — wholesale replace body? diff-style?
- [ ] When Alex iterates on style guide: how does voice-editor pick up the changes? (it reads the file each invocation, so just keep style-guide.md updated)
- [ ] Should /voice-pass also touch update-voice-and-style.md / update-anti-patterns.md skills? (probably not — those are propagation skills, voice-editor is enforcement)

## Future automation (deferred per Alex's instruction — commands first)

When ready:
- Stop hook on any content-creating skill → auto-run /voice-pass on the just-created draft
- Or a periodic scan of needs_review queue

## Ground truth references

- `.claude/agents/content/voice-editor.md` — imported voice-editor agent contract
- `.claude/references/content-style-guide.md` — Alex's voice + style spec
- `.claude/references/content-anti-patterns.md` — what NOT to write
- `.claude/skills/update-voice-and-style.md` — propagation skill for when style evolves
- `.claude/skills/update-anti-patterns.md` — propagation skill for new anti-patterns
- `.claude/skills/content-quality/voice-guidelines/SKILL.md` — imported methodology, supplements local style-guide
