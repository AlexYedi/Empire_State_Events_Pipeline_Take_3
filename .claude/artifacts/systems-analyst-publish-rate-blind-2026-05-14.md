# Systems Analysis (Blind Re-Run) — Content Pipeline Publish-Rate Plateau

**Date:** 2026-05-14
**Scenario:** Empire State Events Pipeline — content drafts accumulate in Notion without reaching `published`
**Agent:** `.claude/agents/ops/systems-analyst.md` (blind-run protocol — see prompt constraints below)
**Status:** **PARKED.** Saved for durable reference; no Linear issue opened; no intervention triggered. YED-23 (the 2026-05-13 goal-flip) needs 2-4 weeks of data before either this diagnostic or the 2026-05-04 prior diagnostic can be re-evaluated against signal.
**Related artifacts:**
- `.claude/artifacts/systems-analyst-test-2026-05-04.md` (first run — withheld from analyst per blind-run protocol)
- `.claude/artifacts/systems-analyst-real-data-2026-05-04.md` (real-data validation — withheld from analyst per blind-run protocol)

---

## Why this run exists

Alex re-asked the original question ("why does the content pipeline keep producing drafts that don't get published") one day after the 2026-05-13 goal-flip (YED-23) shipped. Re-dispatching the analyst on fresh data was premature (intervention is <24h old). Instead, Alex opted for a **fresh second-opinion, no priors** blind run — to test whether the prior diagnostic's conclusions hold up when the analyst forms hypotheses independently.

## Blind-run protocol applied

**Analyst was told to read:** CLAUDE.md, WORKFLOWS.md, the systems-thinking SKILL.md + references, and all content skills involved in the pipeline (pre-event-content, content-correspondent, pattern-synthesis, voice-pass, voice-editor agent, two-thesis-synthesis pattern).

**Analyst was told NOT to read:** prior systems-analyst artifacts (`.claude/artifacts/systems-analyst-*.md`), the v2 stage-2 proposal (`.claude/proposals/content-pipeline-v2-stage2.md`), or any Linear issue body for YED-23. These would have primed the analyst with the prior archetype conclusions.

**Acknowledged priming risk:** CLAUDE.md's `applications-to-software-and-product.md` reference file contains explicit prior archetype mentions ("Shifting the Burden ~80%", "Wrong Goal ~75%"). The analyst could not un-see these. Per the analyst's explicit posture-check: *"the structural evidence for [Seeking the Wrong Goal as primary] is independently present in the skill files. The priming may have made me more attentive to the Shifting the Burden dynamic than I would otherwise have been."*

## Headline divergence from prior diagnostic

The blind run **reordered the archetype rankings**:

| Archetype | 2026-05-04 (prior) | 2026-05-14 (blind) | Escape lever |
|---|---|---|---|
| Seeking the Wrong Goal | ~75% (secondary) | **82% (primary)** | LP #3 (Goals) |
| Shifting the Burden | ~80% (primary) | 74% (secondary) | LP #4 (Self-Organization) |
| Drift to Low Performance | ~50% (watch) | 52% (watch) | — |
| Tragedy of the Commons | Ruled out | Ruled out | — |

**Why the reordering matters:** the escapes diverge. The blind run argues for fixing *goal definition first* (redefine "done" = "shipped post," not "drafted post"). The prior run leaned toward *restoring native publishing capacity* (Shifting the Burden escape). The structural evidence cited for the blind reordering: every skill terminates at `Content Status: needs_review` as its success criterion — that is a production goal, not a publication goal. The Shifting the Burden match is "softer than canonical" — queue-overwhelm, not true capacity atrophy.

**Both runs agree on:** LP #3 (Goals) as the highest-leverage intervention; the perverse decay-as-relief outflow (B2 loop); ruling out Tragedy of the Commons; the counterintuitive warning against building a publishing-automation skill prematurely.

## Falsification triggers to watch (combined from both runs)

Action is gated on one of these firing. Until then: parked.

1. **Publish rate stays flat 4+ weeks after YED-23 goal-flip** + draft queue keeps growing → bottleneck wider than the system bound; reframe with LinkedIn audience / job-search competition in scope.
2. **Publish rate jumps but quality counter-metric crashes** → Goodhart; redesign the metric.
3. **Goal change feels fine to Alex + queue still grows** → not Shifting-the-Burden; pure capacity mismatch; use LP #5 (hard rule, e.g., "every event ships exactly one post by Friday or event closes unpublished").
4. **`approved` queue is large relative to `needs_review`** (observable in Notion at any time) → bottleneck is downstream of review at the publish-activation step; H2 priority flips away from `/voice-pass` wiring.
5. **Alex self-reports publishing block is quality-confidence, not queue volume** → upstream intervention (better skill outputs / efficient quality gate), not goal redefinition.

