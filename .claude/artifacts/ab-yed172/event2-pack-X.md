# PACK X

# Prior-Context Pack — AI Builders Session: Open Models, Model Routing & API Integration (2026-09-24)

## How to use this pack (for every downstream reader)
Prior knowledge = starting context + leads to verify. Treat KNOWN as a foundation to build on, STALE and UNVERIFIED as leads to refresh/confirm via fresh web search. NEVER restate an UNVERIFIED item as fact in research or content. This pack does not replace research — it aims it. **This event is unusually thin on prior context**: all three named entities (3percentclub, Fractal NYC, Maria Ashby) are pure-NEW with zero prior record, and the closest-matching topic record (Model Routing & AI Gateways) is a near-stub. Most of the aiming here has to come from the three topic cards and the cross-cutting market signals, not from entity continuity.

## Continuity Ledger (the arc — for synthesizer + signal-scanner)
- **No prior event brief exists for 3percentclub, Fractal NYC, or Maria Ashby** — this is a first-contact event for all three named entities. There is no "what we covered before about this series" to draw on at the entity level.
- Topic-layer continuity only:
  - Self-hosted inference economics (TCO vs. API pricing, sovereignty, MLOps maturity) was covered from **[Event: "LLM Knowledge Bases, AI Memory, and more," 2026-05-11]** — `STALE` (4.5 months old), a candidate re-grounding lead rather than current state.
  - "Put a router/gateway in front of your models" as an enterprise pattern surfaced at **[Marketing Engineer Meetup, 2026-06-09]** and **[ScaleDown event, 2026-06-26]** — `STALE` (~3 months old), and the topic record itself carries no "Last Updated" date, no body, and no analytical fields — treat as a near-empty record, not an established position.
  - Open-weight model competitiveness (cost/efficiency gains vs. closed models) has an active, twice-updated trend line (Aug 6 → Sep 8, 2026) — the freshest thread in this pack.
- **Angle worth flagging to the synthesizer (observation, not a sourced fact):** the workshop's own content — routing decisions (which model for which task), prompt-caching mechanics, and "task sizing against compute budgets" — is structurally about *verifying model/task fit before you commit spend*, which sits close to Alex's running documentarian thread ("verification is the bottleneck"). This is a framing suggestion for the room, not a prior-knowledge claim — the synthesizer should treat it as an angle to listen for live, not a thesis to assert.
- No arc-narrowing note is possible beyond this — there's no multi-event history on this host/company pair to show a narrowing pattern.

