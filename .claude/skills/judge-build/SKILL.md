---
name: judge-build
description: "Cross-provider LLM-as-judge for build artifacts (skills/commands/hooks/refs/code). Runs a two-seat quorum — Claude/Sonnet (house-aware) + Gemini (independent) — scores each against the build-quality rubric per-criterion (0–1 + reasoning), mechanically enforces the dangling-reference cap, merges to one quorum verdict, writes authoritative run-logs, and prompts Alex to ack/disagree (the calibration field). Agree→auto; disagree→escalate (fail-safe FLAG in autonomous mode). PROVISIONAL-TRUSTED. Coordinates with eval-harness; never auto-rewrites, never hard-blocks."
---

# Judge Build Skill (cross-provider quorum)

You orchestrate the **build-quality judge** so quality is a measurable, cross-provider signal — not a vibe, and not a single model rating its own family's work. Part of the build-rigor measurement layer (PRD US-3 / Linear YED-89; cross-provider quorum = YED-109). Home is `.claude/evals/`. Full design: **`.claude/references/cross-provider-judge.md`** (read it once).

**Load first (every run):**
- `.claude/evals/prompts/judge-system.md` — the immutable judge instructions. Follow verbatim.
- `.claude/evals/rubrics/build-quality-v4.md` — the **current** rubric (`build-quality@4`, live 2026-08-21): 5 criteria + weights, pass band 0.70, and the caps — composite **confidence-honesty cap ≤0.65** (unverified-asserted-as-verified → flag) + completeness caps (dangling-reference ≤0.60; command-skeleton-absent ≤0.35) + the **density cap ≤0.65 (`deep_read` artifacts only)** — padding (high word-to-cited-fact ratio that is generic-explainer filler, NOT legitimate novice on-ramp) → flag. Record `rubric: "build-quality@4"` in every run-log. (`build-quality-v3.md`/`-v2.md`/`.md` = retained `@3`/`@2`/`@1`; never mutate old versions. For every artifact type EXCEPT `deep_read`, `@4` ≡ `@3`.)

**Ground rules:**
- **Provisional-trusted.** Calibration crossed the gate (≥20 @ ≥80%) on a Claude-only sample → gates new/independent builds, advisory on self-produced work. The cross-provider quorum + Approach-B prospective runs (currently ~2 of ~15 Gemini-vs-Alex) is what retires "provisional." Until then, still do NOT hard-block on the score.
- **Score + flag only.** Never rewrite the artifact; never hard-block. Surface a verdict for Alex to ack.
- **Honest:** if a criterion can't be assessed (missing context), say so and score conservatively — don't invent.

---

## Inputs
- **Artifact** — a file path (e.g. `.claude/skills/trend-radar/SKILL.md`) or pasted content. Note its `artifact_type` (skill/command/hook/ref/code).
- **(Optional) Spec** — the issue/PRD/AC it should satisfy (for `correctness`/`completeness`). If absent, infer from the artifact's own stated purpose and say so.
- **Mode** — `interactive` (Alex in the loop, default) or `autonomous` (batch/headless). Drives disagreement resolution.

## Step 0 — Mechanized pre-passes (both seats share this ground truth)
1. **Dangling references.** Run `bash .claude/hooks/check-refs.sh --artifact <path>`. Its stdout is the list of load-bearing `.claude/…` references that **do not exist on disk** — verified fact, not model opinion. This closes the `bf17` gap (models under-apply the cap). Pass this list to BOTH seats. The Gemini adapter runs check-refs itself and enforces the cap; for the Claude seat, treat the list as authoritative and cap completeness ≤0.60 (composite ≤0.60) if it is non-empty.
2. **Density (`deep_read` artifacts only).** If `artifact_type = deep_read`, run `bash .claude/hooks/density-check.sh --artifact <path>`. It reports `words / citations` per section + a `verdict` (`OK` / `PADDING-RISK` / `UNCITED-LONGFORM`). This is the **number-side** of the density cap, **not** a deterministic cap: padding vs. legitimate novice on-ramp (uncited-by-design) is a judgment. Pass the signal to both seats (the Gemini adapter runs it itself for deep_read). The Claude seat applies the density cap ≤0.65 **only** if a `PADDING-RISK`/`UNCITED-LONGFORM` signal is, on inspection, generic-explainer filler — never for an honestly-short section or for legitimate jargon/mechanism on-ramp prose. Skip this pre-pass entirely for non-`deep_read` artifacts.

## Step 1 — Read the artifact + its spec
Read the file(s). If a spec/AC was given (or findable in Linear/the PRD), hold the artifact against it. Note `artifact_type`.

