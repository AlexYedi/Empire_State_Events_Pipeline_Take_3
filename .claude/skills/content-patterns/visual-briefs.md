# Visual Briefs Pattern — Carousel-as-Narrative

A reusable content shape for the visual companion to every LinkedIn post Alex
ships. This file is the authoritative definition. Skills that generate or review
visual briefs (`pre-event-content`, `pattern-synthesis`, `content-correspondent`,
and any future content skills) should read it rather than re-derive the shape.

Owner: Alex — personal voice. Edit this file when the visual style or carousel
structure evolves; all skills that import it inherit the change.

---

## The core idea

A LinkedIn post is a thesis. A visual carousel is that thesis told through
**different perspectives** — not the same image redrawn five times, not three
disconnected hero images, but a deliberate narrative arc where each slide takes
a real angle on the post's argument.

The carousel is the public-facing artifact of Alex's documentarian voice. Where
the post text demonstrates synthesis, the carousel demonstrates that the
synthesis is *visible* — the patterns are real enough to render.

Most LinkedIn carousels fail because they treat the format as a slideshow of
the post's bullet points. That isn't a carousel — that's reading reluctance
disguised as engagement. Alex's carousels earn the swipe by giving each slide
a job the previous slide couldn't do.

---

## Default output

**Most LinkedIn posts ship with an accompanying visual (a single image or a 3-5 slide carousel) — but not all** (softened 2026-05-27).
A text-only post is a valid, intentional variety choice for a simple informative summary; visuals are the default on most posts, not a hard requirement on every one. DMs and prepared questions never get visuals — they are private artifacts.

The carousel brief is embedded in the LinkedIn post's Notion page body under a
`## Visual Brief — N-slide carousel` H2 heading, immediately after the post copy.

**Default ship path (updated 2026-08-07 — Claude design; Gamma REMOVED).** Claude
is the default generator for all structured / label-dense visual content — singles
and carousels. After producing the brief, Claude authors the visual as a
**self-contained HTML/SVG design** and publishes it via the **Artifact tool**;
Alex exports to 4:5 PDF/PNG (⌘P → Save as PDF gives a LinkedIn-ready carousel).
Claude renders exactly what's authored — no re-interpretation, which is what broke
dense labels in Gamma/Canva. See `## Execution — Claude design (default) + Gemini
(pictorial)` below.

**Why Gamma was ripped out (2026-08-07):** Gamma was chosen in 2026-05 over Canva
because Canva's `generate-design` garbled dense labels. But Gamma is still a
constrained app that re-interprets the brief — it re-flows and mangles dense labels
too, and forces a tool→export hand-off. Authoring the pixels directly in HTML/SVG
removes both failure modes: nothing re-interprets the content, and iteration stays
in-conversation (edit the file, republish, same URL). **Pictorial imagery**
(conceptual / editorial / photographic, no dense labels) → **Gemini** (Alex's
subscription, frontier-flexible, not an app harness). **Canva is vestigial.**

Slide count is determined by the post's thesis complexity, not by a default:

- **3 slides** — single-thesis posts with one supporting data point and one CTA
- **4 slides** — single-thesis posts with two supporting angles, or two-thesis
  synthesis posts
- **5 slides** — two-thesis synthesis posts with a comparison view, weekly
  roundup posts covering 3+ events, or multi-data-point posts where each data
  point earns a slide

If the natural arc fits in 3 slides, do not pad to 5. If the arc actually
requires 6+, the post itself is probably trying to do too much — go back to the
copy.

---

## Option framework (added 2026-05-26 — Alex review)

When proposing a post's visual, offer **four distinct format options**, not four near-identical candidates of one design:

1. **Single image A** — one infographic / diagram concept.
2. **Single image B** — a *different* single concept (a different cut: matrix vs. graph vs. comparison).
3. **3-slide carousel** — condensed arc.
4. **5-slide carousel** — full arc.

**Emphasis: real visual information** — infographics, architecture / flow diagrams, statistics, charts/graphs, matrices, before/after, "where the value moves." Typography-only cards are a fallback, not the goal; never stock or decorative AI imagery. Every statistic in the post is a candidate for a chart or a stat-callout.

