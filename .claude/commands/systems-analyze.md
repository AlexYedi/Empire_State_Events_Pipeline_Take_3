---
description: "Workflow E — run a deep systems-thinking diagnostic on a problem. Dispatches the systems-analyst subagent from the parent thread for the full eight-phase Meadows analysis. Use for chronic dysfunction, multi-stakeholder problems, 'why does this keep happening' questions, or second-opinion analyses on high-stakes decisions."
argument-hint: "[problem statement, Notion URL, pipeline component name, or artifact path]"
---

# /systems-analyze — Workflow E

Run a structured systems-thinking analysis on a problem and return a diagnostic the parent (you + Alex) can act on. The analysis is delegated to the `systems-analyst` subagent so the eight-phase walk happens without burning main-context tokens; the parent thread bounds the problem, dispatches, and decides what to do with the result.

**Input:** any of —
- Free-text problem statement ("the content pipeline keeps producing drafts that don't get published")
- Notion page URL (artifact, diagnostic, dashboard, draft)
- Pipeline component name (`pre-event-content`, `event-deep-research`, etc.)
- Path to a local artifact (`.claude/artifacts/<file>.md`)
- Combination of the above

**Output:**
- A structured eight-phase diagnostic presented in conversation
- Optionally saved to `.claude/artifacts/systems-analyst-<slug>-<date>.md` for durable reference
- Optionally followed by a Linear issue draft if the recommendation maps to actionable follow-through

---

## Trigger

This command runs when:
- Alex types `/systems-analyze` followed by a framing question or artifact reference
- Alex says any of: "run a systems analysis on X", "why does X keep happening", "diagnose X with systems-thinking", "second-opinion on this decision", "systems-thinking pass on Y"
- A higher-level workflow (e.g., `head-of-product-engineering` Discovery or Prioritization phase) asks for a delegated systems pass
- An event-deep-research run surfaces a strategically significant pattern Alex wants traced back to system structure (opt-in, see Step 5 below)

## Required inputs

1. **Problem framing** — at minimum a one-sentence statement of what feels wrong, stuck, or surprising. The framing itself may be the problem; the analyst will surface that if so.
2. **(Optional) Artifacts** — Notion URLs, file paths, or prior diagnostic artifacts the analyst should read before walking the phases.
3. **(Optional) Stated scope** — "this week," "this quarter," "long-term paradigm question." Drives where the analyst lands on the H1/H2/H3 horizon view.

If only a vague gesture is provided ("things feel stuck"), ask Alex one clarifying question before dispatching. Don't dispatch on a malformed problem statement.

## Step 1 — Bound the problem (this conversation, NOT a subagent)

Run this in the parent thread:

1. Restate the problem in one sentence — what is the system, what is the observed behavior, and what is the gap between observed and desired.
2. List any artifacts the analyst should read (file paths, Notion URLs). Verify each exists before dispatching.
3. If applicable, note the horizon Alex is asking about (H1 / H2 / H3 / unsure).
4. Identify what success looks like — a list of leverage points, a decision, an archetype confirmation, etc. State this so the analyst can tune the diagnostic.
5. Confirm with Alex before dispatching. Allow override of scope.

**Do NOT delegate this step.** Building the framing requires conversation with Alex.

## Step 2 — Dispatch the systems-analyst subagent (this conversation)

Invoke the `systems-analyst` subagent via the `Agent` tool with `subagent_type: "systems-analyst"`. The dispatch prompt must include:

