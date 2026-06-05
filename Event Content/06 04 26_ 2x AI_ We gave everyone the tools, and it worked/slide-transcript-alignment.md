# Slide ↔ Transcript Alignment — 2x AI: We gave everyone the tools, and it worked

**Event:** 2x AI: We gave everyone the tools, and it worked
**Date:** 2026-06-04 (Thu), evening (~6:22pm ET start)
**Venue:** 18 E 50th St, New York, NY
**Host / presenter:** Brian Donohue — VP Product, Fin (formerly Intercom)
**Co-speaker:** Prithvi Rajasekaran — Technical Staff, Anthropic Labs (organizes GenAI Collective NYC)
**Moderator:** "Christy" (name ASR-unconfirmed — treat her lines as moderator framing, not verbatim-attributable)
**Public companion essays:** `ideas.fin.ai/p/2x-nine-months` (slide footers) · `ideas.fin.ai/p/we-gave-claude-code-to-everyone-at` (Andrii Yakovenko)

---

## What this document is

A one-time, hand-built multimodal alignment of the **9 slide photos** against the **partial transcript** (`Jun 4 at 18_22.txt`, 104 paragraph-lines). It anchors each slide to (a) its exact capture time, (b) the presenter, and (c) the transcript span where it was on screen — and enriches both directions: the slides supply the hard numbers the (near-undiarized) transcript never narrates cleanly; the transcript supplies the verbatim story-telling the slides don't contain.

**Method.** Slide capture times are exact (parsed from `PXL_YYYYMMDD_HHMMSS` filenames = the moment the photo was taken = the moment the slide was on screen). Filenames are **UTC**; this doc presents **ET (UTC−4)** to match the audio/transcript clock. The transcript is sequenced but **not** timecoded, so transcript→time mapping is *anchored-and-interpolated*.

**⚠️ Two caveats specific to this capture:**
1. **The transcript is PARTIAL.** It runs ~40 minutes and cuts off mid-sentence (*"The model is."*) during the product-paradigm panel. It covers Brian's full 2X narrative + the start of the Prithvi/panel discussion. The hard-metrics slides (6–9) were photographed at 18:36–18:39 but their *numbers* are not separately narrated in the captured audio — **for those slides, the slide is the authoritative source.**
2. **The transcript is essentially undiarized** — it is one running `[Speaker 1]` block. All speaker attributions below are reconciled by **segment and content**, confirmed against Alex's in-room recall (steering 2026-06-05): the 2X-deck narration is **Brian**; the "frontend design skill" / creativity lines are **Prithvi**; "Christy" is the **moderator**.

**Confidence legend:** 🟢 High (slide content explicitly referenced in transcript) · 🟡 Medium (inferred from topic adjacency, or slide-authoritative with no verbal anchor) · 🔴 Low (ambiguous / flagged).

---

## Speaker roster (reconciled)

| Name | Role / Company | In pre-event brief? | ASR variants / notes |
|---|---|---|---|
| **Brian Donohue** | VP Product, Fin (11+ yrs Intercom/Fin); host + presenter of the entire 2X deck | ✅ Yes (host) | Clean in transcript by content; deck footer = `ideas.fin.ai` |
| **Prithvi Rajasekaran** | Technical Staff, Anthropic Labs; authored Mar 2026 "harness design for long-running apps"; organizes GenAI Collective NYC (40k+) | ✅ Yes | The design/creativity voice; "wrote the **frontend design skill**" (ASR: "foreign design skill") |
| **"Christy"** | Moderator (asks the panel for "big bets," steers the paradigm Q&A) | ❌ Not in brief | 🔴 Name ASR-unconfirmed — do **not** publish the name or quote her verbatim until confirmed |

