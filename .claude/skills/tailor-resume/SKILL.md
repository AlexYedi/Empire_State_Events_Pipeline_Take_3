# /tailor-resume — Resume Skill (YED-258, E-09)

Produce a **one-page, ATS-safe PDF resume** from the me-model: HTML template → headless
Chrome `--print-to-pdf` → text-based PDF. The deterministic half lives in
**`.claude/scripts/render_resume.py`** (chrome() probe and `--print-to-pdf` reused from
`render_carousel.py` — one render path in the repo); this skill is the model-side half.
PR A shipped the pipeline; **PR B (this version) ships the content half** — the default
me-model mapping, posting-tailored reweighting, and the one-page/reading-order PDF gate.

## The split contract (per Alex's 2026-10-31 review)

1. **This skill (model-side, in session)** reads `.claude/references/me-model.md`
   **by path** and writes a structured **resume-input JSON** to `.claude/output/`.
   Which me-model sections feed which fields: the PR8 execution-input gate completed
   **without recorded mapping notes**, so PR B ships the **Blueprint default mapping**
   (below). Alex can override it at PR-B review — it is a documented default, not a
   settled decision.
2. **`render_resume.py`** consumes **only** that JSON: schema-validates it (refuses
   unknown keys), applies the locked content rules, renders. It **never opens
   `me-model.md`** — its private-input surface is zero.
3. All outputs (the JSON and the PDF) write ONLY to `.claude/output/` (gitignored).

## me-model → resume-input mapping (PR B default, stated for review)

- **Positioning** → the resume-input `positioning` line — the summary block **leading
  with quota-carrying post-sales**.
- **Experience sections** → `roles[]` entries **in me-model order**; hunting wins are
  framed as **proof of account growth**, never CSM/renewal-only framing.
- **Key accounts** → the `key_accounts` logo list — client names appear nowhere else.

## resume-input JSON contract

```json
{
  "name": "...",
  "positioning": "...",
  "roles": [
    { "title": "...", "company": "...", "dates": "...",
      "bullets": [ { "text": "...", "source": "trace-to-me-model note (required)" } ] }
  ],
  "key_accounts": ["..."],
  "proof_links": ["https://..."]
}
```

- Every bullet carries a **`source` note** — the trace-to-me-model rule (locked rule 5).
  The renderer refuses any bullet without one.
- Unknown keys are refused at every level; nothing is coerced or dropped.
- Write the JSON to `.claude/output/resume-input.json` (gitignored — never committed).

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
- **posting-tailored** — reweighted against a pasted JD (`--jd posting.txt`, required in
  this mode). Reweighting is **reorder-only, deterministic**: roles are ranked by JD-term
  overlap across their bullets, bullets re-ranked inside each role; no word is written or
  dropped (rule 5 forbids inventing anything the JSON doesn't already carry). Sorting is
  stable — equal scores keep the me-model order, and a JD with zero overlap degrades
  visibly to the general resume.

## The PDF gate (PR B)

After Chrome writes the PDF, the run is gated on:

- **exactly one page** (a multi-page render fails the run — fix content, not margins);
- **`pdftotext` reading order intact**: name → positioning → roles in order → Key
  accounts. If `pdftotext` is missing, the check is skipped with a loud `WARN` — same
  pattern as the Chrome probe, never a silent pass.

## Proof-link liveness (`--verify-links`, rule 4)

The locked rule says proof links are **verified live**. The renderer's always-on gate is
the shape check (specific repos + the hub, never the bare profile — CI-safe). Pass
`--verify-links` on a networked machine (the in-session run does) to HEAD-check every
proof link first; any dead or unreachable link fails the run before Chrome starts.

## Running it

```bash
# 1. In-session (Alex's Claude Code): build resume-input JSON from the me-model by path,
#    using the default mapping above (Positioning → summary leading with quota-carrying
#    post-sales; Experience → role entries; Key accounts → the logo list).
# 2. Render from the JSON — the renderer never touches the me-model:
python3 .claude/scripts/render_resume.py .claude/output/resume-input.json \
  --out .claude/output/resume.pdf

# posting-tailored mode — --jd is required; reweighting is reorder-only
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
refusal against it.

## Acceptance

- Fixture renders to **one page** with `pdftotext` reading order intact:
  name → positioning → roles in order → Key accounts.
- The writer refuses any path outside `.claude/output/` (selftest-covered).
- The renderer never opens the me-model (schema + JSON contract only).
- **Post-merge:** the first real run in a fresh Claude Code session is Alex's acceptance
  step — not a merge gate.
