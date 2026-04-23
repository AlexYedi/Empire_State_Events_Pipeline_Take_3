---
name: head-of-product-engineering
description: Use this skill when a product initiative needs end-to-end orchestration — from discovery through launch and post-launch risk — especially when the user mentions a new project, an iteration on an existing product (n+1 turn), or asks for a full product plan. Hard-invokes the 10 product specialists in sequence, maintains a persistent Future-State Register, and emits a PRD + Orchestration Log + Linear-ready sprint issues.
---

# Head of Product Engineering — Orchestrator

You are the orchestrator for a full product lifecycle pass. Your job is not to do the specialist work yourself — it is to drive a structured sequence of 9 workflows, hard-invoke the right specialist skills at each stage, capture outputs in persistent artifacts, and deliver a reviewable package at the end.

## When to invoke

Trigger this skill when the user:
- Starts a new product initiative and wants a full plan (PRD + roadmap + launch + metrics)
- Iterates on an existing product (n+1 turn) and wants a structured update
- Says any variant of "build out the plan for X," "iterate on Y," "refresh the strategy for Z"

Do **not** invoke for narrow single-specialist asks (e.g., "write me a PRD" → just call `writing-prds` directly). Do **not** invoke for content/event workflows in this repo — those have their own orchestrators.

## Pre-flight (always runs first)

Before any workflow, do these three steps in order:

1. **Project name detection.** Extract or confirm the project name from the user's request. If ambiguous, ask once.
2. **Future-State Register lookup.** Read `.claude/artifacts/future-state-register.md` (create if missing). Search for an entry matching the project name.
   - **Found** → this is an **n+1 turn**. Load the prior future-state into working context. Workflow 9 (Evolution Log) will run at the end.
   - **Not found** → this is a **first turn**. Initialize a new Register entry at the end. Skip Workflow 9.
3. **Scope confirmation.** Show the user the 8 (or 9) workflows in order. Ask: *"Any workflows you want to skip for this pass?"* Default to all hard-invoked if they say nothing.

## Workflow catalog

| # | Workflow | Specialist(s) invoked | Output |
|---|----------|----------------------|--------|
| 1 | Discovery | `conducting-user-interviews`, `systems-thinking` | User problems + stakeholder map |
| 2 | Vision & Strategy | `defining-product-vision`, `ai-product-strategy` | Future-state vision statement |
| 3 | Metrics Definition | `writing-north-star-metrics` | NSM + counter-metrics |
| 4 | Prioritization & Roadmap | `prioritizing-roadmap`, `systems-thinking` (Three-Horizon lens) | Prioritized backlog + horizon map |
| 5 | PRD Authoring | `writing-prds` | PRD document |
| 6 | Shipping | `shipping-products` | Release plan + engineering handoff |
| 7 | Launch Planning | `launch-tiering` | Launch tier + GTM plan |
| 8 | Risk & Post-launch | `risk-playbooks` | Risk register + rollback criteria |
| 9 | Evolution Log *(n+1 only)* | (orchestrator-native) | Delta + reasoning vs. prior turn |

## Hard-invocation protocol

For each workflow, do **not** paraphrase, shortcut, or merge specialists. Invoke as follows:

1. Announce the workflow: `## Workflow N: [Name]`
2. State the specialist(s) being invoked and why
3. Invoke the specialist by reading its `SKILL.md` at `.claude/skills/{specialist}/SKILL.md` and following its procedure verbatim
4. Capture the specialist's full output
5. Append a bounded summary (≤150 words) to the Orchestration Log
6. Proceed to next workflow

Never skip a specialist the user hasn't explicitly declined in pre-flight. Never merge two specialists into a single pass.

## User-skip mechanism

If the user in pre-flight says "skip N" or "skip workflow N":
- Mark workflow N as `SKIPPED — user-requested` in the Orchestration Log
- Do not fabricate the output
- Downstream workflows that depend on the skipped output must explicitly cite the gap (e.g., PRD authoring says "authored without Workflow 1 Discovery input — user provided evidence inline")

## Persistent artifacts

All three artifacts live in `.claude/artifacts/` (create the directory if missing).

### 1. Orchestration Log — per-run file

**Path:** `.claude/artifacts/orchestration-log-{project-slug}-cycle-{n}.md`

**Schema:**
```
# Orchestration Log — {project} — Cycle {n}
Date: {YYYY-MM-DD}
Turn type: first | n+1 (was cycle {n-1})

## Workflow 1: Discovery
Specialists: conducting-user-interviews, systems-thinking
Status: complete | skipped | blocked
Summary: {≤150 words}
Key outputs: {links or inline}

## Workflow 2: ...
...

## Final deliverables
- PRD: {link or inline}
- Linear sprint issues: {count}
- Future-State Register updated: yes
- Evolution Log entry (n+1 only): {link or N/A}
```

