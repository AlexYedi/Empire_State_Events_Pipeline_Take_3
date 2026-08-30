# Wiring Confluent's MCP servers into Claude Code

Two options. **Layer 0 (Ask-the-Stream) uses the managed servers** — zero install, read-only, perfect for
"query the live stream in natural language." **Flink SQL + produce need the open-source server** (or you
author Flink SQL directly in the Confluent Console). Sources at the bottom (verified 2026-08-30).

---

## A) Managed MCP servers (recommended for Layer 0 — read-only query/inspect)

There are **two** managed servers; add both. Auth is HTTP Basic with a Base64-encoded `key:secret`
from your **Global API key** (resource-scoped keys are rejected → 401).

> Run `python3 signal-stream/scripts/encode_creds.py` — it reads your key/secret from `.env`, Base64-encodes
> them, and prints these exact commands filled in, so you don't fat-finger the encoding.

```bash
# Global server — env / cluster / connector / metrics discovery
claude mcp add --transport http confluent-mcp-global \
  https://api.confluent.cloud/mcp/v1 \
  --header "Authorization: Basic <ENCODED>"

# Regional server — topic list/describe, CONSUME messages, schema subjects
# <region>=e.g. us-east-1  <cloud>=aws|gcp|azure  <org_id>=your Confluent org id
claude mcp add --transport http confluent-mcp-regional \
  https://mcp.<region>.<cloud>.confluent.cloud/mcp/v1/organizations/<org_id> \
  --header "Authorization: Basic <ENCODED>"
```

- **Scope:** these commands add the servers at **local (project) scope** by default — the credential lives in
  your machine-local Claude config, **NOT** in a committed file. Do **not** put the header in `.mcp.json`
  (that file is checked in). Add `-s user` to make them available in every project instead.
- **Verify:** run `claude mcp list` (or `/mcp` in-session) — both should show connected.
- **Tools you'll use for the demo (regional):** `list_kafka_topics`, `describe_kafka_topic`,
  `consume_kafka_messages` (reads 1–10 sample messages), `list_schema_subjects`, `read_schema_subject`.
- **Read-only reality:** the only writes the managed servers expose are `restart_connector` /
  `update_connector_config`. **You cannot create topics or produce** through them — that's why Layer 0 uses
  the Datagen connector for the stream, and Layer 1 produces via the REST script / CLI.
- **Privacy:** `consume_kafka_messages` sends message content to the model — only point it at demo/HN topics.

### Layer 0 checkpoint (say this to Claude Code once connected)
> "List the topics in my cluster, read the latest messages from `raw_signals`, and describe its schema."

If you get real answers back, **Ask-the-Stream is done.**

---

## B) Open-source MCP server (for Layer 1+ — Flink SQL + produce, if you want it from Claude Code)

`@confluentinc/mcp-confluent` — local Node process (Node 22+), 50+ tools **including produce, create topic,
and Flink SQL**. Three transports (stdio default). Run it and register as a stdio server.

```bash
# generate + edit config (put keys in config.yaml — gitignored)
npx @confluentinc/mcp-confluent --init-config
# then register (source .env so keys aren't inlined, matching repo convention)
claude mcp add -s local confluent-oss \
  -- bash -c "set -a; source '$(pwd)/signal-stream/.env'; set +a; exec npx -y @confluentinc/mcp-confluent --config ./signal-stream/config.yaml"
```
- Opt out of telemetry: `DO_NOT_TRACK=true`.
- Alternative to authoring Flink SQL from Claude Code: just paste `sql/*.flink.sql` into the **Confluent Cloud
  Console → Flink workspace** and run there. Often the fastest, lowest-surprise path.

There is also a convenience **plugin** `@confluentinc/claude-code-confluent-plugin` (slash commands like
`/topics-create`, `/clusters-list`) for provisioning infra in natural language — optional.

---

## Sources (verified 2026-08-30)
- Managed MCP servers: https://docs.confluent.io/cloud/current/ai/ai-tools/managed-mcp-server.html
- Open-source MCP server: https://docs.confluent.io/cloud/current/ai/ai-tools/open-source-mcp-server.html
- GA blog (2026-05-19): https://www.confluent.io/blog/ai-developer-tools-mcp-server-agent-skills-ga/
- OSS repo: https://github.com/confluentinc/mcp-confluent
- Free trial ($400 / 30 days): https://docs.confluent.io/cloud/current/get-started/free-trial.html
- Datagen connector: https://docs.confluent.io/cloud/current/connectors/cc-datagen-source.html
