# Deep-Dive — Eric Nowoslawski (Build your first AI employee)

> **Quote-accuracy note.** Every verbatim quote below is drawn from the POST-EVENT BRIEF's HIGH-confidence quote bank (reconciled against the slide photos). Eric's three slides (Context / Connection / Creation) were read directly and match the brief. MED-confidence material is paraphrased, not quoted. Nothing is fabricated. The "Hermes / OpenClaw" harness names and "trigger.dev" are reproduced as Eric stated them on the night; framework attribution is to Eric Nowoslawski / Growth Engine X throughout. See `[VERIFY]` flags in the final hand-off note.

**Type:** Evergreen deep-dive (LinkedIn) — teach one presenter's framework
**Source event:** NYC GTM + AI Masterclass #5 (2026-06-03), Insight Partners HQ
**Presenter:** Eric Nowoslawski — Founder, Growth Engine X (one of the earliest Clay practitioners)
**Framework:** "Build your first AI employee" — Context → Connection → Creation
**Author voice:** Alex — senior B2B GTM/revenue practitioner, documentarian

---

## 1. Deep-Dive Post (2,861 / 3,000 chars)

Most people meet a frontier model the way they'd meet a genius temp: hand it one instruction and wait for magic. Then they're disappointed.

Eric Nowoslawski — founder of Growth Engine X, one of the earliest Clay practitioners — put it bluntly at a recent NYC GTM + AI session: "If they're not doing what you want, that's your fault. Your business is not that complicated."

His reframe is the unlock: an AI agent isn't a tool, it's a hire. You front-load the training once, and it never sleeps, never takes PTO, never leaves for a competitor. His own proof point: "I accidentally cut my team by 50%, and we're sending more emails, because I made an AI employee."

Here's how he builds one. Three steps — Context, Connection, Creation.

1) CONTEXT — build the company brain.
The model is only as good as the knowledge you give it. Collect how your company thinks, sells, and decides: SOPs, ICP definitions, campaign examples, decision rules, examples of great work. Point it at what you already have — call recordings, Slack, old emails — and prompt: "make a company brain in markdown." Don't over-organize it. A 1M-token window holds roughly the Bible in words; most companies have less context than that. Let the model file itself.

2) CONNECTION — give it access to where work happens.
Wire it into meetings, Slack, CRM, and email — read-only first, expand after it earns trust. Two rules worth stealing: avoid brittle automation in v1 (no live spreadsheet edits, no browser automation yet), and never hand an agent your API keys — route them through a service like trigger.dev so the keys live there, not in the agent.

3) CREATION — the suggest-then-approve loop.
This is where the work is, and where the discipline lives. A new meeting recording lands → the agent pulls the transcript, reads the company brain, and *suggests* a next action. A human approves, tweaks, or rejects. Feedback is saved for next time. Eric calls these human checkpoints "meat gates" — copy never reaches a customer without passing one.

The detail that makes it work: an adversarial pass. "Whenever you make a skill, try to make an adversarial skill — pretend this is the worst idea in the world and find every problem." Models flatter you by default; the adversarial step kills the sycophancy before it ships.

The bar he holds the output to is the whole philosophy: "I want to send the same message I would send if I manually researched somebody's company and them personally for 10 minutes."

Notice what's NOT automated: the judgment. Every demo of a working AI employee I've seen keeps a human in the loop. The frontier isn't full autonomy — it's a tireless apprentice you actually trained.

Context. Connection. Creation. You can start the first two tomorrow.

Framework credit: Eric Nowoslawski, Growth Engine X.

#AIagents #GTM #GrowthEngineX #AInative #SalesEngineering

---

## 2. Visual Brief — 5-slide carousel (Arc: 1 — Hook → Evidence → Mechanism → CTA)

**Carousel thesis:** An AI employee is a hire you train once, wired into where work happens, supervised through a suggest→approve loop — Eric's three slides redrawn as one buildable system, not three disconnected diagrams.

