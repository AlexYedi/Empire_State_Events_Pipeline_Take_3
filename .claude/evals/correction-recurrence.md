# Correction-recurrence log

Append-only. Tracks **recurring corrections** (the same class of mistake across builds) surfaced in the weekly `/rigor-review`. A class hitting threshold (≥ N) triggers a **proposed** codified fix (rubric / DoD / skill / few-shot) → Alex approves → applied (versioned). This is the feedback→improvement channel that makes corrections *stick* instead of evaporating (the root-cause the measurement layer cures).

Format: `- {YYYY-MM-DD} | class: {short label} | count: {n} | action: {watch | proposed: <fix> | applied: <fix + version>}`

## Entries

### 2026-07-15 — first `/rigor-review` (window: 2026-07-08 → 2026-07-15)
- 2026-07-15 | class: thin-declarative-command (a `.claude/commands/*.md` names real agents but ships no orchestration — no dispatch order, no parallel/serial control flow, no output destination) | count: 5 (run-market-landscape-study, analyze-competitive-landscape, create-messaging-brief, generate-channel-copy, test-and-report — all built Jul-2 in one sitting) | action: **proposed** — a command-orchestration authoring convention + a DoD scope-test note for command/pipeline builds (see rigor-review 2026-07-15; PENDING Alex approval). Judge detection was correct (Alex acked all 5 flags agree); the recurrence is in the *builder*, not the judge.
- 2026-07-15 | class: dangling-reference-in-skill (a SKILL.md references a repo file that was never created — trend-radar → `.claude/references/signal-taxonomy.md`) | count: 1 | action: **watch** — below threshold. Queued fix if it recurs (or on Alex go-now): `build-quality@2` completeness anchor so a load-bearing referenced-but-absent file caps the composite below the 0.70 pass band. Surfaced by the one judge–human disagree this batch (judge passed trend-radar at 0.76; Alex: should have flagged — judge too lenient on missing references).
- 2026-07-15 | class: judge-item-waived-advisory (DoD item 4 waived because the judge is pre-calibration / new skills need a fresh session to register) | count: 2 (sessions 9523d6a1, aa0f8ce9) | action: **watch** — self-resolving; calibration now 15/20 acked runs @ 93.3% agreement, closing on the ≥20-run gate that retires this waiver reason.

**State:** rigor **holding** — the loop is closed and has now run once end-to-end. DoD writer confirmed (2 non-null `{dod_met,dod_waived,correction_rounds}` triplets vs 0 of 130+ before). Judge–human agreement 93.3% (≥80%). One real recurrence (thin commands, count 5) surfaced and proposed; two watch-list classes logged. No manufactured work.
