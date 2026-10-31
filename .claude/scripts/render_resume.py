#!/usr/bin/env python3
"""Render a one-page, ATS-safe resume PDF from a resume-input JSON (YED-258, E-09 PR A).

The deterministic half of /tailor-resume, so a resume can't "look done" and still be wrong.
The pipeline is split so the renderer's private-input surface is zero:

  - **The skill** (`.claude/skills/tailor-resume/`, model-side, in session) reads
    `.claude/references/me-model.md` by path and writes a structured **resume-input JSON**
    to `.claude/output/`. This script NEVER opens the me-model — parsing it is not here
    (section-to-field mapping is a PRD decision for PR B with Alex).
  - **This script** consumes only that JSON: schema-validates it (refuses unknown keys),
    applies the locked content rules offline, builds the one-page ATS-safe template
    (name → positioning → roles in order → Key accounts), and prints it via headless
    Chrome `--print-to-pdf`, reusing render_carousel.py's chrome() path probe and run()
    method (no new render path — E-07's proven mechanism).
  - **PR B (YED-258)** — the content half now ships for real: the me-model → resume-input
    mapping is documented as the Blueprint default (Positioning → summary leading with
    quota-carrying post-sales; Experience → role entries with hunting-wins-as-account-growth
    framing; Key accounts → the logo list), posting-tailored mode **reweights** by reordering
    roles/bullets against a pasted JD (reorder-only — rule 5 forbids writing a word), proof
    links get an optional live check (`--verify-links`, rule 4 "verified live"), and the
    rendered PDF is gated: exactly one page and `pdftotext` reading order intact, exit code
    gates the run.
  - **Guard** — every generated resume writes ONLY to `.claude/output/` (gitignored); any
    other path is refused loudly.

The offline `--selftest` exercises the schema, the content rules, the reading order and the
path guard with no Chrome — that is the CI-exercised path. The Chrome render is exercised
in-session where Chrome exists (same split as render_carousel.py, E-07): its chrome() probe
targets macOS paths, so on the Linux sandbox the print step reports the miss instead of
half-rendering.

Usage: render_resume.py <resume-input.json> [--mode general|posting-tailored]
                       [--out .claude/output/resume.pdf] [--jd posting.txt]
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
# The only writable destination for generated resumes and resume-input JSON
# (E-09 addition 3; gitignored in PR A).
OUTPUT_DIR = os.path.normpath(os.path.join(SCRIPTS, os.pardir, "output"))

# Reuse the E-07 render path: same Chrome probe, same headless invocation. One render
# mechanism in the repo, not two (the same "one executable copy" rule as comp_gate.py).
from render_carousel import chrome, pdf_page_count, run  # noqa: E402

# ---- locked content rules (Blueprint region "tailor-resume"; E-09 additions 1–4) -----------

# Rule 3: no vertical-territory labels in titles — "never 'Financial Services' as a title
# component". Denylist checked against role-title lines only, not body copy.
VERTICAL_LABELS = (
    "financial services", "healthcare", "fintech", "insurance", "banking",
    "retail", "energy", "telecom", "pharma", "logistics", "real estate",
)

# Rule 6 grep gate: the gitignored private inputs are read by the SKILL in-session only;
# their filenames must never appear inside any committed fixture, template, or output.
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


# ---- resume-input schema: validate, refuse unknown keys, never guess -----------------------
RESUME_INPUT_KEYS = {"name", "positioning", "roles", "key_accounts", "proof_links"}
ROLE_KEYS = {"title", "company", "dates", "bullets"}
BULLET_KEYS = {"text", "source"}


def _nonempty_str(v) -> bool:
    return isinstance(v, str) and v.strip() != ""


def validate_resume_input(data, where: str = "resume-input") -> list:
    """Validate the resume-input JSON contract; return a list of errors (empty = valid).

    Contract (skill-owned, written to .claude/output/):
      name, positioning              non-empty strings
      roles[]                        non-empty; {title, company, dates, bullets[]}
      bullets[]                      non-empty; {text, source} — `source` is the
                                     trace-to-me-model note (rule 5), required per bullet
      key_accounts[], proof_links[]  non-empty arrays of non-empty strings
    Unknown keys are refused at every level; nothing is coerced or dropped.
    """
    errors = []
    if not isinstance(data, dict):
        return [f"{where}: expected an object, got {type(data).__name__}"]
    unknown = sorted(set(data) - RESUME_INPUT_KEYS)
    if unknown:
        errors.append(f"{where}: unknown key(s) {unknown} — allowed: {sorted(RESUME_INPUT_KEYS)}")
    missing = sorted(RESUME_INPUT_KEYS - set(data))
    if missing:
        errors.append(f"{where}: missing key(s) {missing}")
    for key in ("name", "positioning"):
        if key in data and not _nonempty_str(data[key]):
            errors.append(f"{where}.{key}: non-empty string required")
    roles = data.get("roles")
    if not isinstance(roles, list) or not roles:
        errors.append(f"{where}.roles: non-empty array required")
    else:
        for i, role in enumerate(roles):
            rw = f"{where}.roles[{i}]"
            if not isinstance(role, dict):
                errors.append(f"{rw}: expected an object")
                continue
            unknown = sorted(set(role) - ROLE_KEYS)
            if unknown:
                errors.append(f"{rw}: unknown key(s) {unknown} — allowed: {sorted(ROLE_KEYS)}")
            for key in ("title", "company", "dates"):
                if key in role and not isinstance(role[key], str):
                    errors.append(f"{rw}.{key}: string required")
            if not _nonempty_str(role.get("title", "")):
                errors.append(f"{rw}.title: non-empty string required")
            bullets = role.get("bullets")
            if not isinstance(bullets, list) or not bullets:
                errors.append(f"{rw}.bullets: non-empty array required")
            else:
                for j, bullet in enumerate(bullets):
                    bw = f"{rw}.bullets[{j}]"
                    if not isinstance(bullet, dict):
                        errors.append(f"{bw}: expected an object with text and source")
                        continue
                    unknown = sorted(set(bullet) - BULLET_KEYS)
                    if unknown:
                        errors.append(f"{bw}: unknown key(s) {unknown} — allowed: {sorted(BULLET_KEYS)}")
                    for key in ("text", "source"):
                        if not _nonempty_str(bullet.get(key, "")):
                            errors.append(f"{bw}.{key}: non-empty string required (rule 5 traceability)")
    for key in ("key_accounts", "proof_links"):
        value = data.get(key)
        if not isinstance(value, list) or not value:
            errors.append(f"{where}.{key}: non-empty array required")
        elif not all(_nonempty_str(x) for x in value):
            errors.append(f"{where}.{key}: non-empty strings required")
    return errors


def load_resume_input(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        sys.exit(f"{path} is not valid JSON: {exc}")
    errors = validate_resume_input(data)
    if errors:
        print(f"resume-input schema failed for {path} — nothing rendered:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    return data


# ---- template: fixed structure, ATS-safe, one page. PR A shape; PR B owns reweighting ----
def build_resume_html(me: dict, mode: str = "general") -> str:
    roles_html = "\n".join(
        f'    <h2 class="role-title">{r["title"]}</h2>\n'
        f'    <p class="role-meta">{r["company"]} ({r["dates"]})</p>\n'
        + "\n".join(f"    <li>{b['text']}</li>" for b in r["bullets"])
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
  <p class="key-accounts"><strong>Key accounts:</strong> {', '.join(me['key_accounts'])}</p>
  <section id="proof-links">
    <ul>
{links_html}
    </ul>
  </section>
</body>
</html>
"""


