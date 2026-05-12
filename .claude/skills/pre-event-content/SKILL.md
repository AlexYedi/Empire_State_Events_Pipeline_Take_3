---
name: pre-event-content
description: Generate pre-event content for NYC AI/tech events from completed research briefs. Produces LinkedIn posts (personal and "The Upcoming Week" roundup), speaker/host DMs with personalization, and prepared questions. Writes to Notion Content Drafts database. Use when Alex says "draft pre-event content for [event]", "write the LinkedIn post for [event]", "DMs for [speaker/host]", "Sunday roundup post", or anything similar. Requires a completed research brief in Notion.
---

# Skill: Pre-Event Content Generation

Generate pre-event content for NYC AI/tech events based on completed research briefs.
Produces LinkedIn posts, speaker/host DMs, and prepared questions. Writes to Notion
Content Drafts database.

**Prerequisites:** The event must have a completed research brief in Notion (generated
by the event-research skill). The skill reads from the brief — it does not do its own research.

**Reference files (read before generating any content):**
- `.claude/references/content-style-guide.md` — voice, tone, post architecture, audience, formatting
- `.claude/references/content-anti-patterns.md` — words, phrases, and patterns to avoid
- `.claude/references/outreach-templates.md` — DM structural patterns and personalization rubric

**Skills imported as craft references (read the SKILL.md when entering the relevant step):**
- `.claude/skills/brand-storytelling/SKILL.md` — narrative arcs, "5-second moment," movement framing → used in Step 2 + Step 3
- `.claude/skills/copywriting/message-architecture/SKILL.md` — Promise → Proof → Hook → CTA, hook formulas → used in Step 3
- `.claude/skills/content-patterns/visual-briefs.md` — carousel-as-narrative pattern, four arcs, per-slide schema, quality gates → used in Step 3b
- `.claude/skills/copywriting/cold-email-personalization/SKILL.md` (+ assets) — custom-signal openers, scoring rubric, QA checklist → used in Step 4
- `.claude/skills/marketing-autoresearch/SKILL.md` — variant/judge optimization loop → invoked at Step 5

The imported skills *augment* but do **not override** the existing reference files. When guidance conflicts (e.g., voice rules), `content-style-guide.md` and `content-anti-patterns.md` win. Imported skills supply structure and rigor; the references supply Alex's voice.

---

## Input

Alex provides one of:
- An event name (skill fetches the research brief from Notion)
- A pasted research brief (if generating outside the Notion workflow)
- A list of events for The Upcoming Week post

---

## Step 1: Load Context

1. Read all three reference files listed above
2. Fetch the research brief from Notion (search Content Drafts for the event name, Content Type = research_brief)
3. Extract from the brief:
   - Event name, date, location (virtual vs. in-person)
   - Topics with Current Events, Opportunities, Challenges, Use Cases, Top Questions
   - People with roles, POVs, connection angles
   - Companies with recent developments
   - Documentarian angle
4. Confirm with Alex what content types to generate for this event:
   - The Upcoming Week post (only if multiple events queued for the week)
   - Pre-Event LinkedIn post
   - Speaker/Host DMs
   - All of the above

---

## Step 2: Generate The Upcoming Week Post (if requested)

**When:** Sunday post covering all events for the coming week.
**Input:** Multiple event research briefs (one per event that week).
**Length:** Long-form.

**Before drafting, read `.claude/skills/brand-storytelling/SKILL.md`.** Apply specifically:
- **"Lead a movement, don't just solve a problem"** (Andy Raskin) — frame the week as a shift, a tension, or a question the NYC AI scene is collectively wrestling with. Not a list of events, a thesis about the week.
- **"Find the five-second moment"** (Matthew Dicks) — the entire roundup should orbit one moment of realization or transformation in the week's events. The synopses provide context to make that moment clear.
- **"Hook, message, celebration"** (Christina Wodtke) — the structure below maps to this: HOOK = mystery/surprise, FOR EACH EVENT = the message, CTA = the celebration/invitation.

### Structure

```
HOOK — Set the frame for the week. What's the through-line across the events?
       A trend, a tension, a question the week's events collectively address.

FOR EACH EVENT:
  - Event name + date + format (in-person / virtual)
  - 2-3 sentence synopsis: Why this event is relevant and consequential RIGHT NOW.
    Draw from one of these angles (pick the strongest for each event):
    * Trendiness — what's dominating the conversation in this space
    * Recent technological development — product launch, framework release, breakthrough
    * Product/industry segment shift — competitive dynamics, market moves
    * Macro/geopolitical impact — regulation, trade, investment patterns
    * Timeless criticality — if none of the above apply, why this topic is foundational
  - 1-2 sources/citations for the research behind the synopsis (so Alex can share deeper links)

EVENTS PENDING (if any):
  - Brief mention of events Alex has applied to / hoping to attend
  - Same synopsis treatment but lighter touch

CTA:
  "If you can't make it or aren't in the NYC area but have a question you wish you could
  ask — connect, message me and I'll ask it. If you're going, happy to connect before,
  don't hesitate to say and I'll see you there."
```

