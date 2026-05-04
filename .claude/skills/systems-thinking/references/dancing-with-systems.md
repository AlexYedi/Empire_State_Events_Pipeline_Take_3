# Dancing with Systems — Practitioner Conduct

The 15 guidelines from Meadows' chapter 7 ("Living in a World of Systems") and her Whole Earth Review essay "Dancing with Systems" (2001), which the chapter is adapted from. Originally distilled from her decades of system-dynamics practice at MIT and the Sustainability Institute.

This is the **how-you-act** half of systems thinking. The leverage points and archetypes tell you *where* to push and *what* patterns to recognize. The dance is *how to be a person engaging with a complex system without making it worse.*

> Self-organizing, nonlinear, feedback systems are inherently unpredictable. They are not controllable. They are understandable only in the most general way. The goal of foreseeing the future exactly and preparing for it perfectly is unrealizable. — Meadows, ch. 7

The list comes in two slightly different versions in the book — the chapter prose and the appendix list. The numbering is from the appendix (15 items) which combines the chapter version (~14 items) with the related "Dancing with Systems" essay.

---

## The 15 guidelines

### 1. Get the beat of the system
Before you intervene, **watch how the system behaves**. Don't jump to causes. Don't even jump to interpretations. Observe behavior over time. Look at history. Track the actual numbers, the actual patterns. **The first response to a system you don't understand is to study it long enough to see its rhythm.**

For practitioners: when joining a new team, codebase, market — *don't reorganize in the first quarter*. Watch. Sketch. Ask. The actual loops are not what's on the org chart.

### 2. Expose your mental models to the light of day
Everything you "know" about the system is a model. Externalize it. Draw it. Write it. Show others. Invite them to challenge your assumptions and add their own. Collect competing models — don't champion one — until evidence rules some out.

> Getting models out into the light of day, making them as rigorous as possible, testing them against the evidence, and being willing to scuttle them if they are no longer supported is nothing more than practicing the scientific method.

For practitioners: write the actual decision down. Make the assumed mechanism explicit. "I think X is happening because Y → Z." Then look for evidence that Y → Z is wrong.

### 3. Honor, respect, and distribute information
> Decision makers can't respond to information they don't have, can't respond accurately to information that is inaccurate, and can't respond in a timely way to information that is late. I would guess that most of what goes wrong in systems goes wrong because of biased, late, or missing information. — Meadows ch. 7

Don't distort. Don't delay. Don't withhold. Information is the cheapest high-leverage intervention available (leverage point #6). The Toxic Release Inventory dropped chemical emissions 40% in two years with no fines, just by making the data public.

For practitioners: build dashboards engineers can see. Surface NPS scores to feature teams. Make support tickets visible in standup. Default to transparency.

### 4. Use language with care, and enrich it with systems concepts
Our information streams are mostly language. Our mental models are mostly verbal. Words are how we share, and shape, what we can think.

> A society that talks incessantly about "productivity" but that hardly understands, much less uses, the word "resilience" is going to become productive and not resilient.

For practitioners: name the phenomenon you're looking at. "This is a balancing loop with a long delay." "This is success-to-the-successful." Naming it makes it manipulable. Refusing the vocabulary keeps the team stuck on symptoms.

### 5. Pay attention to what is important, not just what is quantifiable
> If quantity forms the goals of our feedback loops, if quantity is the center of our attention and language and institutions, if we motivate ourselves, rate ourselves, and reward ourselves on our ability to produce quantity, then quantity will be the result.

This is Meadows' direct shot at Goodhart's Law. **Things that are hard to measure don't stop existing.** Justice, democracy, security, freedom, truth, love, quality. None can be defined or measured cleanly. All of them must be spoken for or systems won't be designed to produce them.

> Be a quality detector. Be a walking, noisy Geiger counter that registers the presence or absence of quality.

