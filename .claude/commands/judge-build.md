---
description: "Cross-provider build-quality judge — score an artifact (skill/command/hook/ref/code, or a deep_read render) with a two-seat quorum (Claude/Sonnet + Gemini) against build-quality@5: mechanized dangling-ref cap + deep_read density pre-pass, per-criterion 0–1, weighted composite, merge to one quorum verdict, authoritative run-logs, capture your ack (calibration). Escalates on verdict mismatch, score divergence, a flat-1.0 seat, or missing evidence parity (fail-safe FLAG in autonomous). Gemini seat advisory. Never rewrites, never blocks."
argument-hint: "[artifact path or pasted content] [+ optional: the issue/AC it should satisfy]"
---

# /judge-build — Cross-provider build-quality judge

Run the **judge-build** quorum on an artifact. Methodology: `.claude/skills/judge-build/SKILL.md`. Design: `.claude/references/cross-provider-judge.md`.

**Input:** a file path (e.g. `/judge-build .claude/skills/trend-radar/SKILL.md`) or pasted content, optionally with the spec/AC it should meet.

## Trigger
Runs when Alex types `/judge-build <artifact>` or says "judge this build", "score this skill/hook against the rubric", or at a DoD boundary once the judge is calibrated.

## Orchestration (execute `.claude/skills/judge-build/SKILL.md`)
1. **Intake** — resolve the artifact path + `artifact_type`; capture any spec/AC; determine **mode** (interactive = Alex in the loop, default; autonomous = batch/headless).
2. **Pre-pass (mechanized)** — `bash .claude/hooks/check-refs.sh --artifact <path>` → the verified missing-references list (ground truth for both seats; enforces the `@5` dangling-ref cap deterministically). **If `artifact_type = deep_read`, also run** `bash .claude/hooks/density-check.sh --artifact <path>` → the words/citations density signal (flag only — the judge decides padding vs. legitimate on-ramp; NOT a hard cap).
3. **Dispatch two seats** — (a) **Claude/Sonnet** seat via the `Agent` tool with `model: sonnet` (house-aware, independent of the Opus main thread); (b) **Gemini** seat via `bash .claude/hooks/gemini-judge.sh --artifact <path> --artifact-type <t> --calibration-set prospective`. Both score all 5 `build-quality@5` criteria (0–1 + reasoning, **defects listed first**) using `judge-system-v2.md` + `build-quality-v5.md`. The Gemini adapter enforces the order via `responseSchema` and **the harness computes the composite/verdict** — the model never does. **For a rendered Deep Read, pass `--artifact-type deep_read`** so Step 0's density pre-pass runs.
4. **Collect** — the Gemini adapter wrote its own run-log line; append the Claude/Sonnet seat's line (`judge_provider:"anthropic"`, `rubric:"build-quality@5"`).
5. **Merge → named output** — `bash .claude/hooks/quorum-merge.sh --artifact <path> --mode <mode> --claude-verdict '<json>' --gemini-log <path>` writes the authoritative **`quorum` record** with `agree` + `divergence` + `escalation_reasons[]` + `resolution` (`auto` / `escalated` / `failsafe_flag`) + `final_verdict`. **Matching verdicts no longer auto-accept:** it escalates on score divergence ≥0.15, a flat-1.0 seat, or a Gemini run without evidence parity (YED-206).
6. **Present + ack (calibration)** — show both seats' per-criterion scores (scoped-quorum weighting noted); on **agree** ask "agree / disagree?" once; on **escalated** show the divergent criterion side-by-side and ask Alex to adjudicate; write the answer to the quorum record's `alex_ack`. Autonomous mode records `failsafe_flag` and does not block.
7. **Failure modes** — no spec → score vs stated purpose, flag reduced confidence; artifact too large → judge load-bearing sections, no silent truncation; **Gemini seat errors → do NOT silently single-judge**: record the Claude seat, mark the quorum incomplete, flag for re-run.

## Guardrails
- **Per-seat standing** — Sonnet = trusted seat; **Gemini = ADVISORY** (rubber-stamp triage 2026-09-19, YED-206) and cannot auto-accept. Four-number gate in `.claude/evals/README.md`. Don't hard-block on the score.
- Scores + flags; **never rewrites, never hard-blocks.** Honest about un-assessable criteria.
- Authoritative run-logs are local (`.claude/evals/logs/`); Notion/PostHog projection deferred.
- **No model tiebreak** — a disputant can't adjudicate its own split; Alex is the only independent tiebreaker (fail-safe FLAG when he's not in the loop).

## Ground truth
- Methodology + rubric + judge prompt: `.claude/evals/` · calibration gate: `.claude/evals/README.md` · quorum design: `.claude/references/cross-provider-judge.md`
- Scripts: `.claude/hooks/{check-refs,density-check,gemini-judge,quorum-merge}.sh` · Coordinates with `eval-harness` (Notion `348d3699…`).
