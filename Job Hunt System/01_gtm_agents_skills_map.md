# gtm-agents: Curated Skills & Agents Map for the Full-Stack GTM Job Hunt

**Companion to `00_full_stack_gtm_roadmap.md` (V1.1)**
**Source catalogs:** `docs/agent-reference.md` (203 agents) + `available_skills.xml` (243 skills) in `GitHub/gtm-agents`
**Date:** 2026-04-20

---

## How to read this doc

Alex's prompt was: *"consider the research, sales, marketing, product [and CS] skills and agents that could create expert execution throughout this and then to generate outputs."*

This is **not** a catalog. The gtm-agents repo has 203 agents and 243 skills — most of which you will never touch. This doc filters to the ~40 agents and ~55 skills that produce measurable leverage on four specific use cases:

1. **Coursework execution** (Part 1 Domains 1–9): learning by doing, not reading.
2. **Job-hunt funnel execution** (Part 2 Stages 1–8): turning the funnel into real output.
3. **Portfolio capstones** (Domain 3 + Stage 3 intersection): the nine-play catalog from the Clay blog, built for real.
4. **Post-hire ramp** (Day-1 through first 90): what the function actually does once you're in the seat.

**Two modes of use for every skill/agent below:**

- **Execute-with** — invoke the agent/skill via a slash command or subagent call to generate an output you ship (draft, brief, dashboard, sequence).
- **Internalize-as-credential** — the skill is itself the body of knowledge you're being hired for. Fluency *is* the signal. Don't just run the command; read the SKILL.md, understand the framework, be able to whiteboard it.

**A note on the two clones.** `GitHub/gtm-agents` and `Desktop/gtm-agents copy` are near-identical. Treat the `GitHub` clone as canonical. Any customization goes there so it's under version control.

---

## Part 0 — Mastery-proofs: the subset where fluency = the credential

These are the plugins where being able to *speak the framework fluently* in an interview is itself the hiring signal. You don't need to have used every skill — you need to be able to describe the shape, the sequence, the measurement plan, and the failure modes for the following:

| # | Plugin | Why this is a credential | Key skill files to internalize |
|---|--------|--------------------------|--------------------------------|
| 1 | **data-signal-enrichment** | The whole Clay thesis is "unify signals into a layer your sellers act on." This plugin *is* that layer. | `data-sourcing`, `firmographic-analysis`, `signal-scoring`, `suppression-logic` |
| 2 | **intent-signal-orchestration** | Rung 3 of the Clay maturity model ("activation"). Reverse-IP, buying-committee, outbound plays live here. | `signal-scoring`, `outbound-plays`, `suppression-logic` |
| 3 | **analytics-pipeline-orchestration** | Rung 1 of the Clay maturity model ("data foundation"). This is where most companies stumble. | `instrumentation`, `quality-gates`, `visualization-patterns` |
| 4 | **business-intelligence** | Semantic layer and data contracts — the GTME's strategic asset. | `data-contract-framework`, `metric-governance-kit`, `dashboard-playbook` |
| 5 | **revenue-analytics** | Exec briefing language. How you talk about pipeline in the CRO/CEO room. | `cohort-analysis`, `deal-quality-model`, `revenue-health-dashboard`, `exec-briefing-kit` |
| 6 | **growth-experiments** | Every build you ship must have a hypothesis and a measurement plan. Clay's "no measurement plan" = red flag. | `experiment-design-kit`, `hypothesis-library`, `guardrail-scorecard` |
| 7 | **enterprise-sales** | Your 12 years of credibility translate here. Interviewers test for MEDDPICC + command of value story. | `value-story-framework`, `cxo-briefing-kit`, `pursuit-governance`, `procurement-playbook`, `risk-register` |
| 8 | **sales-prospecting** | The bridge between GTM engineering and sales reality. Every play you build ends in an SDR's outbound queue. | `cold-outreach`, `lead-qualification`, `objection-handling`, `social-selling` |

