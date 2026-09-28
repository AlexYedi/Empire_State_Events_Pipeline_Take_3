# `.claude/evals/` — the shared eval home

The single home for LLM-as-judge quality evaluation in this pipeline (established 2026-06-26, YED-89; coordinates
with the `eval-harness` project, Notion `348d3699…`). **One judge system, not two.** Since YED-231 (2026-09-28) the
build judge is **one Sonnet reviewer that raises flags**: design `.claude/references/judge.md`, method
`.claude/skills/judge-build/SKILL.md`.

## Layout
| File | Job |
|---|---|
| `judge.py` | the one entry point: `run` (bundle + reviewer brief) → `run --resume` (log + one-line verdict) → `ack` (flags only) |
| `judge_lib.py` | score (`build-quality@6` caps), `finalize()` (final pass/flag + reasons, guarded paths), bundle build (file / files / git range), quote check, privacy guard |
| `../hooks/seat-log.py` | the ONLY writer of reviewer rows (real UTC time, content hash, harness-computed score) |
| `rubrics/build-quality-v6.md` | the rubric, **frozen at `@6`**; never mutate it. Older versions (`@1`–`@5`) are in git history |
| `prompts/judge-system-v2.md` | the reviewer's instructions (defects before scores, earned 1.0). v1 is in git history |
| `calibration_stats.py` | a plain **report**: judge-vs-Alex agreement, always-pass baseline, κ, flag recall, flat-1.0 rate, runs per artifact class. **Nothing gates on it** |
| `controls.py` · `controls/manifest.json` | the control set (real labelled states by git blob). `controls.py plan` prints the runs. Run it only when the reviewer's model id changes |
| `logs/*.jsonl` | **authoritative, append-only** run log. Local only: gitignored and untracked since 2026-09-28 (history to that date is in git at `2510701`) |
| `rubrics/dossier-quality.md` | the `/interview-prep` dossier rubric |
| `score_entities.py` · `post-event-brief-template-evidence.md` | transcription entity scorer and brief-template evidence, still cited by `/ingest-recording` and `/post-event-content` |
| `test_judge_lib.py` · `test_judge_e2e.py` · `test_bundle_multifile.py` · `test_null_baseline.py` | offline, free; run all four (`python3 .claude/evals/test_<name>.py` from the repo root) before changing any of the above |
| `test_event_claim.py` | the `event-claim.py` hook's tests (not the judge) |

## Run-log rows
Reviewer row (written by `seat-log.py`):
```json
{ "run_id":"", "timestamp":"", "artifact":"path | range:abc1234..def5678 | files:N@sha", "artifact_sha256":"",
  "artifact_type":"skill|command|hook|code|ref|deep_read|dossier", "rubric":"build-quality@6",
  "judge_model":"claude:sonnet", "judge_provider":"anthropic", "session_id":"",
  "criterion_scores":[{"id":"","score":0.0,"reasoning":""}], "weighted_score":0.0, "verdict":"pass|flag",
  "final_verdict":"pass|flag", "flag_reasons":[], "defects":[], "quote_check":{}, "calibration_set":"prospective",
  "evidence_parity":true, "bundle_sha256":"", "bundle_version":3, "alex_ack":null }
```
`verdict` is the score verdict; `final_verdict` adds the deterministic rules (guarded path, privacy flag, flat 1.0,
fabricated quotes). Ack row (written by `judge.py ack`, never by editing a row):
`{"record_type":"ack", "run_id", "artifact", "artifact_sha256", "verdict": <final_verdict>, "alex_ack":"agree|disagree", "alex_ack_at", "note"}`.
Older rows from the retired seats (`gemini`, `openai`, `quorum`, `quorum_ack`) are in git history at `2510701`.

## Reading the report honestly
A metric a do-nothing policy scores just as well on is not a standard (YED-212): "83% agreement" was once exactly the
always-pass baseline. `calibration_stats.py` prints every agreement number beside that baseline, and its `--json`
carries a `null_check` per seat: `unvalidated` when agreement does not beat the baseline by +0.10 (n ≥ 10). Truth is matched on content hash, not file name. Alex's acks
seed truth; rows in `calibration_set` {control, bakeoff, negative-control, triage-experiment} never count.

## What was removed (YED-231)
The Gemini and OpenAI seats, the quorum merge, seat statuses and demotion rules, canaries, the last-voting-seat guard,
the spend cap and `pricing.json`; on 2026-09-28 their residue (rubrics @1–@5, prompt v1, bake-off
controls, `emit-judge-runs.sh`, `spend-ledger.jsonl`) and the June transcription-eval corpus were removed from the tree. The judge scores and flags; it never auto-rewrites and never hard-blocks.
