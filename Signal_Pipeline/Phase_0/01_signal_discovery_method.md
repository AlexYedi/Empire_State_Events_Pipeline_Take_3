# Phase 0 — Signal Discovery Method

**Status:** V0, 2026-04-21. Written before execution. Expect meaningful revision after first pass against real data.
**Precondition:** `00_data_inventory_protocol.md` has been run and `inventory_findings.md` exists.
**Output:** `signal_seed_list.md` — the 5–10 named signal types that Phase 1 builds ingestion for.

---

## The core question

*What, of the data we already have, predicts "worth writing about / worth reaching out on" — for Alex's specific goal of a Clay-tier GTME role?*

Notice the framing: we're not asking what predicts buyer intent for a SaaS product, or what predicts likelihood-to-purchase for a B2B company. Those are the questions the reference sources (Clay, Pocus, Common Room) answer, and they're load-bearing but not *our* question.

Our question is narrower and easier to validate empirically, because we have a ground truth: *Alex already has a record of what he chose to write about, DM about, and apply to.* That history IS the training signal. The modeling exercise is working backwards from "what did I engage with" to "what attributes, if I'd seen them ahead of time, would have told me to engage?"

---

## Why this is not a watchlist exercise

The instinct (which I defaulted to last turn and got pushed back on correctly) is to construct a watchlist — "these 25 companies, these 12 humans" — and then build a pipeline around it. That's a *thesis-first* approach. The problem is:

1. The named watchlist was built from Clay's blog and Alex's skills-map. It's theoretically grounded but empirically unvalidated for Alex's specific goal. Some of those companies/humans may turn out to produce signal Alex doesn't actually engage with.
2. A watchlist is a filter on *who*, not on *what kind of signal*. If the signal type is wrong, a perfect watchlist produces useless data.
3. A watchlist grows stale. A *signal type* stays relevant across changing rosters.

Signal discovery asks the opposite question: *what categories of observable events, if we saw them, would consistently be worth Alex's attention?* Then it matches those categories against the existing data to see which are actually detectable at our scale and cost.

---

## The method, in four steps

### Step 1 — Candidate signal enumeration (2 hours)

From the inventory findings + the clay-play-patterns cheat sheet + the skills-map named operators, list every *kind* of event that could plausibly be a signal for Alex. Don't filter. Include obvious ones and weird ones. Target: 30–50 candidates.

Group by level:

**Company-level signal candidates**
- Funding round (Seed through Public)
- Exec hire / departure
- Public-facing GTME / RevOps / Growth role posted
- Product launch touching agentic / GTME-adjacent surface
- Customer win or case study published
- Conference / event hosting
- Podcast appearance by company exec
- Public POV (blog post, LinkedIn article) from company leadership on GTME topics
- Open-source release or contribution
- Partnership announcement
- Competitive positioning shift (messaging change on website)
- Layoff / restructuring
- Office / geographic expansion
- Pricing change or packaging change (signals monetization shift)
- M&A (acquiring or being acquired)

**Person-level signal candidates**
- New role / job change
- Promotion to a role Alex is targeting
- Public POV post on a topic Alex tracks
- Podcast / conference appearance
- Book / long-form publication
- LinkedIn post reaction/comment from a target-company employee to another target-company employee (visible transitively through your network)
- Engagement with Alex's content (reaction, comment, visit, follow, connect)
- Recently-mutual connection
- Shared event attendance (your Events DB has this)
- Topic-overlap signal: they wrote about a topic you also wrote about

**Topic-level signal candidates**
- New entrant into a topic (company or person)
- Consensus shift on a topic (what was contested is now settled, or vice versa)
- Velocity spike (suddenly many public posts on a topic)
- Velocity collapse (topic going stale)
- Intersection activity (two of your tracked topics suddenly overlapping)
- Academic / research milestone (paper, benchmark)
- Tooling milestone (new framework, library, product category)

**Alex's-own-funnel signal candidates**
- Event attended produced N meaningful conversations
- Content published produced M engagements
- DM sent produced reply / no reply
- Project shipped produced demo-worthy output
- Interview scheduled / completed / converted

