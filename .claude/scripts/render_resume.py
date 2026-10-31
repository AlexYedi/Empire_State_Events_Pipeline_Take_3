#!/usr/bin/env python3
"""Render a one-page, ATS-safe resume PDF from a me-model source (YED-258, E-09 PR A).

The deterministic half of /tailor-resume, so a resume can't "look done" and still be wrong:
  1. parse — reads a me-model-shaped markdown file BY PATH (never copied into any output);
  2. render — builds the locked HTML template (name → positioning → roles in order →
     Key accounts) and prints it via headless Chrome --print-to-pdf, reusing
     render_carousel.py's chrome() path probe and run() method (no new render path — E-07's
     proven mechanism, documented in content-patterns/visual-briefs.md);
  3. guard — every generated resume writes ONLY to .claude/output/ (gitignored); any other
     path is refused loudly;
  4. rules — the seven locked content rules (Blueprint region "tailor-resume") are checked
     offline on the rendered HTML before anything is printed.

An offline `--selftest` (template + content rules + path guard, no Chrome) lands in the
following commit — that is the CI-exercised path. The Chrome render is exercised in-session
where Chrome exists (same split as render_carousel.py, E-07): its chrome() probe targets
macOS paths, so on the Linux sandbox the print step reports the miss instead of
half-rendering.

Usage: render_resume.py <me-model-or-fixture.md> [--mode general|posting-tailored]
                       [--out .claude/output/resume.pdf] [--jd posting.txt]
"""
import argparse
import json
import os
import re
import sys
import tempfile

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
# The only writable destination for generated resumes (E-09 addition 3; gitignored in PR A).
OUTPUT_DIR = os.path.normpath(os.path.join(SCRIPTS, os.pardir, "output"))

# Reuse the E-07 render path: same Chrome probe, same headless invocation. One render
# mechanism in the repo, not two (the same "one executable copy" rule as comp_gate.py).
from render_carousel import chrome, run  # noqa: E402

# ---- locked content rules (Blueprint region "tailor-resume"; E-09 additions 1–4) -----------

# Rule 3: no vertical-territory labels in titles — "never 'Financial Services' as a title
# component". Denylist checked against role-title lines only, not body copy.
VERTICAL_LABELS = (
    "financial services", "healthcare", "fintech", "insurance", "banking",
    "retail", "energy", "telecom", "pharma", "logistics", "real estate",
)

# Rule 6 grep gate: the gitignored private inputs are referenced by path at run time and
# their names must never appear inside any committed fixture, template, or output.
PRIVATE_INPUT_NAMES = ("me-model.md", "target-companies.md")

POSITIONING_LEAD = "quota-carrying post-sales"  # rule 1: always the lead


# ---- output-path guard (E-09 addition 3): the writer refuses any path outside OUTPUT_DIR ----
def resolve_output_path(out: str) -> str:
    target = os.path.realpath(os.path.abspath(out))
    if target != OUTPUT_DIR and not target.startswith(OUTPUT_DIR + os.sep):
        sys.exit(
            f"REFUSED: {out} resolves to {target} — generated resumes write ONLY to\n"
            f"  {OUTPUT_DIR} (gitignored; E-09 addition 3). Nothing lands outside it.")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return target


# ---- me-model parsing: by path, into a plain dict. Nothing here touches private content ----
def parse_me_model(path: str) -> dict:
    """Parse a me-model-shaped markdown source into template fields.

    Shape: `# Name` · `Positioning: …` · `## Experience` with `### Title — Company (dates)`
    blocks of `- ` bullets · `## Key accounts` one line · `## Proof links` URL list.
    """
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    name = (re.search(r"^# (.+)$", text, re.M) or [None, ""])[1].strip()
    positioning = (re.search(r"^Positioning: (.+)$", text, re.M) or [None, ""])[1].strip()
    roles = []
    for block in re.findall(r"^### (.+)$\n((?:^- .+\n?)*)", text, re.M):
        title_line, bullets_raw = block
        m = re.match(r"(.+?) — (.+?) \((.+?)\)\s*$", title_line)
        roles.append({
            "title": m.group(1).strip() if m else title_line.strip(),
            "company": m.group(2).strip() if m else "",
            "dates": m.group(3).strip() if m else "",
            "bullets": [b[2:].strip() for b in bullets_raw.splitlines()],
        })
    key_accounts = (re.search(r"^## Key accounts\s*\n(.+)$", text, re.M) or [None, ""])[1].strip()
    proof_links = re.findall(r"^-\s+(https?://\S+)", text, re.M)
    return {"name": name, "positioning": positioning, "roles": roles,
            "key_accounts": key_accounts, "proof_links": proof_links}


