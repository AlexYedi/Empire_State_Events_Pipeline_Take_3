#!/usr/bin/env python3
"""substrate — the ONE producer library for the Knowledge Substrate (ADR-10; YED-160 / YED-169).

Spec: docs/adr/ADR-10-knowledge-substrate.md · .claude/notes/knowledge-substrate-architecture-2026-09-18.md
(§2, §6.4) as amended by .claude/notes/knowledge-substrate-review-2026-09-18.md.

Every write goes through spine_client (ADR-9: the single guarded write path). There is no
backfill script: the backfill runs THIS code over a list of manifests, the same code the live
/post-event-content Step 3.8 calls. If a backfill needs behaviour the live producer lacks, the
producer is wrong. Idempotency proof for every verb: the second run reports `created: 0`.

Verbs (W1 four + the S1b-lite `merge`; record-usage / record-outcome stay out of scope per the review):
  ensure-entity   --manifest m.json   companies / people / topics  (match-before-create)
  ensure-event    --manifest m.json   the event row + its entities + event_entity hyperedges
  ensure-document --manifest d.json   one artifact row (versioned by external_ref) + document_entity
  stage-claims    --brief b.md --manifest m.json [--brief-ref notion:<id>] [--approve]
                  parse a post_event_brief's learnings sections into `claim` rows (first_hand),
                  embed them (local bge-small, same space as doc_chunks), link speakers
  expect-research --manifest m.json   (YED-205) open the PRE-EVENT gate row `research:<page id>` — no graph write
  stage-research  --manifest m.json --evidence ev.md --brief-ref notion:<research brief id>
                  (YED-205) the pre-event write: roster entities + the research_brief document + one claim per
                  Evidence Ledger row (web-verified w/ URL -> web_verified; email-signal w/ public URL -> email_signal;
                  everything else skipped + counted). NO event row — attendance is never inferred (ADR-10 D9); the
                  post-event ensure-event attaches these claims when the attended row appears.
                  Spec: .claude/notes/yed-205-spec-2026-09-27.md
  publish         --manifest pub.json   (YED-208) published Content Drafts -> event(kind='published', url) +
                  documents(linkedin_post, public_ok) + one embedded chunk per post VARIANT + artifact_outcome.
                  A post already in the graph with no new body only refreshes its outcome. Spec:
                  .claude/notes/yed-208-spec-2026-09-27.md
  published-refs  print the Notion page ids of posts already in the graph (for /tag-outcome's publish-sync)
  merge           --table company|person|topic --from <id|name> --into <id|name> --reason "…" [--dry-run]
                  HUMAN-ONLY, REVERSIBLE soft-merge (YED-47, ADR-4 D3): re-points every edge it can, transfers
                  engagement, tombstones the source (metadata.merged_into + an edge snapshot). Deletes nothing.
                  `merge --revert --table T --from <id|name>` restores from the snapshot. The agent PROPOSES
                  with --dry-run; Alex runs the live one. Replaces merge_topics.py (retired 2026-09-27 — it
                  hard-deleted the source, contra ADR-4 D3).

Identity (YED-47 S1b-lite, no DDL): company `Name (Qualifier)` resolves to `Name` ONLY when the bare-name
candidate is unique AND both website hosts agree; every less-certain case is created AND surfaced to
.claude/artifacts/identity-ambiguity.jsonl (never guessed). Every resolver follows a tombstone to its live
target. Persons: page-id -> LinkedIn -> exact name + company; ambiguous -> create + surface. No fuzzy person
matching, ever (ADR-4 D3). Weekly probe: .claude/scripts/identity_probe.py (from /rigor-review).

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
role_context. Never `bio`, never text lifted from a transcript — that rule is THIS producer's discipline
(the guard allows `bio`); the guard backstops only contact detail (email/phone refused anywhere, incl. inside bio).
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
    # YED-218 (2026-09-24). Questions were the legacy Notion pull's single biggest advantage in the
    # YED-172 A/B: Topic pages carry a `Top Questions` property that has been accumulating for months,
    # and the graph had no question-shaped claim to retrieve, so every pack re-derived them from
    # statements. `claim_type` is unconstrained text, so this needs no DDL.
    (("top questions", "prepared questions", "open questions", "questions"), "question"),
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

# ---------------------------------------------------------------------------------------------
# Graph-write freeze (YED-213 reconciliation, 2026-09-21).
# The freeze and the substrate gate watch DIFFERENT HALVES of the same write:
#   freeze -> may this write happen at all?      (checked here, BEFORE ensure-event touches the graph)
#   gate   -> did a write that happened finish?  (checked by substrate-gate.sh at Stop, on PENDING rows)
# Enforcing the freeze here is what keeps them from conflicting: a refused write never reaches
# `ledger_mark(..., "pending")`, so the gate has nothing to block on. The old failure shape was a
# run that called ensure-event (already violating the freeze), then stopped short of stage-claims
# and got blocked by the gate for honouring a rule it had already broken.
# Rows opened BEFORE a freeze was declared are closed with `waive --reason` — deliberately not
# blocked, because the escape valve must stay reachable while frozen.
# ---------------------------------------------------------------------------------------------
FREEZE_PATH = os.path.join(ROOT, ".claude", "references", "graph-freeze.json")
FREEZE_LOG = os.path.join(ROOT, ".claude", "artifacts", "graph-freeze-overrides.jsonl")
# Verbs that change graph state. `waive` and `preview-claims` are absent on purpose (see above);
# --dry-run is exempted at the call site, not here.
FREEZE_BLOCKS = ("ensure-entity", "ensure-event", "ensure-document", "stage-claims",
                 "backfill", "backfill-questions", "approve-claims", "merge", "stage-research", "publish")


def freeze_state() -> dict | None:
    """The active freeze, or None. A malformed/unreadable file is NOT treated as 'no freeze' —
    it returns a synthetic active freeze, so a corrupted marker fails closed like the gate does."""
    if not os.path.exists(FREEZE_PATH):
        return None
    try:
        f = json.load(open(FREEZE_PATH, encoding="utf-8"))
    except (ValueError, OSError) as e:
        return {"active": True, "issue": "?", "reason": f"graph-freeze.json is unreadable ({e}) — "
                "failing closed. Fix or repair the file rather than deleting it."}
    return f if isinstance(f, dict) and f.get("active") else None


def freeze_check(verb: str, dry_run: bool, override: str | None) -> int:
    """0 = proceed. 4 = refused by an active freeze (distinct from 3 = 'no claims parsed')."""
    if verb not in FREEZE_BLOCKS or dry_run:
        return 0
    fz = freeze_state()
    if not fz:
        return 0
    if override:
        import datetime
        os.makedirs(os.path.dirname(FREEZE_LOG), exist_ok=True)
        with open(FREEZE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"event": "graph_freeze_override", "verb": verb,
                                "issue": fz.get("issue"), "override_reason": override,
                                "session": os.environ.get("CLAUDE_CODE_SESSION_ID", "_pending"),
                                "ts": datetime.datetime.now(datetime.timezone.utc)
                                        .strftime("%Y-%m-%dT%H:%M:%SZ")}) + "\n")
        print(f"⚠️  GRAPH FREEZE OVERRIDDEN ({fz.get('issue')}): {override}\n"
              f"    logged to {os.path.relpath(FREEZE_LOG, ROOT)} — proceeding.")
        return 0
    print(f"""⛔ GRAPH-WRITE FREEZE ACTIVE ({fz.get('issue', '?')}) — `{verb}` refused, nothing was written.

{fz.get('reason', '')}

Lifts when: {fz.get('lifts_when', 'see .claude/references/graph-freeze.json')}

This is NOT the substrate gate. The gate asks whether a write that happened finished; this asks
whether the write may happen at all. Because this refusal happens first, no PENDING gate row was
opened and the Stop hook will not block you for stopping here.

Your options:
  1. Wait for the freeze to lift (the honest default).
  2. Re-run with --dry-run to see what WOULD be written.
  3. If an event already has a PENDING gate row from before the freeze, close it:
       .venv/bin/python .claude/scripts/substrate.py waive --manifest <m.json> \\
           --reason "graph freeze {fz.get('issue', '')}: claims staged after it lifts"
  4. Genuine emergency: --freeze-override "<why>" (allowed, and logged as data).

