#!/usr/bin/env python3
"""reconcile — the READ-ONLY completeness ledger for the knowledge graph (YED-384; graph-completeness plan B1).

Joins four inventories by event date + normalized title and emits one row per event with a status vector:
  local  : `Event Content/MM DD YY Title/` folders (filesystem, not git: some folders are untracked)
           `event-transcripts/YYYY-MM-DD_Title.*`
           `.claude/.state/research/*.manifest.json` · `.claude/.state/briefs/*.md` · `.claude/.state/post-event/*/run-state.json`
  prod   : `event` (kind attended|researched) · `claim` counts per event by provenance_tier · `documents`
           (research_brief / post_event_brief), all via spine_client.req("GET", …). Nothing is ever written.

  substrate.py reconcile --report [--root DIR] [--baseline PRIOR_QUEUE.json]
  substrate.py reconcile --queue [PATH]          (default .claude/.state/reconcile-queue.json, gitignored)
  python3 .claude/scripts/reconcile.py --selftest  (offline: fixture tree + stubbed req)

Gaps per row (the work queue the nightly job will drain later):
  no_row                    uploaded attendance evidence (transcript / post-event brief / ledger), no attended row
  research_not_staged       a local research file or manifest, 0 research claims in the graph
  post_event_not_staged     a local post-event brief, 0 first-hand claims
  transcript_not_staged     a local transcript, 0 first-hand claims
  attended_no_local_source  an attended row with 0 first-hand claims and nothing on disk to stage from (needs Notion)
  ambiguous                 an item that scored equally against 2+ rows; never merged, kept as its own row for Alex

Privacy (ADR-9, invariant 4): output carries event titles, dates and counts only. Claim text is never selected
(the claim GET names its columns), file CONTENTS are never read except the event title/date/id of a research
manifest and the event name of a run-state ledger, `*.PRIVATE.*` files are skipped by name and never opened, and
every title passes the spine_client email/phone patterns before it reaches stdout or the queue.
Attendance is never inferred (ADR-10 D9): `attendance_evidence_uploaded` is a proposal for Alex to confirm.
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, re, sys, tempfile, zoneinfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spine_client  # noqa: E402  (module import: the selftest stubs spine_client.req)
from spine_client import EMAIL_RE, PHONE_RE  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DEFAULT_QUEUE = os.path.join(ROOT, ".claude", ".state", "reconcile-queue.json")
# YED-406: reviewed file-name -> event Notion page id aliases, for session-level or undated files whose names can't
# title-match their event ("revolt-s2-airspeed", "ElasticON-NYL-Picheria-…"). Keys are "<source>:<parsed title>".
ALIASES_PATH = os.path.join(ROOT, ".claude", "references", "reconcile-aliases.json")
OCCASION_KINDS = ("attended", "researched")    # `researched` is plan B0; harmless to ask for before it exists
RESEARCH_TIERS = ("web_verified", "email_signal")
GAP_TYPES = ("no_row", "research_not_staged", "post_event_not_staged", "transcript_not_staged",
             "attended_no_local_source", "ambiguous")
NY = zoneinfo.ZoneInfo("America/New_York")
# The null baseline (plan Part 2 §2.1, prod read 2026-11-10). Gap totals have no prior number: this run is their null.
BASELINE_2026_11_10 = {"attended_first_hand": [30, 85], "attended_any_claim": [32, 85],
                       "researched_with_row": [7, 50], "research_claims_with_event": [852, 5800]}

FOLDER_RE = re.compile(r"^(\d\d) (\d\d) (\d\d) (.+)$")
DATED_FILE_RE = re.compile(r"^(\d{4})-(\d\d)-(\d\d)[_ -](.+)$")
NON_EVENT_RE = re.compile(r"upcoming week|roundup|visual prompts|elevated posts|combined .*events|"
                          r"^\w+day nyc ai events$|chain test", re.I)          # content folders, not occasions
PRIVATE_RE = re.compile(r"(^|[._ -])private([._ -]|$)", re.I)
MEDIA_EXT = (".png", ".jpg", ".jpeg", ".gif", ".pdf", ".html", ".m4a", ".mp3", ".mp4", ".mov", ".wav", ".docx",
             ".pptx", ".svg", ".webp", ".zip")
STOP = {"the", "a", "an", "with", "and", "of", "in", "at", "by", "for", "on", "to", "x", "vs", "w", "research",
        "brief", "event", "events", "recording", "transcript", "elevenlabs", "raw", "md", "txt", "json"}
YEARS = {"2025", "2026", "2027", "25", "26", "27"}
GENERIC = {"ai", "nyc", "meetup", "night", "week", "day", "talk", "talks", "panel", "session", "live", "virtual",
           "webinar", "agents", "agent", "gtm", "builders", "hackathon", "summit", "demo", "demos", "party",
           "january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
           "november", "december", "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov",
           "dec"}                                                     # month words: the date already carries them


def safe(s: str) -> str:
    """Titles only ever leave this module through here: email / phone shapes become [redacted]."""
    return PHONE_RE.sub("[redacted]", EMAIL_RE.sub("[redacted]", s or "")).strip()


def tokens(title: str) -> frozenset:
    t = re.sub(r"\bnew[\s_-]+york\b", "nyc", (title or "").lower()).replace("&", " and ")
    t = re.sub(r"[{}'’!.]", "", t)                                  # Elastic{ON} -> elasticon, MongoDB.local
    t = re.sub(r"(?<=[a-z])(?=\d)|(?<=\d)(?=[a-z])", " ", t)         # day2 -> day 2, s1 -> s 1
    return frozenset(w for w in re.split(r"[^a-z0-9]+", t)
                     if w and w not in STOP and w not in YEARS and not (len(w) == 1 and w.isalpha()))


def _numbers_conflict(a: frozenset, b: frozenset) -> bool:
    na, nb = {w for w in a if w.isdigit()}, {w for w in b if w.isdigit()}
    return bool(na and nb and not (na & nb))                         # "AI Demos #10" is not "AI Demos #11"


def _score(a: frozenset, b: frozenset) -> tuple[float, float, int]:
    inter = len(a & b)
    if not inter:
        return 0.0, 0.0, 0
    return inter / min(len(a), len(b)), inter / len(a | b), inter


def pid(v) -> str | None:
    h = re.sub(r"[^0-9a-f]", "", str(v or "").lower())
    return h[-32:] if len(h) >= 32 else None


def _shift(d: str, days: int) -> str:
    return (dt.date.fromisoformat(d) + dt.timedelta(days=days)).isoformat()


def local_day(v) -> str | None:
    """The New York calendar day of a timestamptz. Exactly 00:00:00 UTC is a date-only write (76/85 prod rows on
    2026-11-11, e.g. Revolt Day 1 = 2026-10-14T00:00Z) and keeps its UTC date; any real time of day is converted."""
    s = str(v or "")
    try:
        t = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return s[:10] or None
    if t.tzinfo is None or (t.utcoffset() == dt.timedelta(0) and t.time() == dt.time(0)):
        return t.date().isoformat()
    return t.astimezone(NY).date().isoformat()


def specific(tk: frozenset) -> frozenset:
    """Tokens that can tell two events apart: generic words out, numbers kept (the number guard needs them)."""
    return tk - GENERIC


class Ambiguous:
    """match() result when 2+ rows score equally: the item is never merged (a false merge costs more than a split)."""
    def __init__(self, rows):
        self.rows = rows


def match(item: dict, rows: list[dict]) -> dict | Ambiguous | None:
    """Best existing row for an inventory item, None (a new row) or Ambiguous (a tie). Pure; covered by the selftest.
    Containment and overlap count specific (non-generic) words; Jaccard ranks on all words. Tiers: notion id · same date (containment ≥0.6) · same date,
    session file, one row sharing ≥2 specific words (1 word only when it is the date's sole row) · ±1 day
    (containment ≥0.8 and Jaccard ≥0.6, ≥2 shared) · undated (containment ≥0.75, ≥2 shared). Any equal-score tie
    is Ambiguous; attendance never breaks a tie."""
    cands = [r for r in rows if not r["non_event"]]
    if item.get("nid"):
        for r in cands:
            if item["nid"] in r["nids"]:
                return r
    tk, d = specific(item["tokens"]), item.get("date")

    def best(pool, min_cont, min_jac=0.0, min_inter=1):
        scored = []
        for r in pool:
            if _numbers_conflict(tk, r["tokens"]):
                continue
            c, _, n = _score(tk, specific(r["tokens"]))               # gate on words that tell events apart
            j = _score(item["tokens"], r["tokens"])[1]                    # rank on all words, as before
            if c >= min_cont and j >= min_jac and n >= min_inter:
                scored.append(((c, j), r))
        scored.sort(key=lambda x: x[0], reverse=True)
        if not scored:
            return None
        tied = [r for s, r in scored if s == scored[0][0]]
        return tied[0] if len(tied) == 1 else Ambiguous(tied)

    if d:
        same = [r for r in cands if r["date"] == d]
        r = best(same, 0.6)
        if r:
            return r
        if not tk:                                                    # an all-generic title ("AI Demo Night") joins
            plain = [r for r in same if not specific(r["tokens"])     # only a row that adds nothing specific either
                     and _score(item["tokens"], r["tokens"])[0] >= 0.6]
            if len(plain) == 1:
                return plain[0]
            if plain:
                return Ambiguous(plain)
        if item["source"] in ("transcript", "brief"):                 # session-level file names (speaker · talk)
            words = lambda r: {w for w in tk & r["tokens"] if not w.isdigit()}  # noqa: E731
            hits = [r for r in same if len(words(r)) >= 2 or (len(same) == 1 and words(r))]
            if len(hits) == 1:
                return hits[0]
            if hits:
                return Ambiguous(hits)
        return best([r for r in cands if r["date"] in (_shift(d, -1), _shift(d, 1))], 0.8, 0.6, 2)
    return best(cands, 0.75, 0.0, 2)


def classify(name: str) -> set:
    """Evidence classes from a file NAME (contents are never opened). Private and media files carry none."""
    n = name.lower()
    if n.startswith(".") or PRIVATE_RE.search(n) or n.endswith(MEDIA_EXT):
        return set()
    out = set()
    if "transcript" in n or n.endswith(".vtt"):
        out.add("transcript")
    if re.search(r"post[-_ ]event", n) and "brief" in n or "showcase_brief" in n:
        out.add("post_event_brief")
    if "research" in n or re.search(r"pre[-_ ]event[-_ ]brief|deep[-_ ]read|evidence", n):
        out.add("research")
    # Hackathon build journals are post-event content too (Alex, 2026-11-11: attended = post-event
    # content uploaded and acknowledged). Name-only, like every other class.
    if re.search(r"journal|week[-_ ]log|(?<![a-z])retro(?![a-z])", n):
        out.add("journal")
    return out


# ---------------------------------------------------------------------------------------------
# inventories
# ---------------------------------------------------------------------------------------------
def load_aliases(path: str = ALIASES_PATH) -> dict:
    """{"<source>:<title>": notion page id}. Missing file = no aliases; a value that isn't a page id is ignored."""
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh).get("aliases") or {}
    except (OSError, ValueError):
        return {}
    return {k: pid(v) for k, v in raw.items() if isinstance(k, str) and pid(v)}