> **🆕 Roster delta vs. pre-event research.** The pre-event brief expected **two** speakers (Brian + Prithvi) and framed Prithvi around *agent reliability / the doer-judge harness*. In the captured room, Prithvi instead talked **model design + creativity** (he authored Claude's **frontend design skill**) — a different facet of the same person, not a new speaker. A **moderator ("Christy")** ran the paradigm Q&A and is not in the brief. No new Notion People record is needed for Prithvi/Brian (both exist); **"Christy" gets no record until the name is confirmed.**
>
> **Name reconciliations (brief is source of truth):** Host = **Brian Donohue, VP Product** — *not* Brian Scanlan (Sr Principal Eng, who tells a parallel "2x engineering velocity" story on the *How I AI* podcast) and *not* Andrii Yakovenko (who authored the "Claude Code for everyone" essay). The public record has three different Intercom/Fin people narrating the 2X story; the man on this stage is Donohue.

---

## Slide capture timeline (exact, from filenames; shown ET)

```
18:23:57  start          ← Brian, growth-rate chart (first shot)
18:23:58  +0m01s         ← same chart, re-shot clean
18:26:41  +2m43s         ← productivity flat-line (Mar–Oct '25)  🟡
18:28:10  +1m29s         ← Fin Hackathon Leaderboard
18:33:45  +5m35s         ← Raptor 1/2/3 engines (simplification metaphor)  🔴 attribution
18:36:36  +2m51s         ← THE BURNDOWN ("zero bugs" story)
18:38:11  +1m35s         ← PR metrics triptych (5.2x / 19% / 86%)
18:39:28  +1m17s         ← Weekly Claude Code spend ($128K)
18:39:42  +0m14s         last captured slide (45% cost-per-PR decline)
```

The whole 9-slide burst spans **~16 minutes** (18:23–18:39) — Brian's deck was front-loaded; Alex photographed the results-heavy back half (slides 6–9) in a tight 3-minute run. The transcript's design/paradigm panel (lines ~56–104) runs *past* the last photo, slideless.

---

## The aligned timeline

### SEGMENT 1 — Brian Donohue (Fin): "The 2X Story"
*~18:18–18:40 · the keynote: crisis → 2X bet → forced adoption → results*

| # | Time | Slide | Presenter | Transcript anchor | Conf |
|---|---|---|---|---|---|
| 1 | 18:23:57 | **SaaS vs. Intercom growth rate** — line chart Q4'20→Q4'26. Intercom growth craters from **37% (2021) → ~4% trough (~Q1'23, at the Fin launch / CEO change)**, then climbs back to **37% projected (Q4'26)**, crossing back above the SaaS average. Markers: *"CEO change"* (~Q4'22), *"Fin launch"* (~Q2'23). Dashed = projection. *Source tags: Aventis Advisors & Capital IQ (SaaS); Intercom (Intercom).* | Brian | Lines 2–12: *"2022 was not a good time… our CEO came back… November 2022 when ChatGPT launched… you have to be willing to make our own business die… roughly around the fin launch… it really dramatically changed the trajectory… our fin revenue is going to be over half of our business by the end of the year."* | 🟢 |
| 2 | 18:23:58 | Same chart, re-shot (full, un-occluded) | Brian | Same span | 🟢 |
| 3 | 18:26:41 | **Productivity — the flat early months** — two near-overlapping lines, roughly flat/slightly rising, **Mar 2025 → Oct 2025**, x-axis "Month." (Slide label largely illegible in capture.) | Brian | Lines 28–32: *"phase one… softly, softly encourage… whatever tool you want, no spending limits… and basically a flat line. Flatline for like six months… mediocre adoption, very little standardization, incremental gain, no real meaningful change."* | 🟡 |
| 4 | 18:28:10 | **Fin Hackathon Leaderboard** — *"Real-time rankings of individual performance."* Columns: **1. Simple · 2. Complex · 3. Final Boss · Total · Last Update.** #1 **Henry Larkin** 26.96 · #2 **Miles McGuire** 25.68 · #3 **Ciaran Lee** 25.65 · #4 Murat Toygar · #5 Gustavs Cirulis · #6 James Cash · #7 Emanuele Sparvoli · #8 Eduardo Carvalho · #9 Andrew Murtagh … Joao Fernandes. | Brian | Lines 38–54: *"we did this hackathon… build a RAG system everyone can set up to build Fin yourself… here's the questions to evaluate, there's a score… run it and score it against the leaderboard… the basic gamification works as a drug… a lot of people had no idea what they're doing and entirely Vibe coding through Claude… 'holy s***, I knew nothing about this and I was getting to a reasonable place' — that mental unlock is what we got."* | 🟢 |
| 6 | 18:36:36 | **THE BURNDOWN — "One year of accumulation. Then the cliff."** Stacked-area chart (Low/Medium/High/Critical), Apr'25→Apr'26, peak **1,780 → 420**. Side stats: **Total Resolved 2,500+ · New Incoming Absorbed 1,400+.** The "zero bugs" proof. | Brian | No verbatim narration in the captured ~40 min (this is the "zero bugs a reality" beat from the pre-event Event Description). **Slide is authoritative.** | 🟡 |
| 7 | 18:38:11 | **PR results triptych** — **MEDIAN TIME TO MERGE: 5.2x faster** (auto-approved **14.6 min** vs org median **73.8 min**) · **AUTO-APPROVAL: 19%** of all PRs auto-approved (60% goal; 60% evaluated → 19% approved) · **AUTO-APPROVED PR SIZE: 86% ≤20 lines** (41% = 1–5 lines, 45% = 6–20, 11% = 21–50). Footer: `ideas.fin.ai/p/2x-nine-mon…` | Brian | No separate narration captured. **Slide authoritative.** Relates to lines 34: *"putting it into PR reviews… way more deliberate, opinionated about the system, aggressively driving change."* | 🟡 |
| 8 | 18:39:28 | **WEEKLY CLAUDE CODE SPEND — $128K peak.** Bar chart ramping Jan 5 (~$10K) → **$128K** (mid-Mar). Caption: *"Weekly Claude Code API spend. Not yet optimized for cost. Mar 30 + Apr 6 dips reflect public/school holidays."* | Brian | No separate narration captured. **Slide authoritative.** The "no spending limits / we'll [pay for] anything" posture (line 28) is the cultural anchor for this number. | 🟡 |
| 9 | 18:39:42 | **45% DECLINE IN COST PER PR** — fully-loaded $/PR (payroll + AI): Oct **$1,097** → Nov $1,190 → Dec **$1,477** → Jan $1,123 → Feb $831 → Mar **$603**. Caption: *"Dec spike from reduced holiday productivity. Increasing PRs/head drives cost down."* | Brian | No separate narration captured. **Slide authoritative.** | 🟡 |

**Cross-enrichment (Segment 1):**
- The transcript is the cleaner source for the **story**; the slides are the cleaner source for the **numbers** — they barely overlap, which is exactly why reading them together is the value. Brian *tells* the crisis-and-turnaround arc (slides 1–4) and *shows* the receipts (slides 6–9) but doesn't read the receipts aloud in the captured audio.
- **Phase structure (from transcript):** Phase 1 = *"softly, softly encourage"* (bottoms-up, no limits) → 6-month flatline (slide 3). Phase 2 = *"way more deliberate… opinionated about the system, aggressively driving change… telling you what to do, how to do it… putting it into PR reviews"* (forced, top-down). The hackathon (slide 4) is the hinge that made forced adoption *stick* by making it fun.
- **The rename is news:** *"we actually finally changed the name of our company. From Intercom to Fin, just a couple weeks ago."* (lines 16–18) — Intercom → **Fin**, ~late May 2026.
- **Ciaran Lee** (leaderboard #3) is an **Intercom co-founder & former CTO** — the detail that the co-founder is *in the hackathon, mid-pack* is a strong "everyone, including the founders" color note.

**Verbatim worth keeping (Brian):**
- *"You have to basically be willing to make our own business die."* (line 6) — the all-in thesis.
- *"The best way to get behavior change is to force it."* (line 38)
- *"The basic gamification works as a drug."* (line 44) + *"It got everyone like 'holy s***, I knew nothing about this and I was actually getting to a reasonable place.' That mental unlock is what we got."* (line 50)
- *"2X is ambitious and simultaneously not, at the same time — that's what it felt like… and we said let's actually measure it. It took us nine months to get there. And we did it."* (lines 22–26) — **the measured-not-vibe money quote.**

---

### SEGMENT 2 — Prithvi Rajasekaran (Anthropic) + paradigm panel
*~18:30–18:42 · model design, creativity, and the next product paradigm · mostly slideless*

| # | Time | Slide | Presenter | Transcript anchor | Conf |
|---|---|---|---|---|---|
| 5 | 18:33:45 | **Raptor 1 / Raptor 2 / Raptor 3** — three SpaceX rocket engines side by side, each visibly **simpler / cleaner** than the last. The iterate-toward-simplicity metaphor. | 🔴 **Attribution uncertain** — thematically distinct from Brian's metrics deck; best fit is the design/iteration discussion (Prithvi) or a Brian "our systems got simpler" aside. No verbal anchor in captured transcript. | Topic-adjacent to lines 58–78 (models improving by *"breaking it down into a mathematical or scientific manner… that last mile of human intuition, judgment, taste"*) | 🔴 |

**The slideless panel content (lines 56–104) — verbatim bank:**
- **Prithvi on creativity (lines 66–68):** *"There's a book… 'Steal Like an Artist'… every good piece of art is a remix of some other piece of art. If you give the model a reference and have it remix in some way — that's going to be very favorable. We're almost asking, like, what real creativity can be."* (Austin Kleon, *Steal Like an Artist* — real book. 🟢)
- **Prithvi on the design skill (line 74):** *"A lot of the capability comes from the **frontend design skill**, which is something that I wrote — a set of instructions to make the model more creative… I saw the model get to a point where it was designing things way better than what I was designing."* (ASR rendered "frontend design skill" as "foreign design skill"; "Claude design" as "cloud design." 🟢 with correction.)
- **On the last mile (lines 58–60):** *"The models get very good, but under the hood we're breaking it down into almost a mathematical or scientific manner… that last mile of human intuition, judgment, taste — that'll be the last thing to go."*
- **Paradigm — goal vs. task (lines 92–94):** *"You're working with the LLMs in a goal-driven way, not a task-driven way. That's the huge shift… it moves up the stack of value… conversations will be increasingly dominant as the form of UI, but not on their own — the rest doesn't go away. You still need reference artifacts."*
- **On the GUI (lines 82–84):** *"The GUI is not dead… background and chat with on-demand GUI being built in… everyone's figuring out the dynamic between what is the UI."*
- **Christy [MODERATOR — paraphrase only, 🟡]:** asked the panel where they'd *"place your big bets on the next paradigm shift"* (line 98); began answering with a customer-problem-first vs. model-capability-first framing (lines 100–104) before the recording cut off.

**Cross-enrichment (Segment 2):** This is the freshest, least-public material — an Anthropic engineer saying out loud that *he* hand-wrote the skill that makes Claude design better, and that creativity is "remix." It pairs cleanly with Brian's skills/hackathon story: **both speakers treat a written "skill" as the unit of capability** (Brian: engineers building eval/RAG skills in the hackathon; Prithvi: the frontend-design skill). That convergence is a post angle in itself.

---

## Event-wide patterns the alignment surfaces

These only become visible reading slides + transcript together:

1. **"Measured, not a vibe" — and here are the receipts.** Brian explicitly frames 2X as *measured over nine months* (line 26), and the back-half slides are the audited proof: 5.2x faster merge, 45% lower cost-per-PR, a 1,780→420 bug burndown. This is the spine of the lead post (Alex's chosen angle): the pre-event question was *"is 2X measured or a poster?"* — the slides answer **measured.** The honest counter-beat: the productivity line was **flat for 6 months first** (slide 3), and they're spending **$128K/week** on Claude Code to get it (slide 8).
2. **Force beats encourage.** The single most counter-cultural admission of the night: bottoms-up *"use whatever you want, no limits"* produced a 6-month flatline; the breakout came only when leadership got *"opinionated… aggressively driving change… telling you what to do."* The gamified hackathon is what made the force *feel* like fun. Strong contrarian hook against the "just give people AI and get out of the way" orthodoxy.
3. **A written "skill" is the unit of capability — said by both companies.** Fin's engineers build eval/RAG skills in a hackathon; Anthropic's Prithvi hand-writes the frontend-design skill. The skill file, not the prompt, is where the leverage is. Convergent with the 6/3 Masterclass thread ("nobody reads the skills") — **synthesis candidate.**
4. **The cost story cuts both ways.** $128K/week peak spend "not yet optimized for cost," *and* a 45% decline in fully-loaded cost-per-PR. Going all-in is simultaneously expensive and deflationary — the most nuanced, least-tweeted number in the deck.
5. **Everyone, including the co-founder.** Ciaran Lee (Intercom co-founder) sits mid-leaderboard; non-engineers "vibe-coding through Claude" reached "a reasonable place." The "we gave *everyone* the tools" claim is literally visible in the leaderboard.

---

## ASR correction glossary (slides / facts fixing the transcript)

| Transcript (wrong) | Correct |
|---|---|
| intercom (the company) | **Intercom** → renamed **Fin** (~late May 2026) |
| Finn / fin | **Fin** (company name + the AI agent) |
| Chad GPT | **ChatGPT** |
| Ford deployed engineer | **forward-deployed engineer** |
| rat system / rack system / Guild your own rack | **RAG system** ("build your own RAG system") |
| thoughts / pod / pods | 🔴 internal tool name — unverified; do not quote |
| foreign design skill | **frontend design skill** (Prithvi's) |
| cloud design | **Claude design** |
| steal like an artist | **"Steal Like an Artist"** (Austin Kleon, real book) |
| Dara / Darren / Tara / Nicole / Mario | 🔴 internal Fin names — ASR-uncertain; **do not attribute quotes to them.** (Public record: the CEO who returned Oct/Nov 2022 is **Eoghan McCabe** — but the transcript does not reliably name him; don't publish a name.) |
| Ciaran Lee (leaderboard) | **Ciaran Lee** — Intercom co-founder / former CTO ✅ |

---

## Open ambiguities (verify before public use)

- 🔴 **Moderator "Christy":** name unconfirmed — do not publish or quote verbatim.
- 🔴 **Slide 5 (Raptor engines):** presenter + exact point unconfirmed; use as a *visual metaphor* (iterate toward simplicity), don't attribute a spoken line to it.
- 🟡 **Slide 3 (flat-line chart):** label illegible; interpreted as the phase-1 productivity flatline from the transcript. Don't cite specific values off it.
- 🟡 **Slides 6–9 numbers:** authoritative *from the slides* (and corroborated by `ideas.fin.ai/p/2x-nine-months`), but **not** spoken in the captured audio — cite them as "from Fin's deck," not "Brian said."
- 🔴 **Internal names** (Dara/Darren/Tara/Nicole/Mario): excluded from all public copy.
- ✅ **Speaker split** (Brian = 2X deck; Prithvi = design/creativity; Christy = moderator): confirmed by Alex's in-room recall, 2026-06-05.

---

## How to use this in `/post-event-content`

- Feed this file alongside the conditioned transcript as a **reference input** to the `post_event_brief`. The quote bank tags each verbatim with the slide it pairs with — e.g., Brian's *"willing to make our own business die"* pairs with the growth-rate crater chart for a quote-card-with-context visual.
- **Lead angle (Alex's pick): "measured, not a vibe."** The post tests the 2X claim against the deck's audited numbers (slides 6–9), then keeps it honest with the two costs the headline hides: the 6-month flatline and the $128K/week spend.
- The **event-wide patterns** are pre-built angles: #2 (force beats encourage) is the strongest *alternate* single post; #3 (the skill is the unit of capability) is the **synthesis candidate** with the 6/3 Masterclass "nobody reads the skills" thread.
- The **ASR glossary** should be applied during transcript-conditioning (Step 3.5) so no garbled brand/name reaches a draft. **No internal Fin names** in public copy.
- The strongest **carousel source material** is the numbers themselves — a Gamma "is 2X real?" scorecard (claim → slide number → caveat) rather than re-printing any one chart. Slides 1 (crater→recovery), 7 (PR triptych), 9 (cost decline) are the cleanest redraw inputs.

---
*Built 2026-06-05 · one-time manual alignment · partial transcript (~40 min, cuts off mid-panel). Mirrors the 6/3 Masterclass alignment method. If this materially improves the drafts, formalize as a slide-index step in `/post-event-content` per CLAUDE.md "build-better-not-faster" discipline.*