**Tooling (updated 2026-08-07): Claude design is the DEFAULT generator for all structured visual content** — every single image and every carousel — authored as self-contained HTML/SVG and published via the Artifact tool, because Claude renders exactly the labels / diagrams / matrices / stat-callouts as authored (no app re-interpretation — the failure mode of both Gamma and Canva).
- **Author:** hand-write the design — dark editorial ground, ONE meaning-bearing accent (see palette below), real typographic hierarchy, inline SVG for diagrams / arrows / timelines. Load the `artifact-design` (+ `artifact-diagramming`, `dataviz`) skills first for calibration.
- **Size + export:** 4:5 (1080×1350) per slide; use container-query units so it's exact at full size and responsive. Add print CSS (`@page{size:1080px 1350px}` + a page-break per slide) so ⌘P → Save as PDF yields a clean multi-page carousel PDF.
- **Pictorial only:** Gemini for conceptual / editorial / photographic imagery with no dense labels (Claude writes the prompt; Alex generates). Gamma removed; Canva vestigial.

**Post-event learnings cuts (added 2026-06-27, YED-96).** When the source is a v2 `post_event_brief` with a learnings tier, three high-value visual cuts open up — each must ADD the tactic, never re-print the post's quotes:
- **Pro-Tips checklist** — the room's "if X, do Y" tips as a clean checklist / framework card (Arc 1 mechanism, or a standalone matrix).
- **Pitfalls / anti-patterns** — what NOT to do, as a contrast or red-accent risk card.
- **Best-practice before→after** — a pattern shown as the shift it produces (Arc 3).
Source each tip to the named speaker in the brief; the Arc-4 guard still applies (no quote-card-per-speaker repetition of the post body).

## The four narrative arcs

Every carousel uses one of these four arcs. Each arc is a different way to render
the *same* thesis. The skill picks the arc that matches the post's argument
structure, not the one that's prettiest.

### Arc 1 — Hook → Evidence → Mechanism → CTA

Best for: **single-thesis posts grounded in a specific data point.**

| Slide | Job | Visual mode |
|---|---|---|
| 1 | Hook — a provocation, headline, or unanswered question | Bold typography card |
| 2 | Evidence — the data point that makes the hook real | Single-number data viz with one annotation |
| 3 | Mechanism — the diagram or org chart that explains *why* the data is what it is | Diagram / org chart |
| 4 (optional) | Counterpoint — the strongest objection or the nuance the data hides | Quote card or split-frame comparison |
| Final | CTA — the question the post is asking the reader | Bold typography card with the closing question |

Use this when you want the carousel to mirror the post's argumentative structure.

### Arc 2 — Thesis A → Thesis B → Tension → Take → Invitation

Best for: **two-thesis synthesis posts (pattern-synthesis skill output).**

| Slide | Job | Visual mode |
|---|---|---|
| 1 | Thesis A — one side of the tension, with the speaker/event credited | Quote card or org chart of the side's structure |
| 2 | Thesis B — the other side, in the same visual shape as Slide 1 | Quote card or org chart, mirrored layout |
| 3 | Tension — the strategic question the two theses force against each other | Diagram showing the two arrows pointing at the same target |
| 4 | Take — Alex's lean (or the criterion he's using to decide) | Bold typography with the take in 1-2 sentences |
| 5 (optional) | Invitation — the open question to the reader | Bold typography card |

Slides 1 and 2 must be visually parallel — same layout, same color logic, same
type hierarchy. The parallel structure IS the editorial choice. If the two sides
look different, the reader concludes one is more important than the other.

### Arc 3 — Before → After → What Changed → So What

Best for: **change-over-time posts** (DORA paradox, hiring shift, role
convergence, title rewrite, "category invented in 60 days").

| Slide | Job | Visual mode |
|---|---|---|
| 1 | Before — what the world looked like 1-3 years ago | Org chart, diagram, or stat card |
| 2 | After — what it looks like now | Same shape as Slide 1, transformed |
| 3 | What changed — the specific mechanism or trigger | Diagram with the delta highlighted |
| 4 (optional) | Implication — what teams should do differently now | Bold typography card |
| Final | So what — the question the reader should now ask of their own org | Bold typography card |

Slides 1 and 2 must use the **same visual frame** (same axes, same layout, same
color palette assignments) so the change is legible at a glance. If the frames
differ, the change is hidden.

### Arc 4 — One Question, Five Perspectives

Best for: **multi-speaker panel posts** (the per-speaker curiosity snippet
format), **weekly roundup posts** covering multiple events.

