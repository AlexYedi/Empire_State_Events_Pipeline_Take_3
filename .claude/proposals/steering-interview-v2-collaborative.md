# Spec — Steering Interview v2: Collaborative Creation (two-touch)

**Status:** proposed → building (branch `alex/steering-v2-collaborative`)
**Linear:** YED-143 (this workstream)
**Owner:** Alex · **Date:** 2026-08-28

## Problem

The `steering-interview` skill runs a single 5-question intake **before** research/generation.
That placement is right for one thing (Q3 steers the research fan-out) but wrong for the moment
that actually produces collaborative, higher-quality content: the sharp, piece-specific questions
that only become askable **after** the research/prep surfaces the real forks. Observed live this
session — the interaction felt like co-creation precisely when the questions were *informed forks
derived from the work*, not generic up-front prompts. Generic pre-questions ("what's the angle?")
are weak; "the transcript leaned hard on X but your slug says Y — which post?" is the co-creation.

Root cause (systems framing): the current design has the elicitation loop in the wrong place
relative to the information it needs. The fix is not to move it — Q3 genuinely must run before the
fan-out — but to **split it into two touches**.

## Solution — two-touch steering

- **Touch 1 — AIM (before research):** the existing light intake, reframed. Its job is to *point
  the fan-out* — capture deeper-research direction (Q3), audience (Q5), and any strong upfront
  content/context (Q1/Q4). Fast, batched, fully skippable. Runs before `/event-deep-research`
  (and before Step 3.6 enrichment on the post-event side).
- **Touch 2 — SHARPEN (after prep, before drafting):** NEW. After the research brief /
  `post_event_brief` exists, the model **derives 2–3 genuine forks from what the prep surfaced**
  and puts them to Alex — real decisions the draft hinges on, not restated options. The loop is
  **kept open**: surface forks → Alex answers/pushes → adjust → only then draft. This is the
  collaborative-creation gate.

Both touches persist to the same **Author Steer** block (mineable by `update-voice-and-style`).

## The two operating principles (the reusable method)

1. **Prep-then-ask.** A Touch-2 question must be *derived from the prep* and specific to *this*
   piece. If the question could have been asked before any research, it belongs in Touch 1 (or is
   too generic to ask). Doing the homework first is what earns the right to ask a good question.
2. **Loop-kept-open.** Do not auto-draft straight to "done." Present the forks, incorporate the
   answer/pushback, iterate. The best output comes from the loop, not the first pass.

## Wiring (auto-fire — no extra trigger from Alex)

The gate is invoked as a **step in each content flow's spec**, so it fires deterministically when
any flow runs — no special command needed. Insertion points:

| Flow | Touch 1 (Aim) | Touch 2 (Sharpen) |
|---|---|---|
| `/check-new-events` → `/event-deep-research` + `pre-event-content` | Step 6a.0 (exists) | after the research brief, before `pre-event-content` generation |
| `post-event-content` | top / folded into Step 3.6 aim | **new Step 3.9**, after `post_event_brief` (3.7), before content-correspondent (Step 4) |
| `weekly-recap` | top | after event set assembled, before drafting |
| `pattern-synthesis` | — | after the 2 briefs are read, before the two-thesis draft |
| `content-correspondent` (direct) | — | after material is conditioned, before drafting |

The one non-deterministic seam: firing on a **bare casual mention** with no command relies on
CLAUDE.md's Tier-1 proactivity (model judgment), not a hook. By design — not hardwired.

## Non-goals / guards

- Not a hook. The interview is interactive → parent-thread skill, invoked by the flow specs.
- Still **always skippable**, per-question and overall. Never blocks.
- Does not change any pipeline's existing writes/gates (CLAUDE.md invocation policy layer B).

## Pre-mortem (adversarial pass — DoD item 3)

- **Failure: Touch 2 becomes friction / question fatigue.** Two touches could feel like being
  interviewed twice. Mitigation: Touch 1 is light and often "skip"; Touch 2 is ≤3 forks and only
  the *genuine* ones (if the prep surfaced no real fork, skip Touch 2 entirely and say so).
- **Failure: generic Touch-2 questions** (the exact anti-pattern this fixes) — the model asks
  "what's the angle?" after prep instead of a real fork. Guard: the skill mandates each Touch-2
  question name the specific tension from the brief; a question that isn't grounded in a brief
  section is disallowed.
- **Failure: loop-kept-open → never ships** (the deferral trap, cf. execution-focus 2026-06-11).
  Guard: Touch 2 is bounded to one round of forks by default; "kept open" means responsive to
  pushback, not infinite. Alex can always say "just draft it."
- **Failure: validation.** Skill/command edits are registry-frozen this session → must smoke-test
  in a fresh conversation before trusting auto-fire. Flagged in the skill's Rules.

## Definition of Done

Spec (this doc) · Linear YED-143 · adversarial pre-mortem (above) · build on branch → PR ·
`/dod-close`. ChatPRD/Notion PRD mirror **waived** — this is a method-upgrade to an existing skill,
not a net-new product surface; the in-repo spec + Linear issue are the source of truth.
