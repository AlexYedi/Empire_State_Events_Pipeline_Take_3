---
description: "Signal scanner — who's trending / social listening. Seeds a watchlist from Alex's existing Notion People DB, tracks those voices OFF LinkedIn (Substack/blog/GitHub/Reddit/podcast RSS + Google Alerts), optionally enriches via Apollo/Clay (credit-gated), and flags net-new voices. Notion-only, human-in-the-loop. Legitimate-only — no LinkedIn/X scraping."
argument-hint: "[optional: watchlist scope + topic lens + window, e.g. 'people from last 3 events, evals, last 2 weeks']"
---

# /scan-voices — Voice Radar

Run the **voice-radar** methodology to track who in Alex's network is saying something new, and surface net-new voices. Methodology in `.claude/skills/voice-radar/SKILL.md`.

**Input (all optional):** watchlist scope, topic lens, window. Defaults: speaker/host/recently-researched People, broad, last 14 days.

## Trigger
Runs when Alex types `/scan-voices [args]` or says "who's trending", "social listening", "what are my people posting about".

## Orchestration shape
Single-thread skill run. Execute `.claude/skills/voice-radar/SKILL.md` end-to-end:
1. **Step 1 — Build watchlist FROM Notion People** (`collection://4a1af67f-9141-4ba5-aa9d-88b07dcd5f86`) — NOT from external "top voices" (design principle).
2. **Step 2 — Find each voice's off-LinkedIn channels** (Substack/blog/GitHub/Reddit/podcast) via `WebSearch`; capture RSS.
3. **Step 3 — Pull recent activity + mentions** (`WebFetch` feeds + Google Alerts RSS); discover net-new voices from co-occurrence.
4. **Step 4 — Optional enrichment** (Clay balance check first; Apollo with exact credit confirmation) — credit-gated, HITL.
5. **Step 5 — Present findings. STOP for approval.**
6. **Step 6 — Write approved** updates: append dated notes to existing People; create net-new People rows only on approval.
7. **Step 7 — Close out** + offer the content/outreach bridge.

## Guardrails
- **Watchlist from existing data only** — never scrape a "top LinkedIn voices" list. Net-new voices are discovered through real signal and added only with approval.
- Legitimate sources only — no LinkedIn/X scraping. Off-platform cross-posts are the proxy.
- **Credit discipline:** check Clay balance (`get-credits-available`) before enrich; Apollo needs its exact credit confirmation. No spend without approval.
- Human-in-the-loop before any Notion write. `notion-search`/`notion-fetch` only. Honest gaps; no fabricated metrics.

## The honest gap (say it to Alex)
LinkedIn-native engagement/trend velocity is NOT legitimately accessible and is NOT replicated here. Some voices are LinkedIn-only and fall outside legitimate tracking. Alex's own periodic LinkedIn data export is the one legitimate window into his network's LinkedIn signal — complementary, not part of this command.

## What comes next
| Want to... | Do |
|---|---|
| Turn a POV into a post / warm-outreach note | `pre-event-content` / `pattern-synthesis` |
| Roles at a voice's company | `/scan-roles` |

## Ground truth
- Methodology: `.claude/skills/voice-radar/SKILL.md`