## Step 2 — Run the two seats (both score all 5 criteria independently, 0–1 + reasoning)
- **Claude (Sonnet) seat — house-aware.** Dispatch via the `Agent` tool with **`model: sonnet`** (independent of the Opus main thread, avoids Opus-judging-Opus self-preference; keeps house context). Give it `judge-system.md` + `build-quality-v4.md` + the artifact + the Step-0 missing-refs list + (for `deep_read`) the density signal + any spec. It returns the 5-criterion JSON (`{criterion_scores[], confidence_honesty_violation, weighted_score, verdict}`). Apply the **judge-circularity caution** (be *more* skeptical of plausible-but-wrong work).
- **Gemini seat — independent (cross-provider).** Run `bash .claude/hooks/gemini-judge.sh --artifact <path> --artifact-type <t> --calibration-set prospective [--context "<spec>"]`. It scores the same rubric (`@4`), mechanically enforces the dangling-ref cap, runs the density pre-pass for `deep_read` (flag, not hard-cap), and **writes its own run-log line** (`judge_provider:"google"`). **Pass `--artifact-type deep_read` when judging a rendered Deep Read** so the density signal is computed.
- **Scoped quorum weighting** (per the spec): Gemini carries **full weight** on the provider-neutral criteria (`correctness`, `completeness`); the Claude/Sonnet seat is **primary** on the house-specific criteria (`convention_adherence`, `anti_pattern_avoidance`) where Gemini lacks native Empire-State context; `diagnostics` shared.

## Step 3 — Write the Claude seat's run-log line
Append the Sonnet verdict as one JSON line to `.claude/evals/logs/<YYYY-MM-DD>-<artifact-slug>-<run-id>.jsonl` per the README schema (`judge_model:"claude:sonnet"`, `judge_provider:"anthropic"`, `rubric:"build-quality@4"`, `calibration_set:"prospective"`, `alex_ack:null`). (The Gemini line was written by its adapter in Step 2.) These local logs are the source of truth.

## Step 4 — Merge to one quorum verdict
Run `bash .claude/hooks/quorum-merge.sh --artifact <path> --mode <interactive|autonomous> --claude-verdict '<sonnet json>' --gemini-log <the gemini log path from Step 2> [--claude-run-id <id>]`. It computes `agree`, resolves (`auto` / `escalated` / `failsafe_flag`), and appends the `quorum` record. **Resolution:** agree → auto-verdict; disagree + interactive → **escalate to Alex**; disagree + autonomous → **fail-safe FLAG** (non-destructive, queued for later review — never auto-resolve a split with a correlated model).

## Step 5 — Present verdict + ack (the calibration step)
```
## Build-quality quorum — {artifact}  →  {final_verdict}  ({resolution})
Claude/Sonnet {ws}  |  Gemini {ws}   agree: {bool}
- correctness {c-s}/{g-s} — {why}         [Gemini full weight]
- completeness {c-s}/{g-s} — {why}        [Gemini full weight; check-refs: {missing or none}]
- convention_adherence {c-s}/{g-s} — {why}[Claude primary]
- anti_pattern_avoidance {c-s}/{g-s} — {why}[Claude primary]
- diagnostics {c-s}/{g-s} — {why}
{if escalated: the divergent criterion, both seats' reasoning SIDE-BY-SIDE, highlighted}
{if flag: the 1–2 highest-leverage fixes}
```
- **Agree** → ask once: **"Agree with this verdict? (agree / disagree — and why)"** → write into the quorum record's `alex_ack`.
- **Escalated** → the disagreement is the highest-value output: show it, ask Alex to adjudicate → that call becomes the `alex_ack` and the tiebreak. A disagree is *more* valuable than an agree — it shows where to tighten the rubric.
- **Autonomous** → no prompt; record `failsafe_flag` and note it's queued. Tell Alex the running Approach-B agreement rate if ≥5 prospective acks exist.

## Failure modes
- **No spec available** — score `correctness`/`completeness` against the artifact's own stated purpose; flag reduced confidence.
- **Artifact too large** — judge the load-bearing sections; note what wasn't covered (no silent truncation).
- **Gemini seat errors** (billing lapse → Flash-Lite, HTTP error) — the adapter surfaces it and exits non-zero; do NOT silently fall back to a single-judge pass. Record the Claude seat, note the quorum is incomplete, and flag for a re-run.
- **Rubric feels wrong for this artifact type** — record it in the ack note; a signal to add an artifact-type rubric later (don't bend the score).

## Reuses / references
- `.claude/hooks/{check-refs.sh, density-check.sh, gemini-judge.sh, quorum-merge.sh}` · `.claude/evals/{prompts/judge-system.md, rubrics/build-quality-v4.md, README.md}` · design: `.claude/references/cross-provider-judge.md`.
- Coordinates with `eval-harness` (Notion `348d3699…`) — same judge home; eval-harness owns `rubric_version`.
