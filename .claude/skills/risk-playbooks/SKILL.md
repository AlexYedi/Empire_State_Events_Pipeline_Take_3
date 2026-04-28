---
name: risk-playbooks
description: Use when identifying launch risks, mitigation plans, and escalation owners.
---

# Risk Playbooks

Help the user surface launch risks honestly, write mitigation plans that will actually execute under pressure, and install escalation paths before launch week — drawing from Google's SRE book, Atlassian's Incident Management handbook, Charity Majors on observability, John Allspaw on operational readiness, and Jez Humble on release engineering.

## How to Help

When the user asks for help with launch risk:

1. **Pre-mortem before post-mortem** — before any launch, force the user to write down what could go wrong. "Imagine it's two weeks after launch and this failed. Why did it fail?" This surfaces risks that a forward-looking plan misses.
2. **Separate likelihood from impact** — risks are cheap to list and expensive to mitigate. Score each on both axes; only the top-right quadrant needs a full playbook. The rest gets an acknowledgement.
3. **Assign a human to every risk** — a risk with no named owner is a risk with no mitigation. Force the user to name someone for each red-cell risk, with backup contact.
4. **Define the trigger before you need it** — "we'll roll back if things go wrong" is not a plan. The trigger must be a specific metric, threshold, and observation window, named up front.
5. **Rehearse the rollback** — the one who writes the rollback and the one who executes it under pressure should not be the same person meeting the plan for the first time. Dry-run at least once.

## Core Principles

### Every launch has a pre-mortem
Gary Klein / popularized in Atlassian's incident management handbook: explicitly imagine the failure state before the launch happens. Have the team write down what could have caused it. This surfaces risks that forward-looking planning misses, because pre-mortems invert the cognitive bias — people are more honest about failure they're imagining than failure they're denying.

### Risk categories are coverage, not taxonomy
SRE / launch-review practice: the five categories (Product & Reliability, Go-to-Market, Compliance & Legal, Support & Success, External Factors) exist to make sure no class of risk is forgotten, not to neatly file each risk. A single risk may sit in two categories. The test is coverage, not categorization.

### Score likelihood × impact, act only on the top-right
John Allspaw on operational safety: you cannot mitigate every risk. Score each risk 1–3 on likelihood and 1–3 on impact. Cells ≥ 6 get a full playbook; cells 4–5 get a named owner and a one-line mitigation; cells ≤ 3 are acknowledged and logged. This is the only sustainable rhythm.

### Named owners, not functional owners
Atlassian incident management: "Engineering" is not an owner. "Maya Chen, backup: Priya Patel" is an owner. Functional ownership evaporates under pressure; named ownership persists. Every red-cell risk gets a primary and a backup, both with direct contact info.

### Triggers are observable, specific, and pre-agreed
Charity Majors / observability-driven release: "error rate > 2% sustained over 5 minutes on the checkout path" is a trigger. "Things seem bad" is not. The trigger must be a metric, a threshold, a window, and an observation source, all pre-agreed and wired to an alert. Without pre-agreed triggers, launch-week escalation turns into debate.

### Rollback is a feature, not a fallback
Jez Humble / Continuous Delivery: rollback capability is part of the product, not a safety net bolted on at the end. If you can't roll back in under 15 minutes, you don't have a launch plan — you have a hope. Feature flags, data migration reversibility, and cached prior-version artifacts are the engineering prerequisites.

### Support is the first detector
Zendesk / Intercom launch-ops patterns: support sees production failures before dashboards do, because users report experience before instrumentation catches it. Support must be briefed, staffed, and given an escalation path *before* launch. A launch-day support queue without an engineering escalation owner is a launch that will fail silently.

### Severity is a decision, not a description
Google SRE handbook: severity levels (Sev-1 through Sev-4) are pre-agreed decision points that unlock specific responses — war-room, exec page, public comms, customer notification. They are not vague descriptors. The response plan is attached to the severity label, so the label triggers the plan automatically.

### Post-launch retros feed the next launch's playbook
Spotify / Shopify launch-ops: every launch ends with a retro that updates the playbook. What risks surfaced? What triggers fired? What mitigations worked? What got missed? Without this feedback loop, risk playbooks become museum pieces; with it, they become sharper every launch.

