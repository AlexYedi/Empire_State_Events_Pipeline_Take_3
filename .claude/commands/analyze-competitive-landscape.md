---
description: "Executive competitive-landscape brief — threat levels, differentiators, counter-plays. Use when sizing up rivals in a segment before a GTM push, board update, or competitive deal. Fans out research + battlecard specialists from this thread, then synthesizes an exec brief."
argument-hint: "[scope + audience + window + format, e.g. 'enterprise-saas, exec, 30d, deck']"
---

# /analyze-competitive-landscape

Produce an executive **competitive-landscape brief** — threat levels, differentiators, counter-plays.
Multi-agent fan-out runs **from this parent thread** (subagents cannot spawn subagents — SDK constraint);
this file is the orchestration shape. Conforms to `.claude/references/command-orchestration-convention.md`.

## Step 1 — Intake & validate (this thread, not a subagent)
Collect and confirm:
1. **scope** (required) — product line, segment, or geo focus. If missing, ask; don't guess.
2. **audience** — `exec` (default) | product | sales | marketing.
3. **window** — 30d (default) | 60d | quarter | custom.
4. **format** — `conversation` (default) | deck | memo.
5. **named competitors** (optional) — if Alex names rivals, keep them as a `VERBATIM SOURCE` block carried
   into every dispatch. If none named, Step 2's research pass identifies the top 3–6 first.
6. **signals** (optional) — URLs/files (research, CRM export, win/loss) to feed the specialists.

## Step 2 — Fan-out (this thread, parallel `Agent` calls in one message)
Dispatch in parallel; each dispatch leads with scope + verbatim competitor block + window:
1. **competitive-signal-scanner** — last-`window` market signals per competitor (funding, exec moves,
   launches, POV shifts). Returns a tagged signal log (severity + confidence + relevance).
2. **battlecard-program-manager** — per-competitor differentiators, objections, and counter-plays vs Alex's
   positioning. Returns differentiation + plays.
3. (If no competitors were named) **research-analyst** — identify the top 3–6 rivals in `scope` first, so
   1 & 2 have targets. Run this serially *before* 1 & 2 when the field is unknown.
Wait for all to return. If one is thin, re-invoke just that one with deeper scope — don't restart.

## Step 3 — Synthesize (delegate packaging to market-insights-director)
Dispatch **market-insights-director** (synthesis-only: text in, text out, no further dispatch) with all
specialist returns + `audience`. It assembles: threat matrix (competitor × severity × confidence),
differentiation map, and a prioritized counter-play **action register** (play · rationale · owner-hint).
Compose `alex:executive-briefing-kit` for the exec narrative shape.

## Step 4 — Output destination (NAME IT)
- **`conversation`** (default) — present the brief inline: threat matrix, differentiators, counter-plays.
- **`deck`** — also generate a Gamma deck (`mcp__claude_ai_Gamma__generate`, `format: "social"` for 4:5),
  one slide per section (CLAUDE.md rule 13 — Gamma is the default visual generator).
- **`memo`** — present as a structured long-form memo in conversation.
This command does **not** write to HubSpot/CRM (Static Lists unavailable via MCP; CRM writes are a separate,
judgment-gated step). If Alex wants the brief in Notion for review, offer it as an explicit follow-up.

## Failure modes
- **scope missing** — stop and ask; the whole brief depends on it.
- **No competitors identifiable** — say so, present what research found, and ask Alex to name targets.
- **A specialist returns thin** — re-invoke just that one; note the gap in the brief rather than inventing signals.
- **Gamma unavailable** — fall back to the `conversation` deliverable; don't block.

## Ground-truth references
- `.claude/references/command-orchestration-convention.md` — the required skeleton
- Agents: `competitive-signal-scanner`, `battlecard-program-manager`, `market-insights-director`, `research-analyst`
- Skills: `alex:executive-briefing-kit`, `alex:competitive-analysis`, `alex:battlecard-system`
