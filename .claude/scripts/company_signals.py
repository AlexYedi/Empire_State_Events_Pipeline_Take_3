#!/usr/bin/env python3
"""YED-349 lane 2 — company signals: the "$0 stack + Clay" producer.

Decision (Alex, 2026-11-08, YED-349) on the bake-off in docs/bakeoff/2026-11-05-lane2/README.md
(run 1 + run 1b) and the design in docs/proposals/2026-11-05-company-signals-lane-stack.md:
a weekly free-source fetch (Sunday GitHub Action) plus a Clay research-agent leg every second
Monday session. Company RSS/press feeds are lane 4's job (feeds.py, PR #272) — NOT fetched here.

Subcommands (all stage rows in the feed_items row contract of migration 0020 / PR #305):
  fetch --watchlist <watchlist.json> --days 7 [--out run.json] [--write]
        GDELT DOC 2.0 (ONE batched OR query per week, chunked under the query-length limit, 429
        backoff) + HN Algolia stories (>= 5 points) + SEC EDGAR 8-Ks for entries with a `cik`
        (only when EDGAR_USER_AGENT is set — a declared contact is required by sec.gov, YED-337;
        skipped with a notice otherwise). GitHub releases are dropped (0 true signals in run 1).
  clay-ingest <values.json> [--watchlist <watchlist.json>] [--days 14] [--credits N] [--write]
        Parses the Claygent output the Monday session pulls through the Clay MCP every second
        week. Input: a JSON object {company_name: claygent_text}. One line per event:
        YYYY-MM-DD | kind | headline | url. With --watchlist, an unknown company's lines are
        counted refused.
  write <run.json> [--started-at ISO]
        The gated write of a saved run (the Action's write step: the only step holding the key).

Watchlist (private — the Action materialises it from the COMPANY_SIGNALS_WATCHLIST secret; the
bake-off's companies.json shape): a JSON array [{"name": str, "domain": str, "q": str|null,
"cik": str|null}]; extra keys such as `gh` are ignored. `q` is a disambiguating GDELT query
(e.g. '"Harvey AI"' or '"Kestrel Labs" OR "Talon AI"'); without it the quoted name is used.
A simple q (one quoted phrase or one bare word) is batched with the others; a compound q runs as
its own query (GDELT allows parentheses only around one OR list, so it cannot be nested). HN
uses q's first quoted phrase (Algolia has no OR syntax), else the name. GDELT hits are
attributed by the company's query terms (name + every quoted phrase in q) found in the title.
A malformed watchlist exits 3; error messages name an entry index and a field, never a value.

Row contract (public.feed_items, 0020): source_key = sha256 of the canonical URL (feeds.item_key —
tracking params stripped by feeds.canonical_url, reused, never a local copy), company (watchlist
name only — link-to-existing, never a free-form entity), feed_url = a stable source tag
('gdelt:doc2', 'hn:algolia', 'edgar:8k', 'clay:claygent'), url, title, published, summary,
kind, signal_type_guess, fetched_at, metadata = {source, kind_hint, lane: 'company_signals'}.
Lane 2 rows are kind='market' with signal_type_guess 'news', or 'partnership'/'layoff' when the
source itself labels the item so (Clay P/X, EDGAR item 2.05). The DB check pairs kind='market'
with a non-null guess; kind_hint keeps the finer label (funding, launch, exec_move …) for the
Monday-session classifier, which stays authoritative.

Write gate (--write / write): rows reach spine_client.write('feed_items', on_conflict=source_key)
ONLY IF 'feed_items' is in spine_client.ALLOW (it lands with PR #272 — a guard file, human
review) AND a table-exists probe answers 200 (migration 0020 applied). Otherwise a notice, no
feed_items write, exit 0, and the lane_run row records status 'skipped' with the reason. The
lane_run ledger row (lane key 'company_signals', seeded inactive by 0016) is written through
spine_client.write exactly as ats_pulse does; items_written counts rows ACTUALLY inserted (the
upsert returns only new rows), never rows built.

UNTRUSTED TEXT: every title, summary and URL in a row is third-party text (news sites, HN,
Claygent output) and may carry prompt-injection payloads. This producer runs no model, so
nothing here can be steered by it. The Monday-session classifier MUST treat the fields as
data: run it in a no-tools subagent, and quote each field as data in its prompt (delimited,
labelled, never spliced into instructions). Hostile URLs are counted invalid_url per item,
and no exception text that could echo input ever reaches a log.

PII (ADR-9), as ats_pulse: spine_client's own EMAIL_RE/PHONE_RE (never a local copy). A hit in
an INPUT item counts that item refused and skips it; a hit in EMITTED text hard-fails the run.
spine_client's guard re-checks every row on write.

Logs: output that names companies never reaches stdout — counts and source tags only. Request
errors log the exception TYPE only (a GDELT URL carries the batched company names). run.json
names companies: it is local, and the Action deletes it.

The Claygent prompt (Clay custom data point, Monday session, every second week; reconstructed
from run 1b — third-party sources only, the company's own site excluded because lane 4 covers
it; the window is the 14 days since the last Clay run):

    For {Company Name} ({Domain}), list news events about this company published between
    {window_start} and {window_end}. Use THIRD-PARTY sources only: news outlets, press-release
    wires (PR Newswire, Business Wire, GlobeNewswire), partner or customer announcements, and
    SEC filing coverage. EXCLUDE every page on {Domain} or its subdomains, including the
    company's own blog, newsroom and changelog. Return one line per distinct event, newest
    first, in exactly this format and nothing else:
    YYYY-MM-DD | KIND | headline | URL
    KIND is one letter: F funding, M M&A, L product launch, E executive move, X layoff,
    I incident or legal, R earnings, P partnership or customer deal, H hiring or new office.
    The date is the article's publication date; the URL is the article you read. One line per
    event, not per article. If nothing qualifies, return NONE. No commentary.

Selftest: inline fixtures, offline, negative-PII cases. Run: python3 company_signals.py --selftest
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feeds import canonical_url, item_key  # noqa: E402  (lane 4's URL identity — one definition)
from spine_client import EMAIL_ALLOWLIST_RE, EMAIL_RE, PHONE_RE, PIIViolation  # noqa: E402

LANE = "company_signals"              # public.lane_registry key (seeded inactive by 0016)
TABLE = "feed_items"
SOURCE_TAGS = {"gdelt": "gdelt:doc2", "hn": "hn:algolia", "edgar": "edgar:8k", "clay": "clay:claygent"}
GUESSES = {"news", "partnership", "layoff", "paper", "model_release"}   # the 0020 CHECK vocabulary
# Clay KIND codes (letter or word) → kind_hint; partnership/layoff carry through as the guess.
CLAY_KINDS = {"f": "funding", "m": "m_and_a", "l": "launch", "e": "exec_move", "x": "layoff",
              "i": "incident_legal", "r": "earnings", "p": "partnership", "h": "hiring_office"}
CLAY_WORDS = {"funding": "f", "fundraise": "f", "raise": "f", "m&a": "m", "acquisition": "m",
              "merger": "m", "launch": "l", "product": "l", "exec": "e", "executive": "e",
              "layoff": "x", "layoffs": "x", "incident": "i", "legal": "i", "earnings": "r",
              "partnership": "p", "partner": "p", "deal": "p", "hiring": "h", "office": "h"}
GUESS_FROM_HINT = {"partnership": "partnership", "layoff": "layoff"}
# EDGAR 8-K items, most informative first; 9.01 (exhibits) never labels a filing.
EDGAR_ITEMS = [("2.01", "m_and_a", "acquisition/disposition completed"), ("2.05", "layoff", "exit/restructuring costs"),
               ("5.02", "exec_move", "director/officer change"), ("2.02", "earnings", "results of operations"),
               ("1.01", "material_agreement", "material agreement"), ("1.02", "material_agreement", "agreement terminated"),
               ("8.01", "filing", "other events"), ("7.01", "filing", "Reg FD disclosure")]

UA = "EmpireStateEventsPipeline-company-signals/1.0 (+github.com/AlexYedi)"
GDELT = "https://api.gdeltproject.org/api/v2/doc/doc"
# GDELT DOC 2.0 refuses over-long queries with a non-JSON message. The exact limit is not
# documented where we read it; 240 chars per query (before URL encoding) is a conservative
# guess — the run log reports chunks that come back non-JSON, so a wrong guess is visible.
GDELT_QUERY_MAX = 240
GDELT_TAIL = " sourcelang:english"
GDELT_PAUSE = 6                       # ~1 request / 5 s is GDELT's unofficial ceiling (run 1)
GDELT_BACKOFF = (20, 45, 90)          # seconds before retries 2-4 on HTTP 429
HN = "https://hn.algolia.com/api/v1/search"
HN_MIN_POINTS = 5
SEC_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"
SIMPLE_Q = re.compile(r'"[^"]+"|[^\s"()]+')   # one quoted phrase or one bare word — batchable


# ---------------------------------------------------------------------------
# Watchlist
# ---------------------------------------------------------------------------

def load_watchlist(obj: object) -> list[dict]:
    """Validate the watchlist JSON → [{name, domain, q, cik}]. ValueError on any shape problem;
    messages carry an entry index and a field name only — never a value (the list is private)."""
    if not isinstance(obj, list) or not obj:
        raise ValueError("watchlist must be a non-empty JSON array")
    out, names = [], set()
    for i, e in enumerate(obj):
        if not isinstance(e, dict):
            raise ValueError(f"watchlist[{i}] is not an object")
        name = e.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"watchlist[{i}].name must be a non-empty string")
        if not isinstance(e.get("domain"), str):
            raise ValueError(f"watchlist[{i}].domain must be a string")
        q = e.get("q")
        if q is not None and (not isinstance(q, str) or not q.strip()):
            raise ValueError(f"watchlist[{i}].q must be a non-empty string or null")
        cik = e.get("cik")
        if cik is not None and not re.fullmatch(r"\d{1,10}", str(cik)):
            raise ValueError(f"watchlist[{i}].cik must be digits or null")
        if name.strip().lower() in names:
            raise ValueError(f"watchlist[{i}].name duplicates an earlier entry")
        names.add(name.strip().lower())
        out.append({"name": name.strip(), "domain": e["domain"].strip(),
                    "q": q.strip() if q else None, "cik": str(cik) if cik is not None else None})
    return out


def _phrases(q: str | None) -> list[str]:
    return [p.strip() for p in re.findall(r'"([^"]+)"', q or "") if p.strip()]


def query_terms(e: dict) -> list[str]:
    """Attribution terms: the name plus every quoted phrase in q (and a bare-word q)."""
    terms = [e["name"]] + _phrases(e["q"])
    if e["q"] and SIMPLE_Q.fullmatch(e["q"]) and not e["q"].startswith('"'):
        terms.append(e["q"])
    return list(dict.fromkeys(terms))


def gdelt_term(e: dict) -> str:
    return e["q"] or '"' + e["name"].replace('"', "") + '"'


def hn_query(e: dict) -> str:
    """Algolia has no OR syntax: q's first quoted phrase, a bare-word q, else the name."""
    ph = _phrases(e["q"])
    if ph:
        return ph[0]
    if e["q"] and SIMPLE_Q.fullmatch(e["q"]):
        return e["q"]
    return e["name"]


