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

# post_event_brief section -> claim_type. Briefs drifted across sessions (verified against real
# briefs 2026-09-18: Postgres Sep-16 · Agents Behaving Badly Jun-25 · Shortlist Aug-24), so each
# kind has aliases. A heading matches when it STARTS WITH an alias.
SECTIONS = [
    (("the thesis", "thesis", "headline insight"), "thesis"),
    (("pro-tips", "pro tips", "gotchas"), "practice"),
    (("best practices", "best-practices"), "practice"),
    (("pitfalls",), "pitfall"),
    (("hot takes", "hot-takes"), "hot_take"),
    (("substantive insights", "top insights", "key insight", "ranked insights", "insights", "top takeaways", "takeaways"), "learning"),
    (("stat bank",), "statistic"),
]
# Sections that are NEVER staged, whatever they contain (a promise made in the room outranks the graph).
EXCLUDED_SECTIONS = ("confidentiality", "⛔")
# Founder-showcase format (content-patterns/founder-showcase.md): per-company `### N. Name — url`
# blocks with **Label:** bullets. Label -> (claim_type, provenance_tier); None = not a claim.
SHOWCASE_SECTION = "company breakdowns"
SHOWCASE_LABELS = {
    "problem": ("thesis", "first_hand"), "unique": ("learning", "first_hand"),
    "culture": ("learning", "first_hand"), "hiring": ("learning", "first_hand"),
    "recent (public)": ("statistic", "web_verified"), "recent": ("statistic", "first_hand"),
    "who": None,                                       # roster, not a claim (people are entities)
}
DO_NOT_PUBLISH_RE = re.compile(r"rule\s*12|unsourced|do(?:n'?t| not) publish|never publish|never repeat", re.I)
CONFIDENTIAL_RE = re.compile(r"stays in the room|confidential|⛔|off the record", re.I)
CONF_RE = re.compile(r"\b(HIGH|MED)\b")


# ---------------------------------------------------------------------------------------------
# Substrate gate ledger (the Step-4.5 lesson: a skipped step must FAIL the run, not close green).
# /post-event-content 3.8b calls `ensure-event --expect-claims` -> a PENDING row; 3.8c
# `stage-claims` success flips it to STAGED. .claude/hooks/substrate-gate.sh (Stop hook) fails
# the run while any row is PENDING. Backfill calls ensure-event WITHOUT --expect-claims (most
# backfilled events have no brief), so it never creates gate rows.
# Same JSONL shape + _pending session fallback as deep-read-ledger.sh.
# ---------------------------------------------------------------------------------------------
STATE_DIR = os.path.join(ROOT, ".claude", ".state")
GATE_FAIL_LOG = os.path.join(ROOT, ".claude", "artifacts", "substrate-gate-failures.jsonl")


def _ledger_path() -> str:
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID") or "_pending"
    return os.path.join(STATE_DIR, f"{sid}.substrate_gate.jsonl")


def ledger_mark(key: str, title: str, marker: str, reason: str | None = None, *, keep_if: tuple = ()) -> None:
    """Upsert one row by key. keep_if: markers that must not be downgraded (idempotent add)."""
    import datetime
    path = _ledger_path()
    os.makedirs(STATE_DIR, exist_ok=True)
    rows, kept = [], None
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                rows.append(line)                     # preserve corrupt lines verbatim (gate counts them)
                continue
            if isinstance(r, dict) and r.get("key") == key:
                kept = r
                continue
            rows.append(line)
    if kept and kept.get("marker") in keep_if:
        rows.append(json.dumps(kept))
    else:
        row = {"key": key, "event": title, "marker": marker,
               "ts": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        if reason:
            row["reason"] = reason
        rows.append(json.dumps(row))
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(rows) + "\n")
    os.replace(tmp, path)
    if marker == "waived":
        os.makedirs(os.path.dirname(GATE_FAIL_LOG), exist_ok=True)
        with open(GATE_FAIL_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"event": "substrate_gate_waived", "key": key, "title": title,
                                "reason": reason, "session": os.environ.get("CLAUDE_CODE_SESSION_ID", "_pending")}) + "\n")


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


