#!/usr/bin/env python3
"""Feed classifier contract — JSON schema + validator for lane 4 (YED-304 Phase A, per #268).

The feed lane (feeds.py) stages RAW feed_items; classification happens in the Monday
session inside a NO-TOOLS SUBAGENT returning JSON (design §6 architecture, §8 prompt-
injection row). This module is the parent-side contract that subagent output must
satisfy before anything reaches a feed_items row or an event manifest:

  item in (feeds.py shape)  ->  classified record out:

    {
      "item_key":       "<64-hex sha256 of the canonical item URL — feeds.item_key>",
      "relevance":      0.0–1.0   how close the item is to Alex's themes/watchlist,
      "event_candidate": true|false,
      "kind":           null | "launch" | "market",
      "signal_type":    null | "news" | "partnership" | "layoff" | "paper" | "model_release",
      "companies":      ["existing company names to link — link-to-existing only"],
      "topics":         ["existing topic names to link — link-to-existing only"],
      "redacted_body":  redact_body(item.summary) — DETERMINISTIC, re-computed here,
      "reason":         "≤500 chars, why this classification"
    }

Redaction and the PII guard are tested alone (privacy-layer rule, #268 §8):
redact_body() is imported from substrate (ONE confidentiality dialect — no fork), and
every string in the record AND the source item is scanned with spine_client's own
EMAIL_RE / PHONE_RE / allowlist — a second dialect is what check_pii_regex_parity.py
exists to prevent. An email anywhere (e.g. a press contact in a summary) is a HARD
FAIL: PIIViolation, exit 2, no in-run override — the same contract as spine_client.

Pure/static: no network, no model calls, no file writes. The selftest runs offline on
repo fixtures (supabase/fixtures/feed_classifier/, *.example domains only — AGENTS.md
rule 4) and inline cases.

Usage:
    python3 .claude/scripts/feed_classifier.py --schema
    python3 .claude/scripts/feed_classifier.py --validate --record R.json --item I.json
    python3 .claude/scripts/feed_classifier.py --selftest

Exit codes (mirror spine_client): 0 = valid, 1 = schema/semantic violation or selftest
failure, 2 = PIIViolation.
"""
from __future__ import annotations
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spine_client import EMAIL_ALLOWLIST_RE, EMAIL_RE, PHONE_RE, PIIViolation  # noqa: E402
from substrate import redact_body  # noqa: E402  ONE confidentiality dialect (substrate.py:185)

# event.kind values lane 4 may claim (event_kind_enum, migration 0009; #268 lane 4:
# "classified launch/market events" — funding/exec_move are akta lane 2, not feeds).
CANDIDATE_KINDS = ("launch", "market")
# event.signal_type enum from #268 §3.1 minus hiring_pulse (lane 1 ats_pulse) — feeds
# can carry news, partnerships, layoffs, papers and model releases, never hiring pulses.
MARKET_SIGNAL_TYPES = ("news", "partnership", "layoff", "paper", "model_release")
# event_candidate=true requires at least this relevance (#268: the Monday brief counts
# only items the classifier judged relevant). Proposed default — the session-side
# manifest step may tighten it, never loosen it below the floor it documents.
EVENT_CANDIDATE_FLOOR = 0.6

REQUIRED_KEYS = ("item_key", "relevance", "event_candidate", "kind", "signal_type",
                 "companies", "topics", "redacted_body", "reason")
KEY_MAX, LIST_MAX, REASON_MAX = 120, 20, 500


class SchemaViolation(ValueError):
    """The record does not satisfy the classifier contract — hard fail, exit 1."""


# --------------------------------------------------------------------- JSON Schema
# Draft 2020-12, for pasting into the no-tools classifier subagent's prompt (--schema).
# Cross-field rules (kind/signal_type consistency, floor, entity edge) are semantic and
# live in validate_record — JSON Schema cannot express them without a second dialect.
SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Feed classifier output record (YED-304 Phase A, #268 lane 4)",
    "type": "object",
    "additionalProperties": False,
    "required": list(REQUIRED_KEYS),
    "properties": {
        "item_key": {"type": "string", "pattern": "^[0-9a-f]{64}$",
                     "description": "sha256 of the canonical item URL — feeds.item_key(item)"},
        "relevance": {"type": "number", "minimum": 0, "maximum": 1,
                      "description": "closeness to Alex's themes/watchlist; candidates need >= 0.6"},
        "event_candidate": {"type": "boolean",
                            "description": "true = warrant an event row via the Monday manifest"},
        "kind": {"enum": [None, *CANDIDATE_KINDS],
                 "description": "event.kind for the candidate row; null when not a candidate"},
        "signal_type": {"enum": [None, *MARKET_SIGNAL_TYPES],
                        "description": "event.signal_type (design §3.1); null for kind=launch"},
        "companies": {"type": "array", "items": {"type": "string", "minLength": 1},
                      "description": "EXISTING company names to link — link-to-existing only"},
        "topics": {"type": "array", "items": {"type": "string", "minLength": 1},
                   "description": "EXISTING topic names to link — link-to-existing only"},
        "redacted_body": {"type": "string",
                          "description": "EXACTLY redact_body(item.summary) — re-computed and enforced"},
        "reason": {"type": "string", "minLength": 1, "maxLength": 500},
    },
}


