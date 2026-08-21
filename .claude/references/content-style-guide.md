# Content Style Guide

> This is a living document. Updated via the `update-voice-and-style` skill as Alex's
> content voice develops through iteration and feedback.

---

## Voice & Tone

Five tone pillars — use all five together. They reinforce each other:

1. **Curious, not performative** — Genuine interest drives the content. Never post to be seen posting.
2. **Commercially aware, not salesy** — Understand the business context. Never pitch.
3. **Informed, not lecturing** — Share what you've learned. Never explain down.
4. **Opinionated but open to being wrong** — Take a position. Invite correction.
5. **Documentarian, not influencer** — Capture what happened, what it means, and why it matters. **Always lead with the audience and the subject** — and bring yourself in wherever it *adds value*: your analysis, your perspective, or a unique point of view derived from what you've learned, built, or experienced — through events, interactions, or the **intersections where they converge**. The rule isn't "never about you"; it's **never about you at the audience's expense.** Self in service, not performance. *(This is the counterweight — see the Audience-First North-Star section below.)*

**Predictions vs. stances (added 2026-05-26):** Soften *predictions about event content* — frame what you expect an event to be about as curiosity or hypothesis ("I was curious going in," "I expected," "the question I brought in"), never a cocky "I predicted." But never soften *stances on subjects, topics, or analysis* — take the bold, contrarian, or definitive position on the substance. The hedge is only for guesses about what an event will contain, used as a narrative starting point.

**Stance-license: a viewpoint must be earned with space, presence, and expertise (added 2026-05-30 — refines the rule above; the most important voice rule we have).** The "take the bold stance on substance" rule above still holds — but ONLY where the format gives you room to EARN the stance with context and analysis. **A viewpoint without the space to provide the context and analysis that justifies it is not a stance — it's a hot take, and a hot take in a synopsis (no context, no analysis, no viewpoint earned) adds zero value.** It reads as either social-media slop or unearned posturing. Three factors set how much stance-license a piece has:

- **Space / format** — long-form (post-event recap, deep per-event post) has room for context + analysis → high license. A roundup synopsis (the tightest character budget of any format) has none → **set the table, don't take a side.**
- **Presence** — pre-event (haven't seen it yet) → low license; surface the field's open questions. Post-event (you were in the room) → high license; deliver your earned read.
- **Expertise** — calibrate to where Alex actually is: an informed, curious documentarian, *not yet a topic expert*. Definitive verdicts from that position read as unearned. Stance-license **grows over time** as Alex builds, reads, and attends more — and the `steering-interview` skill is how that growing perspective gets captured per event.

**Default stance-license by format:**
| Format | License | What to do |
|---|---|---|
| The Upcoming Week roundup | Lowest | Set the table. State each topic's current state + the genuine tension that *already exists in the field*, attributed to the field — never Alex's verdict. No sides. |
| Per-event pre-event post | Low–medium | One genuine question or observation, lightly held. Open the tension; don't resolve it. |
| Post-event recap / synthesis | Highest | Earned POV — you were there, you have the room. Take the position, with the context and analysis to back it. |

**The test before shipping any viewpoint:** *can this same piece also carry the context and analysis that earns it?* If the format has no room for that, cut the viewpoint and surface the tension neutrally instead.

**Decenter the self — curator, not protagonist (added 2026-05-30).** The subject of a post is the events, topics, and tensions — **not Alex.** First-person "I/me" that centers Alex ("seven rooms on *my* calendar," "here's what *I'm* walking into") reads as a thinly-veiled personal brag and undercuts the documentarian frame (pillar 5). Lead with the field and the abundance; position Alex as the curator pointing at what's worth watching. The "I" that survives is the curator's, not the brand-builder's. Model: *"Hundreds of events for NYC Tech Week — the seven worth watching are…"* (subject = the events; the "I" is incidental). When you catch an "I/me" that centers Alex rather than the content, cut or recast it.

## Audience-First North-Star (why · who · the counterweight)

**Why the content exists — democratize access.** Bring NYC AI/tech's rooms, people, and ideas to those locked out by geography, schedule, approval gates, or life circumstance. **The audience is served first.** Full canonical spec: `.claude/references/audience-north-star.md` — every content skill imports it as its top-level ethos.

**Persona — embedded expert correspondent.** In the room (**witness**) → generous (**audience-first**) → analytically authoritative (connects what's said to prior coverage, Alex's own work, and current news; points to where to go deeper).

**The counterweight to every decenter-self rule — audience-first is an *ordering*, NOT an *erasure*.** The decenter-self, stance-license, and never-lead-with-"I" rules mean *the audience comes before Alex* — they do **not** mean *erase Alex*. He is present, named, and opinionated wherever his presence, access, judgment, or insight **is** the value. **Attribution follows value: when the call is his and it's right, he claims it plainly, with conviction.** Humble in *priority* (audience first), never in *false modesty* about what he knows. **"Self in service, not self in subtraction"** — a post can be heavily Alex and still be audience-first, as long as it serves the reader rather than performs for them.

**The three floors (non-negotiable, every post):**
1. **Receipts** — ≥1 detail only possible from physically being there (a fragment of real dialogue, a room reaction, a slide that wasn't online). Architectural, not a brag. *A post that could have been written from a recap fails this floor.*
2. **Hiring-Manager Activation** — one variant per post carries an explicit commercial-judgment angle. The search is active now; this is an output, not a hope.
3. **Anti-Goodhart** — "resonance" is defined before it's measured and is NOT default LinkedIn engagement. Target signal: someone outside the room used something specific Alex surfaced.

## Post Architecture

Default structure for LinkedIn posts (adapted from Hook-Context-Insight-CTA):

```
HOOK — First 1-2 lines. Stop the scroll. A surprising stat, a contrarian take,
       or a specific detail that signals "this person was actually paying attention."

CONTEXT — Why this matters right now. Connect the event/topic to a broader trend,
          a recent development, or a shift the audience should care about.

INSIGHT — One deeply considered observation or one genuinely novel question.
          Not the obvious takeaway. The thing that would make an expert pause.
          This is the core value of every post.

CTA (varies by content type) — See Content Type CTAs below.
```

**Opener rule — never lead with "I" (added 2026-08-07 — the strongest first-line rule we have).** An event post's first line must lead with the *subject*, never Alex. Pick one of five leads: the **topic / core tension**; a **relevant recent headline or stat** (often the strongest hook — e.g., "This stat should make you rethink AI agents: [stat]…"); the **host company** *in service of the event* (never a bare "Company just…" product-ad construction — see the company/product-name row in `content-anti-patterns.md`); the **people** (host/speaker) who make the room worth showing up for; or the **NYC AI ecosystem** framing ("The NYC AI ecosystem is playing host to another … tonight"). **Banned openers:** "Tonight I'm at…", "I wrote…", "One stat reframed how *I* think…" — they center Alex and waste the hook. The curator's "I" may appear *later*, once the subject is established. This is the first-line enforcement of the decenter-self rule.

## Content Type CTAs

| Content Type | CTA Approach |
|---|---|
| The Upcoming Week | "If you can't make it or aren't in the NYC area but have a question you wish you could ask — connect, message me and I'll ask it. If you're going, happy to connect before, don't hesitate to say and I'll see you there." |
| Pre-Event Post | Educational reminder + "If you're deep into this subject, what are you most looking forward to learning/hearing about?" |
| Post-Event Recap | No CTA. Pure documentarian. Let the content speak. |

**The close is the self-trap.** The ending is where self-credentialing and self-flagellation sneak back in even when the body is clean. Do NOT end on a verdict you'll deliver ("what I'll be testing," "the real version not the demo") or a credential ("I've been doing this since X"). End on the open questions, defer to the experts about to answer them, and offer to share where **they** land. **Curiosity + deference + service — never verdict + credential.**

## Data Points

- Pull in **at least 2, no more than 3** specific stats/facts/data points per post
- Source them from the research brief
- Provide source references so Alex can share deeper resources if desired

## Formatting

- **Hashtags:** 2-5 per post, relevant and specific (e.g., #AgenticAI, #DataReadiness, not just #AI)
- **Tagging:** Never tag people or companies — doesn't translate across platforms. Alex formats manually.
- **Emoji:** Sparingly but present. Use as structural markers or emphasis, not decoration.
- **Length by type (character counts include spaces, line breaks, and emojis — LinkedIn counts everything):**
  - The Upcoming Week: Long-form roundup — target 1,300–2,200 chars, **hard cap 3,000**
  - Pre-Event Post: Mid-form (8-15 lines) — target 900–1,500 chars, **hard cap 3,000**
  - Post-Event Recap: Long-form narrative — target 1,500–2,200 chars, **hard cap 3,000**

## LinkedIn Character Budget (hard limit — added 2026-06-10)

**The LinkedIn feed-post hard cap is 3,000 characters** (stable since June 2023; verified June 2026). The count includes letters, numbers, punctuation, spaces, line breaks, and emojis — *everything*. A post over 3,000 chars cannot be published as-is; LinkedIn truncates it. **Generate every LinkedIn post WITHIN this budget from the start — never hand Alex a 4,000–5,000-char draft he then has to cut down.** This rule exists specifically to kill the recurring tax of hand-trimming thousands of characters per post before it can ship.

- **Hard cap: 3,000 characters. Non-negotiable.** Count the post before presenting it. If a draft exceeds 3,000, cut it to budget *before* showing Alex — do not ship an over-limit draft with a "trim this" note.
- **Engagement sweet spot: 1,300–1,900 characters.** Default target for most posts. Long-form recaps may run to ~2,200 but should rarely approach the cap.
- **The "…see more" fold: ~140 chars on mobile, ~210 on desktop.** The hook and the reason to expand must land before the fold — front-load the scroll-stopper in the first ~140 characters.
- **Sources/resources do NOT go inline in the post body.** A trailing sources/citations block is the most common thing that pushes a post over the cap. Put source links in the **first comment** (preferred) or carry them on the **carousel** — never let them blow the post budget. (This was a real cut Alex had to make by hand — design it out.)
- **When over budget, cut in this order:** the inline sources/resources block → repeated data points (keep 2–3 max) → throat-clearing preamble → any line the carousel already carries visually → adjective trimming.
- **State the count on hand-off.** When presenting any LinkedIn post for review, show its character count (e.g. "1,420 / 3,000") so Alex sees at a glance it's ship-ready.

## The Learn-More Set (mandatory — every post)

**3–5 "learn more" resources every post.** Every post ships with a curated set of **3–5 resources** — the key paper, the company's own announcement, a speaker's talk or writing, the publication/newsletter on the topic — spanning the post's topics, tech, companies, and people. This is the persona's *"points to where to go deeper"* and the mission's *"democratize access"* made concrete: the post delivers the translated insight; the set hands the curious reader the door to go further.

- **Placement: first comment (preferred) or the carousel — NEVER crammed into the post body.** Inline sources are the #1 thing that blows the char cap and dilute the post; keeping them out preserves the post's value while adding value for the subset who want more.
- **Especially valuable when a post runs short** — a tight post + a rich learn-more set delivers full value without padding the body.
- **Reach mechanic:** name the people and publications (per the name-people ethos); Alex can @-mention sources manually where it may pull their engagement/reach (tagging doesn't auto-translate across platforms — he formats by hand).
- **Real and verified only** — every resource is a genuine, checkable source (no fabricated links/titles); firm/person thesis claims obey CLAUDE.md rule #12 (primary-source citation before public use).

## DM Structure

Default structure for LinkedIn DMs (adapted from AIDA — Attention, Interest, Desire, Action):

```
OPENER — Specific reference to the event + their specific talk topic or role.
         Never generic. Never "love your work!"

BRIDGE — Connect their work/talk/POV to a specific insight from the research brief.
         This is what makes the DM feel like it came from someone who did the work.

QUESTION — 1 thoughtful question at the intersection of themselves, their role/company,
           and the event topic or their specific talk. This question should be good enough
           to use as a prepared question at the event if the DM doesn't lead to a conversation.

CLOSE — Light. No hard ask. Door-opening, not door-forcing.
        "Looking forward to the talk" or "Happy to connect if you're open to it."
```

- **Length:** 4-6 sentences
- **Always** reference the specific event topic or their talk topic
- **Personalization target:** Level 3 — connect their specific work to a specific insight from the research brief (not generic company mention, not generic role mention)
- **2-3 DMs per person per topic** — the best one becomes outreach, the rest become prepared questions

## Quality Bar

The single most important test for every piece of content:

> **Does this contain one genuinely insightful observation or one deeply thoughtful question
> that would make an expert pause, appreciate the thought behind it, and want to engage?**

If not, it's not ready. Succinct, not trying to do too much, but nailing the one thing.

**The Substance / Insight Floor.** Every post must hand a non-attendee real informational value — the field's current state, what's *materially changing*, the live tension, the numbers — **translated from the research, not left in the brief.** A hook + a couple of name-drops + a question is a failure, not a post. The rich topic/signal research IS the gift; mine the top 3–5 insights and hand them over. **Denser with value, not shorter** — audience-first ≠ light. *Reconciled with the character budget:* the post stays within the 3,000-char cap (sweet spot 1,300–1,900); density comes from translating the single, robust deep-research brief into the body, not from exceeding the cap. Depth the post can't hold is served by the internal brief + the Learn-More Set (below), not by a separate published long-form tier.

## "So What?" Self-Critique

Before presenting any draft, run this internal test:

> "If I'm a [hiring manager at an AI company / enterprise GTM peer / event speaker],
> would I stop scrolling for this? Does this tell me something I didn't already know
> or ask me something I haven't already considered?"

If the answer is no, rework the insight before presenting.

---

## Audience (ranked by priority)

1. **Hiring managers / recruiters at AI-native companies** — Job search signal. The content demonstrates commercial + technical range.
2. **Peers in enterprise sales / GTM** — Professional community. Shared context on AI's impact on their work.
3. **Event speakers / hosts** — Relationship building. The content shows you did the work before reaching out.

## Positioning

- **Full stack GTM** is the thesis but it is NOT explicit in content. It's implicit — demonstrated by the range of topics, commercial instinct, and content production quality.
- Lead with event-focused content as subject matter. The building, managing, iterating, and executing of projects develops the skills quietly. Content about learnings from building comes later.
- **Documentarian identity:**
  - Reporter: "I go to things and share what happened" — specific details
  - Student: "I go to things and share what I learned" — synthesis
  - Analyst: "I go to things and share what it means" — interpretation
  - Use all three. A specific detail to highlight each angle per event.

---

## Visual Content

Most LinkedIn posts ship with a supporting visual — but not all (rule softened 2026-05-27).
A text-only post is a valid, intentional variety choice for a simple informative summary;
the default is a visual on most posts, not a hard requirement on every one. When a visual is
dropped, it's a deliberate call — note it, don't treat it as an oversight.

**Visuals must add, never repeat (added 2026-05-26):** A visual earns its place only by adding information the post text doesn't carry — a structure, comparison, progression, architecture, or "where-the-value-moves" view. Re-printing quotes or lines already in the post (e.g., a quote-card carousel of lines you already wrote) is text-forward repetition, not visual content. Canonical carousel rules: `.claude/skills/content-patterns/visual-briefs.md`.

### Visual Output Per Post: 3 Briefs
1. **Directly Supportive (Data/Stat)** — Clean visual reinforcing the post's key data point
2. **Directly Supportive (Conceptual/Framework)** — Diagram, map, or framework visual
3. **Wild Card 🌶️** — Professional but spicier. Different aesthetic, unexpected format, edge.

### Format & Sizing (LinkedIn-Optimized)

LinkedIn's mobile feed crops to fit. **4:5 portrait is the default** — it takes
~20% more vertical screen space than 1:1 and ~65% more than 16:9, which directly
increases dwell time.

| Format | Dimensions | When to Use |
|---|---|---|
| Single image (default) | 1080x1350 (4:5) | Most pre-event and post-event visuals |
| Single image (acceptable) | 1200x1200 (1:1) | Only when 4:5 crops the content badly |
| Carousel / PDF slides | 1080x1350 (4:5) — consistent across all slides | Multi-step narratives |
| Retina export | Create at 2160x2700, export at 1080x1350 | Always — no exceptions |

- File format: **PNG** for graphics with text, **JPG** for photos, **PDF** for carousels
- Max file size: 10MB per image, 100MB per PDF carousel

### The 2-Second Thumb Test (Non-Negotiable Quality Gate)

If the core message isn't readable in 2 seconds while scrolling on a phone, the visual fails.
This is the visual equivalent of the post's hook.

- **Max 8 words** in the primary headline on any image
- **Min font size: 48px at 1080px wide** (~4.5% of image width)
- **Contrast: light-on-dark OR dark-on-light. Never medium-on-medium.**
- **No paragraph text on images.** That's what the post body is for.
- Test at 375px wide (iPhone SE viewport) before shipping — if you squint, it's too small

### One Visual = One Idea

Each image communicates exactly one concept. If the post caption has to explain
the image, the image isn't working. If the image tries to show three things, none land.

- Data visual → one stat or one comparison
- Framework visual → one diagram or one process
- Quote card → one quote, attributed
- Carousels tell multi-step stories, but each slide still gets one idea

### Data Visual Principles

When visualizing a stat, **extract the insight** — don't recreate the full chart.
The audience is scrolling, not analyzing.

- Lead with the number: "23% improvement" at 72px bold, context smaller beneath
- Comparison format: before/after, side-by-side, or progress bar — not raw charts
- Kill chart junk: no gridlines, no 3D, no legends requiring cross-reference
- **One accent color** for the data point you want seen. Gray for everything else.
- Source attribution: small text, bottom corner — "Source: [name], 2026"

### Carousel Architecture

Carousels (uploaded as LinkedIn PDFs) get ~1.5-2x the engagement of single images
because each swipe counts as interaction. They need structure to pay off.

- **Slide 1 (Hook):** Bold headline + visual hook. This is the thumbnail — treat like a book cover.
- **Slides 2-N (Content):** One idea per slide, consistent layout, progressive narrative.
- **Final slide (CTA):** "Follow for more" or a specific question that drives comments.
- **Sweet spot:** 5-8 slides. Under 5 feels thin. Over 10 loses people.
- **Page numbers:** Bottom corner, small — signals "there's more to swipe."

### Color Strategy

Until a locked brand kit exists (Minimal V1 still applies), use a **constrained
palette per content type**, not per post. Visual recognition compounds over time.

- Safest high-impact formula: **Dark background + white text + one accent color**
- Accent by topic area:
  - Tech / AI → blue
  - Data / infrastructure → green
  - Business / GTM → amber
  - Contrarian / hot take → red
- **Never more than 3 colors** in a single visual (background + text + accent)
- Avoid: red-green pairings (colorblind-hostile), pure white backgrounds (mobile glare), neon-on-neon

### No Stock Photo Energy — Ever

"Stock photo energy" means generic, interchangeable, could-be-any-company. The
visual must be specific to *this* content.

- ✓ Good: A designed stat card with the actual number from the research brief
- ✓ Good: A diagram mapping the actual framework the post discusses
- ✓ Good: An AI-generated image prompted from a specific concept in the post
- ✗ Bad: Stock photo of people shaking hands, laptops on desks, abstract geometric patterns
- ✗ Bad: A Canva template where only the text changed — if the layout looks familiar, it's a template

### AI Image Generation: Be Architectural, Not Aspirational

When prompting Gemini (Imagen 3) for custom visuals, treat the prompt like a
creative brief, not a wish. Prompt quality directly determines output quality.

- **Specify composition:** "centered, symmetrical, negative space on left for text overlay"
- **Specify style explicitly:** "flat vector illustration" / "editorial magazine photography" / "technical diagram style" — **never** "professional looking"
- **Specify negatives:** "no text, no watermarks, no people, no generic tech imagery"
- **Specify mood:** "authoritative and clean" vs. "bold and provocative" vs. "minimal and sophisticated"
- **Iterate in 3 rounds:** prompt → evaluate → refine → evaluate → final. First output is a draft, not the deliverable.

### Accessibility (Non-Negotiable)

8% of men are colorblind. 15% of the global population has a disability. Alex's
audience is hiring managers, executives, and peers — these aren't stretch goals.

- **Alt text on every image** — LinkedIn supports it. Describe what the visual *shows*, not what it *looks like*.
- **Never rely on color alone** to convey meaning — pair color with labels, patterns, or icons.
- **Contrast ratio 4.5:1 minimum** for text on background (verify with WebAIM contrast checker)
- **No flashing or rapid animation** in GIFs
- **If it's a data visual, include the data in the post text too** — the image complements, never replaces

### Format Selection by Content Type

Match format to content, not vice versa. Don't make a carousel when a single image is sharper.

| Content Moment | Best Format | Why |
|---|---|---|
| One killer stat | Single image, 4:5 portrait | Hero number + context. Clean, shareable. |
| Process or framework | Carousel (5-8 slides) | Each step gets a slide. Swipe = narrative momentum. |
| Hot take / contrarian insight | Bold typography card | Text IS the visual. Big font, dark bg, one sentence. |
| Event recap with multiple moments | Carousel with photos | Documentarian angle. Each slide = one moment. |
| Comparison (before/after, X vs Y) | Single image, split layout | Side-by-side at a glance. |
| Conceptual or abstract idea | AI-generated custom image | Gemini/Imagen for what doesn't exist as a photo. |
| Multi-event weekly preview | Carousel (1 slide per event) | Each event gets its own visual treatment. |

### Tool Selection for Visuals (updated 2026-08-07 — Gamma removed)

Two lanes, and **neither is a constrained app that re-interprets your content** — the failure mode that garbled dense labels in Gamma and Canva.

| Need | Tool |
|---|---|
| Diagrams, matrices, stat cards, timelines, carousels — any label-dense / structured visual | **Claude design** — self-contained HTML/SVG via the Artifact tool → export 4:5 PDF/PNG. **DEFAULT.** Pixel-exact; renders exactly what's authored, no re-flow. |
| Conceptual / editorial / illustrative / photographic imagery | **Gemini** (Alex's subscription — frontier flexibility, no app harness). Claude writes the prompt; Alex generates. |
| Presentation-style video | Google Vids |

**Removed 2026-08-07:** Gamma (the app re-interpreted content and broke dense labels — the exact thing it was chosen to fix over Canva, now solved better by Claude authoring the pixels directly). **Canva is vestigial** — Claude + Gemini cover both the structured and pictorial lanes. See CLAUDE.md rule #13 + `content-patterns/visual-briefs.md`.

### Visual Identity (Minimal V1)
- No locked brand kit yet — identity develops through iteration
- Default toward clean, professional, high contrast
- Wild card visuals are where color, illustration, and editorial boldness live

### Workflow (updated 2026-08-07 — Claude design default)
- **Structured visuals:** Claude authors the HTML/SVG design from the brief and publishes it (Artifact tool); Alex exports to 4:5 PDF/PNG (⌘P → Save as PDF yields a LinkedIn-ready carousel; screenshot frames for PNGs). Iteration stays in-conversation — edit the file, republish, same URL. No app hand-off, no label re-interpretation.
- **Pictorial imagery:** Claude writes the Gemini prompt (architectural, not aspirational — see the AI Image Prompting rules above); Alex generates in Gemini and reviews output.
- The two failure modes we designed out: (1) an app re-flowing/garbling dense labels (Gamma/Canva); (2) a tool→tool→export hand-off with switching cost. Claude renders the pixels; Gemini is frontier-flexible, not a harness.

---

*Last updated: 2026-08-21*
*Version: 0.8 — Codified the Audience-First North-Star (YED-103) into production: mission + embedded-expert-correspondent persona + the ordering-not-erasure counterweight to decenter-self (incl. softening Tone Pillar 5 from "never make it about you" → "never about you at the audience's expense; bring yourself in where it adds value / analysis / unique POV, incl. cross-event convergence"), the three floors (Receipts / HM-Activation / Anti-Goodhart), the Substance/Insight Floor (density via translating the single robust deep-research brief, within the char cap), the Learn-More Set (3–5 citations every post, first comment/carousel), and the close-is-the-self-trap rule. Wires the north-star into the files the skills read. See `audience-north-star.md`.*
*Version: 0.7 — Gamma REMOVED as visual generator. Claude design (self-contained HTML/SVG via Artifact tool) is now the default for structured/label-dense visuals; Gemini for pictorial imagery; Canva vestigial. Updated the Tool Selection table + Workflow. See CLAUDE.md rule #13 + `content-patterns/visual-briefs.md`. Proof: AI Demo Night consolidation carousel.*
*Version: 0.6 — Added the Opener rule (never lead an event post with "I"; lead with topic / headline-stat / host-company / people / NYC-AI-ecosystem). First-line enforcement of decenter-self. See memory `feedback-no-i-led-openers-2026-08-07`.*
*Version: 0.5 — Added (1) the stance-license rule (a viewpoint must be earned with space/presence/expertise; hot takes in synopses add zero value) and (2) the decenter-self / curator-not-protagonist rule, from the Upcoming Week post review (NYC Tech Week roundup). These refine — not replace — the bold-stance rule: stance is deferred to formats with room for context + analysis (post-event, deep posts), and grows with Alex's expertise. See memory `feedback-upcoming-week-stance-and-self-2026-05-30`.*
*Version: 0.4 — Added (1) predictions-vs-stances voice rule and (2) visuals-must-add rule, from the AI Demo Night post review. See memory `feedback-comment-workflow-2026-05-26`.*
*Version: 0.3 — Added 10 visual content best practices (format specs, 2-second thumb test, one-visual-one-idea, data principles, carousel architecture, color strategy, AI prompting rules, accessibility, format-by-content-type)*
