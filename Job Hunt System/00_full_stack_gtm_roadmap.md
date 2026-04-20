# The Full-Stack GTM Roadmap — V1.1

**Author:** Claude (with Alex) · **Date:** 2026-04-20 · **Status:** V1.1 — Clay GTM engineering blog integrated

---

## How to read this document

This is V1.1. Two parts that stand alone (per your instructions) and are meant to be argued with, not accepted:

- **Part 1 — Coursework.** The skill domains and sequencing required to become the "Full-Stack GTM Pro" archetype implied by the five Clay JDs, the Clay GTM-engineering thesis, and the broader movement. Organized by capability domain, with depth targets, resources, and benchmarks.
- **Part 2 — Job-hunt funnel.** The search run as an AI-native full-funnel GTM motion, from market mapping through offer close and ramp. Each stage has objective, actions, tools, artifacts, metrics, and a "what the top 1% does" differentiator.

**What changed from V1 → V1.1 (Clay GTM engineering blog integration):**

1. Part 0 opens with the consultative-seller thesis — this is Clay's explicit hiring mental model ("Harvey uses lawyers, Clay uses GTMEs"), and it is your positioning bullseye.
2. Part 0 adds the three-rung maturity model (Data foundation → Data modeling → Data activation) as the operating sequence the nine domains serve.
3. Part 0 adds the "GTM alpha" concept and a concrete org-model taxonomy (GTME inside RevOps vs. GTME inside Growth), with named companies + humans.
4. Domain 3 (GTM Engineering Craft) gets six concrete portfolio play patterns drawn from real Clay builds, plus the "meetings booked / hours saved" measurement frame.
5. Part 2 Stage 1 (Market Mapping) gets a named-human tier-1 target list at Intercom, Canva, Notion, Anthropic, Ramp, Verkada, Rippling.
6. Part 2 Stage 6 (Evaluation) is rewritten to teach to Clay's actual published three-part assessment rubric (business problem investigation → systems sketch → mini build challenge), including their stated red flags.

**Still outstanding:** the coursework has not yet been cross-mapped to the Empire State Events Pipeline build plan — per your instructions, that's the next pass.

**Source material used:** Five Clay JDs (Forward Deployed GTM Engineer, Head of GTM Architecture, Product Marketing, Analytics Engineer, Enterprise Growth Strategist-CS); the Clay GTM engineering blog post (clay.com/blog/gtm-engineering, integrated in V1.1); the `gtm-agents` marketplace (243 skills across 67 plugins); your CLAUDE.md project architecture for the Empire State Events pipeline.

---

## PART 0 — Role Archetype Synthesis

Before the coursework, a quick grounding on what the five JDs + the Clay blog actually collapse into. This is the target you're optimizing for.

### The thesis, stated plainly: you are Clay's archetypal hire

Clay's GTM engineering post says the quiet part loudly: "Just as Harvey uses lawyers to sell legal software and Prompt Health uses therapists to sell and support their product, Clay uses GTMEs to sell Clay. These sellers have deep empathy for our customers and speak their language."

Read against your background — 12+ years enterprise AE closing the exact workflow Clay automates, now building agentic systems in the same thesis space — you are not an AE learning to code. **You are the consultative seller who's lived the workflow AND can now build against it.** That is Clay's explicit hiring mental model for the Forward Deployed GTME role, and it is the single sharpest frame for your positioning. Part 2 Stage 2 operationalizes this; flag it now because it should color how you read the rest of this document.

### The operating sequence: data foundation → modeling → activation

Clay's blog makes one taxonomic claim that is non-negotiable:

> "GTM Engineers offer a portable toolkit that only works when the stack beneath it is solid. Their work progresses through three rungs, each building upon the last."

1. **Data foundation** — clean, deduped, trustworthy CRM + warehouse records. Automated enrichment jobs, schema audits, merge-and-purge routines, ownership rules.
2. **Data modeling** — unique data points that *predict* purchase, expansion, or churn. Propensity scores, ICP attributes, AI-data points.
3. **Data activation** — unique data points deployed in revenue-generating workflows. Automated outreach, meeting notes, churn-risk nudges, sales enablement.

"Most companies stumble on the first rung." That is both the market truth and the interview punchline. The nine coursework domains in Part 1 each serve one or more of these rungs — I flag which one(s) as we go. When you're building your portfolio (Domain 3) and answering assessment questions (Part 2 Stage 6), default to: *what rung is this serving, and have we earned the right to be on it?*

### "GTM alpha": the concept you are selling yourself as a vector for

Clay's framing: GTM tactics have commoditized ("prospects get hundreds of generic cold emails"), and the edge now lives in **unique data + differentiated plays**. They call this *GTM alpha*. The example in the post — "you should spend resources targeting NYC cafes with $10-20 entrees who just joined DoorDash—and help you reach them tomorrow, not next quarter" — is narrow, signal-rich, and executed in hours, not quarters.

This is the concept to anchor your narrative on. Your interview answers, your LinkedIn posts, your portfolio writeups should demonstrate that you think in terms of GTM alpha — signal density, segmentation narrow enough to be defensible, execution speed measured in hours. The opposite (the thing you are *against*) is the "hire 10 more reps for every 10% pipeline lift" worldview.

### Where the function actually lives: two org-model archetypes

Clay documents the two dominant patterns. Both are real, and they determine what the role you're applying for *actually does*:

**Model 1 — GTME inside RevOps (the dominant pattern).** GTMEs report into RevOps or GTM ops. Often splits into prototypers and implementers: generalists close to sales hack proofs-of-concept, engineers harden winners for millions of CRM rows. Named setups in the blog:

- **Intercom** — Alexander DeMoulin's GTM Ops pilots plays (e.g., TAM enrichment); GTM Systems, embedded in R&D, scales to production.
- **Canva** — Robert Jones's GTM AI team automates workflows (e.g., transcript summarization); separate enrichment team pipes novel data in.
- **Notion** — three teams: Evan Peters owns RevOps + Strategy with a GTM innovation pod (→ CRO); Jalal Iftikhar and Shelley Lee own BizTech + automation engineering (→ CFO); Theo Bleier is an embedded AI engineer (→ CTO).
- **Anthropic** — GTM Infrastructure & Incentives pod under Adam Wall; a "Productivity Engineering" sub-squad wields Claude + Clay.

Why it works: "RevOps already owns data pipelines and quality, so lodging GTMEs here draws a straight line from 'we spotted a friction point' to 'we shipped the fix.'"

**Model 2 — GTME inside Growth.** Technical talent beside demand gen, unlocks programmatic landing pages, real-time intent harvesting, SDR automation. Named setups:

- **Ramp** — Growth Platform squad under PMs like Keyan Sarrafzadeh, partnered with Growth Engineering; two-week sprints; separate Business Systems group for Salesforce plumbing.
- **Verkada** — GTMEs under Davide Grieco in the Growth team reporting to CMO; 80-100 meetings per rep per month via SDR workflow automation.
- **Rippling** — GTM engineering inside Noah Adelstein's international growth team + US growth team; frequent growth experiments, automated outbound + direct mail.

Why it works: "embedding technical talent beside demand gen unlocks ideas — programmatic landing pages, real-time intent harvesting — that traditional marketers might never attempt."

**Cross-model lessons you should internalize before any interview:**

1. "Start in ops, federate later." Most companies incubate GTME under RevOps then push talent outward once foundations are solid.
2. Balance rapid prototyping with stable implementation. Data engineering skills matter when experiments scale.
3. Data hygiene is non-negotiable. Every win traces back to clean, enriched, well-modeled data.

These three lines should appear in your interview answers. They're table-stakes fluency now.

### What the five JDs have in common (the archetype)

Reading across the JDs, seven traits show up in every one of them — these are the archetype's **load-bearing pillars**, not the surface-level responsibilities:

1. **AI multiplier, not AI user.** "You don't just use AI, you build leverage with it." Every role expects someone who extends their own capacity with agentic systems. This is the single most consistent requirement.
2. **0→1 builder DNA.** "Process-light, outcome-heavy." "Design scalable frameworks, playbooks, and initiatives for future customers." "Reinvented the playbook from first principles and are excited to do it again." Structure-creators, not structure-inheritors.
3. **Practitioner-evangelist.** The Head of GTM Architecture sits in every forecast call *and* speaks at customer events. The Enterprise Growth Strategist partners with customers *and* influences Clay's roadmap. The wall between "doing" and "telling the story" is gone.
4. **Cross-funnel fluency.** Every role expects you to speak the language of RevOps, Marketing Ops, Sales, CS, and Product. Not necessarily expert in each — but fluent.
5. **Commercial seriousness.** The roles involve enterprise stakeholders, complex deals, and revenue accountability. None of these are "nice-to-have IC" roles — they carry P&L weight.
6. **Written communication as a weapon.** Messaging frameworks, playbooks, narratives, exec briefs. You ship documents, not just decks.
7. **Comfort with ambiguity + high agency.** "You don't wait for permission or perfect information." "Energized by variety, you don't need a perfectly scoped role to do great work." The role description itself is often a starting point.

### Where the five roles diverge (the skill surface)

| Role | Primary axis | You must be "Own" level | You must be "Do" level |
|---|---|---|---|
| Forward Deployed GTME | Enterprise delivery + workflow build | Discovery, Clay/workflow eng, stakeholder orchestration | Data eng lite, PMM storytelling |
| Head of GTM Architecture | Revenue operating model design | GTM finance & modeling, inspection cadences, comp/territory | Workflow eng, AI tools |
| Product Marketing (the file) | Narrative + revenue enablement | Positioning, messaging, competitive, enablement | Data analysis, pricing |
| Analytics Engineer | Modern data stack ownership | SQL, dbt, Dagster, Snowflake, AWS | GenAI in data products |
| Enterprise Growth Strategist | Strategic CS + co-creation | Customer strategy, expansion plays, product voice | Workflow eng, data interpretation |

