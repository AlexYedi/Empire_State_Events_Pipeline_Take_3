# Value-Action Registry (the strict value-action contract)

Every metric in the build-rigor + measurement layer, with its `{threshold → action → surface}`. **No orphan metrics:** if a metric can't name the action it triggers, it isn't collected (PRD US-8 / Linear YED-94). This is the governance capstone — review it whenever a metric is added or changed. Owner of every action at crawl = Alex (HITL).

| Metric | Source | Threshold | Action | Surface |
|---|---|---|---|---|
| build-quality judge score | US-3 judge | < 0.70 | flag artifact for rework before "done" | in-session (judge verdict / DoD) |
| judge–human agreement | US-3 calibration (`alex_ack`) | < 80% | judge stays **advisory**; tighten rubric, don't trust the score | weekly review |
| judge last-ran | US-1 DoD meta-item | > N hrs on a build | DoD item FAILS (anti-silent-rot) | in-session DoD boundary |
| DoD waiver-rate on builds | US-1 waiver log | climbing wk/wk | revisit the scope test / enforcement | weekly review |
| corrective-rounds ÷ acted-on value | US-2 `user_prompts` + US-5 | up 2+ consecutive wks | find where the agent keeps missing; tighten the skill/rubric | weekly review |
| correction-recurrence (same class) | US-7 recurrence log | ≥ N across builds | system **proposes** a codified fix (rubric/DoD/skill/few-shot) → Alex approves | weekly review |
| acted-on outcome vs goal | US-4 + US-5 | trending down | kill / retune the build or the distribution play | Hub dashboard + weekly |
| owned-asset engagement | US-5 / US-6 | below goal target | revise the asset / distribution strategy | Hub dashboard + weekly |
| telemetry ingestion health | US-2 hook | 0 `build_session` events / 48h on active days | investigate hook/exporter (observability-of-observability) | weekly / PostHog alert (US-6) |

## Rules
- **Adding a metric?** It does not ship without a row here (threshold + action + surface). Can't fill the row ⇒ don't collect the metric.
- **Surfaces are capped at three** — *in-session DoD boundary · Hub dashboard · weekly review*. Don't add a 4th; route new metrics to one of these (extra surfaces = noise nobody acts on).
- **Actions stay HITL at crawl.** Automating any action is a deliberate, separate decision (not a default).
- **Thresholds are starting values.** `N` / "2+ wks" / "< 0.70" are seeds — tune them in the weekly review as real data accrues, and record the change here (this doc is versioned in git; never silently re-tune).
