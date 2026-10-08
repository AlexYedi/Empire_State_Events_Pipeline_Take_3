# A Better Way to Build Agents: Workflows — Pre-Event Content

**Date:** Monday, April 20, 2026 · 5:30–8:30 PM ET
**Venue:** 6 St Johns Ln, NYC (same venue as Acacia FDE Panel same night — documentarian-worthy coincidence)
**Host:** Vercel (Caroline Ciaramitaro runs the series)
**Attendance:** In-person confirmed
**Research Brief:** https://www.notion.so/347d3699c2db818abe8af62332e5913b
**Status:** needs_review (local draft)

---

## 1. Pre-Event LinkedIn Post

### Variant A — "Your AI agent probably should be a workflow" (industry-consensus thesis)

> 2024: "Build autonomous agents."
> 2026: "Your AI agent probably should be a workflow."
>
> The quiet capitulation has been building for 18 months. Monday it becomes public.
>
> Vercel is putting "A Better Way to Build Agents: Workflows" on at 6 St Johns Ln — the clearest moment I've seen where four shipping teams say the same thing on the same stage:
>
> → Peter Wielander on Vercel's Workflow DevKit (GA, 200K weekly npm downloads, 54% median speedup at GA)
> → Mark Nowicki & Maggie Russo on Claude Managed Agents (public beta April 8, $0.08/hr active runtime)
> → Danny Aziz on building FLORA's creative agent on WDK
> → John Lindquist deconstructing a workflow live
>
> The shared thesis in one line: agents are while-loops + tools + LLMs, and while-loops in production need durable state.
>
> What I'm listening for:
> • For teams already on Temporal for non-AI workloads, the migration calculus into WDK
> • Whether Managed Agents is a Vercel Sandbox substitute or a layer above it
> • The FLORA failure mode that actually pushed them off bespoke orchestration
>
> Durable execution is the database moment for AI agents. Monday is where that stops being a hot take and starts being consensus.
>
> #AIAgents #VercelWorkflows #ClaudeManagedAgents

**Line count:** ~17 lines · **Hook fits in first 2 lines:** yes
**Thesis:** The industry is quietly converging on workflows as the default agent pattern, and this event is where it becomes public consensus.

#### Anti-pattern check
- [x] No "I'm excited to…" opener
- [x] Hook lands in first 2 lines (2024/2026 contrast)
- [x] No "leverage/unlock/ecosystem/game-changer"
- [x] Specific numbers (200K, 54%, $0.08/hr) not vague claims
- [x] "What I'm listening for" CTA is specific, not "thoughts?"
- [x] 3 hashtags, relevant
- [x] Documentarian voice — I'm in the room observing an inflection, not selling

---

### Variant B — "Three launches in a trench coat" (narrative-design thesis)

