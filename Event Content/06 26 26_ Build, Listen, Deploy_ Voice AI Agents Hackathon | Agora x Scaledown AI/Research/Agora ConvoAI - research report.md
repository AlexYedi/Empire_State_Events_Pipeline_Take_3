# Agora Voice AI Hackathon — Research Report (Agora stack)
_Compiled 2026-06-21 for the Agora × ScaleDown Voice AI Agents Hackathon (Jun 26–27, NYC)._

## 1. Agora Conversational AI Engine (ConvoAI) — core capabilities
Real-time voice AI platform that orchestrates ASR (speech-to-text), LLM, and TTS into natural, low-latency conversations. You provide a channel, LLM endpoint, and agent config; Agora handles audio transport, noise filtering, turn-taking, and interruption.

**You provide vs. Agora provides:**
- You: LLM API keys & endpoint, ASR/TTS vendor choice + config, system prompt/greeting/agent logic, web client UI (JS).
- Agora: orchestration, token auth, channel management, real-time audio transport (SD-RTN), interruption handling, noise suppression, echo cancellation, VAD, millisecond-level latency pipeline.

**Agent join flow:** `POST /api/conversational-ai-agent/v2/projects/{appid}/join` → agent enters channel as a UID → listens to subscriber UIDs → responds via RTC audio + RTM transcripts. Backend generates RTC + RTM tokens; client joins channel + publishes mic; client calls invite-agent with LLM/ASR/TTS config.

## 2. Supported vendors
- **ASR:** Agora ARES (default), Microsoft Azure, Deepgram, OpenAI Whisper, Google Cloud STT, AWS Transcribe.
- **LLM:** OpenAI (GPT-4o, GPT-4o-mini — primary), Azure OpenAI, xAI, custom/self-hosted (any HTTP callback URL), Google Gemini.
- **TTS:** Microsoft Azure (recommended default), ElevenLabs, OpenAI TTS (Beta), Cartesia (Beta), Hume AI (Beta), Google Cloud TTS, AWS Polly.
- Note: Cartesia/OpenAI TTS/Hume are "Beta." Deepgram is ASR-only in ConvoAI docs.

## 3. Latency benchmarks (published)
- End-to-end response latency: **650 ms** minimum (optimized pipeline).
- Interruption response: **340 ms** minimum.
- Network RTT (SD-RTN): **76 ms median** global; 100–300 ms typical.
- Network resilience: tolerates 80% packet loss + 3–5 s disconnection.
- Perceptual "instant" threshold: 200–300 ms.
- Typical end-to-end with slow vendor choices: **3.5–7.6 s** → vendor choice is the latency lever.
- Claim: 3× faster than major LLM providers' voice mode; >50% latency reduction vs public internet.

## 4. Interruption / barge-in / endpointing / VAD / turn-taking
Agora natively handles these. Config:
- **Start of speech (VAD):** `interrupt_duration_ms` (160 = immediate, 300–500 noisy), `prefix_padding_ms` (~300), `threshold` (0.0–1.0, ~0.5).
- **End of speech:** `mode` `"silence"` (default) or `"semantic"` (AI-based, beta); `silence_duration_ms` (~640 prevents premature cutoff); `max_wait_ms` (~5000).
- **Interrupt:** client `interrupt()` method, or `POST /api/conversational-ai-agent/v2/projects/{appid}/agents/{agentId}/interrupt`.
- Barge-in keeps VAD active during agent TTS; on user speech mid-playback, agent cancels TTS and hands control to STT.

```json
{ "turn_detection": { "mode": "vad", "config": {
  "start_of_speech": { "interrupt_duration_ms": 160, "prefix_padding_ms": 300, "threshold": 0.5 },
  "end_of_speech": { "mode": "silence", "silence_duration_ms": 640, "max_wait_ms": 5000 } } } }
```

## 5. Supporting APIs & web/JS SDK
- **RTC SDK (web):** `agora-rtc-sdk-ng` v4.24.4+; `AgoraRTC.createClient()`, mic via local audio track, `user-published`/`user-unpublished` events, full-duplex.
- **Signaling / RTM:** metadata/transcripts/events, <200ms global (<100ms in region); user + stream channels, presence. In ConvoAI, deliver live transcripts over RTM while audio streams over RTC.
- **AI Noise Suppression / Denoiser:** 100+ noise types, echo cancellation, ~95% effectiveness; web/iOS/Android/etc.
- **Real-time STT:** separate product; live captions, up to 3 simultaneous speakers; $0.10/min separately.
- **Cloud Recording:** individual or mixed; multi-party channels (human + agent + human specialist) → warm transfer (agent introduces specialist, steps back).

## 6. Pricing & "ConvoAI minutes"
- Clock runs while the agent is in the channel; **all participants billed**.
- **Free trial: first 300 min/month** (shared with Real-Time STT), then **$0.10/min**.
- ConvoAI does NOT use the standard 10,000 free RTC min/month pool — separate budget.
- Hackathon implication: 300 min ≈ 5 hrs → likely exhausts mid-event; request supplemental credits.