# ---- offline checks: the locked rules, verifiable without Chrome ---------------------------
def check_content_rules(html: str, json_text: str = "") -> list:
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
    # Rule 2 (PR B): client names never appear in bullet copy — outcomes are unnamed.
    # The account list is known only when the resume-input JSON is available. Match the
    # full name AND its parenthetical-stripped form, so "Northwind Analytics Co" is caught
    # even when the accounts list carries a "(fictional)" qualifier.
    if json_text:
        try:
            accounts = json.loads(json_text).get("key_accounts", [])
        except json.JSONDecodeError:
            accounts = []
        bullets = re.findall(r"<li>(.*?)</li>", html, re.S)
        for account in accounts:
            variants = {account.lower()}
            stripped = re.sub(r"\s*\([^)]*\)", "", account).strip().lower()
            if stripped:
                variants.add(stripped)
            for bullet in bullets:
                for variant in variants:
                    if variant in bullet.lower():
                        fails.append(f"rule 2: client name {account!r} appears in bullet copy — "
                                     "outcomes are described unnamed")
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
    # Rule 6 — gitignored private-input filenames never appear in output or committed JSON.
    for needle in PRIVATE_INPUT_NAMES:
        if needle in html or (json_text and needle in json_text):
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


# ---- posting-tailored reweighting (PR B): reorder, never rewrite ----------------------------
def jd_terms(jd_text: str) -> set:
    """Token set from a pasted JD; tokens of 2+ chars, lowercased, punctuation-split."""
    return {w for w in re.findall(r"[a-z0-9#+]+", jd_text.lower()) if len(w) > 1}


