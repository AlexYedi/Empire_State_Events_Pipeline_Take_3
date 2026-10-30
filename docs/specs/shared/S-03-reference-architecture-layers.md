# S-03 · Reference-architecture layers (Shared)

**Linear:** YED-126 · **Repo:** Empire_State_Events_Pipeline_Take_3 (the hub view is E-10)

## Product
The 266 topics in the graph are a flat list, with near-duplicates such as "Agent Observability & Management" and "Agent Observability & Monitoring". So the engine can't answer "what's moving in the harness layer" or "where is our own pipeline weakest". Give every topic a `layer` from one Applied-AI Reference Architecture, so both hubs can show signal density per layer.

## Input
`.claude/references/topics-snapshot.json`: every topic's `id` and `name`, exported read-only from `public.topic` on 2026-10-30. Refreshed the same day after the topic soft-merges: `topics` holds live rows only, and `aliases` lists each merged-away row (`id`, `name`, `merged_into`) so name-keyed consumers (the hub's layer view) resolve old names to the live topic. The selftest checks every alias points at a live topic. (The old `signal-taxonomy.md` was retired to `docs/archive/` on 10/24; don't revive it.)

## Technical (factory)
1. **The layers.** New `.claude/references/reference-architecture.md` defining exactly these layer ids, each with a one-line definition and 2–3 example topics from the snapshot:
   `model`, `environment`, `harness`, `factory`, `data-retrieval`, `evals-observability`, `identity-governance`, `gtm-distribution`, `domain-applications`, `market-context`.
2. **The map.** New `.claude/references/topic-layers.json`: `{ "<topic id>": { "layer": "<id>", "secondary": "<id>|null", "duplicate_of": "<topic id>|null" } }` for **every** topic id in the snapshot.
   - `duplicate_of` flags near-duplicate names.
   - It's a proposal only; merging stays with Alex.
3. **The check.** `.claude/scripts/topic_layers.py --selftest` verifies that every snapshot id is mapped, every layer id is valid, and every `duplicate_of` points at a real id. It also prints per-layer counts.

## Must not
Rename topics · write to the `topic` table. If Alex approves, the session applies layers and merges later through `spine_client`.

**Done when:** all 266 topics are mapped, the selftest passes, and the PR body lists the per-layer counts plus the proposed duplicates.