def local_items(root: str, inv: dict, aliases: dict | None = None) -> list[dict]:
    items = []
    aliases = aliases or {}

    def add(source, title, date=None, nid=None, flags=(), folder=None, non_event=False):
        alias = None if nid else pid(aliases.get(f"{source}:{title}"))
        if alias:
            inv["aliased"] = inv.get("aliased", 0) + 1
        items.append({"source": source, "title": safe(title), "date": date, "nid": pid(nid) or alias, "flags": set(flags),
                      "folder": safe(folder) if folder else None, "non_event": non_event, "tokens": tokens(title)})

    ec = os.path.join(root, "Event Content")
    for name in sorted(os.listdir(ec)) if os.path.isdir(ec) else []:
        path = os.path.join(ec, name)
        m = FOLDER_RE.match(name)
        if PRIVATE_RE.search(name):                                     # never walked, never titled
            inv["private_skipped"] += 1
            continue
        if not os.path.isdir(path) or not m:
            inv["folders_unparsed"] += 1
            continue
        inv["folders"] += 1
        flags = set()
        for dirpath, dirs, files in os.walk(path):
            dirs[:] = [x for x in dirs if not PRIVATE_RE.search(x) and not x.startswith(".")]
            if os.path.basename(dirpath).lower() == "journal" and any(
                    not PRIVATE_RE.search(f) and not f.startswith(".") for f in files):
                flags.add("journal")
            for fn in files:
                flags |= classify(fn)
        title = m.group(4)
        non_event = bool(NON_EVENT_RE.search(title))
        inv["folders_non_event"] += non_event
        add("folder", title, f"20{m.group(3)}-{m.group(1)}-{m.group(2)}", flags=flags, folder=name,
            non_event=non_event)
    et = os.path.join(root, "event-transcripts")
    for fn in sorted(os.listdir(et)) if os.path.isdir(et) else []:
        m = DATED_FILE_RE.match(fn)
        if (not m or not os.path.isfile(os.path.join(et, fn)) or PRIVATE_RE.search(fn)
                or fn.lower().endswith(MEDIA_EXT)):                     # an image or audio file is not a transcript
            inv["transcripts_unparsed"] += 1
            continue
        inv["transcripts"] += 1
        flags = classify(fn) or {"transcript"}                         # a pre-event brief filed here is not a transcript
        add("transcript", os.path.splitext(m.group(4))[0], f"{m.group(1)}-{m.group(2)}-{m.group(3)}", flags=flags)
    st = os.path.join(root, ".claude", ".state")
    rd = os.path.join(st, "research")
    for fn in sorted(os.listdir(rd)) if os.path.isdir(rd) else []:
        if not fn.endswith(".manifest.json") or PRIVATE_RE.search(fn):
            continue
        try:
            with open(os.path.join(rd, fn), encoding="utf-8") as fh:
                ev = json.load(fh).get("event") or {}
        except (OSError, ValueError):
            inv["manifests_unreadable"] += 1
            continue
        inv["manifests"] += 1                                         # only title / date / page id are read
        add("manifest", ev.get("title") or fn[:-14], local_day(ev.get("event_date")),
            nid=ev.get("notion_page_id"), flags={"research"})
    bd = os.path.join(st, "briefs")
    for fn in sorted(os.listdir(bd)) if os.path.isdir(bd) else []:
        if not fn.endswith(".md") or PRIVATE_RE.search(fn):
            continue
        inv["briefs"] += 1
        m = re.match(r"^(\d{4}-\d\d-\d\d)-(.+)\.md$", fn)
        t = re.match(r"^(.+)-(\d{4}-\d\d-\d\d)\.md$", fn)                # date as prefix or suffix
        title, date = (m.group(2), m.group(1)) if m else (t.group(1), t.group(2)) if t else (fn[:-3], None)
        add("brief", title, date, flags={"post_event_brief"})
    pd = os.path.join(st, "post-event")
    for slug in sorted(os.listdir(pd)) if os.path.isdir(pd) else []:
        rs = os.path.join(pd, slug, "run-state.json")
        if PRIVATE_RE.search(slug):
            inv["private_skipped"] += 1
            continue
        if not os.path.isfile(rs):
            continue
        try:
            with open(rs, encoding="utf-8") as fh:
                name = json.load(fh).get("event") or slug
        except (OSError, ValueError):
            name = slug
        inv["ledgers"] += 1
        add("brief", name, None, flags={"post_event_ledger"})
    return items


