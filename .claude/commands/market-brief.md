---
description: "Render the Monday Market Brief for an ISO week from the knowledge graph (read-only), then show it to Alex for review. Seven sections: bottom line, this week's rooms, themes moving (with the shuffle null), new to the graph, room vs market, conflicts, graph health. Publishing to Notion is a later step."
argument-hint: "[--week 2026-W47] [--sweeps DIR] [--today YYYY-MM-DD]"
---

# /market-brief — the Monday Market Brief (YED-384)

The weekly reader of the knowledge graph. The script does all the work and is **read-only**: GETs through
`spine_client.req`, no database writes, no Notion. The brief is a thing Alex reads, not a queue he works
(2026-11-04 ruling).

## Steps
1. **Render** from the repo root (the `main` checkout, so `Event Content/` and `.claude/.state/research/` are
   the live ones; from a worktree add `--root <main checkout>`):
   ```bash
   .venv/bin/python .claude/scripts/market_brief.py $ARGUMENTS
   ```
   Default week: the week of the next Monday. Output:
   `.claude/.state/market-briefs/market-brief-<isoweek>.md` (gitignored). Exit 2 means an email- or
   phone-shaped string reached the brief and nothing was written: find the source row, do not edit the guard.
2. **Show** the rendered file to Alex in full. Do not summarize or rewrite it; the numbers and their baselines
   are the point. Call out any section that printed "no data yet" and its reason.
3. **Stop.** Publishing to Notion (a `documents` row, `source_type='scan_digest'`, through `notion-writer`
   from a parent-built payload) is a later step and is not wired here.

## Reading it
- Every number sits beside its do-nothing baseline. When "rising" themes are not above the shuffle null, the
  brief says "no information"; take it at its word.
- Sweep items show company, kind, date and source host only. Headlines stay in the manifest (web text).
- Person names never appear, except public speakers named in an event folder title.
