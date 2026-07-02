<identity>
You are working with Alex — a senior enterprise B2B SaaS professional (12+ years) 
currently building at the intersection of AI and GTM. Background spans enterprise 
account management, new business, and customer success at companies including 
Meltwater, Bazaarvoice/Curalate, and Cohley. Currently Lead Enterprise Account 
Director at GKY Industries.

Alex has spent a lot of time developing knowledge across AI, LLMs, Deep Learning, Agents, and Agentic Systems; 
However, much of that has been theoretical, and coming from a nontechnical background, I require explanations throughout every project we do.
Make sure to offer explanations of core and complex concepts as well as the thought process, best practices, or other influences over decisions
at the beginning and end of the defined phases and sections in our project roadmaps. 
If explanations are needed during development, I will invoke the explainer skill 
</identity>

<communication_rules>
- Match Alex's register: direct, commercially fluent, technically aware but not technically fluent.
- Keep any business fundamental references brief, but acknowledge them when they arise.
  Go deeper on technical and architectural concepts when they arise, reference frameworks, best practices, seminal papers, projects, and other work product where relevant.
- Responses should be as long as the task requires and no longer
- Use headers and structure for complex outputs; prose for conversational answers
- Default to a strong recommendation when trade-offs are not a concern
- When tradeoffs matter, present max 3 options with a clear signal on which to choose
- Do not add disclaimers unless they are legally or technically material
- Do not restate the question before answering it
- When providing n8n, API, or platform configuration instructions: specify every field value explicitly. 
  Never assume Alex knows platform defaults or UI conventions. Number every step, indent sub-tasks as bullets.
</communication_rules>

<behavioral_rules>
- Always stop, think, assess all referenced resources, lead with planning, strategy, and ask clarifying questions before producing complex deliverables
- Flag irreversible decisions explicitly before proceeding
- If a task is ambiguous, state your interpretation and collaborate to clarify before proceeding
- Push back constructively when a direction seems suboptimal; explain why
- Assume Alex owns budget authority and decision-making power unless told otherwise
- Lead with existing tech stack, then free services, then paid solutions with clear rationale
- When proposing solutions, state confidence levels honestly (percentage + plain language qualifier)
- When debugging: inspect actual data before proposing fixes. Never propose theoretical fixes without observing the failure point first.
- Use /calmate skill when progress stalls after multiple attempts
- **MCP automation defaults (added 2026-05-24 — corrects the misread of cost discipline as a blanket "prefer manual" rule).** Three distinct cases, applied in order:
  1. **MCP-to-existing-subscription-vendor (DEFAULT: automate).** Any connected MCP whose underlying work is billed by an existing subscription Alex already pays for (Canva, Gamma, Notion, HubSpot, Granola Business, Linear, etc.) should be wired into the skill's workflow, not handed off manually. The Anthropic-side token cost of an MCP call is negligible (small JSON request/response). Manual handoff in these cases is friction without quality lift.
  2. **Manual step justified by judgment load (KEEP manual).** When the step requires Alex's judgment (review before a contact lands in CRM, approve copy before publishing to a channel, sign off on a strategic decision), keep it manual. The rule is *automate where automation preserves quality*, not *automate everything that's MCP-eligible.*
  3. **Anthropic-side inference cost discipline (the original rule, still applies).** Don't burn Claude tokens on redundant inference, oversized contexts, repeated re-runs of expensive operations, or architecture that compounds API spend. This rule is about Anthropic billing, NOT about whether to use vendor MCPs.
- **Pattern to watch for:** "Tool: X" in a skill spec usually meant *Alex copies output into tool X manually* — that's a manual handoff pattern from before MCPs were broadly available. When you see this pattern, audit whether the tool has a connected MCP; if yes, default to automation per rule 1 above unless judgment load (rule 2) gates it.
- **Command/skill invocation proactivity — BALANCED default (added 2026-07-02).** Two layers, never conflated:
  **(A) Invocation** = whether to START a workflow without Alex typing `/x` — *this policy governs only this.*
  **(B) In-pipeline behavior** = what a running workflow writes and where its gates are — **owned entirely by each pipeline's own spec** (decided at design time). This policy NEVER overrides, adds, or removes a running pipeline's internal writes/gates; a write a pipeline was designed to do automatically keeps happening as designed.
  Three invocation tiers:
  - **Tier 1 — auto-fire:** research / drafting / analysis / synthesis (reviewable artifact, nothing irreversible). Proactively invoke when the moment clearly matches the tool's trigger (e.g., Alex mentions an upcoming event → run event research + pre-event draft unprompted).
  - **Tier 2 — auto-START, then stop at the pipeline's own gate:** workflows with a write/approval step (`/scan-*` present a digest; `/event-deep-research` presents a brief before writing). Proactively start; they pause at their built-in gate. Safe by construction.
  - **Tier 3 — manual only:** truly irreversible / outward-facing / judgment-heavy — external publish (LinkedIn), CRM writes, spending Apollo/Clay credits, anything Alex has said is his call. Surface + recommend; don't start unprompted.
  When unsure which tier, treat as the higher (more cautious) tier. "Proceed without prompting" / batch-autonomy instructions temporarily raise the ceiling (see [[feedback_ship_all_variants_2026-05-30]]). Discover the toolkit via `/toolbox`.
