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

Refusal telemetry (YED-320): every refusal appends one JSON line to `.claude/.state/pii-refusals.jsonl`
(gitignored) naming the rule, never the value, then raises exactly as before; every 50th clean row
that req() is about to send records its scan time. Best effort: a telemetry failure is swallowed and
the refusal still raises. Off switch: SPINE_TELEMETRY=off, or spine_client.telemetry(False).

Usage from scripts:      from spine_client import req, write, q, PIIViolation
CLI (see spine_write.py) python3 .claude/scripts/spine_write.py <table> --json '{...}'
Self-test:               python3 .claude/scripts/spine_client.py --selftest   (123 cases)
Repo check (AC2):        python3 .claude/scripts/spine_client.py --check-writers

Conventions preserved from the six writers this replaced: (status, parsed_json) return shape;
`prefer=` header; 30s default timeout (pass timeout=60 for doc-KB); `raise_on_error=True` gives
dockb's raise-on-HTTPError semantics. Exit codes: 2 = PIIViolation, 1 = selftest/check failure.
"""
from __future__ import annotations
import fnmatch, http.client, json, os, re, ssl, sys, time, urllib.error, urllib.parse, urllib.request

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
    "topic": {"id", "name", "description",
              # YED-304 W1: cluster assignment columns (ADR-9: none is contact PII)
              "cluster_id", "cluster_assignment_confidence", "cluster_assigned_by"} | _MI_COMMON,
    "event": {"id", "title", "kind", "event_date", "description", "url", "source", "confidence",
              "notion_page_id", "metadata", "created_at", "updated_at",
              "signal_type"},   # YED-307 / migration 0016: hiring_pulse · paper · model_release · news · partnership · layoff
    # --- migration 0016 (ADR-13, PR #274): market-lens tables. topic_cluster_membership is deliberately ABSENT:
    # its only writer is the topic_membership_sync trigger; a direct write would race it (one-open-row rule).
    # target_tier mirrors the PRIVATE target list: DB-only, never exposed by mi_slice (ADR-13 F1).
    "company_segment_history": {"segment_id", "company_id", "stage", "industry", "headcount_band", "hq_metro",
                                "target_tier", "valid_from", "valid_to", "source", "created_at"},
    "lane_run": {"run_id", "lane", "started_at", "finished_at", "status", "items_seen", "items_written",
                 "items_refused", "credits_spent", "error"},
    # lane_registry deliberately NOT allowlisted: `active` gates the freshness alarm, so a producer must not be
    # able to switch its own monitor off (or rename a lane). Every lane_registry change ships as a migration.
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
    # --- lane 4 feeds (migration 0017, market-lens proposal §2) — raw public-feed staging ------
    # No person rows, no entity edges; source_key is the canonical-URL sha256 (feeds.item_key).
    # GUARD DIFF: adding a table = one ALLOW row; reviewed by Alex per ADR-9 before merge.
    "feed_items": {"source_key", "company", "feed_url", "url", "title", "published", "summary",
                   "kind", "signal_type_guess", "fetched_at", "metadata", "created_at"},
}
# Forbidden on EVERY table, regardless of allowlist — contact PII never enters the spine.
FORBIDDEN_COLUMNS = {"email", "e_mail", "phone", "phone_number", "mobile", "telephone"}

# Patterns scanned over every string value. Phone requires separators or a leading +/( so that
# 10-digit integers (unix timestamps, ids) never false-positive. The optional leading-1 prefix
# (S-04 A2, YED-183) catches leading-country-code US numbers while the guard lookbehind still
# applies to the whole number, so `1-` after a word char or `.` cannot slip through.
# Third alternative (YED-309): international with separators — `+CC`, an optional `(0)` trunk, then
# 2–5 digit groups split by space/dot/dash. The lookahead counts 7–15 digits across the whole
# separated run (so `+3 4 5` and `+12.50` pass); the tail guard refuses a stop before another
# `sep+digit`, so over-long dotted runs (`+1.2.3.4.5.6.7`) pass too. A leading `+` stays mandatory:
# separator-less 10-digit numbers remain OUT (A3, YED-183). Carried byte-for-byte by the DB backstop
# (pii-db-check.sql / migration 0017) — check_pii_regex_parity.py enforces it.
EMAIL_RE = re.compile(r"(?<![\w/])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}(?![\w])")
PHONE_RE = re.compile(
    r"(?<![\w.+-])(?:1[\s.-])?(?:\+\d{1,3}[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]\d{3}[\s.-]\d{4}(?![\w])"   # 555-123-4567 / 1-555-123-4567
    r"|(?<![\w.])\+\d{10,15}(?![\w])"                                                          # +15551234567 — E.164 compact
    r"|(?<![\w.+-])\+(?=\d(?:(?:[\s.-]?\(0\))?[\s.-]?\d){6,14}(?![\s.-]?\d))"                    # +44 20 7946 0958 — intl, YED-309
    r"\d{1,3}(?:[\s.-]?\(0\)[\s.-]?|[\s.-])\d{1,8}(?:[\s.-]\d{1,8}){1,4}(?![\w]|[\s.-]\d)"      # ...incl. +44 (0)20 7946 0958
)
# Bot / no-reply addresses are not personal data (git trailers surface them in generated artifacts).
EMAIL_ALLOWLIST_RE = re.compile(r"^(?:noreply|no-reply|donotreply)@|@users\.noreply\.github\.com$", re.I)


# ---------------------------------------------------------------------------
# Refusal telemetry (YED-320, measuring the YED-319 decision). Best effort and never in the way: the
# record is built and written inside try/except, then PIIViolation raises with the same message as
# before. NEVER the value: regex rules record only a shape (digit -> 9, letter -> a, <=40 chars) and
# two booleans computed in memory (prose_hint, asset_code); `table` and the top-level column are
# recorded only when allowlisted, every nested key becomes `*` (list indices kept), else `<unlisted>`.
# Single-threaded like req(): _BATCH, _OK_ROWS and _COUNT_OK are plain module state.
# ---------------------------------------------------------------------------
TELEMETRY_PATH = os.path.join(ROOT, ".claude", ".state", "pii-refusals.jsonl")
OK_SAMPLE_EVERY = 50             # every Nth clean row req() sends records {"rule":"ok_sample","scan_ms",…} (F6)
_BATCH = 1                       # rows in the body being guarded; guard_body sets it, a direct guard() call is 1
_OK_ROWS = 0
_COUNT_OK = False                # True only while req() guards the body it is about to send
_TELEMETRY_ON = True
# Classifiers for the watcher's precision triggers (pii_guard_watch.py builds its SQL from these lists).
PROSE_UNITS = ("usd", "eur", "gbp", "k", "m", "bn", "b", "x", "pp", "bps", "pts", "percent", "pct", "ms", "sec",
               "gb", "mb", "tb", "km", "kg", "users", "people", "customers")
PROSE_WORDS = ("revenue", "growth", "grew", "delta", "up", "down", "shares", "users", "arr", "mrr", "yoy", "qoq",
               "increase", "decrease", "rose", "fell", "gain", "loss")
_PROSE_AFTER_RE = re.compile(r"[%$\u20ac\u00a3\u00a5]|\b(?:" + "|".join(PROSE_UNITS) + r")\b", re.I)
_PROSE_BEFORE_RE = re.compile(r"\b(?:" + "|".join(PROSE_WORDS) + r")\b", re.I)
_ALL_THREES_RE = re.compile(r"\+\d{1,3}(?:[\s.]\d{3})+")
EMAIL_ASSET_CODE_RE = re.compile(r"\.(png|jpe?g|gif|svg|webp|ico|css|js|mjs|ts|tsx|py|rb|go|json|ya?ml|toml|md|pdf"
                                 r"|mp4|mov|zip|lock)$|@[0-9]+x\.|@[0-9]+(\.[0-9]+)+|^git@"
                                 r"|@(example|test|domain|email)\.(com|org|net)$", re.I)


def telemetry(enabled: bool = True) -> None:
    """Switch refusal telemetry for this process (selftests and dry runs: telemetry(False)).
    SPINE_TELEMETRY=off in the environment switches it off as well. Never affects the guard."""
    global _TELEMETRY_ON
    _TELEMETRY_ON = bool(enabled)


def _telemetry_on() -> bool:
    return _TELEMETRY_ON and os.environ.get("SPINE_TELEMETRY", "").strip().lower() not in ("off", "0", "false", "no")


def _label_table(table: str) -> str:
    return table if table in ALLOW else "<unlisted>"


def _label_col(table: str, col) -> str:
    """A top-level column name is recorded only from the fixed vocabularies (ALLOW / FORBIDDEN_COLUMNS)."""
    c = str(col).lower()
    return c if c in ALLOW.get(table, ()) or c in FORBIDDEN_COLUMNS else "<unlisted>"
_PHONE_ALTS: tuple[str, list] | None = None   # (pattern, compiled alternatives): labelling only, never matching


def split_alternatives(pattern: str) -> list[str]:
    """Split a regex source on its TOP-LEVEL `|` (paren depth 0, outside [...], unescaped). The parts
    joined with `|` are the pattern exactly; the selftest pins that, so labels can never drift."""
    parts, depth, in_class, start, i = [], 0, False, 0, 0
    while i < len(pattern):
        c = pattern[i]
        if c == "\\":
            i += 2
            continue
        if in_class:
            in_class = c != "]"
        elif c == "[":
            in_class = True
            i += 2 if pattern[i + 1:i + 3] == "^]" else 1 if pattern[i + 1:i + 2] == "]" else 0  # leading ] is literal
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        elif c == "|" and depth == 0:
            parts.append(pattern[start:i])
            start = i + 1
        i += 1
    parts.append(pattern[start:])
    return parts


def _phone_rule(s: str, start: int, pattern: str | None = None) -> str:
    """Which PHONE_RE alternative matched at `start`: the first one that matches there (re's own order)."""
    global _PHONE_ALTS
    pattern = pattern or PHONE_RE.pattern
    if _PHONE_ALTS is None or _PHONE_ALTS[0] != pattern:
        _PHONE_ALTS = (pattern, [re.compile(p) for p in split_alternatives(pattern)])
    for i, alt in enumerate(_PHONE_ALTS[1], 1):
        if alt.match(s, start):
            return f"phone_alt{i}"
    return "phone_unlabelled"


def _shape(s: str) -> str:
    return "".join("9" if c.isdigit() else "a" if c.isalpha() else c for c in s)[:40]


def _record(rec: dict) -> None:
    try:
        if not _telemetry_on():
            return
        os.makedirs(os.path.dirname(TELEMETRY_PATH), exist_ok=True)
        with open(TELEMETRY_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, sort_keys=True) + "\n")
    except Exception:
        pass                         # telemetry never blocks, weakens or replaces a refusal