# Non-claim sections a bold-only sub-label can also open — they END the claim section above them.
BOUNDARY_SECTIONS = ("anecdotes", "concept glossary", "quote bank", "full quote bank", "speaker map",
                     "documentarian", "open loops", "verification flags", "tools", "slides", "conditioning")


def redact_body(md: str) -> str:
    """Brief text handed to ensure_document obeys the SAME confidentiality rules as claim parsing: excluded
    sections (e.g. '## ⛔ Confidentiality flag') dropped whole, CONFIDENTIAL_RE lines dropped. Today the
    documents row stores only a hash + word_count (never the text), so this is a guard for any future
    text/chunk storage, not a fix for a live leak."""
    out, skip = [], False
    for line in md.splitlines():
        h = re.match(r"^##\s+(.+)", line)
        if h:
            skip = any(x in h.group(1).lower() for x in EXCLUDED_SECTIONS)
        if skip or CONFIDENTIAL_RE.search(line):
            continue
        out.append(line)
    return "\n".join(out)


def _known_section(title: str) -> bool:
    """For bold sub-labels only (## headings open a section unconditionally). Stricter than
    startswith: the name must end the label or be followed by punctuation — so '**Pitfalls / anti-patterns**'
    opens a section but '**Thesis evolution across the three rooms:**' (about OTHER events) does not."""
    names = [a for aliases, _ in SECTIONS for a in aliases] + list(BOUNDARY_SECTIONS)
    return any(re.match(re.escape(n) + r"(?:\s*[^\w\s]|\s*$)", title) for n in names)


def split_sections(md: str) -> dict[str, str]:
    """'## Heading' -> body. Also: '## 6. Pro-Tips' (numbered headings) and a bold-only line like
    '**Pro-Tips (if X → do Y)**' nested under a catch-all heading, when it names a known section."""
    out, cur, buf = {}, None, []
    for line in md.splitlines():
        m = re.match(r"^##\s+(?:\d{1,2}\s*[.·]\s+)?(.+?)\s*$", line)
        b = re.match(r"^\*\*([^*]+)\*\*\s*$", line)
        # '**Pro-Tips (if X → do Y)** — a · b · c': an inline label opening a section on its own line
        il = None if (m or b) else re.match(r"^\*\*([^*]+)\*\*\s*[—–:-]\s*(.+)$", line)
        title = (m or b or il).group(1).strip().lower() if (m or b or il) else None
        if title:
            title = re.sub(r"^(?:the\s+)?(?:\d{1,2}\s+)?", "", title)   # 'the 5 top takeaways' -> 'top takeaways'
        if m or ((b or il) and _known_section(title)):
            if cur is not None:
                out[cur] = "\n".join(buf)
            cur, buf = title, ([il.group(2)] if il else [])
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        out[cur] = "\n".join(buf)
    return out


# Where older briefs keep the roster when there is no "Speaker Map" (fallback, in order of preference).
ROSTER_SECTIONS = ("speakers", "presenter map", "people & outreach")
NAME_RE = re.compile(r"^[A-Z][\w'.-]+(?: [A-Z][\w'.-]+)+$")


def _person_from_cell(cell: str) -> str | None:
    """'Jared Robin — Co-founder & CEO' / 'Alex Lindahl (transcript: …)' / 'Ryan Booz' -> the name."""
    head = re.split(r"\s+[—–-]\s+|\s+·\s+|\s*\(", clean_md(cell))[0].strip(" *")
    return head if NAME_RE.match(head) else None


def speaker_names(sections: dict[str, str]) -> list[str]:
    """Names from the Speaker Map — tables (any number) or '- **Name** — role' bullets."""
    body = next((v for k, v in sections.items() if k.startswith("speaker map")), "") \
        or next((v for k, v in sections.items() if k.startswith(ROSTER_SECTIONS)), "")
    names = []
    rows = _table_rows(body)
    for r in rows[1:]:                                   # row 0 is the header
        for cell in r[:3]:                               # the person column varies between briefs
            n = _person_from_cell(cell)
            if n and n not in names:
                names.append(n)
                break
    for m in re.finditer(r"^[-*]\s+\*\*([^*]+)\*\*", body, re.M):
        n = _person_from_cell(m.group(1))
        if n and n not in names:
            names.append(n)
    return names