Source of truth: .claude/references/graph-freeze.json""")
    return 4


def _ledger_path() -> str:
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID") or "_pending"
    return os.path.join(STATE_DIR, f"{sid}.substrate_gate.jsonl")


def ledger_mark(key: str, title: str, marker: str, reason: str | None = None, *, keep_if: tuple = (),
                phase: str = "post_event") -> None:
    """Upsert one row by key. keep_if: markers that must not be downgraded (idempotent add).
    phase: 'post_event' (key = Notion event page id) or 'pre_event' (key = 'research:' + page id — a DISTINCT key,
    because the gate never downgrades STAGED: a shared key would let a staged pre-event row satisfy the post-event
    gate). substrate-gate.sh reads `phase` to name the right fix."""
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
        row = {"key": key, "event": title, "marker": marker, "phase": phase,
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


# ---------------------------------------------------------------------------------------------
# Identity S1b-lite (YED-47; PRD approved 2026-09-19) — pure helpers, covered by --selftest.
# The premise was re-scoped on data (live probe 2026-09-19, re-run 2026-09-27): 0 exact company
# collisions, 1 exact person duplicate, and every other duplicate is a PARENTHETICAL TWIN
# ('AWS (Amazon)' / 'AWS') that a name_norm index would not have caught and that THIS producer minted.
# So: no DDL; one narrow company tier; tombstone-following resolvers; a human-only reversible merge.
# ---------------------------------------------------------------------------------------------
QUALIFIER_RE = re.compile(r"^(.*\S)\s*\(([^()]+)\)\s*$")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
AMBIGUITY_LEDGER = os.path.join(ROOT, ".claude", "artifacts", "identity-ambiguity.jsonl")
MERGE_LOG = os.path.join(ROOT, ".claude", "artifacts", "identity-merges.jsonl")
TOMBSTONE_DEPTH = 5           # merge refuses a tombstoned target, so a chain longer than this is corruption


def split_qualifier(name: str) -> tuple[str, str | None]:
    """'AWS (Amazon)' -> ('AWS', 'Amazon'); 'AWS' -> ('AWS', None). Only a TRAILING parenthetical counts."""
    m = QUALIFIER_RE.match(name or "")
    return (m.group(1).strip(), m.group(2).strip()) if m else ((name or "").strip(), None)


def web_host(url: str | None) -> str | None:
    """'https://www.AWS.amazon.com/x?y' -> 'aws.amazon.com'; empty -> None. Subdomains are NOT folded:
    aws.amazon.com vs amazon.com is a different host, which keeps that case unresolved and surfaced."""
    if not url or not str(url).strip():
        return None
    h = re.sub(r"^\s*(?:https?:)?//", "", str(url).strip().lower()).split("/")[0].split("?")[0]
    h = h.split("@")[-1].split(":")[0]
    return (h[4:] if h.startswith("www.") else h) or None


def resolve_company_tier(name: str, website: str | None, candidates: list[dict]) -> tuple[dict | None, str]:
    """Spec item 1 (YED-47). SCOPE: applies only when the INCOMING name carries a trailing qualifier.
    `Name (Qualifier)` resolves to `Name` when exactly one live candidate carries the bare name AND both
    website hosts exist and are equal. Returns (row, why); every other case is (None, why) and the caller
    creates + surfaces — it never guesses. A bare incoming name is never resolved to a qualified row."""
    base, qual = split_qualifier(name)
    if not qual:
        return None, "no qualifier"
    cands = [c for c in candidates if norm_text(c.get("name") or "") == norm_text(base)]
    if not cands:
        return None, "no bare-name candidate"
    if len(cands) > 1:
        return None, f"{len(cands)} bare-name candidates"
    hi, hc = web_host(website), web_host(cands[0].get("website"))
    if not hi or not hc:
        which = "both" if not (hi or hc) else ("incoming" if not hi else "candidate")
        return None, f"website host missing on {which}"
    if hi != hc:
        return None, f"website hosts differ ({hi} vs {hc})"
    return cands[0], f"qualifier tier: unique bare-name candidate + host {hc} agrees"


def _utcnow() -> str:
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------------------------
# YED-205 — the pre-event write path: Evidence Ledger parsing (pure, covered by --selftest).
# The research specialists (company-researcher / person-researcher / topic-landscape-analyst) each emit
#   ##### Evidence Ledger — <Name>
#   - claim: <≤15 words> | tier: web-verified | source: <site> | url: <URL> | date: <YYYY-MM-DD>
# and the synthesizer passes those rows through verbatim in its Evidence Set. They ARE the claims.
# ---------------------------------------------------------------------------------------------
RESEARCH_SECTION = "evidence_ledger"
# A heading ('##### Evidence Ledger — X') or, pre-mortem 2026-09-27, the same label set in bold on its own line.
LEDGER_HEAD_RE = re.compile(r"^(?:#{2,6}\s*|\*\*\s*)Evidence Ledger\s*[—–:-]\s*(.+?)\s*(?:\*\*)?\s*$", re.I)
# Pre-mortem 2026-09-27: a URL alone does not prove an email-signal row is public — a specialist can attach the
# company homepage to "open thread with their CEO about a pilot". A row whose SOURCE is a mailbox, or whose TEXT reads
# as correspondence, is private relationship state (ADR-9: HubSpot's), whatever URL it carries. Conservative on purpose.
MAILBOX_SOURCE_RE = re.compile(r"\b(gmail|inbox|mailbox|e-?mail thread|correspondence|dm|direct message|linkedin message)\b", re.I)
CORRESPONDENCE_RE = re.compile(r"\b(thread|replied|reply|emailed|e-?mailed|inbox|dm'?d|reached out|intro(?:duced)? (?:by|via)|"
                               r"last (?:reply|message|contact)|our (?:call|chat|conversation)|Alex)\b", re.I)
LEDGER_ROW_RE = re.compile(r"^\s*[-*]\s*claim\s*:\s*(.+)$", re.I)
LEDGER_FIELD_SPLIT = re.compile(r"\s*\|\s*(?=(?:tier|source|url|date)\s*:)", re.I)
TIER_MAP = {"web-verified": "web_verified", "web_verified": "web_verified",
            "email-signal": "email_signal", "email_signal": "email_signal",
            "notion-prior": "notion_prior", "notion_prior": "notion_prior"}
RESEARCH_CONF = {"web_verified": 0.7, "email_signal": 0.5}


# ---------------------------------------------------------------------------------------------
# YED-208 — published posts. A published Content Draft page mixes PUBLIC post text (the variants) with PRIVATE
# working notes (a preamble that can name an excluded confidential round, visual briefs, steering). Only the
# variant sections are ever embedded, and they still pass redact_body. Pure; covered by --selftest.
# ---------------------------------------------------------------------------------------------
# Layouts seen across the 41 published drafts (2026-09-27): '## Variant A — …', '# VARIANT A — …' (H1), '## Copy (ready to
# post)', '## ⭐ SHIP THIS — Primary', '## LinkedIn — Pre-Event Post', '## Primary / Alternate / Option / Version …'.
POST_SECTION_RE = re.compile(r"^[^\w]*(variant\b|post\b|linkedin\b|final\b|published\b|copy\b|ship this\b|primary\b|"
                             r"alternate\b|alt\b|option\b|version\b)", re.I)
POST_SKIP_RE = re.compile(r"(visual|carousel brief|first comment|comment|steer|notes?\b|brief\b|questions?)", re.I)
CHUNK_CHARS = 1800           # ~400 tokens: inside bge-small's 512-token window
MAX_POST_CHUNKS = 3


def post_chunks(body_md: str) -> list[dict]:
    """Published draft markdown -> [{'label', 'text'}], one per variant section (<= MAX_POST_CHUNKS). Only '##'/'###'
    sections whose heading names a post variant are taken; a draft with no such heading falls back to its body with
    the pre-heading preamble and any note/brief/comment sections removed. Everything passes redact_body."""
    body = redact_body(body_md or "")
    secs, cur, buf, pre = [], None, [], True
    for line in body.splitlines():
        h = re.match(r"^#{1,3}\s+(.+?)\s*$", line)
        if h:
            if cur is not None:
                secs.append((cur, "\n".join(buf)))
            cur, buf, pre = h.group(1).strip(), [], False
        elif not pre:
            buf.append(line)
    if cur is not None:
        secs.append((cur, "\n".join(buf)))
    picked = [(t, b) for t, b in secs if POST_SECTION_RE.match(clean_md(t).strip('"“ ')) and not POST_SKIP_RE.search(t.split("—")[0])]
    if not picked:                                   # no variant headings: every non-note section, preamble dropped
        picked = [(t, b) for t, b in secs if not POST_SKIP_RE.search(t)]
    out = []
    for t, b in picked[:MAX_POST_CHUNKS]:
        text = clean_md(b)
        if len(text) >= 80:
            out.append({"label": clean_md(t)[:80], "text": text[:CHUNK_CHARS]})
    return out


def research_source_key(notion_event_id: str) -> str:
    """One source_key per researched event. Post-event ensure-event recomputes it to attach these claims."""
    return sha("research:" + pid_variants(notion_event_id)[0])


def research_gate_key(notion_event_id: str) -> str:
    return "research:" + pid_variants(notion_event_id)[0]


def _public_url(u: str | None) -> str | None:
    u = (u or "").strip().strip("<>").strip()
    return u if re.match(r"^https?://[^\s/]+\.[^\s]+", u, re.I) else None


def parse_ledger(md: str) -> tuple[list[dict], dict[str, int]]:
    """Evidence Set / specialist returns -> (claim candidates, skip counts). Parsing only — zero inference.
    Decision 2 (spec): web-verified WITH a URL -> web_verified; email-signal WITH a public http(s) URL ->
    email_signal (a lead); email-signal without one is private correspondence -> skipped (relationship state is
    HubSpot's, ADR-9); notion-prior -> skipped (it came from the graph/Notion); a web-verified row missing its URL
    -> skipped (the specialist contract makes the URL mandatory). Every skip is counted, never silent."""
    out, skipped, entity = [], {}, None

    def skip(why: str):
        skipped[why] = skipped.get(why, 0) + 1
    for line in (md or "").splitlines():
        h = LEDGER_HEAD_RE.match(line)
        if h:
            entity = clean_md(h.group(1)).strip("[] ") or None
            continue
        if re.match(r"^#{1,6}\s", line):            # any other heading ends the current ledger
            entity = None
            continue
        m = LEDGER_ROW_RE.match(line)
        if not m or not entity:
            if m:
                skip("row_outside_a_ledger")
            continue
        parts = LEDGER_FIELD_SPLIT.split(m.group(1))
        fields = {"claim": clean_md(parts[0])}
        for p in parts[1:]:
            k, _, v = p.partition(":")
            fields[k.strip().lower()] = v.strip()
        tier = TIER_MAP.get((fields.get("tier") or "").strip().lower())
        url = _public_url(fields.get("url"))
        text = fields["claim"].strip(" .")
        if len(text) < 8 or text.startswith("["):   # empty / template placeholder
            skip("empty_or_template")
            continue
        if tier == "notion_prior":
            skip("notion_prior")
            continue
        if tier == "email_signal" and (not url or MAILBOX_SOURCE_RE.search(fields.get("source") or "")
                                       or CORRESPONDENCE_RE.search(text)):
            skip("email_signal_private")
            continue
        if tier == "web_verified" and not url:
            skip("web_verified_missing_url")
            continue
        if tier not in RESEARCH_CONF:
            skip("unknown_tier")
            continue
        date = (fields.get("date") or "").strip()
        date = date[:10] if re.match(r"^\d{4}-\d{2}-\d{2}", date) else None
        full = f"{entity}: {text}"                   # stands alone in retrieval
        out.append({"entity": entity, "text": full, "claim_key": claim_key(full), "tier": tier, "url": url,
                    "source": clean_md(fields.get("source") or "") or None, "date": date,
                    "confidence": RESEARCH_CONF[tier]})
    seen, uniq = set(), []
    for it in out:                                   # the same fact repeated across sections = one claim
        if it["claim_key"] in seen:
            skip("duplicate_row")
            continue
        seen.add(it["claim_key"])
        uniq.append(it)
    return uniq, skipped


def roster_match(heading: str, roster: list[tuple[str, str, str]]) -> tuple[str, str] | None:
    """Ledger heading -> (type, id) among THIS event's roster only (type, name, id). Tiers, first unique hit wins:
    exact normalized name; the name without a trailing '(Qualifier)'; then (pre-mortem 2026-09-27) name-token
    containment for COMPANIES AND TOPICS ONLY ('Soxton' ~ 'Soxton.AI', the same rule stage_claims uses for founder
    showcases). People are exact-only — no fuzzy person matching, ever (ADR-4 D3). Returns None when absent OR
    ambiguous at the first tier that has hits — never guessed; the caller counts it and stages the claim unlinked.
    Linking here only attaches a claim to an entity already on this event's roster; it never creates or merges one."""
    tiers = (lambda t, n: norm_text(n) == norm_text(heading),
             lambda t, n: norm_text(split_qualifier(n)[0]) == norm_text(split_qualifier(heading)[0]),
             lambda t, n: t != "person" and same_company(split_qualifier(heading)[0], split_qualifier(n)[0]))
    for test in tiers:
        hits = {(t, i) for t, n, i in roster if test(t, n)}
        if len(hits) == 1:
            return next(iter(hits))
        if len(hits) > 1:
            return None
    return None


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

    def embed(self, texts: list[str]) -> list[str]:
        """pgvector literals for `texts` (local bge-small, same space as every other claim; no metered API).
        A method so the offline selftest can substitute a stub."""
        if self.dry:
            return ["[dry-run: not embedded]"] * len(texts)
        sys.path.insert(0, DOCKB)
        from dockb_common import embed_passages, vec_literal
        return [vec_literal(v) for v in embed_passages(texts)]

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
    def follow(self, table: str, row: dict | None) -> dict | None:
        """Spec item 3 (YED-47): a row soft-merged away (metadata.merged_into) resolves to its live target.
        Chain-safe: `merge` refuses a tombstoned target, so a chain deeper than TOMBSTONE_DEPTH is corruption
        and fails loud rather than guessing. A dangling merged_into fails loud too."""
        hops = 0
        while row and (row.get("metadata") or {}).get("merged_into"):
            if hops >= TOMBSTONE_DEPTH:
                raise SystemExit(f"{table} {row.get('id')}: tombstone chain deeper than {TOMBSTONE_DEPTH} — refusing to guess")
            tid = row["metadata"]["merged_into"]
            tgt = self.get(f"/{table}?id=eq.{q(tid)}&select=*&limit=1")
            if not tgt:
                raise SystemExit(f"{table} {row.get('id')}: merged_into {tid} does not exist — revert or repair the tombstone")
            row, hops = tgt[0], hops + 1
            self.stats.bump(table, "followed_tombstone")
        return row

    def by_pid(self, table: str, pid: str | None, select: str = "*") -> dict | None:
        v = pid_variants(pid)
        if not v:
            return None
        rows = self.get(f"/{table}?notion_page_id=in.({','.join(q(x) for x in v)})&select={select}&limit=2")
        return self.follow(table, rows[0]) if rows else None

    def live_by_name(self, table: str, name: str) -> list[dict]:
        """Every row whose name equals `name` (case/space-insensitive), each followed through its tombstone
        and de-duplicated by id — a tombstone and its target count once."""
        rows = self.get(f"/{table}?name=ilike.{q(name.replace('*', ''))}&select=*&limit=5")
        out: dict[str, dict] = {}
        for r in rows:
            if norm_text(r["name"]) == norm_text(name):
                r = self.follow(table, r)
                out.setdefault(r["id"], r)
        return list(out.values())

    def by_name(self, table: str, name: str) -> dict | None:
        rows = self.live_by_name(table, name)
        return rows[0] if rows else None

    # -- entities --------------------------------------------------------------------------------
    def _fill_missing(self, table: str, row: dict, fields: dict):
        patch = {k: v for k, v in fields.items() if v not in (None, "", []) and row.get(k) in (None, "", [])}
        if patch and not str(row.get("id", "")).startswith("dry:"):
            self.patch(table, f"id=eq.{row['id']}", patch)
            self.stats.bump(table, "enriched")

    def ensure_company(self, e: dict) -> str:   # NOTE: same-name ambiguity is surfaced, never silently duplicated
        fields = {"name": e["name"], "website": e.get("website"), "description": e.get("description"),
                  "linkedin_url": e.get("linkedin_url"), "notion_page_id": (pid_variants(e.get("notion_page_id")) or [None])[-1]}
        row = self.by_pid("company", e.get("notion_page_id")) or self.by_name("company", e["name"])
        if not row:
            base, qual = split_qualifier(e["name"])
            if qual:
                # Spec item 1 — the resolution tier, scoped to an incoming name WITH a qualifier.
                cands = self.live_by_name("company", base)
                row, why = resolve_company_tier(e["name"], e.get("website"), cands)
                if row:
                    self.stats.bump("company", "qualifier_resolved")
                elif cands:
                    self.note_ambiguous("company", e["name"], cands, why)
                # zero bare-name candidates: an ORDINARY create, not an ambiguity — there is nothing it could
                # have been confused with, so it is not surfaced (judge, 2026-09-27: say so explicitly).
            else:
                # A bare incoming name whose qualified twin(s) exist ('AWS' vs 'AWS (Amazon)'): the tier is
                # one-directional by spec, so this is created AND surfaced — never resolved to a qualified row.
                twins = self.get(f"/company?name=ilike.{q(base.replace('*', '') + ' (*')}&select=*&limit=5")
                twins = list({r["id"]: r for r in (self.follow("company", t) for t in twins
                              if norm_text(split_qualifier(t["name"])[0]) == norm_text(base))}.values())
                if twins:
                    self.note_ambiguous("company", e["name"], twins,
                                        "qualified twin(s) exist; bare -> qualified is never auto-resolved")
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

    def note_ambiguous(self, table: str, name: str, rivals: list[dict], why: str) -> None:
        """A same-name row exists but was not matched. Creating a second row may be right (two real people)
        or wrong (one person who changed employer — the commonest event in this graph). Either way it is a
        judgement, so it is never silent: it prints, it counts, and it lands in a review file for S1b (YED-47).
        """
        self.stats.bump(table, "ambiguous_name")
        detail = "; ".join(f"{r.get('name')} [{str(r.get('id'))[:8]} · {r.get('source') or '—'}]" for r in rivals[:3])
        sys.stderr.write(f"  ⚠️  {table} '{name}': creating a NEW row though {len(rivals)} candidate row(s) exist "
                         f"({why}) → {detail}. Review for merge: substrate.py merge --dry-run (YED-47).\n")
        if not self.dry:
            # The ledger is created on the first live ambiguity. Its absence means "no data yet", not
            # "no ambiguities". identity_probe.py counts DISTINCT (table, name) per window, so a re-run
            # that re-surfaces one ambiguity cannot inflate the DDL re-trigger (>=10 distinct in 30 days).
            path = AMBIGUITY_LEDGER
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": _utcnow(), "session": os.environ.get("CLAUDE_CODE_SESSION_ID", "_pending"),
                                    "table": table, "name": name, "why": why,
                                    "existing": [{"id": r.get("id"), "name": r.get("name"), "source": r.get("source"),
                                                  "company_id": r.get("company_id")} for r in rivals[:5]]}) + "\n")

    def ensure_person(self, e: dict) -> str:
        company_id = self.ensure_company({"name": e["company"]}) if e.get("company") else None
        li = (e.get("linkedin_url") or "").strip() or None
        fields = {"name": e["name"], "title": clean_title(e.get("title")), "company_id": company_id, "linkedin_url": li,
                  "notion_page_id": (pid_variants(e.get("notion_page_id")) or [None])[0]}  # persons: undashed
        row = self.by_pid("person", e.get("notion_page_id"))
        if not row and li:
            core = re.sub(r"^https?://(www\.)?", "", li.rstrip("/").lower())
            rows = self.get(f"/person?linkedin_url=ilike.*{q(core)}*&select=*&limit=3")
            row = self.follow("person", rows[0]) if len(rows) == 1 else None
        if not row:
            same_name = self.live_by_name("person", e["name"])      # followed + de-duplicated (spec item 3)
            rows = [r for r in same_name if company_id is None or r.get("company_id") in (None, company_id)]
            row = rows[0] if len(rows) == 1 else None                # ambiguous name -> create, never guess
            if not row and same_name:
                # the commonest case here is ONE person who changed employer, not two people with one name
                self.note_ambiguous("person", e["name"], same_name,
                                    "different company_id" if rows != same_name else f"{len(rows)} same-name matches")
        if row:
            self.stats.bump("person", "matched")
            self._fill_missing("person", row, {k: v for k, v in fields.items() if k != "name"})
            return row["id"]
        # The per-run cache is keyed by name AND company for persons. Keyed by name alone it handed the
        # second 'Angie Jones' in one run the first one's id right after note_ambiguous had said a NEW row
        # was being created — caught by the YED-47 offline selftest, 2026-09-27.
        ckey = f"{e['name']}|{company_id or ''}"
        if (hit := self._cached("person", ckey)):
            return hit
        self.stats.bump("person", "created")
        return self._remember("person", ckey,
                              self.post("person", {**{k: v for k, v in fields.items() if v}, "source": SOURCE})[0]["id"])

    def ensure_entity(self, e: dict) -> tuple[str, str]:
        t = e["type"]
        fn = {"company": self.ensure_company, "person": self.ensure_person, "topic": self.ensure_topic}.get(t)
        if not fn:
            raise SystemExit(f"unknown entity type {t!r}")
        return t, fn(e)

    # -- soft-merge (spec item 2, YED-47; ADR-4 D3: tombstone, never delete) ----------------------
    EDGE_TABLES = ("event_entity", "claim_entity", "document_entity")

    def say(self, msg: str) -> None:
        if not getattr(self, "quiet", False):
            print(msg)

    def entity_ref(self, table: str, ref: str) -> dict:
        """id or exact name -> the row itself, NOT followed (merge must see the tombstone, revert needs it)."""
        if UUID_RE.match(ref or ""):
            rows = self.get(f"/{table}?id=eq.{q(ref)}&select=*&limit=1")
        else:
            rows = [r for r in self.get(f"/{table}?name=ilike.{q(ref.replace('*', ''))}&select=*&limit=5")
                    if norm_text(r["name"]) == norm_text(ref)]
        if len(rows) != 1:
            raise SystemExit(f"merge: {table} {ref!r} -> {len(rows)} row(s); need exactly one (pass the id)")
        return rows[0]

    def _patch_try(self, table: str, flt: str, row: dict) -> tuple[bool, int, int]:
        """PATCH that reports instead of aborting: (ok, http status, rows touched). A 409 is the unique-edge
        collision (the target already carries this edge) and is the one status merge treats as 'keep on
        source' — nothing is ever deleted to make room."""
        guard(table, row, op="update")
        if self.dry:
            return True, 200, 1
        st, body = req("PATCH", f"/{table}?{flt}", row, prefer="return=representation")
        n = len(body) if isinstance(body, list) else 0
        return st in (200, 204) and n > 0, st, n

    @staticmethod
    def _edge_key(table: str, r: dict) -> dict:
        if "id" in r:                                   # event_entity has a surrogate id
            return {"id": r["id"]}
        owner = "claim_id" if table == "claim_entity" else "document_id"
        return {owner: r[owner], "entity_type": r["entity_type"], "role": r["role"]}

    def merge_plan(self, table: str, src: dict) -> dict:
        edges = []
        for et in self.EDGE_TABLES:
            for r in self.get(f"/{et}?entity_type=eq.{table}&entity_id=eq.{q(src['id'])}&select=*"):
                edges.append({"table": et, "key": self._edge_key(et, r), "role": r.get("role"),
                              "event_id": r.get("event_id")})
        persons = [r["id"] for r in self.get(f"/person?company_id=eq.{q(src['id'])}&select=id")] if table == "company" else []
        return {"edges": edges, "persons": persons, "engagement": src.get("engagement_count") or 0,
                "last_engaged_at": src.get("last_engaged_at")}

    def _log_merge(self, row: dict) -> None:
        os.makedirs(os.path.dirname(MERGE_LOG), exist_ok=True)
        with open(MERGE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({**row, "ts": _utcnow(),
                                "session": os.environ.get("CLAUDE_CODE_SESSION_ID", "_pending")}) + "\n")

    def merge(self, table: str, src: dict, tgt: dict, reason: str) -> int:
        """Human-only, reversible. Re-points every edge it can from src to tgt, transfers engagement, then
        tombstones src: metadata.merged_into + metadata.merge (the snapshot --revert replays). DELETES NOTHING:
        an edge the target already carries stays on the source (recorded as kept_on_source). Idempotent:
        a tombstoned source reports 'already merged' and changes nothing."""
        if src["id"] == tgt["id"]:
            raise SystemExit("merge: source == target")
        if (src.get("metadata") or {}).get("merged_into"):
            self.say(f"  ✅ {table} '{src['name']}' already merged into {src['metadata']['merged_into']} — nothing to do")
            return 0
        if (tgt.get("metadata") or {}).get("merged_into"):
            raise SystemExit(f"merge: target '{tgt['name']}' is itself a tombstone (merged_into "
                             f"{tgt['metadata']['merged_into']}) — merge into THAT row; chains are not minted")
        plan = self.merge_plan(table, src)
        self.say(f"  {table} '{src['name']}' [{src['id'][:8]}] → '{tgt['name']}' [{tgt['id'][:8]}]")
        self.say(f"     re-point {len(plan['edges'])} edge(s) "
                 + ", ".join(f"{e['table']}:{e['role']}" for e in plan["edges"][:8]) + (" …" if len(plan["edges"]) > 8 else ""))
        if plan["persons"]:
            self.say(f"     re-point person.company_id on {len(plan['persons'])} person(s)")
        self.say(f"     engagement +{plan['engagement']} · then tombstone the source (metadata.merged_into) — delete nothing")
        if self.dry:
            self.say("     DRY RUN — no writes. Alex runs the live merge (every merge is human-approved).")
            return 0
        for e in plan["edges"]:
            flt = "&".join(f"{k}=eq.{q(v)}" for k, v in e["key"].items()) + f"&entity_id=eq.{q(src['id'])}"
            ok, st, n = self._patch_try(e["table"], flt, {"entity_id": tgt["id"]})
            e["moved"], e["status"] = bool(ok and n == 1), st
            if not e["moved"]:
                e["kept_on_source"] = "conflict: target already carries this edge" if st == 409 else f"http {st}, {n} row(s)"
            self.stats.bump(e["table"], "repointed" if e["moved"] else "kept_on_source")
        moved_persons = []
        for pid in plan["persons"]:
            ok, st, n = self._patch_try("person", f"id=eq.{q(pid)}&company_id=eq.{q(src['id'])}", {"company_id": tgt["id"]})
            if ok:
                moved_persons.append(pid)
        self.stats.bump("person", "company_repointed", len(moved_persons))
        if plan["engagement"] or plan["last_engaged_at"]:
            last = max([x for x in (tgt.get("last_engaged_at"), plan["last_engaged_at"]) if x], default=None)
            patch = {"engagement_count": (tgt.get("engagement_count") or 0) + plan["engagement"]}
            if last:
                patch["last_engaged_at"] = last
            self.patch(table, f"id=eq.{q(tgt['id'])}", patch)
        snapshot = {"merged_into": tgt["id"], "merged_into_name": tgt.get("name"), "ts": _utcnow(), "reason": reason,
                    "session": os.environ.get("CLAUDE_CODE_SESSION_ID", "_pending"),
                    "edges": plan["edges"], "persons": moved_persons, "engagement_moved": plan["engagement"],
                    "target_last_engaged_before": tgt.get("last_engaged_at")}
        meta = dict(src.get("metadata") or {})
        meta.update({"merged_into": tgt["id"], "merge": snapshot})
        # engagement was TRANSFERRED, not copied: the tombstone keeps 0 so a relevance recompute cannot count
        # it twice (pre-mortem 2026-09-27); revert puts it back from engagement_moved.
        # relevance_score is nulled (nulling is always allowed): the hub's viewpoint filters `relevance_score=gt.0`
        # and recompute_relevance skips tombstones, so a merged topic leaves the dashboard the same day.
        # engagement_count / relevance_score are _MI_COMMON columns on all three mergeable tables (company,
        # person, topic — spine_client.ALLOW), so this PATCH is deliberately unconditional, not topic-only.
        self.patch(table, f"id=eq.{q(src['id'])}", {"metadata": meta, "engagement_count": 0, "relevance_score": None})
        self.stats.bump(table, "tombstoned")
        kept = [e for e in plan["edges"] if not e["moved"]]
        self._log_merge({"event": "merge", "table": table, "from": src["id"], "from_name": src.get("name"),
                         "into": tgt["id"], "into_name": tgt.get("name"), "reason": reason,
                         "edges_moved": len(plan["edges"]) - len(kept), "edges_kept_on_source": len(kept),
                         "persons_repointed": len(moved_persons)})
        self.say(f"     ✅ merged — {len(plan['edges']) - len(kept)} edge(s) re-pointed, {len(kept)} kept on the tombstone "
                 f"(target already had them), {len(moved_persons)} person(s) re-pointed. Source row still exists. "
                 f"Undo: merge --revert --table {table} --from {src['id']}")
        return 0

    def revert(self, table: str, src: dict) -> int:
        """Replay the snapshot backwards. Each edge is restored only if it still sits on the merge target
        (a later move is left alone and reported), engagement subtracts what was moved, and the tombstone
        marker comes off with the snapshot filed under metadata.merge_history."""
        meta = dict(src.get("metadata") or {})
        snap = meta.get("merge")
        if not meta.get("merged_into") or not snap:
            raise SystemExit(f"revert: {table} '{src.get('name')}' is not a tombstone with a snapshot — nothing to revert")
        tgt_id = meta["merged_into"]
        moved = [e for e in snap.get("edges", []) if e.get("moved")]
        self.say(f"  revert {table} '{src['name']}' [{src['id'][:8]}] ← '{snap.get('merged_into_name')}' [{tgt_id[:8]}]: "
                 f"restore {len(moved)} edge(s), {len(snap.get('persons', []))} person(s), engagement −{snap.get('engagement_moved', 0)}")
        if self.dry:
            self.say("     DRY RUN — no writes.")
            return 0
        restored = skipped = 0
        for e in moved:
            flt = "&".join(f"{k}=eq.{q(v)}" for k, v in e["key"].items()) + f"&entity_id=eq.{q(tgt_id)}"
            ok, st, n = self._patch_try(e["table"], flt, {"entity_id": src["id"]})
            restored += 1 if ok else 0
            skipped += 0 if ok else 1
        for pid in snap.get("persons", []):
            ok, _, _ = self._patch_try("person", f"id=eq.{q(pid)}&company_id=eq.{q(tgt_id)}", {"company_id": src["id"]})
        if snap.get("engagement_moved"):
            tgt = self.get(f"/{table}?id=eq.{q(tgt_id)}&select=engagement_count&limit=1")
            if tgt:
                self.patch(table, f"id=eq.{q(tgt_id)}",
                           {"engagement_count": max(0, (tgt[0].get("engagement_count") or 0) - snap["engagement_moved"])})
        meta.pop("merged_into", None)
        meta.pop("merge", None)
        meta.setdefault("merge_history", []).append({**snap, "reverted_at": _utcnow()})
        self.patch(table, f"id=eq.{q(src['id'])}", {"metadata": meta, "engagement_count": snap.get("engagement_moved", 0) or 0})
        self.stats.bump(table, "reverted")
        self._log_merge({"event": "revert", "table": table, "from": src["id"], "from_name": src.get("name"),
                         "was_into": tgt_id, "edges_restored": restored, "edges_skipped": skipped})
        self.say(f"     ✅ reverted — {restored} edge(s) restored, {skipped} skipped (moved again since), tombstone cleared")
        return 0

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
        if (row or {}).get("kind", ev.get("kind")) == "attended":   # decision 1: attach onto an ATTENDED row only
            self.attach_research(ev, eid)
        return eid

    def attach_research(self, ev: dict, eid: str) -> None:
        """YED-205 decision 1: pre-event research claims were staged with NO event (attendance is never inferred).
        Once an event row exists for the same Notion page, attach them, and their brief document, to it. Only rows
        still unattached are touched, so a re-run is a no-op. Scope: the event's own Notion page id; nothing else."""
        if not ev.get("notion_page_id") or str(eid).startswith("dry:"):
            return
        rk = research_source_key(ev["notion_page_id"])
        loose = self.get(f"/claim?source_key=eq.{rk}&event_id=is.null&select=id,document_id")
        if not loose:
            return
        self.patch("claim", f"source_key=eq.{rk}&event_id=is.null", {"event_id": eid})
        self.stats.bump("claim", "research_attached", len(loose))
        docs = sorted({c["document_id"] for c in loose if c.get("document_id")})
        if docs:
            self.patch("documents", f"id=in.({','.join(docs)})&event_id=is.null", {"event_id": eid})

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
            "embedding_model": EMBED_MODEL, "metadata": d.get("metadata"),
        }.items() if v not in (None, "", {})}
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
    vectors = g.embed([it["text"] for it in new]) if new else []   # local bge-small; no metered API
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
    # claim_key -> claim id, fetched ONCE and shared by the three linking blocks below (speakers,
    # showcase companies, questions). Was re-queried per block; the Gemini seat flagged it 2026-09-25.
    ids: dict[str, str] = {}
    # speakers -> claim_entity(asserted_by). Resolved ONLY against persons already linked to THIS
    # event (the roster ensure-event wrote), by name-token containment: 'Mila Zhou' matches
    # 'Miaolai (Mila) Zhou'. Scoping to the roster is what makes the fuzzy match safe.
    speakers = {it["speaker"] for it in items if it["speaker"]}
    if speakers and not g.dry:
        ids = ids or {r["claim_key"]: r["id"] for r in g.get(f"/claim?source_key=eq.{skey}&select=id,claim_key")}
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
        ids = ids or {r["claim_key"]: r["id"] for r in g.get(f"/claim?source_key=eq.{skey}&select=id,claim_key")}
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
    # question claims -> claim_entity(topic, about) for the topic(s) each question MOST associates
    # with, chosen among THIS event's roster topics by embedding similarity (same local bge-small the
    # claims are embedded with — no new dependency, no metered API). Alex's call 2026-09-25: per-question
    # association, not the whole roster. The event anchor is already set (claim.event_id above); the
    # topic anchor is what makes a question resurface when the TOPIC recurs at a different event.
    # Selection: the top topic always, plus any near-tie within 0.03 cosine, capped at 3 — a question
    # genuinely spanning two topics gets both, one that clearly belongs to one topic gets one.
    # Roster scoping keeps the fuzzy match safe, exactly as it does for speaker attribution above.
    # Schema already permits it: claim_entity's CHECKs allow entity_type='topic' + role='about'.
    questions = [it for it in items if it["claim_type"] == "question"]
    if questions and not g.dry:
        ids = ids or {r["claim_key"]: r["id"] for r in g.get(f"/claim?source_key=eq.{skey}&select=id,claim_key")}
        topic_ids = [r["entity_id"] for r in
                     g.get(f"/event_entity?event_id=eq.{eid}&entity_type=eq.topic&select=entity_id")]
        trows = g.get(f"/topic?id=in.({','.join(topic_ids)})&select=id,name") if topic_ids else []
        if not trows:
            g.stats.bump("claim_entity", "question_topic_unresolved", len(questions))
        else:
            sys.path.insert(0, DOCKB)
            from dockb_common import embed_passages
            qvecs = embed_passages([it["text"] for it in questions])
            tvecs = embed_passages([t["name"] for t in trows])

            def cos(a: list[float], b: list[float]) -> float:
                dot = sum(x * y for x, y in zip(a, b))
                na = sum(x * x for x in a) ** 0.5 or 1.0
                nb = sum(y * y for y in b) ** 0.5 or 1.0
                return dot / (na * nb)

            links = []
            for it, qv in zip(questions, qvecs):
                if it["claim_key"] not in ids:
                    continue
                ranked = sorted(((cos(qv, tv), t) for tv, t in zip(tvecs, trows)), key=lambda x: -x[0])
                top = ranked[0][0]
                # Fan out to near-ties only when the top match is itself confident. THRESHOLDS ARE
                # PROVISIONAL, derived from a dry-check of only FOUR real questions against seven topic
                # names (2026-09-25) — not a calibration run. In that check the three clean hits scored
                # 0.68–0.76 with a ≥0.07 margin; the one question with NO real home on the roster scored
                # a flat 0.60/0.59/0.59 and the near-tie rule scattered it across three topics, one plainly
                # wrong. Flat + weak means "uncertain", so commit to the single best topic and make the
                # weakness visible via the stat below. Revisit 0.65/0.03 once `question_topic_weak_match`
                # has accumulated across real runs; the judge (2026-09-25) rightly flagged n=4 as thin.
                if top >= 0.65:
                    chosen = [t for s, t in ranked if s >= top - 0.03][:3]
                else:
                    chosen = [ranked[0][1]]
                    g.stats.bump("claim_entity", "question_topic_weak_match")
                links += [{"claim_id": ids[it["claim_key"]], "entity_type": "topic", "entity_id": t["id"],
                           "role": "about"} for t in chosen]
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


