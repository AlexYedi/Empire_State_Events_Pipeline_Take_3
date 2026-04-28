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
</behavioral_rules>

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

### Core Skill: Event Research (TO BE BUILT)
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

**Notion** (Content + Research Hub) — 6 interconnected databases (verified via MCP, 2026-04-09):
- Events (8 props): Event Name (title), Event Date (date), Location (text), Event Description (text),
  Event Status (select: intake/researched/content_drafted/attended/post_complete), 
  relations to People/Companies/Topics/Content Drafts
  Note: Event Description stores the raw pasted invite text. No Calendar Source property — 
  the pipeline generates value for events Alex attends AND events he doesn't (content + outreach 
  aren't gated by physical attendance).
- People (11 props): Name (title), Current Title (text), Email (email), Phone Number (phone), 
  LinkedIn URL (url), Known POV / Bio (text), Notes (text), Role Context (multi-select: 
  speaker/host/organizer/attendee/contact), Last Researched (date), 
  relations to Events/Company/Content Drafts
- Companies (9 props): Company Name (title), Description (text), Website (url), Industry / Space 
  (multi-select: AI/ML, Enterprise Software, Developer Tools, VC/Investment, Data Infrastructure), 
  Funding Stage (select: Seed, Series A, Series B, Series C, Series D, Series E, Series F, Series G, 
  Series H, Series I, Public — NO "Pre-IPO" option; use latest Series letter for late-stage private cos), 
  Recent Funding ($) (number), Recent Developments (text), Last Researched (date), 
  relations to Events/People
- Topics (9 props): Topic (title), Current Events (text), Opportunities (text), Challenges (text),
  Use Cases & Practical Applications (text), Top Questions (text), Last Updated (date), 
  relations to Events/People/Linkedin Post Drafts (→ Content Drafts, intentional naming — 
  pulls Content Drafts filtered by linkedin post content types)
- Content Drafts (8 props): Title (title), Content Type (select: research_brief/linkedin_dm_speaker/
  linkedin_dm_host/linkedin_post_pre/linkedin_post_post/prepared_questions/linkedin_post_synthesis), 
  Event Phase (select: pre_event/during_event/post_event), Content Status (select: needs_review/
  approved/scheduled/published/archived), Platform (select: linkedin/slack/notion_only), 
  Published URL (url), relations to Event/People/Topics/Project Ideas
  Note: linkedin_post_synthesis (added 2026-04-19) is used by the pattern-synthesis skill for 
  two-thesis posts that relate to 2+ Events. Multi-Event relations are the tell for this type.
  Views (added 2026-04-18): 🎯 Active Kanban (Board, grouped by Content Status, filter:
  Status ≠ archived) — daily workspace. 🗄 Archive (Table, filter: Status = archived) —
  terminal state, preserves relation graph for future knowledge base synthesis.
  Status flow: needs_review → approved → scheduled → published. archived is reachable from
  any state and is terminal. Archived content stays in the same DB (relations intact) —
  deliberately not a separate archive table, to keep the graph whole for Phase 3-6 knowledge base mining.
- Project Ideas (17 props): Project Name (title), Status (select: needs_review/active/shipped/
  archived/deleted), Proposal Type (select: feasible/stretch), Complexity Band (select: 
  prototype/small_tool/MVP/full_project), Stack Coverage % (number), Relevance (number 1-10),
  Creativity & Uniqueness (number 1-10), Tool Coverage (number 1-10), Conversation Starter 
  (number 1-10), Demonstrability (number 1-10), Content Moments (number 1-10), 
  Composite Score (number), Architecture Summary (text), Created (created_time), 
  Last Updated (last_edited_time), relations to Events/Topics/Content Drafts
  Active projects tracked via Status select. No hard cap — Alex manages bandwidth manually (cap removed 2026-04-20).

**HubSpot** (CRM — Contacts & Companies):
- Standard contact fields: firstname, lastname, email, phone, company, jobtitle
- Company records with standard fields
- Notes attached to contacts with just the event title as body text (primary event-tracking mechanism)
- Event association via Notes: each Note body = event name, searchable for "all contacts from Event X"
- Do NOT set industry on company records — generic categories are unhelpful
- Static Lists NOT available via MCP (OBJECT_LIST write = NOT_AVAILABLE) — Notes approach is the MVP workaround
- Fresh account (created April 5, 2026), full read/write on Contacts, Companies, Notes, Deals
- HubSpot owner ID: 90413044

**Apollo** (Not integrated — separate evaluation):
- Not part of the event research pipeline. Alex evaluates Apollo independently via web UI
  on high-value contacts to determine if paid plan (900 credits) justifies integration.
- API blocked on free plan (`API_INACCESSIBLE` on people endpoints). If upgraded, integration
  becomes a separate decision.

### Notion Database IDs
- Content Drafts: collection://6c24c9f5-66c9-4eed-a61d-3f9b87c3f775
- Events: collection://9dcbc999-b4ed-4a51-b48a-10aaf171f1ba
- People: collection://4a1af67f-9141-4ba5-aa9d-88b07dcd5f86
- Topics: collection://d61ce9df-94b3-4637-aa09-d77e09ab3a74
- Companies: collection://d5910dc3-8327-4b49-9294-fc9499709a98
- Project Ideas: collection://0956e6ed-8555-4d8f-8856-388966dedaab
- Parent page (NYC AI Event Content Hub): 338d3699c2db808781d5d4675dcc5e33

