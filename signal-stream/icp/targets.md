# ICP / Target list — the classification ground truth

This file is the "what counts as a GTM signal for Alex" reference. Layer 1a injects a condensed
version of it into the Flink `ML_PREDICT` classification prompt; Layer 1b embeds it for `VECTOR_SEARCH`.

Edit freely — this is the knob that tunes precision/recall of the signal stream.

## What Alex is watching for (relevant = TRUE)
- **AI-native companies** hiring for or led by **enterprise GTM / sales / CS** roles (Alex's job search).
- **Funding / exec-change / product-launch / layoff** signals at **AI infra + GTM tooling** companies.
- **NYC AI ecosystem** events, meetups, and community moves.
- Movement in Alex's **build stack** (Claude/Anthropic, Notion, Supabase, Confluent, Linear, PostHog, Vercel).
- The **"agents on streaming data"** and **"replace SaaS with AI-built apps"** theses (his current content lanes).

## Target companies / spaces (non-exhaustive — extend)
- Data / streaming infra: Confluent (IBM), Databricks, Snowflake, Redpanda, ClickHouse
- AI app builders: MindStudio/Remy, Lovable, Replit, Cursor, Vercel, Retool
- GTM / AI-sales tooling: Clay, Apollo, HubSpot, Attention, Spara
- Voice AI: AssemblyAI, LiveKit, Deepgram, ElevenLabs, Cartesia, Boardy
- Agent infra / MCP ecosystem: Anthropic, OpenAI, LangChain, the Agentic AI Foundation

## Not relevant (relevant = FALSE)
- Generic consumer tech, crypto price moves, non-AI enterprise IT, pure hardware.
- Anything with no tie to AI GTM, Alex's stack, the NYC ecosystem, or his content theses.

## Output contract (what the classifier should emit per event)
- `relevant`: true|false
- `signal_type`: funding | exec_change | product_launch | layoff | hiring | event | thesis | other
- `company`: best-guess company/entity name (or null)
- `why`: one sentence on why it's relevant to Alex
- `confidence`: 0.0–1.0