def stage_research(g: Graph, md: str, manifest: dict, *, brief_ref: str | None) -> int:
    """YED-205 — the pre-event write. Spec: .claude/notes/yed-205-spec-2026-09-27.md.
    Roster entities -> the research_brief document -> one claim per admitted Evidence Ledger row, linked
    claim_entity(about) to its heading's entity (roster-scoped). No event row is created (ADR-10 D9); if one
    already exists for this page (a re-run after attendance), claims attach to it. Returns 3 on zero claims
    (loud; the gate stays PENDING), 5 when the manifest lacks the Notion event page id (4 is the graph freeze's)."""
    ev = manifest.get("event") or {}
    if not ev.get("notion_page_id"):
        sys.stderr.write("stage-research: manifest.event.notion_page_id is required (it keys the claims + the gate)\n")
        return 5
    items, skipped = parse_ledger(md)
    for why, n in sorted(skipped.items()):
        g.stats.bump("ledger_row", f"skipped_{why}", n)
    if not items:
        sys.stderr.write("LOUD FAILURE: 0 admissible Evidence Ledger rows. Expected '##### Evidence Ledger — <Name>' "
                         "headings with '- claim: … | tier: web-verified | source: … | url: … | date: …' rows. "
                         f"Skipped: {skipped or 'nothing matched'}. If the synthesizer dropped the headings, pass the "
                         "raw specialist returns instead.\n")
        return 3
    roster = []
    for e in manifest.get("entities", []):
        t, iid = g.ensure_entity(e)
        if iid:
            roster.append((t, e["name"], iid))
    existing = g.find_event(ev)                      # never created here — only found (re-run after attendance)
    eid = existing["id"] if existing else None
    doc_id = None
    if brief_ref:
        doc_id = g.ensure_document({"external_ref": brief_ref, "title": f"Research brief — {ev.get('title', '')}",
                                    "source_type": "research_brief", "body_text": redact_body(md),
                                    "doc_date": (ev.get("event_date") or "")[:10] or None,
                                    "produced_by": "/event-deep-research",
                                    "metadata": {"notion_event_id": pid_variants(ev["notion_page_id"])[0],
                                                 "phase": "pre_event"}}, event_id=eid)
    skey = research_source_key(ev["notion_page_id"])
    have = {r["claim_key"] for r in g.get(f"/claim?source_key=eq.{skey}&select=claim_key")}
    new = [it for it in items if it["claim_key"] not in have]
    g.stats.bump("claim", "matched", len(items) - len(new))
    fallback = (ev.get("event_date") or "")[:10] or None
    rows = []
    for it, vec in zip(new, g.embed([it["text"] for it in new]) if new else []):
        rows.append({k: v for k, v in {
            "source_key": skey, "claim_key": it["claim_key"], "claim_text": it["text"], "claim_type": "fact",
            "locator": {"section": RESEARCH_SECTION, "entity": it["entity"], "source": it["source"], "url": it["url"]},
            "document_id": doc_id, "event_id": eid, "provenance_tier": it["tier"], "confidence": it["confidence"],
            "asserted_at": it["date"] or fallback, "status": "candidate", "extractor": "parse", "lane": "research",
            "embedding": vec, "embedding_model": EMBED_MODEL,
            "metadata": {"phase": "pre_event", "url": it["url"],
                         "notion_event_id": pid_variants(ev["notion_page_id"])[0]},
        }.items() if v is not None})
    if rows:
        g.stats.bump("claim", "created", len(rows))
        g.post("claim", rows, prefer="resolution=ignore-duplicates,return=minimal", on_conflict="source_key,claim_key")
    ids = {r["claim_key"]: r["id"] for r in g.get(f"/claim?source_key=eq.{skey}&select=id,claim_key")} if not g.dry else {}
    links, unresolved = [], set()
    for it in items:
        hit = roster_match(it["entity"], roster)
        if not hit:
            unresolved.add(it["entity"])
            continue
        if it["claim_key"] in ids:
            links.append({"claim_id": ids[it["claim_key"]], "entity_type": hit[0], "entity_id": hit[1], "role": "about"})
    g.stats.bump("claim_entity", "about_unresolved_heading", len(unresolved))
    if links:
        g.stats.bump("claim_entity", "linked (idempotent)", len(links))
        g.post("claim_entity", links, prefer="resolution=ignore-duplicates,return=minimal",
               on_conflict="claim_id,entity_type,entity_id,role")
    by_tier: dict[str, int] = {}
    for it in items:
        by_tier[it["tier"]] = by_tier.get(it["tier"], 0) + 1
    # the exact Step 4.2d line, so the command can paste it into the Step 6 summary unchanged
    print(f"Graph: {len(items)} research claims (web {by_tier.get('web_verified', 0)} · email-lead "
          f"{by_tier.get('email_signal', 0)}) · skipped {sum(skipped.values())} {skipped or ''} · unlinked headings "
          f"{', '.join(sorted(unresolved)) or 'none'} · event row: {'attached' if eid else 'none (pre-event)'}")
    return 0