## Company Cards (for company-researcher + competitive-signal-scanner)
### 3percentclub — prior path: NEW, no record
No prior Companies record exists. Nothing to carry forward as prior knowledge. The invite itself (not prior knowledge — the verbatim source, already in the specialists' hands) describes it as a nonprofit focused on "increasing diversity in tech by providing underrepresented talent with accessible education," running this session as part of its AI Architects Fellowship Builders Track ahead of an October Civic Hackathon — that's a fresh-research starting point, not a conditioned fact.
- **Refresh leads:** confirm org structure/funding model, prior cohorts/fellowship outcomes, and any NYC AI-education ecosystem overlap (e.g., with Fractal NYC) via fresh web search.

### Fractal NYC — prior path: NEW, no record
No prior Companies record exists. No prior knowledge to carry.
- **Refresh leads:** identify what Fractal NYC is (community, studio, dev collective?) and its relationship to 3percentclub as co-host — pure fresh research.

## People Cards (for person-researcher)
### Maria Ashby — [Host]
No prior People record exists. **Name-collision guard:** a search surfaced only **Maria Morin** (EliseAI, from an April 2026 event) — a *different* person. Do not inherit any bio/title/pronoun detail from that record; it does not describe this Maria Ashby. This mirrors the standing Tanny Kang pronoun-inheritance caution in project memory — treat name-matches with the same skepticism.
- **Refresh leads:** confirm role/title at 3percentclub or Fractal NYC, and whether she's a fellowship instructor, program lead, or community organizer — all fresh research, zero prior basis.

## Topic Cards (for topic-landscape-analyst)

### Self-Hosted AI Inference — prior path: REFRESH (Last Updated 2026-05-11 → 136 days old)
- Sovereign-AI/data-residency tailwind (EU AI Act provenance rules), Ollama >100K GitHub stars, Groq LPU narrowing the cloud/self-host latency gap, AI Alliance "Project Tapestry" (federated training, April 2026) — `STALE` `[Topics: Self-Hosted AI Inference, prior brief "LLM Knowledge Bases, AI Memory, and more" · 2026-05-11]`
- Opportunities on file: data-residency compliance demand, cost economics at high-volume workloads, easier fine-tuned-model deployment, narrowing open-vs-frontier quality gap, sovereign-AI procurement tailwind — `STALE`, same source/date
- Challenges on file: MLOps capability gap, lagging reasoning quality, GPU cost/availability, self-hosted ≠ automatically more secure, manual upgrade/versioning burden — `STALE`, same source/date
- Use cases on file: regulated industries, high-volume/latency-sensitive inference, domain fine-tunes, air-gapped/defense, EU sovereign deployments — `STALE`, same source/date
- Top questions on file: TCO breakeven volume, model-version upgrade handling, minimum MLOps maturity bar — `STALE`, same source/date
- **Refresh leads:** this record predates the Ollama-via-workshop framing entirely — re-verify GitHub star count, whether Groq's latency claims still hold, and whether the EU AI Act provisions referenced actually took effect as described (data-provenance rules are a common source of misstatement). Given tonight's workshop runs Ollama hands-on, this is the single highest-value re-grounding target in the pack.

### Open-Weight LLMs — prior path: REFRESH (Last Updated 2026-09-08 → 16 days old)
- Body/definition on file: "the open-weight model layer (inference) — distinct from open-source AI infrastructure… the race among open frontier models (DeepSeek, Mistral, Qwen, GLM, Kimi)" — `KNOWN` `[Topics: Open-Weight LLMs · 2026-09-08]` (positioning-style framing language but descriptive of the field, not a firm/person thesis — carried as KNOWN given recency, still worth a light re-check)
- Trend Radar 2026-09-08 (3 sources: HN + HF + newsletters, confidence 0.98): Mistral raised €3B "to push sovereign open-weight AI to frontier"; GLM-5.3 + Qwen3.8-27B top HF trending; NYT covered corporate open-source-AI adoption — `KNOWN` `[Trend Radar · 2026-09-08 · https://mistral.ai/news/mistral-makes-sovereign-open-weight-ai-to-frontier/]`
- Interpretive claim "open winning token volume, closed still winning revenue" — `UNVERIFIED` (market-sentiment framing, no primary source cited beyond the Mistral funding link) `[Trend Radar · 2026-09-08]` — do not restate as fact; useful only as a question to test live.
- Trend Radar 2026-08-06 (3 sources, confidence 0.90): DeepSeek V4-Flash beat its own Pro tier on all 9 agent benchmarks; Mistral ShieldStral 3B matched 7x-larger models; HF's CEO stated China is dominating open models — `KNOWN` `[Trend Radar · 2026-08-06 · https://deepseek.ai/blog/deepseek-v4-flash-ga-agent-benchmarks]` (the HF-CEO attribution is a quoted opinion — treat that specific line as `UNVERIFIED` even though the record overall is fresh)
- Opportunities / Challenges / Use Cases / Top Questions — **all empty on this record.** No fabricated content; this is a genuine gap, not an omission.
- **Refresh leads:** Qwen and DeepSeek are named directly in tonight's workshop (via Ollama/OpenRouter) — verify current DeepSeek/Qwen benchmark standing is still accurate as of 09-24 (this field moves in days, not months), and pressure-test the "open winning volume, closed winning revenue" framing against anything said in the room.

### Model Routing & AI Gateways — prior path: REFRESH, but record is a near-stub (Last Updated: not set)
- Only populated field: signal from **Marketing Engineer Meetup (2026-06-09)** + **ScaleDown event (2026-06-26)** — pattern is "put a routing/gateway layer in front of LLMs so models swap without re-plumbing" (Vercel AI Gateway named; Haiku for cheap steps / Opus for reasoning as a worked split); enterprises reportedly want internal routers over OpenRouter dependence; ScaleDown's classifier SLMs referenced as feeding that routing decision — `STALE` (~90–107 days old, and the record has no Last-Updated date at all, so true age is unconfirmed) `[Topics: Model Routing & AI Gateways — no url captured in the pull]`
- Body: blank. Opportunities / Challenges / Use Cases / Top Questions: **all empty.** Two prior linked events exist on this record but neither was named or dated in this pull — genuine gap, flagged rather than guessed at.
- **Refresh leads:** this is, by title, the topic closest to tonight's actual content (the workshop explicitly teaches Opus-for-planning / Sonnet-or-Qwen-for-execution routing) — yet it's the thinnest record in the pack. High-value target for the topic-landscape-analyst to rebuild essentially from scratch tonight: what's the current enterprise appetite for internal routers vs. OpenRouter, and does ScaleDown's classifier-SLM approach still hold as a live pattern.

## Graph Signals (cross-cutting — for signal-scanner + synthesizer)
Recent market/funding/launch signals judged relevant to tonight's open-weights/routing/cost theme (20 of 43 recent signals were flagged relevant in the pull; the items below are the ones with direct bearing on this event's content — see Audit for what was cut):
- 2026-09-08 · market · **Open-Weight LLMs – rising** (Mistral €3B, GLM-5.3/Qwen3.8-27B trending, NYT open-source-AI coverage) — `KNOWN` `[graph · 2026-09-08 · confidence n/a]`
- 2026-09-08 · funding · **Mistral — €3B (~$3.5B) Series D, Samsung-led, €21B valuation** (a16z / NVIDIA / Salesforce Ventures participated) — `KNOWN` `[graph · 2026-09-08]`
- 2026-09-08 · market · **Frontier Model Releases (GPT-6 / Gemini / Fable) – rising** — compressing release cadence — `KNOWN` `[graph · 2026-09-08]`
- 2026-09-04 · launch · **OpenAI GPT-6 Astra** — 1.05M-token context, first model at "Critical" cybersecurity tier (enterprise access off by default) — `KNOWN` `[graph · 2026-09-04]`
- 2026-09-08 · market · **Cloud Sandboxes for AI Agents – rising** — Daytona forkable sandboxes, FreeToken edge-MoE serving, **Cerebras running Qwen3.8 at 1500 tok/s**, TPU InferenceX — `KNOWN` `[graph · 2026-09-08]` — the Cerebras/Qwen throughput figure is directly relevant to tonight's "task sizing against compute budgets" lab content.
- 2026-08-07 · market · **Mistral ShieldStral** — 3B open-weight multimodal moderation model (480 HN pts) — `KNOWN` `[graph · 2026-08-07]`
- 2026-09-08 · market · **OpenAI Navier-Stokes proof claim** — disputed by NYU's Tristan Buckmaster over training-data provenance — `UNVERIFIED` (an active dispute, not a settled result) `[graph · 2026-09-08]` — tangential to tonight but a live "verification is the bottleneck" data point if the synthesizer wants it.

