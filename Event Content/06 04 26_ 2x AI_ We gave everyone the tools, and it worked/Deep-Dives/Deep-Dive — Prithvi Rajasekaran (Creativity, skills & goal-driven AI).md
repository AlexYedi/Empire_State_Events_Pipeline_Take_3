# Deep-Dive — Prithvi Rajasekaran (Creativity, skills & goal-driven AI)

> **Quote-accuracy note.** Verbatim lines are used only where the diarized ElevenLabs transcript is HIGH-confidence and the post-event brief banked them: *"every good piece of art is a remix of some other piece of art,"* the frontend-design-skill passage (*"something that I wrote… a set of instructions… make the model more creative"* / *"designing front ends that were like way better than what I was designing"*), and the last-mile passage (*"that last mile of human intuition, judgment, taste… that'll be the last thing to go"*). **ASR correction:** the transcript and one prior doc rendered the skill as "foreign design skill" / "cloud design" — it is the **frontend design skill** (corrected; cross-verified against Anthropic's published `frontend-design` skill, which Prithvi co-authored). The "vision / strategy / execution" stack and the "10× code = 10× QA" line are Prithvi's, verbatim-paraphrased. **Attribution guard:** the goal-driven-vs-task-driven and "GUI moved to the background" lines were spoken by **Brian Donohue**, not Prithvi — used here as supporting context and credited to Brian, not folded into Prithvi's quotes. The **Raptor 1/2/3** SpaceX slide is used only as a concept illustration of iterate-toward-simplicity; in the diarized transcript it is narrated by Brian, so it is NOT asserted as Prithvi's slide. The moderator is unnamed by design. **Names VERIFIED:** Prithvi Rajasekaran, Member of Technical Staff, Anthropic Labs; co-author of Claude's frontend-design skill (w/ Alexander Bricken); organizer of The AI Collective (formerly GenAI Collective) NYC chapter.

---

## 1. Deep-Dive Post (LinkedIn) — 2,698 / 3,000 characters

Ask most people what AI can't do and they say "be creative." An Anthropic engineer gave the most useful answer to that I've heard — by reframing the question.

At an AI Collective panel in NYC, Prithvi Rajasekaran (Anthropic Labs) pointed to a real book — Austin Kleon's "Steal Like an Artist" — and its claim that every good piece of art is a remix of some other piece of art.

His point: give a model a reference and ask it to remix, and you're "almost asymptotically approaching what real creativity can be." Creativity isn't a switch the model lacks. It's a framing problem on our side.

That reframe sits on top of three ideas worth stealing:

1) The written skill is the unit of capability.

The line that stopped me: Anthropic's frontend design ability, he said, comes largely from a frontend design skill — "something that I wrote… a set of instructions to make the model more creative." And then: he watched the model design front ends "way better than what I was designing."

Sit with that. The leverage wasn't a bigger model or a clever one-off prompt. It was a written artifact — a skill — that any number of people can now reuse. Capability got encoded once and distributed. If you're still optimizing prompts you retype every session, you're working a layer below where the value is.

2) Goal-driven, not task-driven.

Prithvi's frame for where the value sits: vision → strategy → execution. AI has made execution close to trivial, so the bottleneck — and the value — moves up the stack. You stop issuing granular tasks and start shaping the goal. (Brian Donohue, on the same panel, called this the shift to working with models "in a goal-driven way, not a task-driven way." Same idea, two seats.)

3) The last mile is taste.

The cost of producing things collapses, but, he noted, "if you're producing ten times the volume of code, there's ten times the QA." The work doesn't vanish — it relocates downstream to judgment. His closing read: models will keep getting good at what's "easy to verbalize rigorously," but "that last mile of human intuition, judgment, taste — that'll be the last thing to go."

Put together, it's a quiet, optimistic playbook:

→ Frame creative work as remix-from-reference, not generate-from-nothing.
→ Encode what works as a reusable skill, not a disposable prompt.
→ Spend your scarce attention on the goal and the taste — not the keystrokes.

The uncomfortable, freeing version: execution is getting cheap. What you choose to make, and whether it's any good, is the part that's still yours.

Credit to Prithvi Rajasekaran (Anthropic Labs), shared on a panel hosted by The AI Collective NYC.

#AI #ProductThinking #Creativity #AgenticAI #ClaudeCode

---

**First-comment block (sources — keeps the post body under budget):**

> "Steal Like an Artist," Austin Kleon (2012). · Anthropic's frontend-design skill (co-authored by Prithvi Rajasekaran): github.com/anthropics/claude-code/tree/main/plugins/frontend-design · On harness design: anthropic.com/engineering/harness-design-long-running-apps · Ideas shared by Prithvi Rajasekaran (Anthropic Labs) on a panel hosted by The AI Collective NYC, June 2026.

---

## Visual Brief — 4-slide carousel (Arc: 1 — Hook → Evidence → Mechanism → CTA)

**Carousel thesis:** Creativity with models isn't a missing switch — it's a framing problem; the leverage is the reusable *skill*, the value has moved up the vision→strategy→execution stack, and taste is the last thing left to humans. (Slideless speaker — render the ideas as concept cards, NOT quote echoes of the post.)

**Slide count:** 4
**Aspect ratio:** 4:5 (1080×1350) — LinkedIn carousel default
**Tool routing summary:** All slides → Gamma (`format: "social"`, `4x5`, Stratos dark theme, `imageOptions.source: "noImages"`). Slides 1 & 4 are typography; Slides 2 & 3 are diagram/stack. Export as one PDF for the LinkedIn document post.

