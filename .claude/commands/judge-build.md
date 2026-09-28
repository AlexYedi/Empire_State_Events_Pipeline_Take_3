---
description: "Build-quality judge — ONE Sonnet reviewer scores an artifact, file list or git range against build-quality@6 (defects before scores) and raises flags. Harness computes score + final pass/flag; guarded privacy/spine paths always flag for human review. You are asked only on a flag. Never rewrites, never blocks."
argument-hint: "[artifact path | file list | BASE..HEAD range] [+ optional: the spec/AC it should satisfy]"
---

# /judge-build — build-quality judge (single reviewer)

Method: `.claude/skills/judge-build/SKILL.md` (includes WHEN to run it — the artifact-class triggers). Design:
`.claude/references/judge.md`.

## Orchestration
1. **Intake** — resolve the target: `--artifact <path>`, `--files A B …`, or `--range $(git merge-base origin/main HEAD)..HEAD`
   for a PR; its `artifact_type`; any in-repo spec (`--spec-file`) or ad-hoc spec text (`--context`). If the target is
   the judge layer, stop: it is never judged by itself.
2. **Build** — `python3 .claude/evals/judge.py run <target> --artifact-type <t> [--spec-file S] [--context C]`. Builds
   the bundle (privacy guard + deterministic pre-passes) and writes the reviewer brief. Exit 3 = privacy guard.
3. **Dispatch** — from this (parent) thread, `Agent` tool with `model: sonnet`, using the prompt `judge.py` printed.
4. **Collect** — save the reviewer's JSON; `python3 .claude/evals/judge.py run --resume <run-id> --verdict <json>`.
   `seat-log.py` writes the row; never hand-write one.
5. **Named output** — the one line `judge.py` prints: `PASS` or `FLAG` + reasons, and the log path.
6. **Present** — on PASS, report it and stop (no ack). On FLAG, show the reasons + the 1–2 highest-leverage defects
   and ask Alex "agree / disagree — and why"; record with `judge.py ack --run <run-id> agree|disagree "why"`.
7. **Failure modes** — verdict rejected → re-dispatch, nothing was logged; no spec → reduced confidence, say so;
   parity warning → rebuild with `--spec-file` if a spec exists.

## Guardrails
- Scores + flags; never rewrites, never hard-blocks. No calibration number gates anything.
- Authoritative logs are local and append-only (`.claude/evals/logs/`).
