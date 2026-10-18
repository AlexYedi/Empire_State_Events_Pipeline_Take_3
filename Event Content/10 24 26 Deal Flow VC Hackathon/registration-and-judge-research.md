# Deal Flow: NYC's First VC Hackathon — registration and judge research

- **Event:** Deal Flow, hosted by localhost:nyc and VCLab at betaworks, Saturday 2026-10-24. One day, in person, 9 hours, teams of 4, live demos judged by NYC fund partners. Sponsor: SeedLegals. Only prize named: intros to the judges' funds. No scoring rubric published as of 2026-10-18.
- **Tracks:** Sourcing · Diligence · Portfolio ops · LP reporting ([GarysGuide listing](https://www.garysguide.com/events/l2mm85l/Deal-Flow-NYC-s-First-VC-Hackathon)).
- **Prepared:** 2026-10-18, pre-registration. Judge research by two `alex:research-analyst` runs, public sources only.

## Event problem statement (as published)

> Venture capital runs on spreadsheets, gut feel and endless inbox triage. Firms move billions of dollars with tools that haven't changed in a decade. Your challenge is to build software that helps VCs find better companies, make faster decisions and support their founders after the check clears.

## Ideas considered

1. **Sourcing: rank founders from events and inbound (chosen).** Pull founders from NYC event listings (speakers, demo presenters, organizers) and a fund's inbound, research each with sourced claims, score against the fund's thesis with a visible rationale, surface the warmest intro path, push into the fund's deal tracker for human review. Chosen because it is the pipeline Alex already runs for his own event coverage, it demos live on that week's real events, and the judges recognize the problem.
2. **Diligence: first-meeting memo with sourced claims.** Deck or URL in, market map plus competitor table plus memo out, every claim cited or flagged verify/soften/cut. Strong differentiator in the sourcing discipline, but memo drafting will be the most crowded idea in the room.
3. **Portfolio ops: enterprise intro engine.** Match each portfolio company's ICP against the fund's network and other portfolio companies' customers; rank warm enterprise intros. Best use of Alex's enterprise sales background, weakest demo (no real fund data on the day).

## The reframe from the judge research

None of the confirmed judges' funds is short of founders. Plug and Play runs on high-volume accelerator and corporate-partner intake; Everywhere Ventures runs on referrals from ~500 founder and operator LPs. "Find more founders" solves a problem they don't have. **Rank founders, explain each score, and show the warm intro path** solves the one they do. Same build, different promise.

## Registration text (final, 2026-10-18)

> **Problem:** VC funds don't lack founders; they lack a fast way to rank them. Pre-seed has little traction data, so partners triage hundreds of inbound applications and referrals by gut feel, while the earliest public signals (founders speaking, demoing and organizing at events) go untracked. I want to build an agent pipeline that pulls founders from event listings and a fund's inbound, researches each one with every claim sourced, scores them against the fund's thesis with a visible rationale, and surfaces the warmest intro path (a portfolio founder, an LP, a shared event) before pushing them into the fund's deal tracker for a human to review.
>
> **Business:** Priced per seat for emerging managers, scout programs and platform teams.
>
> **What I bring:** 12+ years in enterprise B2B SaaS sales and GTM. I already run an AI research pipeline that does event, founder and company research for my NYC event coverage, so I'll own the research method, product design and pitch. Looking for engineers strong in APIs/scraping, LLM agent orchestration and a light front end.

## Judge panel

| Judge | Identity confidence | What matters | Likely question |
|---|---|---|---|
| Abeera Saeed, Plug and Play | 75% | Enterprise and AI B2B, pre-seed to Series A; Plug and Play's NYC AI Nexus (opened Nov 2025 with NYCEDC) targets F&B, media/advertising, travel/hospitality, professional services | "We drown in applications. Does this rank inbound, or only find outbound?" |
| Michael Barone, Everywhere Ventures | 85% | Global pre-seed, $250K first checks, ~300 portfolio companies; hosts the *Venture Everywhere* podcast | "Does this work outside NYC?" |
| D.J. Patel | Unresolved | Very likely not DJ Patil (former US Chief Data Scientist, GreatPoint Ventures); no reliable match found | Founder test: "Would I want to be scored by this? What's the false-positive rate?" |
| Garrett Higgins, PointOne (ex-Rilla) | 85% | Finance and GTM operations at two fast-growing AI workflow companies; angel investing claimed, unverified | CRM write, dedup, hours saved vs. doing nothing, who pays |
| Radhika Khandelwal, Wand AI | 35% | Only source is the event page; prior VC firm not findable; Plug and Play is listed as a Wand AI investor | Agent design and accuracy: sourcing per claim, score calibration, plus the business |
| Bettina Sosa, Yaven | 95% | Yaven overlaps this build (trigger-event prospecting, contact mapping for event invites); privacy-first; appears to be part of betaworks | Where the data lives, who sees it, cost per run |

### Abeera Saeed — Plug and Play

- **Identity (75%).** Event page: Ventures Principal, Plug and Play. Byline on the Plug and Play Enterprise & AI newsletter, 2026-10-07 ([Substack](https://pnpenterpriseai.substack.com/p/deep-dive-permission-not-power)). Indexed LinkedIn still shows a prior role at Propel Capital (Brooklyn impact investor), likely a pre-move snapshot. "Principal" title not independently verified.
- **Thesis and checks.** Enterprise and AI; aggregator figures put pre-seed at $25–150K and seed at $100–500K ([f4.fund](https://f4.fund/firms/plug-n-play-ventures)). Low-quality, inconsistent data: medium confidence.
- **Portfolio.** Nothing found that Abeera personally led; the fund has 1,000+ companies.
- **Public POV.** The one public piece argues community consent, not power, is the data-center bottleneck. Nothing found on sourcing or AI in VC.
- **How the fund sources.** Accelerator batches (140 startups in the Fall 2026 Silicon Valley cohort) and 500+ corporate partners seeking pilots. NYC launch with NYCEDC: NYC AI Nexus targets 165 startups and 96 pilots ([PR Newswire](https://www.prnewswire.com/news-releases/plug-and-play-expands-to-new-york-city-to-accelerate-ai-and-deeptech-innovation-across-key-industries-302621846.html)).
- **Demo implications.** Score against "pre-seed to A enterprise AI that can pilot with a Fortune 500 partner in an NYC AI Nexus vertical." Add a corporate-partner-fit field to the dossier.

### Michael Barone — Everywhere Ventures

- **Identity (85%).** Indexed LinkedIn title "Associate at Everywhere Ventures"; hosted *Venture Everywhere* Ep. 110 (2026-03-10), billed as investment analyst ([Apple Podcasts](https://podcasts.apple.com/us/podcast/all-in-one-zelt-solution-chris-priebe-with-michael-barone/id1683046904?i=1000754472655)). Likely a recent promotion.
- **Thesis and checks.** Global pre-seed, $250K first checks, ~$100M AUM, 300 portfolio companies in 30 countries; future of work, fintech, health, deep tech, climate ([everywhere.vc](https://www.everywhere.vc/)). High confidence.
- **Portfolio.** Fund-level, none attributed to Michael: Cube (FP&A), Eudia (legal AI), Starcloud (AI infrastructure).
- **Public POV.** The Zelt episode covers product depth vs. ease of use and change management in AI adoption. Nothing found on sourcing.
- **How the fund sources.** ~500 founder and operator LPs refer, diligence and mentor deals; GPs vet ([AngelList](https://venture.angellist.com/everywhere-ventures/syndicate)).
- **Demo implications.** Show a "warm path via founder LP" signal. Show that event sources are pluggable beyond NYC. A future-of-work thesis example fits.

### D.J. Patel

- **Identity unresolved.** ~85% confident this is not DJ Patil: Patil's record is angel investing (Figma, RelateIQ), not three founder exits, and the event spells the name "Patel" ([Axios](https://www.axios.com/2023/02/22/dj-patil-greatpoint-ventures)). No NYC "D.J. Patel" with a VC and three-exit record found.
- **Demo implications.** Expect the founder-operator test. Show the reasoning behind each score and the human-review step.

### Garrett Higgins — PointOne

- **Identity (85%).** Event page: "GTM, PointOne." LinkedIn headline (search snippet): "Finance & GTM @ PointOne."
- **Background.** Rilla (AI coaching for field sales), ~2023 to mid-2025, Finance Lead then Head of Finance & Operations; Sacra estimates ~$70M ARR (Apr 2026) ([Sacra](https://sacra.com/c/rilla)). Now PointOne (AI time capture for lawyers), $16M Series A in Mar 2026 led by 8VC with Bessemer, General Catalyst and YC ([Global Legal Post](https://www.globallegalpost.com/news/time-recording-start-up-pointone-secures-16m-in-funding-round-395953331)). Founded a $120K student investment fund (2020 onward).
- **Investments.** None found; angel status unverified.
- **Demo implications.** Show the CRM write: which tracker (Affinity, Attio, HubSpot), how duplicates are avoided, what triggers the write. Give an hours-saved number with its do-nothing baseline.

### Radhika Khandelwal — Wand AI

- **Identity (35%).** Event page only: "AI Product Lead, Wand AI," wants "both slick code and a real business." No profile linking Radhika to Wand or a VC firm; several people share the name. Prior VC firm: not findable. Ask, don't guess.
- **Wand AI.** An operating system for mixed human and AI-agent teams, with prebuilt agents for finance, HR and legal ([wand.ai](https://wand.ai/product-page)). CEO Rotem Alaluf. ~$33M raised per PitchBook ([PitchBook](https://pitchbook.com/profiles/company/504115-39)); Plug and Play listed as an accelerator investor. Acquired Accern ([Forbes, Feb 2025](https://www.forbes.com/sites/alexyork/2025/02/07/under-30-company-accern-gets-acquired-by-hotter-ai-startup/)).
- **Demo implications.** Be ready on agent design: why specialist agents vs. one, how fabricated founder facts are prevented (every claim sourced), how the fit score is calibrated. Bring a small eval (precision on 20 hand-labeled founders) and a one-line pricing and buyer slide.

### Bettina Sosa — Yaven

- **Identity (95%).** Event page, [Yaven About](https://www.yaven.ai/about), LinkedIn and GitHub agree.
- **Background.** MEng Design Engineering, Imperial College London (2021). Founding engineer then Head of Engineering across blockchain, zero-knowledge and developer tools; Head of Developer Relations at Partisia Blockchain. Co-founder and CTO Nick Price previously built AI agent infrastructure for a hedge fund.
- **Yaven.** Private AI assistant for Mac aimed at independent creative agencies ([yaven.ai](https://www.yaven.ai/)): trigger-event prospecting (new marketing hire, funding round), drafting replies to inbound briefs, client market monitoring, flagging past clients due for work. Personal context stays on the Mac, no training on client data. Waitlist; no public pricing. About page says "part of Betaworks" (likely Betaworks Camp; no cohort list confirms). Seed-stage per [F4](https://f4.fund/startups/yaven).
- **Public POV (LinkedIn, last month).** Privacy first; cut tool and model routing cost and latency ~5x and presented it at a TypeSafe AI event; used Yaven to map overlapping people for an invite-only NYC AI dinner.
- **Demo implications.** Expect "where does founder and thesis data live, and who sees it?" Answer: contact details stay out of the research store. Show cost per run and batch latency.

## What the demo must show

1. Each score with its rationale and sources (Radhika, D.J.).
2. A small accuracy check: 20 hand-labeled founders, top-pick precision vs. a random-ranking baseline.
3. Contact details kept out of the research store, plus cost per run (Bettina).
4. A record landing in the fund's tracker with no duplicate (Garrett).
5. Pluggable event sources beyond NYC (Michael) and a corporate-partner-fit field (Abeera).

## Open before Saturday

- Confirm Radhika Khandelwal's prior VC firm from LinkedIn (Alex, 2 minutes).
- Ask the organizers (localhost:nyc or VCLab) for D.J. Patel's LinkedIn.

## Caveats

Check sizes come from aggregators that disagree. Neither confirmed investor judge has public writing on sourcing or AI in VC, so "what they value" is inferred from each fund's model, not stated views.
