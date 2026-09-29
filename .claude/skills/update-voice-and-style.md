---
name: update-voice-and-style
description: Capture voice/style learnings from Alex's content feedback and propagate them to reference files (content-style-guide.md, content-anti-patterns.md, outreach-templates.md) and dependent content skills. Use when Alex gives feedback on generated content ("this felt too formal", "the hook on option B was better"), observes a tone preference, flags an anti-pattern, or shares an example to extract patterns from. Also the quick path for the anti-patterns list: "add X to the anti-patterns", "remove Y from off-limits", "never do Z in posts", or a batch of items that bugged him in recent drafts. Also invoked proactively when patterns emerge across multiple content sessions.
---

# Skill: Update Voice & Style

Capture learnings about Alex's content voice and style preferences, then propagate
changes to all reference files and content skills that depend on them.

**Invoked when:** Alex provides feedback on generated content — what worked, what didn't,
what felt right, what felt off. Also invoked proactively when patterns emerge across
multiple content generation sessions.

---

## Input

Alex provides one or more of:
- Feedback on a specific piece of generated content ("this felt too formal", "the hook on option B was better because...")
- A new anti-pattern to add ("never use the word 'delve'")
- A tone/voice observation ("I want to sound more like X, less like Y")
- A structural preference ("I prefer posts that start with a question")
- An example of content they liked (their own or someone else's) — extract patterns
- An example of content they hated — extract anti-patterns
- A direct anti-patterns edit: add, remove or amend a word/phrase, structural or DM pattern, or add a new category
- A bulk update ("here are 5 things that bugged me about today's drafts") — process each item individually, present as one batch

---

## Step 1: Categorize the Update

Classify each piece of feedback into:

| Category | Updates File | What Changes |
|---|---|---|
| Tone/voice | `content-style-guide.md` | Voice pillars, tone descriptors |
| Post structure | `content-style-guide.md` | Post architecture, length preferences |
| DM structure | `content-style-guide.md` + `outreach-templates.md` | DM patterns, personalization approach |
| Anti-pattern (word/phrase) | `content-anti-patterns.md` | Off-limits words table |
| Anti-pattern (structural) | `content-anti-patterns.md` | Structural anti-patterns table |
| Anti-pattern (DM) | `content-anti-patterns.md` | DM anti-patterns table |
| Anti-pattern remove / amend / new category | `content-anti-patterns.md` | Delete the row (confirm first), update example/category/rationale, or add a category row with examples and rationale |
| Audience/positioning | `content-style-guide.md` | Audience section, positioning notes |
| Quality bar | `content-style-guide.md` | Quality bar definition |
| Formatting | `content-style-guide.md` | Hashtags, emoji, length, CTA approach |
| Character variant (C) / personality floor / recurring series (Room #N, Hype Check, Over-Engineered, Job Hunt Week N, Best of Builds) | `content-style-guide.md` | The voice v2 rules for that item |

**Voice v2 iteration log (2026-09-28; 4-week test, read 2026-10-26).** When mining Alex's Notion comments, check every batch explicitly for these three: comments on Variant C (which cold opens landed, which `[PERSONALITY LINE NEEDED]` flags he filled and how), the personality floor, and each recurring series. Record each learning as a **dated in-place annotation** on the rule it changes (`(2026-10-05: …)`), not a separate log; the 2026-10-26 read is a pass over those annotations.

---

## Step 2: Present Proposed Changes

Before updating any file, show Alex:

```
## Proposed Voice & Style Updates

### [File Name]
**Section:** [which section is being updated]
**Current:** [what it says now]
**Proposed:** [what it will say]
**Rationale:** [why this change based on the feedback]
```

Anti-pattern edits present as one table instead: `| Action | Table | Entry | Category | Rationale |`.

Get explicit approval before writing.

---

## Step 3: Apply Updates

1. Edit the affected reference file(s)
2. Update the `Last updated` date and version number at the bottom of each file
3. If the change affects skill behavior (not just reference content), check whether
   `pre-event-content.md` or `post-event-content.md` (when it exists) need updates too:
   - New anti-pattern → skills reference the file dynamically, no skill edit needed
   - New structural preference → may need to update the post architecture in the skill
   - New content type or CTA → likely needs skill edit
   - Removed anti-pattern that a skill hard-codes → flag it and propose the skill edit
4. If a skill file needs updating, show the proposed skill change and get approval

---

## Step 4: Confirm

```
## Voice & Style Updated

### Files Modified
- [file]: [what changed]
- [file]: [what changed]

### Skills Affected
- [skill]: [updated / no change needed]

### Version
Style Guide: v[X.Y]
Anti-Patterns: v[X.Y]
Outreach Templates: v[X.Y]
```

---

## Proactive Pattern Detection

When running content generation skills, if you notice a pattern across Alex's feedback
(e.g., he consistently picks the shorter variant, or always removes a certain type of
phrase), flag it:

> **Pattern noticed:** Across the last [N] content sessions, you've consistently
> [observation]. Want me to update the style guide to codify this?

This helps the voice develop faster than waiting for explicit feedback.