# --------------------------------------------------------------------- validation
def _walk(value, where):
    """(path, string) for every string inside nested dicts/lists/scalars — same traversal
    as spine_client._walk so paths read identically in guard messages."""
    if isinstance(value, str):
        yield where, value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield from _walk(v, f"{where}.{k}")
    elif isinstance(value, (list, tuple)):
        for i, v in enumerate(value):
            yield from _walk(v, f"{where}[{i}]")


def _scan_pii(obj: dict, where: str, problems: list[str]) -> None:
    """Collect contact-PII findings using spine_client's patterns — no second dialect."""
    for path, s in _walk(obj, where):
        for m in EMAIL_RE.finditer(s):
            if not EMAIL_ALLOWLIST_RE.search(m.group(0)):
                problems.append(
                    f"{path} contains an email address · ADR-9 tier 2: contact PII never "
                    f"enters the spine · fix: drop it from the producer (contact detail "
                    f"belongs in HubSpot) — hard fail, no in-run override")
        if PHONE_RE.search(s):
            problems.append(
                f"{path} contains a phone number · ADR-9 tier 2: contact PII never enters "
                f"the spine · fix: drop it from the producer (contact detail belongs in "
                f"HubSpot) — hard fail, no in-run override")


def _names(record: dict, key: str, problems: list[str]) -> None:
    vals = record[key]
    if not isinstance(vals, list):
        problems.append(f"{key}: must be an array of strings · got {type(vals).__name__}")
        return
    for i, v in enumerate(vals):
        if not isinstance(v, str) or not v.strip():
            problems.append(f"{key}[{i}]: must be a non-empty string")
        elif len(v) > KEY_MAX:
            problems.append(f"{key}[{i}]: exceeds {KEY_MAX} chars — link EXISTING names, "
                            f"not descriptions (#268 §3.2 link-to-existing only)")
    if len(vals) != len({str(v) for v in vals}):
        problems.append(f"{key}: duplicate entries")


