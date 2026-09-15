#!/usr/bin/env python3
"""inbox_boundary — the /scan-inbox scan boundary as a MECHANISM, not a convention (YED-161, ADR-7 D3).

Before this file, `inbox-denylist.md` described itself as "the primary PII/SEC control" and nothing
executed it. This module is the single parser + matcher for BOTH boundary files, and the runtime gate
ADR-7 carried as prose: the first whole-inbox (Stage A) scan refuses to run while the denylist is DRAFT.

  gate    python3 .claude/scripts/inbox_boundary.py gate --stage discover|extract
            exit 0 = boundary satisfied · 2 = a boundary file is missing · 3 = gate closed
            (discover: denylist not `v1 ACCEPTED`; extract: allowlist has no curated senders)
  filter  echo '<json array of thread metadata>' | python3 .claude/scripts/inbox_boundary.py filter --stage A|B
            Stage A keeps METADATA ONLY (never snippet/body) for non-denylisted threads.
            Stage B keeps only threads that are allowlisted AND not denylisted (denylist wins).
            Output: {"kept": [...], "skipped": [{"thread_id", "reason"}], "counts": {...}, "status": ...}
            A denylisted sender's address/domain NEVER appears in the output — only a reason class.
  check   python3 .claude/scripts/inbox_boundary.py check --sender a@b.com [--labels 'Me/Health,Inbox']
  report  python3 .claude/scripts/inbox_boundary.py report          (what the live files parse to)
  --selftest                                                        (fixture inbox; pins every rule)

Thread metadata shape (what the parent normalizes from Gmail `search_threads`):
  {"thread_id", "message_id", "from": "Name <addr@dom>" | "addr@dom", "subject", "date",
   "labels": ["Content/Newsletters", ...], "has_list_unsubscribe": bool}
Gmail may return label IDs; the caller maps them to names via `list_labels` first (v1 matches on names).

Matching rules (from inbox-denylist.md / inbox-allowlist.md, now executable):
  * sender  = exact address, case-insensitive
  * domain  = part after @, case-insensitive, subdomains included; `*` globs allowed
  * label   = the thread carries the label or any child of it (`Me` matches `Me/Health/Gym`)
  * order   = sender → domain → label, BEFORE any body is read; a match at any level → skip entirely
  * denylist wins over allowlist on conflict (ramp.com receipt vs ramp.com careers → skip in v1)
"""
from __future__ import annotations
import argparse, fnmatch, json, os, re, sys
from dataclasses import dataclass, field

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DENYLIST_PATH = os.path.join(ROOT, ".claude", "references", "inbox-denylist.md")
ALLOWLIST_PATH = os.path.join(ROOT, ".claude", "references", "inbox-allowlist.md")
ALLOWED_LABELS_DEFAULT = ("Content/Newsletters", "Pipeline/signal-source")   # inbox-allowlist.md "Matching rules"
RETAIN_STAGE_A = ("thread_id", "message_id", "subject", "date", "labels", "has_list_unsubscribe")  # + sender/domain; NEVER snippet/body

_SECTION_RE = re.compile(r"^##\s+(.*?)\s*$", re.M)
_TOKEN_RE = re.compile(r"`([^`\n]+)`")
_STATUS_RE = re.compile(r"\*\*Status:\s*v(\d+)\s+(DRAFT|ACCEPTED|SCAFFOLD)", re.I)
_ADDR_RE = re.compile(r"<([^<>\s]+@[^<>\s]+)>|([^\s<>\"']+@[^\s<>\"']+)")


@dataclass
class Denylist:
    domains: set = field(default_factory=set)
    globs: list = field(default_factory=list)
    senders: set = field(default_factory=set)
    labels: list = field(default_factory=list)
    status: str = "MISSING"
    version: int = 0
    ignored: list = field(default_factory=list)   # bare words like `docusign` — too broad to match on
    prose_skipped: list = field(default_factory=list)  # backticked tokens found in prose/blockquotes — never entries
    path: str = DENYLIST_PATH

    @property
    def accepted(self) -> bool:
        return self.status.upper() == "ACCEPTED"


@dataclass
class Allowlist:
    domains: set = field(default_factory=set)
    senders: set = field(default_factory=set)
    labels: set = field(default_factory=lambda: set(ALLOWED_LABELS_DEFAULT))
    status: str = "MISSING"
    path: str = ALLOWLIST_PATH

    @property
    def curated(self) -> bool:
        return bool(self.domains or self.senders)


