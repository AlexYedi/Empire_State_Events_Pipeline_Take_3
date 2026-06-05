# Slide ↔ Transcript Alignment — NYC GTM+AI Masterclass #5

**Event:** NYC GTM + AI Masterclass #5 — NY Tech Week Special
**Date:** 2026-06-03 (Tue), evening
**Venue:** Insight Partners HQ, NYC
**Host community:** NYC Go-To-Market (GTM) Community (founder: Nemo)
**Sponsor:** Swan (discount credits / S1 tooling)

---

## What this document is

A one-time, hand-built multimodal alignment of the **22 slide photos** against the **diarized transcript** (`Jun 3 at 18_04.txt`, 862 lines). It anchors each slide to (a) its exact capture time, (b) the presenter, (c) the transcript span where it was on screen, and enriches both directions: slides supply the structured frameworks the ASR garbled; the transcript supplies the verbatim commentary the slides don't contain.

**Method.** Slide capture times are exact (parsed from `PXL_YYYYMMDD_HHMMSS` filenames = the moment the photo was taken = the moment the slide was on screen). The transcript is sequenced but **not** timecoded, so transcript→time mapping is *anchored-and-interpolated*: pinned where a slide's content is explicitly referenced, interpolated between anchors.

**Confidence legend:** 🟢 High (slide content explicitly referenced in transcript) · 🟡 Medium (inferred from topic adjacency) · 🔴 Low (ambiguous / flagged).

**⚠️ Diarization caveat.** The transcript's `[Speaker N]` labels are unreliable — they swap mid-sentence and a single person is split across multiple numbers. All speaker attributions below are reconciled by **segment and content**, not by Speaker number. Treat names as the source of truth; ignore the raw `[Speaker N]` tags.

---

## Speaker roster (reconciled)

| Name | Role / Company | In pre-event brief? | ASR variants in transcript |
|---|---|---|---|
| **Jennifer Schwarz** | MC / co-host, NYC GTM Community (EcoMotion) | ✅ Yes | "Jennifer", "Schwartz" |
| **Nimo Shkedy** | Founder, NYC GTM Community / Impact 11; ran the Swan/S1 cloud-harness demo | ✅ Yes (host) | "Nemo" |
| **Sangram Vajre** | CEO, GTM Partners; ex-Terminus founder, ex-Pardot | ✅ Yes | "Sandra", "sangram", "Sangram Vaire" |
| **Eric Nowoslawski** | Founder, Growth Engine X (cold-email agency; early Clay collaborator) | ✅ Yes | "Eric", possibly mis-intro'd as "Harry" |
| **Nikita** | Optimizely — PM on **Opal** (AI agent harness for marketers); Insight portfolio | ❌ **Added after** | "Nikita" |
| **Kenny** | Head of Marketing / "GTM engineer", **CoverForce** (Insight portfolio) | ❌ **Added after** | "Kenny", "coverforce" / "Hubbard Forest" |
| **Jack** | Insight Partners — AI Lab / advisory (applied AI team); venue host | ❌ Not in brief (host intro) | "Jack" |

> **🆕 Roster delta vs. pre-event research.** The pre-event brief (`NYC GTM+AI Masterclass #5 — Research Brief`, Notion) covered 4 people: Sangram, Nimo, Eric, Jennifer. **Two content presenters were added after** and appear only in the event material: **Nikita (Optimizely / Opal)** and **Kenny (CoverForce)** — both Insight Partners portfolio companies, slotted in by the venue host (Jennifer: *"we're gonna hear two of them today"*). Plus **Jack** (Insight AI Lab) did the venue intro. → These three have **no Notion People records yet**; create them when committing post-event content. Jack maps directly to the brief's "Insight Onsite" bonus job-search target (Success Signal #4).
>
> **Name reconciliations (brief is source of truth):** Host's real name is **Nimo Shkedy** (transcript ASR = "Nemo"). Sangram = **Vajre** (his book/brand; the slide footer's "Vajre" confirms — I mis-typed "Vaire" from the photo). Jennifer's surname: brief = **Schwarz**, transcript = "Schwartz" — 🟡 confirm.
>
> **Identity flag:** Jennifer announces the cold-email presenter as "Harry," but he self-IDs as running **Growth Engine X** + early Clay → **Eric Nowoslawski** (later addressed as "Eric" by Nimo). 🟡 "Harry" is likely ASR error.

---

## Slide capture timeline (exact, from filenames)

