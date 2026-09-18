#!/usr/bin/env python3
"""substrate — the ONE producer library for the Knowledge Substrate (ADR-10; YED-160 / YED-169).

Spec: docs/adr/ADR-10-knowledge-substrate.md · .claude/notes/knowledge-substrate-architecture-2026-09-18.md
(§2, §6.4) as amended by .claude/notes/knowledge-substrate-review-2026-09-18.md.

Every write goes through spine_client (ADR-9: the single guarded write path). There is no
backfill script: the backfill runs THIS code over a list of manifests, the same code the live
/post-event-content Step 3.8 calls. If a backfill needs behaviour the live producer lacks, the
producer is wrong. Idempotency proof for every verb: the second run reports `created: 0`.

Verbs (W1 — four only; merge / record-usage / record-outcome are out of scope per the review):
  ensure-entity   --manifest m.json   companies / people / topics  (match-before-create)
  ensure-event    --manifest m.json   the event row + its entities + event_entity hyperedges
  ensure-document --manifest d.json   one artifact row (versioned by external_ref) + document_entity
  stage-claims    --brief b.md --manifest m.json [--brief-ref notion:<id>] [--approve]
                  parse a post_event_brief's learnings sections into `claim` rows (first_hand),
                  embed them (local bge-small, same space as doc_chunks), link speakers

Common flags: --dry-run (no writes; still reports matched/would-create) · --json (machine summary)
Self-test (offline, no network): python3 .claude/scripts/substrate.py --selftest

Conventions verified against prod 2026-09-18 (read-only):
  * notion_page_id is stored BOTH dashed (event, company) and undashed (person) — match both forms.
  * event_entity roles in use: person→speaker|host|attendee · topic→tagged_topic · company→subject.
Manifest shape:
  {"event": {"notion_page_id", "title", "kind"="attended", "event_date", "description", "url"},
   "entities": [{"type": "person"|"company"|"topic", "name", "role", "notion_page_id",
                 "title", "company", "linkedin_url", "website", "description"}]}
PII (ADR-9): persons get professional fields only — name · title · company_id · linkedin_url ·
role_context. Never `bio`, never text lifted from a transcript. The guard backstops this.
"""
from __future__ import annotations
import argparse, hashlib, html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from spine_client import PIIViolation, guard, q, req  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DOCKB = os.path.join(ROOT, ".claude", "skills", "doc-knowledge-base")
SOURCE = "substrate:notion"          # entity/event rows created by this producer
EMBED_MODEL = "BAAI/bge-small-en-v1.5"

ROLE_MAP = {  # manifest role -> the graph's existing vocabulary
    "person": {"speaker": "speaker", "host": "host", "organizer": "host", "attendee": "attendee",
               "panelist": "speaker", "moderator": "host"},
    "topic": {"topic": "tagged_topic", "tagged_topic": "tagged_topic", "subject": "tagged_topic"},
    "company": {"host": "subject", "sponsor": "subject", "subject": "subject", "mentioned": "subject"},
}

# post_event_brief section -> claim_type. Order matters only for reporting.
SECTIONS = [
    ("the thesis", "thesis"),
    ("pro-tips", "practice"),
    ("best practices", "practice"),
    ("pitfalls", "pitfall"),
    ("hot takes", "hot_take"),
    ("substantive insights", "learning"),
    ("stat bank", "statistic"),
]
DO_NOT_PUBLISH_RE = re.compile(r"rule\s*12|unsourced|do(?:n'?t| not) publish|never publish|never repeat", re.I)
CONF_RE = re.compile(r"\b(HIGH|MED)\b")


class Stats:
    def __init__(self):
        self.c: dict[str, dict[str, int]] = {}

    def bump(self, table: str, what: str, n: int = 1):
        self.c.setdefault(table, {}).setdefault(what, 0)
        self.c[table][what] += n

    def created(self) -> int:
        return sum(v.get("created", 0) for v in self.c.values())

    def report(self) -> str:
        return "\n".join(f"  {t:16s} " + "  ".join(f"{k}={v}" for k, v in sorted(d.items()))
                         for t, d in sorted(self.c.items()))


