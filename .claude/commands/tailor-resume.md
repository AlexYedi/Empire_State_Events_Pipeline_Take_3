---
description: "Render a one-page, ATS-safe resume PDF (YED-258). In-session: build resume-input JSON from the me-model by path; render_resume.py consumes ONLY that JSON (schema-validated, never opens the me-model). Two modes: general or posting-tailored. Output goes only to .claude/output/."
argument-hint: "[general | posting-tailored + paste JD] — reads .claude/references/me-model.md by path, renders from resume-input JSON"
---

# /tailor-resume — Resume rendering lens

**One in, one out (decided 2026-10-31):** this command retires the ad-hoc markdown →
Google Doc resume flow and is the **only resume path**.

Methodology, the split contract, the resume-input JSON schema, and the seven locked
content rules: **`.claude/skills/tailor-resume/SKILL.md`**. Read it first. The render path
is **`.claude/scripts/render_resume.py`** (reuses render_carousel.py's chrome probe +
`--print-to-pdf`; offline `--selftest` for CI).

## Step 1 — Mode and source (in-session, model-side)

1. Ask which mode if not stated: **general** (master resume) or **posting-tailored**
   (paste the JD verbatim).
2. Source is `.claude/references/me-model.md`, read **by path only**. If it is absent
   (fresh worktree without the local file): stop and ask — nothing renders without it.
3. Build a **resume-input JSON** (schema in the SKILL.md: `name`, `contact[]` (optional
   in the schema, **required for a real render**: the run refuses without it),
   `positioning`, `roles[] {title, company, dates, bullets[] {text, source[, original]}
   [, key_accounts[]]}`, `key_accounts[]` (top-level, OR per role, never both; each
   account a string or `{name, aliases[]}`, with aliases filled from the me-model's short
   forms; aliases are blocked by rule 2 and never rendered),
   `proof_links[]` OR `builds[] {links[][, description]}` (description: one line, ≤70
   chars, refused not truncated), `education[]` (optional)) and write it to
   `.claude/output/resume-input.json`.
   Per-role key accounts render a `Key accounts:` line under each role and suppress the
   top-level line (YED-280).
   Every bullet carries a `source` note (trace-to-me-model). Use the **decided mapping**
   (SKILL.md — Alex's spec walk, 2026-10-31): Positioning → summary leading with
   quota-carrying post-sales; Experience sections → role entries in me-model order;
   Key accounts → the logo list.
4. **Posting-tailored only** — rewording is constrained: bullets may be reworded into the
   posting's vocabulary, adding **no new facts**. A reworded bullet keeps its `source`
   note and carries **`original`** (the verbatim me-model bullet); the renderer fails the
   run naming any bullet whose numbers, $-figures, percentages or proper nouns are absent
   from its `original`. A client name in either text fails rule 2.

## Step 2 — Render (renderer never touches the me-model)

```bash
python3 .claude/scripts/render_resume.py .claude/output/resume-input.json \
  [--mode posting-tailored --jd posting.txt] --out .claude/output/resume.pdf
```

- The renderer schema-validates the JSON and refuses unknown keys; a schema or content-rule
  failure fails the render before Chrome runs — fix the JSON, not the checker.
- Output path is guarded: anything outside `.claude/output/` is refused loudly. Never
  redirect it elsewhere.
- Pass `--verify-links` on a networked machine so rule-4 liveness runs before Chrome.

## Step 3 — Verify in-session

The run itself is gated: it exits non-zero unless the PDF is exactly one page, the
`pdftotext` reading order holds (name → positioning → roles in order, each with its own
Key accounts line in per-role mode → Key accounts (top-level mode) → Selected builds with
their description lines → Education when present), and the section labels extract unbroken (the
≤0.3pt letter-spacing ATS cap — "E D U C AT I O N" extraction fails the run).
If `pdftotext` is missing the order check is skipped with a loud `WARN` — install
poppler-utils rather than trust it.

## Failure modes

- **Chrome not found** (bare sandbox): the render path probes macOS Chrome first, then
  chromium/chrome on Linux. Run `--selftest` for the offline path; the visual render
  runs wherever a browser exists.
- **me-model.md absent**: stop and ask (private input, not in git by design).
- **Schema failure**: fix the resume-input JSON (unknown key, missing per-bullet `source`,
  wrong shape) — the renderer never guesses.
- **Rule failure named `rule N`**: the seven locked rules in the SKILL.md are the contract;
  rework the content, never the checker.
- **Rewording fidelity failure** (`rule 5 (rewording fidelity)`): a reworded bullet uses a
  number, $-figure, percentage or proper noun its `original` (verbatim me-model wording)
  doesn't carry. Rewrite the bullet to stay within the me-model's facts, or drop the
  rewording — never widen the gate.
