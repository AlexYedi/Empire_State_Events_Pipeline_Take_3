#!/usr/bin/env python3
"""Render a one-page, ATS-safe resume PDF from a resume-input JSON (YED-258, E-09 PR A).

The deterministic half of /tailor-resume, so a resume can't "look done" and still be wrong.
The pipeline is split so the renderer's private-input surface is zero:

  - **The skill** (`.claude/skills/tailor-resume/`, model-side, in session) reads
    `.claude/references/me-model.md` by path and writes a structured **resume-input JSON**
    to `.claude/output/`. This script NEVER opens the me-model — parsing it is not here
    (section-to-field mapping is a PRD decision for PR B with Alex).
  - **This script** consumes only that JSON: schema-validates it (refuses unknown keys),
    applies the locked content rules offline, builds the one-page ATS-safe **minimal
    template** (Alex's blind pick on PR #247, comment 6551704109: letter page, 0.4in/0.55in
    margins, Helvetica Neue 9.4pt, no colour accents; header name → contact; sections
    Positioning → Experience → Key accounts → Selected builds → Education), and prints it
    via headless Chrome `--print-to-pdf`, reusing render_carousel.py's chrome() path probe
    and run() method (no new render path — E-07's proven mechanism).
  - **PR B (YED-258)** — the content half now ships for real: the me-model → resume-input
    mapping is documented as the Blueprint default (Positioning → summary leading with
    quota-carrying post-sales; Experience → role entries with hunting-wins-as-account-growth
    framing; Key accounts → the logo list), posting-tailored mode **reweights** by re-ranking
    bullets inside each role against a pasted JD (roles stay in me-model order, YED-330;
    reorder-only — rule 5 forbids writing a word), proof
    links get an optional live check (`--verify-links`, rule 4 "verified live"), and the
    rendered PDF is gated: exactly one page, `pdftotext` reading order intact, and section
    labels extracted unbroken (the ATS letter-spacing cap), exit code gates the run.
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
import html as htmllib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
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
RESUME_INPUT_KEYS = {"name", "positioning", "contact", "roles", "key_accounts",
                     "proof_links", "builds", "education"}
# Always required. key_accounts and proof_links are each required unless their per-role /
# builds[] replacement is used instead (YED-280) — see validate_resume_input.
REQUIRED_KEYS = {"name", "positioning", "roles"}
ROLE_KEYS = {"title", "company", "dates", "bullets", "key_accounts"}
BULLET_KEYS = {"text", "source", "original"}
BUILD_KEYS = {"description", "links"}
# One line under Selected builds (YED-280). Over the cap is REFUSED, never truncated: an
# auto-ellipsis could cut a fact mid-figure ("grew 12…" of "grew 120%"), which rule 5
# forbids. The skill writes the line to fit; the renderer never adds or removes a word.
BUILD_DESCRIPTION_MAX = 70


def _nonempty_str(v) -> bool:
    return isinstance(v, str) and v.strip() != ""


def _nonempty_str_list(v) -> bool:
    return isinstance(v, list) and bool(v) and all(_nonempty_str(x) for x in v)


def uses_per_role_accounts(me: dict) -> bool:
    """Per-role mode (YED-280): any role carries its own key_accounts. The top-level
    Key accounts line is then suppressed — the schema refuses mixing the two, so nothing
    the skill wrote is ever dropped silently."""
    return any(isinstance(r, dict) and "key_accounts" in r for r in me.get("roles") or [])


# A key account is a string, or {name, aliases[]} (Alex, 2026-11-05): aliases are short
# forms rule 2 also blocks ("Quillmark" for "Quillmark Freight"). Only `name` renders.
ACCOUNT_KEYS = {"name", "aliases"}


def account_name(account) -> str:
    return account["name"] if isinstance(account, dict) else account


def account_names(accounts) -> list:
    return [account_name(a) for a in accounts or []]


def _account_list_errors(value, w: str) -> list:
    if not isinstance(value, list) or not value:
        return [f"{w}: optional, but when present it must be a non-empty array of accounts "
                "(a string, or {name, aliases[]})"]
    errors = []
    for k, a in enumerate(value):
        if isinstance(a, dict):
            unknown = sorted(set(a) - ACCOUNT_KEYS)
            if unknown:
                errors.append(f"{w}[{k}]: unknown key(s) {unknown} — allowed: {sorted(ACCOUNT_KEYS)}")
            if not _nonempty_str(a.get("name", "")):
                errors.append(f"{w}[{k}].name: non-empty string required")
            if not _nonempty_str_list(a.get("aliases")):
                errors.append(f"{w}[{k}].aliases: non-empty array of non-empty strings "
                              "required (use a plain string when there is no alias)")
        elif not _nonempty_str(a):
            errors.append(f"{w}[{k}]: a non-empty string or {{name, aliases[]}} required")
    return errors


def _all_account_items(me: dict) -> list:
    items = list(me.get("key_accounts") or [])
    for r in me.get("roles") or []:
        if isinstance(r, dict):
            items += r.get("key_accounts") or []
    return items


def all_key_accounts(me: dict) -> list:
    """Every client name the input declares (the rendered names)."""
    return account_names(_all_account_items(me))


def account_block_terms(me: dict) -> list:
    """(name, [name, *aliases]) per account — the rule-2 denylist for prose."""
    return [(account_name(a), [account_name(a)] + list(a.get("aliases", []))
             if isinstance(a, dict) else [a]) for a in _all_account_items(me)]


def proof_links(me: dict) -> list:
    """Every proof link, from builds[] when present, else the legacy proof_links[]."""
    if "builds" in me:
        return [u for b in me["builds"] for u in b["links"]]
    return me["proof_links"]


def validate_resume_input(data, where: str = "resume-input") -> list:
    """Validate the resume-input JSON contract; return a list of errors (empty = valid).

    Contract (skill-owned, written to .claude/output/):
      name, positioning              non-empty strings
      roles[]                        non-empty; {title, company, dates, bullets[]}
      bullets[]                      non-empty; {text, source[, original]} — `source` is the
                                     trace-to-me-model note (rule 5), required per bullet;
                                     `original` (optional) is the verbatim me-model wording,
                                     required whenever the skill reworded the bullet for a
                                     posting (spec-walk decision 2, 2026-10-31)
      key_accounts[], proof_links[]  non-empty arrays of non-empty strings
      roles[].key_accounts[]         OPTIONAL per-role logo line (YED-280). When any role
                                     carries one, the top-level key_accounts must be absent
                                     (its line is suppressed; mixing would drop data).
      builds[]                       OPTIONAL replacement for proof_links (YED-280):
                                     {links[], description?} — description is one line,
                                     ≤ BUILD_DESCRIPTION_MAX chars, refused (never
                                     truncated) when longer. Exactly one of proof_links /
                                     builds.
      contact[], education[]         OPTIONAL arrays of non-empty strings (minimal-template
                                     follow-up, PR #247 comment 6551704109): the header
                                     contact line and the one-line Education section
                                     (degree · activities · certs). Absent → section omitted.
    Unknown keys are refused at every level; nothing is coerced or dropped.
    """
    errors = []
    if not isinstance(data, dict):
        return [f"{where}: expected an object, got {type(data).__name__}"]
    unknown = sorted(set(data) - RESUME_INPUT_KEYS)
    if unknown:
        errors.append(f"{where}: unknown key(s) {unknown} — allowed: {sorted(RESUME_INPUT_KEYS)}")
    missing = sorted(REQUIRED_KEYS - set(data))
    if missing:
        errors.append(f"{where}: missing key(s) {missing}")
    per_role = uses_per_role_accounts(data)
    if per_role and "key_accounts" in data:
        errors.append(f"{where}: key_accounts given both top-level and per role — use one: "
                      "per-role lines suppress the top-level line, so it would be dropped")
    if not per_role and "key_accounts" not in data:
        errors.append(f"{where}: missing key(s) ['key_accounts'] (top-level, or per role "
                      "as roles[].key_accounts)")
    if ("proof_links" in data) == ("builds" in data):
        errors.append(f"{where}: exactly one of proof_links / builds required "
                      f"(got {'both' if 'builds' in data else 'neither'})")
    builds = data.get("builds")
    if "builds" in data and (not isinstance(builds, list) or not builds):
        errors.append(f"{where}.builds: non-empty array required when present")
    elif isinstance(builds, list):
        for k, build in enumerate(builds):
            bw = f"{where}.builds[{k}]"
            if not isinstance(build, dict):
                errors.append(f"{bw}: expected an object with links[] and an optional description")
                continue
            unknown = sorted(set(build) - BUILD_KEYS)
            if unknown:
                errors.append(f"{bw}: unknown key(s) {unknown} — allowed: {sorted(BUILD_KEYS)}")
            if not _nonempty_str_list(build.get("links")):
                errors.append(f"{bw}.links: non-empty array of non-empty strings required")
            if "description" in build:
                desc = build["description"]
                if not _nonempty_str(desc) or "\n" in desc:
                    errors.append(f"{bw}.description: one non-empty line required when present")
                elif len(desc) > BUILD_DESCRIPTION_MAX:
                    errors.append(f"{bw}.description: {len(desc)} chars, over the "
                                  f"{BUILD_DESCRIPTION_MAX}-char one-line cap — shorten it "
                                  "(the renderer never truncates)")
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
            if "key_accounts" in role:
                errors += _account_list_errors(role["key_accounts"], f"{rw}.key_accounts")
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
                    if "original" in bullet and not _nonempty_str(bullet["original"]):
                        errors.append(f"{bw}.original: non-empty string required when present "
                                      "(verbatim me-model wording of a reworded bullet)")
    if "key_accounts" in data:
        errors += _account_list_errors(data["key_accounts"], f"{where}.key_accounts")
    for key in ("proof_links", "contact", "education"):
        value = data.get(key)
        if key in data and (not isinstance(value, list) or not value
                            or not all(_nonempty_str(x) for x in value)):
            errors.append(f"{where}.{key}: optional, but when present it must be a "
                          "non-empty array of non-empty strings")
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


# ---- template: minimal spec (Alex's blind pick, PR #247 comment 6551704109) -----------------
# Letter page, 0.4in/0.55in margins, Helvetica Neue 9.4pt, line-height 1.27, text #16181d,
# no colour accents. Section-label letter-spacing is an ATS cap: at 1.2pt pdftotext
# extracts "E D U C AT I O N", which breaks ATS parsing — the PDF gate asserts the cap
# on the rendered sample, since pdftotext output is the exact surface it protects.
SECTION_LABEL_LETTER_SPACING_PT = 0.3
PALETTE = ("#16181d", "#5a5f6b", "#c9ccd3", "#3c4049")  # every colour the template may use
SECTION_LABELS = {"experience": "Experience", "key-accounts": "Key accounts",
                  "selected-builds": "Selected builds", "education": "Education"}


def _esc(s: str) -> str:
    """Text-node escape (& < >). Every resume-input field goes through this or _esc_attr;
    quotes stay literal in text so plain-ASCII input renders byte-identical to before."""
    return htmllib.escape(s, quote=False)


def _esc_attr(s: str) -> str:
    return htmllib.escape(s, quote=True)


def _join(items, sep: str) -> str:
    return sep.join(_esc(x) for x in items)


def _role_accounts_html(r: dict) -> str:
    if not r.get("key_accounts"):
        return ""
    return ('\n    <p class="role-accounts"><span class="role-accounts-label">Key accounts:'
            f'</span> {_join(account_names(r["key_accounts"]), ", ")}</p>')


def _build_items(me: dict) -> list:
    """Selected-builds <li>s. Legacy proof_links and description-less builds render one
    link per <li>, exactly as before; a described build is one <li>: description, then
    its links."""
    def anchor(u):
        return f'<a href="{_esc_attr(u)}">{_esc(u)}</a>'
    if "builds" not in me:
        return [f"<li>{anchor(u)}</li>" for u in me["proof_links"]]
    items = []
    for b in me["builds"]:
        anchors = [anchor(u) for u in b["links"]]
        if b.get("description"):
            items.append(f'<li><span class="build-desc">{_esc(b["description"])}</span> — '
                         + " · ".join(anchors) + "</li>")
        else:
            items += [f"<li>{a}</li>" for a in anchors]
    return items


def build_resume_html(me: dict, mode: str = "general") -> str:
    roles_html = "\n".join(
        f'    <div class="role-head">\n'
        f'      <h3 class="role-title">{_esc(r["title"])}</h3>\n'
        f'      <span class="role-dates">{_esc(r["dates"])}</span>\n'
        f'    </div>\n'
        f'    <p class="role-company">{_esc(r["company"])}</p>\n'
        f'    <ul class="bullets">\n'
        + "\n".join(f"      <li>{_esc(b['text'])}</li>" for b in r["bullets"]) + "\n    </ul>"
        + _role_accounts_html(r)
        for r in me["roles"])
    links_html = "\n".join(f"      {li}" for li in _build_items(me))
    # Top-level logo line only in legacy mode; per-role mode suppresses it (YED-280).
    key_accounts_html = ""
    if me.get("key_accounts"):
        key_accounts_html = (
            '  <section class="key-accounts">\n'
            '    <h2 class="section-label">Key accounts</h2>\n'
            f'    <p class="logo-line">{_join(account_names(me["key_accounts"]), ", ")}</p>\n'
            '  </section>')
    contact_html = ""
    if me.get("contact"):
        contact_html = f'\n  <p class="contact">{_join(me["contact"], " · ")}</p>'
    education_html = ""
    if me.get("education"):
        education_html = (
            '  <section id="education">\n'
            '    <h2 class="section-label">Education</h2>\n'
            f'    <p class="education-line">{_join(me["education"], " · ")}</p>\n'
            '  </section>')
    name, positioning = _esc(me["name"]), _esc(me["positioning"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{name} — Resume ({mode})</title>
<style>
  /* Minimal template — the winning blind-pick variant (PR 247, Alex's design decision).
     ATS-safe: single column, standard fonts, text-selectable (Chrome --print-to-pdf).
     No accents: the palette below is the full colour set this template may emit. */
  @page {{ size: letter; margin: 0.4in 0.55in; }}
  body {{ font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 9.4pt;
          line-height: 1.27; color: #16181d; margin: 0; }}
  header {{ border-bottom: 0.6pt solid #c9ccd3; padding-bottom: 6pt; }}
  h1 {{ font-size: 20pt; font-weight: 600; letter-spacing: -0.2pt; margin: 0; }}
  p.contact {{ font-size: 9pt; color: #5a5f6b; margin: 2pt 0 0; }}
  p.positioning {{ font-size: 10.5pt; margin: 8pt 0 2pt; }}
  h2.section-label {{ font-size: 8.5pt; font-weight: 600; text-transform: uppercase;
                      color: #5a5f6b; letter-spacing: 0.3pt; margin: 10pt 0 3pt; }}
  .role-head {{ display: flex; justify-content: space-between; align-items: baseline; }}
  h3.role-title {{ font-size: 10.5pt; font-weight: 600; margin: 4pt 0 0; }}
  span.role-dates {{ font-size: 9pt; color: #5a5f6b; font-variant-numeric: tabular-nums; }}
  p.role-company {{ font-size: 9.5pt; color: #3c4049; margin: 0; }}
  ul {{ margin: 1pt 0 3pt; padding-left: 12pt; }}
  li {{ margin: 0 0 1.5pt; }}
  p.logo-line, p.education-line {{ margin: 0; }}
  p.role-accounts {{ font-size: 9pt; color: #3c4049; margin: 0 0 3pt; }}
  span.role-accounts-label {{ font-weight: 600; }}
</style>
</head>
<body>
  <header>
    <h1 class="resume-name">{name}</h1>{contact_html}
  </header>
  <p class="positioning">{positioning}</p>
  <section id="experience">
    <h2 class="section-label">Experience</h2>
{roles_html}
  </section>
{key_accounts_html}
  <section id="selected-builds">
    <h2 class="section-label">Selected builds</h2>
    <ul>
{links_html}
    </ul>
  </section>
{education_html}
</body>
</html>
"""


# ---- rule-2 matching: normalise both sides, then whole-word match (YED-280 review) ---------
# NFKC does not fold Cyrillic/Greek look-alikes into Latin ("а" U+0430 stays Cyrillic), so
# the common ones are mapped explicitly. Not a full UTS #39 confusables table: a look-alike
# outside this map still slips through (documented in SKILL.md).
_CONFUSABLES = str.maketrans({
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y", "х": "x", "і": "i",
    "ј": "j", "ѕ": "s", "ԁ": "d", "һ": "h", "А": "A", "В": "B", "Е": "E", "К": "K",
    "М": "M", "Н": "H", "О": "O", "Р": "P", "С": "C", "Т": "T", "Х": "X", "І": "I",
    "ο": "o", "α": "a", "ν": "v", "ρ": "p", "ι": "i", "Α": "A", "Β": "B", "Ε": "E",
    "Ζ": "Z", "Η": "H", "Ι": "I", "Κ": "K", "Μ": "M", "Ν": "N", "Ο": "O", "Ρ": "P",
    "Τ": "T", "Υ": "Y", "Χ": "X"})
_APOSTROPHES = str.maketrans({c: "'" for c in "’‘ʼ′`"})


def normalise_for_match(text: str) -> str:
    """Case-kept normal form for rule 2: tags stripped and entities unescaped (repeated, so
    an escaped tag or a double-escaped &amp; also resolves), NFKC, Latin look-alikes,
    one apostrophe, dashes between letters as a space, whitespace runs collapsed."""
    for _ in range(3):
        text = htmllib.unescape(re.sub(r"<[^>]*>", "", text))
    text = unicodedata.normalize("NFKC", text).translate(_CONFUSABLES).translate(_APOSTROPHES)
    text = re.sub(r"(?<=\w)[-‐‑‒–—―](?=\w)", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _account_variants(account: str) -> list:
    """The full name and its parenthetical-stripped form ("Northwind Analytics Co")."""
    variants = [normalise_for_match(account)]
    stripped = normalise_for_match(re.sub(r"\s*\([^)]*\)", "", account))
    if stripped and stripped not in variants:
        variants.append(stripped)
    return [v for v in variants if v]


def names_account(text: str, account: str) -> bool:
    """True when `text` names `account` as a whole word sequence (optional possessive 's),
    after normalising both sides and casefolding. Also catches the space-stripped form
    ("QuillmarkFreight"). A ONE-word account must also be capitalised where it appears,
    so "Gap" trips "Gap" / "GAP" but not "the pipeline gap"."""
    kept = normalise_for_match(text)
    folded = kept.casefold()
    for variant in _account_variants(account):
        words = variant.casefold().split(" ")
        forms = [r"\s".join(map(re.escape, words))]
        if len(words) > 1:
            forms.append(re.escape("".join(words)))
        for form in forms:
            pattern = rf"(?<!\w){form}(?:'s)?(?!\w)"
            if len(words) > 1:
                if re.search(pattern, folded):
                    return True
            elif any(m.group(0)[0].isupper()
                     for m in re.finditer(pattern, kept, re.IGNORECASE)):
                return True
    return False


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
    # Rule 2 — client names only as Key accounts logo lines (addition 2): the one top-level
    # line, OR per-role lines under their roles (YED-280) — never both.
    role_lines = html.count('class="role-accounts"')
    if role_lines and 'class="key-accounts"' in html:
        fails.append("rule 2: per-role Key accounts lines and a top-level line both rendered")
    elif not role_lines and html.count('class="key-accounts"') != 1:
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
            data = json.loads(json_text)
        except json.JSONDecodeError:
            data = {}
        accounts = account_block_terms(data) if isinstance(data, dict) else []
        # List items = bullets + build descriptions. Link anchors are left unscanned (a
        # known limitation, SKILL.md): a URL slug is not prose.
        bullets = [re.sub(r"<a\b[^>]*>.*?</a>", " ", b, flags=re.S)
                   for b in re.findall(r"<li>(.*?)</li>", html, re.S)]
        # Everything else a reader sees, minus the logo lines themselves and the employer
        # field (YED-280: positioning, titles, dates, headers — not only bullets — are prose).
        # Tags become line breaks so separate elements never fuse into one word; tags
        # INSIDE a field are escaped text here and fuse back in normalise_for_match.
        prose = re.sub(r"<head>.*?</head>|<li>.*?</li>"
                       r'|<p class="(?:logo-line|role-accounts|role-company)">.*?</p>',
                       "\n", html, flags=re.S)
        prose = re.sub(r"<[^>]+>", "\n", prose)
        for account, terms in accounts:  # terms = name + every alias
            for bullet in bullets:
                if any(names_account(bullet, t) for t in terms):
                    fails.append(f"rule 2: client name {account!r} appears in bullet copy — "
                                 "outcomes are described unnamed")
            if any(names_account(prose, t) for t in terms):
                fails.append(f"rule 2: client name {account!r} appears outside a Key accounts "
                             "line — outcomes are described unnamed")
            # Decision 2 (spec walk 2026-10-31): the verbatim `original` of a reworded
            # bullet never names clients either — rule 2 covers BOTH texts.
            for i, role in enumerate(data.get("roles", [])):
                for j, b in enumerate(role.get("bullets", [])):
                    original = b.get("original", "")
                    if isinstance(original, str) and any(names_account(original, t) for t in terms):
                        fails.append(f"rule 2: client name {account!r} appears in the original "
                                     f"of roles[{i}].bullets[{j}] — outcomes are described unnamed")
    # Rule 3 — no vertical-territory labels in titles (PR-B review addition).
    for title in re.findall(r'<h3 class="role-title">(.*?)</h3>', html, re.S):
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


def check_reading_order(html: str, me: dict | None = None) -> list:
    """Name → positioning → roles → Key accounts → Selected builds → Education, in DOM order
    (PR-A exit d; extended to the minimal-template sections). Education is conditional on
    the resume-input — pass `me` to have its absence flagged; without `me`, an education
    section present in the HTML is still checked for position. With `me`, each role title
    is checked in order and a per-role Key accounts line (YED-280) must sit after its own
    role's title and before the next role's."""
    marks = [('class="resume-name"', "name"), ('class="positioning"', "positioning"),
             ('id="experience"', "roles")]
    per_role = me is not None and uses_per_role_accounts(me)
    if me is not None:
        for r in me["roles"]:
            marks.append((f'<h3 class="role-title">{_esc(r["title"])}</h3>', f"role {r['title']!r}"))
            if r.get("key_accounts"):  # this role's own list, not just any accounts line
                marks.append(('class="role-accounts"', f"Key accounts under {r['title']!r}"))
                marks.append((f'</span> {_join(account_names(r["key_accounts"]), ", ")}</p>',
                              f"Key accounts under {r['title']!r}"))
    if not per_role:
        marks.append(('class="key-accounts"', "Key accounts"))
    marks.append(('id="selected-builds"', "Selected builds"))
    if me is not None and me.get("education"):
        marks.append(('id="education"', "Education"))
    cursor = 0
    for m, label in marks:  # monotonic: each marker after the previous one
        found = html.find(m, cursor)
        if found == -1:
            return ["reading order broken: expected name → positioning → roles (each with "
                    "its Key accounts line when per-role) → Key accounts → Selected builds "
                    f"(→ Education when present) — {label} out of place"]
        cursor = found + len(m)
    return []


# ---- template-spec guards (minimal template, PR #247 comment 6551704109) ---------------------
def list_structure_errors(html: str) -> list:
    """Every <li> must sit inside a <ul> — the PR-A template emitted bare <li>, which
    renders but is malformed HTML and confuses strict ATS parsers."""
    without_uls = re.sub(r"<ul\b[^>]*>.*?</ul>", "", html, flags=re.S)
    if "<li" in without_uls:
        return ["list structure broken: a <li> appears outside any <ul>"]
    return []


def palette_errors(html: str) -> list:
    """No colour accents: every hex colour in the output must be one of the template's
    neutral palette values (the acid-green #8FE83A accent variant lost the blind pick)."""
    used = {c.lower() for c in re.findall(r"#[0-9a-fA-F]{3,8}\b", html)}
    stray = sorted(used - {c.lower() for c in PALETTE})
    if stray:
        return [f"colour accent detected — only the neutral palette {list(PALETTE)} is "
                f"allowed, found {stray}"]
    return []


def letter_spacing_errors(html: str) -> list:
    """Section-label letter-spacing must stay at or under the ATS cap (0.3pt). At 1.2pt
    pdftotext extracts "E D U C AT I O N" and ATS parsing breaks — see
    section_label_extraction_errors, the rendered-PDF twin of this check."""
    over = [v for v in re.findall(r"letter-spacing:\s*(-?[\d.]+)pt", html)
            if float(v) > SECTION_LABEL_LETTER_SPACING_PT]
    if over:
        return [f"letter-spacing over the {SECTION_LABEL_LETTER_SPACING_PT}pt ATS cap: {over}"]
    return []


# ---- posting-tailored reweighting (PR B): reorder, never rewrite ----------------------------
def jd_terms(jd_text: str) -> set:
    """Token set from a pasted JD; tokens of 2+ chars, lowercased, punctuation-split."""
    return {w for w in re.findall(r"[a-z0-9#+]+", jd_text.lower()) if len(w) > 1}


def _bullet_score(text: str, terms: set) -> int:
    return sum(1 for w in set(re.findall(r"[a-z0-9#+]+", text.lower())) if w in terms)


def reweight_for_jd(me: dict, jd_text: str) -> dict:
    """Deterministic JD reweighting: re-rank bullets inside each role by JD-term overlap.

    Roles never move: they keep the input (me-model, reverse-chronological) order
    (YED-330, Alex 2026-11-05, amends spec-walk decision 2's "roles ranked by JD-term
    overlap"). The SCRIPT never writes a word — it only reorders what the JSON contains.
    Bullet REWORDING is model-side (the skill), constrained by spec-walk decision 2
    (2026-10-31): a reworded bullet carries `original` (its verbatim me-model wording)
    and rewording_fidelity_errors() pins its facts to that original. Sorting is stable,
    so equal scores keep the me-model order and a JD with zero overlap is a no-op
    (which makes posting-tailored with a disjoint JD degrade to the general resume,
    visibly).
    """
    terms = jd_terms(jd_text)
    roles = []
    for role in me["roles"]:
        bullet_scores = [(_bullet_score(b["text"], terms), j, b)
                         for j, b in enumerate(role["bullets"])]
        bullets = [b for _, _, b in sorted(bullet_scores, key=lambda t: (-t[0], t[1]))]
        roles.append({**role, "bullets": bullets})
    return {**me, "roles": roles}


# ---- constrained-rewording fidelity gate (spec-walk decision 2, 2026-10-31) -----------------
_FACT_RE = re.compile(r"\$?\d[\d,.]*[KMB%xX]?")
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9-]*")
_WORD_PIECE_RE = re.compile(r"[A-Za-z]+")

# Spelled-out quantities are facts (review 2026-11-01): "three-rep" vs "two-rep" is the
# same class of invention as "$920K" vs "$860K". Matched as hyphen-split word pieces.
_NUMBER_WORDS = frozenset("""one two three four five six seven eight nine ten eleven
    twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty
    forty fifty sixty seventy eighty ninety hundred thousand million billion dozen half
    double triple twice""".split())

# A bullet's first word is capitalized by convention, not by being a proper noun — but
# only action verbs get that pass (review 2026-11-01). Anything else capitalized in the
# leading position ("Heliosoft: closed …") is a fact the original must carry. The
# allowlist is documented in SKILL.md; the fixture test cross-checks the two stay in sync
# (the renderer cannot depend on skill files at runtime).
ACTION_FIRST_WORDS = frozenset(
    "closed drove grew owned led built sold saved landed scaled enabled applied".split())


def _fact_tokens(text: str) -> list:
    """Facts the fidelity gate pins: numbers/$-figures/percentages, spelled-out
    quantities, and proper-noun candidates (capitalized tokens — the first word only
    when it is not an allowlisted action verb; single-letter tokens are unit suffixes
    like the K in $860K, except "I")."""
    tokens = _FACT_RE.findall(text)
    words = _WORD_RE.findall(text)
    tokens += [w for i, w in enumerate(words)
               if w[0].isupper() and (len(w) > 1 or w == "I")
               and not (i == 0 and w.lower() in ACTION_FIRST_WORDS)]
    tokens += [w for w in _WORD_PIECE_RE.findall(text) if w.lower() in _NUMBER_WORDS]
    return list(dict.fromkeys(tokens))


def original_required_errors(me: dict) -> list:
    """Always-on `original` in posting-tailored mode (review 2026-11-01): every bullet
    carries `original` — its verbatim me-model wording, set equal to `text` when the
    bullet is not reworded. Today a reworded bullet that omits `original` skips the
    fidelity gate silently and the renderer cannot tell; the contract makes that
    impossible instead of trusting the skill to self-mark."""
    fails = []
    for i, role in enumerate(me.get("roles", [])):
        for j, bullet in enumerate(role.get("bullets", [])):
            original = bullet.get("original", "")
            if not (isinstance(original, str) and original.strip()):
                fails.append(f"rule 5 (always-on original): roles[{i}].bullets[{j}] has "
                             "no `original` — posting-tailored requires it on every "
                             "bullet (set it equal to `text` when not reworded)")
    return fails


def rewording_fidelity_errors(me: dict) -> list:
    """Gate for spec-walk decision 2: a reworded bullet may use the posting's vocabulary
    but may add NO new facts. Every number/$-figure/percentage and proper noun in the
    reworded text must appear in the bullet's `original` (its verbatim me-model wording),
    or the run fails naming the bullet. Bullets without `original` pass here untouched —
    posting-tailored mode refuses them upstream via original_required_errors()."""
    fails = []
    for i, role in enumerate(me.get("roles", [])):
        for j, bullet in enumerate(role.get("bullets", [])):
            original = bullet.get("original", "")
            if not (isinstance(original, str) and original.strip()):
                continue
            missing = [t for t in _fact_tokens(bullet["text"])
                       if not re.search(rf"(?<!\w){re.escape(t)}(?!\w)", original, re.I)]
            if missing:
                fails.append(f"rule 5 (rewording fidelity): roles[{i}].bullets[{j}] "
                             f"introduces fact token(s) {missing} absent from its original "
                             f"(verbatim me-model wording): {bullet['text'][:60]!r}")
    return fails


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
    """Pure check on extracted text: name → positioning → role titles in order → Key accounts
    → Selected builds → (Education when present).

    Matches on squashed text: pdftotext breaks lines mid-word at hyphens
    ("workflow-software" extracts as "workflowsoftware"), so exact substring
    matching on raw text would false-fail a perfectly ordered PDF.
    """
    flat = _squash(pdf_text)
    marks = [me["name"], me["positioning"]]
    for r in me["roles"]:
        marks.append(r["title"])
        if r.get("key_accounts"):  # per-role line, under its own role (YED-280)
            marks.append("Key accounts: " + ", ".join(account_names(r["key_accounts"])))
    if me.get("key_accounts"):
        marks.append("Key accounts")
    marks.append("Selected builds")
    marks += [b["description"] for b in me.get("builds", []) if b.get("description")]
    if me.get("education"):
        marks.append(" ".join(me["education"]))  # the one-line Education section content
    # Monotonic search: each marker must appear AFTER the previous marker's position.
    # Plain find() would match a later marker inside earlier prose — "Account Executive"
    # occurs inside the positioning line "quota-carrying post-sales account executive".
    cursor = 0
    for m in marks:
        found = flat.find(_squash(m), cursor)
        if found == -1:
            return ["reading order broken in PDF text: expected name → positioning → "
                    "roles in order → Key accounts → Selected builds (→ Education when "
                    "present) (marker "
                    f"{m[:40]!r} not found after position {cursor})"]
        cursor = found + len(_squash(m))
    return []


def section_label_extraction_errors(pdf_text: str, labels: list) -> list:
    """The ATS cap, asserted on the surface it protects: each section-label word must be
    extracted by pdftotext as an unbroken token. Over-spaced labels extract as
    "E D U C AT I O N" — real ATS parsers die exactly there."""
    errors = []
    for label in labels:
        for word in label.split():
            if len(word) >= 3 and not re.search(rf"\b{re.escape(word)}\b", pdf_text):
                errors.append(f"section label {label!r} extracted with internal spaces "
                              f"({word!r} not found unbroken) — letter-spacing over the "
                              f"{SECTION_LABEL_LETTER_SPACING_PT}pt ATS cap?")
    return errors


# The documented one-page envelopes (SKILL.md "Fit"), measured on rendered samples.
FIT_ENVELOPE = {"per-role": (6, 13), "top-level": (7, 15)}


def fit_summary(me: dict) -> str:
    """Why a render overflowed: this input's counts against the documented envelope."""
    roles = len(me["roles"])
    bullets = sum(len(r["bullets"]) for r in me["roles"])
    account_lines = sum(1 for r in me["roles"] if r.get("key_accounts"))
    described = sum(1 for b in me.get("builds", []) if b.get("description"))
    mode = "per-role" if account_lines else "top-level"
    max_roles, max_bullets = FIT_ENVELOPE[mode]
    return (f"This input: {roles} roles, {bullets} bullets, {account_lines} per-role Key "
            f"accounts lines, {described} described builds. Documented envelope ({mode} "
            f"accounts): {max_roles} roles / {max_bullets} bullets"
            + (" with every per-role line and description at max." if mode == "per-role"
               else " with the top-level Key accounts line.")
            + " Cut roles or bullets first.")


def verify_pdf(pdf_path: str, me: dict) -> list:
    """One-page + reading-order + label-extraction gate on the rendered PDF.
    pdftotext-missing is a loud skip (same pattern as the Chrome probe), never a silent
    pass."""
    errors = []
    with open(pdf_path, "rb") as fh:
        pages = pdf_page_count(fh.read())
    if pages != 1:
        errors.append(f"PDF is {pages} pages — the resume is ONE page; fix content, not "
                      f"margins. {fit_summary(me)}")
    if shutil.which("pdftotext"):
        proc = subprocess.run(["pdftotext", pdf_path, "-"], capture_output=True,
                              text=True, timeout=30)
        if proc.returncode != 0:
            errors.append(f"pdftotext failed: {proc.stderr.strip()[:200]}")
        else:
            errors += pdf_reading_order_errors(proc.stdout, me)
            labels = [SECTION_LABELS["experience"], SECTION_LABELS["selected-builds"]]
            if me.get("key_accounts"):  # the top-level section exists only in legacy mode
                labels.insert(1, SECTION_LABELS["key-accounts"])
            if me.get("education"):
                labels.append(SECTION_LABELS["education"])
            errors += section_label_extraction_errors(proc.stdout,
                                                      [l.upper() for l in labels])
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
    case("reading order name→positioning→roles→Key accounts→Selected builds→Education",
         check_reading_order(html, me) == [])
    # Minimal-template spec (PR #247 comment 6551704109): well-formed lists, neutral
    # palette only, section-label letter-spacing at or under the ATS cap.
    case("every <li> sits inside a <ul>", list_structure_errors(html) == [])
    bare_li = html.replace('<ul class="bullets">\n      <li>', "")
    case("a bare <li> outside any <ul> fails", list_structure_errors(bare_li) != [])
    case("template emits only the neutral palette (no colour accents)",
         palette_errors(html) == [])
    accent = html.replace("color: #5a5f6b", "color: #8FE83A")
    case("a colour accent fails the palette check", palette_errors(accent) != [])
    case("section-label letter-spacing is at or under the 0.3pt ATS cap",
         letter_spacing_errors(html) == [] and "letter-spacing: 0.3pt" in html)
    overspaced = html.replace("letter-spacing: 0.3pt", "letter-spacing: 1.2pt")
    case("1.2pt letter-spacing (the known-bad value) fails the cap",
         letter_spacing_errors(overspaced) != [])

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

    # Minimal-template follow-up (PR #247 comment 6551704109): optional contact and
    # education arrays — present and well-formed passes; wrong shapes refused.
    case("schema accepts optional contact and education arrays",
         schema_errors({**me, "contact": ["New York, NY"],
                        "education": ["B.A., State University (fictional)"]}) == [])
    case("schema refuses a non-list contact",
         any("contact" in e for e in schema_errors({**me, "contact": "New York, NY"})))
    case("schema refuses an empty education item",
         any("education" in e for e in schema_errors({**me, "education": [""]})))

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

    # PR B — spec-walk decision 2 (2026-10-31): constrained rewording. The skill may reword
    # a bullet into the posting's vocabulary; it carries `original` (verbatim me-model
    # wording) and the renderer pins the reworded text's facts to it.
    reword_ok = json.loads(json.dumps(me))
    reword_ok["roles"][0]["bullets"][0] = {
        "text": "Drove $860K in new and expansion revenue across a two-rep territory "
                "(proof of account growth).",
        "source": reword_ok["roles"][0]["bullets"][0]["source"],
        "original": "Closed $860K of new and expansion revenue in a two-rep territory "
                    "(proof of account growth).",
    }
    case("rewording fidelity passes a faithful reword",
         rewording_fidelity_errors(reword_ok) == [])
    reword_num = json.loads(json.dumps(reword_ok))
    reword_num["roles"][0]["bullets"][0]["text"] = \
        "Drove $920K in new revenue across a two-rep territory."
    case("rewording fidelity fails an invented number",
         any("rewording fidelity" in r for r in rewording_fidelity_errors(reword_num)))
    reword_noun = json.loads(json.dumps(reword_ok))
    reword_noun["roles"][0]["bullets"][0]["text"] = \
        "Closed $860K of new and expansion revenue at Heliosoft."
    case("rewording fidelity fails an invented proper noun",
         any("rewording fidelity" in r for r in rewording_fidelity_errors(reword_noun)))
    reword_client = json.loads(json.dumps(reword_ok))
    reword_client["roles"][0]["bullets"][0]["text"] = "Closed the Northwind Analytics Co deal."
    case("rule 2 catches client name in reworded bullet copy",
         any("rule 2" in r and "bullet copy" in r
             for r in check_content_rules(build_resume_html(reword_client),
                                          json.dumps(reword_client))))
    reword_client_orig = json.loads(json.dumps(reword_ok))
    reword_client_orig["roles"][0]["bullets"][0]["original"] = \
        "Closed the Northwind Analytics Co deal."
    case("rule 2 catches client name in a bullet's original",
         any("rule 2" in r and "original" in r
             for r in check_content_rules(build_resume_html(reword_client_orig),
                                          json.dumps(reword_client_orig))))
    case("schema accepts an optional original on a bullet",
         schema_errors(reword_ok) == [])
    bad_original = json.loads(json.dumps(reword_ok))
    bad_original["roles"][0]["bullets"][0]["original"] = ""
    case("schema refuses an empty original",
         any("original" in e for e in schema_errors(bad_original)))

    # Review 2026-11-01 probes: spelled-out quantities are facts; the first word is
    # exempt only when it is an allowlisted action verb.
    reword_spell = json.loads(json.dumps(reword_ok))
    reword_spell["roles"][0]["bullets"][0]["text"] = \
        "Drove $860K of new revenue in a three-rep territory."
    case("rewording fidelity fails an invented spelled-out quantity",
         any("rewording fidelity" in r for r in rewording_fidelity_errors(reword_spell)))
    reword_first = json.loads(json.dumps(reword_ok))
    reword_first["roles"][0]["bullets"][0]["text"] = \
        "Heliosoft: closed $860K of new revenue in a two-rep territory."
    case("rewording fidelity fails a non-allowlisted first word (Heliosoft probe)",
         any("rewording fidelity" in r for r in rewording_fidelity_errors(reword_first)))
    no_original = json.loads(json.dumps(reword_ok))
    del no_original["roles"][0]["bullets"][0]["original"]
    case("posting-tailored refuses a bullet without original",
         any("always-on original" in r for r in original_required_errors(no_original)))
    case("every-bullet contract flags a fixture with no originals",
         original_required_errors(me) != [])

    # PR B — posting-tailored reweighting: reorder-only, deterministic, no-op on disjoint JDs.
    analytics_jd = "Own analytics pilots and multi-team rollout; unstick a stalled pilot into a rollout."
    reweighted = reweight_for_jd(me, analytics_jd)
    # YED-330: the later role out-scores the first (7 vs 0 JD-term hits) yet roles keep
    # me-model order; only that role's bullets are re-ranked.
    case("reweight keeps role order even when a later role far out-scores the first",
         [r["company"] for r in reweighted["roles"]] == [r["company"] for r in me["roles"]])
    case("reweight re-ranks the high-overlap later role's bullets in place",
         [b["text"] for b in reweighted["roles"][1]["bullets"]]
         == [me["roles"][1]["bullets"][1]["text"], me["roles"][1]["bullets"][0]["text"]])
    before = [b["text"] for r in me["roles"] for b in r["bullets"]]
    after = [b["text"] for r in reweighted["roles"] for b in r["bullets"]]
    case("reweight reorders but never rewrites a word", sorted(before) == sorted(after))
    case("reweight leaves a zero-overlap role's bullets in me-model order",
         reweighted["roles"][0]["bullets"] == me["roles"][0]["bullets"])
    case("zero-overlap JD leaves the me-model order untouched",
         reweight_for_jd(me, "xyzzy plugh zork")["roles"] == me["roles"])

    # PR B — PDF gate: pure reading-order check over extracted pdftotext text.
    good_text = f'{me["name"]} {me["positioning"]} ' + " ".join(r["title"] for r in me["roles"]) \
        + " KEY ACCOUNTS SELECTED BUILDS" + (" " + " ".join(me["education"])
                                              if me.get("education") else "")
    case("PDF reading-order check passes on ordered text",
         pdf_reading_order_errors(good_text, me) == [])
    scrambled = f'Key accounts first. {me["name"]} {me["positioning"]} ' \
        + " ".join(r["title"] for r in me["roles"])
    case("PDF reading-order check catches scrambled roles",
         pdf_reading_order_errors(scrambled, me) != [])
    # The ATS cap asserted on the surface it protects: over-spaced labels fail.
    case("section-label extraction passes unbroken uppercase labels",
         section_label_extraction_errors("EXPERIENCE KEY ACCOUNTS SELECTED BUILDS EDUCATION",
                                         ["EXPERIENCE", "KEY ACCOUNTS", "SELECTED BUILDS",
                                          "EDUCATION"]) == [])
    case("section-label extraction catches the E D U C AT I O N failure",
         section_label_extraction_errors("E D U C AT I O N", ["EDUCATION"]) != [])

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

    # ---- YED-280: per-role key accounts + build description line. These test the SPEC
    # through the visible text (tags stripped — the pdftotext stand-in), not the markup.
    def load_fx(name):
        with open(os.path.join(os.path.dirname(FIXTURE), name), encoding="utf-8") as fh:
            text = fh.read()
        return json.loads(text), text

    def visible(h):
        h = re.sub(r"<head>.*?</head>", " ", h, flags=re.S)
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)).replace(" ,", ",")

    def in_order(text, seq):
        cursor = 0
        for s in seq:
            found = text.find(s, cursor)
            if found == -1:
                return False
            cursor = found + len(s)
        return True

    pr, pr_text = load_fx("resume-input-fixture-per-role.json")
    pr_html = build_resume_html(pr)
    case("per-role fixture validates and passes every locked rule and template guard",
         schema_errors(pr) == [] and check_content_rules(pr_html, pr_text) == []
         and check_reading_order(pr_html, pr) == [] and list_structure_errors(pr_html) == []
         and palette_errors(pr_html) == [] and letter_spacing_errors(pr_html) == [])

    # Spec 1 — per-role accounts render under the right role, in reading order.
    own_order = []
    for r in pr["roles"]:
        own_order += [r["title"], "Key accounts: " + ", ".join(account_names(r["key_accounts"]))]
    case("each role's Key accounts line renders under that role, before the next role",
         in_order(visible(pr_html), own_order + ["Selected builds"]))
    # Every "Key accounts" on the page is a per-role line: no top-level label or logo line.
    case("per-role mode suppresses the top-level Key accounts line",
         visible(pr_html).count("Key accounts") == len(pr["roles"])
         == visible(pr_html).count("Key accounts:"))
    swapped = json.loads(pr_text)
    swapped["roles"][0]["key_accounts"], swapped["roles"][1]["key_accounts"] = \
        swapped["roles"][1]["key_accounts"], swapped["roles"][0]["key_accounts"]
    swapped_html = build_resume_html(swapped)
    case("reading-order gate (HTML) fails accounts rendered under the wrong role",
         check_reading_order(swapped_html, pr) != [])
    case("reading-order gate (PDF text) fails accounts rendered under the wrong role",
         pdf_reading_order_errors(visible(pr_html), pr) == []
         and pdf_reading_order_errors(visible(swapped_html), pr) != [])
    case("schema refuses top-level and per-role key_accounts together",
         any("both top-level and per role" in e
             for e in schema_errors({**pr, "key_accounts": ["Quillmark Freight (fictional)"]})))
    no_accounts = json.loads(pr_text)
    for r in no_accounts["roles"]:
        del r["key_accounts"]
    case("schema refuses an input with no key accounts anywhere",
         any("key_accounts" in e for e in schema_errors(no_accounts)))
    empty_role_accounts = json.loads(pr_text)
    empty_role_accounts["roles"][0]["key_accounts"] = []
    case("schema refuses an empty per-role key_accounts list",
         any("roles[0].key_accounts" in e for e in schema_errors(empty_role_accounts)))

    # Spec 2 — no client name appears anywhere outside a Key accounts line.
    def names_outside_logo_lines(h, data):
        h = re.sub(r'<p class="(?:logo-line|role-accounts)">.*?</p>', " ", h, flags=re.S)
        text = visible(h).lower()
        return [a for a in all_key_accounts(data)
                if a.lower() in text or re.sub(r"\s*\([^)]*\)", "", a).strip().lower() in text]
    case("per-role fixture names no client outside its Key accounts lines",
         names_outside_logo_lines(pr_html, pr) == [])
    for where, mutate in (
            ("positioning", lambda d: d.update(
                positioning=d["positioning"] + " Expanded Quillmark Freight.")),
            ("a build description", lambda d: d["builds"][0].update(
                description="Quillmark Freight rollout tracker")),
            ("another role's bullet", lambda d: d["roles"][1]["bullets"][0].update(
                text=d["roles"][1]["bullets"][0]["text"] + " Won Quillmark Freight.")),
            ("a role title", lambda d: d["roles"][1].update(
                title="Quillmark Freight Account Executive"))):
        leaked = json.loads(pr_text)
        mutate(leaked)
        leaked_html = build_resume_html(leaked)
        case(f"rule 2 fails a per-role client name leaked into {where}",
             names_outside_logo_lines(leaked_html, leaked) != []
             and any(r.startswith("rule 2") for r in check_content_rules(leaked_html,
                                                                       json.dumps(leaked))))

    # Review fixes (YED-280): rule 2 normalises both sides and matches whole words.
    def rule2_trips(account, text, field="bullet"):
        d = json.loads(pr_text)
        d["roles"][0]["key_accounts"] = [account]
        if field == "bullet":
            d["roles"][1]["bullets"][0]["text"] = text
        else:
            d["positioning"] = d["positioning"] + " " + text
        return any(r.startswith("rule 2")
                   for r in check_content_rules(build_resume_html(d), json.dumps(d)))
    qf = "Quillmark Freight (fictional)"
    for label, account, text, field in (
            ("hyphenated", qf, "Grew Quillmark-Freight spend.", "bullet"),
            ("en-dash", qf, "Grew Quillmark–Freight spend.", "bullet"),
            ("no space", qf, "Grew QuillmarkFreight spend.", "bullet"),
            ("double space", qf, "Grew Quillmark  Freight spend.", "bullet"),
            ("NBSP", qf, "Grew Quillmark Freight spend.", "bullet"),
            ("newline", qf, "Grew Quillmark\nFreight.", "positioning"),
            ("UPPER case", qf, "Grew QUILLMARK FREIGHT.", "bullet"),
            ("possessive 's", qf, "Grew Quillmark Freight's spend.", "bullet"),
            ("curly apostrophe", "Macy's", "Grew Macy’s 2x.", "bullet"),
            ("tag split Quill<b></b>mark", qf, "Grew Quill<b></b>mark Freight.", "bullet"),
            ("&amp; entity", "Ben & Jerry's", "Grew Ben &amp; Jerry's.", "bullet"),
            ("Cyrillic look-alike а (explicit confusables map; NFKC alone does not fold it)",
             qf, "Grew Quillmаrk Freight.", "bullet"),
            ("one-word account, exact", "Target", "Expanded Target 3x.", "bullet"),
            ("one-word account, possessive", "Target", "Grew Target's spend.", "bullet")):
        case(f"rule 2 catches a client name written {label}", rule2_trips(account, text, field))
    for label, account, text, field in (
            ("'targets' (account Target)", "Target", "Beat targets by 20%.", "bullet"),
            ("'Targeted' (account Target)", "Target", "Targeted enterprise.", "positioning"),
            ("'inbox' (account Box)", "Box", "Built an inbox triage tool.", "bullet"),
            ("capitalised 'Inbox' (account Box)", "Box",
             "Inbox triage tool, built from scratch.", "bullet"),
            ("'Quillmark Freighters' (multi-word boundary)", qf,
             "Grew the Quillmark Freighters league.", "bullet"),
            ("'coaching' (account Coach)", "Coach", "Ran coaching for 4 reps.", "bullet"),
            ("'pipeline gap' (account Gap: one-word accounts must be capitalised)",
             "Gap", "Closed the pipeline gap.", "bullet")):
        case(f"rule 2 does not trip on {label}", not rule2_trips(account, text, field))
    case("NFKC alone leaves the Cyrillic а unfolded (why the confusables map exists)",
         unicodedata.normalize("NFKC", "а") != "a"
         and normalise_for_match("а") == "a")
    url_only = json.loads(pr_text)
    url_only["builds"][1]["links"].append("https://example.com/quillmark-freight")
    case("link URLs stay unscanned by rule 2 (documented limitation)",
         not any(r.startswith("rule 2") for r in check_content_rules(
             build_resume_html(url_only), json.dumps(url_only))))

    # Decision 2 (Alex, 2026-11-05): an account may carry aliases; rule 2 blocks every
    # alias with the same normalisation + boundaries; only `name` ever renders.
    aliased = pr["roles"][0]["key_accounts"][0]
    case("per-role fixture carries a {name, aliases[]} account",
         isinstance(aliased, dict) and "Quillmark" in aliased["aliases"])
    alias_leak = json.loads(pr_text)
    alias_leak["roles"][1]["bullets"][0]["text"] = "Grew Quillmark 3x across the book."
    case("rule 2 refuses an account's short-form alias in a bullet",
         any(r.startswith("rule 2") for r in check_content_rules(
             build_resume_html(alias_leak), json.dumps(alias_leak))))
    alias_upper = json.loads(pr_text)
    alias_upper["positioning"] += " Ran the QMF rollout."
    case("rule 2 refuses an alias in positioning (NBSP-adjacent)",
         any(r.startswith("rule 2") for r in check_content_rules(
             build_resume_html(alias_upper), json.dumps(alias_upper))))
    case("aliases are never rendered; only the account name appears",
         "QMF" not in visible(pr_html) and "Key accounts: Quillmark Freight (fictional), "
         in visible(pr_html))
    case("schema refuses an aliased account without aliases, or with an unknown key",
         any("aliases" in e for e in schema_errors(
             {**pr, "roles": [{**pr["roles"][0], "key_accounts": [{"name": "Solo Co"}]},
                              pr["roles"][1]]}))
         and any("unknown key" in e for e in schema_errors(
             {**pr, "roles": [{**pr["roles"][0], "key_accounts": [
                 {"name": "Solo Co", "aliases": ["Solo"], "tier": 1}]}, pr["roles"][1]]})))
    # Decision 4 (Alex, 2026-11-05): single-account roles are allowed (no minimum).
    case("schema accepts a role with a single key account",
         schema_errors({**pr, "roles": [{**pr["roles"][0], "key_accounts": ["Solo Co"]},
                                        pr["roles"][1]]}) == [])

    # Decision 1 (Alex, 2026-11-05): contact is required on real renders; the schema keeps
    # it optional (fixtures carry no personal data). Both paths run main() as a subprocess
    # and stop before Chrome, so this stays CI-safe.
    def main_output(data):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        fd, path = tempfile.mkstemp(suffix=".json", dir=OUTPUT_DIR, prefix=".selftest-")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        try:
            proc = subprocess.run([sys.executable, os.path.abspath(__file__), path],
                                  capture_output=True, text=True, timeout=60)
        finally:
            os.remove(path)
        return proc.returncode, proc.stdout + proc.stderr
    code, out_text = main_output({k: v for k, v in me.items() if k != "contact"})
    case("a real render without contact fails loudly, naming the field",
         code != 0 and "REFUSED" in out_text and "`contact`" in out_text)
    # With contact present, the run gets past the contact check (stopped here by a
    # deliberate rule-1 failure so no Chrome is needed).
    code, out_text = main_output({**me, "positioning": "Customer success leader."})
    case("a real render with contact passes the contact check",
         code != 0 and "rule 1" in out_text and "`contact`" not in out_text)

    # Review fix 5: every field is HTML-escaped; rule 2 matches the unescaped text.
    escaped = json.loads(pr_text)
    escaped["roles"][0]["bullets"][0]["text"] = "Ran R&D <script>x</script> pilots."
    escaped["builds"][0]["description"] = "A & B <i>build</i>"
    escaped_html = build_resume_html(escaped)
    case("bullet and description markup is escaped, never emitted raw",
         "R&amp;D &lt;script&gt;" in escaped_html and "<script>" not in escaped_html
         and "A &amp; B &lt;i&gt;build&lt;/i&gt;" in escaped_html
         and list_structure_errors(escaped_html) == [])

    # Review fix 4: an overflow says why, against the documented envelope.
    summary = fit_summary(pr)
    case("overflow message names the counts and the documented envelope",
         "2 roles, 4 bullets, 2 per-role Key accounts lines, 1 described builds" in summary
         and "6 roles / 13 bullets" in summary
         and "7 roles / 15 bullets" in fit_summary(me))

    # Spec 3 — a top-level-only legacy input renders byte-identical text to before YED-280.
    # The golden is the pre-YED-280 render of the untouched legacy fixture; the only
    # allowed difference is new CSS rules for classes the legacy markup never uses.
    with open(os.path.join(os.path.dirname(FIXTURE), "resume-legacy.golden.html"),
              encoding="utf-8") as fh:
        golden = fh.read()
    split = lambda h: (h.split("<style>")[1].split("</style>")[0], h.split("<body>", 1)[1])
    (gold_css, gold_body), (now_css, now_body) = split(golden), split(html)
    case("legacy input: <body> is byte-identical to the pre-YED-280 golden",
         now_body == gold_body)
    case("legacy input: every pre-YED-280 CSS line survives unchanged, in order",
         in_order(now_css, gold_css.splitlines(keepends=True)))
    as_builds = {k: v for k, v in me.items() if k != "proof_links"}
    as_builds["builds"] = [{"links": me["proof_links"]}]
    case("builds[] without a description renders byte-identical to legacy proof_links",
         build_resume_html(as_builds) == html and schema_errors(as_builds) == [])
    case("schema refuses proof_links and builds together, and neither",
         any("exactly one of proof_links / builds" in e
             for e in schema_errors({**me, "builds": [{"links": me["proof_links"]}]}))
         and any("exactly one of proof_links / builds" in e
                 for e in schema_errors({k: v for k, v in me.items() if k != "proof_links"})))
    case("contact and education are genuinely optional (absent still validates)",
         schema_errors({k: v for k, v in me.items() if k not in ("contact", "education")}) == [])

    # Spec 4 — a description renders before its links and respects the cap.
    desc = pr["builds"][0]["description"]
    pr_vis = visible(pr_html)
    case("a build description renders before its own links",
         in_order(pr_vis, ["Selected builds", desc, pr["builds"][0]["links"][0],
                           pr["builds"][1]["links"][0]]))
    at_cap = "A" * BUILD_DESCRIPTION_MAX
    over_cap = "A" * (BUILD_DESCRIPTION_MAX + 1)
    with_desc = lambda d: {**pr, "builds": [{"description": d, "links": pr["builds"][0]["links"]}]}
    case(f"a description exactly at the {BUILD_DESCRIPTION_MAX}-char cap validates and "
         "renders whole (no truncation, no ellipsis added)",
         schema_errors(with_desc(at_cap)) == []
         and at_cap in build_resume_html(with_desc(at_cap))
         and "…" not in build_resume_html(with_desc(at_cap)))
    case("a description one char over the cap is refused, not truncated",
         any("over the" in e and "cap" in e for e in schema_errors(with_desc(over_cap))))
    case("a multi-line description is refused (one line)",
         any("description" in e for e in schema_errors(with_desc("Line one\nLine two"))))
    case("PDF reading-order gate fails a description that never rendered",
         pdf_reading_order_errors(visible(pr_html.replace(desc, "")), pr) != [])

    # Spec 5 — the page count stays 1 with every new field at its max. Needs Chrome +
    # pdftotext; missing either is a loud skip, never a silent pass.
    mx, _ = load_fx("resume-input-fixture-max.json")
    case("max fixture fills every new field: per-role accounts on every role, every "
         "description at the cap",
         schema_errors(mx) == [] and all(r.get("key_accounts") for r in mx["roles"])
         and all(len(b.get("description", "")) == BUILD_DESCRIPTION_MAX for b in mx["builds"]))
    bin_ = chrome()
    if bin_ and shutil.which("pdftotext"):
        # Local-only (CI has no Chrome). A Chrome failure records a FAIL case instead of
        # exiting the selftest midway.
        fit_out = resolve_output_path(os.path.join(OUTPUT_DIR, ".selftest-max-fit.pdf"))
        try:
            render_pdf(bin_, build_resume_html(mx), fit_out)
            fit_errors = verify_pdf(fit_out, mx)
        except (SystemExit, OSError, subprocess.SubprocessError) as exc:
            fit_errors = [f"Chrome render failed: {exc}"]
        finally:
            if os.path.exists(fit_out):
                os.remove(fit_out)
        for err in fit_errors:
            print(f"    {err}")
        case("max fixture renders to exactly one page with pdftotext order + labels intact",
             fit_errors == [])
    else:
        print("WARN Chrome or pdftotext not found — max-length one-page render case SKIPPED")

    fails = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  {'ok  ' if ok else 'FAIL'} {n}")
    print(f"selftest: {len(checks) - len(fails)}/{len(checks)} render-resume cases pass")
    return 0 if not fails else 1


