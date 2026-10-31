# /tailor-resume — Resume Skill (YED-258, E-09)

Produce a **one-page, ATS-safe PDF resume** from the me-model: HTML template → headless
Chrome `--print-to-pdf` → text-based PDF. The deterministic half lives in
**`.claude/scripts/render_resume.py`** (chrome() probe and `--print-to-pdf` reused from
`render_carousel.py` — one render path in the repo); this skill is the methodology and the
mode contract. PR A scaffolds the pipeline; PR B (resume-content) builds the real template
reweighting.

## Private-input rule

Read `.claude/references/me-model.md` **by path only**. It is gitignored and never copied
into fixtures, outputs, or committed files. All generated resumes write ONLY to
`.claude/output/` (gitignored) — `render_resume.py` refuses any other path.

## The seven locked content rules (Blueprint region "tailor-resume")

1. **Quota-carrying post-sales is always the lead.** Hunting wins appear only as *proof of
   account growth*; never CSM/renewal-only framing.
2. **Client names only as a "Key accounts" logo line.** Outcomes are described unnamed.
3. **No vertical-territory labels in titles** (e.g. never "Financial Services" as a title
   component).
4. **Proof links are verified live** and point at specific repos and the hub — never the
   bare GitHub profile.
5. **Nothing is invented beyond the me-model.** Every claim traces to it.
6. **Reads me-model by path only** — never copied into fixtures or outputs.
7. **All generated resumes write to `.claude/output/`** (gitignored); the writer refuses any
   other path.

## Modes

- **general** — master resume from the me-model experience sections, in order, led by the
  quota-carrying post-sales positioning line. *(PR A: renders the locked template with the
  fixture fields. PR B: full master-resume content rules.)*
- **posting-tailored** — reweighted against a pasted JD. *(PR A: mode is accepted and
  recorded in the render metadata; reweighting rules land in PR B.)*

## Running it

```bash
# general mode (fixture in CI, real me-model in-session)
python3 .claude/scripts/render_resume.py <me-model-or-fixture.md> \
  --out .claude/output/resume.pdf

# posting-tailored mode (JD reweighting lands in PR B)
python3 .claude/scripts/render_resume.py .claude/references/me-model.md \
  --mode posting-tailored --jd posting.txt --out .claude/output/resume.pdf

# offline selftest — template + content rules + path guard, no Chrome (CI path)
python3 .claude/scripts/render_resume.py --selftest
```

The Chrome render runs in-session where Chrome exists (Alex's Mac); in a fresh sandbox the
script reports "Chrome not found" rather than half-rendering — that is the E-07 split.

## Fixture

`.claude/skills/tailor-resume/fixtures/me-model-fixture.md` is fully fictional (people,
companies, `*.example` hub link). It renders all sections and passes every locked rule in
the `--selftest`.

## Acceptance

- Fixture renders to **one page** with `pdftotext` reading order intact:
  name → positioning → roles in order → Key accounts.
- The writer refuses any path outside `.claude/output/` (selftest-covered).
- **Post-merge:** the first real run in a fresh Claude Code session is Alex's acceptance
  step — not a merge gate.
