# Spec: Deep Read marker-enforcement gate (YED-139)

**Date:** 2026-08-25 · **Type:** durable guardrail (spec-before-code) · **Branch:** `alex/yed-139-deep-read-gate` · **Linear:** YED-139 · **Builds on:** YED-138 (prompt-level Step 4.5 wiring + fail-loud, merged PR #49)

## Problem

The Deep Read (Step 4.5, rendered by `field-guide-renderer`) can be skipped and the run still closes green. Two independent failure paths already bit us (Aug 2026 batch, 38/38 briefs shipped Scan-head-only):
1. The batch runner never *called* Step 4.5 ("Steps 1–6" excluded the non-integer step).
2. Step 4.5 failed **silent** — a render failure left the `<!-- deep_read_rendered: pending -->` marker and continued.

YED-138 fixed both at the **prompt level** (mandate the step + fail loud). That is discipline, not a mechanism — an LLM that skips Step 4.5 can also skip the prose that says "surface PENDING." YED-139's ask: make a silent skip **fail the run instead of closing green.**

**Honest scope of the guarantee (post adversarial review).** There is exactly **one** deterministic, LLM-independent layer: the Stop hook, and its guarantee is *fail-closed on the local ledger* — it FAILS the run on any `pending` row, any unparseable ledger line, or an empty stdin session id. It is **not** literally "impossible to close green": it is contingent on the ledger `add` happening (the one residual hole, mitigated below) and on the ledger not being bypassed via the documented `waive` / `settings.local.json disable` escapes (both now recorded durably, so a bypass is *visible*, not silent). The second layer (the in-conversation terminal gate) is **authoritative-when-present** reconciliation against real Notion state, but it is skippable by the same LLM — so it is a reconciliation aid, not an independent mechanical guarantee. The durable failure log is what actually retires the Aug-2026 *invisibility* regardless of which layer fires.

## Hard constraint that shapes the design

The `deep_read_rendered` marker lives **in Notion** (on the Event page + the `research_brief` Content Draft). Notion is reachable **only via the in-conversation MCP connector** — there is no Notion REST key in this repo (unlike Supabase), and MCP is unavailable inside shell hooks and subagents. **Therefore a shell Stop hook cannot read the authoritative marker.** Any design that claims a pure-hook Notion check is fiction. The authoritative read must happen in-conversation.

## Design — two layers, fail-closed by default

### Layer 1 — local ledger + Stop hook (the mechanical floor)

A per-session ledger: `.claude/.state/<session>.deep_read_gate.jsonl`, one JSON row per Event page the run touches:

```json
{"event":"<title>","page_id":"<notion-id>","marker":"pending","ts":"<iso>"}
```

- **Written at Step 4g** (Scan-head commit — the unavoidable step every processed event passes through), defaulting `marker: "pending"`.
- **Flipped to `"rendered"`** only on **Step 4.5d** success (Deep Read appended, Notion marker set to a date).
- A new Stop hook `deep-read-gate.sh` reads the ledger for the current session; **any `pending` row (or unparseable line, or empty session id) → FAIL the run** naming the event(s). Wired into the settings.json Stop chain alongside the existing hooks.
- **Durable failure log (review finding #2b): `.claude/artifacts/deep-read-gate-failures.jsonl`.** The Aug-2026 regression was invisible *after the fact* — a perishable transcript message would repeat that. On a close-with-pending the hook appends a `deep_read_gate_failed` row (session, pending count, corrupt count, event list); `deep-read-ledger.sh waive` appends a `deep_read_gate_waived` row. So both a failed close and a self-waive survive the transcript for `/rigor-review` / a human to see. This is the single highest-leverage guarantee: whichever hole leaks, the close-with-pending is *recorded*.

**Why fail-closed:** the row is written at commit time and *defaults to pending*. A run that commits a Scan head but never renders leaves the row pending → the hook FAILS. The only path to a false green is skipping the ledger-append at 4g entirely — so that append is made a **mandatory, co-located sub-step of the commit** (right next to the Notion write the parent cannot skip without failing the event). This converts "did you remember Step 4.5?" from prose discipline into a deterministic, default-fail ledger check that fires on every session end regardless of what the LLM remembered.

### Layer 2 — authoritative terminal gate (in-conversation)

A new explicit **run-close gate step**:
- `check-new-events.md` — new **Step 8** (after the Step 7 summary).
- `event-deep-research.md` — a single-run close gate (for direct, non-batch runs).

The gate:
1. Enumerates the Event pages touched this run (from the ledger + the run's own record).
2. `notion-fetch`es each and reads the **real** `deep_read_rendered` marker.
3. Reconciles against the ledger (catches ledger/Notion drift).
4. **Any `pending`:**
   - **Interactive** → **block close.** Do not declare the run "done." Present the pending list + offer the idempotent Step 4.5 re-run.
   - **Autonomous / batch** → report run **FAILED** with the pending list (per `feedback_ship_all_variants` batch-autonomy: execute fully, but a pending Deep Read is a FAILED run, not a silent pass).

This reads real Notion state, so it is authoritative and is the interactive block; the Stop hook is the deterministic backstop that fires even when the terminal step itself is skipped (the exact failure class).

## Acceptance (from YED-139)

- [x] Run-close step enumerates touched Event pages and their marker state → Layer 2 Step 8.
- [x] Any `pending` marker → FAILED (autonomous) or blocks close (interactive) → Layer 2 + Layer 1 backstop.
- [x] Covered by the build-quality judge / DoD gate → adversarial pass + `/judge-build` + `/dod-close`.

## Adversarial pre-mortem

| Failure | Caught by |
|---|---|
| LLM skips Step 4.5 silently (the original bug) | Ledger row stays `pending` (default) → Stop hook FAILS + Step 8 FAILS + durable log row. |
| LLM skips the Step 8 terminal gate too | Stop hook still reads the ledger and FAILS at session end. |
| LLM skips the ledger-append at 4g | The residual hole. Mitigation: append co-located with the 4g Notion commit. **Not mechanically coupled** (it's a separate parent Bash call, not atomic with the subagent's MCP write) — behavioral reliability, not a guarantee. Stronger fix (harness-drive the row via PostToolUse) logged as a follow-up. |
| **Corrupt/unparseable ledger line** (review #1) | **Fixed.** `_upsert` is line-by-line (a bad line never wipes others; corrupt lines are preserved); counters treat any unparseable line as `pending` (fail-closed). Verified. |
| **FAILED signal not durable → invisible after the fact** (review #2b) | **Fixed.** On close-with-pending the hook appends to `deep-read-gate-failures.jsonl`; waives log there too. |
| **Empty stdin session id → silent miss** (review #4a) | **Fixed.** Empty session id → hook scans *all* `.state/*.deep_read_gate.jsonl` (fail-closed) instead of exiting 0. |
| **Self-waive as a soft-off button** (review #5) | **Mitigated.** `waive` is still LLM-callable, but every waive is written to the durable log, so a self-waive reads as not-green in rigor-review (visible, not silent). |
| Ledger says `rendered` but Notion is actually `pending` (drift) | Step 6.5 / Step 8 re-fetch the real Notion marker and reconcile — authoritative read wins. |
| `jq` / ledger file missing | Hook treats absent ledger as "nothing to check," exits clean (a run that wrote no rows touched no events). |

## Logged follow-ups (from the adversarial review — deferred, not built here)

- **Harness-drive row creation** (review #3, the stronger residual-hole fix): a `PostToolUse` hook keyed on the `notion-writer` dispatch auto-writes the pending row, so skipping it requires skipping the actual write. Retires the "LLM skips the `add`" hole. Larger change (the page_id is created *inside* the subagent's MCP writes, invisible to the hook — needs a coarse commit-vs-render counter instead).
- **`.state` ledger GC + shared-`_pending` scoping** (review #4b): real-SID ledgers and the shared `_pending` bucket are never cleaned; stale rows can produce spurious FAILs under `--resume`. Add a TTL/cleanup and stamp rows with the resolved session id.
- **Concurrent-writer locking** (review, hygiene): the atomic `mv` protects a single write, not the read-modify-write pair — two sessions on one checkout (the documented shared-checkout hazard) can still interleave. Add advisory locking.

## Non-goals

- No Notion REST integration (no key in repo; MCP-in-conversation is the read path).
- The hook does not itself *fix* a pending render — it FLAGS; re-running Step 4.5 (idempotent) is the fix.
- No change to the decoupled-by-design property: Step 4.5 failure still doesn't block the Scan-head commit mid-run; the gate simply makes an *unresolved* pending impossible to close green.