# ---------------------------------------------------------------------------
# Pure stages
# ---------------------------------------------------------------------------

def scan_pii(obj: object) -> None:
    """ADR-9 scan over EVERY string with spine_client's regexes (ats_pulse's scan, same rules)."""
    stack = [obj]
    while stack:
        v = stack.pop()
        if isinstance(v, str):
            for m in EMAIL_RE.finditer(v):
                if not EMAIL_ALLOWLIST_RE.search(m.group(0)):
                    raise PIIViolation("email address detected")
            if PHONE_RE.search(v):
                raise PIIViolation("phone number detected")
        elif isinstance(v, dict):
            stack.extend(v.values())
        elif isinstance(v, (list, tuple)):
            stack.extend(v)


def _clean(s: str | None, cap: int) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(s or ""))).strip()[:cap]


def attribute(title: str, candidates: list[dict]) -> str | None:
    """A GDELT hit carries no company: the first candidate (watchlist order, restricted to the
    query that returned the hit) whose query terms appear in the title owns it. No term in the
    title → unattributed, dropped (a body-only mention is the rubric's C class, not a signal)."""
    for e in candidates:
        for t in query_terms(e):
            if re.search(rf"(?<!\w){re.escape(t)}(?!\w)", title or "", re.I):
                return e["name"]
    return None


def gdelt_queries(watchlist: list[dict], limit: int = GDELT_QUERY_MAX) -> tuple[list[tuple[str, list[dict]]], list[str]]:
    """Watchlist → [(query, the entries it covers)]. Simple terms batch as '("A" OR "B")
    sourcelang:english', chunked under `limit`; a single-term chunk drops the parentheses
    (GDELT allows them only around OR'd terms); a compound q runs alone. A quoted name shorter
    than 3 chars is skipped (GDELT refuses short phrases). Returns (queries, skipped names)."""
    def render(terms):
        joined = " OR ".join(terms)
        return (f"({joined})" if len(terms) > 1 else joined) + GDELT_TAIL

    queries, solos, chunk, skipped = [], [], [], []
    for e in watchlist:
        term = gdelt_term(e)
        if (not e["q"] and len(e["name"]) < 3) or len(term + GDELT_TAIL) > limit:
            skipped.append(e["name"])
            continue
        if not SIMPLE_Q.fullmatch(term):
            solos.append((term + GDELT_TAIL, [e]))
            continue
        if chunk and len(render([gdelt_term(x) for x in chunk] + [term])) > limit:
            queries.append((render([gdelt_term(x) for x in chunk]), chunk))
            chunk = []
        chunk.append(e)
    if chunk:
        queries.append((render([gdelt_term(x) for x in chunk]), chunk))
    return queries + solos, skipped


