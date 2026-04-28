---
name: launch-tiering
description: Use when sizing go-to-market launches by impact, resources, and governance needs.
---

# Launch Tiering

Help the user size every launch honestly — matching investment to impact — using a tiered framework drawn from published launch-ops practice at Asana, Figma, HubSpot, Atlassian, and Reforge.

## How to Help

When the user asks for help with launch tiering:

1. **Lead with the outcome, not the feature** — ask what business outcome this launch is meant to produce (ARR, activation lift, competitive response, category framing). The outcome sets the tier; the feature is the artifact.
2. **Anchor against a tier definition up front** — propose a tier (0/1/2/3) before listing workstreams. Force the user to agree or counter the tier *first*, so the rest of the plan aligns.
3. **Scope the workstreams to the tier** — higher tiers add channels, approvals, and instrumentation. Lower tiers strip them. Never build a Tier-2 plan for a Tier-0 feature.
4. **Write the tier down** — launch tier belongs in the PRD and the launch brief. A tier decided in a hallway is a tier that will get re-litigated twice.

## Core Principles

### Most launches are Tier 0 — and that's fine
Reforge / Lenny Rachitsky public launch frameworks: the median feature ships with a changelog entry, an in-app nudge, and nothing else. The scarce resource isn't the feature — it's the attention your audience can give a launch. Spending Tier-2 effort on a Tier-0 feature dilutes the signal when a real Tier-2 lands. Default to Tier 0 unless there's explicit evidence otherwise.

### Tier is set by impact, not effort
Asana's internal launch-tier guidance (public talks): the tier corresponds to *expected impact* — ARR, audience reach, strategic positioning — not to how much engineering effort went in. A two-day build that opens an enterprise account is Tier 2. A six-month refactor invisible to users is Tier 0. Engineers conflate these; PMs resist the conflation.

### Name the tier before planning the workstreams
Atlassian launch playbook: declaring the tier first is a forcing function. It surfaces disagreement about impact *before* the team invests in collateral, creative, PR outreach, and comms sequencing that might be wrong-sized. Re-tiering a plan after the fact wastes all of it.

### The launch tier should match the product horizon
Horizon (from `systems-thinking`) and launch tier travel together. An H1 MVP almost always warrants a Tier 0 launch — the product isn't ready to absorb attention. H2 products unlock Tier 1–2. H3 enterprise-grade products can support Tier 2–3. A Tier-2 launch for an H1 product creates expectations the product will fail to meet.

### Tier 1+ needs exec air cover
HubSpot / Figma launch practice: once a launch crosses into Tier 1 (paid channels, press, sales enablement), a single named executive sponsor is non-negotiable. They're the escalation owner, the message approver, and the public face if the launch underperforms. Launches without an exec sponsor above Tier 0 drift and miss dates.

### Instrument the launch before you run it
Reforge / Amplitude launch-measurement practice: every tier needs measurement, but the granularity scales. Tier 0 can be a weekly active usage check. Tier 1+ needs a live launch dashboard — adoption, activation, retention cohort at day 7/30, and one counter-metric (churn, support ticket rate, latency). If you can't measure the launch, you can't learn from it, and the next tier decision will be guess-work.

### Re-tier on new evidence, not on ego
SaaStr / Jason Lemkin: mid-launch re-tiering happens when the market signal changes — a competitor ships first, a customer commits to a larger deal, press interest materializes or evaporates. Re-tiering because someone wants a bigger launch is ego. Re-tiering because the world changed is discipline. Log the reason either way.

### Keep a launch log
Atlassian / Shopify launch-ops: every launch, regardless of tier, gets a one-page log entry: tier, outcome hypothesis, actual result, variance reason. After ~10 launches you have real tier benchmarks that beat any framework. The log is the only way to know if your tiering is calibrated or consistently off.

## Tier Reference

| Tier | Trigger | Typical investment | Governance |
|------|---------|--------------------|------------|
| **Tier 0** | Changelog-worthy. No revenue or positioning shift expected. | In-app nudge + changelog + (optional) tweet. Hours of GTM work. | PM owns. No exec sign-off. |
| **Tier 1** | Material adoption or retention lift expected. Single-channel campaign warranted. | Blog post + email + social + sales talking points. 1–2 weeks of GTM work. | PMM owns. Exec sponsor named. |
| **Tier 2** | New segment, pricing change, or competitive response. Multi-channel push. | Paid + press + webinar + sales enablement + partner comms. 4–8 weeks of GTM work. | Named exec sponsor. War-room for launch week. |
| **Tier 3** | Category-defining. Annual flagship. Analyst briefings. | All channels + press tour + keynote + analyst relations + customer event. Quarter+ of runway. | CEO/CPO sponsor. Board-visible. Formal launch committee. |

## Questions to Help Users

- "What outcome does this launch need to produce — revenue, positioning, adoption, retention?"
- "What's the smallest launch that would accomplish that outcome?"
- "Which product horizon is this at — H1, H2, or H3? Does the proposed tier match?"
- "Who is the executive sponsor if this is Tier 1+?"
- "What's the single most important metric for this launch, and what's your counter-metric?"
- "What would cause you to re-tier mid-flight, and who owns that call?"
- "Where does this launch get logged for future benchmarking?"

## Common Mistakes to Flag

- **Tier inflation** — treating every launch as Tier 2 because it feels important to the builder. The audience can't tell, and real Tier 2s lose signal.
- **Effort-based tiering** — "we spent six months on this, so it's Tier 3." Tier is impact, not effort.
- **Skipping the tier declaration** — planning workstreams before the tier is named produces over-built Tier 0s and under-built Tier 2s.
- **Tier-product mismatch** — Tier 2 launch wrapped around an H1 product sets expectations the product fails to meet.
- **No instrumentation** — launching without a measurement plan means every future launch is still a guess.
- **No launch log** — without a log of tier-vs-outcome, the framework is theater; it never calibrates to reality.
- **No exec sponsor at Tier 1+** — launches without air cover drift, miss dates, and lack a decision-maker when something goes wrong.

## Deep Dive

For extended sourcing (Asana's public launch-tiering talks, Reforge's launch-ops curriculum, Lenny Rachitsky's launch-tier newsletter entries, HubSpot's launch framework, Atlassian's launch handbook), see `references/guest-insights.md`.

Note: unlike other product specialists in this library, launch-tiering is synthesized from published practitioner frameworks rather than a single interview series. Treat the Core Principles section as the authoritative summary; the Deep Dive is extended sourcing.

## Related Skills

- `shipping-products` — shipping velocity within a tier; launch-tiering sizes the wrapper around what you ship.
- `systems-thinking` — product horizon (H1/H2/H3) drives which tiers are even available.
- `risk-playbooks` — tier determines the depth of risk planning. Tier 0 gets a line; Tier 2+ gets a register.
- `writing-north-star-metrics` — the launch metric is a downstream view of the NSM; tier defines how much instrumentation is warranted.
- `prioritizing-roadmap` — tier is one of the comparison dimensions when sequencing launches.
