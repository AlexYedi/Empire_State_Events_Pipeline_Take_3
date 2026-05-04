---
name: systems-thinking
description: Help users think in systems and understand complex dynamics. Use when someone is dealing with multi-stakeholder problems, trying to understand second-order effects, managing platform ecosystems, analyzing complex organizational dynamics, diagnosing chronic issues, or making decisions where leverage matters.
---

# Systems Thinking

Help the user apply systems thinking to complex problems using the canonical frameworks distilled from Donella Meadows' *Thinking in Systems: A Primer* (2008), the upstream guest insights from Alex's product-leader podcast set, and Alex's own H1/H2/H3 horizon framework. Together these give a working toolkit for diagnosing, intervening in, and living alongside complex systems.

## When to use this skill

- Multi-stakeholder problems where each actor's incentives matter.
- Chronic issues where the obvious fix keeps not working.
- Decisions where leverage matters — picking *where* to push, not just *what* to push.
- Roadmap or prioritization choices that need second-order-effects analysis.
- Organizational dynamics, team velocity, content systems, GTM motions.
- Architecture and system-design decisions with long-lived consequences.
- Any "why does this keep happening?" or "we've tried everything" situation.

## How to help — the eight-phase analysis

Don't jump to interventions. Walk through the diagnosis.

1. **Bound the system** — what's in, what's out, who decided.
2. **Map stocks and flows** — what's accumulating, what's moving.
3. **Identify feedback loops** — R loops, B loops, where the delays are.
4. **Test for archetype shape** — match against the 8 named patterns.
5. **Locate players and their incentives** — bounded rationality applies to all of them.
6. **Find the highest workable leverage point** — on the 12-point hierarchy.
7. **Test second-order effects** — what breaks if we push?
8. **Check posture** — am I dancing with this system, or trying to control it?

Each phase has a working question bank in `references/diagnostic-questions.md`. When time is short, run phases 1, 2, 3, and 4 — that's usually enough to reframe the problem.

## Core principles (the foundation)

### See the system, not just the elements
Meadows: a system has elements (visible), interconnections (often informational), and a function or purpose (least obvious, most determinative). Most decisions get made at the elements layer where leverage is lowest. Watch for the rules and the goal underneath the rules.

### Stocks and flows
A stock is what accumulates. A flow is what changes it. The bathtub equation: stock(t) = stock(t-dt) + (inflow − outflow) × dt. **A stock can be raised by increasing inflows OR decreasing outflows.** Most "growth" plans focus only on inflow.

### Feedback loops
Two kinds, only two:
- **Balancing (B):** goal-seeking, stability-restoring. The system's self-correction.
- **Reinforcing (R):** self-amplifying. Exponential growth or collapse.
Most chronic system pain is a reinforcing loop running unchecked, or a balancing loop that's been stripped of redundancy.

### Bounded rationality
Each actor in a system makes "rational" decisions inside their limited view. The decisions aggregate to outcomes nobody wanted. Don't assume malice when bounded rationality explains it.

### Second-order effects
After the first-order impact comes the system's response, then the actors' adaptation. Pre-mortem: imagine the intervention failed spectacularly; what went wrong? The answer is usually a second-order effect.

### Find leverage points; check direction
Some places to push are 100x more effective than others. People often locate them correctly and push them in the wrong direction. The full hierarchy lives in `references/leverage-points.md`.

### Beware the eight system traps
Most chronic systemic problems are one of eight named patterns: Policy Resistance, Tragedy of the Commons, Drift to Low Performance, Escalation, Success to the Successful, Shifting the Burden, Rule Beating, Seeking the Wrong Goal. Each has a known way out. Catalog in `references/system-archetypes.md`.

### Manage for resilience, self-organization, and hierarchy
Healthy systems have all three. Productivity-only optimization erodes them by default. See `references/system-properties.md`.

### Dance, don't control
Self-organizing nonlinear feedback systems are inherently unpredictable. The discipline is to dance with them: get the beat, expose mental models, honor information, design for feedback, listen for system wisdom, stay humble. See `references/dancing-with-systems.md`.

### Upstream guest principles (preserved from prior version)

These six insights from product-leader interviews are still useful as concrete handles on Meadows' abstractions:

- **Seth Godin:** "What does it mean to be a strategic thinker? It means to see the system." The invisible rules, culture, and interoperability that govern how products and organizations succeed or fail.
- **Sriram:** "Think of all the players in the system, think of all of their incentives and how they interact with each other." Strong handle on Meadows' bounded rationality.
- **Will Larson:** "Stocks are things that accumulate and flows are the movement from a stock to another thing." Hands-on application to hiring pipelines and user funnels.
- **Hari Srinivasan:** Managing complex ecosystems requires understanding effects that cascade beyond immediate impact.
- **Nickey Skarstad:** "Second order thinking is you being able to think beyond the decisions that you're making today."
- **Melissa Perri + Denise Tilles:** Identify recurring manual pains and build systems around them.