| Slide | Job | Visual mode |
|---|---|---|
| 1 | The question or theme that runs through all perspectives | Bold typography card |
| 2-N | One perspective per slide — each named (speaker / event / company) | Quote card or stat card per perspective |
| Final | Synthesis — what the perspectives reveal together that none reveal alone | Diagram or typography card |

Slides 2-N must all follow the same template (name + role + their angle) so
the reader can compare. Vary the *content*, not the *frame*.

> **Arc 4 guard (added 2026-05-26):** quote/stat cards are valid ONLY if each
> perspective slide ADDS context the post body doesn't already state — e.g., what
> the speaker actually built/demoed, or a distinct data point. If the post text
> already lists the quotes, a quote-card-per-speaker carousel is pure repetition.
> Pick a different arc instead (often Arc 1 or Arc 3) that visualizes the
> *implication* of the convergence rather than re-printing the quotes.

---

## Universal slide requirements

Every slide in every carousel must specify:

1. **Slide N of N** — explicit position in the arc, with the arc name from above.
2. **Job** — one sentence on what this slide does that the others don't.
3. **Visual mode** — pick from:
   - Bold typography card
   - Single-number data viz
   - Diagram / org chart
   - Quote card (named source, dated)
   - Split-frame comparison
   - Framework / matrix
4. **Headline** — max 8 words. Will be rendered at ~48px minimum on 1080px-wide
   canvas.
5. **Body / content** — the text, data, or diagram description that fills the
   slide. Spell out exact text — do not say "include the relevant stat" without
   naming the stat.
