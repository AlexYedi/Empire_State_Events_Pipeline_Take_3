# Clay / Pocus / Common Room — Play Pattern Cheat Sheet

**Purpose:** Reference doc for Phase 0 signal discovery. What "a play" actually is in Clay-speak, what modeling looks like at the rung-2 level, and how the three reference companies (Clay, Pocus, Common Room) each decompose a signal → attribute → score → activation.

**Not:** a build spec. This is a vocabulary doc. We'll use it to make Phase 0 decisions; we won't copy any of it wholesale.

**Status:** V0, 2026-04-21. Sourced from Clay's public GTM-engineering blog, Common Room and Pocus public playbook pages, the gtm-agents skills catalog, and the search results captured during Phase 0 kickoff. Treat it as a living doc — add examples as we study more.

---

## The three rungs, with the work each one actually involves

Clay's blog makes one taxonomic claim that's non-negotiable and it maps cleanly to how we should sequence Phase 0 → Phase 1 → Phase 2:

| Rung | What it is | Work at this rung | What "done" looks like |
|---|---|---|---|
| 1. Data foundation | Clean, deduped, trustworthy records. Enrichment jobs, schema audits, merge-and-purge, ownership rules. | Entity identity keys, source provenance, dedup rules, freshness TTLs, schema contracts, completeness scoring, suppression lists. | You can answer "where did this record come from, when was it last verified, and what's missing?" for any entity in the system. |
| 2. Data modeling | Unique data points that *predict* something actionable. Propensity scores, ICP attribute stacks, AI-data points. | Attribute engineering from raw signals, scoring logic, segmentation, AI-derived fields, suppression as an output. | You can answer "what *makes* this person/company worth reaching out to, right now?" with a defensible attribute-level reason. |
| 3. Data activation | Unique data points deployed in revenue-generating workflows. Signal digests, intelligent routing, transcript → CRM, VIP invites. | Ship ONE narrow play with a measurement plan. Don't start here. | A measurable outcome traceable to a modeled signal. |

**The quote to keep in front of you:** "Most companies stumble on the first rung by either trying fancy campaigns on incomplete data or wasting 80% of their time on data hygiene, leaving only 20% for strategic work." Clay's pitch is that their tooling buys you the time back. Ours is a one-user system — so the rule is *don't try to buy time back, just design the hygiene proportionally the first time.*

---

## What "a play" actually is (Clay / Pocus / Common Room — same shape, different vocabulary)

Every play these companies publish follows the same anatomy. If you can't fill in all five boxes, it's not a play — it's a wish.

| Box | Clay says | Pocus says | Common Room says |
|---|---|---|---|
| 1. **Trigger** (the raw signal) | Job change, funding event, website visit, tech-stack change, hiring signal | Product-usage event: seats used, feature used, workspace created | Community activity: Slack mention, GitHub star, pricing-page view, competitor mention |
| 2. **Qualifier** (ICP / fit gate) | Firmographic + technographic filter: right industry, right size, right stack | ICP fit attribute: ARR potential, segment | Account-level fit + person-level role (buying committee) |
| 3. **Derived attribute** (the modeled value) | AI-data columns: "is this company AI-native?", visit-pattern phase (research / eval / decision) | Product-Qualified Account (PQA) score | "Intent keyword strength" composite; role-weighted community score |
| 4. **Suppression** (who to exclude) | Existing customers, active opps, competitors, recent-touch cap | Already-contacted accounts, out-of-segment | Opt-outs, bots, employees, existing customers |
| 5. **Activation** (what you actually do) | Slack digest, personalized outreach, inbound routing, auto-assignment | Warm-outbound sequence from rep, expansion nudge | Alert to rep, auto-tag as PQL, enroll in sequence |

**Alex-specific translation for the job-hunt funnel.** The same shape works with different content:

