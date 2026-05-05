---
description: "Workflow A — full event research pipeline. Parses a pasted calendar invite, runs entity triage, fans out 4 parallel research subagents, synthesizes the brief, and writes to Notion + HubSpot. Replaces the monolithic event-research skill flow with a multi-agent orchestrated version."
argument-hint: "[paste calendar invite text after the command]"
---

# /event-deep-research — Workflow A

Run the full event research pipeline using multi-agent fan-out.

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
2. **(Optional) Stated focus** — if Alex says "I'm going to find a hiring manager" or "I want to test my POV on agentic systems", pass that downstream so Success Signals are tailored

## Step 1 — Parse and triage (this conversation, NOT a subagent)

Run **Steps 1, 1.5 of `.claude/skills/event-research/SKILL.md`** in this conversation:

1. Parse the invite into entities (Event, People, Companies, Topics)
2. Confirm entities with Alex
3. Run dedup search against Notion (5 DBs) per the canonicalization rules
4. Classify each entity: NEW / REFRESH-light / REFRESH-full / SKIP / APPEND-CURRENT-EVENTS-ONLY
5. Present triage plan to Alex for approval
6. Apply Alex's overrides (if any)

**Do NOT delegate this step.** The orchestrator and subagents trust the triage plan; building the plan requires conversation with Alex.

## Step 2 — Multi-agent research fan-out

Once triage is approved, invoke the orchestrator via the Task tool:

```
subagent_type: event-research-orchestrator
prompt: [event invite + triage plan + Alex's stated focus]
```

The orchestrator will:
1. Fan out 4 specialists in parallel (single Task message with 4 invocations):
   - `company-researcher` — every NEW + REFRESH company
   - `person-researcher` — every NEW + REFRESH person
   - `topic-landscape-analyst` — every Topic (NEW / REFRESH / APPEND-CURRENT-EVENTS-ONLY)
   - `competitive-signal-scanner` — runs across ALL companies including SKIPs, last 60 days
2. Reconcile cross-references (signal-scanner findings vs. company-researcher findings)
3. Write Quick Take, Success Signals, Documentarian Angle
4. Format the final brief in the schema from event-research SKILL.md Step 3

The orchestrator returns the assembled brief as text. **No Notion / HubSpot writes happen yet.**

## Step 3 — Present brief for Alex review

Display the brief from the orchestrator. Wait for Alex's approval.

Alex may request:
- Add or remove people / companies → restart from Step 1 with adjusted entity list
- Adjust research depth on specific entities → re-invoke specific subagent (just that one) with deeper scope
- Correct factual errors → patch the brief in conversation
- Add context that web search didn't surface → patch the brief in conversation

Iterate until Alex says "write it" / "proceed" / "looks good".

## Step 4 — Notion writes (delegated)

Invoke notion-writer subagent:

```
subagent_type: notion-writer
prompt: [approved brief + triage plan + raw invite text + today's date]
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

- **Subagent returns thin output** — re-invoke that one subagent with deeper scope or more specific direction. Don't rerun the whole orchestration.
- **Orchestrator times out** — split: run company-researcher + person-researcher in one orchestration call, topic-landscape-analyst + competitive-signal-scanner in another, then merge.
- **Triage plan disagreement post-hoc** — if while reviewing the brief Alex realizes an entity should have been REFRESH instead of SKIP, re-invoke just the relevant subagent with the corrected path; don't restart the whole flow.
- **notion-writer hits a schema validation error** — the live Notion schema is authoritative. Use the API error text to fix the property value, retry. Per CLAUDE.md gotcha (e), verify with notion-fetch on the data_source URL if it persists.

## Ground truth references

The orchestration shape is defined here. The actual research / write methodology is in:
- `.claude/skills/event-research/SKILL.md` — full 7-step methodology (parse → triage → research → present → Notion writes → HubSpot writes → retro)
- `.claude/agents/research/event-research-orchestrator.md` — orchestrator contract
- `.claude/agents/research/{company-researcher, person-researcher, topic-landscape-analyst, competitive-signal-scanner}.md` — specialist contracts
- `.claude/agents/ops/notion-writer.md` — Notion write contract
- `CLAUDE.md` § Project Architecture — Notion/HubSpot schemas, write order, gotchas