> Monday in NYC is three product launches stacked inside one event.
>
> The speaker order gives it away:
>
> 1/ Peter Wielander introduces Vercel's Workflow DevKit — the surface
> 2/ Mark Nowicki & Maggie Russo validate the surface via Claude Managed Agents — the runtime
> 3/ Danny Aziz shows FLORA shipping on it — the proof
> 4/ John Lindquist deconstructs the whole thing live — the pedagogy
>
> Named as an arc, it reveals how "A Better Way to Build Agents: Workflows" was designed. This isn't four independent talks. It's a coordinated thesis rollout from three shipping teams aligning on one claim: agents are workflows, and durable execution is the primitive that makes that work in production.
>
> What I'm watching for:
> • The seam between self-hosting the Claude Agent SDK on Vercel Sandbox and Managed Agents — where do you cross the line
> • How FLORA handles LLM payload saturation (the Temporal-era problem WDK's marketing is quiet about)
> • Whether Lindquist's deconstruction exposes the WDK patterns that will — and won't — generalize past Vercel
>
> The NYC angle matters. This narrative has been a West Coast infrastructure conversation. It lands in New York at 6 St Johns Ln with a FLORA engineer on stage. Worth naming the East Coast builder consolidation.
>
> #AIAgents #DurableExecution #BuildInPublic

**Line count:** ~18 lines · **Hook fits in first 2 lines:** yes
**Thesis:** The event is a deliberately designed narrative arc — three product moments sequenced as one argument — and the geographic move to NYC is itself a signal.

#### Anti-pattern check
- [x] No "I'm excited to…"
- [x] Hook specific (three launches / one event)
- [x] No buzzwords
- [x] Speaker arc structure shows analysis, not listing
- [x] "What I'm watching for" is specific
- [x] Closing names the East Coast angle without being cheerleadery
- [x] 3 hashtags

---

### Recommendation

**Primary: Variant A.** It's the sharper documentarian framing — it argues a thesis that extends beyond the event ("2024 vs 2026") and uses the event as the proof. Variant B is strong but more inside-baseball; it reads as event recap in advance, which is a narrower angle.

**Backup: Variant B** if Alex wants to prime a same-week synthesis post pairing this event with another workflow/agent-infra event (pattern-synthesis territory).

---

## 2. Visual Briefs

Format spec: 1080 × 1350 (4:5 portrait), high contrast, max 3 colors, max 8 words headline, source attribution small in bottom corner, alt text drafted.

### Visual A1 — Stat card (for Variant A)

**Concept:** The "54%" Vercel Workflows median speedup number as the centerpiece stat card.
**Composition:** Huge "54%" numeral, top-center. Subhead below: "median speedup. Vercel Workflows GA, 2026." Bottom: tiny source line "Source: Vercel, WDK GA announcement, April 2026."
**Palette:** Near-black background (#0A0A0A), off-white type (#F5F5F5), single accent — Vercel-adjacent electric cyan for the numeral only (#00E5FF). Three colors total.
**Mood:** Editorial, infrastructure-press, not marketing.
**Tool:** Canva or Figma. Native typography — Inter or Söhne. No templates.
**Alt text:** "Stat card showing 54 percent as the median speedup reported at Vercel Workflows GA in 2026, with source attribution to Vercel."
**Negative prompts (if AI-generating):** no stock photography, no generic abstract tech imagery, no multiple charts, no gridlines.

### Visual A2 — Quote pull-out (for Variant A)

**Concept:** The headline quote "Your AI agent probably should be a workflow" framed as a pull-quote.
**Composition:** Quote centered, one line per phrase. Attribution below in smaller type: "— the emerging 2026 consensus, across Vercel, Anthropic, and the teams shipping production agents." Negative space on all sides.
**Palette:** Off-white background (#FAFAFA), near-black type (#111), one accent orange line under the word "workflow" (#FF6B35).
**Mood:** Editorial magazine pull-quote. Authoritative, not shouty.
**Typography:** Serif headline (Tiempos, GT Sectra, or similar) for the quote; geometric sans (Inter) for attribution.
**Alt text:** "Pull-quote reading Your AI agent probably should be a workflow, attributed to the emerging 2026 consensus across Vercel Anthropic and production agent teams."
**Negative prompts:** no quotation-mark decorative elements, no stock background, no people.

### Visual A3 — Architectural diagram (for Variant A)

**Concept:** While-loop → checkpointed workflow visual metaphor. Show the evolution structurally.
**Composition:** Left half — a naive while-loop drawn as a circular arrow (agent.run() forever). Right half — same loop with durable checkpoints drawn as node-circles at each iteration, and a small "state persisted" indicator between each step. Arrow from left to right labeled "2024 → 2026."
**Palette:** Black background (#000), white primary (#FFF), single cyan accent for checkpoint nodes (#00E5FF).
**Mood:** Technical diagram, not infographic. Minimal labeling, architecturally clean.
**Tool:** Figma or Excalidraw. Hand-drawn-feel is fine (documentarian signal).
**Alt text:** "Diagram showing a naive agent while-loop on the left evolving into a checkpointed durable workflow on the right, labeled 2024 to 2026."
**Negative prompts:** no 3D effects, no gradients on checkpoint nodes, no stock imagery, no code screenshots.

### Visual B1 — Speaker arc card (for Variant B)

**Concept:** Four numbered boxes showing the speaker order as a thesis-rollout arc.
**Composition:** Vertical stack, 4 rows. Each row: number (1/2/3/4) left-aligned large, speaker name + role center, one-word role-in-arc right-aligned ("surface" / "runtime" / "proof" / "pedagogy"). Headline above: "Monday's speaker order is the argument."
**Palette:** Off-white background, near-black type, one accent color per row (cyan / magenta / yellow / green — but all muted, editorial not highlighter).
**Mood:** Editorial infographic, not deck slide.
**Typography:** Single geometric sans family, varied weights.
**Alt text:** "Four-row card showing Monday's speaker arc: Peter Wielander as surface, Mark Nowicki and Maggie Russo as runtime, Danny Aziz as proof, John Lindquist as pedagogy."
**Negative prompts:** no stock photos of speakers, no company logos, no gridlines.

### Visual B2 — "3 products. 1 thesis. 1 room." editorial headline card

**Concept:** Minimal text-only editorial card. The three-line headline IS the visual.
**Composition:** Three lines, centered, large weight. "3 products. 1 thesis. 1 room." Below in small type: "A Better Way to Build Agents: Workflows · NYC · April 20."
**Palette:** Pure black background, off-white headline, small cyan period after "room."
**Mood:** Editorial poster. Reads like a New Yorker event listing.
**Typography:** Serif headline (Tiempos) for gravitas.
**Alt text:** "Editorial poster reading three products, one thesis, one room, referencing A Better Way to Build Agents Workflows in NYC on April 20."
**Negative prompts:** no decorative elements, no imagery, no brand logos.

### Visual B3 — NYC-at-dusk editorial photo overlay

**Concept:** Photographic — NYC skyline or Tribeca streetscape at dusk — with a minimal type overlay.
**Composition:** Full-bleed moody NYC photo (Tribeca streetscape preferred, industrial-brick energy). Top-third overlay in off-white: "The workflow conversation comes east." Small subhead: "April 20 · 6 St Johns Ln."
**Palette:** Photo's natural palette (blue hour tones), one off-white type layer.
**Mood:** Documentarian photojournalism.
**Source:** Unsplash Tribeca dusk photo (credit-required), or Alex's own iPhone shot.
**Alt text:** "Photograph of Tribeca at dusk overlaid with the text The workflow conversation comes east, April 20, 6 St Johns Lane."
**Negative prompts:** no heavy photo filters, no stock "NYC tech scene" imagery, no blurred skylines.

---

## 3. DMs

Targeting Level 3 personalization per outreach-templates.md. Three options per target, each ending with a question good enough to be a prepared question if the DM goes unanswered.

### DM Target 1 — Caroline Ciaramitaro (Host, Community at Vercel)

**Pattern:** DM Pattern 2 (Host / Organizer)
**Personalization hook:** Her "the real story behind the facts of our lives" philosophy + Zero to Agent series curation.

**Option A (philosophy bridge):**
> The line "the real story behind the facts of our lives" is hard to top as a frame for what a community programmer should be paying attention to right now. The Zero to Agent series reads like you're tracking the same inflection the events claim to cover — Monday's lineup is the cleanest public moment I've seen for the "agents-as-workflows" thesis, with WDK + Managed Agents + FLORA on the same stage by design, not coincidence. When you're shaping a series like this, how much of the design is reacting to what builders are asking for in the room vs. naming a conversation that hasn't quite formed yet?

**Option B (curation-as-argument):**
> Your Zero to Agent sequencing reads intentional — the curation itself argues a thesis about where agents are going. Monday's lineup (WDK + Managed Agents + FLORA + Lindquist deconstruction) is the moment that thesis goes public. One thing I'd love your POV on: the gap between the builders you're seeing at these events and the teams still skipping prompt chaining straight to orchestrator-workers — is that gap closing, or is the middle of the stack still missing?

**Option C (shorter, specific question):**
> Community programming that sequences talks as a coordinated argument is underrated. Monday at 6 St Johns Ln reads that way — Peter → Anthropic → Danny → John is an arc, not a lineup. One question I'm bringing to the room: for teams already on Temporal for non-AI workflows, what's the migration calculus into WDK? Looking forward to being there.

**Recommended:** Option A — her philosophy line is a real personalization anchor, and the curation-as-design bridge shows I see her role as more than logistics.

---

### DM Target 2 — Danny Aziz (Engineer at FLORA, NYC)

**Pattern:** DM Pattern 1 (Speaker before their talk)
**Personalization hook:** FAUNA launched April 3 on Vercel Workflows + FLORA's NYC HQ + Nike/Netflix/Pentagram customer load.

**Option A (failure-modes angle):**
> Your Monday talk on FLORA's agent on Vercel Workflows is the one I'm most curious about — specifically the failure modes that pushed you off whatever you were using before WDK. FAUNA's April 3 launch signaled a real bet on the workflow-as-primitive thesis. One thing I'll be listening for: where LLM payload saturation shows up in practice (the Temporal-era problem WDK's marketing is conspicuously quiet about). How are you handling checkpoint payload size with multimodal generations in the loop?

**Option B (agent-vs-workflow reality-check):**
> The FLORA creative agent on WDK is the production proof-point I've been waiting to see publicly deconstructed. Nike / Netflix / Pentagram / Wonder Studios on the customer list means real enterprise load, not toy-scale demos. How often is the agent actually exercising dynamic direction vs. running a highly deterministic workflow with LLM steps? The 2026 "your AI agent probably should be a workflow" take only holds if the answer is "mostly deterministic" — wondering if that matches the FLORA reality.

**Option C (shortest, seam-question):**
> Looking forward to your Monday talk. The question I'm bringing: where does durable execution stop and evals/observability begin in the FLORA loop? Most teams hit that seam before they hit scale, and WDK + AI SDK is quiet on it. Curious how you've drawn that line.

**Recommended:** Option A — the payload-saturation question is the technically deepest hook, and it signals I know the Temporal-era baggage. FLORA engineer will recognize the framing.

---

### DM Target 3 — John Lindquist (Co-Founder egghead.io, AI DX at Vercel, Claude Code Ambassador)

**Pattern:** DM Pattern 1 (Speaker before their talk)
**Personalization hook:** Claude Code ambassador + prolific public pedagogy on agent tooling.

**Option A (pipeline-parallel, demo-friendly):**
> Your Monday "deconstruct a workflow" session is the one I'm most looking forward to — the pedagogy of taking apart a real WDK build publicly is what I wish existed for every new primitive. I've been running Claude skills as the research + content engine for an AI-native events pipeline (skill-first, direct MCP writes to Notion + HubSpot, no middleware). When you're teaching a workflow pattern, what's the tell that a student should have used LLM-driven direction vs. deterministic code at a given step? That seems to be where most teams guess wrong.

**Option B (public-curriculum frame):**
> Your Claude Code content has been the closest thing to a public curriculum for advanced agent tooling. Monday's deconstruction is going to make a lot of that implicit knowledge legible. One question I'll be listening for: the most common mistake teams make skipping from prompt chaining straight to orchestrator-workers without doing routing or parallelization first. Is that a skills gap or a tooling gap?

**Option C (shortest, heuristic-focused):**
> Looking forward to Monday's WDK deconstruction. One question from my own skill-based pipeline work: where does a deconstructed workflow tell you "this step is a prompt" vs. "this step is code calling an LLM"? The heuristic matters more than the framework.

**Recommended:** Option A — the concrete project reference ("I've been running Claude skills as the research + content engine…") makes it unmistakably personalized, and the question is at the intersection of his pedagogy and my build.

---

### Optional (only if volume allows) — DM Target 4: Peter Wielander

**Rationale for deferring:** Peter is the builder — engineer-built-the-thing profile. Per the research brief, "specific implementation questions, not abstract strategy." Better to ask him in-person during Q&A than DM pre-event; save the good implementation question for the room.

### Optional — Mark Nowicki / Maggie Russo

**Rationale for deferring:** Mark's public footprint is low (don't overclaim familiarity). Maggie's Applied AI Architect role is high-leverage but best approached with a "what's breaking in the early cohort" question in-person. Save for the room.

---

## 4. Prepared Questions

Sourced from: (a) research brief Top Questions by topic, (b) unused DM question angles above, (c) room-level questions that benefit from live context.

### For Peter Wielander (Vercel, WDK)

1. For teams already running Temporal for non-AI workloads, what's the migration calculus into WDK — same mental model, or different primitives? *[source: research brief]*
2. How does WDK handle pause/resume for LLM calls that exceed Vercel Function execution windows? *[source: research brief]*
3. What does the observability stack look like in practice — OpenTelemetry spans, Vercel's own traces, or both? *[source: research brief]*

### For Mark Nowicki & Maggie Russo (Anthropic, Claude Managed Agents)

4. Mental model for Managed Agents vs self-hosting the Claude Agent SDK on Vercel Sandbox — when do you cross that line? *[source: research brief + Variant B DM angle]*
5. How do we extend Anthropic's sandbox with internal tools / MCP servers without exposing credentials? *[source: research brief]*
6. Multi-tenant permission model — per-user, per-org, or customer-fronted auth? *[source: research brief]*
7. (To Maggie specifically) From the early-adopter cohort pattern data — what's the #1 thing breaking that surprised you? *[source: unused DM angle]*

### For Danny Aziz (FLORA)

8. Where does durable execution stop and evals/observability begin inside the FLORA loop? *[source: Option C DM]*
9. How are you handling checkpoint payload size when multimodal generations sit in state? *[source: Option A DM]*
10. How often is the FLORA agent actually exercising dynamic direction vs. running a deterministic workflow with LLM steps? *[source: Option B DM]*

### For John Lindquist

11. Heuristic for LLM-driven vs deterministic code at each step — how do you teach the tell? *[source: Option A DM]*
12. Most common mistake teams make skipping prompt chaining straight to orchestrator-workers — skills gap or tooling gap? *[source: Option B DM]*

### For Caroline Ciaramitaro (if there's a moment)

13. When you curate a series like Zero to Agent, how much is reacting to what builders ask for vs. naming a conversation that hasn't formed yet? *[source: Option A DM]*

### Room-level (good for Q&A if a speaker defers)

14. What's actually different about AI agent workloads that breaks the payments/ETL durable-execution playbook? *[source: research brief]*
15. Does the durable-execution decision come down to model provider or infra location? *[source: research brief]*

---

## 5. Content Status (for Notion writeback)

**Push to Notion:**
- `linkedin_post_pre` — **Variant A** (recommended). Content includes: post copy + 3 visual briefs (A1, A2, A3).
- `prepared_questions` — grouped list, 15 questions, source-attributed.

**Keep local for Alex's selection:**
- DMs — 3 targets × 3 options = 9 DM drafts. Alex picks which to send per target, then we optionally push the selected 3 as separate `linkedin_dm_speaker` / `linkedin_dm_host` drafts if he wants them in Notion.

**Relations for Notion writes:**
- Event: https://www.notion.so/347d3699c2db814aa3a3f1b62d05d9bb
- People (all 6 from research brief): Caroline, Peter, Mark, Maggie, John, Danny
- Topics (all 4 from research brief): Vercel Workflows, Claude Managed Agents, Durable Execution for AI Agents, Agent Architecture Patterns

---

*Last updated: 2026-04-19 · Pre-event · Event date 2026-04-20*