def _bullet_score(text: str, terms: set) -> int:
    return sum(1 for w in set(re.findall(r"[a-z0-9#+]+", text.lower())) if w in terms)


def reweight_for_jd(me: dict, jd_text: str) -> dict:
    """Deterministic JD reweighting: reorder roles and bullets by JD-term overlap.

    Locked-rule constraint (rule 5): reweighting NEVER writes a word — it can only
    reorder what the resume-input JSON already contains. Sorting is stable, so equal
    scores keep the me-model order and a JD with zero overlap is a no-op (which makes
    posting-tailored with a disjoint JD degrade to the general resume, visibly).
    """
    terms = jd_terms(jd_text)
    scored = []
    for i, role in enumerate(me["roles"]):
        bullet_scores = [(_bullet_score(b["text"], terms), j, b)
                         for j, b in enumerate(role["bullets"])]
        bullets = [b for _, _, b in sorted(bullet_scores, key=lambda t: (-t[0], t[1]))]
        role_score = sum(s for s, _, _ in bullet_scores)
        scored.append((-role_score, i, {**role, "bullets": bullets}))
    roles = [r for _, _, r in sorted(scored, key=lambda t: (t[0], t[1]))]
    return {**me, "roles": roles}


# ---- proof-link liveness (rule 4 "verified live"): opt-in, network-dependent ----------------
def verify_proof_links(links: list, timeout: int = 10) -> list:
    """HEAD each proof link; any failure means the link is not verified live (rule 4).

    Opt-in (`--verify-links`) because CI has no network guarantee; the SKILL.md
    in-session run passes it so a dead repo link never reaches the PDF.
    """
    errors = []
    for url in links:
        try:
            req = urllib.request.Request(url, method="HEAD",
                                         headers={"User-Agent": "resume-render/1.0 (link check)"})
            urllib.request.urlopen(req, timeout=timeout)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            errors.append(f"rule 4: proof link not live: {url} ({exc})")
    return errors


# ---- PDF gate (PR B): one page + pdftotext reading order — exit code gates the run ----------
def _squash(s: str) -> str:
    """Lowercase alphanumerics only — immune to line breaks, hyphenation and spacing."""
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def pdf_reading_order_errors(pdf_text: str, me: dict) -> list:
    """Pure check on extracted text: name → positioning → role titles in order → Key accounts.

    Matches on squashed text: pdftotext breaks lines mid-word at hyphens
    ("workflow-software" extracts as "workflowsoftware"), so exact substring
    matching on raw text would false-fail a perfectly ordered PDF.
    """
    flat = _squash(pdf_text)
    marks = [me["name"], me["positioning"]] \
        + [r["title"] for r in me["roles"]] + ["Key accounts"]
    # Monotonic search: each marker must appear AFTER the previous marker's position.
    # Plain find() would match a later marker inside earlier prose — "Account Executive"
    # occurs inside the positioning line "quota-carrying post-sales account executive".
    cursor = 0
    for m in marks:
        found = flat.find(_squash(m), cursor)
        if found == -1:
            return ["reading order broken in PDF text: expected name → positioning → "
                    "roles in order → Key accounts (marker "
                    f"{m[:40]!r} not found after position {cursor})"]
        cursor = found + len(_squash(m))
    return []


def verify_pdf(pdf_path: str, me: dict) -> list:
    """One-page + reading-order gate on the rendered PDF. pdftotext-missing is a loud
    skip (same pattern as the Chrome probe), never a silent pass."""
    errors = []
    with open(pdf_path, "rb") as fh:
        pages = pdf_page_count(fh.read())
    if pages != 1:
        errors.append(f"PDF is {pages} pages — the resume is ONE page; fix content, not margins")
    if shutil.which("pdftotext"):
        proc = subprocess.run(["pdftotext", pdf_path, "-"], capture_output=True,
                              text=True, timeout=30)
        if proc.returncode != 0:
            errors.append(f"pdftotext failed: {proc.stderr.strip()[:200]}")
        else:
            errors += pdf_reading_order_errors(proc.stdout, me)
    else:
        print("WARN pdftotext not found — PDF reading-order check skipped (install poppler-utils)")
    return errors


# ---- selftest: schema + rules + reading order + path guard, no Chrome (the CI path) --------
FIXTURE = os.path.join(SCRIPTS, os.pardir, "skills", "tailor-resume", "fixtures",
                       "resume-input-fixture.json")


