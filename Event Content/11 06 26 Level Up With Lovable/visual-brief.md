# Level Up With Lovable — Pre-Event Carousel Visual Brief (2026-11-06)

Source of record: Notion Content Draft "Level Up With Lovable — Pre-Event Post" (needs_review). Render not yet run.

## Visual Brief — 5-slide carousel (Arc: Arc 3 — Before → After → What Changed → Implication → So What)

**Carousel thesis:** A coding agent leaves the plumbing to you, and a product agent takes it over layer by layer, moving the AI bill and the model clock onto the platform. That leaves one question to settle on Friday: what is still yours?

**Slide count:** 5
**Aspect ratio:** 4:5 (1080x1350), LinkedIn carousel default
**Tool routing summary:** all slides → Claude design (HTML/SVG). No pictorial slides, so no Gemini.
**Palette (all slides):** dark slate ground #0F172A + white text #FFFFFF + ONE accent, Tech/AI blue #3B82F6. This is the lighter cobalt the Ghosts carousel used, because #1E40AF fails contrast on a dark ground. Signature acid green #8FE83A appears only as the name-mark underline in the footer, per the brand tokens. Page number bottom-right on every slide.

---

### Slide 1 of 5 — Before: with a coding agent, every layer is yours

- **Visual mode:** Diagram (five-row layer stack with an owner column)
- **Headline:** Coding agent: you own the plumbing
- **Body / content:** A vertical stack of five labelled rows, top to bottom: "Hosting, database, auth" · "AI keys and billing" · "Model choice" · "Live data" · "Getting found (SEO/GEO)". The right-hand column is headed "Who holds it", and every row reads "You" in white. Caption under the stack: "Coding agent (Claude Code, Cursor): edits your repo. You run, review and deploy."
- **Palette:** dark bg + white text + #3B82F6 (accent on the column header only)
- **Source attribution:** "Framework: coding agent vs product agent. Layers from the Level Up With Lovable agenda, luma.com/35iuoq3d, 2026."
- **Alt text:** A five-layer stack (hosting, AI keys, model choice, live data, getting found) in which the builder holds every layer when working with a coding agent.
- **Tool:** Claude design (HTML/SVG)

### Slide 2 of 5 — After: the same stack with a product agent, per Friday's agenda

- **Visual mode:** Diagram (identical frame to slide 1; only the owner column changes)
- **Headline:** Product agent: the platform holds it
- **Body / content:** The same five rows in the same order. The "Who holds it" column now reads "Platform" in accent blue, with an agenda tag and one fact per row:
  - "Hosting, database, auth": Cloud DB and secrets
  - "AI keys and billing" [A1]: one key per project, billed as Run credits
  - "Model choice" [A2]: a default plus alternates per use case
  - "Live data" [A3]: managed Firecrawl, Perplexity and Parallel, no vendor account
  - "Getting found" [A4]: server rendering for apps since 2026-05-13, Markdown for verified AI crawlers
- **Palette:** dark bg + white text + #3B82F6 on every "Platform" cell
- **Source attribution:** "Sources: docs.lovable.dev/features/ai, /features/seo, /changelog (2026); agenda IDs A1–A4 from luma.com/35iuoq3d."
- **Alt text:** The same five-layer stack, now with the platform holding every layer; each layer is tagged to one of the event's four agenda blocks and to a documented Lovable feature.
- **Tool:** Claude design (HTML/SVG)

### Slide 3 of 5 — What changed: the AI bill moves inside the platform

