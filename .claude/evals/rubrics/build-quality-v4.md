# Rubric: `build-quality@4`

Scope: **build artifacts** in the Empire State pipeline — skills, commands, hooks, reference docs, and code —
**plus** rendered **`deep_read`** content artifacts (the prose Deep Read of the event research brief, ADR-5 / YED-136).
Owned by the eval convention (`rubric_version` = `build-quality@4`; never mutate — bump to `@5`).

**What changed from `@3` (2026-08-21, YED-136):** one **artifact-type-scoped composite cap** added — the **density cap**,
which fires **only for `artifact_type = deep_read`**. For every other artifact type, `@4` is byte-identical to `@3`
(same 5 criteria, same weights, same pass band, same confidence-honesty + completeness caps). `@3` stays valid for
runs scored under it; new runs use `@4`. This is the additive-cap pattern `@2→@3` used for confidence-honesty.

- **NEW — the density cap (deep_read only).** The Deep Read's whole reason to exist is *substance* — historical spine,
  mechanism, cited facts — NOT length. Its section budgets are **hard maxes, never quotas**, and padding to length is
  the failure mode the anti-padding gate exists to prevent (spec: `.claude/proposals/event-field-guide.md`). If a
  `deep_read` artifact shows a **padding signal** — LONG prose thin on grounded facts (a high word-to-cited-fact ratio,
  or long-form prose that asserts facts with no endnotes) that on inspection is **generic-explainer filler**
  ("As enterprises increasingly adopt agents…") rather than legitimate novice on-ramp — the **composite is capped at
  0.65 (→ flag)**. The number-side is mechanized by `bash .claude/hooks/density-check.sh --artifact <path>`
  (words ÷ consolidated endnote count; default flag > 300 words/citation). **The script flags; the judge decides:**
  uncited **novice on-ramp** prose (defining jargon, explaining a mechanism from common technical background) is
  correct and must NOT be capped for being uncited — the cap is for *padding*, not for *teaching*. A section rendered
  honestly short because the evidence was thin is a **pass**, not a shortfall.

Score each criterion **independently 0–1**. Composite = weighted sum, **then apply the caps**.
**Verdict: pass if (capped) composite ≥ 0.70, else flag-for-rework.**

| id | weight | what "good" means |
|---|---|---|
| `correctness` | 0.30 | Does what its spec/PRD/issue/AC says. Logic sound; references real tools/DB-ids/files; if code, it parses/runs. **For `deep_read`: every stated fact is web-verified or web-re-grounded; jargon defined correctly; mechanisms accurate.** |
| `completeness` | 0.20 | All required parts present; covers the AC; no TODO stubs; handles obvious edge/failure cases. **Cap ≤ 0.60 if a load-bearing referenced file/rubric/doc does not exist.** **For commands: cap ≤ 0.35 if the orchestration skeleton is absent (agents listed but never dispatched, or no named output destination).** **For `deep_read`: the required sections present at appropriate depth, endnotes consolidated, no `> Gap` left silently unresolved.** |
| `convention_adherence` | 0.20 | House conventions: file placement + frontmatter, naming (**project** skills in `.claude/skills/` take NO `alex:` prefix), source-of-truth discipline, MCP/tool + Notion-plan constraints (`notion-search` not `notion-query-data-sources`), SDK constraints (fan-out from parent thread; MCP writes parent-thread only). **For `deep_read`: prose-not-lattice; jargon defined inline; citations as ENDNOTES not inline (audio-clean); provenance discipline (no `notion-prior` stated as fact without web re-grounding — Rule 12).** |
| `anti_pattern_avoidance` | 0.20 | Avoids: over-engineering/ceremony, duplicating state, resurrecting a tombstoned decision (gtm-os/Langfuse; Supabase-as-*measurement*-store — but Supabase IS the sanctioned Market-Intelligence store), fabricated numbers/specificity, orphan metrics, hardcoded secrets, lossy summarization where fidelity matters, speculative surface with no named friction. **For `deep_read`: no generic-explainer padding, no bullet-lattice fallback, no duplicating the Scan head or `pre-event-content`'s outbound copy (triggers the density cap when it inflates length).** |
| `diagnostics` | 0.10 | Legible + maintainable; clear comments/errors; failures explicable; **honest about gaps/confidence** (no overclaiming; a skeleton presented as finished, or an unverified claim stamped "verified", is dishonest framing). **For `deep_read`: `> Gap` notes present where evidence was thin; company-reported vs. audited distinguished.** |

### Composite caps (applied AFTER the weighted sum)
1. **Confidence-honesty cap → composite ≤ 0.65** when an unverified/uncited claim is asserted as verified (any criterion may detect it; the cap fires regardless).
2. **Density cap → composite ≤ 0.65** when `artifact_type = deep_read` AND a padding signal (per `density-check.sh`) is, on inspection, generic-explainer filler rather than legitimate on-ramp. Does NOT fire for other artifact types, and does NOT fire on honestly-short sections or on uncited-but-legitimate novice on-ramp prose.
3. (Inherited per-criterion completeness caps above: dangling-reference ≤ 0.60; command-skeleton-absent ≤ 0.35.)

### Per-criterion anchors (≥1 pass, ≥1 fail)
- **correctness** — pass: a hook tested to emit a valid record; a Deep Read whose every funding/CVE/metric claim traces to an endnote URL. fail: references a tool/DB that doesn't exist; a Deep Read asserting a thesis claim with no source.
- **completeness** — pass: methodology + failure-modes + references *that all exist*; a Deep Read with all warranted sections + consolidated endnotes. fail: an AC item silently unaddressed; `TODO` left in; a Deep Read dropping the Companies section though companies were researched.
- **convention_adherence** — pass: correct placement/frontmatter; a Deep Read in flowing prose with endnote citations and inline-defined jargon. fail: hardcoded secret; a Deep Read that regressed to a bullet lattice or put URLs inline.
- **anti_pattern_avoidance** — pass: contract-first lean foundation; a Deep Read that runs short because evidence was thin. fail: builds the platform when "lean" was decided; a Deep Read padded with "as enterprises increasingly adopt AI…" filler (also triggers the density cap).
- **diagnostics** — pass: comments explain the contract; a Deep Read that flags `> Gap` on a missing URL. fail: opaque failure mode; overclaims certainty; asserts unverified as verified (also triggers the confidence-honesty cap).

### Machine-readable
```json
{
  "rubric_version": "build-quality@4",
  "pass_band": 0.70,
  "criteria": [
    {"id": "correctness", "weight": 0.30},
    {"id": "completeness", "weight": 0.20},
    {"id": "convention_adherence", "weight": 0.20},
    {"id": "anti_pattern_avoidance", "weight": 0.20},
    {"id": "diagnostics", "weight": 0.10}
  ],
  "composite_caps": [
    {"when": "confidence-honesty violation (unverified claim asserted as verified)", "max": 0.65},
    {"when": "artifact_type=deep_read AND density padding signal is generic-explainer filler", "max": 0.65, "mechanized_by": ".claude/hooks/density-check.sh"},
    {"when": "references a load-bearing file/rubric/doc that does not exist", "max": 0.60, "criterion": "completeness"},
    {"when": "artifact_type=command AND orchestration skeleton absent", "max": 0.35, "criterion": "completeness"}
  ]
}
```