- The bounded problem statement from Step 1
- All artifact paths/URLs the analyst should read
- Horizon scope (or "unsure" if Alex hasn't decided)
- Alex's stated success criteria
- An explicit instruction to walk all eight phases — do not skip even if a phase produces a thin result (thin results are findings).

**SDK constraint reminder:** the parent thread owns this dispatch. The analyst is a synthesis-only subagent — it reads, walks the phases, returns markdown. It does NOT dispatch further subagents. (See CLAUDE.md "SDK runtime constraints" section.)

**Wait for the analyst to return before continuing.** If the return is thin or skips phases, re-invoke once with a sharper framing — do not stitch a partial diagnostic in the parent thread.

## Step 3 — Present the diagnostic (this conversation)

When the analyst returns:

1. **Surface the recommendation up top** — one line, with confidence percentage and what would falsify the analysis. Don't bury the actionable bit under the eight phases.
2. **Show the H1/H2/H3 horizon view** verbatim — Alex prioritizes by horizon.
3. **Flag any archetype match with high confidence** — these are the system traps. Name the archetype and its canonical escape.
4. **Identify the highest-leverage intervention** — quote it from the diagnostic.
5. **Surface posture-check items** — what the analyst said it might be wrong about, what would warrant more evidence.
6. **Present the full diagnostic in collapsed form** if appropriate — Alex can expand for full eight-phase detail.

## Step 4 — Decide and route (this conversation, with Alex)

After Alex reads the diagnostic, ask which of the following applies:

a. **Save the artifact.** Write the full diagnostic to `.claude/artifacts/systems-analyst-<slug>-<YYYY-MM-DD>.md` for durable reference. Default = yes when the analysis surfaces a high-confidence archetype match OR a recommendation Alex agrees with.

b. **Open Linear issue(s) for the recommended interventions.** Use Linear MCP `save_issue` with priority mapped from the horizon (H1 → High, H2 → Medium, H3 → Low). Link back to the saved artifact. Default = yes when the recommendation is actionable in <2 weeks AND Alex confirms intent to execute.

c. **Update CLAUDE.md** if the diagnostic changes a project-level invariant (e.g., a new gotcha, a structural rule, a deprecated pattern). Default = ask Alex explicitly before editing CLAUDE.md.

d. **Run a follow-on workflow.** Examples:
   - If the diagnostic recommends a build → `head-of-product-engineering` Discovery phase
   - If the diagnostic surfaces a content-pipeline structural issue → revisit `.claude/proposals/content-pipeline-v2-stage2.md` triggers
   - If the diagnostic identifies a missing measurement → propose the metric in conversation, don't auto-create

e. **Park the diagnostic.** Default when posture-check confidence is below 60% or the recommendation is "wait for more signal." Save the artifact anyway so the framing is preserved.

## Step 5 — Optional: chain into event-deep-research

If `/systems-analyze` was invoked as a pre-step inside an event-deep-research workflow (the orchestrator flagged a high-stakes event where structural framing matters), return the diagnostic to that workflow as additional context. Do NOT auto-trigger event-deep-research from this command; the chaining is one-direction (event-deep-research → systems-analyze, never reverse).

---

## Anti-patterns

- **Don't dispatch the analyst on a malformed problem statement.** "Things feel off" is not a problem statement — ask one clarifying question first.
- **Don't summarize the analyst's diagnostic into a one-paragraph TL;DR that drops the posture-check.** The posture-check is where the analysis becomes actionable; keep it.
- **Don't auto-create Linear issues from H3 recommendations.** H3 work is paradigm-level and almost always premature. Park it explicitly.
- **Don't use this command for single-step tactical asks.** If the answer is obvious, the systems analysis is overhead. Trust the question filter in the agent definition.

## Known gotchas

- **Agent registry is session-frozen.** Per CLAUDE.md "SDK runtime constraints" — edits to `.claude/agents/ops/systems-analyst.md` mid-conversation are not picked up. Validate any analyst changes in a fresh conversation.
- **The analyst reads `.claude/skills/systems-thinking/` references.** Edits to those reference files require a fresh conversation to land in the analyst's context.
- **Horizon framing is project-specific.** The H1/H2/H3 view in the analyst output assumes Alex's framework documented in `.claude/skills/systems-thinking/SKILL.md`. If using this command in a different project, the analyst will note the absence of a horizon framework rather than fabricating one.

## Related workflows

- `event-deep-research` (Workflow A) — can optionally chain INTO this command for strategic events
- `head-of-product-engineering` — calls this command as part of Discovery and Prioritization phases
- `.claude/skills/systems-thinking/SKILL.md` — the methodology this command operationalizes
