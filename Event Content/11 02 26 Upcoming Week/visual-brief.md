## Visual Brief — 5-slide carousel (Arc: Arc 4, One Question, Five Perspectives, condensed)

**Carousel PDF title:** The Upcoming Week, Nov 2–6, 2026: ten AI events (six in NYC, four streaming), one question

**Carousel thesis:** the week's ten events on one calendar, what each one checks, what evidence would settle its open question, and the three answers the week tests to "who checks the agent": a person, a machine, or a metric. The timing, the settle criteria, the provenance of the two PR numbers and the three-way synthesis are not in the post copy.

**Slide count:** 5. Ten events would need 12 per-event slides, so the perspectives are condensed into two grids that share one template (slide 2 for livestreams, slide 3 for in-person). This follows the 10/26 brief's pattern.
**Aspect ratio:** 4:5 (1080x1350), LinkedIn carousel default.
**Tool routing summary:** all slides → Claude design (HTML/SVG) → headless Chrome PDF. No pictorial slides.
**Palette (whole carousel):** dark slate #0F172A background, white #FFFFFF text, ONE accent blue #3B82F6 (meaning-bearing only: livestream bars, the "what gets checked" column, the number callouts). Acid green #8FE83A appears ONLY as the underline on the name mark (small, bottom-left, every slide). Muted labels use white at 70% opacity, not a second hue.

### Slide 1 of 5 — The week as a map (shows timing, format and the Tuesday/Wednesday pile-up the copy only lists)
- **Visual mode:** Diagram / timeline.
- **Headline:** Ten events, four you can stream
- **Body / content:** A Monday-to-Friday timeline, 9 AM to 10 PM ET, with five day lanes. Legend on top: solid white bar = in person; accent-outlined bar with an accent "STREAM" tag = livestream (outline plus tag, so meaning never rests on colour alone). Bars:
  - Mon: "VirtusLab · Can your agents ship?" (solid), starting 6:30 PM, with the end fading out because no end time is published.
  - Tue: "AI DevCon NYC" 9:20 AM–5:30 PM (stream) · "Snowflake Expedition · technical" 1:00–6:00 PM (stream) · "AIMLC · Navier-Stokes" 5:30–7:15 PM, solid, with the talk block 6:15–7:15 marked.
  - Wed: "Revolt Demo Day 1" 12:00–1:00 PM (stream) · "Expedition · GTM" 1:00–6:30 PM (stream) · "Agentics Spotlight" 6:00–10:00 PM (solid).
  - Thu: "Revolt Demo Day 2" 12:00–1:00 PM (stream) · "Ghosts in the System" 6:00–8:30 PM (solid).
  - Fri: "Level Up With Lovable" 11:00 AM–3:00 PM (solid) · "Voice Agent Hackathon" 3:00–9:00 PM (solid).
  - Small footer tag on the Tue lane: "Election Day".
- **Palette:** #0F172A bg + white text + accent #3B82F6 (stream outlines and tags only).
- **Source attribution:** Source: event listings (Luma, Tessl, Snowflake, RevGenius), Nov 2026. Times ET.
- **Alt text:** A Monday-to-Friday timeline of ten AI events, marking four livestreams and six in-person events, with three events each on Tuesday and Wednesday.
- **Tool:** Claude design (HTML/SVG).

### Slide 2 of 5 — Watch from anywhere: what each stream checks and what would settle it
- **Visual mode:** Framework / matrix, 4 rows × 3 columns (Event + how to join · What gets checked · What would settle it). The row template is identical to slide 3's.
- **Headline:** Four streams, watch online
- **Body / content:**
  - AI DevCon NYC (Tessl) · YouTube, Tue · "the merge" · "A speaker naming the method and baseline behind a vendor number"
  - Snowflake Expedition, technical · Tue · "agent controls" · "GA, preview or roadmap, said out loud, for each control shown"
  - Snowflake Expedition, GTM · Wed · "the marketing number" · "A budget that moved because an experiment beat the dashboard"
  - Revolt! Demo Days (RevGenius) · Wed + Thu · "the CRM write" · "A live demo showing who approved the write, on realistic data"
- **Palette:** #0F172A bg + white text + accent #3B82F6 on the "What gets checked" column only.
- **Source attribution:** Source: event agendas and research briefs, Nov 2026.
- **Alt text:** A four-row table pairing each livestreamed event with what it checks and the observable evidence that would answer its open question.
- **Tool:** Claude design (HTML/SVG).

