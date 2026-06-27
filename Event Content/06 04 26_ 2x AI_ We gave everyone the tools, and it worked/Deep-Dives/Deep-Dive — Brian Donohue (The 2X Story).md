# Deep-Dive — Brian Donohue (The 2X Story)

> **Quote-accuracy note.** Verbatim quotes below are HIGH-confidence (drawn from the diarized ElevenLabs transcript + post-event brief quote bank). All hard numbers are read directly from Brian's own slides and cross-checked against Fin's published essay (`ideas.fin.ai/p/2x-nine-months-later`). Paraphrases are marked as such. This is **Brian DONOHUE, VP Product, Fin** (formerly Intercom) — not Brian Scanlan, not Andrii Yakovenko. The Salesforce ~$3.6B acquisition is post-event context (June 15, 2026).

---

## 1. Deep-Dive Post (LinkedIn)

Most "AI adoption" advice tells you to give your team the tools and get out of the way.

A product leader at Fin (formerly Intercom) stood up and said the opposite — with nine months of audited receipts to back it.

Brian Donohue, VP Product, walked through how Fin set a deliberate goal to 2X R&D output and actually hit it. The counterintuitive part wasn't the model. It was the rollout.

Phase 1 was the playbook everyone preaches. Use whatever tool you want. No spending limits. Softly, softly — encourage.

It flatlined. For six months.

Phase 2 is where the line breaks upward. Leadership got opinionated — "telling you what to do, how to do it." Adoption became part of performance reviews. A company-wide, gamified hackathon turned skeptics into addicts ("the basic gamification works as a drug"). His blunt summary:

"The best way to get behavior change is to force it."

That lands hard if you've ever rolled AI into a sales, CS, or ops team and watched a pilot quietly die. The orthodoxy — buy seats, run a lunch-and-learn, wait for organic adoption — is exactly the Phase 1 that flatlined.

What makes it credible: they didn't run it on vibes, they measured it.

→ Median time-to-merge: 5.2x faster (14.6 min on auto-approved PRs vs. a 73.8 min org median)
→ Customer-bug backlog: 1,780 → 420, even while absorbing 1,400+ new bugs
→ Fully-loaded cost per PR (payroll + AI): down 45%, from $1,097 to $603

And the number nobody screenshots — peak Claude Code spend hit $128K/week, "not yet optimized for cost." Going all-in is expensive AND deflationary per unit of output. If you're building the AI business case, you need both halves of that sentence.

The playbook, if you want to run it:

1. Name the goal so you're forced to measure it. "2X" wasn't aspiration — it converted a vibe into a tracked number.
2. Pick a "good-enough" proxy fast. They used merged-PRs-per-head, admitted it was crude, and moved on instead of spending three months perfecting a metric.
3. Triangulate it. Merge speed → bug burndown → cost-per-PR. No single number stands alone, which is how you defend against gaming.
4. Force the behavior, then make it stick with a game. The mandate sets the floor; the leaderboard supplies the motivation.

The honest caveats Brian kept in the room: expect the flatline, budget for the spend, and remember the model step-change was necessary but not sufficient. The system around it did the work.

Worth noting as context: eleven days after this talk, Salesforce agreed to acquire Fin for ~$3.6B. The "we have to be willing to make our own business die" turnaround was, in real time, an exit story. Read every number through that lens — but the rollout mechanics stand on their own.

Credit to Brian Donohue and the Fin team for showing the receipts, including the unflattering ones.

If you're rolling AI into a team right now: are you still in Phase 1, waiting for organic adoption that isn't coming?

#AIadoption #RevOps #ChangeManagement #AIstrategy #FutureOfWork

---

## 2. Visual Brief — 5-slide carousel (Arc: Before → After → What Changed → So What)

**Carousel thesis:** Bottoms-up AI adoption flatlines; forced, measured, gamified adoption is what breaks the line upward — and Fin has the audited receipts to prove output doubled and unit cost fell at the same time.

**Slide count:** 5
**Aspect ratio:** 4:5 (1080x1350) — LinkedIn carousel default
**Tool routing summary:** All slides → Gamma (`format: social`, dark Stratos theme, `imageOptions.source: noImages`). Slides 2-4 are data charts rebuilt from Brian's slides; Slides 1 and 5 are typography.

---

### Slide 1 of 5 — Hook: name the contrarian thesis

