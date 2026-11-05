# /tailor-resume — Resume Skill (YED-258, E-09)

Produce a **one-page, ATS-safe PDF resume** from the me-model: HTML template → headless
Chrome `--print-to-pdf` → text-based PDF. The deterministic half lives in
**`.claude/scripts/render_resume.py`** (chrome() probe and `--print-to-pdf` reused from
`render_carousel.py` — one render path in the repo); this skill is the model-side half.
PR A shipped the pipeline; **PR B (this version) ships the content half** — the **decided**
me-model mapping, **constrained posting-tailored rewording** (reorder pass + reword with a
fidelity gate), the one-page/reading-order PDF gate, and the **one-in-one-out** retirement of
the ad-hoc markdown → Google Doc resume flow. The **minimal template** (Alex's blind pick
on PR #247, comment 6551704109) is applied as spec'd below.

## The split contract (per Alex's 2026-10-31 review)

1. **This skill (model-side, in session)** reads `.claude/references/me-model.md`
   **by path** and writes a structured **resume-input JSON** to `.claude/output/`.
   Which me-model sections feed which fields: the **mapping below is decided**
   (Alex's spec walk, 2026-10-31, recorded on PR #247) — it is not a default to override.
2. **`render_resume.py`** consumes **only** that JSON: schema-validates it (refuses
   unknown keys), applies the locked content rules, renders. It **never opens
   `me-model.md`** — its private-input surface is zero.
3. All outputs (the JSON and the PDF) write ONLY to `.claude/output/` (gitignored).

## me-model → resume-input mapping (decided — Alex's spec walk, 2026-10-31)

- **Positioning** → the resume-input `positioning` line — the summary block **leading
  with quota-carrying post-sales**.
- **Experience sections** → `roles[]` entries **in me-model order**; hunting wins are
  framed as **proof of account growth**, never CSM/renewal-only framing.
- **Key accounts** → the `key_accounts` logo list — client names appear nowhere else.
  Where the me-model ties accounts to a role, use per-role `roles[].key_accounts`
  instead (YED-280); never both.

## One in, one out (decided — Alex's spec walk, 2026-10-31)

`/tailor-resume` **retires the ad-hoc markdown → Google Doc resume flow** and is the
**only resume path**. Résumés are built and rendered through this skill and its
resume-input JSON → `render_resume.py` pipeline; new ad-hoc markdown or Google Doc
resume files are not produced.

## resume-input JSON contract

```json
{
  "name": "...",
  "contact": ["..."],
  "positioning": "...",
  "roles": [
    { "title": "...", "company": "...", "dates": "...",
      "bullets": [ { "text": "...",
                     "source": "trace-to-me-model note (required)",
                     "original": "verbatim me-model bullet (required when reworded)" } ],
      "key_accounts": ["... (optional, per role — see below)"] }
  ],
  "key_accounts": ["... (top-level; omit when roles carry their own)"],
  "proof_links": ["https://... (or builds[] instead — exactly one of the two)"],
  "builds": [ { "description": "one line, optional", "links": ["https://..."] } ],
  "education": ["..."]
}
```

- **Per-role key accounts (YED-280).** `roles[].key_accounts` is optional. When any role
  carries one, a `Key accounts: A, B` line renders under that role (after its bullets) and
  the **top-level Key accounts line is suppressed**. The two modes do not mix: an input
  with both a top-level `key_accounts` and any `roles[].key_accounts` is refused, so no
  list the skill wrote is ever dropped silently. Roles without notable accounts simply
  omit the key. A **top-level-only input renders exactly as before** (byte-identical
  body, pinned by `fixtures/resume-legacy.golden.html`). Rule 2 holds either way: client
  names appear only on Key accounts lines, and the renderer checks every other visible
  line (positioning, titles, bullets, build descriptions), not just bullets.
- **Build description line (YED-280).** `builds[]` is the optional replacement for
  `proof_links`: each build is `{links[], description?}`. A description renders before
  that build's links on one list item (`Description — link · link`); a build without one
  renders one link per item, exactly as `proof_links` does. The description is **one
  line of at most 70 characters**. Over the cap is **refused, never truncated** and no
  ellipsis is ever added: a cut could land mid-figure ("grew 12…" of "grew 120%"), which
  is rule 5's failure. Write the line to fit. 70 is measured, not picked: a 100-char line
  plus its link wrapped to two lines on every build.
- **Golden update rule.** `fixtures/resume-legacy.golden.html` is the pre-YED-280 render
  of the legacy fixture. Regenerate it only for a deliberate, reviewed template change,
  and say so in that PR.

- **`contact` and `education` are optional** (minimal-template follow-up, 2026-11-01):
  arrays of non-empty strings. `contact` renders as the header line under the name
  (joined " · "); `education` renders as the one-line Education section (degree ·
  activities · certs). Absent → the section is omitted. No email or phone ever enters
  committed fixtures — those stay in the gitignored output JSON only.

- Every bullet carries a **`source` note** — the trace-to-me-model rule (locked rule 5).
  The renderer refuses any bullet without one.
- A bullet the skill **reworded for a posting** also carries **`original`** — its verbatim
  me-model wording. The renderer pins the reworded text's facts to that original and fails
  the run naming any bullet that introduces a fact the me-model doesn't carry.
- **In posting-tailored mode, `original` is required on *every* bullet** — set it **equal
  to `text`** when the bullet is not reworded. A reworded bullet that omitted `original`
  would skip the fidelity gate silently and the renderer cannot tell, so the contract
  makes that impossible; the render refuses any bullet without it.
- Unknown keys are refused at every level; nothing is coerced or dropped.
- Write the JSON to `.claude/output/resume-input.json` (gitignored — never committed).

## The minimal template (decided — Alex's blind pick, 2026-11-01)

Two variants (minimal vs. a single acid-green #8FE83A accent) were rendered blind on real
content; **minimal won**. The template is locked to this spec:

- Letter page, margins `0.4in 0.55in`; Helvetica Neue stack, 9.4pt, line-height 1.27,
  text `#16181d`; **no colour accents** (the neutral palette `#16181d / #5a5f6b /
  #c9ccd3 / #3c4049` is the full colour set — the renderer refuses any other hex).
- Header: name 20pt/600, letter-spacing −0.2pt; contact line 9pt `#5a5f6b`; a 0.6pt
  `#c9ccd3` rule under the header.
- Positioning 10.5pt. Role title 10.5pt/600 with dates right-aligned 9pt tabular-nums;
  company 9.5pt `#3c4049`.
- Section labels: 8.5pt/600 uppercase `#5a5f6b`, **letter-spacing ≤ 0.3pt** — an ATS cap,
  not a style choice: at 1.2pt, pdftotext extracts "E D U C AT I O N" and ATS parsing
  breaks. The PDF gate asserts the cap on the rendered sample.
- **Every `<li>` sits inside a `<ul>`** (the pre-spec template emitted bare `<li>`);
  the render refuses malformed list structure.
- Section order: header (name → contact) → Positioning → Experience → Key accounts →
  Selected builds (the proof links) → Education (degree · lacrosse · certs on one line).
  In per-role mode the Key accounts lines sit inside Experience, each under its role,
  and the top-level section is absent.
- Per-role Key accounts line: 9pt `#3c4049`, label "Key accounts:" at 600 (palette
  unchanged).
- Fit: one page at **7 roles / 15 bullets** and the full education line with the
  top-level Key accounts line, verified on the rendered stress sample (pdftotext surface).
  **With every YED-280 field at its max** (a full-line Key accounts list on every role,
  three builds with 70-char descriptions) the one-page envelope is **6 roles / 13
  bullets**: each per-role line costs a line, and 7/15 spills Education onto page 2.
  `fixtures/resume-input-fixture-max.json` pins that envelope; the run's one-page gate
  is the backstop beyond it.

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
  quota-carrying post-sales positioning line.
- **posting-tailored** — tailored against a pasted JD (`--jd posting.txt`, required in
  this mode), in two passes (spec-walk decision 2, 2026-10-31):
  1. **Reorder (deterministic, script-side):** roles ranked by JD-term overlap across
     their bullets, bullets re-ranked inside each role; stable sort keeps the me-model
     order on ties, and a JD with zero overlap degrades visibly to the general resume.
  2. **Constrained rewording (model-side, skill):** bullets may be **reworded into the
     posting's vocabulary**, adding **no new facts** — every reworded bullet keeps its
     `source` note and carries **`original`** (the verbatim me-model bullet). The
     renderer fails the run naming any bullet whose **fact tokens** are absent from its
     `original`; a client name in **either** text fails rule 2.

**Fact tokens** (what the fidelity gate pins, review 2026-11-01): numbers, $-figures,
percentages, **spelled-out quantities** (one…twenty, thirty…ninety, hundred, thousand,
million, billion, dozen, half, double, triple, twice — hyphen-split, so "three-rep"
counts), and proper-noun candidates. A capitalized token is a proper-noun candidate
**including in the leading position** — the first word is exempt only when it is an
allowlisted action verb: **Closed, Drove, Grew, Owned, Led, Built, Sold, Saved, Landed,
Scaled, Enabled, Applied**. "Heliosoft: closed …" therefore fails when `original` has no
Heliosoft. The runtime allowlist lives in `render_resume.py` (`ACTION_FIRST_WORDS` — the
renderer cannot depend on skill files at runtime); this section is its documentation and
the fixture test fails if the two drift.

## The PDF gate (PR B)

After Chrome writes the PDF, the run is gated on:

- **exactly one page** (a multi-page render fails the run — fix content, not margins);
- **`pdftotext` reading order intact**: name → positioning → roles in order (each
  followed by its own `Key accounts:` line in per-role mode) → Key accounts (top-level
  mode) → Selected builds → each build description in order (→ Education when
  present). If `pdftotext` is missing, the check is skipped with a loud `WARN`, the same
  pattern as the Chrome probe, never a silent pass;
- **section labels extract unbroken** (`EXPERIENCE`, `KEY ACCOUNTS` when the top-level
  section renders, `SELECTED BUILDS`, `EDUCATION`) — the rendered-surface assertion of
  the ≤0.3pt letter-spacing ATS cap. An over-spaced label ("E D U C AT I O N") fails
  the run.

## Proof-link liveness (`--verify-links`, rule 4)

The locked rule says proof links are **verified live**. The renderer's always-on gate is
the shape check (specific repos + the hub, never the bare profile — CI-safe). Pass
`--verify-links` on a networked machine (the in-session run does) to HEAD-check every
proof link first; any dead or unreachable link fails the run before Chrome starts.

## Running it

```bash
# 1. In-session (Alex's Claude Code): build resume-input JSON from the me-model by path,
#    using the decided mapping (Positioning → summary leading with quota-carrying
#    post-sales; Experience → role entries; Key accounts → the logo list).
# 2. Render from the JSON — the renderer never touches the me-model:
python3 .claude/scripts/render_resume.py .claude/output/resume-input.json \
  --out .claude/output/resume.pdf

# posting-tailored mode — --jd is required; reorder pass + constrained rewording
# (every bullet carries `original`: verbatim me-model wording, = text when not reworded)
python3 .claude/scripts/render_resume.py .claude/output/resume-input.json \
  --mode posting-tailored --jd posting.txt --out .claude/output/resume.pdf

# same, with rule-4 liveness (in-session run always passes this):
python3 .claude/scripts/render_resume.py .claude/output/resume-input.json \
  --verify-links --out .claude/output/resume.pdf

# offline selftest — schema + content rules + reading order + path guard, no Chrome (CI)
python3 .claude/scripts/render_resume.py --selftest
```

The Chrome render runs wherever Chrome/Chromium exists (Alex's Mac, or a sandbox with
chromium on PATH); in a fresh sandbox without either, the script reports "Chrome not
found" rather than half-rendering — that is the E-07 split. The PDF gate runs after the
render: exactly one page, `pdftotext` reading order intact, exit code gates the run.

## Fixture

`.claude/skills/tailor-resume/fixtures/resume-input-fixture.json` is fully synthetic
(fictional people/companies, `*.example` hub link, per-bullet source notes citing the
fixture itself). The selftest validates schema, content rules, reading order, and path
refusal against it. It is the **legacy (top-level-only) input** and stays untouched.

YED-280 fixtures, equally synthetic:
- `resume-input-fixture-per-role.json` — per-role key accounts (fictional clients distinct
  from the employers) and `builds[]`, one with a description, one without.
- `resume-input-fixture-max.json` — every new field at its max (6 roles / 13 bullets,
  a full-line accounts list per role, three 70-char descriptions). The selftest renders
  it through Chrome when Chrome and `pdftotext` exist and asserts one page; otherwise
  it prints a loud `WARN ... SKIPPED`.
- `resume-legacy.golden.html` — the pre-YED-280 render of the legacy fixture (see the
  golden update rule above).

## Acceptance

- Fixture renders to **one page** with `pdftotext` reading order intact: name → contact →
  positioning → roles in order → Key accounts → Selected builds → Education.
- Section labels extract unbroken (the ATS letter-spacing cap holds on the rendered PDF).
- Fit: **7 roles / 15 bullets** still render on exactly one page with the top-level
  Key accounts line (stress-rendered sample, pdftotext-verified); **6 roles / 13
  bullets** with every per-role and build-description field at its max (selftest-rendered).
- Per-role mode: each role's `Key accounts:` line renders under that role, the top-level
  line is suppressed, and no client name appears outside a Key accounts line.
- The writer refuses any path outside `.claude/output/` (selftest-covered).
- The renderer never opens the me-model (schema + JSON contract only).
- **Post-merge:** the first real run in a fresh Claude Code session is Alex's acceptance
  step — not a merge gate.
