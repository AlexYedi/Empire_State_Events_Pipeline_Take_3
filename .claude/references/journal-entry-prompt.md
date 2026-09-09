# Journal-entry prompt — the in-the-moment prose capture (shared module)

The reusable "capture Alex's voice at a break point" routine. Invoked two ways:
- **Auto** — as the closing step of `/dod-close` (every non-trivial build close-out).
- **Manual** — the standalone `/journal-entry` command, for any break point that isn't a full DoD
  close (a content/carousel ship, a milestone, a scaffold).

It exists because the build journal's **facts** self-instrument (git + telemetry → `build_journal.py`),
but the **prose sidecar** (`.claude/data/build-journal-prose.json`) is human-owned and lapses silently
when it depends on the agent *remembering* to write it (it did: Aug 7→21, and again Aug 26→Sep 9).
This turns "remember to write prose" into a triggered ritual that pulls Alex's actual take while it's
fresh — richer than a facts-only day, and impossible to skip silently.

## Operating principle — prep-then-ask (mirrors steering-interview v2)
Do **not** ask generic cold questions. **Draft first from the session's own facts, then ask ≤3
sharpening forks** where the draft is genuinely uncertain or where only Alex's take adds what the
artifacts can't. Informed forks ("the PR says scaffold — did the demo actually land, or is it still
scaffold?") beat blank prompts. Keep the loop open: one tight round, Alex can answer selectively or
say "ship as drafted."

## Shape (single-thread, main conversation — never a subagent; MCP/interaction needs the parent)

1. **Date + scope.** Date = today (UTC, `date -u +%Y-%m-%d`). Gather what shipped *today* from facts:
   ```
   git -C <repo> log --since=<today>T00:00 --pretty='%ad | %s' --date=short   # both repos
   ```
   Note the merged PRs (`Merge pull request #N`) and the feature commits + YED- refs. This is the
   same substrate `build_journal.py` reads — so the prose you write will sit over matching facts.

2. **Pre-draft the candidate entry** from those facts — a `headline` + a `summary` of **≤3 lines**
   answering **WHAT** shipped / **WHY** it mattered (the friction removed or problem solved) /
   **VALUE** to a reader (hiring manager or peer). Honest voice, no fluff, no overclaim; name what was
   hard and what's still open. Match the existing entries' register (read a couple from the sidecar).
   For a multi-ship day, separate ships with `  — Second ship: …`.

3. **Ask ≤3 sharpening forks** — only where the draft can't be sourced from artifacts. Good targets:
   - the non-obvious insight / what you'd tell another builder;
   - reception or outcome the git history can't know (did the demo land? did the post resonate?);
   - a positioning call that's Alex's to make (candor level on a public, hiring-manager-facing surface);
   - which of two framings is true ("reps I built" vs "demo I ran").
   Present the draft **and** the forks together. Alex answers what he wants.

4. **Compose the final entry** by folding his answers into the draft. Keep ≤3 lines. If he added
   nothing, ship the draft as-is (honest facts-based prose is still a real entry).

5. **Write the prose** — merge into `.claude/data/build-journal-prose.json`, keyed by today's date:
   - Validate JSON after writing (`python3 -c "import json;json.load(open(...))"`).
   - If the date key already exists: this is a **second ship** for the day — append to the existing
     summary with a `  — ` separator (don't clobber), unless Alex says replace.
   - Newest date first for readability (keys are a dict; order is cosmetic but kept tidy).

6. **Regenerate the facts+prose journal:**
   ```
   python3 .claude/scripts/build_journal.py        # writes ../empire-state-hub/src/data/build-journal.json
   ```
   Confirm today's entry now renders **curated (✍)** in the summary line.

7. **Named output + hand-off (the publish gate).** Report: the date, headline, the shipped PR chips,
   and — explicitly — that the **`/journal` page only goes live after the hub repo is committed +
   deployed**. That is a separate, outward-facing step: **flag it, do not auto-deploy** (branch-first +
   Alex's GitHub Desktop flow own the commit; Vercel owns the deploy). Offer to stage the hub change,
   but leave the push/deploy to Alex.

## Failure modes
- **No shipped facts today** (pure research / churn) → say so; offer a prose-only entry (the generator
  renders any date that has curated prose even with zero PRs), or skip. Don't invent a ship.
- **Subagent context** → refuse; this is interactive + touches the sidecar and generator in the parent.
- **Generator errors / hub path missing** → write the prose anyway (it's the durable artifact) and
  report that regeneration must be re-run when the hub checkout is present.
- **Prose JSON invalid after edit** → restore and re-apply as a single well-formed block; never leave
  the sidecar unparseable (the generator falls back to facts-only and the day goes voiceless).

## Ground truth
- Facts generator: `.claude/scripts/build_journal.py` (squash `(#N)` **and** merge-commit PRs).
- Prose sidecar: `.claude/data/build-journal-prose.json` (human-owned; this routine writes it).
- Auto-refresh Stop hook: `.claude/hooks/build-journal-refresh.sh` (regenerates + nudges on change).
- Public surface: the `/journal` page on **empire-state-hub** (separate repo → separate deploy).
- System issue: YED-119 (self-instrumenting build journal).