_ITEM_RE = re.compile(r"^\s*(?:[-*\u2022]|\d+\.)\s+")


def _entry_lines(body: str) -> tuple[list[str], list[str]]:
    """Split a section body into (entry lines, prose lines). An ENTRY is a markdown list item plus its
    indented continuation lines. Blockquotes (`>`), headings, and bare paragraphs are PROSE — a question
    or a guidance sentence must never become an executed rule (judge finding 2026-09-13)."""
    entries, prose, in_item = [], [], False
    for line in body.splitlines():
        if line.lstrip().startswith(">"):
            in_item = False; prose.append(line); continue
        if _ITEM_RE.match(line):
            in_item = True; entries.append(line); continue
        if in_item and line.startswith((" ", "\t")) and line.strip():
            entries.append(line); continue                       # wrapped continuation of the item
        in_item = False
        if line.strip():
            prose.append(line)
    return entries, prose


def _sections(text: str) -> list[tuple[str, str]]:
    parts = _SECTION_RE.split(text)
    out = [("_head", parts[0])]
    for i in range(1, len(parts) - 1, 2):
        out.append((parts[i].lower(), parts[i + 1]))
    return out


def _shape(tok: str) -> tuple[str, str] | None:
    t = tok.strip().strip(",;")
    if not t or t.startswith("#"):
        return None
    if t.lower().startswith("label:"):
        return ("label", t[6:].strip())
    if "@" in t:
        local, _, dom = t.lower().lstrip("@").partition("@")
        if not local or "." not in dom:
            return ("word", t)                                   # `product@` — a guidance prefix, not an address
        return ("sender", f"{local}@{dom}")
    if "*" in t:
        return ("glob", t.lower())
    if "." in t and " " not in t:
        return ("domain", t.lower().lstrip("@").rstrip("."))
    return ("word", t)


def parse_denylist_text(text: str, path: str = DENYLIST_PATH) -> Denylist:
    d = Denylist(path=path)
    m = _STATUS_RE.search(text)
    if m:
        d.version, d.status = int(m.group(1)), m.group(2).upper()
    else:
        d.status = "UNKNOWN"
    for title, body in _sections(text):
        entry_lines, prose_lines = _entry_lines(body)
        if any(k in title for k in ("denylisted gmail labels", "denylisted domains", "denylisted senders", "spam / noise")):
            d.prose_skipped += [t.strip() for t in _TOKEN_RE.findall("\n".join(prose_lines))]
        entries = "\n".join(entry_lines)
        if "denylisted gmail labels" in title:
            for tok in _TOKEN_RE.findall(entries):
                t = tok.strip()
                if t and not t.startswith("#"):
                    d.labels.append(t)                                 # every LIST-ITEM token here is a label path
        elif "denylisted domains" in title or "denylisted senders" in title or "spam / noise" in title:
            for tok in _TOKEN_RE.findall(entries):
                s = _shape(tok)
                if not s:
                    continue
                kind, v = s
                if kind == "sender":
                    d.senders.add(v)
                elif kind == "domain":
                    d.domains.add(v)
                elif kind == "glob":
                    d.globs.append(v)
                else:
                    d.ignored.append(v)                               # `docusign` — bare word, not matched
        # every other section (rules, always-allowed markers, review log) is documentation, not entries
    return d


def load_denylist(path: str = DENYLIST_PATH) -> Denylist:
    if not os.path.exists(path):
        return Denylist(path=path, status="MISSING")
    return parse_denylist_text(open(path, encoding="utf-8").read(), path)


def parse_allowlist_text(text: str, path: str = ALLOWLIST_PATH) -> Allowlist:
    a = Allowlist(path=path)
    m = _STATUS_RE.search(text)
    a.status = m.group(2).upper() if m else "UNKNOWN"
    for title, body in _sections(text):
        if "allowed senders" in title:
            entry_lines, _ = _entry_lines(body)
            for tok in _TOKEN_RE.findall("\n".join(entry_lines)):
                s = _shape(tok)
                if not s:
                    continue
                if s[0] == "sender":
                    a.senders.add(s[1])
                elif s[0] == "domain":
                    a.domains.add(s[1])
                elif s[0] == "label":
                    a.labels.add(s[1])
        elif "matching rules" in title:
            for tok in _TOKEN_RE.findall(body):
                t = tok.strip()
                if t.lower().startswith("label:"):
                    t = t[6:].strip()                                  # `label:Content/Newsletters` → the label path
                if "/" in t and "." not in t and " " not in t:
                    a.labels.add(t)                                    # e.g. `Content/Newsletters`, `Pipeline/signal-source`
    return a


