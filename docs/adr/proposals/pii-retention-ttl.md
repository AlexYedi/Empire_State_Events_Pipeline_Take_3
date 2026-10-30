# DRAFT ADR — PII Phase 2: retention/TTL for `person` and `claim` rows

**Status:** PROPOSAL — not adopted. Alex decides. (S-04, YED-183; docs lane — this file changes no code, no DDL, no config.)
**Builds on:** [ADR-9](../ADR-9-pii-boundary.md) — specifically its "Consequences" section, which **deliberately deferred** retention/TTLs as "a future ADR". This is that future ADR, in draft.

## Context

ADR-9 (accepted 2026-09-13, YED-81) settled *where* personal data may live: email and phone never enter the Supabase spine (tier 2); contact detail lives in HubSpot. It did **not** settle *how long* spine rows that legitimately exist — a person's professional-public identity, a claim about what a speaker said — are kept.

Two reasons this question now has a date on it:

1. **ADR-9 unblocked YED-160 (post-event → MI) and YED-161 (whole-inbox scan).** Both multiply the rate at which `person` and `claim` rows accumulate. The graph today only ever grows; nothing expires.
2. **The tier-2 table is scanned free text.** `person.bio`, `person.role_context`, `claim.claim_text`, `claim.quote` are pro-grade but human-authored at ingestion time; the Python guard scans them at the write chokepoint. A row that was clean on write-in can become stale relative to what the person would want retained, with nothing revisiting it.

There is currently **no deletion path at all** for spine rows other than a hand-run `curl`/dashboard delete — which ADR-9 invariant 1 actively discourages (no hand-rolled writes). So "delete it later" has no mechanism today.

**Do-nothing baseline (the metric every option below is priced against):** keep rows forever, delete nothing automatically. Cost today: $0, zero code, zero risk of deleting something wanted. Cost grows linearly with events attended, and the "stale row" exposure never improves.

## Options

### Option A — Status quo (do nothing)

Keep the ADR-9 deferral permanent. Rows live forever; deletion stays a manual, hand-run exception.

- **Pros:** zero work; nothing can be wrongly deleted; simplest to reason about.
- **Cons:** the exposure ADR-9 deferred never shrinks; "no mechanism" is also true for legitimate cleanup after a bad ingest; graph size and retrieval noise grow monotonically.
- **When this wins:** if the graph stays small (low hundreds of persons, low thousands of claims) and nothing sensitive ever lands. Honest label: this is also the *implicit* current choice — every other option buys something with real money/complexity.

### Option B — Hard TTL via scheduled job (pg_cron / external cron + `spine_client` delete op)

Add a scheduled job that hard-deletes rows past an age threshold.

- **Pros:** simplest mechanism; genuinely removes data (the only real remediation); symmetric with existing "guard refuses, you fix upstream" philosophy.
- **Cons:** hard delete is unforgiving — a bug in the TTL query destroys canonical graph structure (a `person` row carries `company_id` FK and `event_entity`/`claim_entity` links; deletion cascades or orphans them). pg_cron adds a scheduling dependency on the Supabase project. Deleting a person silently breaks `asserted_by` speaker links on historical claims.
- **Kill criterion:** if there is no tested PITR/restore rehearsal (invariant 2's twin-rehearsal discipline), a hard-delete job should not ship.

### Option C — Archive-then-purge (cold table, delayed hard delete)

Rows past a soft age move to an `_archive` schema (same structure, RLS deny-all); rows past a hard age are purged from there.

- **Pros:** reversible by default (archive restore instead of loss); preserves referential history for claims that cite a person who has since "aged out"; matches the two-step DDL discipline the repo already uses.
- **Cons:** two more tables per entity to keep in schema parity (canonical_v2 pattern again); "deleted" is not really deleted until the purge leg runs, so the privacy win is delayed; archive rows can silently rot out of parity with migrations.

### Option D — Tiered, state-driven TTL (recommended)

TTL keyed on each row's own lifecycle state, not a flat age:

| Table | State | Action (proposed) |
|---|---|---|
| `person` | `last_engaged_at` older than **18 months** | flag `stale` in `metadata`, exclude from retrieval ranking |
| `person` | stale AND no `event_entity`/`claim_entity` link touched in **24 months** | archive (Option C's mechanism) |
| `claim` | `status = 'rejected'` | purge after **90 days** (rejected claims carry no signal and may carry quotes) |
| `claim` | `status = 'candidate'`, un-reviewed for **12 months** | auto-archive (never auto-delete — candidates are the only record an extraction happened) |
| `claim` | `status = 'approved'` | **no TTL** — approved claims are the product; review at each widening checkpoint (ADR-12) instead |

- **Pros:** deletion decisions rest on signals the graph already stores (`last_engaged_at`, `status`, link tables), so the blast radius of a bad rule is bounded to rows that were already inert; preserves the historical record that makes the graph valuable.
- **Cons:** the most complex option (state machine, not a cron query); the thresholds are judgment calls this ADR only proposes; needs a `--ttl-report` dry-run mode in whatever script implements it before any delete leg is enabled.

## Recommendation

**Option D**, with Option A as the explicit fallback if the operational cost offends: ship the **report-only leg first** (a dry-run listing what *would* expire), let Alex eyeball one quarter of reports, then enable the archive leg. No hard-delete leg ships until an archive-restore rehearsal has actually been run. `person` hard delete is the least recommended piece of any option here — speaker links on historical claims have no graceful story.

All thresholds above are proposals, not decisions. Adopting any of them is a Phase-2 implementation task (a new spine script + migration for the archive schema), out of scope for this docs lane.

## Consequences if adopted

- One new scheduled job + one archive schema + a `--ttl-report` mode. Implementation PR would be a guarded-path-adjacent change (it writes to the graph) and takes human review under invariant 1's spirit even though it touches no guard file.
- The do-nothing baseline stays available forever: disabling the job returns the system to Option A with no residue except archived rows.
- Metric to track once live: rows expiring per quarter vs. rows re-activated before expiry (the false-TTL rate). If the false-TTL rate exceeds ~5%, thresholds are wrong, not the mechanism.

## Relations

Refines **ADR-9** (the deferred retention item, and tier-2 `person`/`claim` scope). Touches **ADR-12**'s widening-checkpoint cadence (adopted-TTL review belongs on that checklist). Implementation would use **ADR-1**'s canonical project and additive-increment discipline.
