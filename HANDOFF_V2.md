# HANDOFF V2 — Personal Full-Stack GTM System Kickoff

> **Context:** The prior session ended early (context exhaustion from many skills/repo files loaded at once). We had worked through a strategic framing conversation but got cut off right at the moment of committing to an approach. Do not reload every skill and every doc eagerly — load on demand as decisions require.

## Who I am and the ambition

I'm Alex. I'm building toward a Clay-tier full-stack GTM engineer role (the "$1M GTMEs" described in Clay's own content). I already have a working, shipped NYC AI/tech events intelligence pipeline — event-research skill + pre-event-content + pattern-synthesis skills, writing to 6 interconnected Notion DBs and HubSpot via MCP, with Apollo enrichment. It's real, not a sketch. The constraint: it's time-bound to IRL events, which caps signal volume and publishing cadence, and my work is currently framed as "events content pipeline" rather than GTM engineering portfolio. I want to take this up several levels so the work product is good enough to land a Clay-tier role.

## Repos and source-of-truth docs (load on demand, not all at once)

All in `alexyedi/empire_state_events_pipeline_take_3`:
- `PROJECT_BRIEF.md` — current state, active projects (gtm-os, eval-harness, scaffold-skill), recent decision log
- `Job Hunt System/00_full_stack_gtm_roadmap.md` — my coursework: 9 domains + 8 funnel stages with Own/Do/Recognize depth targets
- `Job Hunt System/01_gtm_agents_skills_map.md` — skills map, cross-mapped skill surface
- `Job Hunt System/02_cross_map_pipeline_to_roadmap.md` — coverage matrix showing what's covered (Domains 3, 5, 7 full; 1, 6, 9 partial; 4 is the headline gap) and five reframing moves R1–R5 plus three net-new builds N1–N3
- `Job Hunt System/Role_Descriptions/` — Clay JDs I'm targeting
- `STACK_README.md` — my tooling stack
- Also: `alexyedi/alex-agents-skills` (the enterprise-grade skills library — product, cto/architect, marketing/social, analytics, orchestration) and `alexyedi/job-hunt-system`

Development branch across all three repos: `claude/summarize-chat-session-aWoX3`.

## What the last session converged on (treat as decided, do not relitigate unless I flag)

1. **Two missing pieces** to take a level up without building in silence for months:
   - **Always-on signal layer** — social listening, PR monitoring, active listening on a target watchlist of companies + people; decouples content from IRL events, increases volume of high-quality specific material.
   - **Digital hub** — a website as canonical distribution surface (start Framer, graduate to Next.js when pipeline outputs warrant embedding), with LinkedIn as primary amplification.

2. **Split into two parallel projects, different cadences:**
   - **Project A — Signal Pipeline:** iterative, long-running, one durable project with a roadmap of source integrations, data-quality layers, scoring/classification upgrades, and eval harnesses. Pipeline "ships" are internal; outputs feed content + dashboard + job-hunt intelligence. The existing events pipeline is the first completed module, folded in as "event-sourced signals" — not rebuilt.
   - **Project B — Hub:** frontloaded sprint to v1 on Framer in 1–2 weeks using material that already exists (R1/R3/R5 writeups, positioning one-pager, "currently building" page). After v1 goes live, hub becomes a weekly publishing surface with occasional embed swaps as pipeline capabilities come online.
   - Coupling is deliberate and thin. The hub must not block pipeline work and vice versa.

3. **Enterprise-grade, interpreted proportionally:** not Kubernetes-for-one-user. What it actually means here is production-quality *patterns* applied proportionally — data contracts, schema rigor, idempotent pipelines, secrets hygiene, real logging, real evals on LLM-driven parts. Push back if I ever drift toward over-engineering.

4. **9-domain overlay mechanism (approach decided in principle, details TBD):**
   - Hybrid (not a standalone skill file): standing instruction in `CLAUDE.md` + mandatory "Roadmap Mapping" sections in PROJECT_BRIEF and architecture decisions + a `roadmap-overlay.md` reference doc.
   - **Tiebreaker rule (firm):** build merits first. Overlay is a tiebreaker when alternatives are genuinely equivalent, and a gap-flag when we're about to leave a domain cold. Never the primary driver. If you ever catch yourself saying "let's do X because it's Domain 4," push back on yourself.
   - I decided the sequencing: **first develop the strategy and plan, then talk through details not yet discussed, THEN overlay the 9 domains** to see what's covered and to what extent. Gaps in the overlay become my focused "study time" — the rest gets absorbed naturally through the build. Do NOT force build changes to pad domain coverage.

## Still open — the clarifying questions we never got to answer

The prior session asked these and I never answered them. These are the blockers for locking the plan:

### Signal layer scope
1. Starting watchlist — proposed: 7 named Clay-blog companies (Intercom, Canva, Notion, Anthropic, Ramp, Verkada, Rippling) + Clay itself + ~12 named humans from the skills map V1.1. Right size, or wider (YC AI batch, a16z AI portfolio), or narrower?
2. Signal sources — tiered as free/cheap, mid-cost, expensive (Bloomberg). Proposal: start free/cheap + what I already pay for; skip Bloomberg for now. Agree?
3. Podcast/transcript ingestion — include (Listen Notes / Podscribe) or defer? Determines whether we need vector store + RAG from day one.

### Hub
4. Framer (brochure v1) vs. Next.js on Vercel (system, later) — confirm Framer first; spec Next.js as a later slice.
5. Hub jobs to do at v1 — pick 2–3 of: proof gallery, thought-leadership archive, live signal widget/dashboard, explicit conversion CTA.

### Distribution
6. Channels beyond LinkedIn — Substack/email? X? Existing audience anywhere?
7. Publishing cadence — system surfaces candidate posts and I decide (strong recommendation), or auto-publish? Sustainable volume?

### Constraints
8. Budget per month all-in, pre-job. Bands: <$100, $100–300, $300+. Determines about half the tool choices.
9. Social-listening ethics guardrail — no LinkedIn scraping (TOS + credibility risk with targets). Public APIs, RSS, official endpoints only. Confirm this is the rule.

## What I want this session to do, in order

1. **Read** `PROJECT_BRIEF.md` and `Job Hunt System/02_cross_map_pipeline_to_roadmap.md` first. Skim `00_full_stack_gtm_roadmap.md` and `01_gtm_agents_skills_map.md`. Don't load the full roadmap unless needed for a specific decision.
2. **Ask me the open questions above** — but cluster them, propose defaults where you have a real recommendation, and let me answer in bulk. Don't make me re-answer anything already decided above.
3. **Then produce a strategy and plan** covering both Project A (Signal Pipeline roadmap — first 6–8 weeks, priority-ordered, deliverables per week) and Project B (Hub v1 spec + v1.1/v2 evolution). Shape it as separate documents with thin, deliberate coupling.
4. **Surface details we haven't discussed** — things like: Supabase vs. Postgres-on-Vercel for the data spine; n8n vs. Inngest vs. Vercel Workflows (note: `gtm-os` project is already on Vercel Workflow DevKit — may want to converge); Buffer vs. Typefully vs. custom for LinkedIn scheduling; observability choice (PostHog is already available); how the existing Notion DBs integrate with the new Supabase/Postgres spine (replicate, stay on Notion, or migrate); eval harness scope for content generation skills; IP/legal surface for the watchlist and any scraped-ish data.
5. **Only after steps 1–4**, do the 9-domain overlay pass. For each Project A + B deliverable, note which Part 1 domains and Part 2 stages it exercises, at what depth, and which domains remain cold. The output is a short "study gap" list I can use to allocate focused learning time — not changes to the plan.

## The collaboration contract

- Ask as many clarifying questions as you need before committing to architecture. Cluster them so I can answer in one pass.
- Offer recommendations — don't just surface options neutrally. Tell me which one you'd pick and why.
- Call out potential issues — timelines, complexity, scope creep, the "building in silence" failure mode, over-engineering, skill-tree gaming.
- Honest, respectful, not always agreeing. Push back when I'm wrong.
- Tiebreaker rule above is firm. Build merits first.

## Guardrails specific to this project

- **Do not restart the events pipeline.** It's shipped, it's real, it's the first module of Project A.
- **Do not conflate the events pipeline with the job-hunt funnel.** They share Stages 1 and 4 but are different artifacts.
- **Do not ship a sixth content skill before the measurement layer exists** (R2 dashboard). More content without measurement is Clay red-flag #4.
- **No LinkedIn scraping.** Public APIs, RSS, official endpoints only.
- **Respect the active-project list in `PROJECT_BRIEF.md`** (gtm-os, eval-harness, scaffold-skill). If this new personal-GTM system overlaps with gtm-os conceptually (it may), flag the overlap explicitly and propose whether to merge, sequence, or keep parallel.

Start by reading the two docs named in step 1, then come back with the clustered question set from step 2.