def render_pdf(bin_: str, html: str, out: str) -> None:
    """Chrome --print-to-pdf of `html` to `out` (already path-guarded by the caller)."""
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
    # Contact is required on every REAL render (Alex, 2026-11-05). The schema keeps it
    # optional so committed fixtures carry no personal data; --selftest and the fixture
    # contract test never reach main(), so they are exempt.
    if not me.get("contact"):
        print("REFUSED: resume-input has no `contact` — a real render needs the header "
              "contact line (the schema allows omitting it only for fixtures). Nothing rendered.")
        return 1
    jd_reweighted = False
    if a.mode == "posting-tailored":
        input_roles = [(r["title"], r["company"], r["dates"]) for r in me["roles"]]
        with open(a.jd, encoding="utf-8") as fh:
            me = reweight_for_jd(me, fh.read())
        # YED-330: the reading-order gates below check against the reweighted `me`, so
        # they can't see a role shuffle. Pin role order to the INPUT here (independent oracle).
        if [(r["title"], r["company"], r["dates"]) for r in me["roles"]] != input_roles:
            print("FAILED: posting-tailored reweighting moved roles; roles must keep the "
                  "input (me-model) order (YED-330). Nothing rendered.")
            return 1
        jd_reweighted = True
    html = build_resume_html(me, a.mode)

    with open(a.source, encoding="utf-8") as fh:
        json_text = fh.read()
    fails = check_content_rules(html, json_text) + check_reading_order(html, me) \
        + list_structure_errors(html) + palette_errors(html) + letter_spacing_errors(html) \
        + rewording_fidelity_errors(me)
    if a.mode == "posting-tailored":
        # Always-on `original` (review 2026-11-01): a reworded bullet cannot skip the
        # fidelity gate by omitting its original — every bullet must carry one here.
        fails += original_required_errors(me)
    if fails:
        print("Content rules failed — nothing rendered:")
        for f in fails:
            print(f"  - {f}")
        return 1
    if a.verify_links:
        link_fails = verify_proof_links(proof_links(me))
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
    # Render to a scratch name under OUTPUT_DIR; only a PDF that passes the gate ever lands
    # at --out, so a failed render can never overwrite a good resume (YED-280 review).
    fd, pending = tempfile.mkstemp(suffix=".pdf", dir=OUTPUT_DIR, prefix=".resume-pending-")
    os.close(fd)
    os.remove(pending)
    render_pdf(bin_, html, pending)

    # The PDF gate: exactly one page, pdftotext reading order intact — exit code gates the run.
    pdf_fails = verify_pdf(pending, me)
    if pdf_fails:
        failed = os.path.splitext(out)[0] + ".FAILED.pdf"
        os.replace(pending, failed)
        print("PDF gate failed:")
        for f in pdf_fails:
            print(f"  - {f}")
        print(f"  (the failed render is at {failed}; {out} was not written)")
        return 1
    os.replace(pending, out)

    print(json.dumps({"ok": True, "pdf": out, "mode": a.mode,
                      "jd_reweighted": jd_reweighted, "roles": len(me["roles"])}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
