# A/B protocol — does the Knowledge Substrate make event prep better? (YED-172)

**Status:** DRAFT for Alex's review · 2026-09-19 · decides ADR-10 → Accepted/rework · deadline 2026-09-26
**Pre-registered:** the scoring rubric and decision rule below are fixed BEFORE any pack is seen. Changing them after seeing results voids the test.

## The question
Does the substrate pack (`retrieve.py --lens event`, reads the claims graph) give better *prior context* for an event than the legacy pull (Step 1.7a: Notion loop + graph reads)? "Better" = more useful in the room, fewer errors.

**Why at the pack level, not the whole brief:** the pack is the only thing that differs between arms. Running the full brief twice doubles cost (4 research agents × 2) and adds noise (the agents vary run to run), which would hide the signal we want.

## Arms (identical except the one variable)
| Arm | Input to `knowledge-conditioning` | Output |
|---|---|---|
| **A — legacy** | Step 1.7a pull only | Prior-Context Pack A |
| **B — substrate** | `retrieve.py` pack only | Prior-Context Pack B |

Same conditioner agent, same prompt, same verbatim invite text, same triage plan, same "Alex's focus" line. Only the prior-knowledge input differs.

## Blinding
1. Both packs are produced, then a coin flip (`random.choice`) assigns them the labels **X** and **Y**.
2. The key (X→A/B) is written to `.claude/.state/<session>.ab_key` and **not shown** until both raters have scored.
3. Alex sees two pages labelled X and Y only — no source tags that reveal the arm (the audit lines are stripped; "graph=rpc", "claims-layer" and similar tells are removed).

## Raters
- **Alex** (primary, decides).
- **Claude/Sonnet** (second rater, same rubric, same blinding). **Not Gemini** — the Gemini seat is under triage for rubber-stamping (1.0 on every criterion, twice) and is excluded until it's fixed.

## Scoring rubric (per pack, per event)
| # | Criterion | Scale |
|---|---|---|
| 1 | **Use in the room** — would I actually use items from this in a conversation, a question, or deciding who to find? | 1–5 |
| 2 | **Errors** — count of items that are wrong, stale presented as current, or misattributed | count (lower is better) |
| 3 | **New to me** — things I didn't already know or remember | 1–5 |
| 4 | **Changed my plan** — did it change a question, talking point, or target person? | yes / no + which |
| 5 | **Overall preference** | X / Y / tie |

## Decision rule (fixed now)
Across the two events:
- **B replaces A** if B is preferred or tied on **both** events **and** B's error count ≤ A's on both. → retire the legacy pull, ADR-10 → Accepted, start the other lenses (interview-prep, content).
- **Keep A, rethink B** if A is preferred on **both**.
- **Split (1–1)** → run a third event (Wed 9/23 Databricks "Closing the AI Context Gap" or the next available).
- **Indistinguishable** (ties on both, similar scores) → that is a real result: the substrate doesn't elevate prep yet. Stop and rethink before building more lenses.

## Events
1. **Mon 9/21 — AI Show and Tell (Global AI NY @ Microsoft).** Agent evaluation / governance / multi-agent. Probe 2026-09-19: graph returns 30 relevant claims from a thin seed, 0 prior occasions with these people → tests *topic* recall.
2. **Wed 9/23 — Clay: Agentic GTM with Grok Bot (livestream).** Graph holds 5+ Clay-related events and people → tests *entity/relationship* recall. Different strength than event 1, which is the point.

## Procedure (per event)
1. `/event-deep-research` Steps 1–1.6 as normal (roster from the Luma page, triage).
2. Step 1.7a (legacy) and 1.7a-S (substrate) both run; their raw outputs are saved separately.
3. Conditioner runs **twice**: A-only, B-only → Pack A, Pack B.
4. Blind + label X/Y; publish both to one Notion page for Alex; Sonnet scores independently.
5. Alex scores (≈10 minutes) → key revealed → both scores logged to `.claude/evals/logs/<date>-ab-yed172-<event>.jsonl`.
6. The brief proceeds from Alex's preferred pack (or both merged on a tie) — prep is never worse than today.

## Guards
- **No new producers during the test window** (the pre-event write path is built *after* Wednesday's run) so the graph doesn't change mid-experiment except through the normal post-event flow.
- Monday's own post-event claims land before Wednesday's run — that's the system working as designed, not contamination; noted in the log.
- If `retrieve.py` exits 5 (loud failure) on an event, that event counts as an **A win** and the failure is logged, not hidden.

## Cost
One extra conditioner run per event (a few minutes, ~20–30k tokens) + ~10 minutes of Alex scoring. No extra research fan-out.
