---
name: mock-interviewer
description: Run structured mock-interview practice rounds against a dossier — real (from interview-prep-dossier) or the bundled fixture — across four families (behavioural, commercial depth, technical/role-specific, curveball/stress). Probes the failure path harder than the happy path, scores every round on 7 fixed dimensions with quoted evidence, and emits a debrief shaped for a Notion needs_review draft. The parent Claude Code session orchestrates the rounds and owns every Notion write; this skill never calls Notion write tools. Use when Alex says "mock interview me", "run practice rounds for [company]", "grill me before the [stage] with [interviewer]", or after /interview-prep produces a dossier he wants to rehearse against.
---

# Mock Interviewer — failure-path practice rounds (E-09 · YED-256)

Practice rounds for the job-search loop: a dossier goes in, a scored, evidence-quoted debrief comes
out. The design bet is that interviews are lost on the failure path — the second follow-up that asks
for the volume behind the story, the "what did YOU do" attribution probe, the renewal that should
have churned — so every round drills failure cases harder than happy-path storytelling.

**Orchestration split (hard boundary).** This file is the methodology: round scripts, scoring
contract, scoresheet format, debrief contract. The parent Claude Code session does everything else —
picks rounds from the dossier, plays each interviewer persona, paces probes, transcribes answers,
applies the scoresheet, and writes the final debrief to Notion as a `needs_review` draft through the
sanctioned parent-owned write path (CLAUDE.md invariant 5). **This skill never calls Notion write
tools** — it produces debrief content and structure only.

## Inputs

- **A dossier** — either a real one (output of `interview-prep-dossier`, read by path at run time)
  or the bundled fixture `fixtures/dossier-northwind-freight.md` (fictional company + interviewers,
  for calibration and offline testing). Fields consumed: company snapshot · role, decoded ·
  interview stage · interviewer profile(s) · likely rounds.
- **Private inputs stay private.** `me-model.md` and `target-companies.md` are gitignored: read by
  path at run time only, never copied into this skill, its fixtures, transcripts, or debriefs.
  Fixture people and companies are fictional.
- Optional focus from Alex ("I always wobble on volume follow-ups") steers round selection.

## The failure-path-first rule

Happy-path confirmation gets **at most one question** per round. The script then moves down the
probe ladder into the failure case — volumes that must hold, an account that was lost, a handoff
that dropped, an AI claim that has to survive scoping. A round that ends without touching a failure
path was not run to spec. Rationale: the polish is already in the dossier; the round exists to find
what breaks under follow-up while there is still time to fix it.

## Round types — four families, nine scripts

| # | Family | Round | What it stresses · failure path it probes |
|---|---|---|---|
| 1 | Behavioural | Frustrated rep (discovery) | Listening under hostility; diagnoses before building |
| 2 | Behavioural | Hiring manager (behavioural) | Second/third follow-ups that ask for volumes — did the numbers hold? |
| 3 | Behavioural | Portfolio skeptic | Claims vs. evidence; attribution honesty on past projects |
| 4 | Behavioural | Take-home panel | Decisions under time pressure; scoping discipline |
| 5 | Commercial depth | Commercial: discovery call | Commercial bias — leading with the business problem |
| 6 | Commercial depth | Commercial: book review | Account-growth evidence; quota-attainment framing |
| 7 | Commercial depth | Commercial: QBR / renewal save | Failure paths, adoption and handoff, renewal mechanics |
| 8 | Technical / role-specific | Technical deep-dive | Depth on the 2–3 competencies the decoded role actually tests |
| 9 | Curveball / stress | Curveball / stress | Composure and prioritization under interruption and shifting constraints |

### Round scripts

Each script: **persona & posture → opening → probe ladder (F1/F2/F3) → failure-path probes → exit
condition → what good looks like.** F2/F3 are where rounds earn their keep; never skip them.

**1 · Frustrated rep (discovery)** — an irritated rep opening mid-complaint.
- Persona: impatient, interrupt-prone, skeptical of "discovery questions".
- Opening: "You've got ten minutes and I've already told this story to three people."
- Ladder: F1 let them vent, reflect the problem in their words → F2 ask the question that changes
  the diagnosis ("when did it last work correctly?") → F3 name the tradeoff they won't like and hold.
- Failure-path probes: does the candidate diagnose before proposing? Does the proposal survive the
  constraint the persona hasn't stated yet?
- Exit condition: the persona confirms a diagnosis with "at least you actually asked".
- What good looks like: two clarifying questions before any solution language.

