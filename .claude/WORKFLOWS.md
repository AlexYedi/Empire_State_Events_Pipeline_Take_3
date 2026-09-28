# Empire State Events Pipeline — Workflows Reference

This document is the rerun manual for the pipeline workflows. Read top to bottom to understand the system; jump by section when re-running a specific workflow.

**Status legend:**
- ✅ **Wired** — fully built, tested, ready to run
- 🟠 **Built, validation blocked** — files exist, but runtime invocation has a known gap (see "Known gap" below)
- 🟡 **Scaffolded** — command file exists with documented triggers/inputs/flow, agent wiring not yet executed end-to-end
- ⚪ **Future** — referenced but not yet started

| Workflow | Status | Command | Purpose |
|---|---|---|---|
| **A.0 — Calendar Auto-Ingest** | ✅ Wired (validated 2026-05-20) | `/check-new-events` | Thin wrapper on top of A — detects PIPELINE-block events in "Going to Events" GCal, dedups, then loops A + pre-event-content with continue-or-quit between events |
| A — Event Deep Research | ✅ Wired (synthesizer pivot landed 2026-05-07 — fan-out runs in parent thread) | `/event-deep-research` | Pre-event: parse invite → 4-specialist parallel fan-out → synthesizer → Notion + HubSpot |
| B — Post-Event | ✅ Wired | `/post-event-content` | Post-event: transcript → conditioning → `post_event_brief` → drafts + outreach |

**Retired 2026-09-27:** the `/post-event-synthesis`, `/weekly-recap` and `/voice-pass` scaffolds (drafted 2026-05-04, never wired) were deleted. Their jobs already run elsewhere: post-event = `/post-event-content`; the Sunday "Upcoming Week" roundup = the `pre-event-content` skill; voice polish = the rules inside every content skill + Alex's Notion comment loop. YED-198 closed. Rebuild any of them only against a named publishing friction.

### Commands added since (2026-05 → 2026-07) — not part of the original workflow spine

The workflows above are the pipeline core. These commands were built afterward and were not
reflected in this table until the 2026-07-11 refresh (the doc had drifted ~2 months behind reality).

| Command | Status | Purpose |
|---|---|---|
| `/post-event-content` | ✅ Wired | Day-to-day post-event: Supercut transcript (or audio file / paste) → conditioning → `post_event_brief` → content-correspondent drafts. |
| `/ingest-recording` | ✅ Wired | Any event audio (phone `.m4a`, or a Supercut audio asset) → ElevenLabs scribe_v2 roster-seeded, diarized transcript (feeds `/post-event-content`). |
| `/interview-prep` | ✅ Wired | **Market-Intelligence Engine — Milestone 1 (Job-Search lens).** 4-axis dossier → judge-gate → Postgres spine + Notion. |
| `/scan-roles` | ✅ Wired | Job-search signal scanner (skill `role-radar`), Notion-only, HITL, legitimate-sources only. |
| `/judge-build` | ✅ Wired (advisory) | LLM-as-judge scores a build artifact vs `build-quality@1`; writes run-log + calibration ack. Advisory until ≥20 runs @ ≥80% agreement. |
| `/dod-close` | ✅ Wired (2026-07-11) | Closes a non-trivial build against the DoD gate; writes `dod_met`/`dod_waived`/`correction_rounds` to telemetry via `.claude/hooks/dod-close.sh`. The writer that closed the rigor loop. |
| `/rigor-review` | ✅ Wired (first run pending) | Weekly ≤10-min learning loop over build-sessions + judge log + waivers + outcomes; proposes codified fixes. |
| `tag-outcome` (skill) | ✅ Wired | Manual outcome-tagging ritual — closes the acted-on-value loop (Goal vs realized Outcome). Still invocable as `/tag-outcome`; the wrapper command file was pruned 2026-09-28. |

**Pruned 2026-09-28 (0–1 uses in 30 days):** `/evergreen-deep-dive`, `/scan-trends`, `/scan-voices` (+ skills `trend-radar`, `voice-radar`), `/systems-analyze` (call the `alex:systems-analyst` plugin agent directly), `/toolbox`, `/morning-refresh`, `/recompute-relevance` (the script `.claude/scripts/recompute_relevance.py` stays), and the imported suite `/run-market-landscape-study` · `/analyze-competitive-landscape` · `/create-messaging-brief` · `/generate-channel-copy` · `/test-and-report`. Recover any with `git checkout archive/pre-reset-2026-09-28 -- <path>`.

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

**Where the record lives:** `.claude/references/sdk-runtime-constraints.md` (the resolved diagnostic; the May 2026 one-off diagnosis/validation artifacts were pruned 2026-09-28 and are recoverable from tag `archive/pre-reset-2026-09-28`).

---

## How the workflows fit together

