# POST-EVENT BRIEF — NYC GTM + AI Masterclass #5 (NY Tech Week Special)

**Event:** NYC GTM + AI Masterclass #5 — NY Tech Week Special
**Date:** 2026-06-03 (Tue) evening · **Venue:** Insight Partners HQ, NYC
**Host community:** NYC Go-To-Market (GTM) Community (founder: Nimo Shkedy) · **Sponsor:** Swan (S1) — 20% discount credits
**Format:** Five 15-min case-study talks + Q&A, ~100 attendees, MC Jennifer Schwarz

> **Quote-accuracy caveat.** Quotes are reconstructed from the ElevenLabs (scribe_v2) transcript, reconciled against the slide photos and the hand-built slide↔transcript alignment doc. Speaker diarization in the raw ASR is unreliable (labels swap mid-sentence); attributions here are reconciled by segment + content, not by raw `[speaker_N]` tags. Where a word was low-confidence I paraphrase or flag `[VERIFY]`. **Slides override ASR for all names, brands, and numbers.** Nothing here is fabricated; unverifiable items are flagged in §18.

---

## 1. Quick Take

The single most role-relevant night in the set: five practitioners showed, not told, how AI is rewriting the GTM operating model — from a category-creator's strategic frame down to the wire of an in-house ABM bot. The throughline was **convergent architecture**: four speakers independently drew the *same* reference system — a context store + connectors + agents/skills + a human approval loop — at four maturity levels (solo agency, enterprise product, in-house mid-market build, multiplayer cloud harness). The word of the night, by the host's own admission, was **"harness."** The most useful tension was a real, unscripted disagreement about whether cold outbound has a future. The most quotable through-line: **three separate builders said, on the record, that they never read their own skill files** — they trust the model to self-organize and "just imagine it works."

For a senior GTM/revenue operator, the takeaways are unusually actionable: a one-slide strategy artifact you can run with your exec team tomorrow (Sangram), a literal three-step "build your first AI employee" playbook you can start tonight for ~$20–400/mo (Eric), the enterprise-grade nine-lesson harness blueprint (Nikita/Opal), the internal-vs-external multiplayer thesis (Nimo), and a fully-reconstructed end-to-end ABM agent system with cadence, word budgets, and tool stack (Kenny).

---

## 2. The Thesis

**GTM is being re-platformed onto AI, and the unit of work is shifting from the human rep to the human-supervised agent.** Each speaker attacked a different layer of that shift:

- **Strategy layer (Sangram):** In a world where product is no longer a moat and every company is "in a problem-market-fit," the durable advantage is *clarity* — and clarity is a structured artifact (the 8-question GTM Operating System), owned by the CEO, because "go-to-market *is* the business."
- **Execution layer (Eric, Kenny):** The frontier models are good enough that the bottleneck is no longer intelligence — it's *context + connection*. Whoever feeds the agent their company brain and wires it to where work happens gets a tireless employee. Eric cut his team 50% and sends *more* email; Kenny collapsed a 4–5 hour ABM setup into 10–15 minutes of prompting.
- **Platform layer (Nikita):** Doing this at enterprise scale (1,000 marketers, legal/compliance gates, audit trails) requires treating agents as first-class users with identity, governance, reliability engineering, and org-level context — i.e., a *harness*, not a chatbot.
- **Network layer (Nimo):** The next moat is *external* and *multiplayer*: as outreach/ads/content all flood and decay, **co-creation and network-building replace cold outreach.** Qualify by *influence*, not title.

The honest counter-narrative running underneath all of it: **nobody claimed full autonomy.** Every demo kept a human in the loop — Eric's "meat gates," Nikita's governance volume table, Kenny's Slack AE approvals.

---

## 3. Pre→Post Gap

The pre-event research brief (Notion) covered **4 people**: Sangram Vajre, Nimo Shkedy, Eric Nowoslawski, Jennifer Schwarz. The actual event added **two content presenters** discovered only on the night — both **Insight Partners portfolio companies** slotted in by the venue host:

- **Nikita Bokil (Optimizely / Opal)** — added after; enterprise AI-harness lessons.
- **Kenneth "Kenny" Tsai (CoverForce)** — added after; the in-house ABM bot.
- **Jack (Insight Partners "AI Lab")** — did the venue intro; maps to the brief's "Insight Onsite" job-search target (Success Signal #4).

→ These three have **no Notion People records yet** — create on commit. Two other refinements vs. the spine: Nimo introduced himself on stage as founder of **"Two Hops," a GTM agency specializing in network operations** (the spine had "Impact 11" — Two Hops is what he said on the night; verify which is current). And Sangram's framework on the slide is the **8-question** GTM Operating System (an expansion of the 4-question MOVE book framework — see §6.1).

---

## 4. Speaker / Company Map

| Speaker | Goes by / ASR variants | Role · Company | Talk | Notion record? |
|---|---|---|---|---|
| **Jennifer Schwarz** | "Jennifer," "Schwartz" | MC / co-host, NYC GTM Community | Opening + Q&A moderation | ✅ exists |
| **Nimo Shkedy** | "Nemo" | Founder, NYC GTM Community; founder, **Two Hops** (network-ops GTM agency) | "Multiplayer GTM" — cloud harness (Swan/S1) + external multiplayer | ✅ exists |
| **Jack** | "Jack" | Insight Partners — **AI Lab** (applied-AI advisory team) | 1-min venue intro | ❌ create |
| **Sangram Vajre** | "Sandra," "sangram," "Vaire" | CEO/co-founder, **GTM Partners**; ex-founder Terminus; ex-Pardot | "The GTM Operating System" | ✅ exists |
| **Eric Nowoslawski** | intro'd as "Harry"; "Eric" | Founder, **Growth Engine X** (cold-email agency); early Clay | "Build your first AI employee" | ✅ exists |
| **Nikita Bokil** | "Nikita" | PM on **Opal**, **Optimizely** | "Nine lessons from building Opal" | ❌ create |
| **Kenneth (Kenny) Tsai** | "Kenny," co. "Hubbard Forest" | GTM Engineer / Founding Marketer, **CoverForce** | "The ABM bot, end to end" | ❌ create |

*(Web-verified company/funding detail in §18.)*

---

## 5. Slide Catalog (all 22)

Times = exact capture timestamps from `PXL_…` filenames (= moment slide was on screen).

