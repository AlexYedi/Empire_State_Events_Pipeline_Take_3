# Knowledge-Graph Delta — MCP Release Party (2026-07-28)

For Step 3.8 write-back. Each row is my best NEW vs MATCH guess — **the parent must `notion-search` each DB before creating (dedup is mandatory, rules #10/#11).** Enriched net-new entities carry a source URL. Relink every touched row to the Event (`3abd3699c2db8101a296c5405e3ee315`).

Schema ref: `.claude/references/notion-schema.md`.

---

## PEOPLE (7 to write/enrich)

### 1. Angie Jones — likely NEW ⭐ (enriched)
- **Name:** Angie Jones
- **Current Title:** VP, Developer Experience — Agentic AI Foundation (AAIF)
- **Role Context:** MC/host of the NYC MCP Release Party. Ex-Global VP Developer Relations at Block (led AI-agent rollout to ~12,000 employees); founder of Test Automation University (100k+ engineers trained); first Black woman named a Java Champion; 27 patents.
- **Known POV/Bio:** Open-source + DevRel veteran; frames MCP's value through community vibrancy and developer adoption. Runs AAIF's six-city party series, AgentCon/MCPCon, and the first official MCP certification.
- **LinkedIn:** linkedin.com/in/angiejones
- **Confidence/source:** HIGH — enrichment. [linkedin.com/in/angiejones · aaif.io/author/angie-jones]

### 2. Alex Hancock — likely MATCH (in pre-event brief) 
- **Name:** Alex Hancock
- **Current Title:** Software Engineer, Block; MCP maintainer (Rust SDK); core maintainer, Goose
- **Role Context:** Talk 1 — the stateless-spec overview. 10 years at Block. On the MCP Steering Committee.
- **Known POV/Bio (append):** Remote-first framing of the 2026-07-28 release; statelessness as the marquee change; MRTR ≈ x402; Tasks/Apps as the first two extensions; "use the SDKs, don't hand-roll."
- **Confidence/source:** HIGH — on stage (primary) + pre-event roster. Enrich existing row; bump Last Researched; add Events relation.

### 3. Scott Yak — likely MATCH (in pre-event brief)
- **Name:** Scott Yak
- **Current Title:** Senior Software Engineer, Datadog — Applied AI (MCP services); ex-Google Research
- **Role Context:** Talk 2 — lessons from operating the Datadog MCP server.
- **Known POV/Bio (append):** "Monolithic MCP servers don't scale organizationally"; context-as-shared-commons; distributed per-team MCP servers behind one URL; eval-authoring is the next bottleneck.
- **LinkedIn:** linkedin.com/in/scottyak
- **Confidence/source:** HIGH — on stage + roster. Enrich existing row.

### 4. Michael Levan — likely MATCH (in pre-event brief; fix spelling)
- **Name:** Michael Levan (⚠️ transcript renders "Levin" — canonical **Levan**)
- **Current Title:** AI Architect / Principal Solutions Engineer, Solo.io
- **Role Context:** Talk 3 — "MCP and the Authorization Gap Nobody's Closing." Microsoft MVP, CNCF Ambassador, AAIF "AI Young Ambassador," Kubernetes release-team alum.
- **Known POV/Bio (append):** Security belongs at the AI gateway, not the MCP server (server = black box); agent identity via SPIFFE/workload identity; ~15–18 tool ceiling; secure the response path; ABAC/ReBAC + OBO/token exchange.
- **LinkedIn:** linkedin.com/in/michaellevan
- **Confidence/source:** HIGH — on stage + roster. Enrich; correct spelling if stored as "Levin."

### 5. David Soria Parra (DSP) — likely MATCH (mentioned in pre-event brief) — NOT present
- **Name:** David Soria Parra
- **Current Title:** MCP co-creator (Anthropic); based in London
- **Role Context:** Named on stage as MCP's creator; hosting the London party; did not attend NYC.
- **Confidence/source:** HIGH — [anthropic.com/news/model-context-protocol]. Enrich existing/mentioned row; add Events relation only if you track "mentioned."

### 6. Justin Spahr-Summers — likely NEW (enriched) — NOT present
- **Name:** Justin Spahr-Summers
- **Current Title:** MCP co-creator (Anthropic)
- **Role Context:** Named by Hancock ("David and Justin working on it") as the other original MCP author.
- **Confidence/source:** HIGH — [anthropic.com/news/model-context-protocol]. Optional add (mention-only).

### 7. Demetrios (Brinkmann) — likely MATCH (in pre-event brief) — NOT present
- **Name:** Demetrios (transcript "Dimitrios")
- **Current Title:** MLOps Community lead; host of AAIF's "Agentic Conversations" podcast
- **Role Context:** Named by Angie as her colleague running the AAIF podcast.
- **Confidence/source:** HIGH — on stage + roster.

**Non-speaking organizers (create/link only if you track organizers):** Lahari Chowtoori (AAIF NY organizer, ex-AWS TPM) and David DeStefano (AAIF NY co-organizer, identity not fully confirmed) — thanked generically, did not speak. LOW priority; do not attribute content.

**Audience Q&A members:** unnamed — no People rows.

---

## COMPANIES (7–8 to write/enrich)

### 1. Agentic AI Foundation (AAIF) — likely NEW ⭐ (enriched)
- **Description:** Nonprofit under the Linux Foundation for agentic-AI open standards/protocols. Per Angie on stage, founded by Anthropic, OpenAI, and Block (⚠️ Rule 12 — verify three-founder claim). Home of MCP since its Dec 2025 donation; runs the six-city party series, AgentCon/MCPCon (San Jose, Oct), and the first official MCP certification.
- **Industry/Space:** AI standards / open-source foundation
- **Website:** aaif.io
- **Confidence/source:** HIGH (org exists) / MED (founders claim). [aaif.io]

### 2. Datadog — likely MATCH (host/sponsor)
- **Description:** Observability platform (metrics, traces, logs). Ships a Datadog MCP Server giving AI agents NL access to observability data.
- **Industry/Space:** Observability / DevOps / AI infra
- **Website:** datadoghq.com
- **Role Context:** Venue + sponsor; Yak's case study. 47→197 MCP tools, ~83 products. Uses MCP Apps + Bits AI daily bug-sweep.
- **Confidence/source:** HIGH. Enrich; add Events relation.

### 3. Block — likely MATCH
- **Description:** Fintech; origin of Goose (donated to Linux Foundation); AAIF co-founder (per Angie). Hancock's + Jones's (former) employer.
- **Industry/Space:** Fintech / AI tooling
- **Website:** block.xyz
- **Confidence/source:** HIGH.

### 4. Solo.io — likely NEW (enriched)
- **Description:** Cloud-native application-networking company; makers of agentgateway (AI-native proxy that speaks MCP/A2A), kagent, and Agent Mesh (agent identity via SPIFFE in an Istio ambient mesh). Levan's employer.
- **Industry/Space:** AI gateway / cloud-native security
- **Website:** solo.io
- **Confidence/source:** HIGH. [solo.io/press-releases/solo-io-launches-agent-gateway-and-introduces-agent-mesh]

### 5. Anthropic — likely MATCH
- **Description:** Creator of MCP (David Soria Parra + Justin Spahr-Summers); AAIF co-founder (per Angie); maker of Claude / Claude Code / Claude Desktop.
- **Industry/Space:** Frontier AI lab
- **Website:** anthropic.com
- **Confidence/source:** HIGH.

### 6. OpenAI — likely MATCH
- **Description:** AAIF co-founder (per Angie); Codex (now on the MCP Rust SDK per Hancock — Rule 12); ChatGPT (MCP Apps support).
- **Industry/Space:** Frontier AI lab
- **Website:** openai.com
- **Confidence/source:** MED (mentions only).

### 7. Coinbase (x402) — likely NEW (enriched, mention-only)
- **Description:** Payments company; author of x402, an HTTP-402-based payments protocol for internet-native / AI-agent micropayments (now under Linux Foundation governance). Cited as MRTR's structural twin.
- **Industry/Space:** Payments / crypto infra
- **Website:** github.com/coinbase/x402
- **Confidence/source:** HIGH. Optional (mention-only). [github.com/coinbase/x402]

### 8. MLOps Community — likely MATCH (mention-only)
- **Description:** Practitioner community led by Demetrios; runs AAIF's "Agentic Conversations" podcast.
- **Website:** mlops.community
- **Confidence/source:** HIGH.

_(Lower priority mentions — create only if tracked: GitHub/Copilot, Linux Foundation, Google Research (Yak's past).)_

---

## TOPICS (10 to write/link — one-liners)

1. **MCP statelessness (2026-07-28 spec)** — the marquee release change: no `initialize`/session; self-contained requests enable standard load-balancing/autoscaling.
2. **MRTR (Multi-Round Trip Request)** — new server→client ask pattern (SEP-2322); replaces held-open SSE streams; shape mirrors x402.
3. **MCP extensions framework (SEP-2133)** — formal experimental→official path; MCP Apps (SEP-1865) and Tasks (SEP-2663) are the first two.
4. **MCP Tasks extension** — async, long-running / human-in-the-loop tool calls via create→task-ID→poll→complete.
5. **MCP authorization / runtime authZ scope** — what an agent may *do* after auth; the "gap nobody's closing"; gateway-enforced, not spec-enforced.
6. **Agent identity & tool isolation** — per-agent identity (SPIFFE/workload) + limiting exposed tools (~15–18) for security and token cost.
7. **AI gateway as enforcement layer** — auth, guardrails, rate-limiting, OBO/token-exchange, ABAC/ReBAC done at the gateway (Solo.io agentgateway/Agent Mesh).
8. **MCP server organizational scaling** — monolith → distributed per-team servers behind one URL; context-as-shared-commons; eval-authoring bottleneck (Datadog).
9. **MCP observability & token economics** — initialize-vs-tool-call inefficiency; max_tokens limits; token cost lands on the host, not the server.
10. **MCP governance (Linux Foundation / AAIF)** — MCP donated to AAIF (Dec 2025); first official MCP certification; SDK "tier-one" maintainer model.

---

## Write summary for the parent
- **People:** 7 primary (2 likely NEW: Angie Jones, Justin Spahr-Summers; 5 likely MATCH — dedup-verify) + 2 non-speaking organizers (optional) + audience (none).
- **Companies:** 8 (likely NEW: AAIF, Solo.io, Coinbase/x402; MATCH: Datadog, Block, Anthropic, OpenAI, MLOps Community — verify).
- **Topics:** 10 net-new/refresh.
- **Enriched net-new with source URLs:** Angie Jones, Justin Spahr-Summers, Solo.io, Coinbase/x402, AAIF (sources inline above).
- **⚠️ Rule-12 gate before any public/tagged use:** AAIF three-founder claim; Goose "first client"; Codex/Copilot-on-Rust-SDK. Fix "Levin"→"Levan" spelling on write.