## Counterintuitive direction warning (both runs flag this)

**Do not wire `/voice-pass` end-to-end as the first H2 build.** It feels high-leverage (shorten `needs_review` → `approved` delay) but if the real bottleneck is the final publish act (Alex-as-publisher activation cost), automating polish only moves drafts faster into `approved` while `published` stays flat. The `approved` queue grows; net publish rate: zero. Ship H1 behavior change first, observe 2-3 weeks, then commit to H2.

Equivalent warning from 2026-05-04: a "build a publishing automation skill" would deepen the Shifting-the-Burden trap.

---

## Full blind-run diagnostic (verbatim)

# Systems Analysis: Content Drafts Accumulate in Notion Without Reaching Published Status

**Headline finding:** The pipeline embodies a Seeking the Wrong Goal trap compounding with a Shifting the Burden dynamic, producing a system where maximizing upstream throughput (research quality, draft volume) actively crowds out the intended downstream outcome (published posts). The two archetypes co-occur and mutually reinforce each other; the primary leverage point is LP #3 (Goals), specifically redefining what "done" means at the pipeline's operational level.

**Confidence:** 78% — moderately high. The structural evidence for both archetypes is clear and multiple. The Drift to Low Performance dimension is plausible but underspecified without longitudinal publish-rate data I cannot observe. The posture-check section notes the priming risk from CLAUDE.md.

---

## 1. Bounded System

**Parts:**
- Alex's NYC AI/tech event calendar (the raw input)
- `/event-deep-research` (Workflow A) — multi-agent research pipeline
- `pre-event-content` skill — generates LinkedIn posts, DMs, visual briefs, prepared questions
- `content-correspondent` skill — post-event outreach and public content
- `pattern-synthesis` skill — two-thesis cross-event posts
- `/voice-pass` (Workflow D) — polish layer (currently scaffolded, not wired end-to-end)
- Notion Content Drafts database — the accumulating queue (six status levels: `needs_review`, `approved`, `scheduled`, `published`, `archived`, plus implicit decay)
- Alex's attention, judgment, and time — the finite cognitive resource that bridges draft production and publication
- LinkedIn — the terminal destination (outside the boundary by instruction)

**Interconnections:**
- Event invites trigger research, which feeds into content-skill invocations
- Each research brief fans out to 4–7 draft assets per event (pre-event post + carousel brief + 2-3 DMs per person + prepared questions, plus synthesis post if two briefs pair)
- Every asset lands in Notion `Content Drafts` at `needs_review` — requiring Alex's review before any status transition
- Status can only advance through Alex's action (review, approve, schedule, publish) or decay (event passes, post becomes stale, entry is archived)
- The `/voice-pass` polish layer sits between `needs_review` and `approved` but is not yet wired end-to-end — meaning the path from draft to publish requires manual multi-step action Alex must initiate

**Function/purpose (deduced from behavior, not rhetoric):**
The system is producing and accumulating research briefs and content drafts at high volume. It is not, at the same rate, producing published content. Behavioral evidence of purpose: the system appears to be optimizing for completeness of the research and drafting artifact set, not for conversion of those artifacts to publication. The system "succeeds" at each upstream step independently of whether the downstream step fires.

**Boundary chosen:** Event-invite intake to `published` status in Notion with optional Published URL. This boundary captures the full handoff chain and includes the critical transition points where the stall is occurring (the review/approve/publish seam), while correctly excluding LinkedIn algorithm response.

**What's outside the boundary that might matter:**
- LinkedIn posting frequency norms (external standard Alex might be implicitly anchored to)
- Alex's energy state and job-search cognitive load — the job search runs in parallel and may be consuming the same review-and-publish attention that the pipeline needs
- The actual time elapsed between events and publication — without time-stamps on decay, we can't measure the magnitude of the decay outflow
- Feedback from published posts (comments, connection requests, DM replies) that would strengthen or weaken the publishing reinforcing loop — this loop is outside the boundary but starved of fuel *because* the system isn't publishing

---

## 2. Stocks and Flows

| Stock | Description | Current level | Desired level | Notes |
|---|---|---|---|---|
| **Content Drafts (needs_review)** | Drafts produced but not yet approved by Alex | Rising | Low / clearing regularly | Primary symptom — the accumulating queue |
| **Content Drafts (approved)** | Reviewed and approved, not yet shipped | Variable, under-observed | Should be thin/fast-clearing | CLAUDE.md flags this as "under-instrumented" |
| **Content Drafts (published)** | Successfully shipped to LinkedIn | Flat | Rising | The stated desired output |
| **Alex's review/publish attention** | Finite cognitive capacity available for review and publication acts | Fixed daily quota | — | Non-renewable within a day; the critical bottleneck resource |
| **Research briefs in Notion** | Completed event research briefs | Rising | Rising (healthy) | Inflow side is healthy; this is not the bottleneck |
| **Documentarian reputation (slow stock)** | Alex's standing as a consistent NYC AI/tech voice | Slow-rising | Rising faster | Starved of fuel by flat publish rate |
| **Drafts aged past event relevance** | Pre-event drafts whose event has already passed | Untracked | Should be 0 or explicitly archived | Silent stock — no explicit counter |

