---
description: "Recompute relevance_score for every topic in the Market-Intelligence graph — recency decay × engagement, plus an upcoming-event proximity boost. Pure math, no LLM, no API tokens. Turns the graph's flat list into a real evolving ranking (the dashboard + /morning-refresh sort by this). Standalone; also the final step /morning-refresh calls. YED-115 prereq 2."
argument-hint: "[--dry-run to preview without writing | --top N to show N in the report]"
---

# /recompute-relevance — Relevance Recompute

Runs the deterministic recompute engine over the MI graph and writes an updated `relevance_score`
per topic. **Free — pure arithmetic, no model inference, no API tokens.** This is what makes "what's
rising × relevant" real instead of a raw `engagement_count` proxy.

## Trigger
`/recompute-relevance [--dry-run|--top N]`, or Alex says "recompute relevance", "refresh the rankings".
Also invoked as the last step of `/morning-refresh` (so daily accumulation → fresh ranking automatically).

## What it does (the engine: `.claude/scripts/recompute_relevance.py`)
For every topic:
```
relevance = recency_decay(last_engaged_at)     # 14-day half-life — recent signals weigh more
          × engagement_weight(engagement_count) # 1 + ln(1+count) — more signals, log-scaled
          + event_proximity_boost               # linked to an upcoming ATTENDED event ≤30d → boost
```
Then it writes back **only the topics whose score changed** (skips no-op churn). Idempotent — same data,
same scores; safe to re-run.

## Run it
```bash
python3 .claude/scripts/recompute_relevance.py            # live: recompute + write changed topics
python3 .claude/scripts/recompute_relevance.py --dry-run  # preview only, no writes
python3 .claude/scripts/recompute_relevance.py --top 25   # show N in the report
```
Reports: topics scanned · changed · written · upcoming-event boosts · the Top-N ranked · active-vs-dormant count.

## Deliberately deferred (fast-follows, not in this V1)
- **`coverage_penalty` ("uncovered")** — down-rank topics already posted about recently (needs the
  Content-Drafts join). The "uncovered" leg of *rising × relevant × uncovered*.
- **Confidence-weighting** — weight `engagement` by each signal's `confidence`/`source_count`, not just
  the raw count, so a strong signal outranks a weak one (differentiates same-day topics sooner).
- **`pg_cron` in-database version** — a Postgres function on a schedule; the REST script is the V1 (no DDL,
  no dashboard step, runnable now).

## Failure modes
- **Graph unreachable / key bad / project paused** → the script exits with the REST error; nothing partially written beyond the topics already PATCHed (each write is independent). Re-run when reachable.
- **A single topic write fails** → logged (`⚠️ write failed`), the rest continue.
- **No signals yet / first run** → most topics compute to 0 (correct — nothing active); only recently-engaged topics score > 0.

## Ground truth / references
- Engine: `.claude/scripts/recompute_relevance.py`
- Graph contract: `.claude/references/market-intel-spine.md`
- Design of record: **YED-115** (this is prereq 2 — the decay+reinforce recompute)
