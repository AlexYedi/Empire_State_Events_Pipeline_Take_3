# Right-size the build-quality judge — build spec (YED-231)

**Status:** Accepted 2026-09-28 (Alex ruled §9) · infra spec (satisfies DoD item 1 per YED-129) · Linear YED-231 · supersedes the
run-path sections of `cross-provider-judge.md` and `.claude/proposals/third-judge-seat-openai.md` §1–2 (they stay as history).
**Rubric unchanged:** `build-quality@6` stays; this is a harness change, not a rubric bump.

## 1. Problem (with the evidence)

The eval layer costs more per build than the build it gates, and it manufactures fix-on-fix work.

| Evidence (from `.claude/evals/logs/`, read 2026-09-28) | What it shows |
|---|---|
| **YED-227:** 6 judge rounds (`r1, r2, r2b, r3, r4, r5`), 16 seat rows, 6 committed `.patch` files (2,612 lines in `logs/`). Gemini said `pass 0.94–0.97` in every round; OpenAI/Sonnet flagged rounds 1–3. Both quorums escalated on `score_divergence` — driven by the seat with κ 0.07. | An uninformative seat sets the escalation rate. |
| **YED-236:** build → judge fixes → privacy-guard → quorum disagree → new rubric cap (`@6`) → re-judge → ack. Multi-file work was hand-assembled into `artifacts/judge-inputs/*.md` (3,334 lines across 3 docs). | Multi-file builds have no first-class path; the workaround is a hand-built bundle. |
| **`no_voting_seat · evidence_unverified:claude`** on `deep-read-gate.sh` and `gate-sweep-sessionstart.sh` (09-27): Sonnet quoted from the *spec files in the bundle* and from a sibling hook; `verify_quotes()` only searches the artifact file → 3/4 and 2/4 "unverified" → vote stripped → `flag`, acked. | The quote-checker's haystack is one file; the bundle is not. Correct quotes are counted as fabrication. |
| **Gate today** (`calibration_stats.py --gate`): Sonnet κ 0.25 / recall 0.44 (n=15) → *would be demoted*, held only by the last-voting-seat guard. OpenAI κ 0.55 / recall 0.67 (n=13) → sits in **shadow**, "demoted" by a canary failure that the recurrence log records as an adapter bug. Gemini κ 0.077 → effective shadow. | The ladder holds the worst-measuring seat as the voter and shadows the best one. It has produced 0 promotions in 70 days; every output is overridden. |
| 50 quorum rows: 16 escalated. Reasons: `score_divergence` 8, `no_voting_seat` 4, `flat_ceiling` 2, `verdict_mismatch` 1, `advisory_flag` 1, `seat_missing` 1. | Only **1 of 16** escalations was a genuine verdict split. 15 were mechanics. |
| `alex_ack` is written by hand into the JSONL (SKILL Step 5: "write into the quorum record"). | The exact defect class `seat-log.py` was built to end (hand rows corrupted the scorecard 09-19). |

## 2. Target shape

**Before (per artifact):** build bundle → run 3 seats by hand (Gemini sh, OpenAI sh, Sonnet subagent) → `seat-log.py` → `quorum_merge.py` (calls `calibration_stats.gate()` → ladder → effective status; reads canary state) → escalate on 11 reason types → ask Alex to ack every run → hand-edit `alex_ack` → optional `--reveal-shadow`.
Multi-file: hand-write a `.patch`/`judge-inputs/*.md`, judge it as `code`, quotes verified against that one file.

