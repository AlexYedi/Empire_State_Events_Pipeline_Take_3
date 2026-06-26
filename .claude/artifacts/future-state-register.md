# Future-State Register

This file tracks the current future-state for every product passed through the head-of-product-engineering orchestrator. One entry per project, updated in place each cycle. The `Prior cycles` trail is append-only.

---

## eval-harness — LLM-as-Judge Quality Harness for Event Pipeline Skills
- Slug: eval-harness
- Notion Project Ideas page: 348d3699-c2db-81b6-bf38-d4e360419c82
- Current cycle: 1
- Last updated: 2026-04-24
- Future-state: Alex ships edits to event-pipeline skills the way a surgeon closes a suture — with immediate, objective confirmation that the work held. Voice drift, shallow research, and rubric violations are caught the moment they appear, not weeks later on a LinkedIn post that didn't land. The documentarian angle compounds instead of eroding because every output that goes to Notion or LinkedIn has passed a machine-readable version of Alex's own taste.
- North-star metric: Skill regressions caught before production, per cycle (target H1: ≥1 real / 2-week cycle, Alex-ack'd)
- Horizon: MVP (H1)
- Prior cycles: cycle 1

### Deferred items

| Deferred Item | Trigger to Address | Effort Estimate |
|---|---|---|
| Rubrics for event-research, post-event-content, pattern-synthesis, project-ideation | H1 pilot survives 2 weeks of real use | 8h (2h × 4) |
| CI hook on PRs touching `.claude/skills/*` | 3+ skills have rubrics + manual adoption confirmed | 6h |
| Judge-human calibration loop / weekly review | Run-log accumulates ≥20 ack'd verdicts | 8h |
| Drift-over-time dashboard | CI ships + cross-cycle data exists | 12h |
| Multi-judge quorum for voice (R1 mitigation) | H2 stable 1 cycle OR agreement <80% | 16h |
| Rubric versioning + audit | First rubric breaking-change in production | 8h |
| Specialized judges per skill | H2 stable + ≥50 runs per skill | 20h+ |
| Pre-commit warning hook (R3 mitigation) | H1 ships — pull into H1 if adoption looks at risk | 1h |

### H2 escalation trigger
Tier-1 internal launch + portfolio explainer when: rubrics for 3+ skills AND CI ships.

### Rollback
2 cycles NSM=0 AND judge-human agreement <80% → rewrite rubric before H2.

---

## Empire State — Build-Rigor + Measurement/Eval/Observability Layer
- Slug: empire-state-build-rigor
- ChatPRD: 61bb864f-5e01-4247-a2cc-e963ad7e07f2
- Linear project: empire-state-build-rigor-and-measurement-layer-1795b16a8ba9 (Empire State initiative, team YED)
- Current cycle: 1
- Last updated: 2026-06-25
- Future-state: every build + published artifact carries immediate objective confirmation it held, plus a trended acted-on-value signal vs its assigned goal; rigor lives in the execution path, so the pipeline compounds instead of drifting.
- North-star metric: acted-on value (outcome vs assigned goal, trended)
- Horizon: MVP (crawl→walk)
- Prior cycles: cycle 1
- Coordinates with: eval-harness (Tier-2 judge sub-component) · Empire State Hub (viz + build-in-public)

### Deferred items
| Deferred Item | Trigger to Address | Effort Estimate |
|---|---|---|
| Automated propose→approve learning loop | manual ritual proves value over ~1 mo | 4h |
| Langfuse (self-host) | prompt-level debugging weekly OR PII review fails | — |
| Cross-judge quorum | judge agreement <80% OR contested artifacts | 4h |
| Promote DoD → agent-skills canonical | DoD changes behavior without drag (4–6 wks) | 1h |
| Deep beta OTEL traces | needs Anthropic allowlist | — |

### Rollback
2 cycles: waiver-rate high on builds AND no acted-on-outcome renders AND judge agreement <80% → stop; simplify or escalate to H3.
