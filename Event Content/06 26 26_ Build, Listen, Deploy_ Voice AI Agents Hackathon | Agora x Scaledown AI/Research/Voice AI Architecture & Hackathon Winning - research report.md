# Voice AI Architecture & Hackathon Winning — Research Report
_Compiled 2026-06-21 for the Agora × ScaleDown Voice AI Agents Hackathon._

## 1. Latency budget — the 800ms target
- **Target <800 ms** end-to-end mouth-to-ear for natural feel; production median today 1.4–1.7 s; **>3 s feels broken**; humans expect 200–300 ms.
- Component budget (typical → optimized): STT 200–400→100–200 ms · LLM 300–1000→200–400 ms · TTS 150–500→100–250 ms · network 100–300→50–150 ms · turn detection/VAD 200–800→200–400 ms · overhead 50–200→20–50 ms. End-to-end 1000–3200→**670–1450 ms**.
- **LLM ≈ 70% of latency → model selection is the #1 lever.**
- Best-in-class (2025–26): Deepgram Nova-3 STT 150 ms · ElevenLabs TTS 75 ms first-byte · Cartesia Sonic 3 Turbo 40–90 ms · OpenAI Realtime 300–500 ms speech-to-speech.

## 2. Turn detection / endpointing / barge-in
- **VAD (Silero):** neural speech/silence per frame, threshold ~0.7, hysteresis (end threshold 0.15 below start). Robust to noise; needs per-environment calibration.
- **STT endpointing:** uses punctuation/phrase-completeness (Deepgram, AssemblyAI) — fastest default.
- **Semantic turn detection:** small classifier/LLM on partial transcript predicts completeness; fires before trailing silence; higher accuracy, more compute (FastTurn, arxiv:2604.01897).
- **Barge-in:** keep turn detection active during agent speech; **TTS must stop within ~60 ms** of detected user speech or it feels ignored. Client-side echo cancellation filters agent audio.
- **Backchannels/fillers:** brief "mm-hmm"/"let me check…" mask latency; GPT Realtime ~16% filler rate (healthy) vs pathological 88%.

## 3. Stream everything
- Sequential pipeline kills latency. Stream ASR partials → LLM consumes tokens → TTS starts from first chunk.
- **Sentence-chunk TTS:** buffer LLM tokens to first sentence boundary, synthesize immediately → first audio sub-300 ms even on long responses.
- Aim RTF < 1.0 across all three components.

## 4. Small/fast models (SLMs)
- SLMs handle 80–90% of voice subtasks (intent, routing, extraction, light summarization) at 10–100× lower cost, lower latency, more deterministic.
- Options: **GPT-4o-mini** (~200–400 ms TTFT), **Llama 3.1 8B via Groq** (50–100 ms, ~2200 tok/s, text-only), Llama 4 Scout, Mistral Voxtral Mini (<200 ms).
- Infra: Groq LPU (~160–190 ms TTFT), Cerebras wafer-scale. Pair Groq (text) with Deepgram STT + Cartesia TTS.
- **Fewer input tokens = faster TTFT** → prompt compression (LLMLingua-2 up to 20×/3–6× faster) is a real latency lever for agent workloads.

## 5. Demo failure modes & live tactics
- 60% of voice agents fail demo→production. Watch: latency degrades 40–120% under load; STT accuracy drops 10–25% in real noise; model drift; hallucination 3–5× higher on unseen input; telephony fails at scale; multi-turn state breaks; observability gaps.
- WiFi adds 50–100 ms; echo >150 ms is disorienting; **cold start 2–5 s on first call** (do a throwaway warm-up call before pitching).
- Tactics: AirPods Pro / headset w/ noise isolation; **test in the venue 15 min before**; scope to ONE happy-path 60–90 s; **pre-record a 2–3 min backup video**; offline/pre-loaded context (no live RAG network calls); simple SLM over big model.