## Risk Register Template

| Risk | Category | Likelihood (1-3) | Impact (1-3) | Score | Owner (primary / backup) | Trigger | Mitigation | Rollback | Status |
|------|----------|------------------|--------------|-------|--------------------------|---------|------------|----------|--------|
| e.g., auth service degrades under launch-day load | Product & Reliability | 2 | 3 | 6 | M. Chen / P. Patel | p95 login latency > 3s for 5min | Pre-scale + circuit breaker | Feature flag → prior auth | open |

**Score bands:**
- **7–9 (red):** full playbook required — trigger, mitigation, rollback, named owner, rehearsal.
- **4–6 (yellow):** one-line mitigation + named owner, logged in register.
- **1–3 (green):** acknowledged in register, no action required pre-launch.

## Severity Reference

| Sev | Meaning | Response |
|-----|---------|----------|
| **Sev-1** | Customer-facing outage, data loss risk, or security incident | War-room within 15 min, exec page, hourly comms until resolved |
| **Sev-2** | Material degradation for significant cohort; workaround exists | War-room within 1 hour, PM + EM paged, daily comms |
| **Sev-3** | Limited impact or edge case; no workaround needed | Ticket, owner assigned, standard queue |
| **Sev-4** | Cosmetic / internal-only | Backlog, next sprint |

## Questions to Help Users

- "If we were two weeks past launch and this failed, what would the failure report say?"
- "For each risk, what's the likelihood (1-3) and the impact (1-3)?"
- "Who — by name, not function — owns this risk if it fires?"
- "What exact metric, threshold, and window would tell you the risk has fired?"
- "Can you roll this back in under 15 minutes? If not, what's missing?"
- "Who on support is briefed on this launch, and what's their escalation path into engineering?"
- "What severity would you declare if this went wrong, and what response does that unlock?"
- "Where does what-we-learned live, so the next launch has a better playbook?"

## Common Mistakes to Flag

- **Skipping the pre-mortem** — only listing forward-looking risks. People are more honest about failure they're imagining than failure they're denying.
- **Functional ownership** — "Engineering owns this" is not an owner. A name and a backup name, with contact info, is an owner.
- **Vague triggers** — "if things look bad, we'll roll back" is not a plan. Metric, threshold, window, alert source, pre-agreed.
- **No rollback** — treating rollback as optional. If you can't revert in under 15 minutes, reconsider the launch scope.
- **Over-registering** — writing playbooks for every risk. Only red-cell risks warrant full playbooks; yellow is a line, green is acknowledged.
- **Support as an afterthought** — launching without briefing + staffing support, and without an engineering escalation path from the support queue.
- **Severity without a response plan** — calling something "Sev-1" without a pre-agreed action (war-room, page, comms cadence) attached.
- **No retro feedback into the next playbook** — the playbook goes stale without a post-launch update loop.

## Deep Dive

For extended sourcing (Google SRE book chapters on incident response and release engineering, Atlassian's Incident Management handbook, Charity Majors' observability-first release essays, John Allspaw on operational readiness, Jez Humble on Continuous Delivery rollback patterns, Klein on pre-mortems), see `references/guest-insights.md`.

Note: unlike other product specialists in this library, risk-playbooks is synthesized from published operations and incident-management practice rather than a single interview series. Treat the Core Principles section as the authoritative summary; the Deep Dive is extended sourcing.

## Related Skills

- `launch-tiering` — tier determines how much risk planning is warranted. Tier 0 gets a one-liner; Tier 2+ gets a full register + rehearsed rollback.
- `shipping-products` — shipping velocity is constrained by rollback readiness. Pre-rollback discipline unlocks faster shipping, not the reverse.
- `systems-thinking` — risk categories intensify per horizon. A Product & Reliability risk at H1 is "works on my laptop"; at H3 it's "five nines with documented failover."
- `ai-product-strategy` — AI products add non-determinism risk. Eval regressions and behavior drift are risk categories that don't exist for deterministic products.
