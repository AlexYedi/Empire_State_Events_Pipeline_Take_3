# Voice AI Hackathon — Deep Brief (Agora × ScaleDown, Jun 26–27 2026)

## Context
Alex's **first hackathon**: "Build, Listen, Deploy: Voice AI Agents Hackathon | Agora × ScaleDown AI."
- **Fri Jun 26, 5:30 PM** — kickoff, lightning talks, **team formation**, challenge announcements, food.
- **Sat Jun 27, 9 AM–5 PM** — build, mentorship, demos + judging, awards.
- 📍 Amazon JFK27 "Hank", 12 W 39th St, Midtown NYC. Hosts: **Agora, Hermes & Neal Patel**.
- **Prizes:** Grand $1.5k cash + $1k ConvoAI minutes + 10B ScaleDown tokens · Runner-up $750 + $500 ConvoAI minutes + 5B ScaleDown tokens.

**Goal of this doc:** go 3 cycles deep on 4 categories so Alex can practice-build beforehand and show up ready to win, network, and place.
Categories: **A. Event/landscape · B. The 5 project ideas · C. Voice-AI best practices · D. Networking/winning.**
Method: 3 research agents (Agora ConvoAI/RTC · ScaleDown + compression · voice architecture + winning) → layer specificity each cycle, pause between cycles.

**Alex's edge:** GTM/product operator (Apollo/Clay/HubSpot stack, eval-harness, objection-handling/reinforcement skills). Most attendees are AI engineers — he should weaponize GTM storytelling + a vertical wedge.

---

# CYCLE 1 — Research-grounded specifics