def publish_posts(g: Graph, manifest: dict) -> int:
    """YED-208 — the `published` producer. Spec: .claude/notes/yed-208-spec-2026-09-27.md.
    Manifest: {"posts": [{"notion_page_id", "title", "content_type", "published_url", "published_date", "event_date",
               "goal", "target", "outcome", "outcome_value", "outcome_date",
               "event_notion_ids": [<every covered event's page id; a roundup covers several>],
               "topics": [{"name"?, "notion_page_id"}], "people": [{"name"?, "notion_page_id", "company"?}],
               "body_md": "<page markdown; optional for a post already in the graph>" | "body_path": "<file>"}]}
    Id-only relations (the Notion SQL export gives page ids, not names) resolve by page id and are never created
    nameless. Publish date: explicit published_date, else 'Posted YYYY-MM-DD' in the LinkedIn-export Outcome Value,
    else the earliest covered event's date.
    Per post: ensure event(kind='published') -> edges (own topics + people + the covered event's topics) ->
    document(linkedin_post, public_ok) + variant chunks -> artifact_outcome (upsert). One post's PII refusal is
    counted and skipped; it never aborts the others."""
    posts = manifest.get("posts") or []
    if not posts:
        sys.stderr.write("publish: manifest has no posts\n")
        return 3
    done = 0
    for p in posts:
        title = (p.get("title") or "").strip()
        if not p.get("published_url"):
            g.stats.bump("post", "skipped_no_url")
            continue
        if not p.get("notion_page_id"):
            g.stats.bump("post", "skipped_no_page_id")
            continue
        pid = pid_variants(p["notion_page_id"])[0]
        if not p.get("body_md") and p.get("body_path"):      # a file keeps big bodies out of the manifest
            p = {**p, "body_md": open(p["body_path"], encoding="utf-8").read()}
        try:
            chunks = post_chunks(p.get("body_md") or "")
            for c in chunks:                          # guard the text FIRST: a refused post writes nothing at all
                guard("doc_chunks", {"content": c["text"], "locator": {"variant": c["label"]}})
            covered_ids = [x for x in (p.get("event_notion_ids") or ([p["event_notion_id"]] if p.get("event_notion_id") else [])) if x]
            covered = [r for r in (g.by_pid("event", x, select="id,event_date") for x in covered_ids) if r]
            g.stats.bump("post", "covered_event_not_in_graph", len(covered_ids) - len(covered))
            # Notion has no published-date property. Never the outcome-grading date.
            posted = re.search(r"Posted (\d{4}-\d{2}-\d{2})", p.get("outcome_value") or "")
            when = (p.get("published_date") or (posted.group(1) if posted else None) or p.get("event_date")
                    or min((str(r.get("event_date"))[:10] for r in covered if r.get("event_date")), default=None))
            ev = {"notion_page_id": pid, "title": title, "kind": "published", "url": p["published_url"], "event_date": when}
            eid = g.ensure_event({"event": ev, "entities": []})
            want = [("topic", g.ensure_topic(t), "tagged_topic") for t in p.get("topics", []) if t.get("name") or t.get("notion_page_id")]
            for x in p.get("people", []):
                if x.get("name"):
                    want.append(("person", g.ensure_person(x), "subject"))
                else:                                 # id-only: resolve, never create a nameless person
                    row = g.by_pid("person", x.get("notion_page_id"), select="*")
                    want.append(("person", row["id"] if row else None, "subject"))
                    g.stats.bump("person", "matched" if row else "skipped_id_only_absent")
            for c in covered:                         # decision 3: inherit every covered event's topics
                for r in g.get(f"/event_entity?event_id=eq.{c['id']}&entity_type=eq.topic&select=entity_id"):
                    want.append(("topic", r["entity_id"], "tagged_topic"))
            have = set()
            if not str(eid).startswith("dry:"):
                have = {(r["entity_type"], r["entity_id"], r["role"])
                        for r in g.get(f"/event_entity?event_id=eq.{eid}&select=entity_type,entity_id,role")}
            rows = [{"event_id": eid, "entity_type": t, "entity_id": i, "role": role}
                    for t, i, role in dict.fromkeys(want) if i and (t, i, role) not in have]
            if rows:
                g.stats.bump("event_entity", "created", len(rows))
                g.post("event_entity", rows, prefer="resolution=ignore-duplicates,return=minimal",
                       on_conflict="event_id,entity_type,entity_id,role")
            ref = f"notion:{pid}"
            cur = g.get(f"/documents?external_ref=eq.{q(ref)}&is_current=is.true&select=id&limit=1")
            if p.get("body_md") and not chunks:
                g.stats.bump("post", "no_post_text_found")
            if chunks or not cur:
                body = "\n\n".join(c["text"] for c in chunks) or title
                doc_id = g.ensure_document({
                    "external_ref": ref, "title": title, "source_type": "linkedin_post", "body_text": body,
                    "doc_date": (when or "")[:10] or None, "produced_by": "linkedin",
                    "visibility": "public_ok", "notion_page_id": pid,
                    "metadata": {"published_url": p["published_url"], "content_type": p.get("content_type"),
                                 "about_event_notion_ids": [pid_variants(x)[0] for x in covered_ids] or None,
                                 "variants": len(chunks)}}, event_id=eid)
                if chunks and not str(doc_id).startswith("dry:"):
                    have_ix = {r["chunk_index"] for r in g.get(f"/doc_chunks?document_id=eq.{doc_id}&select=chunk_index")}
                    new = [(i, c) for i, c in enumerate(chunks) if i not in have_ix]
                    if new:
                        vecs = g.embed([f"{title}\n{c['text']}" for _, c in new])
                        g.post("doc_chunks", [{"document_id": doc_id, "chunk_index": i, "content": c["text"],
                                               "embedding": v, "token_count": len(c["text"]) // 4,
                                               "locator": {"variant": c["label"], "url": p["published_url"]}}
                                              for (i, c), v in zip(new, vecs)],
                               prefer="resolution=ignore-duplicates,return=minimal", on_conflict="document_id,chunk_index")
                        g.stats.bump("doc_chunks", "created", len(new))
            else:
                doc_id = cur[0]["id"]
                g.stats.bump("documents", "matched")
            outcome = {k: v for k, v in {
                "document_id": doc_id, "goal": p.get("goal"), "target": p.get("target"),
                "outcome": p.get("outcome") if p.get("outcome") in ("hit", "partial", "miss", "pending", "na") else None,
                "outcome_value": p.get("outcome_value"), "outcome_date": p.get("outcome_date"), "source": "notion_sync",
            }.items() if v not in (None, "")}
            if len(outcome) > 2 and not str(doc_id).startswith("dry:"):
                g.post("artifact_outcome", outcome, prefer="resolution=merge-duplicates,return=minimal",
                       on_conflict="document_id")
                g.stats.bump("artifact_outcome", "upserted")
            done += 1
        except PIIViolation as e:
            g.stats.bump("post", "refused_pii")
            sys.stderr.write(f"  ⚠️  post {title[:60]!r} refused by the ADR-9 guard, skipped: {e}\n")
    print(f"publish: {done}/{len(posts)} posts in the graph · skipped {len(posts) - done}")
    return 0