def validate_record(record, item) -> None:
    """Validate one classified record against its source item.

    Raises PIIViolation when contact PII survives anywhere (exit 2) or SchemaViolation
    when the contract is broken (exit 1). Returns the record unchanged when valid.
    """
    problems: list[str] = []

    # Structure — fail-closed on unknown keys: a record carrying extra keys (prompt
    # injection trying to smuggle an instruction into the manifest writer) is invalid.
    if not isinstance(record, dict):
        raise SchemaViolation(f"record: must be a JSON object · got {type(record).__name__}")
    unknown = set(record) - set(REQUIRED_KEYS)
    if unknown:
        problems.append(f"record: unknown key(s) {sorted(unknown)} · additionalProperties: false")
    missing = [k for k in REQUIRED_KEYS if k not in record]
    if missing:
        problems.append(f"record: missing required key(s) {missing}")

    # PII over the record AND the source item — before semantic checks, so a summary
    # carrying a press contact hard-fails as a privacy breach, not a shape complaint.
    _scan_pii(record, "record", problems)
    _scan_pii(item, "item", problems)

    # Identity: the record must classify THE item it was given with.
    if "item_key" in record and isinstance(record["item_key"], str):
        from feeds import item_key
        if record["item_key"] != item_key(item):
            problems.append("item_key: does not match sha256(canonical item url) — "
                            "record/classified item mismatch")

    # Relevance.
    rel = record.get("relevance")
    if not isinstance(rel, (int, float)) or isinstance(rel, bool):
        problems.append(f"relevance: must be a number · got {type(rel).__name__}")
    elif not 0.0 <= rel <= 1.0:
        problems.append(f"relevance: must be within [0, 1] · got {rel}")

    # Event-candidate flags and their consistency matrix (#268 lane 4 + §3.1).
    cand = record.get("event_candidate")
    kind, sig = record.get("kind"), record.get("signal_type")
    if not isinstance(cand, bool):
        problems.append(f"event_candidate: must be a boolean · got {type(cand).__name__}")
    else:
        if not cand and (kind is not None or sig is not None):
            problems.append("event_candidate=false: kind and signal_type must both be null")
        if cand:
            if kind not in CANDIDATE_KINDS:
                problems.append(f"kind: candidate must be one of {list(CANDIDATE_KINDS)} "
                                f"· got {kind!r} (funding/exec_move are lane 2, not feeds)")
            if kind == "market" and sig not in MARKET_SIGNAL_TYPES:
                problems.append(f"signal_type: kind='market' requires one of "
                                f"{list(MARKET_SIGNAL_TYPES)} · got {sig!r}")
            if kind == "launch" and sig is not None:
                problems.append(f"signal_type: kind='launch' is its own kind — signal_type "
                                f"must be null · got {sig!r}")
            if not record.get("companies") and not record.get("topics"):
                problems.append("event_candidate=true requires >=1 company or topic edge "
                                "· market facts with no edge are refused (#268 §3.1)")
            if isinstance(rel, (int, float)) and rel < EVENT_CANDIDATE_FLOOR:
                problems.append(f"event_candidate=true requires relevance >= "
                                f"{EVENT_CANDIDATE_FLOOR} · got {rel}")
        _names(record, "companies", problems)
        _names(record, "topics", problems)

    # redacted_body: DETERMINISTIC. The validator re-computes redact_body(item.summary)
    # and accepts nothing else — subagent text never becomes the stored body.
    if "redacted_body" in record:
        if not isinstance(record["redacted_body"], str):
            problems.append("redacted_body: must be a string")
        else:
            want = redact_body(item.get("summary") or "")
            if record["redacted_body"] != want:
                problems.append("redacted_body: must equal redact_body(item.summary) "
                                "exactly — redaction is deterministic, not editorial")

    # reason: the Monday session reads it when deciding what makes the brief.
    if "reason" in record:
        if not isinstance(record["reason"], str) or not record["reason"].strip():
            problems.append("reason: must be a non-empty string")
        elif len(record["reason"]) > REASON_MAX:
            problems.append(f"reason: exceeds {REASON_MAX} chars")

    pii = [p for p in problems if "ADR-9" in p]
    if pii:
        raise PIIViolation("; ".join(pii))
    if problems:
        raise SchemaViolation("; ".join(problems))
    return record


