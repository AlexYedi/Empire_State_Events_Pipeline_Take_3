# Empire State Events Pipeline — Workflows Reference

This document is the rerun manual for the four pipeline workflows. Read top to bottom to understand the system; jump by section when re-running a specific workflow.

**Status legend:**
- ✅ **Wired** — fully built, tested, ready to run
- 🟠 **Built, validation blocked** — files exist, but runtime invocation has a known gap (see "Known gap" below)
- 🟡 **Scaffolded** — command file exists with documented triggers/inputs/flow, agent wiring not yet executed end-to-end
- ⚪ **Future** — referenced but not yet started

| Workflow | Status | Command | Purpose |
|---|---|---|---|
| A — Event Deep Research | 🟠 Built, validation blocked | `/event-deep-research` | Pre-event: parse invite → multi-agent research → Notion + HubSpot |
| A (inline path) | ✅ Wired (proven 2026-05-04) | event-research SKILL.md inline | Same as A but without multi-agent fan-out — main conversation does research itself |
| B — Post-Event Synthesis | 🟡 Scaffolded | `/post-event-synthesis` | Post-event: transcripts/notes → DMs + posts + retro |
| C — Weekly Recap | 🟡 Scaffolded | `/weekly-recap` | Sunday: upcoming-week post + cross-event synthesis |
| D — Voice Pass | 🟡 Scaffolded | `/voice-pass` | Polish: voice-editor over `needs_review` Content Drafts |

---

## ⚠️ Known gap (discovered 2026-05-04)

**Custom agents in `.claude/agents/` are NOT discoverable by the Task tool mid-conversation.** Validation of the orchestrator on the Wednesday Agentics event failed at step 1 with: `Agent type 'event-research-orchestrator' not found. Available agents: claude-code-guide, Explore, general-purpose, Plan, statusline-setup, vercel-plugin:*`.

**Hypothesis:** Task tool's available `subagent_type` enumeration is set at conversation start. Custom `.claude/agents/*.md` files created mid-conversation are not picked up until a fresh conversation starts.

**Workaround for now:** Run Workflow A through the inline path (event-research SKILL.md Steps 1–7 executed in main conversation). This is what was used to produce the May 5–7 NYC event briefs successfully.

**Validation queued:** Open a fresh Claude Code conversation in this repo, then run the orchestrator via Task tool with `subagent_type: event-research-orchestrator` against the Wednesday Agentics event. If it resolves, the agents are picked up at conversation start as expected. See `.claude/artifacts/orchestrator-validation-handoff.md` for the ready-to-paste prompt.

**If a fresh conversation also fails to register the agents,** the architecture needs a different registration mechanism — likely either:
- Plugin namespace (`.claude-plugin/plugin.json` + agents under a plugin directory), or
- A different `agents/` location/format Claude Code's loader actually scans

That investigation is its own task.

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
| 2 | `event-research-orchestrator` agent (sonnet) | Fans out 4 specialists in parallel: `company-researcher`, `person-researcher`, `topic-landscape-analyst`, `competitive-signal-scanner`; reconciles cross-references; writes Quick Take, Success Signals, Documentarian Angle | Assembled brief |
| 3 | Main conversation | Present brief, iterate with Alex | Approved brief |
| 4 | `notion-writer` agent (haiku) | Dependency-ordered writes: Companies → Topics → People → Event → Content Draft per Step 4 of event-research SKILL.md | Notion confirmation block + page URLs |
| 5 | Main conversation | HubSpot recurrence check + Companies + Contacts (with associations) + Notes (event name body) | HubSpot confirmation block |
| 6 | Main conversation | Final summary | Summary report |

### Agents involved
- `event-research-orchestrator` (sonnet) — top-level orchestrator
- `company-researcher` (haiku) — per-company depth
- `person-researcher` (haiku) — per-person depth + talking points + prioritization signals
- `topic-landscape-analyst` (sonnet) — 5-dimension topic research
- `competitive-signal-scanner` (haiku) — cross-company recency, last 60 days
- `notion-writer` (haiku) — dependency-ordered MCP writes

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

## Workflow B — `/post-event-synthesis` 🟡 SCAFFOLDED

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
- *Custom (built for Workflow A):* `event-research-orchestrator`, `company-researcher`, `person-researcher`, `topic-landscape-analyst`, `competitive-signal-scanner`

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

*Last updated: 2026-05-04 — initial workflow scaffold.*
