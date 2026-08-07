# Empire State Events Pipeline — Workflows Reference

This document is the rerun manual for the four pipeline workflows. Read top to bottom to understand the system; jump by section when re-running a specific workflow.

**Status legend:**
- ✅ **Wired** — fully built, tested, ready to run
- 🟠 **Built, validation blocked** — files exist, but runtime invocation has a known gap (see "Known gap" below)
- 🟡 **Scaffolded** — command file exists with documented triggers/inputs/flow, agent wiring not yet executed end-to-end
- ⚪ **Future** — referenced but not yet started

| Workflow | Status | Command | Purpose |
|---|---|---|---|
| **A.0 — Calendar Auto-Ingest** | ✅ Wired (validated 2026-05-20) | `/check-new-events` | Thin wrapper on top of A — detects PIPELINE-block events in "Going to Events" GCal, dedups, then loops A + pre-event-content with continue-or-quit between events |
| A — Event Deep Research | ✅ Wired (synthesizer pivot landed 2026-05-07 — fan-out runs in parent thread) | `/event-deep-research` | Pre-event: parse invite → 4-specialist parallel fan-out → synthesizer → Notion + HubSpot |
| B — Post-Event Synthesis | 🟡 Scaffolded | `/post-event-synthesis` | Post-event: transcripts/notes → DMs + posts + retro |
| C — Weekly Recap | 🟡 Scaffolded | `/weekly-recap` | Sunday: upcoming-week post + cross-event synthesis |
| D — Voice Pass | 🟡 Scaffolded | `/voice-pass` | Polish: voice-editor over `needs_review` Content Drafts |

### Commands added since (2026-05 → 2026-07) — not part of the original four-workflow spine

The four workflows above are the pipeline core. These commands were built afterward and were not
reflected in this table until the 2026-07-11 refresh (the doc had drifted ~2 months behind reality).

| Command | Status | Purpose |
|---|---|---|
| `/post-event-content` | ✅ Wired | Day-to-day post-event: manual transcript → conditioning → `post_event_brief` → content-correspondent drafts. (The live B path; `/post-event-synthesis` is the deferred fuller chain.) |
| `/ingest-recording` | ✅ Wired | Event `.m4a` → ElevenLabs scribe_v2 roster-seeded clean transcript (feeds `/post-event-content`). |
| `/evergreen-deep-dive` | ✅ Wired | Presenter-level evergreen deep-dive posts, decoupled from event timing (content bank). |
| `/interview-prep` | ✅ Wired | **Market-Intelligence Engine — Milestone 1 (Job-Search lens).** 4-axis dossier → judge-gate → Postgres spine + Notion. |
| `/scan-trends` · `/scan-roles` · `/scan-voices` | ✅ Wired | Signal scanners (skills `trend-radar` / `role-radar` / `voice-radar`), Notion-only, HITL, legitimate-sources only. |
| `/judge-build` | ✅ Wired (advisory) | LLM-as-judge scores a build artifact vs `build-quality@1`; writes run-log + calibration ack. Advisory until ≥20 runs @ ≥80% agreement. |
| `/dod-close` | ✅ Wired (2026-07-11) | Closes a non-trivial build against the DoD gate; writes `dod_met`/`dod_waived`/`correction_rounds` to telemetry via `.claude/hooks/dod-close.sh`. The writer that closed the rigor loop. |
| `/rigor-review` | ✅ Wired (first run pending) | Weekly ≤10-min learning loop over build-sessions + judge log + waivers + outcomes; proposes codified fixes. |
| `/tag-outcome` | ✅ Wired | Manual outcome-tagging ritual — closes the acted-on-value loop (Goal vs realized Outcome). |
| `/systems-analyze` | ✅ Wired | Dispatches `systems-analyst` for the eight-phase Meadows diagnostic (Workflow E). |
| `/toolbox` | ✅ Wired | Discovery — lists the toolkit. |
| `/run-market-landscape-study` · `/analyze-competitive-landscape` · `/create-messaging-brief` · `/generate-channel-copy` · `/test-and-report` | ✅ Built (thin docs, 2026-07-02) | Imported market-research + copywriting command suite; no PRD/Linear yet (candidate for retro-codification). |

