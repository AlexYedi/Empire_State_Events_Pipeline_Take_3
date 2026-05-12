# Content Pipeline v2 — Stage 2 Proposal

**Status:** Awaiting decision — review at next session start
**Authored:** 2026-05-12 (end of Empire State week #1 with 4 events shipped)
**Decision needed:** build all / build subset / kick the can
**Reviewer:** Alex

---

## TL;DR

The visual-brief gap exposed this week was a symptom of a structural issue, not
a one-off miss. The content pipeline is at **Stage 1: flat skill invocation** —
every skill is a one-shot producer with no shared artifact types, no eval
harness, and no composition contracts. The fix shipped today (carousel-as-narrative
in `visual-briefs.md`) closed the symptom. The underlying state is unchanged.

This proposal lays out **Stage 2** — artifact schemas as first-class types,
typed skill contracts, eval gates, and machine-routable status transitions —
and three build paths (full / subset / defer). My recommendation: **kick the
can this week, but commit to revisit when 2-of-3 triggers fire weekly** (current
state: 1 firing intermittently).

---

## Where Stage 1 sits today (state as of 2026-05-12)

### What works
- Multi-agent fan-out from parent thread is reliable (4 events × 4 specialists
  + synthesizer + notion-writer = 24 agent invocations this week, zero "agent
  not found" failures)
- Synthesizer text-in/text-out contract holds across runs
- Notion-writer `tools:` whitelist discipline keeps "Prompt is too long" away
- File-persistence for oversized outputs works without manual intervention
  (59KB person-researcher + 78KB synthesizer outputs both shipped fine)
- The triage step catches genuine gaps (this week: Postman SKIP-vs-CREATE
  decision, Checkmarx/Kong needed for People relations the original triage
  didn't anticipate)

### What's brittle
- **Output shape isn't enforced.** The pre-event-content skill spec from
  2026-05-05 said every LinkedIn post ships with visual briefs. This week, I
  shipped 7 LinkedIn posts to Notion with zero visual briefs. The spec existed;
  it wasn't enforced. There's no validation gate between "skill ran" and
  "output meets spec."
- **No measurement.** We don't track post engagement, DM reply rates, visual
  CTR, or signal-success-rate retros. Without measurement, every iteration is
  intuition not improvement.
- **No composition contracts.** Each skill regenerates from scratch — when
  `pre-event-content` reads a research brief, it parses Notion page body
  markdown each time instead of consuming a typed `Brief` artifact. Same with
  `pattern-synthesis` reading two briefs, `content-correspondent` reading
  observations, etc.
- **HubSpot batch size 10** is encoded nowhere; caught at runtime this week.
  Same for the agent-registry-session-frozen rule (it's in CLAUDE.md but the
  workflow doesn't enforce a fresh-conversation check before testing new
  skills).

---

## The diagnosed problem

The visual-brief gap was easy to diagnose: the skill spec said "produce visual
briefs"; the agent didn't. The fix was easy: tighten the spec and add a
canonical pattern reference. Done in 30 minutes.

But the same class of failure can fire on any spec rule that's specified-but-not-enforced:
- Voice-and-style rules in `content-style-guide.md` — no validation
- Anti-pattern enforcement from `content-anti-patterns.md` — relies on agent
  self-policing
- Cold-email personalization score ≥80 gate — relies on agent self-reporting
- Cadence rules (max 1 synthesis post/week, autoresearch on DMs = never) —
  relies on agent reading them every invocation

The structural fix is **artifact contracts**: define the shape of each output
type, validate before write, route failures back to the producing skill. This
is more leverage than adding more specs because it changes *enforcement* not
*intention*.

---

## Proposed Stage 2 architecture

Four components. Each one independently valuable; together they convert
specified-but-not-enforced into validated-and-enforced.

### Component 1 — Typed artifact schemas

Define the shape of each artifact the pipeline produces:

```typescript
type Brief = {
  event_name: string
  event_date: ISO8601
  quick_take: string  // 3 sentences max, mobile-readable
  headline_findings: HeadlineFinding[]  // 3-5 required
  topics: TopicBlock[]  // with 5-dim or APPEND-CURRENT-EVENTS-ONLY flag
  people: PersonBlock[]  // with DM tier, hooks, prioritization signals
  companies: CompanyBlock[]
  documentarian_angle: DocumentarianAngle  // primary + optional secondary
  success_signals: Signal[]  // 3-5 with anti-signal
  verification_flags: Flag[]  // surfaced at top if load-bearing
}

type LinkedInPost = {
  thesis: string  // one sentence
  hook: string
  body: string  // 150-300 words for short post, 180-295 for synthesis
  cta: string
  visual_brief: VisualBrief  // REQUIRED — no LinkedIn post ships without one
  voice_check: VoiceCheck  // pass/fail per anti-patterns file
}

type VisualBrief = {
  arc: "Hook→Evidence→Mechanism→CTA" | "Thesis A→B→Tension→Take→Invitation"
     | "Before→After→What Changed→So What" | "One Question, N Perspectives"
  slide_count: 3 | 4 | 5
  slides: Slide[]
  quality_gates: QualityGateResults  // per visual-briefs.md
}

type DM = {
  person_id: string
  tier: 1 | 2 | "skip"
  hook: string  // specific personalization signal
  body: string  // 4-6 sentences
  personalization_score: number  // ≥80 required for Tier 1
  no_cta_check: boolean  // first touch with Bucket A = no CTA
}
```

Define them once as types. Reference them by name in every skill that
produces or consumes them.

### Component 2 — Validation gates between skills

Every skill declares which artifact types it consumes and produces:

```
event-research → produces: Brief
pre-event-content → consumes: Brief; produces: LinkedInPost[], DM[], PreparedQuestions
pattern-synthesis → consumes: Brief × 2; produces: LinkedInPost (Arc 2)
content-correspondent → consumes: RawEventInput; produces: LinkedInPost, DM[]
notion-writer → consumes: any artifact; produces: NotionPageURL[]
```

Before any skill writes to Notion, the artifact is validated against its
type. If validation fails (e.g., LinkedInPost has no visual_brief, or DM has
personalization_score < 80), the write is blocked and the artifact routes
back to the producing skill with the specific failure.

This is what "needs_review → approved" becomes: machine-gated, not just
human-gated.

### Component 3 — Eval harness per artifact type

Currently, post quality is measured by Alex reading and reacting. That doesn't
scale and doesn't generate signal for improvement.

Stage 2 adds:
- `content-quality/` skill (already exists as a directory — empty SKILL.md)
  runs evaluations against typed artifacts
- For LinkedInPost: voice match score, length compliance, data-citation
  density, CTA presence, anti-pattern detection
- For DM: personalization score (existing rubric), word count, no-CTA check
  for first-touch
- For VisualBrief: arc-fit, job-differentiation, frame-parallelism, source
  citations present
- For Brief: required-fields-present, headline-findings count, success-signals
  count with anti-signal

Results write back to the Content Drafts page as a `## Quality Report`
section. Alex sees the scores when reviewing.

### Component 4 — Status-transition automation

The Content Drafts DB has a status flow: `needs_review → approved → scheduled
→ published`. Currently all transitions are manual. Stage 2 wires:

- **Auto-promote needs_review → approved** when all quality gates pass AND
  Alex's approval threshold is met (his choice — strict / permissive)
- **Auto-route approved → scheduled** if Alex has wired a publishing
  integration (e.g., Buffer, Hypefury, or a custom n8n flow). Currently out
  of scope; this is a hook for later.
- **Auto-track published → retro** by linking the published post's
  engagement data back to the brief's success signals for measurement.

The retro link is what closes the measurement loop. Right now Step 7 retros
exist on Event pages, but they're disconnected from per-post performance.

---

## Triggers for build (when to commit)

Stage 2 is worth the build cost when **2 of 3 conditions fire weekly**:

| Condition | What "firing" looks like | Status this week |
|---|---|---|
| **1. Output quality is inconsistent** | Skill produces output that doesn't match its own spec | 🟡 Firing intermittently — visual briefs missed this week, fix shipped, but no enforcement layer means it can repeat on other spec rules |
| **2. Can't measure improvement** | Alex wants to know "are my posts getting better" and there's no answer | ⚪ Not firing yet — Alex hasn't asked the measurement question explicitly this week |
| **3. Composing skills requires custom orchestration each time** | New chains require writing new dispatch logic vs. clicking artifact types together | ⚪ Not firing — the four workflows (event-deep-research, post-event-synthesis, weekly-recap, voice-pass) all run with existing orchestration |

**Current state: 1 of 3 firing intermittently.** Not yet at the 2-of-3
threshold that justifies the build.

---

## Decision options

### Option A — Build all (full Stage 2)

**Scope:** All 4 components shipped in sequence
**Estimate:** 1-2 focused weeks of build (not background-mode; this needs
priority attention)
**Sequence:**
1. Component 1 (typed schemas) — 2-3 days
2. Component 2 (validation gates) — 3-4 days
3. Component 3 (eval harness) — 3-5 days, requires defining the scoring rubrics
4. Component 4 (status transitions) — 1-2 days

**When this is right:**
- You're pausing event attendance for a week to invest in pipeline
- You've decided the publishing-rate-driving-decay problem (YED-23) is
  actually a quality problem in disguise, and quality needs measurement
- You're hitting 2-of-3 triggers weekly

**When this is wrong:**
- Events are dense (this week's 4-event load showed the pipeline holds; no
  immediate crisis)
- The fixes shipped today (visual-brief enforcement via spec tightening)
  buy 2-3 more weeks of runway
- Stage 1.5 changes (encode HubSpot batch limit, add more spec tightening,
  improve handoffs without typing) might close 60% of the gap at 20% of
  the cost

### Option B — Build subset

Three high-leverage cuts, ranked by ROI per effort:

**Subset B1 — Component 2 only (validation gates)**
- 3-4 days build
- Catches the visual-brief-gap class of failure without typing every artifact
- Implementation: write a `content-quality/` SKILL that runs as a Step 7.5
  in pre-event-content, pattern-synthesis, and content-correspondent — reads
  the Notion Content Draft page body, runs spec compliance checks, flags
  failures BEFORE final approval
- This is the smallest valuable cut

**Subset B2 — Component 3 only (eval harness for LinkedInPost)**
- 3-5 days build
- Defines voice match, anti-pattern detection, length compliance,
  data-citation density, CTA presence for LinkedIn posts
- Doesn't touch types or status transitions
- Outputs a `## Quality Report` section in each post Content Draft page body
- This gives you the measurement loop without the typing investment

**Subset B3 — Component 1 minimal (Brief schema only)**
- 2-3 days build
- Define `Brief` as a typed artifact; everything downstream still untyped
- Skills that consume Brief (pre-event-content, pattern-synthesis,
  content-correspondent) read structured fields instead of parsing markdown
- This is the foundation that makes Components 2 and 3 easier to add later
- Lower immediate ROI; higher option value

### Option C — Kick the can

**What this means:** No build this session. Revisit at the start of next
session (this proposal auto-loads via CLAUDE.md).

**Between now and next decision, watch for:**
- Trigger 1 escalating from intermittent to weekly (a second class of
  specified-but-not-enforced failure surfaces)
- Trigger 2 firing — Alex asking "are my posts working" and not having an
  answer
- Trigger 3 firing — a new workflow that requires orchestration code instead
  of clicking existing pieces together
- The YED-23 publishing-rate-driving-decay problem getting worse (more
  drafts piling up at `needs_review`)

**What to do in the meantime:**
- Continue Stage 1 invocations
- Track which spec rules drift between invocations (informal signal for
  Trigger 1)
- Note when you wish you had quality metrics (informal signal for Trigger 2)
- Note when you write new orchestration vs. compose existing (Trigger 3)

---

## Recommendation (confidence: 70%)

**Option C — kick the can this week, with a tight watch list.**

Reasoning:
1. **The fixes shipped today close the immediate gap.** Visual-brief
   enforcement via spec tightening is a 30-minute change that solves the
   80% case for the next ~2-3 weeks. The remaining 20% is the structural
   issue that justifies Stage 2.
2. **Trigger threshold isn't met.** 1-of-3 firing intermittently doesn't
   warrant a 1-2 week build. Building too early creates the same problem
   as building the wrong agent topology — over-engineered solutions for
   problems that aren't yet acute.
3. **YED-23 is the higher-priority pipeline question right now.** The
   publishing-rate-driving-decay analysis from 2026-05-04 says the goal
   flip needs to land before more pipeline automation, or it deepens the
   trap. Stage 2 components 3 (eval harness) and 4 (status transitions)
   are partially YED-23 territory and shouldn't ship until the goal flip
   lands.
4. **Stage 1.5 has runway.** If you do want to invest a week before Stage
   2, it's likely better spent on: encoding the runtime constraints
   we've discovered (batch limits, agent-registry rule, file-persistence
   threshold), tightening more specs, and shipping the YED-23 dashboard.

Confidence is 70% because if Trigger 2 fires this week (e.g., a post bombs
and you want a measurement loop ASAP), the calculus shifts toward Subset B2.

---

## If decision = build some — which subset

If you'd rather build a subset now:

**Pick Subset B1 (validation gates) if:** another spec-drift failure has
surfaced since you read this and you want to prevent that class.

**Pick Subset B2 (eval harness for LinkedInPost) if:** you want measurement
on the posts shipping this week and next. This is the only subset that
generates new signal you don't currently have.

**Pick Subset B3 (Brief schema only) if:** you anticipate writing a new
content skill in the next 2-3 weeks (e.g., a project-ideation-from-brief
skill, an interview-prep-from-brief skill). The typing investment pays off
when new skills consume the same artifact.

Avoid building Component 4 (status transitions) until YED-23 goal flip
lands. Automating publication flow before fixing the publishing-rate-as-goal
problem deepens the wrong-goal trap.

---

## Implementation outline (if approved)

For reference at decision time — not for execution now.

### Component 1 — Typed schemas
- Create `.claude/types/` directory
- Files: `Brief.md`, `LinkedInPost.md`, `VisualBrief.md`, `DM.md`,
  `PreparedQuestions.md`, `Signal.md` — each with the type definition and
  required fields
- Update CLAUDE.md to reference the types directory
- Update each skill's import block to declare consumes/produces

### Component 2 — Validation gates
- Build out `.claude/skills/content-quality/SKILL.md`
- Define validators per artifact type (function: artifact → pass/fail + reasons)
- Wire validators into Step 7 of pre-event-content, Step 8 of pattern-synthesis,
  output step of content-correspondent
- Failure routes back to the producing skill with the specific failure

### Component 3 — Eval harness
- Define scoring rubrics for each artifact type
  - LinkedInPost: voice match (0-100), anti-pattern count, length compliance,
    data-citation density (citations per 100 words), CTA presence (yes/no),
    insight pause-test (yes/no — manual gate)
  - VisualBrief: arc-fit (pass/fail), all six quality gates (pass/fail each)
  - DM: existing personalization rubric (already 0-100)
  - Brief: required-fields-complete (pass/fail), headline-findings count,
    success-signals count with anti-signal present
- Quality Report writes to page body of every Content Draft as `## Quality
  Report` H2
- Aggregate quality scores over time → dashboard view in Notion

### Component 4 — Status transitions
- Auto-promote `needs_review → approved` when all quality gates pass
- Hold for human review if any gate flagged
- Out-of-scope this stage: scheduling/publishing automation

### Estimate refinement
- Full build (all 4 components): 1-2 weeks priority
- B1 only: 3-4 days
- B2 only: 3-5 days
- B3 only: 2-3 days

---

## Notes for next session

When this proposal loads at next session start:

1. Read this file in full before any work — context is important
2. Check whether Triggers 2 or 3 fired during the intervening week
3. If they did → reassess recommendation (likely shifts toward Subset B2 or
   Option A)
4. If they didn't → kick the can again, update this file with the new date
   and a single-line note on what stayed unchanged
5. Either way: capture the decision in this file's status header at the top
6. If decision is to build (full or subset): create implementation tickets,
   move this file to `.claude/proposals/archive/`, and reference from
   CLAUDE.md

The point of saving this is to prevent the decision from re-deriving every
session. The work to write this proposal is done. Future sessions inherit
it and decide.

---

## Reference

- `.claude/artifacts/systems-analyst-real-data-2026-05-04.md` — YED-23
  diagnostic, publishing-rate-driving-decay analysis
- `.claude/skills/content-patterns/visual-briefs.md` — visual brief
  canonical spec shipped 2026-05-12 (closes the immediate symptom)
- `.claude/WORKFLOWS.md` — Stage 1 workflow rerun manuals
- CLAUDE.md — overall architecture, Stage 1 components, SDK constraints