</behavioral_rules>

<definition_of_done>
**Definition of Done for non-trivial builds (pilot — added 2026-06-25).** A *dynamic feedback policy, NOT a static brake.* Diagnosed root cause (systems analysis, `alex:systems-analyst`): rigor lived in optional docs/tools, never the execution path, so the memory-less agent shipped on "green checks" without durable artifacts, and the consequence surfaced weeks later. This gate puts a floor under "done" without blocking flow.

**Scope test — the agent proposes, Alex confirms at session start.** A build is *non-trivial* if it: adds/changes a skill, agent, command, or pipeline component; alters a schema or data contract; came from an approved plan; or is hard to reverse. Everything else (typo, single-line fix, config tweak, doc edit, pure research/exploration) is *trivial* and auto-waives this gate.

**The gate (≤3 items).** A non-trivial build session does not silently close until each item is satisfied or **explicitly waived with a one-line reason** (waivers are logged as data, not failures, so the pattern is visible):
1. **Spec artifact before code** — a PRD or one-pager in **ChatPRD**, mirrored to **Notion** (the source of truth for artifacts), created *before* the build where feasible (guards against retroactive cargo-cult PRDs).
2. **Linear issue** opened or updated for the workstream (the source of truth for "what's open").
3. **One adversarial pass in writing** — a pre-mortem question, or an `alex:cto-principal-architect` / `alex:risk-playbooks` check.
4. **(Activates once the eval/measurement layer is live)** the build-quality **judge ran within N hours** — if stale, this item FAILS. The measurement system's health is a *precondition of the gate*, not a separate dashboard (prevents silent metric rot).

**Discipline:** keep this at ≤3 (+1) items. If it creeps toward 7, *shrink it* — growth is the rule-beating signal. The agent must surface this checklist (met / waived-with-reason per item) before closing a non-trivial build; it never hard-blocks (it informs).

**Promotion path:** piloted here in Empire State first; promote to canonical `~/Documents/GitHub/alex-agents-skills/Me/canonical-claude-md.md` (user-scope, inherits everywhere) once it has proven it changes behavior without becoming a drag — the YED-29/30 project-scope-first-then-promote pattern. Plan of record: `~/.claude/plans/my-linkedin-on-the-scalable-acorn.md`.
</definition_of_done>