**Rule of thumb:** if you can't whiteboard the framework from memory in 4 minutes, it's not a credential yet. Pull the SKILL.md, read it, translate the framework into your own language, and rehearse it out loud.

---

## Part 1 — Coursework execution map (Part 1 Domains 1–9)

For each domain, three columns: **what to execute with**, **what to internalize**, **output the domain should produce**.

### Domain 1 — Modern GTM Theory & Buyer Psychology

- **Execute-with:** `content-marketing:thought-leader` + `copywriting:copy-strategist` — generate short-form POVs as you study each framework (MEDDPICC, SPICED, Bowtie). Posting the POVs = reps.
- **Internalize:** `sales-enablement/skills/messaging-framework`, `product-marketing/skills/positioning`, `pricing-strategy/skills/pricing-architect` (Command of the Message vocabulary).
- **Output:** 1 POV per framework, posted. 1 "my own buyer journey model" artifact that explicitly shows Bowtie → Pre-sales / Activation / Expansion translation.

### Domain 2 — Sales Methodologies & Psychology

- **Execute-with:** `sales-calls:call-strategist` to pre-plan reps on whatever deals you still run at GKY (then mine transcripts). `sales-coaching:performance-coach` for post-call feedback to yourself.
- **Internalize:** `sales-calls/skills/meddic-checklist`, `sales-calls/skills/call-analysis-framework`, `sales-calls/skills/call-brief-framework`, `sales-coaching/skills/coaching-framework`, `sales-coaching/skills/reinforcement-drills`.
- **Output:** 3 call-review artifacts (your own calls), scored against MEDDPICC. These become interview stories ("I review every call against MEDDPICC, here's one where procurement was missing…").

### Domain 3 — GTM Engineering Craft (the credential domain)

This is the highest-leverage domain. It's also where the gtm-agents catalog is richest.

- **Execute-with (build with these):**
  - `/data-enrichment-master` — company dossiers, contact enrichment, provider orchestration. Use `enrichment-orchestrator` agent for any multi-provider lookup.
  - `/data-signal-enrichment` — normalize signals into a unified layer. `signal-integrator` agent is the GTME-in-miniature.
  - `/intent-signal-orchestration` — run a reverse-IP or an outbound play end-to-end. This builds literal portfolio pieces.
  - `/personalization-engine` — build a tiny profile schema + decision flow for one of your Empire State events ("VIP invite routing").
  - `/analytics-pipeline-orchestration` — design the event model for any build you ship.
- **Internalize:** All four agents in `data-enrichment-master` (company-analyst, contact-hunter, enrichment-orchestrator, quality-analyst) and all three in `data-signal-enrichment`. Know what each does and when to reach for it.
- **Output:** The 9-play portfolio cross-walk (see Part 3 of this doc). Minimum: 3 builds shipped with Loom + measurement plan.

### Domain 4 — Data & Analytics Fluency

- **Execute-with:** `analytics-pipeline-orchestration:analytics-data-strategist` agent (sonnet) to design the event model for each build. `analytics-pipeline-orchestration:analytics-modeling-lead` (haiku) to spec the tables. `business-intelligence:data-architecture-lead` (sonnet) for the semantic layer conversation.
- **Internalize:** `analytics-pipeline-orchestration/skills/instrumentation`, `analytics-pipeline-orchestration/skills/quality-gates`, `business-intelligence/skills/data-contract-framework`, `business-intelligence/skills/metric-governance-kit`.
- **Output:** One "semantic layer as strategic asset" explainer in your own words. One dashboard in Hex or Streamlit that pulls from a real dataset you built.

### Domain 5 — AI & Agent Systems Literacy

- **Execute-with:** Custom — this is where you actually *use* Claude Code, the Agent SDK, n8n, MCPs to ship things. Not heavy on gtm-agents invocations, because the gtm-agents catalog is itself the proof that you can *read and use* an agent system.
- **Internalize:** Read 10 of the orchestrator plugin agent definitions. Understand why `campaign-manager` is sonnet and `channel-coordinator` is haiku. That model-selection rationale *is* AI-system-literacy.
- **Output:** A short "why these plugins picked these models" writeup for your own portfolio. This demonstrates you can read an agent system, not just drive one.

