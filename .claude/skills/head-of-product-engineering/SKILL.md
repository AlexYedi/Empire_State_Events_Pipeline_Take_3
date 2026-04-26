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
2. **Future-State Register lookup.** First try the Notion Project Ideas DB — search for a row matching the project name and load its page body. If Notion MCP is unavailable, fall back to the local mirror at `.claude/artifacts/future-state-register.md` (create if missing).
   - **Found** (either source) → this is an **n+1 turn**. Load the prior future-state into working context. Workflow 9 (Evolution Log) will run at the end.
   - **Not found** in both → this is a **first turn**. Initialize a new Register entry at the end (DB row + local mirror). Skip Workflow 9.
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

**Note on specialist count:** the library has **10 product specialists**, but `systems-thinking` is hard-invoked twice — once in Workflow 1 (Discovery, stakeholder map) and once in Workflow 4 (Prioritization, Three-Horizon lens). The two invocations apply different lenses from the same skill; treat them as distinct passes.

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

### 2. Future-State Register — per-project, in Notion Project Ideas DB row

**Primary location:** The Project Ideas Notion DB row for this project, written in the row's page body.

**Local mirror:** `.claude/artifacts/future-state-register.md` — single file, one entry per project. Used as offline fallback for n+1 detection and as the source of truth during the orchestrator run.

**Schema (same in both locations):**
```
## {Project Name}
- Slug: {project-slug}
- Current cycle: {n}
- Last updated: {YYYY-MM-DD}
- Future-state: {1–3 sentence canonical description}
- North-star metric: {metric + target}
- Horizon: {MVP | Scaling | Enterprise-Prod}
- Prior cycles: {cycle 1 → cycle 2 → ...} (links to Evolution Log entries)

### Deferred items
| Item | Trigger to address | Effort estimate |
|------|--------------------|-----------------|
| {e.g., SSO auth} | {first enterprise inbound} | {2-3 days} |
```

The **Deferred items** table is the Three-Horizon artifact from `systems-thinking/SKILL.md` — folded into the Register so a single per-project document carries both the future-state metadata and the deferred-polish backlog.

**Update rule:** on every run, overwrite `Future-state`, `Current cycle`, `Last updated`, `North-star metric`, `Horizon`. **Never** delete the `Prior cycles` trail — append only. Deferred items: add new items and mark resolved items as `~~resolved~~ {date}`; do not delete.

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

1. **Notion — Project Ideas DB:** create or update the row for this project. Use the project name as the row title. Populate the structured properties (per Project Ideas schema in CLAUDE.md). In the row's page body, write the following blocks **in this order**:

    1. **Page-index callout** (always first). Format: blockquote with 📑 emoji, bold "Page index", bullet list of the H1 sections on the page (PRD, Orchestration Log summary, Future-State Register, Evolution Log if n+1, plus any toggled archives), each with a one-line description. End the callout with the italic tip: *"Place cursor below this callout and type `/toc` to add Notion's interactive auto-updating table of contents — one-time per page."* (Markdown TOC syntax is not supported by the Notion MCP — see "Notion delivery gotchas" below — so the page-index callout is the static fallback and `/toc` is a one-time manual step.)
    2. **Context callouts** (optional, contextual). E.g., redesign banners on n+1 turns where the architecture has materially changed.
    3. **`# PRD — {project name}`** — full PRD body.
    4. **`---`** divider, then **`# Orchestration Log summary (cycle {n})`** — W1–W9 walkthrough (one paragraph per workflow). On n+1 runs include the Workflow 9 Evolution Log entry inline.
    5. **`---`** divider, then **`# Future-State Register (cycle {n})`** — metadata header + Deferred items table + H2 escalation trigger + Rollback. (This is the same content that lives in the local mirror at `.claude/artifacts/future-state-register.md`.)
    6. **Deprecated/superseded prior content** (n+1 only when prior cycle's design was replaced wholesale): wrap in `<details><summary>{title} (deprecated {YYYY-MM-DD}, cycle {n})</summary>...</details>`. Notion parses this as a native collapsible toggle. **Do not delete prior cycles' content** — toggle preserves history on the same page, avoiding sub-page sprawl.

    Update strategy: use `replace_content` only on first turn or when the page body is scaffolding-only. On n+1, prefer `update_content` with anchored swaps so existing content is preserved unless explicitly superseded. Per-property updates (e.g., Architecture Summary) use `update_properties`.

2. **Linear:** emit one issue per PRD user story, labeled `cycle-{n}` and `project-{slug}`. Wire `blockedBy` from the PRD's "Depends on" lines so the dependency graph is queryable in Linear's view layer. Create labels as workspace-scoped if they don't already exist.

### Notion delivery gotchas (verified 2026-04-26)

- **Markdown TOC syntax does NOT work via the Notion MCP.** Tested and rejected: `[[toc]]`, `[TOC]`, `+++`, `<toc/>`, `<table_of_contents/>` — all land as escaped literal text. Only workaround is the static page-index callout above plus the `/toc` slash command in the Notion UI (one-time per page, then auto-updates).
- **Toggle/collapsible sections use `<details><summary>...</summary>...</details>` HTML.** Notion-specific `+++ title ... +++` syntax does NOT work. The `<details>` tag is the only allowlisted HTML form for toggles.
- **Multi-select properties take a JSON-array-string, not a comma-string or native array.** See CLAUDE.md "Notion create-pages gotchas" for full list.
- **Tables**: write as standard markdown `|`-table; Notion auto-converts to native `<table header-row="true">` block on write. Rendered tables sort/filter/resize natively in Notion.
- **Auto-escaping of `<`**: `<5min` becomes `\<5min` in the stored markdown but renders correctly. Cosmetic only.

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
