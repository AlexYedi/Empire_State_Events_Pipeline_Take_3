---
description: "Messaging brief — headline, pillars, proof points, hook bank, CTA strategy. Use when launching or repositioning an offer, or standing up copy for a persona/channel, before writing the actual copy. Fans out positioning + copy specialists from this thread, then synthesizes the brief."
argument-hint: "[goal + persona + offer, e.g. 'pipeline, RevOps, AI copilot']"
---

# /create-messaging-brief

Produce a **messaging brief** — the upstream artifact `/generate-channel-copy` consumes. Multi-agent fan-out
runs **from this parent thread** (subagents cannot spawn subagents — SDK constraint); this file is the
orchestration shape. Conforms to `.claude/references/command-orchestration-convention.md`.

## Step 1 — Intake & validate (this thread, not a subagent)
Collect and confirm:
1. **goal** (required) — awareness | pipeline | expansion | reposition. If missing, ask.
2. **persona** (required) — target audience (role + segment). If missing, ask.
3. **offer** (required) — product/feature/value prop. If missing, ask.
4. **proof_assets** (optional) — customer quotes, metrics, analyst notes. Keep verbatim as a `VERBATIM
   SOURCE` block; **do not fabricate proof** — if none provided, the brief marks proof points as
   `[NEEDS PROOF]` rather than inventing numbers.
5. **channels** (optional) — email | ads | landing | social; scopes the hook bank.

## Step 2 — Fan-out (this thread, parallel `Agent` calls in one message)
Dispatch in parallel; each leads with goal + persona + offer + the verbatim proof block:
1. **copy-strategist** — message architecture: headline candidates, 3 message pillars, supporting
   statements, CTA-by-funnel-stage. Compose `alex:message-architecture` + `alex:positioning-messaging`.
2. **conversion-copywriter** — the hook bank: multiple hook formulas per channel, tuned to persona pain.
   Compose `alex:copy-frameworks`.
Wait for both. If one is thin, re-invoke just that one — don't restart.

## Step 3 — Synthesize + voice-check (serial, this thread)
Assemble inline: headline + pillars + proof matrix (with `[NEEDS PROOF]` flags) + hook bank + CTA strategy +
an experiment backlog (candidate copy tests with the KPI each would move). Then dispatch **voice-editor**
(synthesis-only) for one guideline/voice pass. Compose `alex:voice-guidelines`.

## Step 4 — Output destination (NAME IT)
- **`conversation`** (default) — present the full brief.
- **Handoff:** the brief is structured so `/generate-channel-copy` can consume it directly (pillars → hooks →
  CTAs map 1:1). Offer that as the next step.
- Offer a Notion write (Content Drafts or a messaging page) as an explicit follow-up if Alex wants it archived
  for the comment-review loop — parent-thread MCP only, `notion-search` not `notion-query-data-sources`.

## Failure modes
- **A required input missing** — stop and ask; the brief is persona/offer-specific.
- **No proof assets** — proceed but mark every proof point `[NEEDS PROOF]`; never fabricate metrics/quotes.
- **A specialist returns thin** — re-invoke just that one.

## Ground-truth references
- `.claude/references/command-orchestration-convention.md` — the required skeleton
- Downstream: `/generate-channel-copy` (consumes this brief), then `/test-and-report`
- Agents: `copy-strategist`, `conversion-copywriter`, `voice-editor`
- Skills: `alex:message-architecture`, `alex:positioning-messaging`, `alex:copy-frameworks`, `alex:voice-guidelines`
