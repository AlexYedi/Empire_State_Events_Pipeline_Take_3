# Cross-Map: Empire State Events Pipeline ↔ Full-Stack GTM Roadmap

**Companion to `00_full_stack_gtm_roadmap.md` (V1.1) and `01_gtm_agents_skills_map.md`**
**Date:** 2026-04-20

---

## Headline: the overlap is large, but the framing is the bottleneck

Plain English first:

- Of the 9 coursework domains, **6 are materially covered** by builds you have already shipped or are shipping in Phase 1–2b.
- Of the 8 job-hunt funnel stages, **5 are materially covered** (Stages 1, 3, 4 fully; Stage 2 and 8 partially).
- The **credential gap is narrower than the plan suggests.** The builds are mostly there. What's missing is a measurement layer and the right labels.
- The **framing gap is wider than the plan suggests.** Nothing in the Empire State repo currently calls itself "GTM engineering" or ships with a hypothesis + measurement plan. An interviewer at Clay or Intercom would not recognize these builds as rung-1/2/3 portfolio work — not because they aren't, but because they're framed as "events content pipeline."

**Net:** you are farther along than the roadmap treats you as. The smart move is not to start six new projects. It's to (a) reframe and measure what exists so it reads as GTME portfolio work, and (b) add two net-new small builds that close the specific remaining gaps.

---

## Build inventory (what we're mapping from)

Seven Empire State artifacts count as "builds" for this cross-walk:

| # | Build | Phase | Status |
|---|-------|-------|--------|
| B1 | **event-research skill** — reads pasted invite, writes structured research to 5 Notion DBs + HubSpot via MCP | 1 | Shipped / first real event run complete |
| B2 | **pre-event-content skill** — Sunday "Upcoming Week" post, per-event LinkedIn post, speaker/host DMs, prepared questions | 2 | In progress |
| B3 | **pattern-synthesis skill** — two-thesis LinkedIn post from 2 event briefs | 2 | Shipped (added 2026-04-19) |
| B4 | **post-event-content skill** — screen grabs, decks, recap, documentarian angle | 2 | To be built |
| B5 | **project-ideation skill** — generates 3 project proposals (2 feasible + 1 stretch) from event topics; 6-dim scoring + arch-confidence gate | 2b | In progress |
| B6 | **Notion schema design** — 6 interconnected DBs (Events, People, Companies, Topics, Content Drafts, Project Ideas) with bidirectional relations and Active Kanban + Archive views | 1 | Shipped |
| B7 | **HubSpot write orchestration** — companies → contacts → notes with event-name bodies as the dedup/association layer (workaround for Static Lists unavailable via MCP) | 1 | Shipped |

---

## Matrix A — Builds → Part 1 Coursework Domains