```
   Calendar invite
        ▼
   Workflow A — /event-deep-research   (parse → triage → 4-agent fan-out → brief → Notion + graph)
        ▼
   pre-event-content skill             (posts · connection notes · questions; Sunday "Upcoming Week" roundup)
        ▼
   Alex reviews drafts in Notion       (inline comments = the voice pass)
        ▼
   [ATTEND EVENT]
        ▼
   Workflow B — /post-event-content    (transcript → post_event_brief → drafts + outreach)
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
  - `alex:market-signal-tracker`, `alex:battlecard-library` (plugin skills; the project copies were pruned 2026-09-28)

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

- **B — `/post-event-content`** ✅ WIRED (Supercut-anchored since 2026-09-28, manual upload before that; `post_event_brief` first-class artifact added 2026-05-28). The day-to-day post-event flow. Supercut transcript (Step 2A; audio file or paste as fallbacks; `.claude/references/supercut.md`) → `transcript-conditioning` (Step 3.5) → **`post_event_brief` synthesis (Step 3.7 — the data store / short-term memory)** → `content-correspondent` drafts Tier 1 comment + Tier 2 primary post (pre→post bridge) + Tier 2 alternate + bucket-sorted outreach DMs → optional Claude-design carousel render → Notion rows written inline in the parent thread (subagents lack claude.ai connectors). The brief is the post-event mirror of the pre-event `research_brief`; every downstream draft references it in its body. Granola auto-fetch path retained but DISABLED (app nonoperational on Alex's device).

### Retired scaffolds
`/post-event-synthesis` (Workflow B's chained version), `/weekly-recap` (Workflow C) and `/voice-pass` (Workflow D) were deleted 2026-09-27 — see the note under the status table. The individual pieces they would have chained (`transcript-analysis`, `objection-mining`, `pattern-synthesis`) remain callable on their own; `commercial-insight-generator` and `voice-editor` were pruned from this repo 2026-09-28 (source copies live in `alex-agents-skills`).

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
4. Check `.claude/references/notion-schema.md` for schema and CLAUDE.md §3 for DB IDs

The command file is the orchestration shape. The skill is the methodology. The agent is the role contract. They compose; if one drifts from the others, fix the drift.

---

## Quick reference — all imported assets

### Skills imported from alex-agents-skills (Tier 1)

**Research methodology** (`.claude/skills/research-methodology/`):
- `research-brief-blueprint/` — scoping + checklist
- `market-scenario-modeler/` — TAM/SAM/SOM, sensitivity
- `insights-repository-kit/` — research artifact governance

**Copywriting** (`.claude/skills/copywriting/`, read by `pre-event-content`):
- `message-architecture/` — hook banks, CTA playbooks
- `cold-email-personalization/` — personalization rubric

**Transcript intelligence** (`.claude/skills/transcript-intelligence/`):
- `transcript-analysis/` — extract from sales/event transcripts
- `objection-mining/` — friction signal extraction

**Pruned 2026-09-28** (verbatim copies of `alex:*` plugin skills, 0 uses in 30 days): `company-deep-research/`, `content-quality/`, `icp-research/`, `cold-email/`. Use the plugin versions (`alex:battlecard-library`, `alex:market-signal-tracker`, `alex:executive-briefing-kit`, `alex:voice-guidelines`, `alex:persona-development`, `alex:account-qualification`, `alex:copy-frameworks`, `alex:personalization-engine`, `alex:sequence-architecture`).

### Agents imported

**Research** (`.claude/agents/research/`):
- *Custom (built for Workflow A):* `event-research-synthesizer`, `company-researcher`, `person-researcher`, `topic-landscape-analyst`, `competitive-signal-scanner`, `knowledge-conditioning`
- *Job-search lens:* `dossier-synthesizer`

**Content** (`.claude/agents/content/`):
- `field-guide-renderer`

**Ops** (`.claude/agents/ops/`):
- *Custom:* `notion-writer`

**Pruned 2026-09-28** (0 dispatches in 30 days; byte-identical source copies live in `alex-agents-skills`): `insights-research-director`, `qualitative-field-lead`, `quant-insights-architect`, `market-insights-director`, `win-loss-analyst`, `battlecard-program-manager`, `voice-editor`, `copy-strategist`, `conversion-copywriter`, `cold-email-specialist`, `commercial-insight-generator`, `reframe-architect`, `mobilizer-mapper`, and the project copy of `systems-analyst` (use `alex:systems-analyst`).

### Commands imported (in addition to the workflow commands)

None remain; the five imported commands were pruned 2026-09-28 (see the status table note).

### References

`.claude/references/`:
- `research-analyst-prompt.md` — top-level analyst prompt (imported)
- `content-style-guide.md`, `content-anti-patterns.md`, `outreach-templates.md`, `pipeline-operations-guide.md`, `portfolio-tracker.md`, `stack-readme.md`, `systems-thinking-workflow.md` (existing)

---

## What's NOT here (intentionally — Tier 2 deferred) — RECORD: bring in when a use case warrants; no issue (2026-09-18)

Per Alex's decision (2026-05-04): Tier 2 imports skipped this round. Includes:
- `positioning-messaging`, `launch-marketing`, `media-relations` (GTM Marketing)
- `value-story-framework`, `cxo-briefing-kit` (Enterprise Sales)
- `vertical-solution-templates` (Growth Strategist)
- `partnership-bd`
- `business-intelligence/*`, `statistical-analyst/`

Bring in later when use cases warrant.

## What's NOT here (intentionally — automation deferred)

The 2026-05-04 hooks/scheduled-task ideas (intake-count nudges, auto voice pass, "just got back from" prompt, Sunday auto-recap) were dropped with YED-198 on 2026-09-27. Reintroduce one only when a named friction motivates it.

---

*Partial refresh 2026-07-11 — added the "Commands added since" table (the doc had drifted ~2 months behind; the MI Engine, signal scanners, judge/rigor layer, and market-research suite were all missing). The four-workflow body below is unchanged and still accurate.*

*Status note (2026-09-18): the 2026-05-07 orchestrator→synthesizer pivot and its "VALIDATION PENDING" caveat are SUPERSEDED — Workflow A has run end-to-end in fresh sessions dozens of times since (e.g. the 2026-08-25 and 2026-09-12 batches). The four-workflow body above is the rerun manual; per-command specs in `.claude/commands/` are authoritative where they differ. Registry-freeze constraint is recorded in `sdk-runtime-constraints.md`.*