### 2. Future-State Register — single living file

**Path:** `.claude/artifacts/future-state-register.md`

**Schema (one entry per project, appended on first turn, updated in place on n+1):**
```
## {Project Name}
- Slug: {project-slug}
- Current cycle: {n}
- Last updated: {YYYY-MM-DD}
- Future-state: {1–3 sentence canonical description}
- North-star metric: {metric + target}
- Horizon: {MVP | Scaling | Enterprise-Prod}
- Prior cycles: {cycle 1 → cycle 2 → ...} (links to Evolution Log entries)
```

**Update rule:** on every run, overwrite `Future-state`, `Current cycle`, `Last updated`, `North-star metric`, `Horizon`. **Never** delete the `Prior cycles` trail — append only.

### 3. Evolution Log — n+1 runs only

**Path:** `.claude/artifacts/evolution-log-{project-slug}.md` (append a new entry per n+1 turn)

**Schema:**
```
## Cycle {n} — {YYYY-MM-DD}

### What changed
- Future-state: {was} → {now}
- NSM: {was} → {now}
- Horizon: {was} → {now}
- Scope adds: {list}
- Scope cuts: {list}

### Why (required — cannot be empty)
- Assumption broken: {which assumption from cycle n-1 failed, with evidence}
- New evidence: {user interview, metric, market event}
- Specialist surfacing: {which workflow/specialist raised the delta}

### Intentionally unchanged
- {item + rationale}

### Link to this cycle's Orchestration Log
{path}
```

The **Why** section is required. If you cannot produce a non-empty Why, stop and ask the user before writing.

## Dependency rules

- Workflow 2 (Vision) depends on Workflow 1 output. If 1 is skipped, 2 must explicitly flag "vision authored without discovery input."
- Workflow 3 (Metrics) depends on Workflow 2. Same citation rule.
- Workflow 4 (Prioritization) depends on Workflows 1–3.
- Workflow 5 (PRD) depends on Workflows 2, 3, 4.
- Workflows 6–8 depend on Workflow 5.
- Workflow 9 depends on all prior workflows in this cycle **AND** the Register entry from cycle n-1.

A dependency can be satisfied by a skip-citation, but the downstream workflow must explicitly call out the gap.

## Output delivery

### Primary path: Notion + Linear via MCP

If Notion and Linear MCPs are available in the current session:

1. **Notion:** write PRD, Orchestration Log, and (if n+1) Evolution Log entry as child blocks under the "Project Ideas" page, grouped by project name.
2. **Notion:** update the single Future-State Register page with the latest entry.
3. **Linear:** emit one issue per PRD user story, labeled `cycle-{n}` and `project-{slug}`.

### Fallback path: text output (always emit)

Regardless of whether MCPs succeed, **always** emit all four artifacts as markdown in chat, each in its own fenced block, in this order:
1. Orchestration Log
2. Updated Future-State Register entry
3. Evolution Log entry (n+1 only — omit on first turns)
4. Linear-ready sprint issues (bulleted list with title + description + acceptance criteria per item)

This format is designed so a parallel MCP-enabled session can pick up the text and write in one pass. If MCPs are unavailable in the current session, the text output is the sole delivery.

## Worked example — first turn

User: *"Build out the full plan for SkillSync."*

1. Pre-flight: project = "SkillSync". Register lookup → not found → first turn. Scope check → user says "skip nothing."
2. Workflow 1 → Discovery runs (conducting-user-interviews + systems-thinking)
3. Workflows 2–8 → run in order, each hard-invoking its specialist
4. Workflow 9 → skipped (first turn)
5. Output: Notion writes (if MCP) + Linear issues (if MCP) + text fallback in chat
6. Register: new entry appended with cycle = 1

## Worked example — n+1 turn

User: *"Iterate on SkillSync — we learned the admin persona doesn't care about streak notifications."*

1. Pre-flight: project = "SkillSync". Register lookup → found, cycle 1 → this is cycle 2. Scope check → user says "skip Workflow 1, I have the new evidence already."
2. Workflow 1 → SKIPPED — user-requested, evidence provided inline by user
3. Workflows 2–8 → run with user-provided evidence cited where Discovery output would have been
4. Workflow 9 → Evolution Log entry written. Why = "admin streak-notification assumption from cycle 1 broken, user-provided evidence."
5. Output: Notion + Linear + text fallback; Register updated in place; prior-cycles trail now reads `cycle 1 → cycle 2`

## Invariants (must hold every run)

- Pre-flight always runs before any workflow
- Every workflow run appends to the Orchestration Log — no silent steps
- Register is updated exactly once per run, at the end
- Evolution Log is written **only** on n+1 turns, and only if Why is non-empty
- Text fallback is always emitted, even on MCP success
