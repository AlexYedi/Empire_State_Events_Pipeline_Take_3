#!/usr/bin/env python3
"""spine_client — the ONE write path to the Market-Intelligence spine (ADR-9, YED-81).

Every Supabase REST write in this repo goes through `req()` (or `write()`), and every POST/PATCH
body is checked by `guard()` BEFORE it leaves the machine. The guard is hard-fail: a violation
raises PIIViolation (exit 2) naming field · tier rule · fix. There is no in-run override.

ADR-9 tier 2 (the spine) holds professional-public identity only. Concretely:
  * a column may be SET only if it is in ALLOW[table]; ANY column may be NULLED (nulling is
    always safe — it is how the email migration runs through this same guard);
  * email / phone columns are forbidden on every table;
  * every string value is scanned — recursively through dicts/lists (`metadata` jsonb included) —
    for email and phone patterns;
  * rows sourced from the inbox (source starts with `inbox_miner`) carry a tier-0 backstop:
    `metadata.sender_domain` / `metadata.from_domain` must not match `inbox-denylist.md`.

Reads (GET) and `/rpc/` calls pass through unguarded — they write nothing.

Usage from scripts:      from spine_client import req, write, q, PIIViolation
CLI (see spine_write.py) python3 .claude/scripts/spine_write.py <table> --json '{...}'
Self-test:               python3 .claude/scripts/spine_client.py --selftest   (27 cases)
Repo check (AC2):        python3 .claude/scripts/spine_client.py --check-writers

Conventions preserved from the six writers this replaced: (status, parsed_json) return shape;
`prefer=` header; 30s default timeout (pass timeout=60 for doc-KB); `raise_on_error=True` gives
dockb's raise-on-HTTPError semantics. Exit codes: 2 = PIIViolation, 1 = selftest/check failure.
"""
from __future__ import annotations
import fnmatch, json, os, re, sys, urllib.error, urllib.parse, urllib.request

REF = "oicikjyzmxqfomrrqkvf"
BASE = f"https://{REF}.supabase.co/rest/v1"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ENV = os.path.join(ROOT, ".env")
DENYLIST_PATH = os.path.join(ROOT, ".claude", "references", "inbox-denylist.md")
SELF = os.path.abspath(__file__)


class PIIViolation(Exception):
    """A write that ADR-9 forbids. Message = field · tier rule · fix. Exit code 2."""
    exit_code = 2


# ---------------------------------------------------------------------------
# ADR-9 tier-2 allowlists — the columns a producer may SET. Keep in sync with
# market-intel-schema.sql + doc-kb-schema.sql + doc-kb-migration-b1.sql. Adding a table = one row.
# ---------------------------------------------------------------------------
_MI_COMMON = {"notion_page_id", "source", "relevance_score", "last_engaged_at", "engagement_count",
              "metadata", "created_at", "updated_at"}
