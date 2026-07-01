# Market-Intel graph — one-time Notion → graph entity backfill (runbook)

Seeds the graph's entity tables (`company`, `topic`, `person`) from Alex's existing Notion knowledge graph
so the `/ops/market-intel` dashboard has an immediate watchlist + non-zero counts. **One-time data op**, not
a recurring Hub feature. REST only (never the Supabase MCP — removed). Read-before-write dedup throughout.
Coordinates + rules: `.claude/references/market-intel-spine.md`.

## Setup
- Read `SUPABASE_API_KEY` (sb_secret) from `.env` — never print it. Base:
  `https://oicikjyzmxqfomrrqkvf.supabase.co/rest/v1`. Headers: `apikey`, `Authorization: Bearer <key>`,
  `Content-Type: application/json`, `Prefer: return=representation` (+ `resolution=merge-duplicates` on upserts).
- Enumerate Notion rows via `notion-fetch` on each data source / `notion-search` scoped to it (NOT
  `notion-query-data-sources` — plan-gated). Verify live property names first.

## Mapping (Notion DB → graph table)
| Notion DB (data_source) | → table | Field map |
|---|---|---|
| **Companies** `collection://d5910dc3-8327-4b49-9294-fc9499709a98` | `company` | `Company Name`→name · `Description`→description · `Website`→website · `Industry / Space`→industry[] · `Funding Stage`→funding_stage · page id→notion_page_id |
| **Topics** `collection://d61ce9df-94b3-4637-aa09-d77e09ab3a74` | `topic` | `Topic`→name · `Current Events` (trimmed)→description · page id→notion_page_id |
| **People** `collection://4a1af67f-9141-4ba5-aa9d-88b07dcd5f86` | `person` | `Name`→name · `Current Title`→title · `LinkedIn URL`→linkedin_url · `Known POV / Bio`→bio · `Role Context`→role_context · `Company` relation→company_id (resolve after companies) · page id→notion_page_id |

All rows: set `source='notion_backfill'`. Leave `relevance_score=0`, `engagement_count=0` (computed later).

## Order & dedup (write companies + topics first, then people)
1. **company / topic** — `GET /<table>?name=eq.{name}&select=id`. If found → PATCH notion_page_id/fields; else
   `POST` (unique index on `lower(name)` also protects against races — `Prefer: resolution=merge-duplicates`).
2. **person** — no hard unique (people share names): `GET /person?name=eq.{name}&select=id,company_id` and
   disambiguate by company; insert only if no match. Resolve `company_id` by looking up the company row by name.

## Verify
- `GET /company?select=id` / `topic` / `person` counts == Notion row counts (allow for SKIP/dupes you chose to merge).
- Spot-check 2–3 rows have `notion_page_id` + `source='notion_backfill'`.

## Notes
- People appear on the dashboard as a **count only** (privacy-by-design; names not surfaced) — but full rows
  are stored so future lenses/producers can use them.
- Idempotent: safe to re-run; read-before-write + `lower(name)` unique prevent duplicates.
- If a Notion DB is large, batch by page; log what was covered vs. skipped (no silent truncation).
