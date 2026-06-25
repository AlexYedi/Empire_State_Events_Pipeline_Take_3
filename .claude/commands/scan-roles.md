---
description: "Signal scanner — aggregate relevant roles from legitimate sources (Dice MCP, Apollo job-postings, RSS.app feeds from saved LinkedIn searches), dedupe, score against Alex's ICP rubric, and track them in a Notion Roles DB. Notion-only, human-in-the-loop. No LinkedIn scraping."
argument-hint: "[optional: role focus + location + recency, e.g. 'GTM engineer + RevOps, NYC + remote, last 3 days']"
---

# /scan-roles — Role Radar

Run the **role-radar** methodology to find, score, and track relevant roles. Methodology in `.claude/skills/role-radar/SKILL.md`.

**Input (all optional):** role focus, location, recency, and any RSS.app feed URLs. Defaults: target archetypes, NYC + Remote-US, last 7 days.

## Trigger
Runs when Alex types `/scan-roles [args]` or says "find roles", "run role radar", "what jobs are out there this week".

## Orchestration shape
Single-thread skill run. Execute `.claude/skills/role-radar/SKILL.md` end-to-end:
1. **Setup (first run):** create the Notion Roles DB (HITL — approve schema once). Note RSS.app feed setup.
2. **Step 1 — Pull (parallel):** Dice (`search_jobs`, free) · RSS.app feeds (`WebFetch`, manual paste) · Apollo job-postings (credit-gated, optional).
3. **Step 2 — Dedupe** by `content_hash` (title|company); `notion-search`-scoped dedup vs. Roles DB (NOT `notion-query-data-sources`).
4. **Step 3 — Score** each role 0–100 against the self-contained ICP rubric (archetype · AI-nativeness · Tier-1 · GTM-alpha · logistics). Tier A≥75 / B 55–74 / C 35–54 / drop<35.
5. **Step 4 — Present ranked roles. STOP for approval.**
6. **Step 5 — Write approved** roles to Roles DB (`Status = new`).
7. **Step 6 — Close out** + offer A-tier contact pull (`voice-radar`).

## Guardrails
- Legitimate sources only — RSS.app reads a saved-search feed, never the LinkedIn account.
- **Dice AI disclosure** is mandatory on results: *"These job listings were found using AI-powered search. Verify details directly with employers before applying."*
- **Apollo credit confirmation** (exact): `"This will consume 1 credit. Do you want to proceed?"` (or "N credits" for a batch). No call without approval.
- Human-in-the-loop before any Notion write. Search before create. Honest source gaps; no fabricated roles.

## What comes next
| Want to... | Do |
|---|---|
| Pull hiring managers/contacts at A-tier companies | `voice-radar` / Clay enrich (credit-gated) |
| What's trending (talking points for outreach) | `/scan-trends` |

## Ground truth
- Methodology: `.claude/skills/role-radar/SKILL.md` (the ICP rubric is self-contained there).