def _get_all(path: str, page: int = 1000) -> list:
    out, off = [], 0
    while True:
        status, rows = spine_client.req("GET", f"{path}&limit={page}&offset={off}")
        if status >= 400:
            raise RuntimeError(f"GET {path.split('?')[0]} -> {status}")
        out += rows or []
        if len(rows or []) < page:
            return out
        off += page


def prod_inventory() -> dict:
    """GET only. Claims: the three columns needed to count, never claim_text / quote."""
    kinds = ",".join(OCCASION_KINDS)
    events = _get_all(f"/event?select=id,kind,title,event_date,source,notion_page_id&kind=in.({kinds})&order=id")
    claims = _get_all("/claim?select=event_id,provenance_tier,nid:metadata->>notion_event_id&order=id")
    status, _ = spine_client.req("GET", "/documents?select=id&limit=1")        # check, don't assume
    docs = (_get_all("/documents?select=id,source_type,event_id,title,doc_date,nid:metadata->>notion_event_id"
                     "&source_type=in.(research_brief,post_event_brief)&order=id") if status < 400 else None)
    return {"events": events, "claims": claims, "documents": docs}


# ---------------------------------------------------------------------------------------------
# the join
# ---------------------------------------------------------------------------------------------
def _new_row(title, date, non_event=False):
    return {"title": title, "date": date, "tokens": tokens(title), "non_event": non_event, "nids": set(),
            "event_id": None, "kind": None, "in_graph": False, "research_doc_in_graph": False,
            "post_event_doc_in_graph": False, "flags": set(), "folders": [], "sources": set(), "ambiguous_with": []}


