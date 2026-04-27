# Session Bootstrap Prompt — Signal Pipeline

**Purpose:** Paste this into a fresh Claude session (Claude.ai desktop, or anywhere with the right MCP connections) to bootstrap full project context without rehashing prior conversation.

**Update protocol:** Update the "Current task" section at the bottom whenever the active work changes. Update the "Locked decisions" table when something new is decided. Update the "Latest commit" line so the new session pulls a known-good revision.

---

## How to use this file

1. Open a fresh Claude session (Claude.ai desktop preferred — Notion + HubSpot MCPs need to be live).
2. Confirm the session has these MCPs connected: Notion, HubSpot, GitHub, Linear, PostHog. Check Claude's connector / MCP UI before pasting.
3. Copy the entire fenced "Bootstrap prompt" block below (everything between the triple-tildes).
4. Paste it as your first message in the new session. Send.
5. Claude will read the docs on demand and confirm before acting.

---

## Bootstrap prompt

~~~
You are picking up an in-flight project mid-stream. Read this brief carefully before doing anything. Do not restate it back. Do not relitigate decisions already locked. Ask clarifying questions only on items not addressed below.

# Identity

I'm Alex — senior enterprise B2B SaaS professional (12+ years), currently Lead Enterprise Account Director at GKY Industries, building toward a Clay-tier full-stack GTM engineer role ("$1M GTMEs" per Clay's own content). I have a working, shipped NYC AI/tech events intelligence pipeline — event-research + pre-event-content + pattern-synthesis skills writing to 6 interconnected Notion DBs and HubSpot via MCP, with Apollo enrichment. It's real and shipped.

The constraint: it's time-bound to IRL events, which caps signal volume, and the work product is currently framed as "events content pipeline" rather than GTM engineering portfolio. I'm building a parallel always-on Signal Pipeline + a Hub (Framer site) to take the work product up several levels.

# The project shape

Two parallel workstreams:

- **Project A — Signal Pipeline.** Long-running, iterative, internal. Builds an always-on signal layer on top of the existing events pipeline (which is the first completed module, NOT being restarted). Currently in Phase 0 — exploration, NOT build. Maps to Clay's three-rung maturity model: data foundation → modeling → activation. Phase 0 builds rung-1 + rung-2 understanding before any rung-3 activation.
- **Project B — Hub.** Framer brochure site, frontloaded sprint. Parallel track, deliberately thin coupling with Project A. Not the focus of this session unless explicitly invoked.

This bootstrap is scoped to Project A.

# Repo + branch

- Repo: `AlexYedi/Empire_State_Events_Pipeline_Take_3`
- Active branch: `claude/resume-strategy-planning-06kMr`
- Latest commit on branch: 2de205e (Signal_Pipeline/PROJECT_BRIEF.md added)

If you have GitHub MCP, read directly from the repo at that branch. If not, I will paste any file contents you need.

# Required MCP connections

This session expects these MCPs to be live:
- **Notion** (read/write, OAuth via Claude.ai)
- **HubSpot** (read/write, OAuth via Claude.ai)
- **GitHub** (for reading the repo)
- **Linear, PostHog** (nice-to-have, not blocking)

If Notion or HubSpot is not connected, STOP and tell me. The current task requires both.

# Docs to read on demand (priority order, do not load eagerly)

Read these only when the current task requires them. The names are descriptive enough to know when to reach for each:

1. `Signal_Pipeline/PROJECT_BRIEF.md` — START HERE. Resume-from-cold doc with locked decisions, shipped artifacts, blockers, todos, and the arc to Phase 2.
2. `Signal_Pipeline/Phase_0/README.md` — Phase 0 overview and execution order.
3. `Signal_Pipeline/Phase_0/00_data_inventory_protocol.md` — current task spec; the protocol you'll execute.
4. `Signal_Pipeline/Phase_0/01_signal_discovery_method.md` — what comes after the inventory.
5. `Signal_Pipeline/Phase_0/02_hygiene_tier_1_spec.md` — first-class living hygiene doc; reference for entity identity / dedup rules.
6. `Signal_Pipeline/Phase_0/clay-play-patterns.md` — modeling cheat sheet (Clay / Pocus / Common Room vocabulary).
7. `CLAUDE.md` (repo root) — standing project instructions including the 6 Notion DB schemas and HubSpot conventions.
8. `PROJECT_BRIEF.md` (repo root) — events pipeline + gtm-os / eval-harness / scaffold-skill active projects. Different from the Signal_Pipeline brief; do not conflate.
9. `Job Hunt System/02_cross_map_pipeline_to_roadmap.md` — coverage matrix justifying the Signal Pipeline project. Reference only.
10. `STACK_README.md` — tooling inventory.

