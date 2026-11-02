# Ghosts in the System — Pre-Event Carousel Visual Brief (2026-11-05)

Source of record: Notion Content Draft "Ghosts in the System - How AI Powers Scale — Pre-Event Post" (needs_review). Render not yet run.

## Visual Brief — 5-slide carousel (Arc: Arc 1 — Hook → Evidence → Mechanism → Counterpoint → CTA)

**Carousel thesis:** A triage tool can be fast, with a 94% catch rate by its own published figures, and still leave the question that matters open: who catches the messages it never flagged, and does anyone verify the miss rather than the headline?

**Slide count:** 5
**Aspect ratio:** 4:5 (1080x1350), LinkedIn carousel default
**Tool routing summary:** all slides → Claude design (HTML/SVG). No pictorial slides, so no Gemini.
**Palette (all slides):** dark slate ground #0F172A + white text #FFFFFF + ONE accent, Tech/AI blue #3B82F6 (a lighter cobalt than #1E40AF, chosen for contrast on dark). Signature acid green #8FE83A only as the name-mark underline in the footer, per the brand tokens. Page number bottom-right on every slide.

---

### Slide 1 of 5 — Hook: put the unanswered question on the cover

- **Visual mode:** Bold typography card
- **Headline:** If 94% are caught, who finds the rest?
- **Body / content:** Sub-line: "Ghosts in the System · Ro HQ, NYC · Thu Nov 5". The "94%" is set in the accent blue; everything else is white.
- **Palette:** dark bg + white text + #3B82F6
- **Source attribution:** "Source: Ro, ro.co/dtp/ai-triage (Ro's own published figures, self-reported), 2025."
- **Alt text:** A title card asking who finds the messages that a triage tool with a reported 94% catch rate does not flag, for the Ghosts in the System event at Ro on November 5.
- **Tool:** Claude design (HTML/SVG)

### Slide 2 of 5 — Evidence: show the speed win and the possible gap side by side

- **Visual mode:** Single-number data viz (two paired bars)
- **Headline:** Faster. And maybe 6 in 100 unflagged?
- **Body / content:**
  - **Top:** a horizontal bar pair labelled "Median response time": "Before: 115 min" (grey, full width) vs "After: 33 min" (blue, ~29% width).
  - **Bottom:** one 100-unit stacked bar labelled "Real side-effect messages (implied, if 94% is sensitivity)": 94 segments blue ("flagged") + 6 segments outlined white with a dashed border ("not flagged").
  - **Legend:** sits above the bars.
  - **Annotation (one):** "Urgent-subset miss rate: not found in Ro's published material."
- **Palette:** dark bg + white text + #3B82F6 (the "before" bar is #94A3B8 grey so it stands off the dark ground)
- **Source attribution:** "Source: Ro, ro.co/dtp/ai-triage (Ro's own published figures, self-reported), 2025. 6-in-100 split is my inference from the 94% true-positive rate."
- **Alt text:** Two bar charts: median response time falls from 115 to 33 minutes, and if the 94% figure is sensitivity, about 6 of every 100 real side-effect messages would go unflagged.
- **Tool:** Claude design (HTML/SVG)

### Slide 3 of 5 — Mechanism: why each job fails differently

- **Visual mode:** Diagram (three-column flow)
- **Headline:** Three jobs. Three ways to fail.
- **Body / content:**
  - **Flow:** three boxes, left to right, joined by arrows: CLASSIFY → TRIAGE → ROUTE / DRAFT.
  - **Two rows under each box:**

    | Row | Classify | Triage | Route / Draft |
    |---|---|---|---|
    | Failure | wrong label | urgent message not flagged | bad draft gets approved |
    | Who notices | an audit sample | nobody, it just waits | the human reading it, if they read closely |

  - **Highlight:** the TRIAGE column is outlined in accent blue, the only highlighted element.
- **Palette:** dark bg + white text + #3B82F6
- **Source attribution:** "Three-job breakdown and failure modes: my mapping."
- **Alt text:** A three-step diagram, classify then triage then route or draft, showing that a triage miss is the one failure no one is alerted to.
- **Tool:** Claude design (HTML/SVG)

### Slide 4 of 5 — Counterpoint: everyone verifies, but by their own account

- **Visual mode:** Framework / matrix (3 rows × 2 columns)
- **Headline:** Three reliability stories, each self-reported
- **Body / content:**

  | Company | How they say they keep it reliable | Who checked it |
  |---|---|---|
  | Ro | Ongoing human expert audits | Self-reported (Ro's own page) |
  | Decagon | Simulations pre-launch, Watchtower always-on QA, Experiment Hub | Vendor-run benchmark (DuetBench) |
  | Nayya | Expert-curated datasets, automated evals across thousands of scenarios, playtesting | Vendor-described |

  The column headers are blue; the cells are white.
- **Palette:** dark bg + white text + #3B82F6
- **Source attribution:** "Sources: ro.co/dtp/ai-triage (2025); decagon.ai (2026); nayya.ai (2026)."
- **Alt text:** A table comparing how Ro, Decagon and Nayya publicly describe verifying their AI, and showing that each account comes from the company itself.
- **Tool:** Claude design (HTML/SVG)

### Slide 5 of 5 — CTA: hand the reader the question to bring

- **Visual mode:** Bold typography card
- **Headline:** Verify the headline, or the miss?
- **Body / content:** Sub-line: "Ro · Decagon · Nayya. Thursday at Ro HQ. What would you ask them?" A small footer line: "Questions in the comments go into the Q&A." Name-mark with the #8FE83A underline.
- **Palette:** dark bg + white text + #3B82F6
- **Source attribution:** none (no data point or quote)
- **Alt text:** A closing card asking whether these teams verify the headline accuracy number or the misses, and inviting readers to send questions for Thursday's panel.
- **Tool:** Claude design (HTML/SVG)

---

**Quality gate checks:**
- Arc fit: pass. The post rests on one data point (94% / 115→33) and its implication, so Arc 1 fits. Arc 4 was rejected because per-speaker cards would re-print the post's three-reliability-models list (Arc 4 guard).
- Job differentiation: pass. Hook (question), evidence (numbers), mechanism (why the miss is silent), counterpoint (who verified the verification), CTA (the reader's question).
- Frame parallelism (if Arc 2 or 3): n/a (Arc 1). Slides 1 and 5 share the typography-card frame.
- Thumb test per slide: pass. Headlines run 5–8 words at 48px or larger at 1080 wide; slide 4's cells are short phrases.
- Source citations: pass. Slides 1–4 carry source lines; slide 2 labels the 6-in-100 split as inference; slide 5 has no data.
- Adds information (not repetition): pass. Slide 2 shows the implied gap, slide 3 adds "who notices" per job, and slide 4 adds the "who checked it" column and DuetBench.
- Final slide earns the swipe: pass. It ends on the open question.
