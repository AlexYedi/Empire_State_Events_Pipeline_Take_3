#!/usr/bin/env python3
"""ats_pulse.py — lane 1 hiring pulse (YED-304, #268 design): ats_pull TSV → per-company weekly counts.

Spec: docs/proposals/2026-11-04-market-lens-and-slices.md §2 lane 1 and §3.1 (signal_type).
Producer chain: ats_pull.py (boards → TSV) → THIS → substrate.py ensure-event (dry-run until
migration 0015/0016 adds event.signal_type). Weekly consumer: the Monday Market Brief (§5).

  ats_pulse.py [TSV ...] [--prior pulse.json] [--asof YYYY-MM-DD] [--out FILE]
  ats_pulse.py --validate FILE            # offline manifest check — the Action's dry-run write step
  ats_pulse.py --selftest                 # inline fixtures + negative-PII cases, no network

One hiring_pulse market event per company per ISO week. COUNTS ONLY — role titles are counted, then
dropped; no title, name, or person ever reaches the output (a structural guarantee, not a convention:
the manifest builder never sees a title it could emit, and every emitted string is re-scanned with
spine_client's ADR-9 email/phone regexes — a hit is a hard fail, defense in depth against upstream
format drift). Counts: metadata {roles_open, gtm_roles, ai_gtm_roles, delta_wow}.

  roles_open    rows for the company in the input TSV (ats_pull output is already GTM-filtered, so
                on today's input this equals gtm_roles; the separate fields keep the manifest contract
                stable if a future lane feeds unfiltered boards)
  gtm_roles     rows whose title passes ats_pull.keep_title (imported, never re-implemented)
  ai_gtm_roles  gtm_roles whose title also carries an AI signal (AI/ML/LLM/GPT/agentic/…)
  delta_wow     roles_open this week − last week's roles_open, from --prior (last week's pulse.json);
                None = no baseline yet (the null-baseline rule — never report a delta without one)

Dedup: rows dedupe on the ats_pull `key` (vendor:id) first, then the manifest's per-event dedup key is
(company, kind, week) — the §3.2 secondary key; canonical-URL dedup does not apply (a pulse has no URL).

Exit codes: 0 ok · 1 selftest or --validate failure · 2 bad args · 3 unreadable/malformed input.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
import tempfile
from datetime import date, datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
import ats_pull  # noqa: E402  (parse/projection only — the pulse never fetches boards itself)
from spine_client import EMAIL_ALLOWLIST_RE, EMAIL_RE, PHONE_RE, PIIViolation  # noqa: E402

SOURCE = "ats_pulse"                    # event.source prefix (§3.1 source_system)
SIGNAL_TYPE = "hiring_pulse"            # event.signal_type once migration 0016 lands
META_KEYS = ("roles_open", "gtm_roles", "ai_gtm_roles", "delta_wow")
# Case-insensitive \bAI\b also matches a bare "ai" ("Root.ai") — treated as an AI signal on purpose.
AI_TERM = re.compile(r"\bAI\b|\bML\b|LLM|GPT|GenAI|A\.I\.|agentic|machine learning|copilot", re.I)

MANIFEST_KEYS = ("week", "generated_at", "signal_type", "producer", "counts_only", "events")


# ---------------------------------------------------------------------------
# Pure functions — input TSV → counts → manifest
# ---------------------------------------------------------------------------

def read_tsv(paths: list[str]) -> list[dict]:
    """ats_pull TSV (header + rows, tab-separated) → row dicts. Duplicates on `key` are dropped."""
    out, seen = [], set()
    for path in paths:
        fh = sys.stdin if path == "-" else open(path, encoding="utf-8")  # noqa: SIM115 — closed by csv
        try:
            reader = csv.DictReader(fh, delimiter="\t")
            if not reader.fieldnames or "company" not in reader.fieldnames or "key" not in reader.fieldnames:
                raise ValueError(f"not an ats_pull TSV (expected a 'company' and 'key' column): {path}")
            for row in reader:
                key = (row.get("key") or "").strip()
                if not key or key in seen:
                    continue
                seen.add(key)
                out.append(row)
        finally:
            if path != "-":
                fh.close()
    return out


def week_bucket(d: date) -> str:
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def counts(rows: list[dict]) -> dict:
    """One company's rows → the four counts. Titles are consumed here and never leave this function."""
    gtm = sum(1 for r in rows if ats_pull.keep_title(r.get("title") or ""))
    return {"roles_open": len(rows), "gtm_roles": gtm,
            "ai_gtm_roles": sum(1 for r in rows if ats_pull.keep_title(r.get("title") or "")
                                and AI_TERM.search(r.get("title") or ""))}