def selftest() -> int:
    checks = []

    def case(name, ok):
        checks.append((name, ok))

    def schema_errors(data):
        return validate_resume_input(data)

    # The committed fixture validates and passes every locked rule + reading order.
    with open(FIXTURE, encoding="utf-8") as fh:
        fixture_text = fh.read()
    me = json.loads(fixture_text)
    html = build_resume_html(me)
    case("fixture JSON validates against the resume-input schema",
         schema_errors(me) == [])
    case("fixture renders all sections",
         all([me["name"], me["positioning"], me["roles"], me["key_accounts"], me["proof_links"]]))
    case("fixture passes all locked content rules", check_content_rules(html, fixture_text) == [])
    case("reading order name→positioning→roles→Key accounts", check_reading_order(html) == [])

    # Schema rejections — unknown keys, missing traceability, wrong shapes.
    case("schema refuses unknown top-level key",
         any("unknown key" in e for e in schema_errors({**me, "summary": "invented"})))
    case("schema refuses unknown role key",
         any("roles[0]" in e and "unknown key" in e
             for e in schema_errors({**me, "roles": [{**me["roles"][0], "grade": "S"}]})))
    bullet_missing_source = json.loads(fixture_text)
    del bullet_missing_source["roles"][0]["bullets"][0]["source"]
    case("schema refuses bullet without a trace-to-me-model source",
         any("source" in e for e in schema_errors(bullet_missing_source)))
    empty = json.loads(fixture_text)
    empty["positioning"] = ""
    case("schema refuses empty positioning", any("positioning" in e for e in schema_errors(empty)))
    case("schema refuses a non-object input", schema_errors(["not", "an", "object"]) != [])

    # Rule 1: a positioning line that doesn't lead with quota-carrying post-sales fails.
    bad = build_resume_html({**me, "positioning": "Customer success leader with deep renewals focus."})
    case("rule 1 catches non-quota-lead positioning",
         any(r.startswith("rule 1") for r in check_content_rules(bad)))

    # Rule 3: a vertical-territory label in a title fails.
    tilted = html.replace("Senior Account Executive", "Financial Services Account Executive")
    case("rule 3 catches vertical label in title",
         any(r.startswith("rule 3") for r in check_content_rules(tilted)))

    # Rule 4: a bare GitHub profile link fails; a specific repo passes.
    bare = html.replace("https://github.com/jaellis-fixture/resume-proof-fixture",
                        "https://github.com/jaellis-fixture")
    case("rule 4 catches bare GitHub profile link",
         any(r.startswith("rule 4") for r in check_content_rules(bare)))

    # Rule 6: the gitignored private-input filenames never appear in committed text.
    case("rule 6 catches private-input filename in output",
         any(r.startswith("rule 6") for r in check_content_rules(html, 'source": "from me-model.md')))

    # Rule 2 (PR B): a client name inside bullet copy fails; the Key accounts line is the only place.
    client_leak = json.loads(fixture_text)
    client_leak["roles"][0]["bullets"][0]["text"] += " Closed the Northwind Analytics Co deal."
    leak_html = build_resume_html(client_leak)
    case("rule 2 catches client name in bullet copy",
         any("rule 2" in r and "bullet copy" in r
             for r in check_content_rules(leak_html, json.dumps(client_leak))))

    # PR B — posting-tailored reweighting: reorder-only, deterministic, no-op on disjoint JDs.
    analytics_jd = "Own analytics pilots and multi-team rollout; unstick a stalled pilot into a rollout."
    reweighted = reweight_for_jd(me, analytics_jd)
    case("reweight promotes the JD-relevant role first",
         reweighted["roles"][0]["company"] == me["roles"][1]["company"])
    before = [b["text"] for r in me["roles"] for b in r["bullets"]]
    after = [b["text"] for r in reweighted["roles"] for b in r["bullets"]]
    case("reweight reorders but never rewrites a word", sorted(before) == sorted(after))
    case("reweight promotes the JD-relevant bullet within a role",
         [b["text"] for b in reweighted["roles"][0]["bullets"]][0]
         == me["roles"][1]["bullets"][1]["text"])
    case("zero-overlap JD leaves the me-model order untouched",
         reweight_for_jd(me, "xyzzy plugh zork")["roles"] == me["roles"])

    # PR B — PDF gate: pure reading-order check over extracted pdftotext text.
    good_text = f'{me["name"]} {me["positioning"]} ' + " ".join(r["title"] for r in me["roles"]) \
        + " Key accounts: everything after the roles"
    case("PDF reading-order check passes on ordered text",
         pdf_reading_order_errors(good_text, me) == [])
    scrambled = f'Key accounts first. {me["name"]} {me["positioning"]} ' \
        + " ".join(r["title"] for r in me["roles"])
    case("PDF reading-order check catches scrambled roles",
         pdf_reading_order_errors(scrambled, me) != [])

    # PR B — rule 4 liveness: an unparseable URL fails loudly without network.
    case("link liveness fails loudly on a non-URL",
         len(verify_proof_links(["not a url"])) == 1
         and verify_proof_links(["not a url"])[0].startswith("rule 4"))

    # Rule 7 / addition 3: the writer refuses any path outside .claude/output/.
    for bad_path in ("/tmp/resume.pdf", "./resume.pdf",
                     os.path.join(OUTPUT_DIR, os.pardir, "resume.pdf")):
        refused = False
        try:
            resolve_output_path(bad_path)
        except SystemExit:
            refused = True
        case(f"path guard refuses {os.path.basename(os.path.dirname(bad_path)) or bad_path}",
             refused)
    allowed = resolve_output_path(os.path.join(OUTPUT_DIR, "resume.pdf"))
    case("path guard allows .claude/output/resume.pdf", allowed == os.path.join(OUTPUT_DIR, "resume.pdf"))
    nested = resolve_output_path(os.path.join(OUTPUT_DIR, "sub", "resume.pdf"))
    case("path guard allows nested path under .claude/output/", nested.endswith("sub/resume.pdf"))
    alias = resolve_output_path(os.path.join(OUTPUT_DIR, os.pardir, "output", "resume.pdf"))
    case("path guard resolves ../output alias back into .claude/output/",
         alias == os.path.join(OUTPUT_DIR, "resume.pdf"))

    # Both modes render offline (reweighting happens before build; the template is mode-agnostic).
    case("both modes render without Chrome",
         all(build_resume_html(me, m) for m in ("general", "posting-tailored")))

    fails = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  {'ok  ' if ok else 'FAIL'} {n}")
    print(f"selftest: {len(checks) - len(fails)}/{len(checks)} render-resume cases pass")
    return 0 if not fails else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("source", nargs="?", help="path to a resume-input JSON (written by the skill)")
    ap.add_argument("--mode", choices=("general", "posting-tailored"), default="general")
    ap.add_argument("--out", default=os.path.join(OUTPUT_DIR, "resume.pdf"))
    ap.add_argument("--jd", help="pasted JD text file (required for --mode posting-tailored)")
    ap.add_argument("--verify-links", action="store_true",
                    help="rule 4: HEAD-check every proof link before rendering (needs network)")
    ap.add_argument("--selftest", action="store_true",
                    help="offline schema+rules+reading-order+guard checks, no Chrome")
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if not a.source:
        ap.error("a resume-input JSON path is required (or run --selftest)")
    if a.mode == "posting-tailored" and not a.jd:
        ap.error("--mode posting-tailored requires --jd <posting.txt>")

    me = load_resume_input(a.source)
    jd_reweighted = False
    if a.mode == "posting-tailored":
        with open(a.jd, encoding="utf-8") as fh:
            me = reweight_for_jd(me, fh.read())
        jd_reweighted = True
    html = build_resume_html(me, a.mode)

    with open(a.source, encoding="utf-8") as fh:
        json_text = fh.read()
    fails = check_content_rules(html, json_text) + check_reading_order(html)
    if fails:
        print("Content rules failed — nothing rendered:")
        for f in fails:
            print(f"  - {f}")
        return 1
    if a.verify_links:
        link_fails = verify_proof_links(me["proof_links"])
        if link_fails:
            print("Proof-link liveness failed — nothing rendered (rule 4: verified live):")
            for f in link_fails:
                print(f"  - {f}")
            return 1

    out = resolve_output_path(a.out)
    bin_ = chrome()
    if not bin_:
        sys.exit("Chrome not found — the Chrome render runs in-session where Chrome exists "
                 "(Alex's Mac); CI exercises `--selftest` (no Chrome).")

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

    # The PDF gate: exactly one page, pdftotext reading order intact — exit code gates the run.
    pdf_fails = verify_pdf(out, me)
    if pdf_fails:
        print("PDF gate failed:")
        for f in pdf_fails:
            print(f"  - {f}")
        return 1

    print(json.dumps({"ok": True, "pdf": out, "mode": a.mode,
                      "jd_reweighted": jd_reweighted, "roles": len(me["roles"])}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