**After (one command):**
```
python3 .claude/evals/judge.py run  (--artifact P | --files A B C | --range BASE..HEAD) --artifact-type T
                                     --spec-file S [--context ...] [--mode interactive|autonomous]
python3 .claude/evals/judge.py ack  --run <quorum-run-id> agree|disagree ["note"]      # the ONLY ack writer
```
`run` = bundle (multi-file aware) → dispatch OpenAI (+Gemini if enabled) adapters on the bundle → print the Sonnet
brief for the parent thread to dispatch (SDK: the subagent must be spawned by the parent) → `seat-log.py` → merge →
**one line of output**. Verdict = the voting seat's. Prompt Alex only on: `verdict_mismatch` (a shadow's verdict
differs), `score_divergence` (|Δ| ≥ 0.15 vs a quote-verified shadow), `shadow_major_defect:<seat>` (a shadow filed a
`major` defect whose quote verified, on a pass), or an integrity reason (voting seat missing/invalid/unverified →
`flag`). Clean pass → logged, `alex_ack: null`, no prompt. Shadow verdicts stay hidden until `ack`.
`seats.json` becomes a static role map. `calibration_stats.py --check` reports per-seat κ/recall/null-check and raises
the **revisit banner**; it changes no status.

## 3. Removal list (each: what · why)

**Files deleted (5):**
- `.claude/hooks/run-canaries.sh` (90) — canaries retired (Alex). Its state was last written 09-21 and is wrong today.
- `.claude/evals/controls/state.json` — canary state; the only reader was `gate()`.
- `.claude/evals/test_canary_gate.py` (43) — tests rules that no longer exist.
- `.claude/hooks/quorum-merge.sh` (148) — the 2-seat merge and the **third copy** of the scoring arithmetic; superseded by `quorum_merge.py` since YED-209. No caller after SKILL/command rewrite.
- `.claude/evals/test_quorum_scenarios.py` (45) — tests `quorum-merge.sh`; every scenario has an equivalent in `test_quorum_nseat.py`.

**Functions / fields deleted:**
- `calibration_stats.py`: `gate()`'s ladder body — `ORDER`, `CANARY_STATE`, `CANARY_STALE_DAYS`, the 3 canary rules, `meets_voting_bar`, the last-voting-seat guard (~70 lines). Replaced by `check()` (§4). `compute()`, `kappa()`, `null_check()`, content-matched truth: **kept verbatim**.
- `quorum_merge.py`: advisory tier and `advisory_flag`; independence blocs / `same_group_only` / `independent_blocs` (one voter → no blocs); `canary_freshness`; `demotions`; the `gate()` call; legacy `claude`/`gemini` back-compat blocks; `quorum_rules` string (~90 lines). Kept: integrity reasons, `evidence_unverified` stripping, hide-until-ack, `--reveal-shadow` refusal, append-only log.
- `seats.json`: `statuses` doc block, `independence_group`, per-seat `note`/bake-off prose. Kept: `id`, `seat_name`, `provider`, `runner`, `model`, `since`, plus new `role: voting|shadow|off`.
- `test_quorum_nseat.py`: the ~14 advisory/bloc/canary cases. `test_judge_lib.py`: the `quorum-merge.sh` parity block (~15).
- `.claude/evals/logs/*.patch` — **stop committing** (a range bundle is reproducible from `BASE..HEAD`). Existing 10 files stay (log rows name them); their removal rides YED-229.

**Doc sections deleted:** `judge-build/SKILL.md` "three-seat run" 5-step + Steps 2–4 two-seat fallback + per-seat standing + scoped weighting (97 → ~45 lines) · `commands/judge-build.md` orchestration steps 3–5 rewritten to the one command · `cross-provider-judge.md` "Scoped quorum", "Quorum resolution", "Judge-trigger / merge mechanic" (→ one pointer here) · `evals/README.md` "Three seats, one trust ladder" table rows for canaries/gate, the Canaries and Demotion-rules paragraphs, the last-voting-seat paragraph · `rigor-review/SKILL.md` line 23 (`run-canaries.sh`) · `value-action-registry.md` row 42 (seat effective status → revisit trigger) · `third-judge-seat-openai.md`: one header line "§1–2 superseded by judge-right-size-yed-231.md".

**Kept on purpose:** `controls.py` + `controls/manifest.json` (16 labelled blobs; the on-demand regression set that validated `@6` an hour before this spec — it is data, not the canary mechanism; `--artifact-blob` and `verified_blobs` in the privacy guard stay for it) · `test_adapter_contract.py` · `emit-judge-runs.sh` · spend ledger/caps · `check-refs`/`check-tombstones`/`density-check` pre-passes · all rubric caps incl. `privacy_layer_defect` · `seat-log.py` · defects-before-scores schema.

