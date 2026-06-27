---
description: "The weekly ≤10-min rigor review (manual learning loop): review the week's build sessions, judge scores, DoD waivers, and outcomes against the value-action registry; spot recurring corrections; propose→approve a codified fix so feedback becomes durable improvement. HITL, not automation."
argument-hint: "[optional: window, e.g. 'last 2 weeks']"
---

# /rigor-review — Weekly rigor review

Run the **rigor-review** methodology. Methodology: `.claude/skills/rigor-review/SKILL.md`.

## Trigger
Weekly, or when Alex types `/rigor-review`, says "rigor review", "did the system learn this week". Natural alongside `/weekly-recap`.

## Shape (single-thread, HITL, ≤10 min)
1. **Pull** the week's signals — `build-sessions.jsonl`, `.claude/evals/logs/*`, the DoD waiver log, this week's `/tag-outcome` results.
2. **Review against the registry** (`value-action-registry.md`) — judge scores <0.70, corrective-rounds trend, waiver-rate, judge–human agreement, outcome-vs-goal trend. Take the named action for any threshold crossed.
3. **Correction-recurrence** — same-class corrections across builds; ≥ threshold ⇒ **propose** a codified fix (rubric/DoD/skill/few-shot). **STOP for approval.**
4. **Apply (on approval, versioned) + log** to `.claude/evals/correction-recurrence.md`; record any threshold tuning back in the registry.

## Guardrails
- ≤10 min; review only action-triggering metrics. **Propose → approve; never auto-apply.** No fabricated data (missing ⇒ say so).

## Ground truth
- Methodology: `.claude/skills/rigor-review/SKILL.md` · metrics+actions: `.claude/references/value-action-registry.md` · log: `.claude/evals/correction-recurrence.md`