def published_refs(g: Graph) -> list[str]:
    """Undashed Notion page ids of every published post already in the graph."""
    rows = g.get("/documents?source_type=eq.linkedin_post&is_current=is.true&select=external_ref&limit=2000")
    return sorted({r["external_ref"].split(":", 1)[1] for r in rows if str(r.get("external_ref", "")).startswith("notion:")})


def source_key_for_topic_questions(notion_topic_id: str) -> str:
    return sha("notion_topic_questions:" + pid_variants(notion_topic_id)[0])


# Real banks (inspected 2026-09-25, 200 topics) come in THREE shapes: numbered lines split by
# <br>/newline; prose joined with " · " (the briefs' middle-dot separator); and — the majority, 81 of
# the first 100 — questions run together as plain sentences with no separator at all, each ending in
# "?". So a "?" followed by whitespace and a capital/quote/paren is also a boundary. The lookbehind
# keeps the "?" on the question it closes.
# A FOURTH shape surfaced on the second pass: "1) … 2) … 3) …" numbered INLINE in one paragraph, so a
# 1–2 digit number + ")" or "." followed by a capital/quote is a boundary anywhere, not just at line
# start. (Two digits max + required capital keeps "v2.5" and "60% to 25%." from splitting.)
QUESTION_SPLIT_RE = re.compile(
    r"(?:^|<br\s*/?>|\n)\s*(?:\d+[.)]\s*|[-*•]\s*)"      # numbered / bulleted at line start
    r"|\s+\d{1,2}[.)]\s+(?=[A-Z\"'(“])"                     # numbered inline: "… 2) Where …"
    r"|\s+·\s+"                                             # middle-dot joined
    r"|(?<=\?)\s+(?=[A-Z\"'(“])")                           # run-on sentences, each ending "?"


def split_questions(blob: str) -> list[str]:
    """A Notion `Top Questions` property is one text blob in any of four shapes (see the regex).
    Return the individual questions, cleaned. A part with no "?" at all is a preamble or label
    ("Seven calibrated questions for X:"), not a question — dropped. Markdown heading residue that
    leaked into a property ("… ## 2026-…") is cut off. The length floor only guards against
    punctuation fragments ("?" alone, "…?"); the "?" requirement is what filters preambles. The judge
    (2026-09-25) caught the earlier floor of 12 silently eating real short questions ("Is it safe?")."""
    out = []
    for p in QUESTION_SPLIT_RE.split(html.unescape(blob or "")):
        p = clean_md(p or "").split(" ## ")[0].strip()
        if len(p) > 4 and "?" in p:
            out.append(p)
    return out


def backfill_questions(g: Graph, manifest: dict) -> int:
    """YED-218 backfill: the Notion Topics DB `Top Questions` banks -> question claims.

    Different producer path from stage_claims on purpose: a topic question bank has no brief and no
    event. Each question becomes a claim with event_id ABSENT, anchored to its topic via
    claim_entity(topic, about) — exactly, not by embedding match, because here we KNOW the topic.
    asserted_at = the Topic page's Last Updated date (Alex's call 2026-09-25): entity_neighborhood
    orders `asserted_at desc nulls last limit N`, so an undated backfilled row would sort last and be
    cut; Last Updated is honest about when the question was last considered live. provenance_tier =
    notion_prior (already in the CHECK); status approved — this is Alex's own curated bank.
    Idempotent on (source_key, claim_key); re-runs relink existing claims.
    Manifest: {"topics": [{"notion_page_id", "name", "last_updated", "questions": [str] | "top_questions": str}]}
    """
    topics = manifest.get("topics") or []
    if not topics:
        sys.stderr.write("backfill-questions: manifest has no topics\n")
        return 3
    total_new = total_links = 0
    for t in topics:
        qs = t.get("questions") or split_questions(t.get("top_questions", ""))
        if not qs:
            g.stats.bump("question_backfill", "topic_without_questions")
            continue
        tid = g.ensure_topic({"name": t["name"], "notion_page_id": t.get("notion_page_id")})
        if not tid:
            g.stats.bump("question_backfill", "topic_unresolved")
            continue
        skey = source_key_for_topic_questions(t["notion_page_id"])
        when = (t.get("last_updated") or "")[:10] or None
        have = {r["claim_key"] for r in g.get(f"/claim?source_key=eq.{skey}&select=claim_key")}
        new = [q for q in qs if claim_key(q) not in have]
        g.stats.bump("claim", "matched", len(qs) - len(new))
        if new:
            vecs = g.embed(new)
            rows = []
            for q_text, vec in zip(new, vecs):
                row = {"source_key": skey, "claim_key": claim_key(q_text), "claim_text": q_text,
                       "claim_type": "question", "locator": {"section": "Top Questions", "topic": t["name"]},
                       # 0.7 = this file's default for an untagged first-hand claim (see CONF_RE handling
                       # and its selftest). A curated-but-unverified bank question earns the same default:
                       # Alex chose to keep it, nobody has confirmed it against a primary source.
                       "provenance_tier": "notion_prior", "confidence": 0.7, "asserted_at": when,
                       "status": "approved", "extractor": "parse", "lane": "A",
                       "embedding": vec, "embedding_model": EMBED_MODEL,
                       "metadata": {"backfill": "notion_topic_questions", "notion_topic_id": t.get("notion_page_id")}}
                rows.append({k: v for k, v in row.items() if v is not None})
            g.stats.bump("claim", "created", len(rows))
            total_new += len(rows)
            g.post("claim", rows, prefer="resolution=ignore-duplicates,return=minimal", on_conflict="source_key,claim_key")
        if not g.dry:
            ids = [r["id"] for r in g.get(f"/claim?source_key=eq.{skey}&select=id")]
            links = [{"claim_id": cid, "entity_type": "topic", "entity_id": tid, "role": "about"} for cid in ids]
            if links:
                g.stats.bump("claim_entity", "linked (idempotent)", len(links))
                total_links += len(links)
                g.post("claim_entity", links, prefer="resolution=ignore-duplicates,return=minimal",
                       on_conflict="claim_id,entity_type,entity_id,role")
        print(f"  {'dry ' if g.dry else ''}{t['name'][:60]:60s} questions={len(qs):2d} new={len(new):2d} asserted_at={when}")
    print(("DRY-RUN " if g.dry else "") + f"backfill-questions: {len(topics)} topics · new claims={total_new} · topic links={total_links}")
    print(g.stats.report())
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


class _FakeGraph(Graph):
    """Offline stand-in for --selftest: an in-memory graph answering the PostgREST filter shapes this file
    issues (eq / in / is / ilike with `*`, select, limit). Lets the resolvers, merge and revert run end to end
    with no network. A test double, NOT a second write path — nothing here reaches spine_client.req."""
    def __init__(self):
        super().__init__(dry_run=False, stats=Stats())
        self.quiet = True
        self.t: dict[str, list[dict]] = {k: [] for k in ("company", "person", "topic", "event", "event_entity",
                                                          "doc_chunks", "artifact_outcome",
                                                          "claim_entity", "document_entity", "documents", "claim")}
        self.n = 0

    def uuid(self) -> str:
        self.n += 1
        return f"00000000-0000-4000-8000-{self.n:012d}"

    @staticmethod
    def _match(row: dict, key: str, op: str, val: str) -> bool:
        cur = row.get(key)
        if op == "eq":
            return str(cur) == val
        if op == "in":
            return str(cur) in [x.strip() for x in val.strip("()").split(",")]
        if op == "is":
            return (cur is None) if val == "null" else (cur is not None)
        if op in ("gte", "lte"):
            return cur is not None and (str(cur) >= val if op == "gte" else str(cur) <= val)
        if op == "ilike":
            pat = "^" + ".*".join(re.escape(p) for p in val.split("*")) + "$"
            return cur is not None and re.match(pat, str(cur), re.I) is not None
        raise ValueError(op)

    def _select(self, path: str) -> list[dict]:
        import urllib.parse
        table, _, qs = path.lstrip("/").partition("?")
        out, limit = list(self.t[table]), None
        for k, v in urllib.parse.parse_qsl(qs, keep_blank_values=True):
            if k in ("select", "offset", "order"):
                continue
            if k == "limit":
                limit = int(v)
                continue
            op, _, val = v.partition(".")
            out = [r for r in out if self._match(r, k, op, val)]
        return out[:limit] if limit else out

    def get(self, path: str) -> list:
        return [dict(r) for r in self._select(path)]

    def embed(self, texts):
        return ["[0.1,0.2]"] * len(texts)

    DEFAULTS = {"documents": {"is_current": True, "version": 1}}   # column defaults the real schema applies

    def post(self, table, row, prefer="return=representation", on_conflict=None):
        out = []
        cols = on_conflict.split(",") if on_conflict else []
        for r in (row if isinstance(row, list) else [row]):
            guard(table, r)
            if cols and any(all(o.get(c) == r.get(c) for c in cols) for o in self.t[table]):
                continue                              # resolution=ignore-duplicates, as PostgREST does on the unique key
            r = {**self.DEFAULTS.get(table, {}), **r, "id": r.get("id") or self.uuid()}
            self.t[table].append(r)
            out.append(dict(r))
        return out

    def _patch_try(self, table, flt, row):
        guard(table, row, op="update")
        hits = self._select(f"/{table}?{flt}")
        if table in self.EDGE_TABLES and "entity_id" in row:      # the unique-edge collision -> 409, like PostgREST
            for h in hits:
                owner = "event_id" if table == "event_entity" else ("claim_id" if table == "claim_entity" else "document_id")
                if any(o is not h and o[owner] == h[owner] and o["entity_type"] == h["entity_type"]
                       and o["entity_id"] == row["entity_id"] and o["role"] == h["role"] for o in self.t[table]):
                    return False, 409, 0
        for h in hits:
            h.update(row)
        return bool(hits), 200, len(hits)

    def patch(self, table, flt, row):
        self._patch_try(table, flt, row)


