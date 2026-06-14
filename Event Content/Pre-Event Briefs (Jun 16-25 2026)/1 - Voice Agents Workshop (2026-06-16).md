# Research Brief: Voice Agents Workshop — No Coding Skills

**Date:** Tuesday, June 16, 2026, 5:30–8:30 PM ET
**Format:** In-person, hands-on workshop (build-along). Networking over pizza + drinks after.
**Location:** Fabrik DUMBO, 20 Jay St, Suite 218, Brooklyn, NY
**Host / Platform:** Chanl (chanl.ai)
**Organizer:** Dean Grover — Founder/Co-Founder, Chanl ⚠️ (exact title unconfirmed — see Verification Gaps)
**Luma:** https://luma.com/dl1zaw1q
**Prereq:** Familiarity with Claude + a Claude Pro subscription. $100 in Chanl platform credits provided.

---

## The 90-Second Frame

This is a **builder workshop, not a conference** — and the room it draws is the tell. The agenda ("clone your own voice, connect your data, deploy to phone/web/WhatsApp, test for hallucinations, smart human hand-off, all in one evening") is a live demonstration of the single most important thing happening in voice AI right now: **the entire voice-agent stack has commoditized to the point where a non-coder can ship a working, multi-channel, memory-equipped agent in three hours.** Eighteen months ago that was a multi-week engineering project. The "$100 in platform credits" line tells you Chanl is running this partly as top-of-funnel for its own product — that's not a knock, it's the read.

