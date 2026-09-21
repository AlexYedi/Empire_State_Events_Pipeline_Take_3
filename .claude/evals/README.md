# `.claude/evals/` — the shared eval home

The single home for LLM-as-judge quality evaluation in this pipeline. Established 2026-06-26 by the build-rigor layer (Linear YED-89 / PRD US-3); **coordinates with the `eval-harness` project** (Notion Project Ideas `348d3699…`), which owns the rubric/judge conventions and `rubric_version`. When eval-harness is built, its skill rubrics (pre-event-content, etc.) live here too. **One judge system, not two** (never-duplicate-state).

## Layout
- `rubrics/<name>.md` — rubric-as-code: criteria + weights + pass bands + ≥1 pass/fail example each, plus a machine-readable JSON block. Versioned as `<name>@N`; never mutate old versions (bump instead). **Current build rubric: `build-quality@5`** (`rubrics/build-quality-v5.md`, live 2026-09-19 — earned-1.0 scale + 0.85 mid anchor, `defects[]` required, NEW spec-drift cap correctness ≤0.70; YED-206). Previous: **`build-quality@4`** (`rubrics/build-quality-v4.md`, live 2026-08-21 — added the artifact-type-scoped **density cap** ≤0.65 for `deep_read` renders, mechanized by `hooks/density-check.sh`; YED-136). For every artifact type except `deep_read`, `@4` ≡ `@3`. `build-quality-v3.md` (`@3`, confidence-honesty cap), `build-quality-v2.md` (`@2`, dangling-ref + command-skeleton caps) and `build-quality.md` (`@1`) are retained for runs scored under them.
- `prompts/judge-system.md` — the shared judge system prompt, v1 (kept for runs scored under it).
- `prompts/judge-system-v2.md` — **current** (2026-09-19, YED-206): defects-before-scores, an earned 1.0, spec-before-impression, don't-trust-docstrings; the harness (not the judge) computes the composite.
- `calibration_stats.py` — per-seat agreement · always-pass baseline · Cohen's κ · flag recall · flat-1.0 rate.
- `logs/<YYYY-MM-DD>-<artifact>-<run-id>.jsonl` — **authoritative** append-only run-log (the source of truth). Notion is a *deferred projection*, not the store (same contract-first pattern as `build-session-contract.md`).

## Run-log record schema
```json
{ "run_id":"", "timestamp":"", "artifact":"", "artifact_type":"skill|command|hook|ref|code",
  "rubric":"build-quality@1", "judge_model":"", "session_id":"",
  "criterion_scores":[{"id":"","score":0.0,"reasoning":""}],
  "weighted_score":0.0, "verdict":"pass|flag", "alex_ack":null }
```
`alex_ack` is the **calibration field** — `null` until Alex reviews, then `"agree" | "disagree"` (+ optional note).

## The calibration gate — per seat, and raw agreement is NOT enough (revised 2026-09-19, YED-206)
LLM-as-judge has **self-preference bias** — here it's judging work produced by a similar model (the "judge circularity" risk eval-harness flagged as R1). The original gate was "≥20 runs at ≥80% judge–human agreement". **That number is gameable by a seat that passes everything**: when Alex flags ~1 in 5 artifacts, a constant "pass" scores ~80% on its own. The Gemini seat's celebrated "83%" was exactly its always-pass baseline (triage: `.claude/notes/gemini-judge-triage-2026-09-19.md`).

**The gate is now four numbers per seat**, produced by `python3 .claude/evals/calibration_stats.py`:

| metric | bar | why |
|---|---|---|
| agreement vs Alex | ≥ 0.80 **and above that seat's always-pass baseline** | the old number, kept but no longer alone |
| Cohen's κ | ≥ 0.60 | agreement corrected for chance; κ≈0 = adds nothing over always-passing |
| flag recall | ≥ 0.60 | of the artifacts Alex would send back, how many the seat caught — what a gate actually needs |
| flat-1.0 rate | < 0.30 | a seat scoring 1.0 on every criterion is low-information whatever its verdict |

**Standing as of 2026-09-19, recomputed after YED-201 restored the round-1 records a log-overwrite bug had been
destroying** (53 acked runs over 34 artifacts — a bigger, flag-heavier sample than the first cut of this table):

| seat | scored vs Alex | agree | baseline | κ | flag recall | flat 1.0 | standing |
|---|---|---|---|---|---|---|---|
| `claude:haiku` | 27 | 0.82 | 0.67 | 0.55 | 0.56 | 0.00 | advisory (κ + recall under) |
| `claude:sonnet` | 15 | **0.73** | 0.33 | **0.50** | 0.60 | 0.00 | advisory (agreement + κ under) |
| `gemini` | 26 | 0.65 | 0.62 | **0.12** | **0.10** | **0.81** | **advisory — fails 3 of 4** |
| `claude:opus` | 6 | 1.00 | 1.00 | — | — | 0.00 | not a seat; κ undefined (zero-variance sample) |