def _identity_selftest(ok) -> None:
    """YED-47 acceptance 1–3, offline. The ledger + merge log are redirected so a selftest never writes the
    audit files (same rule as the freeze-override log in spine_client's selftest)."""
    import tempfile
    g = globals()
    saved = (g["AMBIGUITY_LEDGER"], g["MERGE_LOG"])
    tmp = tempfile.mkdtemp(prefix="identity-selftest-")
    g["AMBIGUITY_LEDGER"], g["MERGE_LOG"] = os.path.join(tmp, "ambiguity.jsonl"), os.path.join(tmp, "merges.jsonl")
    try:
        ok("qualifier: 'AWS (Amazon)' splits; bare name has none",
           split_qualifier("AWS (Amazon)") == ("AWS", "Amazon") and split_qualifier("AWS") == ("AWS", None))
        ok("host: scheme/www/path/case stripped; empty -> None",
           web_host("HTTPS://www.AWS.amazon.com/x?y") == "aws.amazon.com" and web_host("") is None and web_host(None) is None)
        ok("host: subdomains are NOT folded (aws.amazon.com != amazon.com)", web_host("https://aws.amazon.com") != web_host("https://amazon.com"))
        fg = _FakeGraph()
        aws = fg.post("company", {"name": "AWS", "website": "https://aws.amazon.com", "source": SOURCE})[0]["id"]
        ok("tier: 'AWS (Amazon)' -> AWS when the candidate is unique and hosts agree (acceptance 1a)",
           fg.ensure_company({"name": "AWS (Amazon)", "website": "https://www.aws.amazon.com/"}) == aws
           and fg.stats.c["company"].get("qualifier_resolved") == 1 and len(fg.t["company"]) == 1)
        pace = fg.post("company", {"name": "Pace", "website": "https://pace.com"})[0]["id"]
        pace_acme = fg.ensure_company({"name": "Pace (Acme)", "website": "https://acme.com"})
        ok("tier: hosts differ -> NEW row, surfaced to the ledger, never guessed (acceptance 1b)",
           pace_acme != pace and fg.stats.c["company"].get("ambiguous_name") == 1
           and os.path.exists(AMBIGUITY_LEDGER) and "hosts differ" in open(AMBIGUITY_LEDGER).read())
        ok("tier: two bare candidates -> no match (acceptance 1c)",
           resolve_company_tier("Nori (X)", "https://a.io", [{"name": "Nori", "website": "https://a.io"},
                                                             {"name": "Nori", "website": "https://a.io"}])[0] is None)
        ok("tier: website missing on either side -> no match",
           resolve_company_tier("AAIF (x)", None, [{"name": "AAIF", "website": "https://aaif.io"}])[0] is None
           and resolve_company_tier("AAIF (x)", "https://aaif.io", [{"name": "AAIF"}])[0] is None)
        zed_ai = fg.post("company", {"name": "Zed (AI)", "website": "https://zed.dev"})[0]["id"]
        zed = fg.ensure_company({"name": "Zed", "website": "https://zed.dev"})
        ok("tier: bare incoming name never resolves TO a qualified row — created + surfaced (one-directional by spec)",
           zed != zed_ai and fg.stats.c["company"].get("ambiguous_name") == 2)
        ok("tier: dry-run never writes the ledger", (lambda d: (d.ensure_company({"name": "Pace (Beta)", "website": "https://b.io"}),
                                                                 os.path.getsize(AMBIGUITY_LEDGER))[1])(_dry_fake(fg))
           == os.path.getsize(AMBIGUITY_LEDGER))
        acme, beta = fg.ensure_company({"name": "Acme"}), fg.ensure_company({"name": "Beta"})
        p1 = fg.ensure_person({"name": "Angie Jones", "company": "Acme"})
        p2 = fg.ensure_person({"name": "Angie Jones", "company": "Beta"})
        ok("person: same name, different company, no LinkedIn -> still created + surfaced (acceptance 1d; no fuzzy match)",
           p1 != p2 and fg.stats.c["person"].get("ambiguous_name") == 1)
        ok("person: re-run resolves to the company-matching row (no third row)",
           fg.ensure_person({"name": "Angie Jones", "company": "Beta"}) == p2 and len(fg.t["person"]) == 2)
        # ---- merge + revert (acceptance 2) ----
        ev1 = fg.post("event", {"title": "E1", "kind": "attended"})[0]["id"]
        ev2 = fg.post("event", {"title": "E2", "kind": "attended"})[0]["id"]
        fg.post("event_entity", {"event_id": ev1, "entity_type": "company", "entity_id": pace_acme, "role": "subject"})
        fg.post("event_entity", {"event_id": ev1, "entity_type": "company", "entity_id": pace, "role": "subject"})   # target has it too
        fg.post("event_entity", {"event_id": ev2, "entity_type": "company", "entity_id": pace_acme, "role": "subject"})
        pat = fg.post("person", {"name": "Pat Lee", "company_id": pace_acme})[0]["id"]
        for r in fg.t["company"]:
            if r["id"] == pace_acme:
                r["engagement_count"] = 3
        src, tgt = fg.entity_ref("company", pace_acme), fg.entity_ref("company", "Pace")
        rows_before, edges_before = len(fg.t["company"]), len(fg.t["event_entity"])
        dry = _dry_fake(fg)
        dry.merge("company", src, tgt, "dry")
        ok("merge --dry-run: prints the plan and changes nothing", len(fg.t["event_entity"]) == edges_before
           and not (fg.entity_ref("company", pace_acme).get("metadata") or {}).get("merged_into"))
        fg.merge("company", src, tgt, "selftest: Pace (Acme) is Pace")
        e_by = lambda ev: [e for e in fg.t["event_entity"] if e["event_id"] == ev]
        ok("merge: movable edge re-pointed to the target", any(e["entity_id"] == pace for e in e_by(ev2)))
        ok("merge: colliding edge KEPT on the source — nothing deleted",
           len(e_by(ev1)) == 2 and any(e["entity_id"] == pace_acme for e in e_by(ev1))
           and len(fg.t["event_entity"]) == edges_before and len(fg.t["company"]) == rows_before)
        ok("merge: person.company_id re-pointed", next(p for p in fg.t["person"] if p["id"] == pat)["company_id"] == pace)
        ts = fg.entity_ref("company", pace_acme)
        ok("merge: tombstone + snapshot written (merged_into, 2 edges of which 1 moved, 1 person, engagement 3)",
           ts["metadata"]["merged_into"] == pace and len(ts["metadata"]["merge"]["edges"]) == 2
           and sum(e["moved"] for e in ts["metadata"]["merge"]["edges"]) == 1 and ts["metadata"]["merge"]["persons"] == [pat]
           and fg.entity_ref("company", pace)["engagement_count"] == 3
           and fg.entity_ref("company", pace_acme)["engagement_count"] == 0)   # transferred, not copied
        ok("merge: logged to identity-merges.jsonl", '"event": "merge"' in open(MERGE_LOG).read())
        ok("resolver: a seed naming the tombstone resolves to its target — by name AND via ensure_company (acceptance 3)",
           fg.by_name("company", "Pace (Acme)")["id"] == pace and fg.ensure_company({"name": "Pace (Acme)"}) == pace
           and fg.stats.c["company"].get("followed_tombstone", 0) >= 2)
        ok("resolver: person.company resolution follows the tombstone too",
           fg.ensure_person({"name": "Sam Ortiz", "company": "Pace (Acme)"}) and
           next(p for p in fg.t["person"] if p["name"] == "Sam Ortiz")["company_id"] == pace)
        n_edges = len(fg.t["event_entity"])
        ok("merge: re-run says 'already merged' and changes nothing",
           fg.merge("company", fg.entity_ref("company", pace_acme), tgt, "again") == 0 and len(fg.t["event_entity"]) == n_edges)
        try:
            fg.merge("company", fg.entity_ref("company", zed), fg.entity_ref("company", pace_acme), "into a tombstone")
            ok("merge: into a tombstone is REFUSED (no chains minted)", False)
        except SystemExit:
            ok("merge: into a tombstone is REFUSED (no chains minted)", True)
        fg.revert("company", fg.entity_ref("company", pace_acme))
        back = fg.entity_ref("company", pace_acme)
        ok("revert: edge restored, person restored, engagement subtracted, tombstone cleared, history kept",
           any(e["entity_id"] == pace_acme for e in e_by(ev2))
           and next(p for p in fg.t["person"] if p["id"] == pat)["company_id"] == pace_acme
           and fg.entity_ref("company", pace)["engagement_count"] == 0 and back["engagement_count"] == 3
           and "merged_into" not in back["metadata"] and len(back["metadata"]["merge_history"]) == 1)
        ok("revert: the row resolves to ITSELF again", fg.by_name("company", "Pace (Acme)")["id"] == pace_acme)
        try:
            fg.revert("company", fg.entity_ref("company", pace_acme))
            ok("revert: a non-tombstone is refused", False)
        except SystemExit:
            ok("revert: a non-tombstone is refused", True)
    finally:
        g["AMBIGUITY_LEDGER"], g["MERGE_LOG"] = saved
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


RESEARCH_SAMPLE = """
## Evidence Set (for the Deep Read render — do not display to Alex as brief content)
### Companies
##### Evidence Ledger — Soxton.AI
- claim: Raised a $4M seed led by Primary in August 2026 | tier: web-verified | source: TechCrunch | url: https://techcrunch.com/soxton-seed | date: 2026-08-14
- claim: Sells AI contract review to mid-market legal teams | tier: web-verified | source: soxton.ai | url: https://soxton.ai/ | date: 2026-09-01
- claim: Newsletter says Soxton is hiring a founding AE | tier: email-signal | source: Term Sheet newsletter | url: https://fortune.com/termsheet/0926 | date: 2026-09-26
- claim: Existing thread with their CEO about a pilot | tier: email-signal | source: Gmail | url: n/a | date: 2026-05-02
- claim: Positioned as legal-ops first per prior brief | tier: notion-prior | source: prior brief | url: n/a | date: 2026-08-24
- claim: Claims 40% faster contract turnaround | tier: web-verified | source: blog | url: | date: 2026-07-01
- claim: [≤15 words] | tier: web-verified | source: [publication/site] | url: [full URL] | date: [YYYY-MM-DD]
### People
##### Evidence Ledger — Logan Brown
- claim: Previously led legal engineering at Ironclad | tier: web-verified | source: LinkedIn | url: https://www.linkedin.com/in/loganbrown | date: 2026-09-10
##### Evidence Ledger — Nobody On The Roster
- claim: Spoke at Legal Geek NYC on contract AI in 2025 | tier: web-verified | source: Legal Geek | url: https://legalgeek.co/nyc-2025 | date: 2025-11-04
### Primer
##### Evidence Ledger — Contract AI
- claim: Raised a $4M seed led by Primary in August 2026 | tier: web-verified | source: TechCrunch | url: https://techcrunch.com/soxton-seed | date: 2026-08-14
- claim: Legal AI funding hit $2.1B in H1 2026 | tier: web-verified | source: Crunchbase News | url: https://news.crunchbase.com/legal-ai-h1-2026 | date: 2026-07-15
### The Frame
- claim: stray row after a non-ledger heading | tier: web-verified | source: x | url: https://x.com/a | date: 2026-01-01
"""


