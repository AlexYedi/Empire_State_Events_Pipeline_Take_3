# ADR-12 — Job-search loop V1, its known limits, and the triggers that open V2

**Status:** **Accepted 2026-10-11** (Alex: "yes" to the V1 + revisit-trigger approach).
**Governs:** how `/scan-roles` (role-radar, `ats_pull.py`, `comp_gate.py`) keeps its rules correct over time, and when each known shortfall gets a bigger fix.

## Context

A review on 2026-10-11 found four ways the loop can go wrong without anyone noticing:

1. **One rule, three copies.** Comp rules lived in `me-model.md` (gitignored), in `comp_gate.py` and in role-radar `SKILL.md`. The 2026-10-07 commission ruling (no split stated → top ÷ 0.75) was recorded in prose and never reached the script.
2. **Silent assumptions.** Ashby posts "$X – $Y • Offers Commission" with no base/OTE label. The gross-up reads the band as base and returned a clean PASS, with no sign that this was a guess.
3. **Tests only covered cases written by hand.** The selftests proved the code did what was intended. Nothing showed whether the scan was finding the right roles. Ramp's Customer Activation Manager family sat outside the keep-list unseen until it was found by accident.
4. **Nothing noticed a quiet loop.** A two-week gap with no scan and an empty Friday review log raised no flag.

The roadmap's guardrails (no new stores, hooks or dashboards; one-in-one-out) rule out a heavyweight fix. Most of these limits may never matter before the search ends. So each gets the smallest fix that works now (V1), plus a measurable trigger that says when the larger fix (V2) has earned its cost.

## Decision

**V1 ships now, inside existing files:**

| # | V1 (shipped 2026-10-11) |
|---|---|
| 1 | `comp_gate.py` is the only executable statement of the comp rules: a dated ruling ledger in its docstring, pinned by `--selftest`. `me-model.md` keeps the policy, the floor and the ruling dates. `SKILL.md` points to the script and no longer restates the arithmetic. A new ruling lands as a script change plus a selftest case in the same commit. |
| 2 | When the figure comes from grossing up a band that never says "base" or "salary", the rule reads "(band assumed base)" and the note adds an `ASSUMED … verify with the recruiter` line. The verdict is unchanged (the 2026-10-11 ruling stands). |
| 3 | The nine real Ramp Activation postings are now regression cases: the comp figures in `comp_gate.py --selftest`, the titles in `ats_pull.py --selftest`. Each scan also prints **unmatched titles** to stderr: in-location titles that sound commercial, that neither the keep-list nor the drop-list rules on, and that are not a known non-seller family. role-radar Step 4 lists the in-scope-looking ones as keep-list candidates for Alex to rule on. |
| 4 | The Friday review (Notion roadmap) gains one line: days since the last `/scan-roles`, applications this week, and "any ADR-12 trigger fired?" |

**V2 is built only when its trigger fires:**

| # | V2 | Trigger (any one) |
|---|---|---|
| 1 | Rules move to one config file that both the script and the docs read, plus a parity test that fails when they disagree. | A second ruling fails to reach the script. **Or** a second tool (e.g. `/interview-prep`) needs the comp rules. |
| 2 | A confidence field in the Roles DB. Assumed figures land in a REVIEW status instead of PASS. | A recruiter's real number differs from the computed figure by >10%. **Or** three `ASSUMED` roles reach `applied`. |
| 3 | A labelled set of real postings, with each scan measuring how many in-scope roles it found and how many out-of-scope ones it let through. | A second in-scope role is found outside the scan (as Ramp's was). **Or** the unmatched list stays over 50 on two scans in a row after the first backlog is ruled on. |
| 4 | An automatic nudge on a schedule. | Two Friday reviews in a row are skipped, meaning V1 is not being read. |

**Backstops:**
- At the 2026-10-31 widening checkpoint, review all four triggers whether or not any has fired.
- **Sunset:** an accepted offer retires the job-search loop. No V2 gets built after that.

## Consequences

- The first scan with V1 (2026-10-11) printed **96 unmatched titles**, over the 50 line. This is the first-run backlog, not yet a trigger. It also surfaced likely gaps in the keep-list:
  - "Director of Sales" (the keep-list matches "Sales Director" only)
  - "AI Success Manager"
  - "Enterprise AI adoption lead"
  - "Director, Global Enterprise Accounts"

  These are Alex's to rule on. Rulings go to `KEEP`, or into the `QUIET` non-seller list in `ats_pull.py`.
- The unmatched list is display only. It never changes which rows pass, and the passing set was diffed unchanged on the first run.
- Reversing any V1 piece, or building a V2 before its trigger fires, needs a new ADR or a dated line in this one.

## Status history

| Date | Status | Note |
|---|---|---|
| 2026-10-11 | Accepted | V1 shipped on branch `alex/job-search-mission-scaffold` with the Activation and stated-split rulings. |
