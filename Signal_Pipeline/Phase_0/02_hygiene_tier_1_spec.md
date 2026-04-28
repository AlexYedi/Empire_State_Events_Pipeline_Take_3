# Phase 0 — Data Hygiene Tier 1 Specification (Living Document)

**Status:** V0, 2026-04-21. First-class workstream. Expected to iterate for the life of the signal pipeline.
**Framing:** This is the rung-1 (data foundation) portfolio asset. Written once here, revised continuously, cited as proof that Alex treats hygiene as first-class craft — which the Clay blog explicitly names as the make-or-break rung for GTME credibility.
**Scope:** Tier 1 hygiene only. Tier 2 (completeness scoring, conflict detection, staleness policies) and Tier 3 (quality gates as tests, LLM eval harness) are referenced at the bottom but deferred.

---

## Why hygiene is a standalone writeup

Two reasons.

1. **Clay's maturity model says so.** Rung 1 (data foundation) is where "most companies stumble." A candidate who shows up with a hygiene document before a modeling document is inverting the industry norm in the direction Clay cares about. That's a positioning asset in itself.

2. **Hygiene is the work that continues forever.** Modeling and activation are projects that ship and are done. Hygiene is maintenance with compounding returns. Documenting it as a living system — versioned, with a changelog — is how you show that you operate like the senior voice in the room and not like someone passing through.

The event-research skill already encodes real hygiene instincts (entity canonicalization, NEW/REFRESH/SKIP triage, audit-trail on refreshes, merge semantics per property). This document formalizes those, extends them across the whole signal layer, and gives them a home that's not buried inside one skill file.

---

## What Tier 1 covers (and what it doesn't)

**Tier 1 = the four things that must exist before any always-on ingestion runs.**

1. Entity identity resolution
2. Source provenance + freshness stamping
3. Schema contracts
4. Dedup / merge rules
5. (Bonus) Suppression list — technically tier-1-adjacent because it enables rather than ensures quality, but we're putting it here because nothing else can ship without it.

**Explicitly not Tier 1:** scoring, attribute engineering, LLM-derived fields, eval harnesses, attribution, freshness decay policies, quality-gate test suites. Those are Tier 2 / Tier 3 and have their own docs when we get there.

---

## 1. Entity identity resolution

### 1.1 — Canonical entity types

The signal layer recognizes exactly these entity types. Anything that doesn't fit one of these doesn't get written until we've decided whether to extend the taxonomy or drop it.

| Entity | Primary identity key | Secondary | Tertiary (last resort) |
|---|---|---|---|
| Person | `email_lower` (lowercased email) | `linkedin_url_normalized` (strip trailing slash, strip query params, lowercase host) | `normalized_name` + `company_domain` |
| Company | `company_domain` (registered domain, lowercased, no protocol, no www) | `normalized_name` (see rules below) | — |
| Topic | `canonical_slug` (kebab-case English) | `synonym_set` reference | — |
| Event | `event_slug` (date + venue + normalized title) | `source_calendar_id` if we ever ingest from calendar | — |
| Signal (a detected raw event) | `source` + `source_record_id` | `content_hash` (fallback for sources without stable IDs) | — |
| Content Draft | Notion page ID | — | — |

### 1.2 — Normalization rules

These are already partially implemented in `.claude/skills/event-research.md` (Step 1.5a). Promoting them here so they're the single source of truth; the skill references this doc rather than defining them inline.

**Company name normalization:**
- Strip (case-insensitive): `Inc.`, `Inc`, `Corp.`, `Corp`, `Corporation`, `LLC`, `L.L.C.`, `Ltd.`, `Ltd`, `Co.`, `Company`, `PBC`, `GmbH`, `S.A.`, `plc`
- Collapse whitespace, lowercase for compare.
- Preserve original casing in `display_name` property.

**Company domain normalization:**
- Lowercase.
- Strip `http://`, `https://`, `www.`
- Strip trailing `/` and any path.
- Preserve subdomain if it's meaningful (rare — usually strip to registered domain).

