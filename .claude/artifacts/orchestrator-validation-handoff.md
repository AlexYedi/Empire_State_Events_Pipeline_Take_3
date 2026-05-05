# Orchestrator validation — handoff for fresh conversation

**Created:** 2026-05-04
**Why this exists:** Validation of `event-research-orchestrator` failed mid-session because the Task tool didn't enumerate custom `.claude/agents/` files at conversation start. Open a fresh Claude Code conversation in this repo and use the prompt below.

---

## Step 1 — Open a fresh conversation in this repo

```
cd /Users/sameoldexpressions/Documents/GitHub/Empire_State_Events_Pipeline_Take_3
claude
```

Or just open a new chat tab in your normal Claude Code surface, with this repo as the working directory.

## Step 2 — Verify custom agents are now discoverable

Before running the validation, ask Claude to list available `subagent_type` values for the Task tool. Look for `event-research-orchestrator`, `company-researcher`, `person-researcher`, `topic-landscape-analyst`, `competitive-signal-scanner`, `notion-writer` in the list.

If they ARE there → proceed to Step 3.

If they are NOT there → registration mechanism is the problem. See `.claude/WORKFLOWS.md` "Known gap" section. The agent files may need to live in a plugin namespace or a different format. That's a separate investigation, not a validation run.

## Step 3 — Paste this validation prompt

> Run the `event-research-orchestrator` agent (Task tool, subagent_type: `event-research-orchestrator`) on the May 6, 2026 Agentics NYC event. This is a validation pass — produce the brief independently of the existing Wednesday brief in Notion ([Agentics Event page](https://www.notion.so/357d3699c2db81028878c1efd0a55a65) and [its existing research_brief Content Draft](https://www.notion.so/357d3699c2db81a28374ca42e054b0a7)).
>
> Inputs to pass to the orchestrator:
>
> **Event invite text:**
> Event title: Agentics: Use AI coding agents effectively
> Presented by: Agentics NYC
> Location: 233 Spring St, floor 11, New York
> Date: May 6, 2026 (Wednesday), 6-9pm
>
> About: Join Nori, Vellum, Cognee, and Modal in New York on May 6 for an evening of presentations from teams at the cutting edge of agentic development. Practitioners sharing what works, what doesn't, what's next. Educational event, not pitch night.
>
> **Triage plan (already executed):**
> - Companies — all NEW: Agentics NYC, Nori (heynori.com / Tilework — agent infrastructure, NOT the YC health-AI Nori at nori.ai), Vellum, Cognee, Modal Labs
> - Topics — AI Coding Agents (existing, recently refreshed → APPEND-CURRENT-EVENTS-ONLY) · AI Agent Memory Layer (NEW) · AI Coding Agent Infrastructure (NEW) · Agentic AI (existing, refreshed → APPEND-CURRENT-EVENTS-ONLY)
> - People — none specifically named (skip person-researcher)
>
> **Stated focus:** Alex is attending for technical context that maps to enterprise GTM positioning. Non-obvious angle: see the four presenters as one STACK, not four pitches — Modal (GPU/infra), Nori (runtime), Vellum (orchestration), Cognee (memory). Cross-stack lens is the documentarian opportunity.
>
> **Constraints:**
> - DO NOT write to Notion or HubSpot. Return brief as text only.
> - DO NOT consult the existing inline-path brief — produce independently.
> - Today: 2026-05-04. Event: 2026-05-06.
>
> **Output:** Brief in event-research SKILL Step 3 schema (Quick Take · Topics × 5 dimensions · People (skipped) · Companies × all 5 NEW · Documentarian Angle · Success Signals 3–5 + anti-signal). Plus a Validation notes block at the end:
> - Did all 3 specialists complete? (company-researcher, topic-landscape-analyst, competitive-signal-scanner)
> - Any subagent contract drift?
> - Any tools/inputs you needed but couldn't access?
> - Estimated wall-clock time
> - Places where you had to invent context

## Step 4 — Compare side-by-side

After the orchestrator returns its brief:

1. **Write it to a NEW Notion Content Draft** titled `[orchestrator validation] Agentics — Research Brief`, content type `research_brief`, related to the existing Wednesday Event page.
2. **Compare against the inline-path brief** ([existing Content Draft](https://www.notion.so/357d3699c2db81a28374ca42e054b0a7)) on three axes:
   - **Structural** — did the orchestrator run cleanly? (yes/no, where it failed if so)
   - **Coverage** — what does the orchestrator brief cover that the inline didn't? (and vice versa)
   - **Quality** — Alex's judgment call after reading both
3. **Decide which to keep** — archive the loser, optionally merge if they each add unique value.

## Step 5 — Update WORKFLOWS.md

After validation:

- If the orchestrator works as designed → update WORKFLOWS.md status from 🟠 to ✅ and remove the "Known gap" section.
- If it fails or produces materially worse output → log the specific failure modes in WORKFLOWS.md and decide whether to fix agent definitions or fall back to inline path as the canonical Workflow A.

---

## What's already in Notion for context

**Wednesday event:** https://www.notion.so/357d3699c2db81028878c1efd0a55a65

**Existing inline-path Content Drafts (the baseline):**
- [Research Brief](https://www.notion.so/357d3699c2db81a28374ca42e054b0a7)
- [LinkedIn post (pre-event)](https://www.notion.so/357d3699c2db8145b726e4e2f0491d26)
- [Prepared Questions](https://www.notion.so/357d3699c2db8163ac53faf59c6857a3)

**Project ideation outputs (3 ideas tied to Wed):**
- [Cognee Coding Memory Skill for Claude Code](https://www.notion.so/357d3699c2db81c683b3dea9583d598a) — feasible prototype, composite 9.0
- [Vellum 'Tool Survivorship' Decision Agent](https://www.notion.so/357d3699c2db8189a200ccaa48c16d94) — feasible prototype, composite 8.8
- [Agent Infra Decision Tool](https://www.notion.so/357d3699c2db81c4bae2cb9ecf030dec) — stretch MVP, composite 8.2
