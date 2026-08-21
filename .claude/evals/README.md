# `.claude/evals/` — the shared eval home

The single home for LLM-as-judge quality evaluation in this pipeline. Established 2026-06-26 by the build-rigor layer (Linear YED-89 / PRD US-3); **coordinates with the `eval-harness` project** (Notion Project Ideas `348d3699…`), which owns the rubric/judge conventions and `rubric_version`. When eval-harness is built, its skill rubrics (pre-event-content, etc.) live here too. **One judge system, not two** (never-duplicate-state).

## Layout
- `rubrics/<name>.md` — rubric-as-code: criteria + weights + pass bands + ≥1 pass/fail example each, plus a machine-readable JSON block. Versioned as `<name>@N`; never mutate old versions (bump instead). **Current build rubric: `build-quality@4`** (`rubrics/build-quality-v4.md`, live 2026-08-21 — added the artifact-type-scoped **density cap** ≤0.65 for `deep_read` renders, mechanized by `hooks/density-check.sh`; YED-136). For every artifact type except `deep_read`, `@4` ≡ `@3`. `build-quality-v3.md` (`@3`, confidence-honesty cap), `build-quality-v2.md` (`@2`, dangling-ref + command-skeleton caps) and `build-quality.md` (`@1`) are retained for runs scored under them.
- `prompts/judge-system.md` — the shared, immutable judge system prompt.
- `logs/<YYYY-MM-DD>-<artifact>-<run-id>.jsonl` — **authoritative** append-only run-log (the source of truth). Notion is a *deferred projection*, not the store (same contract-first pattern as `build-session-contract.md`).

## Run-log record schema
```json
{ "run_id":"", "timestamp":"", "artifact":"", "artifact_type":"skill|command|hook|ref|code",
  "rubric":"build-quality@1", "judge_model":"", "session_id":"",
  "criterion_scores":[{"id":"","score":0.0,"reasoning":""}],
  "weighted_score":0.0, "verdict":"pass|flag", "alex_ack":null }
```
`alex_ack` is the **calibration field** — `null` until Alex reviews, then `"agree" | "disagree"` (+ optional note).

## The calibration gate (≥80%) — the judge is ADVISORY until it earns trust
LLM-as-judge has **self-preference bias** — here it's judging work produced by a similar model (the "judge circularity" risk eval-harness flagged as R1). So:
- The judge is **advisory only** until ≥20 logged runs reach **≥80% judge–human agreement** (Alex acks). Do NOT gate the DoD on it before then.
- Re-check agreement on a rolling basis; <80% ⇒ tighten the rubric, don't trust the score.
- The judge **scores + flags; it never auto-rewrites and never hard-blocks.**

## Deferred (non-destructive, do NOT build now)
A separate-model / cross-judge quorum (independence) and a Notion/PostHog projection of scores — per the lean-foundation decision (2026-06-26). The run-log contract above stays stable when added.