The last group is the most important and the most ignored. Alex's own outputs and their outcomes are the highest-signal training data we have.

### Step 2 — Per-signal availability check (3–4 hours)

For each candidate, answer four questions:

1. **Is this detectable at all?** (Are the events actually published somewhere we can read? Or are they private by default?)
2. **Is it detectable from free / already-paid sources?** (Our budget constraint says yes to free + already-paid, no to new paid tools pre-MVP value-proof.)
3. **What's the detection latency?** (Real-time? Daily? Weekly? Months-delayed?)
4. **What's the noise rate?** (If we fired on every occurrence, how many false positives per real one? Rough estimate.)

Produce a table:

| Signal candidate | Level | Detectable? | Free? | Latency | Noise rate | Notes |
|---|---|---|---|---|---|---|
| Funding round | Co | Yes | Crunchbase Basic / Google News | 1–3 days | Low | Annual |
| Public-facing GTME role posted | Co | Yes | LinkedIn Jobs RSS / company careers page RSS | 1–2 days | Medium | Title taxonomy fuzzy |
| Exec hire | Co | Yes | LinkedIn Posts (they post it) / news / company blog | 1–7 days | Medium | "New hire" ≠ "GTM hire" |
| Person job change | Per | Yes | LinkedIn (via official API only — very limited), news if notable | Variable | Medium | No bulk tracking |
| LinkedIn engagement w/ target | Per | Partial | Your own notifications / export; not bulk | Same-day | Low on own posts | |
| Podcast appearance | Per/Co | Partial | Podcast RSS; transcripts expensive until Week 4+ | Days–weeks | Low | Transcripts needed for actual content mining |
| ... | ... | ... | ... | ... | ... | ... |

Anything with **Detectable = No** or **Free = No** gets deferred or deleted.

Anything with **very high noise rate** gets flagged for hygiene / suppression work, not modeling work.

### Step 3 — Ground-truth check against Alex's history (2–3 hours)

This is the step that makes this method work. For each remaining candidate, run a retrospective check against the inventory findings:

**The question:** for the content Alex has actually written about and the people he's actually reached out to, was the signal *present* before the action?

Example for "public POV post from target person":
- Look at the Content Drafts Alex published that were about or referenced a specific target-list person.
- For each, check: did that person post a public POV within 30 days before Alex wrote about them?
- If yes for most → strong signal. If no / rarely → either Alex isn't discovering targets this way, or this isn't a high-quality signal for his workflow.

Example for "funding round":
- Look at the Content Drafts Alex wrote about a specific company.
- Did a funding event for that company precede by 0–90 days?
- If yes sometimes → decent signal. If almost never → Alex's content isn't funding-driven, which is fine, just means this isn't our signal.

Example for "shared event attendance":
- Look at the People Alex has sent DMs to (capturable via HubSpot Notes + Content Drafts with DM content types).
- Did that person appear in an Event Alex attended?
- If yes almost always → this is a dominant signal and the events pipeline is doing its job as a signal source.

Produce a small table scoring each candidate:

| Candidate | Times Alex acted with signal present | Times Alex acted without it | Precision estimate | Keep / Defer / Drop |
|---|---|---|---|---|
| Shared event attendance | 15 / 15 DMs | 0 | Very high | Keep (core) |
| Public POV post (target person) | 6 / 20 posts | 14 | Medium | Keep (useful, not dominant) |
| Funding round | 2 / 20 posts | 18 | Low for Alex | Defer |
| Job change | 4 / 20 posts | 16 | Low-med | Defer |
| ... | ... | ... | ... | ... |

**The hard rule:** if a signal candidate has zero historical hits in Alex's acted-on data, we do not build ingestion for it in Phase 1. Period. We can revisit later, but Phase 1 ingestion is for signals we've already proven matter.

### Step 4 — Select the 5–10 "seed signals" (1 hour)

From the survivors, pick 5–10 that together meet these criteria:

- **At least 3 are high-precision for Alex's existing behavior.** These are the workhorses.
- **At least 1 is a novelty signal** — something Alex doesn't currently discover through, but that you've identified as likely valuable. Treat it as an experiment with explicit measurement.
- **At least 1 is an Alex's-own-funnel signal** — something about his own output/outcomes, not about targets. This is the feedback loop that makes the system improve.
- **No more than 2 require new paid tooling.** Honor the budget.
- **At least 3 have detection latency under a week.** Real-time-ish signals drive content cadence.

Document each in `signal_seed_list.md` with the five-box anatomy from `clay-play-patterns.md`:
- Trigger (the raw event)
- Qualifier (fit gate — is this target-universe?)
- Derived attribute (what we'd model from the raw event)
- Suppression (who to exclude)
- Activation (what action we'd plausibly take — ≤2 per signal, keep it narrow)

**This list is the input to Phase 1.** Phase 1 builds ingestion for exactly these signals. Nothing else. If during Phase 1 we discover a signal is cheaper or more valuable than we thought, we revise this doc and the phase plan — not sideload.

---

## What "let the data speak" protects us from

Three failure modes. Naming them explicitly so we can catch ourselves.

1. **Thesis laundering.** Constructing the watchlist from the Clay blog, then "validating" it by reading the blog again. The inventory + ground-truth check forces the validation to happen against *Alex's own acted-on data,* which we can't manipulate after the fact.

2. **Framework gaming.** Building sophisticated modeling on signals because the framework *looks impressive for interviews,* not because the signals actually predict. The ground-truth check makes this visible: a signal with zero historical hits is framework-gaming if we ship it anyway.

3. **Activation anchoring.** Choosing signals because we already have an activation idea we like (e.g., "I want to write a weekly digest" → "so I need weekly-cadence signals"). The method pushes activation to Step 4, after we've already filtered for detectability and precision. The activation emerges from the signals, not the other way.

---

## Key judgment calls

Flagging these so they get explicit decisions rather than drifting:

1. **How thin is too thin?** If Alex's history of published content is under 10 posts, the ground-truth check is statistically thin. In that case: run the method anyway as directional, but explicitly mark the seed list as V0-pending-more-data. Revisit at Phase 1 midpoint.

2. **What counts as "acted on"?** Default: a Content Draft with `Content Status = published` or `approved`, OR a DM recorded in HubSpot Notes / Content Drafts. We might broaden to "a Project Idea scored > 8.0" if the discovery needs more data points.

3. **Novelty-signal budget.** One experimental signal per seed list is the cap. Two is drift. If we're tempted to add a second novelty, one of the workhorses is probably overkill and should be demoted instead.

4. **When does the seed list get revised?** Quarterly by default, OR immediately when Phase 1 ingestion reveals a signal's real noise rate is dramatically different from the Step 2 estimate. Revision is expected; drift isn't. Document revisions in a `signal_seed_list_changelog.md`.

---

## What this method does NOT attempt

- **Predicting external outcomes** (who's about to raise a round, who's about to get acquired). That's a B2B sales-intel use case and not what we need.
- **Building a general-purpose signal platform.** This is scoped to Alex's personal GTM funnel. Generalization is explicitly out of scope.
- **Replacing the events pipeline.** The events pipeline is the first and best signal source; it's a *module* in the signal layer, not a thing being subsumed.

---

## Output of the discovery method

One file: `signal_seed_list.md`. Each entry contains:

```
## Signal N — [name]

**One-sentence description:**

**Trigger:** [the raw event type]

**Detection:** [source, latency, cost]

**Qualifier:** [fit gate — what makes this target-universe for Alex specifically]

**Derived attribute:** [the modeled value we'd compute — what cardinality, what freshness]

**Suppression:** [who / what to exclude]

**Possible activations:** [≤2 concrete actions Alex might take]

**Historical precision in Alex's data:** [from Step 3 — X of Y acted-on events had this signal present]

**Phase 1 priority:** [P0 workhorse / P1 supporting / P2 experimental]

**Hygiene dependencies:** [what entity identity / dedup / suppression work must exist before this signal can be ingested cleanly]
```

The full file is the input to Phase 1 scoping. It's also a writeup-grade portfolio asset: a rung-2 modeling document with empirical grounding. That's genuinely rare in the candidate pool.
