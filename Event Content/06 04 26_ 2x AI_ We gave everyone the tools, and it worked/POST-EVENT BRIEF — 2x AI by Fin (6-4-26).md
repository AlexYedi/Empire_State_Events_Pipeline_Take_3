# POST-EVENT BRIEF — "2x AI: We gave everyone the tools, and it worked"

**Event:** 2x AI: We gave everyone the tools, and it worked
**Date / venue:** 2026-06-04 (Thu), ~6:22pm ET · 18 E 50th St, New York, NY
**Host org:** GenAI Collective NYC (now "The AI Collective") — NYC chapter led by Prithvi Rajasekaran
**Speakers:** Brian Donohue (VP Product, Fin — formerly Intercom) · Prithvi Rajasekaran (Member of Technical Staff, Anthropic Labs) · moderator (name unconfirmed — see flags)
**Companion essays:** Darragh Curran, *"2×"* (`ideas.fin.ai/p/2`) and *"2× – nine months later: We did it"* (`ideas.fin.ai/p/2x-nine-months-later`, Apr 16 2026); Andrii Yakovenko, *"We Gave Claude Code to Everyone at Intercom"* (`ideas.fin.ai/p/we-gave-claude-code-to-everyone-at`).

> **Quote-accuracy caveat.** This brief draws on a well-diarized ElevenLabs transcript (speaker_0 = Brian; speaker_1 = moderator; speaker_2 = Prithvi; speaker_3/4 = audience), the 9 slide photos (authoritative for all hard numbers), and web-verified enrichment. Slides override ASR for names/numbers. Low-confidence ASR spots are marked `[VERIFY @mm:ss]`; internal Fin personal names mangled by ASR are **not** attributed. The transcript is partial (~50 min, cuts off mid-audience-Q). Where a number was shown on a slide but not spoken aloud, it is cited "from Fin's deck / essay," not "Brian said."

---

## 1. Quick Take

Fin (the company formerly known as Intercom) set a **deliberate, measured goal to 2× R&D productivity** and hit it in **9 months** — and over 16 months actually 3×'d it. This was the rare AI-adoption talk with audited receipts: 5.2× faster median time-to-merge, a 1,780→420 customer-bug burndown, 93.6% of PRs now agent-driven, and a **45% decline in fully-loaded cost-per-PR** even while peak Claude Code spend hit **$128K/week**. The single most counter-cultural lesson: **bottoms-up "use whatever you want, no limits" flatlined for six months; the breakout came only when leadership got opinionated and *forced* it** — through performance reviews and a gamified hackathon that "works as a drug." Prithvi (Anthropic) supplied the model-side frame: execution is now near-trivial, value moves up the stack to vision/strategy/taste, and the "last mile" of human judgment is the last thing to go. Highly relevant to Alex: this is a concrete, numbers-backed org-change playbook for AI adoption — the GTM-adjacent version of "what good looks like."

> **Material context (post-event):** Intercom renamed itself **Fin** on **May 12, 2026** (~3 weeks before this talk), and on **June 15, 2026** — just 11 days *after* this event — **Salesforce agreed to acquire Fin for ~$3.6B**. The "willing to make our own business die" turnaround story was, in real time, an exit story. Read every claim through that lens.

---

## 2. The Thesis

**"2X was a measured goal, not a vibe — and forcing adoption beat encouraging it."**

The talk has two interlocking arguments:

1. **The measurement thesis (Brian / Darragh Curran's framing).** AI productivity gains are real and auditable if you (a) pick a "good-enough" proxy metric fast (merged **PRs per R&D head**), accept its flaws, and move on; and (b) triangulate it with downstream value (bug burndown, cost-per-PR, breaking-change rate, product-change velocity) so it isn't a vanity number. They named the goal "2×," made it a goal *so they would measure it*, and treated the 16-month 3× as proof it wasn't proxy-gaming.

2. **The forcing-function thesis.** "The best way to get behavior change is to force it." Phase 1 (bottoms-up, no spend limits, "softly, softly encourage") produced a **6-month flatline**. Phase 2 — top-down, opinionated, "telling you what to do, how to do it," baked into performance reviews, kicked off by a company-wide hackathon — is what broke the plateau. Model capability (the Dec'25–Jan'26 step-change) was necessary but *not sufficient*; the culture and the system around the model did the work.

Prithvi's counter-melody: as execution collapses in cost, the bottleneck and the value migrate **up the stack** (QA, architecture, product discovery, taste) and toward **goal-driven** rather than task-driven work with the model.

---

## 3. Pre→Post Gap

The pre-event brief expected two speakers (Brian + Prithvi) and framed Prithvi around *agent reliability / the doer-judge harness*. Deltas surfaced in the room and via enrichment:

| Expectation | Reality |
|---|---|
| Prithvi on agent reliability / harness | Prithvi talked **model design, creativity, and the "frontend design skill" he co-authored** — same person, different facet. (Harness work is real but came up only in audience Q.) |
| GenAI Collective "40k+" members | Now **70,000+ members across 25+ chapters** (rebranded "The AI Collective"); **Prithvi leads the NYC chapter** — he's both speaker and host-org leader. |
| Company = "Intercom" | Renamed **Fin** on **May 12, 2026** — Brian announces it on stage as news ("a couple weeks ago"). |
| A turnaround story | **11 days later (Jun 15, 2026), Salesforce agreed to acquire Fin for ~$3.6B.** The talk is, in hindsight, the pre-exit victory lap. |
| CEO "Dara/Darren/Tara" wrote the 2X letter | The 2X letters were authored by **Darragh Curran** (CTO / EVP Engineering), not the CEO. ASR mangled "Darragh." (Brian calls him "our CEO" loosely; the public-record CEO is Eoghan McCabe.) |

---

## 4. Speaker / Company Map

| Person | Role / Company | At this event | Notes (verified) |
|---|---|---|---|
| **Brian Donohue** | VP Product, Fin (formerly Intercom) | Keynote — "The 2X Story" + panel | Long-tenured Intercom/Fin product leader; delivered the deck "last minute," presents at "2× speed." Distinct from Brian *Scanlan* (Sr Principal Eng, who tells the parallel "2x engineering velocity" story on Lenny's *How I AI*). |
| **Prithvi Rajasekaran** | Member of Technical Staff, Anthropic **Labs** | Panel / co-speaker | Co-authored Claude's **frontend-design skill** (w/ Alexander Bricken, Oct 2025; 277K+ installs in 4 mo). Authored Mar 2026 "Harness design for long-running apps" (GAN-style generator/evaluator). Formerly on Anthropic's **Apply AI** team. **Leads GenAI/AI Collective NYC chapter + international.** LinkedIn: prithvi72. |
| **Moderator** | (name unconfirmed) | Ran panel Q&A | Joined Fin Jan 2026, non-technical; "finished ~130 of 700" in the hackathon. 🔴 Do not publish a name. |
| **Darragh Curran** | CTO / EVP Engineering, Fin | *Not present* — authored the "2×" essays | The internal "2X" letters' author; "any team leveraging existing tools well should expect ≥2×." |
| **Fin (formerly Intercom)** | AI customer-service company, Dublin/SF | Subject company | ~1,305 employees; Fin (the AI agent) is the core product; Fin revenue projected >half of business by end of 2026. Acquired by Salesforce ~$3.6B (Jun 2026). |
| **Anthropic** | Claude / Claude Code maker | Model + tooling provider | The "RNN suit"/harness around the model is where capability gets unlocked (Prithvi). |
| **GenAI / The AI Collective** | Community (70k+, 25+ chapters) | Host | NYC chapter led by Prithvi. |

---

## 5. Slide Catalog

All numbers below are read directly from the 9 slide photos (high-confidence) and cross-checked against the `2x-nine-months-later` essay. Capture times are ET (from `PXL` UTC filenames −4).

| # | Time | Slide — what it showed | Speaker | Framework / numbers on it |
|---|---|---|---|---|
| **1** | 18:23:57 | **SaaS vs. Intercom growth rate**, line chart Q4'20→Q4'26. Two series: SaaS growth rate (black, src *Aventis Advisors & Capital IQ*) and Intercom growth rate (blue, src *Intercom*). Intercom craters from ~**29–30% (2021) → 4% trough (Q1'23)**, then climbs a "rollercoaster" back to **37% projected (Q4'26)**, re-crossing above the SaaS average. Red markers: **"CEO change"** (~Q4'22) and **"Fin launch"** (~Q2'23). Dashed tail = projection. | Brian | The crisis→turnaround spine. Trough 4%; recovery to 37% (proj.). "Solid line is real numbers; dashed is targets." |
| **2** | 18:23:58 | Same chart, re-shot clean/un-occluded. | Brian | Same. |
| **3** | 18:26:41 | **Productivity — the flat early months.** Two near-overlapping lines, roughly flat/slightly rising, x-axis **Mar 2025 → Oct 2025** ("Month"). Trendlines (blue + orange dashed) basically parallel and flat. | Brian | The **6-month flatline** of Phase 1 (bottoms-up). Don't cite exact y-values (label illegible). |
| **4** | 18:28:10 | **Fin Hackathon Leaderboard** — "Real-time rankings of individual performance." Columns: **1. Simple · 2. Complex · 3. Final Boss · Total · Last Update.** #1 **Henry Larkin 26.96** · #2 **Miles McGuire 25.68** · #3 **Ciaran Lee 25.65** · #4 Murat Toygar 25.61 · #5 Gustavs Cirulis 25.35 · #6 James Cash 25.15 · #7 Emanuele Sparvoli 25.11 · #8 Eduardo Carvalho 25.10 · Andrew Murtagh 25.10 … Joao Fernandes 24.84. | Brian | Gamified, individual, public ranking = the adoption "drug." **Ciaran Lee (#3) is an Intercom co-founder/former CTO** — "everyone, including the founders." |
| **5** | 18:33:45 | **Raptor 1 / Raptor 2 / Raptor 3** — three SpaceX engines side by side, each visibly simpler/cleaner than the last. | Brian (spoken aloud) | "Iterate toward simplicity" metaphor: early systems are "messy as hell," then "beautifully clean and simple." Brian explicitly narrates this slide (transcript ¶ on factories/electricity + SpaceX). *(Prior alignment doc flagged attribution as uncertain; the diarized transcript resolves it to Brian.)* |
| **6** | 18:36:36 | **THE BURNDOWN — "One year of accumulation. Then the cliff."** Stacked-area chart (Low/Medium/High/Critical), **Apr'25 → Apr'26**, peak **1,780 → 420**. Side stats: **Total Resolved 2,500+** · **New Incoming Absorbed 1,400+.** | Brian | The "zero bugs is real" proof. Customer-reported defects, not theoretical. Essay: **54% defect-backlog reduction** YTD; some teams hit **zero defects**. |
| **7** | 18:38:11 | **PR results triptych.** ① **MEDIAN TIME TO MERGE — 5.2× FASTER** (auto-approved **14.6 min** vs ORG MEDIAN **73.8 min**). ② **AUTO-APPROVAL PROGRESS — 19% of all PRs auto-approved** (bar: Evaluated 60% → Approved 19%; dashed "50% goal" line). ③ **AUTO-APPROVED PR SIZE — 86% ≤20 lines** (1–5 lines = 41%, 6–20 = 45%, 21–50 = 11%). Footer: `ideas.fin.ai/p/2x-nine-mon…` | Brian | Smaller, focused PRs = the quality pattern they want. Essay text: org median **75.8 min**, auto-approval **19.2%**, goal **>50%**. |
| **8** | 18:39:28 | **WEEKLY CLAUDE CODE SPEND — $128K** peak. Bar chart ramping **Jan 5 (~$10K) → $128K (mid-Mar)**. Caption: *"Weekly Claude Code API spend. Not yet optimized for cost. Mar 30 + Apr 6 dips reflect public/school holidays."* | Brian | The cost-of-going-all-in number. "Not yet optimized." |
| **9** | 18:39:42 | **45% DECLINE IN COST PER PR** — fully-loaded $/PR (payroll + AI): **Oct $1,097 → Nov $1,190 → Dec $1,477 → Jan $1,123 → Feb $831 → Mar $603.** Caption: *"Fully loaded cost (payroll + AI) per merged PR. Dec spike from reduced holiday productivity. Increasing PRs/head drives cost down."* | Brian | The deflation counter-narrative to slide 8: all-in is expensive *and* deflationary per unit of output. |

---

## 6. Full Quote Bank

Speaker labels from the diarized ElevenLabs transcript. `[VERIFY]` flags low-confidence ASR words (see §17).

### Brian Donohue (Fin)
- *"We have to basically be willing to make our own business die."* (00:00) — the all-in thesis, paired with slide 1's crater.
- *"Our Fin revenue is gonna be over half of our business by the end of the year."* (00:00)
- *"We actually finally changed the name of our company, from Intercom to Fin, just a couple weeks ago."* (00:00)
- On the 2X framing: *"It feels like we should say 10X, but I don't know if we'll be able to do 2X. And 2X is still ambitious… we're gonna measure this, and let's actually do it. … This is not like an aspiration. Make this a goal, and therefore measure it."* (paraphrasing Darragh's letter). *"It took us nine months to get there, and we did it."*
- *"Phase one… softly, softly. Encourage… whatever tool you want, use anything… there's no spending limits here. … And basically — flatlined. Flatlined for like six months."*
- *"The best way to get behavior change is to force it."* (~00:00 segment, Phase 2)
- *"We are going in and telling you what to do, how to do it… being opinionated about the system and aggressively driving change."*
- *"The basic gamification works as a drug."* + *"It got everyone like, 'Holy [redacted], I knew nothing about this, and I was actually getting to a reasonable place.' That mental unlock is what we brought with that gamification."*
- *"We need to onboard your agent, Claude, like you would a senior engineer."*
- *"Thirteen plugins, like a hundred skills and hooks… sixty people contributing"* (March) → *"nearly seventy engineers contributing"* (Feb '26). *(Essay reconciles to the cumulative figure: 267 skills, 153 contributors.)*
- *"This is not optional. You must use this. It was part of performance reviews for engineers. … EMs need to have shipped ten PRs."*
- *"The first time they build the factories with electricity, the factories are still built in the old way. You need to rebuild the thinking of the factory, find the bottlenecks."*
- On the proxy metric: *"Is that not a ridiculously reductionistic measurement? … It was good enough… rather than us spending three months trying to get the right metric. … Darragh's like, 'Oh, that was one of our best decisions. Just go with that.'"* [Darragh name = ASR-corrected; see flags]
- *"We've teams with zero defects. I never thought we would ever have that. … This is a product that's like twelve years old."*
- *"We're shipping lots of money to Anthropic here… and we did not expect this… but the flip side is the cost per PR is actually reduced."*
- *"You're by default thinking too small of what you can accomplish with this. You need to think way more ambitiously about what you're setting Claude out after to build."*
- *"Darragh's still thinking we can 2X again this year. … There doesn't feel like there's a ceiling we've reached so far."*
- On the future of UI: *"The GUI is not dead, but it's moved to the background… you're working with the LLMs in a goal-driven way, not a task-driven way. That's the huge shift. … Conversations will be increasingly dominant as the form of UI, but not on their own — you still need reference artifacts."*
- On product boundaries: *"AI is a convergent force"* (attributed to a Fin co-founder) — *"any boundaries you put around your product, AI just kind of washes those away."*

### Prithvi Rajasekaran (Anthropic)
- On flattening: *"There's definitely folks that a few years ago you would never see near the code base that are shipping tons and tons of PRs now… we definitely see the boundaries getting a little bit fuzzier with AI."*
- The value-stack frame: *"You can roughly split it into vision, strategy, execution. With AI, execution has become a lot more trivial than it was a few years ago. … You need higher-level systems for people to coordinate toward a common goal."*
- On slop / volume: *"If you're producing ten times the volume of code, there's like ten times the QA. … Before I was spending more time writing the code; now I'm probably spending more time QA-ing the code, making sure it follows the right architecture and design patterns."*
- On the "last mile": *"We'll see the models get very good, but under the hood we're breaking it down into almost a mathematical or scientific manner that's easy to verbalize rigorously. That last mile of human intuition, judgment, taste — that'll be the last thing to go."*
- On creativity: *"There's a book… 'Steal Like an Artist.' The assertion is every good piece of art is a remix of some other piece of art. If you give the model a reference and have it remix it in some way… you're almost asymptotically approaching what real creativity can be."*
- On the design skill: *"A lot of our front-end capability comes from a **frontend design skill**, which is something that I wrote — a set of instructions to make the model more creative. … I definitely saw the model get to a point where it was designing front-ends way better than what I was designing."* [ASR: "foreign design skill"/"cloud design" — corrected]
- On harness engineering (audience Q): *"Harness engineering is the layer immediately wrapping the model — system prompt, tooling, GUI. … Claude Code is a great example: we had the model and the capability, but it wasn't until we put it in this [harness] suit that it could go start doing these things. Someone writes the perfect prompt, orchestrates the tools correctly, and suddenly the model achieves state-of-the-art performance."* [ASR rendered the harness metaphor as "RNN suit" — `[VERIFY @43:53]`]
- On the next paradigm: *"The place you start from is the customer problem… and on the technical side, what is the model capability I'm trying to invoke? Agentic coding wasn't even a thing three years ago because we didn't have the capability to harness."* [`invoke` flagged @42:23]

### Moderator (name unconfirmed — paraphrase only)
- Joined Fin in January as a non-technical hire; *"finished ~130 of 700 people in the hackathon."*
- Framed the Netflix culture-deck parallel; asked where each speaker would "place your big bets on the next paradigm shift." 🔴 Do not quote verbatim or name.

---

## 7. Pro-Tips (actionable)

1. **Make it a goal so you're forced to measure it.** Naming "2×" wasn't aspiration — it converted a vibe into a tracked metric. (GTM analog: pick a number, instrument it, accept it'll be imperfect.)
2. **Pick a "good-enough" proxy fast; don't spend 3 months perfecting the metric.** Merged-PRs-per-head was admittedly crude — and was "one of our best decisions." Triangulate it with 4–5 downstream signals to defend against gaming.
3. **Run a gamified, company-wide hackathon to manufacture the "mental unlock."** A real-time individual leaderboard + a buildable mini-RAG target turned skeptics into addicts. Open it to *everyone*, not just engineers.
4. **Onboard the agent like a senior hire.** Treat Claude like a new staff engineer: give it the same context, conventions, code-review standards, and skills you'd give a human — encoded as plugins/skills/hooks.
5. **Bake adoption into performance reviews.** "Not optional." EMs had a 10-PR floor; engineers had a 90%-by-EOFeb PR target. Force the behavior, then operationalize it.
6. **Instrument cost-per-unit-of-output, not just spend.** $128K/week looks alarming alone; cost-per-PR falling 45% reframes it as efficiency. Always show both.
7. **Hunt the new bottleneck.** Speeding execution exposes downstream bottlenecks (review, QA, product discovery, customer feedback loops). "Rebuild the factory," don't electrify the old one.
8. **For design/creative tasks, give the model a reference to remix.** Framing a fuzzy task ("make this beautiful") as a tactical, well-specified one ("remix this reference") unlocks much better output.

---

## 8. Best Practices / Patterns

- **Two-phase adoption (encourage → force).** Bottoms-up to surface champions; top-down mandate to cross the chasm. The flatline is expected; plan for it.
- **A written "skill" is the unit of capability — said by both companies.** Fin's engineers build eval/RAG/observability/incident-response skills; Anthropic's Prithvi hand-writes the frontend-design skill. Leverage lives in the skill file, not the one-off prompt.
- **Distribute skills via an internal marketplace.** Fin built an auto-updating plugin marketplace; ~267 skills, 153 contributors (31% of R&D) in 3 months — "the most actively contributed project at the company."
- **Smaller PRs as a quality lever.** 86% of auto-approved PRs ≤20 lines; "solve one problem, test it." Auto-approval is gated on PR shape, not just content.
- **Triangulate the headline metric.** PRs/head → defect burndown → cost-per-PR → breaking-change rate (−35%) → product-change velocity (>2×) → idea-to-ship time (−39%). No single number stands alone.
- **Domain "guidance skills" for non-engineers.** "Claude for data" encodes the right tables/metrics/terminology so non-experts don't pull wrong numbers — the org-wide leverage layer.

---

## 9. Pitfalls / Anti-Patterns

- **"Just give everyone AI and get out of the way" stalls.** Six-month flatline under no-limits bottoms-up. The orthodoxy is wrong at org scale.
- **Volume-without-QA = slop.** 10× code → 10× QA. Output volume itself became a problem (Prithvi confirmed by show of hands in the room).
- **Mistaking model capability for the whole story.** The Dec–Jan model step-change was necessary but not sufficient; without the cultural/system work it would have stayed flat.
- **Over-optimizing the metric before shipping.** The trap they explicitly avoided — perfecting the measurement instead of moving.
- **Averages hide the distribution.** Huge variance persists even post-adoption: top 5% of contributors = 6× median PR throughput. Manage the long tail, don't celebrate the mean.
- **Cost denial.** The spend problem doesn't go away just because cost-per-PR fell — "this doesn't solve the spend problem." Budget for it.
- **Thinking too small.** The recurring failure mode: under-scoping what you ask the model to build.

---

## 10. Hot Takes

- *"The best way to get behavior change is to force it."* — A direct repudiation of bottoms-up adoption gospel.
- *"You have to be willing to make our own business die."* — Self-cannibalization as strategy (and, 11 days later, a $3.6B exit).
- *"Gamification works as a drug."* — Said admiringly, twice. The leaderboard was the conversion engine.
- **Execution is now trivial; taste is the moat.** (Prithvi) The "last mile of human intuition/judgment/taste… is the last thing to go."
- **The GUI is moving to the background; chat becomes the primary UI** — but "the rest doesn't go away; you still need reference artifacts." (Brian, goal-driven vs task-driven.)
- **"AI is a convergent force"** — product boundaries are dissolving; everyone is on a collision course (Brian's answer on Zoom/agentic positioning).

---

## 11. Substantive Insights (ranked)

1. **Force beats encourage — with receipts.** The 6-month flatline → forced-adoption breakout is the rare A/B test of AI rollout strategy, run inside one company. Highest-value, most contrarian takeaway.
2. **2X was measured, and the proof is multi-metric.** 5.2× faster merge, 1,780→420 burndown, 93.6% agent-driven PRs, −45% cost-per-PR, −35% breaking changes, >2× product velocity, −39% idea-to-ship. The triangulation is the credibility.
3. **The cost story cuts both ways.** $128K/week peak ("not yet optimized") *and* 45% cheaper per PR. Going all-in is simultaneously expensive and deflationary — the most nuanced, least-tweeted number in the deck.
4. **The "skill" is the unit of capability — convergently, from both Fin and Anthropic.** A portable, version-controlled instruction file is where leverage compounds; an internal marketplace distributes it.
5. **Value migrates up the stack as execution collapses.** QA, architecture, product discovery, and taste become the bottleneck and the differentiator (Prithvi). The "factory" must be redesigned, not electrified.
6. **"Everyone" is literal — and qualitatively different from 2×.** Non-engineers vibe-coding to "a reasonable place"; a VP building a 270-event marketing calendar in a day. Extending Claude Code beyond engineering yields not 2× but "a company where anyone can build software."
7. **Distribution variance is the management problem.** Top 5% = 6× median. The average flatters; the tail is where the program lives or dies.

---

## 12. Anecdotes

- **The vacation leaderboard.** An engineer on holiday couldn't put the hackathon down — "You're spending way too much time on this damn leaderboard, come back to the family." The gamification "drug" in one image.
- **The non-technical moderator's 130/700.** A non-technical Fin hire (joined Jan 2026) entered the hackathon in week two and placed ~130th of 700 — proof the unlock reached beyond engineers. (He noted, wryly, he didn't crack the top 100.)
- **The co-founder mid-leaderboard.** Ciaran Lee, Intercom co-founder/former CTO, sits at #3 (25.65) — leadership in the arena, not above it.
- **"Suspicious — do we really buy this?"** When the bug burndown looked too good, they used an LLM to audit how many "fixes" were just duplicate/no-op closes. Only ~5% were non-fixes; the rest were genuine code-shipping closes.
- **"We're running out of stuff to do."** A team came to Brian asking for *more roadmap* — a sentence he'd never heard — after execution sped up.
- **Raptor 1→3.** Brian used SpaceX's engine evolution (messy → "beautifully clean and simple") as the visual for how their internal system matured through "hundreds of iterations and loops."

---

## 13. Concept Glossary

- **2× / 2X** — Fin's named goal to double R&D productivity; deliberately set *as a goal so it would be measured*. Hit in 9 months; 3× over 16 months.
- **Merged-PRs-per-R&D-head** — the chosen "good-enough" proxy productivity metric (denominator = all of R&D: PMs, designers, engineers).
- **Auto-approval** — PRs reviewed *and* approved by Claude with no human gate; 19.2% of all PRs, 497 fully-autonomous in the first 4 weeks; goal >50%.
- **Harness / harness engineering** — the layer wrapping the model (system prompt, tooling, GUI). "The model had the capability, but it wasn't until we put it in [the harness] that it could do these things." (Prithvi's specialty.)
- **Skill / Agent Skill** — a portable instruction file encoding how to do a task (e.g., frontend-design, RAG eval, observability). The unit of capability both companies build and distribute.
- **Frontend-design skill** — Prithvi + Alexander Bricken's Claude skill (Oct 2025) that makes the model design better; famously "bans Inter, Roboto, and purple gradients"; 277K+ installs in 4 months.
- **Goal-driven vs task-driven** — the UI/interaction shift: you shape *the goal* conversationally rather than issue granular tasks; the GUI moves to the background.
- **"AI is a convergent force"** — a Fin co-founder's phrase: AI dissolves the boundaries you draw around a product's scope.
- **Cowork / Operator** — Anthropic/Fin agentic-workspace concepts Brian referenced as candidate "future of all apps" surfaces.
- **Fully-loaded cost-per-PR** — payroll + AI spend ÷ merged PRs; the deflation metric (−45%).

---

## 14. Tools / Companies Mentioned

- **Claude Code** (Anthropic) — the central tool; 93.6% of PRs agent-driven.
- **Anthropic** — model + Claude Code provider; "shipping lots of money to Anthropic."
- **Fin / Intercom** — subject company; Fin = the AI customer-service agent + (now) the company name. Intercom 2 = the rebuilt help-desk product.
- **"Claude for data" plugin** (internal) — domain-guidance layer for non-engineers; 2,000+ self-serve reports.
- **Internal AI-built GTM tools** — AI answer optimization, data quality engine, automated outreach (shown from an all-hands).
- **PlanetScale, Snowflake, Slack, Google Drive** — referenced infra/integrations (essays).
- **SpaceX (Raptor engines)** — visual metaphor only.
- **Zoom** — cited in an audience Q on agentic enterprise positioning.
- **Netflix** — moderator's culture-deck / existential-pivot parallel.
- **OpenAI / ChatGPT** — the Nov 2022 catalyst; an audience member referenced a prior meeting "at OpenAI's office."
- **GenAI / The AI Collective** — host community.
- **"Steal Like an Artist"** (Austin Kleon) — real book Prithvi cited on creativity.

---

## 15. Stat Bank

Slide-sourced = high confidence. Essay-sourced = `2x-nine-months-later` (Curran) or `we-gave-claude-code-to-everyone-at` (Yakovenko). Where slide and essay differ, both are listed.

| Stat | Value | Source |
|---|---|---|
| Productivity goal | 2× R&D productivity in 12 months | Spoken / essay |
| Time to hit 2× | **9 months** | Spoken / essay |
| 16-month figure | **3×** | Spoken / essay |
| Intercom growth trough | **4%** (Q1'23) | Slide 1 |
| Intercom growth recovery | **37%** projected (Q4'26) | Slide 1 |
| Fin revenue share | **>half of business** by end 2026 | Spoken |
| Phase-1 flatline | **~6 months** | Spoken / Slide 3 |
| Bug burndown | **1,780 → 420** (Apr'25→Apr'26) | Slide 6 |
| Total defects resolved | **2,500+** | Slide 6 |
| New incoming absorbed | **1,400+** | Slide 6 |
| Defect-backlog reduction (YTD) | **54%** | Essay |
| Non-fix closures (audited) | **~5%** | Spoken |
| Median time to merge | **5.2× faster** | Slide 7 |
| Auto-approved merge time | **14.6 min** | Slide 7 / essay |
| Org median merge time | **73.8 min** (slide) / **75.8 min** (essay) | Slide 7 / essay |
| % of PRs auto-approved | **19%** (slide) / **19.2%** (essay) | Slide 7 / essay |
| Auto-approval goal | **>50%** (slide annotates "60% evaluated, 50% goal") | Slide 7 / essay |
| Auto-approved PR size | **86% ≤20 lines** (41% 1–5, 45% 6–20, 11% 21–50) | Slide 7 |
| % of PRs agent-driven | **93.6%** (peaked ~95%) | Essay (spoken: "<40% → >90%") |
| Fully-autonomous PRs (first 4 wks) | **497** | Essay |
| Peak weekly Claude Code spend | **$128K** | Slide 8 |
| Cost-per-PR decline | **45%** ($1,097→$603, Oct→Mar; Dec peak $1,477) | Slide 9 |
| Breaking-change reduction | **−35%** (despite 2× deploys) | Spoken / essay |
| Product-change velocity | **>2×** | Spoken / essay |
| Idea-to-ship time | **~39% faster** | Essay |
| Code quality | first **5-week** net-positive streak; "crossed into the green" | Spoken / essay |
| Skills built | **267** | Essay (spoken: "~100" in March, growing) |
| Skill contributors | **153 (31% of R&D)** in 3 months | Essay (spoken: "~60–70") |
| Plugins | **13** | Spoken |
| EM requirement | **10 PRs shipped** | Spoken |
| PR target | **90% by end Feb '26** | Spoken |
| Company headcount | **~1,305** | Spoken / essay |
| Peak active Claude Code users | **1,100** | Essay |
| Hackathon participants | **700+** | Spoken |
| Self-serve data reports | **2,000+** | Spoken |
| Top-contributor variance | top **5% = 6×** median PR throughput | Essay |
| R&D headcount (denominator) | **~500** | Essay |
| Codebase size | **~8.5M lines**; 313 daily prod deploys; 2,539 CI jobs/day | Essay |
| Director+ active users | **60%** | Essay (Yakovenko) |
| Salesforce acquisition | **~$3.6B** (Jun 15, 2026) | Web — Irish Times / Intercom blog |
| Intercom/Fin total ARR | **$400M** (Apr 2026; up from $382M EOY'25) | Web — Sacra |
| Fin (agent) ARR | **>$100M**, growing **~3.5×/yr**; ~8,000 businesses | Web — Sacra |
| Net revenue retention | **112% → 146%** (outcome-based pricing) | Web — Mostly Metrics |
| Fin revenue "half of business" | **projection** (on pace ~half by early 2027; today ~¼ of ARR but ~all growth) | Web / spoken |
| Frontend-design skill installs | **277K+** in 4 months | Web — Anthropic |

---

## 16. Documentarian Angles (GTM / revenue lens)

1. **"Is 2X real? I read the receipts."** A scorecard post: claim → slide → caveat. Lead with the audited triangulation (merge speed, burndown, cost-per-PR), then keep it honest with the two costs the headline hides (the 6-month flatline + $128K/week). *Visual: a "claim → evidence → asterisk" scorecard (Gamma), not a re-printed chart.*
2. **"The bottoms-up AI rollout is a myth — here's the org that proved it."** The force-beats-encourage thesis, framed for GTM/RevOps leaders rolling AI into sales/CS teams. The hackathon as the conversion play. *Visual: the two-phase adoption curve (flatline → breakout) with the forcing functions labeled.*
3. **"$128K/week — and cheaper than ever."** The cost-paradox post: spend exploded *and* unit cost fell 45%. The CFO-grade reframe of AI spend as efficiency. Directly relevant to anyone building the AI business case. *Visual: dual-axis — spend up, cost-per-PR down.*
4. **"The skill is the new unit of work."** Synthesis with the 6/3 Masterclass "nobody reads the skills" thread: both Fin and Anthropic treat the written skill file as the leverage point; Fin built an internal marketplace for it. *Visual: where leverage moved — prompt → skill → skill-marketplace.*
5. **"Execution is free now. Taste is the moat."** Prithvi's value-stack frame for a GTM/PM audience: as execution collapses, differentiation moves to discovery, judgment, and taste — the "last mile." Tie to "everyone can build software now, so what's scarce?" *Visual: the vision/strategy/execution stack with the value arrow moving up.*

*(Cadence note: #1 is the lead per the alignment doc's "measured, not a vibe" pick; #4 is the cross-event synthesis candidate. Max 1 synthesis post/week.)*

---

## 17. Open Loops & Verification Flags

- 🔴 **Moderator name** — unconfirmed; do not publish or quote verbatim.
- 🟢→corrected **"Dara / Darren / Tara"** = **Darragh Curran** (CTO/EVP Eng), author of the 2X letters. Brian calls him "our CEO" loosely; the public-record CEO is **Eoghan McCabe**. Do not publish "Darragh as CEO."
- 🔴 **Other internal Fin names** (Mario, "Nicole," "Sarah" @11:14) — ASR-uncertain; do not attribute quotes.
- 🟡 **"RNN suit" @43:53** — ASR garble of Prithvi's harness metaphor ("we put it in this ___ suit"); intended sense = the harness/scaffold around the model. Paraphrase, don't quote the literal phrase.
- 🟡 **Low-confidence ASR words** (from REVIEW list): `technical` @25:32, `MRI` @26:03 (likely "moment"/context word), `ChatGPT` @26:04, `invoke` @42:23, `Green` @32:37 (likely a name — "Brian"/"Ryan" used by moderator for Brian), `season` @33:03, `quality` @31:33, `office` @48:56. Paraphrase around these.
- 🟡 **Moderator calls Brian "Ryan" / "Green Product"** in a couple of spots (@32:31, @41:00) — ASR/aside artifact; it's Brian Donohue throughout. Do not introduce a "Ryan."
- 🟡 **Merge-time + auto-approval mismatch** (slide 73.8 min / 19% vs essay 75.8 min / 19.2%) — cite the essay's text figures as canonical; slides are rounded snapshots.
- 🟡 **Slide 3 y-values** — label illegible; describe as "flat," don't quote numbers.
- ✅ **Speaker split** confirmed by diarization + Alex's in-room recall: Brian = 2X deck + Raptor slide; Prithvi = design/creativity/harness; moderator ran Q&A.
- 🟢 **Salesforce acquisition** — confirmed (Jun 15, 2026, ~$3.6B); newer than the in-room talk, include as material post-event context.

---

## 18. Enrichment Resolutions (web-verified)

1. **Intercom → Fin rename.** Confirmed: announced **May 12, 2026** — "Today Intercom becomes Fin." The company took the name of its AI agent (the core product for ~3 years); the help-desk product continues as "Intercom" / "Intercom 2." *(Confidence: high.)* — [Intercom blog](https://www.intercom.com/blog/today-intercom-becomes-fin/), [CX Today](https://www.cxtoday.com/contact-center/intercom-rebrands-to-fin/)
2. **Salesforce acquires Fin.** Confirmed: **June 15, 2026**, definitive agreement, **~$3.6B**. Occurred 11 days after this event. *(High.)* — [Irish Times](https://www.irishtimes.com/business/2026/06/15/salesforce-to-buy-fin-formerly-intercom-for-36bn/), [Intercom blog](https://www.intercom.com/blog/salesforce-signs-definitive-agreement-to-acquire-fin/)
3. **The "2X" essays / author.** Authored by **Darragh Curran** (Intercom CTO/EVP Engineering): *"2×"* (`ideas.fin.ai/p/2`) and *"2× – nine months later: We did it"* (Apr 16 2026). Resolves the ASR "Dara/Darren/Tara." His thesis: any team using existing tools well should expect ≥2×. *(High.)* — [Fin Ideas](https://ideas.fin.ai/p/2x-nine-months-later)
4. **Hard numbers (Curran essay), cross-checked vs slides.** 3× over 16 months; ~500 R&D denominator; 93.6% agent-driven PRs; 19.2% auto-approved (goal >50%); 497 autonomous PRs in first 4 weeks; 14.6 vs 75.8 min merge; 86% ≤20 lines; 267 skills / 153 contributors (31% of R&D); top 5% = 6× median; 54% defect-backlog reduction; −35% downtime from breaking changes; >2× product changes; ~39% faster idea-to-ship; ~1,305 employees, 1,100 peak Claude Code users. *(High — primary source.)*
5. **"Everyone" essay.** **Andrii Yakovenko** (data/AI transformation at Intercom): 1,000+ with access, 300+ weekly active, 60% of Director+ active; a VP of Demand Gen built a 270-event global marketing calendar in a day; "guidance skills" encode company-specific domain knowledge; the system is a self-improving flywheel. Key line: *"When people you've never met are casually talking about doing in an hour what used to take three months… something real is happening."* *(High.)* — [Fin Ideas](https://ideas.fin.ai/p/we-gave-claude-code-to-everyone-at)
6. **Brian Donohue vs Brian Scanlan.** Two distinct people: **Donohue** = VP Product (this event); **Scanlan** = Sr Principal Eng, who tells the parallel "2x'd engineering velocity in 9 months with Claude Code" story on Lenny Rachitsky's *How I AI*. Both narrate the same initiative. *(High.)* — [Lenny's Newsletter](https://www.lennysnewsletter.com/p/this-week-on-how-i-ai-how-intercom)
7. **Prithvi Rajasekaran.** Member of Technical Staff, Anthropic **Labs** (formerly **Apply AI**). Co-authored the **frontend-design skill** (w/ Alexander Bricken, Oct 2025; 277K+ installs in 4 months; "bans Inter, Roboto, purple gradients"). Authored Mar 2026 *"Harness design for long-running application development"* (GAN-style generator/evaluator architecture). **Leads the GenAI/AI Collective NYC chapter + international.** *(High.)* — [Anthropic Engineering](https://www.anthropic.com/engineering/harness-design-long-running-apps), [frontend-design plugin](https://github.com/anthropics/claude-code/tree/main/plugins/frontend-design), [LinkedIn](https://www.linkedin.com/in/prithvi72/)
8. **GenAI / The AI Collective.** Rebranded "The AI Collective"; **70,000+ members across 25+ global chapters** (founders/researchers/operators/investors). NYC chapter active; **led by Prithvi Rajasekaran**. The pre-event "40k+" figure is dated/low. *(High.)* — [aicollective.com/about](https://www.aicollective.com/about), [NYC chapter](https://www.aicollective.com/chapters/nyc)
9. **Ciaran Lee.** Intercom **co-founder & former CTO**; appears at #3 on the hackathon leaderboard — "everyone, including the founders." *(High — corroborated by slide 4.)*
10. **"Steal Like an Artist."** Real book by **Austin Kleon** (2012); thesis "good art is a remix." Prithvi cited it on model creativity. *(High.)*
11. **Eoghan McCabe.** Intercom co-founder; **returned as CEO Oct 6, 2022** (replacing Karen Peacock) — the "CEO change" marker on slide 1, ~Q4'22. Curran's 2X essay *references* a prior McCabe post ("exhilarating rebirth phase"). The 2X *letters* are Curran's (CTO), not McCabe's (CEO). Two distinct people; do not conflate. *(High.)* — [TechCrunch (McCabe return)](https://techcrunch.com/2022/10/06/)
12. **Fin / Intercom financials.** **$400M total ARR** (Apr 2026, up from $382M EOY'25); **Fin (agent) >$100M ARR** growing **~3.5×/yr** across ~8,000 businesses; **NRR 112%→146%** under outcome-based pricing. "Fin revenue >half the business by EOY" is a **forward-looking projection** (on pace for ~half by early 2027; today Fin is ~¼ of ARR but nearly all the growth). Salesforce deal ≈ 9× full-business ARR / ~36× Fin ARR. *(High on ARR/NRR; medium on the "half" framing — it's a projection.)* — [Sacra](https://sacra.com/c/intercom/), [Mostly Metrics](https://www.mostlymetrics.com/p/how-intercom-reaccelerated-growth-with-outcome-based-pricing)
13. **Brian Donohue bio (supplementary).** VP Product at Fin/Intercom, **~11 years** tenure; came up via UX design → PM; ~2.5 years "all in" on Fin. *(High on role/tenure.)* — [Intercom blog author page](https://www.intercom.com/blog/author/brian_donohue/)

---

*Built 2026-06-27 · Sources: ElevenLabs diarized transcript (~50 min, partial) + 9 slide photos + slide-transcript-alignment.md + web enrichment. 9/9 slides integrated. ~40 verbatim quotes banked (Brian + Prithvi). Internal Fin personal names excluded from all public-ready copy per quote-safety.*