def load_allowlist(path: str = ALLOWLIST_PATH) -> Allowlist:
    if not os.path.exists(path):
        return Allowlist(path=path, status="MISSING")
    return parse_allowlist_text(open(path, encoding="utf-8").read(), path)


# ---------------------------------------------------------------------------
# matching
# ---------------------------------------------------------------------------
def parse_from(value: str) -> tuple[str, str]:
    """'Name <a@b.com>' or 'a@b.com' → (address, domain), lower-cased."""
    if not value:
        return "", ""
    m = _ADDR_RE.search(value)
    addr = (m.group(1) or m.group(2)) if m else value
    addr = addr.strip().lower()
    return addr, (addr.split("@", 1)[1] if "@" in addr else "")


def domain_matches(host: str, domains: set, globs: list) -> bool:
    host = (host or "").lower()
    if not host:
        return False
    if host in domains or any(host.endswith("." + d) for d in domains):
        return True
    return any(fnmatch.fnmatch(host, g) for g in globs)


def label_matches(labels, deny_labels) -> str | None:
    for l in labels or []:
        ll = str(l).strip().lower()
        for d in deny_labels:
            dl = d.lower()
            if ll == dl or ll.startswith(dl + "/"):
                return d
    return None


def classify(thread: dict, deny: Denylist, allow: Allowlist | None, stage: str) -> dict:
    """Decide one thread. Never echoes a denylisted address/domain back — reason classes only."""
    sender, domain = parse_from(thread.get("from") or thread.get("sender") or "")
    labels = thread.get("labels") or []
    if sender and sender in deny.senders:
        return {"skip": True, "reason": "deny:sender"}
    if domain_matches(domain, deny.domains, deny.globs):
        return {"skip": True, "reason": "deny:domain"}
    if label_matches(labels, deny.labels):
        return {"skip": True, "reason": "deny:label"}
    if stage == "A":
        kept = {k: thread[k] for k in RETAIN_STAGE_A if k in thread}
        kept["sender"], kept["domain"] = sender, domain
        return {"skip": False, "reason": None, "thread": kept}          # snippet/body deliberately dropped
    # Stage B — allowlist-only bodies
    allow = allow or Allowlist()
    allowed = (sender in allow.senders) or domain_matches(domain, allow.domains, []) or \
              label_matches(labels, list(allow.labels)) is not None
    if not allowed:
        return {"skip": True, "reason": "not-allowlisted"}
    kept = dict(thread); kept["sender"], kept["domain"] = sender, domain; kept["body_allowed"] = True
    return {"skip": False, "reason": None, "thread": kept}


def filter_threads(threads: list[dict], stage: str, deny: Denylist, allow: Allowlist | None) -> dict:
    kept, skipped, counts = [], [], {"input": len(threads), "kept": 0}
    for t in threads:
        r = classify(t, deny, allow, stage)
        if r["skip"]:
            skipped.append({"thread_id": t.get("thread_id"), "reason": r["reason"]})
            counts[r["reason"]] = counts.get(r["reason"], 0) + 1
        else:
            kept.append(r["thread"]); counts["kept"] += 1
    counts["skipped"] = len(skipped)
    return {"stage": stage, "denylist_status": f"v{deny.version} {deny.status}", "kept": kept,
            "skipped": skipped, "counts": counts}


def gate(stage: str, deny: Denylist, allow: Allowlist) -> tuple[int, str]:
    if deny.status == "MISSING":
        return 2, f"REFUSE: denylist missing at {deny.path} — the scan boundary does not exist"
    if stage == "discover" and not deny.accepted:
        return 3, (f"GATE CLOSED: inbox-denylist.md is v{deny.version} {deny.status} — the first whole-inbox "
                   f"scan runs only after Alex's review flips it to `v{deny.version} ACCEPTED` (ADR-7 D3). "
                   f"Stage B (allowlist-only) is unaffected.")
    if stage == "extract":
        if allow.status == "MISSING":
            return 2, f"REFUSE: allowlist missing at {allow.path}"
        if not allow.curated:
            return 3, "GATE CLOSED: allowlist has no curated senders/domains — run `discover` first"
    return 0, json.dumps({"stage": stage, "denylist": f"v{deny.version} {deny.status}",
                          "deny": {"domains": len(deny.domains), "globs": len(deny.globs), "senders": len(deny.senders),
                                   "labels": len(deny.labels), "ignored_bare_words": deny.ignored},
                          "allow": {"domains": len(allow.domains), "senders": len(allow.senders), "labels": sorted(allow.labels)}})


