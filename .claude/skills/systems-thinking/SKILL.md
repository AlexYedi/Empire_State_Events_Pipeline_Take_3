---
name: systems-thinking
description: Help users think in systems and understand complex dynamics. Use when someone is dealing with multi-stakeholder problems, trying to understand second-order effects, managing platform ecosystems, or analyzing complex organizational dynamics.
---

# Systems Thinking

Help the user apply systems thinking to complex problems using frameworks and insights from 6 product leaders.

## How to Help

When the user asks for help with systems thinking:

1. **Map the system** - Help them identify all players, their incentives, and how they interact with each other
2. **Identify stocks and flows** - Understand what accumulates (stocks) and what moves between states (flows)
3. **Trace second-order effects** - Work through what happens after the first-order impact of any change
4. **Find leverage points** - Identify where small interventions can create large systemic changes

## Core Principles

### See the system
Seth Godin: "What does it mean to be a strategic thinker? It means to see the system." Understanding the invisible rules, culture, and interoperability that govern how products and organizations succeed or fail is the foundation of strategic thinking.

### Think about all players and incentives
Sriram: "Systems thinking. Think of all the players in the system, think of all of their incentives and how they interact with each other." This approach is superior to Jobs-to-be-Done for handling complex product trade-offs and multi-agent incentives.

### Use stocks and flows
Will Larson: "Systems thinking is basically you try to think about stocks and flows. Stocks are things that accumulate and flows are the movement from a stock to another thing." Model business processes like hiring pipelines or user funnels using this framework.

### Consider second, third, and fourth-order effects
Hari Srinivasan: "The skillsets that you think through and manage in a complicated ecosystem are quite different." Managing complex ecosystems requires understanding effects that cascade beyond the immediate impact.

### Think beyond today's decisions
Nickey Skarstad: "Second order thinking is you being able to think beyond the decisions that you're making today." Consider how current decisions impact future constraints and ecosystem dynamics.

### Automate recurring pains
Melissa Perri + Denise Tilles: "Tell me about some process you really hated and ended up trying to automate or build a system around to make it better." Identify recurring manual pains and build automated systems or frameworks to solve them.

## Three-Horizon Iteration Framework

*Alex-specific amendment to the upstream skill. Use to frame every build across MVP → Scaling → Enterprise-Prod horizons so polish decisions are explicit per iteration and future states are deliberately deferred, not accidentally forgotten.*

Every product — portfolio projects, pipeline tooling, hypothetical SaaS — benefits from being scoped against three horizons simultaneously. The horizons aren't sequential phases you'll definitely reach; they're lenses. Most builds land at H1 permanently. A few graduate to H2. Very few need H3. But *thinking* about all three at intake forces honest trade-off decisions and prevents the worst failure modes: over-engineering at H1, under-building at H2 when scale hits, never shipping because H3 polish was mistaken for minimum viable.

### Horizon 1 — MVP

The smallest thing that proves the core loop works. "Would a user use / pay for / recommend this?" level.

**Characteristics:**
- Single-user or tight-loop testing (N=1 is acceptable)
- Manual fallbacks acceptable
- Hardcoded values acceptable
- One happy path, happy-path-only error handling
- Deployed somewhere a link can be shared (Replit / Vercel preview)
- Documented in a README, not a KB

**Polish bar:** works, not beautiful. Any UX friction you notice personally, fix. Anything you don't notice, ship.

### Horizon 2 — Scaling

What breaks when usage goes from 1 to 50 to 500. The "a bunch of people like this and are using it" stage.

**Characteristics:**
- Rate limits, caching, pagination mandatory
- DB indexes on hot paths
- Structured logging + error tracking (Sentry or equivalent)
- Retry logic with exponential backoff on external calls
- Auth with real session management, not just magic links
- Multi-user data isolation
- Onboarding flow that doesn't require hand-holding
- Feature flags for risky launches
- CI that runs tests on every PR

**Polish bar:** reliable + debuggable. UX friction that 5%+ of users hit, fix. Edge cases shared by <1%, log and defer.

### Horizon 3 — Enterprise-Prod

The bar required for a paying enterprise customer to deploy this into production. The "would this survive a security review" stage.

