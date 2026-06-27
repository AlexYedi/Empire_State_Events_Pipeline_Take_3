# Deep-Dive — Kenny Tsai (The End-to-End ABM Bot)

> **Quote-accuracy note:** Quotations below are verbatim from the HIGH-confidence quote bank in the POST-EVENT BRIEF (§6.5, §7) and the ElevenLabs transcript of Kenny's span. The architecture (Signals In → 4 agents → Outbound, the Supabase spine, the funnel, the cadence, the word budget) is transcribed from Kenny's own slides — `PXL_20260603_234703820.jpg` (system end-to-end), `…836595.jpg` (four agents), `…953860.jpg` (account brief + Online Stalker), `…300392.jpg` (cadence), `…730429.jpg` (tools). The slides are the authoritative spellings (CoverForce · HeyReach · Instantly · Supabase · Clay), since ASR mangled several of them. No claim is asserted that isn't sourced to Kenny or his slides (CLAUDE.md Rule 12). One verbatim discrepancy is flagged in §5.

---

## 1. The Deep-Dive Post (LinkedIn)

Most "AI for outbound" demos are a better spam cannon. This one was the opposite — the cleanest reference architecture I've seen for agentic GTM.

Kenny Tsai is the GTM engineer at CoverForce (insurance-tech, Insight Partners portfolio). He sells to billion-dollar US insurance brokers — a tiny set of huge accounts. The job AEs hate: hunting LinkedIn to find the ~12 people inside a giant org actually worth contacting. So he built a bot for it. Setup that took 4–5 hours now takes 10–15 minutes of prompting per company.

The architecture is worth copying exactly, because every part has one job:

SIGNALS IN — what the bot reads:
Gong transcripts · HubSpot pipeline + replies · Notion ICP definitions · web (financials, news) · LinkedIn. Everything lands in one Supabase DB, deliberately separate from HubSpot so testing never pollutes the CRM. One account = one row.

FOUR AGENTS — the middle:
1. Research — *why* target them. Builds the account brief everything runs from. Its sharpest piece is the "Online Stalker": a per-contact monitor watching connections ("do we know anybody connected?"), LinkedIn activity, events, quotes, news — a play with "very high conversion rates to meetings."
2. Contact Selection — *who*. Scores the buying committee and narrows the list. On Aon (~60,000 people), seniority filters give ~15,000 — useless for a BDR. VP+ ≈ 3,000. The bot ranks it to 12: "We narrowed sixty thousand contacts down to twelve, just through a click of a button."
3. Sequence — *what*. Under 50 words, one markdown playbook, zero templates reused. Each message composed live: buyer type × ICP segment → pull the angle → signal as the hook.
4. Routing — *how*. Picks channel and sender; the AE owns the thread; CEO-to-CEO outreach routes through the founder.

OUTBOUND OUT — where it lands:
Instantly (email) · HeyReach (LinkedIn) · Slack (AE approvals) · gifting. Cadence: 10 touches over ~22 days (4 email · 3 LinkedIn · 3 gift), staggered (~4 contacts/account/day, then a pause) so you don't bombard an account and tank your reputation.

Two things make it work, both the opposite of "spray and pray":

The hook is never templated. "Every email opens with something specific and recent — not a templated hook." Signal-as-first-line, every time.

And a human stays in the loop. AEs approve, pause, or edit the whole sequence in Slack. Nobody claimed full autonomy — the bot does the grunt work; the human keeps the judgment.

The build: all of it in Claude Code, wiring APIs together. His tell on the skills layer — "I don't know what it's doing, but I just imagine it works."

Credit where it's due: this is Kenny Tsai's system at CoverForce. I keep coming back to it because it's a settled blueprint — context store, connectors, scoped agents, a human approval loop. The differentiation isn't the agents. It's the signal you feed them.

If you were building this, which agent would you trust to run unsupervised first — and which one never?

#GTM #AgenticAI #ABM #AIengineering

---

## 2. Visual Brief — 5-slide carousel (Arc: Arc 1 — Hook → Evidence → Mechanism → CTA)

**Carousel thesis:** A working agentic-ABM system is a settled architecture — signals in, four scoped agents, outbound out, human in the loop — and the centerpiece is the 60,000→12 funnel that proves the value is in *narrowing*, not blasting. A reader should be able to screenshot the system diagram and the funnel and map them onto their own stack.

**Slide count:** 5
**Aspect ratio:** 4:5 (1080x1350) — LinkedIn carousel default
**Tool routing summary:** Slides 1, 5 → Canva typography cards; Slide 2 → single-number funnel data viz (Gamma/Canva); Slides 3–4 → labeled flow / matrix diagrams (Canva typography + shapes, real editable text labels — NEVER a generated raster, labels would garble). Default generator: Gamma `format: "social"`, dark theme (Stratos), `imageOptions.source: "noImages"`. Accent = blue (Tech / AI / agents).

---

### Slide 1 of 5 — Hook: name what makes this different