def scan_pii(obj: object) -> None:
    """ADR-9 scan over EVERY string — used on the input rows AND the manifest. Raises PIIViolation.

    Input-side scanning is deliberate: counts-only already guarantees titles are structurally dropped,
    but a title (or company name) carrying contact detail is an upstream drift this lane must fail loud
    on, not aggregate silently. Uses spine_client's own regexes — never a local copy (regex parity is
    CI-checked upstream)."""
    stack = [obj]
    while stack:
        v = stack.pop()
        if isinstance(v, str):
            for m in EMAIL_RE.finditer(v):
                if not EMAIL_ALLOWLIST_RE.search(m.group(0)):
                    raise PIIViolation(f"ats_pulse: emitted text contains an email address — counts-only "
                                       f"contract breached · fix: fix the upstream TSV, never the output")
            if PHONE_RE.search(v):
                raise PIIViolation("ats_pulse: emitted text contains a phone number — counts-only contract "
                                   "breached · fix: fix the upstream TSV, never the output")
        elif isinstance(v, dict):
            stack.extend(v.values())
        elif isinstance(v, (list, tuple)):
            stack.extend(v)


def build_manifest(rows: list[dict], asof: date,
                   prior: dict | None = None) -> dict:
    """Aggregate rows → the hiring_pulse manifest (one event per company per week)."""
    scan_pii(rows)                    # layer 1: the input itself (see scan_pii docstring)
    by_company: dict[str, list[dict]] = {}
    for r in rows:
        by_company.setdefault((r.get("company") or "").strip(), []).append(r)
    by_company.pop("", None)          # a row without a company name cannot carry an entity edge
    prior_counts = {}
    for ev in (prior or {}).get("events", []):
        pc = (ev.get("metadata") or {}).get("roles_open")
        if isinstance(pc, int):
            prior_counts[ev.get("company")] = pc
    week = week_bucket(asof)
    events = []
    for company in sorted(by_company):
        c = counts(by_company[company])
        delta = c["roles_open"] - prior_counts[company] if company in prior_counts else None
        events.append({
            "company": company,
            "kind": "market",
            "signal_type": SIGNAL_TYPE,
            "event_date": asof.isoformat(),
            "title": f"Hiring pulse — {company} ({week})",   # company + week; counts appear in metadata only
            "url": "",
            "source": SOURCE,
            "metadata": {"roles_open": c["roles_open"], "gtm_roles": c["gtm_roles"],
                         "ai_gtm_roles": c["ai_gtm_roles"], "delta_wow": delta},
            "entities": [{"type": "company", "name": company, "role": "subject"}],
            "dedup_key": f"{SOURCE}:{company}:{week}",       # §3.2 secondary key (no canonical URL here)
        })
    manifest = {"week": week, "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "signal_type": SIGNAL_TYPE, "producer": SOURCE, "counts_only": True, "events": events}
    scan_pii(manifest)
    return manifest


def validate_manifest(manifest: dict) -> list[str]:
    """The ensure-event contract, checked offline (the Action's dry-run write step). Problems, not raises."""
    problems = []
    for k in MANIFEST_KEYS:
        if k not in manifest:
            problems.append(f"manifest missing {k!r}")
    if manifest.get("counts_only") is not True:
        problems.append("counts_only must be true")
    if manifest.get("signal_type") != SIGNAL_TYPE or manifest.get("producer") != SOURCE:
        problems.append("signal_type/producer drifted from the lane contract")
    week = manifest.get("week", "")
    if not re.fullmatch(r"\d{4}-W\d{2}", str(week)):
        problems.append(f"week {week!r} is not an ISO week bucket")
    for i, ev in enumerate(manifest.get("events", [])):
        tag = f"events[{i}]"
        if ev.get("kind") != "market":
            problems.append(f"{tag}.kind must be 'market'")
        if ev.get("signal_type") != SIGNAL_TYPE:
            problems.append(f"{tag}.signal_type must be '{SIGNAL_TYPE}'")
        if not (ev.get("company") or "").strip():
            problems.append(f"{tag}.company empty")
        if ev.get("source") != SOURCE:
            problems.append(f"{tag}.source must be '{SOURCE}'")
        meta = ev.get("metadata") or {}
        if set(meta) != set(META_KEYS):
            problems.append(f"{tag}.metadata keys must be exactly {META_KEYS}")
        for k in META_KEYS:
            if k in meta and meta[k] is not None and not isinstance(meta[k], int):
                problems.append(f"{tag}.metadata.{k} must be an int or null (got {type(meta[k]).__name__})")
        ents = ev.get("entities") or []
        if not any(e.get("type") == "company" and (e.get("name") or "").strip() for e in ents):
            problems.append(f"{tag} has no company entity edge (ensure-event requires ≥1)")
        for e in ents:
            if e.get("type") != "company":
                problems.append(f"{tag}: entity type {e.get('type')!r} — no person rows from market lanes "
                                f"in Phase A (ADR-7 R2)")
    try:
        scan_pii(manifest)
    except PIIViolation as e:
        problems.append(str(e))
    return problems


# ---------------------------------------------------------------------------
# Selftest — inline fixtures, offline, negative-PII cases
# ---------------------------------------------------------------------------

COLS = ["company", "vendor", "key", "title", "url", "location", "posted", "updated", "remote",
        "comp_text", "comp_verdict", "comp_figure", "comp_rule"]


def _tsv(rows: list[dict]) -> str:
    """Fixture rows → ats_pull-shaped TSV text (quoted through a buffer, like the real writer)."""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLS, delimiter="\t", extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def _fixture_rows() -> list[dict]:
    def row(company, key, title, **kw):
        base = {"company": company, "vendor": "ashby", "key": key, "title": title, "url": "",
                "location": "New York, NY", "posted": "2026-11-01", "updated": "", "remote": "false",
                "comp_text": "", "comp_verdict": "", "comp_figure": "", "comp_rule": ""}
        base.update(kw)
        return base
    return [
        row("Anthropic", "ashby:1", "Account Executive, Enterprise"),
        row("Anthropic", "ashby:2", "Customer Success Manager, AI Startups"),
        row("Anthropic", "ashby:3", "Senior LLM Account Director"),
        row("Anthropic", "ashby:4", "Sales Engineer"),                    # GTM keep-list says drop → gtm 3/4
        row("Runway", "ashby:5", "Enterprise Account Director"),
        row("Harvey", "ashby:6", "Account Executive (agentic infrastructure)"),
        row("Harvey", "ashby:6", "Account Executive (duplicate key — must dedupe)"),
        row("", "ashby:7", "Account Executive"),                          # no company → refused
    ]


def selftest() -> int:
    ok, n = 0, 0

    def check(name, cond):
        nonlocal ok, n
        n += 1; ok += bool(cond)
        print(f"  {'✓' if cond else '✗'} {name}")

    tsv_text = _tsv(_fixture_rows())
    with tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False, encoding="utf-8") as fh:
        fh.write(tsv_text)
        tsv_path = fh.name
    rows = read_tsv([tsv_path])            # the real reader — dedupe on `key` lives there
    os.unlink(tsv_path)

    check("tsv: duplicate keys dedupe (8 rows in, 7 distinct keys)", len(rows) == 7)
    check("tsv: companyless rows are read but refused at manifest time",
          any(not (r.get("company") or "").strip() for r in rows))

    m = build_manifest(rows, date(2026, 11, 1))   # a Sunday → 2026-W44
    evs = {e["company"]: e for e in m["events"]}
    check("week: Sunday 2026-11-01 buckets to 2026-W44", m["week"] == "2026-W44")
    check("aggregate: companyless rows never become events", set(evs) == {"Anthropic", "Runway", "Harvey"})
    a = evs["Anthropic"]["metadata"]
    check("counts: roles_open/gtm/ai per fixture (4/3/2)",
          (a["roles_open"], a["gtm_roles"], a["ai_gtm_roles"]) == (4, 3, 2))
    check("counts: gtm_roles uses ats_pull.keep_title, not a local copy", a["gtm_roles"] == 3)
    check("events: kind/signal_type/source/entity contract",
          evs["Runway"]["kind"] == "market" and evs["Runway"]["signal_type"] == "hiring_pulse"
          and evs["Runway"]["source"] == "ats_pulse"
          and evs["Runway"]["entities"] == [{"type": "company", "name": "Runway", "role": "subject"}])
    check("events: title carries company + week, never a role title",
          evs["Runway"]["title"] == "Hiring pulse — Runway (2026-W44)")
    check("dedup_key: (company, kind, week) secondary key present",
          evs["Harvey"]["dedup_key"] == "ats_pulse:Harvey:2026-W44")

    prior = json.loads(json.dumps(m))          # last week == this week → delta 0
    m2 = build_manifest(rows, date(2026, 11, 1), prior)
    p = {e["company"]: e for e in m2["events"]}["Anthropic"]["metadata"]
    check("delta_wow: same counts as prior week → 0", p["delta_wow"] == 0)
    prior["events"][0]["metadata"]["roles_open"] = 1
    m3 = build_manifest(rows, date(2026, 11, 1), prior)
    p3 = {e["company"]: e for e in m3["events"]}["Anthropic"]["metadata"]
    check("delta_wow: 4 open vs 1 last week → +3", p3["delta_wow"] == 3)
    unseen = _json_copy(m)
    unseen["events"] = [e for e in unseen["events"] if e["company"] != "Runway"]   # Runway absent last week
    m5 = build_manifest(rows, date(2026, 11, 1), unseen)
    check("delta_wow: company unseen last week → null (no invented baseline)",
          {e["company"]: e for e in m5["events"]}["Runway"]["metadata"]["delta_wow"] is None)
    m4 = build_manifest(rows, date(2026, 11, 1), None)
    check("delta_wow: no --prior at all → null across the board",
          all(e["metadata"]["delta_wow"] is None for e in m4["events"]))

    blob = json.dumps(m)
    titles = [r["title"] for r in _fixture_rows()]
    check("counts-only: no fixture title text reaches the manifest",
          all(t not in blob for t in titles))
    check("counts-only: distinctive title words absent (structural, not filtered)",
          "duplicate key" not in blob and "Sales Engineer" not in blob and "Startups" not in blob)

    # Negative PII — a poisoned upstream TSV must hard-fail, never leak into the manifest.
    # build_manifest re-scans the input rows (layer 1) and the emitted manifest (layer 2).
    poisoned = _tsv([_fixture_rows()[0] | {"key": "ashby:9",
                                           "title": "Account Executive — contact hr@agency.example"}])
    try:
        build_manifest(_parse_inline(poisoned), date(2026, 11, 1))
        check("negative PII: email in a title hard-fails the build (input scan)", False)
    except PIIViolation:
        check("negative PII: email in a title hard-fails the build (input scan)", True)
    phone_row = _fixture_rows()[0] | {"key": "ashby:10", "comp_text": "call 555-123-4567"}
    try:
        build_manifest(_parse_inline(_tsv([phone_row])), date(2026, 11, 1))
        check("negative PII: phone in comp_text hard-fails the build (input scan)", False)
    except PIIViolation:
        check("negative PII: phone in comp_text hard-fails the build (input scan)", True)
    bad = _json_copy(m)
    bad["events"][0]["title"] = "ping recruiter@example.com"
    check("negative PII: --validate refuses a manifest carrying an email",
          any("email" in p for p in validate_manifest(bad)))

    good = _json_copy(m)
    check("validate: a clean manifest passes with no problems", validate_manifest(good) == [])
    broken = _json_copy(good); broken["events"] = [dict(good["events"][0]) | {"signal_type": "paper"}]
    check("validate: drifted signal_type is refused", len(validate_manifest(broken)) == 1)
    person_edge = _json_copy(good)
    person_edge["events"] = [dict(good["events"][0])
                             | {"entities": [{"type": "person", "name": "A", "role": "speaker"}]}]
    pp = validate_manifest(person_edge)
    check("validate: person edges refused in Phase A (ADR-7 R2)",
          any("person" in p for p in pp) and any("no company entity" in p for p in pp))
    print(f"selftest: {ok}/{n} ats_pulse cases pass")
    return 0 if ok == n else 1