### Slide 3 of 5 — In New York: same frame, six in-person events
- **Visual mode:** Framework / matrix, 6 rows × 3 columns, the same template as slide 2 (one shared CSS row class).
- **Headline:** Six rooms in New York
- **Body / content:**
  - VirtusLab · Mon · "the merge gate" · "A stated threshold, and who owns it"
  - AIMLC · Tue · "the proof" · "One line on what's established, one on what isn't"
  - Agentics Spotlight · Wed, NYU · "the skill" · "A named failure signature for a skipped skill"
  - Ghosts in the System · Thu, Ro HQ · "the reply at volume" · "A stated miss rate on urgent cases"
  - Level Up With Lovable · Fri AM · "the shipped app" · "One task the tool still leaves to the builder"
  - Voice Agent Hackathon · Fri PM · "the turn" · "A latency number measured on a real phone line"
- **Palette:** #0F172A bg + white text + accent #3B82F6 on the "What gets checked" column only.
- **Source attribution:** Source: event listings and research briefs, Nov 2026.
- **Alt text:** A six-row table pairing each in-person event with what it checks and the evidence that would answer its open question.
- **Tool:** Claude design (HTML/SVG). Densest slide: render the settle column at 44–48px and abbreviate if it squints at 375px.

### Slide 4 of 5 — Two PR numbers, two different measurements (the provenance the post can't hold)
- **Visual mode:** Split-frame comparison, mirrored panels.
- **Headline:** Two numbers, two different measurements
- **Body / content:**
  - Left panel, number callout "≈ 1 in 3": "Zalando PRs auto-approved as low-risk." What it measures: the share of one company's PRs that a risk tier routes past human review, across 250+ teams. Method: first-party and observational; methodology not disclosed. Source line: Zalando Engineering, 2026-08-14.
  - Right panel, number callout "0.5%": "AI-only-review merges at the median company." What it measures: merges reviewed only by AI, across 1,300+ companies. Method: Jellyfish's own dataset. Source line: Jellyfish via R&D World, 2026-10-27.
  - Footer: "One company's policy, one cross-company median. Neither is a controlled study."
- **Palette:** #0F172A bg + white text + accent #3B82F6 on both number callouts (same weight, so neither reads as the winner).
- **Source attribution:** Source: Zalando Engineering blog (2026-08-14); Jellyfish data as reported by R&D World (2026-10-27).
- **Alt text:** Two mirrored panels separating Zalando's roughly one-in-three auto-approved PRs from Jellyfish's 0.5% median rate of AI-only-review merges, noting how each was measured.
- **Tool:** Claude design (HTML/SVG).

### Slide 5 of 5 — Synthesis: who does the checking, across all ten
- **Visual mode:** Bold typography plus a three-column grid, in documentarian mode (off-white on dark slate, no accent). It mirrors slide 1's type scale.
- **Headline:** A person, a machine, or a metric
- **Body / content:** Three equal columns, each listing the events whose open question turns on that kind of check:
  - "A person signs off": VirtusLab (merge gate) · Revolt Day 1 · Revolt Day 2 (CRM write approval)
  - "A machine checks": AIMLC (reported Lean check) · Agentics Spotlight (skill pressure tests) · Level Up With Lovable (SEO review)
  - "A metric decides": Snowflake Expedition (governed definitions, experiments vs attribution) · Voice Agent Hackathon (judged on response time and turn-taking)
  - Footer line: "AI DevCon's nine talks and Ghosts in the System's panel span all three."
- **Palette:** off-white #F8FAFC on #0F172A, no accent (editorial mode). The acid-green #8FE83A name-mark underline only.
- **Source attribution:** none (synthesis; no figures or quotes).
- **Alt text:** Three columns sorting the week's ten events by whether their open question turns on a human sign-off, a machine check or a metric, with two events spanning all three.
- **Tool:** Claude design (HTML/SVG).

**Quality gate checks:**
- Arc fit: pass. This is a weekly roundup, so Arc 4. It is condensed because ten events would mean 12 slides; the deviation is noted above.
- Job differentiation: pass (timing map / livestream settle criteria / in-person settle criteria / one claim pair's provenance / cross-event synthesis). Slides 2 and 3 split by format, so they don't duplicate each other.
- Frame parallelism: slides 2 and 3 share one row template; slide 4's panels are mirrored with equal-weight callouts; slides 1 and 5 share a type scale.
- Thumb test per slide: pass. Headlines run 5–6 words. Slide 3 is the densest: render at 44–48px minimum on the settle column and abbreviate if it squints at 375px.
- Source citations: pass on slides 1–4; slide 5 is synthesis with no figures.
- Adds information, not repetition: pass. Clock times, the Election Day overlap, the "what gets checked" and "what would settle it" columns, the provenance and method of the two PR numbers, and the person/machine/metric sort are all absent from the copy.
- Final slide earns the swipe: pass. It is synthesis, not housekeeping, and it takes no side (it sorts approaches without ranking them).
- Colour rules: pass. One accent (#3B82F6) carries meaning only, paired with outline and tag patterns. Acid green #8FE83A appears only on the name-mark underline. Contrast ≥4.5:1 for all text.
- Public-file check: pass. No private material (no hiring signals, applications or registration status) appears on any slide, since carousel PDFs are downloadable.
