# Empire State Events Pipeline — Project Brief

**Last updated:** 2026-04-20
**Phase:** Active build — `gtm-os` (V1 extension + H1 HockeyStack mirror) on Vercel Workflow DevKit. Learning-mode protocol engaged: explain primitives, decisions, and tradeoffs as we build.
**Status:** Three projects active (gtm-os, eval-harness, scaffold-skill). Project cap removed. Scaffolding kickoff: Monday.

---

## 2026-04-20 Update — Active Build Plan + Project Cap Removal

### Decision log — project cap removed (2026-04-20)
The `max 2 active projects` hard gate (originally enforced by the `project-ideation` skill's Step 0) has been **removed**. Rationale: cramming logically distinct projects into an arbitrary slot limit was producing awkward bundling rather than the intended bandwidth discipline. Active projects are now tracked by the `Status` select on Project Ideas only. Bandwidth is managed manually by Alex.

Files updated:
- `CLAUDE.md` line 136 — active project tracking reworded
- `CLAUDE.md` lines 206-207 — ideation skill gate language flipped to "awareness, not a gate"
- `.claude/skills/project-ideation.md` — Step 0 rewritten as awareness surface, blocking error case removed
- `.claude/references/pipeline-operations-guide.md` lines 84, 95, 220 — gate language removed

### Three active projects (written to Notion Project Ideas, 2026-04-20)

| Project | Type | Complexity | Composite | Notion page |
| --- | --- | --- | --- | --- |
| `gtm-os` — Event Pipeline Agent Extension + HockeyStack Revenue Agent | feasible | MVP | **9.50** | [348d3699-c2db-81f4-8b79-c0a03d6bef33](https://www.notion.so/348d3699c2db81f48b79c0a03d6bef33) |
| `eval-harness` — LLM-as-Judge Quality Harness for Event Pipeline Skills | feasible | small_tool | 8.50 | [348d3699-c2db-81b6-bf38-d4e360419c82](https://www.notion.so/348d3699c2db81b6bf38d4e360419c82) |
| `scaffold-skill` — Ideation-to-Execution Automation | stretch | small_tool | 7.33 | [348d3699-c2db-81c0-a185-d29080996a01](https://www.notion.so/348d3699c2db81c0a185d29080996a01) |

### Priority sequence
1. **`gtm-os`** is the primary build this week. It's directly tied to the Vercel Workflows event and the HockeyStack Rebuilding GTM event — both in the same window. Monday scaffolding starts with `vercel-labs/knowledge-agent-template` seed (Option B: Seed Then Extend, same repo).
2. **`eval-harness`** picks up next after `gtm-os` V1 ships — pairs naturally because we'll have real skill runs to evaluate.
3. **`scaffold-skill`** is stretch, incubates in the background, not on the critical path for either event.

### V1 expansion (recorded 2026-04-19/20)
Original V1 (contact research only) expanded to fill two gaps:
- **Gap 1:** No agent-driven company data refresh — companies go stale after initial enrichment.
- **Gap 2:** `generateDMDraft` runs without deep per-contact company context.

Expanded V1 = parallel fan-out across companies AND contacts, gated by ≤5 concurrent (rate-limit safety), with DM generation consuming the enriched company context.

### Learning-mode protocol (engaged)
> *"the point of this is becoming fluent in Workflow, Vercel, and being able to speak to this granular knowledge at the event and going forward is a core purpose of this effort"* — Alex, 2026-04-19

As we build `gtm-os`, I will:
- Explain each WDK primitive (`'use workflow'`, `'use step'`, `defineHook`, `createWebhook`) at the moment we first use it — what it is, what it replaces, why it matters.
- Flag the non-obvious gotchas live (e.g. `globalThis.fetch = fetch` override, same-file step discovery, single-use webhook URLs).
- Pause before each architectural decision and lay out tradeoffs. No silent choices.
- Reference the canonical source of truth: `gtm-os/Vercel_Workflow_SDK_Best_Practices.md`.

### Primitives cheat sheet (for the live explanation)

| Primitive | What it is | When we'll use it first |
| --- | --- | --- |
| `'use workflow'` | Marks a function as a durable, resumable workflow entry point | Top of `eventEnrichmentWorkflow` |
| `'use step'` | Marks a function as an atomic, retriable unit with auto-persisted return values | Every API call, LLM call, DB write inside the workflow |
| `defineHook<T>()` + `for await` | Long-lived event-driven actor that processes events sequentially per token | Outbound / Deal / Customer agents (H1) |
| `createWebhook()` | Returns a URL + pausing promise — workflow suspends until the URL is hit | Human-in-the-loop approval gates |
| `generateObject({ schema })` | AI SDK structured output with Zod-enforced shape | Company enrichment, DM drafts |
| `FatalError` / `RetryableError` | Control retry behavior — fatal stops the workflow, retryable takes custom delay | Auth failures (fatal), 429 rate limits (retryable) |
| `getWritable()` / `run.readable` | Stream intermediate results to the frontend in real time | Live demo UI during events |
| Postgres + Drizzle | Production state store; in-memory Map for local dev | State that must outlive a single run |

### Monday scaffolding — Step 1 preview
1. Clone `vercel-labs/knowledge-agent-template` locally into `gtm-os/`.
2. Walk the directory structure together — identify which files map to which primitive.
3. First durable workflow run end-to-end, observe replay behavior on step return values.
4. Commit the seed. From there, every change is attributable to our build on top of the template.

---

## 2026-04-18 Update — Content Workflow + Knowledge Base Plan

### Completed today (Phase 1+2 of knowledge base architecture)
- Added `archived` (gray) as 5th option on Content Status select property
- Created **🎯 Active Kanban** view (Board, grouped by Content Status, filter: Status ≠ archived)
- Created **🗄 Archive** view (Table, filter: Status = archived)
- Decision logged: **no separate archive DB**. Archived content stays in Content Drafts to preserve
  relation graph (Events/People/Topics/Project Ideas) — critical for Phase 3-6 knowledge base mining.
- Deferred: Select → Status property type migration (optional UI change, 2 clicks, skipped to avoid
  type-change risk via MCP DDL).

### Status flow (single DB, single property)
`needs_review → approved → scheduled → published`
`archived` is reachable from any state. Terminal.

### Phase 3-6 Handoff — Knowledge Base Evolution Loop
Alex's next steps: ship next week's pre-event content through the new Kanban, accumulate
published/archived drafts for ~1 week. Then resume here to build:

- **Phase 3 (45 min):** Create `Insights` database — atomic timestamped observations with
  relations to Events/People/Topics/Companies/source Content Draft. Schema TBD in that session.
- **Phase 4 (3-4 hrs):** Build `post-content-synthesis.md` skill. Triggered when a draft moves
  to `published` or `archived`. Extracts 2-5 atomic insights, writes to Insights DB, proposes
  updates to affected Topics entries (human-reviewed, never auto-written).
- **Phase 5 (1-2 hrs):** Test synthesis on 2-3 real drafts Alex has generated by then.
- **Phase 6 (1 hr):** Wire Insights pull into `event-research.md` so pre-event research is
  primed by prior observations on adjacent topics/people/companies.

### Architecture pattern (reference for Phase 3-6 session)
- Topics DB = aggregated / evergreen summary, updated in place per topic
- Insights DB = atomic / immutable observations, append-only, tagged
- Synthesis skill is the bridge between Content Drafts (where insight is captured)
  and Topics + Insights (where insight compounds)
- Ref: Zettelkasten (atomic notes) + Matuschak's evergreen notes pattern

### Gotchas to re-read at Phase 3-6 kickoff
- 🔴 Never auto-update Topics — always propose and wait for human review
- ⚠️ Insights dedup is the real scaling risk, not draft dedup — synthesis must search before creating
- ⚠️ Atomic insight discipline (one obs + evidence + tags) or the DB rots into another drafts pile
- ⚠️ Notion relation rendering slows at ~1,500+ rows with 4+ relations (year 2 problem, flag only)

---

## Original Phase 1 Status (preserved for history)

---

## Objective

Turn Alex's event calendar into an intelligence layer — pre-event research, networking
prep, content creation, and CRM management — via a Claude Code skill with direct MCP
writes to Notion and HubSpot.

## Current State

- **CLAUDE.md**: Updated with all verified system state (Notion schemas, HubSpot permissions,
  Apollo credits, write orchestration sequences)
- **Skill file**: `.claude/skills/event-research.md` — complete 7-step workflow
- **Notion**: 5 databases live with correct schemas (verified via MCP)
- **HubSpot**: Fresh account, full read/write on Contacts, Companies, Notes
- **Apollo**: Connected, credits verified (110 lead, 5000 AI)
- **.gitignore + .env**: Created, .env properly ignored

## Architecture Decisions (2026-04-09)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Runtime | Claude Code skill file | Zero deployment surface, full MCP access, iteration speed |
| HubSpot event tracking | Notes on contacts | Static lists not writable via MCP |
| Apollo enrichment | Speakers only (default) | Conserve lead credits, AI research is free |
| Calendar Source property | Dropped | Pipeline value not gated by attendance |
| Calendar Description | Text property on Events | Stores raw invite for reference |
| Long-form content | Notion page body | Properties for structured data, body for research |
| Dedup strategy | Search before create | Notion has no native dedup; HubSpot dedupes on email |

## Time Investment Estimate

| Phase | Estimated | Actual | Notes |
|-------|-----------|--------|-------|
| Schema fixes + setup | 45 min | ~30 min | Done |
| Skill file build | 3-4 hours | ~1 hour | Done (first draft) |
| Test: parse + research | 1-2 hours | — | Next |
| Test: Notion writes | 1-2 hours | — | Next |
| Test: HubSpot writes | 1 hour | — | Next |
| Test: Apollo enrichment | 30 min | — | Next |
| Buffer | 2-3 hours | — | — |
| **Total** | **9-13 hours** | | |

## Open Questions

1. Apollo credit refresh: Do free plan credits refresh monthly? Monitor at next billing cycle.
2. Notion text property length limits: Will Calendar Description or other text fields
   truncate long invite text? Test with a real invite.
3. HubSpot custom property: `event_associations` text field discussed but not yet created.
   Notes approach may be sufficient — decide after first test.

## Tech Debt Log

- None yet (greenfield)

## Gotchas (from CTO review)

- Notion relation writes require exact page URLs, not IDs
- Notion has no dedup — skill must search before creating
- HubSpot dedupes on email — creating contacts without email then enriching later risks duplicates
- Apollo People Match needs name + company minimum for reliable matching
- WebSearch in rapid succession may feel slow — research should be presented incrementally

## Next Steps

1. Alex adds Calendar Description property back to Notion Events database
2. Test skill on a real upcoming event (paste invite, run full workflow)
3. Iterate on research quality based on first test
4. Verify Notion write orchestration works end-to-end (relations especially)

## Handoff Summary

CTO architecture review complete. Skill file built at `.claude/skills/event-research.md`.
All system state verified via live MCP calls. CLAUDE.md updated with ground-truth schemas,
credit pools, and orchestration sequences. Ready for first live test — Alex needs to add
Calendar Description property to Notion Events database, then paste a real calendar invite
to test the full pipeline.