**No seat currently clears all four bars, including the one this file called "trusted" earlier the same day.** That
earlier read came from 10 scored runs on a pass-heavy sample; the restored records added flag-heavy ones and Sonnet's
absolute agreement fell to 0.73. Read honestly: Sonnet is still the most *informative* seat by a wide margin — 0.73
against a 0.33 always-pass baseline is a real signal, where Gemini's 0.65 against a 0.62 baseline is nearly none — but
**the bar is not moved to make a seat pass.** Consequence: the quorum escalates more often, which is the fail-safe
direction. Re-check as acks accrue; if the 0.80 absolute bar proves wrong for flag-heavy samples, change it in a dated
decision, never silently.

- Seats are **advisory** until they clear all four bars; advisory seats are recorded and surfaced but **cannot auto-accept** a quorum (`quorum-merge.sh` escalates on divergence / flat ceiling / missing parity).
- Re-check on a rolling basis; failing a bar ⇒ fix the seat or the rubric, don't trust the score.
- The judge **scores + flags; it never auto-rewrites and never hard-blocks.**

## Three seats, one trust ladder (YED-209, 2026-09-19)

Spec: `.claude/proposals/third-judge-seat-openai.md`. How to run it: the `judge-build` skill.

| File | Job |
|---|---|
| `seats.json` | one row per seat: `status` (shadow / advisory / voting), `independence_group`, `since` (start of its current prompt+rubric regime). Promotion = Alex edits this file. A 4th seat is a row here, not new code |
| `judge_lib.py` | what every seat shares: the scorer (parity-tested against the jq in `gemini-judge.sh`), the one evidence bundle + its sha256, verbatim quote verification, the privacy guard, the spend ledger + caps |
| `quorum_merge.py` | the N-seat merge. Voting seats decide, advisory seats can only add caution, shadow seats are recorded and hidden until Alex acks. A split is never auto-resolved |
| `calibration_stats.py --gate` | each seat's *effective* status: configured, lowered one rung if a demotion rule fires on its last 20 prospective runs since `since` |
| `pricing.json` · `spend-ledger.jsonl` | prices with an as-of date; one ledger row per paid API attempt, failures included. Caps: `JUDGE_MAX_USD_PER_RUN` 0.50 · `JUDGE_MONTHLY_CAP_USD` 8 · `JUDGE_TOTAL_CAP_USD` 45 |
| `controls.py` · `controls/manifest.json` | the control set: real labelled artifact states by git blob. `run` judges them and scores against the label |
| `.claude/hooks/run-canaries.sh` · `controls/state.json` | the SCHEDULED half: a 3-item sample per seat (~$0.13), recorded per seat with the resolved model id. `--full` runs the whole set |
| `test_judge_lib.py` · `test_quorum_nseat.py` · `test_canary_gate.py` · `test_quorum_scenarios.py` | 23 + 40 + 7 + 6 offline cases; run all four before changing any of the above |

**Truth is matched on content, not file name.** Every new row carries `artifact_sha256`; a run is scored only against
acks on the same hash. A legacy row without a hash is left *unscored* if git shows the file changed between the ack
and the run. (Before this, a file that was flagged, fixed and re-judged the same day had its correct "pass" scored
against the old flag, and the trusted seat read κ 0.53.)

**Canaries (built 2026-09-20).** Run `bash .claude/hooks/run-canaries.sh` before `/rigor-review` and after any
seat/model change. A seat is demoted a rung on **two consecutive failures**, when its **resolved model id changed**
since the last green run (a silent snapshot swap invalidates freshness), or when a **voting** seat's canary is
>14d old. A seat that has *never* run one is reported as `never run`, not demoted — absence of evidence is not
failure, but it is never silently read as "fresh" either: every quorum record carries each seat's canary status.

**Demotion rules** (each has a minimum sample; they apply to every seat, the trusted one included): flat-1.0 rate ≥ 0.30
over ≥ 10 runs · flag recall < 0.50 on ≥ 4 real flags · flag precision < 0.40 on ≥ 5 seat flags (over-flagging) ·
κ < 0.40 on n ≥ 15. **Voting bar** (informational; promotion stays manual): n ≥ 25 prospective with ≥ 8 real flags ·
κ ≥ 0.60 · recall ≥ 0.70 · precision ≥ 0.60 · flat < 0.20 · agreement ≥ always-pass baseline + 0.10.
Rows with `calibration_set` in {control, bakeoff, negative-control, triage-experiment} never count toward either.

## Deferred (non-destructive, do NOT build now) — now YED-188 (parked slate) + `platform-constraints.md` (2026-09-18)
A separate-model / cross-judge quorum (independence) and a Notion/PostHog projection of scores — per the lean-foundation decision (2026-06-26). The run-log contract above stays stable when added.
