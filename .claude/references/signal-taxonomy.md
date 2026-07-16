# Signal taxonomy — canonical topic map (v1)

The persistent **topic-normalization** map for the signal scanners (`trend-radar` Step 2; reusable by
`voice-radar` / `role-radar`). Promoted from trend-radar's inline seed on 2026-07-15 (first `/rigor-review`)
so normalization is **consistent run-to-run**, not re-derived ad-hoc each run. Applies the
`alex:signal-taxonomy` schema/mapping discipline.

**How to use:** at the start of trend-radar Step 2, read this file. For each raw item, map its candidate
tags to a `canonical_topic` via the synonym lists below. If a raw tag matches nothing here, create a new
canonical entry (human-readable, GTM-facing) and **append it back to this file** in the same run — that is
how the map grows. Prefer merging near-synonyms (under-merging hides corroboration); split only genuinely
distinct topics (record the split here).

**Matching:** case-insensitive substring / token match against the `synonyms` list. The `canonical_topic`
is what the Notion Topics DB `Topic` title and the Postgres `topic.name` match against — keep it stable.

## Canonical map

| canonical_topic | synonyms / raw tags (→ this) |
|---|---|
| **Agentic AI** | AI agents, agentic, agent frameworks, autonomous agents, multi-agent, agent orchestration, agentic workflows |
| **RAG** | RAG, retrieval augmented generation, retrieval-augmented, vector search + LLM, grounded generation |
| **LLM Evaluation** | LLM eval, evals, evaluation, benchmark, benchmarking, LLM-as-judge, eval harness |
| **MCP / Tool Use** | MCP, model context protocol, tool use, function calling, tool calling, connectors |
| **Model Adaptation** | fine-tuning, LoRA, QLoRA, post-training, RLHF, DPO, distillation, domain adaptation |
| **AI Infra / Serving** | inference, serving, vLLM, quantization, GPU, kernels, model serving, latency optimization |
| **Reasoning Models** | reasoning, chain-of-thought, o1, o3, test-time compute, reasoning traces, thinking models |
| **Multimodal** | multimodal, vision-language, VLM, image understanding, audio models, video generation |
| **AI Coding** | code generation, copilot, coding agents, SWE-agent, code LLM, AI pair programming |
| **GTM Engineering** | GTM engineering, revenue operations + AI, sales engineering, GTM automation, full-stack GTM |
| **AI Product / UX** | AI product, AI UX, human-in-the-loop, AI-native product, agent UX |
| **AI Policy / Safety** | AI safety, alignment, AI regulation, AI policy, model governance, red-teaming |
| **Open Models** | open weights, open-source LLM, Llama, Mistral, Qwen, DeepSeek, open model release |
| **AI Funding / Market** | funding round, raise, valuation, acquisition, AI market, seed/Series, IPO (AI co.) |

## Growth log
- 2026-07-15 — seeded from trend-radar inline map (5 entries) + expanded to 14 for the tracked-domain
  coverage in trend-radar's Inputs (agentic systems, LLM eval, GTM-engineering, AI infra, RAG). Promoted to
  a file per the `dangling-reference-in-skill` correction (rigor-review 2026-07-15).
