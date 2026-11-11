#!/usr/bin/env python3
"""notion_export — headless Notion export of brief bodies for the knowledge-graph backfill (YED-384, plan B3).

Reads Content Drafts rows of Content Type `research_brief` / `post_event_brief` over the Notion REST API, renders each
page's blocks to markdown, and writes one folder per Event:

  .claude/.state/briefs/<YYYY-MM-DD>-<slug>/{research_brief.md, post_event_brief.md, manifest.json}

manifest.json is the shape `substrate.py stage-research` / `stage-claims` already accept ({"event", "entities"}), plus a
`notion_export` block they ignore. `event.kind` is deliberately ABSENT: attendance is never inferred (ADR-10 D9), so
`ensure-event` refuses these manifests until the parent adds it. The export only records the signals (Event Status,
draft status, whether Alex commented) under `notion_export`.

  python3 .claude/scripts/notion_export.py backfill [--out DIR] [--limit N]
  python3 .claude/scripts/notion_export.py incremental [--since ISO] [--out DIR]   # default since = the watermark
  python3 .claude/scripts/notion_export.py --selftest                              # offline, fixture-driven

Read-only against Notion; no database writes anywhere. Token: NOTION_TOKEN from the process environment (never
printed, never written). Content Drafts DB: NOTION_DB_CONTENT_DRAFTS, else the id below.
Privacy: properties of type email / phone_number are never read; every string written (bodies, titles, names) goes
through spine_client's EMAIL_RE / PHONE_RE -> `[redacted]`; pages titled private / off-record / *.PRIVATE are
skipped; comment TEXT is never read into output (only a yes/no on whether a person user commented).
"""
from __future__ import annotations
import argparse, datetime, json, os, re, subprocess, sys, tempfile, time, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from spine_client import EMAIL_RE, PHONE_RE  # noqa: E402  (one copy of the PII patterns, ADR-9)
from substrate import event_slug  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
CONTENT_DRAFTS_DB = "4ed9088e-e967-4bae-b1a1-afa12556a61f"   # Content Drafts (database id; CLAUDE.md §3 has the collection id)
BRIEF_TYPES = ("research_brief", "post_event_brief")
OUT_DIR = os.path.join(ROOT, ".claude", ".state", "briefs")
WATERMARK = os.path.join(ROOT, ".claude", ".state", "notion-export.watermark.json")
FIXTURES = os.path.join(HERE, "fixtures", "notion_export", "api.json")
MIN_INTERVAL = 0.34                      # ~3 requests/s, Notion's documented average
PII_PROP_TYPES = ("email", "phone_number")
PRIVATE_RE = re.compile(r"\.PRIVATE\b|\bprivate\b|off[- ]the[- ]record|\boff[- ]record\b", re.I)
ENTITY_PROPS = (("People", "person"), ("Companies", "company"), ("Topics", "topic"))
NO_CHILD_FETCH = ("child_page", "child_database")   # separate pages, not part of this body


class NotionError(Exception):
    def __init__(self, status: int, msg: str):
        super().__init__(f"Notion {status}: {msg}")
        self.status = status


# ---------------------------------------------------------------------------------------------
# transport
# ---------------------------------------------------------------------------------------------
class Notion:
    """GET/POST with a ~3 req/s pacer and backoff on 429 / 5xx / network errors (honours Retry-After)."""

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
                    return json.load(resp)
            except urllib.error.HTTPError as e:
                if e.code == 429 or e.code >= 500:
                    time.sleep(float(e.headers.get("Retry-After") or 2 ** n))
                    continue
                try:
                    msg = json.loads(e.read().decode()).get("code", "")
                except Exception:
                    msg = ""
                raise NotionError(e.code, msg or e.reason) from None
            except (urllib.error.URLError, TimeoutError):
                time.sleep(2 ** n)
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
def redact(s: str) -> tuple[str, int]:
    """spine_client's EMAIL_RE / PHONE_RE -> '[redacted]'. Returns (text, matches)."""
    s, a = EMAIL_RE.subn("[redacted]", s or "")
    s, b = PHONE_RE.subn("[redacted]", s)
    return s, a + b


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
    return bool(PRIVATE_RE.search(title or ""))


def rich_md(rich: list) -> str:
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
            if t.get("href"):
                core = f"[{core}]({t['href']})"
            s = s[:len(s) - len(s.lstrip())] + core + s[len(s.rstrip()):]
        out.append(s)
    return "".join(out)