## A. Event & landscape context
- **The host is a judging signal.** "Hermes" = **Hermes Frangoudis, Director of DevRel & Partner Engineering at Agora** (writes the ConvoAI Medium tutorials in Go/Python). Find him Friday; reference his posts; ask about ConvoAI **semantic turn detection** (beta). This is the single highest-leverage network move. (Neal Patel's Agora affiliation unconfirmed.)
- **Likely judging rubric** (from Agora's Istanbul Jan-2026 hackathon repo, the closest precedent): Technical Innovation 20% · Experience Design 20% · **Agora Tech Integration 20%** · Impact 15% · Deployment 15% · Execution 10%. Implication: **40% of the score is innovation + clean UX, 20% is explicitly "did you use Agora well."** Use ConvoAI as the spine, not a wrapper.
- **Sponsor prizes are credits = use both tools prominently.** ConvoAI minutes (Agora) + ScaleDown tokens. A build that visibly leans on ConvoAI *and* ScaleDown is the cheapest path to a sponsor's favor.
- **What ConvoAI is:** an engine that orchestrates ASR→LLM→TTS over Agora's SD-RTN network. *You* bring LLM/ASR/TTS keys + system prompt + a web client; *Agora* handles audio transport, VAD, **barge-in/interruption**, noise suppression, turn-taking. Agent joins a channel via REST (`POST /api/conversational-ai-agent/v2/projects/{appid}/join`).
- **Two build paths:** (1) **Agent Studio** (no-code console, ~10 min to a working agent, with a **Knowledge Base** upload + **MCP server "Actions"** so the agent can call external tools/CRMs); (2) **REST API + web client** (`agora-rtc-sdk-ng` v4.24+, RTC for audio + RTM for live transcripts) for full control. There's also a direct **Agora × OpenAI Realtime** path (lowest latency, less barge-in control).
- **Cost reality:** ConvoAI = **300 free min/month** (shared with STT), then **$0.10/min**, billed for *all* channel participants while the agent is live, **separate** from the 10k RTC free pool. 300 min ≈ 5 hrs of testing → **will run thin**. Action: ask organizers for hackathon credits Friday.
- **Market backdrop (for the pitch's "this is real" slide):** voice AI $18.4B→$61.7B; VC funding $2.1B in 2025 (~7× in 3 yrs); **22% of the latest YC batch** building voice; 69% B2B. Vertical specialists win (PolyAI 391% ROI; Retell; Rime at Domino's/Wingstop). **Wedge strategy** (own 5–10% of call volume, prove ROI, expand) beats "full automation."

## B. The 5 project ideas — now with real stack, latency truth, and the exact Agora/ScaleDown hook

> **Recommended default stack** for a snappy demo: **ConvoAI + Deepgram Nova-3 STT (150ms) + gpt-4o-mini or Llama-3.1-8B@Groq + Cartesia Sonic / ElevenLabs Turbo TTS (40–90ms first-byte).** Agora's optimized pipeline floor is ~**650ms** end-to-end and ~**340ms** interruption; bad vendor picks balloon it to 3.5–7.6s, so **vendor choice is the latency lever.**

> **ScaleDown truth (use it honestly — judges/mentors will probe):** the compression call itself costs ~100–500ms, so it is **latency-positive only on large context** (RAG, long conversation memory), where it cuts 40–60% of input tokens and ~25–33% of TTFT. On a thin system prompt its win is **cost + handoff-quality, not turn latency**. So lean ScaleDown into the RAG-/memory-heavy ideas, and run it **in parallel with ASR** so it's off the critical path.

### ⭐ 1. "Warm Hand-off" voice SDR → live human transfer + ScaleDown-compressed brief
- **Agora hook (strong):** ConvoAI qualifies the caller; on a hot signal you add a **human as a 3rd participant to the same RTC channel** (Agora multi-party) and push a brief over **RTM**. This is a genuine Agora-native capability most teams won't use → scores the 20% "Agora integration."
- **ScaleDown hook (genuine):** compress the full running transcript into a 3-bullet briefing for both the rep (RTM card) and the LLM memory. Context is large → compression actually pays.
- **Stack:** ConvoAI pipeline + gpt-4o-mini + Deepgram + Cartesia; RTM for the brief card.
- **Novelty/why it wins:** everyone builds "AI receptionist"; almost nobody nails the **human↔AI handoff with context transfer** — the actually-hard, valuable part.
- **GTM:** SDR/inbound; replaces 2–3 SDR FTEs per AE (market-validated). Alex's home turf.
- **Demo wow:** live transfer on stage — "let me bring in Alex" → you join mid-call already knowing everything; ScaleDown brief renders live.
- **1-day cut:** skip PSTN; two browser clients in one channel. The transfer + compressed brief *is* the demo.

### ⭐ 2. Voice sales-roleplay sparring partner (highest demo-to-effort; best first-hackathon pick)
- **Agora hook:** **barge-in is native** — configure `turn_detection` (`interrupt_duration_ms: 160`) so the "tough buyer" cuts you off. Showcases ConvoAI's interruption directly with near-zero effort.
- **ScaleDown hook (lighter):** compress persona + rolling objection state; honest framing = "keeps the buyer reacting fast + cheap," not a latency miracle.
- **Stack:** classic ASR+LLM+TTS pipeline (not OpenAI Realtime) so you control barge-in; gpt-4o-mini persona; post-call LLM score vs. Alex's objection-handling rubric.
- **Novelty:** a buyer who **interrupts you in real time** is viscerally different from chat roleplay.
- **GTM:** sales enablement/onboarding — ties to Alex's reinforcement-drills + objection-mining skills. Coaching is a funded category (Sesame, Mindtickle).
- **Demo wow:** have a *judge* try to pitch the AI buyer; it interrupts and pushes back.
- **Risk:** lowest — pure browser voice + scorecard, no CRM/telephony auth.

### 3. Hands-free "Drive-Time" voice CRM
- **Agora hook (excellent fit):** **Agent Studio "Actions" → MCP server** lets the agent call CRM tools (HubSpot/Apollo) by voice. "Log that call, set a follow-up Tuesday" → real write. "Take action" is literally the event thesis.
- **ScaleDown hook:** compress the pulled account/CRM context before each turn (medium-size context → real win).
- **Novelty:** voice as a *write* surface for CRM, not dictation.
- **GTM:** reps hate CRM entry; clean wedge; strongest "I live in this stack" story for Alex.
- **Risk:** CRM auth/rate limits eat the day → stub a fake CRM tool if needed, keep the voice→action loop real.

### 4. Voice onboarding/activation agent for PLG SaaS
- **Agora hook:** Agent Studio **Knowledge Base** (upload product docs) → RAG-grounded answers; phone or web.
- **ScaleDown hook (BEST fit):** RAG context is the biggest latency tax in voice; **compress retrieved chunks in parallel with ASR**. This is where you can show a real before/after latency + token number on stage — sponsor candy.
- **GTM:** PLG activation funnel; pairs with Alex's onboarding-blueprint/activation-map skills.
- **Demo wow:** side-by-side latency meter: raw RAG vs. ScaleDown-compressed RAG, quantified.

### 5. Real-time multilingual voice concierge
- **Agora hook:** showcases Agora's **core** differentiator — global SD-RTN ultra-low-latency audio (76ms median RTT) — which most teams ignore. Hits the "human-computer interaction/accessibility" theme judges like.
- **ScaleDown hook:** compress conversation history + domain glossary to hold latency across turns.
- **Novelty here:** make it **bidirectional + barge-in-able** (most multilingual demos aren't).
- **Risk:** most "done before" of the five — win on real-time feel, not concept.

**My pick for Alex:** Build **#2** to guarantee a clean jaw-drop on a first hackathon (lowest risk). Build **#1** to *win* + tell the strongest GTM story (most differentiated, most "him"). Either way ScaleDown is load-bearing and honestly framed.

## C. Voice-AI best practices (researched)
- **Latency budget — target <800ms mouth-to-ear** (production median is 1.4–1.7s; >3s feels broken; humans expect 200–300ms). Component budget (optimized): STT 100–200ms · **LLM 200–400ms (≈70% of total — the #1 lever)** · TTS 100–250ms · network 50–150ms · VAD/turn 200–400ms.
- **Vendor picks that hit budget:** Deepgram Nova-3 (150ms), ElevenLabs (75ms first-byte), Cartesia Sonic (40–90ms), gpt-4o-mini (~200–400ms TTFT) or Llama-3.1-8B@Groq (50–100ms). OpenAI Realtime = 300–500ms speech-to-speech if you go that route.
- **Turn-taking / barge-in:** ConvoAI handles it; tune `interrupt_duration_ms` (160 = snappy, 300–500 in noise) and `silence_duration_ms` (~640 prevents cutting people off). **TTS must stop within ~60ms of detected user speech** to not feel ignored. Semantic endpointing is beta.
- **Stream everything + sentence-chunk TTS** so first audio plays before the full response is generated. Fewer input tokens (ScaleDown) = faster TTFT.
- **SLMs do 80–90% of voice subtasks** (intent, routing, extraction) at 10–100× lower cost — use a small model for turns, big model only for offline scoring/summary.
- **Failure modes to design around:** latency degrades 40–120% under load; STT accuracy drops 10–25% in real noise; **cold start adds 2–5s on first call**; WiFi adds 50–100ms; echo >150ms is disorienting → use AI noise suppression + a good headset.
- **Framework note:** Agora ConvoAI is the spine here, but Pipecat (Python) / Vapi (no-code, provider-swap) are the fast prototyping references if needed.

## D. Networking & winning (researched, first-timer)
- **Friday = team formation; be the GTM/pitch person.** The room is mostly engineers; a credible product voice who can scope + pitch is scarce and wanted. Pitch one idea aloud to attract 1–2 builders. Target team: 1 core coder (async/streaming), 1 integrations person, 1 demo/pitch lead (Alex).
- **Win the sponsors directly:** find Hermes (Agora DevRel) + the ScaleDown reps early; ask *technical* questions ("how do you handle interruption / what's your TTFT budget?"). Use ConvoAI as the spine and ScaleDown visibly → you qualify for both sponsor prizes (you can usually enter ≤2 sponsor challenges + grand prize). **Namedrop the sponsor tech in the pitch** or the judge won't know you used it.
- **Scope brutally to ONE happy-path demo (60–90s).** Pre-load context (no live RAG network calls during the demo). Build the single demo path end-to-end Friday night, polish Saturday.
- **2-minute pitch:** 0–10s hook + names · 10–30s problem + who's hurt + $ impact · 30–90s live demo (the wow) + the ScaleDown/latency number · 90–120s one-line GTM/next-step. Judges remember beginnings + endings.
- **Demo survival:** test on venue WiFi/mic **15 min before**; AirPods Pro or a real headset; **pre-record a 2–3 min backup video** of a clean run.
- **Pre-flight Friday night:** enable ConvoAI in Agora Console, generate RTC+RTM tokens, validate LLM/ASR/TTS keys with curl, get a "hello-voice" round-trip working, confirm HTTPS for mic. Common killers: free-tier exhaustion, 1-hr token expiry (`renewToken`), CORS on the LLM call, agent UID colliding with a human UID.
- **Content moat:** Alex is already running pre-event content in another thread — capture team-formation, build, demo for post-event content regardless of placing.

---

# CYCLE 2 — Architecture, risk, GTM comps, and what-to-cut (all five ideas + deeper A/C/D)

## A. Event & landscape — layer 2
- **Why each sponsor runs this (use it):** Agora is the RTC incumbent moving *up-stack* into AI — they need **ConvoAI developer adoption + tweetable case studies**. ScaleDown is **early** (GitHub `scaledown-team`) and needs **logos + production-voice validation**. Implication: a clean, demo-able, *shareable* build is disproportionately valuable to them — they may amplify it, intro you, or weight your prize. Build something they'd want to retweet.
- **Don't start from scratch.** Clone Friday night: **`AgoraIO-Community/Istanbul-Hackathon-Jan-2026`** (starter + rubric) and **`AgoraIO-Conversational-AI/agent-samples`** (working backends, Python/Node). Also `AgoraIO/openai-realtime-python` if you take the Realtime path.
- **Path decision framework:**
  - **OpenAI Realtime path** (Agora × gpt-4o-realtime): fastest to "hello," lowest latency (~300ms), simplest — but vendor-locked, weaker barge-in control, no clean tool-calling. → good for **#4, #5** (speed/feel demos).
  - **ASR+LLM+TTS pipeline** (BYO Deepgram + gpt-4o-mini + Cartesia): vendor flexibility, full `turn_detection` control, supports tool-calls + ScaleDown insertion. → use for **#1, #2, #3** (control, actions, handoff).
- **Minute budgeting:** every test call burns ConvoAI minutes × participants. Keep test calls short, mute idle clients, ask for credits at kickoff, save 1 hr of minutes for the demo + rehearsal.

## B. The five ideas — architecture / ScaleDown verdict / #1 risk → fix / GTM comp / effort + cut

### 1. Warm Hand-off voice SDR
- **Arch:** Caller (browser A) + ConvoAI agent in channel → on trigger, backend adds human rep (browser B) to the *same* RTC channel + posts ScaleDown brief as an RTM data message → agent drops to observer.
- **ScaleDown verdict:** ✅ genuine — full transcript is large; compression improves both LLM memory and the human's brief.
- **#1 risk → fix:** 3-way channel + "when to transfer" logic is fiddly → **hardcode a trigger phrase** ("connect me to a human") instead of an intent classifier for the demo.
- **GTM comp:** Qualified/Piper AI, 11x (AI SDR) — your differentiator is *context-preserving handoff*, which they don't nail.
- **Effort 4/5. Cut if behind:** drop auto-intent; trigger phrase + pre-templated brief.

### 2. Roleplay sparring partner
- **Arch:** Single browser client + ConvoAI agent, "tough buyer" persona, aggressive `interrupt_duration_ms: 160`; on "end call," POST transcript to gpt-4o → scorecard in UI.
- **ScaleDown verdict:** 🟡 cost/quality only (thin per-turn context) — frame honestly as "compress the scenario/persona library," not a latency win.
- **#1 risk → fix:** persona breaks character or folds too fast → tight system prompt with an explicit objection bank + rule "never concede in <3 exchanges."
- **GTM comp:** **Hyperbound** (AI buyer roleplay, funded), Mindtickle, Sesame.
- **Effort 2/5. Cut if behind:** drop the scorecard; the live interrupting buyer *is* the demo.

### 3. Drive-Time voice CRM
- **Arch:** Agent Studio agent + **MCP server** exposing CRM tools (`log_call`, `create_task`, `get_next_meeting`) → voice command triggers tool call → visible record update.
- **ScaleDown verdict:** ✅ moderate — compress pulled account context before the turn.
- **#1 risk → fix:** OAuth + MCP wiring is the time sink → **stub MCP with an in-memory fake CRM that updates on screen**; keep the voice→action loop 100% real.
- **GTM comp:** Attention, Momentum (call→CRM, but *not* voice-command write) — voice-write is open space.
- **Effort 4/5. Cut if behind:** fake CRM + 2 commands only.

### 4. Onboarding / activation agent
- **Arch:** Agent Studio + **Knowledge Base** (upload product-doc PDF) → ConvoAI answers; instrument TTFT on two paths: raw retrieved chunks vs. **ScaleDown-compressed chunks (async during ASR)**.
- **ScaleDown verdict:** ✅✅ best fit — RAG context is the biggest latency tax; this is your on-stage before/after number.
- **#1 risk → fix:** RAG retrieval on the critical path → pre-embed docs, pre-warm, run ScaleDown in parallel with ASR.
- **GTM comp:** CommandBar/Command AI (onboarding) — voice surface is the novelty.
- **Effort 3/5. Cut if behind:** 3-question scripted onboarding instead of open RAG.

### 5. Multilingual concierge
- **Arch:** ConvoAI, multilingual ASR + translation in the LLM step + multilingual TTS (ElevenLabs 70+ langs); two participants, two languages.
- **ScaleDown verdict:** 🟡 moderate — compress glossary + history.
- **#1 risk → fix:** ASR/LLM/TTS language config must align + cross-language barge-in → fix exactly two languages, test both directions.
- **GTM comp:** PolyAI (45 langs), Retell multilingual.
- **Effort 3/5. Cut if behind:** one direction first (tourist→local).

## C. Voice-AI best practices — layer 2 (implementation specifics)
- **`turn_detection` playbook:** start-of-speech `interrupt_duration_ms` 160 (snappy) → 300–500 (noisy venue, fewer false barge-ins); `threshold` ~0.5; end-of-speech `silence_duration_ms` ~640 (don't go <400 or you cut people off); `max_wait_ms` ~5000. Try `mode: semantic` only if Hermes says it's stable.
- **Sentence-chunk TTS:** buffer LLM tokens to the first sentence boundary, fire TTS immediately, keep buffering → first audio in ~150–300ms even on long answers.
- **SLM routing pattern:** small/fast model for every turn (gpt-4o-mini / Llama-3.1-8B@Groq); escalate to a big model **only offline** (scorecards, post-call summaries) so it never sits on the latency path.
- **Noise/echo:** enable Agora **AI noise suppression**; headset with mic; rely on client-side echo cancellation so the agent doesn't hear itself and false-trigger barge-in.
- **Instrument TTFT per turn and log it** — so in the pitch you can *say the number* ("780ms p50, 33% faster with ScaleDown"). Numbers win technical judges.
- **Do NOT demo under load or multi-turn-complex.** One pre-loaded happy path. Cold start adds 2–5s → make a throwaway warm-up call right before you present.

## D. Networking & winning — layer 2 (scripts)
- **Teammate recruit (Friday, say this):** *"I'm a product/GTM person — I've scoped a voice SDR that does a live warm hand-off with a compressed brief. I'll own the pitch, demo, and the GTM story; I need one backend/streaming dev and one integrations dev. Want in?"*
- **Sponsor questions (technical, not generic):** to Agora/Hermes — *"What `silence_duration_ms` do you recommend for a noisy room, and is semantic endpointing stable yet?"*; to ScaleDown — *"What's your compression API's own latency, and do you support async so I can run it during ASR?"* These signal you actually build.
- **2-min pitch, filled (idea #1):** *"SDRs burn hours on calls that should've been a 2-minute human chat. [demo: AI qualifies, says 'let me bring in Alex,' I join already knowing everything, brief on screen] — that brief is a ScaleDown-compressed transcript, and the whole call ran on Agora ConvoAI at ~700ms. This sells to every inbound team; it replaces 2–3 SDRs per AE. Next: PSTN + CRM write."*
- **Judge Q&A prep:** expect "how's this different from [Vapi/Retell]?" (→ context-preserving handoff), "what's your latency?" (→ have the number), "does it scale?" (→ Agora SD-RTN + wedge strategy), "business model?" (→ per-seat or per-minute, SDR replacement ROI).
- **Capture for content + follow-up:** collect teammates'/mentors' LinkedIns; post the demo clip that night tagging Agora + ScaleDown (sponsors amplify → more reach than the prize).

# CYCLE 3 — Sponsor & judge mastery + GTM theses (final layer)

## SPONSOR & JUDGE MASTERY

### Score the rubric on purpose (Istanbul precedent)
| Bucket | Wt | How to bank it |
|---|---|---|
| Technical Innovation | 20% | Use a capability others skip — multi-party warm transfer (RTM brief), MCP tool-calls, or a live ScaleDown latency delta. |
| Experience Design | 20% | One flawless 60–90s path; natural barge-in; agent sounds human (greeting, fillers). |
| **Agora Tech Integration** | 20% | ConvoAI as the spine + name a 2nd Agora feature (RTM / noise suppression / multi-party). Say it in the pitch. |
| Impact | 15% | Lead with the $ pain + who's hurt + the wedge. |
| Deployment | 15% | It runs live (not slides); deployed token server; have a URL. |
| Execution | 10% | Clean README + architecture diagram + 2-min demo video in the repo. |

### Hermes Frangoudis (Agora DevRel Director — host, highest-leverage contact)
- **Who:** 20+ yrs web, 10+ yrs RTC/AR/AI; ex-lead SE at Blippar NYC; co-founded webXR.tools; author of the ConvoAI Medium tutorials (Go + Python).
- **Opener (specific, not generic):** *"I read your ConvoAI Golang service walkthrough — I'm using the multi-party channel to do a live warm hand-off with an RTM brief. Is semantic endpointing stable enough to trust for the demo, or should I stay on VAD?"*
- **The ask that makes him remember you:** offer to be a **clean case study / demo clip** Agora can share. DevRel lives on shippable community proof.

### ScaleDown reps (early company — they need production validation)
- **What they want:** logos, real benchmarks, devs proving compression works in live voice.
- **Ask:** *"What's the compression API's own latency, do you support async (so I run it during ASR), and does `rate` auto-tune to my target model?"* Check the `ScaleBench` repo.
- **The gift:** publish a **before/after benchmark** (tokens + TTFT, raw vs. compressed) from your build and share it with them — that's marketing gold for an early team → near-guaranteed amplification, maybe the ScaleDown prize.
- **Neal Patel:** affiliation unconfirmed — find out who he is Friday and what he's judging on.

### Judge Q&A — rehearse these (top-2 ideas)
- *"Isn't this just Vapi/Retell?"* → "Those are pipelines; my wedge is **context-preserving human handoff** / **real-time interrupting roleplay** — the part they don't solve."
- *"What's your latency?"* → say the number you logged ("~700–800ms p50; 33% faster turns once RAG is ScaleDown-compressed").
- *"What if ScaleDown drops a critical token?"* → "It classifies keep/drop, no generation, so no hallucinated content; I keep the system prompt + last-N turns verbatim and only compress bulk context."
- *"Does it scale?"* → "Agora SD-RTN handles the transport; I'd land on a wedge (5–10% of calls) and expand."
- *"PII / compliance in a sales context?"* → name it proactively (you already have a guardrails workstream — YED-81): redact before LLM, no PII in logs, human-in-loop on sensitive actions. Naming risk = product maturity.
- *"Business model?"* → per-seat + per-minute passthrough, or outcome-based (per booked meeting / per activation).

### Get amplified beyond the prize (the durable win)
- Ship a **30–60s demo clip** + a short writeup with the benchmark; post that night **tagging Agora + ScaleDown**; DM Hermes the clip and the ScaleDown team the benchmark.
- Sponsor amplification + the relationships outlast the $1.5k. This is also straight fuel for Alex's content engine (the other thread).

## GTM THESES — each idea as a real go-to-market (ICP · pain · wedge · pricing · expansion · comp · why-now · hook)

**1. Warm Hand-off SDR** — *ICP:* B2B SaaS/services, 10–200 reps, inbound volume; buyer VP Sales/RevOps. *Pain:* speed-to-lead (leads rot in minutes) + context lost at handoff. *Wedge:* after-hours/overflow inbound only → prove booked-meeting lift → all inbound → outbound. *Pricing:* per-seat + ConvoAI-minute passthrough, or per-qualified-meeting. *Expansion:* displaces 2–3 SDR FTEs/AE. *Comp:* Qualified, 11x, Piper. *Why now:* sub-second ConvoAI makes live transfer feel human. *Hook:* "An AI SDR that taps a human in mid-call — with a perfect brief."

**2. Roleplay sparring** — *ICP:* sales enablement/L&D, new-rep onboarding; buyer Enablement. *Pain:* ramp time; manager role-play doesn't scale; objection skills learned in lost deals. *Wedge:* one objection-pack for one motion → ramp-time proof → scenario library + scoring + manager dashboards. *Pricing:* per-seat SaaS, tiered by library/analytics. *Expansion:* training → live-call coaching → 100% call QA (Retell-Assure-style). *Comp:* Hyperbound (funded), Mindtickle, Second Nature. *Why now:* barge-in realism + cheap SLMs = unlimited practice reps. *Hook:* "The AI buyer that interrupts you — rehearse the call that scares you."

**3. Drive-Time CRM** — *ICP:* field/outside sales + anyone who hates CRM entry; buyer RevOps. *Pain:* hated data entry → dirty CRM → bad forecasting. *Wedge:* post-meeting voice log (one JTBD) → full hands-free query + update + schedule. *Pricing:* per-seat add-on to existing CRM, land cheap. *Expansion:* logging → querying → proactive pre-meeting briefings. *Comp:* Attention, Momentum (capture, not voice-command). *Why now:* MCP tool-calling makes "act by voice" reliable. *Hook:* "Talk to your CRM like a chief of staff, hands on the wheel."

**4. Onboarding/activation** — *ICP:* PLG SaaS with activation drop-off; buyer Head of Growth. *Pain:* activation cliff — users never hit aha; docs unread; human onboarding doesn't scale. *Wedge:* voice onboarding for one high-value first-action → activation lift → in-app voice help + re-engagement calls. *Pricing:* per-activated-user or platform fee tied to the activation metric. *Expansion:* onboarding → in-app support → churn-save calls. *Comp:* CommandBar (Amplitude), Chameleon. *Why now:* compression makes RAG-voice latency acceptable. *Hook:* "Your product calls the user and walks them to aha in 3 minutes."

**5. Multilingual concierge** — *ICP:* hospitality, healthcare intake, gov/utilities, global support; buyer CX/Ops. *Pain:* language barriers → abandoned calls, costly human interpreters. *Wedge:* one language pair + one use case (e.g., ES↔EN intake) → more pairs + use cases. *Pricing:* per-minute (interpreter-replacement ROI is obvious). *Expansion:* one pair → many → full multilingual contact center. *Comp:* PolyAI ($750M val, 45 langs), Retell. *Why now:* real-time MT + low-latency RTC are finally good enough. *Hook:* "Two people, two languages, one natural conversation — no interpreter."

**Cross-cutting GTM read:** the market rewards **vertical wedges over horizontal platforms** (PolyAI/Retell/Rime all won by going deep). Alex's two strongest *and* most defensible theses are **#1 and #2** — both sit in his sales/enablement domain, both have funded comps proving willingness-to-pay, and both make crisp post-event content.

---
## STATUS: 3 cycles complete across A/B/C/D. Brief is build-ready.
## Suggested next actions (post-plan): (1) build a minimal ConvoAI+ScaleDown hello-world this week; (2) draft the 2-min pitch + slide; (3) prep the demo-backup video plan.

## How Alex uses this
Pre-build one idea (#1 or #2) Fri night; dry-run the single demo path; test venue WiFi/mic; backup video ready.