def _parse_inline(text: str) -> list[dict]:
    """Read a fixture TSV from a string (read_tsv minus the path/stdin handling)."""
    return list(csv.DictReader(io.StringIO(text), delimiter="\t"))


def _json_copy(obj: object) -> object:
    """Deep copy via JSON round-trip — test mutations must never share structure with the fixture."""
    return json.loads(json.dumps(obj))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("tsv", nargs="*", help="ats_pull.py TSV file(s); '-' reads stdin")
    ap.add_argument("--prior", help="last week's pulse.json — the delta_wow baseline")
    ap.add_argument("--asof", help="week bucket to emit (YYYY-MM-DD, default: today UTC)")
    ap.add_argument("--out", help="write the manifest here (default: stdout)")
    ap.add_argument("--validate", help="validate a pulse manifest offline and exit (no network, no writes)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)

    if a.selftest:
        return selftest()
    if a.validate:
        try:
            manifest = json.load(open(a.validate, encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"ats_pulse: cannot read --validate {a.validate}: {e}", file=sys.stderr)
            return 3
        problems = validate_manifest(manifest)
        if problems:
            for p in problems:
                print(f"FAIL  {p}", file=sys.stderr)
            return 1
        n = len(manifest.get("events", []))
        print(f"ats_pulse: manifest valid — {n} hiring_pulse events, week {manifest.get('week')} "
              f"(dry-run: live ensure-event lands with migration 0016)", file=sys.stderr)
        return 0
    if not a.tsv:
        print("ats_pulse: no input TSV given (pass ats_pull output files, or '-' for stdin)", file=sys.stderr)
        return 2

    try:
        rows = read_tsv(a.tsv)
    except (OSError, ValueError) as e:
        print(f"ats_pulse: input unreadable: {e}", file=sys.stderr)
        return 3
    if not rows:
        print("ats_pulse: input TSV holds no rows — the lane may be dead (check ats_pull's gap line)",
              file=sys.stderr)
        return 3
    asof = date.fromisoformat(a.asof) if a.asof else datetime.now(timezone.utc).date()
    prior = None
    if a.prior:
        try:
            prior = json.load(open(a.prior, encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"ats_pulse: --prior unreadable ({e}); delta_wow will be null (no baseline)",
                    file=sys.stderr)
    manifest = build_manifest(rows, asof, prior)
    text = json.dumps(manifest, indent=2, sort_keys=False) + "\n"
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text)
    else:
        print(text, end="")
    print(f"ats_pulse: week {manifest['week']} · {len(manifest['events'])} companies · "
          f"counts only (no titles, no people) · "
          f"delta_wow baseline: {'prior week' if prior else 'none yet (first run)'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
