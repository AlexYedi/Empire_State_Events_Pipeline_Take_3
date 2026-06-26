---
description: "Score a build artifact (skill/command/hook/ref/code) against the build-quality rubric — per-criterion 0–1 + reasoning, weighted composite, pass/flag verdict — write an authoritative run-log, and capture your ack (calibration). Advisory until ≥80% agreement. Never rewrites, never blocks."
argument-hint: "[artifact path or pasted content] [+ optional: the issue/AC it should satisfy]"
---

# /judge-build — Build-quality judge

Run the **judge-build** methodology on an artifact. Methodology: `.claude/skills/judge-build/SKILL.md`.

**Input:** a file path (e.g. `/judge-build .claude/skills/trend-radar/SKILL.md`) or pasted content, optionally with the spec/AC it should meet.

## Trigger
Runs when Alex types `/judge-build <artifact>` or says "judge this build", "score this skill/hook against the rubric", or at a DoD boundary once the judge is calibrated.

## Shape (single-thread)
Execute `.claude/skills/judge-build/SKILL.md`:
1. Load `judge-system.md` + `rubrics/build-quality.md`.
2. Read the artifact (+ spec if given).
3. Score the 5 criteria independently (0–1 + reasoning); apply the judge-circularity caution.
4. Weighted composite → verdict (pass ≥0.70 / flag).
5. Append the run-log JSON line (authoritative).
6. Present the verdict + **ask "agree / disagree?"** → write `alex_ack` (calibration).

## Guardrails
- **Advisory only** until ≥20 runs hit ≥80% Alex-agreement — don't gate the DoD on it yet.
- Scores + flags; **never rewrites, never hard-blocks.** Honest about un-assessable criteria.
- Authoritative run-log is local (`.claude/evals/logs/`); Notion/PostHog projection deferred.

## Ground truth
- Methodology + rubric + judge prompt: `.claude/evals/` · calibration gate: `.claude/evals/README.md`
- Coordinates with `eval-harness` (Notion `348d3699…`).
