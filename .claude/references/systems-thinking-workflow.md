# Planning, Building, Analyzing — A Systems-Thinking-Backed Workflow

A reference that ties Alex's existing skill harness together through Meadows' systems lens. Use when you have an initiative, problem, or question that spans multiple stages — discovery, design, build, ship, post-ship — and want a coherent way to invoke the right skills in the right order.

This file is **not a skill**. It is a workflow card for the orchestrator (Alex, or `head-of-product-engineering`) to consult. The actual work happens via the named skills.

---

## The three modes

Every product/strategic effort spans three modes that recur, often interleaved:

1. **Analyzing** — what's actually happening in this system? What are the loops, the leverage points, the actors, the chronic patterns?
2. **Planning** — given that analysis, what should we do? Which leverage points to push, in what order, at what horizon?
3. **Building** — execute the plan, while preserving the system properties (resilience, self-organization, hierarchy) and not falling into the named archetypes.

The systems-thinking skill (`.claude/skills/systems-thinking/`) provides the diagnostic vocabulary. The other skills are the mode-specific tooling.

---

## Mode 1 — Analyzing

**Goal:** understand the system before acting on it. Most failed interventions skip this mode.

**Lead skill:** `systems-thinking` (with the eight-phase analysis from `references/diagnostic-questions.md`).

**Supporting skills:**
- `conducting-user-interviews` — gather data from inside the system
- `product-management:synthesize-research` — turn raw input into themes
- `data:explore-data`, `data:analyze`, `data:statistical-analysis` — quantitative side
- `engineering:debug` — when the analysis target is a misbehaving software system
- `engineering:incident-response` — when the analysis target is a recent failure (postmortem-style)
- `anthropic-skills:cto-architect` — when system-level architecture is in scope
- `sales:pipeline-review`, `sales:account-research` — when the system is a sales motion
- `marketing:performance-report` — when the system is a marketing channel

**Output of this mode:**
- A bounded system (parts, interconnections, deduced purpose)
- Stocks-and-flows sketch with named loops
- Identified archetypes (if any)
- Player-and-incentives map (bounded rationality of each actor)
- Candidate leverage points

**Don't move to planning mode** until the analysis has produced these artifacts. "I think the problem is X" is not analysis; it's a hypothesis that needs to be tested through the eight phases.

---

## Mode 2 — Planning

**Goal:** decide what to do, where to push, in what sequence.

