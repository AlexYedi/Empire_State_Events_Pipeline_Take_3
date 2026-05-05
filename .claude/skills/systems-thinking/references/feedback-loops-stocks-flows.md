# Feedback Loops, Stocks, and Flows — Foundational Vocabulary

The mental-model primitives that everything else in systems thinking is built from. Drawn from Meadows ch. 1-2 (The Basics; A Brief Visit to the Systems Zoo) and the broader system-dynamics literature.

If you only learn one thing from this directory, learn this. The 12 leverage points and 8 archetypes are useless without the underlying vocabulary of stocks, flows, and feedback loops. If you can sketch a system as stocks-flows-loops on a napkin, you can usually find the leverage point.

---

## 1. Stocks

> A stock is the foundation of any system. Stocks are the elements you can see, feel, count, or measure at any given time. — Meadows, ch. 1

**A stock is an accumulation.** It has a value at a moment in time. It changes only via flows.

Examples:
- Water in a bathtub
- Money in a bank account
- Books on a shelf
- Trees in a forest
- Open issues in a backlog
- Engineers on a team
- Active subscribers
- Unresolved bugs in production
- Customer goodwill (intangible, but still a stock)
- Self-confidence (intangible, still a stock)

**Property #1 — A stock is the present memory of the history of changing flows within a system.** If you've been adding to a savings account for 10 years, the balance is the *integral* over time of every deposit and withdrawal. The stock summarizes the history.

**Property #2 — Stocks act as buffers, delays, or shock absorbers.** Big stocks relative to flows = stable. Small stocks = jumpy. A reservoir buffers rainfall vs. demand. An inventory buffers production vs. orders. A team's capacity buffers commitments vs. delivery.

**Property #3 — Stocks decouple inflows from outflows.** A river's water level *can* drop while it's still raining — if outflow exceeds inflow. Most systems behave this way. Don't assume that "we're hiring" means headcount is growing — it depends on attrition (outflow). Don't assume "revenue is up" means cash is up — it depends on collection rate, costs (outflow), and so on.

---

## 2. Flows

> Flows are filling and draining, births and deaths, purchases and sales, growth and decay, deposits and withdrawals, successes and failures. — Meadows, ch. 1

**A flow is a rate of change of a stock.** It has units of stock-per-time. Cubic feet per second. Customers acquired per month. Lines of code merged per week.

Every stock has at least one inflow and at least one outflow (one of which can be zero).

**The bathtub equation:**

```
Stock(t) = Stock(t-dt) + (Inflow - Outflow) × dt
```

In English: today's level = yesterday's level + (what came in - what went out) since yesterday.

**Property #1 — A stock can be raised by *increasing inflow OR decreasing outflow*.** They are equivalent levers on the stock value, but often very different in feasibility. To increase headcount, you can hire (inflow) or stop attrition (outflow). To increase cash, you can earn more or spend less. Most "growth" plans focus only on inflow.

**Property #2 — Inflows and outflows are independent.** A team can grow even while attrition is high, if hiring is faster. A bank account can drain even while income rises, if spending rises faster.

**Property #3 — Renewable resources are flow-limited; nonrenewable resources are stock-limited.** This is one of Meadows' core distinctions. A forest can sustain a logging rate equal to its growth rate forever. A coal seam, once depleted, is gone. The rule generalizes: when the resource regenerates, manage the flow. When it doesn't, manage the stock.

---

## 3. Feedback Loops

> A feedback loop is a closed chain of causal connections from a stock, through a set of decisions or rules or physical laws or actions that are dependent on the level of the stock, and back again through a flow to change the stock. — Meadows, Appendix

A feedback loop is not "feedback" in the colloquial sense (criticism on your work). It is a *closed causal circuit*: stock → decision/rule → flow → back to stock.

There are exactly two types.

### Balancing (B) loops

**Goal-seeking. Stability-seeking. Equilibrium-restoring.**