**2 · Hiring manager (behavioural)** — volume follow-ups; the numbers must hold.
- Persona: warm, methodical, takes notes; always asks the second AND third follow-up.
- Opening: "Walk me through the win you're proudest of."
- Ladder: F1 the story → F2 the volumes ("how many accounts? what quota? what attainment?") → F3 the
  consistency check ("those numbers don't reconcile — walk me through it again").
- Failure-path probes: a lost account, a quarter that missed, a number that moved between tellings.
- Exit condition: the story survives three follow-ups without shifting.
- What good looks like: volumes offered unprompted; a miss owned with its mechanism, not excused.

**3 · Portfolio skeptic** — claims vs. evidence; attribution honesty.
- Persona: has read the resume closely; assumes inflation until proven otherwise.
- Opening: "Your summary says you 'grew' this book. Define grew, and show your work."
- Ladder: F1 the claim as stated → F2 who actually did what (attribution) → F3 what the claim would
  not survive ("would your CRO have told it this way?").
- Failure-path probes: borrowed credit, team results claimed as personal, positioning drift.
- Exit condition: the candidate re-states one claim more honestly than they entered the round with.
- What good looks like: clean attribution — sourcing named, own motion isolated — before being asked.

**4 · Take-home panel** — decisions under time pressure; scoping discipline.
- Persona: a panel of two; compressed timeline; a mid-exercise constraint change.
- Opening: "You have thirty minutes, not the weekend. Start."
- Ladder: F1 scope it aloud → F2 the constraint change ("assume half the data is unavailable") →
  F3 defend what was cut.
- Failure-path probes: overbuilding, silent scope creep, no cut ever named.
- Exit condition: a cut is named and defended without apology-spiraling.
- What good looks like: the do-nothing baseline stated before the build is proposed.

**5 · Commercial: discovery call** — commercial bias; lead with the business problem.
- Persona: a VP who disengages the moment the call sounds like a process interview.
- Opening: "I took this call because someone said you'd challenge my renewal forecast. Go."
- Ladder: F1 the business problem in their numbers → F2 the cost of inaction, quantified → F3 the
  commercial ask tied to their metric.
- Failure-path probes: feature-first drift, unquantified value, no ask at the close.
- Exit condition: the persona re-states the problem as the candidate framed it.
- What good looks like: the first question is about the persona's metric, not the product.

**6 · Commercial: book review** — account-growth evidence; quota-attainment framing.
- Persona: a CRO reviewing the book line by line; allergic to renewal-only framing.
- Opening: "Your book, last two years. Where did growth come from, and what attests to it?"
- Ladder: F1 the growth map (which accounts, how much) → F2 attainment against quota and base →
  F3 the hunting win as proof of account growth (a new logo only as evidence the motion scales).
- Failure-path probes: CSM/renewal-only framing; expansion credited to pricing; attainment quoted
  without its base.
- Exit condition: the framing survives "so you're really a farmer" without backpedaling.
- What good looks like: quota-carrying post-sales leads the story; hunting framed as proof of
  account growth.

**7 · Commercial: QBR / renewal save** — failure paths, adoption and handoff, renewal mechanics.
- Persona: a sponsor whose adoption is slipping and whose renewal is sixty days out.
- Opening: "Half my team stopped logging in. Convince me this isn't shelfware."
- Ladder: F1 the adoption diagnosis (who stopped, what changed) → F2 the handoff audit (what dropped
  between onboarding and now) → F3 the save mechanics (what renews on what evidence).
- Failure-path probes: blame-the-customer framing, no adoption metric, a save with no mechanism.
- Exit condition: a concrete 30/60-day adoption plan the persona repeats back.
- What good looks like: the handoff failure owned as the vendor's, then the fix priced.

