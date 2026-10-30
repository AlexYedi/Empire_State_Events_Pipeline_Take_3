# S-01 · Graph read loop (Shared)

**Linear:** YED-260 · YED-264 · YED-265 (factory) · YED-261 · YED-262 (Claude Code session, live)
**Repo:** Empire_State_Events_Pipeline_Take_3

## Product
**Problem.** A live read on 2026-10-30 found the MI graph is write-only. `claim` has 4,543 rows (674 added in the last 7 days, all embedded), and `claim_usage` and `artifact_outcome` both have 0 rows. `retrieve.py` exists, but no workflow calls it. 1,004 claims (22%) are linked to no entity, and only 20 of 266 topics have a relevance score.
**Outcome.** Briefs and interview prep read claims; usage gets logged; relevance stays fresh.
**Success.**
- One real event brief cites claims from the graph.
- The company dossier runs for one target company.
- Unlinked claims fall below 5%.
- The nightly recompute runs green three nights in a row.

## Technical (factory executables)
1. **YED-260 · `company` lens on `.claude/scripts/retrieve.py`.** Spec of record: `docs/prd-company-dossier.md`.
   - It MUST reuse the existing scoring and `isolate_job_lens` paths.
   - It MUST add `--selftest` cases on inline fixtures, with no network.
   - It MUST NOT add DDL or a writer.
2. **YED-264 · Entity-link resolver.** A new script, `.claude/scripts/resolve_claim_entities.py`.
   - It reads `claim.proposed_entities` and matches against `company` / `person` / `topic` using the dedup rules in `.claude/references/market-intel-spine.md` (lower(name) for company and topic; name plus company for person).
   - `--dry-run` MUST be the default and MUST print matched / ambiguous / unmatched counts plus the ambiguous list.
   - The write mode MUST call `spine_client.write()` only.
   - Tests use fixtures. **The factory never runs it live.**
3. **YED-265 · Nightly recompute.**
   - First add `--selftest` to `.claude/scripts/recompute_relevance.py`, covering its scoring functions on fixtures.
   - Then add `.github/workflows/relevance-recompute.yml` on a nightly cron that runs the script with `SUPABASE_API_KEY` from repo secrets. Alex adds the secret.
   - Style it after `mi-2b-nightly-healthcheck.yml`.

## Must not touch
`spine_client.py` guard logic or its ALLOW list · `supabase/migrations/` · any live Supabase call in tests.

## Session-side (not the factory)
- **YED-261:** wire `retrieve.py --lens event` into `/event-deep-research` Step 1.7a. A dry run against the live graph is needed.
- **YED-262:** log `claim_usage` through `spine_client`. The table is already on the allowlist.