def parse_gdelt(body: str, candidates: list[dict]) -> tuple[list[dict], int]:
    """GDELT artlist JSON → raw items. Returns (items, unattributed). Non-JSON raises ValueError."""
    if not body.strip().startswith("{"):
        raise ValueError("gdelt answered non-JSON")
    items, unattributed = [], 0
    for a in json.loads(body).get("articles") or []:
        title = _clean(a.get("title"), 300)
        company = attribute(title, candidates)
        if not company:
            unattributed += 1
            continue
        try:
            t = datetime.strptime(a.get("seendate") or "", "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            t = None
        items.append({"src": "gdelt", "company": company, "title": title, "url": a.get("url") or "",
                      "published": t, "summary": "", "kind_hint": "news"})
    return items, unattributed


def parse_hn(body: str, company: str) -> list[dict]:
    """HN Algolia search JSON → raw items, stories with >= HN_MIN_POINTS only (the noise floor)."""
    out = []
    for h in json.loads(body).get("hits") or []:
        if (h.get("points") or 0) < HN_MIN_POINTS or not h.get("created_at_i"):
            continue
        out.append({"src": "hn", "company": company, "title": _clean(h.get("title"), 300),
                    "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                    "published": datetime.fromtimestamp(h["created_at_i"], timezone.utc),
                    "summary": "", "kind_hint": "hn_story"})
    return out


def parse_edgar(body: str, company: str, cik: int) -> list[dict]:
    """data.sec.gov submissions JSON → one raw item per 8-K; kind_hint from its item codes."""
    r = (json.loads(body).get("filings") or {}).get("recent") or {}
    out = []
    forms = r.get("form") or []
    for i, form in enumerate(forms):
        if form != "8-K":
            continue
        codes = {c.strip() for c in ((r.get("items") or [""] * len(forms))[i] or "").split(",") if c.strip()}
        hint, labels = "filing", []
        for code, h, label in EDGAR_ITEMS:
            if code in codes:
                labels.append(label)
                if hint == "filing":
                    hint = h
        acc, doc = r["accessionNumber"][i], r["primaryDocument"][i]
        out.append({"src": "edgar", "company": company,
                    "title": f"{company} 8-K: {'; '.join(labels) or '8-K'}",
                    "url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}/{doc}",
                    "published": datetime.strptime(r["filingDate"][i], "%Y-%m-%d").replace(tzinfo=timezone.utc),
                    "summary": "", "kind_hint": hint})
    return out


def clay_kind(code: str) -> str | None:
    """A Claygent KIND cell → kind_hint ('F' / 'funding' / 'P - partnership' all work)."""
    c = (code or "").strip().lower()
    if c in CLAY_KINDS:
        return CLAY_KINDS[c]
    first = re.split(r"[\s/:\-–—(]+", c)[0] if c else ""
    if first in CLAY_KINDS:
        return CLAY_KINDS[first]
    if first in CLAY_WORDS:
        return CLAY_KINDS[CLAY_WORDS[first]]
    return None


def parse_clay(values: dict, watchlist: list[dict] | None, lo: date, hi: date) -> tuple[list[dict], dict]:
    """{company: claygent_text} → raw items. Lines that are not 'YYYY-MM-DD | kind | headline |
    url' are malformed; dates outside [lo, hi] are out of window. With a watchlist, names match
    case-insensitively to the watchlist spelling and an unknown company's event lines are
    counted refused (feed_items.company is link-to-existing). Returns (items, drops)."""
    drops = {"malformed": 0, "out_of_window": 0, "unknown_company": 0, "refused_unknown": 0}
    known = {e["name"].lower(): e["name"] for e in watchlist} if watchlist is not None else None
    items = []
    for raw_name, text in (values or {}).items():
        name = (raw_name or "").strip()
        company = (known.get(name.lower()) if known is not None else name) or None
        if company is None:
            drops["unknown_company"] += 1
        for line in str(text or "").splitlines():
            p = [s.strip() for s in re.sub(r"^[\s*•-]+(?=\d)", "", line.strip()).split("|")]
            if len(p) < 4 or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", p[0]) or not p[-1]:
                if line.strip() and line.strip().upper() != "NONE":
                    drops["malformed"] += 1
                continue
            try:
                day = date.fromisoformat(p[0])
            except ValueError:
                drops["malformed"] += 1
                continue
            if company is None:
                drops["refused_unknown"] += 1
                continue
            if not (lo <= day <= hi):
                drops["out_of_window"] += 1
                continue
            m = re.search(r"https?://\S+", p[-1])
            url = re.sub(r"[)\]>.,;:'\"]+$", "", m.group(0)) if m else ""
            items.append({"src": "clay", "company": company, "title": _clean(" | ".join(p[2:-1]), 300),
                          "url": url, "published": datetime(day.year, day.month, day.day, tzinfo=timezone.utc),
                          "summary": "", "kind_hint": clay_kind(p[1]) or "unlabelled"})
    return items, drops


def to_rows(items: list[dict], fetched_at: str, lo: datetime, hi: datetime) -> tuple[list[dict], dict]:
    """Raw items → feed_items rows. Input PII refuses the item (counted); a bad URL or an
    out-of-window date drops it; source_key dedupes, first wins. The EMITTED rows are then
    scanned and a hit hard-fails (PIIViolation) — nothing an input refusal missed may ship."""
    stats = {"seen": len(items), "refused": 0, "invalid_url": 0, "out_of_window": 0, "duplicate": 0}
    rows, keys = [], set()
    for it in items:
        try:
            scan_pii({k: it.get(k) for k in ("title", "url", "summary")})
        except PIIViolation:
            stats["refused"] += 1
            continue
        url = (it.get("url") or "").strip()
        try:
            # urlsplit / canonical_url raise ValueError on hostile URLs ('host:notaport/x',
            # 'http://[bad') and the message echoes the URL — per item, counted, never re-raised.
            if not url.lower().startswith(("http://", "https://")) or not urllib.parse.urlsplit(url).hostname:
                raise ValueError
            key, canon = item_key({"url": url}), canonical_url(url)
        except ValueError:
            stats["invalid_url"] += 1
            continue
        pub = it.get("published")
        if pub is None or not (lo <= pub < hi):
            stats["out_of_window"] += 1
            continue
        if key in keys:
            stats["duplicate"] += 1
            continue
        keys.add(key)
        hint = it.get("kind_hint")
        rows.append({
            "source_key": key, "company": it["company"], "feed_url": SOURCE_TAGS[it["src"]],
            "url": canon, "title": it.get("title") or "",
            "published": pub.strftime("%Y-%m-%dT%H:%M:%SZ"), "summary": it.get("summary") or "",
            "kind": "market", "signal_type_guess": GUESS_FROM_HINT.get(hint, "news"),
            "fetched_at": fetched_at,
            "metadata": {"source": it["src"], "kind_hint": hint, "lane": LANE},
        })
    scan_pii(rows)                       # layer 2: emitted text hard-fails
    return rows, stats


def validate_rows(rows: list[dict]) -> list[str]:
    """The 0020 row contract, offline: columns, key shape, kind/guess matrix, provenance."""
    cols = {"source_key", "company", "feed_url", "url", "title", "published", "summary", "kind",
            "signal_type_guess", "fetched_at", "metadata"}
    problems = []
    for i, r in enumerate(rows):
        tag = f"rows[{i}]"
        if set(r) != cols:
            problems.append(f"{tag}: columns drifted from the feed_items contract")
        if not re.fullmatch(r"[0-9a-f]{64}", str(r.get("source_key"))):
            problems.append(f"{tag}: source_key is not sha256 hex")
        if r.get("kind") not in ("launch", "market"):
            problems.append(f"{tag}: kind outside {{launch, market}}")
        g = r.get("signal_type_guess")
        if not ((r.get("kind") == "launch" and g is None) or (r.get("kind") == "market" and g in GUESSES)):
            problems.append(f"{tag}: kind/signal_type_guess violates the 0020 mapping check")
        if r.get("feed_url") not in SOURCE_TAGS.values():
            problems.append(f"{tag}: feed_url is not a lane-2 source tag")
        if (r.get("metadata") or {}).get("lane") != LANE:
            problems.append(f"{tag}: metadata.lane must be {LANE!r}")
        if not (r.get("company") or "").strip():
            problems.append(f"{tag}: company empty")
    return problems


def lane_run_row(run: dict, status: str, written: int, error: str | None, finished_at: str) -> dict:
    """The REAL public.lane_run row (0016 columns), ats_pulse's mapping. Error text names
    source tags and counts only — never a company (logs and the ledger stay name-free)."""
    return {"lane": LANE, "started_at": run["started_at"], "finished_at": finished_at,
            "status": status, "items_seen": run["stats"]["seen"], "items_written": written,
            "items_refused": run["stats"]["refused"], "credits_spent": run.get("credits", 0) or 0,
            "error": error[:1000] if error else None}


def summary_line(run: dict) -> str:
    """The ONLY run description that may reach a CI log: counts and source tags."""
    s, by = run["stats"], {}
    for r in run["rows"]:
        by[r["feed_url"]] = by.get(r["feed_url"], 0) + 1
    srcs = " · ".join(f"{k} {v}" for k, v in sorted(by.items())) or "none"
    return (f"company_signals {run['mode']}: {len(run['rows'])} rows ({srcs}) · seen {s['seen']} · "
            f"refused {s['refused']} · dropped {s['invalid_url'] + s['out_of_window'] + s['duplicate']} · "
            f"source errors {len(run['errors'])} · notices {len(run['notices'])}")


# ---------------------------------------------------------------------------
# Network (never exercised by the selftest)
# ---------------------------------------------------------------------------

def _get(url: str, ua: str = UA, timeout: int = 40) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def _gdelt_window(lo: datetime, hi: datetime) -> str:
    return f"&startdatetime={lo:%Y%m%d%H%M%S}&enddatetime={hi:%Y%m%d%H%M%S}"


def fetch_gdelt(watchlist: list[dict], lo: datetime, hi: datetime, get=_get, sleep=time.sleep):
    """ONE batched pass per week: OR across companies, chunked, paced, 429 backoff."""
    queries, skipped = gdelt_queries(watchlist)
    items, errors, unattributed = [], [], 0
    for qi, (q, chunk) in enumerate(queries):
        url = (f"{GDELT}?query={urllib.parse.quote(q)}&mode=artlist&maxrecords=250&sort=datedesc"
               f"&format=json" + _gdelt_window(lo, hi))
        for attempt in range(len(GDELT_BACKOFF) + 1):
            try:
                got, un = parse_gdelt(get(url, timeout=60), chunk)
                items += got
                unattributed += un
                break
            except Exception as e:      # TYPE only: the URL and any echo carry company names
                is_429 = getattr(e, "code", None) == 429
                if is_429 and attempt < len(GDELT_BACKOFF):
                    sleep(GDELT_BACKOFF[attempt])
                    continue
                errors.append(f"gdelt chunk[{qi}]: {'HTTP 429' if is_429 else type(e).__name__}")
                break
        if qi < len(queries) - 1:
            sleep(GDELT_PAUSE)
    notices = [f"gdelt: {len(skipped)} name(s) too short or long to query"] if skipped else []
    if unattributed:
        notices.append(f"gdelt: {unattributed} article(s) carried no watchlist query term in the title — dropped")
    return items, errors, notices, len(queries)


def fetch_hn(watchlist: list[dict], lo: datetime, hi: datetime, get=_get, sleep=time.sleep):
    items, errors = [], []
    for ci, e in enumerate(watchlist):
        qs = urllib.parse.urlencode({"query": hn_query(e), "tags": "story", "hitsPerPage": 50,
                                     "numericFilters": f"created_at_i>{int(lo.timestamp())},"
                                                       f"created_at_i<{int(hi.timestamp())}"})
        try:
            items += parse_hn(get(f"{HN}?{qs}"), e["name"])
        except Exception as ex:
            errors.append(f"hn company[{ci}]: {type(ex).__name__}")
        sleep(0.5)
    return items, errors


def fetch_edgar(watchlist: list[dict], ua: str, get=_get, sleep=time.sleep):
    """8-Ks for the watchlist entries that carry a `cik`. `ua` is the declared contact — sent to
    sec.gov only, never printed."""
    items, errors = [], []
    for ci, e in enumerate(x for x in watchlist if x["cik"]):
        cik = int(e["cik"])
        try:
            items += parse_edgar(get(SEC_SUBMISSIONS.format(cik=f"{cik:010d}"), ua=ua), e["name"], cik)
        except Exception as ex:
            errors.append(f"edgar filer[{ci}]: {type(ex).__name__}")
        sleep(0.2)                        # sec.gov allows 10 req/s
    return items, errors


# ---------------------------------------------------------------------------
# Runs and the gated write
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _window(asof: date, days: int) -> tuple[datetime, datetime]:
    hi = datetime(asof.year, asof.month, asof.day, tzinfo=timezone.utc) + timedelta(days=1)
    return hi - timedelta(days=days + 1), hi


def build_run(mode: str, items: list[dict], errors: list[str], notices: list[str],
              lo: datetime, hi: datetime, started_at: str, credits: float = 0,
              extra: dict | None = None) -> dict:
    rows, stats = to_rows(items, started_at, lo, hi)
    for k, v in (extra or {}).items():
        stats[k] = stats.get(k, 0) + v
    return {"mode": mode, "started_at": started_at, "credits": credits, "stats": stats,
            "errors": errors, "notices": notices, "rows": rows}


def run_fetch(watchlist: list[dict], asof: date, days: int, get=_get, sleep=time.sleep,
              edgar_ua: str | None = None) -> dict:
    started = _now()
    lo, hi = _window(asof, days)
    items, errors, notices, sources = [], [], [], {}
    got, err, note, calls = fetch_gdelt(watchlist, lo, hi, get=get, sleep=sleep)
    items += got; errors += err; notices += note
    sources["gdelt"] = {"calls": calls, "failed": len(err)}
    got, err = fetch_hn(watchlist, lo, hi, get=get, sleep=sleep)
    items += got; errors += err
    sources["hn"] = {"calls": len(watchlist), "failed": len(err)}
    if edgar_ua:
        got, err = fetch_edgar(watchlist, edgar_ua, get=get, sleep=sleep)
        items += got; errors += err
        sources["edgar"] = {"calls": sum(1 for e in watchlist if e["cik"]), "failed": len(err)}
    else:
        notices.append("edgar: skipped — EDGAR_USER_AGENT is not set (sec.gov needs a declared contact, YED-337)")
    run = build_run("fetch", items, errors, notices, lo, hi, started)
    run["sources"] = sources
    return run


def all_sources_failed(run: dict) -> bool:
    """True only when EVERY source that made calls had all of them fail. A quiet week (zero rows)
    with one source error is partial, not failed (review 2026-11-08, item 6)."""
    used = [s for s in (run.get("sources") or {}).values() if s["calls"]]
    return bool(used) and all(s["failed"] >= s["calls"] for s in used)


def run_clay(values: dict, watchlist: list[dict] | None, asof: date, days: int, credits: float) -> dict:
    started = _now()
    lo, hi = _window(asof, days)
    items, drops = parse_clay(values, watchlist, lo.date(), asof)
    notices = [f"clay: {v} {k.replace('_', ' ')}" for k, v in drops.items() if v]
    unknown = drops["refused_unknown"]
    run = build_run("clay-ingest", items, [], notices, lo, hi, started, credits=credits,
                    extra={"out_of_window": drops["out_of_window"], "seen": unknown, "refused": unknown})
    run["watchlisted"] = watchlist is not None     # write_run refuses an unvalidated Clay run
    return run


def _table_exists(sc) -> bool:
    """Is migration 0020 applied? 200 → yes, 404 → no; anything else raises (never write blind)."""
    code, _ = sc.req("GET", f"/{TABLE}?select=source_key&limit=1")
    if code == 200:
        return True
    if code == 404:
        return False
    raise WriteError(f"company_signals: {TABLE} existence probe failed: HTTP {code}")


class WriteError(RuntimeError):
    """A write-path failure whose message is ours: static text + HTTP status / exception TYPE
    only (an error body can echo a row). The CLI prints it; any other exception prints its type."""


def _write_lane_run(sc, row: dict) -> dict:
    code, _ = sc.write("lane_run", [row])
    if not (isinstance(code, int) and code < 400):
        raise WriteError(f"company_signals: lane_run write failed: HTTP {code}")
    return row


def write_run(run: dict, sc=None, batch: int = 500) -> dict:
    """The gated write. feed_items only if ALLOW has it AND the probe passes; the lane_run
    row always (status 'skipped' when the gate held). A feed_items batch that fails partway
    still ledgers the run ('partial' with the rows actually written, 'failed' if none were),
    then re-raises. Returns the lane_run row written."""
    if sc is None:
        import spine_client as sc
    if run.get("mode") == "clay-ingest" and not run.get("watchlisted"):
        raise WriteError("company_signals: a clay-ingest run without --watchlist cannot be written "
                         "(feed_items.company is link-to-existing)")
    problems = validate_rows(run["rows"])
    if problems:
        raise WriteError(f"company_signals: {len(problems)} row-contract problem(s) — nothing written")
    written, held = 0, None
    if TABLE not in sc.ALLOW:
        held = f"write held: '{TABLE}' is not in spine_client.ALLOW (lands with PR #272, guard review)"
    elif not _table_exists(sc):
        held = f"write held: {TABLE} does not exist yet (migration 0020)"
    else:
        for i in range(0, len(run["rows"]), batch):
            try:
                code, resp = sc.write(f"{TABLE}?on_conflict=source_key&select=source_key",
                                      run["rows"][i:i + batch],
                                      prefer="resolution=ignore-duplicates,return=representation")
                if not (isinstance(code, int) and code < 400):
                    # an error body can echo a row (company names): status only
                    raise WriteError(f"company_signals: {TABLE} write failed: HTTP {code}")
            except Exception as e:
                why = str(e) if isinstance(e, WriteError) else f"{TABLE} write failed: {type(e).__name__}"
                err = "; ".join([f"{why} after {written} row(s) written"] + run["errors"])
                _write_lane_run(sc, lane_run_row(run, "partial" if written else "failed", written, err, _now()))
                raise
            written += len(resp or [])       # ignore-duplicates returns only rows actually inserted
    if held:
        print(f"company_signals: {held} — dry-run, nothing staged")
        status = "skipped"
    elif all_sources_failed(run):
        status = "failed"
    elif run["errors"]:
        status = "partial"
    else:
        status = "success"
    err = "; ".join(([held] if held else []) + run["errors"]) or None
    return _write_lane_run(sc, lane_run_row(run, status, written, err, _now()))


# ---------------------------------------------------------------------------
# Selftest — inline fixtures, offline, negative-PII cases
# ---------------------------------------------------------------------------

WATCHLIST = [
    {"name": "Acmetron", "domain": "acmetron.example.com", "q": None, "cik": None, "gh": ["acmetron"]},
    {"name": "Zephyr", "domain": "zephyr.example.com", "q": '"Zephyr ML"', "cik": None},
    {"name": "Harvey", "domain": "harvey.ai", "q": '"Harvey AI"', "cik": None},
    {"name": "Kestrel", "domain": "kestrel.example.com", "q": '"Kestrel Labs" OR "Talon AI"', "cik": None},
    {"name": "IBM", "domain": "ibm.com", "q": None, "cik": "51143"},
]

GDELT_FIXTURE = json.dumps({"articles": [
    {"url": "https://news.example.com/acmetron-raises?utm_source=x&utm_medium=y", "title": "Acmetron raises new round",
     "seendate": "20261104T120000Z"},
    {"url": "https://news.example.com/acmetron-raises", "title": "Acmetron raises new round (syndicated)",
     "seendate": "20261104T130000Z"},                                       # same canonical URL → dedupe
    {"url": "https://wire.example.com/zephyr-gen5", "title": "Zephyr ML ships Gen-5",
     "seendate": "20261103T090000Z"},                                       # q-phrase attribution
    {"url": "https://blog.example.com/ai-roundup", "title": "Ten AI tools to watch",
     "seendate": "20261103T090000Z"},                                       # no query term → unattributed
    {"url": "https://news.example.com/harvey-old", "title": "Harvey AI hires CRO",
     "seendate": "20261001T090000Z"},                                       # out of window
    {"url": "https://news.example.com/acmetron-pr", "title": "Acmetron: call 555-123-4567 for press",
     "seendate": "20261104T090000Z"},                                       # PII in input → refused
]})
GDELT_COMPOUND = json.dumps({"articles": [
    {"url": "https://news.example.com/talon-update", "title": "Talon AI ships a big update",
     "seendate": "20261104T090000Z"},                                       # q-only term → Kestrel
]})

HN_FIXTURE = json.dumps({"hits": [
    {"title": "Show HN: built on Harvey", "url": "https://hn-linked.example.com/harvey", "points": 42,
     "created_at_i": 1793793600, "objectID": "1"},                          # 2026-11-04T12:00Z
    {"title": "Harvey question", "url": None, "points": 7, "created_at_i": 1793793600, "objectID": "45999"},
    {"title": "Harvey low score", "url": "https://x.example.com/low", "points": 3,
     "created_at_i": 1793793600, "objectID": "2"},                          # < 5 points → dropped
]})

EDGAR_SUBMISSIONS = json.dumps({"filings": {"recent": {
    "form": ["8-K", "10-Q", "8-K"], "filingDate": ["2026-11-04", "2026-11-03", "2026-11-02"],
    "accessionNumber": ["0000051143-26-000001", "0000051143-26-000002", "0000051143-26-000003"],
    "primaryDocument": ["a.htm", "b.htm", "c.htm"], "items": ["2.05,9.01", "", "5.02"]}}})

CLAY_FIXTURE = {
    "Acmetron": "2026-11-02 | P | Acmetron partners with BigCo | https://wire.example.com/acmetron-bigco).\n"
                 "2026-11-03 | F | Acmetron closes Series G | https://news.example.com/series-g\n"
                 "garbage line without pipes\n"
                 "2026-13-40 | F | impossible date | https://news.example.com/bad-date\n"
                 "2026-09-01 | L | too old | https://news.example.com/old\n"
                 "2026-11-04 | X | Acmetron trims team | not-a-url\n"
                 "2026-11-04 | E | Exec joins | https://news.example.com/exec?utm_campaign=z\n"
                 "2026-11-05 | M | Contact ceo@acmetron-press.example.com | https://news.example.com/pii\n",
    "zephyr": "2026-11-05 | layoff | Zephyr reorganizes | https://news.example.com/zephyr-reorg\nNONE",
    "Not On Watchlist": "2026-11-05 | F | Someone raises | https://news.example.com/other\n"
                        "2026-11-04 | P | Someone partners | https://news.example.com/other2",
}


class _FakeSC:
    """spine_client stand-in for the write-gate cases: records every call, sends nothing."""
    def __init__(self, allow: bool, probe: int = 200, inserted: int | None = None,
                 lane_code: int = 201, fail_batch: int | None = None):
        import spine_client as real
        self.ALLOW = dict(real.ALLOW)
        if allow:
            self.ALLOW[TABLE] = set()
        else:
            self.ALLOW.pop(TABLE, None)
        self.probe, self.inserted, self.calls = probe, inserted, []
        self.lane_code, self.fail_batch, self.batches, self.lane_rows = lane_code, fail_batch, 0, []

    def req(self, method, path, *a, **k):
        self.calls.append((method, path))
        return self.probe, []

    def write(self, table, rows, prefer=None, **k):
        self.calls.append(("POST", table))
        if table.startswith(TABLE):
            self.batches += 1
            if self.fail_batch == self.batches:
                return 500, '{"message": "row echo would be here"}'
            n = len(rows) if self.inserted is None else min(self.inserted, len(rows))
            return 201, [{"source_key": r["source_key"]} for r in rows[:n]]
        self.lane_rows.extend(rows)
        return self.lane_code, []


def _raises(fn, exc) -> bool:
    try:
        fn()
    except exc:
        return True
    except Exception:
        return False
    return False


def selftest() -> int:
    ok, n = 0, 0

    def check(name, cond):
        nonlocal ok, n
        n += 1; ok += bool(cond)
        print(f"  {'✓' if cond else '✗'} {name}")

    import spine_client
    spine_client.telemetry(False)        # selftests never write refusal telemetry
    wl = load_watchlist(json.loads(json.dumps(WATCHLIST)))
    names = [e["name"] for e in wl]
    check("watchlist: the bake-off shape loads; extra keys (gh) dropped; cik kept as a string",
          names == ["Acmetron", "Zephyr", "Harvey", "Kestrel", "IBM"]
          and all(set(e) == {"name", "domain", "q", "cik"} for e in wl) and wl[4]["cik"] == "51143")
    bad_shapes = [{}, [], [{"domain": "x.com"}], [{"name": "A", "domain": 3}],
                  [{"name": "Acme", "domain": "acme.com", "q": ""}],
                  [{"name": "Acme", "domain": "acme.com", "cik": "12ab"}],
                  [{"name": "Acme", "domain": "a.com"}, {"name": "acme", "domain": "b.com"}], ["Acme"]]
    refused_all, leaked = True, False
    for b in bad_shapes:
        try:
            load_watchlist(b)
            refused_all = False
        except ValueError as e:
            leaked |= any(s in str(e) for s in ("Acme", "acme", "12ab", "x.com"))
    check("watchlist: 8 malformed shapes refused (not array, empty, no name, bad domain, empty q, "
          "bad cik, duplicate name, non-object)", refused_all)
    check("watchlist: refusal messages name an index + field, never a value", not leaked)

    # --- GDELT batching ---------------------------------------------------------------
    qs, skipped = gdelt_queries(wl)
    check("gdelt: simple terms batch into ONE OR query; the compound q runs alone",
          [q for q, _ in qs] == ['("Acmetron" OR "Zephyr ML" OR "Harvey AI" OR "IBM") sourcelang:english',
                                 '"Kestrel Labs" OR "Talon AI" sourcelang:english']
          and [e["name"] for e in qs[1][1]] == ["Kestrel"] and not skipped)
    many = load_watchlist([{"name": f"Company Number {i:02d}", "domain": ""} for i in range(40)])
    qs2, _ = gdelt_queries(many, limit=120)
    check("gdelt: 40 names chunk under the length limit, every name exactly once",
          len(qs2) > 1 and all(len(q) <= 120 for q, _ in qs2)
          and sum(len(c) for _, c in qs2) == 40)
    single, _ = gdelt_queries(wl[:1])
    check("gdelt: a single-term chunk carries no parentheses", single[0][0] == '"Acmetron" sourcelang:english')
    _, sk = gdelt_queries(load_watchlist([{"name": "AI", "domain": ""}, {"name": "Acmetron", "domain": ""}]))
    check("gdelt: unqualified names under 3 chars are skipped (GDELT refuses short phrases)", sk == ["AI"])
    check("hn: query = q's first quoted phrase, else the name",
          [hn_query(e) for e in wl] == ["Acmetron", "Zephyr ML", "Harvey AI", "Kestrel Labs", "IBM"])
    check("attribution: by q terms — 'Talon AI' in a title attributes to Kestrel; name-only titles still match",
          attribute("Talon AI ships a big update", wl) == "Kestrel"
          and attribute("Harvey AI lands a deal", wl) == "Harvey"
          and attribute("Ten AI tools", wl) is None)

    lo, hi = _window(date(2026, 11, 5), 7)
    calls, sleeps = [], []

    def fake_get(url, ua=UA, timeout=40):
        calls.append(url)
        if url.startswith(GDELT):
            if "Talon" in urllib.parse.unquote(url):
                return GDELT_COMPOUND
            if len([c for c in calls if c.startswith(GDELT)]) == 1:
                raise urllib.error.HTTPError(url, 429, "Too Many Requests", {}, None)
            return GDELT_FIXTURE
        if url.startswith(HN):
            return HN_FIXTURE if "Harvey" in url else json.dumps({"hits": []})
        if "submissions" in url:
            return EDGAR_SUBMISSIONS
        raise AssertionError("unexpected URL")

    run = run_fetch(wl, date(2026, 11, 5), 7, get=fake_get, sleep=sleeps.append, edgar_ua=None)
    gd = [c for c in calls if c.startswith(GDELT)]
    check("gdelt: a 429 backs off and retries the SAME batched query (20 s first); 3 calls for 2 queries",
          len(gd) == 3 and gd[0] == gd[1] and sleeps[0] == GDELT_BACKOFF[0])
    check("hn: one call per company (5)", len([c for c in calls if c.startswith(HN)]) == 5)
    rows = run["rows"]
    by_url = {r["url"]: r for r in rows}
    keys = [r["source_key"] for r in rows]
    check("dedupe: source_key unique; the utm-tagged + plain copies collapse to one row",
          len(keys) == len(set(keys))
          and "https://news.example.com/acmetron-raises" in by_url and run["stats"]["duplicate"] == 1)
    check("canonical: tracking params stripped (feeds.canonical_url, reused)",
          all("utm_" not in r["url"] for r in rows))
    check("attribution: q-phrase 'Zephyr ML' → Zephyr; the compound query's 'Talon AI' hit → Kestrel",
          by_url["https://wire.example.com/zephyr-gen5"]["company"] == "Zephyr"
          and by_url["https://news.example.com/talon-update"]["company"] == "Kestrel")
    check("gdelt: unattributed titles dropped with a counts-only notice",
          not any("roundup" in r["url"] for r in rows)
          and any("no watchlist query term" in x for x in run["notices"]))
    check("window: an out-of-window GDELT hit is dropped", not any("harvey-old" in r["url"] for r in rows))
    check("refused: PII in an INPUT title refuses that item, the run lives",
          run["stats"]["refused"] == 1 and not any("acmetron-pr" in r["url"] for r in rows))
    check("hn: >= 5 points only; a url-less story falls back to its HN item link",
          "https://news.ycombinator.com/item?id=45999" in by_url and not any("low" in r["url"] for r in rows))
    check("edgar: unset EDGAR_USER_AGENT → skipped with a notice, no sec.gov call",
          not any("sec.gov" in c for c in calls) and any("EDGAR_USER_AGENT" in x for x in run["notices"]))
    check("rows: every row passes the 0020 contract", validate_rows(rows) == [])
    check("rows: lane-2 shape — kind market, guess news, stable source tag, metadata {source, kind_hint, lane}",
          all(r["kind"] == "market" and r["signal_type_guess"] == "news"
              and set(r["metadata"]) == {"source", "kind_hint", "lane"} for r in rows)
          and {r["feed_url"] for r in rows} == {"gdelt:doc2", "hn:algolia"})

    calls.clear()
    run_e = run_fetch(wl, date(2026, 11, 5), 7, get=fake_get, sleep=lambda s: None,
                      edgar_ua="selftest-agent contact")
    ed = [r for r in run_e["rows"] if r["feed_url"] == "edgar:8k"]
    check("edgar: with a UA, only entries carrying a cik are fetched (1 call, zero-padded CIK)",
          [c for c in calls if "submissions" in c] == [SEC_SUBMISSIONS.format(cik="0000051143")])
    check("edgar: 8-Ks only (10-Q skipped); item 2.05 → layoff guess, 5.02 → exec_move hint",
          len(ed) == 2 and {r["signal_type_guess"] for r in ed} == {"layoff", "news"}
          and {r["metadata"]["kind_hint"] for r in ed} == {"layoff", "exec_move"})
    check("edgar: the UA value never lands in a row, notice or error",
          "selftest-agent" not in json.dumps(run_e))

    # --- Clay -------------------------------------------------------------------------
    crun = run_clay(CLAY_FIXTURE, wl, date(2026, 11, 5), 14, credits=57.5)
    cr = {r["url"]: r for r in crun["rows"]}
    check("clay: trailing punctuation stripped from the URL ('...bigco).' → '...bigco')",
          "https://wire.example.com/acmetron-bigco" in cr)
    check("clay: P → partnership guess; X/'layoff' word → layoff guess; F → news + funding hint",
          cr["https://wire.example.com/acmetron-bigco"]["signal_type_guess"] == "partnership"
          and cr["https://news.example.com/zephyr-reorg"]["signal_type_guess"] == "layoff"
          and cr["https://news.example.com/series-g"]["metadata"]["kind_hint"] == "funding"
          and cr["https://news.example.com/series-g"]["signal_type_guess"] == "news")
    check("clay: company keys match the watchlist case-insensitively ('zephyr' → 'Zephyr')",
          cr["https://news.example.com/zephyr-reorg"]["company"] == "Zephyr")
    check("clay: malformed lines and impossible dates counted; NONE is not malformed",
          "clay: 2 malformed" in crun["notices"])
    check("clay: out-of-window dates dropped and counted", crun["stats"]["out_of_window"] >= 1
          and "https://news.example.com/old" not in cr)
    check("clay: a non-URL cell is dropped (invalid_url)", crun["stats"]["invalid_url"] == 1)
    check("clay: an unknown company's 2 event lines are counted REFUSED (seen too), never emitted",
          "clay: 1 unknown company" in crun["notices"] and "clay: 2 refused unknown" in crun["notices"]
          and not any("other" in u for u in cr) and crun["stats"]["refused"] == 3)   # 2 unknown + 1 PII
    check("clay: PII in a headline refuses the line", "https://news.example.com/pii" not in cr)
    nowl = run_clay(CLAY_FIXTURE, None, date(2026, 11, 5), 14, credits=0)
    check("clay: without --watchlist a DRY-RUN passes names through, but write_run refuses the run",
          any(r["company"] == "Not On Watchlist" for r in nowl["rows"]) and nowl["stats"]["refused"] == 1
          and _raises(lambda: write_run(nowl, sc=_FakeSC(allow=True)), WriteError))
    check("clay: utm stripped, metadata.source 'clay', feed_url 'clay:claygent', credits carried",
          "https://news.example.com/exec" in cr and cr["https://news.example.com/exec"]["metadata"]["source"] == "clay"
          and all(r["feed_url"] == "clay:claygent" for r in crun["rows"]) and crun["credits"] == 57.5)
    check("clay: kind codes — letters, words and 'P - partnership' forms map; unknown → None",
          clay_kind("F") == "funding" and clay_kind("acquisition") == "m_and_a"
          and clay_kind("P - partnership") == "partnership" and clay_kind("Q") is None)

    # --- Kind/guess matrix and PII negatives ------------------------------------------
    good = dict(crun["rows"][0])
    bad_launch = {**good, "kind": "launch"}                      # launch must carry a NULL guess
    bad_market = {**good, "signal_type_guess": None}             # market must carry a guess
    bad_vocab = {**good, "signal_type_guess": "funding"}         # outside the CHECK vocabulary
    ok_launch = {**good, "kind": "launch", "signal_type_guess": None}
    check("matrix: launch+guess, market+null, off-vocab guess all refused; launch+null passes",
          all(validate_rows([b]) for b in (bad_launch, bad_market, bad_vocab)) and validate_rows([ok_launch]) == [])
    try:
        to_rows([{"src": "clay", "company": "x@y.example.com", "title": "t", "url": "https://a.example.com/1",
                  "published": lo + timedelta(days=1), "summary": "", "kind_hint": "funding"}],
                _now(), lo, hi)
        check("hard fail: PII in EMITTED text (a company name never scanned as input) kills the run", False)
    except PIIViolation:
        check("hard fail: PII in EMITTED text (a company name never scanned as input) kills the run", True)
    try:
        scan_pii({"title": "mail noreply@example.com", "url": "https://a.example.com/2", "summary": ""})
        check("PII: no-reply addresses are allowlisted, as in spine_client", True)
    except PIIViolation:
        check("PII: no-reply addresses are allowlisted, as in spine_client", False)

    # --- Write gate --------------------------------------------------------------------
    sc0 = _FakeSC(allow=False)
    row0 = write_run(crun, sc=sc0)
    check("gate: ALLOW lacks feed_items → no probe, no feed_items write, lane_run 'skipped' with the reason",
          ("GET", f"/{TABLE}?select=source_key&limit=1") not in sc0.calls
          and not any(t.startswith(TABLE) for _, t in sc0.calls)
          and row0["status"] == "skipped" and row0["items_written"] == 0 and "ALLOW" in row0["error"])
    sc1 = _FakeSC(allow=True, probe=404)
    row1 = write_run(crun, sc=sc1)
    check("gate: allowlisted but the table is absent (404) → held, 'skipped', 0 written",
          row1["status"] == "skipped" and "0020" in row1["error"]
          and not any(t.startswith(TABLE) for m, t in sc1.calls if m == "POST"))
    sc2 = _FakeSC(allow=True, probe=200, inserted=2)
    row2 = write_run(crun, sc=sc2)
    check("write: probe 200 → upsert on_conflict=source_key; items_written = rows ACTUALLY inserted (2, not built)",
          any(t.startswith(f"{TABLE}?on_conflict=source_key") for m, t in sc2.calls if m == "POST")
          and row2["items_written"] == 2 and len(crun["rows"]) > 2 and row2["status"] == "success")
    check("lane_run row: 0016 columns, FK key 'company_signals', Clay credits carried, refused counted",
          set(row2) == {"lane", "started_at", "finished_at", "status", "items_seen", "items_written",
                        "items_refused", "credits_spent", "error"}
          and row2["lane"] == "company_signals" and row2["credits_spent"] == 57.5 and row2["items_refused"] == 3)
    try:
        write_run(crun, sc=_FakeSC(allow=True, probe=500))
        check("gate: a probe answering 500 raises (never write blind)", False)
    except RuntimeError:
        check("gate: a probe answering 500 raises (never write blind)", True)
    err_run = {**run, "errors": ["gdelt chunk[0]: HTTP 429"]}
    row4 = write_run(err_run, sc=_FakeSC(allow=True, probe=200))
    check("lane_run: a source error → 'partial'; error text is tags + counts, never a company",
          row4["status"] == "partial" and "Acmetron" not in (row4["error"] or ""))
    check("lane_run: error text capped at the column's 1000 chars",
          len(lane_run_row(run, "partial", 0, "x" * 2000, _now())["error"]) == 1000)

    # --- Review 2026-11-08 (PR #314) ----------------------------------------------------
    hostile = ["https://news.example.com:acmetron-raises/x",    # 'Port could not be cast…'
               "http://[bad"]                                   # 'Invalid IPv6 URL'
    mixed = [{"src": "gdelt", "company": "Acmetron", "title": "t", "url": u, "summary": "",
              "published": lo + timedelta(days=1), "kind_hint": "news"}
             for u in hostile + ["https://news.example.com/fine"]]
    try:
        mrows, mstats = to_rows(mixed, _now(), lo, hi)
        check("malformed URL: hostile URLs are counted invalid_url per item; the run continues",
              mstats["invalid_url"] == 2 and len(mrows) == 1)
    except Exception:
        check("malformed URL: hostile URLs are counted invalid_url per item; the run continues", False)
    import contextlib
    import io
    import tempfile
    tmp = tempfile.mkdtemp()
    wl_path, vals_path = os.path.join(tmp, "wl.json"), os.path.join(tmp, "vals.json")
    with open(wl_path, "w", encoding="utf-8") as fh:
        json.dump(WATCHLIST, fh)
    with open(vals_path, "w", encoding="utf-8") as fh:
        json.dump({"Acmetron": "\n".join(f"2026-11-04 | F | Acmetron raises | {u}" for u in hostile)}, fh)
    out, errs = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(errs):
        rc = main(["clay-ingest", vals_path, "--watchlist", wl_path, "--asof", "2026-11-05"])
    logged = out.getvalue() + errs.getvalue()
    check("malformed URL: the CLI exits 0, logs no URL fragment / parser message, and emits no 'input refused' line",
          rc == 0 and not any(s in logged for s in ("acmetron-raises", "[bad", "Port", "IPv6", "input refused")))
    errs = io.StringIO()
    with contextlib.redirect_stderr(errs), contextlib.redirect_stdout(io.StringIO()):
        rc = main(["clay-ingest", vals_path, "--write"])
    check("clay-ingest --write without --watchlist is refused (exit 3) before anything runs",
          rc == 3 and "requires --watchlist" in errs.getvalue())
    sc5 = _FakeSC(allow=True, probe=200, lane_code=500)
    check("lane_run write answering 500 raises WriteError (the run fails, status only in the message)",
          _raises(lambda: write_run(crun, sc=sc5), WriteError))
    with open(os.path.join(tmp, "run.json"), "w", encoding="utf-8") as fh:
        json.dump(crun, fh)
    orig = globals()["write_run"]
    globals()["write_run"] = lambda r: orig(r, sc=_FakeSC(allow=True, probe=200, lane_code=500))
    try:
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            rc = main(["write", os.path.join(tmp, "run.json")])
    finally:
        globals()["write_run"] = orig
    check("lane_run write answering 500 → the CLI exits non-zero", rc == 1)
    sc6 = _FakeSC(allow=True, probe=200, fail_batch=2)
    raised = _raises(lambda: write_run(crun, sc=sc6, batch=2), WriteError)
    lr = sc6.lane_rows[-1] if sc6.lane_rows else {}
    check("mid-batch failure: a 'partial' lane_run row with the rows actually written (2), then re-raise",
          raised and lr.get("status") == "partial" and lr.get("items_written") == 2
          and "after 2 row(s) written" in (lr.get("error") or "") and "row echo" not in (lr.get("error") or ""))
    sc7 = _FakeSC(allow=True, probe=200, fail_batch=1)
    _raises(lambda: write_run(crun, sc=sc7, batch=2), WriteError)
    check("first-batch failure: the lane_run row is 'failed' with 0 written",
          sc7.lane_rows and sc7.lane_rows[-1]["status"] == "failed" and sc7.lane_rows[-1]["items_written"] == 0)
    quiet = {**run, "rows": [], "errors": ["hn company[0]: URLError"],
             "sources": {"gdelt": {"calls": 2, "failed": 0}, "hn": {"calls": 5, "failed": 1}}}
    dead = {**quiet, "sources": {"gdelt": {"calls": 2, "failed": 2}, "hn": {"calls": 5, "failed": 5}}}
    check("exit rule: a quiet week (0 rows, one source error) is partial, not failed; all-failed is failed",
          not all_sources_failed(quiet) and all_sources_failed(dead)
          and write_run(quiet, sc=_FakeSC(allow=True))["status"] == "partial"
          and write_run(dead, sc=_FakeSC(allow=True))["status"] == "failed")
    check("exit rule: the live selftest fetch recorded per-source calls (gdelt 2, hn 5)",
          run["sources"] == {"gdelt": {"calls": 2, "failed": 0}, "hn": {"calls": 5, "failed": 0}})
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)

    # --- Logs stay name-free ----------------------------------------------------------
    line = summary_line(run) + summary_line(crun) + " ".join(run["errors"] + run["notices"] + crun["notices"])
    check("logs: the summary line, errors and notices never name a watchlist company",
          not any(c.lower() in line.lower() for c in names + ["Not On Watchlist"]))

    # --- Workflow lint ----------------------------------------------------------------
    wf = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                      ".github", "workflows", "company-signals.yml")
    if os.path.exists(wf):
        import ats_pulse
        problems = ats_pulse.lint_workflow_shell(wf)
        check("workflow shell lint: every run: block in company-signals.yml passes bash -n + heredoc pairing"
              + (f" — PROBLEMS: {problems}" if problems else ""), not problems)
        text = open(wf, encoding="utf-8").read()
        check("workflow: the key is scoped to the write step only (one SUPABASE_API_KEY line)",
              text.count("secrets.SUPABASE_API_KEY") == 1)
        check("workflow: writes gated on vars.COMPANY_SIGNALS_WRITE_ENABLED == 'true'",
              "vars.COMPANY_SIGNALS_WRITE_ENABLED == 'true'" in text)
        check("workflow: input is the COMPANY_SIGNALS_WATCHLIST secret; an empty one SKIPS green; "
              "TARGET_COMPANIES_REGISTRY is not used",
              "secrets.COMPANY_SIGNALS_WATCHLIST" in text and "has_watchlist=false" in text
              and "secrets.TARGET_COMPANIES_REGISTRY" not in text)

    print(f"selftest: {ok}/{n} company_signals cases pass")
    return 0 if ok == n else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _watchlist(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return load_watchlist(json.load(fh))


def _save(run: dict, out: str | None) -> None:
    if out:
        if os.path.dirname(out):
            os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(run, fh, indent=1); fh.write("\n")


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch", help="weekly free-source fetch: GDELT + HN (+ EDGAR)")
    f.add_argument("--watchlist", required=True, help="watchlist JSON [{name, domain, q, cik}] (private)")
    f.add_argument("--days", type=int, default=7)
    f.add_argument("--asof", help="window end date YYYY-MM-DD (default: today, UTC)")
    f.add_argument("--out", help="save the run (rows name companies: keep it local)")
    f.add_argument("--write", action="store_true", help="gated write (see the docstring)")
    c = sub.add_parser("clay-ingest", help="parse Claygent output into rows")
    c.add_argument("values", help="JSON object {company_name: claygent_text}")
    c.add_argument("--watchlist", help="validate company names against it (unknown → refused)")
    c.add_argument("--days", type=int, default=14)
    c.add_argument("--asof")
    c.add_argument("--credits", type=float, default=0, help="Clay credits this run spent (lane_run.credits_spent)")
    c.add_argument("--out")
    c.add_argument("--write", action="store_true")
    w = sub.add_parser("write", help="gated write of a saved run (the Action's write step)")
    w.add_argument("run")
    w.add_argument("--started-at", help="override the run's started_at")
    a = ap.parse_args(argv)

    # EVERY message below is static text, a load_watchlist message (index + field, never a value),
    # an HTTP status or an exception TYPE — no exception text that could echo input reaches a log.
    # "input refused:" is the one line the Action greps into the public log: watchlist only.
    if a.cmd == "clay-ingest" and a.write and not a.watchlist:
        print("company_signals: input refused: clay-ingest --write requires --watchlist "
              "(feed_items.company is link-to-existing)", file=sys.stderr)
        return 3
    wl = None
    if a.cmd != "write" and a.watchlist:
        try:
            wl = _watchlist(a.watchlist)
        except json.JSONDecodeError:
            print("company_signals: input refused: the watchlist is not valid JSON", file=sys.stderr)
            return 3
        except ValueError as e:              # load_watchlist's own messages only
            print(f"company_signals: input refused: {e}", file=sys.stderr)
            return 3
        except OSError as e:
            print(f"company_signals: input unreadable: {type(e).__name__}", file=sys.stderr)
            return 3
    try:
        if a.cmd == "write":
            with open(a.run, encoding="utf-8") as fh:
                run = json.load(fh)
            if a.started_at:
                run["started_at"] = a.started_at
        elif a.cmd == "clay-ingest":
            with open(a.values, encoding="utf-8") as fh:
                values = json.load(fh)
            if not isinstance(values, dict):
                print("company_signals: input unreadable: clay values must be a JSON object", file=sys.stderr)
                return 3
    except (OSError, ValueError) as e:
        print(f"company_signals: input unreadable: {type(e).__name__}", file=sys.stderr)
        return 3
    try:
        if a.cmd != "write":
            asof = date.fromisoformat(a.asof) if a.asof else datetime.now(timezone.utc).date()
            if a.cmd == "fetch":
                run = run_fetch(wl, asof, a.days, edgar_ua=os.environ.get("EDGAR_USER_AGENT") or None)
            else:
                run = run_clay(values, wl, asof, a.days, a.credits)
    except PIIViolation as e:                # spine_client's rule message: no value
        print(f"company_signals: emitted text failed the PII scan ({e}) — nothing saved or written", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"company_signals: run failed: {type(e).__name__}", file=sys.stderr)
        return 1

    if a.cmd != "write":
        _save(run, a.out)
        print(summary_line(run))
        for note in run["notices"]:
            print(f"company_signals: {note}")
        for err in run["errors"]:
            print(f"company_signals: source error: {err}")
    if a.cmd == "write" or a.write:
        try:
            row = write_run(run)
        except WriteError as e:
            print(str(e), file=sys.stderr)
            return 1
        except Exception as e:
            print(f"company_signals: write failed: {type(e).__name__}", file=sys.stderr)
            return 1
        print(f"company_signals: lane_run written ({row['status']} · seen {row['items_seen']} · "
              f"written {row['items_written']} · refused {row['items_refused']} · credits {row['credits_spent']})")
    else:
        print("company_signals: dry-run — nothing written (pass --write, or run `write <run.json>`)")
    if a.cmd == "fetch" and all_sources_failed(run):
        return 1                                    # EVERY source failed: let the Action's alarm fire
    return 0


if __name__ == "__main__":
    sys.exit(main())
