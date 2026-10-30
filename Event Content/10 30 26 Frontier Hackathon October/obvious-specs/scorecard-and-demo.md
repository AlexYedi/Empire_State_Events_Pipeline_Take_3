# Live scorecard + demo outline (fill in as you build)

## 8-control scorecard vs the pre-event prediction
Your bar: 5 of 8 solo. The prediction said 4.

| Control | Predicted | Actual (solo / help / out) | Evidence (PR #, minute, what happened) |
|---|---|---|---|
| Specs | solo | | |
| Context | solo | | Track A result goes here |
| Skills | solo | | |
| QA | help | | |
| CI | out | | did secret-scan / public-safety run on its PRs? |
| Review | solo | | |
| Loops | help | | |
| Design systems | out | | Long Reads (04) is the test |

## Ladder results

| Tier | Spec | Executables | PRs opened | Merged | Needed me? (where, why) |
|---|---|---|---|---|---|
| T1 | 01 hub fixes | 9 | | | |
| T1 | 02 pipeline tests | 8 | | | |
| T2 | 03 mid builds | 3 | | | |
| T3 | 04 long reads | 4–5 | | | |
| T4 | 05 Rooms MCP | 3–4 | | | |

Baseline: ~6–7 merged PRs on an ordinary active day (74 + 13 merges over 9/27–10/27).

## Demo, 3 minutes (draft; Claude updates it as results come in)
1. **0:00 The setup (20s).** A non-engineer, two real public repos, and one question: how complex a build can the factory take before it needs a human?
2. **0:20 The input (30s).** Show the ladder table. Thirty executables written as specs, not tickets. Specs are the lever.
3. **0:50 The rules probe (30s).** The CLAUDE.md vs AGENTS.md result, in one line.
4. **1:20 The ladder (60s).** Show where it ran solo and where it stopped. Demo the highest tier that shipped (the Long Reads page, or the MCP server in the Inspector).
5. **2:20 The number (25s).** Merged today vs the ~6–7 baseline.
6. **2:45 The finding (15s).** "It stops being autonomous at ___ because ___."