- **Visual mode:** Bold typography card
- **Headline:** "Force beats encourage."
- **Body / content:** Sub-line: "Fin set out to 2X R&D output. The hard part wasn't the model — it was the rollout." Small footer label: "A measured AI-adoption playbook, with receipts."
- **Palette:** dark slate bg + off-white text + amber accent (#D97706) on the word "Force"
- **Source attribution:** "Brian Donohue, VP Product, Fin — NYC, 2026"
- **Alt text:** Title card reading "Force beats encourage" introducing Fin's AI-adoption story.
- **Tool:** Gamma (typography)

### Slide 2 of 5 — Before: the flatline

- **Visual mode:** Single-line chart (the flatline), rebuilt clean from Brian's productivity slide
- **Headline:** "Phase 1: use any tool, no limits."
- **Body / content:** A near-flat line across Mar 2025 → Oct 2025 (x-axis = month; no y-values — label was illegible, render as relative/flat). Annotation arrow: "6 months. Flat." Caption: "Bottoms-up. Softly encourage. No spending limits."
- **Palette:** dark slate bg + off-white text + muted gray line (deliberately dull — this is the failure state)
- **Source attribution:** "Source: Fin productivity slide, 2026"
- **Alt text:** A flat line from March to October 2025 showing six months of no productivity gain under voluntary AI adoption.
- **Tool:** Gamma (chart)

### Slide 3 of 5 — After: the breakout, in receipts

- **Visual mode:** Three-stat callout row (the PR triptych)
- **Headline:** "Phase 2: forced, measured, gamified."
- **Body / content:** Three stat blocks, equal weight — "5.2x faster median time-to-merge (14.6 min vs 73.8 min)" · "19% of PRs auto-approved" · "86% of auto-approved PRs ≤20 lines". Small connective line beneath: "Mandate + performance reviews + a company-wide hackathon."
- **Palette:** dark slate bg + off-white text + amber accent (#D97706) on the three headline numbers
- **Source attribution:** "Source: Fin deck / ideas.fin.ai, 2026"
- **Alt text:** Three statistics showing 5.2x faster merges, 19% of PRs auto-approved, and 86% of auto-approved PRs under 20 lines.
- **Tool:** Gamma (stat callouts)

### Slide 4 of 5 — What changed: the cost paradox

- **Visual mode:** Split-frame comparison (two charts, one slide) — spend up, unit cost down
- **Headline:** "Expensive AND deflationary."
- **Body / content:** Left mini-bar: weekly Claude Code spend ramping to a $128K peak, label "Not yet optimized for cost." Right mini-bar: fully-loaded cost-per-PR falling Oct $1,097 → Mar $603, label "−45% per PR." Connective caption: "More PRs per head drives the unit cost down."
- **Palette:** dark slate bg + off-white text + amber accent (#D97706); use the accent only on the "$128K" and "−45%" so the two opposing arrows read instantly
- **Source attribution:** "Source: Fin deck, 2026"
- **Alt text:** Two charts side by side — weekly AI spend rising to $128K while cost per merged PR falls 45 percent.
- **Tool:** Gamma (split chart)

### Slide 5 of 5 — So what: the playbook + the question

- **Visual mode:** Framework / checklist card closing on a question
- **Headline:** "Run the play."
- **Body / content:** Four-step checklist: "1. Name the goal so you must measure it · 2. Pick a good-enough proxy fast · 3. Triangulate (speed → burndown → cost) · 4. Force it, then gamify it." Closing question in larger type: "Are you still in Phase 1, waiting for adoption that isn't coming?"
- **Palette:** dark slate bg + off-white text + amber accent (#D97706) on the closing question
- **Source attribution:** "Framework: Brian Donohue / Fin, 2026"
- **Alt text:** A four-step AI-adoption checklist ending with the question of whether the reader is stuck in voluntary Phase 1.
- **Tool:** Gamma (typography / checklist)

---

**Quality gate checks:**
- Arc fit: pass — change-over-time (flatline → breakout) is exactly Arc 3.
- Job differentiation: pass — flatline / receipts / cost-paradox / playbook are four distinct jobs.
- Frame parallelism (Arc 3): pass — Slides 2 and 3 share the "phase" frame and chart language; Slide 4's split-frame is internally parallel.
- Thumb test per slide: pass — each headline ≤6 words; lead numbers are the visual.
- Source citations: pass — every data slide carries a Fin/deck source line.
- Adds information: pass — carousel renders the charts and the spend-vs-unit-cost paradox the post only states in words; no quote re-prints.
- Final slide earns the swipe: pass — closes on the playbook + the reader's own question.

---

## 3. Radar Note (job-search positioning)

Brian Donohue's "2X Story" landed eleven days before Salesforce agreed to acquire Fin for ~$3.6B — making this rollout playbook one of the more validated org-wide AI-adoption case studies in the market right now, and a timely one to be fluent in. For Alex's positioning: this is the exact competency AI-native and revenue-ops orgs are hiring for — not "we bought AI seats," but the measurement rigor and change-management discipline that turns an AI mandate into a tracked, defended, multi-metric result. Amplify it as a curator who can read the receipts (including the unflattering $128K/week and the six-month flatline), not as someone asking to be hired.

---

## 4. Connection Note (≤200 chars, talk-anchored)

Brian — your "2X Story" reframed AI adoption for me: the six-month flatline under "use any tool" vs. the forced + gamified breakout. The measured-not-vibe rigor stuck. Would value connecting.

*(Character count: 191 / 200)*