def name_tokens(name: str) -> set[str]:
    return set(re.findall(r"[a-z0-9']+", name.lower()))


def same_person(brief_name: str, graph_name: str) -> bool:
    """'Mila Zhou' ~ 'Miaolai (Mila) Zhou': one token set contains the other (>=2 tokens each)."""
    a, b = name_tokens(brief_name), name_tokens(graph_name)
    return len(a) >= 2 and len(b) >= 2 and (a <= b or b <= a)


def same_company(brief_name: str, graph_name: str) -> bool:
    """'North' ~ 'North.Cloud', 'Arist' ~ 'Arist': token containment, >=1 token (roster-scoped only)."""
    a, b = name_tokens(brief_name), name_tokens(graph_name)
    return bool(a) and bool(b) and (a <= b or b <= a)


def clean_title(t: str | None) -> str | None:
    """Drop trailing annotations: 'Sr. TPM, AWS (confirmed by Alex …)' -> 'Sr. TPM, AWS'."""
    return re.sub(r"\s*\([^)]*\)\s*$", "", t).strip() or None if t else None


OWNER_FIRST = "Alex"


def attribute(text: str, names: list[str]) -> str | None:
    """'(Ryan, HIGH)' / '(Sow)' / 'Ryan Booz said' -> 'Ryan Booz' when exactly one speaker matches.
    Briefs cite by first name OR surname. The brief owner's first name ('Alex') is never a tell —
    'Alex's pipeline' is Alex, not a same-named speaker; such a speaker still matches by surname."""
    def tells(n: str) -> list[str]:
        t = n.split()
        return [x for x in {t[0], t[-1]} if x != OWNER_FIRST]
    hits = [n for n in names if any(re.search(r"\b" + re.escape(x) + r"\b", text) for x in tells(n))]
    return hits[0] if len(hits) == 1 else None


def _body_items(body: str) -> list[str]:
    """Items from a section body: top-level bullets; else an inline list split on ' · ' or on
    inline '1. … 2. …' numbering; else the paragraph itself (a one-line thesis or stat)."""
    bullets = []
    for line in body.splitlines():
        m = re.match(r"^(?:[-*]|(\d+)\.)\s+(.*\S)", line)
        if not m:
            continue
        # '1. first … 2. second … 3. third' on ONE line: split on inline 'N. ' (decimals like 173.6 survive)
        parts = re.split(r"\s\d{1,2}\.\s+", m.group(2)) if m.group(1) else [m.group(2)]
        bullets += [p for p in parts if p.strip()]
    if bullets:
        return bullets
    # a '> **quote**' blockquote INSIDE a section is content (theses are often set this way) -> unwrap it
    lines = [re.sub(r"^\s*>\s?", "", l) for l in body.splitlines()]
    para = " ".join(l.strip() for l in lines if l.strip() and not l.lstrip().startswith(("<", "|")))
    if not para:
        return []
    if para.count(" · ") >= 2:
        return [p for p in para.split(" · ") if p.strip()]
    numbered = re.split(r"(?:^|\s)\d{1,2}\.\s+", para)
    if len([p for p in numbered if p.strip()]) >= 2:
        return [p for p in numbered if p.strip()]
    return [para]


def _showcase_items(body: str) -> list[dict]:
    """Founder-showcase `### N. Company — url` blocks -> company-attributed claims."""
    out = []
    for block in re.split(r"^###\s+", body, flags=re.M)[1:]:
        head, _, rest = block.partition("\n")
        company = clean_md(re.sub(r"^\d+\.\s*", "", head).split(" — ")[0].split(" - ")[0])
        for m in re.finditer(r"^[-*]\s+\*\*([^*:]+):?\*\*:?\s*(.+)$", rest, re.M):
            label = clean_md(m.group(1)).lower()
            spec = SHOWCASE_LABELS.get(label, SHOWCASE_LABELS.get(label.split(" (")[0]))
            if not spec:
                continue
            ctype, tier = spec
            out.append({"section": f"{SHOWCASE_SECTION}/{company}", "claim_type": ctype, "tier": tier,
                        "about_company": company, "raw": m.group(2),
                        "text": f"{company} — {label.split(' (')[0]}: {clean_md(m.group(2))}"})
    return out


