# Research Brief: Data Driven NYC #121

**Date:** Tuesday, April 28, 2026 (evening)
**Location:** 19 W 22nd St, 2nd floor, NYC (Flatiron — FirstMark venue)
**Host companies:** FirstMark Capital + Ramp
**Curator (host):** Matt Turck — General Partner & Managing Director, FirstMark Capital
**Speakers:**
- Alex Levinson — Applied AI, Ramp Labs
- David Yaffe — Co-Founder & CEO, Estuary

---

## The 90-Second Frame

This is **Matt Turck's room** before it's anything else. Turck has run Data Driven NYC for 12 years; the community has 20,000 members and is the largest tech meetup in the country. The roster of past speakers reads like an AI/data hall of fame — CEOs of Snowflake, Databricks, MongoDB, Datadog, Perplexity, Dataiku, Writer, Modal, Synthesia, Ramp, and more. Speaking at DDNYC means Turck has decided your story matters right now.

**The Tuesday lineup is engineered to answer one question with two complementary halves:**

1. **What does shipped agentic infrastructure look like in production?** Alex Levinson at Ramp Labs has the freshest answer in the city — he and the Labs team just published *"How we made Ramp Sheets self-maintaining"* on the Ramp Labs Substack (March 2026). They're running ~1,000 AI-generated monitors (one per 75 lines of code), Datadog-triggered agents, and Ramp Inspect (their internal background coding agent) — fully deployed, not a demo.
2. **What does the data plumbing under those agents need to look like?** David Yaffe at Estuary just raised a **$17M Series A** (October 2025, M13-led, with **FirstMark participating**) for "right-time" data movement — consolidating CDC, streaming, batch, and ETL/ELT into one managed system. Yaffe is a repeat founder (sold Arbor to LiveRamp in 2016, was COO of LiveRamp).

**Inter-event linkage worth carrying into content:**
- **FirstMark invested in Estuary.** This panel is, in part, a portfolio showcase — Turck is hosting his portfolio company on the stage he runs. Same pattern as Wed-day Cube (Nnamdi Okike / 645 Ventures speaking at a panel for a portfolio company). NYC AI/data ecosystem operates on these tightly looped curator-investor-portfolio cycles. **Worth flagging in the Sunday roundup.**
- **Ramp shows up TWICE this week.** Co-hosting Tue, and named in Cube's prior speaker roster. Ramp's $32B valuation, $1B+ ARR, $2.44B total raised, and aggressive AI agent product cadence (Policy Agents, AP agents, Visa-Ramp bill-pay agents) make them the canonical "AI-native finance" story right now.
- **The week's stack walk is now tighter than it was with the old Tue panel.** Tue (data infrastructure: Estuary + Ramp's production agents) sits cleanly under Wed (semantic + observability) and over Mon (talent). The whole week reads as a coherent walk up the agent stack.

---

## Topic 1: The Two Speakers

### 1.1 Alex Levinson — Applied AI, Ramp Labs

