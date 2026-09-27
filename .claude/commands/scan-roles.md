---
description: "Signal scanner — aggregate roles from legitimate sources (ATS boards APIs — Greenhouse/Lever/Ashby/Workable via curl — primary; + Apollo-at-targets, credit-gated, optional), dedupe on the ATS job-id, score against Alex's Target-Role ICP (me-model §1.5), and track them in a Notion Roles DB. Notion-only, human-in-the-loop. No LinkedIn scraping."
argument-hint: "[optional: role focus + location + recency, e.g. 'GTM engineer + RevOps, NYC + remote, last 3 days']"
---

# /scan-roles — Role Radar

Run the **role-radar** methodology to find, score, and track relevant roles. Methodology in `.claude/skills/role-radar/SKILL.md`.

**Input (all optional):** role focus, location, recency. Defaults: target archetypes, NYC + Remote-US, last 7 days.

## Trigger
Runs when Alex types `/scan-roles [args]` or says "find roles", "run role radar", "what jobs are out there this week".

## Orchestration shape
Single-thread skill run. Execute `.claude/skills/role-radar/SKILL.md` end-to-end:
1. **Setup (first run):** confirm the Notion Roles DB schema via `notion-fetch` (it exists since 2026-09-08).
2. **Step 1 — Pull (parallel):** ATS boards APIs (Greenhouse/Lever/Ashby/Workable via `curl`+`jq`, PRIMARY — company→ATS registry in `target-companies.md`; raw JSON projected before it enters context) · Apollo-at-targets (credit-gated, only when asked). Dice and RSS.app were removed 2026-09-27 (unused).
3. **Step 2 — Dedupe** by natural key `{ats_vendor}:{ats_job_id}` (content_hash `title|company` fallback for non-ATS); one bulk SQL read of the Roles DB for `Content Hash` (`notion-query-data-sources` works but is quota-capped — one read per run), then the title|company fallback (YED-224) so legacy rows are re-keyed, not duplicated.
4. **Step 3 — Score** each role 0–100 against the Target-Role ICP rubric v2 — **by role mechanism, not title** (role-mechanism · AI-native-tier · **leverage/support** incl. PLG · AI-multiplier fit · location/culture). Tier **A≥85 / B 60–84 / C 40–59 / drop<40** (v2.4 — raised from 78 on 2026-09-11; see SKILL Step 3).
5. **Step 4 — Present ranked roles. STOP for approval.**
6. **Step 5 — Write approved** roles to Roles DB (`Status = new`).
7. **Step 6 — Close out** — summary by tier, source gaps, the rows-in-DB-but-not-on-the-boards count (YED-224), + offer A-tier contact pull (`voice-radar`).

## Guardrails
- Legitimate sources only — public ATS board APIs (and Apollo on request). No LinkedIn scraping, no saved-search feeds.
- **Apollo credit confirmation** (exact): `"This will consume 1 credit. Do you want to proceed?"` (or "N credits" for a batch). No call without approval.
- Human-in-the-loop before any Notion write. Search before create. Honest source gaps; no fabricated roles.

## What comes next
| Want to... | Do |
|---|---|
| Pull hiring managers/contacts at A-tier companies | `voice-radar` / Clay enrich (credit-gated) |
| What's trending (talking points for outreach) | `/scan-trends` |

## Ground truth
- Methodology: `.claude/skills/role-radar/SKILL.md` (rubric v2 self-contained). ICP source of truth: `.claude/references/me-model.md` §1.5. Target companies + ATS registry: `.claude/references/target-companies.md`. Program: Linear "Job-Search Engine" (YED-146…152).