**Inflows (to the Content Drafts queue):**

| Flow | Rate | Controlled by |
|---|---|---|
| Pre-event draft creation | 4-7 assets per event × events per week | Volume of events Alex attends × skill invocations |
| Post-event draft creation | 3-5 assets per event via `content-correspondent` | Whether Workflow B is invoked after attendance |
| Pattern-synthesis draft creation | 0-1 per week (gated) | Whether two briefs in a 7-day window have opposing theses |
| Visual carousel briefs | 1 per LinkedIn post (mandatory, added 2026-05-12) | Tied to every LinkedIn post output — multiplies draft volume |

**Outflows (from the Content Drafts queue):**

| Flow | Rate | Controlled by | Type |
|---|---|---|---|
| Publication (needs_review → approved → published) | Flat, below inflow rate | Alex's review + publish actions | **Productive outflow — the intended one** |
| Decay/archival (needs_review → archived without publishing) | Unknown but likely substantial for pre-event drafts | Event timeline expiry; Alex deciding the post is no longer relevant | **Perverse outflow — looks like equilibrium but is loss** |

**Buffers:** The `approved` status is architecturally a buffer between review and publish, but CLAUDE.md flags it as "under-instrumented" — we don't know how much volume is sitting there vs. decaying before it ever reaches `approved`.

**Stocks at risk:**
- Alex's attention stock is the critical constrained resource. It is being drained by the review volume on the inflow side and is the sole throttle on the productive outflow. There is no second actor who can drain this stock positively.
- The reputation stock is slow-building and slow-decaying; it can tolerate the current flat publish rate for a while, but it will not grow without consistent publication cadence.

**Perverse outflow identification:** Pre-event content has a hard expiry — once the event passes without the LinkedIn post being shipped, that draft's relevance collapses. A `needs_review` pre-event post produced Monday for a Wednesday event that passes without publishing by Thursday is functionally dead. The Notion database does not appear to have a mechanism that loudly signals when a pre-event draft has crossed this expiry threshold. The decay happens silently, the queue appears stable (or the archived state grows), and the total published count does not move.

---

## 3. Feedback Loops

**R1 — Research-as-reward loop (currently dominant):**
Event added to calendar → research invoked → high-quality brief produced (fast, satisfying, visible) → positive reinforcement → more events added, more research invoked. Reinforcing. Dominant on the inflow side. No balancing loop on the inflow: there is no cap on events per week, no cap on assets per event, and the addition of carousel briefs (mandatory as of 2026-05-12) has increased the per-event asset count.

**R2 — Asset multiplication loop (currently dominant, accelerating):**
Each event produces 4-7 draft assets minimum (pre-event post + 3-slide carousel + 2-3 DMs per speaker/host + prepared questions). Adding more speakers = more DMs. Adding carousel briefs = more assets. More assets in `needs_review` = more review burden per event. Reinforcing. The gain on this loop increased with the mandatory visual brief addition.

**R3 — Publishing virtuous cycle (currently weak / starved):**
Post published → LinkedIn engagement → positive reinforcement for publishing → more publishing. This is the loop that should eventually become dominant but is currently starved because the productive outflow (publishing) is flat. Without fuel, R3 cannot overtake R1 and R2.

**B1 — Review-as-bottleneck (undersized balancing loop):**
Drafts accumulate in `needs_review` → review pressure builds → Alex reviews and approves → drafts move toward publication → queue decreases. This should be the primary corrective loop. It is undersized because: (a) the volume of drafts entering the queue now significantly exceeds the volume Alex is clearing in review sessions; and (b) the `/voice-pass` polish layer, which was meant to support this loop, is not yet wired end-to-end.

**B2 — Decay-as-relief (perverse balancing loop, currently active):**
Pre-event drafts age past event date → drafts archived or abandoned → queue appears to stabilize → no alarm fires. This loop provides relief to the `needs_review` stock level in a way that looks identical to B1 (publishing) at the stock level. But the outflow is loss, not delivery. The system has no information structure to make this visible. This loop's dominance is the quietest failure mode in the pipeline.

