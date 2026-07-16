---
description: "End-to-end market study — TAM/SAM/SOM, trends, competitor map, scenarios. Use when entering a new market/category or pressure-testing a thesis and you need the full landscape, not a quick scan. Fans out research + modeling specialists from this thread, then synthesizes."
argument-hint: "[scope + regions + horizon + format, e.g. 'AI Sales Tech, na,emea, 3y, deck']"
---

# /run-market-landscape-study

Produce a full **market landscape study** — sizing, trends, competitor map, scenarios. Multi-agent fan-out
runs **from this parent thread** (subagents cannot spawn subagents — SDK constraint); this file is the
orchestration shape. Conforms to `.claude/references/command-orchestration-convention.md`.

## Step 1 — Intake & validate (this thread, not a subagent)
Collect and confirm:
1. **scope** (required) — category, segment, or thesis. If missing, ask; don't guess.
2. **regions** (required) — comma-separated markets.
3. **horizon** — 1y | 3y (default) | 5y.
4. **format** — `conversation` (default) | deck | memo.
5. **sources** (optional) — URLs / analyst reports / internal docs; keep any pasted text as a
   `VERBATIM SOURCE` block carried into every dispatch.
Restate the hypotheses/KPIs the study must answer before proceeding (this frames every specialist).

## Step 2 — Fan-out (this thread, parallel `Agent` calls in one message)
Dispatch in parallel; each leads with scope + regions + horizon + the verbatim source block:
1. **research-analyst** — desk research: TAM/SAM/SOM data points, funding signals, macro forces, adoption
   evidence, with confidence levels + sources. (Compose `alex:research-brief-blueprint` for methodology.)
2. **competitive-signal-scanner** — the competitor map: who's in `scope`, recent moves, positioning, share
   shifts, with citations.
Wait for both. If one is thin, re-invoke just that one with deeper scope — don't restart.

## Step 3 — Model, then synthesize (serial, this thread)
1. Dispatch **quant-insights-architect** (serial, after Step 2) with the research + competitor returns:
   build the sizing + scenario model (growth, adoption curves, share shifts) with **explicit assumptions +
   sensitivity notes**. Compose `alex:market-scenario-modeler`. No fabricated numbers — every figure traces
   to a Step-2 source or a stated assumption.
2. Dispatch **insights-research-director** (synthesis-only: text in, text out, no dispatch) to package the
   study: landscape narrative, competitor matrix, scenario table, and a **recommendation + action register**.

## Step 4 — Output destination (NAME IT)
- **`conversation`** (default) — present: size, trends, competitor matrix, scenarios, recommendations.
- **`deck`** — also a Gamma deck (`mcp__claude_ai_Gamma__generate`, `format: "social"` for 4:5), one section
  per slide (CLAUDE.md rule 13).
- **`memo`** — structured long-form in conversation.
The scenario model is presented inline as a table (assumptions + sensitivity). This command does not write to
external systems; offer a Notion write as an explicit follow-up if Alex wants it archived.

## Failure modes
- **scope/regions missing** — stop and ask.
- **Thin data on a niche category** — present what's grounded, label the gaps honestly, and flag the low-
  confidence cells rather than inventing sizing (no fabricated numbers).
- **A specialist returns thin** — re-invoke just that one; don't restart.
- **Gamma unavailable** — fall back to the `conversation` deliverable.

## Ground-truth references
- `.claude/references/command-orchestration-convention.md` — the required skeleton
- Agents: `research-analyst`, `competitive-signal-scanner`, `quant-insights-architect`, `insights-research-director`
- Skills: `alex:research-brief-blueprint`, `alex:market-scenario-modeler`, `alex:insights-repository-kit`
