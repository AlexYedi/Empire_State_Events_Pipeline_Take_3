---
name: rigor-review
description: "The weekly ≤10-min rigor review — the manual learning loop. Reviews the week's build sessions, judge scores, DoD waivers, and outcomes against the value-action registry; spots recurring corrections; and (HITL) proposes a codified fix for any correction past threshold so feedback turns into durable improvement. A manual ritual, NOT automation."
---

# Rigor Review Skill (weekly, ≤10 min)

This is the **learning loop** — the step that turns feedback into improvement, which the root-cause diagnosis said was missing (corrections evaporated because nothing codified them). Per the systems-analyst, it runs on **human time, not as a built feature**: you review, you decide, the system proposes. Part of the build-rigor layer (PRD US-7 / Linear YED-93).

**Ground rules:** ≤10 min (keep it cheap or it gets skipped). HITL — the system *proposes*, Alex *approves*. Never fabricate; missing data ⇒ say so. Review against `.claude/references/value-action-registry.md` (the action-triggering metrics), not everything.

## Inputs
- **(Optional) Window** — default the last 7 days.

## Step 1 — Pull the week's signals
- **Telemetry:** `.claude/artifacts/build-sessions/*.jsonl` (per-session shards; plus the frozen pre-2026-09-12 `build-sessions.jsonl`) — build sessions, `user_prompts` (feedback rounds), `build_dir_touched`, output/peak tokens.
- **Judge:** `.claude/evals/logs/*.jsonl` — scores + `alex_ack` (for the agreement rate).
- **DoD waivers:** the waiver log (US-1).
- **Outcomes:** Content Drafts tagged this week (`/tag-outcome` results) — Outcome vs Goal.

## Step 2 — Review against the registry (only the action-triggering metrics)
- build-quality scores < 0.70 — were they reworked?
- corrective-rounds ÷ value — trend up?
- DoD waiver-rate — climbing / clustering on builds?
- judge–human agreement (from `alex_ack`) — ≥ 80%? (else judge stays advisory)
- acted-on outcome vs goal — trending which way?
For each that crosses its threshold, take the registry's named **action**.

## Step 2.5 — Container-rule audit (added 2026-09-18)
Run `grep -rniE "awaiting decision|revisit (after|when)|do not build (now|until)|not yet (built|wired)|deferred (to|until|upgrade|\()|\bparked\b" .claude docs --include="*.md" | grep -vE "\.claude/(artifacts|events|evals/logs)/" | grep -viE "YED-|GTM-|notion\.so|notion\.site|platform-constraints|backlog-triage|open-items-inventory|prd-template|systems-analyst\.md"`. Skim the hits: rule text, quoted history, and design-by-design deferrals (ADR "detail deferred to PRD") are noise; every hit that is a *live* parked/deferred/decision thought without a home pointer gets filed (Linear or Notion Project Ideas) in the same review and add the ID to the line. Record the hit count in Step 4; a rising count is the container rule failing. **Then run `python3 .claude/hooks/check-tombstones.py --all`** (YED-201 Fix 2A): lines still naming a removed tool/decision. Baseline 2026-09-19 = 71 hits / 20 files (docs + code) (YED-200 drains it). Record the count; a rising count means a removal didn't propagate.

## Step 3 — Correction-recurrence → propose a codified fix (the loop's payoff)
Identify **same-class corrections recurring across builds** (e.g., "reintroduced a tombstoned decision", "orphan metric", "wrong Notion read tool"). If a class hits threshold (≥ N), **PROPOSE** the codified fix — a rubric bump (`build-quality@N+1`), a DoD tweak, a skill edit, or a few-shot example — and on Alex's approval, apply it (versioned) so it stops recurring.

## Step 4 — Log + tune
- Append to `.claude/evals/correction-recurrence.md` (date · class · count · action).
- If you re-tuned a threshold, record it in the value-action registry (never silently).
- One-line state: "rigor holding / drifting because X".

## Failure modes
- Too much data → review only the registry's action-triggering metrics.
- No recurrences → log "none — system holding"; don't manufacture work.
- **Never auto-apply** a fix — propose → approve. (Automating this loop is a deferred decision.)

## Reuses / references
- `.claude/references/value-action-registry.md` (the metrics + actions) · `.claude/evals/` (judge + calibration) · `build-session-contract.md` (telemetry) · `tag-outcome` (outcomes).
- Can run alongside the content `weekly-recap`; this one is the *build-rigor* review.
