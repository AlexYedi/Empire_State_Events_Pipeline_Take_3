# Goal-tagging convention (Content Drafts) — assigned goal at creation

Added 2026-06-26 (Linear YED-90 / PRD US-4). Every Content Draft gets a **Goal** + **Target** *at creation*, so the measurement layer can later grade **outcome vs. assigned goal** (the acted-on-value north-star). Imported by the content skills (`pre-event-content`, `content-correspondent`, `pattern-synthesis`) and applied by whoever creates the row (Notion writes run in the parent thread per CLAUDE.md invariant 5).

## Notion fields (Content Drafts DB `6c24c9f5…`)
- **Goal** (select): `reach` · `engagement` · `connection` · `meeting` · `hybrid` · `internal`
- **Target** (text): the concrete, checkable target — e.g. `"500 impressions"`, `"3%+ engagement"`, `"accept the connection"`, `"book a coffee"`.

## Default Goal by Content Type (apply unless the skill/Alex overrides)
| Content Type | Default Goal | Target hint |
|---|---|---|
| `linkedin_post_pre` (incl. "The Upcoming Week" roundup) | `reach` | impressions/views; the roundup "sets the table" |
| `linkedin_post_post` | `engagement` | comments/reshares; the depth post |
| `linkedin_post_synthesis` | `engagement` | comments/saves; the documentarian format |
| `linkedin_dm_speaker` / `linkedin_dm_host` (connection notes) | `connection` | accept the connection request |
| `prepared_questions` | `internal` | — (not published) |
| `research_brief` / `post_event_brief` | `internal` | — (notion_only data store) |

- Use `hybrid` only when a post genuinely targets both reach + engagement — name both in Target.
- Goal = the *assigned intent*; the outcome (US-5) is graded against it. **Don't leave Goal empty on a publishable draft.**
- Owned-asset distribution (a site/landing page linked from a post) → tag the post's Goal by its intent; the owned-asset analytics (US-5/US-6) measure the click-through funnel.

## How it's set
1. The content skill picks the Goal (override the default when Alex states an intent via `steering-interview`).
2. The Content Draft create (inline in the parent thread) sets `Goal` + `Target`; if no goal was passed, it applies the default-by-Content-Type above.

## Outcome side (US-5) — closing the loop
After an artifact publishes, `/tag-outcome` records the **realized outcome vs the Goal/Target** on the same row:
- **Outcome** (select): `hit` (met/exceeded Target) · `partial` (real outcome, below Target) · `miss` · `pending` (not yet observable) · `na` (internal goal).
- **Outcome Value** (text): the realized signal + source, e.g. `"[LinkedIn] 620 impressions vs 500 target"`, `"[HubSpot] connected + coffee booked"`.
- **Outcome Date** (date): when observed.

Goal+Target (assigned intent) **+** Outcome (realized) = the **acted-on-value north-star**. Outcome is set manually/HITL at crawl (see `.claude/skills/tag-outcome/SKILL.md`); never fabricated — not observable yet ⇒ leave `pending`.

## Variant tagging + baseline-relative verdicts (3-post structure)

Added 2026-10-31 (E-09 / YED-220, Eric Nowoslawski harvest row 4 — `docs/archive/notes/eric-coldoutboundskills-harvest-2026-09-24.md` §3). When a post ships as 3 variants and the variants actually differ, each variant carries a **machine-readable tag recording which single variable it changes** vs the standing default — so outcomes can be attributed to the change, not guessed at. Verdicts are **baseline-relative** (keep/iterate/kill thresholds), never absolute numbers.

### The tag (one per differing variant)

```text
variant_tag: hook_type   # the single variable this variant changes vs control
```

- Allowed values: `hook_type` · `format` · `opener`. A variant identical to the control carries no tag.
- **Enforcement is tag-only** (Blueprint judgment J3): nothing validates that a variant really changed only its tagged variable — "change one variable per test" is design guidance, not a gate. The tag records the *intended* variable so outcomes stay attributable even when the discipline slips; when two things moved, say so in the log rather than in a validator.

### Baseline-relative verdicts

- **Baseline** = the do-nothing number for the same content type (the null-baseline rule) — e.g. median engagement of the standing format over recent posts. Log it in the experiment block *before* launch.
- **Wait 21 days** from launch before judging. Then, per variant:
  - **≥ 2× baseline → winner** — keep it; consider promoting it to the new default.
  - **< 50% of baseline → loser** — **kill it and log the reason** in the experiment block.
  - In between → iterate (same tag, next experiment).
- Review the experiment set quarterly (harvest-note cadence).

### Where this lives

The harvest note's USE NOW target named `/rigor-review`, which was retired 2026-09-28 (`.claude/WORKFLOWS.md`; the weekly review was replaced by the PR template) — so the convention lands here, where the content skills and `/tag-outcome` already read. Worked example: `fixtures/tagged-variants.md`; executable convention check: `python3 .claude/scripts/test_variant_tags.py --selftest`.
