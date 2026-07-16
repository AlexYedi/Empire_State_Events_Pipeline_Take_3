---
description: "Copy-experimentation plan — hypotheses, sample-size/duration, reporting template, action items. The third link in the copy chain (messaging-brief → channel-copy → test-and-report): designs the A/B plan for the variants and the report that reads it out. Use when A/B testing copy rigorously and tracking to significance."
argument-hint: "[channels + kpis + window, e.g. 'email,ads, ctr,conversion, 14d']"
---

# /test-and-report

Design a **copy-experimentation plan + reporting template** for the A/B variants produced by
`/generate-channel-copy`. This produces the *plan and the read-out template* — Alex (or the channel tool)
runs the actual test and supplies results; this command does not execute live tests. Conforms to
`.claude/references/command-orchestration-convention.md`.

**Grounded use (named friction):** closes the copy chain — without a rigorous test plan, the A/B variants
ship on gut, and "which variant won" is never answered honestly. This is the measure-what-you-shipped link.

## Step 1 — Intake & validate (this thread, not a subagent)
Collect and confirm:
1. **channels** (required) — channels under test. If missing, ask.
2. **kpis** (required) — comma-separated (open, CTR, CVR, CPL, pipeline). Each must be measurable on the
   named channel; flag any KPI the channel can't report. If missing, ask.
3. **window** — reporting cadence (7d | 14d (default) | 30d).
4. **variants** (preferred) — the A/B variants from `/generate-channel-copy`; keep as a `VERBATIM SOURCE`
   block. If absent, offer to run `/generate-channel-copy` first.
5. **segments** (optional) — persona/region tiers to slice by.
6. **baseline volume** (optional but needed for power) — current recipients/impressions per period; without
   it, sample-size is presented as a formula Alex fills in, not a fabricated number.

## Step 2 — Design (serial, this thread — a single specialist, no fan-out ceremony)
This is a design task, not a research fan-out — dispatch **one** specialist. Dispatch **copy-strategist**
(compose `alex:offer-testing` for the statistical guardrails) with the variants + KPIs + baseline volume.
It returns: per-variant **hypothesis** (what changes, expected direction, why), the **primary metric +
guardrail metrics**, and the **sample-size / duration to significance** (from baseline volume + a stated
MDE and alpha/power; if baseline is missing, the formula with the inputs Alex must fill).

## Step 3 — Assemble the plan + reporting template (inline)
Produce: an experiment tracker table (`test | hypothesis | primary KPI | status | owner`); a **reporting
template** (the exact table/chart to fill at read-out, with the significance test named — e.g. two-proportion
z-test for CTR, with the p-value threshold); and an **action rule per outcome** (win → ship + why; flat →
iterate the losing element; inconclusive → extend or increase volume). No orphan metric — every KPI in the
template has a stated decision it triggers.

## Step 4 — Output destination (NAME IT)
- **`conversation`** (default) — present the experiment plan + the reporting template (empty, ready to fill).
- Offer a Notion write (Content Drafts or an experiments page) as an explicit follow-up so results land next
  to the copy — parent-thread MCP only. This dovetails with `/tag-outcome` (the acted-on-value loop): a
  won variant's realized lift is exactly what `/tag-outcome` records against the artifact's goal.

## Failure modes
- **kpis unmeasurable on channel** — flag it and propose a measurable proxy; don't promise a metric the
  channel can't report.
- **No baseline volume** — present sample-size as a formula with named inputs; never fabricate "N = X".
- **No variants supplied** — offer `/generate-channel-copy` first, or design against Alex-described variants.

## Ground-truth references
- `.claude/references/command-orchestration-convention.md` — the required skeleton
- Chain: `/create-messaging-brief` → `/generate-channel-copy` → **/test-and-report** → `/tag-outcome`
- Agents: `copy-strategist`, `voice-editor`
- Skills: `alex:offer-testing`
