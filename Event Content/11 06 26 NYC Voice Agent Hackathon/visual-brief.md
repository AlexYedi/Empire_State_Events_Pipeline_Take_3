# NYC Voice Agent Hackathon (Take2AI × Reach Capital) — Pre-Event Carousel Visual Brief (2026-11-06)

Source of record: Notion Content Draft "NYC Voice Agent Hackathon with Take2AI & Reach Capital — Pre-Event Post" (needs_review). Render not yet run.

## Visual Brief — 5-slide carousel (Arc: Arc 1 — Hook → Evidence → Mechanism → Counterpoint → CTA)

**Carousel thesis:** A voice agent passes or fails a difficult caller on one decision: who owns "the caller is done". The sponsor stack offers three owners, and every speed knob on them has a price.

**Slide count:** 5
**Aspect ratio:** 4:5 (1080x1350), LinkedIn carousel default
**Tool routing summary:** all slides → Claude design (HTML/SVG). No pictorial slides, so no Gemini.
**Palette (all slides):** dark slate ground #0F172A + white text #FFFFFF + ONE accent, Tech/AI blue #3B82F6. Signature acid green #8FE83A only as the name-mark underline in the footer, per the brand tokens. Page number bottom-right on every slide.

---

### Slide 1 of 5 — Hook: put the decision on the cover

- **Visual mode:** Bold typography card
- **Headline:** Who decides the caller is done?
- **Body / content:** Sub-line: "NYC Voice Agent Hackathon · Take2 AI × Reach Capital · Fri Nov 6". "done?" is set in the accent blue; everything else is white.
- **Palette:** dark bg + white text + #3B82F6
- **Source attribution:** none (no data point or quote)
- **Alt text:** A title card asking who decides when a phone caller has finished talking, for the NYC Voice Agent Hackathon on November 6.
- **Tool:** Claude design (HTML/SVG)

### Slide 2 of 5 — Evidence: make "difficult caller" concrete

- **Visual mode:** Framework / matrix (5 rows × 2 columns)
- **Headline:** Five ways a caller breaks an agent
- **Body / content:** Top strip, small caps: "Judged: interruptions · silence · curveballs". Columns: "The caller…" | "A pass looks like". Rows: (1) "Barges in mid read-back: 'no wait, Tuesday'" | "Stops talking, updates the slot, doesn't repeat what was cut". (2) "'Mm-hm', a cough, a door slam" | "Keeps talking, or resumes". (3) "Pauses to think: 'I'd like to book… um…'" | "Doesn't cut in". (4) "8–10 seconds of dead air" | "Reprompts, varies the second one, then ends politely". (5) "'Are you a robot? Can I talk to a human?'" | "Answers honestly, redirects once, offers a handoff or ends". The column headers are blue; the cells are white.
- **Palette:** dark bg + white text + #3B82F6
- **Source attribution:** "Criteria: event invite, Take2 AI × Reach Capital, 2026. Test rows: Alex's own pre-build test plan."
- **Alt text:** A table of five difficult-caller behaviours (barge-in, backchannel noise, a thinking pause, dead air, asking for a human) and what a passing voice agent does for each.
- **Tool:** Claude design (HTML/SVG)

### Slide 3 of 5 — Mechanism: three places to put one decision

- **Visual mode:** Diagram (pipeline with three callouts)
- **Headline:** Three places to put one decision
- **Body / content:** A left-to-right pipeline: PHONE → LIVEKIT ROOM → SPEECH-TO-TEXT → LLM → TEXT-TO-SPEECH → PHONE. Three numbered callouts, each in accent blue: (1) on SPEECH-TO-TEXT: "In the transcriber: Deepgram Flux end-of-turn". (2) a bracket under LIVEKIT ROOM: "In the framework: LiveKit turn detector + adaptive interruption". (3) a second, lower lane that replaces STT → LLM → TTS with one box: "In the model: Gemini Live API hears and speaks". Footer line: "Pick one owner. Two can step on each other."
- **Palette:** dark bg + white text + #3B82F6
- **Source attribution:** "Sources: Deepgram Flux docs; LiveKit turns docs; Google Gemini Live API docs, 2026."
- **Alt text:** A diagram of a phone voice-agent pipeline showing three alternative places the end-of-turn decision can live: the speech-to-text model, the LiveKit framework, or a single speech-to-speech model.
- **Tool:** Claude design (HTML/SVG)

### Slide 4 of 5 — Counterpoint: every speed knob has a price

- **Visual mode:** Single-number data viz (one dial + one stat callout)
- **Headline:** Every speed knob has a price
- **Body / content:** Top: a horizontal dial labelled "Deepgram Flux eot_threshold", scale 0.5 to 1.0, marker at "0.7 default". Left end label: "Faster, more cut-offs". Right end label: "Fewer cut-offs, slower". The legend sits above the dial. Bottom: stat callout "Can raise LLM calls 50–70%", with the label "if you add eager end-of-turn (starts the LLM before the caller is surely done)". Annotation: "Vendor-documented. Friday's test: a live phone call."
- **Palette:** dark bg + white text + #3B82F6 (the dial track is #94A3B8 grey so it stands off the dark ground)
- **Source attribution:** "Source: Deepgram Flux docs (vendor), 2026."
- **Alt text:** A dial showing Deepgram Flux's end-of-turn threshold from 0.5 to 1.0 with a 0.7 default, trading speed against cut-offs, and a callout that eager end-of-turn can raise LLM calls by 50 to 70 percent.
- **Tool:** Claude design (HTML/SVG)

### Slide 5 of 5 — CTA: hand the reader the decision

- **Visual mode:** Bold typography card
- **Headline:** Where would you put the turn?
- **Body / content:** Sub-line: "Transcriber · framework · model. Friday, NYC." Small footer line: "Shipped one on real calls? Tell me what broke first." Name-mark with the #8FE83A underline.
- **Palette:** dark bg + white text + #3B82F6
- **Source attribution:** none (no data point or quote)
- **Alt text:** A closing card asking readers where they would place the end-of-turn decision in a voice agent, and inviting builders to share what broke first on real calls.
- **Tool:** Claude design (HTML/SVG)

---

**Quality gate checks:**
- Arc fit: pass. The post turns on one question, its mechanism and its cost, so Arc 1 fits. Arc 3 (Before → After) was rejected because the April → November narrowing is already written out in the post, and Before/After frames would re-print it. Arc 4 is n/a: no named speakers are confirmed.
- Job differentiation: pass. Hook (the question), evidence (what a difficult caller does), mechanism (where the decision can live), counterpoint (what speed costs), CTA (the reader's call). No two jobs can be swapped.
- Frame parallelism (if Arc 2 or 3): n/a (Arc 1). Slides 1 and 5 share the typography-card frame.
- Thumb test per slide: pass. Every headline is 5–6 words, set at 48px or larger at 1080 wide. Slide 2's cells are short phrases, not paragraphs.
- Source citations: pass. Slides 2–4 carry source lines; slides 1 and 5 have no data.
- Adds information (not repetition): pass. Slide 2 adds the five concrete caller behaviours and their pass conditions (the post only names "a test table"). Slide 3 adds the pipeline geometry. Slide 4 adds the eot_threshold dial and its 0.7 default, which are not in the post. The OpenAI figures stay in the post only.
- Final slide earns the swipe: pass. It ends on the open decision, not housekeeping.