Three layers worth separating as you walk in:
1. **The host's actual product (Chanl).** Despite the "build any voice agent" framing, Chanl's real product is **the testing / observability / training layer** for voice agents — simulate adversarial personas, catch a mishandled scenario, regenerate it as a what-if, regression-test the fix, redeploy. They sit *on top of* the builder platforms (VAPI, Retell, Bland) via MCP, not in competition with them. The workshop teaches you to build; the company sells you the layer that keeps what you built from breaking in production.
2. **The infrastructure being assembled (ElevenLabs, Cartesia, Azure, OpenAI Realtime).** The voices and the real-time loop are now genuinely plug-in components. Latency — once the hard wall — is largely solved at the model layer (sub-40ms TTFA from Cartesia; OpenAI's GPT-Realtime-2 shipped a 128K-context voice model in May).
3. **The unsolved part (reliability, memory, hallucination, hand-off, legal).** Everything *above* the demo. This is where the room's real conversation — and Alex's documentarian edge — lives. The demo always works; the production deployment is where the value and the danger both sit.

**Why it matters for Alex:** This is the cleanest possible artifact for the "full-stack GTM" thesis. A non-technical GTM operator personally shipping a working voice agent that answers customer questions and hands off to a human is *exactly* the kind of cross-the-aisle proof point that lands with hiring managers at AI-native companies. And the topic — voice agents for support/sales orgs — is squarely commercial, not just technical. Dean Grover, as a founder running a hands-on builder community in NYC, is a high-value, low-competition connection (founders running workshops get pitched constantly to *speak*, almost never engaged on *why they built the thing*).

**Best angle to work it:** Document the commoditization, not the build. "I built a working multi-channel voice agent in one evening with no code" is the obvious post — and it's fine — but the *sharper* documentarian angle is what the easy build reveals: **the moat moved.** When building the agent is free, the entire value migrates to the unsexy layer Chanl actually sells — memory, eval, hallucination-testing, hand-off design. That's the post an operator or investor stops scrolling for.

---

## Topics

### Topic 1 — Voice-agent architecture: the STT → LLM → TTS loop (and the platforms that assemble it)

- **Current Events:** The category reorganized around two architectures in 2026. (1) **Vendor-neutral orchestration** — you bring your own speech-to-text (STT), LLM, and text-to-speech (TTS): LiveKit, Pipecat, Vapi, Retell. (2) **Bundled / speech-native** — the platform owns the whole loop: **OpenAI's Realtime API** (declared GA in May 2026, voice-in/voice-out over WebRTC), ElevenLabs Conversational AI, Cartesia Line, Deepgram Voice Agent. The headline shift: OpenAI's **GPT-Realtime-2** shipped with a **128K context window** — directly attacking the "voice agents feel forgetful" problem that plagued the category. Pipecat hit v1.0.0; LiveKit v1.5 added adaptive interruption handling out of the box.
- **Opportunities:** The composable stack means a builder picks best-of-breed per layer — e.g., Deepgram for STT, GPT-5-class model for reasoning, Cartesia/ElevenLabs for the voice — and swaps any layer as it improves. This is what makes a one-evening build possible.
- **Challenges:** With OSS orchestration (Pipecat, LiveKit) "you own the orchestration code, retry logic, barge-in handling, and the pager when something breaks." The demo is easy; owning production reliability is not. Turn-taking / interruption ("barge-in") handling is still where agents feel robotic.
- **Use Cases:** Inbound/outbound phone support, WhatsApp customer service, web chat widgets, appointment booking, lead qualification — the workshop's "deploy on phone, web, or WhatsApp" agenda maps directly onto these.
- **Top Questions:** (1) When does bring-your-own-stack beat a bundled speech-native API like OpenAI Realtime — at what point does the orchestration burden outweigh the control? (2) Where does turn-taking still break first in production?

### Topic 2 — Latency as the core voice-agent constraint

- **Current Events:** Latency was *the* wall and is now largely a solved problem at the model layer. **Cartesia's Sonic Turbo hits sub-40ms time-to-first-audio (TTFA)**; flagship **Sonic-3 ~90ms**. The architectural reason matters: Cartesia is built on **state-space models (SSMs)**, not transformers — SSMs process sequences more efficiently, which is what enables the sub-100ms floor. Azure shipped **Neural HD Flash** voices specifically optimized for low-latency real-time speech-to-speech.
- **Opportunities:** Sub-100ms end-to-end makes voice agents feel conversational rather than like an IVR phone tree. This is the unlock behind the 2026 wave.
- **Challenges:** Model-layer latency is solved; *system-layer* latency (network, tool calls, RAG lookups, hand-off logic) is the new bottleneck. A 40ms TTS doesn't help if a knowledge-base lookup takes 800ms. The constraint moved up the stack.
- **Use Cases:** Real-time phone support where a half-second of dead air loses the caller; live speech-to-speech translation (OpenAI's GPT-Realtime-Translate).
- **Top Questions:** (1) Now that TTS latency is sub-50ms, where does the perceptible lag actually come from in a deployed agent? (2) Is the SSM-vs-transformer distinction something a non-coder builder needs to care about, or is it abstracted away?

### Topic 3 — Memory & RAG for agents (the "remembers past conversations per user" agenda item)

- **Current Events:** 2026 sharpened the distinction between three things that get conflated: **short-term memory** (the current conversation / context window), **RAG** (retrieval of generic external knowledge — your docs/KB), and **long-term memory** (stable, *user-specific* facts and preferences that persist across sessions). The dedicated memory layer is now a funded category — **Mem0 raised $24M** to be "the memory layer for AI"; Letta (the MemGPT team), Zep, and graph-based approaches (Graphiti) compete. MemGPT's original insight — OS-style "paging" of memory in and out of the context window — is now standard.
- **Opportunities:** Per-user persistent memory is what turns a stateless bot into something that feels like it knows the customer ("continuity of user-specific context"). It's a major perceived-quality lever for support/CX.
- **Challenges:** Memory is where hallucination and privacy risk compound — storing distilled "facts" about a user means storing *wrong* facts too, and replaying them confidently. Memory + voice biometrics is also a legal surface (see Topic 6).
- **Use Cases:** A returning support caller the agent already knows; an agent that recalls a prior unresolved ticket without the customer re-explaining.
- **Top Questions:** (1) For a support agent, where's the line between RAG (look it up fresh) and long-term memory (remember it) — what belongs in which? (2) How do you stop an agent from confidently replaying a wrong "remembered" fact?

### Topic 4 — Voice cloning (the "clone your own voice or pick a provider" agenda item)

- **Current Events:** Voice cloning is now a one-click consumer feature. **ElevenLabs** is the category leader in B2B voice cloning; **Cartesia, Azure Custom Neural Voice**, and Microsoft's catalog all offer it. The workshop offers cloning your own voice OR picking from ElevenLabs / Azure / Cartesia — i.e., the build-vs-buy choice is now trivial at the tooling layer.
- **Opportunities:** A branded, consistent agent voice; founders/creators deploying their own voice at scale.
- **Challenges:** This is the **single highest-legal-risk** item on the agenda (see Topic 6). Cloning *your own* voice is clean; the same one-click capability applied to anyone else's is where the litigation is.
- **Use Cases:** Branded support lines, creator/influencer agents, multilingual dubbing in a consistent voice (ElevenLabs Dubbing V2 shipped late May 2026).
- **Top Questions:** (1) For a business deploying a cloned voice, what consent/disclosure scaffolding has to exist before it goes live? (2) Is there a meaningful quality gap left between cloning-your-own vs. a stock premium voice?

### Topic 5 — Hallucination testing & evals for voice agents (Chanl's actual home turf)

- **Current Events:** "Test agents for hallucinations/inaccuracies" is on the agenda because it's the part everyone skips and everyone regrets. A whole eval/simulation category emerged in 2026: **Cekura, Coval, Hamming, Bluejay, Future AGI** — simulation-first testing that generates multi-turn scenarios (interruptions, accents, background noise, edge cases), runs red-team simulations, and monitors production for regressions. Coval's methodology is explicitly borrowed from **Waymo's autonomous-vehicle testing**. An academic benchmark ("Testing the Testers," arXiv 2026) scored the testers themselves — Coval 48.9, Cekura 43.0 — i.e., even the eval tools are imperfect.
- **Opportunities:** Hallucination detection is "non-negotiable for healthcare, lending, and agents under regulatory scrutiny" — which makes eval the gating layer for any serious enterprise deployment, and therefore where durable value (and Chanl's positioning) sits.
- **Challenges:** Voice evals are harder than text evals — you're scoring not just *what* was said but turn-taking, interruption handling, and tone. The benchmarks above show the tooling is still maturing.
- **Use Cases:** Pre-deployment simulation in CI/CD; production-traffic monitoring for drift; "regenerate a mishandled call as a what-if and regression-test the fix" (Chanl's exact pitch).
- **Top Questions:** (1) For a non-coder who just shipped an agent tonight, what's the minimum viable hallucination test before it touches a real customer? (2) Where does eval coverage realistically top out — what classes of failure can't be simulated?

### Topic 6 — The legal surface: voice cloning, biometrics, and the EU AI Act

- **Current Events:** Two hot fronts. (1) **Illinois BIPA litigation** — nine class actions filed in Chicago federal court allege companies ingested broadcasters'/voice-actors' recordings to train "foundational voice models" without written consent; voiceprints are explicitly covered biometric identifiers under BIPA. Nuance: *Carpenter v. McDonald's* found AI-extracted voice characteristics aren't a "voiceprint" unless specific enough to *uniquely identify* the person — so the law is live but contested. (2) **EU AI Act Article 50 takes effect August 2, 2026** — covered providers must mark AI-generated content as machine-readable/detectable, and **deployers must disclose synthetic content at first interaction.** Tennessee's **ELVIS Act** grants a property right in one's voice. 45+ states have deepfake laws.
- **Opportunities:** Compliance-by-design (consent capture, disclosure-at-first-interaction, watermarking) is itself a GTM differentiator for any voice-agent vendor selling into regulated buyers.
- **Challenges:** The rules are fragmented and don't agree across jurisdictions; "deploy a cloned voice agent tonight" and "be compliant in August" are not the same project.
- **Use Cases:** Any production deployment touching EU users after Aug 2; any voice cloning beyond your own consented voice.
- **Top Questions:** (1) For an agent going live this summer with EU exposure, what does the Article 50 "disclose at first interaction" requirement actually look like in a phone call? (2) Does cloning *only your own* voice clear the BIPA/ELVIS risk entirely, or is there still consent scaffolding to do?

### Topic 7 — Smart human hand-off design

- **Current Events:** Hand-off ("escalate to a human when things get complex") is on the agenda because it's the difference between an agent that helps and one that traps customers. Chanl's product surfaces live signals — churn, expansion, risk, intent — to decide "where to deploy AI, where to keep humans."
- **Opportunities:** Good hand-off design is the trust mechanism that makes customers tolerate an agent at all; it's also where the agent can pass *context* (the whole conversation + memory) so the human doesn't start cold.
- **Challenges:** Knowing *when* to hand off is a judgment problem, not a latency problem — too eager and the agent is useless; too reluctant and it's the IVR-from-hell. Detecting frustration/intent in real time is unsolved.
- **Use Cases:** Tier-1 support deflection with clean escalation; sales qualification handing warm leads to a rep with full context.
- **Top Questions:** (1) What's the signal that should trigger a hand-off that teams most often get wrong? (2) When the agent hands off, how much of the memory/context should actually travel to the human?

---

## Companies

### Chanl (chanl.ai) — host
- **What they do:** An AI **training / testing / observability platform for voice (and chat) AI agents.** It sits on top of builder platforms (VAPI, Retell, Bland) via MCP, equips agents with live CRM data + knowledge base + persistent memory + tools, does cross-channel identity resolution (voice/chat/WhatsApp/email), and — the core wedge — simulates adversarial personas to catch failures pre-launch, then "regenerate a mishandled scenario as a what-if, retrain, regression-test, redeploy." Also surfaces live CX signals (churn/expansion/risk/intent). ⚠️ Note a naming collision: the workshop and a blog live at **chanl.ai**, while some related content appears on **channel.tel** — confirm the canonical domain (see Verification Gaps).
- **Recent developments:** Active technical blog (low-resource-language voice AI, multimodal agents, "AI agent frameworks compared 2026"). Running hands-on builder workshops in NYC (this event) with platform credits — classic dev-relations / top-of-funnel motion. ⚠️ No public funding round confirmed.
- **Industry/Space:** AI/ML, Developer Tools, Voice AI infrastructure.
- **Funding stage:** ⚠️ Unconfirmed — presents as early-stage (seed-ish) based on workshop-led GTM and founder-run community, but no round verified.
- **Why it matters for Alex:** The host = the relationship target. A founder running a hands-on community is the highest-leverage, lowest-competition connection in the room. Chanl's positioning (the *reliability* layer, not the builder) is also the sharpest content insight available — it's the literal embodiment of "where the value moves when building gets free."
- **Headwinds:** Crowded eval/observability field (Cekura, Coval, Hamming, Bluejay, Future AGI, Maxim all chasing the same buyer). The "sit on top of VAPI/Retell/Bland" position is dependent on those platforms not absorbing eval natively. Brand/domain ambiguity (chanl.ai vs channel.tel) is a small but real clarity cost.

### ElevenLabs
- **What they do:** Category-leading voice AI — TTS, voice cloning, and now climbing the stack into **Conversational AI / Agents** as a full voice-agent product.
- **Recent developments:** **$500M Series D from Sequoia at an $11B valuation (Feb 2026)** — more than 3x the $3.3B from Jan 2025; a16z quadrupled its check, ICONIQ tripled. Total funding ~$781M across five rounds. **$330M+ ARR in 2025**, targeting double in 2026; NVIDIA (and reportedly Jamie Foxx) on the cap table; eyeing an IPO. Shipped **Dubbing V2 and Music V2** (late May 2026), an "End Call" agent tool, and v3.
- **Industry/Space:** AI/ML, Voice AI infrastructure.
- **Funding stage:** Series D.
- **Recent Funding ($):** 500,000,000
- **Why it matters for Alex:** The bellwether for the whole sector's commercial heat — $11B on voice infra is the macro proof point behind the post. It's also one of the "pick a voice" options in the workshop.
- **Headwinds:** Climbing the stack into agents puts it in competition with the very platforms (Vapi, Retell) that resell its voices; OpenAI Realtime's GA is a direct bundled-stack threat; voice-cloning is the legal lightning rod (BIPA/ELVIS).

### Cartesia
- **What they do:** Low-latency real-time TTS built on **state-space models (SSMs)** rather than transformers; flagship **Sonic** model line.
- **Recent developments:** **Raised $100M in October 2025** and launched **Sonic-3**. Sonic Turbo hits **sub-40ms TTFA**; Sonic-3 ~90ms. Spun out of **Stanford AI Lab** — founders **Karan Goel and Albert Gu**, the researchers behind SSMs (Gu co-authored the Mamba architecture). Sonic-3.5 and Ink-2 now live; available on Amazon SageMaker JumpStart (Feb 2026); Together AI named Cartesia its dedicated enterprise voice model partner.
- **Industry/Space:** AI/ML, Voice AI infrastructure.
- **Funding stage:** ⚠️ Series A/B — $100M Oct 2025 round; exact letter unconfirmed (reported alongside Sonic-3; Series A was March 2025 with Sonic 2.0).
- **Recent Funding ($):** 100,000,000
- **Why it matters for Alex:** The technical-credibility story of the event — the SSM-vs-transformer angle is the one detail that signals Alex understands *why* latency got solved, not just *that* it did. A "pick a voice" option in the workshop.
- **Headwinds:** Going head-to-head with ElevenLabs (10x its capital) and a free-tier OpenAI Realtime; the SSM differentiation narrows as transformer TTS latency also drops.

### Microsoft Azure AI Speech
- **What they do:** Enterprise STT/TTS suite — standard + Custom Neural Voice, real-time and batch synthesis via SDK/REST.
- **Recent developments:** **Neural HD Flash** voices launched for low-latency real-time speech-to-speech (call centers, assistants); Neural HD voices expanding to more regions starting March 2026.
- **Industry/Space:** AI/ML, Enterprise Software, Cloud.
- **Funding stage:** Public (Microsoft).
- **Why it matters for Alex:** The enterprise-incumbent option — the "safe, already-in-the-MSA, compliance-friendly" voice choice. A useful contrast in the room: startups (ElevenLabs/Cartesia) win on quality/latency/dev-experience; Azure wins on procurement and governance.
- **Headwinds:** Generally a half-step behind the specialists on voice quality and latency leadership; the differentiation is the Microsoft enterprise wrapper, not the model.

### (Context company) OpenAI — not a workshop sponsor, but the elephant
- Declared its **Realtime API GA in May 2026** with **GPT-Realtime-2 (128K context voice agent), GPT-Realtime-Translate, GPT-Realtime-Whisper.** The 128K-context voice model directly attacks the "forgetful agent" problem. This is the bundled-stack force reshaping every company above; worth naming in the room even though OpenAI isn't presenting.

---

## People

### Dean Grover — Founder/Co-Founder, Chanl (organizer + likely workshop leader)
- **Known POV / Bio:** ⚠️ Building Chanl as "the platform for AI agents — tools, testing, and observability for customer experience." Background (per ZoomInfo/Crunchbase, not primary-source verified): prior **Co-Founder of Vidlogs**, **CTO at Vimix (Social Video AI)**, and roles/associations spanning Element AI, Paramount, Limbik, Cisco, Redwave Comtech; startup mentor/judge at MassChallenge. A repeat technical founder, video-AI heritage, now in voice/agent infra. ⚠️ Exact current title (Founder vs Co-Founder), whether there's a co-founder, and the career details all need primary-source confirmation — these come from data-broker profiles, not his own pages.
- **Recent activity:** Running this hands-on NYC builder workshop with $100 platform credits (a dev-relations / community-led-growth motion). Chanl's blog is actively publishing builder-oriented technical content (framework comparisons, multimodal agents, low-resource-language voice AI) — plausibly his or his team's editorial voice. ⚠️ Could not confirm recent talks/podcasts via search.
- **Talking Points:**
  - *Personal hook:* ⚠️ None cleanly sourced. Honest fallback: engage on the *teaching* choice — most founders in this space sell, few run free hands-on builds. Ask why he runs the room himself.
  - *Professional hook:* Chanl's positioning as the *reliability/eval* layer rather than another builder. That's a deliberate, contrarian wedge — engage on *why he bet on the testing layer over the build layer* when the build layer is what gets the demos and the hype.
- **Prioritization Signals:**
  - *Prioritize because:* (1) He's the host — highest-leverage relationship in the room. (2) Founder of an early-stage AI-native company in Alex's target zone (could be a hiring lead, an intro node, or just a strong NYC voice-AI relationship). (3) Low competition — hosts get pitched to speak, rarely engaged on their actual product thesis.
  - *De-prioritize because:* If the room is large and he's busy running the build, depth may be limited — get the connection request in and save the real conversation for follow-up.
  - *Open on-site:* (1) Is Chanl raising / hiring on the GTM side? (2) Is the workshop a recurring series (worth being a regular)? (3) What's his read on where the voice-agent value actually concentrates 12 months out — builder, model, or reliability layer?

---

## Signals (last ~60 days, voice-AI space)

- **OpenAI Realtime API → GA (May 2026)** with GPT-Realtime-2 (128K-context voice agent), GPT-Realtime-Translate, GPT-Realtime-Whisper. Severity: HIGH / Confidence: HIGH. The bundled-stack platform shift; the 128K context directly closes the "forgetful voice agent" gap. Relevance: reframes the whole "memory" agenda item — memory is now partly a model feature, not just an external layer.
- **ElevenLabs $500M Series D @ $11B (Feb 2026), $330M+ ARR, IPO-eyeing.** Severity: HIGH / Confidence: HIGH. The macro heat signal; also expanding into agents (Dubbing V2, Music V2, End Call tool, late May).
- **Cartesia $100M + Sonic-3 (Oct 2025); SageMaker JumpStart + Together AI partner (Feb 2026).** Severity: MED / Confidence: HIGH. The SSM low-latency leader scaling distribution.
- **Azure Neural HD Flash low-latency voices + region expansion (March 2026).** Severity: MED / Confidence: MED. Incumbent closing the real-time gap.
- **Illinois BIPA voice-cloning class actions (9 suits, Chicago federal court).** Severity: HIGH / Confidence: HIGH. The legal storm front directly over the "clone your voice" agenda item.
- **EU AI Act Article 50 effective Aug 2, 2026** (mark + disclose synthetic content). Severity: HIGH / Confidence: HIGH. A hard compliance deadline ~7 weeks out for any EU-exposed deployment.
- **Mem0 $24M for the agent "memory layer"; Letta/Zep/Graphiti category forming.** Severity: MED / Confidence: HIGH. Memory is now a funded standalone category — relevant to the "remembers per user" agenda item.
- **Voice-agent eval category consolidating (Cekura, Coval, Hamming, Bluejay, Future AGI, Maxim); "Testing the Testers" arXiv benchmark.** Severity: MED / Confidence: HIGH. This is Chanl's competitive neighborhood — useful context for the host conversation.

---

## Documentarian Angle

**Angle A (sharpest) — "The moat moved."**
When building a working multi-channel voice agent drops to a one-evening, no-code exercise, the value doesn't disappear — it **migrates up the stack** to the parts the demo skips: per-user memory, hallucination eval, hand-off design, and legal/compliance. That's *why* the host (Chanl) sells the reliability layer, not the builder. The post writes itself from the room: "I built a voice agent tonight with no code. The building was the easy part — and that's the whole story."

**Angle B — "Latency was the wall. It's gone. Here's the new wall."**
Sub-40ms TTS (Cartesia/SSMs), 128K-context voice models (OpenAI). The constraint everyone optimized for is solved at the model layer — and the new bottleneck moved to system-level latency (tool calls, RAG, hand-off) and to *reliability*. A cleaner, more technical post for the builder/engineer slice of the audience.

**Angle C — "Seven weeks to compliant."**
The agenda says "deploy tonight." Article 50 says "disclose synthetic content at first interaction" starting Aug 2. The gap between *shipping* a voice agent and *legally operating* one is the under-covered story. Lower priority — risks being a downer/lecture unless framed as an operator's checklist.

Recommend **Angle A** for the personal post; it's the most ownable, most commercial, and most on-thesis for Alex.

---

## Success Signals

1. **Ship the artifact.** Alex personally builds and deploys at least one working voice agent (phone, web, or WhatsApp) by end of night — the proof object for the "full-stack GTM operator who can actually build" content. (hit / partial / missed)
2. **Connect with Dean Grover** — connection request sent and accepted, OR a real in-room conversation about Chanl's reliability-layer thesis. (hit / partial / missed)
3. **Test one operator hypothesis in the room:** does the "moat moved to reliability/memory/eval" framing land with the builders present, or do they push back? (hit / partial / missed)
4. **Surface one non-obvious detail** worth documenting that isn't in this brief (a real failure mode someone hit live, a tool choice, a pricing reality). (hit / partial / missed)
5. **Anti-signal:** If the room is all curious-bystanders and zero operators/builders shipping anything real, or the workshop is a thin product demo dressed as a "build," downgrade Chanl's future events to "attend only if Dean is personally leading." (fired / not fired)

---

## PRE-EVENT CONTENT

### 1. Pre-Event LinkedIn Post — 2 variants

> Note: brief specifies A/B; both share the Angle-A "moat moved" thesis with different hook formulas (one stat-anchored, one contrarian), per the pre-event-content 3-variant rule trimmed to the 2 requested. Stance is lightly held (pre-event, low-license) — opens the tension, doesn't deliver a verdict. Source links go to first comment, not inline.

---

**Variant A — Stat hook (recommended)** — 1,179 / 3,000 chars

Eighteen months ago, building a voice agent that answers customer questions, remembers who's calling, and hands off to a human was a multi-week engineering project.

Tuesday night in DUMBO, the agenda is to build one in three hours. No code.

That's not a workshop gimmick — it's the state of the stack. Text-to-speech latency is down to sub-40 milliseconds (Cartesia, on state-space models). OpenAI shipped a voice model with a 128K-token memory in May. ElevenLabs just raised $500M at an $11B valuation. The pieces are now plug-in components.

Here's the part worth sitting with: when building the agent gets that easy, the agent stops being the valuable thing.

The value moves up — to the parts the demo skips. Does it remember the customer correctly, or confidently replay a wrong fact? Does it know when to stop talking and get a human? Will it pass the hallucination test before it touches a real caller? Is it legal to run after the EU's disclosure rules hit on August 2?

The host of Tuesday's workshop sells exactly that layer — the testing and reliability one — not the builder. Which tells you where they think the value actually went.

If you're shipping voice agents into a support or sales org: where are you spending your time now — building them, or keeping them from breaking?

#VoiceAI #AIagents #ConversationalAI #GTM #AIinfrastructure

---

**Variant B — Contrarian hook** — 1,096 / 3,000 chars

The voice agent is no longer the hard part. That's the uncomfortable read going into Tuesday night.

A no-code workshop in DUMBO is set up to have a room of non-engineers build a working agent — connected to data, with per-user memory, deployed to phone, web, and WhatsApp — in one evening. And it'll work. That's the point.

The stack collapsed into components. Sub-40ms text-to-speech (Cartesia). A 128K-context voice model from OpenAI in May. ElevenLabs at an $11B valuation. Latency — the wall everyone optimized against for two years — is basically gone at the model layer.

So if the build is free, where did the value go?

Up the stack, into everything the three-hour demo doesn't have time for: whether the agent remembers the customer correctly, whether it knows when to hand off to a human, whether it hallucinates a policy that doesn't exist, whether it's compliant when the EU's synthetic-content disclosure rule lands August 2.

Telling detail: the company hosting the build sells the reliability and testing layer — not the builder. The thing they teach you to make in three hours isn't the thing they sell.

For the GTM and support folks here: when agents get easy to build, what's the new moat?

#VoiceAI #AIagents #GTM #ConversationalAI #AIreliabilITY

> ⚠️ Pre-publish source-check: "the host sells the reliability/testing layer" is grounded in Chanl's own public site/blog positioning (eval/observability, "regenerate-retrain-regression-test-redeploy"). Confirm Chanl is the confirmed host and the positioning line is accurate before posting. The $11B / $500M / sub-40ms / 128K / Aug-2 facts are all sourced (see Signals).

---

### 2. Connection-Request Notes — Dean Grover (Founder/Co-Founder, Chanl)

> Free-tier 200-char hard cap. Two variants anchored to materially different signals. No greeting, no self-intro, no CTA — the request IS the CTA.

**Variant A — Host-curation / product-thesis anchored** (Pattern 3) — 191 chars
Signal anchored: Chanl positions as the testing/reliability layer, not another builder — and you run the build night yourself.
> You run a no-code build night but sell the reliability layer, not the builder. That's a deliberate bet that the value moved off the build. Curious what convinced you the moat is eval, not the agent.

Rubric score: 86/100
Pattern: Pattern 3 (host-curation angle)

**Variant B — Adjacent-work anchored** (Pattern 2) — 188 chars
Signal anchored: Founder background in video AI (Vidlogs / Vimix) now pivoted into voice/agent infrastructure. ⚠️ background unverified.
> You went from video AI (Vidlogs, Vimix) to the testing layer for voice agents. Curious what carried over — and what didn't — moving from generating media to keeping conversational agents from breaking.

Rubric score: 81/100
Pattern: Pattern 2 (adjacent-work angle)
> ⚠️ Variant B depends on the Vidlogs/Vimix history, which is sourced only from ZoomInfo/Crunchbase — verify on his own LinkedIn before sending, or default to Variant A (which needs no biographical claim).

---

### 3. Prepared Questions (for the hands-on session / networking)

**For Dean Grover / the Chanl team:**
1. **The moat question** — "You teach people to build an agent in an evening but the product is the testing-and-reliability layer. Where do you think the durable value actually concentrates 12 months out — the builder, the model, or the reliability layer?" *(angle: surfaces his real thesis; the whole event is downstream of this answer.)*
2. **Eval minimum** — "For someone who just shipped an agent tonight, what's the *minimum* hallucination test before it touches a real customer — and what failure class can't be caught by simulation at all?" *(angle: practical + signals you know eval has limits; ties to the "Testing the Testers" reality.)*
3. **Memory vs. RAG line** — "For a support agent, where's the line between RAG'ing a fresh answer and *remembering* it as a per-user fact — and how do you keep it from confidently replaying a wrong memory?" *(angle: the per-user-memory agenda item, pushed one layer past the demo.)*

**On hand-off design (ask if it comes up live):**
4. "What's the hand-off trigger teams most often get *wrong* — handing off too early, too late, or not passing enough context to the human?" *(angle: hand-off is the trust mechanism; this is the operator's real question.)*

**On latency / architecture:**
5. "Now that TTS is sub-50ms, where does the perceptible lag in a deployed agent actually come from — and does a non-coder builder need to care about the SSM-vs-transformer distinction, or is it abstracted away?" *(angle: shows you know latency moved up the stack; Cartesia/SSM detail signals depth.)*

**On the legal surface:**
6. "For an agent going live this summer with any EU exposure, what does Article 50's 'disclose synthetic content at first interaction' actually look like inside a phone call?" *(angle: the seven-weeks-to-compliant gap; operator-grade, not academic.)*

**On voice cloning:**
7. "Does cloning *only your own* voice clear the BIPA/ELVIS risk entirely, or is there still consent scaffolding to do before a cloned voice goes into production?" *(angle: the highest-legal-risk agenda item, asked precisely.)*

---

### 4. Visual Carousel Brief

## Visual Brief — 4-slide carousel (Arc: Arc 3 — Before → After → What Changed → So What)

**Carousel thesis:** Building a voice agent went from a multi-week engineering project to a one-evening no-code build — and that collapse pushed all the value up to the reliability layer (memory, eval, hand-off, compliance) that the demo skips.

**Slide count:** 4
**Aspect ratio:** 4:5 (1080x1350) — LinkedIn carousel default
**Tool routing summary:** All 4 → Gamma (`format: social`, 4:5, Stratos dark theme, `imageOptions.source: noImages`). Slides 1–2 are paired before/after frames; Slide 3 is a stat strip; Slide 4 is the "where value moved" diagram. Canva typography fallback only if Gamma over-designs.

---

### Slide 1 of 4 — Before: the world 18 months ago

- **Visual mode:** Diagram (stacked build timeline) — paired frame with Slide 2
- **Headline:** "Building a voice agent: ~6 weeks"
- **Body / content:** A vertical stack of the work it used to take: Wire STT → Tune LLM → Integrate TTS → Build memory store → Telephony plumbing → Test & deploy. Label the whole stack "Engineering project." Time tag: "≈ multiple weeks, dedicated engineers."
- **Palette:** dark slate bg + off-white text + blue accent (#1E40AF) on the "≈ weeks" tag
- **Source attribution:** none (framing slide)
- **Alt text:** A six-step vertical stack showing the multi-week engineering effort a voice agent used to require.
- **Tool:** Gamma (Canva fallback)

### Slide 2 of 4 — After: the world now

- **Visual mode:** Diagram — IDENTICAL frame to Slide 1 (same axis, same layout), transformed
- **Headline:** "Same agent: one evening, no code"
- **Body / content:** The same six layers, now collapsed into plug-in component chips (STT · LLM · TTS · Memory · Telephony) feeding one box: "Working multi-channel agent." Time tag: "≈ 3 hours, no engineers." Frame must visually mirror Slide 1 so the collapse is legible at a glance.
- **Palette:** same dark slate + off-white + blue accent (#1E40AF) on the "≈ 3 hours" tag — identical assignments to Slide 1
- **Source attribution:** none (framing slide)
- **Alt text:** The same six layers from the prior slide, collapsed into plug-in components producing a working agent in three hours.
- **Tool:** Gamma (Canva fallback)

### Slide 3 of 4 — What changed: the constraint that broke

- **Visual mode:** Single-stat strip (three numbers, one row)
- **Headline:** "Latency stopped being the wall"
- **Body / content:** Three stat callouts left-to-right: **"<40ms"** (TTS time-to-first-audio, Cartesia / state-space models) · **"128K"** (token memory in OpenAI's GPT-Realtime-2 voice model, May 2026) · **"$11B"** (ElevenLabs valuation, Feb 2026). One-line undercaption: "The components got fast, cheap, and fundable."
- **Palette:** dark slate + off-white + green accent (#059669) on the three numbers (data/infrastructure topic)
- **Source attribution:** "Sources: Cartesia; OpenAI; TechCrunch, 2025–2026"
- **Alt text:** Three statistics — sub-40ms TTS latency, 128K voice-model context, and ElevenLabs' $11B valuation — showing the voice stack matured.
- **Tool:** Gamma

### Slide 4 of 4 — So what: where the value moved

- **Visual mode:** "Where the value moves" diagram (arrow from a shrinking box to a growing box)
- **Headline:** "When the build is free, the moat moves up"
- **Body / content:** Left box, shrinking/grayed: "BUILD — STT/LLM/TTS/telephony (commoditized)." Arrow pointing up-right to a larger accented box: "RELIABILITY — per-user memory · hallucination eval · hand-off design · compliance (Aug 2 EU disclosure)." One-line closer beneath: "The thing you build in an evening isn't the thing worth selling."
- **Palette:** dark slate + off-white + amber accent (#D97706) on the "RELIABILITY" box (business/GTM topic)
- **Source attribution:** none (synthesis slide)
- **Alt text:** A diagram showing value moving from a shrinking commoditized "build" box to a growing "reliability" box covering memory, eval, hand-off, and compliance.
- **Tool:** Gamma (Canva typography fallback)

---

**Quality gate checks:**
- Arc fit: pass — before/after/what-changed/so-what maps cleanly to the commoditization thesis.
- Job differentiation: pass — Slide 1 (old cost), Slide 2 (new cost), Slide 3 (why it changed), Slide 4 (consequence). No two interchangeable.
- Frame parallelism (Arc 3): pass — Slides 1 and 2 specified as identical frames so the collapse reads instantly.
- Thumb test per slide: pass — every headline ≤8 words, one idea per slide.
- Source citations: pass — Slide 3 (the only data slide) carries a source line.
- Adds information (not repetition): pass — no slide re-prints post copy; all four carry structure/stats/diagram the text doesn't render.
- Final slide earns the swipe: pass — Slide 4 is the synthesis ("the moat moved"), not housekeeping.

---

## Verification Gaps

- ⚠️ **Dean Grover's exact title** (Founder vs Co-Founder) and **whether Chanl has a co-founder / other organizer** — unconfirmed. His own LinkedIn was not directly openable (WebFetch blocked); title language is from data-broker snippets (ZoomInfo/Crunchbase).
- ⚠️ **Dean Grover's career history** (Vidlogs co-founder, Vimix CTO, Element AI / Paramount / Limbik / Cisco / Redwave, MassChallenge mentor) — sourced only from ZoomInfo/Crunchbase aggregator snippets, not his own pages. Verify before using in Connection Variant B. Variant A is the safe default (no biographical claim).
- ⚠️ **Chanl domain ambiguity** — the workshop + blog appear at **chanl.ai**, but related "Turn customer conversations into decisions" / framework-comparison content surfaced under **channel.tel**. Confirm the canonical domain and that they're the same company before citing publicly.
- ⚠️ **Chanl funding/stage** — no public round confirmed; "early/seed-stage" is inferred from workshop-led GTM and founder-run community, not verified.
- ⚠️ **Cartesia's exact Series letter** for the $100M Oct 2025 round — reported alongside Sonic-3; Series A (with Sonic 2.0) was March 2025, so the $100M is likely Series B but the letter wasn't explicitly confirmed in results.
- ⚠️ **"Jamie Foxx on the ElevenLabs cap table"** — appeared in one secondary source; treat as unverified gossip, do NOT use in public content. The $500M/$11B/Sequoia/a16z/ICONIQ/NVIDIA facts are well-sourced (TechCrunch, CNBC, ElevenLabs blog).
- ⚠️ **"Chanl sells the reliability/testing layer, not the builder"** is used as a thesis claim in the LinkedIn post — it's grounded in Chanl's own public site/blog positioning, but per Rule 12, confirm the host identity and the positioning line are accurate at event time before posting (the host being Chanl is stated by the brief but should be reconfirmed against the Luma page).
