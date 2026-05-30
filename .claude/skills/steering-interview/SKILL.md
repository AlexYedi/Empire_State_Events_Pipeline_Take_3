---
name: steering-interview
description: A short, 4-question intake that captures Alex's deliverable-specific steering context BEFORE research/content is generated — what to say, how to shape it, what to research deeper, and any personal context/goals/relationships to keep top of mind. Use at the start of any content flow (pre-event, post-event, weekly recap, project ideation, or any standalone content request). Invoke when Alex says "steer this", "interview me first", "before you build it ask me", or automatically as the first step of the event content flows. Runs in the main conversation (it is an interactive interview, NOT a subagent).
---

# Skill: Steering Interview

A lightweight, reusable intake that captures Alex's perspective on a specific deliverable **before** anything is generated — so his freshest, most-informed context steers the research and the content instead of being bolted on as corrections afterward.

This is the **front half** of the content quality loop:

> **Steer (this skill, before) → Generate → Comment (Notion, after) → Mine into rules (`update-voice-and-style`) → propagate to every skill.**

Today the only correction channel is post-hoc Notion comments (reactive). This skill makes steering **proactive** — and over time the accumulated steers are the richest signal for making Alex's voice "more informed" as he attends, builds, and reads more.

---

## Why this is a SKILL, not an agent (architectural note)

An interview is multi-turn and human-in-the-loop **by definition**. In this harness, subagents are one-shot and non-interactive — they receive a single prompt, run autonomously, and return once; they **cannot pause to ask a question and wait for the answer** (same SDK constraint that prevents subagents from spawning subagents). So a "steering interview agent" is the wrong primitive: it can't actually interview.

The interview must run in the **parent thread** (the main conversation), where the model asks and Alex answers. What's reusable is the *protocol* — the questions, the capture schema, and the routing rules — which is exactly what a skill is. **Always run this in the main conversation. Never dispatch it as a subagent.**

---

## When to run

- **Automatically:** as the first step of an event content flow — `/check-new-events` Step 6a.0 (before `/event-deep-research` for each event), or at the top of `pre-event-content` / `post-event-content` / `weekly-recap`.
- **On request:** any standalone content or deliverable ("steer this before you draft", "interview me first").
- **Reusable beyond events:** project-ideation, a one-off LinkedIn post, a research brief — anywhere Alex wants to steer before generation.

**Skippable by design.** If Alex has nothing to add for a given item, he says "skip" / "nothing for this one" and the flow proceeds with zero friction. Never block on it.

---

## The interview — one batched prompt, four questions

Ask all four together in a **single conversational message** (not four round-trips), tied to the specific deliverable by name. Free-text answers — these are open-ended elicitation, so do NOT use multiple-choice (`AskUserQuestion` is for picking between options, which this is not). Alex may answer any subset, or skip entirely.

Present it like this (adapt the deliverable name):

> **Quick steer before I build [DELIVERABLE] — anything to keep top of mind? (answer any, or "skip")**
> 1. **Content** — anything specific you want it to say, include, or avoid? A take you're forming, a stat you saw, an angle, a point you want made (or NOT made)?
> 2. **Structure / format** — any format preference for this one? (carousel vs single, short vs long, a specific hook, a thread, lead with X, etc.)
> 3. **Additional research** — anything to dig deeper on? A person, company, source, claim, or angle you want researched harder than the default.
> 4. **Anything else** — context from something you read / built / attended, a relationship or goal tied to this, a person you want to land well with, where your own thinking has moved. (This is the one that makes your voice more informed over time — don't skip it if you have something.)

---

## What each answer steers (routing — this is the point)

The four answers do NOT all feed the same stage. Route them:

| # | Answer | Must land before | Routes into |
|---|---|---|---|
| 1 | **Content** | content generation | the post's insight/hook, the point made/avoided, the framing |
| 2 | **Structure / format** | content generation | content shape + the visual-brief arc/format |
| 3 | **Additional research** | **the research fan-out** (so it can actually steer the agents) | the `/event-deep-research` specialist prompts (company/person/topic/signal scope) |
| 4 | **Anything else** | everywhere | research + content + the voice corpus (see persistence) |

**Critical timing:** because #3 steers research, the interview must run **before** the research fan-out — not after the brief. In `/check-new-events` that means Step 6a.0, ahead of `/event-deep-research`.

---

## Capture & persistence

Capture the answers verbatim (lightly cleaned) into a structured **Author Steer** block, and persist it so it's durable and mineable:

```
## Author Steer — [YYYY-MM-DD]
- **Content:** [verbatim answer, or "—"]
- **Structure/format:** [verbatim answer, or "—"]
- **Additional research:** [verbatim answer, or "—"]
- **Anything else:** [verbatim answer, or "—"]
```

**Where it lands:**
- **Events:** append to the **Event page body** under `## Author Steer — [date]` (sits alongside the brief; reviewable later; survives the session).
- **Non-event deliverables:** attach to the relevant artifact (the Content Draft page, the project page, etc.).
- Always thread the captured answers into the downstream prompts per the routing table above (don't just store them — *use* them in the same run).

**The compounding payoff:** accumulated Author Steer blocks are the highest-value input for `update-voice-and-style`. They capture Alex's perspective at the moment it's freshest (right before something he cares about), in his own words. Periodically — or whenever the voice files feel stale — mine the steers to update `content-style-guide.md` and `content-anti-patterns.md`. This is how stance-license grows with Alex's expertise instead of staying frozen.

---

## Integration points (where this is wired in)

- **`/check-new-events`** → **Step 6a.0: Steering interview**, run per event *before* `/event-deep-research`. Pass answer #3 into the research input; carry #1/#2/#4 to the `pre-event-content` invocation.
- **`pre-event-content`** → honors the captured steer when generating posts/notes/questions (content #1, format #2, context #4).
- **`event-deep-research`** → its input accepts an optional steer block; #3 scopes the fan-out.
- **`post-event-content` / `weekly-recap` / `project-ideation`** → same intake at the top.

---

## Rules

- **Never a subagent.** Run in the main conversation (see architectural note).
- **Always skippable**, per-question and overall. No friction when Alex has nothing to add.
- **One batched prompt**, free-text, not multiple-choice.
- **Run before research** when answer #3 could change the fan-out.
- **Persist verbatim**, then route — capture is worthless if it isn't threaded into the same run AND left for `update-voice-and-style` to mine.
- **Validation:** edits to this skill (and the commands that call it) need a **fresh conversation** to smoke-test — the skill/agent registry is loaded at conversation start (see CLAUDE.md § SDK runtime constraints).