# ---------------------------------------------------------------------------------------------
# pure helpers (covered by --selftest)
# ---------------------------------------------------------------------------------------------
def pid_variants(pid: str | None) -> list[str]:
    """Both storage forms of a Notion page id: undashed 32-hex and dashed 8-4-4-4-12."""
    if not pid:
        return []
    h = re.sub(r"[^0-9a-f]", "", pid.lower().split("?")[0].split("/")[-1])[-32:]
    if len(h) != 32:
        return [pid]
    return [h, f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}"]


def norm_text(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def claim_key(text: str) -> str:
    return sha(norm_text(text))


def source_key_for_event(notion_event_id: str) -> str:
    return sha("post_event:" + pid_variants(notion_event_id)[0])


def clean_md(s: str) -> str:
    s = html.unescape(s)
    s = re.sub(r"<mention-[^>]*/>", "", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)        # [text](url) -> text
    s = s.replace("**", "").replace("\\~", "~").replace("\\*", "*")
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _table_rows(block: str) -> list[list[str]]:
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", block, re.S):          # Notion HTML tables
        rows.append([clean_md(td) for td in re.findall(r"<td>(.*?)</td>", tr, re.S)])
    if not rows:                                                   # markdown pipe tables
        for line in block.splitlines():
            if line.strip().startswith("|") and not re.match(r"^\|\s*:?-{2,}", line.strip()):
                rows.append([clean_md(c) for c in line.strip().strip("|").split("|")])
    return rows


def split_sections(md: str) -> dict[str, str]:
    out, cur, buf = {}, None, []
    for line in md.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if cur is not None:
                out[cur] = "\n".join(buf)
            cur, buf = m.group(1).strip().lower(), []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        out[cur] = "\n".join(buf)
    return out


def speaker_names(sections: dict[str, str]) -> list[str]:
    body = next((v for k, v in sections.items() if k.startswith("speaker map")), "")
    rows = _table_rows(body)
    names = []
    for r in rows[1:] if rows else []:
        if len(r) >= 2 and re.match(r"^[A-Z][\w'.-]+(?: [A-Z][\w'.-]+)+$", r[1]):
            names.append(r[1])
    return names


def name_tokens(name: str) -> set[str]:
    return set(re.findall(r"[a-z0-9']+", name.lower()))


def same_person(brief_name: str, graph_name: str) -> bool:
    """'Mila Zhou' ~ 'Miaolai (Mila) Zhou': one token set contains the other (>=2 tokens each)."""
    a, b = name_tokens(brief_name), name_tokens(graph_name)
    return len(a) >= 2 and len(b) >= 2 and (a <= b or b <= a)


def clean_title(t: str | None) -> str | None:
    """Drop trailing annotations: 'Sr. TPM, AWS (confirmed by Alex …)' -> 'Sr. TPM, AWS'."""
    return re.sub(r"\s*\([^)]*\)\s*$", "", t).strip() or None if t else None


def attribute(text: str, names: list[str]) -> str | None:
    """'(Ryan, HIGH)' / '(Ryan)' / 'Ryan Booz said' -> 'Ryan Booz' when unambiguous."""
    hits = [n for n in names if re.search(r"\b" + re.escape(n.split()[0]) + r"\b", text)]
    return hits[0] if len(hits) == 1 else None


def parse_brief(md: str) -> list[dict]:
    """post_event_brief markdown -> claim candidates. Parsing only — zero inference."""
    sections = split_sections(md)
    names = speaker_names(sections)
    items: list[dict] = []
    for key, ctype in SECTIONS:
        body = next((v for k, v in sections.items() if k.startswith(key)), None)
        if body is None:
            continue
        if ctype == "statistic":
            rows = _table_rows(body)
            for r in rows[1:]:
                if len(r) >= 2 and r[0] and r[1]:
                    items.append({"section": key, "claim_type": ctype,
                                  "raw": " — ".join(x for x in r if x),
                                  "text": f"{r[0]}: {r[1]}" + (f" ({r[2]})" if len(r) > 2 and r[2] else "")})
            continue
        for line in body.splitlines():
            m = re.match(r"^(?:[-*]|\d+\.)\s+(.*\S)", line)          # top-level bullets only
            if m:
                items.append({"section": key, "claim_type": ctype, "raw": m.group(1), "text": clean_md(m.group(1))})
            elif ctype == "thesis" and line.strip() and not line.startswith(("<", ">")):
                items.append({"section": key, "claim_type": ctype, "raw": line, "text": clean_md(line)})
    out = []
    for it in items:
        if len(it["text"]) < 12:
            continue
        cm = CONF_RE.search(it["raw"])
        conf = 0.8 if (cm and cm.group(1) == "HIGH") else 0.6 if cm else 0.7
        dnp = bool(DO_NOT_PUBLISH_RE.search(it["raw"]))
        if dnp:
            conf = min(conf, 0.5)
        out.append({**it, "confidence": conf, "do_not_publish": dnp,
                    "speaker": attribute(it["raw"], names), "claim_key": claim_key(it["text"])})
    seen, uniq = set(), []
    for it in out:                                                    # same text twice in one brief = one claim
        if it["claim_key"] not in seen:
            seen.add(it["claim_key"])
            uniq.append(it)
    return uniq


# ---------------------------------------------------------------------------------------------
# graph access (all writes via spine_client.req, which guards every body)
# ---------------------------------------------------------------------------------------------
class Graph:
    def __init__(self, dry_run: bool, stats: Stats):
        self.dry, self.stats, self._n = dry_run, stats, 0
        self._made: dict[tuple[str, str], str] = {}   # (table, normalized name) -> id created THIS run

    def _cached(self, table: str, name: str) -> str | None:
        hit = self._made.get((table, norm_text(name)))
        if hit:
            self.stats.bump(table, "matched")
        return hit

    def _remember(self, table: str, name: str, rid: str) -> str:
        self._made[(table, norm_text(name))] = rid
        return rid

    def get(self, path: str) -> list:
        st, body = req("GET", path)
        if st != 200:
            raise SystemExit(f"GET {path} -> {st}: {str(body)[:300]}")
        return body or []

    def post(self, table: str, row: dict | list, prefer: str = "return=representation", on_conflict: str | None = None):
        rows = row if isinstance(row, list) else [row]
        for r in rows:
            guard(table, r)                                          # fail before any network call
        if self.dry:
            self._n += 1
            return [{**r, "id": r.get("id") or f"dry:{table}:{self._n}:{i}"} for i, r in enumerate(rows)]
        path = f"/{table}" + (f"?on_conflict={on_conflict}" if on_conflict else "")
        st, body = req("POST", path, rows, prefer=prefer)
        if st not in (200, 201):
            raise SystemExit(f"POST /{table} -> {st}: {str(body)[:400]}")
        return body or []

    def patch(self, table: str, flt: str, row: dict):
        guard(table, row, op="update")
        if self.dry:
            return
        st, body = req("PATCH", f"/{table}?{flt}", row, prefer="return=minimal")
        if st not in (200, 204):
            raise SystemExit(f"PATCH /{table}?{flt} -> {st}: {str(body)[:400]}")

    # -- lookups -------------------------------------------------------------------------------
    def by_pid(self, table: str, pid: str | None, select: str = "*") -> dict | None:
        v = pid_variants(pid)
        if not v:
            return None
        rows = self.get(f"/{table}?notion_page_id=in.({','.join(q(x) for x in v)})&select={select}&limit=2")
        return rows[0] if rows else None

    def by_name(self, table: str, name: str) -> dict | None:
        rows = self.get(f"/{table}?name=ilike.{q(name.replace('*', ''))}&select=*&limit=5")
        rows = [r for r in rows if norm_text(r["name"]) == norm_text(name)]
        return rows[0] if rows else None

    # -- entities --------------------------------------------------------------------------------
    def _fill_missing(self, table: str, row: dict, fields: dict):
        patch = {k: v for k, v in fields.items() if v not in (None, "", []) and row.get(k) in (None, "", [])}
        if patch and not str(row.get("id", "")).startswith("dry:"):
            self.patch(table, f"id=eq.{row['id']}", patch)
            self.stats.bump(table, "enriched")

    def ensure_company(self, e: dict) -> str:
        fields = {"name": e["name"], "website": e.get("website"), "description": e.get("description"),
                  "linkedin_url": e.get("linkedin_url"), "notion_page_id": (pid_variants(e.get("notion_page_id")) or [None])[-1]}
        row = self.by_pid("company", e.get("notion_page_id")) or self.by_name("company", e["name"])
        if row:
            self.stats.bump("company", "matched")
            self._fill_missing("company", row, {k: v for k, v in fields.items() if k != "name"})
            return row["id"]
        if (hit := self._cached("company", e["name"])):
            return hit
        self.stats.bump("company", "created")
        return self._remember("company", e["name"],
                              self.post("company", {**{k: v for k, v in fields.items() if v}, "source": SOURCE})[0]["id"])

    def ensure_topic(self, e: dict) -> str:
        fields = {"name": e["name"], "description": e.get("description"),
                  "notion_page_id": (pid_variants(e.get("notion_page_id")) or [None])[-1]}
        row = self.by_pid("topic", e.get("notion_page_id")) or self.by_name("topic", e["name"])
        if row:
            self.stats.bump("topic", "matched")
            self._fill_missing("topic", row, {k: v for k, v in fields.items() if k != "name"})
            return row["id"]
        if (hit := self._cached("topic", e["name"])):
            return hit
        self.stats.bump("topic", "created")
        return self._remember("topic", e["name"],
                              self.post("topic", {**{k: v for k, v in fields.items() if v}, "source": SOURCE})[0]["id"])

    def ensure_person(self, e: dict) -> str:
        company_id = self.ensure_company({"name": e["company"]}) if e.get("company") else None
        li = (e.get("linkedin_url") or "").strip() or None
        fields = {"name": e["name"], "title": clean_title(e.get("title")), "company_id": company_id, "linkedin_url": li,
                  "notion_page_id": (pid_variants(e.get("notion_page_id")) or [None])[0]}  # persons: undashed
        row = self.by_pid("person", e.get("notion_page_id"))
        if not row and li:
            core = re.sub(r"^https?://(www\.)?", "", li.rstrip("/").lower())
            rows = self.get(f"/person?linkedin_url=ilike.*{q(core)}*&select=*&limit=3")
            row = rows[0] if len(rows) == 1 else None
        if not row:
            rows = self.get(f"/person?name=ilike.{q(e['name'])}&select=*&limit=5")
            rows = [r for r in rows if norm_text(r["name"]) == norm_text(e["name"])
                    and (company_id is None or r.get("company_id") in (None, company_id))]
            row = rows[0] if len(rows) == 1 else None                # ambiguous name -> create, never guess
        if row:
            self.stats.bump("person", "matched")
            self._fill_missing("person", row, {k: v for k, v in fields.items() if k != "name"})
            return row["id"]
        if (hit := self._cached("person", e["name"])):
            return hit
        self.stats.bump("person", "created")
        return self._remember("person", e["name"],
                              self.post("person", {**{k: v for k, v in fields.items() if v}, "source": SOURCE})[0]["id"])

    def ensure_entity(self, e: dict) -> tuple[str, str]:
        t = e["type"]
        fn = {"company": self.ensure_company, "person": self.ensure_person, "topic": self.ensure_topic}.get(t)
        if not fn:
            raise SystemExit(f"unknown entity type {t!r}")
        return t, fn(e)

    # -- events ----------------------------------------------------------------------------------
    def find_event(self, ev: dict) -> dict | None:
        row = self.by_pid("event", ev.get("notion_page_id"))
        if row or not ev.get("event_date"):
            return row
        day = ev["event_date"][:10]
        rows = self.get(f"/event?title=ilike.{q(ev['title'].replace('*', ''))}&kind=eq.{ev.get('kind', 'attended')}"
                        f"&event_date=gte.{day}T00:00:00Z&event_date=lte.{day}T23:59:59Z&select=*&limit=2")
        return rows[0] if len(rows) == 1 else None

    def ensure_event(self, m: dict) -> str:
        ev = m["event"]
        row = self.find_event(ev)
        if row:
            self.stats.bump("event", "matched")
            eid = row["id"]
        else:
            self.stats.bump("event", "created")
            eid = self.post("event", {k: v for k, v in {
                "title": ev["title"], "kind": ev.get("kind", "attended"), "event_date": ev.get("event_date"),
                "description": ev.get("description"), "url": ev.get("url"), "source": SOURCE,
                "notion_page_id": (pid_variants(ev.get("notion_page_id")) or [None])[-1],
                "metadata": {k2: ev[k2] for k2 in ("location", "google_calendar_event_id") if ev.get(k2)},
            }.items() if v not in (None, "", {})})[0]["id"]
        existing = set()
        if not str(eid).startswith("dry:"):
            existing = {(r["entity_type"], r["entity_id"], r["role"])
                        for r in self.get(f"/event_entity?event_id=eq.{eid}&select=entity_type,entity_id,role")}
        for e in m.get("entities", []):
            t, iid = self.ensure_entity(e)
            role = ROLE_MAP[t].get((e.get("role") or "").lower(), ROLE_MAP[t].get("subject", "subject")
                                   if t != "person" else "attendee")
            if (t, iid, role) in existing:
                self.stats.bump("event_entity", "matched")
                continue
            self.stats.bump("event_entity", "created")
            self.post("event_entity", {"event_id": eid, "entity_type": t, "entity_id": iid, "role": role},
                      prefer="resolution=ignore-duplicates,return=minimal",
                      on_conflict="event_id,entity_type,entity_id,role")
        return eid

    # -- documents -------------------------------------------------------------------------------
    def ensure_document(self, d: dict, event_id: str | None = None) -> str:
        body = d.get("body_text") or open(d["body_path"], encoding="utf-8").read()
        digest = sha(body)
        ref = d["external_ref"]
        cur = self.get(f"/documents?external_ref=eq.{q(ref)}&is_current=is.true&select=id,sha256,version&limit=1")
        if cur and cur[0]["sha256"] == digest:
            self.stats.bump("documents", "matched")
            return cur[0]["id"]
        row = {k: v for k, v in {
            "title": d["title"], "source_type": d["source_type"], "sha256": digest, "external_ref": ref,
            "word_count": len(body.split()), "doc_date": d.get("doc_date"), "event_id": event_id,
            "produced_by": d.get("produced_by"), "visibility": d.get("visibility", "private"),
            "notion_page_id": (pid_variants(d.get("notion_page_id")) or [None])[-1],
            "embedding_model": EMBED_MODEL,
        }.items() if v not in (None, "")}
        if cur:                                   # new version: retire the old current row FIRST (partial unique index)
            self.patch("documents", f"id=eq.{cur[0]['id']}", {"is_current": False})
            row.update({"version": cur[0]["version"] + 1, "supersedes_id": cur[0]["id"]})
            self.stats.bump("documents", "versioned")
        self.stats.bump("documents", "created")
        return self.post("documents", row)[0]["id"]


# ---------------------------------------------------------------------------------------------
# stage-claims
# ---------------------------------------------------------------------------------------------
def stage_claims(g: Graph, md: str, manifest: dict, *, brief_ref: str | None, approve: bool) -> int:
    ev = manifest["event"]
    items = parse_brief(md)
    if not items:
        sys.stderr.write("LOUD FAILURE: 0 claims parsed from the brief. Headings changed? Expected "
                         + ", ".join(k for k, _ in SECTIONS) + "\n")
        return 3
    event = g.find_event(ev)
    if not event:
        sys.stderr.write("stage-claims: event not in the graph — run ensure-event with this manifest first.\n")
        return 4
    eid, when = event["id"], event.get("event_date") or ev.get("event_date")
    doc_id = None
    if brief_ref:
        doc_id = g.ensure_document({"external_ref": brief_ref, "title": f"Post-event brief — {ev['title']}",
                                    "source_type": "post_event_brief", "body_text": md, "doc_date": when,
                                    "produced_by": "/post-event-content"}, event_id=eid)
    skey = source_key_for_event(ev["notion_page_id"])
    have = {r["claim_key"] for r in g.get(f"/claim?source_key=eq.{skey}&select=claim_key")}   # reads are safe in dry-run
    new = [it for it in items if it["claim_key"] not in have]
    g.stats.bump("claim", "matched", len(items) - len(new))
    vectors = []
    if new and g.dry:
        vectors = ["[dry-run: not embedded]"] * len(new)
    elif new:
        sys.path.insert(0, DOCKB)
        from dockb_common import embed_passages, vec_literal   # local bge-small; no metered API
        vectors = [vec_literal(v) for v in embed_passages([it["text"] for it in new])]
    rows = []
    for it, vec in zip(new, vectors):
        rows.append({
            "source_key": skey, "claim_key": it["claim_key"], "claim_text": it["text"], "claim_type": it["claim_type"],
            "locator": {"section": it["section"], "speaker": it["speaker"]}, "document_id": doc_id, "event_id": eid,
            "provenance_tier": "first_hand", "confidence": it["confidence"], "asserted_at": when,
            "status": "approved" if (approve and not it["do_not_publish"]) else "candidate",
            "extractor": "parse", "extractor_model": None, "lane": "A",
            "embedding": vec, "embedding_model": EMBED_MODEL,
            "metadata": {"do_not_publish": True} if it["do_not_publish"] else {},
        })
        rows[-1] = {k: v for k, v in rows[-1].items() if v is not None}
    if rows:
        g.stats.bump("claim", "created", len(rows))
        g.post("claim", rows, prefer="resolution=ignore-duplicates,return=minimal", on_conflict="source_key,claim_key")
    # speakers -> claim_entity(asserted_by). Resolved ONLY against persons already linked to THIS
    # event (the roster ensure-event wrote), by name-token containment: 'Mila Zhou' matches
    # 'Miaolai (Mila) Zhou'. Scoping to the roster is what makes the fuzzy match safe.
    speakers = {it["speaker"] for it in new if it["speaker"]}
    if speakers and not g.dry:
        ids = {r["claim_key"]: r["id"] for r in g.get(f"/claim?source_key=eq.{skey}&select=id,claim_key")}
        roster_ids = [r["entity_id"] for r in g.get(f"/event_entity?event_id=eq.{eid}&entity_type=eq.person&select=entity_id")]
        roster = g.get(f"/person?id=in.({','.join(roster_ids)})&select=id,name") if roster_ids else []
        for name in speakers:
            prows = [p for p in roster if same_person(name, p["name"])]
            if len(prows) != 1:
                g.stats.bump("claim_entity", "speaker_unresolved")
                continue
            links = [{"claim_id": ids[it["claim_key"]], "entity_type": "person", "entity_id": prows[0]["id"],
                      "role": "asserted_by"} for it in new if it["speaker"] == name and it["claim_key"] in ids]
            if links:
                g.stats.bump("claim_entity", "created", len(links))
                g.post("claim_entity", links, prefer="resolution=ignore-duplicates,return=minimal",
                       on_conflict="claim_id,entity_type,entity_id,role")
    by_type: dict[str, int] = {}
    for it in items:
        by_type[it["claim_type"]] = by_type.get(it["claim_type"], 0) + 1
    print(f"  parsed {len(items)} claims: " + ", ".join(f"{k}={v}" for k, v in sorted(by_type.items()))
          + f" · do_not_publish={sum(it['do_not_publish'] for it in items)}"
          + f" · attributed={sum(bool(it['speaker']) for it in items)}")
    return 0


# ---------------------------------------------------------------------------------------------
# self-test — offline, deterministic
# ---------------------------------------------------------------------------------------------
SAMPLE_BRIEF = """
## The Thesis
**"The model doesn't matter that much"** for query tuning. — Ryan Booz (HIGH)
## Speaker Map
<table header-row="true">
<tr><td>Raw ID</td><td>Person</td><td>Role</td></tr>
<tr><td>speaker_0</td><td>Mila Zhou</td><td>Host</td></tr>
<tr><td>speaker_1</td><td>Ryan Booz</td><td>Speaker</td></tr>
<tr><td>speaker_3</td><td>Audience member</td><td>—</td></tr>
</table>
## Pro-Tips
- Turn on **pg_stat_statements** and **auto_explain** before you need them. (Ryan, HIGH)
- Build indexes **CONCURRENTLY** on large prod tables; an AI's first index suggestion usually omits it.
## Pitfalls / Anti-Patterns
- Reading plan cost as a stopwatch; a 21.9M-cost plan beat a 10.4M-cost plan on worst case.
## Hot Takes
- AI is good at Postgres because it's read the open-source code. (Ryan, unsourced; Rule 12)
## Substantive Insights (ranked)
1. **Evidence beats model choice** for plan-level diagnosis: 7/10 → 10/10 with a plan.
## Stat Bank
<table header-row="true">
<tr><td>Stat</td><td>Value</td><td>Confidence / caveat</td></tr>
<tr><td>Plan-given runs naming the correlated subquery</td><td>10 of 10</td><td>HIGH</td></tr>
</table>
## Anecdotes
- **The dead charger.** Not a claim — anecdotes are not staged in W1.
"""


def selftest() -> bool:
    checks = []

    def ok(name, cond):
        checks.append((name, bool(cond)))

    v = pid_variants("https://app.notion.com/p/3ded3699c2db816a828ec6410801d5de?pvs=204")
    ok("pid variants: undashed + dashed", v == ["3ded3699c2db816a828ec6410801d5de", "3ded3699-c2db-816a-828e-c6410801d5de"])
    ok("pid variants: dashed input round-trips", pid_variants(v[1]) == v)
    ok("claim_key ignores case + whitespace", claim_key("A  b\nC") == claim_key("a b c"))
    ok("source_key stable across id formats", source_key_for_event(v[0]) == source_key_for_event(v[1]))
    items = parse_brief(SAMPLE_BRIEF)
    types = sorted(i["claim_type"] for i in items)
    ok("parse: 7 claims from 6 sections", len(items) == 7)
    ok("parse: types", types == ["hot_take", "learning", "pitfall", "practice", "practice", "statistic", "thesis"])
    ok("parse: anecdotes NOT staged", not any("charger" in i["text"] for i in items))
    ok("parse: speaker map read (2 named, audience skipped)", speaker_names(split_sections(SAMPLE_BRIEF)) == ["Mila Zhou", "Ryan Booz"])
    tip = next(i for i in items if "pg_stat_statements" in i["text"])
    ok("parse: '(Ryan, HIGH)' -> speaker + 0.8", tip["speaker"] == "Ryan Booz" and tip["confidence"] == 0.8)
    ok("parse: markdown stripped", "**" not in tip["text"])
    hot = next(i for i in items if i["claim_type"] == "hot_take")
    ok("parse: Rule-12 flag -> do_not_publish + confidence <= 0.5", hot["do_not_publish"] and hot["confidence"] <= 0.5)
    stat = next(i for i in items if i["claim_type"] == "statistic")
    ok("parse: stat-bank row -> 'Stat: Value (caveat)'", stat["text"].startswith("Plan-given runs") and "10 of 10" in stat["text"])
    untagged = next(i for i in items if "CONCURRENTLY" in i["text"])
    ok("parse: untagged confidence = 0.7", untagged["confidence"] == 0.7)
    ok("parse: 0 claims from an unrelated doc", parse_brief("## Intro\n- hello world here") == [])
    ok("speaker: 'Mila Zhou' ~ 'Miaolai (Mila) Zhou'", same_person("Mila Zhou", "Miaolai (Mila) Zhou"))
    ok("speaker: first name alone never matches", not same_person("Mila", "Miaolai (Mila) Zhou"))
    ok("speaker: different surname never matches", not same_person("Mila Chen", "Miaolai (Mila) Zhou"))
    ok("title annotation stripped",
       clean_title("Sr. Technical Program Manager, AWS (confirmed by Alex 2026-09-14)") == "Sr. Technical Program Manager, AWS")
    try:
        guard("claim", {"source_key": "s", "claim_key": tip["claim_key"], "claim_text": tip["text"],
                        "claim_type": tip["claim_type"], "provenance_tier": "first_hand", "confidence": 0.8,
                        "locator": {"section": "pro-tips", "speaker": "Ryan Booz"}, "status": "candidate",
                        "extractor": "parse", "lane": "A", "embedding": "[0.1,0.2]", "embedding_model": EMBED_MODEL})
        ok("guard: a staged claim row passes spine_client", True)
    except PIIViolation:
        ok("guard: a staged claim row passes spine_client", False)
    try:
        guard("person", {"name": "Ryan Booz", "bio": "x"})
        ok("guard still accepts person.bio (substrate simply never sends it)", True)
    except PIIViolation:
        ok("guard still accepts person.bio (substrate simply never sends it)", False)
    fail = 0
    for name, good in checks:
        fail += 0 if good else 1
        print(f"  {'✓' if good else '✗'} {name}")
    print(f"selftest: {len(checks) - fail}/{len(checks)} pass")
    return fail == 0


# ---------------------------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return 0 if selftest() else 1
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("verb", choices=["ensure-entity", "ensure-event", "ensure-document", "stage-claims"])
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--brief")
    ap.add_argument("--brief-ref", help="external_ref for the brief document, e.g. notion:<page id>")
    ap.add_argument("--approve", action="store_true",
                    help="inherited approval: brief-derived claims land approved (do_not_publish ones never do)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    m = json.load(open(a.manifest, encoding="utf-8"))
    stats = Stats()
    g = Graph(a.dry_run, stats)
    rc = 0
    if a.verb == "ensure-entity":
        for e in m.get("entities", []):
            g.ensure_entity(e)
    elif a.verb == "ensure-event":
        g.ensure_event(m)
    elif a.verb == "ensure-document":
        eid = None
        if m.get("event"):
            row = g.find_event(m["event"])
            eid = row["id"] if row else None
        did = g.ensure_document(m["document"], event_id=eid)
        for e in m.get("entities", []):
            t, iid = g.ensure_entity(e)
            g.post("document_entity", {"document_id": did, "entity_type": t, "entity_id": iid,
                                       "role": e.get("role", "about")},
                   prefer="resolution=ignore-duplicates,return=minimal",
                   on_conflict="document_id,entity_type,entity_id,role")
    elif a.verb == "stage-claims":
        if not a.brief:
            ap.error("stage-claims needs --brief")
        rc = stage_claims(g, open(a.brief, encoding="utf-8").read(), m, brief_ref=a.brief_ref, approve=a.approve)
    print(("DRY-RUN " if a.dry_run else "") + f"{a.verb}: created={stats.created()}")
    print(stats.report())
    if a.json:
        print(json.dumps({"verb": a.verb, "dry_run": a.dry_run, "created": stats.created(), "stats": stats.c}))
    return rc


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except PIIViolation as e:
        print(f"PIIViolation: {e}", file=sys.stderr)
        sys.exit(PIIViolation.exit_code)