# ---- template: fixed structure, ATS-safe, one page. PR A shape; PR B owns reweighting ----
def build_resume_html(me: dict, mode: str = "general") -> str:
    roles_html = "\n".join(
        f'    <h2 class="role-title">{r["title"]}</h2>\n'
        f'    <p class="role-meta">{r["company"]} ({r["dates"]})</p>\n'
        + "\n".join(f"    <li>{b}</li>" for b in r["bullets"])
        for r in me["roles"])
    links_html = "\n".join(f'    <li><a href="{u}">{u}</a></li>' for u in me["proof_links"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{me['name']} — Resume ({mode})</title>
<style>
  /* ATS-safe: single column, standard fonts, text-selectable (Chrome --print-to-pdf). */
  body {{ font-family: Helvetica, Arial, sans-serif; font-size: 11pt; margin: 0.6in; color: #111; }}
  h1 {{ font-size: 17pt; margin: 0; }}
  p.positioning {{ font-size: 11pt; margin: 4pt 0 10pt; }}
  h2 {{ font-size: 12pt; margin: 10pt 0 2pt; }}
  p.role-meta {{ margin: 0 0 2pt; color: #333; }}
  ul {{ margin: 2pt 0 6pt; padding-left: 14pt; }}
  p.key-accounts {{ margin-top: 8pt; }}
</style>
</head>
<body>
  <h1 class="resume-name">{me['name']}</h1>
  <p class="positioning">{me['positioning']}</p>
  <section id="experience">
{roles_html}
  </section>
  <p class="key-accounts"><strong>Key accounts:</strong> {me['key_accounts']}</p>
  <section id="proof-links">
    <ul>
{links_html}
    </ul>
  </section>
</body>
</html>
"""


# ---- offline checks: the locked rules, verifiable without Chrome ---------------------------
def check_content_rules(html: str, source_text: str = "") -> list:
    """Return a list of rule-violation strings; empty means every locked rule holds."""
    fails = []
    # Rule 1 — quota-carrying post-sales is always the lead (addition 1).
    pos = re.search(r'<p class="positioning">(.*?)</p>', html, re.S)
    if not pos or POSITIONING_LEAD not in pos.group(1).lower():
        fails.append(f"rule 1: positioning does not lead with '{POSITIONING_LEAD}'")
    for bullet in re.findall(r"<li>(.*?)</li>", html, re.S):
        low = bullet.lower()
        if ("hunting" in low or "new logos" in low) and "account growth" not in low:
            fails.append("rule 1: hunting win framed without 'proof of account growth'")
    # Rule 2 — client names only as the one Key accounts line (addition 2).
    if html.count('class="key-accounts"') != 1:
        fails.append("rule 2: exactly one Key accounts line expected")
    ka = html.find('class="key-accounts"')
    exp = html.find('id="experience"')
    if ka != -1 and exp != -1 and ka < exp:
        fails.append("rule 2: Key accounts line must come after the roles")
    # Rule 3 — no vertical-territory labels in titles (PR-B review addition).
    for title in re.findall(r'<h2 class="role-title">(.*?)</h2>', html, re.S):
        hit = [v for v in VERTICAL_LABELS if v in title.lower()]
        if hit:
            fails.append(f"rule 3: title carries a vertical-territory label ({hit[0]!r}): {title!r}")
    # Rule 4 — proof links to specific repos + the hub, never the bare profile.
    for url in re.findall(r'href="(https?://[^"]+)"', html):
        if re.fullmatch(r"https?://github\.com/[^/\s]+/?", url):
            fails.append(f"rule 4: bare GitHub profile link — point at specific repos/the hub: {url}")
    # Rule 5 — nothing invented beyond the me-model: no template placeholders leak through.
    for marker in ("TODO", "TBD", "Lorem", "PLACEHOLDER", "{{"):
        if marker in html:
            fails.append(f"rule 5: unsubstantiated template marker {marker!r} in output")
    # Rule 6 — gitignored private-input filenames never appear in output or fixture text.
    for needle in PRIVATE_INPUT_NAMES:
        if needle in html or (source_text and needle in source_text):
            fails.append(f"rule 6: private-input filename {needle!r} leaked into committed text")
    return fails


def check_reading_order(html: str) -> list:
    """Name → positioning → roles → Key accounts, in that DOM order (PR-A exit d)."""
    marks = [('class="resume-name"', "name"), ('class="positioning"', "positioning"),
             ('id="experience"', "roles"), ('class="key-accounts"', "Key accounts")]
    positions = [html.find(m) for m, _ in marks]
    if any(p == -1 for p in positions) or positions != sorted(positions):
        return ["reading order broken: expected name → positioning → roles → Key accounts"]
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("source", nargs="?", help="path to me-model.md or a me-model-shaped fixture")
    ap.add_argument("--mode", choices=("general", "posting-tailored"), default="general")
    ap.add_argument("--out", default=os.path.join(OUTPUT_DIR, "resume.pdf"))
    ap.add_argument("--jd", help="pasted JD text file (posting-tailored reweighting; PR B)")
    a = ap.parse_args()

    if not a.source:
        ap.error("a me-model source path is required")

    with open(a.source, encoding="utf-8") as fh:
        source_text = fh.read()
    me = parse_me_model(a.source)
    html = build_resume_html(me, a.mode)

    fails = check_content_rules(html, source_text) + check_reading_order(html)
    if fails:
        print("Content rules failed — nothing rendered:")
        for f in fails:
            print(f"  - {f}")
        return 1

    out = resolve_output_path(a.out)
    bin_ = chrome()
    if not bin_:
        sys.exit("Chrome not found — the Chrome render runs in-session where Chrome exists "
                 "(Alex's Mac); CI exercises `--selftest` (template + rules + guard, no Chrome).")

    # The intermediate HTML also lives under the gitignored output dir — nothing outside it.
    fd, tmp_html = tempfile.mkstemp(suffix=".html", dir=OUTPUT_DIR, prefix=".resume-")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(html)
    try:
        run(bin_, ["--print-to-pdf=" + out, "file://" + tmp_html])
    finally:
        os.remove(tmp_html)

    if not os.path.exists(out):
        sys.exit(f"Chrome did not write {out}")
    print(json.dumps({"ok": True, "pdf": out, "mode": a.mode, "roles": len(me["roles"])}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
