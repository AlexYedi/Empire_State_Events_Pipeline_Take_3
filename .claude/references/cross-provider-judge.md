# Cross-provider judge quorum — spec (v1, 2026-07-17)

> **Right-sized 2026-09-28 (YED-231): the run path, merge and trust rules now live in `.claude/references/judge-right-size-yed-231.md`** (one command, `python3 .claude/evals/judge.py run`; Sonnet voting · OpenAI shadow · Gemini off with its adapter kept; `seats.json` is Alex's static role map). The 2026-09-19 three-seat design (YED-209, `.claude/proposals/third-judge-seat-openai.md`) is history. This file keeps the original two-seat rationale, the run-log contract, the calibration plan and the Gemini build gotchas.

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

## Quorum, resolution and the merge mechanic — superseded
The scoped 50/50 weighting, the two-seat resolution table and `quorum-merge.sh` (removed 2026-09-28) are replaced by
`quorum_merge.py` under the rules in **`.claude/references/judge-right-size-yed-231.md` §2/§4**. What survives from
here: no model tiebreak (Alex is the only tiebreaker), fail-safe FLAG in autonomous mode, and every seat scores the
same bundle with the harness (never the model) computing the composite.

## Run-log (schema stays stable — the contract-first payoff)
Same `.claude/evals/logs/*.jsonl` schema. New/used fields:
- `judge_model`: `"gemini-pro-latest"` (+ capture the **resolved model version** from the API response, since `-latest` aliases shift — preserves calibration traceability).
- `calibration_set`: `"backfill"` (Approach A) | `"prospective"` (Approach B) — **report agreement separately AND combined** so the clean independent signal (B) is never inflated by the correlated backfill (A).
- A `quorum` block on dual-judged artifacts: `{claude, gemini, agree, divergence, escalation_reasons[], flat_ceiling{}, gemini_evidence_parity, weak_corroboration, resolution: auto|escalated|failsafe_flag}`.

## Calibration plan
- **Approach A — backfill (fast, reuses labels):** run Gemini on the same artifact-STATES already Alex-acked. For unchanged files → current on-disk; for files changed after judging → reconstruct as-judged content from git. Report **Gemini-vs-Alex** (calibration) + **Gemini-vs-Haiku/Sonnet** (inter-judge reliability) + the disagreement set. `calibration_set: backfill`.
- **Approach B — prospective (clean, held-out):** every new `/judge-build` runs both judges; Alex acks once; agreement accrues on fresh, independent artifacts. `calibration_set: prospective`. **REVISED 2026-09-19 (YED-206):** raw agreement does not retire "provisional" — a seat that passes everything scores ~80% by itself (Gemini's "83%" *was* its always-pass baseline). A seat is trusted only when it clears all four bars in `.claude/evals/README.md` (agreement above its own baseline · κ ≥ 0.60 · flag recall ≥ 0.60 · flat-1.0 rate < 0.30), measured by `.claude/evals/calibration_stats.py`. Gemini currently fails three of four → **ADVISORY**: it runs, it is recorded, it cannot auto-accept. Triage: `.claude/notes/gemini-judge-triage-2026-09-19.md`.

## Build gotchas (learned during prereq verification)
1. **Gemini Pro is a thinking model** — set `generationConfig.maxOutputTokens` generously (~8000) or reasoning tokens starve the JSON verdict (a 20-token cap returned empty). Consider `responseMimeType: application/json` + a response schema to force clean structured output.
2. **Model-id churn is fast** — 2.5-pro and 3-pro-preview both deprecated within this session. Use `gemini-pro-latest` and record the resolved version per run; don't hardcode a soon-dead pinned preview id.
3. **Key never printed** — source `.env`, pass via `x-goog-api-key` header, never echo the command with the key.
4. **Free tier on this key = Flash-Lite only** — Pro needs billing (enabled 2026-07-17). Don't silently fall back to a free model if billing lapses; surface it.
5. **Cost:** ~2–4¢/run · backfill (~15–22 runs) ≈ $0.50–0.90 one-time · ongoing ≈ $1–6/mo. Claude seat stays subscription-free.

## DoD
Non-trivial build → `/judge-build` the adapter itself (dog-fooding) + `/dod-close`. Spec artifact = this file (mirror to ChatPRD/Notion). Adversarial pass = the quorum-circularity catch (already in writing, this session).

## Bundle mode and quote verification (YED-223, 2026-09-27)

**Evidence parity is a property of the bundle, fixed when `judge_lib.py bundle` builds it.** Every seat scores the bundle's bytes verbatim, so a seat flag cannot add evidence after the fact. The adapters therefore **refuse** `--context`/`--spec-file` together with `--bundle` (exit 2) instead of silently dropping them, and `judge_lib.py bundle` prints an unmissable warning when the bundle carries < 400 chars of spec. The fix for a parity-false bundle is always to rebuild it. Build diff artifacts against the merge-base, never two-dot against a moving `origin/main`.

**Quote verification is format-tolerant for prose only.** A defect's `quote` must appear in the bundle (since YED-231: any file, spec file, the context, or the range's diff) modulo whitespace and case. For prose artifact types (`skill`, `command`, `ref`, `dossier`, `deep_read`) it is also tolerant of dropped markdown `**`, backticks, a word-boundary `*`, and the em-dash / en-dash / spaced-hyphen / colon swap. Code-like types are matched strictly, and `_` is never altered in any mode: in code every delimiter is syntax, and the judge reproduced fabrications against `hay_loose`, `__init__`, `_private`, `*args` and `--bundle` when the first two versions stripped them. Recorded residual: in prose, a quote differing only by that swap or dropped markers verifies. The strict count survives as `unverified_exact`. **Coverage:** quote verification runs for the Claude seat (`seat-log.py`) and the OpenAI seat (`openai_judge.py`). The Gemini seat's response schema has no `quote` field, so it has never been quote-checked; with Gemini `off` since 2026-09-28 (YED-231) this matters only if it is switched back on (YED-187).