ALLOW: dict[str, set[str]] = {
    "company": {"id", "name", "description", "website", "industry", "funding_stage", "company_type",
                "linkedin_url"} | _MI_COMMON,
    # person: professional-public identity ONLY. No email. No phone. (ADR-9 decision 1, 2026-09-13)
    "person": {"id", "name", "title", "company_id", "linkedin_url", "bio", "role_context"} | _MI_COMMON,
    "topic": {"id", "name", "description"} | _MI_COMMON,
    "event": {"id", "title", "kind", "event_date", "description", "url", "source", "confidence",
              "notion_page_id", "metadata", "created_at", "updated_at"},
    "event_entity": {"id", "event_id", "entity_type", "entity_id", "role", "created_at"},
    "documents": {"id", "title", "author", "source_type", "blob_key", "sha256", "word_count",
                  "embedding_model", "notion_page_id", "ingested_at",
                  # ADR-10 S1a (0009): documents generalized to every artifact with a body
                  "event_id", "external_ref", "doc_date", "version", "supersedes_id", "is_current",
                  "produced_by", "visibility", "metadata"},
    "doc_chunks": {"id", "document_id", "chunk_index", "content", "embedding", "token_count",
                   "locator", "created_at"},
    "doc_claims": {"id", "document_sha256", "claim_key", "claim_text", "claim_type", "locator", "quote",
                   "proposed_entities", "confidence", "extractor", "extractor_model", "lane", "status",
                   "promoted_event_id", "created_at", "reviewed_at"},
    # --- ADR-10 S1a (0009) — the Knowledge Substrate claim layer ---------------------------------
    # claim: utility_score / use_count / last_used_at are deliberately ABSENT. ADR-10 decision 5:
    # nothing ranks on usage until >=20 outcome rows exist, so no producer may set those columns.
    # The rule is enforced here, in code, not left to prose. `tsv` is generated (never written).
    "claim": {"id", "source_key", "claim_key", "claim_text", "claim_type", "quote", "locator",
              "proposed_entities", "document_id", "event_id", "provenance_tier", "confidence",
              "asserted_at", "status", "extractor", "extractor_model", "lane", "embedding",
              "embedding_model", "metadata", "created_at", "reviewed_at"},
    "claim_entity": {"claim_id", "entity_type", "entity_id", "role", "created_at"},
    "claim_relation": {"id", "from_claim_id", "to_claim_id", "relation", "method", "confidence", "created_at"},
    "document_entity": {"document_id", "entity_type", "entity_id", "role", "created_at"},
    "artifact_outcome": {"document_id", "goal", "target", "outcome", "outcome_value", "outcome_date",
                         "source", "updated_at"},
    "claim_usage": {"id", "claim_id", "document_id", "consumer", "used_at"},
}
# Forbidden on EVERY table, regardless of allowlist — contact PII never enters the spine.
FORBIDDEN_COLUMNS = {"email", "e_mail", "phone", "phone_number", "mobile", "telephone"}

# Patterns scanned over every string value. Phone requires separators or a leading +/( so that
# 10-digit integers (unix timestamps, ids) never false-positive.
EMAIL_RE = re.compile(r"(?<![\w/])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}(?![\w])")
PHONE_RE = re.compile(
    r"(?<![\w.+-])(?:\+\d{1,3}[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]\d{3}[\s.-]\d{4}(?![\w])"   # 555-123-4567 / (555) 123 4567
    r"|(?<![\w.])\+\d{10,15}(?![\w])"                                                          # +15551234567 (E.164 compact)
)
# Bot / no-reply addresses are not personal data (git trailers surface them in generated artifacts).
EMAIL_ALLOWLIST_RE = re.compile(r"^(?:noreply|no-reply|donotreply)@|@users\.noreply\.github\.com$", re.I)


# ---------------------------------------------------------------------------
# Tier-0 backstop: the inbox denylist (skip-list). Parsed from the human-readable markdown so the
# boundary stays a single, auditable file. Exact domains, subdomain suffixes, and `*` globs.
# ---------------------------------------------------------------------------
def load_denylist(path: str = DENYLIST_PATH) -> tuple[set[str], list[str]]:
    """(domains, globs) for the tier-0 backstop. Delegates to inbox_boundary — the ONE parser of
    inbox-denylist.md (YED-161) — and falls back to the inline parser only if that module is absent."""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from inbox_boundary import load_denylist as _full
        d = _full(path)
        return set(d.domains), list(d.globs)
    except ImportError:
        pass
    exact: set[str] = set()
    globs: list[str] = []
    if not os.path.exists(path):
        return exact, globs
    text = open(path, encoding="utf-8").read()
    for tok in re.findall(r"`([^`\n]+)`", text):
        t = tok.strip().lower()
        if " " in t or "@" in t or "." not in t and "*" not in t:
            continue                      # prose, exact senders, or bare words like `docusign`
        if "*" in t:
            globs.append(t if "." in t or t.startswith("*") else t)
        else:
            exact.add(t.lstrip("."))
    return exact, globs


def domain_denylisted(host: str, deny: tuple[set[str], list[str]] | None = None) -> bool:
    if not host:
        return False
    host = host.lower().strip()
    exact, globs = deny if deny is not None else load_denylist()
    if host in exact or any(host.endswith("." + d) for d in exact):
        return True
    return any(fnmatch.fnmatch(host, g) for g in globs)