**Generate 2 variants** with different hooks/framing angles. Present as inline options.

### Quality Checks
- At least 2, no more than 3 data points per event synopsis
- Each synopsis passes the "So What?" test
- 2-5 relevant hashtags at the end
- Emoji used sparingly as structural markers

---

## Step 3: Generate Pre-Event LinkedIn Post

**When:** Per-event post, typically a few days before the event.
**Length:** Mid-form (8-15 lines).

**Before drafting, read both:**
- `.claude/skills/brand-storytelling/SKILL.md` — for the post's narrative arc. Apply **"Start in the middle of the action"** (Merci Grace) — open inside the tension, not with setup. Apply **"Problems beat successes"** (Jason Feifer) — the post's insight should orbit a real problem in the topic, not a celebration of progress.
- `.claude/skills/copywriting/message-architecture/SKILL.md` — for hook bank structure. Use the framework's **hook formulas** (question / contrarian / stat / story) to generate variants below. The Hook-Context-Insight-CTA architecture below maps to message-architecture's Audience → Promise → Proof → CTA.

### Structure

Follow the Hook-Context-Insight-CTA architecture from the style guide:

```
HOOK — First 1-2 lines. A surprising stat, a specific detail from the research,
       or a framing that makes someone stop. NOT "I'm excited to attend..."

CONTEXT — Why this event/topic matters right now. Connect to a broader trend or
          recent development from the research brief. This is where 2-3 data points land.

INSIGHT — The ONE thing. One deeply considered observation or one genuinely novel
          question about the topic. The thing that would make an expert pause.
          This is the entire value of the post.

CTA — "If you're deep into [topic], what are you most looking forward to learning
      or hearing about?"
```

**Generate 3 variants** with different hook formulas (per message-architecture):
- **Variant A:** Question hook — opens with a sharp question only an insider would ask
- **Variant B:** Contrarian hook — opens with a take that pushes against the consensus on the topic
- **Variant C:** Stat hook OR story hook — opens with a specific data point from the brief, OR a specific moment/anecdote

Present as inline options. Step 5 (autoresearch) will pick the strongest hook and refine.

### Quality Checks
- Exactly 2-3 data points from the research brief, with sources available if Alex wants to reference
- One clear insight or question that passes the expert-pause test
- No words/patterns from the anti-patterns file
- 2-5 relevant hashtags
- Emoji sparingly
- Documentarian framing: specific detail (reporter), synthesis (student), interpretation (analyst) — hit at least one

---

## Step 3b: Generate Visual Carousel Brief

For each LinkedIn post (Upcoming Week and/or Pre-Event), generate a single
**3-5 slide carousel brief** that tells the post's thesis through different
perspectives.

This step is **not optional**. Every LinkedIn post deliverable ships with its
carousel brief embedded in the same Notion page body. DMs and prepared questions
do not get carousels — they are private artifacts.

### Step 3b.1: Read the canonical pattern

Read `.claude/skills/content-patterns/visual-briefs.md` in full. That file is
the authoritative definition of:

- The four narrative arcs (Hook → Evidence → Mechanism → CTA; Thesis A → B →
  Tension → Take → Invitation; Before → After → What Changed → So What; One
  Question, Five Perspectives)
- Universal slide requirements (slide N of N, job, visual mode, headline, body,
  palette, source attribution, alt text, tool routing)
- Quality gates (arc fit, job differentiation, frame parallelism, thumb test,
  source citations, final slide earns the swipe)
- Anti-patterns (recap-of-the-post slides, generic AI hero shots, stat-without-
  context slides, "Follow for more" final slides, color-by-vibe)
- Output schema for the Notion page body

Everything below assumes that file has been loaded. Do NOT re-derive the shape
in this skill; if the spec has drifted, update `visual-briefs.md` directly so
all skills inherit the change.

### Step 3b.2: Pick the narrative arc

Match the post's argument structure to one of the four arcs from
`visual-briefs.md`:

