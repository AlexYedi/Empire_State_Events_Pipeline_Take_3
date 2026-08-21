---
name: pattern-synthesis
description: Generate a two-thesis synthesis LinkedIn post from two event research briefs. Use this skill when Alex wants to contrast two events into a single strategic post, when two event briefs in the same week pose opposing theses, when synthesizing ephemeral NYC AI/tech experiences into a recognizable documentarian format, or when Alex says "synthesis post", "two-thesis post", "pattern post", "contrast these events", "write the post from [Event A] and [Event B]", or anything similar. Triggers for phrases like "same week two-thesis", "platform vs bespoke post", "infrastructure vs integration post", or when Alex flags two recent briefs as a viable pairing. Also triggers when `post-event-content` or `pre-event-content` skills detect a viable synthesis opportunity across two briefs. This is the canonical format for Alex's documentarian angle — use it over ad-hoc synthesis prose whenever two briefs exist that meet the pattern's trigger conditions.
---

# Pattern Synthesis

Turn two event research briefs into one LinkedIn post in the two-thesis synthesis
format — the canonical shape for Alex's documentarian angle.

This skill does NOT invent the format. It orchestrates the pattern defined in
`../content-patterns/two-thesis-synthesis.md`. Read that file first, every time.
It's the authoritative definition of shape, voice, triggers, and gating rules.

---

## Inputs

Required:

1. Two Notion Event page URLs OR two event names (skill resolves names to URLs
   via `notion-search` on the Events collection).

Optional (if provided, skip the corresponding resolution step):

- Thesis A compressed claim (1 sentence) — if Alex already articulated it.
- Thesis B compressed claim (1 sentence) — same.
- Preferred Take direction — if Alex has a lean.

If only one event URL is provided, stop and ask Alex which second event to pair
with. Do NOT guess. The pair determines the whole post.

---

## Workflow

### Step 1 — Load the pattern references
Read `../content-patterns/two-thesis-synthesis.md` in full. The 6-part text
shape, voice rules, and gating conditions come from there.

Also read `../content-patterns/visual-briefs.md` in full. The carousel-as-narrative
spec, the four arcs, the universal slide requirements, and the quality gates
come from there. The required arc for pattern-synthesis output is **Arc 2 —
Thesis A → Thesis B → Tension → Take → Invitation**.

Everything below assumes both files have been loaded.

### Step 2 — Resolve the two events
For each input (URL or name):
- If URL, fetch via `notion-fetch` on the Event page.
- If name, search the Events data source (`collection://9dcbc999-b4ed-4a51-b48a-10aaf171f1ba`)
  via `notion-search` and confirm the match with Alex before proceeding.

Capture for each event: Event Name, Event Date, Event Description, related
People (speakers/hosts), related Topics, related Companies.

### Step 3 — Follow the related pages to pull evidence
For each event, fetch the full content of:
- All related Topic pages (Current Events, Opportunities, Challenges, Use Cases).
- All related People pages (Known POV / Bio) — especially speakers whose words
  anchor the thesis.
- All related Company pages (Recent Developments) — especially the hosting
  company.

The Thesis sentences and evidence sentences are drawn from this material. If
nothing quotable is in the briefs, the briefs aren't deep enough — stop and
tell Alex which brief needs reinforcement before generation is possible.

### Step 4 — Tension extraction (the load-bearing step)
This is where the skill earns its keep. Do NOT skip or shortcut this step.

a. Write Thesis A as one strategic claim — opinionated, falsifiable, specific to
   Event A's speakers/content. Not "Microsoft said things about agents" — "the
   Microsoft thesis is that platform primitives absorb bespoke agent work."
b. Write Thesis B in the same shape.
c. Ask: *do these claims directly oppose each other on a specific dimension?*
   - If yes, name the dimension (e.g., "where value accrues in the stack").
     This dimension IS the Tension.
   - If no, the pattern fails. Stop and tell Alex why. Offer two alternatives:
     (1) a different pairing, or (2) a different content format that doesn't
     require opposing theses.
d. Score the tension strength 1-5 (calibration below). If ≤ 2, stop — weak
   tension produces weak posts even when technically writable.

**Tension strength calibration:**
- **5/5** — The two theses pose a clear architectural, strategic, or market
  question that teams are actively making bets on *right now*. Reader can
  immediately picture which side their company would take and why.
- **4/5** — Clear opposition, but the question is more abstract or longer-horizon.
  Still worth shipping.
- **3/5** — Real opposition, but the dimension is narrow. Post will land with
  a specific sub-audience but probably not broadly.
