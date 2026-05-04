# System Archetypes — The 8 Traps and Their Escapes

From Meadows, *Thinking in Systems*, ch. 5 + Appendix "Springing the System Traps." Originally identified in the system-dynamics tradition (Forrester, Senge, Kim), Meadows' contribution is the explicit "Trap → Way Out" pairing for each.

These are the canonical recurring failure modes of complex systems. Most chronic systems problems — in organizations, products, markets, code, GTM motions — are one of these eight in disguise. Naming the archetype is half the diagnosis.

## How to use this catalog

When something in a system is going chronically wrong:

1. **Match the symptoms to an archetype.** Each one has a distinctive shape — a specific feedback structure that produces a specific behavior over time.
2. **Confirm the structure before acting.** Two archetypes can produce similar symptoms (e.g., "Drift to Low Performance" and "Shifting the Burden" both look like "things are getting worse and we're not sure why"). Trace the actual feedback loops.
3. **Apply the named escape.** Each archetype has a known way out. The escapes are *not* "do the opposite of the trap" — they're specific structural moves that disable the bad feedback loop.

The escapes consistently route through the higher leverage points (information flows, rules, goals) — see `leverage-points.md`. If you're trying to escape an archetype with parameter tweaks, you'll usually fail.

---

## 1. Policy Resistance

**Trap:** Multiple actors in a system pull a stock toward different goals. When one actor pushes the stock toward their goal, the others compensate. Any new policy, *especially* an effective one, pulls the stock farther from the other actors' goals and produces additional resistance. Result: nobody likes where the stock is, but everyone expends massive effort maintaining it.

**Behavior over time:** stuck. Stock stays roughly where it has always been despite increasingly aggressive interventions. Fatigue accumulates.

**Classic examples:**
- War on drugs. Police push supply down → prices rise → profit margins increase → more dealers enter → supply unchanged.
- Diet-then-binge cycles. Restrict calories → body conserves and rebounds.
- Engineering team mandates from leadership that produce malicious compliance.

**Way out:** Let go. Bring in *all* the actors and use the energy formerly expended on resistance to seek mutually satisfactory outcomes — or to redefine larger and more important goals everyone can pull toward together. Operates at leverage points 3 (goals) and 5 (rules).

**Diagnostic question:** "Whose goals am I overriding, and what would they need from a redefined system to stop pulling against me?"

---

## 2. The Tragedy of the Commons

**Trap:** A commonly shared resource. Every user benefits directly from using it but shares the costs of abuse with everyone else. Therefore, very weak feedback from the resource's condition to the resource users' decisions. Result: overuse until the resource collapses and becomes unavailable to anyone.

**Behavior over time:** apparent abundance, then sudden collapse. Often each user's individual usage looks rational and modest; the cumulative effect is destructive.

**Classic examples:**
- Overfishing of a shared fishery.
- Aquifer drawdown by agricultural users.
- Open-source maintainer burnout (everyone consumes, few contribute).
- A shared on-call rotation where individual teams' rate of pages is the externality.
- A team Slack channel where everyone @-here's because the cost lands on others.

**Way out:** Educate users about consequences. AND — more reliably — restore the missing feedback link, either by privatizing so each user feels direct consequences, or (when privatization is impossible) by regulating access. Operates at leverage point 6 (information flows) and leverage point 5 (rules).

**Diagnostic question:** "Where is the cost of this behavior landing, and how would I route it back to the actor making the decision?"

---

## 3. Drift to Low Performance

**Trap:** Performance standards influenced by past performance, with negative bias in perceiving past performance ("things used to be better"). Reinforcing feedback loop of eroding goals: actual performance dips → standards lower to match → less urgency → performance dips further.

**Behavior over time:** slow, almost invisible decline. Each step looks normal because the comparison point keeps moving down with you.