def _place(m, title, date, rows, non_event=False) -> dict:
    """The row an item lands on: its match, or a new row (an Ambiguous match records the tied titles and stays apart)."""
    if isinstance(m, dict):
        return m
    r = _new_row(title, date, non_event)
    if isinstance(m, Ambiguous):
        r["ambiguous_with"] = sorted(x["title"] for x in m.rows)
    rows.append(r)
    return r


def reconcile(root: str, prod: dict, today: str | None = None, aliases: dict | None = None) -> dict:
    today = today or dt.date.today().isoformat()
    inv = {k: 0 for k in ("folders", "folders_non_event", "folders_unparsed", "transcripts", "transcripts_unparsed",
                          "manifests", "manifests_unreadable", "briefs", "ledgers", "private_skipped")}
    rows: list[dict] = []
    by_event: dict[str, dict] = {}
    for e in prod["events"]:                                           # prod rows are anchors; never merged together
        r = _new_row(safe(e.get("title")), local_day(e.get("event_date")))
        r.update(event_id=e["id"], kind=e.get("kind"), in_graph=e.get("kind") == "attended")
        r["nids"] |= {pid(e.get("notion_page_id"))} - {None}
        r["sources"].add("prod_event")
        rows.append(r)
        by_event[e["id"]] = r
    docs = prod.get("documents") or []
    for d in docs:
        if d.get("source_type") == "post_event_brief" and d.get("event_id") in by_event:
            by_event[d["event_id"]]["post_event_doc_in_graph"] = True
    for d in docs:
        if d.get("source_type") != "research_brief":
            continue
        title = re.sub(r"^research brief\s*[—–-]\s*", "", d.get("title") or "", flags=re.I)
        it = {"source": "prod_doc", "title": safe(title), "date": local_day(d.get("doc_date")),
              "nid": pid(d.get("nid")), "tokens": tokens(title)}
        r = _place(by_event.get(d.get("event_id")) or match(it, rows), it["title"], it["date"], rows)
        r["research_doc_in_graph"] = True
        r["nids"] |= {it["nid"]} - {None}
        r["sources"].add("prod_doc")
    for it in local_items(root, inv, load_aliases() if aliases is None else aliases):
        r = _place(None if it["non_event"] else match(it, rows), it["title"], it["date"], rows, it["non_event"])
        r["flags"] |= it["flags"]
        r["nids"] |= {it["nid"]} - {None}
        r["sources"].add(it["source"])
        if it["folder"]:
            r["folders"].append(it["folder"])

    fh, res_ev, res_nid = {}, {}, {}
    res_total = res_linked = 0
    for c in prod["claims"]:
        tier, eid = c.get("provenance_tier"), c.get("event_id")
        if tier == "first_hand":
            if eid:
                fh[eid] = fh.get(eid, 0) + 1
        elif tier in RESEARCH_TIERS:
            res_total += 1
            if eid:
                res_linked += 1
                res_ev[eid] = res_ev.get(eid, 0) + 1
            elif pid(c.get("nid")):
                res_nid[pid(c["nid"])] = res_nid.get(pid(c["nid"]), 0) + 1

    out = []
    for r in rows:
        f = r["flags"]
        row = {"title": r["title"], "event_date": r["date"], "in_graph": r["in_graph"], "kind": r["kind"],
               "non_event": r["non_event"],
               "has_research_file": "research" in f,
               "research_doc_in_graph": r["research_doc_in_graph"],
               "research_claims": res_ev.get(r["event_id"], 0) + sum(res_nid.get(n, 0) for n in r["nids"]),
               "has_transcript": "transcript" in f,
               "has_post_event_brief": "post_event_brief" in f or "post_event_ledger" in f,
               "has_journal": "journal" in f,
               "post_event_doc_in_graph": r["post_event_doc_in_graph"],
               "first_hand_claims": fh.get(r["event_id"], 0),
               "folders": sorted(r["folders"]), "sources": sorted(r["sources"]),
               "ambiguous_with": r["ambiguous_with"]}
        row["attendance_evidence_uploaded"] = row["has_transcript"] or row["has_post_event_brief"] or row["has_journal"]
        gaps = []
        if row["ambiguous_with"] and not row["in_graph"]:
            gaps.append("ambiguous")                                  # identity unknown: no other gap is claimed
        elif not row["non_event"]:
            if row["attendance_evidence_uploaded"] and not row["in_graph"]:
                gaps.append("no_row")
            if row["has_research_file"] and row["research_claims"] == 0:
                gaps.append("research_not_staged")
            if row["has_post_event_brief"] and row["first_hand_claims"] == 0:
                gaps.append("post_event_not_staged")
            if row["has_transcript"] and row["first_hand_claims"] == 0:
                gaps.append("transcript_not_staged")
            if row["in_graph"] and row["first_hand_claims"] == 0 and not row["attendance_evidence_uploaded"]:
                gaps.append("attended_no_local_source")
        row["gap"] = gaps
        out.append(row)
    out.sort(key=lambda x: (x["event_date"] or "9999", x["title"]))
    return {"generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "today": today,
            "read_only": True, "inventory": inv, "documents_table": prod.get("documents") is not None,
            "summary": summarize(out, res_linked, res_total), "rows": out}