- **Visual mode:** Bold typography card
- **Headline:** "Not a spam cannon. A scalpel."
- **Body / content:** Sub-line beneath headline: "How CoverForce built an AI ABM system that narrows a 60,000-person account to the 12 people worth contacting." Small kicker at top: "Agentic GTM, end to end." No diagram yet — this is the book cover.
- **Palette:** dark slate bg (#0F172A) + white text + blue accent (#1E40AF) on "A scalpel."
- **Source attribution:** "System: Kenny Tsai, CoverForce, 2026"
- **Alt text:** A title card reading "Not a spam cannon. A scalpel," describing an AI ABM system that narrows a 60,000-person account to the 12 people worth contacting.
- **Tool:** Canva

### Slide 2 of 5 — Evidence: the funnel that proves the value is in narrowing

- **Visual mode:** Single-number / funnel data viz
- **Headline:** "60,000 → 12"
- **Body / content:** A descending funnel, four steps, with the count beside each tier:
  - 60,000 — everyone at Aon (one of the largest US brokers)
  - 15,000 — after seniority filters ("useless for a BDR")
  - 3,000 — VP and above
  - 12 — the ranked contacts the bot hands to the AE
  Annotation beneath: "Setup that took 4–5 hours now takes 10–15 minutes." The "12" rendered largest, in blue; everything else white/gray.
- **Palette:** dark slate bg (#0F172A) + white text + blue accent (#1E40AF) on the final "12"
- **Source attribution:** "Source: Kenny Tsai, CoverForce, 2026 (Aon example)"
- **Alt text:** A four-step funnel narrowing 60,000 people at Aon to 15,000, then 3,000 VP-plus, then 12 ranked contacts, with a note that setup dropped from 4–5 hours to 10–15 minutes.
- **Tool:** Gamma / Canva

### Slide 3 of 5 — Mechanism: the system, end to end (the centerpiece)

- **Visual mode:** Diagram (labeled three-column flow)
- **Headline:** "Signals in. Agents. Outbound out." (small header above the diagram)
- **Body / content:** Three labeled columns connected by arrows, mirroring Kenny's slide:
  - **SIGNALS IN (what the bot reads):** Gong — call transcripts · HubSpot — pipeline + replies · Notion — ICP definitions · Web signals · LinkedIn
  - **AGENTS (the work):** Research · Contact Selection · Copywriting · Routing
  - **OUTBOUND OUT (where it lands):** Instantly — email · HeyReach — LinkedIn · Slack — AE approvals · Gifting / Direct Mail
  Footer strip across the bottom: "Data spine: everything flows into one Supabase DB — separate from the CRM. One account = one row." Keep all labels as REAL editable text. This slide is the map readers will screenshot.
- **Palette:** dark slate bg (#0F172A) + white labels; the center AGENTS column in blue (#1E40AF) to mark it as the engine; SIGNALS / OUTBOUND columns in muted slate.
- **Source attribution:** "System diagram: Kenny Tsai, CoverForce, 2026"
- **Alt text:** A three-column flow diagram: signals in (Gong, HubSpot, Notion, web, LinkedIn) feed four agents (Research, Contact Selection, Copywriting, Routing) that send outbound via Instantly, HeyReach, Slack approvals, and gifting, with all data flowing into one Supabase database.
- **Tool:** Canva (typography + shapes; real text labels)

### Slide 4 of 5 — Mechanism continued: four agents, one job each

- **Visual mode:** Framework / matrix (2×2)
- **Headline:** "Four agents, one job each."
- **Body / content:** A 2×2 grid, one cell per agent — each cell = agent name + the single question it answers + its one defining move:
  - **Research — *why*:** builds the account brief; runs the "Online Stalker" per-contact monitor
  - **Contact Selection — *who*:** scores the buying committee; ranks 1,000+ down to 12
  - **Sequence — *what*:** under 50 words, one playbook, zero templates; signal as the hook
  - **Routing — *how*:** picks channel + sender; AE owns the thread; CEO-to-CEO via the founder
  Footer line: "A human approves, pauses, or edits the whole sequence in Slack. Nobody runs unsupervised."
- **Palette:** dark slate bg (#0F172A) + white text + blue accent (#1E40AF) on the four *why/who/what/how* tags
- **Source attribution:** "After Kenny Tsai, CoverForce, 2026"
- **Alt text:** A 2x2 grid of the four agents — Research answers why, Contact Selection answers who, Sequence answers what, Routing answers how — with a note that a human approves, pauses, or edits every sequence in Slack.
- **Tool:** Canva (typography + shapes)

### Slide 5 of 5 — CTA: the question back to the reader

- **Visual mode:** Bold typography card
- **Headline:** "The agents are settled. The signal isn't."
- **Body / content:** Sub-line: "Context store + connectors + scoped agents + a human approval loop. That architecture is now a blueprint." Then, smaller: "The edge isn't the agents — it's the quality of the signal you feed them." Closing prompt: "Which agent would you trust to run unsupervised first — and which one never?"
- **Palette:** dark slate bg (#0F172A) + white text + blue accent (#1E40AF) on "The signal isn't."
- **Source attribution:** "System: Kenny Tsai, CoverForce"
- **Alt text:** A closing card stating the agent architecture is now a settled blueprint, that the edge is signal quality not the agents, and asking which agent the reader would trust to run unsupervised first and which never.
- **Tool:** Canva

---

**Quality gate checks:**
- Arc fit: pass — single-thesis post grounded in one data point (the 60,000→12 funnel) with a mechanism (the system + the four agents); Arc 1 mirrors hook→evidence→mechanism→CTA.
- Job differentiation: pass — S1 names what's different, S2 proves it with the funnel, S3 maps the whole system, S4 decomposes the engine, S5 turns it back on the reader. No two jobs swappable.
- Frame parallelism (Arc 2/3): n/a — not a comparison arc.
- Thumb test per slide: pass — S1/S2/S5 are short bold headlines. Flag: S3 (system diagram) and S4 (2×2) are denser by design — they are the screenshot-and-keep slides; acceptable as the deliberate "study me" pair, kept legible with real text labels and a single accent.
- Source citations: pass — every stat/quote/diagram slide carries a Kenny / CoverForce attribution line.
- Adds information (not repetition): pass — S3 renders the full end-to-end system the post only describes in prose; S4 adds the why/who/what/how decomposition + the HITL footer; S2 visualizes the funnel as a shape, not a re-typeset line.
- Final slide earns the swipe: pass — closes on the "architecture is settled, signal is the edge" thesis + a reader prompt, not housekeeping.

---

## 3. Radar Note (CoverForce visibility + Alex's GTM-engineer positioning)

- **The role-fit play:** This is the post where Alex's positioning toward GTM-engineer / AI-native GTM roles does the most work. Kenny's "GTM engineer" build at CoverForce is *exactly* the role Alex is moving toward — and CoverForce is an Insight Partners portfolio company. Teaching his system fluently (signals → scoped agents → outbound, with the Supabase spine and the HITL loop named correctly) demonstrates Alex can read, decompose, and explain a production agentic-GTM architecture — not just admire it. That's the hiring signal, delivered implicitly.
- **The amplification, not the hot take:** The post distributes Kenny's IP straight — credits him and CoverForce by name, ships a clean render of his own system diagram and funnel — so it reads as genuine amplification a builder notices and often engages with, not name-riding. CoverForce, Insight Partners, and the NYC GTM community all sit in the visibility radius.
- **The follow-through:** If Kenny (or anyone at CoverForce / Insight) engages, the connection note below is the natural next touch — talk-anchored, zero ask. The implicit message is peer-to-peer: "I build and reason about these systems too," not "hire me."

---

## 4. Connection-Request Note (≤200 chars, talk-anchored)

> Kenny — your end-to-end ABM bot talk at the NYC GTM+AI Masterclass was the most complete build of the night. The 60k→12 funnel + signal-as-hook discipline stuck with me. Would value connecting.

*(195 characters, incl. spaces — within the 200-char free-tier cap.)*

---

## 5. Final Summary

- **What this is:** An evergreen deep-dive teaching Kenny Tsai's end-to-end ABM bot at CoverForce — Signals In → four scoped agents → Outbound Out, on a Supabase spine, with a Slack human-in-the-loop — so a reader can map the architecture onto their own stack. Framework-first, no event-timing urgency; speaker + company credited throughout. This is the role-fit post: it shows Alex's fluency in agentic GTM systems, with CoverForce / Insight visibility as the upside.
- **Deliverables:** the LinkedIn post + a 5-slide Arc-1 carousel (centerpieces: the end-to-end system diagram in S3 and the 60,000→12 funnel in S2, both transcribed from Kenny's slides) + a radar / positioning note + a 195-char talk-anchored connection request.
- **Post character count:** 2,999 / 3,000 (within budget — hashtags inline, no first-comment block needed). This is at the ceiling: any edit on publish should trim, not add. Easiest cut if needed: drop the "staggered" parenthetical in the OUTBOUND line.
- **[VERIFY] flags:**
  1. **Verbatim discrepancy on the "skills" quote.** The task brief lists it as *"This is Claude Code on Pocket… I also don't ever look at the skills. I don't know what it's doing, but I just imagine it works."* The ElevenLabs transcript of the actual span reads: *"This is all through Claude Code… I also don't ever look at the skills. I don't know what it's doing. But I just tap and it works."* The post uses the conservative, transcript-grounded fragment **"I don't know what it's doing, but I just imagine it works"** — but "imagine it works" matches the brief, not the raw ASR ("tap and it works"). Confirm the exact wording Alex wants before publishing, OR soften to a paraphrase. (ASR is unreliable here; "Pocket" appears to be a mishearing.)
  2. **"Online Stalker" framing.** It's Kenny's own slide label (`…953860.jpg`), used as such — but flag that the word "stalker" in a public post is his term, not Alex's editorializing; kept in quotes to make that clear.
  3. **The funnel numbers** (60,000 / 15,000 / 3,000 / 12, Aon) are from Kenny's talk + slide and the brief's data table — presented as his example, not independently verified.
  4. **"CEO-to-CEO routes through the founder"** — the brief names Cyrus Karai, CoverForce CEO/co-founder (web-verified). The post says "the founder" rather than naming him, to avoid putting a third party's name in public copy without need; confirm if Alex prefers the name.