def _research_selftest(ok) -> None:
    """YED-205, offline, against _FakeGraph + a sample Evidence Set in the specialists' documented format."""
    items, skipped = parse_ledger(RESEARCH_SAMPLE)
    by = {i["text"]: i for i in items}
    ok("ledger: 7 admissible rows — 6 web_verified (incl. an off-roster person + the same fact under a topic), 1 email lead",
       len(items) == 7 and sum(i["tier"] == "web_verified" for i in items) == 6 and sum(i["tier"] == "email_signal" for i in items) == 1)
    ok("ledger: claim text is self-contained '<Entity>: <claim>'",
       "Soxton.AI: Raised a $4M seed led by Primary in August 2026" in by)
    ok("ledger: private email-signal (no URL) skipped + counted", skipped.get("email_signal_private") == 1)
    ok("ledger: notion-prior skipped + counted", skipped.get("notion_prior") == 1)
    ok("ledger: web-verified without a URL skipped + counted", skipped.get("web_verified_missing_url") == 1)
    ok("ledger: the template placeholder row is never a claim", skipped.get("empty_or_template") == 1)
    ok("ledger: a row under a non-ledger heading is never a claim", skipped.get("row_outside_a_ledger") == 1
       and not any("stray row" in i["text"] for i in items))
    ok("ledger: date parsed; email lead conf 0.5, web 0.7",
       by["Soxton.AI: Raised a $4M seed led by Primary in August 2026"]["date"] == "2026-08-14"
       and by["Soxton.AI: Newsletter says Soxton is hiring a founding AE"]["confidence"] == 0.5)
    ok("ledger: the same fact under TWO entities is two claims (different subject), not deduped away",
       "Contract AI: Raised a $4M seed led by Primary in August 2026" in by)
    r = [("company", "Soxton.AI", "c1"), ("person", "Logan Brown", "p1"), ("topic", "Contract AI", "t1"), ("company", "Pascal (Fintech)", "c2")]
    ok("roster: exact + qualifier-stripped match; absent -> None",
       roster_match("Soxton.AI", r) == ("company", "c1") and roster_match("Pascal", r) == ("company", "c2")
       and roster_match("Nobody On The Roster", r) is None)
    ok("roster: company/topic token containment ('Soxton' ~ 'Soxton.AI') is a last, unique-only tier",
       roster_match("Soxton", r) == ("company", "c1"))
    ok("roster: people are exact-only — 'Logan' never matches 'Logan Brown'", roster_match("Logan", r) is None)
    ok("roster: tier-3 pools companies + topics, so a heading contained in BOTH is unlinked, never picked",
       roster_match("Contract", [("company", "Contract Co", "c1"), ("topic", "Contract AI", "t1")]) is None)
    ok("roster: KNOWN LIMIT, pinned: a heading contained in exactly one entity of another type links to it",
       roster_match("Contract", [("company", "Contract Co", "c1"), ("topic", "Agent Evals", "t1")]) == ("company", "c1"))
    ok("roster: containment that hits two entities -> None",
       roster_match("Holly", [("company", "Holly Health", "c1"), ("company", "Holly AI", "c2")]) is None)
    ok("ledger: a bold '**Evidence Ledger — X**' label opens a ledger too",
       len(parse_ledger("**Evidence Ledger — Amperos**\n- claim: Builds battery analytics for fleets | tier: web-verified"
                        " | source: amperos.com | url: https://amperos.com | date: 2026-09-01")[0]) == 1)
    leak, why = parse_ledger("##### Evidence Ledger — Soxton.AI\n"
                             "- claim: Open thread with their CEO about a pilot | tier: email-signal | source: newsletter | url: https://soxton.ai | date: 2026-09-01\n"
                             "- claim: Funding round mentioned in digest | tier: email-signal | source: Gmail | url: https://soxton.ai/news | date: 2026-09-01\n"
                             "- claim: Term Sheet reports a seed extension | tier: email-signal | source: Term Sheet | url: https://fortune.com/ts | date: 2026-09-02")
    ok("ledger: an email-signal row with a URL is STILL private when its text is correspondence or its source a mailbox",
       len(leak) == 1 and leak[0]["text"].endswith("seed extension") and why.get("email_signal_private") == 2)
    ok("roster: same name in two types -> None (never guessed)",
       roster_match("Holly", [("company", "Holly", "c9"), ("topic", "Holly", "t9")]) is None)
    ok("gate: pre-event key is DISTINCT from the post-event key", research_gate_key("a" * 32) != pid_variants("a" * 32)[0]
       and research_gate_key("a" * 32).startswith("research:"))
    # ---- end to end on the fake graph --------------------------------------------------------------
    fg = _FakeGraph()
    pid = "3ded3699c2db816a828ec6410801d5de"
    m = {"event": {"notion_page_id": pid, "title": "The Shortlist: September Founder Showcase", "event_date": "2026-09-28"},
         "entities": [{"type": "company", "name": "Soxton.AI", "website": "https://soxton.ai"},
                      {"type": "person", "name": "Logan Brown", "company": "Soxton.AI"},
                      {"type": "topic", "name": "Contract AI"}]}
    rc = stage_research(fg, RESEARCH_SAMPLE, m, brief_ref="notion:brief123")
    cl = fg.t["claim"]
    ok("stage: rc 0; 7 claims, all candidate, lane research, one source_key",
       rc == 0 and len(cl) == 7 and all(c["status"] == "candidate" and c["lane"] == "research" for c in cl)
       and {c["source_key"] for c in cl} == {research_source_key(pid)})
    ok("stage: NO event row created pre-event (ADR-10 D9); claims carry no event_id",
       fg.t["event"] == [] and all("event_id" not in c for c in cl))
    ok("stage: roster entities ensured (company, person, topic)",
       {r["name"] for r in fg.t["company"]} == {"Soxton.AI"} and len(fg.t["person"]) == 1 and len(fg.t["topic"]) == 1)
    ok("stage: research_brief document written with the Notion event id in metadata",
       len(fg.t["documents"]) == 1 and fg.t["documents"][0]["source_type"] == "research_brief"
       and fg.t["documents"][0]["metadata"]["notion_event_id"] == pid)
    ok("stage: claim_entity(about) links 6 roster-matched claims; the off-roster heading stays unlinked + counted",
       len(fg.t["claim_entity"]) == 6 and all(l["role"] == "about" for l in fg.t["claim_entity"])
       and fg.stats.c["claim_entity"].get("about_unresolved_heading") == 1)
    ok("stage: asserted_at = the source's date", {c["asserted_at"] for c in cl} >= {"2026-08-14", "2026-09-10"})
    before = (len(fg.t["claim"]), len(fg.t["company"]), len(fg.t["documents"]), len(fg.t["claim_entity"]))
    fg.stats = Stats()
    stage_research(fg, RESEARCH_SAMPLE, m, brief_ref="notion:brief123")
    ok("stage: re-run creates nothing (created=0) and adds no rows",
       fg.stats.created() == 0 and (len(fg.t["claim"]), len(fg.t["company"]), len(fg.t["documents"]), len(fg.t["claim_entity"])) == before)
    empty = _FakeGraph()
    ok("stage: zero admissible rows -> exit 3 (loud), and NOTHING is written to any table",
       stage_research(empty, "## Evidence Set\nnothing here", m, brief_ref="notion:x") == 3
       and not any(empty.t.values()))
    ok("stage: manifest without the Notion event id -> exit 5 (not 4: that is the freeze's code)",
       stage_research(_FakeGraph(), RESEARCH_SAMPLE, {"event": {}}, brief_ref=None) == 5)
    # ---- attendance: post-event ensure-event attaches them ----------------------------------------------
    eid = fg.ensure_event({"event": {**m["event"], "kind": "attended"}, "entities": []})
    ok("attend: ensure-event attaches every research claim + the brief document to the attended row",
       all(c.get("event_id") == eid for c in fg.t["claim"]) and fg.t["documents"][0].get("event_id") == eid
       and fg.stats.c["claim"].get("research_attached") == 7)
    fg.stats = Stats()
    fg.ensure_event({"event": {**m["event"], "kind": "attended"}, "entities": []})
    ok("attend: re-run attaches nothing new", "research_attached" not in fg.stats.c.get("claim", {}))
    mk = _FakeGraph()
    stage_research(mk, RESEARCH_SAMPLE, m, brief_ref=None)
    mk.ensure_event({"event": {**m["event"], "kind": "market"}, "entities": []})
    ok("attend: a NON-attended row (kind market) never attaches research claims",
       all("event_id" not in c for c in mk.t["claim"]))
    other = _FakeGraph()
    other.t["claim"].append({"id": "x", "source_key": research_source_key("b" * 32), "claim_key": "k"})
    other.ensure_event({"event": {"notion_page_id": pid, "title": "E", "kind": "attended"}, "entities": []})
    ok("attend: another event's research claims are never touched", "event_id" not in other.t["claim"][0])


PUBLISHED_SAMPLE = """> Post-event recap. Internal: Acme's confidential Series B was excluded. Variant A is long-form.
## Variant A — "Six founders" (portrait gallery)
Six founders stood up at The Shortlist's August showcase and explained why they couldn't not build what they built.
North builds a financial operating system for cloud and AI spend; Antimetal wants production that runs itself.
## Variant B — "The room" (thematic essay)
Watch six founders pitch back-to-back and you stop hearing product descriptions and start hearing worldviews about AI that operates.
## First comment — careers links
Every founder is hiring. North careers page and Antimetal careers page, in order.
## Visual Brief — 8-slide carousel
Cover then six company cards then a synthesis slide, amber accent on a dark editorial ground, rendered to PDF.
"""


def _publish_selftest(ok) -> None:
    """YED-208, offline."""
    ch = post_chunks(PUBLISHED_SAMPLE)
    ok("post: one chunk per variant section (A, B); comment + visual brief never embedded",
       [c["label"][:9] for c in ch] == ["Variant A", "Variant B"] and not any("careers" in c["text"] or "amber" in c["text"] for c in ch))
    ok("post: the private preamble (confidential round) never enters a chunk", not any("Series B" in c["text"] for c in ch))
    ok("post: no variant headings -> non-note sections, preamble still dropped",
       [c["label"] for c in post_chunks("> internal notes, Series B excluded\n## The recap\n" + "A room full of builders talking about agent memory and retrieval. " * 3)] == ["The recap"])
    ok("post: a too-short body yields nothing (no junk chunk)", post_chunks("## Variant A\nshort") == [])
    body = " ".join(["The room argued about agent memory and who owns it."] * 3)
    ok("post: real layouts — H1 '# VARIANT A', '## ⭐ SHIP THIS — Primary', '## Copy (ready to post)' are all post text",
       [c["label"][:9] for c in post_chunks(f"# VARIANT A — x\n{body}\n## ⭐ SHIP THIS — Primary\n{body}\n## Copy (ready to post)\n{body}")]
       == ["VARIANT A", "⭐ SHIP TH", "Copy (rea"])
    ok("post: a page with NO headings yields nothing (its text can't be told from the private preamble)",
       post_chunks("Content Type: roundup · internal note\n" + body) == [])
    fg = _FakeGraph()
    covered = fg.post("event", {"title": "Aug showcase", "kind": "attended", "notion_page_id": "c" * 32})[0]["id"]
    t_ai = fg.post("topic", {"name": "AI Operations"})[0]["id"]
    fg.post("event_entity", {"event_id": covered, "entity_type": "topic", "entity_id": t_ai, "role": "tagged_topic"})
    m = {"posts": [
        {"notion_page_id": "a" * 32, "title": "The Shortlist Aug — Recap", "content_type": "linkedin_post_post",
         "published_url": "https://www.linkedin.com/posts/alexyedi_x", "event_date": "2026-08-24",
         "goal": "reach", "target": "Reach + credibility", "outcome": "hit", "outcome_value": "1121 impressions",
         "outcome_date": "2026-09-14", "event_notion_ids": ["c" * 32],
         "topics": [{"name": "Founder Hiring"}], "people": [{"name": "Andrew Yeung"}], "body_md": PUBLISHED_SAMPLE},
        {"notion_page_id": "b" * 32, "title": "No URL post", "published_url": None, "body_md": PUBLISHED_SAMPLE}]}
    rc = publish_posts(fg, m)
    pub = [e for e in fg.t["event"] if e["kind"] == "published"]
    ok("publish: one published event with the post URL; the URL-less post skipped + counted",
       rc == 0 and len(pub) == 1 and pub[0]["url"].startswith("https://www.linkedin.com")
       and fg.stats.c["post"].get("skipped_no_url") == 1)
    ok("publish: event dated by the covered event, never the outcome-grading date", pub[0].get("event_date") == "2026-08-24")
    edges = {(e["entity_type"], e["role"]) for e in fg.t["event_entity"] if e["event_id"] == pub[0]["id"]}
    inherited = any(e["entity_id"] == t_ai and e["event_id"] == pub[0]["id"] for e in fg.t["event_entity"])
    ok("publish: edges = own topic + person (subject) + the COVERED event's topic (inherited)",
       edges == {("topic", "tagged_topic"), ("person", "subject")} and inherited)
    doc = fg.t["documents"][0]
    ok("publish: linkedin_post document, public_ok, URL in metadata, tied to the published event",
       doc["source_type"] == "linkedin_post" and doc["visibility"] == "public_ok"
       and doc["metadata"]["published_url"].startswith("https://") and doc["event_id"] == pub[0]["id"])
    ok("publish: 2 embedded chunks (one per variant) with the URL in the locator",
       len(fg.t["doc_chunks"]) == 2 and all(c["locator"]["url"].startswith("https://") for c in fg.t["doc_chunks"]))
    ok("publish: artifact_outcome carries goal/target/outcome", fg.t["artifact_outcome"][0]["outcome"] == "hit"
       and fg.t["artifact_outcome"][0]["goal"] == "reach")
    ok("publish: NO attended row created, and research attach never fires for a published row",
       sum(e["kind"] == "attended" for e in fg.t["event"]) == 1)
    snap = {k: len(v) for k, v in fg.t.items()}
    fg.stats = Stats()
    publish_posts(fg, m)
    ok("publish: re-run creates nothing", fg.stats.created() == 0 and {k: len(v) for k, v in fg.t.items()} == snap)
    fg.stats = Stats()
    publish_posts(fg, {"posts": [{**m["posts"][0], "body_md": None, "outcome": "partial"}]})
    ok("publish: an already-published post with no body only refreshes its outcome (no new doc / chunks)",
       fg.stats.c.get("documents", {}).get("matched") == 1 and len(fg.t["documents"]) == 1 and len(fg.t["doc_chunks"]) == 2)
    ok("published-refs: lists the post's Notion page id", published_refs(fg) == ["a" * 32])
    ok("publish: 'Posted YYYY-MM-DD' in the LinkedIn-export outcome note beats the event date",
       (lambda f: (publish_posts(f, {"posts": [{**m["posts"][0], "notion_page_id": "e" * 32, "body_md": None,
                                                "outcome_value": "[LinkedIn export] 900 impressions. Posted 2026-08-25. Grade: hit."}]}),
                   [e for e in f.t["event"] if e["kind"] == "published"][0]["event_date"])[1])(_FakeGraph()) == "2026-08-25")
    idp = _FakeGraph()
    known = idp.post("person", {"name": "Known Person", "notion_page_id": "f" * 32})[0]["id"]
    publish_posts(idp, {"posts": [{**m["posts"][0], "body_md": None, "event_notion_ids": [],
                                   "people": [{"notion_page_id": "f" * 32}, {"notion_page_id": "9" * 32}]}]})
    ok("publish: id-only people resolve by page id; an unknown one is skipped, never created nameless",
       len(idp.t["person"]) == 1 and any(e["entity_id"] == known and e["role"] == "subject" for e in idp.t["event_entity"])
       and idp.stats.c["person"].get("skipped_id_only_absent") == 1)
    pii = _FakeGraph()
    publish_posts(pii, {"posts": [{**m["posts"][0], "notion_page_id": "d" * 32, "event_notion_ids": [],
                                   "body_md": "## Variant A\n" + "Reach me at jane.doe@example.com for the deck and the intro list. " * 3}]})
    ok("publish: a post whose text trips the ADR-9 guard is refused + counted, writes NOTHING, never crashes the run",
       pii.stats.c["post"].get("refused_pii") == 1 and not any(pii.t.values()))


