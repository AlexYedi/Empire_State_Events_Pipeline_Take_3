# Layer 2 — GTM Situation Room (STRETCH)

**Do not start this until Layer 1 (Signal Stream) is demoably done.** This is the multi-agent
extension: it's Signal Stream split into coordinated stages plus per-company state and replay.
If Layer 1 lands with runway → start here; otherwise this is the **Thursday hackathon centerpiece**
(finishing it live is the content moment).

## Shape
Four coordinated Flink statements over the stream, each writing to the next topic:
1. **watcher** — ingest + dedup `raw_signals` → `signals_deduped`
2. **classifier** — the Layer 1a `ML_PREDICT` step → `gtm_signals`
3. **enricher** — pull company context (ideally via `CREATE TOOL` → an MCP call, or a lookup join) → `gtm_signals_enriched`
4. **briefer** — maintain a **per-company** running brief (keyed aggregation / upsert) → `company_briefs` → Notion

## The differentiator to demo
**Replay/audit:** reset a consumer group to offset 0 and replay the stream to show *exactly what each
agent saw and did* — the auditability answer to the "black-box agent" objection (and the exact question
to put to Ahmed Zamzam: "has anyone used Kafka replay for post-incident agent audit in production?").

## Verify before building
- Whether the full `CREATE AGENT` / `AI_RUN_AGENT` "Streaming Agents" syntax is worth it vs chaining
  `ML_PREDICT` statements (start with the statement chain — higher certainty).
- `CREATE TOOL ... MCP` support + how a Flink agent calls an external tool.
- Keyed state / upsert semantics for the per-company brief.