def summarize(rows: list[dict], res_linked: int, res_total: int) -> dict:
    ev = [r for r in rows if not r["non_event"]]
    known = [r for r in ev if "ambiguous" not in r["gap"]]               # metrics count resolved rows only
    att = [r for r in known if r["in_graph"]]
    evid = [r for r in known if r["attendance_evidence_uploaded"]]
    researched = [r for r in known if r["has_research_file"] or r["research_doc_in_graph"] or r["research_claims"]]
    return {
        "rows": len(rows), "event_rows": len(ev),
        "gaps": {g: sum(g in r["gap"] for r in ev) for g in GAP_TYPES},
        "metrics": {
            "attended_first_hand": [sum(r["first_hand_claims"] > 0 for r in att), len(att)],
            "attended_any_claim": [sum(r["first_hand_claims"] + r["research_claims"] > 0 for r in att), len(att)],
            "evidence_with_row": [sum(r["in_graph"] for r in evid), len(evid)],
            "evidence_with_first_hand": [sum(r["first_hand_claims"] > 0 for r in evid), len(evid)],
            "researched_with_row": [sum(r["in_graph"] for r in researched), len(researched)],
            "research_claims_with_event": [res_linked, res_total],
        }}


METRIC_LABELS = {
    "attended_first_hand": "attended events with >=1 first-hand claim",
    "attended_any_claim": "attended events with >=1 claim (any lane)",
    "evidence_with_row": "events with uploaded evidence that have an attended row",
    "evidence_with_first_hand": "events with uploaded evidence that have first-hand claims",
    "researched_with_row": "researched events with an event row",
    "research_claims_with_event": "research claims carrying an event_id",
}


def _pct(pair) -> str:
    n, d = pair
    return f"{n}/{d} ({100 * n / d:.0f}%)" if d else f"{n}/0 (n/a)"


def render(res: dict, baseline: dict | None = None) -> str:
    s, inv = res["summary"], res["inventory"]
    bsum = (baseline or {}).get("summary")
    blabel = f"baseline ({baseline.get('generated_at', '?')[:10]} queue)" if bsum else "baseline"
    L = [f"reconcile --report  ·  READ-ONLY  ·  {res['generated_at']}",
         f"inventory: {inv['folders']} event folders ({inv['folders_non_event']} content-only, "
         f"{inv['folders_unparsed']} unparsed) · {inv['transcripts']} event-transcripts · {inv['manifests']} research "
         f"manifests · {inv['briefs']} local post-event briefs · {inv['ledgers']} post-event ledgers · documents table "
         f"{'present' if res['documents_table'] else 'ABSENT'}",
         f"rows: {s['rows']} ({s['event_rows']} events, {s['rows'] - s['event_rows']} content-only)", "",
         f"{'gap':28s} {'count':>6s}   {blabel}"]
    for g in GAP_TYPES:
        b = str(bsum["gaps"].get(g, "—")) if bsum else "null: this run"
        L.append(f"{g:28s} {s['gaps'][g]:6d}   {b}")
    L += ["", f"{'completeness':58s} {'now':>14s}   {blabel}"]
    for k, label in METRIC_LABELS.items():
        if bsum and k in bsum.get("metrics", {}):
            b = _pct(bsum["metrics"][k])
        elif k in BASELINE_2026_11_10:
            b = _pct(BASELINE_2026_11_10[k]) + " (plan, 2026-11-10)"
        else:
            b = "null: this run"
        L.append(f"{label:58s} {_pct(s['metrics'][k]):>14s}   {b}")
    nr = [r for r in res["rows"] if "no_row" in r["gap"]]
    L += ["", f"attendance confirmation candidates (no_row; proposals, never inferred — ADR-10 D9): {len(nr)}"]
    L += [f"  {r['event_date'] or '????-??-??'}  {r['title']}" for r in nr]
    am = [r for r in res["rows"] if "ambiguous" in r["gap"]]
    L += ["", f"tied items (gap: ambiguous; never merged, Alex to place): {len(am)}"]
    L += [f"  {r['event_date'] or '????-??-??'}  {r['title']}  <-> {' | '.join(r['ambiguous_with'])}" for r in am]
    return "\n".join(L)