## 6. Hackathon winning & networking
- **Universal rubric:** Innovation · Technical execution · **Sponsor-tech alignment** · Demo clarity · Viability/business fit. Red flags: incomplete submissions, recycled ideas, polish over function.
- **Team formation (1–3 hr):** define ONE core feature; roles = 1 core coder, 1 integrations, 1 demo/pitch lead; diverse skills. Scope creep kills hackathons.
- **2-min pitch:** 0–10 s intro+names · 10–30 s problem+impact · 30–90 s demo+technical highlights · 90–120 s close/ask. Judges remember beginnings + endings.
- **Sponsor prizes:** judged independently; enter ≤2 sponsor challenges + grand prize; **namedrop sponsor tech** in pitch; native integration > shoehorned add-on.
- **Networking (first-timer):** get sponsor + judge list early; attend sponsor tech talks; ask *technical* questions ("how do you handle interruption / what's your TTFT budget?"); VCs scout for technical founders who solve real problems.

## 7. Voice AI GTM traction (2025–26)
- Market $18.4B (2025) → $61.7B (2031), 22.4% CAGR. VC funding $315M (2022) → **$2.1B (2025)**, ~7×. Enterprise production +340% YoY; 78% of top-50 banks have production voice agents.
- **22% of latest YC class** building voice; 69% B2B, 18% healthcare, 13% consumer. Typical entry = wedge (small % of call types), then expand.
- Hot verticals + players: Sales/SDR (Qualified/Piper, 11x — replaces 2–3 SDR FTEs/AE) · Financial (**PolyAI** — $86M Series D Dec 2025, $750M val, 2000+ deployments, 391% ROI, $10.3M avg savings) · Healthcare (**Retell AI** — 300%+ QoQ, $40M+ ARR; Retell Assure monitors 100% of calls) · Support/QSR (**Rime** — $5.5M seed, 100M+ calls/mo, Domino's/Wingstop) · Roleplay/coaching (Hyperbound, Sesame, Mindtickle) · Multilingual (ElevenLabs 70+ langs, PolyAI 45).
- **Strategic read:** vertical specialization >> horizontal platforms; wedge strategy scales faster than full automation; pricing compressing (OpenAI cut input 60% / output 87.5%) → winners differentiate on domain models + QA.

## 8. Frameworks (reference, beyond Agora)
- **Pipecat** (Python, v1.0 Apr 2026) — best for hackathon velocity, 60+ integrations (Deepgram/ElevenLabs/Cartesia/OpenAI/Claude/Groq/LiveKit). `pipecat-ai/yc-voice-agents-hackathon` starter.
- **Vapi** (no-code/API) — provider-agnostic, swap mid-build, ~500 ms.
- **OpenAI Realtime API** — easiest hello-world, 300–500 ms, limited customization.
- **LiveKit Agents** — production WebRTC, steeper curve.

## 9. Build stack recommendation
ConvoAI spine (this event) or Pipecat + **Deepgram Nova-3 STT + gpt-4o-mini or Llama-3.1-8B@Groq + Cartesia/ElevenLabs TTS**. Pre-load context, one happy path, instrument and log TTFT so you can say the number, backup video ready.

## Confidence
- High: latency budgets, turn-detection techniques, streaming benefits, market/funding trends, SLM performance.
- Medium: exact TTFT ranges (vary by load/region), semantic turn-detection maturity, filler rates.
- Low: long-term post-price-compression economics, which framework dominates by 2027, exact per-vertical ROI.

## Key sources
Hamming AI (voice latency, 4M+ calls) · LiveKit (turn detection) · Deepgram (low-latency, Flux, TTS chunking) · Twilio · a16z AI voice agents 2025 · AssemblyAI voice-AI-2026 · Retell/PolyAI/Rime announcements · Pipecat + LiveKit docs · Devpost/TAIKAI hackathon-pitch guides · Gradium semantic VAD · arxiv 2508.04721, 2604.01897.
