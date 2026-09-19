# ADR-10 — The Knowledge Substrate: claims first-class, documents generalized, one producer path, one retrieval path

**Status:** Proposed 2026-09-18 — decisions 1–5 ratified by Alex in session (below); moves to **Accepted** when migrations 0009 + 0010 are live on prod and the W1 A/B (YED-172) has run.
**Governs:** the Market-Intelligence Supabase graph's data model beyond ADR-0…4 — how claims, documents, entities and events relate; the single producer path into the graph; the single retrieval path out of it.

## Context

The goal (Alex, 2026-09-18): turn everything the system produces — events, companies, people, topics, briefs, transcripts, learnings, research — into one cohesive source that elevates future event research, content, job hunting, writing, project ideation and software development.

What existed fell short in three measured ways (`.claude/notes/yed-160-scope-2026-09-17.md`):
- **No repeatable producer.** No Notion→graph event path ever existed. The 61 `attended` rows came from a one-off migration sourced from the now-frozen gtm-os spine, plus two ad-hoc curls. By 2026-09-17, 24 of 27 recent events were absent and no person had been added since 08-06. `/post-event-content` Step 3.8 was *named* "Knowledge-graph write-back" and wrote Notion only.
- **Nowhere for knowledge to live.** Entities and events had a home; what was *said or learned* did not. `doc_claims` was a staging table whose only exit was promotion into `event` rows — one fake occasion per claim.
- **A thin read side.** One consumer (`/event-deep-research` Step 1.7a) pulled at most 8 Notion bodies, treated an empty graph as normal ("graph: no signals"), and could not see across events.

Systems read: *Shifting the Burden* — Notion absorbed "where do learnings go?", so the graph producer was never built, and the one-off migration masked the gap.

## Decision

| # | Decision | Why |
|---|---|---|
| 1 | **Claims are first-class and point at events; they are never promoted into events.** One `claim` row per atomic assertion from any source (talk, book, email, transcript, retro), with `provenance_tier`, `confidence`, `asserted_at` (when it was said), an embedding, and links: `claim_entity` (about / **asserted_by** — the canonical speaker link) and `claim_relation` (contradicts / corroborates / supersedes / refines). | The standard assertion / occasion / entity split. Promotion minted N events per occasion, conflated "said" with "happened", and corrupted the hub's producer semantics. Recency ranks on assertion date, not ingest date. |
| 2 | **Documents are generalized to every artifact with a body** (briefs, Deep Reads, transcripts, posts, dossiers, retros), versioned by `external_ref` with exactly one `is_current` row per ref, linked via `document_entity`. | One home for artifacts; a revised brief supersedes rather than duplicates. |
| 3 | **One producer path:** `.claude/scripts/substrate.py` (ensure-entity · ensure-event · ensure-document · stage-claims · backfill), every write through `spine_client` (ADR-9). **Backfill runs through the producer** — there is no separate backfill script. | Makes the 2b failure class (a one-off writer the live pipeline cannot reproduce) structurally impossible, not merely discouraged. |
| 4 | **One retrieval path:** `.claude/scripts/retrieve.py --lens`, returning a token-budgeted Context Pack with an audit line; **loud failure** when the graph holds claims for the seed entities but the pack kept none. W1 ships the `event` lens; other lenses follow the A/B. | Ingestion without retrieval is a landfill. The read path must fail loudly, or a filled substrate silently stops being read. |
| 5 | **Additive-first migration.** 0009 (S1a) adds tables/columns and two widenings; its rollback drops only what it added and stays valid after data lands. The mutating identity half (`name_norm` unique indexes, `entity_alias`, `entity_merge`) is **S1b, week 2** (YED-47). Every migration is rehearsed on Phantom-Test-Case (`ytfzzsxcxxbejnowmkmk`) via `supabase/scripts/rehearse_s1a.py`, including a planted fault the gate must catch and a rollback proven to an identical schema fingerprint. | `migration-playbook.md` moves 5–6 and ADR-4 decisions 2 and 6. The 0-collision identity probe means deferring the unique indexes costs nothing. |
| 6 | **No `observed` event kind** — `attended` keeps its meaning; `event.source` distinguishes the live producer (`substrate:notion`) from the 2b migration. `published` is added; `shipped` is deferred. | Two words for one meaning would be a permanent split every query must remember. |
| 7 | **No Supabase-MCP DDL.** Schema changes stay a dashboard paste Alex reads. The 2026-06-28 rule stands; reversing it needs its own dated ADR. | The original incident was a mis-targeted project; the paste is the only step where a human reads the SQL. |
| 8 | **No ranking on usage until ≥20 outcome rows.** `artifact_outcome` and `claim_usage` exist and log from day one; `w_use = 0` in every lens; `spine_client` refuses writes to `claim.utility_score` / `use_count`. | Ranking on n=3 outcomes is a reinforcing loop on noise. The rule is enforced in code, not prose. |
| 9 | **Attendance is never inferred.** Only events with evidence of attendance (transcript, post-event folder, or Notion status attended/post_complete) get an `attended` row; researched-only events contribute their companies/people/topics without claiming attendance. | The graph's first job is to be true. |

## Consequences

- **Live 2026-09-18 (before any DDL — existing tables only):** entity backfill of 9 attended events, 67 people, 48 companies, 95 hyperedges; second run created 0. All rows `source='substrate:notion'`.
- **`/post-event-content` Step 3.8** becomes 3.8a (Notion) · 3.8b (`ensure-event --expect-claims`) · 3.8c (`stage-claims`), enforced by the `substrate-gate.sh` Stop hook — a sibling of the YED-139 Deep Read gate, with the same fail-closed contract.
- **`/event-deep-research` Step 1.7a** gains 1.7a-S (the substrate pack) alongside the legacy pull for the A/B window; the legacy pull is removed only on evidence (YED-172).
- **`doc_claims`** is deprecated in place (0 rows); S1b drops it. `extract_claims.py` moves to `claim` with S1b.
- **Deferred, deliberately:** S1b identity (YED-47), entity embeddings + `match_entities`, the other four lenses, `/digest` generalization (YED-157), outcome/usage ranking and recompute-v2, the hub trust-strip change, `shipped`, pg_cron (S3).

## Relations

Builds on **ADR-0/1/4** (one graph; expand-contract; twin rehearsal). Writes only through **ADR-9**'s single chokepoint. Refines **ADR-7** (inbox signals become one more producer into the same claim layer). Adds a producer/consumer pair to what **ADR-8**'s system graph can check. Numbered from `main` (stub minted 2026-09-18, `6ea6bde`). Evidence trail: `.claude/notes/yed-160-scope-2026-09-17.md` · `knowledge-substrate-architecture-2026-09-18.md` · `knowledge-substrate-review-2026-09-18.md` · `substrate-vs-reconciliation-sequencing-2026-09-18.md` · `substrate-handoff-to-home.md`.
