## Visual Brief — 5-slide carousel (Arc: Hook → Evidence → Mechanism → CTA)

**Carousel thesis:** Search lifts AI answers a lot, the top providers sit close together, and the links they return still don't prove the claims. So what's left to compete on is checking whether the citations hold up.

**Slide count:** 5
**Aspect ratio:** 4:5 (1080x1350), the LinkedIn carousel default
**Tool routing summary:** all slides → Claude design (HTML/SVG → headless Chrome PDF)
**Palette (all slides):** dark slate background #0F172A, white text #F8FAFC, and one accent: sky blue #38BDF8 (Tech/AI). I chose it over cobalt #1E40AF for contrast on the dark background. Grey #64748B for non-highlighted data. Acid green #8FE83A only for the name-mark underline.

---

### Slide 1 of 5 — Hook: makes the swipe worth it by naming the constraint every team shares

- **Visual mode:** Bold typography card
- **Headline:** Same search for every team. So what wins?
- **Body / content:** Subline: "Ground Truth: The Live Agents Hackathon · a one-day build on the You.com API · Sat 11/14 · Downtown Brooklyn". Footer: "localhost:nyc × The Builder Series × You.com". Page number 1/5.
- **Palette:** dark background + white text + #38BDF8 underline under "So what wins?"
- **Source attribution:** none (no data on this slide)
- **Alt text:** A title card asking what separates hackathon teams when all of them build on the same search API.
- **Tool:** Claude design (HTML/SVG)

### Slide 2 of 5 — Evidence: shows how much search adds and how little the top providers differ

- **Visual mode:** Single-number data viz (horizontal bars, legend on top)
- **Headline:** Search adds ~40 points. Providers differ by 11.
- **Body / content:** Legend on top: grey = no search, blue = with search. One grey bar "Model only: 33". One shaded blue band from 69 to 80 labelled "Every search provider on the index: 69–80". Three markers inside the band: "Exa (auto) 80", "Perplexity (medium) 80", "You.com (highlights) 74 · 20.2 s/task". Annotation: "Same fixed model for every provider; only the search changes." Small caveat line: "Equal-weighted average of DeepSearchQA, BrowseComp and AA-Omniscience."
- **Palette:** dark background + white text + #38BDF8 band, grey #64748B baseline
- **Source attribution:** Source: Artificial Analysis Search API index, live leaderboard, 2026-10-19
- **Alt text:** A bar chart: a model with no search scores 33, and all search providers score between 69 and 80; Exa and Perplexity are at 80 and You.com at 74.
- **Tool:** Claude design (HTML/SVG)

### Slide 3 of 5 — Counterpoint: what the scoreboard hides, because a link attached is not a claim supported

- **Visual mode:** Framework / three-stat timeline
- **Headline:** Three audits, one gap: links aren't proof
- **Body / content:** A left-to-right timeline with three stat blocks in the same frame:
  - "2023 · Liu et al.: 74.5% of citations supported their sentence"
  - "2025 · Tow Center / CJR: over 60% of answers incorrect across 8 tools"
  - "2025 · DeepTRACE: citation accuracy 40–80% across systems"
  - Faint baseline rule under the timeline: "100% = every citation holds".
- **Palette:** dark background + white text + #38BDF8 on the three numbers
- **Source attribution:** Sources: Liu et al., arXiv 2304.09848, 2023; Tow Center for Digital Journalism / CJR, 2025; DeepTRACE, arXiv 2509.04499, 2025
- **Alt text:** A timeline of three independent studies showing that AI search citations often fail to support the claims they are attached to.
- **Tool:** Claude design (HTML/SVG)

### Slide 4 of 5 — Mechanism: where in a grounded agent a receipt can fail, mapped to the hackathon tracks

- **Visual mode:** Diagram (pipeline + three-step check ladder)
- **Headline:** Where a receipt can fail
- **Body / content:**
  - Top row, left to right: "Question" → "Search API (ranked pages + excerpts + page age)" → "Model writes answer [1][2]".
  - The arrow drops into a three-rung ladder: "① Link exists: Cloudflare now requires a source link (Oct 2026)" · "② Page says it: exact quote found at the URL, at fetch time" · "③ Source worth trusting: judgment".
  - Label beside rung ①: "a link-only receipt stops here".
  - Bottom strip, the track map: "Live Wire → freshness · The Analyst → depth · Receipts → rungs ② and ③".
- **Palette:** dark background + white text + #38BDF8 on rungs ② and ③
- **Source attribution:** Source: InfoQ on Cloudflare AI Gateway web search, 2026; Ground Truth invite (Luma), 2026
- **Alt text:** A diagram of how a search-grounded agent answers a question, followed by three checks a citation must pass: the link exists, the page says it, and the source is reliable.
- **Tool:** Claude design (HTML/SVG)

### Slide 5 of 5 — CTA: leaves the reader with the open question

- **Visual mode:** Bold typography card
- **Headline:** Who checks the agent's receipts?
- **Body / content:** "When the agent that wrote the answer checks its own citations, is that verification, or a second claim?" Small footer: "Ground Truth: The Live Agents Hackathon · Sat 11/14 · registration by host approval". Page number 5/5.
- **Palette:** dark background + white text + #38BDF8 underline under "receipts"
- **Source attribution:** none
- **Alt text:** A closing card asking whether an AI agent checking its own citations counts as verification.
- **Tool:** Claude design (HTML/SVG)

---

**Quality gate checks:**
- **Arc fit: pass.** The post argument is data-anchored, so Arc 1 fits. The optional counterpoint slide is used as slide 3.
- **Job differentiation: pass.** The five slides do different jobs: hook, scoreboard, audits, mechanism, question. No two can be swapped.
- **Frame parallelism: n/a** (Arc 1). Slide 3's three stat blocks share one frame.
- **Thumb test per slide: pass.** Every headline is 8 words or fewer. Slide 4 is the densest: keep the ladder labels at 40px or above and the rung text to one line each.
- **Source citations: pass.** Slides 2, 3 and 4 carry source lines.
- **Adds information: pass.** The bar band, the timeline, the pipeline-plus-ladder and the track map are not in any post body. A lists the three questions as text, and slide 4 adds the pipeline and the track mapping.
- **Final slide earns the swipe: pass.** It ends on the open question. With no Pending events, there is no other-events slide.