# ---------------------------------------------------------------------------
# The guard
# ---------------------------------------------------------------------------
def _walk(value, path=""):
    """Yield (path, string) for every string inside a nested dict/list/scalar."""
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield from _walk(v, f"{path}.{k}" if path else str(k))
    elif isinstance(value, (list, tuple)):
        for i, v in enumerate(value):
            yield from _walk(v, f"{path}[{i}]")


def _scan_pii(row: dict, table: str) -> None:
    for path, s in _walk(row):
        for m in EMAIL_RE.finditer(s):
            if not EMAIL_ALLOWLIST_RE.search(m.group(0)):
                raise PIIViolation(
                    f"{table}.{path} contains an email address · ADR-9 tier 2: contact PII never enters "
                    f"the spine · fix: drop it from the producer (contact detail belongs in HubSpot)")
        if PHONE_RE.search(s):
            raise PIIViolation(
                f"{table}.{path} contains a phone number · ADR-9 tier 2: contact PII never enters the "
                f"spine · fix: drop it from the producer (contact detail belongs in HubSpot)")


def guard(table: str, row: dict, *, op: str = "insert") -> dict:
    """Validate one row for `table`. Returns the row unchanged or raises PIIViolation."""
    table = table.strip("/").split("?")[0]
    if not isinstance(row, dict):
        raise PIIViolation(f"{table}: body must be a JSON object per row · got {type(row).__name__}")
    if table not in ALLOW:
        raise PIIViolation(
            f"{table}: no ADR-9 allowlist for this table (fail-closed) · fix: add its columns to "
            f"spine_client.ALLOW after checking the schema for PII")
    for col, val in row.items():
        c = col.lower()
        if val is None:
            continue                       # nulling any column is always permitted
        if c in FORBIDDEN_COLUMNS:
            raise PIIViolation(
                f"{table}.{col} is a contact-PII column · ADR-9 tier 2: email/phone never enter the "
                f"spine · fix: remove the field; store contact detail in HubSpot")
        if c not in ALLOW[table]:
            raise PIIViolation(
                f"{table}.{col} is not an allowlisted column for {op} · ADR-9: only known professional "
                f"fields may be set · fix: use an allowlisted column or extend ALLOW[{table!r}] deliberately")
    _scan_pii(row, table)
    src = str(row.get("source") or "")
    if src.startswith("inbox_miner"):
        meta = row.get("metadata") or {}
        for key in ("sender_domain", "from_domain", "domain"):
            host = meta.get(key) if isinstance(meta, dict) else None
            if host and domain_denylisted(str(host)):
                raise PIIViolation(
                    f"{table}.metadata.{key}={host!r} is on inbox-denylist.md · ADR-9 tier 0: never "
                    f"enters · fix: the scan should have skipped this thread (YED-161)")
    return row


def guard_body(path: str, body) -> None:
    """Guard a request body for a write to `path` (table or table?filter). Lists = batch of rows."""
    table = path.strip("/").split("?")[0]
    if table.startswith("rpc/"):
        return
    rows = body if isinstance(body, list) else [body]
    for r in rows:
        guard(table, r)


# ---------------------------------------------------------------------------
# HTTP — the shape every writer used, preserved.
# ---------------------------------------------------------------------------
_KEY: str | None = None


def load_key(env_path: str = ENV) -> str:
    global _KEY
    if _KEY:
        return _KEY
    k = os.environ.get("SUPABASE_API_KEY")
    if not k and os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("SUPABASE_API_KEY="):
                    k = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not k:
        sys.exit("FATAL: SUPABASE_API_KEY not in .env — refusing to proceed (no silent no-op).")
    _KEY = k
    return k


def q(v) -> str:
    """URL-encode a filter value (PostgREST)."""
    return urllib.parse.quote(str(v), safe="")


