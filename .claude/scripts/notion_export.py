#!/usr/bin/env python3
"""notion_export — headless Notion export of brief bodies for the knowledge-graph backfill (YED-384, plan B3).

Reads Content Drafts rows of Content Type `research_brief` / `post_event_brief` over the Notion REST API, renders each
page's blocks to markdown, and writes one folder per Event:

  .claude/.state/briefs/<YYYY-MM-DD>-<slug>[-<id8>]/{research_brief.md, post_event_brief.md, manifest.json}

manifest.json is the shape `substrate.py stage-research` / `stage-claims` already accept ({"event", "entities"}), plus a
`notion_export` block they ignore. `event.kind` is deliberately ABSENT: attendance is never inferred (ADR-10 D9), so
`ensure-event` refuses these manifests until the parent adds it. The export only records the signals (Event Status,
draft status, whether Alex commented) under `notion_export`.

  python3 .claude/scripts/notion_export.py backfill [--out DIR] [--limit N]
  python3 .claude/scripts/notion_export.py incremental [--since ISO] [--out DIR]   # default since = the watermark
  python3 .claude/scripts/notion_export.py --selftest                              # offline, fixture-driven

Read-only against Notion; no database writes anywhere. Token: NOTION_TOKEN from the process environment (never
printed, never written). Content Drafts DB: NOTION_DB_CONTENT_DRAFTS, else the (non-secret) id below.

Privacy (each layer is tested alone):
  * properties of type email / phone_number are never read (public_props);
  * every text unit (a block's joined plain text, a table cell, a title, an entity name) is checked on its PLAIN text
    by pii_normalize (raw + normalized copy) BEFORE any markdown is added; a hit replaces that unit with its redacted
    normalized plain text. Then the whole rendered body and manifest are scanned again; if that second scan still finds
    a contact the page FAILS CLOSED (nothing written, counted error_pii_scan, retried next run);
  * pages whose title reads private / off-record / OTR / confidential / Chatham House / not for publication / *.PRIVATE
    are skipped ("private equity" / "private markets" are not privacy markers);
  * bodies are scanned for off-the-record markers: counts land in `otr_flags` and `skip_staging: true` is set, for the
    stage verbs to refuse. A title regex is a stopgap: the real convention should be a Notion checkbox.
  * comment TEXT is never read into output, only whether a person user commented.

Comment-check cost: page-level comments first (1 request), then at most COMMENT_BLOCK_CAP (100) blocks, 1 request each,
stopping at the first comment by a person: worst case 101 requests (~34 s at 3 req/s) per post-event brief.
Notion's API returns unresolved comments only, so resolved feedback reads as False.
Watermark: advances only on a run with zero errors; failed page ids are recorded and retried first next run.
"""
from __future__ import annotations
import argparse, datetime, email.utils, http.client, json, os, re, subprocess, sys, tempfile, time, urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pii_normalize  # noqa: E402  (raw spine_client patterns + the normalized copy; one shared layer)
from substrate import event_slug  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
CONTENT_DRAFTS_DB = "4ed9088e-e967-4bae-b1a1-afa12556a61f"   # Content Drafts (database id; not a secret)
BRIEF_TYPES = ("research_brief", "post_event_brief")
OUT_DIR = os.path.join(ROOT, ".claude", ".state", "briefs")
WATERMARK = os.path.join(ROOT, ".claude", ".state", "notion-export.watermark.json")
FIXTURES = os.path.join(HERE, "fixtures", "notion_export", "api.json")
MIN_INTERVAL = 0.34                      # ~3 requests/s, Notion's documented average
RETRY_AFTER_CAP = 60.0
COMMENT_BLOCK_CAP = 100
PII_PROP_TYPES = ("email", "phone_number")
PRIVATE_RE = re.compile(
    r"\.PRIVATE\b|\bprivate\b(?!\s+(?:equity|markets?)\b)|off[\s-]*the[\s-]*record|\boff[\s-]+record\b|\bOTR\b"
    r"|\bconfidential\b|chatham\s+house|not\s+for\s+publication", re.I)
OTR_MARKERS = {
    "off_the_record": re.compile(r"off[\s-]*the[\s-]*record|\boff[\s-]+record\b", re.I),
    "otr": re.compile(r"\bOTR\b"),
    "chatham_house": re.compile(r"chatham\s+house", re.I),
    "not_for_publication": re.compile(r"not\s+for\s+publication", re.I),
    "confidential": re.compile(r"\bconfidential(?:ity)?\b", re.I),
    "stays_in_the_room": re.compile(r"stays?\s+in\s+the\s+room", re.I),
    "no_entry_sign": re.compile("⛔"),
}
ENTITY_PROPS = (("People", "person"), ("Companies", "company"), ("Topics", "topic"))
NO_CHILD_FETCH = ("child_page", "child_database")   # separate pages, not part of this body
MD_MARKS = re.compile(r"[*`~]")


class NotionError(Exception):
    def __init__(self, status: int, msg: str):
        super().__init__(f"Notion {status}: {msg}")
        self.status = status


class FailClosed(Exception):
    """The post-render PII scan disagreed with the per-unit scan: write nothing for this page."""