def _dry_fake(fg: "_FakeGraph") -> "_FakeGraph":
    """A dry-run view over the same in-memory tables (reads real, writes suppressed)."""
    d = _FakeGraph()
    d.t, d.dry, d.n = fg.t, True, fg.n + 1000
    return d


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
        # freeze <-> gate reconciliation (YED-213): the gate must not tell you to run a verb the
        # producer will refuse. With a freeze active its message has to name the freeze + the waive.
        if freeze_state():
            out = run_hook()
            ok("gate: names the active freeze instead of only 'run stage-claims'",
               "GRAPH-WRITE FREEZE IS ACTIVE" in out and "waive" in out)
    finally:
        if os.path.exists(_ledger_path()):
            os.remove(_ledger_path())
        if saved is None:
            os.environ.pop("CLAUDE_CODE_SESSION_ID", None)
        else:
            os.environ["CLAUDE_CODE_SESSION_ID"] = saved
    # ---- question claims (YED-218) -----------------------------------------------------------
    ok("questions: 'Top Questions' heading -> question claims",
       [i["claim_type"] for i in parse_brief("## Top Questions\n1. When your eval harness disagrees with "
                                             "production, which do you trust?\n2. What is the minimum eval "
                                             "suite that catches the regressions that matter?")]
       == ["question", "question"])
    ok("questions: 'Prepared Questions' alias",
       [i["claim_type"] for i in parse_brief("## Prepared Questions\n- Is the permission ceiling scoped per "
                                             "task class, or all-or-nothing?")] == ["question"])
    ok("questions: a question section is a section BOUNDARY like any other",
       [i["claim_type"] for i in parse_brief("## Top Questions\n- Which do you trust?\n## Pitfalls\n- Letting "
                                             "agents self-merge.")] == ["question", "pitfall"])
    ok("questions: do-not-publish still applies to a question",
       parse_brief("## Top Questions\n- Unsourced: how many agents does Datadog run? (do not publish)")
       [0]["do_not_publish"])
    ok("questions: confidentiality still outranks — ⛔ section is never staged",
       parse_brief("## Top Questions ⛔\n- What is your runway?") == [])
    # split_questions — the backfill's splitter, pinned against the four real bank shapes + the two
    # failure modes the judge raised (2026-09-25): silent short-question drop, quoted-question over-split.
    ok("split: numbered lines", split_questions("1. Who owns it?<br>2. What breaks first?") == ["Who owns it?", "What breaks first?"])
    ok("split: middle-dot joined", len(split_questions("Is it real? · Who pays? · When does it ship?")) == 3)
    ok("split: numbered INLINE", split_questions("1) Who owns GTM eng? 2) Where did no-code break?") == ["Who owns GTM eng?", "Where did no-code break?"])
    ok("split: run-on sentences each ending ?", len(split_questions("Where does the agent choose? What does it do when you pause? Which artifacts may it draft?")) == 3)
    ok("split: a SHORT real question is kept (was silently dropped at len>12)",
       "Is it safe?" in split_questions("What is the minimum eval suite? Is it safe?"))
    ok("split: a quoted question inside a question is NOT over-split",
       split_questions("When a user asks 'Is it safe?' what does the agent answer?") == ["When a user asks 'Is it safe?' what does the agent answer?"])
    ok("split: a standalone preamble part with no ? is dropped",
       split_questions("Seven calibrated questions for Wells. · Who pays? · When?") == ["Who pays?", "When?"])
    ok("split: heading residue is cut off", split_questions("Which metric wins? ## 2026-09-08 Trend Radar") == ["Which metric wins?"])
    ok("split: version numbers do not split", len(split_questions("Does v2.5 change the answer on 60% to 25% success?")) == 1)

    # ---- graph-write freeze (YED-213) -------------------------------------------------------
    # Pinned because the whole point is that the freeze is enforced at the producer, not trusted
    # to a sentence in a note. Every case below is a way the two mechanisms could re-collide.
    ok("freeze: the marker is a COMMITTED file, not per-worktree .state",
       FREEZE_PATH.startswith(os.path.join(ROOT, ".claude", "references")))
    ok("freeze: a write verb is refused with exit 4 while active",
       freeze_check("ensure-event", False, None) == 4 if freeze_state() else True)
    ok("freeze: --dry-run is never blocked", freeze_check("ensure-event", True, None) == 0)
    ok("freeze: waive stays reachable (the escape valve for pre-freeze rows)",
       freeze_check("waive", False, None) == 0)
    ok("freeze: preview-claims is offline, never blocked", freeze_check("preview-claims", False, None) == 0)
    ok("freeze: every mutating verb is covered",
       set(FREEZE_BLOCKS) == {"ensure-entity", "ensure-event", "ensure-document", "stage-claims",
                              "backfill", "backfill-questions", "approve-claims", "merge", "stage-research",
                              "publish"})
    _saved_freeze = FREEZE_PATH
    try:                                              # unreadable marker must fail CLOSED
        globals()["FREEZE_PATH"] = os.path.join(ROOT, ".claude", "references", "__nonexistent__.json")
        ok("freeze: absent marker means no freeze (default-open when nothing is declared)",
           freeze_state() is None)
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
            tf.write("{ this is not json")
            broken = tf.name
        globals()["FREEZE_PATH"] = broken
        fz = freeze_state()
        ok("freeze: a CORRUPT marker fails closed (active), like the gate's corrupt-line rule",
           bool(fz) and fz.get("active") is True)
        os.unlink(broken)
    finally:
        globals()["FREEZE_PATH"] = _saved_freeze

    # ---- identity S1b-lite (YED-47): tier · tombstone follow · merge/revert, offline ------------
    _identity_selftest(ok)
    # ---- the pre-event write path (YED-205) --------------------------------------------------------
    _research_selftest(ok)
    # ---- the published producer (YED-208) ----------------------------------------------------------
    _publish_selftest(ok)

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
                                     "backfill", "backfill-questions", "preview-claims", "approve-claims", "merge",
                                     "expect-research", "stage-research", "publish", "published-refs"])
    ap.add_argument("--evidence", help="(stage-research) the Evidence Set, or the raw specialist returns, as markdown")
    ap.add_argument("--phase", choices=["post_event", "pre_event"], default="post_event",
                    help="(waive) which gate row: post_event (default) or pre_event (the research row)")
    ap.add_argument("--table", choices=["company", "person", "topic"], help="(merge) entity table")
    ap.add_argument("--from", dest="merge_from", metavar="ID|NAME", help="(merge) the row to tombstone")
    ap.add_argument("--into", dest="merge_into", metavar="ID|NAME", help="(merge) the row that survives")
    ap.add_argument("--revert", action="store_true", help="(merge) undo a soft-merge from its snapshot")
    ap.add_argument("--manifest", help="one manifest (all verbs except backfill)")
    ap.add_argument("--manifest-dir", help="(backfill) a directory of *.event.json / *.entities.json manifests "
                                           "from supabase/scripts/build_manifests.py — the SAME ensure-event / "
                                           "ensure-entity code, run over a list (there is no separate backfill path)")
    ap.add_argument("--expect-claims", action="store_true",
                    help="(ensure-event, live /post-event-content only) open a PENDING gate row that "
                         "stage-claims must close — the Stop hook fails the run otherwise")
    ap.add_argument("--reason", help="(waive) why this event's claims are deliberately not staged — logged · "
                                     "(merge) why these two rows are one thing — logged; REQUIRED for a live merge")
    ap.add_argument("--freeze-override", metavar="WHY",
                    help="proceed despite an active graph-write freeze (.claude/references/graph-freeze.json). "
                         "Logged to .claude/artifacts/graph-freeze-overrides.jsonl — allowed, never silent")
    ap.add_argument("--brief")
    ap.add_argument("--brief-ref", help="external_ref for the brief document, e.g. notion:<page id>")
    ap.add_argument("--approve", action="store_true",
                    help="inherited approval: brief-derived claims land approved (do_not_publish ones never do)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    rc_freeze = freeze_check(a.verb, a.dry_run, a.freeze_override)   # before ANY write path runs
    if rc_freeze:
        return rc_freeze
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
    if a.verb == "published-refs":
        print("\n".join(published_refs(g)))
        return 0
    if a.verb == "publish":
        if not a.manifest:
            ap.error("publish needs --manifest")
        rc = publish_posts(g, json.load(open(a.manifest, encoding="utf-8")))
        print(("DRY-RUN " if a.dry_run else "") + f"publish: created={stats.created()}")
        print(stats.report())
        return rc
    if a.verb == "merge":
        if not (a.table and a.merge_from):
            ap.error("merge needs --table and --from (+ --into and --reason, or --revert)")
        src = g.entity_ref(a.table, a.merge_from)
        if a.revert:
            rc = g.revert(a.table, src)
        else:
            if not a.merge_into:
                ap.error("merge needs --into (or --revert)")
            if not a.reason and not a.dry_run:
                ap.error("a live merge needs --reason (every merge is human-approved and logged)")
            rc = g.merge(a.table, src, g.entity_ref(a.table, a.merge_into), a.reason or "(dry run)")
        print(("DRY-RUN " if a.dry_run else "") + f"merge: created={stats.created()}")
        print(stats.report())
        if a.json:
            print(json.dumps({"verb": "merge", "dry_run": a.dry_run, "revert": a.revert, "stats": stats.c}))
        return rc
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
    elif a.verb == "backfill-questions":
        return backfill_questions(g, m)
    elif a.verb == "waive":
        if not (gate_key and a.reason):
            ap.error("waive needs a manifest with event.notion_page_id and --reason")
        if a.phase == "pre_event":
            ledger_mark(research_gate_key(gate_key), ev.get("title", ""), "waived", a.reason, phase="pre_event")
        else:
            ledger_mark(gate_key, ev.get("title", ""), "waived", a.reason)
        print(f"waived: {ev.get('title')} — {a.reason} (logged to substrate-gate-failures.jsonl)")
        return 0
    elif a.verb == "expect-research":
        if not gate_key:
            ap.error("expect-research needs a manifest with event.notion_page_id")
        if not a.dry_run:
            ledger_mark(research_gate_key(gate_key), ev.get("title", ""), "pending",
                        keep_if=("staged", "waived"), phase="pre_event")
        print(f"expect-research: gate row research:{gate_key[:8]} PENDING — stage-research closes it")
        return 0
    elif a.verb == "stage-research":
        if not a.evidence:
            ap.error("stage-research needs --evidence")
        rc = stage_research(g, open(a.evidence, encoding="utf-8").read(), m, brief_ref=a.brief_ref)
        if rc == 0 and not a.dry_run and gate_key:
            ledger_mark(research_gate_key(gate_key), ev.get("title", ""), "staged", phase="pre_event")
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
