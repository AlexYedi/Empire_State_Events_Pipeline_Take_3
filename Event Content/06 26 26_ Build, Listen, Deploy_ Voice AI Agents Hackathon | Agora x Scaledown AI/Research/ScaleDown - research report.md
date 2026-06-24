# ScaleDown AI — Research Report (compression + voice integration)
_Compiled 2026-06-21 for the Agora × ScaleDown Voice AI Agents Hackathon._

## Executive summary
ScaleDown is an applied-AI lab providing **task-specific small language models (SLMs) for prompt/context compression** (also summarization, extraction, classification). Core claim: **40–60% token reduction** with preserved semantic quality. For voice: smaller LLM inputs → faster **TTFT** (time-to-first-token), the critical voice-UX metric. Best slotted pre-LLM to compress system prompts, RAG context, and conversation memory.

## 1. Product & org
- **Not just token trimming — semantic compression via token classification.** Given a query, the model classifies which tokens to KEEP vs DROP (no text generation → no hallucination).
- Three-stage pipeline: **HASTE Optimizer** (AST-guided selection, Tree-sitter + BM25 + semantic), **Semantic Optimizer** (FAISS embeddings relevance ranking), **ScaleDown Compressor** (API that semantically rewrites context).
- Site: scaledown.ai · GitHub org: `scaledown-team` (repo `scaledown-team/scaledown`, benchmark `ScaleBench`) · blog: blog.scaledown.ai.
- Claims: production-ready Python SDK; SOC 2 / HIPAA / ISO 27001 / GDPR.

## 2. API & integration
```
Base URL: https://api.scaledown.xyz
Auth: Bearer token — SCALEDOWN_API_KEY="sk-..."
```
**Compress (inferred from SDK):**
```
POST /compress
{ "context": "<long document/prompt>", "query": "<task query>", "target_model": "gpt-4o", "rate": "auto" }
→ { "compressed_context": "...", "original_tokens": 5000, "compressed_tokens": 2000, "savings_percent": 60, "metrics": {...} }
```
- **Python SDK:** `pip install scaledown` (extras: `[semantic]`, `[haste,semantic]`).
```python
from scaledown import ScaleDownCompressor
c = ScaleDownCompressor(target_model="gpt-4o", rate="auto")
r = c.compress(context=long_text, query="Summarize key points")
print(r.metrics.savings_percent, r.compressed_context)
```
- **JS/Node SDK:** not found publicly — call the REST API via HTTP.
- Errors: `AuthenticationError`, `APIError`, `OptimizerError`.
- **"10B tokens" prize** ≈ 10B input tokens of compression credit. Pricing model not public (likely subscription/token bucket).

## 3. Technical approach & numbers
- Token-level semantic relevance scoring (small BERT/RoBERTa-family), query-conditioned pruning, AST-guided filtering (code), semantic search pre-filter, soft/hard token caps (~1200–1800 default).
- **Compression ratio: typically 40–60%** (varies by use case — code/structured compress well; already-dense prompts poorly; some edge cases compress *negatively*).
- Compression API's own latency: ~**100–500 ms** (undocumented; small SLM inference).
- Post-compression LLM speedup ~1.2–1.8×; **TTFT improvement ~50–150 ms** (with small prompts) up to 25–33% on large RAG contexts.

## 4. Voice AI fit (the important part)
**Insert pre-LLM, in parallel with ASR**, so compression is off the critical path. Standard voice pipeline: ASR (~100–200ms) → LLM (500–1500ms, bottleneck) → TTS (~500–800ms). Target TTFT <500–800ms.

Best compression targets:
1. **System prompt** (once per session, negligible latency cost) — ~40% reduction, ~100ms TTFT gain.
2. **RAG context** (per-turn, async during ASR, must finish <200ms) — 70% fewer tokens, ~150–200ms gain. **Highest-impact.**
3. **Conversation memory** (long calls) — summarize old turns, keep recent verbatim, drop redundant; ~50% reduction on 30-min calls.

**Honest caveat:** because the compression call itself costs 100–500ms, it is **latency-positive only on large context** (RAG / long memory). On a thin system prompt the win is **cost + quality, not turn latency**. Run it during ASR.

Expected gains (large-context voice agent): TTFT 1200ms→800–900ms (25–33% faster); input tokens 6000→3000–3600 (40–50%); cost $0.10→$0.04–0.06/call (40–60%); quality maintained.

## 5. Competitive landscape (credibility benchmarks)
- **Microsoft LLMLingua / LLMLingua-2 / LongLLMLingua:** up to 20× compression; 1.4–2.9× end-to-end speedup; <1.5% performance loss; LongLLMLingua is query-aware (best for RAG). Open-source library (`microsoft/LLMLingua`).
- Others: Gist Tokens (up to 26×), RECOMP (5–10×, RAG), Selective Context (30–50%), 500xCompressor, LanguaShrink (~50%).
- **ScaleDown vs LLMLingua-2:** semantic token-classification vs PPL+distillation; both ~2–6× range; ScaleDown's edge is **REST API ease + lowest hallucination risk (no generation)**; LongLLMLingua better for pure retrieval.

## 6. Integration patterns (voice)
1. **System prompt optimization (pre-call):** compress once at session start, reuse all turns.
2. **Parallel RAG + compression (per-turn):** retrieve top-10 (~5000 tok) → compress to ~2500, async while ASR finalizes.
3. **Rolling summarization (long calls):** last ~10 turns verbatim + compressed older turns.
4. **Token-budget enforcement:** cascade-compress history → context → system until under budget (~4000 tok) to guarantee TTFT.

## 7. Demos / resources
- `scaledown-team/scaledown` (SDK + examples), `scaledown-team/ScaleBench` (benchmarks), blog.scaledown.ai (case studies, e.g. data-security context compression).
- Closest public analog walkthrough: Microsoft LLMLingua (GitHub + arxiv:2310.06839).

## Confidence
- High: semantic-compression product, endpoint `api.scaledown.xyz`, Bearer auth, Python SDK, 40–60% reduction, per-call metering, LLMLingua benchmarks, ~25–33% voice TTFT achievable.
- Medium: pricing model, "10B tokens" interpretation, exact request/response shape (inferred from SDK), the Jun 2026 NYC event specifics.
- Low: production compression ratios vs LLMLingua, ScaleDown's own API latency, streaming/async support, JS SDK existence.

## Key sources
scaledown.ai · github.com/scaledown-team · blog.scaledown.ai · microsoft/LLMLingua + arxiv:2310.06839 (LongLLMLingua) · LiveKit voice-agent architecture · Agora ConvoAI optimize-latency docs · various 2026 prompt-compression and real-time-voice-RAG writeups (Redis, Morph, AutoInterviewAI, Softcery).
