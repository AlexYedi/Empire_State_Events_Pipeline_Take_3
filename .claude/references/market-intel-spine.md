# Market-Intelligence Engine — graph spine (system of record)

Canonical reference for the Postgres graph spine that backs the Market-Intelligence Engine
(the lens-agnostic MI/business-analysis/research engine; Job-Search + Content are the two cores).
Plan of record: `.claude/references/roadmap.md` (the former `~/.claude/plans/where-do-we-stand-sunny-puzzle.md` was machine-local and is retired).

## System of record (resolved 2026-06-28)
- **Project:** Supabase org **`A.Yedi`**, project **`empire state ai`** — ref **`oicikjyzmxqfomrrqkvf`**
  (host `oicikjyzmxqfomrrqkvf.supabase.co`). **empire-state-hub has NO Supabase project of its own** — it is
  a read-only PostgREST client of this engine project. *(Note 2026-08-07, YED-130: the ref
  `ytfzzsxcxxbejnowmkmk` — a 2nd project on the A.Yedi account, earlier labeled the "Hub companion" but
  never wired into any code/env — is now repurposed as the MI consolidation **staging twin / test kitchen**,
  NOT the hub's data plane. The hub remains a read-only client of the engine project.)*
- **Access = REST API, NOT the MCP.** Connect via PostgREST at `https://oicikjyzmxqfomrrqkvf.supabase.co/rest/v1/`
  using `SUPABASE_API_KEY` (an `sb_secret_…` key) from `Take_3/.env` — read it at runtime, never print it.
  The secret key bypasses RLS, so reads/writes work. **Verified live 2026-06-28:** full REST smoke test
  passed (insert company + event + hyperedge → read-back → cascade-delete cleanup; all tables back to 0).
- **Supabase MCP REMOVED (2026-06-28).** Alex disconnected the `mcp__claude_ai_Supabase__*` connector
  (it was on a *different* account — org `Same Old Expressions`, projects `GTM_OS_HUB` +
  `Signal_Pipeline_Analytical_Spine`; a schema briefly mis-applied to `abkvgihlbwfloentugtd` was rolled
  back, verified empty). **REST is now the SOLE Supabase path** for Empire State — there is no MCP to
  fall back to. If a Supabase MCP ever reappears, do NOT use it here; REST-to-`oicikjyzmxqfomrrqkvf` only.
- **DDL (table creation) is one-time, by Alex in the dashboard.** PostgREST can't run DDL. Apply
  `.claude/references/market-intel-schema.sql` once via the `empire state ai` SQL Editor (or, if Alex
  provides a connection string, via `psql`). All *ongoing* entity/Event writes are REST `INSERT`/upsert.
- **REST upsert pattern** (dedup-on-conflict): `POST /rest/v1/<table>` with headers
  `apikey`, `Authorization: Bearer <key>`, `Content-Type: application/json`,
  `Prefer: resolution=merge-duplicates,return=representation`. Conflict target follows the table's unique
  index (`company`/`topic` on lower(name); `event` on title+date+kind — handle in the call).
- **Notion** writes still go via the Notion MCP, inline in the parent per
  [[project_notion_writes_must_be_parent_thread]]. Migration SQL: `.claude/references/market-intel-schema.sql`.

## Data model (4 first-class objects + 1 hyperedge)
- **`company`** — first-class. `company_type` carries VC/incumbent/startup (VC is NOT a separate object).
- **`person`** — first-class. `title` / `role_context` are attributes (role is NOT a first-class object).
  `company_id` → company.
- **`topic`** — first-class.
- **`event`** — first-class **temporal hyperedge AND the signal model**. `kind` splits it:
  `attended` (Alex participates — meetups) vs `market` / `funding` / `launch` / `exec_move` (happens *to*
  entities) vs `role_posted` / `application` / `interview` (job-lens lifecycle). **A signal IS an event**
  with `kind` + `source` (citation) + `confidence`.
- **`event_entity`** — the hyperedge join. One event links N entities at a point in time:
  `(event_id, entity_type ∈ {company,person,topic}, entity_id, role)`. Polymorphic (activity-stream
  pattern). The investor↔portfolio link emerges through `funding` events (no separate edge table).

## Relevance lifecycle (decay + reinforcement)
Every entity carries `relevance_score`, `last_engaged_at`, `engagement_count`. **Stored now, computed
later** — the weekly recompute (decay by recency, reinforce by re-engagement + upcoming-event proximity)
is a deferred producer. Do not build the recompute until a named friction calls for it.

## Dedup-before-create (mirror of Notion rules #10/#11)
`company` and `topic` have a `lower(name)` unique index — upsert on lower(name). For `person`, search by
name (+ company) before insert (no hard unique — people share names). `event` dedups on
(title, event_date, kind). Always read-before-write.

## Notion mirror
Each row's `notion_page_id` links to the human-readable Notion view. Notion remains the review surface
(comment-based feedback loop); Postgres is the source of truth the agentic layer reads.

## Producers & readers (as of 2026-07-01 — M2)
- **First producer:** `trend-radar` (`/scan-trends` Step 5.5) emits `market`-kind topic Events via REST
  (provenance `source`+`url`+`metadata.sources` mandatory; normalized `confidence`). Voice/role producers = fast-follow.
- **First reader:** the Hub `/ops/market-intel` dashboard (empire-state-hub) reads this graph over REST with
  a server-only client (`MARKET_INTEL_SUPABASE_URL` + `MARKET_INTEL_SUPABASE_KEY`). See M2 plan.
- **One-time seed:** the Notion→graph entity backfill (`.claude/references/market-intel-backfill.md`).
- **Producer health / freshness** (veracity trust strip) is derived from `max(event_date)` + count per
  `source` prefix — no `producer_run` table in V1 (fast-follow only if "ran-but-empty" fidelity is needed).

## Reversal note
Reintroducing Supabase reverses the earlier measurement-layer tombstone. Ratified by Alex 2026-06-28 and
re-scoped in CLAUDE.md `<measurement_rigor_layer>`: the ban applies to the *measurement/eval* layer only;
Supabase is the sanctioned **market-intelligence system of record**.

## Write path (ADR-9 — accepted 2026-09-13, YED-81)
**There is exactly one way to write to this graph:** `.claude/scripts/spine_client.py` (`req()` / `write()`),
or its CLI `.claude/scripts/spine_write.py <table> --json '…' [--patch <filter>]`. Every POST/PATCH body is
guarded before it leaves the machine: per-table column allowlists (`ALLOW`), **email/phone forbidden on every
table**, a recursive email/phone pattern scan through `metadata` JSON, and a tier-0 backstop for inbox rows
(`metadata.sender_domain` vs `inbox-denylist.md`). **Any column may be nulled; only allowlisted columns may be
set.** A violation is hard-fail (exit 2) and names *field · tier rule · fix*; nothing is written. Reads (`GET`)
and `/rpc/` calls are unguarded. `spine_client.py --selftest` is the living acceptance test;
`--check-writers` fails if any script defines another REST writer. Decision record: `docs/adr/ADR-9-pii-boundary.md`.
`person.email` is null for every row and is never written again (2026-09-13).