---

### Slide 1 of 4 — Hook: reframe the creativity question

- **Visual mode:** Bold typography card
- **Headline:** "Creativity is a framing problem."
- **Body / content:** Sub-line, smaller: "Don't ask the model to create from nothing. Give it a reference and ask it to remix." Tiny tag bottom-left: "Prithvi Rajasekaran · Anthropic Labs · The AI Collective NYC."
- **Palette:** dark slate bg + off-white text + blue accent (#1E40AF) on the word "framing"
- **Source attribution:** "Concept: 'Steal Like an Artist,' A. Kleon, cited by P. Rajasekaran, 2026"
- **Alt text:** A title card reading "Creativity is a framing problem," introducing the idea that models create best by remixing a reference.
- **Tool:** Gamma (typography)

### Slide 2 of 4 — Evidence: the skill is the unit of capability

- **Visual mode:** Diagram (three-rung ladder, value rising)
- **Headline:** "Prompt → Skill → Reuse"
- **Body / content:** Three ascending rungs, lowest to highest:
  - **One-off prompt** — retyped every session · leverage = 0
  - **Written skill** — instructions encoded once · "something I wrote to make the model more creative"
  - **Distributed reuse** — anyone runs the same skill · capability compounds
  Caption under ladder: "The leverage isn't a cleverer prompt. It's the artifact you can reuse." Small note: the frontend-design skill let the model out-design its own author.
- **Palette:** dark bg + white labels + blue accent (#1E40AF) on "Written skill"
- **Source attribution:** "Source: P. Rajasekaran, Anthropic Labs, 2026"
- **Alt text:** A three-rung ladder rising from a disposable one-off prompt, to a written skill, to distributed reuse — showing where capability compounds.
- **Tool:** Gamma (diagram)

### Slide 3 of 4 — Mechanism: where the value moved

- **Visual mode:** Diagram (vertical stack with an upward value arrow)
- **Headline:** "The value moved up the stack"
- **Body / content:** Three stacked bands, with an arrow pointing UP the left edge labeled "where your attention belongs":
  - **VISION** — what to make · taste · judgment ← scarce
  - **STRATEGY** — how it fits, novel synthesis · rising
  - **EXECUTION** — writing the code · now near-trivial
  Right-side annotation aligned to EXECUTION: "10× the output = 10× the QA — the work relocates downstream." Footer: "Execution got cheap. Goal-setting and taste didn't."
- **Palette:** dark bg + white text + amber accent (#D97706) on the VISION band and the upward arrow (signals where value/scarcity sits)
- **Source attribution:** "Source: P. Rajasekaran, Anthropic Labs, 2026"
- **Alt text:** A vision-strategy-execution stack with an upward arrow — execution is now trivial, so value and attention move up toward strategy and vision.
- **Tool:** Gamma (diagram)

### Slide 4 of 4 — CTA: the question that earns the swipe

- **Visual mode:** Bold typography card
- **Headline:** "If execution is free, what's scarce?"
- **Body / content:** Sub-line: "His answer: 'the last mile of human intuition, judgment, taste — that'll be the last thing to go.' So what are you spending yours on?" Small credit line: "Prithvi Rajasekaran · Anthropic Labs."
- **Palette:** dark slate bg + off-white text + amber accent (#D97706) on "scarce"
- **Source attribution:** "Quote: P. Rajasekaran, Anthropic Labs, 2026"
- **Alt text:** A closing card asking "If execution is free, what's scarce?" with the answer being human taste and judgment.
- **Tool:** Gamma (typography)

---

**Quality gate checks:**
- Arc fit: pass — single-thesis post (creativity-as-remix → skill-as-unit → value-up-the-stack → taste); Arc 1 mirrors the post's hook→evidence→mechanism→CTA structure.
- Job differentiation: pass — Slide 2 (the skill ladder) and Slide 3 (the value stack) render two distinct ideas; neither can stand in for the other.
- Frame parallelism: n/a (Arc 1).
- Thumb test per slide: pass — every headline ≤ 6 words; diagrams have ≤ 3 bands/rungs.
- Source citations: pass — every slide carries a source line.
- Adds information (not repetition): pass — the carousel renders the prompt→skill→reuse ladder and the vision/strategy/execution value-arrow as *diagrams*; the post describes them in prose but the visual is the legible structure. No quote-card echoes (this speaker was slideless, so the brief is concept-led by design).
- Final slide earns the swipe: pass — closes on a question, not housekeeping.

---

## Radar Note (job-search / positioning)

Prithvi is a double node: Member of Technical Staff at **Anthropic Labs** (he co-authored Claude's published frontend-design skill) **and** organizer of **The AI Collective NYC** (the rebranded GenAI Collective — now 70k+ members across 25+ chapters), a core network for Alex. This post amplifies his ideas genuinely, in a curator's voice — no pitch — and demonstrates fluency in AI-native *product* thinking: the skill as the unit of capability, value migrating up the vision→strategy→execution stack, taste as the durable human edge. That's exactly the vocabulary AI-native product/GTM hiring managers use, and it positions Alex as someone who can talk shop with an Anthropic engineer, not just about AI. Bonus thread for conversation: the "encode it as a reusable skill, not a one-off prompt" lesson is literally how Alex's own pipeline is built — credible, specific common ground with both Prithvi and the Collective.

---

## Connection Note (≤200 chars, talk-anchored)

Your AI Collective panel point — the frontend design skill you wrote is where capability lives, not the prompt — reframed how I think about AI leverage. Following the Anthropic Labs work.

*(Character count: 187 / 200)*