- **Visual mode:** Diagram (left-to-right flow with one greyed-out path)
- **Headline:** The AI bill moved inside the platform
- **Body / content:** Flow: "Your app's AI call" → "Lovable gateway (one project key)" → "Model" → "Run credits on your Lovable workspace" (this last box in accent blue). Below the flow, a greyed-out, struck-through box with a dashed arrow: "Your OpenAI or Google account". Annotation strip along the bottom: "Free AI grant: 4 credits a month, 'temporary', no rollover" · "429 = rate-limited · 402 = out of credits".
- **Palette:** dark bg + white text + #3B82F6. The bypassed box is #94A3B8 grey and carries a label, so the meaning never rests on colour alone.
- **Source attribution:** "Source: Lovable docs, docs.lovable.dev/features/ai, 2026."
- **Alt text:** A flow diagram in which an app's AI call goes through Lovable's gateway and is billed as Run credits instead of to the builder's own model-provider account, with the free grant and the error codes noted.
- **Tool:** Claude design (HTML/SVG)

### Slide 4 of 5 — Implication: model choice comes with a retirement clock

- **Visual mode:** Single-number data viz (horizontal timeline with three markers)
- **Headline:** Model choice has an expiry date
- **Body / content:** A horizontal timeline with three markers: "Nov 6, 2026: build session" (white) → "Nov 19, 2026: Gemini 3.6 Flash stops" (accent blue, labelled "+13 days") → "Jan 28, 2027: Gemini 3.7 Flash stops" (accent blue, labelled "+83 days"). Caption: "An app built on a retired model may have to be re-pointed. Who does it: you or the platform?"
- **Palette:** dark bg + white text + #3B82F6
- **Source attribution:** "Source: Lovable changelog, docs.lovable.dev/changelog, 2026. Day counts computed from the session date."
- **Alt text:** A timeline showing two Gemini Flash models scheduled to stop 13 and 83 days after the November 6 session.
- **Tool:** Claude design (HTML/SVG)

### Slide 5 of 5 — So what: the scorecard Friday fills in

- **Visual mode:** Framework / matrix (4 rows × 2 columns, with the result column left blank)
- **Headline:** When the platform holds it, what's yours?
- **Body / content:** Column headers: "The test" | "Friday's result". Rows:
  - "Credits at 100 users [A1]" | "____"
  - "Swap a model after launch [A2]" | "____"
  - "Live data with no key [A3]" | "____"
  - "What AI crawlers actually see [A4]" | "____"
  
  Footer: "Results in the follow-up · Level Up With Lovable · Brooklyn · Fri Nov 6". Name-mark with the #8FE83A underline.
- **Palette:** dark bg + white text + #3B82F6 on the column headers
- **Source attribution:** none (no data point or quote)
- **Alt text:** A four-row scorecard of the build tests (credits, model swap, live data, crawler view) with blank results to fill in after the session.
- **Tool:** Claude design (HTML/SVG)

---

**Quality gate checks:**
- **Arc fit:** pass. The post is a change-over-time argument (coding agent → product agent, with the platform absorbing each layer), so Arc 3 fits. Arc 1 was rejected because no single data point carries the post. Arc 4 was rejected because there is one host and no panel.
- **Job differentiation:** pass. Before (who owned it), after (who owns it now, with evidence), mechanism (where the bill goes), implication (the model clock), so what (the open scorecard). No two jobs can be swapped.
- **Frame parallelism (if Arc 2 or 3):** pass. Slides 1 and 2 share one CSS frame: the same five rows in the same order, with only the owner column changed.
- **Thumb test per slide:** pass. Every headline is 5–7 words, set at 48px or larger at 1080 wide. Slide 2's row facts are short phrases of 12 words or fewer.
- **Source citations:** pass. Slides 1–4 carry source lines, and slide 5 has no data.
- **Adds information (not repetition):** pass.
  - Slide 2 maps each agenda block to a documented feature in one view.
  - Slide 3 adds the 429/402 codes, plus the 4-credit grant for readers of Variants A and C.
  - Slide 4 adds the 2027-01-28 Gemini 3.7 Flash date.
  - Slide 5 adds the scorecard device that the post-event post fills in.
- **Final slide earns the swipe:** pass. It ends on the open question and an empty scorecard, which opens the post-event half of the pre→post arc.