```
22:18:48  start
22:19:52  +1m04s
22:26:11  +6m19s
22:43:28  +17m17s   ← presenter change (Sangram → Eric)
22:46:10  +2m42s
22:47:27  +1m17s
23:03:20  +15m53s   ← presenter change (Eric Q&A → Nikita)
23:05:02  +1m42s
23:05:31  +0m29s
23:07:05  +1m34s
23:08:33  +1m28s
23:10:29  +1m56s
23:12:02  +1m33s
23:13:26  +1m24s
23:14:30  +1m04s
23:16:00  +1m30s    ← last Nikita slide before the Nemo/Jack harness interlude
23:36:31  +20m31s   ← Nemo external-multiplayer demo (after ~20m of talk + live S1 demo)
23:47:03  +10m32s   ← presenter change (Nemo → Kenny / CoverForce)
23:48:36  +1m33s
23:49:53  +1m17s
23:53:00  +3m07s
23:57:30  +4m30s    last captured slide
```

The gaps are the event's seams: **+17m / +16m / +20m / +10m** gaps mark presenter transitions and Q&A; the dense **23:03–23:16** run (10 slides in 13 min) is Nikita walking the Opal deck fast.

---

## The aligned timeline

### SEGMENT 1 — Sangram Vajre (GTM Partners): "The GTM Operating System"
*~22:15–22:40 · opening keynote + Q&A*

| # | Time | Slide | Presenter | Transcript anchor | Conf |
|---|---|---|---|---|---|
| 1 | 22:18:48 | **The GTM Operating System** — wheel of 8 questions (Total Relevant Market, Market Investment Map, Brand & Demand, Pipeline Velocity, Customer Time-to-Value, Customer Expansion, Revenue Ops, Leadership & Mgmt). Tag: *Sangram Vajre, CEO @ GTM Partners.* | Sangram | Lines ~85–126: *"it really came down to eight questions… the go to market operating system… building your entire go to market on one slide."* | 🟢 |
| 2 | 22:19:52 | Same wheel (re-shot) | Sangram | Same span; he holds on the wheel while walking the Terminus example (lines 123–149). | 🟢 |
| 3 | 22:26:11 | **"Race to $10M. Different category. Same game."** — Terminus-vs-GTM-Partners comparison list: *Services / GTM / 1 WSJ best-selling book / Roadshow & Roundtable (exec-focused) / Thinkific + Swan + Kit + Claude + Super Agent / 2+ / $1M→$5M→$10M+ / Lifestyle + Franchise model.* | Sangram | Lines ~153–161: *"I'll compare Terminus plus GTM Partners… 2021 bootstrap down market… our tech stack is thinkific Swan kit quad… two co-founders… 10 million dollar business in the last five years."* | 🟢 |

**Cross-enrichment:** The slide is the cleaner source for Sangram's GTM-Partners stack — the transcript mangles it as *"thinkific Swan kit quad"*; the slide reads **Thinkific + Swan + Kit + Claude + Super Agent**. Book = **MOVE** (WSJ bestseller; Geoffrey Moore — "*Jeffrey Motorsay*" in ASR — endorsed it). Terminus = ABM category creator, exited to PE; Sangram's prior path Pardot → ExactTarget ($100M) → Salesforce ($2.7B).
**Verbatim worth keeping (line 246):** *"There is no right answer to any of these questions… It has nothing to do with being right. There is no certainty except taxes and death. What this gives you is clarity."*
**Verbatim (line 221):** *"The CEO owns go-to-market, and therefore go-to-market is the business. Anything that drives business is go-to-market."*

---

### SEGMENT 2 — Eric Nowoslawski (Growth Engine X): "Build your first AI employee"
*~22:42–23:00 · 3-step framework: Context → Connection → Creation*

