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

**Every LinkedIn post ships with one accompanying carousel brief of 3-5 slides.**
DMs and prepared questions do not get carousels — they are private artifacts.

The carousel brief is embedded in the LinkedIn post's Notion page body under a
`## Visual Brief — N-slide carousel` H2 heading, immediately after the post copy.
The brief is what Alex pastes into ChatGPT (GPT-Image-1), Gemini Imagen 4,
Magic Patterns, or Canva to generate the actual slides.

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
9. **Tool routing** — which tool the slide is best generated in:
   - **GPT-Image-1 or Gemini Imagen 4** — clean diagrams with accurate text labels
   - **Magic Patterns** — branded marks, dashboards, designed components
   - **Canva** — bold typography cards, quote cards, simple data viz
   - **Avoid** — Stable Diffusion variants for any slide with dense text labels

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
**Tool routing summary:** [which slides go to which tool; e.g., "Slides 1, 4 → Canva typography; Slides 2-3 → GPT-Image-1 diagram"]

---

### Slide 1 of N — [Job]

- **Visual mode:** [bold typography / data viz / diagram / quote card / etc.]
- **Headline:** [max 8 words]
- **Body / content:** [exact text or diagram description]
- **Palette:** dark bg + white text + [accent color, with hex]
- **Source attribution:** [if any data point or quote — exact source line]
- **Alt text:** [one sentence describing what the slide shows]
- **Tool:** [Canva / GPT-Image-1 / Imagen 4 / Magic Patterns]

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