| Post type | Default arc | Default slide count |
|---|---|---|
| Per-event pre-event post grounded in a data point | Arc 1 — Hook → Evidence → Mechanism → CTA | 3-4 |
| Per-event pre-event post about a panel with multiple speakers | Arc 4 — One Question, Five Perspectives | 4-5 |
| Per-event pre-event post about a change/shift the event surfaces | Arc 3 — Before → After → What Changed → So What | 3-4 |
| The Upcoming Week roundup post | Arc 4 — One Question, Five Perspectives (one slide per event) | 4-5 |
| Two-thesis synthesis (handled by pattern-synthesis skill, not here) | Arc 2 | 4-5 |

If the post doesn't fit cleanly into one arc, the post itself is probably trying
to do too much — go back to Step 3 and tighten the thesis before generating the
brief.

### Step 3b.3: Draft the carousel brief

Produce exactly one carousel brief per LinkedIn post, in the output schema
defined at the bottom of `visual-briefs.md`. The brief must include:

- The arc name (one of the four)
- One-sentence carousel thesis (what the reader walks away with after swiping)
- Slide count (3-5, determined by complexity not default)
- Tool routing summary (which slides → which generation tool)
- Per-slide blocks with: slide N of N, job, visual mode, headline (max 8 words),
  exact body/content text, palette with accent hex, source attribution if any
  data point or quote appears, alt text, tool
- Quality gate self-check at the bottom (arc fit, job differentiation, frame
  parallelism if Arc 2 or 3, thumb test per slide, source citations, final
  slide earns the swipe)

Every slide must be load-bearing. If you can drop a slide and lose nothing, the
carousel is padded — cut it before shipping.

### Step 3b.4: Quality gate enforcement

Before moving to Step 4, run every quality gate from `visual-briefs.md` against
the carousel brief. If any gate fails:

- **Arc fit fails** → return to Step 3b.2 and pick a different arc
- **Job differentiation fails** → cut the redundant slide
- **Frame parallelism fails** (Arc 2 or 3 only) → redraft the paired slides
- **Thumb test fails on any slide** → shorten the headline or cut a sub-headline
- **Source citation missing on a stat or quote slide** → add the source line
- **Final slide is "Follow for more" or recap** → replace with the question,
  take, or synthesis

Do NOT ship a brief with a flagged gate. The gate exists because that failure
mode is repeating across runs.

### Step 3b.5: Important notes

- **Briefs only, not images.** Do NOT generate images via MCP or any image API.
  Alex is building hands-on intuition with the generation tools (GPT-Image-1,
  Imagen 4, Magic Patterns, Canva); the briefs are what he pastes in.
- **The brief is the artifact.** When the post is reviewed, the brief is
  reviewed alongside it. They are one Content Draft, not two.
- **Voice propagation.** If `update-voice-and-style.md` runs and updates the
  written voice, the visual voice in `visual-briefs.md` must be reviewed in the
  same pass. They are paired.

---

## Step 4: Generate Speaker & Host DMs

**For each person** identified in the research brief (speakers, hosts, organizers):

**Before drafting, read `.claude/skills/copywriting/cold-email-personalization/SKILL.md` and these assets:**
- `assets/research-playbook.md` — what counts as a Tier 1 vs Tier 2 signal (recent talks, posts, hires, launches)
- `assets/scoring-rubric.md` — 0-100 scoring; **gate at ≥80 before presenting to Alex**
- `assets/qa-checklist.md` — pre-send checklist
- `assets/email-structure.md` — adapt the 60-120 word structure to LinkedIn DM (4-6 sentences)

**Mapping cold-email patterns → LinkedIn DMs:**
- "Custom Signal" path → use a specific moment from their talk abstract, recent post, podcast, or open-source work as the opener
- "Whole Offer" path is **NOT applicable** — Alex is not selling a product in DMs; he's opening a conversation. Skip.
- The **no-CTA rule** from `content-correspondent` still applies for first-touch with high-signal contacts: no "want to grab coffee" in DM 1.

Generate **2-3 DMs per person per topic** they're associated with. Each DM should:

1. Follow one of the structural patterns from `outreach-templates.md`
2. Meet **Level 3 personalization** (connect their specific work to a specific research insight)
3. Be **4-6 sentences**
4. Always reference the specific event topic or their specific talk topic
5. Include **1 question** good enough to use as a prepared question at the event
6. **Score ≥80 on the cold-email-personalization rubric** before presenting. If below 80, regenerate or flag the gap to Alex.

### DM Angle Differentiation

When generating 2-3 DMs for the same person, vary the angle:
- **DM 1:** Focus on their talk's core thesis — engage with their argument
- **DM 2:** Focus on a tangent or implication of their work — go somewhere adjacent
- **DM 3 (if applicable):** Focus on the intersection of their company/role and the topic — commercial angle