When the stock deviates from a goal, the loop pushes it back toward the goal.

```
   ┌──────────────────────┐
   │                      ▼
[Stock]               [Action]
   ▲                      │
   │                      │
   └────[Compare to goal]─┘
```

**Examples:**
- Thermostat: room temperature deviates from setpoint → furnace activates → temperature returns to setpoint.
- Hunger: blood sugar drops → eat → blood sugar rises.
- Inventory management: stock low → reorder → stock returns to target.
- On-call rotation: alert fires → engineer responds → service restored.
- Code review: PR opens → review → merge or fix.

**Behavior over time:** convergence to equilibrium. Sometimes oscillation if there are delays (see below).

Balancing loops are *what makes systems work* — they self-correct. **Stripping out a balancing loop because it "isn't being used" is one of the most common ways to break a system.**

### Reinforcing (R) loops

**Self-amplifying. Snowballing. Exponential growth or collapse.**

The bigger the stock gets, the faster it grows (or the faster it shrinks).

```
[Stock]──────────[Inflow]
   │               ▲
   │               │
   └───(more X →   │
        more inflow)
```

**Examples:**
- Compound interest: more money in the bank → more interest → more money.
- Population growth: more people → more births → more people.
- Viral spread: more infected → more new infections → more infected.
- Network effects: more users → more value → more users.
- Technical debt: more debt → slower delivery → more shortcuts → more debt.
- Drift to low performance: lower expectations → less effort → lower output → lower expectations.

**Behavior over time:** exponential growth or exponential collapse. **No reinforcing loop runs forever** — eventually a balancing loop kicks in (often violently — population crashes, market corrections, system collapse).

### Causal loop diagram (CLD) notation

In any analysis you sketch, use this notation. It's a near-universal convention in the system-dynamics tradition (Sterman, Senge):

- **Variables** as labeled boxes or just text.
- **Arrows** show causal influence.
- **+** sign on arrow: *same direction*. When cause increases, effect increases (all else equal).
- **−** sign on arrow: *opposite direction*. When cause increases, effect decreases.
- **Loop label** in the center: **R** for reinforcing, **B** for balancing.
- **Hash marks** ( || ) across an arrow: a *delay* on that link.

**Loop polarity rule:** count negative signs around the loop.
- **Even number of negatives (including 0)** → reinforcing (**R**).
- **Odd number of negatives** → balancing (**B**).

**Example — code-review balancing loop:**

```
     ┌────────────[+]────────► [Quality of merged code]
     │                              │
[Lines reviewed]                    │ [+]
     ▲                              ▼
     │ [+]                    [Bugs in production]
     │                              │
     │ [−]                          │ [+]
[Reviewer fatigue] ◄───────────[Time fixing prod bugs]
```

Three positive links, one negative → odd → balancing loop. The system self-corrects: too few reviews → bugs → fatigue from firefighting → less reviewing capacity. Standard B loop.

**Example — technical debt reinforcing loop:**

```
[Tech debt] ──[+]──► [Time per feature] ──[+]──► [Schedule pressure]
     ▲                                                  │
     │                                                  │ [+]
     └───────────────────[+]──[Shortcuts taken]◄────────┘
```

All positive → even (4 positives, 0 negatives) → reinforcing. Once started, debt amplifies itself.

### Delays in loops

> A delay in a balancing feedback loop makes a system likely to oscillate. — Meadows, Appendix

The most common pattern by which balancing loops misbehave is **delay**. If feedback about the stock's state is late, the response is too late, and the stock overshoots its goal. A long-enough delay → oscillation. A really long delay relative to system dynamics → exploding oscillations or collapse.

**Examples of delay in balancing loops:**
- The shower-temperature problem (you adjust the knob, but pipe-volume delay means the temperature change reaches you 20 seconds later — so you over-adjust, then over-correct, then over-adjust again).
- Hiring: company senses headcount need → posts job → finds candidate → onboards → 3-6 months later, capacity arrives. Often the original need has shifted.
- Customer feedback loops: bug ships → user encounters → reports → triaged → fixed → released. Total cycle: weeks. So bugs accumulate while fixes are still in flight.

