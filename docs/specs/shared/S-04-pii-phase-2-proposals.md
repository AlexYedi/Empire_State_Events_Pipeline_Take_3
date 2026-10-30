# S-04 · PII Phase 2: proposals only (Shared)

**Linear:** YED-183 · **Repo:** Empire_State_Events_Pipeline_Take_3

The guard code is human-only (CLAUDE.md invariant 1). This spec produces **documents for Alex to adopt or reject**. It never changes code.

## Deliverables (factory)
1. `docs/adr/proposals/pii-retention-ttl.md`: a draft ADR on retention/TTL for `person` and `claim` rows. Options with trade-offs, and a recommendation. It MUST cite ADR-9.
2. `docs/adr/proposals/pii-regex-set.md`: the exact proposed regex set (email; E.164 plus US phone), with a table of ≥15 true-positive and ≥15 true-negative test strings (all `*.example`/fake). It MUST compare against the patterns `spine_client.py` uses today, by reading them, not changing them.
3. `docs/adr/proposals/pii-db-check.sql`: a **proposed, not applied** CHECK/trigger on `person`, as a new migration draft under `docs/adr/proposals/`, not `supabase/migrations/`.

## Must not touch
`spine_client.py`, `inbox_boundary.py`, `supabase/migrations/`.

**Done when:** the three files exist and the PR is labelled for human review.