**Characteristics:**
- SOC2 Type I posture minimum
- SSO / SAML auth (not just email/password)
- RBAC with audit logs
- Data residency options
- Tenancy isolation (logical or physical)
- Observability: metrics, traces, alerts, runbooks for common failures
- SLA defined with error budgets
- Incident response process + postmortem template
- Vendor risk artifacts (DPA, security questionnaire ready)
- Pen-test readiness
- Full documentation: API docs, admin guides, end-user guides
- Dedicated support channel

**Polish bar:** mandatory everywhere. Every surface is a potential enterprise deal-breaker.

### Trade-off matrix

For every feature/build decision, ask: which horizon am I solving for right now?

| Decision | H1 default | H2 default | H3 default |
|----------|------------|------------|------------|
| Error handling | Happy path only | Retry + log + user-visible error | Retry + log + alert + runbook entry |
| Auth | Magic link / email-only | Session-based + password reset | SSO / SAML + RBAC |
| Observability | Console logs | Sentry + basic dashboards | Full metrics/traces/alerts + incident runbooks |
| Documentation | README | README + API docs | + admin guide + end-user guide + runbooks |
| Data model | Permissive | Migrations + backfills tested | + RLS + audit log + soft deletes |
| Performance | "Fast enough on my laptop" | p95 budgets defined + monitored | SLA-backed + capacity planning |
| Testing | Smoke test by hand | CI + critical path automation | + load tests + chaos testing |
| Security | No secrets in repo | + secrets manager + dependency scanning | + pen test + SOC2 audit + bug bounty |

Use this table to make polish decisions explicit, not implicit. "Skipping CI at H1 is fine — it becomes mandatory at H2 trigger."

### Deferred Items table (part of the Future-State Register)

Every build that ships at H1 or H2 gets a **Deferred Items** table written to the Notion Project Ideas DB row's page body as part of that project's Future-State Register (see `head-of-product-engineering/SKILL.md` for the full Register schema). Three columns:

| Deferred Item | Trigger to Address | Effort Estimate |
|---------------|--------------------|-----------------|
| SSO auth | First enterprise inbound | 2-3 days |
| Rate limiting | >10 concurrent users | 4 hours |
| Audit log | SOC2 evidence gathering | 1 week |

This makes deferrals explicit and revisitable. At each horizon transition, the table becomes the work backlog for that horizon. Reviewed at every `head-of-product-engineering` invocation for the same product.

### How this threads into other skills

- **`shipping-products`** — the "ship to learn, then polish" principle applies *within a horizon*, not across them. Don't use it as a reason to never reach H2.
- **`prioritizing-roadmap`** — when comparing builds, horizon tier is part of the comparison. A Tier-0 launch for an H1 tool ≠ Tier-1 launch for an H2 product.
- **`launch-tiering`** — launch tier should correspond to product horizon. Most H1 work warrants Tier-0 launch effort. Tier-2+ launches imply H2 or H3 product readiness.
- **`ai-product-strategy`** — the "build for the slope, not the snapshot" principle applies across horizons. H1 model choice should be replaceable at H2.
- **`risk-playbooks`** — risk categories intensify per horizon. A Product & Reliability risk at H1 is "it works on my laptop"; at H3 it's "five nines with documented failover."

## Questions to Help Users

- "Who are all the players in this system, and what does each one want?"
- "If you make this change, what happens next? And then what happens after that?"
- "What accumulates over time in this system (the stocks), and what flows between states?"
- "Where are the feedback loops - both reinforcing and balancing?"
- "What constraint, if removed, would unlock the most value in this system?"
- "What recurring manual pain could be systematized?"

## Common Mistakes to Flag

- **Only seeing first-order effects** - Changes ripple through systems in ways that aren't immediately obvious
- **Ignoring incentives** - Every player in a system responds to their own incentives, not yours
- **Optimizing locally** - Improving one part of a system can make the whole system worse
- **Missing feedback loops** - Many systems have self-reinforcing or self-balancing dynamics that amplify or dampen changes
- **Treating symptoms instead of causes** - Systems problems often require addressing root causes, not visible symptoms

## Deep Dive

For all 6 insights from 6 guests, see `references/guest-insights.md`

## Related Skills

- Defining Product Vision
- Prioritizing Roadmap
- Shipping Products
- Launch Tiering
- Risk Playbooks
- AI Product Strategy