**Email normalization:**
- Lowercase.
- Strip whitespace.
- Do NOT strip Gmail `+tag` segments (they're a real dedup risk but some people use them consistently as distinct inboxes — flag for Tier 2 decision).

**LinkedIn URL normalization:**
- Lowercase host.
- Strip protocol, `www.`, trailing `/`.
- Strip query params (`?trk=...`).
- Accept both `/in/handle` and `/in/handle-123abc` forms; prefer longest canonical form if both are seen.

**Person name normalization for tertiary match:**
- Lowercase.
- Strip punctuation.
- Trim.
- Do NOT collapse middle names / initials; those are distinguishing.

**Topic slug normalization:**
- Lowercase.
- Replace spaces with hyphens.
- Strip punctuation except hyphens.
- Trailing-s naive plural collapse (noun-only — be careful with words like "labs" where the `s` is load-bearing).
- Maintain a synonym set per canonical slug (see 1.3).

### 1.3 — Topic synonym set

Topic collapse is a one-way decision — merging back is painful — so the rule is: *when in doubt, don't merge*. Maintain a synonym map as data, not hardcoded:

```
agentic-systems: [agentic-ai, agentic-systems, ai-agents, agents]
retrieval-augmented-generation: [rag, retrieval-augmented-generation, retrieval-augmented]
large-language-models: [llm, llms, large-language-models, foundation-models]
gtm-engineering: [gtme, gtm-engineering, gtm-engineer, revenue-engineering]
```

Adding a new synonym is a deliberate change reviewed in this doc's changelog. Agent-generated synonym additions get reviewed by Alex, not auto-applied.

### 1.4 — Entity ID strategy

Every entity gets a stable internal `entity_id` on creation (UUID v7 for time-sortability). The identity key above is used for *matching on ingest*; the `entity_id` is the join key once created. Identity keys can change (email update, domain change) — `entity_id` is invariant.

Resolution on ingest:
1. Apply normalization.
2. Try to match on primary key.
3. If no match, try secondary.
4. If no match, try tertiary.
5. If no match, create new entity with new `entity_id`.
6. If match: return existing `entity_id` and handle property merge per §4 rules.

---

## 2. Source provenance + freshness stamping

Every record in the spine carries these fields. No exceptions. Any row lacking them is Tier-1 non-compliant and flagged for remediation.

| Field | Required | Description |
|---|---|---|
| `source` | Yes | Enum: `events_pipeline`, `notion_manual`, `hubspot_manual`, `rss.<name>`, `apollo`, `clay`, `linkedin_export`, `other` |
| `source_record_id` | Yes if available | The external system's record ID (HubSpot contact ID, Apollo person ID, RSS item GUID). Nullable only when source doesn't expose one. |
| `content_hash` | Yes if `source_record_id` is null | SHA256 of the normalized content of the record, used as a stability key. |
| `fetched_at` | Yes | UTC timestamp of when we first ingested this record. Never changes. |
| `last_verified_at` | Yes | UTC timestamp of when we last confirmed the record is still valid (source re-check or explicit human verification). |
| `last_modified_at` | Yes | UTC timestamp of when we last wrote to this record. |
| `ingestion_run_id` | Yes | The run/job ID that created this record. Enables blast-radius queries if a bad run gets found. |

The existing event-research skill stores `Last Researched` (date only) on People / Companies and `Last Updated` on Topics. Those map to `last_verified_at`. Fine at Notion-UI granularity; the spine will store full UTC timestamps.

**Principle:** provenance is Day-1 non-negotiable. If a record lands in the spine without provenance, we can't answer "where did this come from?" — which is the one question you always get asked in an interview when discussing data systems.

---

## 3. Schema contracts

Each source has a contract defined in code (Pydantic or Zod), stored alongside the ingestion code, and referenced in this document. Violations fail loudly, don't silently coerce.

### 3.1 — Contract template

Every source contract specifies:

- **Source identifier** (matches the `source` enum above).
- **Raw shape** — what the upstream actually sends (freeform).
- **Canonical shape** — what we store after transformation (our schema).
- **Required fields** — what must be present or we reject the record.
- **Nullable fields** — what can be missing; nullable is explicit, not default.
- **Type coercions** — strings to dates, numeric strings to numbers, etc. Document each.
- **Enum mappings** — if the upstream sends "Series B" and our canonical is `series_b`, document the mapping table.
- **Known drift cases** — every source drifts. Document the drifts we've seen and how we handle each.

### 3.2 — Contract stewardship

- Contracts are reviewed at every Phase (Phase 0 / 1 / 2 / ...) — drift during a phase is expected; silent drift is not.
- Contract changes get a changelog entry. Format: `[YYYY-MM-DD] [source] [what changed] [why]`.
- Breaking contract changes (field removal, type change) require a backfill decision: migrate existing data, or mark old data with the old contract version and read both? Document the decision in the changelog.

### 3.3 — First three contracts we'll write

Phase 1 will start with contracts for exactly the three sources the signal discovery method selected. Don't write contracts ahead of ingestion — you'll get the shape wrong. The first three contracts will almost certainly be:

- `events_pipeline` — the existing Notion DBs (authoritative view).
- `rss.<company-careers>` — RSS of a target-company careers page.
- `rss.<news-aggregator>` — a news RSS or Google Alerts feed.

Placeholder; the real list depends on the seed signals.

---

## 4. Dedup / merge rules

### 4.1 — Priority-ordered merge

When the same entity is detected from multiple sources, we keep one canonical record and merge. Source priority ranking (highest trust first):

1. `notion_manual` — Alex wrote it
2. `events_pipeline` — research + Alex-validated
3. `hubspot_manual` — Alex wrote it directly in HubSpot
4. `apollo` — paid enrichment, high confidence
5. `clay` — (if we integrate) paid enrichment
6. `rss.*` — automated feeds
7. `other` — everything else

For each field on an entity, the canonical value is the one from the highest-priority source that has a non-empty value. Never-touch semantics (see 4.3) override this for specific fields.

### 4.2 — Per-property merge rules (defaults)

The event-research skill already has good defaults for People, Companies, Topics. Extending and explicating:

| Property type | Default merge rule | Exceptions |
|---|---|---|
| Identity keys (email, domain, LinkedIn URL) | Fill-if-empty only; never overwrite | If source priority is higher AND the existing value is clearly wrong (human-flagged), explicit override with audit trail |
| Display fields (name, title) | Highest-priority source wins if populated; fill-if-empty otherwise | Person name never overwritten once set (naming errors compound) |
| Multi-select / tag fields (industry, role context) | Union, never drop | Alex may hand-curate; trust existing tags |
| Enumerated state (funding stage) | Overwrite only if new value is chronologically later than the old (Series A → Series B OK; Series B → Series A flag) | — |
| Numeric state (funding amount) | Overwrite with latest if source priority ≥ existing | — |
| Free text (description, recent developments, notes) | Append with dated block; never overwrite | Description: overwrite allowed if existing is empty or stale-obviously |
| Relation fields | Union | — |
| Timestamps (last_verified_at, last_modified_at) | Always update on write | — |

### 4.3 — Never-touch fields

Some fields are sticky once set. Overwriting them causes data rot. The event-research skill's Person refresh path already documents most of these:

- `entity_id` (obviously)
- Person `email`, `phone`, `firstname`, `lastname`, `linkedin_url` — fill-if-empty only
- Person display name — never overwritten once set
- Company `domain` — never overwritten once set unless verified corrected
- `fetched_at` — never changes

### 4.4 — Conflict handling

When two sources disagree on a non-never-touch field (e.g., current company for a person), the highest-priority source wins and the loser gets logged to a conflict log. The conflict log is reviewed periodically by Alex; resolutions can update the source priority or flag a record for manual review.

Tier 2 will add automated conflict detection. Tier 1 just requires that the log exists and is appended to.

### 4.5 — Audit trail

Any destructive merge (overwrite of a non-empty value, destruction of prior data) gets an audit-trail entry. The event-research skill already does this for Company refreshes (prior `Recent Developments` text gets appended to the Event page body). That pattern generalizes:

- When overwriting, append prior value + prior `last_verified_at` + source of prior value to an audit field on the record OR to a linked audit log table.
- The audit trail must survive the merge; you should be able to reconstruct the record's state as of any point in time.

---

## 5. Suppression list

Tier-1-adjacent. Belongs here because no modeling or activation is safe without it.

### 5.1 — Structure

A single suppression table with these columns:

| Field | Description |
|---|---|
| `entity_id` | The entity being suppressed |
| `entity_type` | Person / Company |
| `reason` | Enum: `current_employer`, `active_pipeline`, `personal_contact`, `opt_out`, `cold`, `competitor`, `in_flight_activation`, `other` |
| `reason_detail` | Freeform text — specifics |
| `added_at` | When suppression was created |
| `expires_at` | Optional; nullable. If set, suppression auto-lifts after this date |
| `added_by` | `alex` or `system` (for automatic suppressions like `in_flight_activation`) |

### 5.2 — Default entries on Day 1

These go in before any signal ingestion runs. Non-negotiable.

- GKY Industries (current employer) — `current_employer`
- All active GKY pipeline contacts — `active_pipeline` (Alex to populate)
- Any person with whom Alex has an explicit "not right now" or "cold" signal — `cold` (populate from memory / HubSpot notes)

### 5.3 — Automatic suppressions

Some suppressions fire automatically:

- `in_flight_activation` — when a DM or application is sent, the target is auto-suppressed for N days (TBD; default 14) to prevent double-tapping.
- `opt_out` — when someone explicitly asks to stop; permanent until Alex explicitly lifts.

### 5.4 — Suppression as output

Every play / activation checks the suppression table *as a required step*, not as an afterthought. The scoring logic (Phase 2) takes suppression as a Boolean gate BEFORE any score is computed — not after. If a record is suppressed, it never enters the scoring stream.

---

## Hygiene changelog

This doc is living. Every revision adds a line here with date, change, rationale.

- **2026-04-21** — Initial V0. Formalized the patterns implicit in `.claude/skills/event-research.md` Step 1.5 + 4b–4d, extended to cover source provenance, schema contracts, and suppression as first-class concerns. Open questions flagged below.

---

## Open questions (V0 → V1)

1. **Gmail `+tag` handling for email normalization.** Currently preserve; may want to collapse for dedup. Decide in Tier 2 after observing false-positive rate.
2. **Topic synonym management.** Currently human-curated; will this scale? Decide at 50+ topics.
3. **Source priority for LinkedIn-derived data** (Alex's own exports vs. other sources). Put LinkedIn export above `rss.*` but below `notion_manual`? Think through at Phase 1 when first LinkedIn export happens.
4. **Person `phone` handling.** Sensitive field; Tier 1 currently treats as fill-if-empty never-overwrite. Consider whether to default to not-ingesting phone at all from public sources; only from Apollo-verified enrichment.
5. **Conflict log location.** Standalone Supabase table? Notion page? Append-only log file in the repo? Decide at Phase 1 start.
6. **Entity-ID strategy across Notion ↔ Supabase.** Notion has its own page IDs. Supabase will have our `entity_id`. The join has to be bidirectional and stable. Decide at Phase 1 spine build.

---

## Tier 2 preview (deferred)

Named here only so we don't forget they exist:

- Completeness scoring per entity (0–1)
- Conflict detection and queuing
- Staleness policies with TTL per entity type
- Re-verification scheduler
- Changelog / history preservation for free-text fields (not just audit trail — full diff history)

## Tier 3 preview (deferred)

- Quality gates as automated tests that run on every ingestion batch and can fail a write
- Golden-set + weekly eval runs for LLM-derived fields (eval harness project scope)
- Data contract violation alerts
- Cross-source consistency scans (e.g., "this company has a different industry in Notion vs. HubSpot")

---

## What this doc IS NOT

- Not a schema. The schemas live in the source-contract files next to the code.
- Not a migration plan. Phase 1 decides the migration from Notion-only to Notion + Supabase spine; this doc describes the hygiene rules that apply regardless of where data physically lives.
- Not a set of hard rules unchangeable by Alex. Everything here is revisable. The changelog keeps revisions visible.

## Related docs

- `.claude/skills/event-research.md` — the implementation site for identity and merge rules in the events pipeline (will reference this doc, not redefine).
- `Signal_Pipeline/Phase_0/00_data_inventory_protocol.md` — the audit protocol that identifies current-state gaps this spec addresses.
- `Signal_Pipeline/Phase_0/01_signal_discovery_method.md` — the signal selection method; each selected signal lists its hygiene dependencies from this spec.
- `Signal_Pipeline/Phase_0/clay-play-patterns.md` — the modeling-side reference; this doc is the foundation-side complement.
