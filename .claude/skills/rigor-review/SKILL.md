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
- **Telemetry:** `.claude/.state/telemetry/build-sessions/*.jsonl` (live per-session shards, gitignored since 2026-09-29/YED-229; plus frozen history: `.claude/artifacts/build-sessions/*.jsonl` and the pre-2026-09-12 `build-sessions.jsonl`) — build sessions, `user_prompts` (feedback rounds), `build_dir_touched`, output/peak tokens.
- **Judge:** `.claude/evals/logs/*.jsonl` — scores + `alex_ack` (for the agreement rate).
- **DoD waivers:** the waiver log (US-1).
- **Outcomes:** Content Drafts tagged this week (`/tag-outcome` results) — Outcome vs Goal.

## Step 2 — Review against the registry (only the action-triggering metrics)
**First, run the null-model check — before reading any metric as good news:**
`bash .claude/hooks/run-canaries.sh` then `python3 .claude/evals/calibration_stats.py --gate`.
Any seat reported `null-model: unvalidated` is no better than always saying "pass" and cannot auto-accept,
whatever its agreement rate looks like. **A metric within +0.10 of its do-nothing baseline is not evidence.**
(YED-212: "83% agreement" was the always-pass baseline for 63 days, and the gate's 80% threshold sat below it.)
Ask the same question of any NEW metric before trusting it: what does this score when the system does nothing?
- build-quality scores < 0.70 — were they reworked?
- corrective-rounds ÷ value — trend up?
- DoD waiver-rate — climbing / clustering on builds?
- **gate failures (YED-228, added 2026-09-27):** count `*_gate_failed` and `*_gate_abandoned` rows in `.claude/artifacts/deep-read-gate-failures.jsonl` and `substrate-gate-failures.jsonl` — **excluding superseded rows**: a `gate_false_positive_correction` row voids every earlier failure row from the same `session` (the logs are append-only, so corrections never delete). Filter: `jq -s '(map(select(.event=="gate_false_positive_correction")) | map({(.session): .ts}) | add // {}) as $c | map(select((.event|test("_gate_(failed|abandoned)$")) and (($c[.session] // "") < .ts or ($c[.session] == null))))' <log>`. Before YED-228 the gates logged one false row per turn of an in-progress run (9 in session b7b796e0, all superseded); after it, any live row is a real skip or an abandoned run — each one gets a named cause in Step 4.
- judge–human agreement (from `alex_ack`) — **is it ≥ +0.10 above the always-pass baseline on the same rows?** Raw agreement alone means nothing (YED-212)
- **ack hygiene (the labeler is a rater too):** what share of escalations did Alex simply agree with, and how fast? A reflexive-agree pattern turns the ground truth into a constant and makes every κ undefined
- acted-on outcome vs goal — trending which way?
- **identity hygiene (YED-47, added 2026-09-27):** run `.venv/bin/python .claude/scripts/identity_probe.py` (read-only). Two registry rows: *identity ambiguity* (distinct ledger entries in 30d; **≥10 reopens the parked DDL half** — the `name_norm` / `entity_alias` / `entity_merge` issue) and *identity duplicates* (exact dupes + qualifier twins + host/LinkedIn collisions + tombstones-with-edges; **any pair → propose it with `substrate.py merge … --dry-run`; Alex approves every merge**, never the agent). Null baseline: an absent or empty ledger over **0 producer sessions** is "no data", not "clean" — read it beside the session count the probe prints.
For each that crosses its threshold, take the registry's named **action**.

## Step 2.5 — Container-rule audit (added 2026-09-18)
Run `grep -rniE "awaiting decision|revisit (after|when)|do not build (now|until)|not yet (built|wired)|deferred (to|until|upgrade|\()|\bparked\b" .claude docs --include="*.md" | grep -vE "\.claude/(artifacts|events|evals/logs)/" | grep -viE "YED-|GTM-|notion\.so|notion\.site|platform-constraints|backlog-triage|open-items-inventory|prd-template|systems-analyst\.md"`. Skim the hits: rule text, quoted history, and design-by-design deferrals (ADR "detail deferred to PRD") are noise; every hit that is a *live* parked/deferred/decision thought without a home pointer gets filed (Linear or Notion Project Ideas) in the same review and add the ID to the line. Record the hit count in Step 4; a rising count is the container rule failing. **Then run `python3 .claude/hooks/check-tombstones.py --all`** (YED-201 Fix 2A): lines still naming a removed tool/decision. Baseline = **0** (YED-200 drained 71 hits / 20 files to 0 on 2026-09-19). Record the count; any hit above 0 means a removal didn't propagate: fix it in the same review, or add a removal word next to a legitimate historical mention.

## Step 2.6 — Second-fix recount (added 2026-09-27)
Check whether the second-fix stop rule (`.claude/references/second-fix-stop-rule.md`) is changing behaviour. From the week's `git log --since="7 days ago" --name-only` plus judge-log filenames, list every system component (file, skill, hook) changed by **≥3 separate fix commits**, and every build with **judge round ≥3**. For each one, check the week's transcripts for an `alex:cto-principal-architect` dispatch *between* fix #2 and fix #3. Record: `spirals: N · with architect review: M`. If M < N for 3 straight weeks, the prose rule isn't working: propose promoting the nudge hook to an `ask` gate. Don't add more prose.

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
- Can run alongside the Sunday Upcoming Week roundup; this one is the *build-rigor* review.
