---
description: "Render a one-page, ATS-safe resume PDF from the me-model (YED-258). Two modes: general (master resume) or posting-tailored (reweighted against a pasted JD). Runs render_resume.py with the locked content rules; output goes only to .claude/output/."
argument-hint: "[general | posting-tailored + paste JD] — reads .claude/references/me-model.md by path"
---

# /tailor-resume — Resume rendering lens

Methodology, the seven locked content rules, and the mode contract:
**`.claude/skills/tailor-resume/SKILL.md`**. Read it first. The render path is
**`.claude/scripts/render_resume.py`** (reuses render_carousel.py's chrome probe +
`--print-to-pdf`; offline `--selftest` for CI).

## Step 1 — Mode and source

1. Ask which mode if not stated: **general** (master resume) or **posting-tailored**
   (paste the JD verbatim).
2. Source is `.claude/references/me-model.md`, read **by path only**. If it is absent
   (fresh worktree without the local file): stop and ask — nothing renders without it.

## Step 2 — Render

```bash
python3 .claude/scripts/render_resume.py .claude/references/me-model.md \
  [--mode posting-tailored --jd posting.txt] --out .claude/output/resume.pdf
```

- Output path is guarded: anything outside `.claude/output/` is refused loudly. Never
  redirect it elsewhere.
- Content-rule failures fail the render before Chrome runs — fix the me-model-derived
  content, not the checker.

## Step 3 — Verify in-session

1. One page (fix content, not margins, if it spills).
2. `pdftotext` reading order: name → positioning → roles in order → Key accounts.
3. Proof links resolve live (rule 4) — open each one before handing the PDF over.

## Failure modes

- **Chrome not found** (Linux sandbox): the render path is macOS-probed (render_carousel's
  chrome()). Run `--selftest` for the offline path; the visual render is Alex's in-session
  run on the Mac.
- **me-model.md absent**: stop and ask (private input, not in git by design).
- **Rule failure named `rule N`**: the seven locked rules in the SKILL.md are the contract;
  rework the content, never the checker.