## 7. Hackathons, ecosystem, hosts
- Platform: **convoai.club** (Agora's curated voice-AI hackathon series).
- Precedent: **Voice AI Hackathon Istanbul (Jan 24 2026)** — starter repo `AgoraIO-Community/Istanbul-Hackathon-Jan-2026`; judging weights: Technical Innovation 20%, Experience Design 20%, **Agora Tech Integration 20%**, Impact 15%, Deployment 15%, Execution 10%.
- **Hermes Frangoudis** — Director of DevRel & Partner Engineering at Agora (20+ yrs web, 10+ yrs RTC; ex-Blippar NYC; co-founded webXR.tools; author of ConvoAI Medium tutorials in Go/Python). Likely the "Hermes" host.
- Neal Patel — Agora affiliation unconfirmed.
- Example projects: voice coding assistant, voice tutor / support agent, game NPCs (Hume emotion), AI companion robot.

## 8. Realistic 1-day build scope
- Minimal (2–3 hr): no-code Agent Studio + UI kit → greeting + FAQ bot.
- MVP (4–6 hr): REST backend + web client + OpenAI + ElevenLabs → support triage / coding assistant.
- Full (6–8 hr): + recording + warm transfer + knowledge base.
- Fast-start (~2 hr to first conversation): console+token (15m) → clone sample backend, deploy (20m) → minimal frontend (15m) → config agent (10m) → test (20m) → demo video + README (40m).
- Submission (Istanbul): README, 1–2 min demo video, /src, deadline 5 PM.

## 9. Agent join REST payload (example)
```
POST https://api.agora.io/api/conversational-ai-agent/v2/projects/{appid}/join
Authorization: Basic base64(appid:appcert)
```
Body includes: `name`, `properties.channel/token/agent_rtc_uid/remote_rtc_uids/idle_timeout`, `asr` (language/vendor), `llm` (url/api_key/vendor/params{model,max_tokens,temperature}/system_messages[]/greeting_message/max_history), `tts` (vendor/params{api_key,model,voice_id,language,stability,similarity_boost}), `turn_detection` (see §4).
Required: `name`, channel/token/agent_rtc_uid/remote_rtc_uids, asr.vendor, llm.url, llm.api_key, tts.vendor.

## 10. Agent Studio (no-code)
Console visual builder; ~10 min to a working agent. Tabs: **Prompt / Models / Advanced / Actions**. Actions tab supports **Knowledge Base** (upload PDFs/docs for RAG) and **MCP server integration** (external tool calls — e.g., CRM). Deploy: assign phone numbers. Observe: transcripts/analytics.

## 11. Agora × OpenAI Realtime API
Direct integration with gpt-4o-realtime; bypasses ASR→LLM→TTS text bottleneck (audio streamed directly). Potentially <300ms perceptual latency with Agora's network. Downside: OpenAI lock-in, no vendor swap, less barge-in control. Example: `AgoraIO/openai-realtime-python`.

## 12. Deployment & token auth
Client → backend `/api/token` (uses AppCert) → returns RTC+RTM tokens → client joins + publishes mic → client calls `/api/invite-agent`. "Backend never touches audio; browser never embeds AppCert." Tokens: 24-hr max, typically 1 hr; refresh via `renewToken()` on `onTokenPrivilegeWillExpire` (~30s before). HTTPS required for mic. CORS headers needed for cross-origin LLM/ASR. Deploy backend on Vercel/AWS Lambda/Railway. Starter: `AgoraIO-Community/agora-token-service`.

## 13. Priority gotchas
- Enable ConvoAI for your App ID in Console.
- Free-tier exhaustion (300 min) → request credits.
- Token expiry (1 hr) → `renewToken`.
- Mic permissions → HTTPS required.
- CORS on LLM call.
- App ID / channel / UID token must match runtime.
- **Agent UID must differ from any human participant UID.**
- `system_messages` is an array; `greeting_message` is spoken (TTS); ASR/LLM/TTS language must align.

## Key sources
- Agora ConvoAI docs: product overview, agent/join REST, studio overview, pricing, interrupt-agent, optimize-latency.
- OpenAI Realtime integration docs + `AgoraIO/openai-realtime-python`.
- `agora-rtc-sdk-ng` (npm), Web SDK API ref v4.24.1+.
- Signaling/RTM overview, AI Noise Suppression, Real-Time STT.
- Low-latency blog + Conversational AI Engine private-beta announcement.
- `AgoraIO-Community/Istanbul-Hackathon-Jan-2026`, convoai.club, `AgoraIO-Conversational-AI/agent-samples`.
- Hermes Frangoudis (Crunchbase + Agora Medium series).

_Confidence: High on vendor lists, REST payload, latency benchmarks (650/340ms), free tier (300 min), $0.10/min, Agent Studio, token auth. Medium on OpenAI Realtime latency claim, Istanbul judging detail, Hermes attribution. Low on the Jun 26–27 NYC event's public specifics, Neal Patel affiliation, Deepgram TTS support._