**Classic examples:**
- A product team that gradually accepts more bugs in production because "this is just how shipping works now."
- A sales org that lowers quota when quota isn't being hit instead of fixing what's broken.
- An engineering culture where p95 latency drift goes unnoticed because everyone's ambient memory of "fast" recalibrates.
- A content cadence that quietly slips from weekly to "when we have time."

**Way out:** Keep performance standards *absolute* — pegged to something external that doesn't drift. Even better: anchor standards to the *best* historical performance instead of the worst. "Set up a drift toward *high* performance." Operates at leverage point 3 (goals).

**Diagnostic question:** "What objective benchmark would I be embarrassed to compare today's performance against?"

---

## 4. Escalation

**Trap:** Two stocks where the state of one is determined by trying to surpass the state of the other — and vice versa. Reinforcing feedback loop. Each side's response provokes the other. Exponential growth → arms race, smear campaign, escalating violence, escalating loudness.

**Behavior over time:** surprisingly fast. Exponential. Stops only when one side collapses.

**Classic examples:**
- Cold-war arms races.
- Competing-feature wars between two SaaS vendors.
- LinkedIn engagement-bait spirals (everyone's posts get more performative because everyone else's are).
- Sales discount races.
- Code-review nitpick wars.

**Way out:** The best way out is not getting in. If already caught, *unilaterally disarm* — refuse to compete on that axis, breaking the reinforcing loop. Or negotiate balancing loops to control the escalation (treaties, antitrust, content guidelines). Operates at leverage point 8 (balancing feedback) and leverage point 3 (goals — by changing what's being optimized).

**Diagnostic question:** "What axis is being raced on, and what happens if I just step off it?"

---

## 5. Success to the Successful (Competitive Exclusion)

**Trap:** Winners of a competition systematically rewarded with the means to win again. Reinforcing feedback loop. Allowed to proceed uninhibited, winners eventually take all and losers are eliminated.

**Behavior over time:** initial diversity → consolidation → monopoly. Often appears just after a phase of healthy competition.

**Classic examples:**
- Wealth concentration (rich earn interest; poor pay it).
- Network-effect platform dynamics (the largest platform attracts more users, attracting more developers, attracting more users).
- Brand-equity compounding for incumbent products in a category.
- Engineering org dynamics where the most senior engineers get the most interesting work, accelerating their advantage over juniors.

**Way out:** Several available, used in combination:
- **Diversification** — losers can exit and start a different game (new market, different niche, new product line).
- **Strict limits on winnings** — antitrust, max pie share, monopoly busting.
- **Level the playing field** — remove some incumbent advantage or boost the disadvantaged.
- **Reward designs that don't bias the next round** — prizes that don't compound.

Operates at leverage point 5 (rules) — explicitly redesigning the competition rules.

**Diagnostic question:** "Is this competition designed so the winner of round N has an unfair advantage in round N+1?"

---

## 6. Shifting the Burden to the Intervenor (The Addiction Loop)

**Trap:** A solution to a systemic problem reduces or disguises the symptoms but does nothing to solve the underlying problem. If the intervention causes the original system's self-maintaining capacity to *atrophy*, a destructive reinforcing feedback loop is set in motion: more solution required → less native capacity → more solution required → …

**Behavior over time:** apparent stabilization, then escalating dependency. The system can no longer function without the intervention.

**Classic examples:**
- Substance addiction in the literal sense.
- Painkiller use that masks the structural problem driving the pain.
- A team that depends on a heroic individual contributor to ship every release; the team's own delivery muscle atrophies.
- Marketing that runs on permanent promotional discounts; full-price demand never develops.
- AI-assisted code that the team can no longer maintain without the AI.
- Funding a startup with debt rounds because revenue muscles never built.

**Way out:**
- The best way out is not getting in. Beware "symptom-relieving or signal-denying policies or practices that don't really address the problem."
- If you are the intervenor: work in such a way as to *restore or enhance the system's own ability to solve its problems, then remove yourself.*
- If you are the dependent: build your own capabilities back up *before* removing the intervention. The longer you wait, the harder withdrawal is.

Operates at leverage point 4 (self-organization).

**Diagnostic question:** "Is this intervention strengthening the system's ability to solve its own problem, or replacing it?"

---

## 7. Rule Beating

**Trap:** Rules to govern a system invite perverse behavior — actors give the appearance of obeying the rules or achieving the goals while actually distorting the system in ways the rules don't catch.

**Behavior over time:** rules proliferate, behavior degrades. Each new rule creates a new evasion. Rule complexity rises, system function falls.

**Classic examples:**
- Tax code arbitrage.
- Vanity-metric gaming when bonuses tie to KPIs (DAUs juiced by background notifications; revenue booked but not collectable; bug-count low because P3s don't get filed).
- Code coverage metrics gamed with trivial tests.
- Standup updates engineered to *sound* like progress.
- Sales reps closing low-quality deals at quarter-end.

**Way out:** Redesign the rules to release creativity *toward* the purpose of the rules, not toward beating them. Realign incentives to the underlying goal, not its proxy. Closely related to Goodhart's Law ("when a measure becomes a target, it ceases to be a good measure"). Operates at leverage point 5 (rules) and leverage point 3 (goals).

**Diagnostic question:** "If actors fully achieved the *letter* of these rules while violating their *spirit*, what would happen? If that scenario is bad, the rules are vulnerable to rule-beating."

---

## 8. Seeking the Wrong Goal

**Trap:** System behavior is exquisitely sensitive to the goals of feedback loops. If the goal is defined inaccurately or incompletely, the system will obediently produce a result that isn't really wanted. The system isn't broken — it's working perfectly toward the wrong target.

**Behavior over time:** apparent success on stated metric, mysterious decline in actual desired outcome.

**Classic examples:**
- "Lines of code per day" as a productivity metric (longer code, not better code).
- "Tickets closed" as a support quality metric (tickets closed without resolution).
- "Time to first response" as a customer success metric (templated responses that don't help).
- GDP as the goal of a national economy when human welfare is the actual aim.
- LinkedIn followers as a personal-brand metric vs. interesting work + meaningful conversations.
- Hiring senior engineers as a leverage-points decision when the bottleneck is decision authority, not talent.

**Way out:** Specify indicators and goals that reflect the *real welfare* of the system. Be especially careful not to confuse *effort* with *result* — you'll end up with a system that produces effort, not result. Operates at leverage point 3 (goals) and leverage point 6 (information flows — measuring what matters).

**Diagnostic question:** "If we hit this metric perfectly but the underlying outcome got worse, would I notice? If not, the metric is the goal in disguise."

---

## Cross-references between archetypes

These traps interact. Common combinations:

- **Drift to Low Performance + Seeking the Wrong Goal:** standards drift down *and* are pegged to the wrong measure. Compounds invisibly.
- **Tragedy of the Commons + Rule Beating:** when access to a commons is regulated, actors find ways to evade the regulation. The history of every common resource ever.
- **Success to the Successful + Policy Resistance:** small interventions to redistribute don't work because the winners have accumulated enough power to resist. (Why progressive taxation tends to weaken over time.)
- **Shifting the Burden + Drift to Low Performance:** the team's own capability atrophies, and "what good output looks like" gets recalibrated downward in parallel. Doubly invisible.
- **Escalation + Seeking the Wrong Goal:** the axis being raced on isn't the one that produces value. Common in feature wars and content engagement spirals.

When you spot one archetype, look for its common partners.

## Cross-references to other reference files

- For why each archetype is hard to escape (the leverage points where the escape lives), see `leverage-points.md`.
- For the underlying mechanics of the feedback loops involved, see `feedback-loops-stocks-flows.md`.
- For applying these archetypes to product, software, and GTM contexts, see `applications-to-software-and-product.md`.
- For the conduct that lets a practitioner notice these traps before getting fully captured by them, see `dancing-with-systems.md`.