## 4. Change list

1. **`judge_lib.build_bundle` → multi-file** (`bundle_version: 3`). Inputs: `--artifact P` (unchanged) | `--files A B…` | `--range BASE..HEAD` (files = `git diff --name-only`, minus `.claude/evals/logs/`, `.claude/artifacts/**.jsonl`, `.claude/.state/`; the unified diff is included as a "WHAT CHANGED" section; pass `--range` against the merge-base, as the skill already says). Bundle carries `files[]` = `{path, sha256, lines}` with each file numbered under its own `===== FILE: path =====` header; pre-passes run per file; privacy guard runs per file (already list-shaped). `artifact` = `P` | `files:<n>@<sha12>` | `range:<base7>..<head7>`; `artifact_sha256` = sha256 over sorted `(path, sha256)` pairs so content-matched calibration still works. **Size rule:** if full-file text > 60k chars, files > 400 lines are sent as changed hunks ±40 lines (`bundle_mode: hunks`, recorded); the quote haystack is exactly what was sent.
2. **`verify_quotes` haystack = every text in the bundle** (all files + spec files + context), returning `matched_in` per defect. A defect schema gains optional `file`. Single-file behaviour is unchanged (the haystack was already the artifact; spec text is added — quoting the decision you say is contradicted is required by judge-system-v2 rule 4, so it must verify).
3. **`judge.py`** (new, ~150 lines): `run` orchestrates §2; `ack` is the sole `alex_ack` writer (stamps `alex_ack_at` UTC, refuses a second ack on the same row, appends a `quorum_ack` row rather than rewriting — append-only holds; `calibration_stats` reads the latest ack per run_id). `judge.py run` prints the revisit banner from `calibration_stats.check()` when due.
4. **`quorum_merge.merge`** simplified per §2/§3; new reason `shadow_major_defect:<seat>` (only from a seat whose quotes verified). The Sonnet seat's own `flag` → `auto flag` (rework is already a conversation; no ack prompt).
5. **`calibration_stats.check(since, min_new_acks=5)`** replaces `gate()`: for the voting seat, on prospective, parity-true acks with `timestamp ≥ since` (`2026-09-28`, from `seats.json.revisit.since`): `revisit_due` when `new_acks ≥ 5` and (`κ < 0.40` on `n ≥ 15` or `flag_recall < 0.50`). Prints the numbers, the null-check, and the named replacement candidate (see Q3). Exit 0 always; the *banner* is the mechanism, Alex's edit to `seats.json` is the decision.
6. **`seats.json`**: `claude: voting`, `openai: shadow`, `gemini: shadow` (or `off`, Q1); `revisit: {since: 2026-09-28, min_new_acks: 5, kappa_floor: 0.40, recall_floor: 0.50, n_min: 15}`.
7. **Weekly batch-ack in `/rigor-review` Step 2**: list the week's un-acked clean passes (artifact, score, top defect) and take one answer — "all agree" or the exceptions — written via `judge.py ack`. This is what keeps the calibration truth set from collapsing to escalations only (pre-mortem 1).
8. **Optional, recommended if Gemini stays on:** add `quote` to the Gemini response schema (`gemini-judge.sh` `SCHEMA`, ~4 lines) and run `verify_quotes` on its row via a 6-line python call, closing YED-187. Without it a Gemini `major` can never escalate (unverifiable = stripped), which is acceptable and should be stated in `seats.json`.

