---
description: "Process the mini's memory inbox under the promotion rubric (YED-447): auto-promote safe new notes into the laptop's memory, auto-draft public-safe system notes as a docs PR (draft, Alex publishes), auto-drop duplicates, and raise only edge cases to Alex. Run on the LAPTOP; /freshen calls it when the inbox isn't empty."
---

# /memory-inbox

Notes learned in mini sessions land in the mini's memory inbox (YED-411 step 4). The laptop's memory is the master copy, so this runs **on the laptop**. Alex approved the rubric below on 2026-11-18. It decides what happens automatically; only the edge cases reach him.

## Steps

1. `python3 ops/mini-runner/memory_inbox.py fetch --dest "$(mktemp -d)"`, then `scan <that dir>`. If there are 0 items, say so and stop.
2. Pair each note with its index line, which comes from the `MEMORY.md` / `MEMORY.additions.md` items in the same date folder.
3. Judge each note against the rubric. For rule 2, read the laptop memory (`~/.claude/projects/<slug>/memory/`), the repo `CLAUDE.md`, `.claude/references/` and the decisions-not-to-reopen memory. `topic_hints` and `privacy_hits` are inputs, not verdicts.
4. Act on each verdict. Do every PROMOTE and DROP before raising anything, then present the RAISE items together.
5. Archive every item you acted on: `memory_inbox.py archive <rel>... --action <promoted|promoted+docs-pr|dropped-duplicate|dropped> --reason "<one line>"`. Archive the index-line items with their note. Raised items stay in the inbox until Alex decides.
6. Summary: one paragraph as a comment on this week's Friday-review Linear issue (YED-447 or its successor), e.g. "promoted 3, dropped 1 (duplicate), 1 docs PR (#n), 1 raised: …". Tell Alex the same in one line.

## The rubric

**PROMOTE to the laptop memory automatically only if ALL hold:**
1. **New:** no laptop note has this file name (`laptop_has_same_name` is false). A mini edit of an existing note is always RAISE.
2. **Not already covered:** no laptop note, `CLAUDE.md` or repo doc states the same fact. If one does, it's DROP (duplicate).
3. **No contradiction:** it doesn't conflict with or change guidance in another note, `CLAUDE.md`, decisions-not-to-reopen or the invariants.
4. **Privacy scan clean** (`privacy_hits` empty; same patterns as the spine guard).
5. **Not a gated topic:** privacy/PII handling, secrets, spend, publishing, CRM writes, hooks/settings, merge policy. These stay under Alex's control.
6. **Your confidence is at least 80%** on rules 2–5.

Do it with `memory_inbox.py promote <file> --index-line "<the note's own index line>"`. That keeps the mini's line identical, so the "awaiting promotion" marker clears at the next sync.

**DOCS LANE: also draft a docs PR if, on top of rules 1–6:**
- **It's about the system, not about Alex:** machine layout, pipeline behaviour, tool gotchas. Never preferences, the job search, people, GKY or me-model content.
- **It passes a stricter public-safety read:** no people's names, no companies from private lists, nothing marked private or off the record. The repos are public (invariant 4).
- **It has an obvious home:** a line or short section in an existing file (`mini-runner.md`, `platform-constraints.md`, a skill reference). Never a new document.

Open it as a **draft** PR (`gh pr create --draft`) from a worktree cut from `origin/main`, never from the main checkout. The factory gate can't auto-merge a draft, so Alex publishes it by marking it ready and merging. If a note fails a docs rule, promote it to memory only, and say why in the summary.

**DROP automatically:** duplicates (rule 2). Archive them with the covering note or doc named in the reason. A dropped mini-only note also leaves the mini's memory: pass `--drop-from-mini-memory`.

**RAISE to Alex:** everything else (a failed rule 1, 3, 4, 5 or 6). For each, give a short brief: the note in two lines, which rule tripped and why, the options (promote / promote edited / drop), and your recommendation. Act on his answer, then archive.

Never: write to any repo's `main`, change an existing laptop note without Alex, or delete an inbox item without archiving it.
