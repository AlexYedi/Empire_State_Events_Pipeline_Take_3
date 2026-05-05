# Orchestrator fan-out fix — fresh-thread handoff

**Created:** 2026-05-05
**Why this exists:** isolating the `event-research-orchestrator` no-fan-out fix into a focused thread so it gets karpathy-discipline planning instead of opportunistic patching. The original validation thread already produced two artifacts (validation comparison + diagnosis) and one failed fix attempt (Fix 1, reverted). The next move requires deliberate design, not another guess.

---

## TL;DR for the new thread

**One-paragraph problem statement:** The custom Claude Code agent `event-research-orchestrator` was designed to dispatch four specialist subagents (`company-researcher`, `person-researcher`, `topic-landscape-analyst`, `competitive-signal-scanner`) in parallel via the `Task` tool, then synthesize their outputs into a research brief. In practice, when invoked, it bypasses fan-out entirely and does the research itself with `WebSearch`. The brief it produces is high-quality (Sonnet is competent), but the multi-agent architecture isn't being exercised — defeating the parallelism, the per-specialist context isolation, and the auditability the design was supposed to deliver.

**One-paragraph mission for the new thread:** Decide whether the architecture is recoverable, and if so, apply the right fix. The first attempted fix (frontmatter `tools: Task, Read` whitelist) backfired — `Task` was removed entirely from the orchestrator's tool surface while `WebSearch`/`WebFetch` survived. Don't repeat that. Approach the fix with karpathy discipline: surface assumptions before coding, run the smallest experiment that proves the mechanism, then apply.

**Done when:** the orchestrator demonstrably dispatches the three needed specialists in parallel during a verification re-run on the May 6 Agentics event, with zero `WebSearch` calls in its tool history. WORKFLOWS.md status flips to ✅ and the "Known gap" section is removed.

---

## How to start the new thread

### Step 1 — Open a fresh Claude Code conversation in this repo

```
cd /Users/sameoldexpressions/Documents/GitHub/Empire_State_Events_Pipeline_Take_3
claude
```

### Step 2 — Paste this opener

> I'm picking up the orchestrator fan-out fix as a focused thread. The full context is in `.claude/artifacts/orchestrator-fanout-fix-handoff.md` — read it first.
>
> Then read these in order: (1) the diagnosis artifact in the same folder, (2) `.claude/references/stack-readme.md` so you understand my current toolchain before proposing anything new, (3) the orchestrator agent definition at `.claude/agents/research/event-research-orchestrator.md`.
>
> Before doing anything else, follow the karpathy-coder discipline (`~/Documents/GitHub/alex-agents-skills/Software Development/karpathy-coder/`): state your assumptions about why the prior Fix 1 failed, and surface any unknowns before proposing a Fix 2 design. Do NOT apply a fix until I approve the design.
>
> Come back with: (a) your read of why Fix 1 failed, (b) two-to-three Fix 2 design options with tradeoffs, (c) the smallest experiment that would falsify each before committing, (d) **a stack-gap callout** — anchored against `stack-readme.md` — flagging if any candidate fix would require a tool not already in my stack, with explicit justification for why the existing stack can't solve it. Then we pick.

That opener forces design before patching, AND forces stack-anchored thinking on any new-tool proposal. Don't shortcut either.

---

## Required reading (in order)

1. **[orchestrator-fanout-diagnosis.md](orchestrator-fanout-diagnosis.md)** — primary doc. Read the Decision Log at the bottom carefully; the 2026-05-05 verification entry is what flipped Fix 1 from "applied" to "reverted."
2. **[orchestrator-validation-comparison.md](orchestrator-validation-comparison.md)** — context on what the inline-research collapse produced vs. what fan-out was supposed to deliver. Read the Structural axis especially.
3. **[orchestrator-validation-handoff.md](orchestrator-validation-handoff.md)** — original validation prompt (use the same prompt, modified, for the next verification re-run).
4. **`.claude/agents/research/event-research-orchestrator.md`** — the agent definition itself. Frontmatter is back to pre-Fix-1 state (no `tools:` line). Lines 22–30 are the fan-out instructions to potentially harden in Fix 2.
5. **`.claude/agents/research/{company-researcher,person-researcher,topic-landscape-analyst,competitive-signal-scanner}.md`** — the four specialists. None have `tools:` whitelists either. Skim only — full read isn't needed unless Fix 4 (architectural) becomes necessary.
6. **`.claude/commands/event-deep-research.md`** — the orchestration shape. Step 2 (lines 43–62) is where fan-out is invoked.
7. **`.claude/WORKFLOWS.md`** — Known Gap section + status row for Workflow A. This is what flips to ✅ when the fix lands.
8. **`.claude/references/stack-readme.md`** — Alex's full toolchain inventory. Read this BEFORE proposing any new-tool addition. Establishes what's already paid for / available / familiar (Claude Code, n8n, Supabase, Linear, PostHog, Vercel, Railway, Cursor, Replit, Devin, Factory, Lovable, Bolt, Framer, Notion, Gamma, Magic Patterns, Gemini, etc.). Anchor the gap analysis below against this baseline.

