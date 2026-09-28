# The build-quality judge (single reviewer, since YED-231, 2026-09-28)

**What it is.** One Claude **Sonnet** reviewer that reads a bundle and raises flags. It scores `build-quality@6` (frozen)
per criterion, defects before scores; the harness computes the composite and the final pass/flag. It never rewrites and
never hard-blocks. Run it with `python3 .claude/evals/judge.py` (method: `.claude/skills/judge-build/SKILL.md`).

**What was removed, and why.** YED-231 (approved by Alex 2026-09-28) retired the machinery that grew around the judge
from 2026-07-17 to 09-27: the Gemini and OpenAI seats and their adapters, the quorum merge, the per-seat trust ladder
(statuses, demotion rules, canaries, the last-voting-seat guard) and the OpenAI spend cap. The extra seats did not earn
their keep: Gemini's agreement was its always-pass baseline, the OpenAI seat stayed in shadow, and the quorum escalated
on its own bundle mechanics, so Alex was asked about runs where nothing was wrong. Historic run logs and
`spend-ledger.jsonl` are kept as history; the retired design is in git history and
`docs/archive/proposals/third-judge-seat-openai.md`.

## How a run works
1. `judge.py run` builds ONE evidence bundle (`judge_lib.build_bundle`): one file, a file list, or a git range
   (bundle_version 3; telemetry and the judge layer are excluded from ranges). The privacy guard refuses anything
   gitignored, out of repo, symlinked or secret-looking. Deterministic pre-passes (`check-refs.sh`,
   `check-tombstones.py`, `density-check.sh` for `deep_read`) go into the bundle as ground truth.
2. The parent thread dispatches the reviewer (`Agent`, `model: sonnet`) on the brief. Subagents cannot spawn
   subagents, so this step cannot live inside a script.
3. `judge.py run --resume` logs the verdict through `.claude/hooks/seat-log.py`, the only writer of reviewer rows
   (real UTC time, content hash, harness-computed score). Quotes are verified against every file in the bundle.
4. `judge_lib.finalize()` decides: **flag** if any of — score < 0.70 · reviewer's `privacy_layer_defect` ·
   a **guarded path** in the bundle (spine write path, privacy filters, allow/deny lists, `.gitignore`: human review
   whatever the score; this replaced the @6 privacy score cap) · flat 1.0 on all five criteria · > 30% of quoted
   defects not found in the bundle. Otherwise **pass**.
5. Alex is asked **only on a flag** (`judge.py ack`, append-only rows). A blind spot-check of passes is optional,
   when Alex asks for one.

## Kept
Defects before scores · the caps (dangling-ref, spec-drift, confidence-honesty, command-skeleton, density) ·
`seat-log.py` (no hand-written rows) · append-only logs · the quote check · the privacy guard.

## Not done any more
No calibration number gates anything (`calibration_stats.py` is a report, including runs per artifact class) ·
no second model, no shadow · no scheduled control runs: the control set (`controls.py plan`) runs only when the
reviewer's model id changes (`judge.py` prints the trigger) · the judge layer is never judged by itself.

## When to run it
The artifact-class trigger list lives in `.claude/skills/judge-build/SKILL.md`. It replaced DoD item 4 (the DoD gate itself was retired 2026-09-28 for `.github/pull_request_template.md`).
