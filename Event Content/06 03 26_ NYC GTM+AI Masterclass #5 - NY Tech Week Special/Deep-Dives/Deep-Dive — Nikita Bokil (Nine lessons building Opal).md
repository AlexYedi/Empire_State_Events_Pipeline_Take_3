# Deep-Dive — Nikita Bokil (Nine lessons from building Opal)

> **Quote-accuracy note.** Two quotes are used verbatim, both HIGH-confidence from the brief: *"Context is king, context is queen"* (paraphrased/attributed loosely in the post as "context is king, context is queen") and *"Treat reliability as a software problem… so quality is provable, not vibes"* (rendered as the post's spine). All numbers (SLOs, volume tiers, $400M ARR, ~1,000 marketers) are transcribed directly from the slide photos, which override ASR. **Name VERIFIED:** "Nikita Bokil" is confirmed via her LinkedIn (linkedin.com/in/nbokil — "Building Opal AI to supercharge marketing") and third-party listings; title varies across sources (Principal/Sr. Principal PM on Opal AI per ZoomInfo/The Org), so the post uses the safe framing "Nikita Bokil's team" / "the Optimizely Opal team" rather than asserting an exact title.

---

## 1. Deep-Dive Post (LinkedIn) — 2,568 / 3,000 characters

Most teams ship an AI agent the way they ship a demo: it works on stage, so it works. Then it hits 1,000 users and you have no idea if it's still working.

At Optimizely (~$400M ARR), Nikita Bokil's team spent two years building Opal — an enterprise agent harness for ~1,000 marketers, in an environment where everything an agent does carries the brand and passes legal, compliance, and product sign-off.

The lesson I keep coming back to isn't about prompts or models. It's the one most AI conversations skip:

Reliability is engineering, not vibes.

Her team adapted the SRE playbook (the discipline that keeps software systems up) to agents. Three moves:

1. Agent SLOs. Beyond uptime, measure what matters: tool_success ≥ 95%, thumbs_down < 10%. Targets, not feelings.

2. An eval gate in the pipeline. change → run evals → pass → deploy / fail → block + alert. Golden datasets catch drift when a platform or external tool quietly changes underneath you.

3. Deep observability. Full conversation traces, tool-call instrumentation, model + prompt version tracking — so when quality slips you can see where.

Pair LLM-as-judge evals (good for the fuzzy stuff) with deterministic measures, and quality becomes provable, not asserted.

The rest of her nine lessons are the reusable layers under that:

→ Context — org / user / agent. "Org-level context is the unlock": one admin sets brand, tone, and taxonomy once, and every agent in the company is useful on day one.

→ Tools — quality over quantity. Their own CMO broke the raw Salesforce connector asking for "golden accounts." The fix wasn't a better connector — it was a skill teaching the model what that term means in their taxonomy. Ten deep tools beat a hundred shallow ones.

→ Agents vs. skills — an agent is the employee who decides; a skill is the SOP they follow. You want both.

→ Identity — agents get their own login, permissions, and audit trail, like any user — but can never escalate their own access. That's what makes a regulated rollout auditable.

→ Governance — match human review to volume: 10 approvals/day fits Slack buttons; 10,000/day needs AI-assisted triage. Don't bolt on a new approval system — extend the work management you already run.

One line, paraphrased, that stuck: context is king, context is queen.

The demo is the easy part. Everything above is what separates a clever demo from a system a thousand people can trust.

Credit to Nikita Bokil and the Optimizely Opal team — shared at NYC GTM + AI Masterclass #5.

#AgenticAI #EnterpriseAI #GTM #AgentReliability #MarTech

---

**First-comment block (sources — keeps the post body under budget):**

> Optimizely's $400M ARR milestone: optimizely.com/company/press/400M-ARR/ · Opal: optimizely.com/ai/ · Framework shared by Nikita Bokil (Opal, Optimizely) at NYC GTM + AI Masterclass #5, June 2026.

---

## Visual Brief — 5-slide carousel (Arc: 1 — Hook → Evidence → Mechanism → CTA)

**Carousel thesis:** An enterprise agent harness isn't a bigger chatbot — it's a stack of reusable layers, and the layer everyone skips (Agent Reliability Engineering) is what turns a demo into a system 1,000 people can trust.

**Slide count:** 5
**Aspect ratio:** 4:5 (1080×1350) — LinkedIn carousel default
**Tool routing summary:** All slides → Gamma (`format: "social"`, `4x5`, Stratos dark theme, `imageOptions.source: "noImages"`). Slides 2–4 are diagram/matrix-led; Slides 1 & 5 are typography. Export as one PDF for the LinkedIn document post.

---

### Slide 1 of 5 — Hook: name the gap

- **Visual mode:** Bold typography card
- **Headline:** "Reliability is engineering, not vibes."
- **Body / content:** Sub-line, smaller: "What it takes to run AI agents for 1,000 marketers — the Opal harness, 9 lessons." Small tag bottom-left: "Optimizely · Opal · NYC GTM + AI Masterclass #5."
- **Palette:** dark slate bg + off-white text + blue accent (#1E40AF) on the word "engineering"
- **Source attribution:** "Framework: Nikita Bokil, Optimizely Opal, 2026"
- **Alt text:** A title card reading "Reliability is engineering, not vibes," introducing nine lessons from building the Opal enterprise AI agent harness.
- **Tool:** Gamma (typography)

### Slide 2 of 5 — Evidence: the harness as a layered stack

- **Visual mode:** Diagram (stack / layer diagram)
- **Headline:** "A harness, not a chatbot"
- **Body / content:** Redraw the Opal architecture as four stacked bands (do NOT screenshot the deck):
  - **INTERFACE** — Chat · Artifacts · Action Cards · Headless (Copilot, Slack)
  - **CORE** — Context · Tools · Skills · Agents
  - **FOUNDATION** — Identity · Memory · Governance · Models
  - **BUILT ON** — Content Mgmt · Experimentation · Personalization · Analytics
  Caption under stack: "Chat is just the doorway. The value is everything underneath."
- **Palette:** dark bg + white labels + blue accent (#1E40AF) on the band titles
- **Source attribution:** "Source: Opal architecture, Optimizely, 2026"
- **Alt text:** A four-band stacked diagram of the Opal agent harness — Interface over Core (Context/Tools/Skills/Agents) over Foundation (Identity/Memory/Governance/Models) over the Optimizely platform.
- **Tool:** Gamma (diagram)

### Slide 3 of 5 — Mechanism A: Agent Reliability Engineering (the gem)

- **Visual mode:** Framework / matrix (three columns)
- **Headline:** "The SRE playbook, for agents"
- **Body / content:** Three columns, each with a title + one line + a mono code chip:
  - **SLOs** — measure what matters → `tool_success ≥ 95%` · `thumbs_down < 10%`
  - **Eval gate** — quality gate before deploy → `change → run evals` · `pass → deploy / fail → block + alert`
  - **Observability** — trace the reasoning → full traces · tool-call instrumentation · model + prompt version tracking
  Footer line: "Pair LLM-as-judge with deterministic measures. Quality becomes provable."
- **Palette:** dark bg + white text + blue accent (#1E40AF) on the three column titles; code chips in monospace on a darker chip
- **Source attribution:** "Source: Nikita Bokil, Opal, 2026"
- **Alt text:** A three-column framework for Agent Reliability Engineering — SLOs with target thresholds, an automated eval gate, and deep observability.
- **Tool:** Gamma (matrix)

### Slide 4 of 5 — Mechanism B: governance scales with volume

- **Visual mode:** Framework / matrix (volume table)
- **Headline:** "Match review to volume"
- **Body / content:** A four-row table, two columns (Volume → What the review looks like):
  - **10 / day** → Slack buttons work fine
  - **100 / day** → Queues & prioritization (things get missed)
  - **1,000 / day** → SLA tracking & escalation (Slack impossible)
  - **10,000 / day** → AI-assisted triage
  Footer: "Don't bolt on a new approval system — extend the work management you already run."
- **Palette:** dark bg + white text + amber accent (#D97706) on the "10,000 / day" row (signals where it breaks)
- **Source attribution:** "Source: Opal governance, Optimizely, 2026"
- **Alt text:** A volume table showing how human-in-the-loop review changes from Slack buttons at 10/day up to AI-assisted triage at 10,000/day.
- **Tool:** Gamma (matrix)

### Slide 5 of 5 — CTA: the question that earns the swipe

- **Visual mode:** Bold typography card
- **Headline:** "Can you prove your agent works?"
- **Body / content:** Sub-line: "Not 'did the demo work' — can you measure it, gate it, and trace it? That's the line between a demo and a system." Small credit line: "9 lessons from Nikita Bokil · Optimizely Opal."
- **Palette:** dark slate bg + off-white text + blue accent (#1E40AF) on "prove"
- **Source attribution:** "Framework: Nikita Bokil, Optimizely Opal, 2026"
- **Alt text:** A closing card asking "Can you prove your agent works?" framing measurement and tracing as the line between a demo and a system.
- **Tool:** Gamma (typography)

---

**Quality gate checks:**
- Arc fit: pass — single-thesis post grounded in specific data (SLOs, volume tiers); Arc 1 mirrors the post's hook→evidence→mechanism→CTA structure.
- Job differentiation: pass — Slide 2 (the stack) and Slides 3–4 (two distinct mechanisms: reliability vs. governance) each do a job the others can't.
- Frame parallelism: n/a (Arc 1), though Slides 3 & 4 deliberately share a matrix frame to read as a pair.
- Thumb test per slide: pass — every headline ≤ 5 words; tables/matrices have ≤ 4 rows/columns.
- Source citations: pass — every slide carries a source line.
- Adds information (not repetition): pass — the carousel renders the architecture stack and the two tables (governance, ARE) as structure; the post text describes them in prose but the visual is the legible artifact.
- Final slide earns the swipe: pass — closes on a question, not housekeeping.

---

## Radar Note (job-search / positioning)

Optimizely (~$400M ARR, Insight Partners portfolio) is a credible enterprise employer building exactly the agent-governance frontier Alex is positioning toward. This post amplifies a named Optimizely PM's work in a curator's voice — not a pitch — and demonstrates fluency in the unsexy enterprise layer (SLOs, eval gates, identity/RBAC, volume-tiered HITL) that separates a deployable agent system from a demo. That fluency maps directly to AI-native / enterprise GTM roles where the buyer cares about provable reliability and auditable rollouts, not vibes. Bonus thread: the ARE discipline is the same measurement-rigor layer Alex is building into his own pipeline — credible to reference in conversation.

---

## Connection Note (≤200 chars, talk-anchored)

Your "reliability is engineering, not vibes" framing from Masterclass #5 reframed agents for me — SLOs + eval gates + identity is the part most AI talks skip. Would love to follow the Opal work.

*(Character count: 198 / 200)*