# ---------------------------------------------------------------------------
# self-test — fixture inbox + synthetic boundary files that mirror the real format
# ---------------------------------------------------------------------------
_DENY_FIXTURE = """# Inbox denylist — test
**Status: v1 DRAFT — requires Alex's review**
## Matching rules
1. `From`, the sender **domain**, labels — ignore me `not-an-entry.example`
## Denylisted domains — institutional (safe defaults, seeded)
- **Financial:** `bank.example`, `ramp.com` *(also a target)*, `docusign` *(bare)*
- **Health:** `myhealth*`, `*insurance*`
- **Gov:** `*.gov`
## Denylisted Gmail labels (POPULATED)
- `Me` and every child: `Me/Health`, `Me/Personal Finance`
- `Job Hunting`

> Confirm: is any `Companies/*` label actually personal (e.g. `Companies/Ramp`, `Companies/Mercury`)? Flag any to move here.
## Denylisted senders — specific addresses
- `hello@alerts.pharmacy.example` — (a pharmacy)
- `# (Alex to add personal contacts)`
## Spam / noise senders
- `blast@coldoutbound.io`
## Review log
- `2026-09-08` seeded
"""
_ALLOW_FIXTURE = """# Inbox allowlist
**Status: v1 SCAFFOLD**
## Matching rules
- Match on domain, sender, or label (`Content/Newsletters`, `Pipeline/signal-source`); the Gmail query form is `label:Content/Newsletters`.
## Allowed senders / domains

*(A few seeds below — confirm/prune. Prefer `product@` / `updates@` / `changelog@` style senders.)*

- `ship@info.vercel.com` — Vercel
- `lancedb.com` — LanceDB
"""
_INBOX_FIXTURE = [
    {"thread_id": "t1", "from": "Bank Alerts <no-reply@alerts.bank.example>", "subject": "Your statement", "labels": ["Inbox"], "snippet": "balance $4,210 acct ending 5531"},
    {"thread_id": "t2", "from": "hello@alerts.pharmacy.example", "subject": "Refill", "labels": ["Inbox"]},
    {"thread_id": "t3", "from": "Dr Office <care@somecare.com>", "subject": "Visit", "labels": ["Me/Health/Dental"]},
    {"thread_id": "t4", "from": "recruiter@bigco.com", "subject": "Application", "labels": ["Job Hunting/Rejection"]},
    {"thread_id": "t5", "from": "portal@myhealthplus.com", "subject": "Results", "labels": ["Inbox"]},
    {"thread_id": "t6", "from": "careers@ramp.com", "subject": "Enterprise AM role", "labels": ["Inbox"]},
    {"thread_id": "t7", "from": "Techpresso <hi@techpresso.co>", "subject": "Mistral raises", "labels": ["Content/Newsletters"], "snippet": "body text"},
    {"thread_id": "t8", "from": "ship@info.vercel.com", "subject": "Ship week", "labels": ["Inbox"]},
    {"thread_id": "t9", "from": "chanchan@lancedb.com", "subject": "LanceDB digest", "labels": ["Inbox"]},
    {"thread_id": "t10", "from": "product@unknownstartup.ai", "subject": "Changelog", "labels": ["Inbox"]},
    {"thread_id": "t11", "from": "mom@gmail.com", "subject": "dinner sunday", "labels": ["Inbox"]},
    {"thread_id": "t12", "from": "notice@state.ny.gov", "subject": "Notice", "labels": ["Inbox"]},
    {"thread_id": "t13", "from": "blast@coldoutbound.io", "subject": "Quick question", "labels": ["Inbox"]},
]