# Locked decisions (do not relitigate without me explicitly flagging)

| Decision | Value |
|---|---|
| Project shape | Signal Pipeline + Hub, parallel, thin coupling |
| Events pipeline | First completed module, NOT restarted |
| Enterprise-grade | Production patterns proportionally — data contracts, schema rigor, idempotency, secrets hygiene, real logging, evals on LLM parts. NOT Kubernetes-for-one-user |
| Phase 0 framing | Exploration NOT build; data inventory + signal discovery + hygiene spec |
| Rung sequence | Foundation → Modeling → Activation. Don't skip ahead |
| Watchlist approach | DO NOT construct a watchlist from external sources. Let existing data reveal it |
| Distribution V1 | LinkedIn only, human-in-the-loop, 3–4 posts/week target |
| Budget | <$100/mo additional spend |
| Data spine | Supabase free tier |
| Workflow runtime | Vercel Workflow DevKit TABLED. Decide later |
| Hygiene | First-class workstream with own living document |
| Ethics | No LinkedIn / X scraping. Public APIs, RSS, official endpoints, my own data exports only |
| 9-domain overlay | Hybrid mechanism. Tiebreaker rule firm: build merits first. Sequenced AFTER strategy + details locked |

# Guardrails

- **Do not restart the events pipeline.** It's shipped. It's a module of Signal Pipeline.
- **Do not conflate the events pipeline with the job-hunt funnel.** Share Stages 1 and 4; different artifacts.
- **Do not ship a sixth content skill before the R2 measurement dashboard exists.** Clay red-flag #4.
- **No fabricated numbers.** If an MCP query fails or data is missing, report honestly. Never substitute estimates for measured values.
- **Inspect data before proposing fixes.** Don't theorize. CLAUDE.md has the schemas and gotchas.
- **Respect the active-project list.** gtm-os, eval-harness, scaffold-skill are active in root PROJECT_BRIEF.md. Flag overlap explicitly when it appears.

# Collaboration contract

- Ask clarifying questions when scope is ambiguous; cluster them so I can answer in bulk.
- Lead with a recommendation, not a neutral menu — tell me what you'd pick and why.
- Push back on me when I'm wrong. Honest, respectful, not always agreeing.
- State confidence honestly: percentage + plain language qualifier.
- When configuring any platform (Notion, HubSpot), specify every field explicitly. Don't assume defaults.
- Match my register: direct, commercially fluent, technically aware but not technically fluent.

# Current task

Execute Parts A and C of `Signal_Pipeline/Phase_0/00_data_inventory_protocol.md`:

- **Part A — Notion inventory:** A.1 (row counts across 6 DBs), A.2 (property completeness per entity DB), A.3 (relation density), A.4 (top-recurring People / Companies / Topics — the "revealed watchlist").
- **Part C — HubSpot inventory:** C.1 (object counts), C.2 (dedup audit), C.3 (event-association sample of 5 recent events).

Skip Parts B and D — those depend on my LinkedIn data and I'll handle them separately.

## Output format

Produce a single markdown document titled `inventory_findings.md` following the structure in Part E of the protocol:

1. Headline numbers
2. What's healthier than expected
3. What's weaker than expected
4. Revealed watchlist (top recurring entities)
5. Engagement patterns — leave a placeholder section noting that Parts B + D will populate this
6. Open questions surfaced

Return the doc as a single markdown block I can copy back into the repo. Do not commit it yourself.

## Process expectations

- Read `Signal_Pipeline/PROJECT_BRIEF.md` and `Signal_Pipeline/Phase_0/00_data_inventory_protocol.md` first. Confirm you have read them before running queries.
- Confirm Notion + HubSpot MCPs are live. If not, stop and tell me.
- Run queries in parallel where they're independent. The 6 DB row counts are independent. Property completeness queries within a DB can run together.
- Time-box: 3–4 hours of focused work. If it's taking longer, the scope is wrong — flag and we'll narrow.
- After completion, propose 2–3 "next questions" you'd want to investigate based on what the data showed. These will inform the signal discovery method in the next phase.

Begin by confirming you've read the two priority docs and that the required MCPs are connected. Then proceed.
~~~

---

## Field notes for Alex

- The fenced block above is what gets pasted. Everything outside it is meta-instructions for you.
- If the desktop session can't read from GitHub directly, paste `00_data_inventory_protocol.md` and `PROJECT_BRIEF.md` (Signal_Pipeline version) directly into the chat after the bootstrap.
- When the inventory comes back, paste it into THIS Claude Code CLI session. I'll write `inventory_findings.md` to the repo, commit it, and move into signal discovery.
- This file is a living artifact. After Phase 0 exits, update the "Current task" section to the next active workstream (Phase 1 spec, R1 writeup, etc.).