**The "full-stack" pitch:** you are not any one of these in isolation. You are the person who, in a small AI-native GTM org, can **credibly cover 60-70% of any single role's surface area and 100% of its integration points**. That's the unicorn you're training into.

### What this means for you specifically (Alex)

You already have the commercial backbone — 12+ years enterprise AE, land-and-expand motion, multi-stakeholder deals — **and you're already mid-build on an agentic system (Empire State Events) that exemplifies the rung-2 + rung-3 work Clay is hiring for.** That combination is exactly the consultative-seller-who-built-it archetype from the opening thesis. The commercial chops are the hardest part to teach; the build chops are what most candidates are missing. You have both, in-flight.

What's still to close for the full-stack archetype:

- **Technical credibility** — not to become an engineer, but to be the person in the room who says "give me the API docs, I'll wire it up" without bluffing.
- **Data fluency** — SQL to a working level, dbt to a vocabulary level, semantic layer to a decision level. This is what lets you operate on rung 1 (foundation) credibly, which is where Clay says most companies fail.
- **AI/agent engineering** — prompting, agents, evals, MCP, context engineering. You're 70% there via the Empire State pipeline; needs reps.
- **PMM craft** — positioning as a discipline, not a vibe. Message architecture. Competitive intel as a system.
- **GTM systems thinking** — operating rhythm, funnel architecture, capacity modeling, inspection cadences. This is the language of the Head of GTM Architecture role and the language the Clay-blog-named operators (DeMoulin, Wall, Sarrafzadeh, Grieco) use in public.

The coursework below is sequenced to close those gaps without losing what you already have, and each domain notes which rung of the Clay maturity model it serves.

---

# PART 1 — Coursework

## Structure of the coursework

**Nine capability domains.** Each has a "why it matters" tied to the JDs, core concepts, frameworks + canonical reading, hands-on benchmarks, and a **depth target** for you.

**Depth tiers:**

- **Recognize** — you can read about it, follow a conversation, know when to ask for help. Minimum bar.
- **Do** — you can execute competently with reference material, produce work product, talk through trade-offs. Working bar.
- **Own** — you can design systems, teach others, and be the senior voice in the room. Senior bar.

For an AI-native GTM senior hire, the realistic target is: **Own in 3-4 domains, Do in the rest, Recognize nothing — you have to be at least Do everywhere to be credible.**

---

## Domain 1 — Commercial & Enterprise Sales Mastery

