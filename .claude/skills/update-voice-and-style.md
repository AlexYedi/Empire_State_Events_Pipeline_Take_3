---
name: update-voice-and-style
description: Capture voice/style learnings from Alex's content feedback and propagate them to reference files (content-style-guide.md, content-anti-patterns.md, outreach-templates.md) and dependent content skills. Use when Alex gives feedback on generated content ("this felt too formal", "the hook on option B was better"), observes a tone preference, flags an anti-pattern, or shares an example to extract patterns from. Also invoked proactively when patterns emerge across multiple content sessions.
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
| Audience/positioning | `content-style-guide.md` | Audience section, positioning notes |
| Quality bar | `content-style-guide.md` | Quality bar definition |
| Formatting | `content-style-guide.md` | Hashtags, emoji, length, CTA approach |

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