def _assert_clean(text: str) -> None:
    if EMAIL_RE.search(text):
        raise RuntimeError("reconcile: an email-shaped string reached the output; refusing to emit it")
    if PHONE_RE.search(text):
        raise RuntimeError("reconcile: a phone-shaped string reached the output; refusing to emit it")


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return 0 if selftest() else 1
    ap = argparse.ArgumentParser(prog="substrate.py reconcile", description=__doc__.split("\n")[0])
    ap.add_argument("--report", action="store_true", help="print the summary table to stdout")
    ap.add_argument("--queue", nargs="?", const=DEFAULT_QUEUE, metavar="PATH",
                    help=f"write the gap list as JSON (default {os.path.relpath(DEFAULT_QUEUE, ROOT)})")
    ap.add_argument("--root", default=ROOT, help="the checkout whose local inventories are read (default: this repo)")
    ap.add_argument("--baseline", metavar="PRIOR_QUEUE.json", help="compare against a previous --queue file")
    a = ap.parse_args(argv)
    if not (a.report or a.queue):
        ap.error("nothing to do: pass --report and/or --queue [PATH]")
    res = reconcile(os.path.abspath(a.root), prod_inventory())
    if a.report:
        base = None
        if a.baseline:
            with open(a.baseline, encoding="utf-8") as fh:
                base = json.load(fh)
        text = render(res, base)
        _assert_clean(text)
        print(text)
    if a.queue:
        payload = {k: v for k, v in res.items() if k != "rows"}
        payload["queue"] = [r for r in res["rows"] if r["gap"]]
        text = json.dumps(payload, indent=1, ensure_ascii=False)
        _assert_clean(text)
        os.makedirs(os.path.dirname(os.path.abspath(a.queue)), exist_ok=True)
        with open(a.queue, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print(f"queue: {len(payload['queue'])} rows with gaps -> {a.queue}")
    return 0


# ---------------------------------------------------------------------------------------------
# selftest — offline: a fixture tree materialized into a temp dir + a stubbed spine_client.req
# ---------------------------------------------------------------------------------------------
FIXTURES = os.path.join(HERE, "fixtures", "reconcile")


def _stub_req(prod: dict, seen: list, handed: dict):
    """A GET-only PostgREST stand-in that honours `select=` (aliases included), so a widened select would hand
    reconcile the claim text and the 'columns handed back' check fails."""
    def project(row, select):
        if not select or select == "*":
            return dict(row)
        out = {}
        for f in select.split(","):
            alias, _, expr = f.partition(":")
            out[alias] = row.get(alias) if expr else row.get(f)
        return out

    def req(method, path, body=None, **kw):
        seen.append((method, path))
        if method != "GET" or body is not None:
            raise AssertionError(f"reconcile issued a non-GET: {method} {path}")
        table = path.split("?")[0].strip("/")
        if "offset=" in path and not path.endswith("offset=0"):
            return 200, []
        sel = re.search(r"[?&]select=([^&]*)", path)
        rows = [project(r, sel.group(1) if sel else "*") for r in prod.get(table, [])]
        handed.setdefault(table, []).extend(rows)
        return 200, rows
    return req


def _raises(fn) -> bool:
    try:
        fn()
    except RuntimeError:
        return True
    return False


def selftest(ok=None) -> bool:
    checks = []
    if ok is None:
        def ok(name, cond):
            checks.append((name, bool(cond)))
    with open(os.path.join(FIXTURES, "tree.json"), encoding="utf-8") as fh:
        spec = json.load(fh)
    with open(os.path.join(FIXTURES, "prod.json"), encoding="utf-8") as fh:
        prod = json.load(fh)

    ok("reconcile: Elastic{ON} New York == ElasticON NYC", tokens("Elastic{ON} New York") == tokens("ElasticON NYC"))
    on = lambda t, d="2026-06-24", src="folder": {"source": src, "title": t, "date": d, "tokens": tokens(t)}  # noqa: E731
    r10 = [_new_row("NYC AI Demos #10", "2026-06-24")]
    ok("reconcile: near-miss 'AI Demos #11' does not match '#10' on the same date", match(on("AI Demos #11"), r10) is None)
    ok("reconcile: 'AI Demos 10' matches '#10'", match(on("NYC AI Demos 10"), r10) is r10[0])
    # finding 1: sibling events on one date share only generic words
    ok("reconcile: same date, 'AI Week Closing Party' does not match 'AI Week Opening Party'",
       match(on("AI Week Closing Party"), [_new_row("AI Week Opening Party", "2026-06-24")]) is None)
    ok("reconcile: same date, 'Demo Night' does not match 'Robotics Demo Night'",
       match(on("Demo Night"), [_new_row("Robotics Demo Night", "2026-06-24")]) is None)
    ok("reconcile: same date, all-generic 'AI Demo Night' still joins 'AI Demo Night New York'",
       isinstance(match(on("AI Demo Night"), [_new_row("AI Demo Night New York", "2026-06-24")]), dict))
    ok("reconcile: same date, 'Frontier Hackathon October' joins '... Frontier Hackathon: ... — Oct 30 2026'",
       isinstance(match(on("Frontier Hackathon October"),
                        [_new_row("NYC Frontier Hackathon: Build your Autonomous Code Factory — Oct 30 2026",
                                  "2026-06-24")]), dict))
    # finding 2: a session file sharing one word with one of several same-date events
    dd = lambda: [_new_row("Deepline Deepdives: Clay workflows", "2026-11-10"),  # noqa: E731
                  _new_row("Hard Negatives Debate Night", "2026-11-10")]
    ok("reconcile: session file sharing one word ('Clay') does not join when the date has another event",
       match(on("Clay-Kareem-talk-on-retrieval", "2026-11-10", "transcript"), dd()) is None)
    ok("reconcile: session file sharing one word joins when it is the date's only event",
       isinstance(match(on("Clay-Kareem-talk-on-retrieval", "2026-11-10", "transcript"), dd()[:1]), dict))
    ok("reconcile: session file sharing two specific words joins among several events",
       match(on("Clay-workflows-Kareem-demo", "2026-11-10", "transcript"), dd())["title"].startswith("Deepline"))
    # finding 5: an equal-score tie is never broken by attendance
    tie = [_new_row("Vector Search Night", "2026-11-12"), _new_row("Vector Search Night", "2026-11-12")]
    tie[0]["in_graph"] = True
    ok("reconcile: an equal-score tie (attended vs not) is Ambiguous, not the attended row",
       isinstance(match(on("Vector Search Night", "2026-11-12"), tie), Ambiguous))
    # finding 4: timestamptz -> New York day
    ok("reconcile: local_day — 8:30pm EDT stored as the next UTC day -> the New York day",
       local_day("2026-10-15T00:30:00+00:00") == "2026-10-14")
    ok("reconcile: local_day — exactly 00:00 UTC is a date-only write and keeps its date",
       local_day("2026-10-14T00:00:00+00:00") == "2026-10-14" and local_day("2026-10-12") == "2026-10-12"
       and local_day(None) is None)
    # finding 3: each privacy layer alone
    ok("reconcile: _assert_clean raises on a raw email", _raises(lambda: _assert_clean("x jane.doe@example.com y")))
    ok("reconcile: _assert_clean raises on a raw phone", _raises(lambda: _assert_clean("call 212-555-0147 now")))
    ok("reconcile: _assert_clean passes ISO dates and counts", not _raises(lambda: _assert_clean("2026-11-11 860/5808")))
    ok("reconcile: safe() redacts a phone-shaped folder title",
       safe("11 07 26 Call 212-555-0147 Night") == "11 07 26 Call [redacted] Night")
    # finding 8
    ok("reconcile: 'retrofit' is not a retro journal; 'retro.md' is",
       "journal" not in classify("retrofit-notes.md") and "journal" in classify("hackathon_retro.md"))

    seen, handed = [], {}
    real_req = spine_client.req
    with tempfile.TemporaryDirectory(prefix="reconcile-selftest-") as tmp:
        for rel in spec["files"]:
            p = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w"):
                pass
        for rel, body in spec["json_files"].items():
            p = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(body, fh)
        spine_client.req = _stub_req(prod, seen, handed)
        try:
            res = reconcile(tmp, prod_inventory(), today="2026-11-11", aliases={})
            import copy
            prod2 = copy.deepcopy(prod)
            for e in prod2["event"]:
                if e["id"] in ("e2", "e4"):
                    e["notion_page_id"] = {"e2": "3ead3699-c2db-81dc-8c08-c18502592bee",
                                           "e4": "3fbd3699-c2db-8188-853f-eb1390785c27"}[e["id"]]
            spine_client.req = _stub_req(prod2, [], {})
            res_al = reconcile(tmp, prod_inventory(), today="2026-11-11", aliases={
                "transcript:ElasticON-S1-Picheria-SOC-Data-Pyramid": "3ead3699c2db81dc8c08c18502592bee",
                "brief:revolt-2026-day-2": "3fbd3699-c2db-8188-853f-eb1390785c27"})
        finally:
            spine_client.req = real_req
    rows = res["rows"]
    by = lambda frag: [r for r in rows if frag.lower() in r["title"].lower()]  # noqa: E731
    gaps = lambda frag: by(frag)[0]["gap"] if by(frag) else None  # noqa: E731

    ok("reconcile: every request is a GET", seen and all(m == "GET" for m, _ in seen))
    ok("reconcile: claim GET never selects claim_text / quote / *",
       all("claim_text" not in p and "quote" not in p and "select=*" not in p for _, p in seen))
    ok("reconcile: claim rows handed back (stub honours select=) carry no claim_text",
       handed.get("claim") and all("claim_text" not in r for r in handed["claim"]))
    ok("reconcile: documents table checked by a GET before use", any(p.startswith("/documents?select=id&limit=1") for _, p in seen))
    ok("reconcile: transcript, no attended row -> no_row + transcript_not_staged",
       gaps("Grok Bot") == ["no_row", "transcript_not_staged"])
    ok("reconcile: same-date near-miss stays its own row (Alt Cloud is not Revolt)",
       len(by("Alt Cloud")) == 1 and "no_row" in gaps("Alt Cloud") and "Alt Cloud" not in str(by("— Day 1")[0]["folders"]))
    ok("reconcile: folder 'Revolt 2026' (10-14) joins 'Revolt! 2026 — Day 1' stored 10-15 UTC (8:30pm New York)",
       by("— Day 1")[0]["folders"] == ["10 14 26 Revolt 2026"] and by("— Day 1")[0]["event_date"] == "2026-10-14")
    ok("reconcile: attended, 0 first-hand, nothing on disk -> attended_no_local_source",
       gaps("— Day 1") == ["attended_no_local_source"])
    ok("reconcile: undated brief tied between Day 2 and doc-only 'Demo Day | Day 2' -> ambiguous, merged into neither",
       gaps("revolt-2026-day-2") == ["ambiguous"] and len(by("revolt-2026-day-2")[0]["ambiguous_with"]) == 2
       and not by("Demo Day")[0]["has_post_event_brief"] and not by("— Day 1")[0]["has_post_event_brief"])
    ok("reconcile: report shows the ambiguous gap with its own count",
       res["summary"]["gaps"]["ambiguous"] == 1 and "tied items (gap: ambiguous" in render(res))
    ok("reconcile: attended with first-hand claims and a brief -> no gap", gaps("— Day 2") == [])
    ok("reconcile: session transcript sharing one word with Elastic{ON} stays apart (Hack Day 1 shares the date)",
       gaps("Elastic{ON}") == ["attended_no_local_source"] and gaps("Picheria") == ["no_row", "transcript_not_staged"])
    ok("reconcile: transcript 09-23 + folder 09-24 GTM World Tour -> one row (±1 day)",
       len(by("GTM World Tour")) == 1 and gaps("GTM World Tour") == ["no_row", "transcript_not_staged"])
    ok("reconcile: two Deal Flow folders, one row", len(by("Deal Flow")) == 1 and len(by("Deal Flow")[0]["folders"]) == 2)
    ok("reconcile: brief slug with a trailing date joins its event", by("Deal Flow")[0]["has_post_event_brief"])
    by_al = lambda frag: [r for r in res_al["rows"] if frag.lower() in r["title"].lower()]  # noqa: E731
    ok("reconcile (YED-406): aliased session transcript joins its event row by page id, no no_row row",
       not by_al("Picheria") and "Picheria" not in str([r["title"] for r in res_al["rows"]])
       and by_al("Elastic{ON}")[0]["has_transcript"])
    ok("reconcile (YED-406): aliased undated brief resolves the Day 2 tie, no ambiguous row",
       not by_al("revolt-2026-day-2") and res_al["summary"]["gaps"]["ambiguous"] == 0
       and by_al("— Day 2")[0]["has_post_event_brief"] and not by_al("Demo Day")[0]["has_post_event_brief"])
    ok("reconcile (YED-406): alias file loader ignores bad ids and a missing file",
       load_aliases("/nonexistent/aliases.json") == {})
    ok("reconcile: research file, 0 research claims -> research_not_staged (not merged into AI Builders)",
       gaps("AI Demos #11") == ["research_not_staged"] and not by("AI Builders")[0]["has_research_file"])
    ap_row = by("Durable State")[0]
    ok("reconcile: manifest joins by notion id; research claims via metadata.notion_event_id counted",
       ap_row["has_research_file"] and ap_row["research_claims"] == 4 and "research_not_staged" not in ap_row["gap"])
    ok("reconcile: research doc with no event row -> its own row with claims, no gap",
       by("Future Talk") and by("Future Talk")[0]["research_claims"] == 2 and gaps("Future Talk") == []
       and not by("Future Talk")[0]["in_graph"])
    ok("reconcile: post-event ledger counts as uploaded evidence", by("Ledger Night")[0]["attendance_evidence_uploaded"])
    ok("reconcile: a hackathon journal counts as uploaded evidence", by("Journal Hack")[0]["attendance_evidence_uploaded"])
    ok("reconcile: a journal/ folder holding only *.PRIVATE.* files sets no journal flag",
       not by("Quiet Hack")[0]["has_journal"] and not by("Quiet Hack")[0]["attendance_evidence_uploaded"])
    ok("reconcile: 'retrofit-notes.md' is not a journal", not by("Retrofit")[0]["has_journal"])
    ok("reconcile: an image in event-transcripts/ is not a transcript",
       not by("Slide-Photo") and res["inventory"]["transcripts_unparsed"] >= 1)
    ok("reconcile: content folder (Upcoming Week) -> non_event, no gaps",
       by("Upcoming Week")[0]["non_event"] and gaps("Upcoming Week") == [])
    ok("reconcile: *.PRIVATE.* files never count as evidence",
       by("Ghosts")[0]["has_transcript"] is False and gaps("Ghosts") == [])
    blob = json.dumps(res, default=sorted) + render(res)
    ok("reconcile: privacy — a private Event Content folder is never titled or walked",
       "Private Dinner" not in blob and res["inventory"]["private_skipped"] == 2)
    ok("reconcile: privacy — a private post-event slug is skipped before its ledger is read", "Offsite Ledger" not in blob)
    ok("reconcile: privacy — email in a folder title is redacted", "jane.doe@example.com" not in blob and by("[redacted]"))
    ok("reconcile: privacy — phone in a folder title is redacted", "212-555-0147" not in blob and by("Call [redacted]"))
    ok("reconcile: privacy — no claim text and no email from the stubbed prod rows reach the output",
       "SECRET CLAIM TEXT" not in blob and "alice@corp.com" not in blob)
    ok("reconcile: privacy — output passes the email + phone assertion", not _raises(lambda: _assert_clean(blob)))
    m = res["summary"]["metrics"]
    ok("reconcile: attended_first_hand counts prod attended rows", m["attended_first_hand"] == [2, 5])
    ok("reconcile: research_claims_with_event", m["research_claims_with_event"] == [1, 7])
    ok("reconcile: report prints a baseline beside every gap and metric",
       all(("null: this run" in ln or "plan, 2026-11-10" in ln) for ln in render(res).splitlines()
           if any(ln.startswith(g) for g in GAP_TYPES) or any(ln.startswith(v) for v in METRIC_LABELS.values())))

    if checks:
        fail = sum(not g for _, g in checks)
        for name, good in checks:
            print(f"  {'✓' if good else '✗'} {name}")
        print(f"reconcile selftest: {len(checks) - fail}/{len(checks)} pass")
        return fail == 0
    return True


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