---

## What's been tried (do NOT repeat)

### Fix 1 — frontmatter `tools: Task, Read` whitelist — REVERTED

**Hypothesis:** if WebSearch/WebFetch are removed from the orchestrator's tool surface, the agent has no choice but to dispatch via Task.

**Result observed:** `Task` was REMOVED from the orchestrator's tool surface entirely (absent from both directly-callable AND deferred-via-ToolSearch lists). `WebSearch` and `WebFetch` were NOT removed — they remained as deferred tools. Net effect: fan-out became architecturally impossible while inline-research tools were retained — the opposite of intent on both axes.

**Likely root cause (per orchestrator self-report — needs verification):** `Task` is a Claude Code SDK primitive, not an MCP tool. Frontmatter `tools:` whitelists appear to filter against the MCP tool namespace and may actively *prevent* SDK primitives like `Task` from being inherited when listed in a restrictive allowlist.

**Don't:** add a `tools:` line to the orchestrator frontmatter again until Fix 4 (correct syntax) is researched and proven.

---

## Recommended fixes (priority order)

### Fix 2 — Strengthen prompt-level instruction language (PRIMARY)

The orchestrator's current instructions (lines 22–30 of its agent file) describe fan-out as a *process* but don't assert it as a *contract*. Reword to make Task dispatch the only acceptable behavior, with explicit anti-patterns called out.

Use **`Software Development/advanced-prompting-techniques`** to design this — specifically the Modular Prompt Framework + constrained-sampling angle. The goal isn't more words; it's the right structural elements (Persona / Instruction / Constraint / Negative-example) so a competent Sonnet can't rationally choose the inline shortcut.

**Verification mechanism:** the orchestrator's first action on every run is a tool-surface report (carry this forward from the prior run — it's a useful invariant). If `WebSearch` is in its tools and the instructions still say "you may not research inline," the model has been told clearly enough.

### Fix 4 — Correct tool-restriction syntax (OPEN ARCHITECTURAL QUESTION)

Before any further frontmatter `tools:` edits, answer:

1. Is `Task` whitelistable via the `tools:` field at all? Search alex-agents-skills and the Anthropic skills library for any agent that explicitly whitelists `Task` and works. If none exist, the answer is likely "no — Task is always inherited or always absent based on a different mechanism."
2. Is the right syntax something other than a comma-separated list? Some Claude Code agent definitions use array syntax. Verify against working examples.
3. Is the right approach to allow-list everything *except* WebSearch/WebFetch? Or is exclusion not supported and the right move is purely instruction-level (Fix 2)?

Where to look:
- `~/Documents/GitHub/alex-agents-skills/Software\ Development/karpathy-coder/agents/karpathy-reviewer.md` — has agent frontmatter, may show working tool config patterns
- The Anthropic skills mcp-builder skill (already in project) — likely has agent definition examples
- Claude Code official docs on agent definition format — search for "subagent_type tools whitelist"

### Fix 3 — Self-check at agent start (DEFENSE IN DEPTH, ONLY IF FIX 2 DOESN'T HOLD)

Have the orchestrator inspect its own tool surface as its first action and abort if `WebSearch`/`WebFetch` are present (with the message: "orchestrator misconfigured: research tools should not be in orchestrator surface, only specialists"). This makes the architectural invariant a runtime check.

The orchestrator already did this voluntarily in the failed Fix 1 verification run — it can be made mandatory in Fix 3.

### Fix 5 — Out-of-stack alternative (LAST RESORT, REQUIRES STACK-GAP JUSTIFICATION)

If Fixes 2/3/4 cannot deliver a working multi-agent fan-out within Claude Code, escalate to: "is multi-agent fan-out the wrong abstraction for this platform, and should the orchestration live somewhere else in the stack?" Candidate alternatives that already exist in Alex's toolchain (read `.claude/references/stack-readme.md` to confirm current state before proposing):