**Lead skills:** `head-of-product-engineering` (for full lifecycle plans), or for narrower scopes:
- `defining-product-vision` — paradigm-level (#2)
- `writing-north-star-metrics` — goal-level (#3) with Goodhart resistance
- `prioritizing-roadmap` — leverage-point distribution check
- `product-management:write-spec`, `writing-prds` — feature-level (#5 rules / #6 info flows)
- `engineering:architecture` — software architecture (#10)

**Supporting skills:**
- `risk-playbooks` — pre-mortem against the 8 archetypes before committing
- `launch-tiering` — size second-order analysis to scope of intervention
- `ai-product-strategy` — when AI-specific feedback-loop design is in scope
- `engineering:system-design` — when system design is the lever
- `product-management:roadmap-update` — operational layer

**Plan-quality checks (run before committing):**
- [ ] Have we identified the highest workable leverage point?
- [ ] Is at least one item in the plan operating above #9 (delays)?
- [ ] Have we screened the plan against all 8 archetypes for unintended setups?
- [ ] Does the plan strengthen or weaken system properties (resilience, self-organization, hierarchy)?
- [ ] Have we run a pre-mortem on second-order effects?
- [ ] Is the launch tier sized correctly to the scope of the intervention?

If any of these are skipped, the plan is more likely to produce surprise outcomes.

---

## Mode 3 — Building

**Goal:** execute without falling into the archetypes; preserve system properties.

**Lead skills:** `shipping-products` (in-flight execution discipline) + the operational engineering skills.

**Supporting skills:**
- `engineering:code-review` — strengthen the balancing loop (#8)
- `engineering:tech-debt` — manage the reinforcing loop (#7)
- `engineering:testing-strategy` — design balancing loops at appropriate levels
- `engineering:deploy-checklist` — pre-deploy verification
- `engineering:incident-response` — when something breaks
- `engineering:standup` — operational comms
- `claude-api`, `vercel-plugin:ai-sdk` — implementation patterns for AI features
- `simplify` — remove accidental complexity introduced during build

**Discipline during build (per `dancing-with-systems.md`):**
- Honor information flows. Default to surfacing data, dashboards, telemetry to the team.
- Make feedback policies for feedback systems. Don't write static rules to govern dynamic conditions.
- Stay humble. Small reversible commits. Two-way doors before one-way doors. Error-embracing.
- Watch for Drift to Low Performance. Anchor quality bars to absolute standards, not "average of last sprint."

---

## Mode-shift signals

Move from analyzing → planning when:
- The system map stabilizes across multiple stakeholders
- The dominant feedback loops are named and signed (R/B)
- At least one named archetype is matched to behavior
- A leverage point hierarchy is sketched

Move from planning → building when:
- Highest workable leverage point identified
- Pre-mortem run; second-order effects enumerated
- Risk register with named owners exists at appropriate tier
- Success metric (and counter-metrics) defined

Move back from building → analyzing when:
- An unexpected system response is observed (wasn't predicted in the plan)
- Performance drift detected without obvious cause
- Stakeholders are pulling in directions that suggest hidden goals
- Quick fixes are starting to compound into dependency

The modes interleave; they're not strictly sequential. The skill is recognizing which mode you're actually in, not just which one you intended to be in.

---

## Worked example — refactoring the Empire State Events Pipeline

**Trigger:** Alex notices the pipeline is producing more event briefs but content output is plateauing. Why?

**Analyze mode:**
- Run `systems-thinking` eight-phase analysis on the pipeline as a system.
- Identify stocks: events researched (rising), content drafts (plateauing), published content (plateauing).
- Identify flows: research throughput is up, content drafting is the bottleneck.
- Match to archetype: Tragedy of the Commons (Alex's drafting time is the shared resource being claimed by every event).
- Run `data:explore-data` on Notion DB to confirm content draft creation rate.

**Plan mode:**
- Decide: lever is information flow (#6) — surface drafting load to Alex earlier — and rule (#5) — change definition-of-done so research includes a content scaffold.
- Use `prioritizing-roadmap` leverage-point distribution check to confirm.
- Use `risk-playbooks` to screen the change against archetypes (e.g., does scaffold-included research create Shifting the Burden where research quality drops?).
- Use `head-of-product-engineering` for full lifecycle if the change is significant.

**Build mode:**
- Update `event-research.md` skill to include a content scaffold step.
- Use `simplify` to ensure the addition doesn't bloat the skill.
- Update `pre-event-content` to consume the scaffold.
- Set a 2-week measurement window before declaring success.

**Re-analyze:**
- Did content output rise? If yes, what's the new bottleneck (next-leverage-point question)? If no, what loop did we miss?

This is the cycle: analyze → plan → build → re-analyze. The skills compose; the systems-thinking lens is what makes them coherent.

---

## When to pull this file

- At the start of any non-trivial product/strategic initiative.
- When a `head-of-product-engineering` orchestration kicks off (the Workflow 1 + 4 systems-thinking invocations should consult this file).
- When debugging a chronic team/product/GTM issue and "we've tried everything" has been said.
- When designing a new skill or evolving an existing one (the mode classification helps decide the skill's actual purpose).
- During quarterly retros — which mode did we under-invest in?

## See also

- `.claude/skills/systems-thinking/SKILL.md` — the systems-thinking skill itself
- `.claude/skills/systems-thinking/references/` — the eight reference files this workflow draws on
- `.claude/skills/head-of-product-engineering/SKILL.md` — the orchestrator that hard-invokes systems-thinking twice
- `.claude/agents/ops/systems-analyst.md` — the delegated systems-analysis agent (when you want a sub-agent to run a full eight-phase analysis without consuming main-context tokens). Note: per `.claude/WORKFLOWS.md` "Known gap" section, custom agents may not be discoverable mid-conversation; invoke from a fresh session for now.
