# Skill: Update Anti-Patterns

Quick-access skill for managing the content anti-patterns list. Add, remove, append,
or amend individual words, phrases, or entire pattern sets.

**Target file:** `.claude/references/content-anti-patterns.md`

---

## Input

Alex provides one or more of:
- A word or phrase to add: "add 'delve' to the off-limits list"
- A word or phrase to remove: "remove 'ecosystem' — I actually use that naturally"
- A category to add: "add a new category for [X] with these examples..."
- An amendment: "change the 'why' on [word] to [new reason]"
- A structural anti-pattern: "never start a post with [X]"
- A DM anti-pattern: "never do [X] in DMs"
- A bulk update: "here are 5 things that bugged me about today's drafts"

---

## Step 1: Classify the Change

| Action | What Happens |
|---|---|
| **Add word/phrase** | New row in Off-Limits Words & Phrases table |
| **Add structural pattern** | New row in Structural Anti-Patterns table |
| **Add DM pattern** | New row in DM Anti-Patterns table |
| **Remove entry** | Delete the row, confirm before removing |
| **Amend entry** | Update the example, category, or rationale |
| **New category** | Add a new category row with examples and rationale |
| **Bulk update** | Process each item individually, present as a batch |

---

## Step 2: Present Proposed Changes

```
## Proposed Anti-Pattern Updates

| Action | Table | Entry | Category | Rationale |
|--------|-------|-------|----------|-----------|
| Add | Off-Limits Words | "delve" | Omnipresent buzzwords | AI-generated tell, instantly signals the content wasn't written by a human |
| Remove | Off-Limits Words | "ecosystem" | — | Alex uses this naturally and it fits his voice |
| Amend | Structural | Starting with "I'm excited..." | [updated rationale] | — |
```

Approve? [Yes / No / Edit]

---

## Step 3: Apply Changes

1. Edit `content-anti-patterns.md` with the approved changes
2. Update the `Last updated` date and version number
3. Confirm what changed

---

## Step 4: Check Propagation

After updating, check if any content skills need adjustment:

- If a **new structural anti-pattern** was added that conflicts with a skill's default
  post architecture → flag it and propose a skill update
- If a **removed entry** was previously hard-coded into a skill → flag it
- Otherwise, skills reference the anti-patterns file dynamically — no skill edits needed

Report:

```
## Anti-Patterns Updated

### Changes
- [Added/Removed/Amended]: [entry] in [table]

### File
- content-anti-patterns.md → v[X.Y]

### Propagation
- [No skill changes needed / Skill X needs update because Y]
```