### Domain 6 — Product & Technical Fluency

- **Execute-with:** `product-marketing:product-narrative-lead` (sonnet) + `product-marketing:launch-strategist` (sonnet) — use to position *your own builds* for the writeups.
- **Internalize:** `product-marketing/skills/positioning`, `product-marketing/skills/launch-plays`, `product-marketing/skills/competitive-intel`.
- **Output:** A 1-pager for each build that reads like a launch brief ("problem, audience, what ships, measurement, what's next"). This is how you translate your builds into product-marketer-readable language.

### Domain 7 — Modern Tooling Stack

- **Execute-with:** Cross-cut. `marketing-automation:journey-architect` for MAP thinking. `email-sequence-orchestration:email-architect` for lifecycle flows. `sales-prospecting:outreach-specialist` for sequence design.
- **Internalize:** `marketing-analytics/skills/attribution-playbook`, `marketing-analytics/skills/exec-dashboard-blueprint`, `email-sequence-orchestration/skills/cadence-design`, `email-sequence-orchestration/skills/qa-gates`.
- **Output:** Stack audit of the Empire State repo itself — what tools, what they replace, what they'd cost in a real org. This is an interview answer, not a deliverable to anyone else.

### Domain 8 — Deep Subject Matter on AI-Native Customer

- **Execute-with:** `market-research:insights-research-director` (opus) for structured ICP interviews. `voice-of-customer:customer-insights-lab-analyst` (opus) for synthesis. `customer-feedback-orchestration:research-lead` (sonnet) for the interview guide itself.
- **Internalize:** `market-research/skills/research-brief-blueprint`, `market-research/skills/insights-repository-kit`, `voice-of-customer/skills/customer-feedback-taxonomy`, `voice-of-customer/skills/signal-correlation-workbench`.
- **Output:** 3–5 recorded ICP conversations synthesized into a "what AI-native buyers actually want" artifact. This is rare and high-signal.

### Domain 9 — Execution Craft

- **Execute-with:** `sales-operations:capacity-planner` (haiku) — use to think about *your own* time allocation. Seriously. It will expose time-budget leaks.
- **Internalize:** `growth-experiments/skills/experiment-design-kit`, `growth-experiments/skills/guardrail-scorecard`, `growth-experiments/skills/hypothesis-library`. These three shape how you talk about every build.
- **Output:** One "Alex's operating rhythm" document. Weekly/monthly cadences, what gets measured, what gets pruned.

---

## Part 2 — Job-hunt funnel execution map (Part 2 Stages 1–8)

### Stage 1 — Market mapping & target list

- **Execute-with:**
  - `/data-enrichment-master:company-analyst` (sonnet) — build a dossier per tier-1 target (Intercom, Canva, Notion, Anthropic, Ramp, Verkada, Rippling, Clay). Firmographics, recent news, stack, hiring activity.
  - `/data-enrichment-master:contact-hunter` (haiku) — contact enrichment on the named operators already in V1.1 (DeMoulin, Jones at Canva, Peters, Iftikhar, Lee, Bleier at Notion, Wall, Sarrafzadeh, Grieco, Adelstein, Keith Jones at Clay, Rachel Hepworth).
  - `/market-research:quant-insights-architect` (opus) — build a small forced-choice survey on "what GTME role means at top AI-native cos" if you want original data.
- **Internalize:** `data-enrichment-master/skills/firmographic-analysis`, `abm-orchestration/skills/account-tiering`.
- **Output:** Named target table (already in V1.1), with live dossiers in Notion keyed to each row.

### Stage 2 — Positioning yourself as the candidate

- **Execute-with:** `product-marketing:product-narrative-lead` (sonnet) and `copywriting:copy-strategist` (sonnet) — treat *you* as the product. Ship two positioning variants (consultative-seller-who-built-it vs. enterprise-veteran-now-technical). A/B them in conversations.
- **Internalize:** `product-marketing/skills/positioning`, `sales-enablement/skills/messaging-framework`.
- **Output:** Headline + 150-word About + short elevator in two variants. Tested in 3 real conversations.

