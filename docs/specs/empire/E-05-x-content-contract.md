# E-05 · X content contract (Empire)

**Repo:** Empire_State_Events_Pipeline_Take_3 (the hub surfaces are E-06)

## Product
X (Twitter) becomes a first-class channel (Alex's decision, 10/15), using native X formats, not reformatted LinkedIn copy. Every event that gets LinkedIn content also gets X drafts in the same Notion `needs_review` flow:
- **Pre-event:** 1 single post and 1 thread (4–7 posts).
- **In-event:** 2–3 live-post templates.
- **Post-event:** 1 thread and 1 quote-post of the LinkedIn recap.

Each post ships **3 variants**, and **nothing posts automatically**. The channel plan of record is `docs/spec-distribution-channels.md`; this spec MUST stay consistent with it. Read it first.

## Technical (factory executables)
1. **Reference.** New `.claude/references/x-content.md`:
   - 280 chars per post; thread hook under 200; at most 1 link per thread, in the last post;
   - at most 1 hashtag; alt text required on images; @handles only when verified.
   - Each rule MUST be marked as either "X platform rule" (with a source URL) or "house style".
2. **Voice.** Add an "X" section to `.claude/references/content-style-guide.md` and to `content-anti-patterns.md`.
   - **Additive only.** It MUST NOT change any existing LinkedIn rule.
   - Alex reviews the voice.
3. **Checks.** Add an `x` mode to `.claude/scripts/output_checks.py` covering per-post length, hook length, link placement and hashtag count, plus selftest cases for each check.
4. **Skill text.**
   - Describe an X step in `.claude/skills/pre-event-content/SKILL.md` and in `.claude/skills/content-correspondent/SKILL.md` (post-event archetypes).
   - X drafts are separate Content Drafts rows with `Platform = X`.
   - If that option doesn't exist, document the needed schema change in `.claude/references/notion-schema.md` under a "Proposed" heading.
   - The skills MUST NOT call Notion write tools directly (invariant 5).
5. **Media.** `.claude/scripts/render_carousel.py --x` also exports each slide as a 1:1 PNG, because X has no PDF carousels. Unit-test the pure sizing maths; there's no headless Chrome in tests.

## Must not
Add any X API client, key or posting code · change LinkedIn rules · write to Notion.

**Done when:** the reference exists, the voice sections are added, the `x` checks pass their selftest, both skills describe the X step, and `--x` export works on an existing carousel HTML.
