# Rubric: `build-quality@5`

Scope: **build artifacts** in the Empire State pipeline — skills, commands, hooks, reference docs, and code —
**plus** rendered **`deep_read`** content artifacts (the prose Deep Read of the event research brief, ADR-5 / YED-136).
Owned by the eval convention (`rubric_version` = `build-quality@5`; never mutate — bump to `@6`).
Pair with the judge system prompt **`prompts/judge-system-v2.md`**.

**What changed from `@4` (2026-09-19, YED-206 — the Gemini rubber-stamp triage):**
`@4` had one pass anchor and one fail anchor per criterion and defined 1.0 as "matches the pass anchor or better", so a
judge that found no fail anchor could legally return 1.0 on everything. The Gemini seat did exactly that on 20 of 23
real prospective artifacts (triage: `.claude/notes/gemini-judge-triage-2026-09-19.md`). Three changes; criteria,
weights and pass band are **unchanged**, so `@5` composites are comparable to `@4`:
1. **The top of the scale must be earned** — 1.0 = "searched this criterion for defects and can name what was checked";
   a **0.85 middle anchor** ("ships with reviewer nits") is added to every criterion.
2. **Defects before scores** — every run returns a `defects[]` list (line/section, criterion, spec ref, severity) *before*
   criterion scores. A run with **all five criteria at 1.0** is recorded `flat_ceiling: true` and treated as
   **low-information** by the quorum (it escalates instead of auto-accepting) — earned 1.0s on a single criterion are fine.
3. **NEW cap — spec drift:** when a spec/ADR/decision record is supplied and the artifact's behaviour **contradicts a
   numbered decision** in it, **correctness ≤ 0.70**. Motivating case: `substrate.py` defaulted event `kind` to
   `'attended'`, contradicting ADR-10 decision 9 ("attendance is never inferred"); one seat praised that line as good
   practice.

Score each criterion **independently 0–1**. Composite = weighted sum, **then apply the caps**. **The harness, not the
judge, computes the composite and the verdict** from criterion scores + cap flags.
**Verdict: pass if (capped) composite ≥ 0.70, else flag-for-rework.**

