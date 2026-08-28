---
name: steering-interview
description: Two-touch collaborative steering for any content deliverable. TOUCH 1 (Aim) — a light, skippable intake BEFORE research that points the fan-out (what to research deeper, who it's for, any strong upfront take). TOUCH 2 (Sharpen) — the collaborative gate AFTER the research/prep, where 2–3 genuine forks derived from what the brief surfaced are put to Alex before drafting. Use at the start of and midway through any content flow (pre-event, post-event, weekly recap, pattern-synthesis, project ideation, standalone posts). Invoke when Alex says "steer this", "interview me first", "before you build it ask me", or automatically as wired steps in the content flows. Runs in the main conversation (interactive — NOT a subagent).
---

# Skill: Steering Interview (v2 — two-touch collaborative)

A reusable intake that captures Alex's perspective on a specific deliverable so his freshest,
most-informed context steers both the research and the content — instead of being bolted on as
corrections afterward.

**v2 change (2026-08-28, YED-143):** steering is now **two touches**, because the questions that
actually create collaborative, higher-quality content are *informed forks that only exist after the
prep* — not generic up-front prompts. Splitting the single pre-research intake into **Aim (before)**
+ **Sharpen (after prep)** keeps the one thing that must run early (research direction) while adding
the co-creation moment where it belongs. Spec: `.claude/proposals/steering-interview-v2-collaborative.md`.

This is the **front half** of the content quality loop:

> **Aim → research → Sharpen → Generate → Comment (Notion, after) → Mine into rules (`update-voice-and-style`) → propagate.**

---

## The two operating principles (read these first — they ARE the method)

1. **Prep-then-ask.** The strongest steering question is *derived from the work* and specific to
   *this* piece: "the transcript leaned hard on X but your slug says Y — which post?" beats "what's
   the angle?" every time. If a question could have been asked before any research, it belongs in
   **Touch 1** (or it's too generic to ask at all). **Doing the homework first is what earns the
   right to ask a good question** — that is the whole reason v2 exists.
2. **Loop-kept-open.** Do not auto-draft straight to "done." Surface the forks → let Alex answer or
   push back → adjust → *then* draft. The best output comes from the loop, not the first pass. "Kept
   open" means responsive, not infinite: one round of genuine forks by default, and Alex can always
   say "just draft it."

Meta (from the live session that motivated v2): collaboration ignites when **Alex brings the *why*
and the pushback**, and **the model earns good questions by having done the prep**. Neither works
alone. Design every touch to invite the first and depend on the second.

---

## Why this is a SKILL, not an agent (architectural note)

An interview is multi-turn and human-in-the-loop **by definition**. In this harness, subagents are
one-shot and non-interactive — they cannot pause to ask a question and wait for the answer (same SDK
constraint that prevents subagents from spawning subagents). So the interview must run in the
**parent thread** (the main conversation). What's reusable is the *protocol* — the questions, the
capture schema, the routing rules — which is exactly what a skill is. **Always run this in the main
conversation. Never dispatch it as a subagent.**

---

# TOUCH 1 — AIM (before research)

**Purpose:** point the research fan-out and capture any strong upfront context. Light, batched,
fully skippable. Runs **before** `/event-deep-research` (and before the post-event Step 3.6
enrichment) so answer #3 can actually steer the agents.

Ask all five together in a **single conversational message** (not five round-trips), tied to the
deliverable by name. Free-text — open-ended elicitation, so do NOT use `AskUserQuestion` (that's for
picking between options). Alex may answer any subset, or skip entirely.

> **Quick steer before I research [DELIVERABLE] — anything to aim me? (answer any, or "skip")**
> 1. **Content** — anything you want it to say, include, or avoid? A take you're forming, a stat, an angle, a point to make (or NOT make)?
> 2. **Structure / format** — any format preference for this one? (carousel vs single, short vs long, a specific hook, lead with X.)
> 3. **Additional research** — anything to dig deeper on? A person, company, source, claim, or angle to research harder than the default. *(This one steers the fan-out — it must land before research.)*
> 4. **Anything else** — context from something you read / built / attended, a relationship or goal tied to this, a person you want to land well with, where your thinking has moved. *(The one that makes your voice more informed over time.)*
> 5. **Audience** — who is this primarily for? Which segment(s) — remote/excluded builder, time-constrained practitioner, aspirant/outsider, GTM peer, hiring manager, speakers/hosts — and any specific reader or outcome you're aiming at?

**Routing (this is the point — the five answers do NOT all feed the same stage):**

| # | Answer | Must land before | Routes into |
|---|---|---|---|
| 1 | **Content** | content generation | the post's insight/hook, the point made/avoided |
| 2 | **Structure / format** | content generation | content shape + the visual-brief arc/format |
| 3 | **Additional research** | **the research fan-out** | the `/event-deep-research` specialist prompts (company/person/topic/signal scope) |
| 4 | **Anything else** | everywhere | research + content + the voice corpus |
| 5 | **Audience** | content generation | which segment's job the post serves → what to surface + which variant carries the HM-activation angle |

---

# TOUCH 2 — SHARPEN (after prep, before drafting) — the collaborative gate

**Purpose:** the co-creation moment. The research brief / `post_event_brief` now exists; it has
surfaced real tensions, competing theses, quote-safety calls, and angle options. Put the **genuine
forks** to Alex before a single draft is written.

**How to run it well (mandatory):**

1. **Derive the forks from the brief — do not invent generic ones.** Read what the prep actually
   surfaced and name the specific tensions. Each fork must point at a real section of the brief.
   Good Touch-2 forks look like:
   - *"The room split — Speaker A argued [X], Speaker B [opposite]. Lead with the tension, or pick a side? (post-event stance-license is high here.)"*
   - *"Your strongest line is [Z], but it's MED-confidence in the quote bank — paraphrase it, drop the @-tag, or cut it?"*
   - *"The brief found two documentarian cuts: [the contrarian one] vs [the synthesis one]. Which is the post, and does the other become a synthesis candidate?"*
   - *"Research surfaced [non-obvious fact] that isn't in your slug — worth making the hook, or keep your original angle?"*
2. **Keep it to ≤3 forks**, ranked — the ones the draft genuinely hinges on. If the prep surfaced
   **no real fork**, say so in one line and skip straight to drafting: *"Brief is unambiguous — no
   forks worth your time; drafting now."* A manufactured question is worse than none.
3. **Present as forks, not a fill-in-the-blank.** These CAN use `AskUserQuestion` when they're
   genuine either/or choices (unlike Touch 1's open elicitation) — a fork is exactly a pick-between.
   Use free-text when the answer is open.
4. **Keep the loop open.** Incorporate the answer/pushback, adjust the plan, confirm, *then* draft.

**Timing:** runs **after** the brief is synthesized and **before** generation — never after a draft
exists (that's the reactive Notion-comment channel, which this is meant to front-run).

---

## Capture & persistence (both touches → one block)

Capture answers verbatim (lightly cleaned) into a structured **Author Steer** block and persist it:

```
## Author Steer — [YYYY-MM-DD]
**Aim (pre-research):**
- Content: [verbatim, or "—"]
- Structure/format: [verbatim, or "—"]
- Additional research: [verbatim, or "—"]
- Anything else: [verbatim, or "—"]
- Audience: [verbatim, or "—"]
**Sharpen (post-brief forks):**
- [fork put] → [Alex's call / pushback, verbatim]
- …
```

**Where it lands:**
- **Events:** append to the **Event page body** under `## Author Steer — [date]` (sits alongside the brief; survives the session).
- **Non-event deliverables:** attach to the relevant artifact (Content Draft page, project page).
- Always thread captured answers into the downstream prompts per the routing table — don't just
  store them, *use* them in the same run.

**The compounding payoff:** accumulated Author Steer blocks are the highest-value input for
`update-voice-and-style` — Alex's perspective at its freshest, in his own words, at the exact fork.
The **Sharpen** answers are especially rich: they are Alex's editorial judgment on real decisions,
which is precisely the signal that grows stance-license with his expertise instead of freezing it.
Periodically (or when the voice files feel stale) mine the steers to update `content-style-guide.md`
and `content-anti-patterns.md`.

---

## Integration points (where each touch is wired — auto-fires, no extra trigger from Alex)

| Flow | TOUCH 1 (Aim) | TOUCH 2 (Sharpen) |
|---|---|---|
| **`/check-new-events`** → `/event-deep-research` + `pre-event-content` | Step 6a.0, per event, before research | after the research brief commits, before `pre-event-content` generation |
| **`pre-event-content`** | honors the Aim steer (content #1 / format #2 / context #4 / audience #5) | runs the Sharpen forks on the committed brief before drafting posts/notes/questions |
| **`event-deep-research`** | input accepts the Aim block; #3 scopes the fan-out | n/a (research stage) |
| **`post-event-content`** | Aim folded in at/around Step 3.6 (aims enrichment + names the "land-well-with" person) | **Step 3.9** — after the `post_event_brief` (3.7), before content-correspondent (Step 4) |
| **`weekly-recap`** | Aim at top | Sharpen after the event set is assembled, before drafting |
| **`pattern-synthesis`** | — | Sharpen after both briefs are read, before the two-thesis draft |
| **`content-correspondent`** (direct) | — | Sharpen after material is conditioned, before drafting |

---

## Rules

- **Never a subagent.** Run in the main conversation (see architectural note).
- **Always skippable**, per-question and overall — both touches. No friction when Alex has nothing.
- **Touch 1:** one batched prompt, free-text (not multiple-choice), runs before research.
- **Touch 2:** ≤3 forks, each grounded in a specific brief section; skip cleanly if the brief has no
  real fork; may use `AskUserQuestion` for genuine either/or picks; keep the loop open (responsive,
  not infinite).
- **Prep-then-ask:** a question that isn't derived from the prep is a Touch-1 question or no
  question. Never ask a generic Touch-2 question.
- **Persist verbatim, then route** — capture is worthless if it isn't threaded into the same run AND
  left for `update-voice-and-style` to mine.
- **Never blocks a running pipeline's own writes/gates** (CLAUDE.md invocation policy, layer B).
- **Validation:** edits to this skill (and the commands that call it) need a **fresh conversation**
  to smoke-test — the skill/agent registry loads at conversation start (CLAUDE.md § SDK runtime
  constraints). Auto-fire cannot be trusted until validated in a fresh session.
