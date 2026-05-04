---
name: shipping-products
description: Help users ship products faster and with higher quality. Use when someone is planning a launch, struggling to release features, dealing with shipping velocity issues, or trying to establish better release practices.
---

# Shipping Products

Help the user ship products effectively using frameworks and insights from 47 product leaders.

## How to Help

When the user asks for help with shipping:

1. **Understand the blocker** - Ask what is preventing the ship: scope, quality concerns, dependencies, or organizational friction
2. **Assess the context** - Determine if this is a new product, feature iteration, or infrastructure change
3. **Challenge timelines** - Apply the 'maximally accelerated' principle to identify the critical path
4. **Guide quality tradeoffs** - Help balance speed with appropriate quality standards for the product type

## Core Principles

### Speed is a signal of competence
Nan Yu: "If you look at people at the pinnacle of their craft, you can tell how good the output is going to be by how fast they're going." High speed combined with quality indicates mastery, not sloppiness. Use speed to increase iterations and variations tested.

### Ship to get feedback
Dylan Field: "Get it out as fast as you possibly can. The faster you get it out, the more feedback you get." Prioritize shipping speed to accelerate the feedback loop, which is the most valuable asset in early product development.

### Speed and stability move together
Nicole Forsgren: "When you move faster, you are more stable. You're pushing smaller changes more often with a smaller blast radius." Push smaller changes more frequently to reduce complexity and make failures easier to debug.

### 99% done is 0% done
Dmitry Zlokazov: "If something is 99% done, it's closer to 0% rather than 100%." A product provides zero customer value until fully finished and launched. Maintain relentless focus until shipping is complete.

### Ask why you can't ship tomorrow
Nick Turley: "Why can't we do this now? If this was the most important thing and you wanted to truly maximally accelerate it, what would you do?" Use this question to strip away non-essential blockers and identify the critical path.

### Use quality checklists
Matt MacInnis: "We have a Product Quality List that articulates the standards we want you to meet when you ship." Create a PQL checklist of quality standards that must be met before release, and iterate on it when bugs slip through.

### Ship to learn, then polish
Nick Turley: "You won't know what to polish until after you ship." In emergent products like AI, ship early to discover which areas actually require polish based on real-world usage.

### Tempo matters more than org design
Patrick Campbell: "Your tempo framework is more important than your org design. If a team is always planning but doesn't ship, you don't have alignment on what good tempo looks like." Define shipping frequency expectations for every department.

### Perfect execution validates strategy
Naomi Gleit: "Only with perfect execution can we reevaluate whether the strategy is right or wrong." Poor execution leaves the cause of failure ambiguous. Ship properly to learn whether your strategy was correct.

### Small consistent gains compound
Keith Yandell: "If you continuously push up what you ship by a week, you'll end up lapping competitors because you start the next thing a week sooner." Small velocity improvements create massive competitive advantages through compound interest.

## Questions to Help Users

- "What would it take to ship this tomorrow - what's actually blocking you?"
- "Is this a mission-critical product where reliability matters, or can you ship raw and iterate?"
- "What is the smallest version that would let you learn something from real users?"
- "Who is the single person with authority to make the final trade-off decisions?"
- "What quality bar must be met, and what can be polished after launch?"
- "When did you last have a working, testable version of this product?"

## Common Mistakes to Flag

- **Over-polishing before launch** - You can't know what needs polish until you see real usage patterns
- **Waiting for pixel-perfect designs** - Early versions don't need pixel perfection; they need working software you can interact with
- **Feature flag sprawl** - Excessive feature flags create technical debt and hidden failure points during launches
- **No single decision maker** - Coherent product design requires one person with moral authority to make trade-off decisions
- **Confusing activity with shipping** - High-quality ideation and documentation are useless without the velocity to actually release

## Deep Dive

For all 55 insights from 47 guests, see `references/guest-insights.md`

## Systems-thinking lens for shipping

Two Meadows guidelines apply directly to shipping practice (full coverage in `.claude/skills/systems-thinking/references/dancing-with-systems.md`):

**Honor, respect, and distribute information (leverage point #6).** Most shipping problems are information problems. Decision makers can't respond to information they don't have, or that's late, or that's biased. Practical implications:
- Build dashboards engineers can see at-a-glance, not just leadership.
- Surface customer NPS / support tickets / cost-per-request to the team that built the feature, not just to management.
- Default to transparency in ship rituals. The toxic-release-inventory effect (40% drop in emissions just from publishing data, no fines) shows up in product orgs too.

**Make feedback policies for feedback systems.** Don't write static rules to govern dynamic systems. Sprint capacity from trailing 4-sprint velocity, not annual estimate. Pricing tiers that flex on cohort behavior. Hiring plans that adjust on attrition. Static policy on dynamic system → oscillation, overshoot, and miss.

The "drift to low performance" archetype is the silent killer of shipping cadence — see `system-archetypes.md`. Anchor quality bars to *best historical performance*, not to "average of recent sprints," or you'll quietly recalibrate downward and never notice.

## Related Skills

- Writing PRDs
- Launch Tiering
- Risk Playbooks
- Prioritizing Roadmap
- Systems Thinking — info flows + feedback policies above; deeper coverage in `systems-thinking/references/dancing-with-systems.md` and `applications-to-software-and-product.md`
- `engineering:deploy-checklist` — pre-deployment verification
- `engineering:incident-response` — postmortem feeds back into next launch's playbook
