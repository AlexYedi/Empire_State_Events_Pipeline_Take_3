# Spec: Deep Read marker-enforcement gate (YED-139)

**Date:** 2026-08-25 · **Type:** durable guardrail (spec-before-code) · **Branch:** `alex/yed-139-deep-read-gate` · **Linear:** YED-139 · **Builds on:** YED-138 (prompt-level Step 4.5 wiring + fail-loud, merged PR #49)

## Problem

The Deep Read (Step 4.5, rendered by `field-guide-renderer`) can be skipped and the run still closes green. Two independent failure paths already bit us (Aug 2026 batch, 38/38 briefs shipped Scan-head-only):
1. The batch runner never *called* Step 4.5 ("Steps 1–6" excluded the non-integer step).
2. Step 4.5 failed **silent** — a render failure left the `<!-- deep_read_rendered: pending -->` marker and continued.

YED-138 fixed both at the **prompt level** (mandate the step + fail loud). That is discipline, not a mechanism — an LLM that skips Step 4.5 can also skip the prose that says "surface PENDING." YED-139's ask: make a silent skip **mechanically impossible to close green.**

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
- A new Stop hook `deep-read-gate.sh` reads the ledger for the current session; **any `pending` row → emit a loud `⚠️ DEEP READ GATE: FAILED` block** naming the event(s). Wired into the settings.json Stop chain alongside the existing hooks.

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
| LLM skips Step 4.5 silently (the original bug) | Ledger row stays `pending` (default) → Stop hook FAILS + Step 8 FAILS. |
| LLM skips the Step 8 terminal gate too | Stop hook still reads the ledger and FAILS at session end. |
| LLM skips the ledger-append at 4g | The only residual hole. Mitigation: append is a mandatory sub-step co-located with the 4g Notion commit; a run that skips it also skips the commit (fails the event visibly). Cheapest standing safeguard, not perfectly closed — accepted, logged. |
| Ledger says `rendered` but Notion is actually `pending` (drift) | Step 8 re-fetches the real Notion marker and reconciles — authoritative read wins. |
| Session id unavailable to the hook | Hook exits 0 silently (matches existing hook convention — never blocks the pipeline on a hook failure). |
| `jq` / ledger file missing | Hook treats absent ledger as "nothing to check," exits clean (a run that wrote no rows touched no events). |

## Non-goals

- No Notion REST integration (no key in repo; MCP-in-conversation is the read path).
- The hook does not itself *fix* a pending render — it FLAGS; re-running Step 4.5 (idempotent) is the fix.
- No change to the decoupled-by-design property: Step 4.5 failure still doesn't block the Scan-head commit mid-run; the gate simply makes an *unresolved* pending impossible to close green.