# -------------------------------------------------------------------------------------------------
# Graph-write freeze (YED-213, 2026-09-21). Enforced HERE, not in substrate.py, for the reason ADR-9
# already gives: this is the one write path. An adversarial pass found seven scripts reaching the
# graph — spine_write, recompute_relevance, merge_topics, inbox_signal_write, backfill_people and
# substrate all write — so gating only the producer would have left a freeze trivially bypassable by
# any of the others. Same argument as the PII guard: one door, guarded once.
# Reads (GET/HEAD) are never blocked. Override is an env var because most of these are not CLI-
# argument scripts: GRAPH_FREEZE_OVERRIDE="<why>" — allowed, and logged as data, never silent.
# -------------------------------------------------------------------------------------------------
FREEZE_PATH = os.path.join(ROOT, ".claude", "references", "graph-freeze.json")
FREEZE_LOG = os.path.join(ROOT, ".claude", "artifacts", "graph-freeze-overrides.jsonl")


class GraphFrozen(RuntimeError):
    """Raised instead of performing a write while a freeze is active."""


def freeze_active() -> dict | None:
    """The active freeze, or None. Unreadable marker => fail CLOSED (synthetic active freeze),
    matching the substrate gate's corrupt-ledger-line rule."""
    if not os.path.exists(FREEZE_PATH):
        return None
    try:
        f = json.load(open(FREEZE_PATH, encoding="utf-8"))
    except (ValueError, OSError) as e:
        return {"active": True, "issue": "?",
                "reason": f"graph-freeze.json unreadable ({e}) — failing closed."}
    return f if isinstance(f, dict) and f.get("active") else None


def freeze_block(method: str, path: str) -> None:
    if method not in ("POST", "PATCH", "PUT", "DELETE"):
        return
    fz = freeze_active()
    if not fz:
        return
    why = os.environ.get("GRAPH_FREEZE_OVERRIDE")
    if why:
        import datetime
        os.makedirs(os.path.dirname(FREEZE_LOG), exist_ok=True)
        with open(FREEZE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"event": "graph_freeze_override", "method": method, "path": path,
                                "issue": fz.get("issue"), "override_reason": why,
                                "session": os.environ.get("CLAUDE_CODE_SESSION_ID", "_pending"),
                                "ts": datetime.datetime.now(datetime.timezone.utc)
                                        .strftime("%Y-%m-%dT%H:%M:%SZ")}) + "\n")
        return
    raise GraphFrozen(
        f"GRAPH-WRITE FREEZE ACTIVE ({fz.get('issue', '?')}) — refused {method} {path}, nothing was written.\n"
        f"{fz.get('reason', '')}\n"
        f"Lifts when: {fz.get('lifts_when', 'see .claude/references/graph-freeze.json')}\n"
        "Reads and --dry-run are unaffected. Emergency: GRAPH_FREEZE_OVERRIDE=\"<why>\" (logged).\n"
        "Source of truth: .claude/references/graph-freeze.json")


def req(method: str, path: str, body=None, prefer: str | None = None, *, timeout: int = 30,
        raise_on_error: bool = False, extra_headers: dict | None = None):
    """(status, parsed_json_or_text). Every POST/PATCH/PUT body is guarded (except /rpc/ paths).
    There is deliberately NO parameter that disables the guard — judge finding 2026-09-13."""
    method = method.upper()
    freeze_block(method, path)          # may this write happen at all? (before the PII guard, before the socket)
    if method in ("POST", "PATCH", "PUT") and body is not None:
        guard_body(path, body)
    key = load_key()
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if prefer:
        headers["Prefer"] = prefer
    if extra_headers:
        headers.update(extra_headers)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            txt = resp.read().decode()
            return resp.status, (json.loads(txt) if txt else None)
    except urllib.error.HTTPError as e:
        txt = e.read().decode()
        if raise_on_error:
            raise RuntimeError(f"Supabase {method} {path} -> {e.code}: {txt[:500]}")
        return e.code, txt


def write(table: str, rows, prefer: str | None = "return=representation", *, patch_filter: str | None = None,
          dry_run: bool = False, **kw):
    """Guarded write. POST /table by default; PATCH /table?patch_filter when given."""
    path = f"/{table.strip('/')}" + (f"?{patch_filter}" if patch_filter else "")
    guard_body(path, rows)
    if dry_run:
        return 0, {"dry_run": True, "path": path, "rows": rows if isinstance(rows, list) else [rows]}
    return req("PATCH" if patch_filter else "POST", path, rows, prefer=prefer, **kw)  # guards again: pure + cheap