**Why this arc, not Arc 4:** The centerpiece is Eric's three on-stage diagrams (Company Brain bullets, the hub-and-spoke connection map, the 6-step suggest→approve flow). Arc 1 lets the carousel *render the architecture* — it adds the diagrams the post can only describe in prose. Per the visual-briefs Arc-4 guard, a quote-card-per-step carousel would just re-print the post; these slides instead carry the structure the copy can't.

**Slide count:** 5
**Aspect ratio:** 4:5 (1080x1350) — LinkedIn carousel default
**Accent color:** blue (tech / AI / agents) — #1E40AF, on dark slate (#0F172A) background, white text
**Tool routing summary:** All 5 slides → **Gamma** (`format: "social"`, `cardOptions.dimensions: "4x5"`, theme Stratos, `imageOptions.source: "noImages"`, `additionalInstructions`: "render the labeled diagrams exactly; turn the three-step framework into clean boxes-and-arrows; no stock imagery"). Slides 2–4 are label-dependent diagrams — if Gamma garbles labels, fall back to Canva typography + shape layout (NEVER a single generated image; labels must be real text).

---

### Slide 1 of 5 — Hook: reframe the agent as a hire

- **Visual mode:** Bold typography card
- **Headline:** "An AI agent isn't a tool. It's a hire."
- **Body / content:** Sub-line beneath, smaller: "Front-load the training once. It never sleeps, never takes PTO, never leaves for a competitor." Bottom strip: "Build your first AI employee — in 3 steps."
- **Palette:** dark slate bg + white text + blue accent on the word "hire"
- **Source attribution:** "Framework: Eric Nowoslawski, Growth Engine X · 2026"
- **Alt text:** Title card stating an AI agent is a hire, not a tool, introducing a three-step framework for building an AI employee.
- **Tool:** Gamma (fallback: Canva typography)

### Slide 2 of 5 — Step 1, Context: the company brain (renders Slide 4 of Eric's deck)

- **Visual mode:** Framework / diagram — a labeled "brain" intake box
- **Headline:** "Step 1 — Context: build the company brain"
- **Body / content:** A single rounded container labeled "COMPANY BRAIN (markdown)" with five feeder chips pointing in: "SOPs & operating principles," "ICP & client context," "Campaign + sales messaging," "Reporting templates & decision rules," "Examples of great work." Small caption under the box: "Start with what you have: call recordings, Slack, old emails. ~1M tokens ≈ the Bible in words — let the model organize itself."
- **Palette:** dark slate bg + white text + blue accent on the COMPANY BRAIN container border
- **Source attribution:** "Source: Eric Nowoslawski, Growth Engine X · 2026"
- **Alt text:** Diagram showing five knowledge sources feeding into a single markdown company-brain store.
- **Tool:** Gamma (fallback: Canva typography + shapes — labels must be real text)

### Slide 3 of 5 — Step 2, Connection: hub and spoke (renders Slide 5 of Eric's deck)

- **Visual mode:** Diagram — hub-and-spoke
- **Headline:** "Step 2 — Connection: wire it to where work happens"
- **Body / content:** Center hub node labeled "AGENT HARNESS." Six spokes radiating out, each a labeled node: "Meetings," "Slack," "CRM," "Email," "Company notes," "Skills & code." Overlay tag on the spokes: "READ-ONLY FIRST." Two caption lines below: "Expand access after it earns trust." / "Avoid brittle automation in v1. Never give the agent your API keys — route them through a key service (e.g. trigger.dev)."
- **Palette:** dark slate bg + white text + blue accent on the central hub node
- **Source attribution:** "Source: Eric Nowoslawski, Growth Engine X · 2026"
- **Alt text:** Hub-and-spoke diagram with a central agent harness connected to six read-only work systems.
- **Tool:** Gamma (fallback: Canva typography + shapes — labels must be real text)

