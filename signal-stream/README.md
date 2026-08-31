# Signal Stream — a real-time GTM signal agent on Confluent

Built as hackathon warm-up for **Confluent AI Day NYC (Thu Sept 3, 2026)**. A live news/HN stream flows
into Kafka; a Flink job classifies each item against Alex's ICP with an LLM; relevant signals land in
Notion. It's the event-driven mirror of the Market-Intelligence Engine — the same job, done always-on.

**Layered build** (each layer is independently demoable — stop anywhere and you still have something):

| Layer | You get | Status target |
|---|---|---|
| **0 — Foundation** | Query a live topic from Claude Code via Confluent's managed MCP server | Sun |
| **1 — Signal Stream** (firm) | Flink classifies the stream vs your ICP → hits appear in Notion | Mon–Tue |
| **2 — Situation Room** (stretch) | Multi-agent watcher→classifier→enricher→briefer + replay | if runway / Thu hackathon |

---

## 0. One-time prerequisites (YOUR steps — credentials/accounts can't be automated)
1. **Sign up** at confluent.cloud → $400 promo credit / 30-day trial (needs a payment method; card isn't
   charged until the trial ends). → create an **Environment** → a **Basic cluster** in a region with
   **Flink** → a topic named `raw_signals`.
2. **Global API key** (Console → API keys → *Global access*, NOT resource-scoped) → paste key+secret into `.env`.
3. Fill the rest of `.env`: `cp signal-stream/.env.example signal-stream/.env` then edit (org id, region,
   cloud, cluster id, REST endpoint, a model-provider key, Notion token + DB).
4. **Model provider:** VERIFY which providers Confluent Flink `CREATE MODEL` supports and use a key you have.
5. **Notion:** create an internal integration + a "Signal Inbox" DB (title prop "Name"), share the DB with
   the integration, put the token + DB id in `.env`.

## Layer 0 — Foundation (Ask-the-Stream)
1. In the Console, add a **Datagen Source connector** (`STOCK_TRADES` or `USERS`, JSON) targeting `raw_signals`
   — a live fake-data stream, zero code, to prove the plumbing.
2. Wire the managed MCP servers into Claude Code:
   ```bash
   python3 signal-stream/scripts/encode_creds.py   # prints the two ready `claude mcp add` commands
   ```
   Run the two commands it prints. Then `claude mcp list` → both connected.
3. **Checkpoint:** ask Claude Code *"list my topics, read the latest raw_signals messages, describe the
   schema."* Real answers = Layer 0 done. (Full details: `mcp/confluent-mcp.md`.)

## Layer 1 — Signal Stream (the deliverable)
1. Put your real ICP in `icp/targets.md` (already seeded).
2. **VERIFY** the Flink AI syntax against current docs, then run `sql/01_classify.flink.sql` in the
   Console → Flink workspace (`CREATE CONNECTION` → `CREATE MODEL` → `CREATE TABLE gtm_signals` → the
   `INSERT … ML_PREDICT …` continuous job). Start prompt-based (1a); it needs no vector store.
3. Swap Datagen for real data:
   ```bash
   python3 signal-stream/producers/hn_producer.py --dry-run          # preview (hits HN live, no produce)
   python3 signal-stream/producers/hn_producer.py --query "AI" --limit 15   # produce for real
   ```
4. Land hits in Notion (pipe the consumed sink topic through the sink):
   ```bash
   confluent kafka topic consume gtm_signals --value-format json -o latest \
     | python3 signal-stream/sinks/notion_sink.py
   ```
5. **Checkpoint = done:** a real HN item flows in → classified relevant → appears in Notion. Record a
   30-sec screen capture (the content asset + the Graczewski demo).
6. **1b upgrade (only if 1a is solid):** `sql/02_vector_search.flink.sql` grounds classification in
   `VECTOR_SEARCH` over an embedded ICP.

## Layer 2 — Situation Room (stretch)
See `sql/situation_room/README.md`. Don't start until Layer 1 demos cleanly.

---

## ⚠️ Burn discipline (real money after the $400 credit)
The Datagen connector and any running Flink statement **consume credit continuously**. After each session:
**pause/delete the Datagen connector and stop the Flink `INSERT` statement.** Drop the demo objects when done.

## Security
- `.env` and `config.yaml` are gitignored. **Never commit credentials.**
- The managed-MCP Basic-auth header goes in via `claude mcp add` (machine-local), **not** `.mcp.json`.
- `consume_kafka_messages` sends message content to the model — only point it at the demo/HN topics.

## Honesty notes (things to verify, not assume)
- The `*.flink.sql` files are **close templates with VERIFY banners** — Confluent Cloud Flink's AI syntax
  (`CREATE MODEL` / `ML_PREDICT` / `VECTOR_SEARCH`, and the newer `CREATE AGENT`) is version-specific; confirm
  against the docs before running.
- The Kafka REST produce endpoint path in `hn_producer.py` is the v3 records API — confirm your cluster's
  REST endpoint.
- `VECTOR_SEARCH` external-store support (pgvector?) is unconfirmed — verify before Layer 1b.

## What's here
```
signal-stream/
  README.md · .env.example · .gitignore
  mcp/confluent-mcp.md          managed + OSS MCP setup
  scripts/encode_creds.py       prints the claude mcp add commands
  producers/hn_producer.py      HN/RSS → raw_signals (Kafka REST)
  sinks/notion_sink.py          consumed gtm_signals → Notion
  sql/01_classify.flink.sql     Layer 1a: ML_PREDICT classification
  sql/02_vector_search.flink.sql Layer 1b: VECTOR_SEARCH upgrade
  sql/situation_room/           Layer 2 stretch
  icp/targets.md                classification ground truth
```