For practitioners: when reviewing a feature for ship, the question isn't only "does it move the metric?" Also: is it ugly? Tacky? Inappropriate? Does it make the product *worse* in ways the metric won't catch? Don't be stopped by "if you can't measure it, you can't manage it."

### 6. Make feedback policies for feedback systems
> A dynamic, self-adjusting feedback system cannot be governed by a static, unbending policy.

Design policies that *change in response to the state of the system*, not policies that mandate a fixed behavior regardless of conditions. Meadows' worked example: the Montreal Protocol on the ozone layer — built in monitoring + reconvening to adjust phase-out schedules as new data arrived.

For practitioners: don't write rules that assume conditions stay constant. Build in the trigger that changes the rule. Sprint capacity is set by trailing 4-sprint velocity, not by an annual estimate. Pricing changes by cohort behavior. Hiring plans flex with attrition data.

### 7. Go for the good of the whole
> Hierarchies exist to serve the bottom layers, not the top.

Don't maximize parts of systems at the expense of the whole. Don't, as Boulding said, go to great trouble to optimize something that never should be done at all. Aim for system-wide properties: growth, stability, diversity, resilience, sustainability — *whether they are easily measured or not.*

For practitioners: a team optimizing its sprint velocity at the expense of code review quality is hurting the org. A platform team optimizing its own SLOs at the expense of consumer teams is hurting the platform. Watch for local optima.

### 8. Listen to the wisdom of the system
> Aid and encourage the forces and structures that help the system run itself. Notice how many of those forces and structures are at the bottom of the hierarchy. Don't be an unthinking intervenor and destroy the system's own self-maintenance capacities. Before you charge in to make things better, pay attention to the value of what's already there.

The Guatemala-aid story Meadows tells: foreign agencies kept arriving to "create jobs" while walking past a thriving local market full of basket makers, vegetable growers, butchers, candy sellers all running their own tiny businesses. The leverage was in supporting what was already working — small loans, literacy classes, accounting training — not importing a factory.

For practitioners: an existing process that "looks chaotic" may have load-bearing function you don't see. Before refactoring an architecture, ask what it's *actually* doing. Before reorganizing a team, ask what informal coordination structures it's evolved.

### 9. Locate responsibility within the system
**"Intrinsic responsibility"** — the system is designed to send feedback about the consequences of decisions *directly, quickly, and compellingly* to the decision makers.

> Because the pilot of a plane rides in the front of the plane, that pilot is intrinsically responsible. He or she will experience directly the consequences of his or her decisions.

For practitioners: the on-call rotation that pages the engineer who shipped the bug = intrinsic responsibility. The architecture review where the proposer also runs the migration = intrinsic responsibility. Designs that *export* consequences (one team builds, another team operates, a third team deals with users) tend to produce systems whose builders never see what they built.

### 10. Stay humble. Stay a learner
The systems work has taught Meadows to trust intuition more and rationality less, to lean on both as much as possible, and to be prepared for surprises.

> The thing to do, when you don't know, is not to bluff and not to freeze, but to learn. The way you learn is by experiment — or, as Buckminster Fuller put it, by trial and error, error, error.

> What's appropriate when you're learning is small steps, constant monitoring, and a willingness to change course as you find out more about where it's leading.

For practitioners: small reversible commitments. Two-way doors before one-way doors. Public retros that own the mistake. The opposite of "stay the course" when you're not sure you're on course.

### 11. Celebrate complexity
> The universe is messy. It is nonlinear, turbulent, and dynamic. It spends its time in transient behavior on its way to somewhere else, not in mathematically neat equilibria. It self-organizes and evolves. It creates diversity and uniformity.

Resist the temptation to flatten variety. Don't insist on uniformity for its own sake. Don't oversimplify. Trust that some of the system's "messiness" is the substrate it needs to evolve.

For practitioners: a codebase that's perfectly uniform is also brittle. A team that's perfectly aligned has no internal critique. An org that's perfectly clean has no learning. Complexity isn't a bug; it's a feature of resilience.