def _prose_hint(text: str, span) -> bool:
    """Numeric-prose context of a phone match (the watcher's F1 classifier), computed in memory."""
    hit = text[span[0]:span[1]]
    return bool(_PROSE_AFTER_RE.search(text[span[1]:span[1] + 12])
                or _PROSE_BEFORE_RE.search(text[max(0, span[0] - 20):span[0]])
                or _ALL_THREES_RE.fullmatch(hit))


def _refuse(rule: str, table: str, path: str, msg: str, *, text: str | None = None, span=None, t0=None):
    """Record one refusal (best effort), then raise PIIViolation(msg), the exact exception as before.
    `path` arrives already masked (see _label_col / _walk_masked)."""
    try:
        if _telemetry_on():
            argv = getattr(sys, "argv", None) or [""]
            rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "table": _label_table(table),
                   "rule": rule, "path": path, "batch_size": _BATCH, "caller": os.path.basename(argv[0] or "")}
            if text is not None and span is not None:
                hit = text[span[0]:span[1]]
                if rule == "phone":
                    rec["rule"] = _phone_rule(text, span[0])
                    rec["prose_hint"] = _prose_hint(text, span)
                else:
                    rec["asset_code"] = bool(EMAIL_ASSET_CODE_RE.search(hit))
                rec["shape"] = _shape(hit)
            if t0 is not None:
                rec["scan_ms"] = round((time.perf_counter() - t0) * 1000, 3)
            _record(rec)
    except Exception:
        pass
    raise PIIViolation(msg)


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


def _walk_masked(value, path: str, masked: str):
    """_walk with a telemetry-safe twin path: same traversal and the same `path` as _walk(row) yields,
    plus `masked`, where every dict key below the top-level column is `*` and list indices are kept."""
    if isinstance(value, str):
        yield path, masked, value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield from _walk_masked(v, f"{path}.{k}", f"{masked}.*")
    elif isinstance(value, (list, tuple)):
        for i, v in enumerate(value):
            yield from _walk_masked(v, f"{path}[{i}]", f"{masked}[{i}]")