### Stage 3 — Signal generation (portfolio)

This is where the catalog pays the highest rent, because you're literally building the things you'll be hired for.

- **Execute-with:**
  - `/intent-signal-orchestration:automation-lead` (haiku) to scaffold the ingestion pipeline for a reverse-IP play.
  - `/intent-signal-orchestration:intent-analyst` (haiku) to score the signals.
  - `/sales-prospecting:outreach-specialist` (sonnet) to draft the sequence the play fires.
  - `/personalization-engine:personalization-architect` (sonnet) for the profile schema when the play needs one.
  - `/growth-experiments:experimentation-strategist` (sonnet) to ensure every build ships with a hypothesis + measurement plan.
- **Internalize:** `intent-signal-orchestration/skills/signal-scoring`, `intent-signal-orchestration/skills/outbound-plays`, `intent-signal-orchestration/skills/suppression-logic`.
- **Output:** Loom + writeup per build, following the V1.1 Stage 3 template (problem → ICP → data → play → measurement → what I'd do next). Minimum three.

### Stage 4 — Outbound / warm-intro generation

- **Execute-with:**
  - `/sales-prospecting:lead-researcher` (haiku) for pre-outreach research per target operator.
  - `/sales-prospecting:social-seller` (sonnet) for LinkedIn engagement sequencing.
  - `/sales-prospecting:outreach-specialist` (sonnet) for personalized outreach drafts.
  - `/copywriting:conversion-copywriter` (haiku) for subject-line and CTA variants.
- **Internalize:** `sales-prospecting/skills/cold-outreach`, `sales-prospecting/skills/social-selling`, `email-sequence-orchestration/skills/cadence-design`, `email-sequence-orchestration/skills/qa-gates`.
- **Output:** Per-operator message pairs (LinkedIn DM + email). Keep a small CRM (Notion or HubSpot) tracking sent / opened / replied. This is a measurable funnel.

### Stage 5 — Interview prep (process-side)

- **Execute-with:** `sales-calls:call-strategist` (sonnet) on every upcoming interview — objectives, discovery flow, multithreading plan.
- **Internalize:** `sales-calls/skills/call-brief-framework`, `sales-calls/skills/meddic-checklist`, `sales-calls/skills/persona-intel`.
- **Output:** A pre-call brief per interview, 1 page. Re-used across the loop.

### Stage 6 — Evaluation / assessments (Clay's three-part rubric)

This is the stage V1.1 rewrote around the Clay blog. The catalog supports it this way:

- **Execute-with:**
  - Assessment-task execution: `/data-enrichment-master:enrichment-orchestrator` (sonnet) + `/intent-signal-orchestration:automation-lead` (haiku) — the two agents you'd actually lean on for a mini-build in a Clay-style test.
  - Loom narration prep: `/sales-calls:call-strategist` (sonnet) to structure the four-beat narration ("here's what I was asked → here's how I interpreted it → here's what I built → here's how I'd measure").
- **Internalize:** `growth-experiments/skills/experiment-design-kit` (so the measurement answer is never hand-wavy), `marketing-analytics/skills/attribution-playbook` (so you can answer "how would you attribute this?"), `business-intelligence/skills/data-contract-framework` (so you can answer "how would you make this durable?").
- **Output:** Memorize Clay's four red flags cold (tunnel vision, single-channel thinking, deliverability blindness, no measurement plan). Memorize the three-rung model and have a sentence on each.

### Stage 7 — Offer, negotiation, close

- **Execute-with:** `pricing-strategy:pricing-architect` (sonnet) — weirdly apt. Use it to think about comp trade-offs (base vs. variable vs. equity vs. bonus vs. sign-on). Also `enterprise-sales:value-architect` (haiku) to build a "value I bring" narrative with actual numbers.
- **Internalize:** `enterprise-sales/skills/value-story-framework`, `enterprise-sales/skills/risk-register` (use the "risk to the employer if they don't hire me" frame).
- **Output:** A comp-scenario matrix, and a one-page case for your asking number.

### Stage 8 — Pre-start ramp

- **Execute-with:** `account-management:success-planner` (sonnet) — apply it to yourself. Your 30/60/90 is a joint success plan between you and your new manager.
- **Internalize:** `account-management/skills/success-planning-framework`, `customer-success/skills/executive-ebr-kit`.
- **Output:** A 30/60/90 draft before your start date that names the maturity rung (per V1.1 Stage 6 "top-1% move"), names the three plays you'd ship in the first 60 days, and names your measurement plan.

---

## Part 3 — Portfolio capstones: 9-play cross-walk

V1.1 Domain 3 listed nine Clay-style play patterns. Here's the agent/skill call-stack for each. Pick three that you'll actually ship — my recommendation is **inbound scoring**, **signal digest**, and **reverse-IP dynamic outreach**, because they cover all three rungs of the Clay model and are each demo-able in under 6 minutes of Loom.

| # | Play | Agents to execute with | Skills to internalize |
|---|------|------------------------|------------------------|
| 1 | Inbound lead scoring | `data-signal-enrichment:signal-integrator` → `intent-signal-orchestration:intent-analyst` → `sales-prospecting:qualification-expert` | `signal-scoring`, `lead-qualification`, `data-contract-framework` |
| 2 | Transcript → CRM auto-sync | `sales-calls:deal-analyst` → `analytics-pipeline-orchestration:analytics-modeling-lead` | `call-analysis-framework`, `crm-hygiene`, `instrumentation` |
| 3 | Buying-committee signal digest | `data-enrichment-master:enrichment-orchestrator` → `intent-signal-orchestration:intent-analyst` → `sales-prospecting:outreach-specialist` | `signal-intel`, `personalization`, `persona-intel` |
| 4 | VIP event invite routing (Empire State tie-in) | `personalization-engine:personalization-architect` → `abm-orchestration:account-planner` → `event-marketing:field-program-manager` | `account-tiering`, `personalization`, `activation-map` |
| 5 | One-click reschedule agent | Custom build (Claude/MCP), light on gtm-agents | `cadence-design`, `qa-gates` |
| 6 | Programmatic partner-source enrichment | `data-enrichment-master:company-analyst` → `partnership-development:partner-program-architect` | `firmographic-analysis`, `data-sourcing` |
| 7 | Reverse-IP → dynamic outreach | `intent-signal-orchestration:automation-lead` → `personalization-engine:personalization-architect` → `sales-prospecting:outreach-specialist` | `signal-scoring`, `suppression-logic`, `outbound-plays`, `cold-outreach` |
| 8 | Ticket-spike → docs agent | `customer-success:escalation-strategist` → `technical-writing:release-documentation-manager` | `sentiment-feedback-loop`, `customer-feedback-taxonomy` |
| 9 | Expansion radar | `customer-analytics:retention-analyst` → `account-management:expansion-playbook` holder → `revenue-analytics:pipeline-analytics-lead` | `cohort-analysis`, `account-health-framework`, `expansion-playbook`, `save-play-library` |

**Build discipline:** every build gets the same 6-section writeup from the V1.1 Stage 3 template. No exceptions. Consistency is part of the signal.

---

## Part 4 — Post-hire ramp: Day 1 through Day 90

The agents below are the ones you'll *actually* use in the seat. Read this section the week before you start, not now.

- **First week — get the lay of the land.** `business-intelligence:data-architecture-lead` (sonnet) and `analytics-pipeline-orchestration:analytics-data-strategist` (sonnet) for the data-foundation audit (what's instrumented, what's garbage, what contracts exist). `revenue-analytics:revenue-intelligence-director` (opus) for the exec-language of how the company already talks about pipeline. `voice-of-customer:voc-program-director` (opus) for the existing customer insights surface.
- **First 30 days — ship one visible thing.** Pick a single rung-1 (data-foundation) or rung-3 (activation) play and ship it. `growth-experiments:experimentation-strategist` (sonnet) so it ships with a measurement plan from day one.
- **30–60 — multi-thread.** `abm-orchestration:abm-strategist` (sonnet) if the role leans ABM. `intent-signal-orchestration:sales-liaison` (sonnet) if the role leans GTME. `sales-enablement:enablement-strategist` (sonnet) to get your plays adopted by the field.
- **60–90 — exec visibility.** `revenue-analytics:exec-briefing-kit` holder + `business-intelligence:insights-program-director` (opus). Present your first QBR-style readout on what you've shipped and what's next.

**The trap to avoid:** ramping with `customer-success` or `sales-pipeline` style agents on Day 1 just because the language is familiar. Those are your *old* center of gravity. The new center of gravity is data-signal, intent, analytics-pipeline, and business-intelligence. Spend the first 30 days *there*.

---

## Part 5 — Gaps in the catalog

Things the Clay-style GTME role demands that the gtm-agents catalog does *not* adequately cover. Flag these so you don't assume the catalog is complete — and so you know where you'll need to supplement with your own builds / outside frameworks.

1. **Semantic layer tooling (Cube.dev, dbt, Hex).** Catalog talks about the *concept* (data contracts, metric governance) but has no skill dedicated to implementing in a specific tool. You'll need the tool-specific muscle from somewhere else.
2. **LLM evals specifically.** `growth-experiments` is strong on A/B testing and experimentation generally. There is no skill on "how to evaluate an LLM-driven agent's outputs." This is core GTME craft now. Build your own reference doc.
3. **Claude Code / Agent SDK mechanics.** The catalog treats agents abstractly. It doesn't teach you how to write a subagent or a hook or an MCP. Lean on Anthropic docs + your own Empire State builds for this.
4. **Warm-intro sourcing at the individual level.** `sales-prospecting` is for prospects, not for hiring-manager warm intros. You're building that muscle yourself via the events pipeline — which is arguably the unfair advantage.
5. **Personal brand / documentarian strategy.** `content-marketing:thought-leader` helps with the *artifact*, but not with the *cadence* and *documentarian angle* that V1.1 Part 0 calls out as your edge. That strategy lives in the Empire State `content-correspondent` skill — which is the correct home for it.
6. **Clay-specific tooling.** Nothing in the catalog is specific to Clay the product. If you're going deep on Clay as a target, you'll need hands-on time with Clay itself. The catalog is Clay-*adjacent* but not Clay-*native*.

---

## Part 6 — Invocation pattern rules (how to actually work this)

Three rules, memorize:

1. **One agent per job, not a pile.** If a task could reasonably be done by a single sonnet agent, don't invoke three. Pick the agent whose description most directly matches the task verb.
2. **Read the SKILL.md before the first invocation in a domain.** Progressive disclosure means the skill metadata is intentionally thin. Reading the full SKILL.md before you first run a plugin is 10 minutes that saves you from producing shallow output.
3. **Every build gets a measurement plan and a writeup.** No exceptions. The `growth-experiments` + `marketing-analytics` skills are how you avoid Clay's red flag #4 ("no measurement plan").

---

## Confidence

- Part 0 Mastery-proofs: **88%** — these are the right eight based on the roadmap and the Clay blog. Could flex by one either direction after a real Clay interview loop.
- Part 1 Coursework map: **78%** — holds if Alex's domain definitions don't drift. Domain 5 (AI/agent systems) is the weakest match to the catalog.
- Part 2 Funnel map: **82%** — Stages 1–5 and 8 are clean fits. Stage 7 (offer/negotiation) is the most speculative use of the catalog but the `pricing-strategy` hack is a legitimate framework transfer.
- Part 3 Portfolio cross-walk: **75%** — the three builds I recommended (scoring, digest, reverse-IP) are the right picks, but which specific agents you lean on inside each build will shift as you touch the code.
- Part 5 Gaps: **90%** — these six gaps are real and the catalog won't close them. Plan accordingly.