- **Trigger:** "Target company posted a senior GTME / Revenue Ops / Founding-Growth role." "Named operator published a LinkedIn post or podcast on rung-2 / rung-3 topics." "Target company shipped a product that changed their GTM surface."
- **Qualifier:** "Company is on my T1 watchlist AND is AI-native AND is hiring in GTM functions."
- **Derived attribute:** "GTME-activity score" = weighted sum of (hiring in GTM roles in last 30d) + (exec public POV in last 30d) + (product launch in last 60d) + (capital event in last 90d).
- **Suppression:** current employer. Personal contacts who aren't targets. People who've explicitly said no. Anyone currently in a GKY deal cycle.
- **Activation:** ONE of — (a) draft a field-note LinkedIn post referencing the signal, (b) DM the operator with a specific observation, (c) apply with a tailored cover mentioning the signal, (d) do nothing and add to weekly digest. Starts at (a) and (d) only in Phase 2.

That translation is the whole point of Phase 0 — to figure out which triggers are actually available to us, which ones predict something worth doing, and what "worth doing" means for a job-hunt funnel (as opposed to a sales funnel).

---

## The "unique data points" / "GTM alpha" frame — what it means concretely

Clay's blog thesis: GTM tactics have commoditized. The edge is **unique data + differentiated plays**. The canonical example is narrow enough to rehearse:

> "You should spend resources targeting NYC cafes with $10–20 entrees who just joined DoorDash — and help you reach them tomorrow, not next quarter."

Break that apart:
- **Unique data point:** DoorDash-signup event joined to avg-entree-price — neither is exotic individually; the *join* is the alpha.
- **Segmentation narrow enough to be defensible:** NYC, $10–20 range, recent DoorDash signup. Three filters; maybe 200 accounts; actionable in a week.
- **Speed:** "tomorrow, not next quarter." The signal has a half-life and the play is engineered for that half-life.

**What this looks like in our world:**
- *Commoditized signal:* "Company X is an AI-native startup in NYC." Every GTME candidate can say that.
- *Unique data point we could build:* "Company X posted ≥2 GTME-adjacent roles in the last 30 days, AND their most-recent product release explicitly references agentic architectures, AND a named operator from my skills-map list has posted publicly about them in the last 14 days." Three joins; probably 3–8 companies at any time; acts on a narrow window.

The Phase 0 question is: *what joins are available to us, from free/cheap data, that produce similar-shape narrow-and-timely segments?* We don't know yet. That's the point of Phase 0.

---

## AI-data points — the specific modeling lesson

Clay's own scoring columns (from public case studies and their docs) include:
- `recent_website_visits` — raw
- `pages_viewed` with weight on pricing / demo pages — derived
- `content_downloads` — raw
- AI-column: `visit_pattern_phase` ∈ {research, evaluation, decision} — AI-derived from visit sequence

The lesson is the last one. An LLM turns a sequence of raw events into a categorical derived attribute that's *cheaper to act on* than the raw sequence. That pattern is what Clay means by "AI-data points."

**Translation for us:** we already have raw events (every event Alex attended, every person researched, every topic populated). A V1 AI-data point could be:
- `topic_maturity_phase` ∈ {nascent, gaining_traction, consensus, contested, stale} — derived from the Current Events blocks we've accumulated per topic.
- `person_gtm_proximity` ∈ {core_gtme, gtm_adjacent, engineering_leader, not_gtm} — derived from their role, recent activity, and named-company context.
- `company_ai_native_confidence` ∈ {high, mixed, low} — derived from website language, funding investors, product surface.

Each of those is cheap to produce at our scale and load-bearing for the "worth writing about / reaching out to" decision. All three should be modeled as LLM-scored columns with a small golden set (eval harness territory) rather than hand-maintained tags.

---

## Pocus's most useful takeaway: playbooks beat scores, and fewer signals beat more

Direct quote paraphrased from Pocus's public playbook blog: *"While scores compose many different attributes into an overall score, Playbooks are driven by specific attributes or signals and are more effective in driving at a particular goal than a score, with the specificity of why a lead or account qualifies helping sales teams understand how, when, and with what message to reach out."*

They also warn: *"Be wary of overwhelming sales reps with too many metrics, and prioritize carefully."*

**Translation:** one monolithic "GTME-activity score" is less useful than three named plays with 3–5 attributes each. Each play tells you *why* this person/company is worth action and *what kind of action*. A generic score tells you neither.