# --------------------------------------------------------------------- selftest
def selftest() -> int:
    """Offline: repo fixtures + inline cases. fetch/network never runs here."""
    here = os.path.dirname(os.path.abspath(__file__))
    fx = os.path.join(here, "..", "..", "supabase", "fixtures", "feed_classifier")
    ok = 0

    def check(label: str, good: bool) -> None:
        nonlocal ok
        ok += good
        print(f"  {'✓' if good else '✗'} {label}")

    def load(name: str):
        with open(os.path.join(fx, name), encoding="utf-8") as f:
            return json.load(f)

    def raises(exc, fn) -> bool:
        try:
            fn()
        except exc:
            return True
        return False

    # --- positive fixtures validate
    for tag in ("launch", "market", "confidential"):
        item, record = load(f"item_{tag}.json"), load(f"classified_{tag}.json")
        try:
            validate_record(record, item)
            good = True
        except (PIIViolation, SchemaViolation) as e:
            print(f"    ({tag}: {e})")
            good = False
        check(f"fixture {tag}: item + classified record validate", good)

    # --- redaction is deterministic and strips confidential lines
    item, record = load("item_confidential.json"), load("classified_confidential.json")
    from substrate import redact_body as rb
    check("redact_body: confidential line dropped, rest intact",
          "stays in the room" not in record["redacted_body"]
          and record["redacted_body"] == rb(item["summary"])
          and "integration launch" in record["redacted_body"])

    # --- schema export stays consistent with the module constants (no second dialect)
    exported = json.dumps(SCHEMA)  # must be JSON-serializable for the subagent prompt
    props = json.loads(exported)["properties"]
    check("schema: signal_type enum matches MARKET_SIGNAL_TYPES + null",
          props["signal_type"]["enum"] == [None, *MARKET_SIGNAL_TYPES])
    check("schema: kind enum matches CANDIDATE_KINDS + null",
          props["kind"]["enum"] == [None, *CANDIDATE_KINDS])
    check("schema: required keys match REQUIRED_KEYS",
          json.loads(exported)["required"] == list(REQUIRED_KEYS))

    # --- negative: identity and shape
    item, record = load("item_launch.json"), load("classified_launch.json")
    check("item_key mismatch -> SchemaViolation",
          raises(SchemaViolation, lambda: validate_record(
              {**record, "item_key": "0" * 64}, item)))
    check("unknown key rejected (fail-closed on smuggled fields)",
          raises(SchemaViolation, lambda: validate_record({**record, "execute": "rm -rf"}, item)))
    check("relevance > 1 -> SchemaViolation",
          raises(SchemaViolation, lambda: validate_record({**record, "relevance": 1.5}, item)))
    check("relevance < 0 -> SchemaViolation",
          raises(SchemaViolation, lambda: validate_record({**record, "relevance": -0.1}, item)))
    check("redacted_body tampered -> SchemaViolation (deterministic redaction)",
          raises(SchemaViolation, lambda: validate_record(
              {**record, "redacted_body": record["redacted_body"] + " (paraphrased)"}, item)))

    # --- negative: candidate flag matrix
    check("kind='funding' rejected (lane 2 kind, not feeds)",
          raises(SchemaViolation, lambda: validate_record({**record, "kind": "funding"}, item)))
    check("kind='market' without signal_type rejected",
          raises(SchemaViolation, lambda: validate_record(
              {**record, "kind": "market", "signal_type": None}, item)))
    check("kind='launch' with signal_type rejected",
          raises(SchemaViolation, lambda: validate_record(
              {**record, "signal_type": "news"}, item)))
    check("candidate with zero entity edges refused (#268 §3.1)",
          raises(SchemaViolation, lambda: validate_record(
              {**record, "companies": [], "topics": []}, item)))
    check("candidate below relevance floor rejected",
          raises(SchemaViolation, lambda: validate_record({**record, "relevance": 0.4}, item)))
    check("non-candidate with kind set rejected",
          raises(SchemaViolation, lambda: validate_record(
              {**load("classified_confidential.json"), "kind": "market",
               "signal_type": "news"}, load("item_confidential.json"))))

    # --- PII: the guard hard-fails, tested ALONE (privacy-layer rule, #268 §8)
    pii_item, pii_record = load("item_pii_email.json"), load("classified_pii_email.json")

    def pii_message() -> str:
        try:
            validate_record(pii_record, pii_item)
        except PIIViolation as e:
            return str(e)
        return ""

    check("email in a summary HARD-FAILS the guard, naming the field path",
          "item.summary" in pii_message() and "email address" in pii_message())
    check("email inside a linked name also hard-fails",
          raises(PIIViolation, lambda: validate_record(
              {**record, "companies": ["press@acme.example"]}, item)))
    check("phone in a summary hard-fails",
          raises(PIIViolation, lambda: validate_record(
              pii_record, {**pii_item, "summary": "Call the newsroom at (212) 555-0148."})))
    check("allowlisted noreply address passes (spine parity)",
          validate_record(
              {**pii_record, "redacted_body": rb("Bounces go to noreply@delta.example.")},
              {**pii_item, "summary": "Bounces go to noreply@delta.example."}) is not None)

    # --- backstop: the same email through spine_client.guard() also hard-fails
    import spine_client
    check("spine guard backstop: same summary via spine_client.guard() raises",
          raises(spine_client.PIIViolation, lambda: spine_client.guard(
              "topic", {"name": "feed-fixture", "metadata": {"summary": pii_item["summary"]}})))

    # --- purity: no network surface in this module's own imports (AST, not text —
    # spine_client itself imports urllib for REST reads; the guard path stays pure)
    import ast
    tree = ast.parse(open(os.path.abspath(__file__), encoding="utf-8").read())
    imported = ({a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import)
                 for a in n.names}
                | {n.module.split(".")[0] for n in ast.walk(tree)
                   if isinstance(n, ast.ImportFrom) and n.module})
    check("pure/static: module imports no network surface",
          not imported & {"urllib", "requests", "http", "socket", "ftplib", "httpx", "aiohttp"})

    total = 24
    print(f"selftest: {ok}/{total} checks pass")
    return 0 if ok == total else 1


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    if "--schema" in argv:
        print(json.dumps(SCHEMA, indent=2))
        return 0
    if "--validate" in argv:
        def _load(flag: str):
            return json.load(open(argv[argv.index(flag) + 1], encoding="utf-8"))
        try:
            validate_record(_load("--record"), _load("--item"))
        except PIIViolation as e:
            print(f"PIIViolation: {e}", file=sys.stderr)
            return 2
        except SchemaViolation as e:
            print(f"SchemaViolation: {e}", file=sys.stderr)
            return 1
        print("record valid")
        return 0
    print(__doc__.strip())
    print("\n--schema | --validate --record R.json --item I.json | --selftest")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