Snippet-only newsletter leads (subjects/snippets only — no bodies retrieved, so treat every line below as a headline-level lead, not a fact):
- SemiAnalysis 09-23, "ClusterMAX 3.0" GPU cloud rating system — `UNVERIFIED` (snippet only) `[Gmail · 2026-09-23]`
- tokens& Weekly 09-23, "GPT-6 and Claude 5.5: The Price of Intelligence Crashes" — `UNVERIFIED` (snippet only) `[Gmail · 2026-09-23]`
- SemiAnalysis 09-18, "Engrams… DRAM/SSD Offloading" (DeepSeek V4.1 Flash architecture) — `UNVERIFIED` (snippet only) `[Gmail · 2026-09-18]`
- genai.works 09-22, "Alibaba is building AI without Nvidia" — `UNVERIFIED` (snippet only) `[Gmail · 2026-09-22]` — directly relevant given Qwen (Alibaba's model family) is named in the invite.
- superhumancode 09-22, "Chinese phone makers enter AI race… run agents 24/7 on your own server" — `UNVERIFIED` (snippet only) `[Gmail · 2026-09-22]`
- marketsentiment 09-17, "The next great AI trade is everything that isn't AI" ("cheap intelligence into durable margin") — `UNVERIFIED` — this is explicit market-thesis framing, flagged per Rule 12 regardless of source confidence `[Gmail · 2026-09-17]`
- Pragmatic Engineer 09-22, "How will AI change operating systems? Part 2: Windows" (local models, agent-friendly OS) — `UNVERIFIED` (snippet only) `[Gmail · 2026-09-22]`

If empty: N/A — graph signals were present in this pull.

## Audit
- **Conditioning confidence: Medium.** Two of three topic records carry real substance (Self-Hosted AI Inference, Open-Weight LLMs), and the market-signal layer is current and directly on-theme. But confidence is capped at Medium because: (1) zero prior record exists for any of the three named entities in this event — company-researcher and person-researcher get no head start; (2) the topic closest to the event's actual title, Model Routing & AI Gateways, is functionally a stub (no body, no dated "Last Updated," no analytical fields); (3) no prior event brief bodies were retrieved at all, so the Continuity Ledger has no direct entity-level arc to draw on.
- **Dropped as not-relevant** (pulled but excluded from this pack):
  - ChinaTalk 09-18, "How Chinese AI Radicalizes" — political/governance framing, not applied-engineering content relevant to a routing/API-integration workshop.
  - The Batch/DeepLearning.AI 09-18, "Who's Responsible for Irresponsible AI?" — AI-safety governance, off-theme for tonight's hands-on content.
  - AI Collective 09-21, "Meta's Agent Made Up Its Own Privacy Policy" — agent-hallucination governance story, not about open-weights/routing/cost.
  - Bond AI NY 09-24 digest — generic NYC events aggregator, no event-specific fact to carry.
- **Coverage gaps (pure-NEW, web-search from scratch tonight):**
  - **3percentclub** — no Companies record. Nonprofit/fellowship-program framing only known from the verbatim invite (not prior knowledge).
  - **Fractal NYC** — no Companies record at all; nothing known about its nature or relationship to 3percentclub beyond "co-host."
  - **Maria Ashby** — no People record; confirmed NOT the same person as Maria Morin (EliseAI) despite shared first name — do not inherit any attribute across that name match.
  - **No prior event briefs** exist for this host/company pairing — the Continuity Ledger above is topic-only, not entity-anchored.
  - **Model Routing & AI Gateways** topic record's two linked prior events are unnamed and undated in this pull — a gap in the record itself, not something this conditioning pass can resolve.
