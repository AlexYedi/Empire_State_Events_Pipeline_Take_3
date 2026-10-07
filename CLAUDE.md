# Empire State Events Pipeline

## 1. Alex, and how to work with him

Alex is a senior enterprise B2B SaaS operator (12+ years: Meltwater, Bazaarvoice/Curalate, Cohley; now Lead Enterprise Account Director at GKY Industries) building at the intersection of AI and GTM, based in NYC, job-searching in parallel for AI-native and enterprise AI sales roles. Deep theoretical grounding in LLMs and agentic systems, non-technical background: **explain core and complex concepts, and the reasoning behind decisions, at the start and end of each phase.** He invokes the explainer skill when he wants more mid-build.

- Register: direct, commercially fluent, technically aware. Business fundamentals brief; technical and architectural depth welcome, with frameworks, papers and prior art named.
- As long as the task needs and no longer. Headers for complex outputs, prose for conversation. No restating the question, no immaterial disclaimers.
- Strong recommendation when trade-offs don't matter; max 3 options with a clear pick when they do.
- Platform configuration (Notion, HubSpot, Supabase, n8n): every field value explicit, every step numbered.
- Plan and ask clarifying questions before complex deliverables. State your interpretation when a task is ambiguous. Flag irreversible decisions before acting.
- Push back when a direction looks wrong, with the reason. Alex owns budget and decisions.
- Confidence as a percentage plus a plain-language qualifier. A stated 40% beats an inflated 80%.
- Debugging: inspect the actual data at the failure point before proposing a fix. Verify live system state via MCP before assuming. Use `/calmate` after two failed attempts at the same problem.
- Stack first, then free, then paid with rationale. Never commit secrets: keys live in `.env`.
- Design and architecture questions go to `alex:cto-principal-architect` (Fable for reasoning-heavy work); systems diagnosis to `alex:systems-analyst`; `general-purpose` is a container for fan-out, not a thinker.

## 2. What this is

An AI-native pipeline that turns Alex's event attendance into research, networking preparation, published content and CRM records. Claude skills do the research and writing; MCP connectors write directly to Notion and HubSpot; a human review in Notion sits between generation and publishing. **The pipeline is the product.** Its value is substantive knowledge (topics, people, companies) deep enough to be the most informed person in the room, not contact enrichment.

```
Google Calendar ─► /check-new-events ─► /event-deep-research
   (4 specialists ∥ + knowledge-conditioning → synthesizer → Deep Read renderer)
   ─► Notion (Events · People · Companies · Topics · Content Drafts) + HubSpot
   ─► pre-event-content (posts ×3 variants · connection notes A/B · questions · carousel PDF)
   ─► attend (Supercut records) ─► /post-event-content ─► content-correspondent ─► Notion ─► HubSpot (gated)
Job-search loop: /scan-roles · role-radar · Notion Roles DB · me-model.md · /interview-prep
Passive store: Supabase MI graph (post-event claims + roles) via spine_client.py
```

Human-in-the-loop by design: Alex reads every brief and every draft in Notion and reviews by inline comment. That review is the quality gate; the tooling exists to feed it.

## 3. Where things live

