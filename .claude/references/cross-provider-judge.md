# Cross-provider judge quorum — spec (v1, 2026-07-17)

**Why.** The build-quality judge is `provisional-trusted` (crossed 20-@-80% but on a Claude-only, ~1/3-self-produced
sample). The unclosed risk is **judge circularity / self-preference** (R1): Claude rating Claude-produced work.
A **second judge from a different provider (Google Gemini)** is the documented next step (deferred 2026-06-26) —
the concrete path to dropping "provisional." This spec is the design; build follows.

## The two judges (locked 2026-07-17)
| Seat | Model | Runs via | Auth / cost |
|---|---|---|---|
| **House-aware** | Claude **Sonnet** | `Agent` tool (subagent, in-harness) | Claude subscription (no `$` marginal) |
| **Independent** | **`gemini-pro-latest`** (current Gemini Pro, ≈3.x) | `.claude/hooks/gemini-judge.sh` (curl → `generativelanguage.googleapis.com`) | `GEMINI_API_KEY` in `.env`; billed ~2–4¢/run |

- Why Sonnet not Haiku: Haiku wobbled this session (rubric-fit misses, gcc-v2 inconsistency). Not Opus: quota-heavy + Opus-judging-Opus amplifies same-family self-preference.
- Why Gemini Pro not Flash-Lite: free tier on this key = Flash-Lite only (too weak → noisy disagreements). Billing enabled 2026-07-17; Pro is the quality independent seat. Cost is negligible at judge volume.

## Scoped quorum (not naïve 50/50)
Both judges score all 5 `build-quality@3` criteria, BUT their votes are **weighted by domain competence**:
- **Provider-neutral criteria** (`correctness`, `completeness`) — Gemini's independent read carries full weight; this is where cross-provider catches Claude's blind spots.
- **House-specific criteria** (`convention_adherence`, `anti_pattern_avoidance`) — Claude (Sonnet) retains primary judgment; Gemini lacks native Empire-State context (notion-search vs notion-query-data-sources, SDK subagent constraint, tombstoned decisions) unless heavily briefed. Gemini's vote here is advisory only.
- `diagnostics` — shared.
Gemini gets the SAME `judge-system.md` + `build-quality@3` + per-artifact spec/context the Claude judge gets (apples-to-apples), plus a house-context primer for the convention criteria.

## Quorum resolution (no model tiebreak — it would be circular)
A disputant cannot adjudicate its own disagreement, and we have no genuinely-independent *third* provider. So:
- **Agree** (both pass / both flag) → auto-verdict, high confidence, no human needed.
- **Disagree** → **escalate to Alex** (the only independent tiebreaker). The disagreement set is the highest-value output.
- **Disagree in autonomous/batch mode** (Alex not in the loop) → **fail-safe to FLAG** (non-destructive — "review before done") + queue the disagreement for later human review. Never auto-resolve a split with a correlated model.
- Escalations surface **both judges' per-criterion reasoning side-by-side**, with the divergent criterion highlighted → a ~15-second human call.

## Run-log (schema stays stable — the contract-first payoff)
Same `.claude/evals/logs/*.jsonl` schema. New/used fields:
- `judge_model`: `"gemini-pro-latest"` (+ capture the **resolved model version** from the API response, since `-latest` aliases shift — preserves calibration traceability).
- `calibration_set`: `"backfill"` (Approach A) | `"prospective"` (Approach B) — **report agreement separately AND combined** so the clean independent signal (B) is never inflated by the correlated backfill (A).
- A `quorum` block on dual-judged artifacts: `{claude: <verdict>, gemini: <verdict>, agree: <bool>, resolution: auto|escalated|failsafe_flag}`.

## Calibration plan
- **Approach A — backfill (fast, reuses labels):** run Gemini on the same artifact-STATES already Alex-acked. For unchanged files → current on-disk; for files changed after judging → reconstruct as-judged content from git. Report **Gemini-vs-Alex** (calibration) + **Gemini-vs-Haiku/Sonnet** (inter-judge reliability) + the disagreement set. `calibration_set: backfill`.
- **Approach B — prospective (clean, held-out):** every new `/judge-build` runs both judges; Alex acks once; agreement accrues on fresh, independent artifacts. `calibration_set: prospective`. **This is what actually retires "provisional"** — target ≥80% Gemini-vs-Alex across ~15+ prospective runs.

## Build gotchas (learned during prereq verification)
1. **Gemini Pro is a thinking model** — set `generationConfig.maxOutputTokens` generously (~8000) or reasoning tokens starve the JSON verdict (a 20-token cap returned empty). Consider `responseMimeType: application/json` + a response schema to force clean structured output.
2. **Model-id churn is fast** — 2.5-pro and 3-pro-preview both deprecated within this session. Use `gemini-pro-latest` and record the resolved version per run; don't hardcode a soon-dead pinned preview id.
3. **Key never printed** — source `.env`, pass via `x-goog-api-key` header, never echo the command with the key.
4. **Free tier on this key = Flash-Lite only** — Pro needs billing (enabled 2026-07-17). Don't silently fall back to a free model if billing lapses; surface it.
5. **Cost:** ~2–4¢/run · backfill (~15–22 runs) ≈ $0.50–0.90 one-time · ongoing ≈ $1–6/mo. Claude seat stays subscription-free.

## DoD
Non-trivial build → `/judge-build` the adapter itself (dog-fooding) + `/dod-close`. Spec artifact = this file (mirror to ChatPRD/Notion). Adversarial pass = the quorum-circularity catch (already in writing, this session).
