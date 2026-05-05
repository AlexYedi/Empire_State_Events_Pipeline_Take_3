# Applications to Software and Product — Empire State Events Pipeline

This file is the **project-specific** applications layer. The general-purpose translation of Meadows' frameworks to product, engineering, and GTM work lives in the global library at:

> `~/Documents/GitHub/alex-agents-skills/Product/systems-thinking/references/applications-to-product-and-engineering.md`

That global file covers software architecture as stock-and-flow, technical debt as reinforcing loop, code review as balancing loop, information flows in software systems, engineering team archetypes (Drift to Low Performance, Shifting the Burden, Tragedy of the Commons), product management (Goodhart's Law, roadmap prioritization, vision-as-paradigm), GTM (Success to the Successful, Escalation, pricing as feedback policy), AI products (bounded rationality of LLMs, build for the slope), and content systems (stocks-flows of audience attention, content as reinforcing loop with delay, drift in cadence).

**Read the global file first.** This file only contains what's specific to the Empire State Events Pipeline.

---

## The Empire State Events Pipeline as a system

A worked diagnostic, applied to Alex's own pipeline. Use this whenever the systems-analyst agent is invoked on a pipeline-related question, and as the seed for re-running the eight-phase analysis quarterly.

### Stocks

- **Event invites in calendar** — rising
- **Researched briefs in Notion Events DB** — rising
- **Content Drafts** in `needs_review` — *rising; primary symptom of the 2026-05-04 publishing-plateau diagnosis*
- **Content Drafts in `approved` / `scheduled`** — variable; under-instrumented
- **Published LinkedIn posts** — flat (the diagnosed symptom)
- **Alex's review-and-polish attention** — finite, fixed daily quota
- **Documentarian-of-NYC-AI reputation** — slow-rising
- **HubSpot contacts + Notes** — accumulating, not the bottleneck
- **Project portfolio (active builds)** — managed manually

### Flows

- **Inflows:**
  - Event intake (calendar invites pasted in)
  - Research synthesis (event-research skill writing to Notion)
  - Content drafting (multiple skills producing 4-7 draft assets per event)
  - Outreach attempts (DMs)
  - Project ideation → architecture → build
- **Outflows:**
  - Content publishing to LinkedIn (the *intended* outflow, currently flat)
  - **Content decay** — pre-event drafts aging out as events pass without publishing (the *perverse* outflow, currently substantial — see `feedback-loops-stocks-flows.md` §5b on perverse balancing loops)
  - Project ship events
  - Audience attention to other things

### Dominant feedback loops

- **R1 — Research-as-reward (currently dominant on input):** event happens → research is fast and gratifying → Alex adds more events → more research. Reinforcing, no balancing loop on input side.
- **R2 — Content-asset multiplication:** each event produces multiple draft asset types. More skills → more asset types per event → more drafts per event. Reinforcing on draft inflow.
- **B1 — Review-as-bottleneck (weak):** drafts pile up → review pressure → review session → drafts decrease. Should be balancing — undersized relative to R2's gain.
- **B2 — Decay-as-relief (perverse):** drafts age out without publishing → drafts decrease. Looks like B1 working; actually the system silently failing.
- **R3 — Publishing reinforcement (currently weak):** publish → engagement → reputation → confidence to publish more. Should be the dominant R loop. Currently starved because publishing rate is flat.
- **R4 — Documentarian flywheel:** more events attended (in person) → more documentarian moments → reputation rises → more event invites → more events attended. Operates partly outside the publishing pipeline.

### Diagnosed archetype matches (2026-05-04)

- **Shifting the Burden to the Intervenor (~80%):** the skills made research effortless, but the act of *deciding to publish* — Alex's native publishing capability — is being atrophied by the volume of unshipped drafts. The intervention is replacing native capacity, not enhancing it.
- **Seeking the Wrong Goal (~75%):** the pipeline implicitly optimizes for *briefs created* (visible, satisfying, easy to count). It does not equally reward *posts shipped*.
- **Drift to Low Performance (~50%, watch):** if the flat publish rate continues, it becomes the new normal.

**Considered and ruled out — Tragedy of the Commons:** earlier hypothesis. Wrong, because Commons requires multiple actors externalizing cost onto a shared resource. Alex is the only actor; there's no externality. What looks like Commons is actually multiplicative inflow + fixed-capacity outflow + atrophying native capability — that's Shifting the Burden, not Commons. **Escapes are different**: Commons → privatize/regulate; Shifting → restore native capacity *before* removing intervention.

### Highest-leverage interventions

- **#3 Goals (highest workable):** redefine the pipeline's success metric from "researched events" to "published posts per week" with a quality counter-metric. Re-anchor every skill, dashboard, and Notion view against "does this serve published content or just researched content?"
- **#6 Information flows:** weekly Notion snapshot showing (a) briefs created, (b) drafts created, (c) drafts published, (d) drafts decayed without publishing. Decay metric should be loud.
- **#5 Rules:** change the definition-of-done. Currently "done" for event-research = "wrote to Notion." Re-rule: "done" = "produced one specific, ship-ready post by Friday or it doesn't count."
- **#7 Reduce gain on inflow:** cap event intake or assets-per-event so the multiplier on the inflow side stops outrunning the fixed outflow capacity.

### Counterintuitive direction warning

The *intuitive* fix is to add a "publishing automation skill" or scheduling tool that drafts faster. **That is the Shifting-the-Burden trap deepening.** It would relieve symptoms while atrophying Alex's actual publishing muscle further. Per `system-archetypes.md` §6: "If you are the intervenor, work in such a way as to *restore or enhance the system's own ability to solve its problems, then remove yourself.*" The intervention should make Alex *publish more*, not make the skills *draft more*.

---

## Leverage points the pipeline already uses (positive baseline)

- **#6 (information flows):** Notion + HubSpot make Alex's research visible and findable to himself.
- **#9 (delays):** the pipeline closes the research-to-content loop in hours instead of days.
- **#5 (rules):** definition-of-done for events (skills check), content (style guide), project ideation (architecture confidence ≥ 90%).
- **#4 (self-organization):** the skills-evolve-the-skills pattern (`update-voice-and-style.md`, `update-anti-patterns.md`).

## Leverage points worth adding deliberately

- **#6 (info flows):** the publish-rate-vs-decay dashboard (recommended above).
- **#3 (goals):** an explicit re-articulation each quarter of *what's the system actually optimizing* — networking, content velocity, learning, job pipeline?
- **#1 (transcending paradigms):** quarterly review of whether the documentarian-of-NYC-AI paradigm itself is still serving the actual goal (job pipeline + AI-native reputation + ongoing learning). The paradigm is a hypothesis, not a fact.

---

## When to re-run this analysis

- **Quarterly** as part of pipeline review.
- **Whenever a new skill is added** to the pipeline — does it strengthen or weaken system properties (resilience, self-organization, hierarchy)?
- **When stakes change** — e.g., job-search activity ramps up; published content starts mattering more.
- **When metrics surprise** — flat output despite rising input is exactly the signal that triggered the 2026-05-04 analysis.

Each re-run should produce a fresh artifact at `.claude/artifacts/systems-analysis-<date>.md` and update this file's archetype-match section if the dominant archetypes shift.

---

## See also

- The systems-analyst agent at `.claude/agents/systems-analyst.md` — invoke for delegated runs of this analysis
- Test artifact at `.claude/artifacts/systems-analyst-test-2026-05-04.md` — first eight-phase run with full output
- Workflow card at `.claude/references/systems-thinking-workflow.md` — three-mode (Analyzing/Planning/Building) framing
- Global applications file at `~/Documents/GitHub/alex-agents-skills/Product/systems-thinking/references/applications-to-product-and-engineering.md` — for general-purpose product/engineering/GTM applications