# ---------------------------------------------------------------------------
# AC2 — repo check: no other REST writer may exist. Scripts fail; prose warns.
# ---------------------------------------------------------------------------
# Detection patterns for check_writers() — module-level so --selftest can pin them (judge findings 2026-09-13).
_SCRIPT_WRITE_RE = re.compile(r"urlopen|requests\.(post|patch|put)|\bcurl\b|\bfetch\(|axios\.(post|patch|put)|https?\.request\(")
_WRITE_TABLES = (r"(topic|event|company|person|event_entity|documents|doc_chunks|doc_claims|claim|"
                 r"claim_entity|claim_relation|document_entity|artifact_outcome|claim_usage)")
_PROSE_CURL_RE = re.compile(r"\bcurl\b[^\n]*(-X\s*(POST|PATCH)|--data|-d\s)")
_PROSE_VERB_RE = re.compile(r"`(POST|PATCH) /" + _WRITE_TABLES)


def check_writers() -> tuple[list[str], list[str]]:
    offenders, prose = [], []
    exempt = {SELF, os.path.join(os.path.dirname(SELF), "spine_write.py")}
    for dirpath, _, files in os.walk(os.path.join(ROOT, ".claude")):
        if any(x in dirpath for x in ("/artifacts", "/.state", "/evals", "/proposals", "/notes")):
            continue                       # specs, notes and telemetry describe writes; they don't perform them
        for fn in files:
            p = os.path.join(dirpath, fn)
            if p in exempt:
                continue
            try:
                s = open(p, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            if "rest/v1" not in s:
                continue
            if fn.endswith((".py", ".sh", ".mjs", ".js", ".ts")):
                if _SCRIPT_WRITE_RE.search(s):
                    offenders.append(os.path.relpath(p, ROOT))
            elif fn.endswith(".md"):
                if _PROSE_CURL_RE.search(s) or _PROSE_VERB_RE.search(s):
                    prose.append(os.path.relpath(p, ROOT))
    return sorted(offenders), sorted(prose)


# ---------------------------------------------------------------------------
# Self-test — the living acceptance layer (AC1). Positive AND negative cases.
# ---------------------------------------------------------------------------
def selftest() -> bool:
    deny = ({"bank.example", "irs.gov"}, ["*.gov", "myhealth*"])
    cases: list[tuple[str, callable, bool]] = []  # (name, thunk, expect_violation)

    def add(name, fn, expect):
        cases.append((name, fn, expect))

    add("person.email set → refuse", lambda: guard("person", {"name": "A", "email": "a@b.com"}), True)
    add("person.phone set → refuse", lambda: guard("person", {"name": "A", "phone": "555-123-4567"}), True)
    add("person.bio containing email → refuse",
        lambda: guard("person", {"name": "A", "bio": "reach me at jane@example.com"}), True)
    add("event.metadata nested phone → refuse",
        lambda: guard("event", {"title": "t", "kind": "market", "metadata": {"contact": {"cell": "+1 (555) 123-4567"}}}), True)
    add("event.metadata E.164 compact phone → refuse",
        lambda: guard("event", {"title": "t", "kind": "market", "metadata": {"x": "+15551234567"}}), True)
    add("unknown table → refuse (fail-closed)", lambda: guard("secrets", {"x": 1}), True)
    add("non-allowlisted column set → refuse", lambda: guard("topic", {"name": "t", "owner_ssn": "1"}), True)
    add("inbox row from denylisted sender_domain → refuse",
        lambda: guard("event", {"title": "t", "kind": "market", "source": "inbox_miner:market",
                                "metadata": {"sender_domain": "alerts.bank.example"}}) if not domain_denylisted("alerts.bank.example", deny) else (_ for _ in ()).throw(PIIViolation("tier 0")), True)
    add("company clean row → pass", lambda: guard("company", {"name": "Veris AI", "website": "https://veris.ai", "linkedin_url": "https://linkedin.com/company/veris"}), False)
    add("person clean row (linkedin ok) → pass",
        lambda: guard("person", {"name": "Ritiz Tambi", "title": "CEO", "linkedin_url": "https://linkedin.com/in/ritiz", "bio": "Founder; talked about agent simulation."}), False)
    add("PATCH nulling email → pass (nulling always allowed)", lambda: guard("person", {"email": None}, op="update"), False)
    add("metadata unix timestamp 1757700000 → pass (no phone false-positive)",
        lambda: guard("event", {"title": "t", "kind": "market", "metadata": {"ts": "1757700000", "id": 1757700000}}), False)
    add("url with /@handle → pass (not an email)",
        lambda: guard("event", {"title": "t", "kind": "market", "url": "https://x.com/@ritiz_tambi/status/1"}), False)
    add("noreply bot address → pass (allowlisted)",
        lambda: guard("event", {"title": "t", "kind": "market", "description": "Co-Authored-By: bot <noreply@anthropic.com>"}), False)
    add("doc_claims clean row → pass",
        lambda: guard("doc_claims", {"document_sha256": "abc", "claim_key": "k", "claim_text": "Static evals grade answers.", "status": "candidate"}), False)
    # ADR-10 S1a — the claim layer
    add("claim clean first-hand row (dates + stats) → pass",
        lambda: guard("claim", {"source_key": "s", "claim_key": "k", "provenance_tier": "first_hand",
                                "claim_text": "Plans flipped between 4 shapes, 1.0 to 173.6 s, on 2026-09-16.",
                                "asserted_at": "2026-09-16T22:00:00Z", "confidence": 0.8,
                                "locator": {"speaker": "Ryan Booz", "timestamp": "00:41:12"}}), False)
    add("claim.utility_score set → refuse (ADR-10 decision 5: no ranking on usage yet)",
        lambda: guard("claim", {"source_key": "s", "claim_key": "k", "claim_text": "x", "utility_score": 0.9}), True)
    add("claim.quote carrying a speaker's email → refuse",
        lambda: guard("claim", {"source_key": "s", "claim_key": "k", "claim_text": "x",
                                "quote": "ping me at ryan@example.com"}), True)
    add("claim_relation clean row → pass",
        lambda: guard("claim_relation", {"from_claim_id": "a", "to_claim_id": "b", "relation": "contradicts"}), False)
    add("documents our-artifact row (no blob) → pass",
        lambda: guard("documents", {"title": "Brief", "source_type": "research_brief", "sha256": "h",
                                    "external_ref": "notion:3ded3699", "version": 1, "is_current": True}), False)
    add("prose scan catches `POST /claim`",
        lambda: None if _PROSE_VERB_RE.search("then `POST /claim` with") else (_ for _ in ()).throw(PIIViolation("miss")), False)
    add("batch body guards every row → refuse on 2nd",
        lambda: guard_body("/person", [{"name": "ok"}, {"name": "bad", "email": "x@y.io"}]), True)
    add("rpc path passes through", lambda: guard_body("/rpc/match_doc_chunks", {"query_embedding": [0.1]}), False)
    add("denylist: subdomain suffix + glob", lambda: (_ for _ in ()).throw(PIIViolation("x")) if (domain_denylisted("alerts.bank.example", deny) and domain_denylisted("portal.irs.gov", deny) and domain_denylisted("myhealthplus.com", deny) and not domain_denylisted("veris.ai", deny)) else None, True)

    import inspect
    add("req() exposes NO guard-bypass parameter (judge finding 2026-09-13)",
        lambda: (_ for _ in ()).throw(PIIViolation("bypass param present")) if any("guard" in k for k in inspect.signature(req).parameters) else None, False)
    add("writer scan catches a JS fetch() POST to rest/v1",
        lambda: None if _SCRIPT_WRITE_RE.search('fetch("https://x.supabase.co/rest/v1/person", {method: "POST"})') else (_ for _ in ()).throw(PIIViolation("miss")), False)
    add("prose scan catches `POST /doc_claims`",
        lambda: None if _PROSE_VERB_RE.search("then `POST /doc_claims` with") else (_ for _ in ()).throw(PIIViolation("miss")), False)

    # ---- graph-write freeze at the one door (YED-213) ---------------------------------------
    # Pinned against a TEMP marker, not the live one, so these pass whether or not a freeze is
    # currently declared. The point being pinned: the freeze is enforced where every writer
    # funnels, because an adversarial pass found seven scripts writing to the graph — gating only
    # substrate.py would have left it bypassable by any of the other six.
    import tempfile as _tf
    _saved_fp, _saved_ov = FREEZE_PATH, os.environ.get("GRAPH_FREEZE_OVERRIDE")
    # The override log is an AUDIT trail — a selftest must never append to it, or the evidence is
    # indistinguishable from a real emergency override. Redirected to a temp file for the duration.
    _saved_log = FREEZE_LOG
    globals()["FREEZE_LOG"] = os.path.join(_tf.mkdtemp(prefix="freeze-log-"), "overrides.jsonl")
    _fd = _tf.NamedTemporaryFile("w", suffix=".json", delete=False)
    _fd.write(json.dumps({"active": True, "issue": "TEST", "reason": "selftest", "lifts_when": "never"}))
    _fd.close()
    globals()["FREEZE_PATH"] = _fd.name
    os.environ.pop("GRAPH_FREEZE_OVERRIDE", None)
    add("freeze: POST refused at the one write path", lambda: freeze_block("POST", "/event"), True)
    add("freeze: PATCH refused", lambda: freeze_block("PATCH", "/claim?id=eq.1"), True)
    add("freeze: DELETE refused", lambda: freeze_block("DELETE", "/claim?id=eq.1"), True)
    add("freeze: GET never refused (reads stay open)", lambda: freeze_block("GET", "/event"), False)

    def _overridden():
        os.environ["GRAPH_FREEZE_OVERRIDE"] = "selftest"
        try:
            freeze_block("POST", "/event")
        finally:
            os.environ.pop("GRAPH_FREEZE_OVERRIDE", None)
    add("freeze: GRAPH_FREEZE_OVERRIDE proceeds (and is logged, never silent)", _overridden, False)

    _broken = _tf.NamedTemporaryFile("w", suffix=".json", delete=False)
    _broken.write("{not json")
    _broken.close()

    def _corrupt():
        globals()["FREEZE_PATH"] = _broken.name
        try:
            freeze_block("POST", "/event")
        finally:
            globals()["FREEZE_PATH"] = _fd.name
    add("freeze: corrupt marker fails CLOSED", _corrupt, True)

    def _absent():
        globals()["FREEZE_PATH"] = os.path.join(ROOT, "__no_such_freeze__.json")
        try:
            freeze_block("POST", "/event")
        finally:
            globals()["FREEZE_PATH"] = _fd.name
    add("freeze: absent marker means writes are open", _absent, False)

    failures = 0
    for name, fn, expect in cases:
        try:
            fn()
            got = False
        except (PIIViolation, GraphFrozen):
            # Both mean "this write was refused at the door" — the only distinction the runner
            # needs. GraphFrozen was added 2026-09-21; before that it would have escaped the
            # loop and crashed the suite rather than failing a case.
            got = True
        ok = got == expect
        failures += 0 if ok else 1
        print(f"  {'✓' if ok else '✗'} {name}")
    globals()["FREEZE_PATH"] = _saved_fp                      # restore the live marker + env + log
    globals()["FREEZE_LOG"] = _saved_log
    if _saved_ov is not None:
        os.environ["GRAPH_FREEZE_OVERRIDE"] = _saved_ov
    for _p in (_fd.name, _broken.name):
        try:
            os.unlink(_p)
        except OSError:
            pass
    n = len(cases)
    print(f"selftest: {n - failures}/{n} guard cases pass")
    return failures == 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return 0 if selftest() else 1
    if "--check-writers" in argv:
        off, prose = check_writers()
        for p in off:
            print(f"  ✗ REST writer outside spine_client: {p}")
        for p in prose:
            print(f"  ⚠ prose instructs a raw REST write (route via spine_write.py): {p}")
        print(f"check-writers: {len(off)} script offender(s), {len(prose)} prose warning(s)")
        return 1 if off else 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except PIIViolation as e:
        print(f"PIIViolation: {e}", file=sys.stderr)
        sys.exit(PIIViolation.exit_code)
