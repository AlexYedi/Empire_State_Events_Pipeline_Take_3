## Visual Brief — 5-slide carousel (Arc 1: Hook → Evidence → Mechanism → Counterpoint, with the final slide set by your override)

**Carousel thesis:** Watching a TAM is a stack of decisions (what to watch, what each finding costs, where the filter sits, how much coverage each plan allows), and Deepline's own documents show where each one lives.

**Slide count:** 5
**Aspect ratio:** 4:5 (1080x1350)
**Tool routing summary:** all slides → Claude design (HTML/SVG) → headless Chrome PDF. No Gemini.

**Palette (all slides):**
- Dark slate #111418 background, off-white #F2F2EE text.
- One accent, amber #D97706, because the topic is business/GTM.
- Acid green #8FE83A only as the headline underline and the name mark.
- Legend on top of charts; dark label text on bright fills.

### Slide 1 of 5 — Hook
- **Visual mode:** bold typography card
- **Headline:** "What does watching a whole TAM cost?"
- **Body:**
  - Strip under the headline: "Deepline Deepdives · hosted by Jai Toor · Tue 11/10, 12:00 PM ET · free, online"
  - Bottom-left: "Agenda: free people search · Monitors · self-improving plays"
- **Palette:** dark + off-white; acid-green underline under "whole TAM"
- **Source:** Deepline invite and Luma page, 2026
- **Alt text:** Title card asking what it costs to watch a whole TAM, with the Deepline Deepdives session details.
- **Tool:** Claude design (HTML/SVG)

### Slide 2 of 5 — Evidence: the rate card by signal
- **Visual mode:** horizontal bar chart, legend on top
- **Headline:** "Most signals bill per finding. One doesn't."
- **Body:** bars in credits, with $ at $0.10 per credit:
  - Company social post: 0.75 ($0.075)
  - Job opening: 1.25 ($0.125)
  - New hire: 1.75 ($0.175)
  - Contact job change: 3.5 per tracked contact per 30 days ($0.35). This bar is amber, hatched, and labelled "flat fee".
  - Funding round: 5 ($0.50)
  - New company: 7.5 ($0.75)
  - Legend: "Off-white = charged per finding · Amber hatched = flat per contact, every 30 days"
- **Palette:** off-white bars, one amber bar
- **Source:** Deepline Monitors docs, retrieved 2026-11-09
- **Alt text:** Bar chart of Deepline Monitor prices per finding, from 0.75 credits for a social post to 7.5 for a new company, with contact job changes shown separately as a flat 3.5 credits per contact every 30 days.
- **Tool:** Claude design (HTML/SVG)

### Slide 3 of 5 — Mechanism: where the money and the filter sit
- **Visual mode:** left-to-right flow diagram
- **Headline:** "Filter at the Monitor, not the Play"
- **Body:**
  - Flow: [Monitor: one company, contact or market × one signal] → [Finding] → [Database row] → [Play: workflow in code] → [Rep / action].
  - An amber "$ charged here" tag on the Finding box.
  - Amber callout on the Monitor: "Filters here cut charges."
  - Grey callout on the Play: "Filters here don't."
  - Footnote: "Stopping a Play doesn't stop its Monitor. A stopped or out-of-credit Monitor doesn't replay what it missed."
  - A dashed box after Rep, labelled "Self-improving? Feedback signal and approver: not yet public."
- **Palette:** dark + off-white + amber callouts
- **Source:** Deepline Monitors and Plays docs, retrieved 2026-11-09
- **Alt text:** Flow from a Monitor to a finding, a database row, a Play and a rep, showing that charges happen at the finding and that filters cut cost only at the Monitor.
- **Tool:** Claude design (HTML/SVG)

### Slide 4 of 5 — Counterpoint: coverage by plan
- **Visual mode:** step chart / plan ladder
- **Headline:** "'Entire TAM' is an Enterprise line item"
- **Body:**
  - Four steps:
    - Pay-as-you-go $0: 15 monitored accounts (combined with scheduled plays); 5,000 free people searches a month
    - Growth $395/mo: up to 500 accounts; 200,000 searches
    - Team $995/mo: up to 500 accounts; 500,000 searches; unlimited email enrichment
    - Enterprise: custom price; full-TAM monitoring and custom signals
  - Footer question: "Whole list or tiered slice: what earns an alert?"
- **Palette:** off-white steps, amber Enterprise step
- **Source:** Deepline pricing page, as of 2026-11-09
- **Alt text:** Plan ladder showing Deepline's monitored-account limits rising from 15 to 500, with full-TAM monitoring only on custom-priced Enterprise.
- **Tool:** Claude design (HTML/SVG)

### Slide 5 of 5 — Also on today's calendar
- **Visual mode:** typography list, three identical rows
- **Headline:** "Also notable today"
- **Body:**
  - "12:00 PM · online · Get Hired in Tech: Live Q&A with recruiter Julian Simon-Parson (Aura Recruit) · 3percentclub"
  - "5:00 PM · Entrepreneurs Roundtable #219 (ERA) · Owen Davis, Contour Venture Partners · host Lou Abrams, First Citizens Innovation Banking"
  - "6:30 PM · Hard Negatives debate night · Qdrant, Agora, Hermes · the room votes live"
- **Palette:** dark + off-white; amber times
- **Source:** event invites, 2026
- **Alt text:** List of three other notable NYC events on November 10: a recruiter Q&A, a founder pitch night and an AI debate night.
- **Tool:** Claude design (HTML/SVG)

**Quality gate checks:**
- Arc fit: pass. Hook, evidence, mechanism, counterpoint. The final slide is the required other-events slide.
- Job differentiation: pass. No two slides could swap jobs.
- Frame parallelism: n/a (Arc 1).
- Thumb test: pass. Every headline is 8 words or fewer. Watch slide 2: six bars need labels of at least 40px.
- Source citations: pass on every slide with a number.
- Adds information: pass on slides 2 and 3; neither the per-signal prices nor the filter placement is in any variant. Slide 4 overlaps A's hook on 15/500/Enterprise but adds plan prices and search allowances. Drop it to 4 slides if A ships.
- Final slide earns the swipe: flagged. Your override puts the event list last; the open question sits on slide 4 instead.
- The carousel is public and downloadable; nothing on it is sensitive.

=====