> **Market-Intelligence Engine** is its own arc (spine + `/ops/market-intel` dashboard in the
> `empire-state-hub` repo). Source of truth: `.claude/references/roadmap.md` +
> `.claude/references/market-intel-spine.md`. **Rigor/measurement layer** source of truth:
> `.claude/references/{roadmap,build-session-contract,value-action-registry}.md`.

---

## ✅ Resolved 2026-05-07 — orchestrator → synthesizer pivot

**Root cause confirmed:** subagents cannot spawn other subagents. This is an Anthropic SDK runtime constraint, not a config gap or a prompt-level instruction problem.

> "Subagents cannot spawn other subagents. If your workflow requires nested delegation, use Skills or chain subagents from the main conversation." — [code.claude.com/docs/en/sub-agents.md](https://code.claude.com/docs/en/sub-agents.md)

**How we got here:**

- 2026-05-05: original `event-research-orchestrator` validation run produced a high-quality brief but the orchestrator did inline `WebSearch` instead of fanning out — diagnosed at the time as either a prompt-language issue or a tool-whitelist issue.
- 2026-05-05: Fix 1 (`tools: Task, Read` whitelist on orchestrator) applied + reverted same day — `Task` was removed entirely while `WebSearch` survived; tool whitelist filters against MCP namespace, not SDK primitives.
- 2026-05-06: parent-level fan-out test confirmed parent dispatch works cleanly.
- 2026-05-07 (Fix 3 verification run): orchestrator was re-invoked from a fresh conversation. Orchestrator's own audit reported `Task invocations: 0` and admitted the violation honestly: `"Task tool: absent from tool surface (not deferred, not loaded)... ToolSearch for 'select:Task' returned 'No matching deferred tools found'... specialist fan-out via Task dispatch was architecturally impossible in this invocation."`
- 2026-05-07 (layer-by-layer diagnostic): tool surfaces of all 6 relevant agents reported in parallel. `Task`/`Agent` was absent from EVERY subagent's surface — orchestrator AND all four specialists AND notion-writer. Confirmed via `ToolSearch select:Task,Agent` → "No matching deferred tools found" in 5/5 attempts.
- 2026-05-07 (claude-code-guide research): official Anthropic docs confirmed the constraint is by design ("prevents infinite nesting") and not configurable. `Task` was renamed to `Agent` in v2.1.63; both names are aliases.

**Pivot landed (2026-05-07):**

- `event-research-orchestrator` deleted; replaced by `event-research-synthesizer` (text-in, brief-out, no `Task`/`WebSearch` contract).
- Slash command (`/event-deep-research` Step 2) now fans out the four specialists in parallel **from the parent thread** — where `Agent` IS available. Step 2.5 dispatches the synthesizer.
- `notion-writer` had a separate "Prompt is too long" failure (Haiku model + inherited 250-tool deferred list). Fixed by scoping `tools:` frontmatter to Notion MCP + Read only.
- All four specialists got `tools: WebSearch, WebFetch, Read` for hygiene.

**Architectural rule (now codified in CLAUDE.md):** any "orchestrator" pattern that needs to fan out specialists must run from the parent / slash command thread, not from inside another subagent. Synthesis-only agents (text in, text out) are fine as subagents — they don't need dispatch capability.

**Artifacts of record:** `.claude/artifacts/orchestrator-fanout-diagnosis.md` (original diagnosis), `.claude/artifacts/orchestrator-validation-comparison.md` (side-by-side from 2026-05-05 run).

---

## How the four workflows fit together

```
                         ┌─────────────────────────┐
                         │  Calendar invite drops  │
                         │   (paste into chat)     │
                         └────────────┬────────────┘
                                      ▼
   ┌────────────────────────────────────────────────────────────┐
   │  Workflow A — /event-deep-research                          │
   │    parse → triage → 4-agent fan-out → brief → Notion/HS    │
   └────────────────────────┬───────────────────────────────────┘
                            ▼
              ┌─────────────┴──────────────┐
              ▼                            ▼
   ┌──────────────────┐         ┌──────────────────────┐
   │ pre-event-content│         │  project-ideation    │
   │  (existing skill)│         │  (existing skill)    │
   │  → DMs + posts   │         │  → 3 project ideas   │
   └────────┬─────────┘         └──────────────────────┘
            ▼
   ┌──────────────────────┐
   │  Workflow D —        │
   │  /voice-pass         │  ◀──── (over any Content Drafts in needs_review)
   └──────────────────────┘
            ▼
        [ATTEND EVENT]
            ▼
   ┌────────────────────────────────────────────────────────────┐
   │  Workflow B — /post-event-synthesis                         │
   │   transcripts/notes → transcript-analysis → objection-mining│
   │   → commercial-insight-generator → content-correspondent    │
   │   → pattern-synthesis (if 2 briefs disagree)                │
   └────────────────────────┬───────────────────────────────────┘
                            ▼
   ┌────────────────────────────────────────────────────────────┐
   │  Workflow C — /weekly-recap (Sunday)                        │
   │   queries Notion → upcoming-week post + synthesis post      │
   │   → /voice-pass over everything → all to needs_review       │
   └────────────────────────────────────────────────────────────┘
```

---

## Workflow A — `/event-deep-research` ✅ WIRED

The full pre-event research pipeline. Replaces the monolithic `event-research` skill flow with multi-agent fan-out.

### Triggers
- Alex pastes a calendar invite description in chat
- Alex says: "research this event", "deep research on [event]", "run the event pipeline", "do event-research on [event]"
- Alex types `/event-deep-research` followed by invite text

### Required inputs
1. **Event invite text** — pasted invite description, OR natural-language description with cues like "Speaker: Jane Smith, CTO at Acme; Topics: agentic systems, enterprise AI"
2. **(Optional) Stated focus** — e.g., "I'm hunting hiring managers" or "I want to test my POV on agentic systems" — feeds Success Signals tailoring

### Flow

| Step | Where it runs | What happens | Output |
|---|---|---|---|
| 1 | Main conversation | Parse invite into entities (Event/People/Companies/Topics); confirm with Alex | Confirmed entity list |
| 1.5 | Main conversation | Dedup search Notion (5 DBs) + canonicalize names + classify NEW/REFRESH/SKIP per entity, present plan, get approval | Triage plan |
| 2 | Main conversation (parallel fan-out) | Dispatch 4 specialists in parallel from the parent thread (subagents cannot dispatch sub-agents per Anthropic SDK design): `company-researcher`, `person-researcher`, `topic-landscape-analyst`, `competitive-signal-scanner` | 4 specialist returns |
| 2.5 | `event-research-synthesizer` agent (sonnet) | Reconciles cross-references; surfaces verification flags; writes Quick Take, Success Signals, Documentarian Angle; formats brief in Step 3 schema | Assembled brief |
| 3 | Main conversation | Present brief, iterate with Alex | Approved brief |
| 4 | `notion-writer` agent (haiku) | Dependency-ordered writes: Companies → Topics → People → Event → Content Draft per Step 4 of event-research SKILL.md | Notion confirmation block + page URLs |
| 5 | Main conversation | HubSpot recurrence check + Companies + Contacts (with associations) + Notes (event name body) | HubSpot confirmation block |
| 6 | Main conversation | Final summary | Summary report |

### Agents involved
- `event-research-synthesizer` (sonnet) — assembles brief from 4 specialist returns; text-in, brief-out; no dispatch capability by design
- `company-researcher` (sonnet) — per-company depth; `tools: WebSearch, WebFetch, Read`
- `person-researcher` (sonnet) — per-person depth + talking points + prioritization signals; `tools: WebSearch, WebFetch, Read`
- `topic-landscape-analyst` (sonnet) — 5-dimension topic research; `tools: WebSearch, WebFetch, Read`
- `competitive-signal-scanner` (sonnet) — cross-company recency, last 60 days; `tools: WebSearch, WebFetch, Read`
- `notion-writer` (haiku) — dependency-ordered MCP writes; `tools:` scoped to Notion MCP + Read only (prevents Haiku context overflow from inheriting full deferred-tool list)

All under `.claude/agents/research/` and `.claude/agents/ops/`.

### Notion writes (5 DBs, in order)
1. Companies (`d5910dc3-...`) — parallel-safe with Topics
2. Topics (`d61ce9df-...`) — parallel-safe with Companies
3. People (`4a1af67f-...`) — needs Company URLs from #1
4. Events (`9dcbc999-...`) — needs People + Companies + Topics URLs
5. Content Drafts (`6c24c9f5-...`) — needs Event URL; creates the `research_brief` Content Type

### HubSpot writes
1. Companies (recurrence check first; create or refresh — never touch `industry`)
2. Contacts (with company associations; never overwrite email/phone/firstname/lastname)
3. Notes (event name as body, attached per contact — primary event-tracking mechanism)

### Where the methodology lives
- **Multi-step orchestration shape:** [.claude/commands/event-deep-research.md](commands/event-deep-research.md)
- **Per-step research/write methodology:** [.claude/skills/event-research/SKILL.md](skills/event-research/SKILL.md) — read this for actual property schemas, write semantics, gotchas
- **Methodology references** (orchestrator and topic-landscape-analyst draw from these):
  - [research-brief-blueprint](skills/research-methodology/research-brief-blueprint/SKILL.md)
  - [market-scenario-modeler](skills/research-methodology/market-scenario-modeler/SKILL.md)
  - [insights-repository-kit](skills/research-methodology/insights-repository-kit/SKILL.md)
  - [market-signal-tracker](skills/company-deep-research/market-signal-tracker/SKILL.md)
  - [battlecard-library](skills/company-deep-research/battlecard-library/SKILL.md)

### Common follow-ons
After A completes, the natural next moves:
- **Pre-event content** → invoke `pre-event-content` skill (it pulls the brief from Notion)
- **Project ideation** → invoke `project-ideation` skill (it pulls topics + event from Notion)
- **Step 7 retro** (after attending) → see Workflow B

### Failure modes
- Subagent returns thin output → re-invoke just that one with deeper scope
- Orchestrator times out → split: 2 specialists at a time, then merge
- Triage plan disagreement post-hoc → re-invoke specific subagent with corrected path
- notion-writer schema validation error → trust API error text; verify with `notion-fetch` on data_source URL

---

## Workflow B — Post-Event

Two paths exist:

- **B-active — `/post-event-content`** ✅ WIRED (manual-upload anchored since 2026-05-27; `post_event_brief` first-class artifact added 2026-05-28). The day-to-day post-event flow. Manual transcript paste → `transcript-conditioning` (Step 3.5) → **`post_event_brief` synthesis (Step 3.7 — the data store / short-term memory)** → `content-correspondent` drafts Tier 1 comment + Tier 2 primary post (pre→post bridge) + Tier 2 alternate + bucket-sorted outreach DMs → optional Gamma carousel render → `notion-writer` commits all rows. The brief is the post-event mirror of the pre-event `research_brief`; every downstream draft references it in its body. Granola auto-fetch path retained but DISABLED (app nonoperational on Alex's device).
- **B-scaffolded — `/post-event-synthesis`** 🟡 (below). The larger systemization with transcript-analysis → objection-mining → commercial-insight-generator → content-correspondent → pattern-synthesis chained automatically. Not yet wired end-to-end.

### `/post-event-synthesis` 🟡 SCAFFOLDED

Turns post-event raw material into structured intel + content drafts.

### Triggers
- Alex says: "just got back from [event]", "back from [event]", "wrapped up [event]"
- Alex pastes a Granola/Wispr transcript, voice notes, or freeform recap
- Alex says: "post-event content for [event]", "synthesize last night", "turn my notes into content"

### Required inputs
1. **Raw material** — Granola transcript, Wispr voice notes, freeform recap, photos with captions
2. **Event name** (so the original brief can be pulled from Notion)
3. **(Optional) Contact list** — names Alex met that should get DMs

### Planned flow (not yet wired end-to-end)

```
1. Pull research brief from Notion (main conversation)
2. transcript-analysis skill → action items, themes, quotes, objections
3. objection-mining skill → friction signals
4. commercial-insight-generator agent → documentarian thesis / Reframe
5. content-correspondent skill → bucket-sort contacts (A/B/C), draft DMs, Tier 1 comments, Tier 2 post
6. pattern-synthesis skill (only if ≥2 briefs in last 7 days have opposing theses)
7. /voice-pass over all generated drafts (Workflow D)
8. Write all to Notion Content Drafts with Event Phase = post_event, Status = needs_review
```

### What works today
- `content-correspondent` skill is the existing path — it works standalone
- `transcript-analysis`, `objection-mining`, `commercial-insight-generator` are imported and callable individually

### What's not wired yet
- The chained orchestration (steps 2 → 3 → 4 → 5 → 6)
- Programmatic detection of "opposing theses" for pattern-synthesis trigger
- Single-command entry point — today, run the steps manually or just call `content-correspondent`

### Where to look
- [.claude/commands/post-event-synthesis.md](commands/post-event-synthesis.md) — full TODO list + wiring decisions to make

---

## Workflow C — `/weekly-recap` 🟡 SCAFFOLDED

Sunday-cadence synthesis across the week's events, content, and outreach.

### Triggers
- Alex says: "weekly recap", "wrap the week", "build the Sunday post"
- Sunday evening (manual cadence today; future scheduled-task candidate)
- Alex asks: "what events do I have this week?" before content sprint

### Required inputs
- **None** — all inputs come from Notion queries
- **(Optional) Date range override** — for backfilling

### Planned flow (not yet wired end-to-end)

```
1. Query Notion: Events in upcoming 7 days + Content Drafts from past 7 days (status ≠ archived)
2. Group: upcoming events / attended events / drafts in flight
3. UPCOMING events → pre-event-content skill builds "The Upcoming Week" Sunday post
4. ATTENDED events → if ≥2 briefs have opposing theses, run pattern-synthesis (cap: 1/week)
5. /voice-pass over all drafts produced (Workflow D)
6. Write everything to Content Drafts with status = needs_review
7. Summary report: posts ready, events upcoming, drafts in flight, anti-signals fired
```

### What works today
- `pre-event-content` skill produces "The Upcoming Week" roundup standalone
- `pattern-synthesis` skill runs standalone given two briefs

### What's not wired yet
- The cross-week aggregation
- Programmatic "opposing theses" detection
- Cadence-rule enforcement (max 1 synthesis post / 7 days)

### When this becomes useful
After 3–5 events have been put through Workflow A. Building it before that operates on empty data.

### Where to look
- [.claude/commands/weekly-recap.md](commands/weekly-recap.md) — full wiring TODO

---

## Workflow D — `/voice-pass` 🟡 SCAFFOLDED

Polish layer over Content Drafts in `needs_review` status.

### Triggers
- Alex says: "voice pass", "polish my drafts", "run voice-editor"
- Drafts are stuck in `needs_review` and Alex wants a quality pass

### Required inputs
- **None** — defaults to scanning all `needs_review` drafts
- **(Optional) Specific Content Draft URL** or scope filter (by Content Type / date range)

### Planned flow (not yet wired end-to-end)

```
1. Query Notion: Content Drafts where Status = needs_review (+ optional filters)
2. For each, invoke voice-editor agent with content + style-guide.md + anti-patterns.md
3. voice-editor returns: severity (clean/minor/moderate/major) + specific before/after fixes
4. Group by severity, present to Alex
5. Apply accepted edits to Notion; optionally bump status to approved
```

### What works today
- `voice-editor` agent is imported and callable directly with pasted draft content
- `update-voice-and-style.md` and `update-anti-patterns.md` skills propagate style updates

### What's not wired yet
- The batch-query + per-draft loop
- Severity rubric definition
- Notion update flow (replace body wholesale vs. diff-style)

### Where to look
- [.claude/commands/voice-pass.md](commands/voice-pass.md) — full wiring TODO
- [.claude/agents/content/voice-editor.md](agents/content/voice-editor.md) — agent contract
- [.claude/references/content-style-guide.md](references/content-style-guide.md) — voice spec

---

## How to rerun any workflow

Each workflow has the same anatomy in its command file:
1. Trigger (when to run)
2. Required inputs (what to provide)
3. Step-by-step flow (where each step runs)
4. Agents involved
5. Where the methodology lives
6. Failure modes

If a workflow goes sideways:
1. Check the command file in `.claude/commands/<workflow>.md`
2. Check the agent contract in `.claude/agents/<category>/<agent>.md`
3. Check the underlying skill in `.claude/skills/<skill>/SKILL.md`
4. Check CLAUDE.md § Project Architecture for schema + DB IDs

The command file is the orchestration shape. The skill is the methodology. The agent is the role contract. They compose; if one drifts from the others, fix the drift.

---

## Quick reference — all imported assets

### Skills imported from alex-agents-skills (Tier 1)

**Research methodology** (`.claude/skills/research-methodology/`):
- `research-brief-blueprint/` — scoping + checklist
- `market-scenario-modeler/` — TAM/SAM/SOM, sensitivity
- `insights-repository-kit/` — research artifact governance

**Company deep research** (`.claude/skills/company-deep-research/`):
- `battlecard-library/` — per-company battlecard templates
- `market-signal-tracker/` — severity + confidence signal log
- `executive-briefing-kit/` — exec recap format

**Content quality** (`.claude/skills/content-quality/`):
- `voice-guidelines/` — tone/style/localization rules
- `message-architecture/` — hook banks, CTA playbooks
- `cold-email-personalization/` — personalization rubric

**Transcript intelligence** (`.claude/skills/transcript-intelligence/`):
- `transcript-analysis/` — extract from sales/event transcripts
- `objection-mining/` — friction signal extraction

**ICP research** (`.claude/skills/icp-research/`):
- `persona-development/` — buyer personas
- `account-qualification/` — account scoring + qualification

**Cold email** (`.claude/skills/cold-email/`):
- `copy-frameworks/` — battle-tested cold email structures
- `personalization-engine/` — signal detection + personalization layers
- `sequence-architecture/` — multi-touch sequence design

### Agents imported

**Research** (`.claude/agents/research/`):
- *Imported:* `insights-research-director`, `qualitative-field-lead`, `quant-insights-architect`, `market-insights-director`, `win-loss-analyst`, `battlecard-program-manager`
- *Custom (built for Workflow A):* `event-research-synthesizer`, `company-researcher`, `person-researcher`, `topic-landscape-analyst`, `competitive-signal-scanner`

**Content** (`.claude/agents/content/`):
- `voice-editor`, `copy-strategist`, `conversion-copywriter`, `cold-email-specialist`

**Sales methodology** (`.claude/agents/sales-methodology/`):
- `commercial-insight-generator`, `reframe-architect`, `mobilizer-mapper` (Challenger Sale)

**Ops** (`.claude/agents/ops/`):
- *Custom:* `notion-writer`

### Commands imported (in addition to the 4 workflow commands)

`.claude/commands/`:
- `create-messaging-brief` — copywriting kit
- `generate-channel-copy` — copywriting kit
- `test-and-report` — copywriting kit
- `run-market-landscape-study` — market research
- `analyze-competitive-landscape` — competitive intel

### References

`.claude/references/`:
- `research-analyst-prompt.md` — top-level analyst prompt (imported)
- `content-style-guide.md`, `content-anti-patterns.md`, `outreach-templates.md`, `pipeline-operations-guide.md`, `portfolio-tracker.md`, `stack-readme.md`, `systems-thinking-workflow.md` (existing)

---

## What's NOT here (intentionally — Tier 2 deferred)

Per Alex's decision (2026-05-04): Tier 2 imports skipped this round. Includes:
- `positioning-messaging`, `launch-marketing`, `media-relations` (GTM Marketing)
- `value-story-framework`, `cxo-briefing-kit` (Enterprise Sales)
- `vertical-solution-templates` (Growth Strategist)
- `partnership-bd`
- `business-intelligence/*`, `statistical-analyst/`

Bring in later when use cases warrant.

## What's NOT here (intentionally — automation deferred)

Per Alex's decision (2026-05-04): hooks and scheduled tasks deferred until commands are working. Future automation candidates:
- SessionStart hook → check Events with status=intake, surface count to Alex
- Stop hook on content-creating skills → auto-run /voice-pass on the just-created draft
- UserPromptSubmit hook matching "just got back from" → suggest /post-event-synthesis
- Scheduled task: Sunday 6pm → /weekly-recap
- Scheduled task: daily 8am → nudge if events with status=intake older than 24h

---

*Partial refresh 2026-07-11 — added the "Commands added since" table (the doc had drifted ~2 months behind; the MI Engine, signal scanners, judge/rigor layer, and market-research suite were all missing). The four-workflow body below is unchanged and still accurate.*

*Last updated: 2026-05-07 — orchestrator → synthesizer pivot landed ON DISK. Anthropic SDK constraint (subagents cannot spawn subagents) confirmed via official docs + 6-agent layer-by-layer test. Fan-out moved to parent thread; synthesizer is text-in/brief-out. `notion-writer` updated to `model: sonnet` + scoped `tools:` frontmatter. All 4 specialists got `tools: WebSearch, WebFetch, Read` for hygiene. **VALIDATION PENDING:** all changes were made mid-session, but the harness loads the agent registry at session start and freezes it — meaning none of these changes are visible in the current conversation's registry (confirmed when `notion-writer-v2` test failed with "Agent type not found" while the deleted `event-research-orchestrator` was still listed as available). End-to-end validation requires a FRESH conversation. Workflow A status: 🟠 → ✅ on disk; pending fresh-conversation validation.*