| # | Time | Slide | Presenter | Transcript anchor | Conf |
|---|---|---|---|---|---|
| 4 | 22:43:28 | **Context: Build the Company Brain** (STEP 1 OF 3). *"Your AI employee is only as good as the knowledge you give it."* SOPs, ICP defs, campaign examples, reporting templates. Callout: *not a technical person? that's the point.* | Eric | Lines ~322–340: *"you need to solve for context… give it the standard operating procedures… make a company brain for me in markdown files… 1M token context window = the Bible."* | 🟢 |
| 5 | 22:46:10 | **Connection: Give It Access to Where Work Happens** (STEP 2 OF 3). Hub-and-spoke: **Hermes / OpenClaw** center; Fathom (meetings), Slack (comms), CRM (deal data), Email (outreach), Obsidian (company), Codex (skills & code). Warn: *avoid brittle automation first.* | Eric | Lines ~342–348: *"the second thing… is connection… everybody asking me for API keys… open your Chrome history, dedupe, give me a list of all the tools."* | 🟢 |
| 6 | 22:47:27 | **The First Workflow to Build** (MEETING→SUGGESTION→APPROVAL): 01 New Fathom recording detected · 02 Pull transcript + identify context · 03 Read company brain + relevant skills · 04 Suggest what to do next · 05 Human approves/tweaks/rejects · 06 Save feedback for future runs. | Eric | Lines ~350–360: *"our loop is: new Fathom recording detected, pull the transcript, read the company brain and relevant skills, suggest what to do next, we approve or tweak, it saves feedback."* Near-verbatim match to slide. | 🟢 |