| id | weight | what "good" means |
|---|---|---|
| `correctness` | 0.30 | Does what its spec/PRD/issue/AC says. Logic sound; references real tools/DB-ids/files; if code, it parses/runs. **Behaviour checked against each numbered spec decision supplied — contradiction caps ≤ 0.70.** **For `deep_read`: every stated fact is web-verified or web-re-grounded; jargon defined correctly; mechanisms accurate.** |
| `completeness` | 0.20 | All required parts present; covers the AC; no TODO stubs; handles obvious edge/failure cases. **Cap ≤ 0.60 if a load-bearing referenced file/rubric/doc does not exist.** **For commands: cap ≤ 0.35 if the orchestration skeleton is absent (agents listed but never dispatched, or no named output destination).** **For `deep_read`: the required sections present at appropriate depth, endnotes consolidated, no `> Gap` left silently unresolved.** |
| `convention_adherence` | 0.20 | House conventions: file placement + frontmatter, naming (**project** skills in `.claude/skills/` take NO `alex:` prefix), source-of-truth discipline, MCP/tool + Notion-plan constraints, SDK constraints (fan-out from parent thread; MCP writes parent-thread only). **For `deep_read`: prose-not-lattice; jargon defined inline; citations as ENDNOTES not inline; provenance discipline (Rule 12).** |
| `anti_pattern_avoidance` | 0.20 | Avoids: over-engineering/ceremony, duplicating state, resurrecting a tombstoned decision (gtm-os/Langfuse; Supabase-as-*measurement*-store — but Supabase IS the sanctioned Market-Intelligence store), fabricated numbers/specificity, orphan metrics, hardcoded secrets, lossy summarization where fidelity matters, speculative surface with no named friction. **For `deep_read`: no generic-explainer padding, no bullet-lattice fallback, no duplicating the Scan head or outbound copy.** |
| `diagnostics` | 0.10 | Legible + maintainable; clear comments/errors; failures explicable; **honest about gaps/confidence** (no overclaiming; a skeleton presented as finished, a docstring promising a property the code doesn't have, or an unverified claim stamped "verified", is dishonest framing). **For `deep_read`: `> Gap` notes present where evidence was thin; company-reported vs. audited distinguished.** |

### Composite caps (applied AFTER the weighted sum, by the harness)
1. **Confidence-honesty cap → composite ≤ 0.65** when an unverified/uncited claim is asserted as verified.
2. **Density cap → composite ≤ 0.65** when `artifact_type = deep_read` AND a padding signal (per `density-check.sh`) is, on inspection, generic-explainer filler rather than legitimate on-ramp.
3. Per-criterion caps: **spec drift → correctness ≤ 0.70 (NEW)**; dangling-reference → completeness ≤ 0.60 (also composite ≤ 0.60, mechanized by `check-refs.sh`); command-skeleton-absent → completeness ≤ 0.35.

### Per-criterion anchors (pass · mid · fail)
- **correctness** — pass (1.0): checked every numbered spec decision and the main code paths; none contradicted. mid (0.85): works as specified; one minor edge-case or naming slip. fail: references a tool/DB that doesn't exist; **code contradicts a numbered spec decision** (cap ≤ 0.70); a Deep Read asserting a thesis claim with no source.
- **completeness** — pass: methodology + failure-modes + references *that all exist*. mid: all AC items present; one secondary part thin or a non-load-bearing piece deferred and *said so*. fail: an AC item silently unaddressed; `TODO` left in; a Deep Read dropping a researched section.
- **convention_adherence** — pass: correct placement/frontmatter/naming throughout. mid: conventions followed; one cosmetic slip. fail: hardcoded secret; bypasses the single guarded write path; a Deep Read regressed to a bullet lattice.
- **anti_pattern_avoidance** — pass: contract-first lean foundation. mid: lean, with one piece of speculative surface or duplicated state. fail: builds the platform when "lean" was decided; resurrects a tombstoned decision.
- **diagnostics** — pass: comments explain the contract; failures are loud and specific; docstrings match behaviour. mid: failures loud, but a reported count or docstring overstates what's proven. fail: opaque/silent failure mode; overclaims certainty; asserts unverified as verified (also triggers the confidence-honesty cap).

### Machine-readable
```json
{
  "rubric_version": "build-quality@5",
  "judge_system": "judge-system-v2",
  "pass_band": 0.70,
  "criteria": [
    {"id": "correctness", "weight": 0.30},
    {"id": "completeness", "weight": 0.20},
    {"id": "convention_adherence", "weight": 0.20},
    {"id": "anti_pattern_avoidance", "weight": 0.20},
    {"id": "diagnostics", "weight": 0.10}
  ],
  "required_output": ["defects[] before criterion_scores", "cap flags", "NO judge-computed composite/verdict"],
  "low_information": "all five criteria == 1.0 -> flat_ceiling:true -> quorum escalates",
  "composite_caps": [
    {"when": "confidence-honesty violation (unverified claim asserted as verified)", "max": 0.65},
    {"when": "artifact_type=deep_read AND density padding signal is generic-explainer filler", "max": 0.65, "mechanized_by": ".claude/hooks/density-check.sh"},
    {"when": "behaviour contradicts a numbered decision in a supplied spec/ADR", "max": 0.70, "criterion": "correctness"},
    {"when": "references a load-bearing file/rubric/doc that does not exist", "max": 0.60, "criterion": "completeness", "mechanized_by": ".claude/hooks/check-refs.sh"},
    {"when": "artifact_type=command AND orchestration skeleton absent", "max": 0.35, "criterion": "completeness"}
  ]
}
```