- **2/5** — Opposition is manufactured or depends on a strained reading of one
  brief. Don't ship.
- **1/5** — The theses converge. No post exists.

### Step 5 — Apply gating conditions
Run through the "Gating conditions" section in the pattern file:
- Theses converge rather than diverge?
- Tension is about tooling preference, not strategy?
- One brief too thin?
- Pattern fatigue (already shipped one this week)?
- Generic Invitation?

If any gate fails, stop and report to Alex with a clear "skill declined to
generate because X." Do not force a post through a failed gate.

### Step 6 — Draft the post (2 variants)
Follow the 6-part shape from the pattern file exactly. Word targets are targets,
not caps, but stay within 180-295 words total — and a **hard cap of 3,000 characters**
(LinkedIn's limit; 180-295 words sits well inside it). Count before presenting; sources
go to the first comment, never inline. See `../references/content-style-guide.md` →
LinkedIn Character Budget. (Added 2026-06-10.)

Produce 2 distinct variants. They should differ in a meaningful way, not just
wording:
- **Variant 1** — leads with the tension in the Hook. Takes a clear side in the Take.
- **Variant 2** — leads with a concrete detail (a quote, a stat, a specific
  architecture choice) in the Hook. Take is more exploratory — invites the
  reader to help Alex decide.

Both variants must pass the voice rules: name names, no throat-clearing, first
person singular, specific over clever, no consultant-ese.

### Step 6b — Draft the visual carousel brief

Every synthesis post ships with a visual carousel brief. This step is **not
optional**. Read `../content-patterns/visual-briefs.md` in full before drafting.

The default arc for pattern-synthesis output is **Arc 2 — Thesis A → Thesis B →
Tension → Take → Invitation** because the post structure already maps onto this
arc one-to-one. The carousel makes the parallel structure visible:

- Slide 1: Thesis A (quote/diagram crediting Event A's speaker + the side's
  position)
- Slide 2: Thesis B (mirrored visual frame to Slide 1 — same layout, type
  hierarchy, palette assignments; only the content differs)
- Slide 3: Tension (the strategic question the two theses force against each
  other — diagram with two arrows converging on a single question)
- Slide 4: Take (Alex's lean OR the criterion he's using to decide — bold
  typography card with the take in 1-2 sentences)
- Slide 5 (optional): Invitation (the open question to the reader — bold
  typography card)

Slide count: 4 if the Invitation is integrated into Slide 4. 5 if the
Invitation earns its own slide. Never fewer than 4 — a two-thesis post requires
both theses + the tension + Alex's framing at minimum.

**Frame parallelism is the load-bearing constraint.** Slides 1 and 2 must share
visual frame exactly — same layout, same color logic, same type hierarchy. The
parallel structure IS the editorial choice. If the two sides look visually
different, the reader concludes one is more important than the other before they
read either.

Produce the carousel brief in the output schema defined at the bottom of
`visual-briefs.md`. Run the quality gates listed there:

- Arc fit (Arc 2 — required for pattern-synthesis output)
- Job differentiation (each slide does what no other slide does)
- Frame parallelism (Slides 1 and 2 share frame — flagged red if not)
- Thumb test per slide
- Source citations on any slide with a stat or named quote
- Final slide earns the swipe (no "Follow for more")

If any gate fails, redraft before moving to Step 6c.

### Step 6c — Auto-render the carousel via Gamma MCP (default; updated 2026-05-26)

After the brief passes Step 6b's quality gates AND Step 8 writes the Content
Draft to Notion, generate the carousel with `mcp__claude_ai_Gamma__generate`
(`format: "social"`, `cardOptions.dimensions: "4x5"`, `numCards` = slide count,
Stratos theme, `imageOptions.source: "noImages"`, stats-as-visuals in
`additionalInstructions`) per `../content-patterns/visual-briefs.md` →
`## MCP execution — Gamma (default); Canva (fallback only)`. Gamma is the default
ship path; Canva is a fallback only (demoted 2026-05-26 for garbling dense
labels). The Canva sequence below is retained as that fallback.

**Critical for pattern-synthesis: frame parallelism is load-bearing.** Slides 1
and 2 (Thesis A and Thesis B) MUST share visual frame exactly. When building
the `query` payload for Slide 2, include the explicit instruction: "LAYOUT:
Must use IDENTICAL layout to slide 1 of this same carousel — same quote
placement, same attribution layout, same type hierarchy. Frame parallelism is
the editorial choice — without it, the reader concludes one thesis is more
important than the other." Without this, Canva auto-styles each independently
and the parallel structure breaks.

Sequence per slide:
1. Build `query` payload from the slide spec.
2. Call `mcp__claude_ai_Canva__generate-design` with `design_type: "instagram_post"`.
3. Receive 4 candidates per slide.
4. Surface all candidates (4-5 slides × 4 candidates = 16-20 total) in a single
   markdown table covering all slides.
5. On Alex's selection, fire `mcp__claude_ai_Canva__create-design-from-candidate`
   per chosen design.
6. If tweaks needed, iterate via `mcp__claude_ai_Canva__perform-editing-operations`
   — do not re-fire `generate-design` for minor changes.

The brief still lives in the Notion page body as a human-readable reference;
auto-render runs alongside, not instead.

### Step 7 — Draft speaker/host DMs (sub-outputs)
For each speaker or host whose thesis anchors the post (typically 2-4 people total
across both events), draft a short DM that:

- Opens with a specific detail from their event contribution (not "great event").
- Tells them a synthesis post is coming that includes their thesis.
- Invites them to respond publicly or privately after it ships.
- Ends with a soft intro for Alex's continued contact.

Length: 60-100 words per DM. This is NOT the pre/post-event-content DM format —
those are separate. These are *synthesis-post-specific* DMs that ride on the post.

### Step 8 — Write to Notion + return output
Create a Content Draft via `notion-create-pages` targeting data source
`collection://6c24c9f5-66c9-4eed-a61d-3f9b87c3f775` with:

- **Title:** `[Theme] — [Event A] vs [Event B]` (e.g., "Platform vs Bespoke — FDE vs Microsoft")
- **Content Type:** `linkedin_post_synthesis` (the new option added 2026-04-19)
- **Event Phase:** `post_event` if both events are attended; `during_event` if
  one is still upcoming; `pre_event` if both are still upcoming.
- **Content Status:** `needs_review`
- **Platform:** `linkedin`
- **Event relation:** JSON-array-string of BOTH Event page URLs.
- **People relation:** JSON-array-string of the union of named speakers/hosts
  from both events.
- **Topics relation:** JSON-array-string of the union of related topics from both
  briefs.
- **Body:** Both variants, clearly labeled "Variant 1" and "Variant 2," followed
  by the **Step 6b carousel brief under a `## Visual Brief — N-slide carousel`
  H2** (Arc 2 — required for synthesis posts; see `../content-patterns/visual-briefs.md`
  for the canonical output schema), followed by the per-person DM drafts under
  a "Speaker/Host DMs" header.

Follow the Notion gotchas from CLAUDE.md exactly:
- Multi-select: JSON-array-STRING (`"[\"x\",\"y\"]"`), not native array.
- Relations: JSON-array-string of full page URLs, not bare IDs.
- Select: exact match to defined options.
- Verify the Content Drafts schema with `notion-fetch` before batch create if
  you haven't seen the current state in this session.

Return to Alex:
- Notion Content Draft URL.
- The two variants inline (so Alex can react without clicking through).
- The speaker DMs inline (same reason).
- Tension strength score (1-5) with the calibration rationale.
- Any gating checks that were close calls — Alex decides whether to ship.

---

## When NOT to trigger this skill

- Single-event posts — use `pre-event-content` or `post-event-content` instead.
- Synthesis across 3+ events — use a different format ("pattern across 5 events,"
  not yet built). This skill is strictly 2-thesis.
- Pure recap posts — no opposing theses needed = use post-event recap format.
- When Alex asks for a "hot take" or a "reaction" — those are one-thesis posts
  with an edge. Different format, not this one.

---

## Interaction notes

- If tension score is 3/5, lean toward asking Alex before shipping — sometimes
  a 3/5 becomes a 4/5 with a better compression of Thesis A or B.
- If gating fails, offer the alternative formats explicitly rather than just
  declining. The point is to get content shipped, not to gatekeep.
- If Alex has already articulated the Tension himself in chat, use his framing.
  Don't re-derive what he's already done.
- Speaker DMs can be skipped if Alex says so — but offer them by default. They're
  the reason the post ships with compounding value.

---

## Reference

- `.claude/references/audience-north-star.md` — **top-level ethos** (mission, persona, three floors, Learn-More Set); `.claude/references/content-style-guide.md` + `content-anti-patterns.md` codify the operative rules and win on voice conflicts.
- `../content-patterns/two-thesis-synthesis.md` — text pattern definition
  (required reading every invocation).
- `../content-patterns/visual-briefs.md` — carousel-as-narrative visual pattern
  (required reading every invocation; Arc 2 is the required arc for synthesis
  posts).
- Project CLAUDE.md — Notion schema, write orchestration, property format gotchas.