### Slide 4 of 5 — Step 3, Creation: the suggest→approve loop (renders Slide 6 of Eric's deck)

- **Visual mode:** Diagram — numbered vertical flow with a feedback loop
- **Headline:** "Step 3 — Creation: suggest, then approve"
- **Body / content:** Six numbered steps top to bottom: "01 New recording detected → 02 Pull transcript + identify context → 03 Read company brain + relevant skills → 04 Suggest the next action → 05 Human approves, tweaks, or rejects → 06 Save feedback for next run." A curved arrow returns from 06 back to 01 (the loop). Callout box beside step 05: "The 'meat gate' — copy never reaches a customer without passing a human."
- **Palette:** dark slate bg + white text + blue accent on step 05 (the human gate) and the return arrow
- **Source attribution:** "Source: Eric Nowoslawski, Growth Engine X · 2026"
- **Alt text:** Six-step vertical workflow from new recording to saved feedback, with a human-approval gate at step five and a loop back to the start.
- **Tool:** Gamma (fallback: Canva typography + shapes — labels must be real text)

### Slide 5 of 5 — CTA: what's not automated

- **Visual mode:** Bold typography card
- **Headline:** "What's not automated? The judgment."
- **Body / content:** Sub-line: "The frontier isn't full autonomy — it's a tireless apprentice you actually trained." Bottom strip, three words spaced as a sequence: "Context → Connection → Creation. Start the first two tomorrow."
- **Palette:** dark slate bg + white text + blue accent on "judgment"
- **Source attribution:** "Framework: Eric Nowoslawski, Growth Engine X · 2026"
- **Alt text:** Closing card stating that judgment stays human, restating the three-step Context-Connection-Creation framework.
- **Tool:** Gamma (fallback: Canva typography)

---

**Quality gate checks:**
- Arc fit: pass — single-thesis framework post; Arc 1 lets the three deck diagrams lead.
- Job differentiation: pass — hook / brain intake / connection map / approval loop / CTA are each distinct.
- Frame parallelism: n/a (not Arc 2/3); slides 2–4 share the diagram aesthetic, slides 1 & 5 share the typography frame.
- Thumb test per slide: pass — each headline ≤ 8 words; diagrams use ≤ 6 labeled nodes.
- Source citations: pass — every slide carries the Growth Engine X attribution.
- Adds information (not repetition): pass — the carousel renders Eric's three diagrams (architecture the post only describes in prose); no quote re-printing.
- Final slide earns the swipe: pass — lands on the "judgment stays human" synthesis, not housekeeping.

---

## 3. Radar Note (speaker / company visibility + peer-fit)

**For Alex's reference — the strategic "why this post" in 3 lines.**

- **Amplify:** Eric Nowoslawski / Growth Engine X — one of the earliest Clay practitioners and among the sharpest public voices on AI-native outbound. This post leads with his framework and credits him + the company by name (no urgency, no "I attended last week"), so it reads as genuine value that surfaces on his and GEX's radar over time.
- **Peer-fit (strongest of the night):** Eric's stack — Claude + Clay, markdown company brain, skills, a suggest→approve human-in-the-loop — is a near-exact overlap with what Alex already builds (the Empire State pipeline: Claude skills, company-brain context store, MCP connectors, human-review gates). The post demonstrates fluency with his exact architecture rather than asserting it, positioning Alex as a practitioner-peer.
- **Posture:** curator/peer, not "hire me." The signal is "I build this too and can teach it cleanly" — which is the credential that travels in this small NYC GTM-engineering circle.

---

## 4. Connection Note (≤200 chars, talk-anchored)

> Your "build your first AI employee" framework at the GTM + AI Masterclass was the sharpest of the night — Context→Connection→Creation. I build on the same Claude + Clay shape. Would value connecting.

**Char count:** 199 / 200 ✅ (free-tier connection-request cap)