# ---------------------------------------------------------------------------------------------
# transport
# ---------------------------------------------------------------------------------------------
def retry_after(headers, n: int) -> float:
    """Retry-After as seconds (delta or HTTP-date), capped; exponential fallback."""
    v = headers.get("Retry-After") if headers else None
    s = None
    if v:
        try:
            s = float(v)
        except ValueError:
            try:
                s = (email.utils.parsedate_to_datetime(v) - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
            except (TypeError, ValueError):
                s = None
    return max(0.0, min(RETRY_AFTER_CAP, 2.0 ** n if s is None else s))


class Notion:
    """GET/POST with a ~3 req/s pacer; retries 429 / 5xx / connection errors / non-JSON 200s, no sleep after the
    last attempt."""

    def __init__(self, token: str, tries: int = 6):
        self._h = {"Authorization": f"Bearer {token}", "Notion-Version": NOTION_VERSION,
                   "Content-Type": "application/json"}
        self.tries, self.calls, self._last = tries, 0, 0.0

    def call(self, method: str, path: str, body: dict | None = None) -> dict:
        data = json.dumps(body).encode() if body is not None else None
        for n in range(self.tries):
            wait = self._last + MIN_INTERVAL - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            self.calls += 1
            try:
                r = urllib.request.Request(API + path, data=data, headers=self._h, method=method)
                with urllib.request.urlopen(r, timeout=60) as resp:
                    return json.loads(resp.read())
            except urllib.error.HTTPError as e:
                if not (e.code == 429 or e.code >= 500):
                    try:
                        msg = json.loads(e.read().decode()).get("code", "")
                    except Exception:
                        msg = ""
                    raise NotionError(e.code, msg or e.reason) from None
                delay = retry_after(e.headers, n)
            except (OSError, http.client.HTTPException, ValueError):   # resets, timeouts, RemoteDisconnected, bad JSON
                delay = min(RETRY_AFTER_CAP, 2.0 ** n)
            if n < self.tries - 1:
                time.sleep(delay)
        raise NotionError(0, f"gave up after {self.tries} tries: {method} {path.split('?')[0]}")


def paged(nc, method: str, path: str, body: dict | None = None):
    """Yield every result across Notion's cursor pagination."""
    cursor = None
    while True:
        if method == "POST":
            b = dict(body or {}, page_size=100, **({"start_cursor": cursor} if cursor else {}))
            r = nc.call("POST", path, b)
        else:
            sep = "&" if "?" in path else "?"
            r = nc.call("GET", path + (f"{sep}page_size=100" + (f"&start_cursor={cursor}" if cursor else "")))
        yield from r.get("results", [])
        if not r.get("has_more"):
            return
        cursor = r.get("next_cursor")


# ---------------------------------------------------------------------------------------------
# pure helpers (covered by --selftest)
# ---------------------------------------------------------------------------------------------
def safe_plain(s: str, hits: list) -> str | None:
    """None when the plain text is clean; else its redacted normalized plain text (markdown dropped for that unit)."""
    if not pii_normalize.has_pii(s or ""):
        return None
    out, n = pii_normalize.redact(s)
    if pii_normalize.has_pii(out):
        out, n = "[redacted]", max(n, 1)
    hits[0] += n
    return out


def clean_text(s: str, hits: list) -> str:
    """Plain strings for the manifest (titles, names)."""
    r = safe_plain(s, hits)
    return s if r is None else r


def public_props(page: dict) -> dict:
    """The page's properties minus every email / phone property. All property reads go through here."""
    return {k: v for k, v in (page.get("properties") or {}).items() if v.get("type") not in PII_PROP_TYPES}


def plain(rich: list) -> str:
    return "".join(t.get("plain_text", "") for t in rich or [])


def prop_title(page: dict) -> str:
    return next((plain(v["title"]) for v in public_props(page).values() if v.get("type") == "title"), "")


def prop_select(page: dict, name: str) -> str | None:
    v = public_props(page).get(name) or {}
    return ((v.get("select") or {}).get("name")) if v.get("type") == "select" else None


def prop_date(page: dict, name: str) -> str | None:
    v = public_props(page).get(name) or {}
    return ((v.get("date") or {}).get("start") or "")[:10] or None if v.get("type") == "date" else None


def is_private(title: str) -> bool:
    return bool(PRIVATE_RE.search(pii_normalize.normalize(title or "")))


def otr_flags(md: str) -> dict:
    n = pii_normalize.normalize(md)
    return {k: c for k, rx in OTR_MARKERS.items() if (c := len(rx.findall(n)))}


def rich_md(rich: list, hits: list) -> str:
    """Rich text -> markdown. The PII check runs on the JOINED plain text first: a contact split across runs
    ('**jane**' + '@fakeco.test') is caught before any markup can separate it."""
    red = safe_plain(plain(rich), hits)
    if red is not None:
        return red
    out = []
    for t in rich or []:
        s, a = t.get("plain_text", ""), t.get("annotations") or {}
        if s.strip():
            core = s.strip()
            if a.get("code"):
                core = f"`{core}`"
            if a.get("bold"):
                core = f"**{core}**"
            if a.get("italic"):
                core = f"*{core}*"
            if a.get("strikethrough"):
                core = f"~~{core}~~"
            href = t.get("href")
            if href and pii_normalize.has_pii(href):    # link targets are not in plain text: checked on their own
                href, hits[0] = None, hits[0] + 1    # (e.g. an invite URL carrying `%40`-encoded mail)
            if href:
                core = f"[{core}]({href})"
            s = s[:len(s) - len(s.lstrip())] + core + s[len(s.rstrip()):]
        out.append(s)
    return "".join(out)


def render(blocks: list, hits: list, depth: int = 0) -> list[str]:
    """Notion blocks (each may carry a pre-fetched `_children`) -> markdown lines. Line shapes match what
    substrate's parsers read: '## Heading', '- bullet', pipe tables, '**Label:**' bold."""
    pad, lines, num = "  " * depth, [], 0
    for b in blocks:
        t, body = b.get("type"), b.get(b.get("type"), {}) or {}
        kids = b.get("_children") or []
        text = rich_md(body.get("rich_text"), hits)
        num = num + 1 if t == "numbered_list_item" else 0
        child_depth = depth + 1
        if t and t.startswith("heading_"):
            lines += ["", "#" * int(t.split("_")[1]) + " " + text]
            child_depth = depth
        elif t == "paragraph":
            lines.append(pad + text)
        elif t in ("bulleted_list_item", "toggle"):
            lines.append(f"{pad}- {text}")
        elif t == "numbered_list_item":
            lines.append(f"{pad}{num}. {text}")
        elif t == "to_do":
            lines.append(f"{pad}- [{'x' if body.get('checked') else ' '}] {text}")
        elif t in ("quote", "callout"):
            lines.append(f"{pad}> {text}")
        elif t == "code":
            src = clean_text(plain(body.get("rich_text")), hits)
            lines += [f"{pad}```{body.get('language') or ''}", *[pad + ln for ln in src.split('\n')], f"{pad}```"]
        elif t == "divider":
            lines.append(pad + "---")
        elif t == "equation":
            lines.append(f"{pad}$${clean_text(body.get('expression', ''), hits)}$$")
        elif t in ("bookmark", "embed", "link_preview") and body.get("url"):
            lines.append(f"{pad}<{clean_text(body['url'], hits)}>")
        elif t == "child_page":
            lines.append(f"{pad}[child page: {clean_text(body.get('title', ''), hits)}]")
        elif t == "table":
            rows = [[rich_md(c, hits) for c in (r.get("table_row") or {}).get("cells", [])] for r in kids]
            for i, row in enumerate(rows):
                lines.append(pad + "| " + " | ".join(c.replace("|", "/") for c in row) + " |")
                if i == 0:
                    lines.append(pad + "|" + " --- |" * len(row))
            continue
        elif t in ("image", "file", "pdf", "video", "audio") and body.get("caption"):
            lines.append(f"{pad}[{t}: {rich_md(body['caption'], hits)}]")
        elif t in ("column_list", "column", "synced_block"):
            child_depth = depth                      # containers: children render in place
        if kids:
            lines += render(kids, hits, child_depth)
    return lines


def to_markdown(title: str, blocks: list, hits: list) -> str:
    md = "\n".join([f"# {clean_text(title, hits)}", *render(blocks, hits)]).strip() + "\n"
    return re.sub(r"\n{3,}", "\n\n", md)


def post_scan(*texts: str) -> None:
    """Second layer: the rendered output, with markdown marks stripped, must be contact-free. Fail closed if not."""
    for s in texts:
        if pii_normalize.has_pii(MD_MARKS.sub("", s)):
            raise FailClosed("rendered output still carries a contact after per-unit redaction")


def after(ts: str | None, since: str | None) -> bool:
    """last_edited_time strictly later than `since` (both ISO-8601; None since = everything)."""
    if not since:
        return True
    p = lambda s: datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
    return p(ts) > p(since)


def rank(entry: dict) -> tuple:
    """Which of two drafts of the same type for one event wins: non-archived first, then most recently edited."""
    return (entry.get("content_status") != "archived", entry.get("last_edited_time") or "")


def dedup(ids, *, drop=()) -> list:
    out = []
    for i in ids:
        if i and i not in out and i not in drop:
            out.append(i)
    return out


# ---------------------------------------------------------------------------------------------
# write guard
# ---------------------------------------------------------------------------------------------
def true_case(path: str) -> str:
    """Resolve symlinks, then the on-disk case of every existing component (APFS is case-insensitive: a
    case-changed path names the same directory and must get the same answer)."""
    p = os.path.realpath(path)
    parts, cur = p.split(os.sep)[1:], os.sep
    for i, part in enumerate(parts):
        try:
            hit = next((e for e in os.listdir(cur) if e.casefold() == part.casefold()), None)
        except OSError:
            hit = None
        if hit is None:
            return os.path.join(cur, *parts[i:])
        cur = os.path.join(cur, hit)
    return cur


def ensure_ignored(path: str) -> None:
    """Refuse to write into any git work tree unless git ignores the (real, true-cased) path."""
    p = true_case(path)
    probe = os.path.join(p, "manifest.json")
    anc = p
    while not os.path.isdir(anc):
        anc = os.path.dirname(anc)
    top = subprocess.run(["git", "-C", anc, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if top.returncode != 0:
        return                                       # not inside any work tree (e.g. a temp dir)
    if subprocess.run(["git", "-C", top.stdout.strip(), "check-ignore", "-q", probe]).returncode != 0:
        raise SystemExit(f"notion_export: {p} is inside a git work tree and not ignored; refusing to write")


# ---------------------------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------------------------
class Exporter:
    def __init__(self, nc, out_dir: str, db: str):
        self.nc, self.out, self.db = nc, out_dir, db
        self._pages: dict[str, dict] = {}
        self._persons: set[str] | None = None
        self._comments_ok = True                     # flips off on the first 403 (capability missing)
        self.stats: dict[str, int] = {}
        self.failed: list[str] = []
        self.done: set[str] = set()
        self.dirs: dict[str, str] = {}               # folder key -> folder name (in-run)

    def bump(self, k: str, n: int = 1):
        self.stats[k] = self.stats.get(k, 0) + n

    def page(self, pid: str) -> dict:
        if pid not in self._pages:
            self._pages[pid] = self.nc.call("GET", f"/pages/{pid}")
        return self._pages[pid]

    def children(self, bid: str) -> list:
        out = []
        for b in paged(self.nc, "GET", f"/blocks/{bid}/children"):
            if b.get("has_children") and b.get("type") not in NO_CHILD_FETCH:
                b["_children"] = self.children(b["id"])
            out.append(b)
        return out

    def relation_ids(self, page: dict, name: str) -> list[str]:
        v = public_props(page).get(name) or {}
        if v.get("type") != "relation":
            return []
        if not v.get("has_more"):                  # the page object caps relations at 25
            return [r["id"] for r in v.get("relation", [])]
        return [it["relation"]["id"] for it in
                paged(self.nc, "GET", f"/pages/{page['id']}/properties/{v['id']}") if it.get("type") == "relation"]

    def entities(self, event: dict, hits: list) -> list[dict]:
        out, seen = [], set()
        for prop, typ in ENTITY_PROPS:
            for rid in self.relation_ids(event, prop):
                if (typ, rid) in seen:
                    continue
                seen.add((typ, rid))
                try:
                    name = prop_title(self.page(rid)).strip()
                except NotionError:
                    self.bump(f"{typ}_unreadable")
                    continue
                if name:
                    out.append({"type": typ, "name": clean_text(name, hits), "notion_page_id": rid})
        return out

    def person_commented(self, page_id: str, blocks: list) -> tuple[bool | None, str]:
        """(Did a person user (the workspace has one: Alex) leave an open comment?, scan scope). Count-only: comment
        text is never kept. Page-level first, then up to COMMENT_BLOCK_CAP blocks. None = capability missing."""
        if not self._comments_ok:
            return None, "unavailable"

        def ids(bs):
            for b in bs:
                yield b["id"]
                yield from ids(b.get("_children") or [])
        try:
            if self._persons is None:
                self._persons = {u["id"] for u in paged(self.nc, "GET", "/users") if u.get("type") == "person"}
            hit = lambda bid: any((c.get("created_by") or {}).get("id") in self._persons
                                  for c in paged(self.nc, "GET", f"/comments?block_id={bid}"))
            if hit(page_id):
                return True, "page"
            all_ids = list(ids(blocks))
            for n, bid in enumerate(all_ids[:COMMENT_BLOCK_CAP], 1):
                if hit(bid):
                    return True, f"page+{n} blocks"
            return False, (f"page+{COMMENT_BLOCK_CAP} blocks (capped of {len(all_ids)})"
                           if len(all_ids) > COMMENT_BLOCK_CAP else f"page+{len(all_ids)} blocks")
        except NotionError as e:
            if e.status == 403:
                self._comments_ok = False
                sys.stderr.write("notion_export: users/comments API 403 — the integration lacks a capability; "
                                 "acknowledged_signal.alex_commented = null\n")
                return None, "unavailable"
            raise

    def drafts(self, since: str | None):
        flt = {"or": [{"property": "Content Type", "select": {"equals": t}} for t in BRIEF_TYPES]}
        if since:
            flt = {"and": [flt, {"timestamp": "last_edited_time", "last_edited_time": {"after": since}}]}
        for p in paged(self.nc, "POST", f"/databases/{self.db}/query", {"filter": flt}):
            if prop_select(p, "Content Type") in BRIEF_TYPES and after(p.get("last_edited_time"), since):
                yield p                              # re-checked client-side: the filter is the contract

    def folder(self, key: str, date: str | None, title: str) -> str:
        """Stable per event: a folder already holding a DIFFERENT event (this run or a previous one) is never
        merged into; the newcomer gets `<date>-<slug>-<id8>`."""
        if key not in self.dirs:
            base = f"{date or 'undated'}-{event_slug(title)[:60].strip('-') or 'untitled'}"
            mp = os.path.join(self.out, base, "manifest.json")
            owner = None
            if os.path.exists(mp):
                old = json.load(open(mp, encoding="utf-8"))
                owner = (old.get("notion_export") or {}).get("folder_key") or (old.get("event") or {}).get("notion_page_id")
            taken = any(v == base for k, v in self.dirs.items() if k != key) or (owner not in (None, key))
            self.dirs[key] = f"{base}-{key.replace('-', '')[:8]}" if taken else base
        return os.path.join(self.out, self.dirs[key])

    def export_one(self, d: dict) -> None:
        ctype, dtitle = prop_select(d, "Content Type"), prop_title(d)
        if is_private(dtitle):
            self.bump("skipped_private")
            return
        ev_ids = self.relation_ids(d, "Event")
        event = self.page(ev_ids[0]) if ev_ids else None
        etitle = prop_title(event) if event else dtitle
        if is_private(etitle):
            self.bump("skipped_private")
            return
        edate = (prop_date(event, "Event Date") if event else None) or prop_date(d, "Event Date")
        key = ev_ids[0] if ev_ids else d["id"]
        path = self.folder(key, edate, etitle)
        mpath = os.path.join(path, "manifest.json")
        old = json.load(open(mpath, encoding="utf-8")) if os.path.exists(mpath) else {}
        hits = [0]
        entry = {"page_id": d["id"], "brief_ref": f"notion:{d['id']}", "title": clean_text(dtitle, hits),
                 "content_status": prop_select(d, "Content Status"), "event_phase": prop_select(d, "Event Phase"),
                 "last_edited_time": d.get("last_edited_time"), "file": f"{ctype}.md"}
        prev = ((old.get("notion_export") or {}).get("briefs") or {}).get(ctype)
        if prev and prev["page_id"] != d["id"] and rank(prev) >= rank(entry):
            prev["also_in_notion"] = dedup([*prev.get("also_in_notion", []), d["id"]], drop=(prev["page_id"],))
            self.bump("duplicates_kept_older")
            self._write(path, old, None, None)
            return
        if prev and prev["page_id"] != d["id"]:
            entry["also_in_notion"] = dedup([prev["page_id"], *prev.get("also_in_notion", [])], drop=(d["id"],))
        elif prev and prev.get("also_in_notion"):
            entry["also_in_notion"] = dedup(prev["also_in_notion"], drop=(d["id"],))
        blocks = self.children(d["id"])
        body = to_markdown(dtitle, blocks, hits)
        flags = otr_flags(body)
        entry["otr_flags"] = flags
        if ctype == "post_event_brief":
            seen, scope = self.person_commented(d["id"], blocks)
            entry["acknowledged_signal"] = {"content_status": entry["content_status"], "alex_commented": seen,
                                            "comment_scan": scope}
        ents = self.entities(event, hits) if event else []
        entry["redactions"] = hits[0]
        briefs = {**((old.get("notion_export") or {}).get("briefs") or {}), ctype: entry}
        m = {"event": {k: v for k, v in {"notion_page_id": ev_ids[0] if ev_ids else None,
                                         "title": clean_text(etitle, hits), "event_date": edate}.items() if v},
             "entities": ents,
             "notion_export": {**(old.get("notion_export") or {}),
                               "folder_key": key,
                               "event_status": prop_select(event, "Event Status") if event else None,
                               "event_last_edited_time": (event or {}).get("last_edited_time"),
                               "exported_at": now_iso(),
                               "skip_staging": any(b.get("otr_flags") for b in briefs.values()),
                               "briefs": briefs}}
        if not ev_ids:
            m["notion_export"]["no_event_relation"] = True   # stage-research exits 5 on this manifest, by design
        post_scan(body, json.dumps(m, ensure_ascii=False))   # raises FailClosed: nothing below runs
        if not ev_ids:
            self.bump("no_event_relation")
        if flags:
            self.bump("otr_flagged")
            for k, c in flags.items():
                self.bump(f"otr_{k}", c)
        self.bump("redactions", hits[0])
        self._write(path, m, f"{ctype}.md", body)
        self.bump(ctype)

    @staticmethod
    def _write(path: str, manifest: dict, fname: str | None, body: str | None) -> None:
        ensure_ignored(path)
        os.makedirs(path, exist_ok=True)
        if fname:
            with open(os.path.join(path, fname), "w", encoding="utf-8") as f:
                f.write(body)
        with open(os.path.join(path, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=1, ensure_ascii=False)

    def _try(self, d: dict) -> None:
        self.done.add(d["id"])
        try:
            self.export_one(d)
        except NotionError as e:                      # one bad page never sinks the batch; it is counted + retried
            self.bump(f"error_{e.status}")
            self.failed.append(d["id"])
            sys.stderr.write(f"notion_export: {d['id']} failed: {e}\n")
        except FailClosed as e:
            self.bump("error_pii_scan")
            self.failed.append(d["id"])
            sys.stderr.write(f"notion_export: {d['id']} not written: {e}\n")

    def run(self, since: str | None, limit: int | None = None, retry=()) -> dict:
        for pid in retry:                             # last run's failures first, whatever their edit time
            try:
                d = self.nc.call("GET", f"/pages/{pid}")
            except NotionError as e:
                self.bump(f"error_{e.status}")
                self.failed.append(pid)
                continue
            if prop_select(d, "Content Type") in BRIEF_TYPES:
                self.bump("retried")
                self._try(d)
        for i, d in enumerate(self.drafts(since)):
            if limit is not None and i >= limit:
                break
            if d["id"] not in self.done:
                self._try(d)
        return self.stats


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def watermark_start(start: str) -> str:
    """Notion rounds last_edited_time to the minute: back the watermark off one minute so an edit landing in the
    same minute as this run is re-exported next time (an overwrite, harmless) instead of skipped."""
    t = datetime.datetime.fromisoformat(start.replace("Z", "+00:00")) - datetime.timedelta(minutes=1)
    return t.strftime("%Y-%m-%dT%H:%M:00.000Z")


def main_run(nc, mode: str, out: str, since: str | None, db: str, wm_path: str, limit: int | None = None) -> dict:
    ensure_ignored(out)
    ensure_ignored(os.path.dirname(wm_path))
    wm = json.load(open(wm_path, encoding="utf-8")) if os.path.exists(wm_path) else None
    if mode == "incremental" and not since:
        if wm is None:
            raise SystemExit("notion_export: no watermark yet — run `backfill` first or pass --since")
        since = wm.get("since")                      # None after a failed backfill: a full pass, which is safe
    start = now_iso()
    ex = Exporter(nc, out, db)
    stats = ex.run(since if mode == "incremental" else None, limit, retry=(wm or {}).get("failed", []))
    if limit is None:                                # a partial (--limit) run must not touch the watermark
        errors = sum(v for k, v in stats.items() if k.startswith("error_"))
        held = (wm or {}).get("since") if mode == "backfill" else since
        os.makedirs(os.path.dirname(wm_path), exist_ok=True)
        with open(wm_path, "w", encoding="utf-8") as f:
            json.dump({"since": held if errors else watermark_start(start), "advanced": not errors, "mode": mode,
                       "previous": since if mode == "incremental" else (wm or {}).get("since"),
                       "failed": dedup(ex.failed), "stats": stats}, f, indent=1)
    return stats


# ---------------------------------------------------------------------------------------------
# selftest (offline: fixture JSON stands in for the API)
# ---------------------------------------------------------------------------------------------
class FakeNotion:
    def __init__(self, path: str = FIXTURES):
        self.api, self.calls = json.load(open(path, encoding="utf-8")), []

    def call(self, method: str, path: str, body: dict | None = None) -> dict:
        path = re.sub(r"[?&]page_size=\d+", "", path)
        if body and body.get("start_cursor"):
            path += f"?start_cursor={body['start_cursor']}"
        path = re.sub(r"^([^?]*)&", r"\1?", path)
        self.calls.append(f"{method} {path}")
        if f"{method} {path}" not in self.api:
            raise NotionError(404, f"fixture missing: {method} {path}")
        return json.loads(json.dumps(self.api[f"{method} {path}"]))


EV = "eeeeeeee-0000-0000-0000-000000000001"
P1, P2, P5, P7 = (f"aaaaaaaa-0000-0000-0000-00000000000{i}" for i in (1, 2, 5, 7))
SUMMIT = "2026-10-02-fake-summit-agents-edition"


def selftest() -> bool:
    fails = []

    def ok(name, cond):
        print(("PASS " if cond else "FAIL ") + name)
        if not cond:
            fails.append(name)

    ok("pii_normalize selftest", _quiet(pii_normalize.selftest))
    page = {"properties": {"T": {"type": "title", "title": []}, "E": {"type": "email", "email": "x@y.test"},
                           "P": {"type": "phone_number", "phone_number": "212-555-0100"}}}
    ok("public_props drops email + phone_number properties", list(public_props(page)) == ["T"])
    ok("private: off-record / OTR / confidential / Chatham House / not for publication / *.PRIVATE", all(map(is_private, (
        "Off-record founder dinner", "notes.PRIVATE", "Private dinner", "off the record AMA", "OTR: roundtable",
        "Confidential briefing", "Chatham House session", "offtherecord chat", "Not for publication — notes",
        "Off–the–record supper"))))
    ok("private: 'private equity' / 'private markets' / ordinary titles pass", not any(map(is_private, (
        "Privacy engineering meetup", "Research brief — X", "Private equity in AI", "Private markets summit"))))
    ok("otr_flags: counts markers in a body", otr_flags("x. This is off the record. OTR again. ⛔ note") ==
       {"off_the_record": 1, "otr": 1, "no_entry_sign": 1} and otr_flags("plain body") == {})
    ok("after(): strict, ISO with Z", after("2026-11-05T10:00:00.000Z", "2026-11-05T09:59:00.000Z")
       and not after("2026-11-05T10:00:00.000Z", "2026-11-05T10:00:00.000Z") and after("2026-01-01T00:00:00Z", None))
    ok("watermark backs off one minute", watermark_start("2026-11-11T10:00:30.000Z") == "2026-11-11T09:59:00.000Z")
    ok("rank: non-archived beats newer archived",
       rank({"content_status": "needs_review", "last_edited_time": "2026-01-01"}) >
       rank({"content_status": "archived", "last_edited_time": "2026-12-01"}))

    # fix 2: a contact split across rich-text runs is redacted on the joined plain text
    def rt(s, **a):
        return {"plain_text": s, "annotations": a, "href": None}
    h = [0]
    split = [rich_md([rt("jane", bold=True), rt("@fakeco.test")], h),
             rich_md([rt("call 212-555-"), rt("0100", bold=True)], h)]
    ok("render: split contacts ('**jane**@…', '212-555-**0100**') redacted before markup",
       all("[redacted]" in s and not pii_normalize.has_pii(MD_MARKS.sub("", s)) for s in split) and h[0] == 2)
    ok("render: clean runs keep their markdown", rich_md([rt("Pat", bold=True), rt(" spoke")], [0]) == "**Pat** spoke")
    h = [0]
    linked = rich_md([{"plain_text": "invite", "annotations": {}, "href": "https://cal.fakeco.test/e?cid=dana%40fakeco.test"},
                      {"plain_text": " and ", "annotations": {}, "href": None},
                      {"plain_text": "site", "annotations": {}, "href": "https://fakeco.test/p/1"}], h)
    ok("render: a link target carrying a contact is dropped, the text and clean links kept",
       linked == "invite and [site](https://fakeco.test/p/1)" and h[0] == 1)
    try:
        post_scan("clean line", "pat@fakeco.test")
        ok("post_scan fails closed on a surviving contact", False)
    except FailClosed:
        ok("post_scan fails closed on a surviving contact", True)

    # fix 8: backoff (capped Retry-After, HTTP-date form, no sleep after the last try, resets + bad JSON retried)
    import io
    real_open, real_sleep, real_iv = urllib.request.urlopen, time.sleep, globals()["MIN_INTERVAL"]
    slept = []

    def script(*steps):
        it = iter(steps)

        def fake_open(r, timeout=0):
            s = next(it)
            if isinstance(s, BaseException):
                raise s
            return io.BytesIO(s)
        return fake_open

    def e429(v):
        return urllib.error.HTTPError("u", 429, "rate", {"Retry-After": v}, io.BytesIO(b"{}"))
    globals()["MIN_INTERVAL"] = 0
    time.sleep = slept.append
    try:
        urllib.request.urlopen = script(e429("3600"), http.client.RemoteDisconnected("x"), b"<html>not json")
        try:
            Notion("fixture-token", tries=3).call("GET", "/users")
            gave_up = False
        except NotionError:
            gave_up = True
        ok("backoff: Retry-After capped at 60, no sleep after the final attempt", gave_up and slept == [60.0, 2.0])
        slept.clear()
        future = email.utils.format_datetime(datetime.datetime.now(datetime.timezone.utc)
                                             + datetime.timedelta(seconds=30), usegmt=True)
        urllib.request.urlopen = script(e429(future), ConnectionResetError("r"), OSError("o"), b"not json", b'{"ok": 1}')
        nc = Notion("fixture-token", tries=5)
        ok("backoff: HTTP-date Retry-After, resets, OSError, non-JSON 200 all retried",
           nc.call("GET", "/users") == {"ok": 1} and nc.calls == 5 and 0 < slept[0] <= 30)
    finally:
        urllib.request.urlopen, time.sleep, globals()["MIN_INTERVAL"] = real_open, real_sleep, real_iv

    with tempfile.TemporaryDirectory() as tmp:
        out, wm = os.path.join(tmp, "briefs"), os.path.join(tmp, "wm", "notion-export.watermark.json")
        fake = FakeNotion()
        stats = main_run(fake, "backfill", out, None, "fake-db", wm)
        dirs = sorted(os.listdir(out))
        ok("backfill: one folder per event; private / OTR / Chatham / off-type drafts skipped; 'private equity' kept",
           dirs == ["2026-09-01-private-equity-in-ai-research-brief", "2026-09-01-research-brief-second-fake-meetup",
                    SUMMIT] and stats.get("skipped_private") == 4)
        ok("stats: 3 research, 1 post-event, 1 duplicate kept older", stats.get("research_brief") == 3
           and stats.get("post_event_brief") == 1 and stats.get("duplicates_kept_older") == 1)
        ev = os.path.join(out, SUMMIT)
        rb = open(os.path.join(ev, "research_brief.md"), encoding="utf-8").read()
        pb = open(os.path.join(ev, "post_event_brief.md"), encoding="utf-8").read()
        m = json.load(open(os.path.join(ev, "manifest.json"), encoding="utf-8"))
        allout = rb + pb + json.dumps(m, ensure_ascii=False)
        ok("render: heading, ledger bullet, nested bullet, h4, pipe table, divider",
           "## Evidence Ledger — Fakeco" in rb and "- claim: Fakeco raised $5M seed | tier: web-verified" in rb
           and "  - nested detail" in rb and "#### Stat Bank" in rb and "| Metric | Value |" in rb
           and "| ARR | $2M |" in rb and "\n---" in rb)
        ok("render: bold, link, inline code", "**Pat** spoke" in rb and "[site](https://fakeco.test)" in rb
           and "`eval()`" in rb)
        ok("redaction: no fixture contact in any form survives (split, [at], &#64;, %40, zero-width, dashes, "
           "bare digits, spaced)", not pii_normalize.has_pii(MD_MARKS.sub("", allout))
           and not any(s in allout for s in ("jane", "dana", "212-555", "2125550188", "fakeco [dot]")))
        ok("redaction: URL and id digit runs survive", "https://fakeco.test/p/12345678901" in rb
           and "aaaaaaaa000000000000000000000001" in rb)
        ok("manifest: stage-research shape (event + entities, names only, no kind)",
           m["event"] == {"notion_page_id": EV, "title": "Fake Summit: Agents Edition", "event_date": "2026-10-02"}
           and [(e["type"], e["name"]) for e in m["entities"]] ==
           [("person", "Pat Placeholder"), ("company", "Fakeco"), ("topic", "Agent Evals")]
           and all(set(e) == {"type", "name", "notion_page_id"} for e in m["entities"]))
        ok("manifest: has_more relation paged via property endpoint, deduped",
           sum(e["type"] == "topic" for e in m["entities"]) == 1
           and f"GET /pages/{EV}/properties/tp%3D?start_cursor=t2" in fake.calls)
        b = m["notion_export"]["briefs"]
        ok("manifest: both briefs, status + last_edited_time + brief_ref",
           b["research_brief"]["content_status"] == "needs_review"
           and b["post_event_brief"]["last_edited_time"] == "2026-11-05T10:00:00.000Z"
           and b["post_event_brief"]["brief_ref"] == f"notion:{P2}" and m["notion_export"]["event_status"] == "attended")
        ok("otr: post-event body marker -> otr_flags + skip_staging", b["post_event_brief"]["otr_flags"] ==
           {"off_the_record": 1} and b["research_brief"]["otr_flags"] == {} and m["notion_export"]["skip_staging"] is True)
        ok("acknowledged_signal: person comment (count only, stops at first hit)",
           b["post_event_brief"]["acknowledged_signal"] == {"content_status": "approved", "alex_commented": True,
                                                            "comment_scan": "page+2 blocks"}
           and "FIXTURE COMMENT TEXT" not in allout and "GET /comments?block_id=b2-td" not in fake.calls)
        ok("research brief carries no acknowledged_signal", "acknowledged_signal" not in b["research_brief"])
        nm = json.load(open(os.path.join(out, "2026-09-01-research-brief-second-fake-meetup", "manifest.json"),
                            encoding="utf-8"))
        ok("no Event relation -> flagged, no notion_page_id", nm["notion_export"].get("no_event_relation") is True
           and "notion_page_id" not in nm["event"])
        w = json.load(open(wm, encoding="utf-8"))
        ok("watermark advanced after a clean backfill", w["advanced"] and w["since"].endswith(":00.000Z")
           and w["failed"] == [])

        # fix 10: a second run over the same folder does not duplicate also_in_notion
        main_run(FakeNotion(), "backfill", out, None, "fake-db", wm)
        b2 = json.load(open(os.path.join(ev, "manifest.json"), encoding="utf-8"))["notion_export"]["briefs"]
        ok("also_in_notion: deduped across runs", b2["research_brief"].get("also_in_notion") == [P7])

        # incremental: only drafts edited after `since`; existing manifest entries for the other type survive
        fake2 = FakeNotion()
        s2 = main_run(fake2, "incremental", out, "2026-10-15T00:00:00.000Z", "fake-db", wm)
        m2 = json.load(open(os.path.join(ev, "manifest.json"), encoding="utf-8"))
        ok("incremental: only the post-event brief re-exported", s2.get("post_event_brief") == 1
           and not s2.get("research_brief") and f"GET /blocks/{P1}/children" not in fake2.calls)
        ok("incremental: research entry kept in the merged manifest", set(m2["notion_export"]["briefs"]) ==
           {"research_brief", "post_event_brief"})

        # fix 6: a folder holding a DIFFERENT event (previous run) is never merged into
        out6 = os.path.join(tmp, "b6")
        os.makedirs(os.path.join(out6, SUMMIT))
        json.dump({"event": {"notion_page_id": "ffffffff-0000-0000-0000-000000000009"},
                   "notion_export": {"briefs": {}}}, open(os.path.join(out6, SUMMIT, "manifest.json"), "w"))
        main_run(FakeNotion(), "backfill", out6, None, "fake-db", os.path.join(tmp, "wm6.json"))
        ok("same date + title, different event -> id-suffixed folder; the other folder untouched",
           os.path.exists(os.path.join(out6, SUMMIT + "-eeeeeeee", "research_brief.md"))
           and not os.path.exists(os.path.join(out6, SUMMIT, "research_brief.md")))

        # fix 5: a failure holds the watermark, records the id, and is retried first next run
        class FlakyOnce(FakeNotion):
            broken = True

            def call(self, method, path, body=None):
                if FlakyOnce.broken and path.startswith(f"/blocks/{P5}/children"):
                    raise NotionError(502, "bad gateway")
                return super().call(method, path, body)
        wm5 = os.path.join(tmp, "wm5.json")
        json.dump({"since": "2026-08-01T00:00:00.000Z", "failed": []}, open(wm5, "w"))
        s5 = main_run(FlakyOnce(), "incremental", os.path.join(tmp, "b5"), None, "fake-db", wm5)
        w5 = json.load(open(wm5))
        ok("failure: watermark NOT advanced, failed id recorded", s5.get("error_502") == 1
           and w5["since"] == "2026-08-01T00:00:00.000Z" and not w5["advanced"] and w5["failed"] == [P5])
        FlakyOnce.broken = False
        json.dump({**w5, "since": "2026-10-20T00:00:00.000Z"}, open(wm5, "w"))   # P5's edit time is now older
        f5 = FlakyOnce()
        s5b = main_run(f5, "incremental", os.path.join(tmp, "b5"), None, "fake-db", wm5)
        w5b = json.load(open(wm5))
        ok("failure: retried first next run (edit time older than since), then watermark advances",
           f5.calls[0] == f"GET /pages/{P5}" and s5b.get("retried") == 1 and s5b.get("research_brief") == 1
           and w5b["advanced"] and w5b["failed"] == [])

        # fix 7: a 403 on /users still exports the post-event brief, alex_commented = None
        class NoUsers(FakeNotion):
            def call(self, method, path, body=None):
                if path.startswith("/users"):
                    raise NotionError(403, "restricted_resource")
                return super().call(method, path, body)
        out7 = os.path.join(tmp, "b7")
        s7 = main_run(NoUsers(), "backfill", out7, None, "fake-db", os.path.join(tmp, "wm7.json"))
        a7 = json.load(open(os.path.join(out7, SUMMIT, "manifest.json")))["notion_export"]["briefs"]["post_event_brief"]
        ok("users 403 -> post-event brief still exported, alex_commented None", s7.get("post_event_brief") == 1
           and a7["acknowledged_signal"]["alex_commented"] is None and not any(k.startswith("error_") for k in s7))

        # fix 9: comment scan = page first, then at most COMMENT_BLOCK_CAP blocks
        class Quiet(FakeNotion):
            def call(self, method, path, body=None):
                self.calls.append(path)
                return {"results": [{"id": "u-alex", "type": "person"}]} if path.startswith("/users") else {"results": []}
        nq = Quiet()
        seen, scope = Exporter(nq, tmp, "fake-db").person_commented("pg", [{"id": f"b{i}"} for i in range(150)])
        ncom = [c for c in nq.calls if c.startswith("/comments")]
        ok("comment scan: page first, capped at 100 blocks", seen is False and len(ncom) == 101
           and ncom[0].startswith("/comments?block_id=pg") and "capped of 150" in scope)

    # fix 1: the write guard resolves symlinks and case, and covers every git work tree
    with tempfile.TemporaryDirectory() as tmp:
        link = os.path.join(tmp, "link")
        os.symlink(os.path.join(ROOT, ".claude", "scripts"), link)
        ok("guard: symlink into a tracked repo dir refused", _refuses(link))
        ok("guard: case-changed path into the repo refused", _refuses(ROOT.swapcase() + "/.claude/SCRIPTS"))
        repo = os.path.join(tmp, "other")
        os.makedirs(repo)
        subprocess.run(["git", "init", "-q", repo], check=True)
        ok("guard: any git work tree, not just this repo", _refuses(os.path.join(repo, "out")))
        ok("guard: ignored .state path allowed", not _refuses(os.path.join(ROOT, ".claude", ".state", "briefs")))
        ok("guard: a plain temp dir allowed", not _refuses(os.path.join(tmp, "plain")))
    ok("guard: tracked path refused", _refuses(os.path.join(ROOT, ".claude", "scripts")))
    print(f"\n{'OK' if not fails else 'FAILED'}: {len(fails)} failure(s)")
    return not fails


def _quiet(fn) -> bool:
    import contextlib, io
    with contextlib.redirect_stdout(io.StringIO()):
        return fn()


def _refuses(path: str) -> bool:
    try:
        ensure_ignored(path)
        return False
    except SystemExit:
        return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("mode", nargs="?", choices=["backfill", "incremental"])
    ap.add_argument("--since", help="(incremental) ISO-8601; default = the watermark file")
    ap.add_argument("--out", default=OUT_DIR)
    ap.add_argument("--limit", type=int, help="export at most N drafts (smoke test; does not touch the watermark)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return 0 if selftest() else 1
    if not a.mode:
        ap.error("mode required (backfill | incremental) or --selftest")
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        raise SystemExit("notion_export: NOTION_TOKEN is not set in the environment (it is read from the process "
                         "environment only; the pipeline .env does not carry it yet)")
    nc = Notion(token)
    stats = main_run(nc, a.mode, a.out, a.since, os.environ.get("NOTION_DB_CONTENT_DRAFTS") or CONTENT_DRAFTS_DB,
                     WATERMARK, a.limit)
    print(json.dumps({"mode": a.mode, "requests": nc.calls, **stats}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