**Delays:**
- Between event invite and research brief: same session (short, well-solved by Workflow A).
- Between research brief and content skill invocation: variable; depends on Alex initiating. Could be days.
- Between draft creation and review: unknown, but structured evidence suggests it can be long (drafts accumulate).
- Between review and publication: unknown; Workflow D (voice-pass polish) is scaffolded but not wired, meaning this step requires additional manual action.
- Between publication and feedback (engagement → confidence → more publishing): days to weeks; this is the longest feedback delay in the system and explains why R3 is not providing signal to push through the bottleneck.

**Currently dominant loops:** R1 (research-as-reward) and R2 (asset multiplication) on the inflow side. B2 (decay-as-relief) on the outflow side, masking the absence of B1.

**Loops likely to dominate next (if nothing changes):** B2 will continue to act as primary relief valve. The Content Drafts queue will appear to stabilize or grow slowly while the actual published count stays flat. The decay metric will be unobservable because it is not being measured separately from productive publication.

---

## 4. Archetype Check

### Match (high confidence): Seeking the Wrong Goal — 82%

**Evidence:**
The pipeline's definition of "done" is structural production, not publication. Every skill in the pipeline terminates in a Notion write with status `needs_review`. The skills' success criteria are:
- Research brief: "wrote to Notion"
- Pre-event content: "N content pages created, all relations linked"
- Pattern-synthesis: "Content Draft URL returned, both variants inline"
- Voice-pass: scaffolded entirely — not yet creating a "done" state for publication

The system is "working perfectly" by its own metrics (briefs created, drafts created, assets per event) while the underlying desired outcome (posts published) diverges. This is the canonical Seeking the Wrong Goal structure from `system-archetypes.md`: "System behavior is exquisitely sensitive to the goals of feedback loops. If the goal is defined inaccurately or incompletely, the system will obediently produce a result that isn't really wanted."

The metric that all four workflow skill outputs terminate in — `Content Status: needs_review` — is a production metric. There is no equivalent pipeline-level metric for `published`. The Content Drafts DB has a 🎯 Active Kanban view, but no publish-rate counter visible to the pipeline at invocation time.

### Match (high confidence): Shifting the Burden — 74%

**Evidence:**
The skills are designed to relieve Alex of the effort of producing high-quality content from scratch — which is correct and intended. But the structural consequence is that the high-friction step has shifted, not been solved. Previously, Alex faced "blank page + no research + no drafts." Now he faces "full queue + many options + still must decide and publish." The skills have solved the upstream problem (research, drafting) while the downstream problem (review-approval-publish decision-making and action) has grown in proportion to the volume of drafts.

The Shifting the Burden diagnosis is partial here because the classic form requires the system's "own capacity to solve the problem" to atrophy. There is structural evidence this is beginning: the review and publish step is getting harder, not easier, as more drafts accumulate. A large `needs_review` queue is itself a psychological barrier — more items to review = more friction to even start the review session. This is the addiction loop's reinforcing structure: the more the skills produce, the larger the review burden, the less often review sessions happen, the more pre-event drafts decay, the more the system produces new ones to try again.

**The structural distinction from pure Shifting the Burden:** in the textbook form, the intervenor takes over a function the system previously performed. Here, the intervenor (AI skills) performs a function Alex never performed well at volume (structured event research + multi-format draft production) — so this isn't a straight capacity-atrophy story. The burden has been shifted to a new step that did not previously exist at this volume, not to a step that Alex previously owned. This is why I rate it 74%, not 85%+.

### Match (medium confidence): Drift to Low Performance — 52%

**Evidence:**
If the flat publish rate has become the ambient expectation — "I produce briefs and drafts and occasionally ship a post" — then the standard for publishing is quietly drifting toward whatever rate is currently being achieved. The cadence rule in `content-correspondent` (`within 24h for first-touch DMs`, `within 24h for Tier 2 post`) is stated but unenforceable by the pipeline; there is no balancing loop that fires when 24 hours pass without a post being shipped. The goal is de facto defined by recent behavior.

I rate this at 52% (medium) because without time-series data on the publish rate over multiple months, I can't confirm the drift is occurring rather than simply starting from a low baseline. This archetype requires evidence of a downward trend, not just a low level.

### Considered and ruled out:

**Tragedy of the Commons:** Ruled out. The Commons archetype requires multiple actors externalizing cost onto a shared resource. The system has one primary actor (Alex). The skills are not "users" in the bounded-rationality sense — they do not have goals of their own that diverge from Alex's. What might superficially resemble Commons (unlimited skill invocations draining the attention resource) is not a Commons structure because the cost lands on the same actor making the decision. There is no externality; there is no second actor bearing the cost. Escape paths diverge sharply: Commons → privatize/regulate access; the actual problem here → goal restructuring. Ruling out Commons is important because applying its escape (limiting skill invocations) would reduce input quality without fixing the publish-rate problem.