**Cross-enrichment:** Slide spellings correct the ASR throughout: **Codex** (not "codecs"), **Hermes / OpenClaw** (not "open claw"), **Obsidian**, **Fathom**. Eric's agents are named **Dale** (Carnegie) and **Milton** (Friedman). Security: routes API keys through **trigger.dev** so agents never hold keys.
**Verbatim (line 288):** *"I accidentally cut my team by 50%, and we're sending more emails, because I made an AI employee."* (7 employees vs. peers' ~30 at the same revenue band.)
**Verbatim (line 418, the adversarial-skill tip):** *"Whenever you make a skill, try to make an adversarial skill… 'pretend this is the worst idea in the world and find every problem.' Because AI gets a bit sick of fantasy and just goes 'you're the best guy ever.'"*
**Verbatim (line 412, his copy philosophy):** *"I want to send the same message I would send if I manually researched somebody's company and them personally for 10 minutes."* (Built on a **Josh Braun** framework baked into a meta-skill.)

---

### SEGMENT 3 — Nikita (Optimizely): "Nine lessons from building Opal"
*~23:03–23:16 · enterprise AI agent harness for marketers · ~$400M ARR, two decades*

| # | Time | Slide | Presenter | Transcript anchor | Conf |
|---|---|---|---|---|---|
| 7 | 23:03:20 | **Marketing's coordination problem** — 15,500+ marketing tools · 12+ disconnected systems/campaign · 10+ rounds to get content right · 4+ teams sign off (creative/legal/product/compliance) · 6+ (scaling, cut off). *"Coordination across chaos."* | Nikita | Lines ~503–510: *"the core problem we've always tried to solve is coordination across chaos… high stakes… legal, compliance, product… 15 different systems."* | 🟢 |
| 8 | 23:05:02 | **The Opal platform architecture** — Interface (Chat/Artifacts/Action Cards/Headless) · Context · Tools · Skills · Agents · Foundation (Identity/Memory/Governance/Models) · built on Optimizely (CMP/CMS/DAM/Experimentation). | Nikita | Lines ~511–512: *"this is a high level of our opal platform architecture… the top part is what we've built out over the past two years… fundamental reusable systems across any agent harness."* | 🟢 |
| 9 | 23:05:31 | **Chat, artifacts & action cards** (THE INTERFACE). Lesson: *chat is great but rich UX earns its keep.* | Nikita | Lines ~513–519: *"chat is great… but you don't want to just look at blobs of text… we introduced artifacts… and action cards."* | 🟢 |
| 10 | 23:07:05 | **Knowledge that compounds over time** (COMPONENT 01 · CONTEXT) — org-level / user-level / agent-level. Lesson: *org-level context is a big unlock.* | Nikita | Lines ~521–526: *"we think about context in three layers: organizational, user, and agent level… set up brand guidelines, tone, writing style… valuable for everybody from day one."* | 🟢 |
| 11 | 23:08:33 | **Connecting across your martech stack** (COMPONENT 02 · TOOLS) — Native Optimizely / Third-party 50+ (GA4, Salesforce, Marketo, HubSpot, Google) / Custom tool builder. Lesson: *quality over quantity — 10 well-integrated tools beat 100 shallow ones.* | Nikita | Lines ~527–538: *"quality over quantity… everybody has a HubSpot connector… we wrote a skill to guide the LLM… 'golden accounts'… a translation layer on top of the raw tool call."* | 🟢 |
| 12 | 23:10:29 | **Agents vs. skills** (COMPONENT 3 & 4). Agent = autonomous entity (reasons w/ LLM, lifecycle); Skill = reusable capability (structured logic, no loop, invoked by agents). *In code: Agent = running service, Skill = a library function it calls. On a team: Agent = employee who decides, Skill = the SOP they follow.* | Nikita | Lines ~539–549: *"agents have their own autonomous reasoning loop… skills are more like a static list of instructions… agents = an employee you hand tasks to; skills = the standard operating procedures."* | 🟢 |
| 13 | 23:12:02 | **Quality: Agent Reliability Engineering** (COMPONENT 04 · AGENTS) — Agent SLIs/SLOs (tool_success ≥95%, thumbs_down <10%) · Automated eval pipeline (change→run evals→pass→deploy / fail→block+alert) · Deep observability. Lesson: *treat reliability as a software problem; pair LLM evals with deterministic measures so quality is provable, not vibes.* | Nikita | 🟡 Captured during her run; she moved fast and didn't narrate every box. Slide is the authoritative record here. | 🟡 |
| 14 | 23:13:26 | **Agent Teammates as first-class users** (FOUNDATION · IDENTITY) — Human vs Agent accounts structurally identical (*but a teammate can never escalate its permissions*). Three deployment types: Personal (digital twin) / Team (digital employee) / Public (external-facing, sandboxed). | Nikita | 🟡 Topic-adjacent to lines 541–549; slide carries detail beyond the narration. | 🟡 |
| 15 | 23:14:30 | **Human-in-the-loop, built for scale** (FOUNDATION · GOVERNANCE) — volume table: 10/day Slack buttons work · 100/day things get missed · 1,000/day impossible · 10,000/day AI-assisted triage. Lesson: *don't bolt on a separate approval flow — extend the work management you already run.* | Nikita | 🟡 Governance close; the volume table is the slide's unique contribution. *"Reactive → proactive… with an Agent Teammate acting on its own, risk concentrates."* | 🟡 |
| 16 | 23:16:00 | **Nine lessons from building Opal** — summary grid (01 Interface · 02 Context · 03 Tools · 04 Skills · 05 Agents · 06 Agents vs skills · 07 Reliability · 08 Identity · 09 Governance). | Nikita | Line ~501: *"these are nine lessons that we've learned over the past two years… I'll show this slide at the end as well."* The promised recap. | 🟢 |

**Cross-enrichment:** Opal = Optimizely's marketer-facing agent harness; ~**$400M ARR**, ~two decades old, re-platformed for LLMs. The **"wrote a skill to guide the LLM toward 'golden accounts'"** story (line 533) is the concrete proof point for the org-context lesson. Best soundbite for a "harness" post.
**Verbatim (line 521):** *"Context is king, context is queen."*

---

### SEGMENT 4 — Nimo Shkedy (NYC GTM Community / Swan · S1): the cloud harness + external multiplayer
*~23:16–23:45 · ~20m of framing + live S1 demo, then the network slide*

| # | Time | Slide | Presenter | Transcript anchor | Conf |
|---|---|---|---|---|---|
| 17 | 23:36:31 | **External multiplayer** — Network Analysis & Planning Engine (maps relationships, scores paths, suggests actions) → **Network** (Champions / Creators / Communities / Prospects / Partners) → **Collaborations** (Content / Testimonials / Webinars / Events / Referrals) → feeds back as *"new relationships."* | Nemo | Lines ~677–714: *"co-creation is gonna replace cold outreach… I don't qualify by title or company, I qualify by influence… who has influence over the people I want to sell to… two degrees out."* | 🟢 |

**Cross-enrichment & structure note:** The 20-minute gap (23:16→23:36) is **Jack + Nemo's harness interlude** (transcript ~553–650): Jack reframes Nikita's Opal as *"a go-to-market OS with shared context, shared skills, shared resources… but where does it live? It lives in the cloud, for your whole team"* — vs. Claude Code, which *"lives on your PC."* Then Nemo runs a **live S1 / Swan demo** (the sponsor tool) on a company instance called **copper helm** — shared resources (founders, mailboxes, CRM/Slack), shared skills (a *"reply classification"* skill he built by prompting, not by writing a skill file), and an enrichment/playbook system. The network slide (#17) is the climax: his thesis that **co-creation / network-building replaces cold outreach.**
**Verbatim (line 677, Nemo's POV — strong for a documentarian contrast post):** *"Co-creation is going to replace cold outreach. It's going to replace most of the content… Outreach is flooded, inboxes are flooded, people are becoming blind. What's going to differentiate you is collaborations."*
**🔴 Flags:** Tool naming is muddy — **S1 / Swan / "Super Agent"** appear interchangeably; the demo company is **copper helm**, a client example is **Nokai** (spelling unverified). The *"New York City clay World Cup"* aside (line 572) is real-sounding but worth a sanity check before quoting. Verify product name(s) before any public post.

---

### SEGMENT 5 — Kenny (CoverForce): the ABM bot, end to end
*~23:45–23:58 · "GTM engineer," Insight portfolio · footer reads "CoverForce · ABM bot · Kenny · May 2026"*

| # | Time | Slide | Presenter | Transcript anchor | Conf |
|---|---|---|---|---|---|
| 18 | 23:47:03 | **The system, end to end** — Signals In (Gong call transcripts / HubSpot pipeline+replies / Notion ICP defs / Web signals / LinkedIn) → **Agents** (Research / Contact Selection / Copywriting / Routing) → Outbound Out (Instantly email / HeyReach LinkedIn / Slack AE approvals / Gifting + Direct Mail). Data storage: **Supabase**. | Kenny | Lines ~785–805: *"Gong call transcripts… HubSpot emails… Notion… loaded into Supabase… a couple different agents broken into four: research, context selection, copywriting, routing."* | 🟢 |
| 19 | 23:48:36 | **Four agents, one job each** — Research Agent (divisional research, leadership mapping; reads Web·Gong·HubSpot·Notion·LinkedIn) · Contact Selection (buying-committee scoring; 1,000+ → ranked 12) · Sequence Agent (persona-aware copy, <50 words, 7-step cadence) · Routing Agent (who sends, which channel; *CEO-to-CEO overrides through Cyrus*). | Kenny | Lines ~810–824: *"the research agent's job is to figure out the teams… contact selection identifies the right people… sequence agent: best messaging per channel… routing automates the upload."* | 🟢 |
| 20 | 23:49:53 | **Account context, then the contact** — Account-level brief (recent news, 10-K/10-Q financials, tech initiatives, key hires, events, partnerships; + Gong/HubSpot/Notion internal) **refreshed weekly** · **"The Online Stalker"** per-contact monitor (connections, LinkedIn activity, events attending, direct quotes, news mentions) **refreshed biweekly**. *"Every email opens with something specific and recent — not a templated hook."* | Kenny | Lines ~826–834: *"financial statements is a great one… we also build what I call an online stalker… do we know anybody that's connected? scrape followers… track who they're interacting with."* | 🟢 |
| 21 | 23:53:00 | **Seven touches. Ten for the high-priority list.** — 10-touch / ~22-day cadence (4 email · 3 LinkedIn · 3 gift), Day 1 Intro → Day 22 Breakup. Message build per-contact/per-touch: Buyer type × ICP segment (Brokerage/Wholesaler/InsurTech/PEO) → pull angle from messaging-strategies playbook → signal as hook. *<50 words · 1 markdown playbook · zero templates reused.* | Kenny | Lines ~846–850: *"this AVM [ABM] cadence takes 22 days… a mixture of email, LinkedIn, and gifting… using the buyer type, ICP segment, messaging charters from Notion."* | 🟢 |
| 22 | 23:57:30 | **Tools Used** (10/14) — Claude · Gong · Clay · Instantly · HeyReach · Slack · Supabase · Render · HubSpot. | Kenny | Lines ~842–844: *"this is Claude Code on Pocket… connecting a bunch of systems… I also don't ever look at the skills, I just imagine it works."* | 🟢 |

**Cross-enrichment:** The slides are the authoritative spellings — ASR mangles CoverForce as *"Hubbard Forest,"* HeyReach as *"Hayriage Resort,"* Instantly as *"swing,"* Supabase as *"super base."* The marquee account example is **Aon** (*"ale" / "aeon"* in ASR — a ~60,000-person insurance broker; filters down 15,000 → ~3,000 VP+ → ranked **12** contacts). CoverForce sells to billion-dollar insurance brokers / wholesalers in the US.
**Verbatim (line 842, the "I don't read skills" through-line that recurs across 3 speakers):** *"This is Claude Code on Pocket… I also don't ever look at the skills. I don't know what it's doing, but I just imagine it works."*

---

## Event-wide patterns the alignment surfaces

These only become visible once slides + transcript are read together — they're the documentarian gold:

1. **"I never read the skill files" — said independently by THREE presenters** (Eric line 404–406, Nemo line 623, Kenny line 842). A genuine, slightly subversive theme of the night: practitioners trusting the model to self-organize, treating skills as write-only artifacts. Strong contrarian post hook.
2. **"Harness" became the word of the night** — Nemo explicitly called it out (line 584: *"the word that I almost asked all the speakers not to say, but everybody ended up saying it is harnesses"*). Four different speakers, four different harnesses (Hermes/OpenClaw, Opal, S1/Swan, Claude Code on Pocket).
3. **The same architecture, drawn four ways.** Eric's "Context → Connection → Creation," Nikita's Opal stack, Kenny's "Signals → Agents → Outbound" are the *same reference architecture* (context store + connectors + agents + human approval loop) at three maturity levels: solo (Eric), enterprise product (Nikita), mid-market in-house build (Kenny). A clean "convergent architecture" thesis.
4. **The single real disagreement — cold outreach.** Kenny's entire system *industrializes* cold outbound (100k emails/day elsewhere on the bill); Nemo stands up and says *"co-creation is going to replace cold outreach."* That tension, in the same room on the same night, is the spine of a two-thesis synthesis post.
5. **Human-in-the-loop survived every demo.** Eric's "meat gates," Nikita's governance volume table, Kenny's Slack AE approvals — nobody claimed full autonomy. The honest counter-narrative to "agents replace teams."

---

## ASR correction glossary (slides fixing the transcript)

| Transcript (wrong) | Correct (from slides) |
|---|---|
| Sandra / sangram | **Sangram Vajre** (GTM Partners) |
| Nemo | **Nimo Shkedy** (host) |
| Jeffrey Motorsay | **Geoffrey Moore** |
| codecs | **Codex** |
| open claw / Hermes | **OpenClaw / Hermes** |
| fathom | **Fathom** |
| super base | **Supabase** |
| swing | **Instantly** |
| Hayriage Resort | **HeyReach** |
| Hubbard Forest / coverforce | **CoverForce** |
| ale / aeon | **Aon** (insurance broker) |
| opal | **Opal** (Optimizely) |
| thinkific Swan kit quad | **Thinkific + Swan + Kit + Claude + Super Agent** |
| AVM / accountabis marketing | **ABM** (account-based marketing) |
| copper helm | **copper helm** (Nemo's S1 demo instance — spelling unverified 🔴) |

---

## Open ambiguities (verify before public use)

- 🔴 **Cold-email presenter name:** "Harry" (Jennifer's intro) vs. **Eric Nowoslawski** (self-ID via Growth Engine X + Clay). High confidence it's Eric; confirm.
- 🔴 **Nemo's product naming:** S1 / Swan / "Super Agent" used interchangeably; "copper helm" and "Nokai" spellings unconfirmed.
- 🟡 **Slides 13–15 (Nikita's Reliability / Identity / Governance):** captured but lightly narrated — content is from the slides, not her spoken words. Don't attribute spoken quotes to these.
- ✅ **Sangram surname:** resolved to **Vajre** (brief + slide footer + his book/brand). "Vaire" was my photo mis-read.
- 🟡 **Jennifer surname:** brief = Schwarz, transcript = Schwartz — confirm.

---

## How to use this in `/post-event-content`

- Feed this file alongside the conditioned transcript as a **reference input** to the `post_event_brief`. The quote bank can then tag each verbatim with *which slide was on screen* — e.g., Sangram's "go-to-market is the business" pairs with the GTM Operating System wheel for a quote-card-with-context visual.
- The five **event-wide patterns** above are pre-built post angles (esp. #4 cold-outreach tension → two-thesis synthesis; #1 "nobody reads the skills" → contrarian single post).
- The **ASR glossary** should be applied during transcript-conditioning (Step 3.5) so no garbled brand/name reaches a draft.
- Slides 4–6 (Eric), 10–12 (Nikita), 18–21 (Kenny) are the strongest **carousel source material** — they're already clean architecture diagrams; a visual brief can redraw them as a single "convergent GTM-agent architecture" comparison rather than re-printing any one deck.

---
*Built 2026-06-05 · one-time manual alignment · not yet a pipeline component. If this materially improves the post-event drafts, formalize as a slide-index step in `/post-event-content` (see CLAUDE.md "build-better-not-faster" discipline).*
