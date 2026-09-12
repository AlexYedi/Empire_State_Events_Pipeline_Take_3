# Plan: Signal Stream (layered) — a real-time GTM signal agent on Confluent

## Context
Alex is attending **Confluent AI Day NYC on Thu Sept 3, 2026** — a hands-on build day + 3-hour hackathon on Confluent's own stack (Kafka + Flink Streaming Agents + MCP + vector/RAG). Building on that exact stack *before* the event turns prep into hackathon warm-up **and** a concrete conversation-starter with Tim Graczewski (Head of Confluent for Startups, Alex's top prospecting target) and Ahmed Zamzam (whose "Flink Jobs as Agents" talk is the event's core topic).

From the project-ideation run, three nested proposals emerged. Alex chose to aim high: **build Signal Stream (#1) as the firm pre-Thursday deliverable, with GTM Situation Room (#3) as a stretch.** They aren't separate projects — #3 is #1 plus multi-agent orchestration + replay, and the original "Ask-the-Stream" (#2) is literally the foundation layer of both. So this is **one escalating build with a demoable checkpoint at each layer** — the structure that also avoids the over-scope trap that killed a prior hackathon build (6h on UI, 1h on protocol; see `Opinionated Debate Swarm` retro in Notion Project Ideas).

Goal for this plan: **scaffold** the project so focused dev over Sun–Wed lands Signal Stream, with the Situation Room extension ready to start if there's runway (else it becomes the Thursday hackathon centerpiece).

## The nested architecture (each layer independently demoable)

| Layer | What it adds | Primary dev surface | Demo |
|---|---|---|---|
| **0 — Foundation** (was "Ask-the-Stream") | Confluent Cloud + a topic + a live stream + the **managed MCP server** wired into Claude Code | Confluent Console + `claude mcp add` | Ask Claude Code NL questions: "what topics exist? read the latest messages + describe the schema" |
| **1 — Signal Stream (#1, FIRM TARGET)** | A continuous **Flink SQL** job that classifies each event against Alex's ICP and routes hits to Notion | Flink SQL (Console workspace) + producer/sink scripts | Live: a real HN/news item flows in → gets classified relevant/not → a relevant one appears in Notion |
| **2 — Situation Room (#3, STRETCH)** | Split the one agent into watcher→classifier→enricher→briefer; per-company brief state; Kafka **replay/audit** | More Flink SQL + orchestration | Replay the stream and show what each agent saw/did → an auto-updating per-company brief |

**Key correction baked in (from setup research):** the **managed MCP server is read-only** — it's the *query/inspect* surface (Layer 0), NOT where classification happens. The classification/agent logic is **Flink SQL** authored in the Confluent Cloud Flink workspace (or via the **open-source** `@confluentinc/mcp-confluent` stdio server, which does have Flink SQL + produce tools). Don't plan to "produce" or "run the agent" through the managed server.

## Human-in-the-loop prerequisites (Alex's steps — I cannot do these)
These gate everything and are the real schedule risk (not Claude capacity). Do them **first / early**:
1. **Confluent Cloud signup** (confluent.cloud) → $400 promo credit / 30-day trial. **Requires adding a payment method** (card not charged until trial ends). — *Alex only (account creation + payment method are off-limits for me).*
2. Create an **Environment** → a **Basic cluster** (pick a region where Confluent Cloud **Flink** is available) → a topic (`raw_signals`).
3. Create a **Global API key** (org-scoped — NOT a resource-scoped key; scoped keys are the #1 401 cause) + secret. — *Alex creates; pastes into `.env`.*
4. A **model-provider API key** for Flink `CREATE MODEL` (Flink supports OpenAI / Azure OpenAI / Bedrock / Vertex AI, etc.). Pick a provider Alex has a key for. — *verify supported providers against docs; Alex supplies the key.*
5. (Layer 0 stream) Add a **Datagen Source connector** (built-in `STOCK_TRADES` or `USERS`, JSON) → streams fake data with zero code to prove the plumbing before real data is wired.

## Folder layout to scaffold (`signal-stream/` — dedicated project)
```
signal-stream/
  README.md              # runbook: prereqs, the layered build, demo script, teardown, sources
  .env.example           # CONFLUENT_* + model-provider + NOTION_* keys, with sourcing comments
  .gitignore             # .env, config.yaml, __pycache__
  mcp/
    confluent-mcp.md      # exact `claude mcp add` cmds (managed global+regional) + OSS server setup
  scripts/
    encode_creds.py       # stdlib: reads key:secret from .env, base64-encodes, PRINTS the ready `claude mcp add` commands (avoids fat-fingering)
  producers/
    hn_producer.py        # stdlib urllib: polls HN/RSS → produces to `raw_signals` via Confluent Cloud Kafka REST (no native deps)
  sinks/
    notion_sink.py        # stdlib urllib: consumes `gtm_signals` (via REST) → writes relevant hits to Notion (reuse the pipeline's Notion write patterns)
  sql/
    01_classify.flink.sql        # Layer 1a (RELIABLE CORE): ML_PREDICT classification vs an ICP prompt → sink to gtm_signals
    02_vector_search.flink.sql   # Layer 1b (UPGRADE): VECTOR_SEARCH grounding vs embedded ICP
    situation_room/              # Layer 2 stretch SQL (watcher/classifier/enricher/briefer)
  icp/
    targets.md             # Alex's ICP / target-company list — the classification ground truth
```
Follows the repo's **stdlib ethos** (no package manager; `urllib` + hand-parsed `.env`, mirroring `.claude/scripts/recompute_relevance.py`). Scripts use `--dry-run`. Because it's a dedicated folder, it can carry its own README + `.gitignore` without touching pipeline internals.

## Build sequence (Sun → Wed)

**Layer 0 — Foundation (target: Sun, ~half day)**
- Alex does prereqs 1–3 + 5 (Datagen). I scaffold `mcp/confluent-mcp.md` + `scripts/encode_creds.py`.
- Wire the managed MCP servers via **`claude mcp add --transport http` at local/user scope** (NOT `.mcp.json`) — this keeps the Base64 Basic-auth credential out of the committed repo. Both servers: **global** (`https://api.confluent.cloud/mcp/v1`) for discovery + **regional** (`https://mcp.<region>.<cloud>.confluent.cloud/mcp/v1/organizations/<org_id>`) for topic/consume/schema tools.
- **Checkpoint:** in Claude Code, `/mcp` shows the servers; ask "list my topics, read latest `raw_signals` messages, describe the schema" and get real answers. ← Ask-the-Stream, done.

**Layer 1 — Signal Stream (target: Mon–Tue, the firm deliverable)**
- **1a (reliable core first):** author `sql/01_classify.flink.sql` — a continuous Flink SQL statement that reads `raw_signals`, calls **`ML_PREDICT`** with an LLM (`CREATE MODEL` + `CREATE CONNECTION` to the provider from prereq 4) to classify each event as GTM-relevant vs not against an ICP described **in the prompt** (from `icp/targets.md`), and inserts relevant rows into a `gtm_signals` topic. *Prompt-based ICP first because it needs no vector store — highest certainty.*
- Swap the Datagen stream for real data: run `producers/hn_producer.py` to feed `raw_signals` from HN/RSS.
- Run `sinks/notion_sink.py` to land `gtm_signals` hits in Notion (a `signal_stream` view / the Companies or a new inbox DB).
- **Checkpoint (this is "done"):** a real HN item flows in → classified → a relevant one appears in Notion, live. Capture a 30-sec screen recording (the content asset + Graczewski demo).
- **1b (upgrade, only if 1a is solid):** add `sql/02_vector_search.flink.sql` — embed `icp/targets.md` into a vector store Flink `VECTOR_SEARCH` supports, and ground classification in retrieval instead of a static prompt.

**Layer 2 — Situation Room (STRETCH — start only if Layer 1 lands with runway; else → Thursday hackathon)**
- Split into coordinated statements: watcher (ingest+dedup) → classifier → enricher (pull company context, ideally via a `CREATE TOOL`/MCP call) → briefer (writes a per-company "situation room" brief). Use Kafka consumer-group **replay** to demo "what each agent saw and did" (the auditability differentiator).
- Explicitly time-boxed; a fragile half-built Situation Room is worse than a clean Signal Stream + a strong hackathon start.

## Uncertainties to verify during the build (do NOT hardcode blind)
- **Exact Flink AI / Streaming Agents syntax.** `CREATE MODEL` / `ML_PREDICT` / `VECTOR_SEARCH` are the established verbs; the newer full `CREATE AGENT` / `AI_RUN_AGENT` "Streaming Agents" syntax is fast-moving — **verify against current Confluent Cloud Flink docs before writing the SQL**, and prefer `ML_PREDICT` for the reliable core. (The pack's "Flink tools in the managed MCP server, ~late Sept 2026" claim was **unverified** — treat Flink-from-Claude-Code as the OSS server's job, not the managed server's.)
- **Which vector stores `VECTOR_SEARCH` supports** (for 1b) — verify; pick one Alex can stand up fast (his Supabase/pgvector may or may not be a supported external table).
- **Which model providers Flink `CREATE MODEL` supports** + which key Alex has — verify before prereq 4.
- **Kafka REST produce endpoint shape + auth** for `hn_producer.py` — confirm the cluster's REST endpoint.

## Secrets & cost discipline
- **Never commit credentials.** `.env` is gitignored; the managed-MCP Basic-auth header goes in via `claude mcp add` (machine-local scope), not `.mcp.json`. If the OSS server is used, source `.env` in its launch command (repo convention) — don't inline keys.
- **`consume_kafka_messages` sends message content to the model** — only point it at the demo/HN topic, never a sensitive one.
- **Burn discipline:** Datagen connector + Flink statements consume the $400 credit while running. **Pause/delete Datagen and stop Flink statements after each session**; document teardown in the README.

## Verification (end-to-end, per layer)
- **Layer 0:** `claude mcp list` shows both servers connected; an NL query in Claude Code returns real topic names + sample messages + schema.
- **Layer 1a (the deliverable):** produce a known-relevant test item via `hn_producer.py` (or `confluent kafka topic produce`) → confirm it lands in `gtm_signals` classified relevant → confirm the Notion row appears via `sinks/notion_sink.py`. Produce a known-irrelevant item → confirm it's filtered out. Record the 30-sec demo.
- **Layer 1b:** show a borderline item that prompt-only misclassifies but VECTOR_SEARCH grounding gets right.
- **Layer 2 (stretch):** replay the topic from offset 0 and show the per-agent trace + an updated per-company brief.

## Out of scope / explicitly deferred
- Full `CREATE AGENT` ReAct streaming agent (use `ML_PREDICT` continuous statements instead unless verification shows the AGENT syntax is trivial).
- Any production hardening, custom UI, auth — this is a demo/portfolio build, not a product.
- HubSpot/CRM writes — Notion sink only.