### Presentation Format

Present DMs grouped by person:

```
### [Person Name] — [Role] at [Company]
Talk/Topic: [their specific talk or the event topic]

**DM Option A** (angle: [thesis engagement])
> [full DM text]

**DM Option B** (angle: [adjacent implication])
> [full DM text]

**DM Option C** (angle: [company/role intersection])
> [full DM text]

Alex selects the strongest for outreach. Unused questions feed Step 5.
```

### Quality Checks
- Each DM passes Level 3 personalization (not Level 1 or 2)
- No DM could be sent to a different person by swapping the name
- No anti-pattern phrases ("love your work", "pick your brain", etc.)
- Light close, no hard ask
- 4-6 sentences, no walls of text
- Cold-email-personalization rubric score ≥80 (recorded inline next to each DM option)

---

## Step 5: Optimize the LinkedIn Post(s) via Autoresearch

**When:** After Alex selects the strongest variant from Step 2 and/or Step 3 — and ONLY for the LinkedIn posts. Do not run on DMs or prepared questions (see cadence rule below).

**Skill:** `.claude/skills/marketing-autoresearch/SKILL.md` — read it before invoking.

### What gets optimized

Run autoresearch on each piece, one at a time:
- **The selected per-event LinkedIn post** (Step 3 winner) — always
- **The selected Upcoming Week post** (Step 2 winner) — always, if generated
- DMs and prepared questions — **never**. Over-optimization breaks the personalization signal in DMs and adds zero value to private prep notes.

### Setup

- Persona #5 in the expert panel = **Alex's documentarian voice** (the autoresearch SKILL.md has this configured by default for Empire State runs)
- Score threshold: **80**, max **3 rounds**
- Elements to optimize per LinkedIn post: **Hook (lines 1-2)**, **Insight line**, **CTA**

### Procedure

1. Hand the selected variant from Step 2 or Step 3 to autoresearch
2. Let it run the full round structure (Round 1 → Round 2 → optional Round 3 → cross-breeding)
3. Receive back: optimized post + 2 runner-ups + score report
4. Present to Alex: winner vs. original side-by-side, with the score deltas per dimension
5. Alex picks final version (winner OR original OR a runner-up). Use that for Step 7 Notion writes.

### Outputs

Autoresearch writes to `content-drafts/<event>/autoresearch/`:
- `{event}-linkedin-post-optimized.md`
- `data/{event}-linkedin-post-experiments.json`
- `data/{event}-linkedin-post-optimization-report.md`

The Notion Content Drafts page body uses the **final post Alex picks** in step 4 above. The autoresearch artifacts stay in the repo as the audit trail.

### When to skip Step 5