**The artifact (just shipped):** *"How we made Ramp Sheets self-maintaining"* — published March 2026 on [ramplabs.substack.com](https://ramplabs.substack.com/p/self-maintaining). The system:

- **~1,000 AI-generated monitors** running in production, one per ~75 lines of code.
- **Two-step agent architecture:** (1) on PR merge, an agent reads the diff and generates monitors instrumenting the new code. (2) When a monitor fires, a Datadog webhook kicks off a *new* agent with the alert context.
- **Ramp Inspect** is the internal background coding agent — spins up a full sandboxed dev environment, makes real API requests, runs tests, reproduces bugs end-to-end against live code.
- Agent puts up a PR to address the root cause if it finds a real issue. **No code merged without engineer review** — but the triage + reproduction work is autonomous.

**Why this is the biggest story Tue:** Most "AI agents in production" claims are demos. Ramp Labs has shipped this. Alex's demo will likely be the latest iteration — could be even more aggressive than the published Substack.

**For Alex Yedi specifically:** Alex Levinson is engineering-leadership profile, not a direct GTM contact. **Value is content, not relationship.** What Levinson shows on stage becomes a perfect data point for Alex's own writing about agent reliability, self-maintaining systems, and where AI infrastructure is actually working in production. Tier 2 contact for direct outreach; Tier 1 for content material.

**Best engagement:** Comment substantively on the Ramp Labs Substack post; reference his demo specifically in any post Alex publishes about Tue.

### 1.2 David Yaffe — Co-Founder & CEO, Estuary

**The artifact:** Estuary is the **"right-time" data platform** — Yaffe's term, deliberate distinction from "real-time." Consolidates CDC (Change Data Capture), streaming, batch, and ETL/ELT pipelines into a single managed system. Pricing predictable; latency tunable per use case.

**Funding (fresh):** **$17M Series A, October 2025**, led by M13 with **FirstMark (Turck's firm) and Operator Partners** participating. This panel is partly an investor showcase.

**Founder background:** **Repeat founder.** Sold **Arbor** to LiveRamp in 2016. Then **COO at LiveRamp.** Now CEO of Estuary. That's the founder profile that:
- Knows enterprise data sales motion cold (LiveRamp was/is enterprise data infrastructure).
- Has the operator network to staff a Series A team quickly.
- Is in *expansion-mode hiring* right now (post-Series A).

**Public thesis post (good content material):** *"Is the Modern Data Stack dying, or turning inside out?"* — Yaffe's framing, on LinkedIn. This is the conversation Tue's audience cares about.

**For Alex Yedi specifically:** **GTM-relevance HIGH.** Estuary is at the exact stage (post-Series A, repeat founder, enterprise-data ICP) where Alex's profile fits — first commercial hire, founding GTM, enterprise AE for data infrastructure buyers. Yaffe knows the LiveRamp/data-infra GTM motion that Bazaarvoice/Curalate sales experience maps to. **Tier 1 contact for direct outreach.** Killer opener: *"Your 'modern data stack turning inside out' frame — Tue panel will pair you with Ramp Labs' production-agent story. The thread between you is that the data layer is now actively serving agents, not just dashboards. Where's the next 6-month wedge for Estuary in that shift — agent-shaped customers buying infra, or BI customers being pulled forward?"*

---

## Topic 2: The Two Host Companies

### 2.1 FirstMark Capital — Hosted by Matt Turck

**Firm overview:** NYC-based early-stage VC. **Iconic portfolio includes Pinterest, Shopify, Airbnb, Riot Games.** Active AI/ML/Data investing — current portfolio includes **Dataiku, Synthesia, ClickHouse, Cockroach Labs, Ada, Pigment, Gradium, Daytona, Estuary** (Tue's speaker company).

**Matt Turck — the central node:**
- General Partner & Managing Director, FirstMark.
- Has run **Data Driven NYC for 12 years**. 20,000-member community. **The largest tech meetup in the country.**
- Hosts the **MAD Podcast** (Machine Learning, AI, Data) — long-form interviews with sector leaders. Best known for the **MAD Landscape** (annual map of the AI/ML/Data ecosystem — referenced industry-wide).
- All DDNYC videos archived on FirstMark's site + YouTube channel — 12 years of consistent output.

**Why Turck matters for Alex:** Turck is **TIER 1 — alongside Yeung, Borthwick, and Stratford** — as one of the small set of NYC scene gatekeepers. Getting on his radar is high-leverage:
- His MAD Landscape has been referenced in every AI/ML/Data investor deck for years.
- His podcast amplifies guests to a huge audience.
- His Data Driven NYC events screen for serious operators in the space.
- FirstMark portfolio access is the indirect prize (warm intro to Estuary, Dataiku, Synthesia, etc.).

**Engagement vector:** Don't pitch him on a job (he won't bite). Approach him with a **specific MAD Podcast episode reference + a sharp follow-up question.** Mention what Alex is building (events pipeline / documentarian content) — adjacent to his own community-curation work, makes Alex memorable. Substantive comment on his next LinkedIn post about the panel doubles as public-track engagement.

### 2.2 Ramp — Co-Host

**The state of play:**
- **$32B valuation** as of November 17, 2025.
- **$2.44B total raised** over 14 rounds, 64 investors.
- **$1B+ annualized revenue.**
- **50,000+ businesses** as customers.
- AI-native finance platform: corporate cards, expense, bill pay, procurement, accounting automation, treasury.
- **Lightspeed led the most recent $300M round** with explicit thesis: *"Building the Intelligence Layer for Finance."*

**AI agents shipped (so far):**
- **Policy Agents** — expense review.
- **AP agents** — auto-code transactions, detect fraud, route approvals, schedule payments.
- **Controller agents** — built for finance roles, fully integrated with customer financial data, cite their work.
- **Visa-Ramp partnership** (announced 2026) — joint AI agents automating corporate bill pay.

**Ramp Labs is the AI research arm** — Alex Levinson's home base. Their Substack publishes building-in-public engineering writeups (the self-maintaining sheets piece is the most recent).

**For Alex Yedi specifically:** Ramp at $32B is too late-stage for first-commercial-hire seats — those happened years ago. But Ramp is **massively hiring** at every other level (enterprise AEs, vertical product, partner channel, customer success leadership). Alex's profile fits "Strategic Account Director" or "Enterprise Account Executive" at the upper end of their hiring mix. **Tier 2 for direct talent pipeline; Tier 1 for content / market context.**

---

## Topic 3: Tailwinds — Why Tuesday's Pairing Is the Right Pairing Right Now

The two talks together describe **what production agentic infrastructure actually requires**, from two different layers:

- **The agent layer (Ramp Labs):** Production agents now ship in real codebases (Ramp Sheets), instrument themselves (1,000 monitors, one per 75 LOC), and act on alerts (Datadog → agent → PR). The "agents in production" conversation has graduated from demos to deployed, observable, measurable systems.
- **The data layer (Estuary):** Right-time data movement is the unsexy infrastructure that every production agent eventually needs. CDC + streaming + batch consolidation removes a category of bugs ("which copy of the data is the agent reading?") that breaks demos at scale.

**The 2026 macro:**
- The "modern data stack" (Fivetran/Snowflake/dbt/Looker era) is being inverted — Yaffe's framing — by AI agents that need fewer-but-richer data moves with tunable latency.
- AI agents in production need **observability, instrumentation, and right-time data** in equal measure. The teams shipping (Ramp, Brex, etc.) are figuring this out empirically.
- **The week's full stack visible across 5 events:**
  - Talent (Mon) → Data infra (Tue) → Semantic foundation (Wed-day) → Observability/eval (Wed-eve) → Coordination (Thu)

This is the cleanest week of stack-walking events Alex has had in his calendar so far. **The Sunday roundup writes itself.**

---

## Topic 4: Top Questions Worth Asking in the Room

Ranked by richness of expected answer.

### For Alex Levinson (Ramp Labs)
1. *"You shipped self-maintaining Ramp Sheets with 1,000 monitors and Datadog-triggered agents. What's the failure mode you watch for most carefully — and is it the agents being too aggressive (false-positive PRs) or too cautious (missing real issues)?"* (Forces a real ops answer; reveals whether the production deployment is mature or fragile.)
2. *"Ramp Inspect spins up sandboxed dev environments per agent. What's the cost-per-bug-investigation now, and does the math work compared to a human engineer triaging the same alert?"* (Unit-economics question; treats him as an operator. The answer tells you how serious Ramp Labs is about scaling this.)

### For David Yaffe (Estuary)
3. *"Your 'modern data stack turning inside out' frame: which incumbent (Fivetran? Confluent? Airbyte?) is most exposed to right-time replacing real-time as the dominant pattern? And what's the 12-month indicator we'd see if you're right?"* (Makes him commit to a competitive call; the indicator is the content-worthy data point.)
4. *"You came from LiveRamp / Arbor — enterprise data infrastructure GTM is in your bones. What's structurally different about selling Estuary into AI-shaped buyers vs. selling LiveRamp into ad-tech buyers?"* (GTM-mechanics question, plays to his repeat-founder authority. Best follow-up to surface hiring needs.)

### For Matt Turck (Host)
5. *"You've been running DDNYC for 12 years. In 2014 the room argued about Hadoop vs. Spark; in 2026 it's arguing about agent reliability and data foundations. What's the equivalent of 'we underestimated the cloud' that we'll be saying about this current era of AI in 2030?"* (Long-arc question; treats him as the historian he is. His answer is content gold.)
6. *"The MAD Landscape used to fit on one slide. Now it's a wall poster. What's about to consolidate fastest in the AI/ML/Data stack — and what category that doesn't exist yet shows up on the 2027 map?"* (Forces him into specific predictions; resonates with his MAD Landscape brand.)

### Group / room
7. *"For both panelists: where's the most interesting handoff between the data layer and the agent layer that nobody is building well right now? Specifically — what would you want a startup to ship in the next 12 months that would make your jobs easier?"* (Group question that forces them to point at the gap. Anyone listening with a build idea takes it home as inspiration.)

---

## Topic 5: Documentarian Angle (for Content)

The strongest angles for Alex's audience — ranked by sharpness.

### Angle A (sharpest): "The 'AI agents in production' conversation graduated from demos to deployed this year. Tonight's panel is the proof."

**The play:** Ramp Labs' self-maintaining Sheets system — 1,000 monitors, Datadog-triggered agents, automated PR creation — is the freshest concrete example of agentic infrastructure shipped in production at a $32B-valued company. Pair with Estuary's Series A bet on right-time data as the data layer those agents need. **The panel is what 2026's "agents in production" look like operationally**, not architecturally.

**Hook:** *"A year ago, every 'AI agent in production' demo was a demo. Tonight at Data Driven NYC, Alex Levinson at Ramp Labs is showing 1,000 monitors running across a real codebase — Datadog-triggered agents writing PRs, Ramp Inspect sandboxes reproducing bugs end-to-end. Paired with David Yaffe at Estuary, who just raised $17M from M13 + FirstMark for the data plumbing this kind of system needs. The 'agents in production' conversation graduated this year. Here's what the transition actually looks like."*

**Why it works:** Specific, observable, names-the-shift, anchored in real production deployments rather than vibes. Documentarian voice (analyst). Best content angle for Tue specifically.

### Angle B: "Matt Turck has run NYC's largest data meetup for 12 years. The roster tells you what's about to be true."

**The play:** DDNYC's speaker history is a leading indicator of what becomes important in AI/ML/Data — Snowflake, Databricks, Datadog, Perplexity, Writer, Modal all spoke before they were obvious. Tuesday's lineup is two more bets: Ramp Labs (production agentic infrastructure) and Estuary (right-time data). Both could be obvious in 18 months.

**Hook:** *"Matt Turck has run Data Driven NYC for 12 years. The speakers at DDNYC are usually obvious 18 months later. Tonight: Ramp Labs on shipped agentic infrastructure, Estuary on right-time data. If the pattern holds, both are about to be obvious. Here's what to watch for."*

**Why it works:** Long-arc framing, treats Turck's curation as signal (which is what insiders treat it as). Useful for VC/operator audiences who already know DDNYC.

### Angle C: "The week walks the agent stack."

**The play:** The full-week observation. Mon = talent. **Tue = data infrastructure (this event).** Wed-day = semantic foundation. Wed-eve = observability/eval. Thu = coordination. **Five events, five layers of the stack agents need to actually work in production.** This is the Sunday roundup post.

**Hook:** *"NYC AI/tech this week walks the entire stack agents need to actually work in production — talent, data infrastructure, semantic foundations, observability, coordination. Five events, five layers, all in one week. Here's what each one tells you about where 2026 is heading."*

**Why it works:** Best for Sunday roundup. References this Tue panel as the "data infrastructure layer" of the stack. The other 4 events fill in the rest.

### Cross-event observation

**FirstMark + 645 Ventures + Betaworks all show up across Alex's week as both event hosts AND investors in companies on stage.** The NYC AI/data ecosystem operates on tight investor-curator-portfolio loops. **Worth a 1-line callout in the Sunday roundup; could be its own standalone post on "the NYC AI scene's gatekeeper structure."**

---

## Sources

**Matt Turck / FirstMark / Data Driven NYC:**
- [Matt Turck — personal site](https://www.mattturck.com/)
- [Matt Turck — FirstMark profile](https://firstmark.com/team/matt-turck/)
- [Data Driven NYC — YouTube channel (12 years of archives)](https://www.youtube.com/c/DataDrivenNYC)
- [The MAD Podcast with Matt Turck](https://www.youtube.com/c/DataDrivenNYC)
- [FirstMark Capital — Wikipedia](https://en.wikipedia.org/wiki/FirstMark_Capital)
- [Matt Turck on Twitter/X](https://x.com/mattturck)
- [Data Driven NYC #121 — Luma](https://luma.com/ddnyc121)

**Alex Levinson / Ramp Labs:**
- [How we made Ramp Sheets self-maintaining — Ramp Labs Substack, March 2026](https://ramplabs.substack.com/p/self-maintaining)
- [Alex Levinson — LinkedIn (Applied AI at Ramp)](https://www.linkedin.com/in/alex-levinson/)
- [Ramp Labs](https://labs.ramp.com/)
- [Ramp Labs on X](https://x.com/RampLabs)

**David Yaffe / Estuary:**
- [Estuary Raises $17M Series A — Estuary blog (Oct 2025)](https://estuary.dev/blog/estuary-raises-17m-series-a-right-time-data)
- [Estuary — About](https://estuary.dev/about/)
- [Estuary — Right-Time Data Platform homepage](https://estuary.dev/)
- [David Yaffe — "Is the Modern Data Stack dying, or turning inside out?" LinkedIn post](https://www.linkedin.com/posts/davidyaffe_is-the-modern-data-stack-dying-or-turning-activity-7166445335387578368-1W77)
- [David Yaffe author page — Estuary](https://estuary.dev/author/dave/)

**Ramp (broader context):**
- [Ramp homepage](https://ramp.com/)
- [Ramp raises $500M to rush AI — Payments Dive](https://www.paymentsdive.com/news/ramp-raises-500m-to-rush-ai/756360/)
- [Why We Led Ramp's $300M Round — Lightspeed](https://lsvp.com/stories/why-we-led-ramps-300m-round-building-the-intelligence-layer-for-finance/)
- [Visa and Ramp Develop AI Agents for Corporate Bill Pay — PYMNTS](https://www.pymnts.com/news/b2b-payments/2026/visa-and-ramp-develop-ai-agents-for-corporate-bill-pay/)
- [How Ramp is deploying agentic AI to help contain corporate costs — Fast Company](https://www.fastcompany.com/91502967/ramp-most-innovative-companies-2026)
- [Ramp Debuts AI Agents Designed for Company Controllers — PYMNTS](https://www.pymnts.com/artificial-intelligence-2/2025/ramp-debuts-ai-agents-designed-for-company-controllers/)
- [Ramp Business Breakdown — Contrary Research](https://research.contrary.com/company/ramp)

---

*Brief compiled April 26, 2026 (T-2) for pre-event content generation. Replaces previously-researched 'Software Is the New Media' panel that Alex is no longer attending.*