| Need | Go to |
|---|---|
| How the workflows chain, rerun manual | `.claude/WORKFLOWS.md` |
| Plan of record, decision log, shipped log | Notion "Empire State Roadmap" (https://app.notion.com/p/3e9d3699c2db8163919afb3040099d3c) |
| What's open | To-dos: Notion To-dos database on the roadmap page (`collection://1cd6d576-8a9e-4332-bb81-13a28b55f151`) · build work: Linear (team Yedibalian, `YED-n`) |
| Why the data layer is shaped this way | `docs/adr/README.md` (append-only; reversing an ADR means writing a new one) |
| Environmental limits (harness, Notion, Supabase, vendors, git) | `.claude/references/platform-constraints.md` |
| Notion/HubSpot schema and write order · MCP write formatting | `notion-schema.md` · `notion-write-gotchas.md` |
| MI graph model | `market-intel-spine.md` |
| Content voice | `content-style-guide.md` · `content-anti-patterns.md` · `outreach-templates.md` · `.claude/skills/content-patterns/` |
| Commands, agents, skills | `.claude/commands/` · `.claude/agents/` · `.claude/skills/` (methodology lives in the skill; the command is the orchestration shape, per `command-orchestration-convention.md`) |
| Public/private boundary | `.claude/references/build-in-public.md` |

**Notion database IDs** (parent page NYC AI Event Content Hub `338d3699c2db808781d5d4675dcc5e33`):
Events `collection://9dcbc999-b4ed-4a51-b48a-10aaf171f1ba` · People `collection://4a1af67f-9141-4ba5-aa9d-88b07dcd5f86` · Companies `collection://d5910dc3-8327-4b49-9294-fc9499709a98` · Topics `collection://d61ce9df-94b3-4637-aa09-d77e09ab3a74` · Content Drafts `collection://6c24c9f5-66c9-4eed-a61d-3f9b87c3f775` · Project Ideas `collection://0956e6ed-8555-4d8f-8856-388966dedaab` · Roles `collection://3a174257-e90b-48be-b4bb-097ba5dc4231` · To-dos `collection://1cd6d576-8a9e-4332-bb81-13a28b55f151`. Live schema is the source of truth: `notion-fetch` before batch creates.

**Supabase:** org `A.Yedi`, project `empire state ai` (`oicikjyzmxqfomrrqkvf`), REST with `SUPABASE_API_KEY` from `.env`.

## 4. Invariants

These protect irreversible external effects. They do not get waived.

1. **PII boundary (ADR-9).** Email and phone never enter the Supabase spine; contact detail lives in HubSpot. Every spine write goes through `.claude/scripts/spine_client.py` (hard-fail guard); no hand-rolled curl, no MCP DML. Run `--selftest` and `--check-writers` before any spine PR. A flaw in any layer of a privacy control is a defect even when a backstop would catch it; a diff touching guard, filter or allowlist files gets human review.
2. **Supabase MCP is read-only.** Writes via REST + `spine_client.py`; DDL via dashboard from repo migrations after a twin rehearsal; the connector for `SELECT`, `list_*`, `get_advisors` only (write tools denied in `.claude/settings.json`).
3. **One writer per event.** `.claude/hooks/event-claim.py claim "<event>"` at Step 1.0 of `/event-deep-research` and `/post-event-content` (exit 3 = held; claims expire after 4h). A second session that finds a run in progress goes read-only and reports. Duplicate effort is cheap; contradictory records that later runs read as fact are not.
4. **Public repos, private inputs.** Both repos are public by design. `.env`, `me-model.md`, `target-companies.md`, inbox lists and other people's confidences never enter git; redact off-the-record material in the transcript and every derived file before commit. Never rewrite history to fix a leak without Alex.
5. **MCP writes run in the parent thread.** claude.ai connectors (Notion, HubSpot, Calendar, Gmail) are not available for writes inside subagents; do every write inline. Subagents are for web research and text synthesis. A declared read tool may be delegated.
6. **Subagents cannot spawn subagents.** Fan-out runs from the parent thread; every agent declares a minimal `tools:` line.
7. **The agent registry is session-frozen.** Any edit to `.claude/agents/**` needs a fresh session to test.
8. **Search before create** in Notion and HubSpot (name + company; email is HubSpot's key). Notion has no native dedup.
9. **HubSpot writes are post-event, selective, create-once**, with an inline confirmation table.

## 5. Working rules

**Git.** Branch → PR → merge for anything that adds or changes a skill, agent, command, hook, reference, schema or data contract; trivial churn (content outputs, typos) may go straight to `main`. One live session per checkout; worktrees for real parallelism, cut from `origin/main`, with `.env` symlinked in. The `main` checkout stays on `main`. Shared namespaces (ADR numbers, the Notion roadmap, this file, Linear status) are edited from one session at a time. PR the same hour you stop. When git and Linear disagree, git is the fact and Linear gets corrected. When branches need converging, one session runs `reconciliation-terminal-charter.md` and nobody else builds.

**Linear holds build work that ships as a PR; to-dos live in Notion.** Linear issues for workstreams; the close of a build is a comment on its issue with the PR link. Do not mirror issue state into this file. Canceling an issue auto-closes a PR that says "Closes YED-n": merge first.

**Build discipline lives in the PR template** (`.github/pull_request_template.md`): spec before code (PRD for product builds, ADR or in-repo reference for infra and data-contract changes), Linear issue linked, one adversarial pass. No waiver log, no close-out ritual. Run `/judge-build` only on the artifact-class triggers in `.claude/skills/judge-build/SKILL.md` (one Sonnet reviewer; it flags, it does not gate; spec `.claude/references/judge.md`). A merged PR can still leave work uncommitted: sweep `git status`.

**Never report a metric without its do-nothing baseline** (the null-baseline rule).

**Second-fix stop rule** (`second-fix-stop-rule.md`). On the second fix to the same component in one workstream, judge round 3+, or a Linear issue whose purpose is to follow up something built in the last 7 days: stop patching and ask `alex:cto-principal-architect` one question, "is this a design problem, and what should we remove?" Removal and revert are first-class outcomes.

**Every build removes a named friction on the publishing path.** Speculative architecture with no publishing friction behind it is skipped. A new hook, gate, judge seat, ledger or dashboard needs a named product failure observed at least twice.

**Size ceiling, held by Alex, no enforcement hook.** This file stays ≤1,800 words. At most 3 wired project hooks, none that can block a turn. After the paydown, additions to this file, the hook set, references, agents, commands and skills are one-in-one-out: name what the new thing replaces.

**Automation defaults.** MCP calls to vendors Alex already pays for (Notion, HubSpot, Linear, Canva, Supercut) are automated inside workflows; steps that need his judgment (a contact landing in CRM, copy going public, strategy) stay manual; don't burn Claude tokens on redundant inference or oversized contexts. **Starting a workflow unprompted:** research, drafting and analysis auto-fire when the moment matches; workflows with a built-in approval gate auto-start and pause there; publishing, CRM writes and credit spend (Apollo, Clay) wait for Alex. Unsure → the more cautious tier. "Proceed without prompting" raises the ceiling for that batch.

**Parked thoughts and to-dos** go to the Notion To-dos database (on the roadmap page) in the same turn: anything owed after today, by Alex or a later session, gets a row with Who, Due, Why and Context, plus a Linear link if it ships as a PR. No free-floating "revisit later."

## 6. Content

Voice, structure and anti-patterns live in `content-style-guide.md` and `content-anti-patterns.md` (living documents, updated through `update-voice-and-style`). Connection notes follow `outreach-templates.md`; shared shapes (two-thesis synthesis, visual briefs, goal tagging, founder showcase) live in `.claude/skills/content-patterns/`. Steer before generating (`steering-interview`), generate, comment in Notion, mine the comments back into the guides.

Pipeline contracts that are not voice rules:
- Every post ships **3 inline variants**; connection notes ship **2** (A talk-anchored, B adjacent-work-anchored; 200-char cap; only ship a variant with a real anchor). Ship all variants to Notion `needs_review`; never pre-select.
- **Notion first.** Drafts and variants go to Content Drafts as plain paragraphs (never code blocks); the local event folder holds inputs and rendered finals (carousel HTML/PDF) only.
- Every post ships with a **3–5 slide visual brief** that adds information (`visual-briefs.md`); Claude-authored HTML/SVG → headless Chrome → 4:5 PDF. Gemini for pictorial imagery. No Gamma.
- **Source-check any firm- or person-level thesis claim** (the old "Rule 12") before it appears in public copy; unsourced → verify, soften or cut.
- The **Upcoming Week roundup** is built from event briefs only and sets the table without taking a side.
- Once Alex has **scheduled** a post, it is frozen; record the chosen variant on the draft and wait for the published copy.
