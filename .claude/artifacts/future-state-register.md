# Future-State Register

This file tracks the current future-state for every product passed through the head-of-product-engineering orchestrator. One entry per project, updated in place each cycle. The `Prior cycles` trail is append-only.

---

## eval-harness — LLM-as-Judge Quality Harness for Event Pipeline Skills
- Slug: eval-harness
- Notion Project Ideas page: 348d3699-c2db-81b6-bf38-d4e360419c82
- Current cycle: 1
- Last updated: 2026-04-24
- Future-state: Alex ships edits to event-pipeline skills the way a surgeon closes a suture — with immediate, objective confirmation that the work held. Voice drift, shallow research, and rubric violations are caught the moment they appear, not weeks later on a LinkedIn post that didn't land. The documentarian angle compounds instead of eroding because every output that goes to Notion or LinkedIn has passed a machine-readable version of Alex's own taste.
- North-star metric: Skill regressions caught before production, per cycle (target H1: ≥1 real regression / 2-week cycle, Alex-ack'd as real)
- Horizon: MVP (H1)
- Prior cycles: cycle 1 (this cycle — see orchestration-log-eval-harness-cycle-1.md)

### Deferred items (Three-Horizon Future-State Register table)

| Deferred Item | Trigger to Address | Effort Estimate |
|---|---|---|
| Rubrics for event-research, post-event-content, pattern-synthesis, project-ideation (B9) | H1 pilot rubric (pre-event-content) survives 2 weeks of real use | 8h total (2h × 4 skills) |
| CI hook on PRs touching `.claude/skills/*` (B10) | 3+ skills have rubrics + manual harness adoption confirmed | 6h |
| Judge-human agreement calibration loop / weekly sample review (B11) | First cycle's run-log accumulates ≥20 ack'd verdicts | 8h |
| Drift-over-time dashboard (B12) | CI ships, run-log has cross-cycle data | 12h |
| Multi-judge quorum for voice (B13) — addresses R1 judge circularity | H2 stable for 1 cycle; or judge-human agreement drops below 80% | 16h |
| Rubric versioning + auditability (B14) | First rubric breaking-change in production | 8h |
| Specialized judges per skill (B15) | H2 stable + sufficient eval data per skill (target: ≥50 runs) | 20h+ |
| Pre-commit warning hook (B8a, addresses R3 adoption risk) | H1 ships — install simultaneously | 1h (pull into H1 if adoption looks at risk) |

### H2 escalation trigger (pre-committed in cycle 1)
Tier-1 internal launch + portfolio explainer write-up when: rubrics exist for 3+ skills AND CI integration ships.

### Rollback criteria (cycle 1 → no H2)
If after 2 cycles NSM = 0 real regressions caught AND judge-human agreement <80%: stop, rewrite rubric before H2. Don't propagate to other skills.