| # | Time | Slide title / what it showed | Speaker | Framework / numbers |
|---|---|---|---|---|
| 1 | 22:18:48 | **The GTM Operating System** — wheel of 8 questions around a "GTM Operating System™" hub | Sangram | 8 questions: Total Relevant Market · Market Investment Map · Brand & Demand · Pipeline Velocity · Customer Time-to-Value · Customer Expansion · Revenue Operations · Leadership & Management. Footer: "Sangram Vajre · CEO @ GTM Partners." |
| 2 | 22:19:52 | **Same wheel, re-shot** (clean, full-frame) — the 8 plain-English question prompts | Sangram | Q's: *Where can you grow the most? · Which product(s) create the highest customer value? · How will you engage your customer with a differentiated PoV? · Which GTM motions get you to your revenue goal faster? · What's your ROI in the customers' mind? · How else can you upserve your customers? · Which GTM metrics drive your business health? · How do you give your team clarity, alignment, and trust?* |
| 3 | 22:26:11 | **"Focus. Race to $10M. Different category. Same game."** — Terminus-vs-GTM-Partners comparison column (partial frame, "other" column) | Sangram | Services · GTM · 1 WSJ best-selling book · GTM Partners · Roadshow & Roundtable (Exec-focused) · **Thinkific + Swan + Kit + Claude + Super Agent** · 2+ (co-founders) · **$1M → $5M → $10M+** · Lifestyle + Franchise model |
| 4 | 22:43:28 | **Context: Build the Company Brain** (STEP 1 OF 3) | Eric | "Your AI employee is only as good as the knowledge you give it. Collect how your company thinks, sells, operates, and makes decisions." Bullets: SOPs & operating principles · ICP definitions & client context · Campaign examples & sales messaging · Reporting templates & decision rules · Examples of great work. Callout: *"Not a technical person? That's the point… the agent helps you build the system as you go."* "Start with whatever you already have: past emails, Slack exports, meeting transcripts, old SOPs." |
| 5 | 22:46:10 | **Connection: Give It Access to Where Work Happens** (STEP 2 OF 3) — hub-and-spoke | Eric | Center: **Hermes / OpenClaw**. Spokes: Fathom (meetings) · Slack (comms) · CRM (deal data) · Email (outreach) · Obsidian (company) · Codex (skills & code). "Start with read-only. Expand after it earns trust." Warning box: *"Avoid brittle automation first. No live Sheets editing or browser automation in version one."* |
| 6 | 22:47:27 | **The First Workflow to Build** (MEETING → SUGGESTION → APPROVAL) | Eric | 01 New Fathom recording detected · 02 Pull transcript + identify context · 03 Read company brain + relevant skills · 04 Suggest what to do next · 05 Human approves, tweaks, or rejects · 06 Save feedback for future runs. Green callout: example output = follow-up + campaign opportunity flag + score + approval menu. *"If it's right: 'Great. Remember this.' If it's wrong: tweak it."* |
| 7 | 23:03:20 | **Marketing's coordination problem** — 5 stat cards | Nikita | Tool fragmentation **15,500+** marketing tools · Multi-system coordination **12+** disconnected systems/campaign · Multi-turn iteration **10+** rounds to get content right · High-stakes review **4+** teams sign off (creative, legal, product, compliance) · (5th, cut off) **6+** systems… Caption: *"Marketing's challenge is coordination across chaos."* |
| 8 | 23:05:02 | **The Opal platform architecture** — layered stack | Nikita | **Interface** (Chat · Artifacts · Action Cards · Headless [Copilot, Slack]) → **Context · Tools · Skills · Agents** → **Foundation** (Identity · Memory · Governance · Models) → **Built on Optimizely** (Content Management · Experimentation · Personalization · Analytics). |
| 9 | 23:05:31 | **Chat, artifacts & action cards** (THE INTERFACE) | Nikita | Chat = one NL entry point · Artifacts = "every output is a living document to browse, manage, edit" · Action cards = "agent input AND output as interactive cards to take actions in context." Lesson: *"Chat is great but rich UX earns its keep… lifting quality on both ends."* |
| 10 | 23:07:05 | **Knowledge that compounds over time** (COMPONENT 01 · CONTEXT) | Nikita | Three layers: **org-level** (shared: brand, templates, org skills) · **user-level** (personal workspace: campaigns, content, people, decisions) · **agent-level** (per-agent memory, compounding independently). Lesson: *"Org-level context is a big unlock. One admin sets it once; the whole org benefits."* |
| 11 | 23:08:33 | **Connecting across your martech stack** (COMPONENT 02 · TOOLS) | Nikita | Native Optimizely (CMP · CMS · DAM · Experimentation) · Third-party **50+** pre-built (GA4, Salesforce, Marketo, HubSpot, Google…) · Custom tool builder (REST wrapper · Auth templates · Schema UI · Testing). Lesson: *"Quality over quantity. 10 well-integrated tools beat 100 shallow ones."* |
| 12 | 23:10:29 | **Agents vs. skills** (COMPONENT 3 & 4) | Nikita | **Agent** = autonomous entity (reasons w/ LLM · calls tools & reads context · executes multi-step workflows · has lifecycle: starts/runs/completes). **Skill** = reusable capability (structured logic · *no* autonomous loop · stored in context · invoked by agents). *In code: Agent = running service, Skill = library function it calls. On a team: Agent = employee who decides, Skill = the SOP they follow.* Lesson: *"Agents give autonomy; skills give consistency… in practice you want both."* |
| 13 | 23:12:02 | **Quality: Agent Reliability Engineering** (COMPONENT 04 · AGENTS) | Nikita | "The SRE playbook, adapted." Agent SLIs/SLOs (`tool_success ≥ 95%`, `thumbs_down < 10%`) · Automated eval pipeline (`change → run evals` / `pass → deploy` / `fail → block + alert`) · Deep observability (`monitor → detect drift → adjust/retrain → feed back to dev`; full traces, tool-call instrumentation, model+prompt version tracking). Lesson: *"Treat reliability as a software problem. Pair LLM evals with deterministic measures so quality is provable, not vibes."* |
| 14 | 23:13:26 | **Agent Teammates as first-class users** (FOUNDATION · IDENTITY) | Nikita | Human (`alice@company.com`) vs Agent (`seo-analyst@company.com`) — structurally identical (OptiID account & permissions, workspace & audit trail, assignable) — *"but a virtual teammate can never escalate its permissions."* Three deployment types: **Personal** (digital twin, assume-role) · **Team** (digital employee, team-level memory) · **Public** (external-facing, restricted, rate-limited, sandboxed). |
| 15 | 23:14:30 | **Human-in-the-loop, built for scale** (FOUNDATION · GOVERNANCE) | Nikita | Flow: Agent prepares action → Managed pause → Task created in CMP → Human reviews → Resume or stop. **Volume table:** 10/day Slack buttons work fine · 100/day things get missed (Queues & prioritization) · 1,000/day impossible (SLA tracking & escalation) · 10,000/day AI-assisted triage. *"Reactive → proactive… with an Agent Teammate acting on its own, risk concentrates."* Lesson: *"Don't bolt on a separate approval system — extend the work management you already run."* |
| 16 | 23:16:00 | **Nine lessons from building Opal** — 3×3 recap grid | Nikita | 01 Interface (chat is just the doorway) · 02 Context (org context is the big unlock) · 03 Tools (quality over quantity, 10 deep beat 100 shallow) · 04 Skills (composable logic; define once, reuse everywhere) · 05 Agents (balance ease & control) · 06 Agents vs skills (use both together) · 07 Reliability (reliability is engineering) · 08 Identity (make agents real users) · 09 Governance (extend your work management). |
| 17 | 23:36:31 | **External multiplayer** — flow diagram (dark slide) | Nimo | **Network Analysis & Planning Engine** (maps relationships · scores paths · suggests actions) → **NETWORK** (Champions · Creators · Communities · Prospects · Partners) → **COLLABORATIONS** (Content · Testimonials · Webinars · Events · Referrals) → loops back as **"new relationships."** |
| 18 | 23:47:03 | **The system, end to end** (SIGNALS IN · AGENTS IN THE MIDDLE · OUTBOUND OUT) | Kenny | **Signals In:** Gong (call transcripts) · HubSpot (pipeline + replies) · Notion (ICP definitions) · Web signals · LinkedIn. **Agents:** Research · Contact Selection · Copywriting · Routing. **Outbound Out:** Instantly (email sends) · HeyReach (LinkedIn) · Slack (AE approvals) · Gifting/Direct Mail (shipping). **Data Storage:** all points flow into **Supabase**; relevant events (emails sent, signals, meetings) sync back. Footer: "CoverForce · ABM bot · Kenny · May 2026." |
| 19 | 23:48:36 | **Four agents, one job each** (THE AGENTS) | Kenny | **Research Agent** (divisional research, leadership mapping, competitor context; reads Web·Gong·HubSpot·Notion·LinkedIn; writes Company Report·Contact Report·Triggers). **Contact Selection Agent** (buying-committee scoring on full hierarchy; *reduces a thousand-plus contacts to the ranked twelve worth engaging*; reads Company/Contact Report·HubSpot·Notion; writes Supabase·Account Brief). **Sequence Agent** (persona-aware copy, proof-point rotation, **under 50 words**; one playbook, 7-step LinkedIn + Email cadence + Gift cadence). **Routing Agent** (who sends & which channel; AE owns the thread; **CEO-to-CEO overrides through Cyrus** [= Cyrus Karai, CoverForce's CEO/co-founder — see §18]; email vs LinkedIn by persona; writes HeyReach·Instantly·**n8n**·HubSpot). Footer "04/14." |
| 20 | 23:49:53 | **Account context, then the contact** (RESEARCH AGENT) | Kenny | **Account-level brief — refreshed weekly:** recent news (last 90 days) · financial statements (10-Ks/10-Qs/earnings, strategy pulled from MD&A) · tech initiatives & major projects · key hires · events & conferences · partnerships · + internal (Gong every prior transcript · HubSpot full history · Notion battlecards/ICP). **"The Online Stalker" — per-contact, refreshed biweekly/continuously:** connections (do we know anyone?) · LinkedIn activity · events attending · direct quotes · news mentions. *"Every email opens with something specific and recent — not a templated hook. Triggers fire the moment a contact does something worth reacting to."* Footer "05/14." |
| 21 | 23:53:00 | **Seven touches. Ten for the high-priority list.** (ZOOM IN · SEQUENCE AGENT) | Kenny | **The cadence: 10 touches · ~22 days** (4 email · 3 LinkedIn · 3 gift). Day 1 Email·Intro (signal becomes the hook) → Day 3 LinkedIn·Connect (short note, no pitch) → Day 6 Email·Value point → Day 8 Gift (high-priority only) → Day 9 LinkedIn·Engage (react to recent post) → Day 12 Email·Proof point (logo/case study) → Day 14 Gift Follow-Up → Day 16 LinkedIn·Direct ask (suggest a 20-min call) → Day 20 Gift Follow-Up → Day 22 Email·Breakup (close the thread cleanly). **Message build (composed live), per-contact/per-touch:** 01 Buyer type (Economic/Technical/Champion) → 02 ICP segment (Brokerage/Wholesaler/InsurTech/PEO) → 03 Pull the angle from the messaging-strategies playbook for that buyer × ICP → 04 Signal as hook (first line cites a concrete recent signal). **< 50 words · 1 markdown playbook · zero templates reused.** Footer "07/14." |
| 22 | 23:57:30 | **Tools Used** | Kenny | Claude · Gong · Clay · Instantly · HeyReach · Slack · Supabase · Render · HubSpot. (Left rail: BRAIN · WHO · WHY · WHAT · HOW.) Footer "10/14." |

*Slide-deck pagination note: Kenny's footers ("04/14," "07/14," "10/14") show his deck had ~14 slides; only ~5 were captured. The visible numbers tell us the captures are non-contiguous.*

---

## 6. Segment Deep-Dives — the centerpiece

### 6.1 Sangram Vajre (GTM Partners) — "The GTM Operating System"

**The arc.** Sangram framed the whole night with a then-vs-now comparison: the $100M+ playbook he ran a decade ago at Terminus vs. the $10M lifestyle business he's bootstrapped at GTM Partners over the last five years. His credibility stack: ran marketing at **Pardot** → acquired by ExactTarget (~$100M) → acquired by Salesforce ($2.7B); co-founded **Terminus** (2014), the company that *created the account-based-marketing category* by being first to advertise *to accounts* rather than leads (e.g., "target all the executives at Home Depot"); author of **MOVE** (2021 WSJ bestseller; Geoffrey Moore of *Crossing the Chasm* endorsed it — Sangram recounted the line *"If I were to write Crossing the Chasm again, I would have written Move"*; 🟡 exact endorsement text is widely repeated but not primary-source confirmed — attribute as "as Sangram recounted" in public content).

**The framework — the 8-question GTM Operating System.** His central claim: companies that win have *incredible clarity around eight questions* — they are "not necessarily the best at it" (he noted Salesforce's CRM/data was "crap" and Pardot's nurture was "bad"), but they are crystal clear on the OS. The eight (slide 1–2, the wheel):

1. **Total Relevant Market** — *Where can you grow the most?* (the ICP question; "the #1 reason companies fail" is talking about a broader ICP than they should)
2. **Market Investment Map** — *Which product(s) create the highest customer value?* (find the wedge; "don't make it complex, make it simple")
3. **Brand & Demand** — *How will you engage your customer with a differentiated PoV?* ("if your website looks the same as your competitor's, you don't have a point of view")
4. **Pipeline Velocity** — *Which GTM motions get you to your revenue goal faster?*
5. **Customer Time-to-Value** — *What's your ROI in the customers' mind?*
6. **Customer Expansion** — *How else can you upserve your customers?*
7. **Revenue Operations** — *Which GTM metrics drive your business health?*
8. **Leadership & Management** — *How do you give your team clarity, alignment, and trust?*

> **Relationship to MOVE (web-verified — two *distinct* frameworks, not one expanded into the other):** **MOVE = 4 questions** — **M**arket, **O**perations, **V**elocity, **E**xpansion (who/what/when/where), applied across three maturity stages (Ideation→problem-market fit, Transition→product-market fit, Execution→platform-market fit). The **GTM Operating System = 8 pillars** (the wheel on stage; the expanded GTM Partners framework that notably adds Customer Time-to-Value and Customer Expansion — stages classic funnels miss). Don't conflate them in public content. The wheel is "your entire go-to-market on one slide." (See §18 for sources.)

**The mechanism — clarity, not certainty.** The single most important idea, in response to "what tactical things did you do to land on the *right* answer?": *"There is no right answer to any of these questions… It has nothing to do with being right. There is no certainty except taxes and death. What this gives you is clarity."* The artifact's job is to force a **healthy debate** across the exec team. His research stat: **78% of GTM leaders said "if I know what we're doing and why, we will hit our revenue goals"** — yet most execs lack that clarity. The action item he gave the room: *print the wheel, fill it out with your exec team, debate it.* "You will get better results with a team behind a non-perfect answer than a perfect answer nobody's behind."

**The worked examples.**
- **Terminus (slide, his read-out):** Grow most = demand gen. Highest-value product = advertising (the wedge — "close 25–50 deals a month because it was the easiest to sell"). Differentiation = a *differentiated PoV* built via the **FlipMyFunnel** community (100k+ signups → landed in the Gartner Magic Quadrant *because of* the community, not the product). Fastest growth motion = events. ROI = account-based ("the new novel idea"). Upserve = **acquisition over building** ("in 8 years we acquired 5 companies" — e.g., bought a small chat company instead of building chat; valuation rose each time). Metrics = ARR/GRR. Alignment = a weekly ritual called **"Show Me the Money"** — *"we never started with leads, we only started with customers"* (study the 10–30 customers' journeys, not the thousands of leads).
- **GTM Partners (slide 3 comparison):** 2021, bootstrapped, downmarket, advisory/services, *MOVE* book, community, **roadshows + roundtables** (exec-focused, not big events), tech stack **Thinkific + Swan + Kit + Claude + Super Agent**, 2 co-founders (Sangram + Bryan Brown), "lifestyle + franchise model," **$1M → $5M → $10M+** over five years. Clients run through the same 8 questions: he named **Henry Schuck (ZoomInfo CEO)** and **Yamini Rangan (HubSpot CEO)**. *[VERIFY name spellings.]*

**The two big strategic claims (worth internalizing):**
1. **"Go-to-market is the business."** Via Brian Halligan (HubSpot co-founder), who asked Sangram *who owns GTM?* The room shouted CEO / founders / RevOps / everyone — and "if everyone owns it, no one owns it." The consistent answer from every CEO/venture-MD they interviewed: **the CEO owns GTM** — because the marketing-vs-sales spend decision, the build-vs-acquire decision, and the EMEA-vs-NA decision are all GTM decisions and all CEO decisions. *"Anything that drives business is go-to-market."*
2. **The metric has moved from ARR/GRR to NRR + revenue per employee.** Ten years ago: ~$300–400k revenue per $100k spend. Today, at CEO roundtables, the bar is **~$1M revenue per employee** — because the expectation is now that executives are *operators*, not strategy-deck-makers. *"Most CEOs are tired of hiring an exec who hands them a strategy deck and asks for $1M of tooling and 5 people."*

**The human note (his deliberate "human in the loop").** Building Terminus he "almost got divorced"; the GTM Partners era is built around clarity on faith, marriage, and roots — and the practical advice: *"You and AI is not going to be your best friend… find a great co-founder."* (His kids ran the AV — son on video, was 5 during Terminus, now 15.)

---

### 6.2 Eric Nowoslawski (Growth Engine X) — "Build your first AI employee"

**Who he is / why listen.** Runs **Growth Engine X**, a cold-email/outbound agency; was an early employee at **Clay** "when they had ten employees." The two proof points he opened with: (1) for one enterprise client he runs **150 auto-research campaigns at once**, sending **100,000 cold emails/day**, AI auto-researching, killing the losers, feeding the winners; (2) *"I accidentally cut my team by 50%, and we're sending more emails, because I made an AI employee."* He has **7 employees**; peers at his revenue band have ~30. His agents are named **Dale** (Carnegie) and **Milton** (Friedman) — "naming them is the most important thing."

**The diagnosis.** The mistake people make: *"This is groundbreaking tech, Anthropic is a trillion-dollar company, I'll let them figure it out."* But you'd never hand a *human* hire one instruction and expect magic. **AI is a hire: front-load the training, and it never stops working, never takes time off, never leaves for a competitor.** And the models (as of late last year) are already smart enough — *"if they're not doing what you want, that's your fault. Your business is not that complicated."*

**The 3-step framework: Context → Connection → Creation.**

**STEP 1 — Context: Build the Company Brain (do it tomorrow).**
- The model is only as good as the knowledge you give it: SOPs/operating principles, ICP definitions & client context, campaign examples & sales messaging, reporting templates & decision rules, examples of great work.
- *Mechanism:* give it access to your richest system of record (Eric used **Fathom** call recordings — "three years of everything I've said" — plus **Slack**), then literally prompt: *"Make a company brain for me in markdown files"* (or in **Obsidian**, free/open-source). **No organizational scheme needed** — "the models have a 1M-token context window; the equivalent in written word is the Bible. If you have more context than the Bible, great. Most of you don't." Let it organize itself.
- Then set a **daily scheduled task**: every day, pull new data from your recorders/Slack/CRM/email and update the brain.

**STEP 2 — Connection: Give it access to where work happens (do it tomorrow).**
- The pain: the "days-before-password-managers" scramble for API keys. His 15-minute fix: everyone opens **Chrome history (last 30 days)**, pastes every URL into Claude/ChatGPT, prompts *"dedupe these and give me a list of all the tools I use,"* then you generate API keys for the ones that matter (ClickUp, Instantly, Clay…).
- *Architecture (slide 5):* hub = **Hermes / OpenClaw** (the harness); spokes = Fathom, Slack, CRM, Email, Obsidian, Codex. **Start read-only; expand after it earns trust. Avoid brittle automation first — no live Sheets editing or browser automation in v1.**

**STEP 3 — Creation: the improvement loop (this is where the work is).**
- The loop (slide 6): **01** new Fathom recording detected → **02** pull transcript + identify context → **03** read company brain + relevant skills → **04** suggest what to do next → **05** human approves/tweaks/rejects → **06** save feedback for future runs.
- *Mechanism:* his agents run on a schedule synced to his 30-min meeting blocks (9:35, 10:05, 10:35…). Each run produces an action-item list **plus the steps it would take**. He reviews: *"Great, execute that"* or *"here's more context, refine and remember this for next time."* "It'll take 3× the effort to train — but once trained, it's locked in." *"You are a $20 Codex plan away from changing your life."*

**The harness/tooling stance.** OpenClaw vs Hermes are "interchangeable competing products"; he leans **Hermes** because *"it writes a skill immediately when you say 'you did it right,' and it never disconnects."* For most of the room he recommends **starting with Codex first** (easiest to get going, can control desktop/browser), then have Codex install Hermes. He runs the whole thing on **3 wiped gaming computers he owns** (not the cloud).

**Security (his explicit disclaimer: "I am not a security expert").** He routes everything through **trigger.dev** so *"I've never actually given an API key to an agent"* — the harness calls trigger.dev, which holds the keys.

**Copywriting — the meta-skill stack.** His philosophy: *"I want to send the same message I would send if I'd manually researched somebody's company and them personally for 10 minutes."* Implementation: a **meta-skill** that controls copywriting, calling sub-skills in order — (1) a skill built on the **Josh Braun** framework (*"I stole his course and put it into a skill"*), (2) the customer-approved custom variables from onboarding, (3) an **adversarial skill** that says *"pretend this is the worst idea in the world and find every problem."* The adversarial step is his marquee tip: *"AI gets a bit sycophantic and just goes 'you're the best guy ever, how are you not a trillionaire?'"* — the adversarial pass kills that.

**The honest limits ("meat gates").** He has **never sent agent-written copy straight to a customer** — copywriting always has a human gate. What *is* fully nailed: **list-building** ("just filters + rechecking filters," e.g., he built "every financial advisor in the US" in a Google Sheet on demand) and meeting→action-item extraction ("an easy task for 5.5 at this point"). He won't trust an agent to run a sales call. Cost: **$400/mo** on the agents (Claude Code Max + Codex Max plans); **~$15k/mo** total AI spend across all 60 customers (writing all the cold email).

**The recurring tell.** Asked if he reads his skill files: *"I've never read a skill file."* When he wants to review one, he prompts *"create an HTML mockup and explain it to me like I'm five, with visuals and animations."*

---

### 6.3 Nikita Bokil (Optimizely) — "Nine lessons from building Opal"

**Context.** Optimizely is ~**$400M ARR**, "a little over two decades old," re-platformed its enterprise marketing software for the LLM era. **Opal** is its purpose-built **AI agent harness for marketers**. Nikita's nine lessons are the distilled output of "the past two years" building a truly enterprise-ready harness — the most architecturally complete blueprint of the night, and the one Nimo explicitly framed as "the next generation."

**Why marketing is hard for agents (slide 7).** Unlike engineering (low stakes — ship behind a feature flag, easy rollback, 1–2 reviewers), marketing is **high-stakes and coordination-heavy**: everything shipped represents the brand, goes through legal/compliance/product sign-off, spans many systems. The numbers: **15,500+** marketing tools · **12+** disconnected systems per campaign · **10+** rounds to get content right · **4+** teams sign off. Plus the target keeps moving (SEO → AEO → GEO — optimizing for AI overviews). *"Marketing's challenge is coordination across chaos."*

**The architecture (slide 8) and the nine lessons (the spine of the talk):**

1. **Interface — "chat is just the doorway."** Chat is the NL entry point, but *"you don't want to just look at blobs of text."* So Opal adds **Artifacts** (every output is a living, browsable/editable document — built in-house via a **custom MIME-type renderer**: image/PowerPoint/doc/markdown/code each render natively; plus a unified Artifacts tab) and **Action Cards** (interactive widgets that both *display* rich output and *structure the input* — forms/clarifications that guide the LLM to a better query). Lesson: *rich UX lifts quality on both ends.* **Action cards are open-sourced** (their own protocol + SDK), designed to render identically across Slack Block Kit / Microsoft Adaptive Cards / OpenAI MCP apps — i.e., built for **multiplayer** (Opal used inside Copilot, Slack, Notion, etc.).

2. **Context — "org context is the big unlock."** Three layers: **org** (brand, tone, writing style, allowed terms — *one admin sets it once, the whole org benefits from day one*), **user** (personal workspace), **agent** (per-agent memory that compounds independently). The onboarding ritual for a new enterprise customer: their team goes in and captures the customer's *most-shared organizational context* first. *"Context is king, context is queen."*

3. **Tools — "quality over quantity, 10 deep beat 100 shallow."** Native Optimizely (first-class), 50+ third-party pre-built (GA4, Salesforce, Marketo, HubSpot via remote MCP), plus a custom tool builder. **The killer story:** their own CMO asked the raw Salesforce connection for "data on our top 20 golden accounts last month" and it failed — *"it didn't know what to pull."* The fix wasn't a better connector; they **wrote a skill** as a translation layer teaching the LLM what *"golden accounts"* and specific fields mean *in their org's taxonomy*. The lesson generalizes: an MCP connector is table stakes; the value is the org-specific skill on top of the raw tool call.

4. **Skills — "composable logic; define once, reuse everywhere."** (paired with Agents)

5. **Agents — "balance ease and control."** Assisted builder for the first draft; control levers for advanced cases.

6. **Agents vs Skills — "use both, together"** (slide 12, the cleanest definition of the night). **Agent** = autonomous entity with its own reasoning loop, calls tools/reads context, executes multi-step workflows, has a lifecycle, *can self-correct*, and **you attach evals to it.** **Skill** = a static list of structured instructions, no loop of its own, stored in context, invoked by agents. The analogies: *In code — Agent = a running service, Skill = a library function it calls. On a team — Agent = an employee who decides, Skill = the SOP they follow.* (e.g. agent = "SEO Content Analyzer monitors GA4 and acts"; skill = `brand_voice_validator` any agent can call.)

7. **Reliability — "reliability is engineering"** (slide 13, the most-undervalued lesson). The industry over-indexes on LLM-as-judge evals (good for non-determinism) but ignores the *deterministic* SRE playbook. Opal applies both: **Agent SLIs/SLOs** (`tool_success ≥ 95%`, `thumbs_down < 10%`), an **automated eval pipeline** (golden datasets catch drift from platform/external changes; `change → run evals → pass → deploy / fail → block + alert`), and **deep observability** (full conversation traces, tool-call instrumentation, model+prompt version tracking, anomaly detection on tool-call order). Lesson: *quality should be provable, not vibes.*

8. **Identity — "make agents real users"** (slide 14). Agents are provisioned exactly like humans: their own email, OptiID account, roles/permissions (full RBAC), workspace, and audit trail — **but a teammate can never escalate its own permissions.** Three deployment types: **Personal** (digital twin, assume-role for one user), **Team** (digital employee, team-level memory), **Public** (external-facing, restricted, rate-limited, sandboxed). This is what makes a 1,000-marketer financial-services rollout auditable.

9. **Governance — "extend your work management"** (slide 15). As agents go from **reactive** (triggered) to **proactive** (acting on their own), *"risk concentrates,"* so human-in-the-loop scales by **volume tier**: 10/day → Slack buttons fine · 100/day → queues & prioritization (things get missed) · 1,000/day → SLA tracking & escalation (Slack impossible) · 10,000/day → AI-assisted triage. Lesson: *don't bolt on a separate approval flow — extend the work-management system you already run (CMP, or the enterprise equivalent: Jira/ServiceNow).*

---

### 6.4 Nimo Shkedy (NYC GTM Community / Two Hops · Swan/S1) — "Multiplayer GTM"

**The frame.** Nimo's thesis is that GTM-with-AI is currently a **single-player** activity (everyone hacking alone in Claude Code/Codex) and the frontier is **multiplayer** — both *internal* (your BDRs, AEs, marketing, leadership working in shared AI systems) and *external* (partners, influencers, communities). He polled the room: only ~2 people had their AI systems connected to teammates'. The internal problem: siloed work means *"you're not utilizing the whole brain"* — BDRs build campaigns disconnected from marketing's battlecards; leadership builds things BDRs never use.

**Internal multiplayer — why Claude Code doesn't generalize, and what a "harness" is.** He used Nikita's Opal as the exemplar of "the next generation," then defined the night's keyword: *"the word I almost asked all the speakers not to say, but everybody said: **harnesses.**"* A harness = a way to use AI with tools, shared resources, shared skills, shared context. **Claude Code is a harness too — but it lives on your PC**: you can't share it (teammates aren't technical / it's personal / they'll mess it up), it's complicated, and if your computer reboots it's gone. The new generation does *what Claude Code does, but in the cloud, for the whole team.* Why not just use Clay? *"Clay is basically an Excel spreadsheet everyone can use — but if a BDR makes a mistake, everyone suffers"* (said as a self-described NYC Clay World Cup competitor — *[VERIFY: "NYC Clay World Cup"]*).

**The live demo — Swan (the sponsor).** Swan ("AI GTM Engineer: From Prompt to Pipeline") was the event sponsor (20% off via QR). **Note (web-verified):** Nimo *uses and endorses* Swan but did **not** found it — Swan was founded by Amos Bar-Joseph, Niv Oppenhaim, and Ido Goldberg ($6M led by Link Ventures). The "S1" label he used is unverified shorthand; cite the product as "Swan." He demoed a company instance called **Copperhelm** *[VERIFY spelling]*. He walked the same three pillars:
- **Shared resources:** the 3 founders/senders, mailboxes, CRM, Slack — all connected.
- **Shared skills:** e.g., a **reply-classification** skill he built *by prompting, not by writing a skill file* (*"Eric said he never reads skill files. I never do either — I didn't create this. I just prompted Swan to classify responses"*). The key property: when he edits the skill, **every sender/teammate gets the same update from one place.** Live, he asked it to classify "Amandeep's response" and surface common response classifications.
- **Enrichment + playbooks:** pick a playbook → the whole team is on it → it pulls from HubSpot → builds sequences. *"Taking everything Claude Code does on your computer and putting it in the cloud for your whole team."*

**External multiplayer — the real point of view (slide 17).** This is where his thesis lands and where he openly disagrees with the industrialized-outbound talks: **"Co-creation is going to replace cold outreach."** As outreach floods, ads go blind, and content saturates, the differentiator becomes **collaborations**. The reframe of qualification: *not "who is a good fit," but "who has influence over the people I want to sell to."* You qualify by **influence, not title or company.**

**The mechanism (the loop he built that morning):**
1. **Quantify influence** — deep network research (AI-assisted): for each target/influencer/micro-influencer, capture total posts, avg reactions/post, topics.
2. **Two degrees out** — phase 2 looks at *who comments on and is connected to* those people (*"your ICP's commenters' commenters"*). The goal: find the 5 people connected to your target who are far easier to reach and can introduce you. Sometimes the collaboration isn't even on LinkedIn (event organizers, co-authors).
3. **Network Analysis & Planning Engine** (slide) → maps relationships, scores paths, suggests actions → categorize the **Network** (Champions/Creators/Communities/Prospects/Partners) → drive **Collaborations** (Content/Testimonials/Webinars/Events/Referrals) → each collaboration spawns **new relationships** that feed back into the engine. He showed a management system built for a client, **Knock AI** *[VERIFY spelling]*, that picks thought leaders to collaborate with and suggests the next action/email/collaboration per person. Closing PoV (a deliberate echo of Sangram): *"That's my point of view — co-creation, collaboration, network-building is going to replace cold outreach and most of the content. Relationships compound over time."*

---

### 6.5 Kenneth "Kenny" Tsai (CoverForce) — "The ABM bot, end to end"

**The setup.** Kenny is Head of Marketing at **CoverForce** (insurance-tech, Insight portfolio) and a self-described "GTM engineer" — *"I'm pretty lazy, so I automate as much repeated work as possible."* CoverForce sells to **billion-dollar insurance brokers and wholesalers in the US** — a tiny TAM where each target may have ~100,000 employees and ~10,000 VP-level titles. The pain he set out to kill: the manual, hit-or-miss LinkedIn research AEs do to find the right ~12 contacts inside a giant org. The headline result: an ABM setup that **took 4–5 hours now takes 10–15 minutes of prompting per company.** This was the most complete *implementation* of the night — the working version of the architecture everyone else described.

**The marquee example — Aon (~60,000 employees, one of the largest US brokers).** Filtering by seniority in Clay/Apollo/"Sigma" *[VERIFY: likely "ZoomInfo" or a tool name]* yields ~15,000 contacts → useless for a BDR (abysmal conversion). VP+ only ≈ 3,000. Large enterprises also have many acquired subsidiaries, so you must map who leads each subsidiary team to reach the parent. The bot narrows **~60,000 → ranked 12 top contacts, "through a click of a button."**

**The system, end to end (slide 18).**
- **Signals In (what the bot reads):** Gong call transcripts · HubSpot pipeline + replies · Notion ICP definitions · Web signals (financial/company scraping) · LinkedIn (job signals, tenure).
- **Data spine:** everything flows into **Supabase** (a marketing DB he built — deliberately *separate* from HubSpot so he doesn't pollute the CRM with test/garbage data or bother RevOps; promotes winners back to HubSpot once proven). Each company = one row of data points.
- **Agents (the middle):** four — Research, Contact Selection, Sequence, Routing (he later calls the orchestrator a 5th "brain," the **ABM bot**).
- **Outbound Out (where it lands):** **Instantly** (email) · **HeyReach** (LinkedIn) · **Slack** (AE approvals) · **Gifting/Direct Mail** (a partner).

**Four agents, one job each (slides 19–21):**

1. **Research Agent** — *why* to target them. Divisional research, leadership mapping, competitor context; builds the **account brief everything else runs from.** Reads Web·Gong·HubSpot·Notion·LinkedIn; writes Company Report·Contact Report·Triggers. Two artifacts (slide 20):
   - **Account-level brief (refreshed weekly):** recent news (90 days), **financial statements** (10-Ks/10-Qs/earnings — "strategy pulled from the MD&A"; his favorite signal — "every CEO talks about what projects they're working on"), tech initiatives, key hires, events/conferences (where are they sponsoring/speaking — "make sure our team is there"), partnerships; + internal (every prior Gong transcript, full HubSpot history, Notion battlecards/ICP).
   - **"The Online Stalker" (per contact, refreshed biweekly/continuously):** *the best trigger is "do we know anybody connected?"* — scrape followers/connections, track who they comment on and interact with, events attending, direct quotes (podcasts/panels), news mentions. *"Triggers fire the moment a contact does something worth reacting to."* This connector-relationship play has **"very high conversion rates to meetings."**

2. **Contact Selection Agent** — *who* to target. Buying-committee scoring on the full hierarchy; **reduces 1,000+ contacts to the ranked 12.** Mechanism: scrape each LinkedIn work history for line-of-business keywords (someone titled just "VP" may actually run workers' comp), then **persona tagging** + **ICP scoring** (trained on which job titles converted in past HubSpot meetings) + **signal triggers** (recent website visit, attended an event you spoke at).

3. **Sequence Agent** — *what* to send. Persona-aware copy, proof-point rotation, **< 50 words**, **one markdown playbook**, **zero templates reused.** Cadence (slide 21): **10 touches over ~22 days** (4 email · 3 LinkedIn · 3 gift), Day 1 Intro → Day 22 Breakup; **7 touches for normal accounts, 10 for the high-priority list** (the extra 3 are the gifts). Message build composed live per contact/per touch: **Buyer type** (Economic/Technical/Champion) × **ICP segment** (Brokerage/Wholesaler/InsurTech/PEO) → pull the angle from the **messaging-strategies playbook in Notion** → **signal as the hook** (first line cites a concrete recent signal). Reads Account Brief + Triggers + AE input.

4. **Routing Agent** — *how* it's sent. Decides who sends and on which channel; **AE owns the thread; CEO-to-CEO overrides route through Cyrus** — i.e., **Cyrus Karai, CoverForce's CEO/co-founder** (web-verified; the highest-value outreach is sent founder-to-founder); email vs LinkedIn by persona. Automates the upload to HeyReach/Instantly/**n8n**/HubSpot so AEs don't touch lists.

**The human-in-the-loop + anti-spam discipline.** AEs control the bot through **Slack**: **Approve** the per-company sequence (he doesn't expect AEs to read every email) · **Pause** (90-day hold) · **Edit** (prompt the ABM bot to change copy or remove people). Two hard-won operational rules: **staggered movement** (target ~4 contacts/day per account, then a ~1-week "grieving period" before the next batch — *"don't bombard a company; people talk, it lowers your reputation"*) and **gift-gating** (logistics: never let a gift arrive before the email lands). The improvement loop is currently **manual/weekly**: opens, replies, and dead silence are all signals fed back into the copywriting agent so it learns what performs.

**Build & ops reality.** Built entirely in **Claude Code** — *"we're just connecting a bunch of APIs and it orchestrates from this lovely little API… I also don't ever look at the skills. I don't know what it's doing, but I just imagine it works."* (The third "never read the skills" tell of the night.) Hosting: started on **Render** (a passion project — *"I didn't want to ask my engineering team for GitHub access yet"*), so the bot runs 24/7 for AEs even when his laptop is off; now externalized to AEs and moving into **GitHub** with proper engineering procedures. The playbook is "just an MD file for the orchestrator." Tools (slide 22): Claude · Gong · Clay · Instantly · HeyReach · Slack · Supabase · Render · HubSpot (+ n8n per slide 19).

---

## 7. Full Quote Bank (per speaker; [VERIFY] where flagged)

**Sangram Vajre**
- *"The CEO owns go-to-market, and therefore go-to-market is the business. Anything that drives business is go-to-market."*
- *"There is no right answer to any of these questions… There is no certainty except taxes and death. What this gives you is clarity."*
- *"Seventy-eight percent of [GTM] leaders said, 'If I know what we are doing and why, we will hit our revenue goals.'"*
- *"This is literally building your entire go-to-market on one slide."*
- *"Twenty fourteen, product was the moat. Anybody can build and replicate a product now."*
- *"We never started with leads. We only started with customers."* (the "Show Me the Money" weekly ritual)
- *"You and AI is not going to be your best friend… at some point you're going to need a human. Find a great co-founder."*
- *"Every company is in a problem-market-fit."* [paraphrase of his phrasing]
- On Geoffrey Moore's endorsement of *MOVE*: *"If I were to write Crossing the Chasm again, I would have written Move."* (Moore's words, quoted by Sangram)

**Eric Nowoslawski**
- *"I accidentally cut my team by fifty percent, and we're sending more emails, because I made an AI employee."*
- *"You are a twenty-dollar Codex plan away from changing your life."*
- *"The models have a one-million-token context window. The equivalent in written word is the Bible. If you have more context than the Bible, great — most of you don't."*
- *"If they're not doing what you want them to do, that's your fault. Your business is not that complicated."*
- *"I've never read a skill file."*
- *"Whenever you make a skill, try to make an adversarial skill… 'pretend this is the worst idea in the world and find every problem.' Because AI gets a bit sycophantic and just goes, 'You're the best guy ever.'"*
- *"I want to send the same message I would send if I'd manually researched somebody's company and them personally for ten minutes."*
- On the team gap: *"Other people in my revenue band have like thirty employees. We have seven."*
- On limits: *"I've never sent copywriting straight from an agent to a customer… there are still meat gates."*
- *"What William Shakespeare did for the tragedy, [Sangram] did for marketing."*

**Nikita Bokil**
- *"Context is king, context is queen."*
- *"Marketing's challenge is coordination across chaos."*
- *"Chat is great but rich UX earns its keep."*
- *"Org-level context is a big unlock. One admin sets it once; the whole org benefits."*
- *"Quality over quantity. Ten well-integrated tools beat a hundred shallow ones."*
- *"Agents give you autonomy; skills give you consistency… in practice, you want both."*
- *"Treat reliability as a software problem. Pair LLM evals with deterministic measures so quality is provable, not vibes."*
- *"A virtual teammate and a human look the same at the platform level — but a virtual teammate can never escalate its permissions."*
- *"Don't bolt on a separate approval system; extend the work management you already run."*
- On the CMO/golden-accounts story: *"It didn't do a good job… so we wrote a skill to guide the LLM on what 'golden accounts' means in the context of our organization."*

**Nimo Shkedy**
- *"Co-creation is going to replace cold outreach. It's going to replace most of the content… What's going to differentiate you is collaborations."*
- *"I don't qualify by title or company. I qualify by influence — who has influence over the people I want to sell to."*
- *"You need two degrees out… your ICP's commenters' commenters."*
- *"The word I almost asked all the speakers not to say, but everybody said it, is harnesses."*
- *"Claude Code is a harness too — but it lives on your PC. The new generation does what Claude Code does, but in the cloud, for your whole team."*
- *"I just prompted Swan to classify responses… I never read skill files either. I didn't create this."*
- *"Clay is basically an Excel spreadsheet everyone can use — but if a BDR makes a mistake, everyone suffers."* [VERIFY: "NYC Clay World Cup" self-description]

**Kenny Tsai**
- *"I'm pretty lazy, so I try to automate as much repeated work as possible."*
- *"This is all Claude Code… I also don't ever look at the skills. I don't know what it's doing, but I just imagine it works."*
- *"It used to take me four or five hours to set up completely. Now it takes ten, fifteen minutes of prompting per company."*
- *"We narrowed sixty thousand contacts down to twelve, just through a click of a button."*
- On the Online Stalker: *"The best trigger for us is: do we know anybody that's connected?"*
- On anti-spam: *"You don't want to bombard a company… people talk, and it lowers your reputation. So we use staggered movement."*
- *"Financial statements is a great signal — every CEO talks about what projects they're working on."*

**Jack (Insight Partners, AI Lab)** — *"You can think of it as an applied-AI team for Insight internally, and for our portfolio companies."*

---

## 8. Pro-Tips (actionable "if X, do Y")

1. **If your exec team argues in circles about strategy → print Sangram's 8-question wheel and fill it out together.** The artifact's value is forcing a healthy debate; clarity beats a perfect-but-unowned answer.
2. **If you're choosing a North-Star → track NRR + revenue-per-employee, not just ARR/GRR.** The CEO-roundtable bar is now ~$1M/employee.
3. **If you want your first AI employee tonight → do Context + Connection tomorrow, Creation as a weekly habit.** Buy a $20 Codex plan, point it at your call recordings + Slack, prompt "make a company brain in markdown."
4. **If you're scrambling for which tools to connect → have everyone paste 30 days of Chrome history into an LLM and "dedupe into a tool list."** 15 minutes, done.
5. **If agents flatter you → write an adversarial skill** ("this is the worst idea ever — find every flaw") and run it last in your copy chain.
6. **If you're worried about API-key security → route calls through trigger.dev** (or similar) so the agent never holds keys.
7. **If a raw MCP connector gives bad answers → don't swap the connector, write a skill** that translates *your* taxonomy ("golden accounts" = these fields). (Nikita's CMO story.)
8. **If you're deciding agent vs skill → agent when you need an autonomous loop + evals; skill when you need a consistent, reusable SOP.** Usually both.
9. **If you can't prove agent quality → set SLOs (`tool_success ≥ 95%`, `thumbs_down < 10%`) + an eval gate (`fail → block + alert`) + traces.** Reliability is engineering.
10. **If you're scaling approvals → match HITL to volume tier** (Slack ≤ ~10/day; queues at 100; SLA/escalation at 1,000; AI-triage at 10,000) and extend your existing work-management, don't bolt on a new flow.
11. **If outbound is flooding → invest in co-creation/network plays.** Map two degrees out ("commenters' commenters") and qualify by influence.
12. **If you're sequencing → cap email at <50 words, lead every first line with a concrete recent signal, and stagger ~4 contacts/account/day** with a ~1-week gap to protect reputation; gate gifts so they never beat the email.
13. **If you don't want to bother RevOps while testing → build a separate Supabase marketing DB; promote winners into the CRM after they prove out.** (Kenny.)
14. **If your agents must run when your laptop is off → host on Render/cloud, not your local machine.** (Kenny; Eric runs his on owned hardware — pick by your security posture.)

---

## 9. Best Practices / Patterns

- **Context first, always.** Every builder led with "build the company brain / org context." It's the cheapest, highest-leverage move; tools and agents are downstream.
- **Human-in-the-loop survives at every scale.** Eric's meat gates, Nikita's governance table, Kenny's Slack approvals — supervised autonomy, not full autonomy.
- **Start read-only, expand after trust.** (Eric's slide 5; the universal "avoid brittle automation first.")
- **One artifact, debated by the team.** (Sangram's wheel; the principle that alignment > correctness.)
- **Quality over quantity in connectors.** 10 deep > 100 shallow (Nikita); ~12 ranked contacts > 15,000 (Kenny).
- **Signal-as-hook.** Both outbound systems (Eric, Kenny) open every message with a specific recent signal; "zero templates reused."
- **Compounding memory.** Org/user/agent context (Nikita) and "relationships compound over time" (Nimo) — value accrues with use.
- **Treat agents as employees.** Naming (Eric's Dale/Milton), training time (3×), identity/RBAC/audit (Nikita), AE ownership of the thread (Kenny).
- **Reliability as software discipline.** SLOs + eval gates + observability, not vibes (Nikita) — directly mirrors Alex's own build-rigor/measurement layer.

---

## 10. Pitfalls / Anti-Patterns

- **"Anthropic will figure it out."** Treating a frontier model like a finished employee with one instruction → it fails (Eric).
- **Over-organizing the context store.** Wasted effort given 1M-token windows — let the model self-organize (Eric).
- **Brittle automation in v1.** Live Sheets editing / browser automation before read-only trust is established (Eric's warning box).
- **Shipping the raw MCP tool call.** Without an org-taxonomy skill on top, even a HubSpot/Salesforce connector returns garbage (Nikita).
- **"Quality is vibes."** No SLOs, no eval gate, no traces → unprovable, undeployable at enterprise scale (Nikita).
- **Bolting on a separate approval system** instead of extending existing work-management → governance debt (Nikita).
- **Bombarding a target account.** 20 messages to one company tanks your reputation; use staggered movement (Kenny).
- **Gift arrives before the email.** Logistics break the narrative; gate the gift (Kenny).
- **Polluting the CRM with test data.** Use a sandbox DB; promote winners (Kenny).
- **Cross-company performance leakage (open risk).** Kenny was asked how he prevents one client's ICP/gift/sequence learnings from bleeding into another's; honest answer: *"It might be happening — we haven't gotten that feedback yet, we need to check."* (Each company is its own DB row, which mitigates but doesn't fully solve it.)
- **Sycophancy.** Unchecked, the model tells you you're a genius — counter with an adversarial pass (Eric).
- **Sharing your single-player Claude Code setup.** Personal, fragile, dies on reboot, non-technical teammates break it (Nimo) — the reason the harness must move to the cloud.

---

## 11. Hot Takes

- **"Co-creation is going to replace cold outreach."** (Nimo) — and he said it in a room where two other speakers' entire businesses are industrialized cold outbound (100k emails/day). The night's single real disagreement.
- **"Go-to-market is the business; the CEO owns it."** (Sangram) — a direct shot at the "GTM = marketing + sales" framing.
- **"Product is no longer a moat."** (Sangram) — community / PoV / network are the new moats.
- **"I've never read a skill file."** — said independently by **three** builders (Eric, Nimo, Kenny). Trust-the-model-to-self-organize as a genuine, slightly subversive operating norm. *"I just imagine it works."* (Kenny)
- **"Revenue per employee ~$1M is the new bar."** (Sangram) — executives must be operators, not strategy-deck-makers.
- **"Reliability is engineering, not vibes."** (Nikita) — a quiet rebuke to demo-driven AI hype.
- **"Qualify by influence, not title or company."** (Nimo) — inverts decades of firmographic/title-based ICP.
- **"Websites will turn into chatbots."** (Eric, in Q&A) — "the point of the website becomes 'what do you want to know?'"

---

## 12. Substantive Insights (ranked)

1. **The convergent reference architecture.** Eric's Context→Connection→Creation, Nikita's Opal stack, and Kenny's Signals→Agents→Outbound are the *same* system (context store + connectors + agents/skills + human approval loop) at four maturity levels (solo, enterprise product, in-house mid-market, multiplayer cloud). The architecture is now settled; the differentiation is in *context quality* and *governance*.
2. **The bottleneck has moved from model intelligence to context + connection + governance.** Every speaker agreed the models are good enough; the work is feeding them your company brain, wiring them to where work happens, and supervising them safely.
3. **"Harness" is the new category.** A harness = cloud-hosted, multiplayer, shared context/skills/agents + identity + governance. Claude Code is a single-player harness; Opal/Swan are the multiplayer generation. This is the architectural frame Alex's pipeline should adopt vocabulary from.
4. **Strategy clarity is a structured artifact, and alignment beats correctness.** Sangram's wheel + the 78% stat: the ROI of GTM strategy is in the *shared debate*, not the answer.
5. **Org-level context is the enterprise unlock.** One admin sets brand/tone/taxonomy once → the whole org's agents are useful day one (Nikita) — the multiplayer version of Eric's "company brain."
6. **Reliability/eval discipline is the enterprise moat and the maturity tell.** SLOs + eval gates + observability separate a demo from a deployable system (Nikita). Directly validates Alex's own measurement-rigor layer.
7. **Outbound and network plays are converging on "signal-as-hook," but diverging on whether outbound survives.** Both Eric and Kenny lead with recent signals; Nimo bets the whole motion gets replaced by co-creation. The synthesis: signals power *both* the last era of outbound and the first era of network plays.
8. **Human-in-the-loop is the honest counter-narrative to "agents replace teams."** Nobody claimed full autonomy; the realistic near-term is 50% headcount on supervised agents (Eric), not zero.
9. **Identity/RBAC for agents is the unsung requirement.** Treating agents as provisioned users (own email, permissions, audit, can't self-escalate) is what makes regulated-industry rollouts possible (Nikita).
10. **The economics are striking and citable.** 50% team cut + more output (Eric); 4–5 hrs → 10–15 min (Kenny); $1M→$10M bootstrapped (Sangram); $400/mo agent cost vs $15k/mo total AI spend (Eric).

---

## 13. Anecdotes

- **"Think big."** Sangram's boss said it after Pardot→ExactTarget; said it again after ExactTarget→Salesforce, then: *"No, you don't get it"* — meaning it's not budget or headcount, it's how big you can *think* because you write the rules.
- **The "almost got divorced" admission.** Sangram building Terminus; now builds GTM Partners around clarity on marriage/faith/roots. His kids (12 & 15) ran the AV.
- **Dale & Milton.** Eric's agents, named for Dale Carnegie and Milton Friedman. ("Naming them is the most important thing.")
- **Judith Love Cohen.** Eric's tangent — the NASA engineer who solved an Apollo problem on the way to the hospital and then gave birth to Jack Black.
- **The 3 wiped gaming computers.** Eric runs his entire AI-employee stack on owned hardware, not the cloud.
- **The CMO and the golden accounts.** Optimizely's own CMO broke their Salesforce connector asking for "top 20 golden accounts" — the failure that birthed the org-taxonomy-skill lesson (Nikita).
- **"I built this this morning."** Nimo on his network-influence research system — and his reply-classification skill built live by prompting, not coding.
- **The lazy-marketer origin story.** Kenny built the entire ABM bot as a passion project because *"I just didn't want to upload lists anymore"* — hosted on Render to avoid asking eng for GitHub access.
- **Aon, 60,000 → 12.** The marquee narrowing: a 60k-person broker down to 12 ranked contacts via one button.
- **Insight's "AI Lab" naming.** Jack: *"I did not name it. I was given the name."*
- **The first three masterclasses were at Clay's HQ;** #5 is the fifth month in a row, growing each time (Jennifer/Nimo).

---

## 14. Concept Glossary

- **GTM Operating System (8 questions)** — Sangram/GTM Partners' one-slide strategy artifact (the wheel). Expansion of the 4-question MOVE framework.
- **MOVE** — Sangram's 2021 WSJ-bestselling GTM book (4-question framework); endorsed by Geoffrey Moore.
- **ABM (Account-Based Marketing)** — marketing/selling to whole accounts (and the buying committee) rather than individual leads; category Terminus created.
- **Harness** — the night's keyword: a system to use AI with tools + shared context/skills/agents. Single-player (Claude Code, Codex) vs multiplayer/cloud (Opal, Swan).
- **Company Brain** — a markdown/Obsidian knowledge store of how your company thinks/sells/operates (Eric).
- **Agent vs Skill** — Agent = autonomous reasoning loop, calls tools, has lifecycle, evals attach to it. Skill = static reusable instructions, no loop, invoked by agents. (In code: service vs library function. On a team: employee vs SOP.)
- **Context layers (org/user/agent)** — Nikita's model: shared org context, personal user workspace, per-agent compounding memory.
- **Action Cards / Artifacts** — Opal interface primitives: interactive widgets (input+output) and living editable documents; action cards open-sourced as a cross-platform protocol.
- **Agent Reliability Engineering (ARE)** — SRE playbook for agents: SLIs/SLOs + eval pipeline + observability.
- **Agent Teammate / Identity** — agents as first-class provisioned users (email, RBAC, audit, can't self-escalate); Personal/Team/Public deployment types.
- **AEO / GEO** — Answer Engine / Generative Engine Optimization: optimizing to show up in AI overviews/LLM answers (successor framing to SEO).
- **Meat gate** — Eric's term for a mandatory human checkpoint.
- **Adversarial skill** — a skill that critiques an output as "the worst idea ever" to counter LLM sycophancy.
- **Online Stalker** — Kenny's per-contact monitoring agent (connections, activity, events, quotes, news).
- **Staggered movement** — Kenny's anti-spam rule: ~4 contacts/account/day + ~1-week gap.
- **Two degrees out / commenters' commenters** — Nimo's network-mapping heuristic for finding influence paths.
- **Co-creation** — Nimo's thesis: collaborative content/webinars/referrals with influential network nodes, replacing cold outreach.
- **Revenue per employee** — the new efficiency North-Star (~$1M bar; Sangram).
- **Show Me the Money** — Terminus's weekly ritual of studying closed *customers'* journeys, never leads.
- **trigger.dev** — service Eric routes calls through so agents never hold API keys.

---

## 15. Tools / Companies Mentioned

**Harnesses / orchestration:** Claude Code · Codex (OpenAI) · OpenClaw · Hermes · Nanoclaw (audience rec) · Opal (Optimizely) · Swan / S1 (sponsor) · n8n · trigger.dev · Render
**LLMs/vendors:** Claude / Anthropic · ChatGPT / OpenAI ("Spark" model teased) · "5.5" (model ref)
**GTM data / enrichment:** Clay · Apollo · ZoomInfo · "Sigma [Bill]" [VERIFY tool]
**Outbound / engagement:** Instantly · HeyReach · gifting/direct-mail partner
**Knowledge / meetings:** Fathom · Gong · Obsidian · Notion
**CRM / martech:** HubSpot · Salesforce · Marketo · GA4 · Google · Optimizely (CMP/CMS/DAM/Experimentation)
**Data / infra:** Supabase · ClickUp · Git/GitHub · Thinkific · Kit
**Companies:** GTM Partners · Terminus · Pardot · ExactTarget · Salesforce · Growth Engine X · Optimizely · CoverForce · Aon · Insight Partners (AI Lab) · NYC GTM Community · Two Hops · Knock AI [VERIFY] · Copperhelm (Swan demo instance) · ZoomInfo · HubSpot · Home Depot (example)
**People referenced (not present):** Geoffrey Moore · Brian Halligan · Bryan Brown (+ Lindsay Cordell, Judd Borakove — GTM Partners co-founders, web-verified) · Henry Schuck (ZoomInfo CEO) [VERIFY] · Yamini Rangan (HubSpot CEO) · Josh Braun · Dale Carnegie · Milton Friedman · Judith Love Cohen · Jack Black · **Cyrus Karai** (CoverForce CEO/co-founder — the "Cyrus" in Kenny's routing) · Behram Dinshaw, Kaivan Wadia (CoverForce co-founders) · Amos Bar-Joseph, Niv Oppenhaim, Ido Goldberg (Swan founders)

---

## 16. Stat Bank (every number + source)

| Stat | Source |
|---|---|
| Pardot acquired by ExactTarget ~**$100M** | Sangram |
| ExactTarget acquired by Salesforce **$2.7B** | Sangram |
| Terminus founded **2014**, **3 co-founders**, grew to **300+ employees**, **acquired 5 companies** in 8 yrs, exit to PE | Sangram |
| Terminus revenue ramp: **$1M → $5M → $15M** in first 3 years on **1.5 marketers** | Sangram |
| FlipMyFunnel community: **100,000+** signups | Sangram |
| MOVE readership / GTM OS newsletter: **175,000** readers | Sangram |
| **78%** of GTM leaders: "if I know what/why, we'll hit revenue goals" | Sangram (GTM Partners research) |
| GTM Partners: **2021**, **$1M → $5M → $10M+** in 5 yrs, bootstrapped (Sangram said "2 co-founders" on stage — Sangram + Bryan Brown; firm publicly lists 4: + Lindsay Cordell, Judd Borakove) | Sangram + slide 3 |
| Old efficiency: ~**$300–400k** revenue per **$100k** spend; new bar ~**$1M** revenue/employee | Sangram |
| ~**85–90%** of founders can answer the ICP question; ~**8 of 10** scope ICP too broadly | Sangram |
| Eric: enterprise client = **150** auto-research campaigns, **100,000** cold emails/day | Eric |
| Eric: team cut **50%**; **7 employees** vs peers' ~**30**; **~60 customers** | Eric |
| Eric: generates **200–300 leads/day** for customers | Eric |
| Eric: enterprise client ratio ≈ **70 leads** / 100k emails/day; another got **145 leads** in a day | Eric |
| Eric: agent cost **$400/mo** (Claude Code Max + Codex Max); total AI spend **~$15k/mo** | Eric |
| Context window: **1M tokens ≈ the Bible** in written words | Eric |
| Optimizely: ~**$400M ARR**, ~**2 decades** old | Nikita |
| Marketing coordination: **15,500+** tools · **12+** systems/campaign · **10+** content rounds · **4+** sign-off teams · 6+ (cut off) | Nikita, slide 7 |
| Tools: **50+** third-party pre-built; *"10 deep beat 100 shallow"* | Nikita, slides 11/16 |
| Agent SLOs: **tool_success ≥ 95%**, **thumbs_down < 10%** | Nikita, slide 13 |
| HITL volume tiers: **10 / 100 / 1,000 / 10,000** per day | Nikita, slide 15 |
| Opal lessons distilled over ~**2 years**; **9** lessons | Nikita |
| Nimo poll: only ~**2** attendees had AI systems connected to teammates' | Nimo |
| Network heuristic: **two degrees** out | Nimo |
| CoverForce TAM: **billion-dollar** US brokers/wholesalers; targets up to ~**100,000** employees, ~**10,000** VP titles each | Kenny |
| Aon: ~**60,000** employees → ~**15,000** (seniority filter) → ~**3,000** (VP+) → ranked **12** | Kenny |
| ABM cadence: **10 touches / ~22 days** (4 email · 3 LinkedIn · 3 gift); **7** base, **10** high-priority | Kenny, slide 21 |
| Copy budget: **< 50 words**; **1** markdown playbook; **0** templates reused; ~**4** contacts/account/day; **90-day** pause; **1-week** grieving period | Kenny |
| Setup time: **4–5 hours → 10–15 minutes** per company | Kenny |
| Event: masterclass **#5**, **5** months in a row, ~**100** attendees, **5** speakers; first 3 held at Clay HQ | Jennifer/Nimo |
| Swan sponsor discount: **20%** off | Nimo |

---

## 17. Documentarian Angles (sharp GTM/revenue lens)

1. **"The night four builders drew the same diagram."** The convergent-architecture post: Eric's solo agency, Nikita's enterprise product, Kenny's in-house build, Nimo's cloud harness — one reference architecture (context + connectors + agents/skills + approval loop) at four maturity levels. Carousel: redraw all four as a single comparison (NOT a re-print of any one deck). Thesis: the architecture is settled; the war is over context + governance.
2. **"Co-creation vs. 100,000 emails a day."** The two-thesis synthesis post (pairs cleanly with `pattern-synthesis`): in one room, Kenny/Eric industrialize cold outbound while Nimo declares cold outreach dead. Resolve it: *signals power both — the last era of outbound and the first era of network plays.* Sharp, balanced, earns a POV.
3. **"Three operators told me they never read their own code."** The contrarian single post on "I just imagine it works" — Eric, Nimo, Kenny independently. Is trusting the model to self-organize the new literacy, or accruing invisible debt? (Tie to the cross-company "performance leakage" risk Kenny couldn't fully answer.)
4. **"Reliability is engineering, not vibes."** A craft post off Nikita's ARE slide — SLOs, eval gates, observability for agents — explicitly mapped to how a serious GTM team (or Alex's own measurement layer) should treat agent quality. Differentiates Alex as someone who thinks past the demo.
5. **"Go-to-market is the business."** A leadership/POV post off Sangram's frame + the 8-question wheel + the $1M-revenue-per-employee bar. The artifact-driven-alignment idea ("clarity, not certainty") is highly resonant for a GTM-leadership audience.
6. **"Qualify by influence, not title."** A tactical post off Nimo's two-degrees / commenters'-commenters method — concrete enough to be useful, framed as the network-era successor to firmographic ICP.

---

## 18. Open Loops & Verification Flags + Enrichment Resolutions

### Verification flags (resolve before any public use)
- 🔴 **"Sigma Bill"** (Kenny, slide-tool he contrasted with Clay/Apollo) — almost certainly an ASR garble of **ZoomInfo** or a specific tool; verify before quoting.
- ✅ **"Cyrus" RESOLVED** (Kenny's Routing Agent: "CEO-to-CEO overrides through Cyrus") = **Cyrus Karai, CoverForce's CEO/co-founder** (web-verified). Highest-value outreach is routed founder-to-founder. Not a tool.
- 🔴 **"Knock AI"** (Nimo's network-system client example) — spelling unverified ("Nokai"/"Knock AI" in ASR).
- 🔴 **"Copperhelm"** — Nimo's Swan demo instance name; spelling unverified.
- 🟡 **"NYC Clay World Cup"** (Nimo's self-description) — sounds plausible (Clay runs community competitions) but sanity-check before quoting.
- 🟡 **"Two Hops" vs "Impact 11"** — Nimo said "Two Hops, a GTM agency specializing in network operations" on stage; the spine had "Impact 11." Confirm which is his current entity.
- 🟡 **Henry Schuck (ZoomInfo CEO) / Yamini Rangan (HubSpot CEO)** — Sangram's named clients; verify spellings/titles.
- 🟡 **Jennifer Schwarz vs Schwartz** — brief = Schwarz, ASR = Schwartz; confirm.
- 🟡 **"Harry"** — Jennifer's intro of the cold-email speaker; near-certainly **Eric Nowoslawski** (self-ID via Growth Engine X + Clay). ASR error.
- 🟡 **Slides 13–15 (Nikita: Reliability/Identity/Governance)** — captured but lightly narrated; their detailed content is from the *slides*, not her spoken words — don't attribute spoken quotes to them.
- 🟡 **REVIEW-list low-confidence words** (from the quote-safety doc): "Sigma" @101:06 (the tool above), "Oracle" @26:08 (Sangram said he was "at Oracle" — verify; he's known for Pardot/Salesforce, Oracle is plausible but flagged), "LinkedIn" @103:24, "host"/"base" @117:43/58 (in Kenny's hosting Q&A — resolves to Render/Supabase). Paraphrase these spots if quoting.
- ✅ **Sangram surname = Vajre** (slide footer + brief + book brand). "Vaire" was a photo mis-read.

### Enrichment resolutions (web-verified)
*The web-research pass returned the following (see sources). Items still unconfirmed are marked.*

**Sangram Vajre / GTM Partners (High).** Confirmed: Co-founder & CEO, GTM Partners (data-driven GTM advisory/analyst firm). Co-founded **Terminus** (ABM pioneer; ~$15M in 3 yrs, Deloitte fast-growth). Ran marketing at Pardot (→ ExactTarget → Salesforce). **GTM Partners co-founders are Bryan Brown, Lindsay Cordell, and Judd Borakove** — not just Bryan Brown (the brief's "2 co-founders" is what Sangram said on stage; the firm publicly lists more). Sources: [LinkedIn](https://www.linkedin.com/in/sangramvajre/), [diginomica](https://diginomica.com/go-market-broken-gtm-partners-wants-help-you-fix-your-approach), [Demand Gen Report](https://www.demandgenreport.com/industry-news/why-gtm-must-be-intentional-terminus-co-founder-sangram-vajre-discusses-new-book-move/6970/).
- **FRAMEWORK CORRECTION (important):** **MOVE and the GTM Operating System are two distinct frameworks**, not "MOVE expanded to 8." **MOVE = 4 questions** — **M**arket, **O**perations, **V**elocity, **E**xpansion (who/what/when/where), across three maturity stages (Ideation→problem-market fit, Transition→product-market fit, Execution→platform-market fit). The **GTM OS = 8 pillars** (the expanded GTM Partners framework, which the slide showed; notably adds Customer Time-to-Value and Customer Expansion that classic funnels miss). The GTM OS newsletter has 175K+ subscribers. Sources: [Amazon — MOVE](https://www.amazon.com/MOVE-4-question-Go-Market-Framework/dp/1544523378), [Heinz Marketing summary](https://www.heinzmarketing.com/blog/move-the-4-question-go-to-market-framework-a-summary-of-sections-1-and-2/), [Reachdesk — GTM OS](https://www.reachdesk.com/the-antidote/gtm-partners-and-the-gtm-os). (Body of this brief already states the two-framework distinction in §6.1.) The eight pillar *labels* in §5/§6.1 are transcribed directly from the slide photo (authoritative); the relationship-to-MOVE is now corrected.
- 🟡 **Geoffrey Moore's "I would have written Move" endorsement** is widely repeated but the researcher could **not confirm the exact text from a primary source** — soften to "endorsed MOVE" in public content, or attribute as "as Sangram recounted." Geoffrey Moore authored *Crossing the Chasm* (1991) — **confirmed** ([geoffreyamoore.com](https://geoffreyamoore.com/book/crossing-the-chasm/)).

**Eric Nowoslawski / Growth Engine X (High).** Confirmed: Founder, Growth Engine X (cold-email/outbound agency; one of the first Clay agencies, 300+ customers; LinkedIn handle "outboundphd"). Was **Clay's first marketing contractor when they had ~4 employees** (the brief/his on-stage "~10 employees" is directionally right but ~4 per sources). Now reportedly Clay's largest user by enrichment volume; sends 4M+ emails/month. Active Clay/cold-email educator on LinkedIn + YouTube. Sources: [LinkedIn](https://www.linkedin.com/in/outboundphd/), [Growth Engine X](https://www.growthenginex.com/), [GTM Engineer Substack](https://thegtmengineer.substack.com/p/the-winning-cold-outbound-formula). → The "Harry" intro was indeed an ASR error; confirmed Eric.

**Nikita Bokil / Optimizely / Opal (Medium-High).** Optimizely = leading DXP (CMS, experimentation, commerce, content marketing); formerly **Episerver** (founded 1994), acquired by Insight Partners 2018, acquired Optimizely 2020, rebranded 2021. **$400M ARR confirmed** (reached May 2024; revenue quadrupled in 4 yrs) — [Optimizely press](https://www.optimizely.com/company/press/400M-ARR/). **Opal** = Optimizely's AI orchestration platform for marketers (50+ pre-built no-code agents, drag-drop workflows, trigger-based); initial agents late 2024; full **AEO platform launched June 10, 2026** (Conductor partnership + Agent Visibility Analytics) — [PRNewswire](https://www.prnewswire.com/news-releases/optimizely-launches-full-aeo-platform-to-help-marketers-understand-and-act-on-ai-driven-content-discovery-302795999.html), [Optimizely AI](https://www.optimizely.com/ai/). 🟡 **Name spelling "Nikita Bokil" and her exact PM-on-Opal title were not independently confirmed** from a primary profile — verify against the Luma event page / her LinkedIn before public use. (Note: the event was 2026-06-03; the full AEO launch was 2026-06-10, one week later — her talk previewed it.)

**Nimo Shkedy / NYC GTM Community / Swan (High on community; CORRECTION on Swan).** Confirmed: founder/host of the **NYC GTM+AI Community** (nycgtm.com) — masterclass series for YC founders/GTM leaders, 100+ per event, has hosted at Clay's HQ; Israeli background, YC founder. Sources: [LinkedIn](https://www.linkedin.com/in/nimshkedy/), [Luma](https://luma.com/ixegecee).
- ❗ **CORRECTION — Nimo did NOT found Swan.** **Swan (getswan.com) — "AI GTM Engineer: From Prompt to Pipeline"** — was founded by **Amos Bar-Joseph, Niv Oppenhaim, and Ido Goldberg**; raised **$6M led by Link Ventures**; ~200 customers, run by 3 founders + AI agents. **Nimo is an advocate/affiliate, not a co-founder.** Sources: [getswan.com](https://www.getswan.com/), [Calcalist](https://www.calcalistech.com/ctechnews/article/b1c7ym30011g). On stage Nimo said he *uses* and endorses Swan (the sponsor) — consistent with affiliate, not founder. Cite the sponsor as **"Swan, the AI GTM Engineer."**
- 🔴 **"S1" and "Impact 11" could NOT be verified** — "S1" may be informal shorthand/internal tier; do **not** assert it publicly. ("Two Hops," his network-ops agency, was his on-stage self-description — also unverified externally; confirm with him.)

**Kenneth (Kenny) Tsai / CoverForce (High).** Confirmed: **Kenneth C. Tsai — GTM Engineer & Founding Marketer** at CoverForce (joined as Enterprise AE; "0→1 growth builder"). Use **"GTM Engineer / Founding Marketer,"** not "Head of Marketing," unless the event page says otherwise. **CoverForce = commercial-insurance API/infrastructure** company (unified API to quote/pay/bind/issue policies, connecting carriers/agencies/wholesalers). **$13M Series A led by Insight Partners** (w/ Nyca Partners), announced **March 5, 2025**; Sophie Beshar (Insight) joined the board. Sources: [LinkedIn](https://www.linkedin.com/in/kennethctsai/), [Insight Partners](https://www.insightpartners.com/ideas/coverforce-secures-13-million-in-series-a-funding-led-by-insight-partners-to-build-infrastructure-and-connectivity-between-insurance-carriers-and-agencies/), [PRNewswire](https://www.prnewswire.com/news-releases/coverforce-secures-13-million-in-series-a-funding-led-by-insight-partners-to-build-infrastructure-and-connectivity-between-insurance-carriers-and-agencies-302392405.html).
- ✅ **"Cyrus" RESOLVED.** CoverForce's founders are **Cyrus Karai, Behram Dinshaw, and Kaivan Wadia.** So Kenny's "CEO-to-CEO overrides through **Cyrus**" = routing high-value outreach through **Cyrus Karai, CoverForce's CEO/co-founder** — not a tool. Flag closed.

**Supporting verifications.**
- ✅ **Aon ~60,000 employees** — confirmed (60,000 as of Dec 31, 2024, up ~20% YoY via the NFP acquisition) — [Macrotrends](https://www.macrotrends.net/stocks/charts/AON/aon/number-of-employees). Kenny's "~60,000" is exactly right.
- ✅ **Geoffrey Moore / Crossing the Chasm** — confirmed (1991; >1M copies).
- ✅ **Insight Partners** — $90B+ regulatory AUM (Sept 30, 2024); CoverForce + Optimizely both portfolio — context for the venue.
- 🔴 **Insight "AI Lab" team + host "Jack"** — could **not** verify publicly. Jack self-described the team on stage ("I did not name it"); treat as accurate-per-his-own-words but unconfirmed externally. Still maps to the brief's "Insight Onsite" job-search target.

**Recommended next steps:** (1) Pull the Luma page for Masterclass #5 to lock Nikita's name/title, Kenny's title, Nimo↔Swan relationship, and "Jack." (2) Do not publish the Moore→MOVE endorsement text or "S1"/"Impact 11"/"Two Hops" as fact. (3) For public content needing the 8 GTM-OS pillar names, they are transcribed from the slide in §5 (authoritative) but cross-check against a GTM Partners primary page if used verbatim.

---
*Brief built 2026-06-27 from: primary ElevenLabs transcript (438 lines), slide↔transcript alignment doc, all 22 slide photos (read directly), REVIEW low-confidence list, and a web-enrichment research pass. Slides override ASR for all names/numbers. Quote bank flags every low-confidence span.*