Coverage key: **●** = Full, **◐** = Partial, **○** = Implicit (you're doing it but not labeling it), **—** = Gap.

| Build \\ Domain | 1. GTM Theory | 2. Sales Methods | 3. GTM Eng Craft | 4. Data & Analytics | 5. AI/Agent Systems | 6. Product Fluency | 7. Tooling Stack | 8. AI-Native Customer | 9. Execution Craft |
|---|---|---|---|---|---|---|---|---|---|
| B1 event-research | ○ | — | ● | ◐ | ● | ◐ | ● | ● | ○ |
| B2 pre-event-content | ◐ | ○ | ● | — | ● | ◐ | ◐ | ○ | ○ |
| B3 pattern-synthesis | ● | — | ○ | — | ○ | ◐ | ○ | ● | ○ |
| B4 post-event-content | ◐ | — | ◐ | — | ○ | — | ○ | ◐ | — |
| B5 project-ideation | — | — | ● | ◐ | ● | ● | ◐ | ○ | ● |
| B6 Notion schema | — | — | ● | ● | ◐ | ○ | ● | — | ○ |
| B7 HubSpot orchestration | — | ◐ | ● | ◐ | ◐ | — | ● | — | ○ |
| **Domain coverage summary** | **partial** | **gap-ish** | **full** | **partial** | **full** | **partial** | **full** | **partial** | **partial** |

**Read:**
- **Domain 3 (GTM Engineering Craft), 5 (AI/Agent Systems), 7 (Tooling):** effectively covered right now. This is the credential triad. You are a working GTM engineer today — the builds just don't say so.
- **Domain 1, 6, 9:** partial. These are about *positioning the work*, not doing the work. Small writeups close most of it.
- **Domain 4 (Data & Analytics):** the headline gap. Your builds produce data (Notion entries, HubSpot records) but you're not *measuring the system itself* — no dashboard of "events researched per week," "contacts enriched," "LinkedIn posts published → replies," no instrumentation. This is the Clay rung-1 muscle and it's the one most worth closing.
- **Domain 2 (Sales Methods) and 8 (AI-Native Customer):** gap-ish. Pattern-synthesis and event-research skim Domain 8, but there's no structured ICP research artifact yet. Domain 2 is genuinely orthogonal to the events pipeline — it lives in your day job.

---

## Matrix B — Builds → Part 2 Funnel Stages

| Build \\ Stage | 1. Market Mapping | 2. Positioning | 3. Signal Gen (Portfolio) | 4. Outbound/Warm Intros | 5. Interview Prep | 6. Evaluation | 7. Offer/Close | 8. Pre-start Ramp |
|---|---|---|---|---|---|---|---|---|
| B1 event-research | ● | — | ● | ● | — | ◐ | — | — |
| B2 pre-event-content | ◐ | ◐ | ● | ● | — | ◐ | — | — |
| B3 pattern-synthesis | — | ● | ● | ◐ | — | ◐ | — | — |
| B4 post-event-content | — | ◐ | ● | ◐ | — | — | — | — |
| B5 project-ideation | — | — | ● | — | ○ | ● | — | ○ |
| B6 Notion schema | ● | — | ● | ◐ | — | ● | — | — |
| B7 HubSpot orchestration | ● | — | ● | ● | — | ● | — | — |
| **Stage coverage summary** | **full** | **partial** | **full** | **full** | **gap** | **partial** | **gap** | **gap-ish** |

**Read:**
- **Stage 1 (Market Mapping) and Stage 4 (Outbound/Warm Intros):** fully covered. Every event you research expands your NYC AI/GTM target graph. Every DM you draft is real outbound. This is already a working funnel.
- **Stage 3 (Portfolio):** fully covered **if** the builds are reframed as GTME portfolio pieces rather than "events content." The raw material is there.
- **Stage 6 (Evaluation):** partially covered by B5 project-ideation (forces scoring discipline) and by B6/B7 (prove MCP / multi-system write orchestration). A Clay-style assessment would exercise exactly this muscle.
- **Stages 5, 7, 8:** genuine gaps. Interview prep, offer/close, and pre-start ramp are not what this pipeline is for. That's fine — those belong in separate artifacts.
- **Stage 2 (Positioning):** partially covered by B3 pattern-synthesis (the documentarian angle) and B2 (consistent voice). To get to full, you need to ship the "you-as-the-product" 150-word About + two variant elevators from the skills map.

---

## What this tells you (five high-signal takeaways)

1. **You already have three publishable portfolio pieces hiding inside the events pipeline.** They just aren't labeled as such. Reframe B1 + B6 + B7 as a single writeup titled something like *"Building a small GTM signal layer: how I unified event intelligence across Notion and HubSpot without a middleware"* and you have a rung-1/rung-3 artifact that maps cleanly to Clay's maturity model.
2. **The measurement layer is the single highest-leverage thing to add.** One Streamlit or Hex dashboard pointed at the Notion + HubSpot data, showing "events intake rate, contacts enriched, content drafts published, replies/opens" — closes most of Domain 4, materially strengthens Stage 3 portfolio, and lets you answer "how would you measure this?" in an interview without flinching.
3. **Project-ideation (B5) is already a Clay-style mini-build generator.** A 6-dim rubric with an arch-confidence gate is structurally the same pattern Clay uses to score their own plays. Make the scoring logic itself a writeup and you have Domain 9 (Execution Craft) largely covered.
4. **The documentarian angle (B3, B4) is your Stage 2 positioning work.** It isn't separate from the job hunt — it *is* your positioning proof. Keep shipping pattern-synthesis posts on the cadence rule (max 1/week) and that's your brand building itself.
5. **Stages 5, 7, 8 don't belong in the events pipeline.** Don't try to force them in. Interview prep lives in pre-call briefs (per the skills map). Offer/close lives in the comp matrix. Pre-start ramp is the 30/60/90. Keep them as separate Job Hunt System artifacts.

---

## Reframing moves (small changes, big coverage gains)

Each of these is under a day of work and materially closes a domain or stage.

| Move | Effort | What it closes |
|------|--------|----------------|
| **R1. Writeup: "Event intelligence as a GTM signal layer"** — 6-section brief (problem, ICP analogy, data architecture, write orchestration, measurement plan, what's next) covering B1 + B6 + B7 as a single system. | Half-day | Domain 3 rung-1/rung-3 proof; Stage 3 portfolio asset; Stage 6 assessment rehearsal |
| **R2. Instrumentation dashboard (Streamlit or Hex) over Notion + HubSpot** — KPIs: events researched/week, contacts enriched, content drafts by status, posts published → replies. | 1–2 days | Domain 4 fully; strengthens Stage 3 and Stage 6 |
| **R3. Rewrite the project-ideation skill's rubric as a public Notion doc** with the 6 dimensions, the arch-confidence gate, and an example scored project. | 2–3 hours | Domain 9 (Execution Craft) and Domain 3 capstone proof |
| **R4. Add hypothesis + measurement fields to Content Drafts** (simple: "hypothesis," "metric," "baseline," "result so far"). Populate retroactively for the last 5 drafts. | 1 hour schema + 1 hour backfill | Domain 4 + Stage 6 (directly defangs Clay's red-flag #4) |
| **R5. Publish a "from the field" Stage-3-style writeup** for B3 pattern-synthesis itself — the skill is the portfolio piece. "Here's the pattern detection logic, here's the cadence rule, here's why it works." | Half-day | Stage 2 positioning, Domain 3 craft |

Do R1 and R2 first. They unlock the most coverage per hour.

---

## Net-new builds (don't start these until the reframing is done)

These are not in the current Phase 1–2b plan but close real gaps. Each is a ≤ 1-week build and each maps directly to the capstone 9-play table in the skills map.

| Build | Plays it maps to | Domains / Stages it closes | Suggested order |
|-------|------------------|----------------------------|-----------------|
| **N1. Inbound lead scoring (for your own job-hunt funnel)** — score the people you meet at events (title, company tier, intent signals) and route to DM priority. Literal rung-2/rung-3 play, and it *is* your job-hunt funnel. | Play #1, #3 | Domain 3 rung-2/3; Stage 4 quality; Stage 6 assessment proof | First |
| **N2. Signal digest agent** — pulls across People + Companies + Topics in Notion and emails you a weekly "buying-committee digest" on the top 5 target companies. | Play #3 | Domain 3; Stage 1 depth; Stage 6 assessment proof | Second |
| **N3. Post-event signal capture form (later)** — was in the Phase 3 plan. Defer until N1 and N2 are shipped. | Play #8 (adjacent) | Stage 3 volume | Third, only if volume demands |

**Why these three:** they each exercise a different part of the Clay rubric (scoring, synthesis/orchestration, capture). They each double as "I built this for my own job hunt" stories. And they each take real data that already exists in your Notion.

---

## What NOT to do

- **Do not start over.** The pipeline is working. Restarting forfeits the credibility of having a real, running system.
- **Do not retroactively re-document everything as "GTM engineering."** Reframe three pieces (R1, R3, R5). Let the rest live.
- **Do not ship a sixth content skill before the measurement layer (R2) exists.** More content without measurement is exactly Clay's red flag #4.
- **Do not conflate the events pipeline with the job-hunt funnel.** They overlap heavily on Stage 1 and Stage 4, but the events pipeline is a *system* you're building; the job hunt is a *campaign* you're running. Keep the artifacts in their own folders (already doing this).

---

## Sequenced recommendation for the next two weeks

Week 1:
- Mon–Tue: R1 (GTM signal layer writeup) and R3 (public scoring rubric).
- Wed–Thu: R2 (measurement dashboard) — Streamlit over Notion queries. Keep it minimal: 4 KPIs, 1 chart each.
- Fri: R4 (add hypothesis + metric fields to Content Drafts; backfill 5 prior drafts).

Week 2:
- Mon–Wed: N1 (inbound lead scoring for the job-hunt funnel). This is your first capstone.
- Thu: R5 (pattern-synthesis writeup).
- Fri: publish one "what I've been building" LinkedIn post linking R1 + R2 + N1.

At the end of two weeks you will have: three portfolio writeups, one dashboard, one new capstone build, and a measurable outbound layer. That is a *complete* GTME portfolio. It's also — unusually for a candidate — built on a system that proves itself weekly rather than on snapshot artifacts.

---

## Confidence

- Matrix A coverage ratings: **82%** — a few cells could flex one step either direction, especially Domain 8 (AI-native customer), where "implicit" vs. "partial" is a judgment call based on whether you treat event attendees as an ICP proxy.
- Matrix B coverage ratings: **85%** — Stage 1/3/4 calls are confident. Stage 6 call depends on whether the project-ideation scoring rubric actually reads as assessment-grade to a Clay panel.
- Reframing moves will close the domain/stage gaps listed: **90%** — R1, R2, R3 are the right three and they compound.
- Net-new builds (N1, N2) will read as GTME portfolio work to a senior interviewer: **80%** — contingent on shipping each with a measurement plan from day one.
- Two-week sequence is executable without blowing up Phase 2/2b: **75%** — depends on how much time the job search itself is consuming in parallel. If interview load spikes, R2 slips to week 3 and that's fine.
