# Fix: the batch runner never rendered the Deep Read (brief-v2 regression)

**Date:** 2026-08-24 · **Type:** diagnostic-driven fix (retrospective one-pager, not a pre-build PRD — the diagnosis *was* the spec) · **Branch:** `fix/deep-read-batch-wiring`

## Symptom
Tonight's Shortlist event brief (and every event batched Aug 24–27) read thinner than ever: the Event page had the scannable head but the `## Deep Read` section was a literal placeholder — `<!-- deep_read_rendered: pending -->`. All the depth (enhanced company analysis, trends/segments, signal log) now lives in the Deep Read, so an unrendered Deep Read = a thin brief.

## Root cause (verified, not theorized)
The brief-v2 work (YED-136, ~Aug 21) split the brief into a **Scan head** (Steps 1–4) + a decoupled **Deep Read** rendered in **Step 4.5** by `field-guide-renderer`. Two independent gaps left Step 4.5 un-run:
1. **`check-new-events` never called it.** The batch runner said *"Follow Steps 1 through 6 of /event-deep-research."* Step 4.5 is not an integer step, so it was structurally skipped. Grep confirmed: **no version of `check-new-events.md`, reachable or dangling, ever referenced Deep Read / Step 4.5 / field-guide** (`deep-read-refs=0` across all 38 historical blobs). This was an omission, never a lost commit — the shared-checkout churn restored the *files* but the integration was never made.
2. **Step 4.5 failed silent.** "Decoupled by design" meant any render failure (incl. a session predating the agent's registration) left the `pending` marker and continued — so the most valuable layer was the first thing to silently vanish, discovered only the night of the event.

## Fix (this branch)
- `check-new-events.md`: Step 6a now mandates Step 4.5 explicitly (with the registry precondition); the per-event 6c prompt shows Deep Read rendered/PENDING; Step 7 summary gains a **"Deep Read PENDING"** block; a Failure-modes bullet forbids reporting an event "complete" with an unrendered Deep Read.
- `event-deep-research.md`: Step 4.5e now **fails loud** — a `pending` marker must appear in the run/batch summary, never a silent degrade.

## Adversarial pre-mortem + residual risk
- Agent skips 4.5 anyway → the summary still surfaces PENDING (backstop).
- Renderer unregistered → precondition forces an up-front declaration + lists all pending.
- **Residual (accepted for now):** enforcement is prompt-level, not a hard code gate. The robust version is a post-run/Stop hook that queries Notion for `deep_read_rendered: pending` and alerts. Logged as a follow-up (stronger enforcement), not built here.

## Also shipped this session (not code)
Re-rendered the Shortlist Deep Read end-to-end (4-specialist fan-out → 5-section Opus render → append to Event page + research_brief). Then the Aug 25–27 backlog sweep.