**Resolution of the gate/ladder tension (scope item 4):** the gate **reports and escalates; it never writes status.** `seats.json` is a static role map edited only by Alex. Why: (a) Alex's ruling makes demotion his decision, so the code's job is to make the decision unavoidable, not to take it; (b) an automatic demotion of the only voter can only be "held" (today's guard), which is a status write that is immediately un-written — the guard proved the auto-write was never going to be allowed to act; (c) a single-writer role map removes the whole `configured`/`effective` dual-state that every reader had to reconcile. The revisit trigger survives as a banner with the exact numbers, surfaced at every `judge.py run` and at `/rigor-review`.

## 5. Alternatives considered and rejected
- **Keep the ladder, fix its inputs** (better truth matching, more acks). Rejected: 0 promotions in 70 days; its one live output today (demote Sonnet) is suppressed by its own guard. A mechanism whose output is always overridden is ceremony.
- **Promote OpenAI to voter now** (best κ/recall). Rejected: n=13; Alex's ruling routes this through the revisit trigger. The spec pre-names it as the candidate so the trigger has a default answer.
- **Judge the diff only, never full files.** Rejected as default: spec-drift, dangling-ref and tombstone defects are cross-file. Hunk mode is the size fallback, recorded as such.
- **Sample the shadow (1 in 3 runs) to save cost.** Rejected: Sept spend was $9.04 on 97 OpenAI attempts; the shadow is the recall net for a voter measuring 0.44 and must see every run.
- **Delete `controls.py` with the canaries.** Rejected: it is the only way to re-judge a historical blob under a new rubric through the privacy guard, used for `@6` on 09-28.

## 6. Pre-mortem (3 failures, each with a mitigation)
1. **The truth set starves or skews.** No per-run ack → acks come only from escalations (the hard cases) → κ for the voter is measured on a biased subset → the revisit fires spuriously, or never reaches n. *Mitigation:* change 7 (weekly batch-ack, one answer for the week's clean passes); `check()` prints `n_from_escalation / n_total` next to κ so a skewed sample is visible; the null-check stays.
2. **Range bundles blow the budget or the context.** PR #139 full-file = ~78k chars (spine_client.py alone is 37k) against a 21k-char diff; the OpenAI per-run cap is $0.50 and the Sonnet subagent has a context ceiling. *Mitigation:* the 60k-char rule with hunk mode; telemetry paths excluded by default; `--dry-run` shows the worst-case cost before any spend (already exists); `bundle_mode` in the record so a hunk-mode pass is never mistaken for a full read.
3. **One voter with recall 0.44 means real defects ship as silent "clean passes".** *Mitigation:* `shadow_major_defect` from a quote-verified OpenAI seat (recall 0.67) is exactly the net; the revisit banner is already armed on today's numbers and will very likely fire within the next 5 acks — the spec names the candidate and the decision is a one-line `seats.json` edit. Watch the other side too: if `shadow_major_defect` pushes the escalation rate over the registry's 40% line, tighten it to "major **and** shadow flag" in a dated decision.

## 7. Sequencing (on top of `@6`)
`@6` is **already on `main`** (PR #149, `f725ec5`); this worktree is cut on top of it. Nothing here touches `judge_lib.score()` or the rubric. Order, one PR each, each independently mergeable:
(1) bundle multi-file + haystack quote check + `bundle_version 3` (no behaviour change for single-file runs) → (2) `judge.py run/ack` wrapping the existing adapters and the simplified merge; `seats.json` role map; `check()` → (3) deletions (§3) + doc rewrites → (4) the positive control (§8) and the run's own judge. Cut from `origin/main` after #149; the `esep-cap` worktree named in the brief does not exist on disk, so there is no live diff to compose against.

## 8. Test plan
- **Existing, unchanged:** `test_judge_lib.py` score fixtures (incl. the 3 `@6` privacy fixtures) · `test_null_baseline.py` · `test_adapter_contract.py` (both adapters must still accept `--bundle`, refuse `--context` with it, refuse a forged blob).
- **Existing, trimmed/extended:** `test_quorum_nseat.py` — drop advisory/bloc/canary cases; add: shadow `major` with verified quote on a voter pass → `escalated/pass`; same with `evidence_unverified` → `auto/pass`; shadow verdict mismatch → `escalated/pass`; voter flag → `auto/flag`; voter unverified → `escalated/flag (no_voting_seat)`; autonomous variants → `failsafe_flag`.
- **New `test_bundle_multifile.py` (offline):** range bundle over `c607c08..42602e4` (PR #139) asserts the file list excludes the 5 `.jsonl` telemetry rows and includes the 7 code/doc files; `artifact_sha256` is stable across two builds; a quote from file 2 verifies; a quote from a `--spec-file` verifies (the deep-read-gate regression: the 3 quotes that were stripped 09-27, replayed against a bundle that includes the spec texts, must now verify); a fabricated quote still fails; a range containing a gitignored path is refused (exit 3); the 60k rule flips `bundle_mode` to `hunks`.
- **New `test_check_revisit.py` (offline):** synthetic logs → `check()` says `not_due` at 4 new acks, `revisit_due` at 5 with κ 0.25, `not_due` at 5 with κ 0.6/recall 0.7; never writes `seats.json`.
- **Positive control (live, ~$0.10):** `judge.py run --range c607c08..42602e4 --artifact-type hook --spec-file .claude/evals/test_gate_in_progress.sh` → expect a `pass`/`flag` with **no** `no_voting_seat`, `seat_missing`, `evidence_mismatch`; Sonnet `quote_check.unverified ≤ 1`; one printed line; a prompt only if a shadow disagrees. Then `judge.py run` on this build's own PR (DoD item 4).

## 9. Open questions for Alex
1. **Gemini: shadow (your ruling) or `off`?** Measured κ 0.077 / recall 0.19 / flat 0.36; no `quote` field, so its `major` defects cannot escalate with evidence. My recommendation is `off` with the adapter retained (one-line `seats.json` flip to bring it back). If shadow, change 8 is worth its ~10 lines.
2. **Batch-ack in `/rigor-review`** as the replacement for per-run acks on clean passes — accept? Without it the calibration truth set becomes escalations-only (pre-mortem 1).
3. **Replacement candidate if the revisit fires:** OpenAI `gpt-5.4-mini` (κ 0.55, recall 0.67, n=13, $0.044/run) is the only seat with data; the alternative is Opus, which has none. Name it in `seats.json.revisit.candidate` now?
4. **"HIGH severity" = the schema's `major`?** The schema has `major|minor` only; I read HIGH as `major`. Confirm, or we add a third level (I'd rather not).

## 10. Confidence, irreversibility, estimate
- **Confidence: 75%** (solid: the mechanics diagnosis — 15/16 escalations were harness, not judgement; the quote-haystack root cause is reproducible from the logs. Softer: the 60k/400-line size rule and the 5-ack revisit window are first guesses).
- **Irreversible?** Nothing destructive: deletions are git-recoverable; logs stay append-only. Two things change the *data going forward* and should be named as decisions: (a) clean passes stop carrying a per-run ack (selection of the truth set changes); (b) new quorum rows drop `canary_freshness`/`effective`/legacy `claude`/`gemini` blocks — readers must tolerate absence (calibration_stats already does).
- **Estimate:** removed ≈ 700 lines / 5 files; added ≈ 370 lines / 1 file (`judge.py`) plus 2 test files (~120) → **net ≈ −330 lines, −4 files** (spec doc excluded). Build: 2 sessions.

## Decision log
- 2026-09-28 — Gate reports, never writes status; `seats.json` is Alex's static role map (§4). Rationale: the last-voting-seat guard already proved auto-demotion of the voter was never going to be allowed to act.
- 2026-09-28 — Clean pass = no prompt; truth set maintained by weekly batch-ack (pending Q2).
- 2026-09-28 — `controls.py` kept as on-demand regression data; canary *scheduling + demotion* retired.
- 2026-09-28 — Quote haystack = the whole bundle; `bundle_version 3`; range/files bundles first-class; `.patch` files no longer committed.
- 2026-09-28 — `quorum-merge.sh` deleted (third copy of the arithmetic); `quorum_merge.py` is the one merge.
- 2026-09-28 — **Alex ruled §9:** Q1 Gemini `off`, adapter kept (change 8 dropped) · Q2 weekly batch-ack in `/rigor-review` accepted · Q3 `revisit.candidate` = OpenAI `gpt-5.4-mini` · Q4 HIGH = schema `major`, no new level.
- 2026-09-28 — Sequencing simplified: phases (1)–(3) land as separate commits on one branch / one PR, not three PRs (one reviewer, one judge run).
