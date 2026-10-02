#!/usr/bin/env python3
"""ats_pull.py — role-radar Step 1 as code: registry → ATS boards → projected, title-filtered TSV (YED-255).

Replaces the "5–6 companies per distillation subagent" fan-out, which spent model tokens running curl | jq.
Zero tokens: the raw boards (0.5–12 MB) never enter a model's context. What stays with the model (Step 3)
is judgment: reading each passing role's JD for mechanism (book vs own-the-funnel, IC vs manager, territory).

  ats_pull.py [--registry .claude/references/target-companies.md] [--only Anthropic,Runway]
              [--out roles.tsv] [--jd-dir DIR] [--floor N | --me-model PATH] [--any-location] [--selftest]

TSV columns: company vendor key title url location posted updated remote comp_text comp_verdict comp_figure comp_rule
  key      = {vendor}:{id} — the Step 2 natural key (Workable: shortcode)
  location = default filter NYC + Remote (US); a multi-location string passes if any part matches
  posted   = true posted date (Ashby/Lever/Workable); EMPTY for Greenhouse (updated_at is last-modified, not posted)
  comp_*   = comp_gate.py verdict WITHOUT the emerging-seller flag (a JD judgment): re-run comp_gate --emerging in
             Step 3 when the JD is pitched at an emerging seller.
--jd-dir writes one plain-text JD per passing row ({key}.txt, ':' → '_') for the Step 3 mechanism read.
stderr ends with the gap line Step 4 must report: "N companies returned 0 rows … · M errored … · K excluded … ·
comp gate: ON|OFF". Struck-through registry companies (~~Harvey~~) are skipped, not fetched.
Exit 0 on a completed run (gaps included), 2 on bad args, 3 when the registry can't be parsed.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
import comp_gate  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REGISTRY = os.path.join(ROOT, ".claude", "references", "target-companies.md")
UA = "Mozilla/5.0 (role-radar ats_pull)"
ENDPOINT = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{t}/jobs?content=true",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{t}?includeCompensation=true",
    "lever": "https://api.lever.co/v0/postings/{t}?mode=json",
    "workable": "https://apply.workable.com/api/v1/widget/accounts/{t}?details=true",
}
# Title filter — mirrors role-radar SKILL.md Step 1 (keep-list, then the drop-list WINS; no protected set).
KEEP = re.compile(r"Customer Success|\bCSM\b|Account Manager|Account Director|Account Executive|Engagement Manager|"
                  r"Sales Director|Sales Lead|Sales Leader|Enterprise Sales Director|VP,? Sales|Head of Sales|"
                  r"Growth Strategist|Growth Account|Growth AE|Scaled Growth|Named Account|Client Director|"
                  r"Client Partner|Relationship Manager", re.I)
DROP = re.compile(r"Engineer|Developer|Designer|Scientist|Researcher|Recruiter|Accountant|Controller|Counsel|"
                  r"Marketing Manager|Product Manager|Program Manager|Content|Brand|Demand Gen|"
                  r"Technical Account Manager", re.I)
COMP_LINE = re.compile(r"[^.\n]*\$\s*\d[\d,]*(?:\.\d+)?\s*[kK]?[^.\n]*")
# Location default = NYC + Remote (US) (SKILL Inputs). Multi-location strings pass when ANY part matches;
# an empty location passes (unknown is not a reject). --any-location turns the filter off.
LOC_US = re.compile(r"New York|\bNYC\b|Brooklyn|Manhattan|United States|North America|Americas", re.I)
LOC_US_CASE = re.compile(r"\bNY\b|\bUSA?\b")            # case-sensitive: never the word "us"
REMOTE = re.compile(r"Remote|Anywhere", re.I)
NON_US = re.compile(r"Europe|\bEU\b|EMEA|APAC|LATAM|\bUK\b|United Kingdom|London|Germany|Berlin|France|Paris|"
                    r"Spain|Ireland|Dublin|Netherlands|Amsterdam|Poland|Israel|India|Canada|Toronto|Mexico|Brazil|"
                    r"Australia|Japan|Tokyo|Singapore|Korea|Seoul", re.I)
# A JD sentence counts as comp only when it talks about pay, and not about customers' money.
COMP_KW = re.compile(r"salary|\bpay\b|compensation|\bOTE\b|on[- ]target|\bbase\b|earnings|commission", re.I)
NOT_COMP = re.compile(r"\bspend\b|revenue|\bARR\b|funding|raised|valuation|deal size|contract value|\bACV\b|budget", re.I)
COLS = ["company", "vendor", "key", "title", "url", "location", "posted", "updated", "remote",
        "comp_text", "comp_verdict", "comp_figure", "comp_rule"]


def parse_registry(md: str) -> list[dict]:
    """Rows of the '## Company → ATS registry' table: | Company | ATS | `token` |."""
    m = re.search(r"^## Company → ATS registry.*?$(.*?)(?=^##+ )", md, re.S | re.M)
    if not m:
        return []
    out = []
    for line in m.group(1).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[1].lower() in ENDPOINT:
            tok = re.search(r"`([^`]+)`", cells[2])
            name = re.sub(r"[*~]", "", cells[0]).strip()
            if tok:
                out.append({"company": name, "vendor": cells[1].lower(), "token": tok.group(1),
                            "excluded": "~~" in cells[0]})
    return out


def keep_location(loc: str) -> bool:
    """NYC + Remote (US). Multi-location strings pass when ANY part passes; remote passes unless it names a
    non-US region ("Remote - Germany" drops); empty = unknown, passes."""
    if not loc.strip():
        return True
    for part in re.split(r"[|;/]| or ", loc):
        if LOC_US.search(part) or LOC_US_CASE.search(part):
            return True
        if REMOTE.search(part) and not NON_US.search(part):
            return True
    return False


def keep_title(title: str) -> bool:
    return bool(KEEP.search(title)) and not DROP.search(title)


def _plain(s: str | None) -> str:
    s = s or ""
    for _ in range(3):          # Greenhouse double-escapes (&amp;mdash;) — decode until stable
        u = html.unescape(s)
        if u == s:
            break
        s = u
    s = re.sub(r"<(br|/p|/li|/h\d)[^>]*>", "\n", s, flags=re.I)
    return re.sub(r"[ \t]+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


def project(vendor: str, data) -> list[dict]:
    """Raw board JSON → [{id,title,url,location,posted,updated,remote,jd,comp_src}]."""
    rows = []
    if vendor == "greenhouse":
        for j in data.get("jobs", []):
            rows.append({"id": j.get("id"), "title": j.get("title", ""), "url": j.get("absolute_url", ""),
                         "location": (j.get("location") or {}).get("name", ""), "posted": "",
                         "updated": (j.get("updated_at") or "")[:10], "remote": "", "jd": _plain(j.get("content")),
                         "comp_src": ""})
    elif vendor == "ashby":
        for j in data.get("jobs", []):
            if not j.get("isListed", True):
                continue
            comp = (j.get("compensation") or {}).get("compensationTierSummary") or ""
            rows.append({"id": j.get("id"), "title": j.get("title", ""), "url": j.get("jobUrl", ""),
                         "location": j.get("location") or "", "posted": (j.get("publishedAt") or "")[:10],
                         "updated": "", "remote": str(bool(j.get("isRemote"))).lower(),
                         "jd": j.get("descriptionPlain") or _plain(j.get("descriptionHtml")), "comp_src": comp})
    elif vendor == "lever":
        for j in data:
            ms = j.get("createdAt")
            posted = time.strftime("%Y-%m-%d", time.gmtime(ms / 1000)) if isinstance(ms, (int, float)) else ""
            rng = j.get("salaryRange") or {}
            usd_year = rng.get("currency", "USD") == "USD" and rng.get("interval", "per-year-salary") == "per-year-salary"
            comp = f"${rng['min']:,} - ${rng['max']:,}" if usd_year and rng.get("min") and rng.get("max") else ""
            rows.append({"id": j.get("id"), "title": j.get("text", ""), "url": j.get("hostedUrl", ""),
                         "location": (j.get("categories") or {}).get("location", ""), "posted": posted,
                         "updated": "", "remote": "", "jd": j.get("descriptionPlain") or _plain(j.get("description")),
                         "comp_src": comp})
    elif vendor == "workable":
        for j in data.get("jobs", []):
            rows.append({"id": j.get("shortcode"), "title": j.get("title", ""), "url": j.get("shortlink", ""),
                         "location": f"{j.get('city') or ''} {j.get('country') or ''}".strip(),
                         "posted": j.get("published_on") or "", "updated": "",
                         "remote": str(bool(j.get("telecommuting"))).lower(), "jd": _plain(j.get("description")),
                         "comp_src": ""})
    return rows


def comp_text(row: dict) -> str:
    """Structured comp field first; else the first JD sentence carrying a $ amount that parses as comp."""
    if row["comp_src"]:
        return row["comp_src"]
    for m in COMP_LINE.finditer(row["jd"]):
        sent = m.group(0)
        if COMP_KW.search(sent) and not NOT_COMP.search(sent) and comp_gate.parse_comp(sent):
            return m.group(0).strip()[:240]
    return ""


def fetch(vendor: str, token: str) -> object:
    url = ENDPOINT[vendor].format(t=token)
    last = None
    for timeout in (30, 60):   # retry once with a longer timeout (SKILL Failure modes)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001 — every failure is reported by name, never swallowed
            last = e
    raise RuntimeError(f"{type(last).__name__}: {last}")


def run(entries: list[dict], floor: int | None, jd_dir: str | None,
        any_location: bool = False) -> tuple[list[dict], list[str], list[str], int]:
    out, empty, errored, scanned = [], [], [], 0
    for e in entries:
        if e["excluded"]:      # struck through in the registry (e.g. ~~Harvey~~): every role auto-rejects on company fit
            continue
        try:
            raw = project(e["vendor"], fetch(e["vendor"], e["token"]))
        except Exception as err:  # noqa: BLE001
            errored.append(f"{e['company']} ({e['vendor']}/{e['token']}: {err})")
            continue
        scanned += len(raw)
        if not raw:
            empty.append(e["company"])
        for r in raw:
            if not keep_title(r["title"]) or not (any_location or keep_location(r["location"])):
                continue
            key = f"{e['vendor']}:{r['id']}"
            ct = comp_text(r)
            g = comp_gate.gate(comp_gate.parse_comp(ct), floor) if floor else {"verdict": "", "figure": "", "rules": []}
            out.append({"company": e["company"], "vendor": e["vendor"], "key": key, "title": r["title"],
                        "url": r["url"], "location": r["location"], "posted": r["posted"], "updated": r["updated"],
                        "remote": r["remote"], "comp_text": ct, "comp_verdict": g["verdict"],
                        "comp_figure": g["figure"] if g["figure"] is not None else "", "comp_rule": "; ".join(g["rules"])})
            if jd_dir:
                with open(os.path.join(jd_dir, key.replace(":", "_") + ".txt"), "w", encoding="utf-8") as fh:
                    fh.write(f"{r['title']} @ {e['company']}\n{r['url']}\n\n{r['jd']}\n")
    return out, empty, errored, scanned


def _tsv(v) -> str:
    return str(v).replace("\t", " ").replace("\n", " ")


def selftest() -> int:
    ok, n = 0, 0

    def check(name, cond):
        nonlocal ok, n
        n += 1; ok += bool(cond)
        print(f"  {'✓' if cond else '✗'} {name}")

    reg = parse_registry("## Company → ATS registry (x)\n\n| Company | ATS | Token / board |\n|---|---|---|\n"
                         "| Anthropic | greenhouse | `anthropic` |\n| ***Higgsfield AI*** | ashby | `higgsfieldai` |\n"
                         "| ~~Harvey~~ | ashby | `harvey` |\n| Hugging Face | workable | `huggingface` |\n\n### Next\n"
                         "| Flourish | ashby | `Flourish` |\n")
    check("registry: 4 rows from the registry section only", len(reg) == 4)
    check("registry: markdown stripped from names", reg[1]["company"] == "Higgsfield AI")
    check("registry: struck-through company flagged excluded", reg[2]["excluded"] and not reg[0]["excluded"])
    for t, want in [("Enterprise Sales Director", True), ("Engagement Manager, DaaS", True),
                    ("Strategic Account Executive", True), ("Growth Marketing Manager", False),
                    ("Senior Backend Engineer (Growth)", False), ("Technical Account Manager", False),
                    ("Solutions Engineer", False), ("Customer Success Manager, Enterprise", True)]:
        check(f"title filter: {t!r} → {'keep' if want else 'drop'}", keep_title(t) == want)
    gh = project("greenhouse", {"jobs": [{"id": 7, "title": "AE", "absolute_url": "u", "location": {"name": "NYC"},
                                           "updated_at": "2026-09-30T00:00:00Z", "content": "&lt;p&gt;Pay $180K – $220K OTE&lt;/p&gt;"}]})
    check("greenhouse: posted EMPTY, updated kept", gh[0]["posted"] == "" and gh[0]["updated"] == "2026-09-30")
    check("greenhouse: comp found in escaped-HTML JD", comp_gate.parse_comp(comp_text(gh[0])).get("high") == 220_000)
    lv = project("lever", [{"id": "a", "text": "AM", "hostedUrl": "u", "createdAt": 1790000000000, "categories": {}}])
    for loc, want in [("San Francisco, CA | New York City, NY", True), ("Remote - US", True), ("London, UK", False),
                      ("", True), ("Berlin", False), ("Remote - Germany", False), ("Remote, EU", False),
                      ("Remote", True), ("Join us in Austin", False)]:
        check(f"location filter: {loc!r} → {'keep' if want else 'drop'}", keep_location(loc) == want)
    gh2 = project("greenhouse", {"jobs": [{"id": 8, "title": "CSM", "absolute_url": "u", "location": {"name": "NYC"},
                  "content": "&lt;p&gt;Annual Salary: $151,840 &amp;mdash; $200,000 USD&lt;/p&gt;"}]})
    c2 = comp_gate.parse_comp(comp_text(gh2[0]))
    check("greenhouse: double-escaped &mdash; range parses as a range, labelled base", c2.get("low") == 151_840 and
          c2.get("high") == 200_000 and c2.get("label") == "base")
    fp = project("greenhouse", {"jobs": [{"id": 9, "title": "CSM", "absolute_url": "u", "location": {"name": "NYC"},
                 "content": "Manage accounts ranging from ~$100K to $10M+ in annual spend. Our Series C raised $250M."}]})
    check("comp: customer spend / funding amounts are not pay", comp_text(fp[0]) == "")
    lv2 = project("lever", [{"id": "b", "text": "AM", "hostedUrl": "u", "categories": {},
                             "salaryRange": {"currency": "GBP", "interval": "per-year-salary", "min": 90000, "max": 120000}}])
    check("lever: non-USD salaryRange is not passed off as $", lv2[0]["comp_src"] == "")
    check("lever: createdAt epoch-ms → ISO date", re.fullmatch(r"\d{4}-\d{2}-\d{2}", lv[0]["posted"]) is not None)
    wk = project("workable", {"jobs": [{"shortcode": "ABC123", "title": "AM", "shortlink": "u", "published_on": "2026-09-29"}]})
    check("workable: shortcode is the id", wk[0]["id"] == "ABC123")
    ab = project("ashby", {"jobs": [{"id": "x", "title": "AE", "isListed": False}, {"id": "y", "title": "AE", "jobUrl": "u",
                                     "publishedAt": "2026-09-28T10:00:00Z", "compensation": {"compensationTierSummary": "$200K – $240K • Offers Commission"}}]})
    check("ashby: unlisted jobs skipped, structured comp used", len(ab) == 1 and comp_text(ab[0]).startswith("$200K"))
    print(f"selftest: {ok}/{n} ats_pull cases pass")
    return 0 if ok == n else 1


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--registry", default=REGISTRY); ap.add_argument("--only")
    ap.add_argument("--out"); ap.add_argument("--jd-dir"); ap.add_argument("--floor", type=int)
    ap.add_argument("--me-model", help="path to me-model.md for the OTE floor (gitignored; absent in worktrees)")
    ap.add_argument("--any-location", action="store_true"); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    try:
        entries = parse_registry(open(a.registry, encoding="utf-8").read())
    except OSError as e:
        print(f"ats_pull: registry unreadable: {e}", file=sys.stderr); return 3
    if not entries:
        print(f"ats_pull: no registry rows parsed from {a.registry} — heading or table shape drifted", file=sys.stderr)
        return 3
    if a.only:
        want = {s.strip().lower() for s in a.only.split(",")}
        missing = want - {e["company"].lower() for e in entries}
        if missing:
            print(f"ats_pull: --only names not in the registry: {', '.join(sorted(missing))}", file=sys.stderr)
        entries = [e for e in entries if e["company"].lower() in want]
        if not entries:
            return 2
    floor = a.floor
    if floor is None:
        try:
            floor = comp_gate.read_floor(a.me_model) if a.me_model else comp_gate.read_floor()
        except (OSError, ValueError) as e:
            print(f"ats_pull: no OTE floor ({e}); comp columns left blank", file=sys.stderr)
    if a.jd_dir:
        os.makedirs(a.jd_dir, exist_ok=True)
    rows, empty, errored, scanned = run(entries, floor, a.jd_dir, a.any_location)
    lines = ["\t".join(COLS)] + ["\t".join(_tsv(r[c]) for c in COLS) for r in rows]
    if a.out:
        try:
            open(a.out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        except OSError as e:
            print(f"ats_pull: cannot write --out {a.out}: {e}", file=sys.stderr); return 3
    else:
        print("\n".join(lines))
    print(f"ats_pull: {len(entries)} boards · {scanned} roles scanned · {len(rows)} passed the title filter",
          file=sys.stderr)
    excluded = [e["company"] for e in entries if e["excluded"]]
    print(f"ats_pull: {len(empty)} companies returned 0 rows: {', '.join(empty) or '—'} · "
          f"{len(errored)} errored: {'; '.join(errored) or '—'} · {len(excluded)} excluded (struck through): "
          f"{', '.join(excluded) or '—'} · comp gate: {'ON' if floor else 'OFF — no floor, comp_verdict blank'}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