### 12. Expand time horizons
> One of the worst ideas humanity ever had was the interest rate, which led to the further ideas of payback periods and discount rates, all of which provide a rational, quantitative excuse for ignoring the long term.

Plan with both fast and slow loops in mind. Sustainability is the test that everything is in dynamic equilibrium across the longest relevant horizon, not just optimized for this quarter.

For practitioners: every short-term shortcut is a long-term loop being created. Choose the shortcut deliberately, with the awareness that the loop is now in your future. Some shortcuts are worth it; many aren't, when you score them across years instead of weeks.

### 13. Defy the disciplines
> In spite of what you majored in, or what the textbooks say, or what you think you're an expert at, follow a system wherever it leads. — Meadows ch. 7

Disciplines are useful filters but they cut systems into pieces that don't reflect how systems actually behave. Real systems span engineering, finance, design, ops, customer success, market dynamics, and human psychology simultaneously.

For practitioners: when a problem doesn't fit your usual frame, that's the signal to learn the next discipline, not to force the problem into a frame that misses it. The "GTM problem" might be an architecture problem. The "morale problem" might be a metrics problem. Follow the system.

### 14. Expand the boundary of caring
> The real system is interconnected. No part of the human race is separate either from other human beings or from the global ecosystem.

The boundary you draw around "the system" determines what you optimize. Draw it too narrowly and you optimize at the expense of what's outside. Customers. Suppliers. The next team. The next user cohort. The five-years-from-now version of the company.

For practitioners: when a decision benefits "us" at the expense of "them," ask: what defines us-vs-them, and is that boundary serving the actual system or just our short-term comfort?

### 15. Don't erode the goal of goodness
This is Meadows' direct callback to the "Drift to Low Performance" archetype, applied to ethics.

> Examples of bad human behavior are held up, magnified by the media, affirmed by the culture, as typical. […] The far more numerous examples of human goodness are barely noticed. They are "not news." They are exceptions.

> And so expectations are lowered. The gap between desired behavior and actual behavior narrows. Fewer actions are taken to affirm and instill ideals.

> We know what to do about drift to low performance. Don't weigh the bad news more heavily than the good. And keep standards absolute.

For practitioners: when a colleague does excellent work, name it. When a vendor delivers something unusually good, recognize it. When a feature ships with unusual care, celebrate the care. The negative examples will surface themselves; the positive ones need help. **A culture's standards drift in the direction it pays attention to.**

---

## The point of all 15

Together these aren't a checklist. They're the *posture* required to use the rest of systems thinking without doing damage.

The leverage points (`leverage-points.md`) tell you where to push.
The archetypes (`system-archetypes.md`) tell you what to look out for.
The vocabulary (`feedback-loops-stocks-flows.md`) gives you the building blocks.
The dance is what keeps you honest while you do the work.

Meadows' final line:
> We can't control systems or figure them out. But we can dance with them!

The dance has prerequisites. It needs full humanity — rationality, intuition, compassion, vision, morality. It needs error-embracing. It needs humility. It is, very much, work — but it is the work that lets the rest of the toolkit produce something other than wreckage.

---

## When to invoke this file

- Before any major intervention in a complex system, **read guidelines 1, 2, 8, and 10** to set the right intake posture.
- After a setback or surprise, **read guidelines 3, 5, 9, and 10** to recalibrate.
- When metrics are diverging from outcomes, **read guidelines 5 and 6**.
- When a team or org is drifting, **read guidelines 7, 11, 12, and 15**.
- When making decisions that affect parties outside your immediate concern, **read guidelines 13 and 14**.

## Cross-references

- `meadows-thinking-in-systems.md` — source distillation
- `leverage-points.md` — where to push
- `system-archetypes.md` — what patterns to recognize
- `feedback-loops-stocks-flows.md` — vocabulary for sketching the system
- `system-properties.md` — qualities to design for (resilience, self-organization, hierarchy)
- `applications-to-software-and-product.md` — how all of this lands in product/software/GTM contexts