### Phased Roadmap

**Phase 1: Event Research Skill (Current — CTO review complete 2026-04-09)**
- Build event-research skill (.claude/skills/event-research.md) with paste-the-invite input
- Skill runs inside Claude Code conversation — human-in-the-loop by design
- Research sources: Claude training data + WebSearch
- Direct MCP writes to Notion (all 5 databases, ordered by relation dependencies)
- Direct MCP writes to HubSpot (companies, contacts with associations, Notes for event tracking)
- Dedup check: search Notion + HubSpot for existing records before creating
- Test on one real upcoming event end-to-end

**Phase 2: Content Generation Skills (In Progress — 2026-04-09)**
- Three skills: pre-event-content.md, post-event-content.md, pattern-synthesis/SKILL.md (not monolithic)
- Pre-event skill produces: The Upcoming Week (Sunday LinkedIn post), per-event LinkedIn post,
  speaker/host DMs (2-3 per person per topic), prepared questions (derived from unused DMs)
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

### Notion create-pages gotchas (2026-04-18 — learned live on FDE event writes)
These are non-obvious property format rules that bit us during the first real event run. 
Follow them mechanically; the API error messages are the source of truth if anything drifts.

a. **Multi-select properties take a JSON-array-STRING, not a comma-separated string and not a native array.**
   - Correct: `"Industry / Space": "[\"AI/ML\",\"Enterprise Software\"]"`
   - Rejected: `"Industry / Space": "AI/ML,Enterprise Software"`
   - Rejected: `"Industry / Space": ["AI/ML","Enterprise Software"]`  (native array)
   - Same format for People.Role Context.
b. **Select properties must exactly match a defined DB option.** When validation fails, the API error text 
   lists the valid options — trust the error, not the doc/CLAUDE.md. The authoritative schema lives in Notion.
c. **Relations take a JSON-array-string of full page URLs (not bare page IDs).** Use the `url` field returned by 
   notion-create-pages verbatim. Example: `"Company": "[\"https://www.notion.so/347d3699...\"]"`.
d. **Date properties must use expanded format.** `"date:<Prop>:start"` + `"date:<Prop>:is_datetime"` (0 or 1). 
   For datetimes with end times, add `"date:<Prop>:end"` alongside.
e. **Before any batch create against an unfamiliar DB, verify live schema with notion-fetch on the data_source URL.** 
   Property names, option sets, and types can drift between docs and the live DB.
f. **Write order for bidirectional relations:** Companies + Topics (no deps, parallel-safe) → People (needs Company URLs) 
   → Event (needs People + Companies + Topics URLs) → Content Draft (needs Event URL). Skipping this order silently 
   produces empty relation fields.

### Notion update-page gotchas (2026-04-26 — learned during eval-harness cycle 1 delivery)
These are markdown-flavor rules for `notion-update-page` (and `create-pages` body content) that bit us during 
the orchestrator delivery. Each rejected syntax was tested live and observed to land as escaped literal text.

g. **Toggle/collapsible sections use `<details><summary>...</summary>...</details>` HTML — and ONLY this form.** 
   Notion-flavored markdown's `+++ title ... +++` syntax does NOT work; lands as literal `+++` text. The `<details>` 
   tag is the only allowlisted HTML form for toggles in this MCP. Inner content is auto-tab-indented in fetch output 
   to indicate nesting — that's the visible signal it parsed as a real toggle block. Use this for preserving 
   deprecated/superseded prior content on the same page (avoids sub-page sprawl).
h. **There is NO markdown TOC syntax that works via the Notion MCP.** Tested and rejected: `[[toc]]`, `[TOC]`, 
   `+++`, `<toc/>`, `<table_of_contents/>` — all land as escaped literal text. The only path to a real auto-updating 
   TOC block is the `/toc` slash command in the Notion UI (one-time per page; native block then auto-updates as 
   headings change). Workaround for write-time: insert a static "Page index" callout at top (see convention `i`).
i. **Page-index callout convention** (orchestrator deliveries + any multi-section page worth scanning at a glance): 
   blockquote with 📑 emoji, bold "Page index", bullet list of H1 sections each with a one-line description, 
   ending with the italic tip *"Place cursor below this callout and type `/toc` to add Notion's interactive 
   auto-updating table of contents — one-time per page."* Static fallback that gives glanceable structure; the 
   `/toc` step is opt-in and lives in the UI.
j. **`<` in body text is auto-escaped to `\<`** in stored markdown but renders correctly in the Notion UI 
   (`\<5min` → `<5min`). Cosmetic only — don't try to "fix" it by removing the escape.
k. **Markdown `|`-tables auto-convert to native `<table header-row="true">` blocks** on write. Rendered as 
   real Notion tables (sortable, filterable, resizable columns) — preferred over leaving them as raw markdown.
</project_architecture>
</CLAUDE.md>