def _scan_pii(row: dict, table: str) -> None:
    global _OK_ROWS
    t0 = time.perf_counter()
    for col, value in row.items():          # == _walk(row): a top-level key's path is str(key)
        for path, masked, s in _walk_masked(value, str(col), _label_col(table, col)):
            for m in EMAIL_RE.finditer(s):
                if not EMAIL_ALLOWLIST_RE.search(m.group(0)):
                    _refuse("email", table, masked,
                            f"{table}.{path} contains an email address · ADR-9 tier 2: contact PII never enters "
                            f"the spine · fix: drop it from the producer (contact detail belongs in HubSpot)",
                            text=s, span=m.span(), t0=t0)
            m = PHONE_RE.search(s)
            if m:
                _refuse("phone", table, masked,
                        f"{table}.{path} contains a phone number · ADR-9 tier 2: contact PII never enters the "
                        f"spine · fix: drop it from the producer (contact detail belongs in HubSpot)",
                        text=s, span=m.span(), t0=t0)
    if _COUNT_OK:                           # only rows req() is about to send count as writes
        try:
            _OK_ROWS += 1
            if _OK_ROWS % OK_SAMPLE_EVERY == 0:
                _record({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "rule": "ok_sample",
                         "table": _label_table(table), "scan_ms": round((time.perf_counter() - t0) * 1000, 3)})
        except Exception:
            pass                            # a clean row is never blocked by telemetry


def guard(table: str, row: dict, *, op: str = "insert") -> dict:
    """Validate one row for `table`. Returns the row unchanged or raises PIIViolation."""
    table = table.strip("/").split("?")[0]
    if not isinstance(row, dict):
        _refuse("body_type", table, "", f"{table}: body must be a JSON object per row · got {type(row).__name__}")
    if table not in ALLOW:
        _refuse("no_allowlist", table, "",
                f"{table}: no ADR-9 allowlist for this table (fail-closed) · fix: add its columns to "
                f"spine_client.ALLOW after checking the schema for PII")
    for col, val in row.items():
        c = col.lower()
        if val is None:
            continue                       # nulling any column is always permitted
        if c in FORBIDDEN_COLUMNS:
            _refuse("forbidden_column", table, _label_col(table, col),
                    f"{table}.{col} is a contact-PII column · ADR-9 tier 2: email/phone never enter the "
                    f"spine · fix: remove the field; store contact detail in HubSpot")
        if c not in ALLOW[table]:
            _refuse("not_allowlisted", table, _label_col(table, col),
                    f"{table}.{col} is not an allowlisted column for {op} · ADR-9: only known professional "
                    f"fields may be set · fix: use an allowlisted column or extend ALLOW[{table!r}] deliberately")
    _scan_pii(row, table)
    src = str(row.get("source") or "")
    if src.startswith("inbox_miner"):
        meta = row.get("metadata") or {}
        for key in ("sender_domain", "from_domain", "domain"):
            host = meta.get(key) if isinstance(meta, dict) else None
            if host and domain_denylisted(str(host)):
                _refuse("inbox_denylist", table, f"metadata.{key}",
                        f"{table}.metadata.{key}={host!r} is on inbox-denylist.md · ADR-9 tier 0: never "
                        f"enters · fix: the scan should have skipped this thread (YED-161)")
    return row


def guard_body(path: str, body) -> None:
    """Guard a request body for a write to `path` (table or table?filter). Lists = batch of rows."""
    table = path.strip("/").split("?")[0]
    if table.startswith("rpc/"):
        return
    global _BATCH
    rows = body if isinstance(body, list) else [body]
    _BATCH = len(rows)
    try:
        for r in rows:
            guard(table, r)
    finally:
        _BATCH = 1


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


# Transient-failure retry (YED-205 acceptance run, 2026-09-27). A stage-research run is ~250 sequential
# REST calls; one multi-second network stall anywhere used to kill the whole run (3 of 4 attempts on the
# Shortlist run died on a single `urlopen ... timed out`). Only requests that are safe to repeat are
# retried: a plain-insert POST that timed out may already have landed, so it still fails loud.
REQ_RETRIES = 3                  # total attempts
REQ_BACKOFF = (1.0, 3.0)         # seconds before attempt 2, 3
# ssl.SSLError is a plain OSError (not a ConnectionError): without it a TLS drop on a reused socket escaped as a raw
# traceback (judge, 2026-09-27). urllib used to wrap these into URLError for us; http.client does not.
_TRANSIENT = (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException, ssl.SSLError)

# Persistent connection (YED-149 diagnosis, 2026-09-27, measured): ~10% of FRESH TCP connects from Alex's network
# hang on the SYN — to every host, not just Supabase — and each hang cost the full 30s timeout. One urllib connection
# per call turned a 200-role dry run (455 calls) into ~24 min, 93% of it stalls; over one reused connection the same
# calls took 65s with 0 stalls. So retry-safe calls (GET / set-PATCH / upsert) reuse ONE keep-alive connection, and a
# dropped one is closed and rebuilt by the retry loop. A NON-retryable call (plain insert, /rpc/) always gets its own
# fresh connection, exactly as before: if a reused socket died mid-send we could not know whether the insert landed.
CONNECT_TIMEOUT = 10             # a stalled SYN now costs 10s once, not 30s per call
# Single-threaded by design: every caller is a sequential CLI loop in the parent thread (fan-out never writes).
# _CONN is shared module state with no lock — do not call req() from threads without adding one.


class NotSent(ConnectionError):
    """The connection never opened, so not one byte of the request left this machine. Retrying is safe for ANY
    method, including a plain insert: nothing can have landed (first live backfill died on exactly this, 2026-09-27)."""
_CONN: http.client.HTTPSConnection | None = None


def _drop_conn() -> None:
    global _CONN
    if _CONN is not None:
        try:
            _CONN.close()
        except Exception:
            pass
    _CONN = None


def _send(method: str, path: str, data, headers: dict, timeout: int, reuse: bool) -> tuple[int, str]:
    """One HTTP exchange -> (status, body text). Every connect-time failure is raised as NotSent; a failure after
    connect raises the underlying _TRANSIENT error (or a non-transient one, which req() does not retry).
    The only socket code in this file; the retry selftest stubs it, the lifecycle selftest drives it with a fake
    HTTPSConnection."""
    global _CONN
    host = f"{REF}.supabase.co"
    conn = _CONN if reuse else None
    if conn is None:
        conn = http.client.HTTPSConnection(host, 443, timeout=min(timeout, CONNECT_TIMEOUT))
        try:
            conn.connect()
        except OSError as e:     # ANY connect failure — SYN stall, DNS (gaierror), TLS handshake, no route — sent nothing
            conn.close()
            raise NotSent(f"connect failed before sending: {type(e).__name__}: {e}") from e
        if reuse:
            _CONN = conn
    conn.sock.settimeout(timeout)
    try:
        conn.request(method, "/rest/v1" + path, body=data, headers=headers)
        resp = conn.getresponse()
        return resp.status, resp.read().decode()
    except Exception:
        if reuse:
            _drop_conn()
        else:
            conn.close()
        raise
    finally:
        if not reuse:
            conn.close()