**8 · Technical deep-dive** — role-specific depth (technical/role-specific family).
- Persona: the practitioner peer (for Alex's ICP: GTM-engineering / RevOps) who lives in the seams
  the role owns.
- Opening: "Skip the story. Walk me through the system."
- Ladder: F1 the architecture of the motion (data, seams, owners) → F2 the hardest failure in that
  system and its detection → F3 the AI component scoped honestly (does, doesn't, needs).
- Failure-path probes: buzzwords without mechanics, AI claims without data or eval grounding, the
  CRM-to-product seam nobody owns.
- Exit condition: the candidate draws the system and points at the broken part.
- What good looks like: mechanics, owners, and failure detection named without prompting.

**9 · Curveball / stress** — composure under manufactured chaos (curveball/stress family).
- Persona: an exec who interrupts, re-scopes, and asks the question from a different level.
- Opening: a mid-sentence interruption — "That's the last decade. What about the next one?"
- Ladder: F1 the interruption → F2 the frame flip (strategy ↔ execution) → F3 the hostile ambiguity
  ("just make it work") with no resource increase.
- Failure-path probes: composure, prioritization under constraint, asking for what's needed instead
  of absorbing the impossible.
- Exit condition: the candidate re-scopes the ask out loud and still lands a position.
- What good looks like: names the constraint, re-scopes, asks for the missing resource.

## Scoring — seven fixed dimensions (1–5, anchored)

The same seven dimensions every round; the session debrief rolls them up across rounds. Score
**1–5** and quote the transcript verbatim for every score. If a round never exercised a dimension,
mark it `n/e` (not exercised) with a reason — never invent evidence. **Any score ≤ 2 requires a
specific "what to say instead" rewrite** on the scoresheet. Anchors:

1. **Commercial bias** — leads with the customer's business problem and metric.
   5: opens on their metric unprompted, quantifies impact, never drifts to features · 3: business
   framing arrives, but late or on follow-up · 1: feature/process monologue.
2. **Diagnose before build** — diagnoses before proposing; builds only on stated constraints.
   5: questions visibly change the proposal · 3: diagnoses, then proposes anyway · 1: solution-first.
3. **Failure paths** — names what breaks, when, and how it is detected, before being asked.
   5: walks the failure path unprompted with specifics · 3: acknowledges failure cases when probed ·
   1: happy-path only; failure probes read as a gotcha.
4. **Adoption and handoff** — who must change behavior, how adoption happens, what hands off.
   5: names the adopting roles, the enablement, the handoff artifacts · 3: mentions adoption, no
   mechanism · 1: treats the sale as the finish line.
5. **Experimentation** — measurable tests with a do-nothing baseline and a kill criterion.
   5: test, baseline, and decision rule all stated · 3: test without a baseline · 1: "we'd iterate".
6. **Honest AI scoping** — what the AI component does, doesn't, and needs (data, evals, human gate).
   5: scopes the capability and its failure modes honestly · 3: capability stated, limits only under
   probe · 1: demo-ware claims.
7. **Communication across levels** — the same content tuned for rep / VP / CEO; numbers survive
   follow-up. 5: re-levels fluently, crisp structure · 3: one register only · 1: jargon-locked, or
   numbers shift between tellings.

## Scoresheet format

One scoresheet per round, completed by the parent session as the round runs:

```markdown
## Scoresheet — <round name> — <company, stage>

Interviewer persona: <name, role>

| Dimension | Score | Quoted evidence (verbatim from transcript) |
|---|---|---|
| commercial bias | 4 | "<a line quoted from the transcript>" |
| ... | ... | ... |

### What to say instead (required for every score ≤ 2)

- **<dimension>** (scored <n>): "<the specific rewrite — what to say instead, with its numbers>"
```

## Debrief contract

Two artifacts, both produced as content — never written to Notion by this skill:

1. **Per-round debrief** — immediately after each round: what the round probed, the dimension
   scores, every ≤2 rewrite, one keep / one fix.
2. **Session debrief** — after the last round, shaped as a Notion `needs_review` draft: title,
   three-line summary, per-round notes, dimension rollup across rounds (`n/e` marked), **top-3
   fixes** ranked by expected score movement, and the plan for the next session. The parent session
   owns writing it to Notion for comment review; the debrief carries the review-status line,
   nothing more.

## Fixtures (worked example)

`fixtures/` carries a fully worked three-round example against the fictional dossier — transcripts,
completed scoresheets, per-round debriefs, and a session debrief:

- `fixtures/dossier-northwind-freight.md` — fictional company + interviewers (marked fictional)
- `fixtures/round-1-hiring-manager/`, `fixtures/round-2-commercial-book-review/`,
  `fixtures/round-3-portfolio-skeptic/` — each with `transcript.md` → `scoresheet.md` → `debrief.md`
- `fixtures/session-debrief.md` — the consolidated debrief in the review-draft shape

Run the convention checks: `python3 .claude/scripts/test_mock_interviewer.py`.

## References

- `.claude/skills/interview-prep-dossier/SKILL.md` — the dossier this skill drills against
- `.claude/scripts/comp_gate.py` — the one executable copy of the comp rules; if comp comes up in a
  round, the dossier's research-sourced band and verdict govern (referenced, never restated)
- `.claude/references/me-model.md` §1.5 — Target-Role ICP (gitignored; read by path at run time,
  never quoted into git)
