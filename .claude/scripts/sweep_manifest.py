#!/usr/bin/env python3
"""sweep_manifest.py — validate a theme-sweeper manifest before anything reads it (YED-384, ADR-14 §2.2-2.3).

The `theme-sweeper` agent reads hostile web text and returns ONE JSON manifest. This script is the
parent's gate on that untrusted input: schema, dates inside the window, https only, a kind enum
mapped onto the graph's event.kind / signal_type, no email or phone anywhere (spine_client's own
regexes), dedup by canonical URL (feeds.canonical_url), and `novel` recomputed against a
known-entities list. It never writes to a database; the `stage-market` writer comes after 0022.

Errors name the field path and the rule, never the offending value: the manifest is page-derived
text, and echoing it back into a session is how an injection travels.

Usage:
  python3 sweep_manifest.py validate MANIFEST.json [--known KNOWN.json] [--cap N] [--out NORMALIZED.json]
  python3 sweep_manifest.py --selftest
Exit: 0 valid · 2 manifest violates the contract · 1 bad invocation / unreadable file.
Stdlib only (CI runs it with plain python3).

Manifest schema (strict: unknown keys are a violation, so a stray contact field cannot ride along):
  {
    "theme":      str (1..120),
    "theme_id":   str | null,               # uuid from mi.theme_week when the seed had one
    "query_id":   str | null,               # sweep_query row id, once that table exists
    "window":     {"from": "YYYY-MM-DD", "to": "YYYY-MM-DD"},   # inclusive, from <= to
    "items": [{
      "date":        "YYYY-MM-DD",          # when the thing happened; inside the window
      "kind":        one of KIND_MAP keys,
      "company":     str (1..120),          # the company the event happened to
      "headline":    str (1..300),          # one dated atomic fact, company named
      "url":         "https://…",           # the hit as found
      "primary_url": "https://…" | null,    # the primary page when `url` is an aggregator
      "source_kind": one of SOURCE_KINDS,
      "why":         str (1..240),          # why it matters to the theme
      "quote":       str (<= 25 words) | null,
      "people":      [{"name": str, "role": str}],   # public figures central to the event only;
                                             # exactly these two keys. Passing this validator is NOT
                                             # spine admission: the stage-market writer decides
                                             # whether names reach the graph (ADR-7 R2, ADR-9).
      "confidence":  number 0..1,
      "novel":       bool                    # the agent's guess; this script recomputes it
    }],
    "new_entities": [{"name": str, "website": "https://…" | null, "why": str (1..160)}],
    "audit": {"searches": int >= 0, "fetches": int >= 0, "dropped_out_of_window": int >= 0,
              "dropped_no_date": int >= 0, "source_mix": {source_kind: int}}
  }
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from spine_client import EMAIL_RE, EMAIL_ALLOWLIST_RE, PHONE_RE, FORBIDDEN_COLUMNS  # noqa: E402  (ADR-9 patterns, one source)
from feeds import canonical_url  # noqa: E402  (cross-lane URL identity)

FIXTURES = os.path.join(HERE, "fixtures", "sweep")

# Manifest kind -> (public.event.kind, public.event.signal_type). Targets are the live CHECKs:
# event_kind_enum (0009) market|funding|launch|exec_move for the market lens, and
# event_signal_type_check (0016) paper|model_release|news|partnership|layoff|hiring_pulse.
# acquisition and pricing have no finer graph value yet, so they land as market/news and keep
# their manifest kind for the writer's metadata (flagged in the PR, not decided here).
KIND_MAP = {
    "funding":     ("funding", None),
    "launch":      ("launch", None),
    "release":     ("launch", "model_release"),
    "exec_move":   ("exec_move", None),
    "acquisition": ("market", "news"),
    "partnership": ("market", "partnership"),
    "layoff":      ("market", "layoff"),
    "paper":       ("market", "paper"),
    "pricing":     ("market", "news"),
    "market":      ("market", "news"),
}
GRAPH_EVENT_KINDS = {"market", "funding", "launch", "exec_move"}
GRAPH_SIGNAL_TYPES = {None, "paper", "model_release", "news", "partnership", "layoff", "hiring_pulse"}
SOURCE_KINDS = {"news", "blog", "changelog", "paper", "hn", "newsletter", "release", "filing"}
# Hosts that summarise other people's news: a hit here should carry the primary page too (pilot lesson).
AGGREGATOR_HOSTS = {"news.ycombinator.com", "hn.algolia.com", "news.google.com", "techmeme.com",
                    "finsmes.com", "aitoolsclub.com", "reddit.com", "x.com", "twitter.com",
                    "linkedin.com", "medium.com", "substack.com", "beehiiv.com"}
MIN_SEARCHES = 15
QUOTE_MAX_WORDS = 25

TOP_KEYS = {"theme", "theme_id", "query_id", "window", "items", "new_entities", "audit"}
ITEM_KEYS = {"date", "kind", "company", "headline", "url", "primary_url", "source_kind", "why",
             "quote", "people", "confidence", "novel"}
ENTITY_KEYS = {"name", "website", "why"}
PERSON_KEYS = {"name", "role"}
AUDIT_KEYS = {"searches", "fetches", "dropped_out_of_window", "dropped_no_date", "source_mix"}
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SUFFIXES = ("inc", "llc", "ltd", "corp", "corporation", "co", "gmbh", "sa")


def norm_name(name: str) -> str:
    """Entity identity for novelty: lowercase alphanumerics, trailing corporate suffix dropped."""
    words = re.sub(r"[^a-z0-9 ]+", " ", name.lower()).split()
    while len(words) > 1 and words[-1] in SUFFIXES:
        words.pop()
    return "".join(words)


def parse_date(s) -> date | None:
    if not isinstance(s, str) or not ISO_DATE.match(s):
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def https_host(u) -> str | None:
    """Host of an https URL with a real host, else None."""
    if not isinstance(u, str):
        return None
    p = urllib.parse.urlsplit(u.strip())
    if p.scheme != "https" or not p.hostname or "." not in p.hostname:
        return None
    return p.hostname.lower()


def _walk(value, path=""):
    """Yield (path, key_or_None, string) for every key and string value in the manifest."""
    if isinstance(value, dict):
        for k, v in value.items():
            yield (f"{path}.{k}" if path else str(k)), str(k), None
            yield from _walk(v, f"{path}.{k}" if path else str(k))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from _walk(v, f"{path}[{i}]")
    elif isinstance(value, str):
        yield path, None, value


class Report:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, path: str, rule: str):
        self.errors.append(f"{path}: {rule}")

    def warn(self, path: str, rule: str):
        self.warnings.append(f"{path}: {rule}")


def _str(r: Report, obj: dict, key: str, path: str, lo: int, hi: int, nullable=False):
    v = obj.get(key)
    if v is None and nullable:
        return
    if not isinstance(v, str) or not (lo <= len(v.strip()) <= hi):
        r.err(f"{path}.{key}", f"string of {lo}..{hi} chars{' or null' if nullable else ''}")


def _keys(r: Report, obj, allowed: set, required: set, path: str) -> bool:
    if not isinstance(obj, dict):
        r.err(path or "manifest", "must be an object")
        return False
    for k in sorted(set(obj) - allowed):
        r.err(f"{path}.{k}" if path else k, "unknown key (strict schema)")
    for k in sorted(required - set(obj)):
        r.err(f"{path}.{k}" if path else k, "missing required key")
    return True


def validate(m, known: set[str] | None = None, cap: int | None = None) -> tuple[Report, dict]:
    """(report, normalized). normalized carries graph kinds, canonical URLs and recomputed `novel`."""
    r = Report()
    known = known or set()
    if not _keys(r, m, TOP_KEYS, TOP_KEYS, ""):
        return r, {}

    # PII and forbidden keys first, over the whole document: no layer below may be the only catch.
    for path, key, s in _walk(m):
        if key is not None and key.lower() in FORBIDDEN_COLUMNS:
            r.err(path, "contact-field key forbidden (ADR-9)")
        if s is None:
            continue
        if any(not EMAIL_ALLOWLIST_RE.search(x.group(0)) for x in EMAIL_RE.finditer(s)):
            r.err(path, "contains an email address (ADR-9: contact PII never enters the pipeline)")
        if PHONE_RE.search(s):
            r.err(path, "contains a phone number (ADR-9: contact PII never enters the pipeline)")

    _str(r, m, "theme", "manifest", 1, 120)
    for k in ("theme_id", "query_id"):
        _str(r, m, k, "manifest", 1, 64, nullable=True)

    w = m.get("window")
    lo = hi = None
    if _keys(r, w, {"from", "to"}, {"from", "to"}, "window"):
        lo, hi = parse_date(w.get("from")), parse_date(w.get("to"))
        if lo is None:
            r.err("window.from", "ISO date YYYY-MM-DD")
        if hi is None:
            r.err("window.to", "ISO date YYYY-MM-DD")
        if lo and hi and lo > hi:
            r.err("window", "from is after to")

    items = m.get("items")
    norm_items = []
    if not isinstance(items, list):
        r.err("items", "must be a list")
        items = []
    if cap is not None and len(items) > cap:
        r.err("items", f"{len(items)} items exceed the cap of {cap}")
    seen: dict[str, int] = {}
    for i, it in enumerate(items):
        p = f"items[{i}]"
        if not _keys(r, it, ITEM_KEYS, ITEM_KEYS, p):
            continue
        d = parse_date(it.get("date"))
        if d is None:
            r.err(f"{p}.date", "ISO date YYYY-MM-DD")
        elif lo and hi and not (lo <= d <= hi):
            r.err(f"{p}.date", "outside the window")
        kind = it.get("kind")
        if kind not in KIND_MAP:
            r.err(f"{p}.kind", f"not in {sorted(KIND_MAP)}")
        _str(r, it, "company", p, 1, 120)
        _str(r, it, "headline", p, 1, 300)
        _str(r, it, "why", p, 1, 240)
        host = https_host(it.get("url"))
        if host is None:
            r.err(f"{p}.url", "must be an https URL with a host")
        prim = it.get("primary_url")
        prim_host = None
        if prim is not None:
            prim_host = https_host(prim)
            if prim_host is None:
                r.err(f"{p}.primary_url", "must be an https URL with a host, or null")
        if host and prim is None and any(host == a or host.endswith("." + a) for a in AGGREGATOR_HOSTS):
            r.warn(f"{p}.url", "aggregator host without primary_url (fetch the primary page)")
        if it.get("source_kind") not in SOURCE_KINDS:
            r.err(f"{p}.source_kind", f"not in {sorted(SOURCE_KINDS)}")
        q = it.get("quote")
        if q is not None and (not isinstance(q, str) or not q.strip() or len(q.split()) > QUOTE_MAX_WORDS):
            r.err(f"{p}.quote", f"non-empty string of <= {QUOTE_MAX_WORDS} words, or null")
        people = it.get("people")
        if not isinstance(people, list):
            r.err(f"{p}.people", "must be a list (empty when no one is central)")
            people = []
        for j, person in enumerate(people):
            pp = f"{p}.people[{j}]"
            if _keys(r, person, PERSON_KEYS, PERSON_KEYS, pp):
                _str(r, person, "name", pp, 1, 80)
                _str(r, person, "role", pp, 1, 120)
        c = it.get("confidence")
        if isinstance(c, bool) or not isinstance(c, (int, float)) or not 0 <= c <= 1:
            r.err(f"{p}.confidence", "number in 0..1")
        if not isinstance(it.get("novel"), bool):
            r.err(f"{p}.novel", "boolean")

        keys = {canonical_url(u) for u, h in ((it.get("url"), host), (prim, prim_host)) if h}
        for k in keys:
            if k in seen:
                r.err(f"{p}.url", f"duplicate of items[{seen[k]}] by canonical URL")
                break
        for k in keys:
            seen.setdefault(k, i)

        company = it.get("company") if isinstance(it.get("company"), str) else ""
        novel = bool(company) and norm_name(company) not in known
        ek, st = KIND_MAP.get(kind, (None, None))
        norm_items.append({**it, "novel": novel, "agent_novel": it.get("novel"), "event_kind": ek,
                           "signal_type": st,
                           "canonical_url": canonical_url(prim if prim_host else it["url"]) if (prim_host or host) else None})

    ents = m.get("new_entities")
    norm_ents = []
    if not isinstance(ents, list):
        r.err("new_entities", "must be a list")
        ents = []
    for i, e in enumerate(ents):
        p = f"new_entities[{i}]"
        if not _keys(r, e, ENTITY_KEYS, ENTITY_KEYS, p):
            continue
        _str(r, e, "name", p, 1, 120)
        _str(r, e, "why", p, 1, 160)
        if e.get("website") is not None and https_host(e.get("website")) is None:
            r.err(f"{p}.website", "https URL or null")
        name = e.get("name") if isinstance(e.get("name"), str) else ""
        norm_ents.append({**e, "novel": bool(name) and norm_name(name) not in known})

    a = m.get("audit")
    if _keys(r, a, AUDIT_KEYS, AUDIT_KEYS, "audit"):
        for k in ("searches", "fetches", "dropped_out_of_window", "dropped_no_date"):
            v = a.get(k)
            if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                r.err(f"audit.{k}", "non-negative integer")
        mix = a.get("source_mix")
        if not isinstance(mix, dict) or any(k not in SOURCE_KINDS or isinstance(v, bool) or not isinstance(v, int)
                                            for k, v in mix.items()):
            r.err("audit.source_mix", f"object of {sorted(SOURCE_KINDS)} -> int")
        if isinstance(a.get("searches"), int) and a["searches"] < MIN_SEARCHES:
            r.warn("audit.searches", f"fewer than {MIN_SEARCHES} searches")

    # Self-consistency: the graph mapping must only ever produce values the live CHECKs accept.
    assert all(ek in GRAPH_EVENT_KINDS and st in GRAPH_SIGNAL_TYPES for ek, st in KIND_MAP.values())

    normalized = {**m, "items": norm_items, "new_entities": norm_ents}
    return r, normalized


def summary(r: Report, normalized: dict) -> str:
    items = normalized.get("items", [])
    ents = normalized.get("new_entities", [])
    kinds: dict[str, int] = {}
    for it in items:
        kinds[str(it.get("kind"))] = kinds.get(str(it.get("kind")), 0) + 1
    overrides = sum(1 for it in items if isinstance(it.get("agent_novel"), bool) and it["agent_novel"] != it["novel"])
    lines = [f"sweep_manifest: {'VALID' if not r.errors else 'INVALID'} · items {len(items)} · "
             f"novel {sum(1 for it in items if it.get('novel'))}/{len(items)} (agent flag overridden {overrides}) · "
             f"new_entities {len(ents)} (novel {sum(1 for e in ents if e.get('novel'))}) · "
             f"kinds {json.dumps(kinds, sort_keys=True)}"]
    lines += [f"  ERROR {e}" for e in r.errors]
    lines += [f"  warn  {w}" for w in r.warnings]
    return "\n".join(lines)


def load_known(path: str | None) -> set[str]:
    if not path:
        return set()
    with open(path, encoding="utf-8") as f:
        names = json.load(f)
    if not isinstance(names, list) or not all(isinstance(n, str) for n in names):
        raise ValueError("known-entities file must be a JSON list of names")
    return {norm_name(n) for n in names}


def selftest() -> bool:
    known = load_known(os.path.join(FIXTURES, "known_entities.json"))
    cases = [  # (fixture, expect_valid, rule substring that must appear in an error)
        ("manifest_valid.json", True, None),
        ("manifest_bad_out_of_window.json", False, "outside the window"),
        ("manifest_bad_http_url.json", False, "https URL"),
        ("manifest_bad_email_headline.json", False, "email address"),
        ("manifest_bad_phone_why.json", False, "phone number"),
        ("manifest_bad_duplicate_url.json", False, "duplicate of items[0]"),
        ("manifest_bad_kind.json", False, "kind: not in"),
        ("manifest_bad_contact_key.json", False, "unknown key"),
    ]
    ok = True
    for fn, want_valid, rule in cases:
        with open(os.path.join(FIXTURES, fn), encoding="utf-8") as f:
            m = json.load(f)
        r, norm = validate(m, known, cap=20)
        passed = (not r.errors) == want_valid and (rule is None or any(rule in e for e in r.errors))
        # A violation message must never echo the offending text (injection hygiene).
        if any("@" in e or "http://" in e for e in r.errors):
            passed = False
        ok &= passed
        print(f"{'ok  ' if passed else 'FAIL'} {fn}: {'valid' if not r.errors else r.errors[:2]}")
        if fn == "manifest_valid.json":
            novel = [it["novel"] for it in norm["items"]]
            mapped = [(it["event_kind"], it["signal_type"]) for it in norm["items"]]
            want_novel = [True, False, True]
            want_mapped = [("funding", None), ("launch", "model_release"), ("market", "news")]
            sub = novel == want_novel and mapped == want_mapped and norm["items"][1]["agent_novel"] is True
            ok &= sub
            print(f"{'ok  ' if sub else 'FAIL'} novel recomputed vs known list + kind mapped to graph: {novel} {mapped}")
            warn = any("aggregator" in w for w in r.warnings)
            ok &= warn
            print(f"{'ok  ' if warn else 'FAIL'} aggregator URL without primary_url warns")
    r, _ = validate(json.load(open(os.path.join(FIXTURES, "manifest_valid.json"), encoding="utf-8")), known, cap=2)
    capped = any("exceed the cap" in e for e in r.errors)
    ok &= capped
    print(f"{'ok  ' if capped else 'FAIL'} --cap enforced")
    canon = canonical_url("https://Example.com/a/?utm_source=x#frag") == canonical_url("https://example.com/a")
    ok &= canon
    print(f"{'ok  ' if canon else 'FAIL'} canonical_url folds case, tracking params, fragment, trailing slash")
    print(f"selftest: {'PASS' if ok else 'FAIL'} ({len(cases) + 4} checks)")
    return ok


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv[:1] == ["--selftest"]:
        return 0 if selftest() else 1
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate")
    v.add_argument("manifest")
    v.add_argument("--known", help="JSON list of entity names already in the graph")
    v.add_argument("--cap", type=int, help="maximum items allowed")
    v.add_argument("--out", help="write the normalized manifest (graph kinds, canonical URLs, novel) here")
    a = ap.parse_args(argv)
    try:
        with open(a.manifest, encoding="utf-8") as f:
            m = json.load(f)
        known = load_known(a.known)
    except (OSError, ValueError) as e:
        print(f"sweep_manifest: cannot read input: {type(e).__name__}", file=sys.stderr)
        return 1
    r, norm = validate(m, known, a.cap)
    print(summary(r, norm))
    if r.errors:
        return 2
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(norm, f, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
