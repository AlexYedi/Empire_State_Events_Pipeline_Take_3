# Orchestrator validation — side-by-side comparison

**Created:** 2026-05-05
**Event:** Agentics NYC — "Use AI coding agents effectively" (Wed May 6, 2026)
**Inline-path baseline:** [Wednesday Event page](https://www.notion.so/357d3699c2db81028878c1efd0a55a65) (full brief in body) and its [Content Draft pointer](https://www.notion.so/357d3699c2db81a28374ca42e054b0a7)
**Orchestrator-path artifact:** [\[orchestrator validation\] Agentics — Research Brief](https://www.notion.so/357d3699c2db816792eef9f93adf1caa)

---

## TL;DR

The orchestrator-path brief is the more thorough, schema-faithful research artifact. The inline-path brief is denser and has more product-specific details, but skips the 5-dimension topic structure and Headwinds-per-company that SKILL.md mandates. **Both have unique signal — keep both.** The structural finding (orchestrator did not fan out to subagents) is the dominant takeaway, not the content delta.

---

## Axis 1 — Structural

| Aspect | Inline path | Orchestrator path |
|---|---|---|
| Multi-agent fan-out | N/A (didn't claim to) | **Did not actually happen** — orchestrator collapsed to single-model WebSearch run |
| Agent dispatched cleanly | N/A | Yes — `event-research-orchestrator` was found and invoked via Task tool |
| Schema adherence (event-research SKILL.md Step 3) | Partial — Topics treated as 1-line summaries; Companies as 1-2 line summaries; no Headwinds | Full — 5 dimensions per NEW topic; all 6 fields per company including Headwinds |
| Validation Notes block | N/A | Present (this is the most important output of the run) |
| Run cleanly end-to-end | Yes | Yes (the brief is real and high-quality), but fan-out architecture not exercised |

**Bottom line — structural:** the orchestrator returned a clean brief, but the multi-agent architecture under it is not being exercised. This is logged as a new known-gap in WORKFLOWS.md (the prior gap — "agents not registered at conversation start" — appears resolved; the new gap is "orchestrator does not dispatch subagents").

---

## Axis 2 — Coverage

### What the orchestrator brief covers that the inline did NOT

- **5-dimension treatment for the 2 NEW topics** (AI Agent Memory Layer, AI Coding Agent Infrastructure): Current Events / Opportunities / Challenges / Use Cases / Top Questions — this is the SKILL.md schema, the inline brief skipped it
- **Full Companies treatment** with Description / Recent News / Funding / Industry / Relevance / Headwinds for all five — inline had no Headwinds field anywhere
- **Agentics NYC as a host company entry** — inline brief skipped the host org entirely
- **Specific data points the inline missed:**
  - LOCOMO benchmark for memory evaluation
  - Mem0 latency comparison (1.44s vs 17.12s p95, 91% reduction at 6-pt accuracy cost)
  - Cognee 500x pipeline growth (2,000 → 1M+ runs in 2025)
  - Cognee Pebblebed lead investor detail (Pamela Vagata, OpenAI co-founder; Keith Adams, FB AI Research Lab founder)
  - Vellum customer roster (Drata, Swisscom, Redfin, Headspace)
  - Modal competitor valuations (Baseten $5B, Fireworks $4B) for context
  - Gartner enterprise penetration projection (under 5% → 40% by EOY 2026)
  - Governance gap stats (21% mature governance, 67% executive-acknowledged data breach)
- **Top Questions framework** — 3 pre-built questions per topic, ready to ask at the event (Alex's primary use case)
- **Hit / Partial / Missed scoring criteria** for each Success Signal — makes each signal diagnosable post-event
- **Failure-mode mapping table** in the "88% Problem" Documentarian Angle — concrete layer→failure-mode pairing
- **Validation Notes block** with explicit gaps flagged (Nori funding, Agentics NYC organizer, Modal $2.5B closure status)

### What the inline brief covers that the orchestrator did NOT

- **Modal customer specifics:** Meta (Code World Model) and Scale AI (MCP server orchestration) — high-signal proof points the orchestrator missed
- **Cognee technical phrasing:** "graph-traversal-from-vector-hits approach" — sharper technical specificity than orchestrator's "knowledge graphs as primary memory"
- **Vellum product feature names:** "describe-in-English Agent Builder", "visual canvas", "custom node SDK", "replayable node-level traces" — concrete product surface area
- **Claude Code stat point:** 78.4% on SWE-bench + "4% of public commits" (orchestrator cited 80.8% SWE-bench Verified — note these are different benchmarks; both can be true)
- **Project-ideation tie-back as Success Signal #4** — "Identify whether project-ideation outputs from the topics could materially benefit from Modal hosting (specifically MCP server work)" — this connects to the existing 3 project ideas tied to the event, which the orchestrator missed entirely
- **Prior Snapshots / Retro structure** — event-lifecycle scaffolding for post-event content (the inline brief is on the Event page itself, so it owns the longitudinal view)

### Where the two agree

- Same core thesis: four-layer stack lens (Modal → Nori → Vellum → Cognee)
- Same Documentarian angles in spirit (stack framing + memory underrated)
- Same Nori disambiguation (heynori.com / Tilework, NOT nori.ai health)
- Same Modal funding facts ($87M Series B Sep 2025 at $1.1B; $2.5B talks Feb 2026 with General Catalyst)
- Same Cognee Seed amount ($7.5M) and customer references (Bayer, U Wyoming)
- Same anti-signal (drift to vendor pitches → downgrade)

---

## Axis 3 — Quality (Alex's call)

The two briefs read like two different people prepared for the same event:

- **Orchestrator brief** = the research analyst's work. Schema-faithful, broader research net, more datapoints, scoring criteria for signals, explicit gap-flagging. Better for institutional memory + post-event grading.
- **Inline brief** = the operator's note. Denser, more specific product-feature names, tighter Success Signals, ties back to the project-ideation outputs already in Notion. Better for in-the-room reference.

**My recommendation (Alex's call):** keep both, don't archive either. They aren't redundant — they complement.
- The orchestrator brief is the canonical `research_brief` Content Draft (lives in Content Drafts DB).
- The inline brief is a denser companion that already lives on the Event page itself, doubles as the longitudinal scaffolding (Prior Snapshots / Retro).
- If forced to pick one for the event night itself, the inline brief is more pocket-card useful. For the LinkedIn post afterward, the orchestrator brief has more raw material.

The complementarity here is itself a finding: the SKILL.md schema and a real operator's note want to do different jobs. Future workflow A runs should consider producing both — the structured schema brief plus a 1-page operator distillation.

---

## What changed in WORKFLOWS.md based on this run

1. **Workflow A status:** stays 🟠 but the "Known gap" section is rewritten. The original hypothesis (agents not registered at conversation start) is **resolved** — agents WERE discoverable in this fresh session. The new gap is: **the orchestrator does not actually dispatch subagents** — it executes the research inline using WebSearch.
2. **Recommended near-term workflow:** continue using the inline path as the canonical Workflow A while the fan-out failure is diagnosed (see follow-up artifact).
3. **Path 2 follow-up:** investigate why the orchestrator agent doesn't invoke Task with subagent_type when it should — likely a prompt-level instruction issue in `event-research-orchestrator.md`, possibly compounded by Task being unavailable in the orchestrator's tool set.
