# ADR-11 — Retire the inbox signal lane (supersedes ADR-7)

**Status:** **Accepted 2026-09-28** (Alex, on the prune-sweep recommendation: "execute all recommendations on retiring"). Supersedes [ADR-7](ADR-7-inbox-signal-source.md), whose body stays as the historical record.
**Governs:** whether Gmail is a routinely-mined producer into the Market-Intelligence graph, and the Gmail write scope that ADR-7 granted for it.

## Context

ADR-7 (Accepted 2026-09-12) made the inbox a first-class MI signal source: a two-stage scan (metadata discovery, then allowlist-only body extraction), a `inbox_miner` producer writing `event` + `event_entity` rows, and a Gmail connector expanded from read-only to `gmail.modify` + `gmail.labels` so the miner could label threads in place.

Usage since then, measured at the 2026-09-28 complexity reset (prune sweep, row 16):
- **1 run, 7 threads** (the v1 cohort run of 2026-09-10/11). No Stage A whole-inbox discovery pass and no recurring Stage B run followed.
- **0 uses in the last 30 days.** The morning cron (ADR-7 Decision 4) was never enabled.
- **13 inbox-sourced rows** exist in the graph (`source` prefix `inbox_miner`).

The reset's rule (CLAUDE.md §5) is that every build removes a named friction on the publishing path. The inbox lane removed none. It carried a command, a skill, a writer script, an alias map, a taxonomy reference and a standing Gmail write scope. The scope is the one irreversible-ish authorization in ADR-7, and it sits live on Alex's personal inbox for a lane that does not run.

## Decision

1. **Retire the lane.** Archive to `docs/archive/` (git history kept, nothing deleted):
   - `/scan-inbox` → `docs/archive/commands/scan-inbox.md`
   - the `inbox-miner` skill (incl. `references/aliases.md`) → `docs/archive/skills/inbox-miner/`
   - `inbox_signal_write.py` (the lane's graph writer) → `docs/archive/scripts/inbox_signal_write.py`
   - `signal-taxonomy.md` → `docs/archive/references/signal-taxonomy.md` (no live reader: `role-radar` does not read it, `trend-radar` was pruned the same day, and the inbox miner was the last consumer)
2. **Keep `inbox_boundary.py` in `.claude/scripts/`.** It is not only the lane's scan gate. `spine_client.load_denylist()` delegates to it as the one parser of `inbox-denylist.md` for the ADR-9 tier-0 backstop, and only falls back to a narrower inline parser if the module is absent. Archiving it would silently weaken a privacy layer, which counts as a defect even with a backstop behind it. It stays a guarded path (`judge-build`).
3. **The 13 inbox-sourced rows stay in the graph.** They are sourced, provenance-carrying signal rows. Nothing re-derives or deletes them, and no DML runs as part of this ADR.
4. **The ADR-9 tier-0 inbox denylist check in `spine_client.guard` is untouched.** It still refuses any `inbox_miner`-sourced row from a denylisted sender domain. Changing it is out of scope, and `spine_client.py` is a guarded file.
5. **Revoke the Gmail write scope** (action for Alex, below). Gmail *reads* stay: `company-researcher` and `person-researcher` use `search_threads` / `get_thread` for Gmail-first research.

## Consequences

- The MI graph loses a producer that was not producing. The producer path left is `substrate.py`, per ADR-10.
- `Pipeline/*` labels remain in Gmail. They are harmless, and Alex can delete them by hand at any time.
- History that names the lane stays as written: ADR-7, ADR-8's worked examples, `docs/adr/evidence/`, `.claude/evals/` logs, and the `graph-freeze.*` writer list. The substrate cleanup (PR-E) retires that list.
- Reversing this means a new ADR. Reviving the lane means restoring the archived files and re-granting the scope. Re-granting is the step that needs a decision.

## Action for Alex: revoke the Gmail `gmail.modify` scope granted for this lane

Which surface holds the grant depends on how the claude.ai Gmail connector registers with Google. Both routes are described below. Check which one lists the grant before removing anything.

**Route A: Google Account (authoritative for the OAuth grant)**
1. Go to myaccount.google.com → **Security**.
2. Open **Your connections to third-party apps & services** (older UI: **Third-party apps with account access**).
3. Select the app the Gmail connector authorized as. It is most likely listed as **Claude** or **Anthropic**, and its details show Gmail access including "Read, compose, send…" or "Manage labels".
4. Choose **Delete all connections** (or **Remove access**) and confirm.

**Route B: claude.ai connector settings**
1. Go to claude.ai → **Settings** → **Connectors** → **Gmail**.
2. Choose **Disconnect**.

**Caveat (hedged, roughly 60% confidence):** the connector may request one fixed scope set. If so, there is no read-only re-grant. Removing access also removes the Gmail *reads* that the research specialists use, and reconnecting may re-request `gmail.modify`. If the consent screen offers read-only on reconnect, take it. If it does not, the trade-off is between Gmail-first research and a standing write scope, and that call is Alex's.

## Status history

| Date | Status | Note |
|---|---|---|
| 2026-09-28 | Accepted | Written with the prune-sweep retirement PR (rows 15–17, PR-D). ADR-7's status line is marked superseded; its body is unchanged. |