def _retryable(method: str, path: str, prefer: str | None) -> bool:
    """Idempotent-by-construction only: GET, PATCH (set-to-value), and upsert POSTs (`resolution=` in Prefer).
    /rpc/ is excluded — an rpc may write. Everything else repeats nothing."""
    if path.startswith("/rpc/"):
        return False
    if method in ("GET", "PATCH"):
        return True
    return method == "POST" and "resolution=" in (prefer or "")


def req(method: str, path: str, body=None, prefer: str | None = None, *, timeout: int = 30,
        raise_on_error: bool = False, extra_headers: dict | None = None):
    """(status, parsed_json_or_text). Every POST/PATCH/PUT body is guarded (except /rpc/ paths).
    There is deliberately NO parameter that disables the guard — judge finding 2026-09-13."""
    global _COUNT_OK
    method = method.upper()
    if method in ("POST", "PATCH", "PUT") and body is not None:
        _COUNT_OK = True                 # telemetry only: the rows about to be sent are the "writes" (F6)
        try:
            guard_body(path, body)
        finally:
            _COUNT_OK = False
    key = load_key()
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if prefer:
        headers["Prefer"] = prefer
    if extra_headers:
        headers.update(extra_headers)
    data = json.dumps(body).encode() if body is not None else None
    retryable = _retryable(method, path, prefer)
    attempts = REQ_RETRIES           # a non-retryable call still retries a NotSent failure (see NotSent), nothing else
    for attempt in range(1, attempts + 1):
        try:
            code, txt = _send(method, path, data, headers, timeout, reuse=retryable)
            if code >= 400:                            # a real HTTP answer: never retried
                if raise_on_error:
                    raise RuntimeError(f"Supabase {method} {path} -> {code}: {txt[:500]}")
                return code, txt
            return code, (json.loads(txt) if txt else None)
        except _TRANSIENT as e:                        # no answer at all: stall / reset / dropped socket
            # A non-retryable call may have landed unless nothing was sent: fail loud on the first stall, as before.
            giving_up = attempt >= attempts or (not retryable and not isinstance(e, NotSent))
            if giving_up:
                sys.stderr.write(f"req: gave up after {attempt} attempt(s) on {method} {path[:90]} — {type(e).__name__}: "
                                 f"{str(e)[:120]}. Nothing after this call ran; a re-run is idempotent (upserts "
                                 f"and GETs), and the skipped graph write is reported in the run summary.\n")
                raise
            wait = REQ_BACKOFF[min(attempt, len(REQ_BACKOFF)) - 1]
            sys.stderr.write(f"req: transient {type(e).__name__} ({str(e)[:80]}) on {method} {path[:90]} — "
                             f"retry {attempt}/{attempts - 1} in {wait:g}s\n")
            time.sleep(wait)


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
                 r"claim_entity|claim_relation|document_entity|artifact_outcome|claim_usage|"
                 r"feed_items|company_segment_history|lane_run|lane_registry)")
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
# A local 3-alternative fixture: PR #277's PHONE_RE (YED-309), so labelling is proven against the shape
# the guard is about to carry as well as the 2-alternative one on main. Selftest-only; matches nothing live.
_FIXTURE_3ALT = (
    r"(?<![\w.+-])(?:1[\s.-])?(?:\+\d{1,3}[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]\d{3}[\s.-]\d{4}(?![\w])"
    r"|(?<![\w.])\+\d{10,15}(?![\w])"
    r"|(?<![\w.+-])\+(?=\d(?:(?:[\s.-]?\(0\))?[\s.-]?\d){6,14}(?![\s.-]?\d))"
    r"\d{1,3}(?:[\s.-]?\(0\)[\s.-]?|[\s.-])\d{1,8}(?:[\s.-]\d{1,8}){1,4}(?![\w]|[\s.-]\d)"
)


