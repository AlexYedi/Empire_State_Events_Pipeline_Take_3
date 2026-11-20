## Visual Brief — 5-slide carousel (Arc 1: Hook → Evidence → Mechanism → Counterpoint → CTA)

**Carousel thesis:** Thursday's five events each sit at a different checkpoint for AI output (model, analysis, reviewer, source, run). The claims at each checkpoint come from the people who make them, and the checkers are often related to what they check.

**Slide count:** 5
**Aspect ratio:** 4:5 (1080x1350)
**Tool routing:** all slides → Claude design (HTML/SVG). No pictorial slides.
**Equal-weight rule:**
- Every multi-event slide lists all five events in time order.
- Every event gets the same frame, row height and type size.
- No event gets the accent alone. The accent marks the question, never an event.

**Variant fit:** built for A. Slides 2–4 also support B, C and D, because the evidence, layer and ownership maps are shared facts. Swap slide 5's line to match the chosen variant.

### Slide 1 of 5: Hook
- **Visual mode:** bold typography card
- **Headline:** Who checks the agent's work?
- **Body / content:** A thin timeline strip under the headline with five equal ticks: "12:00 Metabase (online) · 5:00 NY-MLR @ Intuit · 5:30 Cool Machines by Ramp · 6:00 World of Tavily · 6:30 Temporal + MongoDB". Eyebrow: "Thu, Nov 12 · New York".
- **Palette:** dark bg #0F1420 + white text + blue accent #5B8DEF (tech/agents; same token as the Oct 12 pair). The accent is used on the headline underline only.
- **Source attribution:** none
- **Alt text:** Title card asking who checks an AI agent's work, over a timeline of five New York AI events on November 12 shown at equal size.
- **Tool:** Claude design (HTML/SVG)

### Slide 2 of 5: Evidence (who is making each claim)
- **Visual mode:** framework / matrix, 5 rows × 3 columns (Event · The claim · Who said it)
- **Headline:** Who's saying it? The makers.
- **Body / content (rows in time order):**
  - Metabase · "open source AI analytics you can verify" · Metabase
  - NY-MLR @ Intuit · masked diffusion "more performant than previously thought" · the MDLM authors, Schiff among them (2024)
  - Cool Machines · "74% of merged PRs" · Ramp (Oct 27)
  - World of Tavily · "building that stack together" · the invite. Nebius says it acquired Tavily.
  - Temporal + MongoDB · "guaranteed to execute to completion" · Temporal, in the invite
- **Palette:** dark bg + white text + blue accent on the "Who said it" column header only
- **Source attribution:** "Sources: Metabase on Luma; Sahoo et al., arXiv 2406.07524, 2024; Ramp, 2026; Luma/Nebius, 2026; event invite, 2026."
- **Alt text:** Table of five events, each with its headline claim and the party that made it; every claim comes from the company or authors it describes.
- **Tool:** Claude design (HTML/SVG)

### Slide 3 of 5: Mechanism (the five checkpoints)
- **Visual mode:** diagram, a stack of five equal horizontal bands with one question per band
- **Headline:** Five layers, five checks
- **Body / content (bottom to top):**
  - Model · NY-MLR @ Intuit · "Can it take a word back?"
  - Run · Temporal + MongoDB · "Who owns state after a failure?"
  - Source · World of Tavily · "Who checks the grounding?"
  - Analysis · Metabase · "Who verifies the reading?"
  - Review · Cool Machines · "What does a reviewer look at?"
  - Right-edge label: "Output →"
- **Palette:** dark bg + white text + blue accent on the "?" glyphs only
- **Source attribution:** "Analysis by Alex Yedibalian from event invites and company posts, Nov 2026."
- **Alt text:** Five-layer stack diagram (model, run, source, analysis, review), each layer labelled with its event and its open verification question.
- **Tool:** Claude design (HTML/SVG)

### Slide 4 of 5: Counterpoint (who is connected to whom)
- **Visual mode:** diagram, a node-and-arrow ownership map
- **Headline:** The checkers have relationships
- **Body / content:**
  - Nebius → Tavily, labelled "acquired"
  - MongoDB → Temporal, labelled "Ventures portfolio"
  - Founders of Ramp → Crosby, labelled "seed investors"
  - John Sarihan, labelled "ex-Ramp, Crosby CTO"
  - Standalone nodes, same size: "NY-MLR: independent, volunteer-run · Intuit: partner and host" and "Metabase: open source"
  - LangChain shown as co-host beside Tavily with no ownership arrow
- **Palette:** dark bg + white text + blue accent on the arrows
- **Source attribution:** "Sources: Nebius blog, 2026-05-20; MongoDB Ventures page, read 2026-11-01; Crosby launch post, 2025-06-17; Sequoia, 2025; nymlr.com, 2026; Metabase on Luma."
- **Alt text:** Map of relationships among the hosts and speakers: Nebius owns Tavily, MongoDB invests in Temporal, Ramp's founders seeded Crosby; NY-MLR is independent and Metabase is open source.
- **Tool:** Claude design (HTML/SVG)

### Slide 5 of 5: CTA (the open question)
- **Visual mode:** bold typography card
- **Headline:** Which check gives first?
- **Body / content:** "Model. Analysis. Reviewer. Source. Run." on one line in equal weight. Under it: "If you're deep into any of these, what do you want answered on Thursday?"
- **Palette:** dark bg + white text + blue accent on the headline underline
- **Source attribution:** none
- **Alt text:** Closing card asking which of five verification layers fails first, with an invitation to share what you hope Thursday's events answer.
- **Tool:** Claude design (HTML/SVG)

**Quality gate checks:**
- **Arc fit: pass.** A single thesis (checks at five layers) moves through evidence (who claims), mechanism (the layer map) and counterpoint (relationships) to a question. Arc 4 was rejected: one slide per event needs 7 slides, over the 5 cap.
- **Job differentiation: pass.** The five jobs are hook, who said it, where each check sits, who is related, and the open question. No two can be swapped.
- **Frame parallelism: n/a** (Arc 1). Equal-weight rows and bands are enforced instead.
- **Thumb test per slide: pass.** Headlines are 4–6 words at 48px or more. Slide 2 is the densest (15 short cells); render at 375px and cut column 2 to 6 words or fewer if it squints.
- **Source citations: pass.** Slides 2–4 carry source lines.
- **Adds information: pass.**
  - Slide 2 adds the "who said it" column, which is in no variant as a structure.
  - Slide 3 adds the stack ordering.
  - Slide 4 adds the relationship map, including MongoDB Ventures and NY-MLR's independence, which A does not carry.
- **Final slide earns the swipe: pass.** It ends on the open question, with no verdict and no "follow for more".
- **Equal billing: pass.** All five events appear on slides 1–3 in identical frames. Slide 4 gives NY-MLR and Metabase same-size nodes.
- **Public-file check: pass.** No addresses, attendance or private details. Carousel PDFs are downloadable.
