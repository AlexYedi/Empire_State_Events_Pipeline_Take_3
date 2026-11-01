# Writer finding: the nulling-PATCH writer on `public.person`

**S-04 (YED-183) D1 · 2026-11-01 · Author: Obvious (autobuild), for Alex's review**

This resolves the promotion prerequisite recorded in `docs/adr/proposals/pii-db-check.sql`
(prerequisite item 4): *"find the nulling-PATCH writer that keeps the legacy
public.person `email` column alive, then drop the column."* Sequence approved by
Alex 2026-11-01 (YED-183 comment `dd28915c`).

## The finding

**The nulling-PATCH writer is the one-time YED-81 email-null migration — a
manual operational PATCH, not a standing code path.**

When ADR-9 was accepted (2026-09-13, YED-81), the plan called for a one-time
scrub of the legacy `email` column:

> one-time REST `PATCH /person?email=not.is.null` → `{"email": null}` once ADR-9
> is accepted (rows exported to a gitignored file first).
> — `docs/archive/proposals/yed-81-sec-pii-guardrails.md`, Sketch item 4

The YED-81 decision log records how it was executed:

> `2026-09-13` — build-time decisions: … *nulling any column is always allowed,
> setting requires the allowlist* **(the migration runs through the guard)** …

That one-time scrub did its job — every `person.email` value was nulled (re-verified
as 0 populated rows during the PR #235 review of YED-279) — but **nobody ever
dropped the column**. The empty column has sat on `public.person` ever since, which
is exactly why Part 2 of `pii-db-check.sql` as first drafted (refuse on column
*existence*) blocked every write to `public.person` (YED-279 defect 1), and why the
column is the recorded promotion prerequisite.

## Guard-bypass check (YED-183's revisit trigger)

CLAUDE.md invariant 1 says every spine write goes through `spine_client.py`. The
nulling PATCH **did** go through the guard: the YED-81 decision log states "the
migration runs through the guard," and the guard's nulling rule
(*any column may be nulled; setting requires the allowlist*) is what let a
`{"email": null}` PATCH pass while `email` is forbidden to set. That is the
designed behavior, not a bypass — the selftest case "PATCH nulling email → pass"
(`spine_client.py` line 443) documents precisely this path. **No guard-bypass
moment to escalate.** Caveat stated plainly: the guard-routed execution is what
the repo records show; the live execution log lives in Supabase, which this task
does not touch.

## Hunt record (what was searched, 2026-11-01)

| Where | What was looked for | Result |
|---|---|---|
| `.claude/scripts/*.py` (live) | any writer sending `email`/`None` in a person PATCH; any full-row person write | none — the only `email: None` is the guard selftest case |
| `substrate.py` PATCH sites | column-nulling PATCHes on person | merge tombstones null `relevance_score` only (an allowlisted `_MI_COMMON` column); never `email` |
| `_fill_missing` | silent writes | skips null/empty values — never writes them |
| Pruned scripts (git history, `8b79a12` and parents) | retired writers | `backfill_people.py` wrote person fields **excluding** email by its own header; `identity_probe.py` is read/report only |
| Git history `-S '{"email": null}'` | the nulling writer's commit trail | points at YED-81 (PR #73 merge + open-items inventory 3ec5700) — documentation, matching the one-time operational action |
| `supabase/migrations/`, `docs/specs/` | anything reading `person.email` | nothing reads it — the only references are guard selftests and the YED-81 history |

Conclusion: **there is no standing writer to fix.** The offending pattern was a
one-time operational action whose values are gone; the only residual is the
column itself. The fix is the column drop —
`supabase/migrations/0014_drop_legacy_person_email.sql` in the same PR as this
document (no live execution; Alex-gated promotion after twin rehearsal per
CLAUDE.md invariant 2).

## Scope note: `canonical_v2.person` carries the column too

Migration 0006 created `canonical_v2.person` as `like public.person including all`,
so the legacy `email` column exists on both tables and the Phase-2 backstop guards
both. The migration drops it from both, with a catalog guard on the canonical_v2 leg.
