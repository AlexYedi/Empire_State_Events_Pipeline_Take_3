---
name: judge-build
description: "Build-quality judge: ONE Claude Sonnet reviewer scores a build artifact (a file, a file list, or a git range / PR) against build-quality@6, defects before scores, and raises flags. The harness computes the score and the final pass/flag (guarded privacy/spine paths always need human review). Alex is asked only on a flag. Runs on the artifact-class triggers below, never on the judge layer itself. Never rewrites, never hard-blocks."
---

# Judge Build Skill (single reviewer)

One Sonnet reviewer, one command, flags only. Design and history: `.claude/references/judge.md` (YED-231 retired the
Gemini/OpenAI seats, the quorum and the trust ladder on 2026-09-28). Home: `.claude/evals/`.

**The reviewer reads (the bundle includes both):** `.claude/evals/prompts/judge-system-v2.md` (defects before scores,
earned 1.0, don't trust docstrings) and `.claude/evals/rubrics/build-quality-v6.md` (**frozen at `build-quality@6`**:
5 criteria + weights, pass line 0.70, caps: dangling-ref ≤0.60 · spec-drift correctness ≤0.70 · confidence-honesty
≤0.65 · command-skeleton completeness ≤0.35 · density ≤0.65 for `deep_read`). The `@6` privacy score cap is now a
deterministic path rule (below), not arithmetic.

## When to run it (artifact-class triggers — this list replaced DoD item 4)
| Artifact class | Judge? |
|---|---|
| New skill or command | **Once, at first ship.** Later edits fall under "edits & refs". |
| Code | When the change is **> ~150 lines** or touches a **guarded path** (spine write path, privacy filters, allow/deny lists). |
| Edits to existing skills/commands, references, docs | **No judge.** Deterministic checks only: `check-refs.sh`, `check-tombstones.py`, the offline tests. |
| Content (posts, notes, DMs) | **No judge.** Style-guide screen (`content-style-guide.md` + `content-anti-patterns.md`) before Notion. |
| The judge layer itself (`.claude/evals/` judge files, this skill, `/judge-build`, `seat-log.py`, `judge.md`) | **Never judged by itself.** `judge.py` refuses it; its offline tests are the check. |

No routine control runs: the control set runs only when the reviewer's model id changes (`judge.py` prints the trigger).

## Run (one command, paused once for the subagent)
1. **Build + brief:**
   `python3 .claude/evals/judge.py run --range $(git merge-base origin/main HEAD)..HEAD --artifact-type <t> --spec-file <in-repo spec>`
   (or `--artifact <path>` / `--files A B …`; `--context "<text>"` for ad-hoc spec text). Use the **merge-base**, never
   two-dot against a moving `origin/main`. Types: `skill` · `command` · `hook` · `code` · `ref` · `deep_read` · `dossier`.
   Exit 3 = privacy guard (nothing built). An EVIDENCE-PARITY warning means no spec reached the bundle: rebuild with
   `--spec-file` if one exists (a spec cannot be added later). The quote check covers every file, spec and the diff.
2. **Dispatch the reviewer from the parent thread** (subagents cannot spawn subagents): `Agent` tool, `model: sonnet`,
   prompt exactly as `judge.py` prints it (read the brief, return only the JSON). Save the JSON where it says.
3. **Log + verdict:** `python3 .claude/evals/judge.py run --resume <run-id> --verdict <json> [--judge-model claude:sonnet:<id>]`.
   `seat-log.py` is the only writer (never hand-write a row). Prints ONE line: **PASS** (done — do not ask Alex) or
   **FLAG** with its reasons.
4. **On FLAG only:** show Alex the reasons plus the 1–2 highest-leverage defects, ask "agree / disagree — and why", then
   `python3 .claude/evals/judge.py ack --run <run-id> agree|disagree "why"` (append-only, one per run, UTC-stamped).

## What makes a FLAG (judge_lib.finalize — deterministic, no calibration number involved)
- composite < 0.70 after caps
- the reviewer set `privacy_layer_defect` (a confirmed defect in any layer of a privacy/security control)
- a **guarded path** is in the bundle — `.claude/scripts/spine_client.py`, `inbox_boundary.py`, `build_graph.py`,
  `.gitignore`, or any file named like guard/filter/allowlist/denylist/boundary/privacy/redact/pii → human review
  whatever the score
- 1.0 on all five criteria (low-information)
- more than 30% of quoted defects are not in the bundle (fabricated evidence)

## Failure modes
- **Verdict rejected** (malformed JSON, missing criteria) → nothing is logged; re-dispatch the reviewer.
- **No spec** → the reviewer scores against the artifact's own stated purpose and says confidence is reduced.
- **Big range** (> 60k chars) → files over 400 lines go as changed hunks (±40); `bundle_mode: hunks` is recorded.
- **Rubric wrong for this artifact type** → say so in the ack note. The rubric stays frozen at `@6`; changing it is a
  dated decision, not a per-run tweak.

## Files
`.claude/evals/{judge.py, judge_lib.py, calibration_stats.py (report only), controls.py, controls/manifest.json,
prompts/judge-system-v2.md, rubrics/build-quality-v6.md, README.md}` · `.claude/hooks/{seat-log.py, check-refs.sh,
check-tombstones.py, density-check.sh}` · tests: `.claude/evals/test_{judge_lib,judge_e2e,bundle_multifile,null_baseline}.py`.