def render(blocks: list, depth: int = 0) -> list[str]:
    """Notion blocks (each may carry a pre-fetched `_children`) -> markdown lines. Line shapes match what
    substrate's parsers read: '## Heading', '- bullet', pipe tables, '**Label:**' bold."""
    pad, lines, num = "  " * depth, [], 0
    for b in blocks:
        t, body = b.get("type"), b.get(b.get("type"), {}) or {}
        kids = b.get("_children") or []
        text = rich_md(body.get("rich_text"))
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
            lines += [f"{pad}```{body.get('language') or ''}", *[pad + ln for ln in plain(body.get('rich_text')).split('\n')],
                      f"{pad}```"]
        elif t == "divider":
            lines.append(pad + "---")
        elif t == "equation":
            lines.append(f"{pad}$${body.get('expression', '')}$$")
        elif t in ("bookmark", "embed", "link_preview") and body.get("url"):
            lines.append(f"{pad}<{body['url']}>")
        elif t == "child_page":
            lines.append(f"{pad}[child page: {body.get('title', '')}]")
        elif t == "table":
            rows = [[rich_md(c) for c in (r.get("table_row") or {}).get("cells", [])] for r in kids]
            for i, row in enumerate(rows):
                lines.append(pad + "| " + " | ".join(c.replace("|", "/") for c in row) + " |")
                if i == 0:
                    lines.append(pad + "|" + " --- |" * len(row))
            continue
        elif t in ("image", "file", "pdf", "video", "audio") and body.get("caption"):
            lines.append(f"{pad}[{t}: {rich_md(body['caption'])}]")
        elif t in ("column_list", "column", "synced_block"):
            child_depth = depth                      # containers: children render in place
        if kids:
            lines += render(kids, child_depth)
    return lines


def to_markdown(title: str, blocks: list) -> str:
    md = "\n".join([f"# {title}", *render(blocks)]).strip() + "\n"
    return re.sub(r"\n{3,}", "\n\n", md)


def after(ts: str | None, since: str | None) -> bool:
    """last_edited_time strictly later than `since` (both ISO-8601; None since = everything)."""
    if not since:
        return True
    p = lambda s: datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
    return p(ts) > p(since)


