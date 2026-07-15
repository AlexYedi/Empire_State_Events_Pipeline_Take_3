# Command orchestration convention (v1)

**Why this exists.** The first `/rigor-review` (2026-07-15) found a recurring build defect —
`thin-declarative-command` (count 5, the entire Jul-2 GTM suite): a `.claude/commands/*.md` that *names*
agents but ships **no orchestration** — no dispatch order, no parallel/serial control flow, no output
destination, no failure modes. A user running it would get nothing deterministic. This file is the
codified fix: the required skeleton every runnable command must satisfy, grounded in the commands that
already pass the build-quality judge (`/interview-prep` 0.942, `/event-deep-research`).

**A command file IS the orchestration.** The *methodology* (what "good" looks like) belongs in a SKILL.md
or agent definition; the *command* says who runs, in what order, with what input, and where the result
lands. If a command only lists agents under an "Invocations" heading, it is a spec, not a command.

## The required skeleton (each numbered step is load-bearing)

1. **Intake & validate (parent thread — never a subagent).** Enumerate every input, mark which are
   required, and **refuse to proceed if a required one is missing** (ask, don't guess). Preserve any
   pasted source material as a `VERBATIM SOURCE` block carried unchanged into every dispatch. If the
   command dedups/persists, do the **dedup read here** so later writes upsert, not duplicate.
2. **Dispatch / fan-out (parent thread, explicit).** State exactly which agents run, **in parallel or
   serially**, and *why*. Parallel = independent `Agent` calls **in one message**. Each dispatch leads
   with the verbatim source block + a one-line framing of what that specialist returns.
   **SDK constraint (hard):** subagents cannot spawn subagents — **fan-out happens in the parent thread,
   not inside a "lead/orchestrator" agent.** A command that says "agent X orchestrates the others" is wrong.
3. **Collect & handle thin returns.** Wait for all dispatched agents. If one returns thin, **re-invoke
   just that one** with deeper scope — don't restart the whole run.
4. **Synthesize (a synthesis-only subagent, or inline).** One agent (text-in/text-out, no dispatch, no
   MCP) assembles the deliverable to a named structure, OR synthesize inline in the parent. Say which.
5. **Judge gate (advisory) — only if the command produces a quality-graded artifact.** Score against a
   named rubric, per-criterion 0–1 + composite; **advisory** (never hard-block); append to the
   `.claude/evals/` run-log. Omit this step for commands whose output isn't judge-graded — don't add
   ceremony.
6. **Output destination — NAME IT.** Every command states where the result lands and how:
   - **Conversation** (default for analysis/briefs — the honest lean default; don't invent a write).
   - **Gamma** for `deck` format (`mcp__claude_ai_Gamma__generate`, `format: "social"` for 4:5) — the
     default visual generator (CLAUDE.md rule 13).
   - **Notion** for artifacts that enter the review loop — parent-thread MCP only
     ([[project_notion_writes_must_be_parent_thread]]); `notion-search`, never
     `notion-query-data-sources` (plan-gated); real newlines in `update-page`.
   Do **not** promise a write the command doesn't actually perform — that's the fabricated-specificity
   anti-pattern the judge docks.
7. **Failure modes.** At least: a required input missing; a specialist returns thin/empty; an external
   dependency (MCP/API/key) unavailable. Say what the command does in each case (degrade, don't crash).

## Conventions
- **Frontmatter:** `description` (required) + `argument-hint`. Reference plugin skills with the `alex:`
  prefix when they live in the `alex` plugin (e.g. `alex:message-architecture`, not `message-architecture`).
- **Placement:** `.claude/commands/<kebab-name>.md`. Methodology lives elsewhere; the command is the shape.
- **Scaffold ≠ shipped.** A command with orchestration deferred is a **draft** — put it in
  `.claude/proposals/` with a `DRAFT` header, or keep it in `commands/` only once steps 1–7 are real.
  Per the CLAUDE.md steering bias, a command with no named friction on the active publishing path is
  deferred, not built out speculatively.

## Build-time hook (makes the fix stick, not just documented)
- A **command/pipeline** build is *non-trivial* → the DoD gate applies. Its **spec-artifact** item is
  satisfied by conforming to this skeleton (steps 1–7 present or explicitly N/A-with-reason).
- The build-quality judge scores command completeness against this skeleton (`build-quality@2`
  completeness anchor). A command that lists agents without dispatch/collect/output logic **fails**
  completeness — it is not "done."

## Exemplars (read before authoring)
- `.claude/commands/interview-prep.md` — 4-axis intake → parallel fan-out → synthesizer → advisory judge
  → parent-thread persist → present. The canonical multi-agent command.
- `.claude/commands/event-deep-research.md` — the pipeline rerun manual's Workflow A.
