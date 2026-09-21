# The graph-write freeze — and how it relates to the substrate gate

**Status:** live since 2026-09-21 (YED-213). Declared in `graph-freeze.json`, enforced in `spine_client.py`.
**Scope:** infra spec (YED-129 ruling: product = PRD, infra = spec). No ChatPRD mirror owed.

## The two mechanisms are not rivals — they watch different halves of one write

| | **Freeze** | **Substrate gate** |
|---|---|---|
| Question | *May this write happen at all?* | *Did a write that happened finish?* |
| Declared in | `.claude/references/graph-freeze.json` | nothing — it is always on |
| Enforced in | `spine_client.req()` | `.claude/hooks/substrate-gate.sh` (Stop hook) |
| Fires | before the PII guard, before the socket | at session Stop, on any `PENDING` ledger row |
| Failure | `GraphFrozen` raised, nothing written | Stop blocked, run cannot close green |

A write during a freeze is refused **before** `ensure-event` reaches the graph, so no `PENDING` gate row is ever
opened. That ordering is the whole reconciliation: honouring the freeze can no longer trip the gate.

## What was actually wrong before

Nothing conflicted in practice, but the freeze was **convention only** — a sentence in
`.claude/notes/ab-protocol-yed172-2026-09-19.md` and an echo in the SessionStart reminder. Nothing refused a write.

The reachable bad state: a run calls `ensure-event --expect-claims` (already violating the freeze, silently),
stops short of `stage-claims` because someone remembers the freeze, and the gate then blocks it — punishing the
run for honouring a rule it had already broken. The gate was doing its job; the freeze had no job to do.

## Design decisions, and why

**1. The marker is a committed file, not `.claude/.state/`.** `.state/` is gitignored *and* per-worktree. A freeze
there would be invisible to every other session — the same blindness that let two sessions duplicate a Notion
namespace on 2026-09-20. Cost: lifting the freeze needs a commit. That is the right price for a rule that must be
visible to sessions that have never spoken to each other.

**2. Enforcement lives at the one write path, not in the producer.** The first implementation gated `substrate.py`.
An adversarial pass asked whether the producer is the only door; it is not. Seven scripts reach the graph —
`spine_write`, `recompute_relevance`, `merge_topics`, `inbox_signal_write`, `backfill_people`, `substrate`, and
`retrieve` (read-only). Gating the producer alone left the freeze bypassable by five other writers, including
`merge_topics`, which hard-deletes. Enforcement moved to `spine_client.req()` on the same argument ADR-9 makes about
the PII guard: **one door, guarded once.**

**3. A corrupt marker fails closed.** An unreadable `graph-freeze.json` yields a synthetic *active* freeze, matching
the gate's corrupt-ledger-line rule. A freeze you can disable by breaking its config file is not a freeze.

**4. `waive` stays reachable while frozen.** It is the escape valve for gate rows opened *before* the freeze was
declared. Blocking it would strand those rows with no legal way to close them.

**5. Overrides are data, not failures.** `GRAPH_FREEZE_OVERRIDE="<why>"` (env, because most writers take no CLI
args) or `substrate.py --freeze-override "<why>"`. Both append to `.claude/artifacts/graph-freeze-overrides.jsonl`.
Same philosophy as a DoD waiver: an emergency must not be silently blocked, and routine use must be visible.

## What is and is not blocked

**Blocked:** `POST` / `PATCH` / `PUT` / `DELETE` through `spine_client` — every graph mutation, from any script.

**Not blocked:** all reads (`retrieve.py`, `identity_probe.py`, the A/B itself) · `--dry-run` · `waive` ·
`preview-claims` · Notion, HubSpot, content, research, telemetry, the judge · **writing code** that will later write
to the graph. Only the *data* is frozen.

## Known gap — read this before trusting the freeze absolutely

**A worktree or checkout sitting on a commit older than the freeze has no `graph-freeze.json`, so its writes are
allowed.** Committing the marker makes it visible across sessions but not across *time*: a stale checkout is an
unguarded one. Mitigations in force today are weak — the SessionStart reminder states whether writes are open, and
`main` carries the marker. A real fix (refusing writes when the checkout is behind `origin/main`, or moving the
marker to a row in the graph itself) is deliberately not built: it trades a small hole for a network call on every
write, and the freeze is expected to last days, not months. **If freezes become routine, revisit this first.**

## Lifting a freeze

Set `active: false` in `graph-freeze.json`, fill `lifted` and `lifted_note`, commit. Do not delete the block — the
history of what was frozen and why is the point. The SessionStart reminder flips to *"No graph-write freeze active"*
on the next session, which is the confirmation signal.

## Tests that pin this

- `spine_client.py --selftest` — 7 freeze cases: each mutating method refused, `GET` open, override proceeds and
  logs, corrupt marker fails closed, absent marker opens writes. Run against a **temp** marker and a **temp**
  override log, so they pass regardless of the live freeze state and can never append to the real audit trail.
- `substrate.py --selftest` — producer-level refusal, `--dry-run` exempt, `waive` reachable, verb coverage, and the
  gate message naming the freeze.
- `test_ab_reminder.py` — the reminder echoes the marker rather than restating the rule.

## Related

`docs/adr/ADR-9` (one write path, PII boundary) · `.claude/notes/ab-protocol-yed172-2026-09-19.md` (the freeze this
was built for) · YED-213 (single-writer rules for shared systems) · YED-172 (the A/B that lifts it).