def rank(entry: dict) -> tuple:
    """Which of two drafts of the same type for one event wins: non-archived first, then most recently edited."""
    return (entry.get("content_status") != "archived", entry.get("last_edited_time") or "")


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
        self.dirs: dict[str, str] = {}               # event key -> folder (in-run collision guard)

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

    def entities(self, event: dict) -> list[dict]:
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
                    out.append({"type": typ, "name": redact(name)[0], "notion_page_id": rid})
        return out

    def persons(self) -> set[str]:
        if self._persons is None:
            self._persons = {u["id"] for u in paged(self.nc, "GET", "/users") if u.get("type") == "person"}
        return self._persons

    def person_commented(self, page_id: str, blocks: list) -> bool | None:
        """Did a person user (the workspace has one: Alex) leave an open comment on the page or any block?
        Count-only: comment text is never kept. None = the integration lacks the read-comments capability.
        Notion's API returns UNRESOLVED comments only, so resolved feedback reads as False."""
        if not self._comments_ok:
            return None
        people = self.persons()

        def ids(bs):
            for b in bs:
                yield b["id"]
                yield from ids(b.get("_children") or [])
        try:
            for bid in [page_id, *ids(blocks)]:
                if any((c.get("created_by") or {}).get("id") in people
                       for c in paged(self.nc, "GET", f"/comments?block_id={bid}")):
                    return True
            return False
        except NotionError as e:
            if e.status == 403:
                self._comments_ok = False
                sys.stderr.write("notion_export: comments API 403 — the integration lacks 'Read comments'; "
                                 "acknowledged_signal.alex_commented = null\n")
                return None
            raise

    def drafts(self, since: str | None):
        flt = {"or": [{"property": "Content Type", "select": {"equals": t}} for t in BRIEF_TYPES]}
        if since:
            flt = {"and": [flt, {"timestamp": "last_edited_time", "last_edited_time": {"after": since}}]}
        for p in paged(self.nc, "POST", f"/databases/{self.db}/query", {"filter": flt}):
            if prop_select(p, "Content Type") in BRIEF_TYPES and after(p.get("last_edited_time"), since):
                yield p                              # re-checked client-side: the filter is the contract

    def folder(self, key: str, date: str | None, title: str) -> str:
        if key not in self.dirs:
            base = f"{date or 'undated'}-{event_slug(title)[:60].strip('-') or 'untitled'}"
            name = base if base not in self.dirs.values() else f"{base}-{key.replace('-', '')[:6]}"
            self.dirs[key] = name
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
        path = self.folder(ev_ids[0] if ev_ids else d["id"], edate, etitle)
        mpath = os.path.join(path, "manifest.json")
        old = json.load(open(mpath, encoding="utf-8")) if os.path.exists(mpath) else {}
        entry = {"page_id": d["id"], "brief_ref": f"notion:{d['id']}", "title": redact(dtitle)[0],
                 "content_status": prop_select(d, "Content Status"), "event_phase": prop_select(d, "Event Phase"),
                 "last_edited_time": d.get("last_edited_time"), "file": f"{ctype}.md"}
        prev = ((old.get("notion_export") or {}).get("briefs") or {}).get(ctype)
        if prev and prev["page_id"] != d["id"] and rank(prev) >= rank(entry):
            prev.setdefault("also_in_notion", []).append(d["id"])   # a duplicate draft: keep the winner, name the loser
            self.bump("duplicates_kept_older")
            self._write(path, old, None, None)
            return
        if prev and prev["page_id"] != d["id"]:
            entry["also_in_notion"] = [prev["page_id"], *prev.get("also_in_notion", [])]
        blocks = self.children(d["id"])
        body, hits = redact(to_markdown(dtitle, blocks))
        entry["redactions"] = hits
        self.bump("redactions", hits)
        if ctype == "post_event_brief":
            entry["acknowledged_signal"] = {"content_status": entry["content_status"],
                                            "alex_commented": self.person_commented(d["id"], blocks)}
        ents = self.entities(event) if event else []
        m = {"event": {k: v for k, v in {"notion_page_id": ev_ids[0] if ev_ids else None,
                                         "title": redact(etitle)[0], "event_date": edate}.items() if v},
             "entities": ents,
             "notion_export": {**(old.get("notion_export") or {}),
                               "event_status": prop_select(event, "Event Status") if event else None,
                               "event_last_edited_time": (event or {}).get("last_edited_time"),
                               "exported_at": now_iso(),
                               "briefs": {**((old.get("notion_export") or {}).get("briefs") or {}), ctype: entry}}}
        if not ev_ids:
            m["notion_export"]["no_event_relation"] = True   # stage-research exits 5 on this manifest, by design
            self.bump("no_event_relation")
        self._write(path, m, f"{ctype}.md", body)
        self.bump(ctype)

    @staticmethod
    def _write(path: str, manifest: dict, fname: str | None, body: str | None) -> None:
        os.makedirs(path, exist_ok=True)
        if fname:
            with open(os.path.join(path, fname), "w", encoding="utf-8") as f:
                f.write(body)
        with open(os.path.join(path, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=1, ensure_ascii=False)

    def run(self, since: str | None, limit: int | None = None) -> dict:
        for i, d in enumerate(self.drafts(since)):
            if limit is not None and i >= limit:
                break
            try:
                self.export_one(d)
            except NotionError as e:                  # one bad page never sinks the batch; it is counted
                self.bump(f"error_{e.status}")
                sys.stderr.write(f"notion_export: {d['id']} failed: {e}\n")
        return self.stats


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def ensure_ignored(path: str) -> None:
    """Refuse to write inside the repo unless git ignores the path (bodies are private working files)."""
    p = os.path.abspath(path)
    if not p.startswith(ROOT + os.sep):
        return
    probe = os.path.join(p, "manifest.json")
    if subprocess.run(["git", "-C", ROOT, "check-ignore", "-q", probe]).returncode != 0:
        raise SystemExit(f"notion_export: {os.path.relpath(p, ROOT)} is not gitignored; refusing to write")


def watermark_start(start: str) -> str:
    """Notion rounds last_edited_time to the minute: back the watermark off one minute so an edit landing in the
    same minute as this run is re-exported next time (an overwrite, harmless) instead of skipped."""
    t = datetime.datetime.fromisoformat(start.replace("Z", "+00:00")) - datetime.timedelta(minutes=1)
    return t.strftime("%Y-%m-%dT%H:%M:00.000Z")


def main_run(nc, mode: str, out: str, since: str | None, db: str, wm_path: str, limit: int | None = None) -> dict:
    ensure_ignored(out)
    ensure_ignored(os.path.dirname(wm_path))
    if mode == "incremental" and not since:
        if not os.path.exists(wm_path):
            raise SystemExit("notion_export: no watermark yet — run `backfill` first or pass --since")
        since = json.load(open(wm_path, encoding="utf-8"))["since"]
    start = now_iso()
    ex = Exporter(nc, out, db)
    stats = ex.run(since if mode == "incremental" else None, limit)
    if limit is None:                                # a partial (--limit) run must not advance the watermark
        os.makedirs(os.path.dirname(wm_path), exist_ok=True)
        with open(wm_path, "w", encoding="utf-8") as f:
            json.dump({"since": watermark_start(start), "mode": mode, "previous": since, "stats": stats}, f, indent=1)
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


def selftest() -> bool:
    fails = []

    def ok(name, cond):
        print(("PASS " if cond else "FAIL ") + name)
        if not cond:
            fails.append(name)

    # pure helpers
    ok("redact: email + phone -> [redacted], counted",
       redact("mail a.b@fakeco.test or call 212-555-0100 now") == ("mail [redacted] or call [redacted] now", 2))
    ok("redact: prose numbers survive", redact("raised $5M in 2026, 3x growth")[1] == 0)
    page = {"properties": {"T": {"type": "title", "title": []}, "E": {"type": "email", "email": "x@y.test"},
                           "P": {"type": "phone_number", "phone_number": "212-555-0100"}}}
    ok("public_props drops email + phone_number properties", list(public_props(page)) == ["T"])
    ok("private: off-record / *.PRIVATE / private titles", all(map(is_private, (
        "Off-record founder dinner", "notes.PRIVATE", "Private dinner", "off the record AMA"))))
    ok("private: ordinary titles pass", not any(map(is_private, ("Privacy engineering meetup", "Research brief — X"))))
    ok("after(): strict, ISO with Z", after("2026-11-05T10:00:00.000Z", "2026-11-05T09:59:00.000Z")
       and not after("2026-11-05T10:00:00.000Z", "2026-11-05T10:00:00.000Z") and after("2026-01-01T00:00:00Z", None))
    ok("watermark backs off one minute", watermark_start("2026-11-11T10:00:30.000Z") == "2026-11-11T09:59:00.000Z")
    ok("rank: non-archived beats newer archived",
       rank({"content_status": "needs_review", "last_edited_time": "2026-01-01"}) >
       rank({"content_status": "archived", "last_edited_time": "2026-12-01"}))

    # 429 backoff, offline: a fake urlopen raises 429 once, then answers
    import io
    real, seen = urllib.request.urlopen, []

    def fake_open(r, timeout=0):
        seen.append(r.full_url)
        if len(seen) == 1:
            raise urllib.error.HTTPError(r.full_url, 429, "rate", {"Retry-After": "0"}, io.BytesIO(b"{}"))
        return io.BytesIO(b'{"ok": true}')
    urllib.request.urlopen = fake_open
    try:
        nc = Notion("fixture-token")
        ok("429 -> retried, then succeeds", nc.call("GET", "/users") == {"ok": True} and nc.calls == 2)
    finally:
        urllib.request.urlopen = real

    # end to end over the fixtures, into a temp dir (outside the repo)
    with tempfile.TemporaryDirectory() as tmp:
        out, wm = os.path.join(tmp, "briefs"), os.path.join(tmp, "wm", "notion-export.watermark.json")
        fake = FakeNotion()
        stats = main_run(fake, "backfill", out, None, "fake-db", wm)
        dirs = sorted(os.listdir(out))
        ok("backfill: one folder per event (dated, slugged); private + off-type drafts skipped",
           dirs == ["2026-09-01-research-brief-second-fake-meetup", "2026-10-02-fake-summit-agents-edition"])
        ok("stats: 2 research, 1 post-event, 2 private skipped", stats.get("research_brief") == 2
           and stats.get("post_event_brief") == 1 and stats.get("skipped_private") == 2)
        ev = os.path.join(out, "2026-10-02-fake-summit-agents-edition")
        rb = open(os.path.join(ev, "research_brief.md"), encoding="utf-8").read()
        m = json.load(open(os.path.join(ev, "manifest.json"), encoding="utf-8"))
        allout = rb + json.dumps(m) + open(os.path.join(ev, "post_event_brief.md"), encoding="utf-8").read()
        ok("render: heading, ledger bullet, nested bullet, h4, pipe table, divider",
           "## Evidence Ledger — Fakeco" in rb and "- claim: Fakeco raised $5M seed | tier: web-verified" in rb
           and "  - nested detail" in rb and "#### Stat Bank" in rb and "| Metric | Value |" in rb
           and "| ARR | $2M |" in rb and "\n---" in rb)
        ok("render: bold, link, inline code", "**Pat**" in rb and "[site](https://fakeco.test)" in rb and "`eval()`" in rb)
        ok("render: paginated children (second page fetched)", "#### Stat Bank" in rb)
        ok("redaction: no fixture email / phone anywhere written", not any(s in allout for s in (
            "pat.fixture@fakeco.test", "212-555-0142", "jane.fixture@example.org", "212-555-0100", "+1 212 555 0199"))
           and "[redacted]" in rb)
        ok("manifest: stage-research shape (event + entities, names only, no kind)",
           m["event"] == {"notion_page_id": "eeeeeeee-0000-0000-0000-000000000001",
                          "title": "Fake Summit: Agents Edition", "event_date": "2026-10-02"}
           and [(e["type"], e["name"]) for e in m["entities"]] ==
           [("person", "Pat Placeholder"), ("company", "Fakeco"), ("topic", "Agent Evals")]
           and all(set(e) == {"type", "name", "notion_page_id"} for e in m["entities"]))
        ok("manifest: has_more relation paged via property endpoint, deduped",
           sum(e["type"] == "topic" for e in m["entities"]) == 1
           and f"GET /pages/eeeeeeee-0000-0000-0000-000000000001/properties/tp%3D?start_cursor=t2" in fake.calls)
        b = m["notion_export"]["briefs"]
        ok("manifest: both briefs, status + last_edited_time + brief_ref",
           b["research_brief"]["content_status"] == "needs_review"
           and b["post_event_brief"]["last_edited_time"] == "2026-11-05T10:00:00.000Z"
           and b["post_event_brief"]["brief_ref"] == "notion:aaaaaaaa-0000-0000-0000-000000000002"
           and m["notion_export"]["event_status"] == "attended")
        ok("acknowledged_signal: status + person comment (count only, stops at first hit)",
           b["post_event_brief"]["acknowledged_signal"] == {"content_status": "approved", "alex_commented": True}
           and "FIXTURE COMMENT TEXT" not in allout and "GET /comments?block_id=b2-td" not in fake.calls)
        ok("research brief carries no acknowledged_signal", "acknowledged_signal" not in b["research_brief"])
        nm = json.load(open(os.path.join(out, dirs[0], "manifest.json"), encoding="utf-8"))
        ok("no Event relation -> flagged, no notion_page_id", nm["notion_export"].get("no_event_relation") is True
           and "notion_page_id" not in nm["event"])
        w = json.load(open(wm, encoding="utf-8"))
        ok("watermark written after backfill", w["mode"] == "backfill" and w["since"].endswith(":00.000Z"))

        # incremental: only drafts edited after `since`; existing manifest entries for the other type survive
        fake2 = FakeNotion()
        s2 = main_run(fake2, "incremental", out, "2026-10-15T00:00:00.000Z", "fake-db", wm)
        m2 = json.load(open(os.path.join(ev, "manifest.json"), encoding="utf-8"))
        ok("incremental: only the post-event brief re-exported", s2.get("post_event_brief") == 1
           and not s2.get("research_brief") and f"GET /blocks/aaaaaaaa-0000-0000-0000-000000000001/children"
           not in fake2.calls)
        ok("incremental: research entry kept in the merged manifest", set(m2["notion_export"]["briefs"]) ==
           {"research_brief", "post_event_brief"})
        ok("incremental: watermark records the previous since",
           json.load(open(wm, encoding="utf-8"))["previous"] == "2026-10-15T00:00:00.000Z")

        # comments capability missing -> None, and no further comment calls
        class NoComments(FakeNotion):
            def call(self, method, path, body=None):
                if path.startswith("/comments"):
                    self.calls.append(path)
                    raise NotionError(403, "restricted_resource")
                return super().call(method, path, body)
        nc3 = NoComments()
        ex = Exporter(nc3, os.path.join(tmp, "x"), "fake-db")
        r1, r2 = ex.person_commented("p", [{"id": "b"}]), ex.person_commented("q", [])
        ok("comments 403 -> alex_commented None, capability probed once",
           r1 is None and r2 is None and sum(c.startswith("/comments") for c in nc3.calls) == 1)

    ok("ensure_ignored refuses a tracked path", _refuses(os.path.join(ROOT, ".claude", "scripts")))
    print(f"\n{'OK' if not fails else 'FAILED'}: {len(fails)} failure(s)")
    return not fails


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
    ap.add_argument("--limit", type=int, help="export at most N drafts (smoke test; does not move the watermark)")
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