def selftest() -> bool:
    deny = ({"bank.example", "irs.gov"}, ["*.gov", "myhealth*"])
    import tempfile
    g = globals()
    # Every refusal below would append to the real telemetry file: point it at a scratch file instead.
    real_tel, g["TELEMETRY_PATH"] = g["TELEMETRY_PATH"], os.path.join(tempfile.mkdtemp(prefix="spine_selftest_"), "t.jsonl")
    saved_switch = (g["_TELEMETRY_ON"], os.environ.pop("SPINE_TELEMETRY", None))   # telemetry cases need it on
    telemetry(True)
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
    # S-04 A2 (YED-183): leading-1 US numbers with dash/dot separators were a verified miss (G3).
    add("event.metadata leading-1 dash phone → refuse",
        lambda: guard("event", {"title": "t", "kind": "market", "metadata": {"x": "1-555-123-4567"}}), True)
    add("event.metadata leading-1 dot phone → refuse",
        lambda: guard("event", {"title": "t", "kind": "market", "metadata": {"x": "1.555.123.4567"}}), True)
    add("event.metadata leading-1 phone in prose → refuse",
        lambda: guard("event", {"title": "t", "kind": "market", "metadata": {"x": "call 1-800-555-0199"}}), True)
    add("event.metadata leading-1 space phone → refuse",
        lambda: guard("event", {"title": "t", "kind": "market", "metadata": {"x": "1 555 123 4567"}}), True)
    add("event.metadata +1 dash phone → refuse",
        lambda: guard("event", {"title": "t", "kind": "market", "metadata": {"x": "+1-555-123-4567"}}), True)
    add("event.metadata parens-area phone → refuse",
        lambda: guard("event", {"title": "t", "kind": "market", "metadata": {"x": "(555) 123-4567"}}), True)
    # YED-309: international-with-separators. These rows test PHONE_RE ALONE (no guard(), no column
    # rules) so the regex layer is proven on its own. Reserved/fictional numbers only: UK Ofcom drama
    # ranges (020 7946 0xxx, 07700 900xxx), AU ACMA fiction ranges (0491 570 xxx, 02 5550 xxxx),
    # FR ARCEP fiction ranges (01 99 00 xx xx, 06 39 98 xx xx); every other number (DE, IN, JP, BR,
    # SG, NL, ES) uses an all-zero subscriber number.
    def _phone(s):
        if PHONE_RE.search(s):
            raise PIIViolation(f"PHONE_RE matched {s!r}")
    for s in ("+44 20 7946 0958", "+33 1 99 00 12 34", "+49 30 00000000", "+91 00000 00000",
              "+44 (0)20 7946 0958", "+44 7700 900982", "+61 491 570 156", "+61.2.5550.1234",
              "+33 6 39 98 12 34", "+81 3-0000-0000", "+55 11 90000-0000", "+65 6000 0000",
              "+31 20 000 0000", "+34 91 000 00 00", "+44 (0) 20 7946 0123", "call +44 20 7946 0958."):
        add(f"PHONE_RE intl {s!r} → match", lambda s=s: _phone(s), True)
    for s in ("2026-11-04", "1.2.3", "192.168.1.10", "1757700000", "550e8400-e29b-41d4-a716-446655440000",
              "+12.50", "+3 4 5", "2024-2026", "YED-309", "+1.2.3.4.5.6.7", "v1.2.3+20261104",
              "2026-11-04T10:00:00+05:30", "+44 20", "+1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6"):
        add(f"PHONE_RE {s!r} → no match", lambda s=s: _phone(s), False)
    # Regression data: the phone rows of docs/adr/proposals/pii-regex-set.md (T17–T30 caught;
    # phone-relevant N-rows clean). T30 is gap G1 — "missed (accepted)" there, caught since YED-309.
    for s in ("+15551234567", "+1 555 123 4567", "+1-555-123-4567", "+1 (555) 123-4567", "(555) 123 4567",
              "(555) 123-4567", "555-123-4567", "555.123.4567", "555 123 4567", "tel:+15551234567",
              "+1555123456789", "+15551234567.", "+1 (555) 123-4567 (cell)", "+44 20 5555 1234"):
        add(f"PHONE_RE regression {s!r} → match", lambda s=s: _phone(s), True)
    for s in ("1757700000", "ts 1757700000 logged", "https://example.com/pr-1234567", "ticket #1234567 filed",
              "due 2023-10-15 ok", "call 5551234 ext 2", "order 555123456789012345 ok", "at 40.7128, -74.0060",
              "5551234567"):
        add(f"PHONE_RE regression {s!r} → no match", lambda s=s: _phone(s), False)
    add("unknown table → refuse (fail-closed)", lambda: guard("secrets", {"x": 1}), True)
    add("non-allowlisted column set → refuse", lambda: guard("topic", {"name": "t", "owner_ssn": "1"}), True)
    # YED-304 W1: cluster assignment columns on topic
    add("topic cluster assignment row → pass",
        lambda: guard("topic", {"name": "Autonomous agents at trade shows", "cluster_id": "c123",
                                "cluster_assignment_confidence": 0.87, "cluster_assigned_by": "embedding_auto"}), False)
    add("topic unassign (nulling cluster columns) → pass",
        lambda: guard("topic", {"cluster_id": None, "cluster_assignment_confidence": None,
                                "cluster_assigned_by": None}, op="update"), False)
    # YED-304 W1: the new columns are allowed, but PII in them is still refused (allowlist ≠ bypass).
    add("topic cluster_assigned_by email → refuse",
        lambda: guard("topic", {"cluster_assigned_by": "a.b@example.com"}, op="update"), True)
    add("topic cluster_id email → refuse",
        lambda: guard("topic", {"cluster_id": "jane.doe@example.com"}, op="update"), True)
    add("topic cluster_assignment_confidence phone → refuse",
        lambda: guard("topic", {"cluster_assignment_confidence": "+1 (555) 123-4567"}, op="update"), True)
    # YED-307 / 0016: the new tables open their columns, never the PII boundary (each new free-text column probed).
    add("lane_run row → pass", lambda: guard("lane_run", {"lane": "hiring_pulse", "status": "success",
                                                         "items_seen": 40, "items_written": 38}), False)
    add("lane_run error carrying an email → refuse",
        lambda: guard("lane_run", {"lane": "hiring_pulse", "error": "board owner jane.doe@example.com 500"}), True)
    add("lane_run error carrying a phone → refuse",
        lambda: guard("lane_run", {"lane": "hiring_pulse", "error": "call (555) 123-4567"}), True)
    add("company_segment_history source carrying an email → refuse",
        lambda: guard("company_segment_history", {"company_id": "c1", "stage": "seed", "source": "a.b@example.com"}), True)
    add("company_segment_history PII column → refuse",
        lambda: guard("company_segment_history", {"company_id": "c1", "email": "x"}), True)
    add("event signal_type → pass", lambda: guard("event", {"title": "t", "kind": "market", "signal_type": "hiring_pulse"}), False)
    add("company_segment_history clean row → pass",
        lambda: guard("company_segment_history", {"company_id": "c1", "stage": "series_a", "industry": "AI infrastructure",
                                                  "headcount_band": "51-200", "hq_metro": "NYC", "source": "akta"}), False)
    add("company_segment_history industry carrying a phone → refuse (DB CHECK allows digits/dashes)",
        lambda: guard("company_segment_history", {"company_id": "c1", "industry": "Acme 555-123-4567"}), True)
    add("company_segment_history hq_metro carrying a phone → refuse",
        lambda: guard("company_segment_history", {"company_id": "c1", "hq_metro": "NYC (555) 123-4567"}), True)
    add("company_segment_history stage carrying an email → refuse",
        lambda: guard("company_segment_history", {"company_id": "c1", "stage": "a.b@example.com"}), True)
    add("lane_registry active=false → refuse (a producer cannot silence its own alarm)",
        lambda: guard("lane_registry", {"active": False}, op="update"), True)
    add("lane_registry lane rename → refuse",
        lambda: guard("lane_registry", {"lane": "renamed"}, op="update"), True)
    add("topic_cluster_membership direct write → refuse (trigger is the only writer)",
        lambda: guard("topic_cluster_membership", {"topic_id": "t"}), True)
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
    # --- lane 4 feeds (migration 0017, market-lens proposal §2) — raw public-feed staging
    add("feed_items clean staged row → pass",
        lambda: guard("feed_items", {"source_key": "ab" * 32, "company": "Veris AI",
                                     "feed_url": "https://veris.example/feed",
                                     "url": "https://veris.example/blog/p1",
                                     "title": "Introducing Atlas 2.0", "published": "2026-11-01T00:00:00Z",
                                     "summary": "GA release notes.", "kind": "rss",
                                     "signal_type_guess": "launch", "fetched_at": "2026-11-04T00:00:00Z",
                                     "metadata": {"canonical_url": "https://veris.example/blog/p1"}}), False)
    add("feed_items.summary carrying a press email → refuse",
        lambda: guard("feed_items", {"source_key": "ab" * 32, "company": "Veris AI",
                                     "summary": "Questions to press@veris.example", "kind": "rss"}), True)
    add("feed_items.metadata carrying a phone → refuse",
        lambda: guard("feed_items", {"source_key": "ab" * 32, "metadata": {"alt": "+1 (555) 123-4567"}}), True)
    add("feed_items.title carrying an email → refuse",
        lambda: guard("feed_items", {"source_key": "ab" * 32,
                                     "title": "Ping jane.doe@veris.example about Atlas"}), True)
    add("feed_items.url carrying an email → refuse",
        lambda: guard("feed_items", {"source_key": "ab" * 32,
                                     "url": "https://veris.example/contact?mail=press@veris.example"}), True)
    add("feed_items.company carrying a phone → refuse",
        lambda: guard("feed_items", {"source_key": "ab" * 32,
                                     "company": "Veris AI +1 212 555 0142"}), True)
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

    # Transient retry (2026-09-27): the rule is pinned, and the loop is exercised against a stubbed socket.
    add("retry rule: GET / PATCH / upsert-POST retry; plain POST and /rpc/ do not",
        lambda: None if (_retryable("GET", "/person?x", None) and _retryable("PATCH", "/person?id=eq.1", "return=minimal")
                         and _retryable("POST", "/claim?on_conflict=k", "resolution=ignore-duplicates,return=minimal")
                         and not _retryable("POST", "/person", "return=representation")
                         and not _retryable("POST", "/rpc/match_doc_chunks", "resolution=merge-duplicates"))
        else (_ for _ in ()).throw(PIIViolation("retry rule drifted")), False)

    def _retry_loop_case():
        g = globals()
        calls = {"n": 0}

        def fake_send(method, path, data, headers, timeout, reuse):
            calls["n"] += 1
            calls.setdefault("reuse", []).append(reuse)
            if calls["n"] < 3:
                raise NotSent("connect failed") if calls.get("notsent") else urllib.error.URLError("timed out")
            return 200, "[]"
        saved = (g["REQ_BACKOFF"], g["_send"], g["load_key"])
        g["REQ_BACKOFF"], g["_send"], g["load_key"] = (0, 0), fake_send, (lambda: "test-key")
        try:
            st, body = req("GET", "/person?select=id&limit=1")
            if not (st == 200 and body == [] and calls["n"] == 3):
                raise PIIViolation(f"retry loop drifted: status={st} calls={calls['n']}")
            # Exhausted retries say so in one readable line (YED-228 follow-up), then re-raise the same type.
            import io, contextlib
            calls["n"] = -10                                   # every attempt stalls
            buf = io.StringIO()
            try:
                with contextlib.redirect_stderr(buf):
                    req("GET", "/person?select=id&limit=1")
                raise PIIViolation("exhausted retries did not raise")
            except urllib.error.URLError:
                if "gave up after 3 attempt(s) on GET /person" not in buf.getvalue():
                    raise PIIViolation("exhausted retries raised without the readable 'gave up' line")
            calls["n"] = 0
            calls["n"] = 0
            try:
                req("POST", "/person", [{"name": "Plain Insert"}], prefer="return=representation")
                raise PIIViolation("plain POST retried")     # must NOT reach a 3rd call; must raise on the 1st
            except urllib.error.URLError:
                if calls["n"] != 1:
                    raise PIIViolation(f"plain POST made {calls['n']} calls")
                if calls["reuse"][-1] is not False:
                    raise PIIViolation("plain POST went over the shared keep-alive connection")
            # ...but a plain POST whose connection never opened IS retried: nothing was sent.
            calls["n"], calls["notsent"] = 0, True
            st, _ = req("POST", "/person", [{"name": "Plain Insert"}], prefer="return=representation")
            if not (st == 200 and calls["n"] == 3):
                raise PIIViolation(f"NotSent plain POST not retried: calls={calls['n']}")
        finally:
            g["REQ_BACKOFF"], g["_send"], g["load_key"] = saved
    add("retry loop: 2 stalls then success on GET; plain POST fails on the 1st stall unless nothing was sent",
        _retry_loop_case, False)

    def _send_lifecycle_case():
        """Drives the real _send() with a fake HTTPSConnection: reuse, drop-on-error, fresh-for-non-retryable, and
        every connect-time OSError (DNS, TLS, SYN stall) surfacing as NotSent."""
        import socket
        g, made = globals(), []

        class _R:
            status = 200
            def read(self): return b"[]"

        class _Sock:
            def settimeout(self, t): pass

        class _Conn:
            fail_connect = None
            fail_request = None
            def __init__(self, host, port, timeout=None):
                self.closed, self.sock = False, None
                made.append(self)
            def connect(self):
                if _Conn.fail_connect:
                    raise _Conn.fail_connect
                self.sock = _Sock()
            def request(self, *a, **k):
                if _Conn.fail_request:
                    raise _Conn.fail_request
            def getresponse(self): return _R()
            def close(self): self.closed = True

        saved = (http.client.HTTPSConnection, g["_CONN"])
        http.client.HTTPSConnection, g["_CONN"] = _Conn, None
        try:
            _send("GET", "/x", None, {}, 30, reuse=True)
            _send("GET", "/x", None, {}, 30, reuse=True)
            if len(made) != 1:
                raise PIIViolation(f"keep-alive not reused: {len(made)} connections for 2 GETs")
            _send("POST", "/x", b"{}", {}, 30, reuse=False)
            if len(made) != 2 or not made[-1].closed or g["_CONN"] is not made[0]:
                raise PIIViolation("non-retryable call touched the shared connection or left its own open")
            _Conn.fail_request = ConnectionResetError("reset")
            try:
                _send("GET", "/x", None, {}, 30, reuse=True)
                raise PIIViolation("request failure did not raise")
            except ConnectionResetError:
                if g["_CONN"] is not None or not made[0].closed:
                    raise PIIViolation("a failed shared connection was not dropped")
            _Conn.fail_request = None
            for err in (socket.gaierror(8, "nodename nor servname"), ssl.SSLError(1, "handshake"),
                        TimeoutError("timed out"), OSError(65, "no route")):
                _Conn.fail_connect = err
                try:
                    _send("POST", "/x", b"{}", {}, 30, reuse=False)
                    raise PIIViolation(f"{type(err).__name__} at connect did not raise")
                except NotSent:
                    pass
            _Conn.fail_connect = None
        finally:
            http.client.HTTPSConnection, g["_CONN"] = saved
    add("_send lifecycle: one shared conn, non-retryable isolated + closed, dropped on error, any connect OSError -> NotSent",
        _send_lifecycle_case, False)
    add("prose scan catches `POST /doc_claims`",
        lambda: None if _PROSE_VERB_RE.search("then `POST /doc_claims` with") else (_ for _ in ()).throw(PIIViolation("miss")), False)

    # --- YED-320 refusal telemetry ------------------------------------------------------------------
    def _fail(why):
        raise PIIViolation(why)        # in a False-expect case, raising = the case fails

    def _read_tel():
        try:
            return [json.loads(x) for x in open(g["TELEMETRY_PATH"], encoding="utf-8")]
        except FileNotFoundError:
            return []

    def _clear():
        open(g["TELEMETRY_PATH"], "w").close()

    def _leaks(rec, value):
        """Any digit (other than the 9 mask) or 3-letter run of `value` in a value-bearing field."""
        text = json.dumps({k: v for k, v in rec.items() if k not in ("ts", "rule", "scan_ms", "batch_size")}).lower()
        digits = {c for c in value if c.isdigit() and c != "9"}
        runs = {w[i:i + 3] for w in re.findall(r"[^\W\d_]+", value.lower()) for i in range(len(w) - 2)}
        return any(d in text for d in digits) or any(r in text for r in runs)

    def _splitter_case():
        live = split_alternatives(PHONE_RE.pattern)
        fx = split_alternatives(_FIXTURE_3ALT)
        if "|".join(live) != PHONE_RE.pattern or len(live) not in (2, 3):
            _fail(f"live split drifted ({len(live)} parts)")
        if "|".join(fx) != _FIXTURE_3ALT or len(fx) != 3:
            _fail(f"fixture split drifted ({len(fx)} parts)")
        if split_alternatives(r"a(b|c)|[|(]d|\|e|[]|]f") != ["a(b|c)", "[|(]d", r"\|e", "[]|]f"]:
            _fail("splitter mishandles groups / classes / escapes")
        for text, want in (("call 555-123-4567", "phone_alt1"), ("+15551234567", "phone_alt2"),
                           ("+44 20 7946 0958", "phone_alt3")):
            m = re.search(_FIXTURE_3ALT, text)
            got = _phone_rule(text, m.start(), _FIXTURE_3ALT)
            if got != want:
                _fail(f"{text!r} labelled {got}, want {want}")
        m = PHONE_RE.search("555-123-4567")
        if _phone_rule("555-123-4567", m.start()) != "phone_alt1":
            _fail("live pattern labelling broke")
    add("telemetry: alternative splitter joins back to PHONE_RE exactly (live + 3-alt fixture); labels alt1/2/3",
        _splitter_case, False)

    def _walk_parity_case():
        row = {"bio": "x", "metadata": {"a": {"b": ["p", {"c": "q"}]}, "d": "r"}, "name": "n"}
        twin = [(p, s) for col, v in row.items() for p, _, s in _walk_masked(v, str(col), "m")]
        if twin != list(_walk(row)):
            _fail("the masked walk's paths differ from _walk: refusal messages would change")
        masked = [mk for col, v in row.items() for _, mk, _ in _walk_masked(v, str(col), _label_col("person", col))]
        if masked != ["bio", "metadata.*.*[0]", "metadata.*.*[1].*", "metadata.*", "name"]:
            _fail(f"masked paths {masked}")
    add("telemetry: masked walk yields _walk's exact paths (messages unchanged) and masks every nested key",
        _walk_parity_case, False)

    def _no_value_case():
        g["PHONE_RE"], live_re = re.compile(_FIXTURE_3ALT), g["PHONE_RE"]   # #277 shape, so +44 is refused
        _clear()
        inputs = [("+44 20 7946 0958", "phone_alt3", "+99 99 9999 9999"),
                  ("555-123-4567", "phone_alt1", "999-999-9999"),
                  ("ivan.petrov@yandex.ru", "email", "aaaa.aaaaaa@aaaaaa.aa")]
        try:
            for value, _, _ in inputs:
                try:
                    guard_body("/person", [{"name": "ok"}, {"name": "n", "bio": f"reach me: {value}"}, {"name": "z"}])
                    _fail(f"{value!r} not refused")
                except PIIViolation as e:
                    if value in str(e):
                        _fail("refusal message changed shape")
        finally:
            g["PHONE_RE"] = live_re
        recs = _read_tel()
        if len(recs) != 3:
            _fail(f"{len(recs)} records for 3 refusals")
        base = {"ts", "table", "path", "rule", "batch_size", "caller", "shape", "scan_ms"}
        for (value, rule, shape), r in zip(inputs, recs):
            if set(r) != base | ({"asset_code"} if rule == "email" else {"prose_hint"}):
                _fail(f"unexpected fields {sorted(r)}")
            if (r["rule"], r["shape"], r["table"], r["path"], r["batch_size"]) != (rule, shape, "person", "bio", 3):
                _fail(f"record {r} != {(rule, shape, 'person', 'bio', 3)}")
            if _leaks(r, value) or not isinstance(r["scan_ms"], (int, float)):
                _fail(f"value leaked or scan_ms missing: {r}")
    add("telemetry: refusals of +44 20 7946 0958 / 555-123-4567 / an email record rule + shape, never the value",
        _no_value_case, False)

    def _key_table_leak_case():
        _clear()
        cases = [("person", {"name": "n", "metadata": {"Jane Q Doe (Acme, NYC)": "555-123-4567"}}, "Jane Q Doe (Acme, NYC)",
                  ("person", "metadata.*")),
                 ("person", {"name": "n", "metadata": {"2125550134": "call 555-123-4567"}}, "2125550134",
                  ("person", "metadata.*")),
                 ("person", {"name": "n", "metadata": {"notes": ["a", {"Jane Doe home": "555.123.4567"}]}}, "Jane Doe home",
                  ("person", "metadata.*[1].*")),
                 ("person", {"jane@acme.com": "x"}, "jane@acme.com", ("person", "<unlisted>")),
                 ("jane.doe@acme.com", {"x": 1}, "jane.doe@acme.com", ("<unlisted>", ""))]
        for table, row, secret, _ in cases:
            try:
                guard(table, row)
                _fail(f"{secret!r} case not refused")
            except PIIViolation:
                pass
        recs = _read_tel()
        if len(recs) != len(cases):
            _fail(f"{len(recs)} records for {len(cases)} refusals")
        for (_, _, secret, want), r in zip(cases, recs):
            if (r["table"], r["path"]) != want or _leaks(r, secret):
                _fail(f"key/table leak: {(r['table'], r['path'])} for {secret!r}")
    add("telemetry: a name key, a bare-digit key, a nested key, an email column and an email-as-table never surface",
        _key_table_leak_case, False)

    def _hints_case():
        g["PHONE_RE"], live_re = re.compile(_FIXTURE_3ALT), g["PHONE_RE"]
        _clear()
        try:
            for text in ("revenue up +12 345 678 EUR", "office +44 20 7946 0958", "revenue grew +44 20 7946 0958 last",
                         "+44 20 7946 0958 users", "logo@2x.png", "ivan.petrov@yandex.ru"):
                try:
                    guard("person", {"name": "n", "bio": text})
                except PIIViolation:
                    pass
        finally:
            g["PHONE_RE"] = live_re
        got = [(r["rule"], r.get("prose_hint"), r.get("asset_code")) for r in _read_tel()]
        if got != [("phone_alt3", True, None), ("phone_alt3", False, None), ("phone_alt3", True, None),
                   ("phone_alt3", True, None), ("email", None, True), ("email", None, False)]:
            _fail(f"hints {got}")
    add("telemetry: prose_hint / asset_code booleans classify in memory (numeric prose, asset-shaped email)",
        _hints_case, False)

    def _unwritable_case():
        bad = {"name": "n", "bio": "555-123-4567"}
        want = None
        try:
            guard("person", bad)
        except PIIViolation as e:
            want = str(e)
        saved_path, saved_shape = g["TELEMETRY_PATH"], g["_shape"]
        try:
            g["TELEMETRY_PATH"] = os.path.join(os.devnull, "no", "pii.jsonl")       # cannot be created
            for broken in (False, True):
                if broken:
                    g["_shape"] = lambda s: 1 / 0                                    # telemetry itself throws
                try:
                    guard("person", bad)
                    _fail("refusal lost when telemetry failed")
                except PIIViolation as e:
                    if want is None or str(e) != want:
                        _fail("refusal message changed when telemetry failed")
        finally:
            g["TELEMETRY_PATH"], g["_shape"] = saved_path, saved_shape
    add("telemetry: an unwritable path or a telemetry exception leaves the refusal intact (same message)",
        _unwritable_case, False)

    def _stub_req():
        saved = (g["_send"], g["load_key"])
        g["_send"], g["load_key"] = (lambda *a, **k: (201, "")), (lambda: "test-key")
        return saved

    def _ok_sample_case():
        _clear()
        g["_OK_ROWS"] = 0
        for i in range(OK_SAMPLE_EVERY * 2):
            guard("topic", {"name": f"Clean topic {i}"})                 # guard alone is not a write
        if _read_tel():
            _fail("guard() outside req() wrote ok_sample")
        saved = _stub_req()
        try:
            for i in range(OK_SAMPLE_EVERY * 2 + 1):
                req("POST", "/topic", {"name": f"Clean topic {i}", "description": "agents at trade shows"},
                    prefer="resolution=merge-duplicates")
        finally:
            g["_send"], g["load_key"] = saved
        recs = _read_tel()
        if len(recs) != 2 or any(set(r) != {"ts", "rule", "table", "scan_ms"} or r["rule"] != "ok_sample" for r in recs):
            _fail(f"ok_sample records wrong: {recs}")
    add("telemetry: every 50th clean row req() sends writes one content-free ok_sample; guard()/write() pre-check don't",
        _ok_sample_case, False)

    def _fault_case():
        bad = {"name": "n", "bio": "555-123-4567"}
        try:
            guard("person", bad)
        except PIIViolation as e:
            want = str(e)
        saved_req = _stub_req()
        saved_strf, saved_argv = time.strftime, sys.argv
        try:
            for fault in ("strftime", "argv"):
                if fault == "strftime":
                    def _clock_fault(*a):
                        raise RuntimeError("clock fault")
                    time.strftime = _clock_fault
                else:
                    time.strftime = saved_strf
                    del sys.argv
                g["_OK_ROWS"] = OK_SAMPLE_EVERY - 1                       # the next clean row samples
                st, _ = req("POST", "/topic", {"name": "clean"}, prefer="resolution=merge-duplicates")
                if st != 201:
                    _fail(f"{fault}: a clean row failed")
                try:
                    guard("person", bad)
                    _fail(f"{fault}: refusal lost")
                except PIIViolation as e:
                    if str(e) != want:
                        _fail(f"{fault}: refusal message changed")
        finally:
            time.strftime, sys.argv = saved_strf, saved_argv
            g["_send"], g["load_key"] = saved_req
    add("telemetry: fault injection (strftime raises; no sys.argv) never blocks a clean row or changes a refusal",
        _fault_case, False)

    def _rule_labels_case():
        _clear()
        thunks = [lambda: guard("person", {"email": "x"}), lambda: guard("topic", {"owner_ssn": "1"}),
                  lambda: guard("secrets", {"x": 1}), lambda: guard("person", "not a dict")]
        for t in thunks:
            try:
                t()
            except PIIViolation:
                pass
        got = [(r["rule"], r["table"], r["path"]) for r in _read_tel()]
        if got != [("forbidden_column", "person", "email"), ("not_allowlisted", "topic", "<unlisted>"),
                   ("no_allowlist", "<unlisted>", ""), ("body_type", "person", "")]:
            _fail(f"rule labels {got}")
    add("telemetry: column / table / body-type refusals carry their rule label", _rule_labels_case, False)

    def _switch_case():
        bad = {"name": "n", "bio": "555-123-4567"}
        for off in ("env", "api"):
            _clear()
            if off == "env":
                os.environ["SPINE_TELEMETRY"] = "off"
            else:
                telemetry(False)
            try:
                guard("person", bad)
                _fail("switch weakened the guard")
            except PIIViolation:
                pass
            finally:
                os.environ.pop("SPINE_TELEMETRY", None)
                telemetry(True)
            if _read_tel():
                _fail(f"telemetry written with the {off} switch off")
    add("telemetry: SPINE_TELEMETRY=off and telemetry(False) stop recording, never refusing", _switch_case, False)

    failures = 0
    for name, fn, expect in cases:
        try:
            fn()
            got = False
        except PIIViolation:
            got = True
        ok = got == expect
        failures += 0 if ok else 1
        print(f"  {'✓' if ok else '✗'} {name}")
    g["TELEMETRY_PATH"] = real_tel
    g["_TELEMETRY_ON"] = saved_switch[0]
    if saved_switch[1] is not None:
        os.environ["SPINE_TELEMETRY"] = saved_switch[1]
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