6. **Palette** — dark background + white text + ONE accent color. Accent by topic:
   - Tech / AI / agents → blue (#1E40AF or similar saturated cobalt)
   - Data / infrastructure → green (#059669 or similar deep emerald)
   - Business / GTM / hiring → amber (#D97706 or similar burnt orange)
   - Contrarian / security / risk → red (#DC2626 or similar)
   - Documentarian / synthesis → off-white on dark slate, no accent (signals
     editorial mode)
7. **Source attribution** — small text, bottom corner. Format: "Source: [name],
   [year]." Required if any data point or quote appears on the slide.
8. **Alt text** — one sentence describing what the slide *shows*, not how it
   *looks*. This is the accessibility artifact and the LLM-readable version of
   the slide for posts that get scraped by agents.
9. **Tool routing** (updated 2026-08-07 — Claude design default):
   - **Any slide whose meaning depends on text labels** (boxes + arrows, before/after,
     "where the value moves," stack/layer diagrams, matrices, stat cards, timelines) —
     **author as Claude HTML/SVG** (real text + inline `rect`/`line`/`path`, published
     via the Artifact tool). The label is real text, never generated pixels — which is
     why this beats both Canva shape-layouts and any raster tool. This is the default
     for essentially every content-pipeline slide.
   - **Gemini** — photographic, illustrative, or *textless* conceptual imagery only
     (no embedded labels to misspell). Claude writes the prompt.
   - **Avoid** — any generated/raster image for a slide whose meaning depends on text
     labels (labels come out garbled / duplicated / misspelled — observed live on the
     AI Demo Night "moat moves" visual, 2026-05-26). Gamma removed; Canva vestigial.

---

## Execution — Claude design (default) + Gemini (pictorial)

**Default = Claude design (HTML/SVG via the Artifact tool).** Author the carousel/single
as one self-contained HTML file — a `.slide` frame per slide at 4:5 (1080×1350), dark
editorial ground, one meaning-bearing accent, real typographic hierarchy, and
hand-authored inline SVG for diagrams / arrows / timelines. Load `artifact-design`
(+ `artifact-diagramming`, `dataviz`) first. Publish via the Artifact tool → Alex
exports with ⌘P → Save as PDF (each slide prints as one 4:5 page → LinkedIn carousel)
or screenshots frames for PNGs. Iterate in-conversation: edit the file, republish to the
same URL. No app re-interprets the content — the labels render exactly as written.

**Pictorial imagery = Gemini** (Alex's subscription). Claude writes an architectural
prompt (composition + style + mood + negatives — see the style guide's AI Image
Prompting rules); Alex generates and reviews. Use only for conceptual / editorial /
photographic imagery with no dense labels.

> ⛔ **DEPRECATED 2026-08-07 — Gamma removed, Canva vestigial.** The Gamma/Canva MCP
> mechanics below are retained only as historical reference (how the pre-2026-08
> pipeline worked). **Do not use them** — the live path is Claude design + Gemini above.
> Flagged for deletion in a follow-up cleanup.

### Canva fallback — auto-render (added 2026-05-24, demoted to fallback 2026-05-26)

After the slide specs are finalized, the calling skill auto-renders the
carousel by firing one `mcp__claude_ai_Canva__generate-design` call per slide.
This replaces the historical "Alex pastes the brief into Canva manually"
handoff. Per CLAUDE.md's MCP automation rule, manual is reserved for
judgment-load steps; rendering is not one of them.

### Per-slide MCP call shape

For each slide in the brief, construct a `generate-design` call:

```
mcp__claude_ai_Canva__generate-design({
  design_type: "instagram_post",   // STEP 1 ONLY: Canva's single 4:5 (1080×1350) social canvas — NOT a LinkedIn asset yet; resize in Step 2
  query: "<prose payload built from the slide spec — see template below>",
  user_intent: "Generate slide N of M for [post title] — [slide job]"
})
```

⚠️ **Canva `generate-design` has NO `linkedin_post` type** — the enum only offers
`instagram_post`, `facebook_post`, `twitter_post`, `your_story`, `presentation`,
etc. We use `instagram_post` ONLY because it is Canva's single 4:5 portrait social
canvas (1080×1350), which equals LinkedIn's optimal portrait ratio. But it is NOT a
LinkedIn asset on generation: it lands titled "Instagram Post" and can inherit
Instagram design conventions. So generation is a **two-step pattern** — generate the
4:5 canvas (above), then resize to LinkedIn spec (below). Do NOT use `presentation`
(16:9) or `pinterest_pin` (2:3) — wrong ratios. (Recurring defect — visuals shipping
as Instagram posts — fixed 2026-05-26.)

**Step 2 — resize the chosen candidate to LinkedIn spec (MANDATORY; this also re-types it off "Instagram Post"):**

```
mcp__claude_ai_Canva__resize-design({
  design_id: "<created design id>",
  design_type: { type: "custom", width: 1080, height: 1350 },   // LinkedIn 4:5; use 2160×2700 for retina
  user_intent: "Resize to LinkedIn-optimized 4:5 portrait — not an Instagram post"
})
```

**LinkedIn output spec (the target — not Instagram):**
- **Single image (feed):** 1080×1350 (4:5) — the tallest LinkedIn renders in-feed before cropping. Retina: 2160×2700.
- **Carousel:** a LinkedIn carousel is ONE multi-page **PDF** ("document" post) — NOT N separate images (that's the Instagram pattern). After the slide winners are chosen and resized, `merge-designs` them into one multi-page design, then `export-design` as PDF for the LinkedIn document upload.
- Never ship a deliverable as a bare `instagram_post`-typed design.

### Query payload template

The `query` parameter is the prose payload Canva's generation model consumes.
Build it from the slide spec using this template — every field from the slide
spec maps to a labeled section in the query:

```
Generate a typography-led LinkedIn carousel slide (slide N of M).

LAYOUT: [Visual mode from spec — Bold typography card / Quote card / Diagram / etc.]
[For quote cards: emphasize frame parallelism with sibling slides.]

[CONTENT BLOCKS — pull verbatim from spec]
[Headline]: "[exact text]" — [type weight/size guidance]
[Body / content]: [exact text or diagram description]
[Attribution block]: [name / company / category if quote card]
[Footer attribution]: [if any — source + date]

VISUAL STYLE:
- Background: [palette spec — hex code]
- Primary text: [palette spec — hex code]
- Accent: [palette spec — hex code, with usage notes]
- Typography-led. NO imagery, NO stock-AI illustrations, NO gradients, NO decorative iconography[, NO speaker photos].
- High contrast, premium editorial feel.

ASPECT RATIO: 4:5 portrait (1080x1350px).

CONTEXT: [One paragraph — what the carousel is arguing, what role this slide
plays in the arc, who the author is. Pulled from the carousel thesis + slide job.]

CONSTRAINTS — anti-patterns to avoid:
- No glowing brain illustrations
- No robot imagery
- No portraits or photos of speakers
- No pink/purple gradients
- No decorative lightbulbs, gears, or arrows
- No "Follow for more" footer language
- [Add any slide-specific anti-patterns]
```

### Frame parallelism enforcement

For Arc 2 (Thesis A vs B) and Arc 3 (Before vs After), structurally paired
slides MUST share visual frame. To enforce in MCP calls, include this explicit
instruction in the `query` for paired slides:

> "LAYOUT: Quote card. Must use IDENTICAL layout to slide N of this same
> carousel — same quote placement, same attribution layout, same font hierarchy.
> Frame parallelism is critical."

Same applies to Arc 4 (One Question, N Perspectives): slides 2 through N-1
share frame; slide 1 (question) and slide N (synthesis) are distinct typography
slides matching each other.

### Candidate selection flow

`generate-design` returns 4 candidates per slide. The calling skill surfaces
all candidates as a markdown table (slide number, candidate letter, preview
URL, thumbnail URL) and waits for Alex's selection. Once selected, fire
`mcp__claude_ai_Canva__create-design-from-candidate` to land the winners in
Alex's Canva account. Then immediately `resize-design` each winner to LinkedIn
spec (Step 2 above) — do not leave them as Instagram-typed designs. For
multi-slide carousels, `merge-designs` the resized winners into one multi-page
design and `export-design` as PDF for the LinkedIn document post.

If Alex flags any candidate as "close but needs X," use
`mcp__claude_ai_Canva__perform-editing-operations` to iterate without
leaving the conversation. Do not re-fire `generate-design` for tweaks — that
discards visual DNA from the chosen direction.

### Failure modes

- **All 4 candidates fail the brief.** Re-prompt with sharper anti-pattern
  language or pull in a brand kit via `mcp__claude_ai_Canva__list-brand-kits`
  → `brand_kit_id` parameter. If still failing, fall back to manual Canva
  work for that specific slide and log the failure mode in
  `.claude/notes/execution-week-frictions.md` so the pattern can be diagnosed.
- **Frame parallelism broken between slides.** Re-fire the off-pattern slides
  with a stronger "IDENTICAL layout to slide N" instruction. Do not ship a
  carousel where slides 2-N-1 visually drift from each other.
- **MCP returns "Common queries will not be generated" error.** The query
  was too generic. Add slide-specific detail — exact quote text, named
  speaker, specific palette hex codes, the full carousel thesis context.

### Tokens / cost

Per CLAUDE.md MCP automation rule #1: Canva MCP calls are billed by Canva
(under Alex's existing subscription), not by Anthropic. The Claude-side
token cost is the small JSON request/response per call. A 5-slide carousel
= 5 `generate-design` calls + 1-5 `create-design-from-candidate` calls + 0-N
`perform-editing-operations` calls. All effectively free at the Anthropic
billing layer.

---

## Quality gates

Run these against every carousel brief before shipping it into Notion:

- **Arc fit** — does the chosen arc match the post's argumentative structure?
  If you used Arc 1 (Hook → Evidence → Mechanism → CTA) for a two-thesis
  synthesis post, the arc is wrong. Pick again.
- **Job differentiation** — can each slide's "job" sentence be swapped with
  another slide's? If yes, two slides are doing the same thing. Cut one.
- **Frame parallelism** — for Arc 2 (Thesis A vs B) and Arc 3 (Before vs After),
  the structurally paired slides must share visual frame. Different frames hide
  the comparison.
- **Thumb test per slide** — on a 375px iPhone SE viewport, is the headline
  readable in 2 seconds without zooming? If not, the headline is too long or
  the font is too small.
- **Source citations** — any slide with a number or a named quote must have a
  source line. Carousels without sources read as opinion, not reporting.
- **Slide count integrity** — is each slide load-bearing? If you could ship the
  carousel without slide 3 and lose nothing, slide 3 is decoration. Cut it.
- **Adds information (not repetition)** — does each slide carry something the
  post text doesn't already say? A slide that re-prints a quote or line from the
  post fails. Visuals add structure, comparison, progression, or a diagram —
  never a re-typeset of the copy. (Added 2026-05-26.)
- **Final slide earns the swipe** — the final slide is what the reader is left
  with. A weak final slide ("Follow for more") tells the reader the carousel
  was filler. The final slide should be the question, the take, or the
  synthesis — never housekeeping.

---

## Anti-patterns

The following kill carousels and should be flagged in any brief that drifts
toward them:

- **Five versions of the same image.** A carousel is not a redundancy mechanism.
  Each slide must take a different perspective on the same thesis.
- **Recap-of-the-post slides.** "Here's what we covered." The carousel IS the
  coverage. Recap slides signal the carousel doesn't trust the rest of itself.
- **Quote-card carousels that re-print the post body.** If the slides just
  typeset quotes or lines already written in the post, the carousel adds nothing
  — it's text-forward repetition, not visual content. A visual earns its place
  only by adding a structure, comparison, progression, architecture, or
  "where-the-value-moves" view the copy doesn't carry. (Added 2026-05-26, AI Demo
  Night post review.)
- **Generic AI hero shots.** A glowing brain, a robot at a desk, a city skyline
  with overlay text. Stock-AI imagery is the visual equivalent of consultant-ese.
- **Photographic people on individual slides.** Generated faces or photographic
  portraits introduce uncanny-valley risk and consume attention away from the
  argument. Use quote cards with names typed, not faces.
- **Decorative iconography.** Lightbulbs, gears, arrows pointing nowhere. If an
  icon isn't load-bearing in the diagram, remove it.
- **Color-by-vibe.** Pink and purple gradients because they look "AI-ish."
  Accent color is determined by topic per the palette rules above — never by
  mood.
- **"Follow for more" final slides.** The final slide is the synthesis or the
  question. The follow-me ask undermines the documentarian voice.
- **Inconsistent type hierarchy.** Body text smaller than caption text, headline
  competing with multiple sub-headlines. One headline per slide, one body block,
  one annotation max.
- **Stat-without-context slides.** "242%" alone is a number, not an argument.
  Every data point needs the question it answers.

---

## Voice propagation rule

When `update-voice-and-style.md` runs, it propagates to this file too. Visual
voice is part of voice — the typography choices, the color rules, the
anti-patterns listed above all carry editorial weight. If Alex's written voice
evolves (e.g., he leans further into contrarian framing), the visual brief
defaults evolve with it (e.g., red accent becomes more common, quote cards lead
more often).

Edits to this file should be made under one of:

- **Style evolution** — when the visual voice itself changes (new palette, new
  arc, new anti-pattern).
- **Tool capability shift** — when a generation tool's text-rendering quality
  changes the routing logic (e.g., Imagen 5 ships and can do dense org charts
  better than GPT-Image-1).
- **Quality gate failure pattern** — when multiple carousels fail the same gate,
  add it explicitly so the gate becomes preventive.

Do not edit this file to fix a single post's visual problem. Fix the post; only
edit here when the pattern is repeating.

---

## Output schema (copy into the Notion Content Draft page body)

Use this exact structure. Skills that write to Notion should produce this block
verbatim and append it under the LinkedIn post copy with a `## Visual Brief —
N-slide carousel` H2.

```
## Visual Brief — N-slide carousel (Arc: [arc name])

**Carousel thesis:** [one-sentence restatement of the post's thesis, framed
visually — what the reader should walk away with after swiping through.]

**Slide count:** N
**Aspect ratio:** 4:5 (1080x1350) — LinkedIn carousel default
**Tool routing summary:** [nearly always "all slides → Claude design (HTML/SVG)"; note any slide that is textless pictorial → Gemini]

---

### Slide 1 of N — [Job]

- **Visual mode:** [bold typography / data viz / diagram / quote card / etc.]
- **Headline:** [max 8 words]
- **Body / content:** [exact text or diagram description]
- **Palette:** dark bg + white text + [accent color, with hex]
- **Source attribution:** [if any data point or quote — exact source line]
- **Alt text:** [one sentence describing what the slide shows]
- **Tool:** [Claude design (HTML/SVG) — default; Gemini only for textless pictorial]

### Slide 2 of N — [Job]

[same structure]

[... continue for all N slides ...]

---

**Quality gate checks:**
- Arc fit: [pass / flag — why]
- Job differentiation: [pass / flag]
- Frame parallelism (if Arc 2 or 3): [pass / flag / n/a]
- Thumb test per slide: [pass / flag — which slide]
- Source citations: [pass / flag]
- Final slide earns the swipe: [pass / flag]
```

---

## Reference

- `.claude/skills/content-patterns/two-thesis-synthesis.md` — pattern for the
  two-thesis text post that Arc 2 visually mirrors.
- `.claude/references/content-style-guide.md` — written voice rules; visual
  voice rules above must remain consistent with the style guide's tone.
- `.claude/references/content-anti-patterns.md` — language anti-patterns;
  visual anti-patterns above are the parallel set.
- CLAUDE.md — Notion Content Drafts schema, Notion property gotchas (multi-select
  JSON-array-string, relations as full page URLs, etc.).