**Two ways to dampen oscillation:**
1. **Shorten the delay.** Faster CI, faster customer telemetry, faster onboarding.
2. **Slow the rate of change.** Don't add load faster than the system can adjust.

The latter is often the only available move. See `leverage-points.md` #9 (Delays).

---

## 4. Shifting dominance

When multiple loops act on the same stock simultaneously, **the dominant loop is the one whose effect is currently strongest.** Dominance can shift over time as conditions change.

A classic pattern: a reinforcing loop dominates early (exponential growth), a balancing loop dominates later (saturation). Together they produce S-curve behavior.

**Worked example — startup growth:**
- Early: word-of-mouth (R) dominates. Each new user brings 1.2 new users.
- Late: market saturation (B) dominates. Each new acquisition is harder; CAC rises until acquisition stalls.

Recognizing which loop dominates *now* — and which one will dominate *next* — is half of strategic foresight.

---

## 5. Multiple stocks, multiple loops

Real systems have many stocks, many flows, many loops. Three sources of complexity:

1. **Loops within loops.** A single stock can have several balancing loops (different correction mechanisms operating at different time scales) and several reinforcing loops.
2. **Loops across stocks.** Two stocks linked: each affects the other's flow. (See archetypes Escalation, Success to the Successful, Tragedy of the Commons in `system-archetypes.md`.)
3. **Nonlinearity.** When a flow's response to a stock isn't proportional — e.g., predator response saturates as prey become abundant. Nonlinear systems can exhibit threshold effects, multiple stable equilibria, and chaotic behavior.

The discipline isn't to model every loop; it's to identify the *few that matter for this question right now*. In Meadows' phrasing: "Where you draw the boundary depends on the purpose of the discussion."

---

## 5b. Perverse balancing loops — when the outflow is waste, not delivery

> If the sum of outflows equals the sum of inflows, the stock level will not change. — Meadows, Appendix

This logic produces a subtle trap: **a stock can be drained by waste as well as by delivery, and the two look identical at the stock level.** A balancing loop that empties the stock via *decay, expiration, or abandonment* will produce a flat or stable stock level that *appears* to be working — but the system is failing.

**Examples:**
- A content drafts queue stabilizes because pre-event drafts age out (the event passes; the post becomes worthless) before they get published. Looks like equilibrium; actually loss.
- An on-call alert queue stabilizes because alerts auto-close after X hours unacknowledged. Looks like resolution; actually negligence.
- A sales pipeline holds steady because deals quietly get marked "lost — no decision" rather than worked. Looks like throughput; actually attrition.
- A research backlog holds steady because old experiments get archived as "deprioritized." Looks like cleanup; actually abandonment.

**How to detect:** measure both outflows separately. *Drained-via-delivery* and *drained-via-decay* are not interchangeable. Split the metric. The decay metric should be the loud one — if it's the dominant outflow, the system is losing, not equilibrating.

**Why it's not in the canonical 8 archetypes:** Meadows treats this as a structural property of stock-flow systems rather than naming it as its own archetype. But it's distinct enough from Drift to Low Performance (which is about goals slipping) to deserve a separate diagnostic. When you sketch a system and find a balancing loop closing the stock, ask: *is the outflow producing the desired outcome, or just emptying the stock?*

Surfaced in the 2026-05-04 systems-analyst test on the Empire State Events Pipeline (the "decay-as-relief" loop on the Content Drafts queue).

---

## 5c. Single-actor systems with multiple sub-roles

A subtle bounded-rationality pattern Meadows doesn't address directly: **one person inhabiting several functional roles within a system.** Alex-as-researcher, Alex-as-drafter, Alex-as-reviewer, Alex-as-publisher are all the same person — but each role has its own bounded view, its own incentives, its own moment-to-moment goals.