def parse_brief(md: str) -> list[dict]:
    """post_event_brief markdown -> claim candidates. Parsing only — zero inference."""
    sections = split_sections(md)
    names = speaker_names(sections)
    items: list[dict] = []
    for title, body in sections.items():
        if any(x in title for x in EXCLUDED_SECTIONS):
            continue                                   # confidential sections are never staged
        if title.startswith(SHOWCASE_SECTION):
            items += _showcase_items(body)
            continue
        ctype = next((t for aliases, t in SECTIONS if title.startswith(aliases)), None)
        if not ctype:
            continue
        if ctype == "statistic" and _table_rows(body):
            for r in _table_rows(body)[1:]:
                if len(r) >= 2 and r[0] and r[1]:
                    items.append({"section": title, "claim_type": ctype, "raw": " — ".join(x for x in r if x),
                                  "text": f"{r[0]}: {r[1]}" + (f" ({r[2]})" if len(r) > 2 and r[2] else "")})
            continue
        for raw in _body_items(body):
            items.append({"section": title, "claim_type": ctype, "raw": raw, "text": clean_md(raw)})
    out = []
    for it in items:
        if len(it["text"]) < 12:
            continue
        if CONFIDENTIAL_RE.search(it["raw"]):
            continue                                   # a confidential line is dropped, not flagged
        cm = CONF_RE.search(it["raw"])
        conf = 0.8 if (cm and cm.group(1) == "HIGH") else 0.6 if cm else 0.7
        dnp = bool(DO_NOT_PUBLISH_RE.search(it["raw"]))
        if dnp:
            conf = min(conf, 0.5)
        out.append({**it, "confidence": conf, "do_not_publish": dnp, "tier": it.get("tier", "first_hand"),
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

    def ensure_topic(self, e: dict) -> str | None:
        if not e.get("name"):                        # id-only topic (name not yet pulled from Notion)
            row = self.by_pid("topic", e.get("notion_page_id"))
            self.stats.bump("topic", "matched" if row else "skipped_no_name")
            return row["id"] if row else None
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
            if not ev.get("kind"):   # ADR-10 decision 9: attendance is never inferred — the caller must say so
                raise SystemExit(f"ensure-event: manifest for {ev.get('title')!r} has no 'kind'; refusing to "
                                 "create an event without explicit attendance evidence (ADR-10 decision 9)")
            self.stats.bump("event", "created")
            eid = self.post("event", {k: v for k, v in {
                "title": ev["title"], "kind": ev["kind"], "event_date": ev.get("event_date"),
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
            if iid is None:                          # deferred (e.g. id-only topic); a re-run links it
                continue
            role =ROLE_MAP[t].get((e.get("role") or "").lower(), ROLE_MAP[t].get("subject", "subject")
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
        sys.stderr.write("LOUD FAILURE: 0 claims parsed from the brief. Headings changed? Expected one of: "
                         + ", ".join(a for aliases, _ in SECTIONS for a in aliases)
                         + f", or '{SHOWCASE_SECTION}' (founder showcase)\n")
        return 3
    event = g.find_event(ev)
    if not event:
        sys.stderr.write("stage-claims: event not in the graph — run ensure-event with this manifest first.\n")
        return 4
    eid, when = event["id"], event.get("event_date") or ev.get("event_date")
    doc_id = None
    if brief_ref:
        doc_id = g.ensure_document({"external_ref": brief_ref, "title": f"Post-event brief — {ev['title']}",
                                    "source_type": "post_event_brief", "body_text": redact_body(md), "doc_date": when,
                                    "produced_by": "/post-event-content"}, event_id=eid)
    skey = source_key_for_event(ev["notion_page_id"])
    if doc_id and not g.dry:   # claims staged before the brief had a document row get linked, never re-pointed
        g.patch("claim", f"source_key=eq.{skey}&document_id=is.null", {"document_id": doc_id})
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
            "provenance_tier": it["tier"], "confidence": it["confidence"], "asserted_at": when,
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
    speakers = {it["speaker"] for it in items if it["speaker"]}
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
                      "role": "asserted_by"} for it in items if it["speaker"] == name and it["claim_key"] in ids]
            if links:
                g.stats.bump("claim_entity", "linked (idempotent)", len(links))
                g.post("claim_entity", links, prefer="resolution=ignore-duplicates,return=minimal",
                       on_conflict="claim_id,entity_type,entity_id,role")
    # founder-showcase claims -> claim_entity(company, about), resolved against THIS event's roster
    about = {it["about_company"] for it in items if it.get("about_company")}
    if about and not g.dry:
        ids = {r["claim_key"]: r["id"] for r in g.get(f"/claim?source_key=eq.{skey}&select=id,claim_key")}
        co_ids = [r["entity_id"] for r in g.get(f"/event_entity?event_id=eq.{eid}&entity_type=eq.company&select=entity_id")]
        roster = g.get(f"/company?id=in.({','.join(co_ids)})&select=id,name") if co_ids else []
        for name in about:
            match = [c for c in roster if same_company(name, c["name"])]
            if len(match) != 1:
                g.stats.bump("claim_entity", "company_unresolved")
                continue
            links = [{"claim_id": ids[it["claim_key"]], "entity_type": "company", "entity_id": match[0]["id"],
                      "role": "about"} for it in items if it.get("about_company") == name and it["claim_key"] in ids]
            if links:
                g.stats.bump("claim_entity", "linked (idempotent)", len(links))
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


# Excerpts of two REAL brief formats (2026-09-18 drift check) — the parser must handle both.
SHOWCASE_SAMPLE = """
## ⛔ Confidentiality flag (read first)
A founder shared an off-the-record detail on stage and said "this stays in the room." Do NOT publish it.
## The night in one line
Six early-stage NYC founders pitched back-to-back to hire.
## Company breakdowns (6 dimensions)
### 1. North — [north.cloud](http://north.cloud) (Cloud & AI FinOps)
- **Who:** Matt Biringer (CEO), Yassine Açoine (CTO, presented).
- **Problem:** Engineers create cloud/AI spend; finance is accountable — nobody owns the seam.
- **Recent (PUBLIC):** North v3 launched Aug 20 2026. Series A $5M. ⛔ off-the-record detail — excluded.
### 2. Arist — [arist.co](http://arist.co) (Consulting automation)
- **Problem:** Execs don't know their org's real problems; McKinsey costs $5M to find out.
- **Recent (PUBLIC):** Series B $22.5M (SEC Form D, Aug 4 2026); ~$39M total.
- **Hiring:** Ownership-hungry generalists.
"""
JUNE_SAMPLE = """
## Hot Takes
1. **Single agents are usually fine; multi-agent gains are mostly illusory** given million-token context. (Kilian)
## Pitfalls / Anti-Patterns
Agents cheating the eval · benchmark contamination via data vendors · over-constraining a strong model with legacy scaffolding · too many metrics
## Top Insights (ranked)
1. Production is a precondition for evaluation, not its reward. 2. Cheating + contamination are the structural enemies of agent benchmarks. 3. Keep scenarios model-agnostic so evals survive model churn.
## Stat Bank
**$100K** Datadog startup credits (Series A & earlier, yr 1) — the only hard number on stage.
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
    sc = parse_brief(SHOWCASE_SAMPLE)
    blob = " ".join(i["text"] for i in sc).lower()
    ok("showcase: confidential section never staged", "stays in the room" not in blob and "off-the-record detail" not in blob)
    ok("showcase: a line carrying ⛔ is dropped whole", not any(i["about_company"] == "North" and i["claim_type"] == "statistic" for i in sc))
    ok("showcase: 'Who' roster lines are not claims", not any("Biringer" in i["text"] for i in sc))
    ok("showcase: claims attributed to their company",
       {i["about_company"] for i in sc} == {"North", "Arist"} and all(i["text"].startswith(i["about_company"]) for i in sc))
    ok("showcase: Recent (PUBLIC) -> web_verified",
       any(i["about_company"] == "Arist" and i["claim_type"] == "statistic" and i["tier"] == "web_verified" for i in sc))
    ok("showcase: 4 claims total (North problem; Arist problem, recent, hiring)", len(sc) == 4)
    jn = parse_brief(JUNE_SAMPLE)
    ok("june: pitfalls paragraph split on ' · ' -> 4", sum(i["claim_type"] == "pitfall" for i in jn) == 4)
    ok("june: 'Top Insights' alias + inline numbering -> 3", sum(i["claim_type"] == "learning" for i in jn) == 3)
    ok("june: prose stat bank -> 1 statistic", sum(i["claim_type"] == "statistic" for i in jn) == 1)
    sm_table = split_sections("## Speaker Map\n<table>\n<tr><td>ID</td><td>Person · role</td></tr>\n"
                              "<tr><td>spk_3</td><td>**Jared Robin** — Co-founder & CEO, RevGenius (host)</td></tr>\n"
                              "<tr><td>spk_4</td><td>**Alex Lindahl** — Clay (transcript: \"Lindell\")</td></tr>\n</table>")
    ok("speaker map: names inside role cells", speaker_names(sm_table) == ["Jared Robin", "Alex Lindahl"])
    ok("sections: numbered heading '## 6. Pro-Tips (if X, do Y)'",
       [i["claim_type"] for i in parse_brief("## 6. Pro-Tips (if X, do Y)\n- Automate the 90%. (Eric)")] == ["practice"])
    nested = parse_brief("## Learnings tier\n**Pro-Tips (if X → do Y)**\n- RL-fine-tune a small model with GRPO against a verifiable reward.\n**Pitfalls / anti-patterns**\n"
                         "- Mocks tell you nothing.\n**Anecdotes**\n- Live RL on stage.")
    ok("sections: bold sub-labels split a catch-all heading; anecdotes stay out",
       [i["claim_type"] for i in nested] == ["practice", "pitfall"])
    inline = parse_brief("## Learnings Tier\n**Pro-Tips (if X → do Y)** — build one agent for the most painful step · "
                         "route cheap steps to Haiku, reserve Opus for reasoning · set noindex on paid-ad landing pages\n**Anecdotes** — spent $300 on a site redesign")
    ok("sections: inline '**Label** — a · b' opens a section and splits the list",
       [i["claim_type"] for i in inline] == ["practice", "practice", "practice"])
    ok("sections: 'The 5 Top Takeaways' + 'Gotchas' aliases",
       [i["claim_type"] for i in parse_brief("## 4. The 5 Top Takeaways\n1. **A new compute unit for agents is forming.**\n"
                                             "## 6. Gotchas & Practitioner Playbook\n- Flatten your tool arguments into few params.")]
       == ["learning", "practice"])
    ok("sections: '## 2 · The Thesis' numbering",
       [i["claim_type"] for i in parse_brief("## 2 · The Thesis\n**Five funds, one bet each: agents doing real work.**")] == ["thesis"])
    ok("sections: '**Thesis evolution across…:**' (other events) does NOT open a thesis",
       parse_brief("## 7. Cross-Event Overlap\n**Thesis evolution across the three rooms:**\n- GTM Eng NYC said centralize the data.") == [])
    ok("speakers: roster fallback to 'People & Outreach' table",
       speaker_names(split_sections("## People & Outreach State\n<table>\n<tr><td>Person</td><td>Role</td></tr>\n"
                                    "<tr><td>**Sangram Vajre** (GTM Partners)</td><td>Speaker</td></tr>\n</table>")) == ["Sangram Vajre"])
    red = redact_body("## ⛔ Confidentiality flag (read first)\nSeries B $X — stays in the room.\n## Thesis\nPublic line.\n"
                      "- North raised a round (confidential).\n- Antimetal $24.3M.")
    ok("redact_body: excluded section + confidential lines never stored",
       "Series B" not in red and "confidential" not in red and "Public line." in red and "Antimetal" in red)
    rg = ["Jared Robin", "Alex Lindahl", "Mintis Sow", "Tyler Phillips"]
    ok("attribute: surname tell '(Sow)'", attribute("Run a click study (Sow). HIGH.", rg) == "Mintis Sow")
    ok("attribute: owner's first name is not a tell", attribute("Alex's own pipeline gates output", rg) is None)
    ok("attribute: two speakers -> unattributed", attribute("(Phillips, Lindahl)", rg) is None)
    sm_bullets = split_sections("## Speaker Map (clean — 2 named speakers)\n- **Philip Kiely** — Head of AI Education, "
                                "**Baseten**.\n- **Declan Jackson** — Member of Technical Staff.")
    ok("speaker map: bullet form", speaker_names(sm_bullets) == ["Philip Kiely", "Declan Jackson"])
    ok("alias: 'Key Insight 6 — …' staged as learning",
       parse_brief("## Key Insight 6 — the frontier crossing\n- Terminal-Bench v4.0: GLM-5.3 = 41.9%, top open-weight.")[0]["claim_type"] == "learning")
    ok("company: 'North' ~ 'North.Cloud'", same_company("North", "North.Cloud"))
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
    # gate ledger + Stop hook, end to end, in a throwaway session (no network)
    import subprocess
    hook_path = os.path.join(ROOT, ".claude", "hooks", "substrate-gate.sh")
    saved = os.environ.get("CLAUDE_CODE_SESSION_ID")
    os.environ["CLAUDE_CODE_SESSION_ID"] = "substrate-selftest"
    try:
        def run_hook() -> str:
            env = dict(os.environ, CLAUDE_PROJECT_DIR=ROOT)
            p = subprocess.run([hook_path], input=json.dumps({"session_id": "substrate-selftest", "stop_hook_active": False}),
                               text=True, capture_output=True, env=env)
            return p.stdout.strip()
        k, t = "0" * 32, "gate selftest event"
        ledger_mark(k, t, "pending")
        ok("gate: PENDING row blocks the stop", '"decision":"block"' in run_hook())
        ledger_mark(k, t, "staged")
        ledger_mark(k, t, "pending", keep_if=("staged", "waived"))
        ok("gate: re-running ensure-event never downgrades STAGED", run_hook() == "")
        with open(_ledger_path(), "a", encoding="utf-8") as f:
            f.write("{not json\n")
        ok("gate: corrupt ledger line blocks (fail-closed)", '"decision":"block"' in run_hook())
    finally:
        if os.path.exists(_ledger_path()):
            os.remove(_ledger_path())
        if saved is None:
            os.environ.pop("CLAUDE_CODE_SESSION_ID", None)
        else:
            os.environ["CLAUDE_CODE_SESSION_ID"] = saved
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
    ap.add_argument("verb", choices=["ensure-entity", "ensure-event", "ensure-document", "stage-claims", "waive",
                                     "backfill", "preview-claims", "approve-claims"])
    ap.add_argument("--manifest", help="one manifest (all verbs except backfill)")
    ap.add_argument("--manifest-dir", help="(backfill) a directory of *.event.json / *.entities.json manifests "
                                           "from supabase/scripts/build_manifests.py — the SAME ensure-event / "
                                           "ensure-entity code, run over a list (there is no separate backfill path)")
    ap.add_argument("--expect-claims", action="store_true",
                    help="(ensure-event, live /post-event-content only) open a PENDING gate row that "
                         "stage-claims must close — the Stop hook fails the run otherwise")
    ap.add_argument("--reason", help="(waive) why this event's claims are deliberately not staged — logged")
    ap.add_argument("--brief")
    ap.add_argument("--brief-ref", help="external_ref for the brief document, e.g. notion:<page id>")
    ap.add_argument("--approve", action="store_true",
                    help="inherited approval: brief-derived claims land approved (do_not_publish ones never do)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.verb == "preview-claims":                 # offline: what would stage-claims stage? (review surface)
        if not a.brief:
            ap.error("preview-claims needs --brief")
        items = parse_brief(open(a.brief, encoding="utf-8").read())
        for it in items:
            flags = " ⚠do-not-publish" if it["do_not_publish"] else ""
            who = f" · {it['speaker']}" if it.get("speaker") else ""
            co = f" · about {it['about_company']}" if it.get("about_company") else ""
            print(f"  [{it['claim_type']:9s} {it['tier']:12s} {it['confidence']:.1f}{who}{co}{flags}] {it['text'][:150]}")
        print(f"preview: {len(items)} claims" + ("" if items else "  <- LOUD: 0 claims; stage-claims would exit 3"))
        return 0 if items else 3
    stats = Stats()
    g = Graph(a.dry_run, stats)
    if a.verb == "backfill":
        if not a.manifest_dir:
            ap.error("backfill needs --manifest-dir")
        files = sorted(f for f in os.listdir(a.manifest_dir) if f.endswith((".event.json", ".entities.json")))
        for fn in files:
            before = stats.created()
            mm = json.load(open(os.path.join(a.manifest_dir, fn), encoding="utf-8"))
            if fn.endswith(".event.json"):
                g.ensure_event(mm)                       # no --expect-claims: backfill opens no gate rows
            else:
                for e in mm.get("entities", []):
                    g.ensure_entity(e)
            print(f"  {'dry ' if a.dry_run else ''}{fn:78s} created={stats.created() - before}")
        print(("DRY-RUN " if a.dry_run else "") + f"backfill: {len(files)} manifests · created={stats.created()}")
        print(stats.report())
        if a.json:
            print(json.dumps({"verb": "backfill", "dry_run": a.dry_run, "created": stats.created(), "stats": stats.c}))
        return 0
    if not a.manifest:
        ap.error(f"{a.verb} needs --manifest")
    m = json.load(open(a.manifest, encoding="utf-8"))
    rc = 0
    ev = m.get("event") or {}
    gate_key = (pid_variants(ev.get("notion_page_id")) or [None])[0]
    if a.verb == "ensure-entity":
        for e in m.get("entities", []):
            g.ensure_entity(e)
    elif a.verb == "waive":
        if not (gate_key and a.reason):
            ap.error("waive needs a manifest with event.notion_page_id and --reason")
        ledger_mark(gate_key, ev.get("title", ""), "waived", a.reason)
        print(f"waived: {ev.get('title')} — {a.reason} (logged to substrate-gate-failures.jsonl)")
        return 0
    elif a.verb == "ensure-event":
        g.ensure_event(m)
        if a.expect_claims and not a.dry_run and gate_key:
            ledger_mark(gate_key, ev.get("title", ""), "pending", keep_if=("staged", "waived"))
    elif a.verb == "ensure-document":
        eid = None
        if m.get("event"):
            row = g.find_event(m["event"])
            eid = row["id"] if row else None
        did = g.ensure_document(m["document"], event_id=eid)
        for e in m.get("entities", []):
            t, iid = g.ensure_entity(e)
            g.stats.bump("document_entity", "linked")
            g.post("document_entity", {"document_id": did, "entity_type": t, "entity_id": iid,
                                       "role": e.get("role", "about")},
                   prefer="resolution=ignore-duplicates,return=minimal",
                   on_conflict="document_id,entity_type,entity_id,role")
    elif a.verb == "approve-claims":
        # Inherited approval (Alex, 2026-09-18): claims parsed from a brief he has reviewed are approved.
        # do_not_publish claims are NEVER approved by this path.
        skey = source_key_for_event(ev["notion_page_id"])
        rows = g.get(f"/claim?source_key=eq.{skey}&status=eq.candidate&select=id,metadata")
        ids = [r["id"] for r in rows if not (r.get("metadata") or {}).get("do_not_publish")]
        held = len(rows) - len(ids)
        for i in range(0, len(ids), 50):
            g.patch("claim", f"id=in.({','.join(ids[i:i + 50])})",
                    {"status": "approved", "reviewed_at": __import__("datetime").datetime.now(
                        __import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
        stats.bump("claim", "approved", len(ids))
        stats.bump("claim", "held_do_not_publish", held)
    elif a.verb == "stage-claims":
        if not a.brief:
            ap.error("stage-claims needs --brief")
        rc = stage_claims(g, open(a.brief, encoding="utf-8").read(), m, brief_ref=a.brief_ref, approve=a.approve)
        if rc == 0 and not a.dry_run and gate_key:
            ledger_mark(gate_key, ev.get("title", ""), "staged")
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