**Policy Resistance:** Ruled out. Policy Resistance requires multiple actors pulling a stock toward competing goals. Alex is the system's only goal-setting actor. The skills have no goals that conflict with Alex's stated goal of publishing. The resistance here is not multi-actor conflict; it is a single-actor goal-definition gap.

**Escalation:** Ruled out. Escalation requires two stocks competing where each side's response provokes the other. There is no second competitor escalating against Alex's content production.

**Success to the Successful:** Partially relevant but not the primary archetype. Research-as-reward has a "winner gets more" quality (successful events produce more research, more research leads to more events being added), but the critical bottleneck is not about competitive exclusion between content types or assets. Ruled out as the primary diagnosis.

**Rule Beating:** Ruled out. There are no rules being gamed. The pipeline's issue is not actors evading the spirit of rules while complying with their letter; it is that the rules (skill success criteria) are pointed at the wrong goal.

---

## 5. Players and Incentives (Bounded Rationality)

Alex's multiple roles are treated as separate actors because the seam between them is structurally load-bearing. This follows the pattern from `feedback-loops-stocks-flows.md` §5c: "the leverage point is often the seam between two roles within the same person."

| Actor | Stated goal | Operational goal (deduced from behavior) | Information they have | Incentives |
|---|---|---|---|---|
| **Alex-as-researcher** | Build deep, useful event research | Complete a research brief for the current event | Recent news, speaker bios, topic landscape for one event | Immediate reward: high-quality brief produced; positive feedback from the synthesis step |
| **Alex-as-drafter** | Produce strong LinkedIn posts, DMs, prepared questions | Complete the set of draft assets for one event; fill in all skill outputs | Research brief, content style guide, anti-patterns | Immediate reward: drafts written; variants produced; visual briefs attached |
| **Alex-as-reviewer** | Approve the best drafts for publication | Reduce the `needs_review` queue | All drafts in the queue at review time, but reviewing requires re-engaging context for each event's research | Reward is diffuse and delayed; the queue is large; starting a review session has a high activation cost proportional to queue depth |
| **Alex-as-publisher** | Ship content to LinkedIn | Publish one specific post | Approved draft content, LinkedIn UI, current state of Alex's personal energy and schedule | Reward is distant (LinkedIn engagement arrives days/hours after posting); friction is the act of context-switching to LinkedIn, adding hashtags, selecting the right variant, and pressing send |
| **Alex-as-job-seeker** | Get a role at an AI-native company | Prioritize activities most directly connected to job-search outcomes | Open roles, networking opportunities, events, parallel job-search tasks | High-urgency, high-cognitive-load activities competing with review-and-publish for the same daily attention stock |

**The bounded rationality finding:** Each role is behaving locally rationally. Alex-as-researcher invokes the skills when events are upcoming — correct and high-value. Alex-as-drafter runs the skills to completion — correct. Alex-as-reviewer faces a growing, multi-event, multi-format queue and must make a context-load decision to even enter review mode. Alex-as-publisher faces a separate activation to actually send. Alex-as-job-seeker has competing claims on the same attention. No role is misbehaving; the aggregate is a system where the productive outflow (publication) is consistently crowded out by the demands of the other roles running simultaneously.

**The seam with highest friction:** The transition from Alex-as-drafter to Alex-as-reviewer is the highest-friction seam. Drafts are produced in the same session that generates the research brief. Review is implicitly deferred to a later session — the skill instructions say "Alex reviews and moves to `approved` when ready to post." There is no structural mechanism in the pipeline that forces or triggers that later session.

---

## 6. Leverage Points (in increasing order of effectiveness)

**Currently being pushed (and direction):**

- **LP #12 (Numbers/Parameters)** — being pushed in the wrong direction. The addition of mandatory carousel briefs per LinkedIn post (2026-05-12) increased the per-event asset count without increasing the review/publish throughput. More drafts → more review burden → lower publish rate. This feels like "more output = better" but increases the drain on the constraint.
- **LP #9 (Delays)** — being pushed in the right direction on the inflow side. Workflow A closes the research-to-brief delay in hours. This is good leverage, correctly applied, but it only shortens the upstream delay. The downstream delay (draft-to-published) is not being attacked.
- **LP #5 (Rules)** — being pushed in a mixed direction. The definition-of-done for every content skill terminates at `needs_review` write to Notion. This rule correctly governs skill output but implicitly defines "complete" as "written to Notion," not as "published."

**Highest workable leverage point — LP #3 (Goals):**

Redefine the pipeline's operational goal. Currently, every skill, every workflow step, and every success-criteria block terminates at the same operational goal: "wrote assets to Notion at `needs_review`." That is a production goal. The system goal is publishing. The intervention: redefine "done" for any given event's content cycle as "one post published to LinkedIn," not "drafts written to Notion."

