# Orchestrator fan-out failure — diagnosis and fix

**Created:** 2026-05-05
**Triggering observation:** During the orchestrator validation run on the Wednesday Agentics event (see [comparison artifact](orchestrator-validation-comparison.md)), the `event-research-orchestrator` agent dispatched cleanly via Task but did not fan out to the four specialist subagents. It executed the research itself using WebSearch.

The orchestrator's own validation note read:

> *"In this single-model execution (no actual parallel subagents were spawned — the orchestrator ran the research directly using WebSearch), there is no subagent boundary drift to report."*

---

## Root cause

The fan-out failure has a single structural cause and two contributing factors.

### Structural cause — no tool whitelist on the orchestrator

[`event-research-orchestrator.md`](../agents/research/event-research-orchestrator.md) frontmatter:

```yaml
---
name: event-research-orchestrator
description: ...
model: sonnet
---
```

There is no `tools:` field. With no whitelist, the agent inherits the full default tool set — **including WebSearch and WebFetch**. The orchestrator therefore had two paths to "research a company":

1. Dispatch via `Task` to `company-researcher` (the architecturally intended path)
2. Call `WebSearch` directly (the inline shortcut)

When both are available, a competent Sonnet model will rationally pick the shorter path. The architecture is undermined by the tool surface it inherits.

### Contributing factor 1 — soft instruction language

The orchestrator prompt says:

> *"Your job: take the triage plan and produce a complete research brief by **fanning out four specialist subagents in parallel**, then synthesizing their outputs."*
>
> *"Use the Task tool with the following four subagent_types in **one** message — they run concurrently"*

This describes a process. It does not assert a hard contract. There is no language like "you may not research directly" or "WebSearch is not yours to call." A diligent Sonnet reading this can interpret "fanning out" as the recommended approach while still feeling free to optimize for efficiency.

### Contributing factor 2 — no self-check or invariant assertion

The agent does not check its own tool surface at the start. There is no "if WebSearch is in your tool list, that is a misconfiguration — flag and stop" gate. Every other quality bar is asserted ("each topic has 5 dimensions", "no invented hooks") but the architectural invariant (you must dispatch, not research inline) is not asserted.

---

## Why this matters

If the orchestrator path produces decent output anyway (and it did — see the comparison artifact, the validation brief is high quality), the natural next question is: does the architecture even matter?

It does, for three reasons:

1. **Parallelism wins time.** A real fan-out runs four specialists concurrently. Wall-clock time scales with the slowest specialist, not the sum. Single-model inline execution serializes the work.
2. **Specialist context windows.** Each specialist has a fresh context window, dedicated system prompt, and (intentionally) less main-conversation noise. A single Sonnet doing all four roles loses the focus benefit.
3. **Auditability.** Each specialist returns a discrete output that can be re-invoked, inspected, or replaced. Inline single-model execution returns one monolithic blob — re-running just the company research means re-running everything.

The validation brief was high quality despite the architectural failure because Sonnet is competent. That's not an argument against fixing it — it's a sign that quality is decoupled from architecture today, which is a brittle state.

---

## Recommended fix

Three changes, in order of impact. The first is sufficient on its own; the others are defense in depth.

### Fix 1 — Pin the orchestrator's tool whitelist (HIGH IMPACT)

Edit [`event-research-orchestrator.md`](../agents/research/event-research-orchestrator.md) frontmatter:

```yaml
---
name: event-research-orchestrator
description: ...
model: sonnet
tools: Task, Read
---
```

**Effect:** the orchestrator literally cannot research inline because WebSearch and WebFetch are no longer in its tool list. Task becomes the only mechanism for gathering information. `Read` stays so it can read the SKILL.md methodology file.

This is the single most important change. The architectural invariant becomes a tool-level invariant rather than a prompt-language soft constraint. The orchestrator can still synthesize the four specialist outputs into a brief — synthesis only requires reasoning, not research tools.

### Fix 2 — Strengthen instruction language (DEFENSE IN DEPTH)

Edit the "Specialists to invoke" section in the same file. Current text:

> *"Use the Task tool with the following four subagent_types in **one** message — they run concurrently"*

Proposed replacement:

> *"You research nothing yourself. Your only mechanism for gathering information is the Task tool. You do NOT have WebSearch, WebFetch, or any other research tool — and even if your tool surface drifts to include them, you must not use them. Doing the research inline defeats the purpose of this orchestrator: it serializes work that should be parallel, conflates four specialist contexts into one, and produces a non-replayable monolithic output. Dispatch all four specialists in a single Task message so they run concurrently."*

The point is to make the architectural intent unambiguous. If a future tool-whitelist drift re-exposes WebSearch, the prompt language should still hold the line.

### Fix 3 — Add a self-check at the start of the agent's work (DEFENSE IN DEPTH 2)

Add to the top of the system prompt (after "Your job: ..."):

> *"Before doing anything else: confirm that the Task tool is available in your tool surface. If `Task` is not in your tools, you cannot do this job — return immediately with the error 'orchestrator misconfigured: Task tool unavailable, fan-out impossible'. If WebSearch or WebFetch are in your tools, that is a misconfiguration — return with the error 'orchestrator misconfigured: research tools should not be in orchestrator surface, only specialists'. Do not silently fall through to inline research."*

This makes the architectural invariant a runtime check the agent performs on itself.

---

## Verification plan after fix

1. Apply Fix 1 (tool whitelist).
2. Open a fresh conversation in this repo (so the agent definition is reloaded).
3. Re-run the validation prompt from [orchestrator-validation-handoff.md](orchestrator-validation-handoff.md) on the Agentics event.
4. Inspect the orchestrator's tool calls — confirm 4 parallel Task invocations against the four specialists, NO WebSearch calls.
5. Inspect the four specialists' outputs — confirm each ran in its own context.
6. Compare wall-clock time vs. the inline run (~4–5 min) and the path-1 single-model orchestrator run (similar). Real fan-out should approach the slowest specialist's runtime, not the sum.

If verification passes, update WORKFLOWS.md:
- Workflow A status: 🟠 → ✅
- Remove the "Known gap" section
- Update last-updated stamp

If verification fails (e.g., specialists themselves can't research because they're missing tools they need), apply Fix 2 + Fix 3 and check specialist tool whitelists. Specialists should explicitly include `WebSearch, WebFetch, Read, Task` (Task so they can sub-delegate if needed, though they generally shouldn't).

---

## Out of scope for this artifact

- Whether the four specialist agents are individually well-scoped (separate review)
- Whether `notion-writer` has the right tool surface (separate review)
- Whether the orchestration shape itself (4 specialists × 5 dimensions × N entities) is the right decomposition (this is a methodology question, not a fan-out question)

---

## Open question for Alex

Apply Fix 1 immediately, or batch with the broader agent-config audit? My recommendation: apply Fix 1 now. It's a one-line change to the frontmatter, low-risk, and the architectural payoff is high. The other two fixes can wait until the next pass over the agents directory.