When you sketch the players and their incentives (`diagnostic-questions.md` Phase 5), **don't collapse multi-role single actors into one row.** Each role gets its own line. The bounded-rationality finding is often that *each role is making locally rational choices* and the aggregate produces an outcome no role intended.

**Common in:**
- Solo founders / solopreneurs
- Personal-brand operators (creator + editor + publisher + community manager)
- Indie engineers (architect + implementer + on-call + support)
- Anyone running a pipeline with many sub-functions before delegating any of them

**Why this matters:** the temptation is to write "Alex" as one row in the actor table. But the leverage point is often *the seam between two roles within the same person* — the friction at the handoff from researcher-Alex to publisher-Alex. Naming the roles separately surfaces seams the single-actor framing hides.

Surfaced in the 2026-05-04 systems-analyst test — the Shifting-the-Burden diagnosis only became visible once researcher-Alex and reviewer-Alex were treated as separate actors.

---

## 6. Dynamic equilibrium

> If the sum of inflows equals the sum of outflows, the stock level will not change — it will be held in dynamic equilibrium. — Meadows, Appendix

Crucial distinction. A stock at equilibrium isn't *static*. It can have huge flows in and out — they just balance.

A river in steady state has water rushing through it constantly. The level doesn't change. The water does.

A team in steady state hires and loses people constantly; headcount is flat. The people are different.

This matters because **interventions on flows are sometimes invisible at the stock level until something tips the balance.** You can be 5% off-balance for years before it shows. Then it shows fast.

---

## 7. Practitioner moves with stocks-flows-loops vocabulary

When you encounter a complex situation:

1. **Name the stocks.** What is accumulating?
2. **Name the flows.** What is moving in/out?
3. **Identify the dominant feedback loops.** R or B? Where are the delays?
4. **Test for dominance shift.** Will the loop running this system today still be running it in 6 months?
5. **Find the leverage point.** (See `leverage-points.md`.)
6. **Check for archetype shape.** (See `system-archetypes.md`.)

Forty minutes with a whiteboard usually outperforms four hours of debate. The picture beats the prose.

---

## 8. Worked example — engineering team velocity

Imagine a team whose velocity is degrading and nobody can quite say why.

**Stocks:**
- Code in production
- Technical debt
- Open bugs
- Engineer attention/capacity

**Flows:**
- *Inflows:* features merged, debt added, bugs created, attention available (per FTE)
- *Outflows:* features deprecated, debt paid down, bugs closed, attention spent

**Loops:**
- **R1 (debt loop):** more debt → slower features → more shortcuts → more debt. Reinforcing.
- **B1 (bug-fix loop):** bugs accumulate → user reports → fixes prioritized → bugs decline. Balancing.
- **R2 (rework loop):** bugs create rework → less attention for features → more shortcuts → more bugs.
- **B2 (review loop):** code review catches issues → fewer bugs → less rework → more attention for review.

**Diagnosis without the vocabulary:** "The team feels overwhelmed."
**Diagnosis with the vocabulary:** "R1 and R2 are reinforcing each other. B1 and B2 are too weak to dominate. Quickest leverage: strengthen B2 (review capacity) — info flows + balancing loop — or reduce gain on R1 (slow rate of debt accumulation via definition-of-done updates) — leverage point #7."

That's the move from "everyone is exhausted" to "here's the structural fix."

See `applications-to-software-and-product.md` for more worked examples in product/software/GTM contexts.

---

## Cross-references

- For *where* in the loop structure to push, see `leverage-points.md`.
- For *named patterns* of dysfunctional loop structures, see `system-archetypes.md`.
- For the *qualitative properties* that emerge from healthy loop structures (resilience, self-organization, hierarchy), see `system-properties.md`.
- For the *practitioner's posture* when working with these structures, see `dancing-with-systems.md`.
