---
description: "Manual outcome-tagging ritual (<5 min): for published Content Drafts with an assigned Goal but no Outcome, pull the realized signal (HubSpot for connections/meetings; LinkedIn-native numbers for reach/engagement), grade Outcome vs Goal/Target, and write it back. Closes the acted-on-value loop. HITL, Notion-only, no scraping."
argument-hint: "[optional: scope, e.g. 'last week's posts' or an event/artifact name]"
---

# /tag-outcome — Outcome-tagging ritual

Run the **tag-outcome** methodology to record realized outcomes against assigned goals. Methodology: `.claude/skills/tag-outcome/SKILL.md`.

## Trigger
Runs when Alex types `/tag-outcome [scope]`, says "tag outcomes", "did my posts hit their goals", or as a sub-step of the weekly review (US-7).

## Shape (single-thread, HITL)
1. **Find the backlog** — `notion-search` Content Drafts for published items with a `Goal` (≠ internal) and `Outcome` empty/`pending` (NOT `notion-query-data-sources`).
2. **Pull the signal by Goal** — connection/meeting → HubSpot (`search_crm_objects` on the draft's person); reach/engagement → ask Alex for the LinkedIn-native number vs `Target`.
3. **Grade vs Target. STOP for confirmation** — hit / partial / miss / pending (Alex confirms or overrides).
4. **Write back** — `notion-update-page`: `Outcome`, `Outcome Value` (signal + source), `Outcome Date` = today.
5. **Close out** — hit/partial/miss/pending counts + trend.

## Guardrails
- Manual + HITL, **<5 min** — assist, don't automate; never make it heavier.
- Legitimate-only (HubSpot + LinkedIn native, no scraping). **No fabricated numbers** — not observable yet ⇒ leave `pending`.
- `internal` goals → `Outcome = na`.

## Ground truth
- Methodology: `.claude/skills/tag-outcome/SKILL.md` · assigned-goal side: `content-patterns/goal-tagging.md`
- Feeds the north-star (US-6 Hub dashboard) and nests in the weekly review (US-7).