This goal change has cascade effects:
- It reframes the pre-event content skill's Step 8 summary from "N content pages created" to "which one post is most likely to ship before the event?"
- It legitimizes shipping fewer, higher-priority drafts per event instead of all possible drafts
- It changes the information that the pipeline surfaces at completion ("here are 7 drafts" → "here is the one post you should ship today, and here are the others in the queue")

From `leverage-points.md` #3: "The intervention: 'I have watched in wonder as — only very occasionally — a new leader in an organization comes in, enunciates a new goal, and swings hundreds or thousands or millions of perfectly intelligent, rational people off in a new direction.'" In this single-actor system, Alex enunciating the new goal to himself and encoding it in the skill success criteria is the equivalent move.

**Next-highest if LP #3 is blocked — LP #6 (Information Flows):**

Make the decay metric visible and loud. Currently there is no dashboard or pipeline-level output that shows: (a) drafts created this week, (b) drafts published this week, (c) drafts that have aged past event relevance. The B2 (decay-as-relief) loop is invisible. Routing this information to Alex-as-reviewer each time a content skill completes ("You have 14 drafts in needs_review; 3 have passed their event date") would change the decision Alex-as-reviewer is making with each review session.

From `leverage-points.md` #6: "Missing information flows is one of the most common causes of system malfunction. Adding or restoring information can be a powerful intervention, usually much easier and cheaper than rebuilding physical infrastructure."

**Counterintuitive direction warning — LP #9, wrong direction:**

The intuitive next build is Workflow D (voice-pass) end-to-end automation. This feels like a high-leverage move because it shortens the delay between `needs_review` and `approved`. But if the bottleneck is not the polish step (which is plausible — most drafts written by the skills are already of decent quality before the voice-pass) and is instead the publish-decision step (Alex-as-publisher activating to ship), then automating voice-pass merely moves drafts faster from `needs_review` to `approved` without increasing the rate at which they exit `approved` to `published`. The `approved` stock grows instead of the `needs_review` stock. Net publish-rate improvement: zero.

The second intuitive build — adding more content types or more format variants per event — is directly counterproductive. It increases R2 (asset multiplication) without touching B1 (review-as-bottleneck). This is the Seeking the Wrong Goal direction: optimizing draft quality and draft completeness while the system's actual goal is publish rate.

---

## 7. Second-Order Effects of Recommended Intervention

