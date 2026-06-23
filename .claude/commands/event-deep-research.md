---
description: "Workflow A — full event research pipeline. Parses a pasted calendar invite, runs entity triage, fans out 4 parallel research subagents from this conversation, dispatches synthesizer for the brief, and writes to Notion + HubSpot. Replaces the monolithic event-research skill flow with a multi-agent architecture."
argument-hint: "[paste calendar invite text after the command]"
---

# /event-deep-research — Workflow A

Run the full event research pipeline using multi-agent fan-out **from the parent thread** (the slash command's main conversation). Subagents cannot dispatch sub-agents per Anthropic SDK design, so the parent owns the fan-out and a downstream synthesizer assembles the final brief.

**Input:** pasted calendar invite text (or invite + Alex's natural-language context like "Speaker: Jane Smith, CTO at Acme; Topics: agentic systems, enterprise AI").

**Output:**
- A research brief presented in conversation for Alex's review
- Once approved → all 5 Notion DBs written (Companies, Topics, People, Events, Content Drafts) + HubSpot CRM (Companies, Contacts with associations, Notes)

---

## Trigger

This command runs when:
- Alex pastes a calendar invite and wants research
- Alex types `/event-deep-research` followed by invite text
- Alex says "research this event" / "deep research on [event]" / "run the event pipeline"

## Required inputs

1. **Event invite text** — pasted invite description, or natural-language description with speaker/host/topic cues
2. **(Optional) Google Calendar Event ID** — if the input includes a `Google Calendar Event ID:` line (as `/check-new-events` always passes), capture it and forward to `notion-writer` for the Events DB row. This is the deterministic join key to Granola for `/post-event-content`.
3. **(Optional) Stated focus** — if Alex says "I'm going to find a hiring manager" or "I want to test my POV on agentic systems", pass that downstream so Success Signals are tailored

## Step 1 — Parse and triage (this conversation, NOT a subagent)

Run **Steps 1, 1.5 of `.claude/skills/event-research/SKILL.md`** in this conversation:

1. Parse the invite into entities (Event, People, Companies, Topics)
2. Confirm entities with Alex
3. Run dedup search against Notion (5 DBs) per the canonicalization rules
4. Classify each entity: NEW / REFRESH-light / REFRESH-full / SKIP / APPEND-CURRENT-EVENTS-ONLY
5. Present triage plan to Alex for approval
6. Apply Alex's overrides (if any)

**Do NOT delegate this step.** Building the triage plan requires conversation with Alex.

**Preserve the raw description verbatim (added 2026-06-23 — fidelity fix).** Parsing into entities is LOSSY: it is a summary. Keep the full, unedited invite/`description` text as a `VERBATIM SOURCE` block and carry it forward to Step 2 unchanged. The entity list is an *index* into the source, NOT a replacement for it. Never let a downstream agent see only the summarized entities — talk abstracts, named themes (e.g. "partnerships", "go-to-market strategy"), attendee mix, and ordering nuance live in the raw text and are invisible once compressed. Root-cause of a 2026-06-23 defect where all outputs were built off a lossy summary.

## Step 2 — Multi-agent research fan-out (this conversation)

Once triage is approved, **dispatch all four specialists in parallel from this thread** via a single message containing four `Agent` tool calls. This must run in the parent thread because subagents cannot spawn other subagents (Anthropic SDK runtime constraint — see [code.claude.com/docs/en/sub-agents.md](https://code.claude.com/docs/en/sub-agents.md): *"Subagents cannot spawn other subagents. If your workflow requires nested delegation, use Skills or chain subagents from the main conversation."*).

The four parallel dispatches:

1. **company-researcher** — every Company entity that needs research (NEW or REFRESH). Pass the entity list scoped to this specialist + their triage paths + Alex's stated focus.
2. **person-researcher** — every Person entity that needs research (NEW or REFRESH). Skip the dispatch entirely if no people are named or all are SKIP.
3. **topic-landscape-analyst** — every Topic entity (NEW, REFRESH, or APPEND-CURRENT-EVENTS-ONLY). Topics never get full SKIP.
4. **competitive-signal-scanner** — runs across ALL companies (including SKIP) to surface market signals in last 60 days.

For each specialist, pass: **(1) the full `VERBATIM SOURCE` description block from Step 1, quoted unchanged and labeled as the source of truth** ("read every line; derive findings from THIS text — the framing below is supplementary, not a replacement"); (2) the entity list scoped to that specialist; (3) the triage path per entity; (4) the event name + date; (5) Alex's stated focus.

**Mandatory (fidelity fix, 2026-06-23):** the verbatim description is item (1) for a reason — it goes in EVERY specialist dispatch, ahead of the entity list. Do NOT paraphrase it into the prompt and drop the original. If the parent only hands subagents the summarized entity list, the run repeats the defect where talk-abstract nuance and named-but-unsummarized themes never reach research. The Step 2.5 synthesizer also receives the raw invite — keep that.

Wait for all four to return before proceeding to Step 2.5. If a specialist returns thin output, re-invoke just that one with deeper scope — do not restart the whole fan-out.

## Step 2.5 — Synthesis (delegated to event-research-synthesizer)

Invoke the synthesizer subagent with all four specialist returns plus the triage plan and raw invite:

```
subagent_type: event-research-synthesizer
prompt: [event invite + triage plan + Alex's stated focus + all 4 specialist returns]
```

The synthesizer:
1. Reconciles cross-references (signal-scanner findings vs. company-researcher findings)
2. Surfaces verification flags from specialists (mismatched domains, ambiguous identities)
3. Writes Quick Take, Success Signals, Documentarian Angle
4. Formats final brief in the schema from event-research SKILL.md Step 3

The synthesizer returns the assembled brief as text. **No Notion / HubSpot writes happen yet.**

## Step 3 — Present brief for Alex review

Display the brief from the synthesizer. Wait for Alex's approval.

Alex may request:
- Add or remove people / companies → restart from Step 1 with adjusted entity list
- Adjust research depth on specific entities → re-invoke that specific specialist (just that one) with deeper scope from this thread, then re-dispatch synthesizer with the updated returns
- Correct factual errors → patch the brief in conversation
- Add context that web search didn't surface → patch the brief in conversation

Iterate until Alex says "write it" / "proceed" / "looks good".

## Step 4 — Notion writes (delegated)

Invoke notion-writer subagent:

```
subagent_type: notion-writer
prompt: [approved brief + triage plan + raw invite text + today's date + Google Calendar Event ID (if captured in Step 1)]
```

notion-writer executes Steps 4a–4g of `.claude/skills/event-research/SKILL.md`:
- Companies (parallel-safe with Topics) → capture URLs
- Topics (parallel-safe with Companies) → capture URLs
- People (uses Company URLs) → capture URLs
- Event (uses People + Companies + Topics URLs) → capture URL
- Content Draft "[Event Name] — Research Brief" (uses Event URL)

Returns the confirmation block from Step 4g.

## Step 5 — HubSpot writes (this conversation)

Run **Step 5 of `.claude/skills/event-research/SKILL.md`** in this conversation. The HubSpot MCP requires confirmation tables before each create — easier to handle inline with Alex than via subagent.

1. Recurrence check (5.0)
2. Create / refresh Companies (5a)
3. Create / refresh Contacts with company associations (5b)
4. Create Notes per contact with event name as body (5c)
5. Confirm writes (5d)

## Step 6 — Final summary

Present the Step 6 summary block from event-research SKILL.md (Notion + HubSpot results + next steps).

---

## Workflow chain (what comes next)

After `/event-deep-research` completes successfully, common follow-ons:

| Want to... | Run |
|---|---|
| Generate pre-event content (LinkedIn posts, DMs, prepared questions) | `pre-event-content` skill — pulls research brief from Notion |
| Generate project ideas to build before the event | `project-ideation` skill — pulls topics + event from Notion |
| Capture retro after attending | Step 7 of `.claude/skills/event-research/SKILL.md` (handoff to `content-correspondent` for post-event content) |
| Synthesize multiple events from this week into one post | `pattern-synthesis` skill (needs ≥2 briefs) |

See `.claude/WORKFLOWS.md` for the full picture of how the four workflows interrelate.

---

## Failure modes (specific to multi-agent runs)

- **Specialist returns thin output** — re-invoke that one specialist from this thread with deeper scope or more specific direction. Re-dispatch synthesizer with updated returns. Don't restart the whole orchestration.
- **Parent times out during fan-out** — split: dispatch company-researcher + person-researcher in one batch, topic-landscape-analyst + competitive-signal-scanner in another, then dispatch synthesizer with all four returns merged.
- **Triage plan disagreement post-hoc** — if while reviewing the brief Alex realizes an entity should have been REFRESH instead of SKIP, re-invoke just the relevant specialist with the corrected path; don't restart the whole flow.
- **notion-writer hits a schema validation error** — the live Notion schema is authoritative. Use the API error text to fix the property value, retry. Per CLAUDE.md gotcha (e), verify with notion-fetch on the data_source URL if it persists.
- **notion-writer fails with "Prompt is too long"** — its `tools:` whitelist may have drifted to inherit too much. Verify `.claude/agents/ops/notion-writer.md` frontmatter still scopes `tools:` to Notion MCP + Read only.

## Why fan-out runs in the parent thread (architectural note)

Per Anthropic SDK design, subagents dispatched via `Agent` (formerly `Task`) cannot themselves dispatch further subagents — `Agent`/`Task` is not exposed to subagent contexts and cannot be granted via frontmatter. This is a deliberate constraint to prevent runaway nesting. The documented workaround pattern is "chain subagents from the main conversation": orchestrate from the slash command's parent thread, where `Agent` is available.

A previous version of this pipeline used an `event-research-orchestrator` subagent intended to fan out the four specialists from inside its own context. Empirical testing on 2026-05-07 (across 5 different subagents + the orchestrator) confirmed the SDK constraint and validated the pivot to parent-driven fan-out + synthesizer-only downstream agent. See WORKFLOWS.md "✅ Resolved 2026-05-07" section for the full diagnostic record.

## Ground truth references

The orchestration shape is defined here. The actual research / write methodology is in:
- `.claude/skills/event-research/SKILL.md` — full 7-step methodology (parse → triage → research → present → Notion writes → HubSpot writes → retro)
- `.claude/agents/research/event-research-synthesizer.md` — synthesizer contract (text-in, brief-out)
- `.claude/agents/research/{company-researcher, person-researcher, topic-landscape-analyst, competitive-signal-scanner}.md` — specialist contracts
- `.claude/agents/ops/notion-writer.md` — Notion write contract
- `CLAUDE.md` § Project Architecture — Notion/HubSpot schemas, write order, gotchas, SDK constraints
