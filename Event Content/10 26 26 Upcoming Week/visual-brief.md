## Visual Brief — 5-slide carousel (Arc: Arc 4, One Question, Five Perspectives, condensed)

**Carousel thesis:** the week's six rooms on one calendar, the specific open question in each, and what evidence would settle it. That structure and specificity are not in the post copy.

**Slide count:** 5. Six events would need eight per-event slides, so the perspectives are condensed into one comparable grid (slide 2). Frames still share a template.
**Aspect ratio:** 4:5 (1080x1350), LinkedIn carousel default.
**Tool routing summary:** all slides → Claude design (HTML/SVG) → headless Chrome PDF. No pictorial slides.

### Slide 1 of 5 — The week as a map (shows the timing and format that the copy only lists)
- **Visual mode:** Diagram / timeline.
- **Headline:** Six rooms, five days, one double-booked Wednesday
- **Body / content:** A horizontal Mon–Fri timeline with the legend on top: solid bar = in person, outlined bar = online, hatched = format to confirm. The bars are:
  - Mon: 4:30–6:00 "AWS NYC · model evals" (hatched until the format is confirmed); 6:00–8:30 "The Shortlist" (solid).
  - Tue: 1:00–2:00 "DatologyAI · Curation Studio" (outlined).
  - Wed: two stacked bars, both solid. "Daytona AI Builders" runs 5:30–8:30 with a talks block marked 6:00–7:05. "Agents in NYC" runs 5:30–9:00 with a talks block marked 6:30–7:30. The overlap is shaded in the accent.
  - Thu: an empty lane labelled "open".
  - Fri: "Frontier Build NYC" as an all-day bar (solid). No clock times are shown, because sources conflict.
- **Palette:** dark bg + white text + blue #1E40AF.
- **Source attribution:** Source: event listings (Luma, Meetup) and invites, 2026.
- **Alt text:** A Monday-to-Friday timeline of six AI events, with two Wednesday evening events overlapping between 5:30 and 8:30 pm.
- **Tool:** Claude design (HTML/SVG).

### Slide 2 of 5 — One open question per room (the per-room specifics the post cannot fit)
- **Visual mode:** Framework / matrix, 6 rows × 3 columns (Room · What gets checked · The open question). One identical row template per room.
- **Headline:** Six rooms, six open questions
- **Body / content:**
  - AWS NYC · a model before release · "Can Bedrock use a judge from outside its own catalog?"
  - The Shortlist · the hire · "Which seats are open now, and where are they based?"
  - DatologyAI · the training data · "What does a buyer pay for: tokens curated, compute saved, or a seat?"
  - Daytona · what the agent carries · "When forked runs are scored, is the grader inside the sandbox or outside it?"
  - Agents in NYC · the judge · "What human-agreement rate made a no-explanation judge shippable?"
  - Frontier Build · the merge · "Can a reviewer agent satisfy branch protection, and on which paths never?"
- **Palette:** dark bg + white text + blue #1E40AF (accent on the question column only).
- **Source attribution:** Source: event abstracts and public docs, Oct 2026.
- **Alt text:** A six-row table pairing each event with what it evaluates and one unanswered question for that room.
- **Tool:** Claude design (HTML/SVG).

### Slide 3 of 5 — Two Datology numbers, two different measurements (the baselines the post cannot hold)
- **Visual mode:** Split-frame comparison, with mirrored panels.
- **Headline:** Two numbers, two different measurements
- **Body / content:**
  - Left panel: "6x less compute". What it measures: models trained on Studio-curated public datasets matched the largest baseline. Baseline: Datology's own 39-dataset public mix, scaled to 10T tokens. Source line: launch post, 2026-10-09.
  - Right panel: "under 20% of training compute". What it measures: the Thomson Reuters segment, matching the strongest public data baselines. Baseline and compute method: not public. Source line: webinar invite.
  - Footer: "Both are Datology's own figures, measured differently. The TR baseline isn't public yet."
- **Palette:** dark bg + white text + green #059669.
- **Source attribution:** Source: DatologyAI launch post (2026-10-09); DatologyAI webinar invite (2026).
- **Alt text:** Two side-by-side panels separating Datology's 6x public-data compute claim from its under-20%-compute Thomson Reuters claim, noting that the Thomson Reuters baseline isn't public yet.
- **Tool:** Claude design (HTML/SVG).

### Slide 4 of 5 — Who owns the eval tools now (2026 context the post compresses to one clause)
- **Visual mode:** Diagram / dated timeline.
- **Headline:** Who owns the eval tools now
- **Body / content:** A 2026 timeline, January to October, with these dated nodes:
  - Mar 9: OpenAI acquires PromptFoo.
  - Aug 13: Dynatrace announces its Arize acquisition.
  - Sep 24: Datadog publishes running TypeSafe's Jev inside Agent Observability.
  - Early Oct: Dynatrace–Arize closes.
  - Oct: Bedrock's judge list spans OpenAI, Anthropic and other models, all Bedrock-hosted. Mark this "per AWS docs, Oct 2026", because the docs are undated.

  ⟦VERIFY BEFORE RENDER: Langfuse → ClickHouse (Jan 16) and Galileo → Cisco/Splunk (May 22) are notion-prior and not re-verified in the Agents in NYC brief. Add them only after a primary-source check.⟧ Do not show deal prices.
- **Palette:** dark bg + white text + blue #1E40AF.
- **Source attribution:** Source: SiliconANGLE (2026-03-09); Dynatrace press release (2026-08-13); GovConWire / 01net (Oct 2026); Datadog blog (2026-09-24); AWS Bedrock docs (fetched 2026-10-24).
- **Alt text:** A 2026 timeline of evaluation-tool acquisitions and integrations, ending with Bedrock's multi-vendor judge list.
- **Tool:** Claude design (HTML/SVG).

### Slide 5 of 5 — Synthesis: what would settle each question
- **Visual mode:** Bold typography plus a compact grid, in documentarian mode (off-white on dark slate, no accent). It mirrors slide 1's type scale.
- **Headline:** What would settle it, room by room
- **Body / content:**
  - AWS NYC: a named baseline next to cost-per-correct-answer.
  - The Shortlist: a named owner for each open seat.
  - DatologyAI: a billing unit, or a third party reproducing a multiplier.
  - Daytona: a vendor stating where its own product stops.
  - Agents in NYC: a latency or cost-per-task number, and a take count for the robot.
  - Frontier Build: one class of change no agent may merge.
- **Palette:** off-white on dark slate, no accent.
- **Source attribution:** none (synthesis; no figures or quotes).
- **Alt text:** Six short lines naming, for each event, the observable evidence that would answer its open question.
- **Tool:** Claude design (HTML/SVG).

**Quality gate checks:**
- Arc fit: pass. This is a weekly roundup, so Arc 4. It is condensed because six events would mean eight slides; the deviation is noted above.
- Job differentiation: pass (map / questions / one claim pair / market context / evidence criteria).
- Frame parallelism: slide 3 panels are mirrored. Slides 1 and 5 share a type scale.
- Thumb test: pass. All headlines are 8 words or fewer. Slide 2 is the densest, so render at 48px+ for the question column and abbreviate if it squints at 375px.
- Source citations: pass on slides 1–4. Slide 4 has one verify-before-render item.
- Adds information, not repetition: pass. Talk-slot times, per-room questions, baseline composition, dated deal timeline and settle-criteria are all absent from the copy.
- Final slide earns the swipe: pass. It is synthesis, not housekeeping.

⟦carousel-link⟧

---