<measurement_rigor_layer>
**Build-rigor + measurement/eval/observability layer (added 2026-06-25/26).** Cures the diagnosed root cause (Shifting-the-Burden: rigor lived in optional docs/tools, not the execution path). Lean stack: Notion + PostHog + Empire State Hub + ChatPRD — NO Langfuse/gtm-os (those were tombstoned; do not reintroduce). North-star = acted-on value (outcome vs each artifact's assigned goal, trended). **Supabase tombstone re-scoped 2026-06-28 (ratified by Alex):** the ban applies to the *measurement/eval layer only* — do NOT reintroduce Supabase as a measurement/observability store. Supabase IS the sanctioned **system of record for the Market-Intelligence Engine** (the lens-agnostic MI/research engine; Job-Search + Content cores) — Supabase org `A.Yedi`, project `empire state ai` (ref `oicikjyzmxqfomrrqkvf`), accessed via **REST API** with `SUPABASE_API_KEY` from `.env` — **NOT** the Supabase MCP (that connector is on a different account, `Same Old Expressions`/GTM_OS — never use it for Empire State). See `.claude/references/market-intel-spine.md` + plan `~/.claude/plans/where-do-we-stand-sunny-puzzle.md`.
- **Plan of record:** `~/.claude/plans/my-linkedin-on-the-scalable-acorn.md`. **Linear:** project "Empire State — Build-Rigor & Measurement Layer" (YED-87…94, `cycle-1`). **PRD:** ChatPRD `61bb864f…` + Notion Project Ideas `38ad3699…`. **Learnings/gotchas:** `.claude/notes/measurement-layer-learnings.md` (read before extending — it has the PostHog/OTEL/.env/transcript gotchas).
- **Live pieces:** the DoD gate (above) · signal scanners `/scan-trends`,`/scan-roles`,`/scan-voices` (skills `{trend,voice,role}-radar`) · telemetry Stop hook `.claude/hooks/build-session-emit.sh` (contract: `.claude/references/build-session-contract.md`) · the build-quality judge `/judge-build` + `.claude/evals/` (rubric `build-quality@1`, run-log, ≥80% calibration gate — **advisory** until then) · **goal-tagging** (`Goal`/`Target` on Content Drafts; `content-patterns/goal-tagging.md`) + **outcome capture** `/tag-outcome` (`Outcome`/`Outcome Value`/`Outcome Date`) = the acted-on-value north-star · **weekly learning loop** `/rigor-review` + `.claude/evals/correction-recurrence.md` · the **value-action registry** `.claude/references/value-action-registry.md` (no orphan metrics; every metric has {threshold→action→surface}).
- **Coordinates with** the `eval-harness` project (Notion `348d3699…`) as the Tier-2 judge engine (it owns `rubric_version`) and **Empire State Hub** (the viz + build-in-public surface).
- **Pending:** Alex sets `POSTHOG_PROJECT_KEY` (the `phc_` project key) in `.env` → PostHog projection lights up.
</measurement_rigor_layer>

<standing_context>
- Based in New York City
- Actively building AI-native products, GTM systems, and exploring what is possible
- Job searching in parallel — targeting AI-native companies and enterprise AI/software sales roles
- Key tools in stack: Claude, n8n, Supabase, Linear, PostHog, Vercel, Railway, 
  Cursor, GitHub, Replit, Bolt, Lovable, Framer, Notion, Gamma, Canva, Magic 
  Patterns, Miro, Granola, ChatPRD, Perplexity, ElevenLabs, NotebookLM, 
  Google Workspace (incl. Gemini/Imagen 3, Google Vids, Google Slides), 
  Wispr Flow, Warp, Devin, Factory, Mobbin, HubSpot, Apollo
</standing_context>

<project_architecture>
## Empire State Events Pipeline — Take 3

### 🟠 Open priorities at session start (last updated 2026-05-13 — Linear triage session)

**Codification rule (live as of 2026-05-13):** Linear is the single source of truth for "what's open." This block is a transitional duplicate until YED-26 ships and replaces it with a live SessionStart hook pull. Edits here are doc maintenance, not new state.

**Triage 2026-05-13 outcome:** Cancelled YED-1, YED-4, YED-15→YED-22 (Linear seed tutorials + superseded eval-harness cycle-1). Closed YED-23 as Done (goal-flip work shipped independently, mechanism fixes folded into v2 proposal). Eval-harness cycle-1 framing replaced by `.claude/proposals/content-pipeline-v2-stage2.md` — re-issue under v2 Component framing only when 2-of-3 v2 triggers fire weekly. Current state: 1-of-3 firing intermittently.

**Execution-focus window CLOSED 2026-06-11 — brake lifted, replaced by a steering bias.** The 2026-05-15 "no architecture work, publishing baseline only" rule did its job (publishing increased) and then inverted: at execution volume, the deferral discipline itself became the drag — improvements surfaced in real time were being captured-and-deferred instead of built, leaving friction in the active publishing path. The balancing loop that protected the publishing stock had flipped into the constraint draining it. Verdict (Alex, 2026-06-11): retire the rule; build improvements in real time *while* executing. **The replacement is a steering bias, not a brake: build freely, but each build should remove a named friction on the active publishing path. Friction-remover → build it inline, now. Speculative architecture with no named publishing friction behind it → still skip (that's the original R2 / Shifting-the-Burden trap, and it's the only thing this bias rules out).** The friction-remover vs. R2-trap test (from the 2026-05-21 frictions-log entry) is now applied live, not deferred to a batch. Pipeline v2 / Stage 2 proposal (`.claude/proposals/content-pipeline-v2-stage2.md`) is now buildable under this bias when a real publishing friction motivates a component — no longer gated behind the "kick the can / re-measure first" default.

**Live Linear issues** — pulled at session start via `~/.claude/hooks/linear-priorities.sh` (YED-26 shipped 2026-05-13; promoted to user-scope via YED-29 so every project inherits it). Look for the "🟠 Linear priorities" block at the top of session context. If `LINEAR_API_KEY` is not set in env, hook runs in graceful-fallback mode — create a personal API key at https://linear.app/yedibalian/settings/api and export it to activate live pulls. Note: Dock-launched Claude Code does NOT inherit `~/.zshrc` env — launch from terminal for live pulls.

#### 🏛 Three-layer architecture program (2026-05-13) — durable framing

Larger arc the codification work is part of. Goal: make "build-better-not-faster" the default for *every* project Alex opens, not a discipline he has to remember to apply. Per-issue state lives in Linear; this table is the architectural plan.

| Layer | What it does | Linear issues |
|---|---|---|
| **A. Distribution** | Skills/agents/commands ship to all projects | YED-25 (first instance: systems-thinking) → YED-28 ✅ MVP shipped 2026-05-15 — `alex` plugin, 15 skills migrated, user-scope installed |
| **B. Discipline** | Cross-project invariants (Linear source of truth, event-triggered habits) | YED-26 + YED-27 (project-scope first) → YED-29 (promote to user-scope, universal) |
| **C. Workspace** | Project-specific overlays inherit canonical defaults | YED-30 (canonical CLAUDE.md fragment + new-project starter kit) |

**Total program effort:** 1-2 weeks priority mode, or 4-6 weeks background mode. The whole plan is a single architectural arc that ends with: starting any new project = inheriting all of Alex's accumulated discipline + skill conventions automatically.

### Visual brief pattern (added 2026-05-12)
Every LinkedIn post produced by `pre-event-content`, `pattern-synthesis`, and `content-correspondent` now ships with an accompanying **3-5 slide visual carousel brief** that tells the post's thesis through different perspectives (not the same image redrawn). Canonical spec at `.claude/skills/content-patterns/visual-briefs.md`. Four narrative arcs available — pick by post type. The three content skills import from there as a shared reference; edits to the visual voice go in that file once and propagate. **Core principle (added 2026-05-26): visuals must ADD information — architecture, comparison, progression, a "where-the-value-moves" diagram — and must NEVER re-print quotes or lines already in the post. A quote-card carousel that echoes the copy is text-forward repetition, not visual content, and is an anti-pattern.** See `content-anti-patterns.md`, `content-style-guide.md`, and the Arc-4 guard in `visual-briefs.md`. **Validation:** spec changes need a fresh conversation to test the agents end-to-end (agent registry is session-frozen).

### Where to start
**For workflow orchestration (commands, agent fan-out, how the four workflows chain): read `.claude/WORKFLOWS.md` first.** That document is the rerun manual.

The `.claude/` directory now uses the agents + commands + skills triangle:
- `.claude/agents/` — subagent role definitions (called via the Task tool with `subagent_type`). Organized into `research/`, `content/`, `sales-methodology/`, `ops/`.
- `.claude/commands/` — slash-command workflow files. The four pipeline workflows live here: `event-deep-research.md` (✅ wired), `post-event-synthesis.md` (🟡 scaffolded), `weekly-recap.md` (🟡 scaffolded), `voice-pass.md` (🟡 scaffolded).
- `.claude/skills/` — methodology packages with SKILL.md + references/. New parent folders: `research-methodology/`, `company-deep-research/`, `content-quality/`, `transcript-intelligence/`, `icp-research/`, `cold-email/`.

### Purpose
An AI-native pipeline that turns Alex's Google Calendar event attendance into pre-event research, 
networking preparation, content creation, and CRM management — powered by Claude skills with 
direct MCP writes to Notion and HubSpot. No middleware, no n8n, no Supabase.

### Architecture Philosophy
The previous iteration (new-jack-city-events-pipeline) attempted full automation via n8n workflows 
chaining Google Calendar → Claude research → Notion/Supabase writes. It failed repeatedly at the 
integration layer (Notion API chunking, n8n expression handling inside loops, HTTP Request body 
serialization). The core insight: **separate "do great research" from "put it in the right places."**

This iteration uses Claude skills as the research and content engine, with MCP connections writing 
directly to destination systems. Human-in-the-loop by design — Alex reviews research as it's 
generated, which improves quality and eliminates the fragile automation chain.

### Core Skill: Event Research (BUILT — `/event-deep-research`, multi-agent rebuild 2026-05-04)
Invoked manually when Alex adds an event to his calendar. Input: pasted calendar invite text with 
natural language cues about speakers, hosts, topics. Output: structured research written directly 
to Notion and HubSpot via MCP.

#### Input Format
Alex pastes calendar invite description + adds natural language context:
- "Speaker: Jane Smith, CTO at Acme Corp"
- "Host: AI NYC Meetup"
- "Topics: agentic systems, enterprise AI adoption"

#### Research Sections (all equally important)
1. **Topics & Subtopics** — Deep enough to engage confidently in networking and discussions. 
   Used for differentiated pre-event outreach to create soft intros with hosts/speakers.
2. **Hosts & Speakers** — Many are influential people at target companies. Research enables 
   thoughtful engagement about topics they're passionate about. These circuits are small worlds.
3. **Companies** — Target employers and industry players. Recent product releases, funding, 
   milestones, headwinds. Ties companies to events and topics.
4. **Content Generation** — LinkedIn posts, DMs, outreach. Supports Alex's north star of 
   becoming a "full stack GTM" professional. Distribution is critical.
5. **Documentarian Angle** — Alex's edge is being a frequent, interesting documentarian of 
   ephemeral NYC AI/tech experiences that aren't otherwise shared effectively.

#### Output Destinations
Canonical schema for all three write destinations (Notion's 6 databases with full property lists,
HubSpot CRM fields + Notes convention, Apollo non-integration status) lives in
**`.claude/references/notion-schema.md`**. Database IDs are in "Notion Database IDs" below.
Summary: Notion is the Content + Research Hub (Events, People, Companies, Topics, Content Drafts,
Project Ideas — all bidirectionally related); HubSpot holds Contacts/Companies with event-tracking
Notes (Static Lists unavailable via MCP); Apollo is evaluated separately (API blocked on free plan).
Live Notion schema is the source of truth — verify with `notion-fetch` before batch creates.

### Notion Database IDs
- Content Drafts: collection://6c24c9f5-66c9-4eed-a61d-3f9b87c3f775
- Events: collection://9dcbc999-b4ed-4a51-b48a-10aaf171f1ba
- People: collection://4a1af67f-9141-4ba5-aa9d-88b07dcd5f86
- Topics: collection://d61ce9df-94b3-4637-aa09-d77e09ab3a74
- Companies: collection://d5910dc3-8327-4b49-9294-fc9499709a98
- Project Ideas: collection://0956e6ed-8555-4d8f-8856-388966dedaab
- Parent page (NYC AI Event Content Hub): 338d3699c2db808781d5d4675dcc5e33

### Phased Roadmap

**Phase 1: Event Research Skill (Multi-agent rebuild complete 2026-05-04; `/check-new-events` thin-wrapper added 2026-05-20)**
- Original: monolithic `event-research` skill (.claude/skills/event-research/SKILL.md — migrated to folder format)
- Rebuilt as `/event-deep-research` command (Workflow A) with multi-agent fan-out
- **NEW (2026-05-20): `/check-new-events` thin-wrapper command** — calendar-invite-as-structured-intake pattern. Alex pastes a PIPELINE block (template at `.claude/references/pipeline-block-template.md`) into the GCal description at event-acceptance time via text expander `;pipeline`. The command queries the "Going to Events" calendar (`mcp__claude_ai_Google_Calendar__list_events` on calendar ID `4c84184ac3e761c3f94be43193656a785ece4752ed6b553facfcb52e668a333b@group.calendar.google.com`), detects events with the PIPELINE block, dedups against Notion Events DB, then runs `/event-deep-research` + `pre-event-content` interactively per event with continue-or-quit control between events. Validated end-to-end 2026-05-20 on Ray Dev Day. Discipline-break decision record + falsification protocol in `.claude/notes/execution-week-frictions.md`. See also `.claude/commands/check-new-events.md` for orchestration shape, `.claude/references/pipeline-block-template.md` for template spec.
- Orchestration (updated 2026-05-07 — synthesizer pivot): `/event-deep-research` Step 2 fans out 4 specialists in parallel **from the parent thread** (subagents cannot dispatch sub-agents per Anthropic SDK design) — `company-researcher`, `person-researcher`, `topic-landscape-analyst`, `competitive-signal-scanner`. Step 2.5 dispatches `event-research-synthesizer` (sonnet) to assemble the brief. Step 4 dispatches `notion-writer` for dependency-ordered MCP writes. See "SDK runtime constraints" subsection below for the full rationale.
- Skill methodology (Steps 1–7) is unchanged and authoritative: `.claude/skills/event-research/SKILL.md`. The command file is the orchestration shape; the skill is the methodology
- Research sources: Claude training data + WebSearch
- Direct MCP writes to Notion (all 5 databases, ordered by relation dependencies) via notion-writer agent
- Direct MCP writes to HubSpot (companies, contacts with associations, Notes for event tracking) — handled in main conversation (HubSpot MCP needs inline confirmation tables)
- Dedup check (Step 1.5 triage): search Notion + HubSpot for existing records before creating; classify NEW/REFRESH/SKIP
- See `.claude/WORKFLOWS.md` for the full Workflow A rerun manual

**Phase 2: Content Generation Skills (In Progress — 2026-04-09; DM spec patched 2026-05-20; Granola wired 2026-05-21)**
- Three skills: pre-event-content.md, content-correspondent/SKILL.md (post-event), pattern-synthesis/SKILL.md (not monolithic)
- **`/post-event-content` slash command (wired 2026-05-21; Granola disabled 2026-05-27; post_event_brief added 2026-05-28)** — Manual-upload-anchored orchestrator. Resolves event name → Notion Event row → manual transcript paste → **transcript-conditioning** (Step 3.5) → **`post_event_brief` synthesis** (Step 3.7, the canonical data store / short-term memory) → invokes content-correspondent with the conditioned quote bank + brief reference → notion-writer commits drafts. Dual-path event resolution: deterministic `Google Calendar Event ID` match (preferred), title+date fuzzy fallback. Granola auto-fetch path retained but DISABLED (app nonoperational on Alex's device). The post_event_brief is the post-event mirror of the pre-event research_brief — comprehensive, browsable, and referenced by every downstream draft. See `.claude/commands/post-event-content.md` for orchestration shape, `.claude/notes/execution-week-frictions.md` 2026-05-21 entry for the Granola decision record.
- Pre-event skill produces: The Upcoming Week (Sunday LinkedIn post), per-event LinkedIn post,
  speaker/host **connection request notes** (1 best per person, 200-char hard cap — see DM rule below),
  prepared questions (now generated independently from research, not as DM byproducts)
- Post-event flow (`content-correspondent` skill) now has **two input modes** documented in SKILL.md:
  Mode A (preferred) = Granola-anchored structured input via `/post-event-content` command. Skill
  consumes Granola's pre-synthesized `summary_markdown` for angle/thesis decisions and the diarized
  `transcript` for verbatim speaker quotes. Mode B (legacy) = manual paste of raw material — still
  supported for events not recorded in Granola or for ad-hoc walk-in events.
- **Speaker/host outreach is connection-request-note format, NOT LinkedIn DM (rule added 2026-05-20):**
  LinkedIn free-tier limits direct messages to 1st-degree connections; Premium burns InMail credits
  sending to non-connections. The pre-event-content skill produces **200-char connection request notes**
  (free-tier limit; Premium is 300). Notion Content Type names `linkedin_dm_speaker` and `linkedin_dm_host`
  are preserved for backward compatibility, but the content shape is connection notes per
  `.claude/references/outreach-templates.md`. Goal: connection request acceptance, not post-acceptance
  engagement. **Two variants per person (A = talk-anchored, B = adjacent-work-anchored)** anchored to
  materially different signals so the picker decision is signal-based, not phrasing-based. Fallback:
  ship only the variant with a real anchor if one signal type is missing — never ship Level 2 filler.
- Post-event skill: to be built (screen grabs, decks, recap, documentarian angle)
- Pattern-synthesis skill (added 2026-04-19): two-thesis LinkedIn post from 2 event briefs.
  Canonical shape for Alex's documentarian angle. Triggered when 2 briefs in a rolling 7-day window
  pose opposing theses. Writes to Notion with Content Type = linkedin_post_synthesis and
  multi-Event relations. Pattern definition lives in .claude/skills/content-patterns/two-thesis-synthesis.md
  (shared reference file — pre-event and post-event skills can also import it).
- Takes completed research brief from Notion as input
- Writes content drafts to Notion Content Drafts database
- Supporting reference files: content-style-guide.md, content-anti-patterns.md, outreach-templates.md
- Shared patterns directory: .claude/skills/content-patterns/ holds reusable content-shape definitions
  (no SKILL.md — not a skill itself). Any content skill can import from here. First entry:
  two-thesis-synthesis.md.
- Voice & style is a living system — update-voice-and-style.md skill propagates learnings to all files
  including content-patterns/*.md
- Cold outreach only for V1. Warm outreach variant and custom messaging skill deferred.
- 2 inline option variants per content piece. No scheduling/timing logic.
- Audience: hiring managers at AI-native companies, enterprise GTM peers, event speakers/hosts
- Full stack GTM positioning is implicit (demonstrated, not stated)
- Cadence rule for pattern-synthesis: max 1 synthesis post per week (format fatigues fast)

**Phase 2b: Project Ideation Skill (In Progress — 2026-04-09)**
- Skill: project-ideation.md — generates 3 project proposals (2 feasible + 1 stretch) from event topics
- Triggered after event research is complete (all topics populated)
- Intersection quality gate: maps topic pairs, scores strength, prefers strong intersections
- When no strong intersections: selects topics that complement learning trajectory or fill portfolio gaps
- Tool coverage sweet spot: 60-80% current stack = optimal (normalized penalty scales outside range)
- Timeline bands: < 3 days (prototype), 3-7 days (small_tool), 1-2 weeks (MVP), 2+ weeks (full_project)
- Architecture confidence gate: >= 90% or proposal isn't generated
- Active project awareness (not a gate): skill surfaces current active count before generating, but does not block
- Scoring: 6 dimensions (1-10 each, equal weights V1) + 1 pass/fail gate (architecture confidence >= 90%)
- Projects built BEFORE the event — demo, discuss, reference during networking
- Reference file: portfolio-tracker.md (stack tiers, shipped projects, skills inventory)
- Companion skill (deferred): project-complete.md — triggered when projects ship, updates portfolio tracker

**Phase 3: Form + Light Automation (when volume demands it)**
- Vercel/Lovable submission form for event intake
- Form writes to Notion (not Supabase)
- Notification layer only — skill remains the research brain
- Rewire post-event upload form to write to Notion

**Phase 4: Parallel Agents + Full Automation (future)**
- Break skill into sub-agents (company, people, topics)
- Run in parallel from form trigger
- Human review moves from "during generation" to "after generation"

### Post-Event Content Flow
- Vercel upload form for photos/notes/audio after attending an event
- Creates new Content Drafts page with Event Phase = post_event
- Same event name as pre-event content, differentiated by Event Phase property
- Two pages per event in Content Drafts (pre and post), grouped by event name in Notion views

### Predecessor Project
- Repo: new-jack-city-events-pipeline (AlexYedi/new-jack-city-events-pipeline)
- Contains: n8n workflow JSONs (YED-6, YED-12, YED-13, YED-14), Vercel trigger app, 
  Supabase schema, Claude prompt engineering for research and content generation
- Status: Paused. YED-6 (GCal intake) works. YED-12/13 (research/content) had persistent 
  Notion API integration failures. Architecture replaced by skill-first approach.
- Reference value: Claude prompts for research synthesis, field mappings, content templates

### Notion Write Orchestration (verified via MCP, 2026-04-09)
Relations are bidirectional — setting one side auto-populates the other. Write order matters 
because relation fields require page URLs from previously created pages.

```
Step 1: Create Companies (no dependencies) → capture page URLs
Step 2: Create Topics (no dependencies) → capture page URLs
   Steps 1 & 2 can run in parallel
Step 3: Create People (set Company relation using Step 1 URLs) → capture page URLs
Step 4: Create Event (set People/Companies/Topics relations using all URLs)
Step 5: Create Content Draft (set Event/People/Topics relations)
   Event.Content Drafts auto-populates via bidirectional link
```

notion-create-pages returns page URLs. Those URLs ARE the IDs for relation fields (JSON arrays).

### HubSpot Write Orchestration
```
Step 1: Create Company records (standard fields)
Step 2: Create Contact records + associate with Companies (HubSpot association API)
Step 3: Create Note on each Contact (event name + role + talking points in body)
```
Notes approach replaces Static Lists for event association (list write not available via MCP).

### Key Patterns & Rules (learned from predecessor + CTO review 2026-04-09)
1. Never propose fixes without inspecting actual data at the failure point first
2. When configuring any platform (n8n, Notion, HubSpot), specify every field explicitly
3. State confidence levels honestly — a stated 40% is more useful than an inflated 80%
4. Separate research quality from distribution mechanics — research is the value, distribution is plumbing
5. Human-in-the-loop improves research output — don't automate away the review step, move it later in the pipeline over time
6. Create new records rather than updating existing ones when possible — avoids append/update API complexity
7. Use /calmate when progress stalls after 2+ failed attempts at the same problem
8. Always validate live system state via MCP before building — pricing pages and docs can lag behind API reality
9. Notion page body for long-form text, properties for structured/filterable data
10. Search Notion databases for existing records before creating to prevent duplicates (Notion has no native dedup)
11. Search HubSpot by name+company before creating contacts to prevent duplicates (email is primary dedup key)
12. **Source-check firm/person thesis claims before public use (added 2026-05-26).** Any firm- or person-level *thesis / positioning / belief* claim ("X's fund bets on Y over Z", "X believes W") must carry a primary-source citation before it lands in public-facing content (LinkedIn post, connection note, DM). If a research brief asserts such a claim without a cited source, treat it as unverified — verify via web search, or flag it and soften/cut. Prompted by an Alumni Ventures thesis claim that flowed unsourced from brief → public post; it verified clean, but the gap was real.
13. **Gamma is the default visual generator (added 2026-05-26).** Gamma builds accurate infographics/charts/matrices from content and supports true 4:5 via `format: "social"`. Canva `generate-design` garbled dense labels and produced Instagram-typed assets — now a fallback only (clean single typography cards); Imagen for textless conceptual imagery. Canonical spec: `.claude/skills/content-patterns/visual-briefs.md`.
14. **Stance is earned; the roundup sets the table (added 2026-05-30).** A viewpoint without space for context + analysis is a hot take, and a hot take in a synopsis adds ZERO value. Bold POV is deferred to formats with room (post-event recaps, deep per-event posts) and grows with Alex's expertise; the Upcoming Week roundup SETS THE TABLE (topic + state-of-union + field tension, no side). Also decenter the self (curator, not protagonist — the events are the subject, not Alex). Capture per-event steering context BEFORE generation via the `steering-interview` skill. Canonical: `content-style-guide.md` v0.5 + `content-anti-patterns.md` v0.5; the front→back quality loop is steer (`steering-interview`) → generate → comment (Notion) → mine (`update-voice-and-style`).

### SDK runtime constraints (added 2026-05-07 — orchestrator → synthesizer pivot)
Full resolved-diagnostic record in **`.claude/references/sdk-runtime-constraints.md`**. Two durable
constraints govern all agent/command design:
1. **Subagents cannot spawn other subagents** (Anthropic SDK design — `Agent`/`Task` is absent from subagent contexts). Any fan-out must run from the parent thread (the slash command's main conversation); synthesis-only agents (text in, text out, no dispatch) are fine as subagents. Every subagent in `.claude/agents/` must declare an explicit minimal `tools:` frontmatter line (prevents context bloat + "Prompt is too long" failures).
2. **The agent registry is session-frozen** — the harness reads `.claude/agents/**/*.md` ONCE at conversation start. Any add/edit/delete to an agent file requires a FRESH conversation to test; mid-session changes are saved to disk but not reflected in the live registry.

### Notion MCP write gotchas
Property-format rules for `notion-create-pages` and markdown-flavor rules for `notion-update-page`
(toggles, TOC, table conversion, emphasis-marker matching, the `\n`-mangling gotcha) live in
**`.claude/references/notion-write-gotchas.md`** (conventions a–m). Follow them mechanically; the API
error messages are the source of truth if anything drifts. Primary consumers: the `notion-writer`
agent and the pipeline command files.

### Systems-thinking harness (added 2026-05-04)

Backed by 8 reference files in `.claude/skills/systems-thinking/references/` derived from Donella Meadows' 
*Thinking in Systems: A Primer*. Canonical content (the 7 source-grounded files plus the generalized 
applications file) lives in the `alex` plugin at `~/Documents/GitHub/alex-agents-skills/skills/systems-thinking/` 
and is invocable as `alex:systems-thinking` in any project (YED-28 MVP, 2026-05-15). The project-level 
harness here keeps the H1/H2/H3 horizon framework (project-specific) and an Empire-State-specific 
applications file with the pipeline's stocks/flows/loops sketched — invoked as plain `systems-thinking` 
and takes precedence over the plugin version inside this project.

- **Eight-phase analysis** lives in `.claude/skills/systems-thinking/SKILL.md` and the `references/diagnostic-questions.md` question bank. Use phases 1-4 for quick reframes; full 1-8 for chronic problems.
- **Workflow card** at `.claude/references/systems-thinking-workflow.md` ties Analyzing/Planning/Building modes across the broader skill set.
- **Delegated agent** at `.claude/agents/ops/systems-analyst.md` performs the eight-phase analysis as a sub-agent without consuming main-context tokens. First test run on 2026-05-04 (content-publishing-plateau hypothesis) is logged at `.claude/artifacts/systems-analyst-test-2026-05-04.md` and surfaced 3 reference-file gaps that are now applied. Per `.claude/WORKFLOWS.md` Known Gap, custom agent discoverability mid-conversation is unreliable — invoke from a fresh conversation.
- **Adjacent skills updated** with systems-thinking integration sections: `head-of-product-engineering`, `risk-playbooks`, `prioritizing-roadmap`, `defining-product-vision`, `ai-product-strategy`, `shipping-products`, `launch-tiering`, `writing-north-star-metrics`. Each references the canonical leverage-points / archetypes / dancing-with-systems content.
- **Rule-out discipline:** when matching a system archetype, also state which archetypes were considered and rejected (with evidence). Two archetypes can produce identical surface symptoms but their escapes diverge sharply (e.g., Tragedy of the Commons vs. Shifting the Burden — see test artifact for the worked example).
- **Watch for perverse balancing loops:** a stock can be drained by waste/decay/abandonment as well as by delivery. Always split the outflow metric. A flat queue can mean equilibrium *or* loss — they look identical.
- **Single-actor multi-role bounded rationality:** treat Alex-as-researcher / Alex-as-reviewer / Alex-as-publisher as separate rows in the actor table. The leverage point is often the seam between two roles within the same person.
</project_architecture>
</CLAUDE.md>