- **n8n** — paused, but the original architecture lived here. Could host the orchestration loop and call Claude as one node-per-specialist. Pro: durable, parallelizable, observable. Con: re-introduces the integration-layer fragility that Take-3 was built to escape.
- **Vercel Workflow DevKit** — durable orchestration, retries, step-based execution. Could wrap the fan-out as a workflow with one step per specialist. Pro: native crash-recovery. Con: introduces a runtime separate from Claude Code; coupling to Claude is via API not Task tool.
- **Devin / Factory** — agent-of-agents platforms. Different orchestration mental model entirely. Pro: built-for-purpose. Con: net-new tool to learn; cost/lock-in question.
- **Inline path (no fan-out)** — already proven (`event-research` SKILL.md inline path, ✅ wired). The "fix" becomes "accept that Workflow A's true canonical form is the inline path, archive the fan-out architecture, document why."

**Bar for proposing a tool ADDITION (not substitution):** the new thread must demonstrate, with evidence, that NO combination of (a) Fix 2 prompt language, (b) Fix 4 correct tool-restriction syntax, or (c) inline path acceptance solves the problem. Adding a new tool is the most expensive remediation; it requires the strongest justification. Read `stack-readme.md` first; quote the specific gap it can't fill; only then propose.

---

## Skills + agents to bring into the new thread

### From `~/Documents/GitHub/alex-agents-skills/Software Development/`

| Skill | Path | Why for this thread |
|---|---|---|
| **karpathy-coder** | `Software Development/karpathy-coder/` | The most important one. Forces "surface assumptions, surgical changes, verifiable goals" — exactly what Fix 1 violated. Has a review agent + pre-commit-style discipline. |
| **advanced-prompting-techniques** | `Software Development/advanced-prompting-techniques/` | Direct fit for Fix 2. Modular Prompt Framework decomposes the orchestrator instruction into Persona / Instruction / Constraint / Negative-example so the rewrite isn't ad-hoc. |
| **iterative-engineering-practices** | `Software Development/iterative-engineering-practices/` | TDD / fail-fast / shift-left discipline for the verification cycle. Each fix attempt should have a falsification experiment defined *before* it's applied. |
| **cto-architect** | `Software Development/cto-architect/` *(also `anthropic-skills:cto-architect` in project)* | Sanity check on whether the multi-agent fan-out architecture is even right, before sinking more time into fixing it. Use as the design-review gate before Fix 2 is committed. |

### From the project (already imported)

| Skill / Agent | Where | Why |
|---|---|---|
| **systems-thinking** | `.claude/skills/systems-thinking/` | If diagnosis stalls, run the 8-phase analysis on "why does Sonnet rationally choose inline over Task even when told not to." Likely surfaces a Drift-to-Low-Performance or Shifting-the-Burden archetype. |
| **`Plan` agent** | Built into Claude Code | For the design phase. Use it explicitly: "design the Fix 2 prompt change without applying it." |
| **`event-research-orchestrator` agent** | `.claude/agents/research/` | The verification target. Re-run it (only) after each Fix 2 candidate is in place. |

### Order of invocation (suggested)

1. `karpathy-coder` skill — discipline gate before any code change
2. `cto-architect` skill — design review for Fix 2 architecture
3. `advanced-prompting-techniques` skill — Fix 2 prompt construction
4. `iterative-engineering-practices` skill — define the falsification experiment for each Fix 2 candidate
5. (Apply Fix 2 candidate to `event-research-orchestrator.md`)
6. `event-research-orchestrator` agent — verification run with the prompt below

---

## Verification prompt (use after any fix is applied)

Same as the previous re-run, with one tweak — keep the tool-surface report as the first action so we can compare across fix attempts. Paste verbatim:

> VERIFICATION RE-RUN of `event-research-orchestrator` after applying Fix [N]. Same Agentics May 6 inputs as the prior runs.
>
> **Step 1 (mandatory first action):** report your current tool surface in plain text. List directly-callable tools and deferred-via-ToolSearch tools. This is the comparison invariant across fix attempts.
>
> **Step 2:** if `Task` is in your tool surface and `WebSearch`/`WebFetch` are either absent OR you correctly understand the new instruction prohibits using them — proceed to fan out. Dispatch the three needed specialists (`company-researcher`, `topic-landscape-analyst`, `competitive-signal-scanner`; person-researcher SKIPPED per triage) in a single Task message so they run concurrently.
>
> **Step 3:** if Task is missing OR you'd be tempted to use WebSearch — STOP and report. Do not do inline research. Return: "Fix [N] insufficient — [specific observation]."
>
> Inputs (unchanged from prior runs):
> - Event: Agentics: Use AI coding agents effectively, Wed May 6 6–9pm, 233 Spring St floor 11, NYC
> - Companies (all NEW): Agentics NYC, Nori (heynori.com), Vellum, Cognee, Modal Labs
> - Topics: AI Coding Agents (APPEND-CURRENT-EVENTS-ONLY), AI Agent Memory Layer (NEW full), AI Coding Agent Infrastructure (NEW full), Agentic AI (APPEND-CURRENT-EVENTS-ONLY)
> - People: skip (none named)
> - Constraint: do NOT write to Notion or HubSpot — return text only.
>
> Output: brief in event-research SKILL Step 3 schema + Validation Notes block answering: tool surface report, Task invocations made (subagent_type + scope), specialists completed cleanly, contract drift, wall-clock time, and **a structural comparison vs. the failed Fix 1 run from 2026-05-05** (what's different now, what's the same).

---

## Definition of done

The new thread can flip Workflow A to ✅ in WORKFLOWS.md when ALL of these hold on a clean verification re-run:

- [ ] Orchestrator's first action reports `Task` as available in its tool surface (directly-callable OR deferred — either is fine)
- [ ] Orchestrator dispatches a single Task message containing 3 invocations (`company-researcher`, `topic-landscape-analyst`, `competitive-signal-scanner`)
- [ ] No `WebSearch` or `WebFetch` calls appear in the orchestrator's tool history
- [ ] All 3 specialists return cleanly (no subagent contract drift in their output schemas)
- [ ] Wall-clock time is bounded by the slowest specialist (rough check: ≤ 6 min total) rather than serialized inline research
- [ ] Final brief matches the event-research SKILL Step 3 schema
- [ ] Validation Notes block confirms structural difference from the failed Fix 1 run

If any of those fail, the fix is incomplete — log what was observed in [orchestrator-fanout-diagnosis.md](orchestrator-fanout-diagnosis.md) Decision Log and iterate.

---

## Stack-gap analysis bar (added after handoff drafting)

If any candidate fix requires a tool not already in Alex's stack, the new thread MUST:

1. Read `.claude/references/stack-readme.md` first and confirm the gap is real (not just "this would be cool")
2. Quote the specific limitation in the existing stack that the new tool would fill
3. Identify whether an existing stack tool could be re-purposed instead (e.g., n8n for orchestration, Vercel Workflow DevKit for durability) — substitution beats addition
4. Estimate cost (financial + cognitive + integration time) of the addition vs. accepting a degraded fix
5. Flag the proposal in the response with `[STACK GAP]` so Alex sees it, not buries it

**Do not silently introduce a new tool dependency in code or instructions.** Every tool addition is a long-term commitment. Most fan-out fixes should fit inside the current stack — if they don't, the inline-path fallback (already ✅ wired) is the safety net.

---

## Out of scope for the new thread

To keep the thread focused, defer:

- Whether the four specialists are individually well-scoped (separate agent-config audit)
- Whether `notion-writer` has the right tool surface (separate)
- Whether the orchestration shape itself (4 specialists × N entities) is the right decomposition (this is a methodology question, not a fan-out question)
- Visual briefs / pre-event content / any other Workflow A downstream concerns
- Updating MEMORY.md or CLAUDE.md beyond the diagnosis files already touched
- Speculative tool-stack expansion that isn't directly load-bearing for this fix

The new thread does ONE thing: makes the orchestrator actually fan out (or proves it can't, and documents the substitute).

---

## Pointer back to the originating thread

Originating thread session: 2026-05-05.
Artifacts produced this session:
- `.claude/artifacts/orchestrator-validation-comparison.md`
- `.claude/artifacts/orchestrator-fanout-diagnosis.md` (with Decision Log)
- This file
- WORKFLOWS.md updates documenting the Fix 1 apply + revert cycle
- Notion: [\[orchestrator validation\] Agentics — Research Brief](https://www.notion.so/357d3699c2db816792eef9f93adf1caa)

If the new thread needs the original conversation transcript, it's recoverable from session history at the project level.
