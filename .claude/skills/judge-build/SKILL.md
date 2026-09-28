---
name: judge-build
description: "LLM-as-judge for build artifacts (skills/commands/hooks/refs/code, one file, several files or a git range). One command: judge.py builds one evidence bundle, runs the OpenAI shadow seat, hands the parent a brief for the Claude/Sonnet voting seat, merges, and prints one line. The voter's verdict is the verdict; a quote-verified shadow can only escalate. Clean passes are logged without a prompt (batch-acked weekly in /rigor-review); escalations ask Alex to ack via judge.py ack. Never auto-rewrites, never hard-blocks."
---

# Judge Build Skill

You orchestrate the **build-quality judge**: a measurable quality signal on a build, not a vibe. Part of the build-rigor
layer (PRD US-3 / YED-89). Home is `.claude/evals/`. **Spec: `.claude/references/judge-right-size-yed-231.md`** (YED-231,
supersedes the run-path sections of `cross-provider-judge.md`). Rubric: **`build-quality@6`**
(`.claude/evals/rubrics/build-quality-v6.md`: `@5` + the privacy-layer cap, composite ≤ 0.65 when ANY layer of a privacy
control is broken, whatever the backstop). Judge prompt: `.claude/evals/prompts/judge-system-v2.md`.

**Seats** (`.claude/evals/seats.json`, Alex's static role map; no code edits it): `claude` (Sonnet) **voting** ·
`openai` (gpt-5.4-mini) **shadow**, runs on every build, hidden until the ack · `gemini` **off** (adapter kept).
**Ground rules:** score + flag only; never rewrite, never hard-block. Missing context → say so, score conservatively.

## Inputs
- **What changed:** one file (`--artifact P`), several (`--files A B …`), or a git range (`--range BASE..HEAD`). For a
  branch, pass the range against the **merge-base** (`$(git merge-base origin/main HEAD)..HEAD`), never two-dot against
  a moving `origin/main`. Telemetry paths are excluded automatically; don't commit `.patch` bundles to `logs/`.
- **`--artifact-type`** (skill/command/hook/ref/code/deep_read) and **`--spec-file`** (the in-repo spec; repeatable)
  and/or `--context "…"`. Under 400 chars of spec = evidence parity false; rebuild with a spec rather than run blind.
- **Mode:** `interactive` (default) or `autonomous` (every escalation fails safe to FLAG).

## The run
1. **Start:** `python3 .claude/evals/judge.py run --range <base>..HEAD --artifact-type <t> --spec-file <spec>`
   (try `--dry-run` first: builds the bundle, runs the privacy guard, prints the OpenAI worst-case cost, sends
   nothing). It builds ONE bundle (pre-passes `check-refs` / `check-tombstones` / `density-check` per file; exit 3 =
   privacy guard, nothing sent), runs the shadow adapter on it, and prints the brief path.
2. **Sonnet seat (parent thread only; a subagent cannot spawn one):** dispatch the `Agent` tool, `model: sonnet`, prompt
   *"Read `<brief>` and follow it exactly. Return only the JSON object."* Save its JSON to the path `judge.py` printed.
3. **Finish:** `python3 .claude/evals/judge.py run --resume <run-id> --sonnet-verdict <that json>`. It logs the verdict
   through `seat-log.py` (the only writer for this seat: real UTC time, content hash, harness-computed score, quotes
   checked against the whole bundle), merges, and prints **one line**, plus the REVISIT banner when due.
4. **Act on the line:**
   - `PASS (auto)` → done. No prompt; it is batch-acked weekly in `/rigor-review` (`judge.py pending`).
   - `FLAG (auto)` → the voter flagged: show its top 1–2 defects and fix. No ack prompt (rework is the conversation).
   - `… (escalated)` → show the voter's per-criterion reasoning and the reasons (`verdict_mismatch:<shadow>`,
     `score_divergence`, `shadow_major_defect:<shadow>`, or an integrity reason, which always ends in FLAG). Ask Alex
     once: **"agree / disagree, and why?"** Write it with `python3 .claude/evals/judge.py ack --run <quorum-run-id>
     agree|disagree "why"`. Only after the ack does the shadow's verdict appear. Never write `alex_ack` by hand.
   - `failsafe_flag` (autonomous) → recorded; queued for Alex; nothing auto-resolved.

## Failure modes
- **Shadow adapter fails** (network, budget exit 4) → recorded as `shadow_missing`; the voter still decides. Say so.
- **Sonnet JSON rejected** by `seat-log.py` → the voter is missing → integrity FLAG. Re-dispatch, then `--resume` again.
- **Voter quotes unverified** (> 30%) → the voter loses its vote → `no_voting_seat` → FLAG. Check the brief reached it.
- **Big range** (> 60k chars of files) → files over 400 lines go as changed hunks ±40 (`bundle_mode: hunks` in every
  row). Say that a hunk-mode pass is not a full read.
- **Rubric feels wrong for the artifact type** → put it in the ack note; don't bend the score.

## References
`.claude/evals/{judge.py, judge_lib.py, quorum_merge.py, calibration_stats.py, seats.json, README.md}` ·
`.claude/hooks/{seat-log.py, openai-judge.sh, gemini-judge.sh, check-refs.sh, check-tombstones.py, density-check.sh}` ·
spec `.claude/references/judge-right-size-yed-231.md` · coordinates with `eval-harness` (Notion `348d3699…`), which owns `rubric_version`.