**Phase 2 implication:** when we get to the first scored play, don't build a 15-attribute composite. Build 3 named plays (e.g., "hiring-window play," "public-POV play," "product-release play"), each with ≤5 attributes, each with its own activation.

---

## Common Room's most useful takeaway: the suppression list IS the deliverable

Common Room's playbooks treat the suppression list as a first-class output, not a leftover. A play is defined as much by who it *excludes* as who it includes.

**Translation for us:** the suppression list needs to exist before any scoring does. Minimum contents:
- Current employer (GKY Industries).
- Anyone in an active GKY sales cycle.
- Personal contacts who aren't professional targets.
- Anyone who's explicitly said "not right now" or gone cold.
- Anyone already in-flight on a specific job-hunt activation (don't double-DM).

The suppression list is a Tier-1 hygiene artifact (see `02_hygiene_tier_1_spec.md`). It doesn't wait for scoring; it enables scoring.

---

## What this cheat sheet buys us for Phase 0

1. **A vocabulary** — "trigger / qualifier / derived attribute / suppression / activation" is the anatomy we'll use when we look at the existing Notion data and try to name what signals are hiding in it.
2. **A discipline** — we won't jump to activation. We'll stop at modeling (rung 2) until we have foundation and modeling both defensible.
3. **A scope cap** — max 3 named plays at Phase 2, each with ≤5 attributes. No monolithic score.
4. **A hygiene-first posture** — suppression list and identity resolution before any scoring.
5. **A translation** — from "sales play" language (the source material) to "job-hunt funnel" language (our actual use case). This is the bit no reference doc gives us; we have to build it.

---

## Open questions this doc does NOT answer

Flagging these so we don't pretend they're resolved:

1. **Which triggers are actually available from free/cheap data?** TBD in Phase 0 — signal discovery method doc.
2. **What's the half-life of each trigger type we'd use?** Unknown. Needs empirical check against the data we already have in Notion.
3. **How do we avoid "skill-tree gaming" — building sophisticated modeling on signals that don't actually predict anything for our specific goal?** Answer: let the existing data speak first. Signal discovery doc treats this as the core question.
4. **How does this interact with the events pipeline's existing Success Signals + Retro loop?** The event-research skill already produces signal-outcomes-per-event data. That's probably our best training set for what predicts "worth writing about / worth reaching out on." Phase 0 should mine it.

---

## Sources

These were the primary source pages for this cheat sheet. Some blocked WebFetch — the substance came from WebSearch summaries, which are directionally reliable but less citable. Fetch them manually if you want the full text before an interview.

- [The Rise of the GTM Engineer — Clay blog](https://www.clay.com/blog/gtm-engineering) — the three-rung model and GTM alpha concept
- [Playbooks vs. Lead Scoring — Pocus blog](https://www.pocus.com/blog/playbooks-vs-lead-scoring) — specificity over composite scores
- [Product-Led Sales playbook examples — Pocus blog](https://www.pocus.com/blog/product-led-sales-playbook-examples) — PQA score anatomy
- [Find buyer intent keywords — Common Room playbook](https://www.commonroom.io/playbooks/alert-keywords-topics-intent/) — keyword-triggered plays
- [Serve up person-level ABM intent data — Common Room playbook](https://www.commonroom.io/playbooks/serve-up-person-level-abm-intent-data-to-sales/) — person-level signal anatomy
- [Clay Lead Scoring — Octave](https://www.octavehq.com/post/clay-lead-scoring-fit-intent-models) — fit + intent scoring structure
- [Clay Intent Signals — Reply.io](https://reply.io/blog/clay-intent-signals/) — intent-signal catalog

Supporting material already in your stack:
- `gtm-agents/plugins/data-signal-enrichment/skills/signal-scoring/SKILL.md` — read this; it's the internal version of this doc
- `gtm-agents/plugins/data-signal-enrichment/skills/suppression-logic/SKILL.md` — read this before building the suppression list
- `gtm-agents/plugins/intent-signal-orchestration/skills/outbound-plays/SKILL.md` — play anatomy from a different angle
- `gtm-agents/plugins/data-enrichment-master/skills/firmographic-analysis/SKILL.md` — the fit-side vocabulary
