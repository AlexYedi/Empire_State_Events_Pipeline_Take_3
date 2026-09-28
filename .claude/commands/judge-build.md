---
description: "Build-quality judge — score an artifact, a file set or a git range against build-quality@6 with one command (judge.py): one evidence bundle, the OpenAI shadow seat, the Claude/Sonnet voting seat dispatched from this thread, one-line verdict. Escalates only on a shadow disagreement, a quote-verified shadow major, or an integrity problem (fail-safe FLAG in autonomous). Never rewrites, never blocks."
argument-hint: "[artifact path or pasted content] [+ optional: the issue/AC it should satisfy]"
---

# /judge-build — build-quality judge

Run the **judge-build** quorum on an artifact, file set or range. Methodology: `.claude/skills/judge-build/SKILL.md`. Design: `.claude/references/judge-right-size-yed-231.md` (history: `cross-provider-judge.md`).

**Input:** a file path (e.g. `/judge-build .claude/skills/trend-radar/SKILL.md`) or pasted content, optionally with the spec/AC it should meet.

## Trigger
Runs when Alex types `/judge-build <artifact>` or says "judge this build", "score this skill/hook against the rubric", or at a DoD boundary once the judge is calibrated.

## Orchestration (execute `.claude/skills/judge-build/SKILL.md`; spec `.claude/references/judge-right-size-yed-231.md`)
1. **Intake** — resolve what changed (`--artifact` path, `--files`, or `--range <merge-base>..HEAD`) + `artifact_type`; find the in-repo spec (`--spec-file`); determine **mode** (interactive default; autonomous = batch/headless).
2. **Dry run** — `python3 .claude/evals/judge.py run … --dry-run`: builds the bundle (pre-passes + privacy guard, exit 3 = nothing sent) and prints the shadow seat's worst-case cost.
3. **Dispatch** — `python3 .claude/evals/judge.py run …` runs the OpenAI **shadow** seat on the bundle and prints the Sonnet brief. Dispatch the **Claude/Sonnet voting** seat from THIS thread (`Agent` tool, `model: sonnet`, "Read `<brief>` and follow it exactly"); save its JSON where `judge.py` said.
4. **Collect + merge** — `python3 .claude/evals/judge.py run --resume <run-id> --sonnet-verdict <json>` logs the Sonnet row via `seat-log.py`, merges (`quorum_merge.py`), and prints one line + the REVISIT banner when due.
5. **Named output** — the `quorum` record in `.claude/evals/logs/` (`resolution` auto / escalated / failsafe_flag + `final_verdict`) and the one-line verdict.
6. **Ack (calibration)** — only on `escalated`: show the voter's reasoning + the reasons, ask agree/disagree once, write it with `python3 .claude/evals/judge.py ack --run <quorum-run-id> agree|disagree "why"`. Clean passes are batch-acked weekly in `/rigor-review`.
7. **Failure modes** — no spec → score vs stated purpose, flag reduced confidence; shadow adapter fails → `shadow_missing`, the voter still decides; Sonnet JSON rejected → integrity FLAG, re-dispatch and `--resume` again; big range → hunk mode, say it was not a full read.

## Guardrails
- **Roles** (`.claude/evals/seats.json`, edited only by Alex) — Sonnet **voting**, OpenAI **shadow**, Gemini **off**. `calibration_stats.py --check` raises a REVISIT banner; it never changes a role. Don't hard-block on the score.
- Scores + flags; **never rewrites, never hard-blocks.** Honest about un-assessable criteria.
- Authoritative run-logs are local (`.claude/evals/logs/`); Notion/PostHog projection deferred.
- **No model tiebreak** — a disputant can't adjudicate its own split; Alex is the only independent tiebreaker (fail-safe FLAG when he's not in the loop).

## Ground truth
- Methodology + rubric + judge prompt: `.claude/evals/` · calibration gate: `.claude/evals/README.md` · quorum design: `.claude/references/cross-provider-judge.md`
- Scripts: `.claude/evals/judge.py` · `.claude/hooks/{check-refs.sh,density-check.sh,openai-judge.sh,seat-log.py}` · Coordinates with `eval-harness` (Notion `348d3699…`).