**Recommended intervention:** Redefine the operational goal (LP #3) — encode "one published post per event" as the skill's and pipeline's success criterion, surfaced at skill-completion time.

**Immediate (first-order):** The pre-event content skill would need to change its Step 8 summary and its framing of what to hand to Alex. Instead of "here are 7 drafts," it would present: "here is the one post recommended for shipping before [event date]." The Notion `Content Drafts` completion view would surface the publish-priority asset distinctly from the supporting assets.

**After system response (second-order):** Alex-as-reviewer now faces a single-item decision per event rather than a multi-item queue scan. The activation cost of a review session drops. More review sessions happen. The `needs_review` to `approved` transition rate increases. Some volume of DM drafts and prepared-question drafts are written but explicitly de-prioritized for review (they can be retrieved if needed but are not in the primary review queue).

**After actor adaptation (third-order):** Alex-as-publisher begins shipping posts with more regularity. R3 (publishing virtuous cycle) begins to receive fuel: engagement comes back, confidence in the format grows, the documentarian identity reinforces. The slow reputation stock begins to actually accumulate. This creates a positive reinforcing loop that the current system is unable to ignite because the fuel (published posts) is not consistently available.

**Pre-mortem failure modes:**
- Alex-as-researcher is not willing to accept "fewer drafts per event" as an acceptable outcome. The completeness of the research brief is deeply satisfying and the constraint on draft count feels like a quality reduction. If this happens, the goal redefinition fails at the paradigm level — Alex's model of "complete event preparation = all possible assets produced" is the actual blocker.
- The single recommended post is wrong — it's not the post that should ship, and Alex-as-publisher overrides the recommendation, creating a new decision loop on top of the old one. If this happens, the information-flow intervention (LP #6 decay dashboard) should be the primary move instead.
- The publish bottleneck turns out not to be about queue size but about Alex's confidence in any individual post's quality. In that case, the polish step (Workflow D fully wired) is actually the right build, and this analysis has misdiagnosed the constraint.

**New loops introduced:** A lightweight per-event "recommended publish" designation would create a new balancing loop — B3: growing queue of pending recommended posts → urgency signal → publish decision → queue decreases. This loop did not previously exist because the system had no mechanism to distinguish "recommended for immediate publication" from "in queue."

**Loops removed:** B2 (decay-as-relief) would be partially weakened — if pre-event drafts are published before event expiry, the decay outflow decreases. This is the intended effect.

---

## 8. Posture Check

**What I might be wrong about:**

1. **The bottleneck location.** I have diagnosed the seam between Alex-as-drafter and Alex-as-reviewer as the primary friction point, based on structural inference (voice-pass not wired, no publish trigger, skills all terminate at `needs_review`). I cannot observe actual session logs, time-stamps of draft creation vs. publication, or Alex's stated reason for non-publication. It is possible the bottleneck is further downstream — between `approved` and `published` — in which case the failure is not about review friction but about the activation cost of the final publish act (opening LinkedIn, selecting the variant, pressing send).

2. **Whether the decay outflow is actually substantial.** I inferred substantial decay based on the structural architecture (pre-event posts have hard event-date expiry; the pipeline produces them 4-7 per event; publishing is flat). But decay rate is not directly observable from the documents I read. If Alex is consistently archiving all pre-event drafts intentionally after events, the decay may be a deliberate choice rather than a system failure.

3. **Whether the visual brief addition (2026-05-12) materially worsened the problem.** The addition of mandatory carousel briefs per LinkedIn post increased per-event asset count. I have treated this as a gain-increase on R2 (asset multiplication). But if the carousel briefs are actually making the post easier to evaluate and approve (more concrete = easier review decision), the effect may be neutral or positive on review rate. I cannot observe this without data.

4. **Archetype-match confidence.** The Shifting the Burden match at 74% rests on the inference that the review-and-publish capacity is being suppressed by the volume of upstream output. In the textbook archetype, the intervention causes the system's "own capacity to atrophy." Here the mechanism is more about queue overwhelm than atrophy — Alex still could publish, but the queue makes starting harder. This is a softer version of the archetype than the canonical form.

**What I'd want more evidence on before committing:**

- Time-stamp data: how many days elapse between draft creation and the event date for drafts that are never published? If it's consistently less than 48 hours (drafts created but event passes within two days of research), the problem is a timing/scheduling issue, not a queue-volume issue.
- The `approved` stock: how many drafts are sitting in `approved` status without moving to `published`? If the `approved` queue is large, the bottleneck is downstream of review (at the publish act itself). If `approved` is thin or empty, the bottleneck is at the review step.
- Alex's self-diagnosis: what does Alex believe is the reason posts don't get published? The answer will reveal whether the bounded rationality finding matches Alex's own experience.

**Where this analysis is extrapolating beyond the canonical source:**

- The "B2 — decay-as-relief" loop is grounded in the canonical reference (`feedback-loops-stocks-flows.md` §5b on perverse balancing loops), which was itself surfaced from a prior systems-analyst run on this same pipeline. I am not extrapolating the concept; I am applying it to the specific content-expiry dynamic here, which is a valid application.
- The "job-search parallel cognitive load" as a competing claim on Alex's attention stock is a real factor I inferred from CLAUDE.md's standing-context section ("job searching in parallel"). Meadows does not address single-actor multi-goal attention competition directly; I am extrapolating from the bounded-rationality framework to apply it to competing goal-priorities within one person. This extrapolation is reasonable but not sourced in the canonical texts.

**Explicit posture-check on CLAUDE.md priming:**

CLAUDE.md's `applications-to-software-and-product.md` section contains explicit prior archetype diagnoses: Shifting the Burden (~80%), Seeking the Wrong Goal (~75%), Drift to Low Performance (~50%), with Tragedy of the Commons explicitly ruled out. I read this file as part of loading the canonical reference set and cannot fully un-see it.

My independent diagnosis: Seeking the Wrong Goal (82%, primary) and Shifting the Burden (74%, secondary), with Drift to Low Performance at 52% (watch). These rankings differ from the prior run in one meaningful way: I place Seeking the Wrong Goal as the primary archetype, where the prior run appears to have placed Shifting the Burden first. This is not just reordering — the escapes differ. Seeking the Wrong Goal is escaped via LP #3 (Goals) — redefining what the system is optimizing. Shifting the Burden is escaped via LP #4 (Self-Organization) — restoring the system's own capability to solve the problem. My analysis landed at the Goal lever as higher-priority.

If I had read no CLAUDE.md prior-analysis content at all, I believe I would have: (a) independently arrived at both archetypes (the structural evidence is clear), (b) placed Seeking the Wrong Goal first based on the consistent pattern of all skills terminating at `needs_review` as the success criterion, and (c) been more uncertain about the Drift to Low Performance component. The priming may have made me more attentive to the Shifting the Burden dynamic than I would otherwise have been, but the structural evidence for it is independently present in the skill files.

---

## Recommendation

**Highest-leverage intervention:** Redefine the pipeline's operational "done" criterion — at the skill level and at the weekly-cadence level — from "wrote N drafts to Notion" to "shipped one post per event to LinkedIn," operating on Leverage Point #3 (Goals), expected to address the Seeking the Wrong Goal archetype primarily, and to relieve the Shifting the Burden compounding secondarily by making the review decision simpler and more binary.

**Confidence:** 72% — moderately confident. The structural evidence is clear; the actual implementation path has execution risk (requires changing the framing of multiple skill success criteria and Alex's operating habit, not just code changes).

**What I'd watch for after intervening:** Publish rate in the four weeks following the goal redefinition. The target signal is at least one LinkedIn post published per event within 72 hours of the event. If publish rate increases but drafts in `approved` grow instead of in `needs_review`, the bottleneck has shifted downstream (the final publish act) and Workflow D wiring becomes the next intervention.

**What would tell us this analysis is wrong:**
1. Alex reports that he does review drafts regularly but doesn't publish because he doesn't think any of the variants are good enough. If this is true, the bottleneck is quality, not goal-definition or queue volume — and the intervention is upstream (better skill outputs or a more efficient quality gate) rather than a goal redefinition.
2. The `approved` queue is large relative to `needs_review` (observable in Notion). This would indicate Alex is reviewing fine but not publishing — the bottleneck is the final publish act, not the review act, and the goal-level intervention is less relevant.
3. Publish rate does not increase after goal redefinition, despite Alex explicitly attempting it. This would suggest the paradigm-level mental model ("complete event preparation = all possible assets produced") is stronger than the goal-level intervention can override, and the intervention needs to move to LP #2 (Paradigms).

---

## Per-Horizon View

**H1 (MVP-level fix — can do this week):**

Two changes that require no build, only behavior and framing:

1. At the end of every content skill invocation, Alex-as-drafter explicitly designates one draft as "the post to ship." This does not require wiring Workflow D or changing Notion schema. It requires one additional step: "of these 7 drafts, which one ships by [event date]? Name it now." The act of designation creates a commitment.

2. Set a single observable counter: after every content run, note the number of posts in `published` status in the Content Drafts DB. This is the only metric that matters for the next four weeks. Not drafts created, not drafts in review.

These are LP #6 (Information Flows) + LP #3 (Goals) interventions at minimum cost. Total time to implement: one conversation to update the skill's Step 8 summary template and establish the tracking habit.

**H2 (Scaling-level investment — can do this quarter if H1 validates):**

If H1 produces a publish-rate increase, the following investments are warranted:

1. Wire Workflow D (`/voice-pass`) end-to-end. Once drafts are being reviewed and published regularly, a batch polish pass becomes genuinely useful (right now it's upstream of the real bottleneck and will not change the publish rate). The wiring TODO is already documented in the `/voice-pass` scaffold.

2. Add an information-flow layer: a weekly summary at the start of each session (or via the SessionStart hook referenced in CLAUDE.md) that shows (a) events researched in the last 14 days, (b) posts published in the last 14 days, (c) drafts in `needs_review` older than the event date they were written for. This is the decay-visibility intervention at LP #6. The SessionStart hook (YED-26, now shipped) is the right vehicle.

3. Revisit the per-event asset count. If one post per event is the goal, the mandatory carousel brief adds production volume but may also add review friction. Evaluate whether the carousel brief should be optional (invoked only when a post is actually being shipped) rather than mandatory on every draft.

**H3 (Paradigm-level — deferred until a clear trigger fires):**

Do not do this work until H1 and H2 interventions have been running for at least 60 days and the publish rate has been measured.

The H3 question is paradigmatic: is the documentarian-of-NYC-AI identity (the pipeline's implicit goal structure, and therefore its Paradigm per LP #2) still the correct operating frame for Alex's actual stated goals (job pipeline, reputation, ongoing learning)?

The pipeline was designed around the documentarian angle, but the documentarian value proposition only compounds if content is actually published consistently. A paradigm that produces research quality at the expense of publish rate is not serving its own goal. The H3 intervention would be a quarterly explicit review of the paradigm: "Is this pipeline optimizing for the right outcome, or has the operating paradigm drifted from the goal?" This is LP #2 territory and is correctly deferred — it is not an H1 problem, and attempting to address it at H1 would produce analysis paralysis instead of action.

**Horizon trade-off explicit statement:** Do not build H2 (voice-pass wiring) before H1 validates that the review-and-publish bottleneck is the correct diagnosis. Building Workflow D before confirming the bottleneck location risks the counterintuitive failure mode described in Section 6: it makes drafts flow faster through `needs_review` to `approved` while the publish rate stays flat. Ship the H1 behavior change first, observe for 2-3 weeks, then commit to H2 build.
