# Rubric: `dossier-quality@1`

Scope: **interview-prep dossiers** produced by `/interview-prep` (the Market-Intelligence Engine's
Job-Search lens). Owned by the eval convention (`rubric_version` = `dossier-quality@1`; never mutate — bump
to `@2`). Advisory gate (matches `/judge-build` posture) — surfaces a flag, never hard-blocks.

Score each criterion **independently 0–1**. Composite = weighted sum. **Verdict: pass if composite ≥ 0.70,
else flag-for-rework** (re-invoke the synthesizer with the weak criteria, or proceed + note the flag in the
Notion write).

| id | weight | what "good" means |
|---|---|---|
| `four_axis_tailoring` | 0.25 | A reader can tell this dossier is for THIS **company × role × stage × interviewer** — not a generic company brief. Stage-Specific Prep reflects what *this* stage tests; interviewer section is about *this* person. |
| `person_frame` | 0.25 | Hits the north star: proves Alex is the best ***person*** (skills **+ humanity**), not a fact dump. Fit-Thesis pillars each marry a concrete skill with a human dimension; Curiosity & Questions demonstrate genuine engagement, not flattery. |
| `sourcing_honesty` | 0.20 | Thesis/positioning claims carry primary sources (rule #12); unsourced ones live in Verification Flags, not the body. No fabricated hooks ("None found — engage in the room" used instead). Confidence stated honestly; thin research admitted, not padded. |
| `actionability` | 0.15 | Alex could walk in and use it. Questions are THIS-interviewer-specific (could not be asked of anyone else). The role is decoded to its unstated need. Gaps are addressed proactively, not hidden. |
| `completeness` | 0.15 | All 11 sections present and non-stub; the **Blind-Spot Closer** is real (names the dimensions Alex normally papers over and closes them) — it is the dossier's whole point. |

### Per-criterion anchors (≥1 pass, ≥1 fail)
- **four_axis_tailoring** — pass: "for your final-round with the VP Eng, lead with the systems-design story; recruiter-screen framing would waste this slot." fail: a company overview that never mentions the stage or names the interviewer.
- **person_frame** — pass: "Pillar 2: your Curalate CS scars + genuine curiosity about their activation metric → you'll ask, not assert." fail: "You have 12 years of enterprise GTM experience" with no human dimension or curiosity hook.
- **sourcing_honesty** — pass: "their fund bets on infra over apps [TechCrunch, 2026-05]"; an unsourced thesis parked in Verification Flags. fail: states "they're pivoting to consumer" as fact with no source; invents a "you both love climbing" hook.
- **actionability** — pass: "Ask Priya how the FDE team splits discovery vs. delivery now that they've doubled — ties to her March post." fail: "Ask about company culture."
- **completeness** — pass: all 11 sections; Blind-Spot Closer names 2–3 real gaps + framing. fail: missing Org Map; Blind-Spot Closer is "N/A".

### Machine-readable
```json
{
  "rubric_version": "dossier-quality@1",
  "pass_band": 0.70,
  "criteria": [
    {"id": "four_axis_tailoring", "weight": 0.25},
    {"id": "person_frame", "weight": 0.25},
    {"id": "sourcing_honesty", "weight": 0.20},
    {"id": "actionability", "weight": 0.15},
    {"id": "completeness", "weight": 0.15}
  ]
}
```