Skip if:
- The event is < 12 hours away and time pressure is real (defer optimization to post-event learning)
- The brief itself is weak (autoresearch can't fix a missing insight — go back to event-research)
- Score on first pass already ≥85 with no flagged dimensions (rare; ship as-is)

---

## Step 6: Compile Prepared Questions

After Alex selects which DMs to send (Step 4) and the LinkedIn post is finalized (Step 5),
the remaining DM questions become the **Prepared Questions** list for the event.

Format:

```
## Prepared Questions: [Event Name]

### For [Person Name] — [Talk Topic]
1. [Question from unused DM] — (angle: [description])
2. [Question from unused DM] — (angle: [description])

### For [Person Name] — [Talk Topic]
1. [Question from unused DM] — (angle: [description])
```

Include context notes: "Ask this if [X topic] comes up" or "Good follow-up if they mention [Y]"

---

## Step 7: Write to Notion

Write all approved content to the **Content Drafts** database.

**Database:** `collection://6c24c9f5-66c9-4eed-a61d-3f9b87c3f775`

> **Visual carousel persistence rule (revised 2026-05-12):** Every LinkedIn post Content Draft (`linkedin_post_pre`, `linkedin_post_post`, `linkedin_post_synthesis`) MUST include the Step 3b carousel brief in the same page body, appended below the post copy under a `## Visual Brief — N-slide carousel` H2. The brief is one 3-5 slide carousel, not three single-image briefs — see `.claude/skills/content-patterns/visual-briefs.md` for the canonical shape. The carousel brief lives with the post it supports so Alex has both the copy and the per-slide prompts in one place when he opens the page in GPT-Image-1 / Imagen 4 / Magic Patterns / Canva. If Step 3b was skipped for a given post, that's a Step 3b execution gap, not a Step 7 schema gap — go back and run it.

### Content pages to create:

**The Upcoming Week post (if generated):**
```
"Title": "The Upcoming Week — [date range]"
"Content Type": "linkedin_post_pre"
"Event Phase": "pre_event"
"Content Status": "needs_review"
"Platform": "linkedin"
"Event": [relation to all events mentioned in the post]
"Topics": [relation to all topics across events]
```
Page body: the approved post variant + **the Step 3b carousel brief appended under a `## Visual Brief — N-slide carousel` H2** (one 3-5 slide carousel using one of the four arcs from `visual-briefs.md`). For The Upcoming Week roundup, the default arc is Arc 4 — One Question, Five Perspectives, with one slide per event.

**Pre-Event LinkedIn post:**
```
"Title": "[Event Name] — Pre-Event Post"
"Content Type": "linkedin_post_pre"
"Event Phase": "pre_event"
"Content Status": "needs_review"
"Platform": "linkedin"
"Event": [relation to event page]
"People": [relation to people mentioned]
"Topics": [relation to topics covered]
```
Page body: the approved post variant + **the Step 3b carousel brief appended under a `## Visual Brief — N-slide carousel` H2** (one 3-5 slide carousel using one of the four arcs from `visual-briefs.md`). Arc selection per Step 3b.2 — match the post's argument structure to the right arc (data-anchored → Arc 1; multi-speaker panel → Arc 4; change-over-time → Arc 3).

**Speaker/Host DMs (one page per person):**
```
"Title": "DM — [Person Name] re: [Event Name]"
"Content Type": "linkedin_dm_speaker" or "linkedin_dm_host"
"Event Phase": "pre_event"
"Content Status": "needs_review"
"Platform": "linkedin"
"Event": [relation to event page]
"People": [relation to person]
"Topics": [relation to relevant topics]
```
Page body: the selected DM + all alternate DMs preserved for reference

**Prepared Questions:**
```
"Title": "Prepared Questions — [Event Name]"
"Content Type": "prepared_questions"
"Event Phase": "pre_event"
"Content Status": "needs_review"
"Platform": "notion_only"
"Event": [relation to event page]
"People": [relation to all people with questions]
"Topics": [relation to relevant topics]
```
Page body: the compiled question list from Step 5

---

## Step 8: Summary

```
## Pre-Event Content Complete: [Event Name]

### Generated
- The Upcoming Week: [Yes/No] ([X] events covered) + carousel brief ([N] slides, Arc [name])
- Pre-Event Post: [variant selected] (autoresearch score: [X]/100) + carousel brief ([N] slides, Arc [name])
- Speaker/Host DMs: [count] people, [count] DMs total (avg cold-email-personalization score: [X]/100)
- Prepared Questions: [count] questions compiled

### Written to Notion
- Content Drafts: [count] pages created
- All relations linked to Event, People, Topics

### Autoresearch artifacts
- Path: content-drafts/<event>/autoresearch/
- Report: [filename] — biggest score lift on [element]

### Content Status
All drafts set to "needs_review" — Alex reviews and moves to "approved" when ready to post.
```

---

## Error Handling

- **Research brief not found:** Ask Alex to run event-research skill first or paste the brief directly.
- **No people in the brief:** Skip DM generation (Steps 4-5). Only produce posts.
- **MCP write fails:** Report exactly what failed. Offer to retry or present content in conversation for manual copy.
- **Anti-pattern detected in own output:** Flag it, explain why, and regenerate that section.
- **Personalization below Level 3:** Flag the DM as weak and explain what's missing. Offer to regenerate with more context or skip.
- **Autoresearch below threshold (Step 5):** If 3 rounds and final score is still <80, the issue is upstream — usually a weak insight in the source variant or a thin research brief. Don't ship a hyper-optimized variant of a bad post. Flag the dimension that scored worst, explain the likely root cause, and offer to either (a) regenerate Step 3 with a different angle from the brief, or (b) ship the original Step 3 winner unoptimized with a note that the brief needs a stronger insight before the next event.

---

## Cadence rules (do not violate)

- **Autoresearch on DMs:** never. Personalization is the value; optimization erodes it.
- **Autoresearch on prepared questions:** never. Private notes — no audience to score against.
- **Autoresearch on the per-event LinkedIn post:** every event.
- **Autoresearch on the Upcoming Week post:** every Sunday post.
- **Autoresearch on the synthesis post (`pattern-synthesis`):** optional. Run if the score on first pass is ≥75 and Alex wants the lift; skip if Alex wants the raw voice preserved.
- **Max one full pre-event run per event.** Don't re-run autoresearch on the same post unless the brief changes materially.