Full versions in `references/guest-insights.md`.

## Three-Horizon Iteration Framework

*Alex-specific amendment. Use to frame every build across MVP → Scaling → Enterprise-Prod horizons so polish decisions are explicit per iteration and future states are deliberately deferred, not accidentally forgotten.*

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

### Horizons mapped to Meadows' framework

The three horizons aren't just polish levels; they correspond to which system properties (`references/system-properties.md`) are being managed for:

- **H1 — manage for evidence.** The dominant question is: does the core loop produce value? Resilience, self-organization, and hierarchy are mostly nice-to-have at H1; the productive loop has to exist before it can be made resilient.
- **H2 — manage for resilience.** Multiple users, multi-region, varying load. Now the system needs balancing loops that can absorb shocks. Most of the H2 features in the matrix above are resilience investments.
- **H3 — manage for resilience + self-organization + hierarchy.** Audit logs, tenancy isolation, RBAC, SOC2 — these aren't just compliance. They're the substrate that lets the system operate at scale across many sub-systems (customer orgs) that need to be largely self-managing under thin coordination.

This is why H3 work feels qualitatively different from H2. It's not "more H2"; it's a different set of systemic properties being engineered for.

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

## Reference files

| File | When to use |
|---|---|
| [meadows-thinking-in-systems.md](references/meadows-thinking-in-systems.md) | Source distillation; how Meadows defines a system; bibliography |
| [feedback-loops-stocks-flows.md](references/feedback-loops-stocks-flows.md) | Foundational vocabulary; CLD notation; worked examples |
| [leverage-points.md](references/leverage-points.md) | The 12 leverage points with descriptions, examples, and software analogs |
| [system-archetypes.md](references/system-archetypes.md) | The 8 traps with trap/escape patterns |
| [system-properties.md](references/system-properties.md) | Resilience, self-organization, hierarchy as design qualities |
| [dancing-with-systems.md](references/dancing-with-systems.md) | The 15 practitioner-conduct guidelines |
| [diagnostic-questions.md](references/diagnostic-questions.md) | Question bank organized by analysis phase |
| [applications-to-software-and-product.md](references/applications-to-software-and-product.md) | Translation to software architecture, product, GTM, AI products, content systems |
| [guest-insights.md](references/guest-insights.md) | Original 6-guest podcast insights (preserved from prior version) |

## Common mistakes to flag

- **Jumping to intervention before diagnosis.** Run the eight phases first.
- **Pushing on the right leverage point in the wrong direction.** Always ask: am I sure this push moves the system the way I think it does?
- **Treating elements as the leverage point** when rules, goals, or paradigms are the actual lever.
- **Stripping out balancing loops because they "look like overhead."** Most resilience erosion is a sequence of these.
- **Mistaking stability for resilience.** A system that has never been disturbed isn't necessarily resilient; it might just be untested brittleness.
- **Optimizing parts at the expense of the whole.** Local optima are the most common cause of system-level failure.
- **Setting goals that drift with performance.** "Drift to Low Performance" is the silent killer of cultures and codebases.
- **Defining metrics that can be gamed.** Rule Beating + Seeking the Wrong Goal compound; check every KPI for "what would a malicious actor do to win this number?"

## Related skills (in this harness)

| Skill | Connection |
|---|---|
| `defining-product-vision` | Vision is a paradigm-level intervention (leverage point #2) |
| `prioritizing-roadmap` | Roadmap items distributed across leverage points |
| `risk-playbooks` | System traps are a risk taxonomy |
| `shipping-products` | Info flows + feedback policies (`dancing-with-systems` guidelines 3, 6) |
| `launch-tiering` | Second-order effects per launch tier |
| `head-of-product-engineering` | End-to-end orchestration uses the full systems lens |
| `writing-north-star-metrics` | Goodhart's Law / Seeking the Wrong Goal trap |
| `ai-product-strategy` | Bounded rationality of LLMs; feedback loops in AI systems |
| `conducting-user-interviews` | Listening for system structure, not just symptoms |
| `simplify` | Removing accidental complexity vs. essential complexity |

## Related skills (plugin / cross-harness)

| Skill | Connection |
|---|---|
| `engineering:architecture`, `engineering:system-design` | Software architecture as stock-and-flow structure (#10) |
| `engineering:tech-debt` | Tech debt as reinforcing loop (#7) |
| `engineering:incident-response` | Postmortem reveals dominant feedback structure |
| `engineering:debug` | "Debug the system, not just the bug" |
| `anthropic-skills:cto-architect` | Principal-level systems decisions |
| `product-management:metrics-review` | Detecting Drift to Low Performance + Goodhart |
| `product-management:write-spec` | Bounding the system, naming the loops, identifying the goal |
| `marketing-autoresearch` | Selection mechanism in self-organizing content systems |