def selftest() -> bool:
    deny = parse_denylist_text(_DENY_FIXTURE, "fixture"); allow = parse_allowlist_text(_ALLOW_FIXTURE, "fixture")
    checks: list[tuple[str, bool]] = []
    ck = lambda name, cond: checks.append((name, bool(cond)))
    ck("parser: status v1 DRAFT detected", deny.version == 1 and deny.status == "DRAFT" and not deny.accepted)
    ck("parser: domains/globs/senders/labels parsed; bare word ignored",
       deny.domains == {"bank.example", "ramp.com"} and set(deny.globs) == {"myhealth*", "*insurance*", "*.gov"}
       and deny.senders == {"hello@alerts.pharmacy.example", "blast@coldoutbound.io"} and deny.labels == ["Me", "Me/Health", "Me/Personal Finance", "Job Hunting"]
       and deny.ignored == ["docusign"])
    ck("parser: rules/review-log sections contribute NO entries", "not-an-entry.example" not in deny.domains and "2026-09-08" not in deny.senders)
    ck("parser: allowlist senders/domains + default labels", allow.senders == {"ship@info.vercel.com"} and allow.domains == {"lancedb.com"} and {"Content/Newsletters", "Pipeline/signal-source"} <= allow.labels)
    ck("parser: `label:` prefix stripped (no raw query tokens as labels)", not any(l.lower().startswith("label:") for l in allow.labels))
    ck("parser: a blockquote QUESTION never becomes an entry (Companies/Ramp not denylisted)",
       not any(l.startswith("Companies/") for l in deny.labels) and "Companies/Ramp" in deny.prose_skipped)
    ck("parser: guidance prefixes (`product@`, `updates@`) are not senders", not any(x in allow.senders for x in ("product@", "updates@", "changelog@")) and "@" not in "".join(s for s in allow.senders if s.endswith("@")))
    ck("check: an unrelated sender carrying Companies/Ramp is NOT skipped",
       classify({"from": "x@unrelated.ai", "labels": ["Companies/Ramp"]}, deny, allow, "A")["skip"] is False)
    a = filter_threads(_INBOX_FIXTURE, "A", deny, allow)
    kept_ids = {t["thread_id"] for t in a["kept"]}
    ck("Stage A: zero denylisted rows retained", kept_ids == {"t7", "t8", "t9", "t10", "t11"})
    ck("Stage A: subdomain (alerts.bank.example) skipped as deny:domain", any(s["thread_id"] == "t1" and s["reason"] == "deny:domain" for s in a["skipped"]))
    ck("Stage A: exact sender + spam-section sender skipped", {s["reason"] for s in a["skipped"] if s["thread_id"] in ("t2", "t13")} == {"deny:sender"})
    ck("Stage A: label child (Me/Health/Dental, Job Hunting/Rejection) skipped as deny:label", {s["reason"] for s in a["skipped"] if s["thread_id"] in ("t3", "t4")} == {"deny:label"})
    ck("Stage A: globs (myhealth*, *.gov) skipped", {s["reason"] for s in a["skipped"] if s["thread_id"] in ("t5", "t12")} == {"deny:domain"})
    ck("Stage A: denylist wins over a target-company domain (careers@ramp.com skipped)", any(s["thread_id"] == "t6" for s in a["skipped"]))
    ck("Stage A: counts in the report", a["counts"]["input"] == 13 and a["counts"]["kept"] == 5 and a["counts"]["skipped"] == 8 and a["counts"]["deny:domain"] == 4)
    out = json.dumps(a)
    ck("Stage A: NO denylisted address/domain in the output", not any(x in out for x in ("bank.example", "pharmacy.example", "myhealthplus", "ramp.com", "coldoutbound", "state.ny.gov", "somecare", "bigco")))
    ck("Stage A: snippet/body NEVER retained", "snippet" not in out and "balance" not in out and "body text" not in out)
    b = filter_threads(_INBOX_FIXTURE, "B", deny, allow)
    ck("Stage B: only allowlisted, non-denylisted threads keep bodies", {t["thread_id"] for t in b["kept"]} == {"t7", "t8", "t9"} and all(t.get("body_allowed") for t in b["kept"]))
    ck("Stage B: unknown startup + personal sender = not-allowlisted (not deny)", {s["reason"] for s in b["skipped"] if s["thread_id"] in ("t10", "t11")} == {"not-allowlisted"})
    ck("Stage B: newsletter label allows bodies", any(t["thread_id"] == "t7" for t in b["kept"]))
    code, _ = gate("discover", deny, allow); ck("gate: discover CLOSED while DRAFT (exit 3)", code == 3)
    acc = parse_denylist_text(_DENY_FIXTURE.replace("v1 DRAFT", "v1 ACCEPTED"), "fixture")
    code, _ = gate("discover", acc, allow); ck("gate: discover OPEN once ACCEPTED", code == 0)
    code, _ = gate("extract", deny, allow); ck("gate: extract runs on a curated allowlist even while denylist is DRAFT", code == 0)
    code, _ = gate("extract", deny, Allowlist(status="SCAFFOLD")); ck("gate: extract CLOSED with an uncurated allowlist (exit 3)", code == 3)
    code, _ = gate("discover", Denylist(status="MISSING"), allow); ck("gate: missing denylist REFUSED (exit 2)", code == 2)
    ck("parse_from handles 'Name <addr>' and bare", parse_from("X Y <A@B.Com>") == ("a@b.com", "b.com") and parse_from("a@b.com") == ("a@b.com", "b.com"))
    live = load_denylist(); live_allow = load_allowlist()
    ck(f"live denylist parses (v{live.version} {live.status}: {len(live.domains)} domains, {len(live.globs)} globs, {len(live.senders)} senders, {len(live.labels)} labels; {len(live.prose_skipped)} prose tokens skipped)",
       live.status in ("DRAFT", "ACCEPTED") and len(live.domains) >= 10 and len(live.labels) >= 5 and len(live.senders) >= 2)
    # Companies/* labels are allowed only as the specific paths Alex reviewed (2026-09-15) — a new
    # Companies/* denylist entry must be reviewed and added here, never slip in silently.
    reviewed_companies = {"Companies/New York Life", "Companies/Macbook", "Companies/Square Space",
                          "Companies/TopResume", "Companies/Resumeble", "Companies/Jobscan",
                          "Companies/Network(ing)/Gianna Scorsone"}
    ck("live SEMANTICS: every live label is under a reviewed root (Me/Experiences/Job Hunting) or an Alex-reviewed Companies/* path",
       all(l.split("/")[0] in ("Me", "Experiences", "Job Hunting") or l in reviewed_companies for l in live.labels))
    # Protected senders (expert networks) must never be denied — parsed from the file's own Protected section.
    live_text = open(live.path, encoding="utf-8").read() if os.path.exists(live.path) else ""
    protected = {t.lower() for title, body in _sections(live_text) if "protected senders" in title
                 for t in _TOKEN_RE.findall(body) if "." in t}
    denied_domains = set(live.domains) | {s.split("@", 1)[1] for s in live.senders}
    ck(f"live SEMANTICS: no Protected sender domain ({len(protected)}) is denylisted",
       bool(protected) and not any(d == p or d.endswith("." + p) for d in denied_domains for p in protected))
    ck("live SEMANTICS: every live sender (deny + allow) is a real address with a dotted domain",
       all("@" in x and "." in x.split("@")[1] for x in live.senders | live_allow.senders))
    fails = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  {'✓' if ok else '✗'} {n}")
    print(f"selftest: {len(checks) - len(fails)}/{len(checks)} boundary cases pass")
    return not fails


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return 0 if selftest() else 1
    ap = argparse.ArgumentParser(description="the /scan-inbox boundary as a mechanism (ADR-7 D3, YED-161)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gate"); g.add_argument("--stage", choices=["discover", "extract"], required=True)
    f = sub.add_parser("filter"); f.add_argument("--stage", choices=["A", "B"], required=True)
    c = sub.add_parser("check"); c.add_argument("--sender", required=True); c.add_argument("--labels", default=""); c.add_argument("--stage", choices=["A", "B"], default="A")
    sub.add_parser("report")
    a = ap.parse_args(argv)
    deny, allow = load_denylist(), load_allowlist()
    if a.cmd == "gate":
        code, msg = gate(a.stage, deny, allow); print(msg); return code
    if a.cmd == "filter":
        threads = json.load(sys.stdin)
        if not isinstance(threads, list):
            print("filter: expected a JSON array of thread metadata on stdin", file=sys.stderr); return 2
        if deny.status == "MISSING":
            print("REFUSE: denylist missing — nothing filtered, nothing kept", file=sys.stderr); return 2
        print(json.dumps(filter_threads(threads, a.stage, deny, allow), indent=1)); return 0
    if a.cmd == "check":
        r = classify({"from": a.sender, "labels": [x for x in a.labels.split(",") if x]}, deny, allow, a.stage)
        print(json.dumps({"skip": r["skip"], "reason": r["reason"]})); return 0
    if a.cmd == "report":
        code, msg = gate("discover", deny, allow)
        print(f"denylist: v{deny.version} {deny.status} — {len(deny.domains)} domains, {len(deny.globs)} globs, {len(deny.senders)} senders, {len(deny.labels)} labels; non-entries (bare words, never matched): {deny.ignored}; prose/blockquote tokens skipped (questions, guidance — never entries): {deny.prose_skipped}")
        print(f"allowlist: {allow.status} — {len(allow.senders)} senders, {len(allow.domains)} domains, labels {sorted(allow.labels)}")
        print(f"discover gate: {'OPEN' if code == 0 else 'CLOSED — ' + msg}")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