**Depth target: OWN** (this is your moat; sharpen, don't just maintain)

### Why it matters
Every JD assumes commercial seriousness. The Head of GTM Architecture literally "sits in every forecast call." The Enterprise Growth Strategist is a "strategic business partner." Even the Analytics Engineer is building for GTM outcomes. Your selling DNA is the foundation the other eight domains sit on — but in an AI-native context, the bar has moved from "quota-carrying" to "quota-carrying + operates like a revenue architect."

### Core concepts
- Modern enterprise deal shape: committee-based buying, procurement + security gates, multi-threading, economic vs. technical vs. champion personas.
- Value-based selling: quantified business outcomes vs. feature parity.
- Qualification frameworks as **inspection tools**, not scripts.

### Frameworks & canonical sources
- **MEDDPICC** (Metrics, Economic Buyer, Decision Criteria, Decision Process, Paper Process, Identify Pain, Champion, Competition) — lingua franca of enterprise pursuits. Already in your `gtm-agents` repo as a plugin and in your available skills (`the-meddpicc-enterprise-deal-desk`).
- **Command of the Message / Command of the Sale** (Force Management) — value-first messaging at the deal level.
- **Winning by Design — Revenue Architecture** — funnel math, bowtie model, SPICED discovery (Situation, Pain, Impact, Critical Event, Decision). You have the skill installed (`winning-by-design-sales-excellence-framework`) — use it as a daily reference, not a poster.
- **The Challenger Sale** (Dixon/Adamson) — teach, tailor, take control; commercial insight as differentiator.
- **Never Split the Difference** (Voss) — negotiation; late-stage and offer-stage leverage.

### Hands-on benchmarks
- Produce a written **deal strategy memo** (3-5 pages) on a real prospect using MEDDPICC + SPICED, including a multi-thread org map and a "risks-and-mitigations" register. Reuse your existing `gtm-agents/plugins/enterprise-sales/skills/value-story-framework/` skill as a template.
- Record yourself running a mock discovery call with commercial-insight framing; self-review against SPICED and MEDDPICC.
- Draft an **exec-sponsor email** that earns a 30-min meeting with a CRO-level buyer using only public signals.

### Concept explainer — what "value-based selling" actually means at this level
It is not "talk about benefits instead of features." It is arithmetic. You build a model with the prospect that shows: (a) current-state cost of the problem in dollars, (b) probable-state cost with your solution, (c) the delta, and (d) the payback period. If you cannot quantify the delta, you cannot defend the price at procurement. The Value Story Framework skill in your `gtm-agents` repo is a template for this — `plugins/enterprise-sales/skills/value-story-framework/SKILL.md`.

---

## Domain 2 — Full-Funnel GTM Systems Thinking

**Depth target: OWN** (this is the Head-of-GTM-Architecture axis and the single highest-leverage differentiator for a senior IC)

### Why it matters
Clay's Head of GTM Architecture JD: "architect the GTM operating rhythm end-to-end." "Design inspection and accountability cadences." "Operationalize comp rollout." This is the move from "I hit quota" to "I understand why the quota is what it is, and I can redesign the engine that produces it." It is the language that gets a senior AE treated like a peer by a CRO.

### Core concepts
- **The bowtie funnel** (acquisition → retention → expansion) and why SaaS maturity makes the right side of the bowtie the value center.
- **Operating rhythm**: forecast calls, pipeline councils, QBRs, forecast-to-actual variance reviews, rules of engagement.
- **Capacity modeling**: reps × productivity × ramp × territory coverage → quota → capacity gap.
- **Compensation design**: accelerators, SPIFFs, multipliers, clawbacks, the pathology of "paying for activity."
- **Territory and routing**: carve-outs, account assignment, splits, named accounts, lead-to-opp routing.
- **Funnel diagnostics**: conversion by stage, velocity, slippage, CAC, payback, gross retention, net retention, magic number.

### Frameworks & canonical sources
- **"The Revenue Architecture" — Winning by Design** (book + course). Installed as skill.
- **"From Impossible to Inevitable" — Ross & Cannon**. Predictable revenue playbook.
- **"The SaaS CFO" blog** (Ben Murray) — SaaS finance metrics in operator language.
- **Tomasz Tunguz, Jason Lemkin, SaaStr** — public benchmarks for every funnel metric.
- **`gtm-agents` plugins** — `revenue-analytics`, `revenue-forecasting-pipeline`, `enterprise-sales`, `sales-pipeline`, `sales-operations`. Read every SKILL.md at least once; the signal-to-noise is high.

### Hands-on benchmarks
- Build a **capacity model in Excel/Sheets** for a 20-AE team hitting $40M new ARR: ramp curves, productivity assumptions, attrition, hiring plan. Stress-test it.
- Draft a **"rules of engagement" document** for a 2-segment sales org (Commercial ≤500 employees, Enterprise >500) — account assignment logic, deal-split rules, SDR-AE handoff, escalation paths.
- Write a **one-page "operating rhythm" proposal** for a Series B AI-native company: which meetings exist, what each one decides, who owns each, what artifacts come out.
- Take one of your own closed deals and run a retrospective **funnel decomposition**: which stage drove velocity, which created slippage, what would you change about the stage definitions.

### Concept explainer — why "operating rhythm" is a senior skill
A junior operator asks "are we hitting plan?" A senior operator asks "do we have the *meetings, artifacts, and inspection loops* that would let us know if we weren't, and correct before it costs us a quarter?" The job of the Head of GTM Architecture is to design that loop. Understanding it is what lets you walk into any AI-native company's GTM org and say "here's what's missing in your rhythm" — and be right.

---

## Domain 3 — GTM Engineering Craft

**Depth target: OWN** (the "GTM engineer" in "Full-Stack GTM Pro" is load-bearing)
**Rung mapping: all three rungs — this is where the maturity model becomes executable.** You are moving clean foundations (rung 1) into predictive models (rung 2) into revenue-generating workflows (rung 3). Every build you ship should name the rung it serves.

### Why it matters
This is the Forward Deployed GTM Engineer JD near-verbatim, and it is also the backbone of Clay's entire blog thesis. "Design end-to-end Clay workflows and architectures that plug into existing GTM stacks." "Deeply hands-on with GTM tools." The Clay framing: GTMEs are "an internal product team that serves the GTM organization — they identify problems, write specs, ship prototypes, and scale what works, measuring success by metrics like meetings booked and hours saved." If you can do this work, you can walk into any AI-native company and immediately be useful — which is why this is also the fastest proof surface for the job hunt.

**Measurement frame you should adopt now and use forever:** every build, every portfolio artifact, every LinkedIn post about a workflow you shipped should lead with two numbers — **meetings booked** and **hours saved**. That is how Clay's own GTMEs self-report. It is the measurement vocabulary the hiring managers at your Tier 1 targets speak. Replace generic outcome language ("automated a workflow," "improved efficiency") with these two numbers or a hypothesis of them. If you can't quantify either, the build isn't shipped yet.

### Core concepts
- **Workflow orchestration**: event-driven automation, webhooks, triggers, conditional branches, retries, error handling, idempotency.
- **Enrichment waterfalls**: cost-aware provider sequencing, credit budgeting, quality scoring, suppression.
- **Identity resolution**: deduping across sources, match keys, watermarking source-of-truth, privacy considerations.
- **Signal architecture**: intent, product usage, web, job-postings, news, funding, technographic — classified, weighted, decayed, routed.
- **System integration**: CRM (HubSpot/Salesforce), MAP (Marketo/HubSpot/Customer.io), sequencers (Outreach/Salesloft/Apollo), data layer (Segment/RudderStack), warehouse (Snowflake/BigQuery).
- **API literacy**: REST, auth (OAuth/API key), rate limits, pagination, idempotency keys, retries with backoff.

### Tools to actually learn
- **Clay** — the operating environment. Free tier + their academy. Build 5 workflows end-to-end: an inbound enrichment flow, an outbound list-build flow, a signal-based trigger flow, a CRM-write flow with dedup, a Clay-to-Slack alert flow.
- **HubSpot** — you have an account already (per your CLAUDE.md). Get deep: workflows, custom properties, associations, custom objects, reports.
- **Salesforce Admin fundamentals** — even if you don't use it daily, the market runs on it. Trailhead's Admin Beginner track is ~10 hours and sufficient.
- **n8n, Zapier, Make** — you already have n8n chops from the predecessor project. Lean into it.
- **Segment / RudderStack** — event collection basics. You don't need to instrument an app, but you need to read a tracking plan.
- **Postman / HTTPie / `curl`** — API sandboxing. Every GTM engineer lives here.

### Portfolio play patterns to target (drawn from real Clay builds)

The Clay blog lists specific GTME builds from their internal team. These are the *shapes* your portfolio should imitate — not one-to-one copies, but same category. Pick 3-4 to build end-to-end across the 12-week sprint. Each should ship with a meetings-booked or hours-saved number (even if hypothetical and defensible).

| Pattern | What it does | Rung | Clay example |
|---|---|---|---|
| **Inbound scoring + auto-routing** | Scores new signups for fit, auto-assigns to best-fit rep, drafts follow-up referencing similar-customer use cases | 2 → 3 | Manny & Osman: $25k+ potential scoring + routing |
| **Transcript → CRM backfill** | LLM listens to call recording, extracts firmographics + fields, writes to Salesforce, so reps never live in the CRM | 1 → 3 | Blake: Salesforce field auto-population |
| **Signal digest in Slack** | Pipes account-awareness signal digest to individual sellers for call prep | 2 → 3 | Osman: signal digests to sellers |
| **VIP event-invite cross-reference** | Matches event attendee list to CRM + geolocation, surfaces ideal invitees, auto-sends on seller's behalf | 2 → 3 | Spencer: VIP event invite play |
| **One-click call rescheduling** | Auto-fires a "suggest a new time" link when prospect misses a meeting | 1 → 3 | Clay internal |
| **Programmatic partner sourcing** | Scrapes social + website profiles, scores fit, powers influencer/partnership outbound | 1 → 2 → 3 | Tommy: influencer marketing program |
| **Reverse-IP dynamic outreach** | Watches reverse-IP data, triggers personalized email while interest is hot | 2 → 3 | Pranav: dynamic visitor campaigns |
| **Ticket-spike → docs drafting** | Flags surges in support tickets, drafts help-center articles to deflect next wave | 3 (CX) | Bruno: ticket-spike alarm |
| **Expansion radar** | Scans support threads for enterprise-feature requests, feeds signals to AM before renewal | 2 → 3 (CX) | Osman: expansion signals |

Your Empire State Events pipeline *already* maps to 2-3 of these patterns (notably the signal digest shape, the documentarian content-generation shape, and — after Phase 3 — the reverse-intake shape). Make that mapping explicit in your writeups.

### Hands-on benchmarks
- **Capstone 1: Clay-equivalent in your own stack.** Build a workflow in n8n + HubSpot + Apollo/Clay free tier that (a) ingests a new HubSpot contact, (b) enriches with 2 providers in a waterfall, (c) classifies fit via LLM, (d) routes to the right sequence, (e) logs the decision to a Notion audit table. Document it in `workspace/strategies/` in your `gtm-agents` folder. Report: hours saved vs. manual baseline; if inbound, meetings booked uplift hypothesis.
- **Capstone 2: Event-driven outbound engine.** Ingest a signal source (Clay job-postings, BuiltWith, LinkedIn employment changes, funding), filter by ICP rules, generate a personalized first-touch via LLM, write to CRM, trigger sequence. End-to-end in ≤ 48 hours of build. Report: meetings booked per 100 contacts; hours saved vs. manual research.
- **Capstone 3: Forward-deployed consulting simulation.** Pick a public AI-native company (ideally a Tier 1 target from Part 2 Stage 1). Write a 5-page implementation proposal as if you were pitching a Forward Deployed GTME engagement: current-state diagnosis, proposed architecture diagram, 6-week build plan, success metrics (meetings booked + hours saved). Share on LinkedIn. This is both a portfolio artifact and a job-search asset — it can walk in the door to a specific hiring manager.

### Frameworks & canonical sources
- **Clay Academy** (free) — their own curriculum for learning Clay; table stakes if you want a Clay interview.
- **Data-signal-enrichment plugin** in your `gtm-agents` repo (`plugins/data-signal-enrichment/`) — already has: Waterfall Blueprint, Provider Scorecard, Identity Resolution, Signal Taxonomy, Validation Rulebook. This is literal JD-aligned training material.
- **Intent-signal-orchestration plugin** (`plugins/intent-signal-orchestration/`) — Signal Scoring, Suppression Logic, Signal-Aligned Outbound Plays.
- **The HubSpot Academy** — free, official; get the Inbound, Sales Software, and Workflow Automation certifications.
- **Reforge "Growth Engineering" track** (if budget allows) — or at minimum, its free content library.

### Concept explainer — what is an "enrichment waterfall" and why does it matter?
An enrichment waterfall is a cost-aware sequence of data providers that tries provider A first, falls back to provider B if A fails or returns low confidence, and so on, stopping as soon as the data is "good enough." It matters because (a) enrichment credits are expensive and (b) no single provider has great coverage across all segments. Done badly, you blow a $20K/year budget in three months. Done well, you triple your effective coverage at half the cost. The Waterfall Blueprint skill in `gtm-agents/plugins/data-signal-enrichment/skills/waterfall-blueprint/` is a starting template.

---

## Domain 4 — Data & Analytics Fluency

**Depth target: DO** (you don't need to be the Analytics Engineer; you need to be credible talking to one)
**Rung mapping: rung 1 (data foundation) + rung 2 (data modeling).** This domain is specifically how you earn the right to be on rungs 2 and 3. "Most companies stumble on the first rung" — a fluent GTM engineer is the one who recognizes that and fixes it before attempting fancy activation.

### Why it matters
Clay's blog is explicit: data hygiene is non-negotiable, and every win traces back to clean, enriched, well-modeled data. The Analytics Engineer JD tells us what the modern AI-native data stack looks like: Fivetran, Segment, Snowflake, **dbt**, Dagster, Streamlit, Hex, Sigma, Eppo, Census, Cube.dev. You will not master all of these. You need to understand what each one does, speak SQL to a working level, and be able to look at a dbt model and understand what it's doing.

Why? Because the modern GTM org is governed by the **semantic layer** (dbt + metrics definitions), and if you can't read it, you will always be downstream of whoever can. The Head of GTM Architecture JD specifically calls out "exceptional quantitative modeling skills" — they mean you need to be able to open a spreadsheet or a notebook and build the model yourself. And in the assessment rubric Clay publishes (Part 2 Stage 6), a candidate who ignores data-quality or deliverability is flagged as a red flag. This domain is where you avoid that flag.

### Core concepts
- **SQL at working depth**: joins (inner/left/right/full), window functions, CTEs, subqueries, aggregations, date math, NULL handling, grouping sets.
- **The modern data stack layers**: source systems → ELT/ETL (Fivetran, Airbyte, Segment) → warehouse (Snowflake, BigQuery, Databricks, Redshift) → transformation (dbt) → orchestration (Airflow, Dagster, Prefect) → BI (Hex, Sigma, Mode, Tableau, Looker) → reverse ETL (Census, Hightouch).
- **Dimensional modeling basics**: facts vs. dimensions, star schemas, slowly-changing dimensions, grain.
- **Semantic layer / metrics layer**: why having "ARR" defined in one place matters, what breaks when it isn't.
- **Experiment design**: hypothesis, control/treatment, sample sizing, guardrails, p-values (at a "don't embarrass yourself" level).
- **Funnel math & cohort analysis**: stage-to-stage conversion, velocity, retention curves, cohort decay.

### Tools & skills to learn (in priority order)
1. **SQL.** Get to the point where you can write a CTE-chained query with a window function without reference material. Benchmark: Mode's SQL tutorial + the `data:sql-queries` and `data:write-query` skills in your Cowork setup.
2. **Spreadsheet modeling** (Excel/Sheets, and basic Sigma/Hex). The Head of GTM Architecture JD specifically calls out "exceptional quantitative modeling skills." Build a cohort retention model and a CAC-payback model from scratch.
3. **dbt**: read and modify a model. The dbt Fundamentals course (free, ~4 hours) gets you to Recognize. Build one small project to get to Do.
4. **Hex or Streamlit**: stand up one dashboard from scratch end-to-end. Hex is the likely choice given Clay's stack.
5. **Python for data**: pandas, matplotlib/plotly. Not to be a data scientist — to be the person who can run a quick analysis when the data team is busy.

### Hands-on benchmarks
- **Cohort retention analysis from a CSV.** Given a list of customer signup dates and monthly usage, produce a cohort retention heatmap. Write a 1-paragraph narrative of what it says.
- **Build one dbt model.** A `stg_` model and a `fct_` model that transform a raw CRM export into a usable "opportunities" fact table. Document it.
- **Metrics dictionary.** Write the one-page definition of ARR, NRR, GRR, CAC, Payback, Magic Number, Rule of 40 for a hypothetical SaaS company. Make the formulas testable.
- **Experiment post-mortem.** Pick a published A/B test case study; re-derive whether the result was significant given the sample size.

### Frameworks & canonical sources
- **Mode's SQL tutorial** (free) — still the gold standard for working-SQL fluency.
- **dbt Fundamentals** (free, dbt Learn).
- **"Designing Data-Intensive Applications"** — Kleppmann. Way more than you need, but worth skimming chapters on data modeling.
- **Emily Robinson & Jacqueline Nolis — "Build a Career in Data Science"** — the vocabulary of the field.
- **`gtm-agents` plugins**: `analytics-pipeline-orchestration`, `business-intelligence`, `revenue-analytics`, `marketing-analytics`. Each of the SKILL.md files is a ~200-line primer written for GTM audiences.
- **Cowork data skills already available**: `data:analyze`, `data:explore-data`, `data:validate-data`, `data:statistical-analysis`, `data:build-dashboard`, `data:sql-queries`. Use them as homework aids, not crutches.

### Concept explainer — why the semantic layer is a strategic asset, not plumbing
In a pre-semantic-layer world, "ARR" is defined slightly differently in 11 dashboards and 4 executive reports. The Head of Sales reports one number in the forecast call; the CFO reports a different one to the board; neither can be reconciled in under 3 hours. In a post-semantic-layer world (dbt metrics, Cube, LookML, Malloy), ARR is defined *once*, in code, with tests, with version history. Every dashboard and every agent that needs ARR pulls from the same definition. This is why AI-native companies care so much about dbt: because agent-driven analytics is only safe if the metrics are bulletproof. If you walk into a GTM interview and say "I think the semantic layer is the strategic asset that makes agentic revenue-ops possible," you will stand out.

---

## Domain 5 — AI / Agent Engineering

**Depth target: OWN** (this is your "AI multiplier" proof; you're already 60-70% there)

### Why it matters
Every JD says some version of "AI multiplier." You are being hired *because of* your AI fluency, not despite it. The Empire State Events pipeline you are building is literally the proof artifact for this domain. The gap to close is from "builds useful AI workflows" (you) to "speaks the engineering vocabulary of LLMs, agents, and evals fluently enough to sit at a product-engineering table and not be pitied" (target).

### Core concepts
- **LLM fundamentals**: tokens, context windows, temperature, top-p, stop sequences, structured outputs, function/tool calling, streaming.
- **Prompt engineering craft**: system prompts, few-shot vs. zero-shot, role prompting, chain-of-thought, prompt chaining, prompt caching, extended thinking, XML tags as structure.
- **Retrieval-Augmented Generation (RAG)**: embeddings, vector stores, chunking strategies, hybrid retrieval, reranking, grounding.
- **Agents**: the shift from "LLM as answerer" to "LLM as planner-executor with tools." Loop shapes, planning vs. reactive agents, multi-agent systems, hand-offs.
- **Tool use**: function calling, MCP (Model Context Protocol) — you're already using this in the Empire State pipeline.
- **Context engineering**: the discipline of what to put in the context window, when, and why. The successor to "prompt engineering" as the job name.
- **Evals**: offline evals, golden datasets, LLM-as-judge, preference-based evals, regression tests for prompts. Without evals you are building on sand.
- **Cost + latency engineering**: model selection (Haiku/Sonnet/Opus), caching, parallelism, streaming, batching.
- **Safety & alignment basics**: prompt injection, jailbreaking, PII handling, red-teaming.

### Seminal sources to actually read (pick ≥ 6)
- **"Attention Is All You Need"** — Vaswani et al., 2017. The transformer paper. Read the abstract, skim the rest. You want to know what multi-head attention is and why it mattered.
- **"Language Models are Few-Shot Learners"** — GPT-3 paper, 2020. Introduced in-context learning as a paradigm.
- **"Chain-of-Thought Prompting Elicits Reasoning in Large Language Models"** — Wei et al., 2022.
- **"ReAct: Synergizing Reasoning and Acting in Language Models"** — Yao et al., 2022. The agent-loop paper.
- **"Toolformer"** — Schick et al., 2023.
- **Anthropic's "Building Effective Agents"** post (2024) — the cleanest taxonomy of agent patterns in public writing.
- **Anthropic's MCP documentation** — you're already using this; read the spec once to level up from user to fluent user.
- **Simon Willison's blog** — ongoing practitioner commentary, high signal.
- **"Constitutional AI"** (Anthropic, 2022) — if only to understand why Claude's values feel the way they do.
- **LangChain / LlamaIndex docs** — frameworks, even if you don't use them; the vocabulary is shared.

### Tools & platforms
- **Claude Code + Cowork + the Agent SDK** — your daily driver. Get obsessive.
- **Cursor or Windsurf** — code-agent IDE for builds.
- **OpenAI Playground + Anthropic Console** — prompt experimentation.
- **Replit / Bolt / Lovable** — zero-to-deployed AI apps in minutes.
- **LangSmith, Helicone, Langfuse** — evals + observability. Pick one.
- **Pinecone / Weaviate / pgvector** — vector DBs. One is enough.

### Hands-on benchmarks
- **Build one non-Empire-State agentic system end-to-end.** Propose it, scope it, ship it, write it up. 5-10 hour build, single LLM + 3-5 tools + 1 eval suite. Examples: inbound-lead-qualifier agent, content-repurposer, competitive-brief-agent.
- **Write a prompt eval harness** for the Empire State event-research skill. 10 golden examples, LLM-as-judge rubric, score + regression log.
- **Publish one technical write-up** on how you built something — blog, LinkedIn long-form, or the project's GitHub README. Make it detailed enough that another operator could rebuild it.
- **Ship one MCP server of your own.** Use the `mcp-builder` skill in your plugin pack. Even a trivial one (e.g., an MCP server that reads your Notion Events DB). This is a resume credential.

### Frameworks & canonical sources
- **Anthropic's prompt-engineering docs** — https://docs.claude.com/en/docs/build-with-claude/prompt-engineering. Tighter and more practical than most.
- **Lilian Weng's blog** (OpenAI) — excellent synthesis posts on agents, hallucination, evals.
- **"The Prompt Report" (Schulhoff et al., 2024)** — survey of 58 prompt techniques.
- **Your installed `mcp-builder` skill** — use it to build at least one MCP.
- **Your installed `cto-architect` skill** — use it whenever you make architecture decisions for your builds. It will teach you the language by proxy.

### Concept explainer — what "context engineering" means and why prompt engineering became a subset of it
Two years ago, the unit of work was "write a good prompt." Today, the unit of work is "design what goes into the context window, when, and why" — because modern agents chain many LLM calls, pull from many sources, and compose many sub-prompts. The choices look like: do you retrieve and inject, or tool-call and let the model pull? Do you summarize prior turns or keep them raw? Do you use an "orchestrator" model (Opus) to plan and "worker" models (Haiku) to execute? This is engineering, not copywriting. The shift in job title from "prompt engineer" to "AI engineer" or "context engineer" reflects this. If you have an opinion on this shift and can defend it, you're a senior.

---

## Domain 6 — Product Marketing & Narrative

**Depth target: DO** (headed toward OWN as you build a public body of work)

### Why it matters
The "Product Marketing" JD in your uploads (mislabeled as "Analytics Engineer" in the header, but the body is clearly PMM) describes the modern AI-native PMM: "Own Clay's core narrative and messaging frameworks." "Develop segment and persona-specific positioning." "Build and maintain competitive intelligence." Your documentarian angle from Empire State Events is a native PMM skill in disguise — you're already doing thought-leadership content. The gap is turning it from instinct into discipline.

### Core concepts
- **Positioning** (not messaging): who the product is for, against what alternatives, for what value. Positioning is strategy; messaging is expression.
- **The message house / message architecture**: core promise, pillars, proof, audience-specific expressions.
- **Jobs-to-be-Done (JTBD)**: what job is the customer hiring your product to do, in what circumstance.
- **Buyer personas vs. ICP**: persona = who signs, ICP = which accounts fit. Both needed, different functions.
- **Competitive intelligence as a system**: battlecards, win/loss analysis, feature-parity vs. narrative-differentiation, "the story we tell" vs. "the story they tell."
- **Proof hierarchy**: logos, case studies, ROI models, analyst recognition, peer-review (G2, Gartner), benchmarks, free-form testimonial.
- **Enablement**: turning positioning into sales reps' working vocabulary. This is where most PMM work fails.
- **Pricing & packaging**: tiers, fences, value drivers, price-to-willingness-to-pay.

### Frameworks & canonical sources
- **April Dunford — "Obviously Awesome"** and **"Sales Pitch"**. The modern canon on positioning; read both.
- **Andy Raskin's "Strategic Narrative" essays** — the 5-part deck structure every AI-native startup now uses.
- **Geoffrey Moore — "Crossing the Chasm"** — the classic, still load-bearing for any segmented B2B motion.
- **"Jobs to be Done" — Christensen/Ulwick**.
- **Emily Kramer (MKT1 newsletter)** — practitioner cadence on PMM + growth.
- **Packy McCormick (Not Boring), Tomasz Tunguz, Stratechery** — narrative modeling at the company/category level.
- **`gtm-agents` plugins**: `product-marketing`, `brand-strategy`, `competitive-intelligence`, `copywriting`, `pr-communications`. The `product-marketing/skills/positioning/SKILL.md` is a direct transcript of a message-house build process.
- **Cowork skills already available**: `marketing:competitive-brief`, `marketing:brand-review`, `marketing:campaign-plan`, `marketing:content-creation`. Use them on live work.

### Hands-on benchmarks
- **Write a positioning one-pager for yourself** using Dunford's template. The 5 components: competitive alternatives, unique attributes, value, best-fit customers, market category. This doubles as your job-hunt asset.
- **Build a competitive battlecard** for Clay vs. one alternative (pick: Apollo, Outreach, HubSpot's native workflows, Koala, Common Room). Use the Battlecard Library skill. Share it publicly — that's PMM proof and a signal to Clay that you get them.
- **Write one "strategic narrative" piece** (Raskin-style 5-part) on the GTM-engineering category. This is blog-length, ~1500-2000 words, and becomes a pinned post on your LinkedIn.
- **Do a Jobs-to-be-Done synthesis** of 3 people you've met at NYC AI events. What job were they hiring AI to do? Compare across them.

### Concept explainer — "Command of the Message" is a sales methodology, not a marketing one
Common confusion: sales methodology frameworks (Challenger, MEDDPICC, Command of the Message) are often thought of as PMM outputs. They aren't. They are *how the sales team uses* the positioning PMM produces. The handoff works like this: PMM owns the message house; sales enablement builds the call scripts; individual reps adapt it for prospects. If you see yourself as someone who can cross that handoff — write the positioning *and* operationalize it into the sales motion — you are unusually valuable, because most PMMs can't do the second part and most AEs can't do the first.

---

## Domain 7 — Customer Strategy & Expansion

**Depth target: DO** (bordering OWN if you take the Enterprise Growth Strategist path)

### Why it matters
The Enterprise Growth Strategist JD describes a strategic CS role that resembles consulting more than traditional CSM: "You are not just supporting customers, you're a strategic business partner, trusted advisor, and internal product voice." The Forward Deployed GTME JD overlaps heavily — both roles live in discovery + implementation + value realization. If you target CS-adjacent roles, this is the primary axis. Even if you target pure sales roles, every enterprise deal now requires you to sell the expansion path at initial close — so CS fluency raises your ceiling.

### Core concepts
- **Land-Adopt-Expand**: the default model for modern enterprise SaaS; multi-year account strategy.
- **Success planning**: mutual success plan, joint exec sponsor, milestones, KPIs, governance.
- **QBR / EBR mechanics**: what the artifact actually says, how to run the meeting.
- **Onboarding / time-to-value**: the single most predictive metric for expansion.
- **Customer health scoring**: quantitative (usage, engagement) + qualitative (sentiment, champion strength, exec sponsor presence).
- **Expansion motions**: natural account growth, cross-sell, multi-product, new-team expansion.
- **Voice of customer into product**: how practitioner input becomes roadmap.

### Frameworks & canonical sources
- **Lincoln Murphy — "Customer Success"** — the modern playbook.
- **Nick Mehta (Gainsight) writing**.
- **Jason Fried / 37signals — "Shape Up"** (adjacent, but valuable for understanding how modern product orgs think about cycles).
- **Kate Leggett (Forrester) customer-success research**.
- **`gtm-agents` plugins**: `customer-success`, `account-management`, `customer-advocacy-orchestration`, `customer-journey-orchestration`, `renewal-orchestration`. Specifically the `b2b-saas/skills/land-adopt-expand-blueprint/SKILL.md` is JD-aligned.

### Hands-on benchmarks
- **Mutual Success Plan template**: fill one out for a real prospect you know, with actual outcome targets, milestones, KPI definitions, governance cadence.
- **Run a QBR dry-run** with a colleague; produce the pre-read, the deck, the decisions-log.
- **Customer health scorecard**: design a 10-metric scorecard with weights and thresholds for an AI-native SaaS. Justify each weight.
- **Expansion play design**: pick a real B2B SaaS product and design three expansion plays — one usage-trigger, one new-team, one multi-product. Write the play as a 1-page spec including signals, trigger logic, owner, messaging, and success metric.

---

## Domain 8 — Executive Communication & Writing Craft

**Depth target: OWN** (the craft that quietly separates $300K roles from $700K+ roles)

### Why it matters
Every Clay JD values written communication. "Executive (but still grounded) presence: you communicate clearly, challenge assumptions in the room, and are comfortable saying 'I don't know yet!'" "Excellent communicator who can simplify complex concepts and drive alignment from hands-on admins to the C-suite." This domain is a multiplier on everything else — your ability to sell a deal, ship a strategy, or land a job is bottlenecked by your ability to express the thinking behind it precisely and briefly.

### Core concepts
- **Writing as thinking**: if it's unclear on the page, it's unclear in your head. The discipline is to make the page force the clarity.
- **BLUF (Bottom Line Up Front)**: conclusion first, then support. Inverted pyramid.
- **Minto pyramid**: SCQA (Situation, Complication, Question, Answer) plus grouped supporting points.
- **Amazon-style narratives**: the 1-pager and the 6-pager. Read-first meetings.
- **Executive brief craft**: 1 page, ≤ 200 words, TL;DR on top, decision requested, owner, next step.
- **Storytelling arcs**: setup-conflict-resolution; status-quo-threat-hope.
- **Presence**: what to say when you don't know (the Clay JD explicitly values "I don't know yet"). How to challenge in the room without defensiveness. Pausing. Concision.

### Frameworks & canonical sources
- **Barbara Minto — "The Pyramid Principle"**. Canonical.
- **Jeff Bezos's shareholder letters** — the 6-pager discipline in the wild.
- **Paul Graham essays** — concise tech-adjacent prose.
- **Nicole Zhu, "First Round Review"** — modern-operator long-form.
- **Julian Shapiro's writing guide** — free, practical.
- **"On Writing Well" — William Zinsser**.
- **For spoken presence**: Toastmasters; or record yourself + self-review.
- **`gtm-agents` plugins**: `copywriting/skills/voice-guidelines/`, `content-marketing/skills/storytelling/`, `business-intelligence/skills/executive-kpi-briefings/`, `enterprise-sales/skills/cxo-briefing-kit/`.

### Hands-on benchmarks
- **Ship one thing per week in public.** A LinkedIn post, a blog, a video, a walkthrough. Minimum 12 weeks. This is the single highest-leverage practice you can adopt.
- **Write a 1-page executive brief** on a real topic — e.g., "Should our AI-native SaaS adopt a GTM Engineering function in H1?" Get to < 250 words including a decision ask.
- **Narrative rewrite**: take one of your current LinkedIn posts and rewrite it using SCQA. Compare engagement.
- **Post-event documentarian pieces** (from your Empire State pipeline) should be your training ground — you're already doing the reps; discipline them with the frameworks above.

### Concept explainer — why writing is the single most undervalued senior skill
At the IC level, your output is work product. At the senior level, your output is *decisions that other people make differently because of what you wrote*. That's the whole game. The Head of GTM Architecture role's biggest invisible leverage is the documents that shape the CRO's decisions between forecast calls. Nobody gives senior offers to people who can't write. The converse is true too: unusually good writing cannot disguise weak thinking, but unusually clear writing of good thinking will get you hired over better-credentialed candidates every time.

---

## Domain 9 — Meta-Skills & Professional Operating System

**Depth target: OWN** (the one domain that compounds everything else)

### Why it matters
"High agency." "Energized by ambiguity." "You don't wait for permission." These phrases are in every Clay JD. They're not hiring vibes — they're describing a set of learnable operating habits. The tell is whether your *average week* looks like the average week of someone already in the role you want.

### Core concepts & practices
- **First-principles reasoning**: decompose a problem to what is known to be true, rebuild from there. Canonical: Feynman, Musk, Thiel.
- **Systems thinking**: see loops, not linear causes; understand leverage points (Donella Meadows — "Thinking in Systems").
- **Decision journals**: record every non-trivial decision, reasoning, confidence, expected outcome. Review quarterly. (From Shane Parrish — Farnam Street.)
- **Async/written-first operating**: default to doc over meeting; default to clear commit over status update.
- **The weekly review ritual**: 60-90 minutes every Friday. Review goals, calibrate pipeline, capture learnings.
- **Deliberate practice**: isolated skill reps against a scoring rubric, not just "doing the job."
- **Public learning in public**: ship your progress, not your polished end-state.
- **Energy management**, not time management: what drains you, what recharges you, cadence accordingly.
- **AI-multiplier discipline**: every repetitive task either gets templated, automated, or deleted.

### Frameworks & canonical sources
- **"Thinking in Systems" — Donella Meadows**.
- **"Deep Work" + "Digital Minimalism" — Cal Newport**.
- **"The Hard Thing About Hard Things" — Ben Horowitz** — operator-level decision-making under pressure.
- **"High Output Management" — Andy Grove**.
- **"Working Backwards" — Bryar & Carr** — the Amazon operating system, readable.
- **Shane Parrish / Farnam Street** — mental models.
- **Patrick O'Shaughnessy's "Invest Like the Best"** and **Sriram Krishnan's "The Observer Effect"** — the best long-form operator interviews in public.

### Hands-on benchmarks
- **Set up a weekly review template** (Notion or Apple Notes). Use it for 12 weeks. Non-negotiable.
- **Run a "learning in public" cadence**: 1 public post per week on something you learned building.
- **Build a decision journal** and log 1 decision per week for 12 weeks. Review at week 12 — your calibration will improve measurably.
- **Identify your three highest-leverage hours per week** and protect them ruthlessly. Delete, delegate (to AI), or defer everything that doesn't fit.

---

## Coursework sequencing — a 12-week sprint plan

You cannot learn nine domains sequentially without losing momentum. You can, however, run three "tracks" in parallel, each with a weekly rhythm:

| Track | Domains | Weekly cadence | Output |
|---|---|---|---|
| **Track A — Build** | Domains 3, 5 (GTM Eng + AI/Agent) | 8-12 hrs/week, concentrated | Shipped agentic workflows, Clay builds, Empire State pipeline progress |
| **Track B — Study** | Domains 2, 4, 6, 7 (Systems, Data, PMM, CS) | 4-6 hrs/week, daily reading + 1 exercise | 1 written artifact per week (memo, dashboard, positioning one-pager) |
| **Track C — Ship/Public** | Domains 1, 8, 9 (Commercial, Writing, Meta) | Embedded into daily work | 1 LinkedIn post per week; weekly review Friday |

**Week-level cadence:**

- **Mon** — study (2 hrs, Track B) + build (2 hrs, Track A)
- **Tue** — build (3 hrs, Track A) + 1 post draft (Track C)
- **Wed** — study (2 hrs, Track B) + build (2 hrs, Track A)
- **Thu** — build (3 hrs, Track A) + writing craft (1 hr, Track C)
- **Fri** — ship the week's artifact + weekly review (90 min, Track C)
- **Sat/Sun** — 1 deep reading session (2-3 hrs, Track B); rest

**Quarterly capstone:** every 12 weeks, ship one "portfolio anchor" project that is so good it ends up pinned on LinkedIn and linked in every cold outreach.

---

# PART 2 — The Job-Hunt Funnel

## Framing: the search as an AI-native GTM motion

You are not applying for jobs. You are running a full-funnel AI-native GTM motion where:

- **The product is you.** More precisely, "me + an operating system of agents + a body of evidence."
- **The ICP is AI-native companies where full-stack GTM is a real role,** not a buzzword.
- **The persona is the hiring manager + the skip-level + the founding GTM operator** (different plays, different content).
- **The funnel stages are market-mapping → positioning → signal generation → prospecting → outreach → evaluation → offer → ramp.**
- **The differentiator is the method itself.** You are job-hunting the way Clay's Forward Deployed GTME would job-hunt. The process is the portfolio.

The goal of Part 2 is to run this funnel as rigorously as you would run a $5M ABM pursuit.

---

## Stage 1 — Market Mapping (ICP definition)

### Objective
A ranked, tiered list of ~60 target companies that match "AI-native + full-stack-GTM-compatible." Treat it exactly like an ABM target list.

### Actions
1. **Define ICP criteria (written, not vibes).** Candidate criteria:
   - AI is core to the business (AI-native product, or company re-architecting around AI)
   - Stage Series A–C (larger than seed — revenue + GTM function exists; smaller than Series D+ — role shape still fluid enough for a senior generalist to define)
   - 20-250 employees (big enough to need GTM structure, small enough to hire a 1-person full-stack function)
   - NYC or fully remote (matches your standing context)
   - GTM leader is a practitioner, not a career COO (check LinkedIn backgrounds)
   - Signal the company values GTM engineering / AI-native GTM in their public surface
2. **Source the list.** Use:
   - Clay's own customer roster (public: Intercom, Verkada, Anthropic, OpenAI, Rippling, Notion, Ramp, Mercury, Canva — use these as anchors)
   - YC W24/S24/W25/S25 AI-native batches
   - Work at a Startup (YC), Interviewing.io's AI-native board
   - GTMFund, Craft Ventures, Accel AI portfolios
   - ICONIQ, Bessemer, a16z, Greylock, Sequoia AI-portfolio pages
   - Contrary Capital, South Park Commons, Founders Fund
   - Apollo saved search: AI-native + your fit criteria

**Named tier-1 targets from the Clay blog (your starting anchor list).** These are the companies Clay explicitly calls out as running named GTM-engineering functions, with human operators named. Every one is a plausible home for you. Research each human by name, follow them, engage with their content, and map warm paths:

| Company | Org model | Named operators |
|---|---|---|
| **Intercom** | GTME inside RevOps (GTM Ops + embedded GTM Systems in R&D) | Alexander DeMoulin (GTM Ops) |
| **Canva** | GTME inside RevOps (GTM AI team + separate enrichment team) | Robert Jones (GTM AI) |
| **Notion** | Tri-pod structure (RevOps → CRO, BizTech → CFO, embedded AI eng → CTO) | Evan Peters, Jalal Iftikhar, Shelley Lee, Theo Bleier |
| **Anthropic** | GTM Infrastructure & Incentives pod; Productivity Engineering sub-squad | Adam Wall |
| **Ramp** | GTME inside Growth (Growth Platform + Growth Engineering, 2-week sprints) | Keyan Sarrafzadeh (PM) |
| **Verkada** | GTME inside Growth under CMO | Davide Grieco |
| **Rippling** | GTME inside international + US growth teams | Noah Adelstein |

These are your market map anchors. Also: Keith Jones and Rachel Hepworth are named as Clay insiders who shaped the blog — worth following for movement-level signal.
3. **Tier the list** — use your `abm-orchestration/skills/account-tiering/SKILL.md` template literally:
   - **Tier 1 (10-12 companies):** dream fits. Deserve full customized research, personalized outreach, original work artifacts.
   - **Tier 2 (~25 companies):** strong fits. Lightly personalized approach; leverage content + network.
   - **Tier 3 (~25 companies):** volume tier. Templatized application + inbound interest.
4. **Build the artifact.** One Notion database or Airtable base. Fields: Company, Stage, Employees, GTM Leader, Role Match (if hiring), Tier, Last Touch, Next Action, Signal Log, Warm Path.

### Tools & artifacts
- **Apollo** (you have this) — employee growth signals, org charts.
- **Clay free tier** — enrichment + saved searches. This doubles as training for Domain 3.
- **LinkedIn Sales Navigator** (worth 2-3 months at $99/mo even just for the search-query depth) — alumni searches, employment-change alerts.
- **HubSpot** (you have this) — pipeline tracking for the search itself. Yes, really — treat target companies as accounts, hiring managers as contacts, opportunities as applications.
- **Cowork `sales:account-research` skill** — use it per target.

### Metrics to track
- Target list size by tier (60 total is the ballpark)
- Known-warm-path coverage (% of tier 1 where you have a connector)
- Signal density per account (signals logged per company per month)

### What the top 1% does
Publishes a version of their target list as **strategic commentary** — e.g., "The 10 AI-native companies most likely to define the next phase of GTM." Positions you as someone operating at market-analyst level, not candidate level. Note: don't literally publish your "I want to work here" list; publish the *thesis* version that happens to cover your list.

---

## Stage 2 — Positioning & Personal Brand Platform

### Objective
A crisp, defensible positioning statement about you, supported by 3-5 public proof artifacts, so that any warm connection can explain you in one sentence and any stranger can Google you and understand you in 90 seconds.

### Actions
1. **Write your positioning one-pager** using April Dunford's template from Domain 6. Five components:
   - Competitive alternatives (what hiring managers would consider instead of you: a traditional AE + an RevOps analyst; a GTM generalist from a consulting background; an internal promotion)
   - Unique attributes (12+ years enterprise, NYC AI-event documentarian, ships agentic systems weekly, builds in public, **has lived the workflow Clay and Clay-customers are automating**)
   - Value (compressed hiring: 1 senior hire covers AE + ops + AI-tooling + content; you are the consultative-seller-who-built-it archetype Clay explicitly describes — "Harvey uses lawyers, Clay uses GTMEs")
   - Best-fit customers (Series A-C AI-native, 50-150 employees, GTM leader wants a generalist senior)
   - Market category (this is the hardest and most valuable question — pick one: "Full-stack GTM hire," "Founding GTM engineer + AE," "Enterprise AE with operator instincts," "Consultative seller for AI-native GTM products")

**The narrative hook to steal from Clay's blog.** Your positioning doc's opening paragraph should echo (not copy) the Harvey/Clay pattern: *"The best sellers of this product are people who have lived the problem — lawyers selling Harvey, therapists selling Prompt Health, GTM engineers selling Clay. I'm the enterprise AE who's lived twelve years of the workflow these tools are automating, and now I'm building on the other side of it."* That is a one-paragraph frame that aligns you with Clay's stated hiring thesis without you having to claim the title.
2. **Audit and overhaul your LinkedIn.**
   - Headline: role-language that matches your positioning, not job-title-language.
   - About: SCQA structure. Setup (what's changing in GTM), complication (most people are on one side of the AI fence), question (what does full-stack GTM actually look like), answer (here's how I practice it).
   - Experience: rewrite every role into value-delivered, with metrics. Not responsibilities.
   - Featured: 3-5 pinned posts that are your proof artifacts.
3. **Build a minimal personal site** (Framer or Vercel + one Lovable/Bolt page) with: positioning, body of work, current projects, contact. 1 weekend build.
4. **Audit your secondary surface area**: GitHub (even if light — make it presentable), Twitter/X if relevant, public Notion workspace if used, portfolio landing. The goal: no conflicting signal anywhere a hiring manager might land.

### Tools & artifacts
- Cowork `marketing:brand-review` skill on every bio/profile.
- A 5-10 min Loom walking through your work. Becomes a reusable asset.

### Metrics to track
- Inbound recruiter outreach per week (leading indicator)
- Profile views per week
- "Warm intro rate" — % of target companies where you have (or can manufacture within 2 degrees) a warm intro
- Post engagement trend (see Stage 3)

### What the top 1% does
Their positioning is so specific that a hiring manager sees the one-pager and *writes to them before a role opens*. Most people's positioning is generic enough that they fit many searches weakly; the top 1% fit one search *perfectly*. Optimize for fit, not breadth.

---

## Stage 3 — Signal Generation (the flywheel that runs while you sleep)

### Objective
A public body of work that does three jobs at once: (a) proves the skill domains from Part 1, (b) generates inbound interest from target companies, (c) functions as legitimate cold-outreach material.

### Actions
1. **Run your Empire State Events pipeline as the signal engine.** This is the move. Every event attended becomes: 1 LinkedIn post, 2-3 DMs to speakers/hosts (who are at your target companies), 1 project idea. Over 12 weeks, that's ~24 events → ~24 posts + ~60 warm touches + 10-15 shipped small projects.
2. **Publish on three cadences:**
   - **Daily (micro)**: a signal you observed — a tool you tried, a pattern you saw, a thread you joined. LinkedIn, 3-5 sentences.
   - **Weekly (mid)**: a real post — an event recap, a framework, a walkthrough. 150-400 words.
   - **Monthly (macro)**: a long-form — a strategic narrative, a build write-up, a synthesis essay. 1200-2000 words.
3. **Ship shippable artifacts publicly, not privately.** Your Empire State pipeline, your Clay-equivalent build, your prompt eval harness — every one becomes a public GitHub repo + a write-up + a LinkedIn announcement. The write-up is the content; the repo is the proof.
4. **Use the pattern-synthesis skill you've already built.** Two-thesis contrast posts are your canonical documentarian shape — they're a voice-distinguisher and a pattern-recognition signal. Run the rule (max 1/week, needs two briefs).
5. **Target-aware content.** ~20% of your content should be directly relevant to a Tier 1 company's current moment — a new product launch, a recent raise, a new content piece from them. You're not stalking; you're engaging as a peer.

### Tools & artifacts
- Empire State pipeline itself (obvious).
- Cowork `marketing:draft-content`, `marketing:content-creation` as draft partners.
- `content-correspondent` and `post-event-content-generator` skills (already installed).
- LinkedIn's Creator Mode + Featured section.

### Metrics to track
- Weekly posts published (hit rate ≥ 95%)
- Impressions + engagement rate trend (arcs over 8-12 weeks, not week-to-week)
- Warm inbound per week (DMs from new targets)
- Content → meeting conversion (how many posts led to a real conversation with a target-company person)
- **For any build-writeup post: meetings booked + hours saved** (adopt Clay's measurement vocabulary — this is the language hiring managers at your Tier 1 targets use natively)

### What the top 1% does
Publishes a recurring, ownable format. One example: someone publishes a monthly "State of GTM Engineering" essay. Two things happen: (a) hiring managers read it because they want the information, and (b) you become the person they think of when they think about the topic. This is PMM positioning applied to yourself. Your documentarian angle from the Empire State pipeline already *is* an ownable format — productize it.

**The build-writeup template that signals rigor.** Every shipped-project post should follow this skeleton: (1) the problem in one sentence, (2) the rung of the Clay maturity model this build serves, (3) the signal/data source, (4) the workflow shape in 3-5 bullets, (5) the measurement — meetings booked (actual or hypothesized) + hours saved vs. manual baseline, (6) what you'd build next. Six sections, 250-400 words, 1 diagram. This is exactly the shape of the build snippets in the Clay blog (Manny/Osman, Blake, Spencer, Tommy, Pranav, Bruno). Imitating the shape signals fluency.

---

## Stage 4 — Prospecting (identifying exactly who to reach at each target)

### Objective
For every Tier 1 and Tier 2 company, a named list of 3-5 people who could credibly hire you or influence your being hired, enriched and prioritized.

### Actions
1. **For each target, identify:**
   - **Hiring manager** (VP Sales / CRO / Head of GTM / founding GTM operator)
   - **Skip-level** (CEO at Series A-B; CRO/COO at Series C)
   - **Peer in the function** (someone doing a slice of the role today — a senior AE, an ops lead, a GTM eng)
   - **Recruiter** (in-house if they have one; external talent partner otherwise)
   - **Connector path** (someone in your network 1-2 degrees from any of the above)
2. **Enrich.** Use Apollo, LinkedIn Sales Nav, and Clay. Fields: LinkedIn URL, email (work + personal where available), role tenure, last public content, recent activity.
3. **Prioritize within each account:**
   - **Warm path exists →** lead with the warm intro (Stage 5).
   - **No warm path, but strong content overlap →** engage on their content publicly first (Stage 5).
   - **No warm path, no public surface →** cold with an artifact gift (Stage 5).
4. **Maintain the target→contact map in HubSpot** using your existing project's patterns. Associate every person to the company. Note: this is also free practice for Domain 3.

### Tools & artifacts
- Apollo (you have it)
- LinkedIn Sales Navigator
- Clay free tier — use it to practice the craft you're being hired for
- Cowork `sales:account-research` skill

### Metrics to track
- Contacts identified per Tier 1 (target: ≥ 4)
- Warm-path coverage (% of Tier 1 with ≥ 1 warm path)

### What the top 1% does
Treats "warm-path discovery" as a repeatable process, not a lucky accident. LinkedIn alumni search on your most-connected universities/past employers is the single most underused move in executive job-hunting. Within 30 min you will almost always find a second-degree connection to your ICP; the hard part is *asking* for the intro — covered in Stage 5.

---

## Stage 5 — Outreach & Discovery (multi-channel, value-first)

### Objective
Per target company, at least one real conversation with a decision-maker or influencer that either (a) becomes a formal process, (b) produces a specific referral to a formal process, or (c) produces a committed "keep you on my radar" from someone you can re-touch every quarter.

### Actions
1. **Outreach structure (per target):**
   - **Warm intro path:** ask your connector with a 3-sentence "forwardable context" — what you're looking for, why this company, what you'd offer. Make the ask effortless for the connector (one Slack/DM, one-click forward).
   - **Content-engagement path:** thoughtful comment on their content for 2-3 weeks, then DM referencing a specific exchange. Do not DM with "would love to chat."
   - **Cold artifact-gift path:** send a personalized artifact — a competitive teardown, a workflow you built that solves a problem they've posted about, a Loom walking through a play. 3-5 min of video is disproportionately effective for senior outreach.
2. **Message craft (you already have Domain 1 + Domain 8):**
   - **First touch:** relevance signal (why you, why now, why them), offer (a useful artifact or specific observation), ask (small — 20 min, not "pick your brain").
   - **Follow-up 1 (if no response, 5 business days later):** new artifact or new angle; never "just bumping this up."
   - **Follow-up 2 (10 business days later):** a share-and-close; "sharing this in case it's useful, no need to respond."
3. **Discovery call (when you land it):** run it like a sales discovery call against yourself being the product.
   - Their current-state pain (hiring gap? GTM misfit? motion change?)
   - Impact (what does not solving it cost them)
   - Decision process (who else is involved, what's the timeline)
   - Next step (a clear, time-bound follow-up — do not leave a meeting without the next step named)
4. **Post-conversation artifact.** Within 24 hours, send a 1-page "what I heard + what I'd do in the first 90 days" memo. This single act converts interest to offers at a rate that defies most expectations — it signals you operate at a strategic level before you're hired.

### Tools & artifacts
- Gmail + HubSpot for CRM logging
- Loom or Claude-driven video (via `elevenlabs` etc.) for video touches
- Your `gtm-agents` `sales-prospecting/*` skills for sequence design
- Cowork `sales:draft-outreach` skill

### Metrics to track
- Outreach sent per week (target: 10-15 tightly-personalized touches)
- Reply rate (target: 25-40% for warm, 10-20% for cold-with-artifact)
- Conversations booked per week (target: 2-4 at steady state)
- "Process advanced or recycled" per conversation (want: ≥ 60%)

### What the top 1% does
Sends a Loom before the interview offering a teardown of the company's current state, and a 30/60/90. About half of hiring managers skip the rest of the process when they get one of these from someone whose credentials obviously match. The asymmetry is extreme: an hour of your time to make a video vs. 8 hours of interview process avoided. This is also the proof that you operate like a Forward Deployed GTME before the offer.

---

## Stage 6 — Evaluation (interviews + take-home + on-site)

### Objective
Run every process to a "best-in-class" version of itself so that regardless of fit, your reputation with that company compounds for future moves. And — critically — teach to Clay's **published assessment rubric**, because it is the rubric the Intercom / Notion / Ramp / Verkada / Anthropic hiring managers all run implicitly too.

### The three-part assessment Clay publishes (teach to this test)

Clay's blog lays out exactly how they evaluate GTM engineering candidates. The shape is:

**Part A — Business problem investigation.** They hand you a fuzzy problem (e.g., "Our trial-to-paid rate won't budge"). They are evaluating whether you ask the right *first* questions before building anything. Strong candidates ask:

- Who is our ICP?
- What are we missing in their journey?
- Which signals tell us someone is ready to buy or churn?
- What do our most successful customer conversations look like? (work backwards from there)

Answers should explore **both market levers (new intent data) and internal levers (slow SDR-to-AE routing)**. Candidates who only explore one side get screened out. Specificity is the tell — not "I'd look at the funnel" but "I'd pull the last 30 trial cohorts, cut by ICP fit score, and compare their 7/14/30-day activation patterns against converted trials; my hypothesis is the gap is in D3-D7."

**Part B — Systems sketch.** They ask you to turn the insight into a working flow. They are evaluating whether you can:

- Pick good, unique data points to track (rung 2)
- Keep the data clean (rung 1 — don't skip this; this is the stumble point)
- Plug data into a Clay-or-equivalent workflow (rung 3)
- Test, measure results, iterate

The visible signal they want is a mindset of *hypothesis → instrument → measure → iterate*, not *build → launch → hope*.

**Part C — Mini build challenge (take-home).** Actual build, any tool is fair. Example: design and validate a specific set of data points that predict churn. What separates good from weak submissions:

- Explains **assumptions and fallback logic** (e.g., "if the primary enrichment source returns null, I fall back to X because...")
- Addresses **suppression and multi-channel sequencing** (no blast-all emails; no list-bombing)
- Shows how they'll **measure success and iterate** (success criterion stated in advance, not in hindsight)
- Ships a **Loom walkthrough** of the artifact (disproportionately effective — see Stage 5)

**Clay's published red flags (memorize — avoid):**

1. **Tunnel vision** — one solution, no alternatives considered.
2. **Single-channel thinking** — only email, or only ads, or only outbound; no recognition that modern GTM is multi-channel.
3. **Deliverability blindness** — designing outbound without addressing domain warming, suppression, targeting fatigue.
4. **No measurement plan** — proposing a build without stating how success will be verified.

If your take-home contains any of these, you've self-disqualified.

### Actions
1. **Use your own call-prep stack.** For every interview, run `sales:call-prep` and write a 1-page prep doc: interviewer research, expected topics, expected objections, your three highest-leverage questions, your three best examples, the close you'll deploy if asked "do you have any questions."
2. **Interview stages to expect at AI-native companies (approximate):**
   - Recruiter screen → Hiring manager → Skip / peer panel → **Technical / case (structured as A → B → C above at GTME-hiring companies)** → Founder / exec → References + offer.
3. **Take-home strategy, reframed against Clay's rubric:**
   - Scope ruthlessly; ask clarifying questions in writing *before* building. (This is also the behavior they're grading for — candidates who don't ask clarifying questions fail Part A implicitly.)
   - Structure your deliverable around the three parts: *diagnosis → systems sketch → build + measurement plan*. Explicitly.
   - Beat the time-box by *delivering less scope better* rather than *more scope sloppily*.
   - Include a 90-second Loom walkthrough of your artifact. Open the Loom with: "Here's what I was asked, here's how I interpreted the problem, here's what I built and why, here's how I'd measure success and iterate." That is the three-part rubric, in order, on camera.
4. **Assume every company has a "will they raise the bar" question.** For a senior GTM role at an AI-native company, that question is "would this person teach me something about GTM I don't already know?" Every answer should include specific, contrarian, but defensible opinions. "I don't know yet, but here's how I'd find out" is a valid answer; vague motherhood statements are not.
5. **Bring the three Clay cross-model lessons into conversations unprompted:** (a) start in ops, federate later; (b) balance prototypers with implementers; (c) data hygiene is non-negotiable. These are now table-stakes fluency signals for anyone hiring into this function.
6. **Post-interview debrief with yourself.** Same-day, 10 min: what worked, what didn't, what you'd change. Update your prep doc.

### Tools & artifacts
- Cowork `sales:call-prep` and `sales:call-summary` skills
- Granola (you use it) — transcription + notes
- Your event-research pipeline's muscles — you already know how to ingest context quickly
- Your portfolio's three Capstones from Domain 3 — at least one should be tailorable into a take-home answer

### Metrics to track
- Pass-through rate per stage (if < 50% at any one stage, something is systemically off — diagnose)
- Time-to-offer (expect 3-8 weeks at AI-native companies)
- Number of concurrent processes (target: ≥ 3 in late stages when you hit offer — this drives leverage)

### What the top 1% does
Brings a 90-day plan to the on-site that is specific enough that the hiring manager's question shifts from "should we hire you?" to "would you accept if we offered?" This is textbook Challenger: you have taught them something about their own business during the interview process. A strong move at GTME-hiring companies specifically: bring a 30/60/90 that explicitly identifies which maturity rung their current stack is on, what you'd shore up on rung 1 first, and the first three rung-3 plays you'd ship once the foundation is solid. That answer is almost certainly not what other candidates bring.

---

## Stage 7 — Offer Close (multi-process leverage + negotiation)

### Objective
A compensation package that reflects the full-stack role you're filling (not the role they originally wrote), with comp structure and terms that set up years 2-3 for upside.

### Actions
1. **Never negotiate with one offer in hand.** Time-box your processes so that offers land within 2 weeks of each other. This is the hardest operational part of job-hunting and the single most financially material.
2. **Compensation components to negotiate (all of them, not just base):**
   - Base salary
   - Variable / OTE
   - Sign-on bonus (useful for offsetting equity cliff loss from your current role)
   - Equity (amount, strike price, refresh cadence, acceleration on termination)
   - Accelerators and SPIFFs if on a sales comp plan
   - Promotion path + compensation review cycle
   - Quota structure (year 1 ramp, territory definition)
   - Remote / hybrid terms
   - Benefits: PTO, parental leave, equipment budget, learning budget
3. **Use a written "offer summary" document** to evaluate offers side by side. Include: total year-1 comp at plan, upside case, downside case, 4-year equity value at 3 outcome scenarios, non-comp variables.
4. **Negotiation craft.** Run the "Never Split the Difference" / Chris Voss playbook:
   - Anchor high but defensibly
   - Mirror + label emotions to surface unstated objections
   - Use "no-oriented questions" ("would it be ridiculous to consider X?")
   - Get the counterparty to solve your problem ("how am I supposed to take a 20% base cut?")
5. **The letter of acceptance is also the first day of the job.** Set the tone by sending a well-written "here's what I'm excited to do in the first 60 days" note when you accept.

### Tools & artifacts
- Your own comp-comparison model (build in Sheets — simple, 2-hour build)
- Levels.fyi + Pave.com (public comp benchmarks)
- A trusted senior friend or mentor to pressure-test your ask

### Metrics to track
- Total comp delta vs. initial offer (target: 10-25% uplift through negotiation)
- Number of terms improved (not just base — this is where most people leave money)

### What the top 1% does
Brings a quantified, defensible case for the target package grounded in the value they'll deliver in year 1 — not market comp data. "Here's the pipeline I'll build, here's the revenue I'll unlock, here's the comp that makes the math work." Market data is a backstop; value math is the ask.

---

## Stage 8 — Ramp (the first 90 days as the final interview)

### Objective
By day 90, you are visibly the highest-performing hire the company has made this year and the hiring manager is already thinking about where you go next.

### Actions
1. **Day 0-30 — Observe + deliver one visible win.**
   - Meet every stakeholder the role touches (AE team, ops, marketing, product, CS, finance).
   - Ship one small, visible, well-executed thing in weeks 2-3 that matches your strengths (a workflow, a playbook, an analysis). Not the big strategic play — a credibility down-payment.
   - Run your own 30-day diagnostic: where is the operating rhythm strong? where is it weak? what would I change first?
2. **Day 31-60 — Propose + sequence.**
   - Present your diagnostic to your manager. Convert it into 2-3 medium-scoped initiatives for the next 60 days, prioritized.
   - Start working cross-functionally — the Clay JDs' emphasis on "full-funnel fluency" applies from day 1 of the job.
3. **Day 61-90 — Ship the strategic play.**
   - The initiative you proposed in Day 30-60 should ship in this window. Visible, measurable, cross-functional.
   - Request your first formal performance conversation.
   - Set the narrative for year 1: what you'll own, what you won't, what you'll expand into.
4. **Document in public.** If culturally appropriate, your first-90-days writeup (internal or external) becomes the next proof artifact for the next round of your career.

### Metrics to track
- Stakeholder relationships per week (target: 3-5 in weeks 1-3)
- Shipped artifacts by day 30, 60, 90
- Manager feedback loop quality (have you asked, what did you hear)

### What the top 1% does
Treats the first 90 days as a public body of work and a team's onboarding template at once. If you write your 30/60/90 in a way that the company can give to the next hire, your leverage compounds beyond your role.

---

# Part 3 — What's next

With the Clay blog integrated, the remaining iteration passes are:

1. **Fidelity pass on Part 1** — pressure-test domain priorities, depth targets, and the 12-week track design against your actual calendar and constraints. Drop or downshift what doesn't fit. Key open lever: weekly hour budget (see confidence section).
2. **Fidelity pass on Part 2** — red-team the stage definitions, metrics, and differentiators. I'm still certain at least 2 stages have missing contingencies (Stage 5 outreach cadence; Stage 7 multi-process timing). Let's stress-test them.
3. **Cross-map coursework onto the Empire State Events Pipeline build plan** — map each track's weekly work against what you're already building (event-research skill, content skills, pattern-synthesis, project-ideation). The Domain 3 play-pattern table is the connective tissue for this: several Empire State components already map to real Clay-published patterns. This is where the "real world training program" framing earns its keep — every capstone from Part 1 is built on top of Empire State, not next to it.
4. **Second-order build targets from the blog** — the blog names specific GTME team members at Clay itself (Manny, Osman, Spencer, Tommy, Blake, Bruno, Pranav). Their published plays are the highest-resolution public record of what "good" looks like. A later pass: pick 2-3 of those plays, build your own version, publish with a walkthrough. Becomes both portfolio and a conversation-opener into Clay itself.

---

## Confidence on V1.1

- **Role archetype synthesis (Part 0):** 88% (up from 80% in V1). The Clay blog is now integrated; the consultative-seller thesis, three-rung model, and org taxonomy are load-bearing additions. The remaining 12% is that I'm synthesizing across 5 JDs + 1 blog — field-testing with 2-3 actual practitioner conversations would tighten it further.
- **Coursework structure (Part 1):** 78% (up from 75%). Rung mappings and the Domain 3 play-pattern table meaningfully sharpen "what good looks like." Depth targets and 12-week sequencing are still subjective and move once you react.
- **Job-hunt funnel (Part 2):** 78% (up from 70%). Stage 1 named targets and the Stage 6 Clay rubric are the biggest confidence lifts — those are now grounded in Clay's own published material, not inferred. Stages 5 and 7 are still the weakest (contingencies and timing, as called out above).

**The single biggest open variable that would change a lot of this is still your actual weekly hour budget.** The 12-week sprint plan assumes ~16-20 hours/week of directed learning + building, which is aggressive while also holding down your current role. If that number is 8 instead of 18, the whole sequence compresses into a 24-week plan and the emphasis shifts toward Track A (Build) at the expense of Track B (Study).
