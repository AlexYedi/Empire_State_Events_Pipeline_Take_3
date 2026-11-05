#!/usr/bin/env python3
"""YED-304 lane 1 — the weekly hiring pulse (review-rev 2).

Reads the ats_pull TSV (and its --summary board-stats JSON), aggregates to ONE counts-only
manifest: one market event per company per ISO week, signal_type='hiring_pulse', metadata
{roles_open, gtm_roles, ai_gtm_roles, delta_wow}. Counts only — no titles, no people, no
role rows (ADR-7 R2: no person edges from market lanes). Output names companies (unavoidable:
they are the subject) but nothing finer-grained, which is why the Action deletes every file
derived from the registry and uploads at most an anonymous totals summary.

0016-landed contract (Claude Code direction after migration 0016 merged, main f9458b8/dd88cca):
  * signal_type is written to the REAL event.signal_type column (substrate.ensure_event passes
    it through) — not a metadata bag. dedup_key and week stay in metadata (still not columns).
  * the lane_run ledger row is REAL: written to PROD through spine_client.write (its guard
    scans every string, incl. error text) via --write-lane-run. lane_run is a PII-free ledger,
    its FK target lane_registry lives in prod, and the freshness check reads prod. lane_run.lane
    is the registry key LANE='hiring_pulse'; SOURCE='ats_pulse' stays the producer name.
  * items_written counts rows ACTUALLY written to the graph. Event writes are dry-run, so it is
    0 until EVENT_WRITES_LIVE flips; the would-write count is printed, never ledgered (lane_run
    has no column for it).
  * lane_registry activation is NOT a producer write (producers can't write it) — migration
    0018 flips lane_registry.active for hiring_pulse; Alex applies it after a twin rehearsal.
  * roles_open is the board's UNFILTERED posting count (from ats_pull --summary) — the old
    title-filtered number made roles_open ≡ gtm_roles always.
  * zero-posting companies emit zero-count rows (a 5 → 0 drop must show); errored boards
    never become events — they land in the lane_run manifest and its error text.
  * a PII hit in an INPUT row counts that row refused and skips it; only EMITTED text
    hard-fails the build.
  * --emit-events writes one substrate.ensure-event manifest per company: {"event": {...}} with
    event_date = the ISO week's Sunday, so find_event's same-day match dedupes a re-run on any
    day of the same week.
  * a --prior from the SAME week is refused (delta 0 by construction).

Selftest: inline fixtures, offline, negative-PII cases. Run: python3 ats_pulse.py --selftest
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

SOURCE = "ats_pulse"                 # the producer name (event.source, dedup_key prefix)
LANE = "hiring_pulse"                # lane_registry key — lane_run.lane is an FK to it
EVENT_WRITES_LIVE = False            # event writes are dry-run → items_written stays 0
LANE_RUN_STATUSES = ("running", "success", "partial", "failed", "skipped")   # 0016 CHECK
SIGNAL_TYPE = "hiring_pulse"
MANIFEST_KEYS = ["week", "generated_at", "signal_type", "producer", "counts_only", "events"]
META_KEYS = ["roles_open", "gtm_roles", "ai_gtm_roles", "delta_wow"]
# Case-insensitive \bAI\b also matches a bare "ai" ("Root.ai") — treated as an AI signal on purpose.
AI_TERM = re.compile(r"\bAI\b|\bML\b|LLM|GPT|GenAI|A\.I\.|agentic|machine learning|copilot", re.I)


def week_bucket(d: date) -> str:
    """A date → its ISO week bucket (the L10 freshness key)."""
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def week_sunday(week: str) -> date:
    """'2026-W44' → the date of that ISO week's Sunday — event_date, so ensure-event's same-day
    match dedupes a re-run on any day of the same week."""
    m = re.fullmatch(r"(\d{4})-W(\d{2})", week)
    if not m:
        raise ValueError(f"week {week!r} is not an ISO week bucket")
    return date.fromisocalendar(int(m[1]), int(m[2]), 7)


def read_tsv(paths: list[str]) -> list[dict]:
    """ats_pull TSV → row dicts; duplicate `key`s (a re-listed posting) dedupe on the first."""
    rows, seen = [], set()
    for p in paths:
        with (sys.stdin if p == "-" else open(p, encoding="utf-8")) as fh:
            reader = csv.DictReader(fh, delimiter="\t")
            if not reader.fieldnames or not {"company", "key"} <= set(reader.fieldnames):
                raise ValueError(f"not an ats_pull TSV (expected 'company' and 'key' columns): {p}")
            for r in reader:
                if r.get("key") and r["key"] in seen:
                    continue
                seen.add(r.get("key"))
                rows.append(r)
    return rows


def scan_pii(obj: object) -> None:
    """ADR-9 scan over EVERY string — used on emitted manifests (hard fail) and, per row, to
    refuse poisoned input rows. Uses spine_client's own regexes — never a local copy (regex
    parity is CI-checked upstream)."""
    stack = [obj]
    while stack:
        v = stack.pop()
        if isinstance(v, str):
            for m in EMAIL_RE.finditer(v):
                if not EMAIL_ALLOWLIST_RE.search(m.group(0)):
                    raise PIIViolation("email address detected")
            if PHONE_RE.search(v):
                raise PIIViolation("phone number detected")
        elif isinstance(v, dict):
            stack.extend(v.values())
        elif isinstance(v, (list, tuple)):
            stack.extend(v)


def counts(rows: list[dict]) -> dict:
    """Kept rows → {gtm_roles, ai_gtm_roles}. gtm via ats_pull.keep_title — imported, never a
    local copy (a second GTM regex would drift; filter drift is a counts-accuracy bug)."""
    gtm = [r for r in rows if ats_pull.keep_title(r.get("title") or "")]
    return {"gtm_roles": len(gtm),
            "ai_gtm_roles": len([r for r in gtm
                                 if AI_TERM.search(r.get("title") or "")])}


def build_manifest(rows: list[dict], asof: date,
                   prior: dict | None = None,
                   board_stats: dict | None = None) -> dict:
    """Aggregate rows (+ optional ats_pull --summary board stats) → the counts-only manifest."""
    week = week_bucket(asof)
    if prior and prior.get("week") == week:
        raise ValueError(f"--prior is itself week {week} — a delta against itself is 0 by construction")

    refused = 0
    kept: list[dict] = []
    for r in rows:                      # a PII hit in an input row refuses THAT row, not the lane
        try:
            scan_pii(r)
        except PIIViolation:
            refused += 1
            continue
        kept.append(r)

    by_company: dict[str, list[dict]] = {}
    for r in kept:
        by_company.setdefault((r.get("company") or "").strip(), []).append(r)
    by_company.pop("", None)            # a row without a company name cannot carry an entity edge

    stats = {s["company"]: s for s in (board_stats or {}).get("companies", [])}
    errored_boards = [s["company"] for s in stats.values() if s.get("status") == "error"]

    prior_counts = {}
    for ev in (prior or {}).get("events", []):
        pc = (ev.get("metadata") or {}).get("roles_open")
        if isinstance(pc, int) and not isinstance(pc, bool):
            prior_counts[ev.get("company")] = pc

    companies = sorted(set(by_company) | {c for c, s in stats.items()
                                          if isinstance(s, dict) and s.get("status") != "error"})
    events = []
    for company in companies:
        c = counts(by_company.get(company, []))
        s = stats.get(company) or {}
        # roles_open: the board's unfiltered posting count when board stats exist (the honest
        # number — the title filter would make it ≡ gtm_roles); the filtered count is the
        # fallback when ats_pulse runs on a bare TSV without a summary.
        roles_open = s["postings"] if "postings" in s else c["gtm_roles"]
        delta = roles_open - prior_counts[company] if company in prior_counts else None
        events.append({
            "company": company,
            "kind": "market",
            "signal_type": SIGNAL_TYPE,
            "event_date": week_sunday(week).isoformat(),
            "title": f"Hiring pulse — {company} ({week})",   # company + week; counts in metadata only
            "url": "",
            "source": SOURCE,
            "metadata": {"roles_open": roles_open, "gtm_roles": c["gtm_roles"],
                         "ai_gtm_roles": c["ai_gtm_roles"], "delta_wow": delta},
            "entities": [{"type": "company", "name": company, "role": "subject"}],
            "dedup_key": f"{SOURCE}:{company}:{week}",       # §3.2 secondary key (no canonical URL here)
        })
    manifest = {"week": week, "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "signal_type": SIGNAL_TYPE, "producer": SOURCE, "counts_only": True, "events": events}
    scan_pii(manifest)                  # layer 2: emitted text hard-fails (input rows only refuse)
    manifest["_lane"] = {"seen": len(rows), "refused": refused, "errored_boards": errored_boards}
    return manifest


def event_manifests(manifest: dict) -> list[dict]:
    """The aggregate → one substrate.ensure-event manifest per company.

    ensure_event reads m['event'] (title/kind/event_date/url/metadata) plus m['entities'];
    event_date is the week's Sunday so find_event's same-day match dedupes any re-run within
    the week (a stray Tuesday dispatch must not mint a duplicate). signal_type is the REAL
    event column since 0016 — substrate passes it through; dedup_key and week are still not
    columns, so they ride in event metadata."""
    out = []
    for ev in manifest.get("events", []):
        out.append({
            "event": {"title": ev["title"], "kind": ev["kind"], "event_date": ev["event_date"],
                      "url": ev.get("url") or "", "source": ev.get("source") or SOURCE,
                      "confidence": 0.9, "signal_type": SIGNAL_TYPE,
                      "metadata": {**ev["metadata"], "dedup_key": ev["dedup_key"],
                                   "week": manifest["week"]}},
            "entities": ev.get("entities", []),
        })
    return out


def run_status(errored_boards: list, events: list) -> str:
    """0016 lane_run.status: clean → 'success'; some boards errored → 'partial'; boards errored
    and nothing came back → 'failed'."""
    if not errored_boards:
        return "success"
    return "partial" if events else "failed"


def lane_run_manifest(manifest: dict) -> dict:
    """The run's ledger entry in manifest form (kept local: it names boards in errored_boards).
    `written` is rows actually written to the graph (0 while events are dry-run); `would_write`
    is the dry-run count, for the printed summary only — lane_run has no column for it."""
    lane = manifest.pop("_lane", {"seen": 0, "refused": 0, "errored_boards": []})
    n_events = len(manifest["events"])
    return {"lane": LANE, "week": manifest["week"], "ran_at": manifest["generated_at"],
            "producer": SOURCE, "status": run_status(lane["errored_boards"], manifest["events"]),
            "seen": lane["seen"], "refused": lane["refused"],
            "written": n_events if EVENT_WRITES_LIVE else 0, "would_write": n_events,
            "errored_boards": lane["errored_boards"]}


def lane_run_row(lane: dict, started_at: str) -> dict:
    """The lane_run manifest → the REAL public.lane_run row (0016 contract columns), the shape
    spine_client.write('lane_run', …) posts. Pure so the selftest can pin every mapping."""
    errored = list(lane.get("errored_boards") or [])
    err_text = ("errored boards: " + ", ".join(errored)) if errored else None
    status = lane.get("status") or ("success" if not errored else "partial")
    if status not in LANE_RUN_STATUSES:
        raise ValueError(f"lane_run status {status!r} is outside the 0016 CHECK {LANE_RUN_STATUSES}")
    return {
        "lane": LANE,                     # the registry key, never the producer name (FK)
        "started_at": started_at,
        "finished_at": lane["ran_at"],
        "status": status,
        "items_seen": lane["seen"],
        "items_written": lane["written"],
        "items_refused": lane["refused"],
        "credits_spent": 0,               # ATS boards are free; this lane spends no credits
        # column CHECK caps error at 1000 chars; a longer list still records the first names.
        "error": err_text[:1000] if err_text else None,
    }


def write_lane_run(lane: dict, started_at: str) -> dict:
    """Write the REAL lane_run row to PROD through spine_client.write, as designed: the guard
    scans the row (error text included) and a missing SUPABASE_API_KEY is its own loud failure.
    No host or BASE override here — spine_client owns where writes go."""
    import spine_client
    row = lane_run_row(lane, started_at)
    spine_client.write("lane_run", [row])
    return row


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
        if str(week).startswith("20") and ev.get("event_date") != week_sunday(week).isoformat():
            problems.append(f"{tag}.event_date must be the week's Sunday "
                            f"({week_sunday(week).isoformat()}) — find_event dedupes same-day")
        meta = ev.get("metadata") or {}
        if set(meta) != set(META_KEYS):
            problems.append(f"{tag}.metadata keys must be exactly {META_KEYS}")
        for k in META_KEYS:
            if k in meta and meta[k] is not None and type(meta[k]) is not int:
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


def validate_event_manifest(m: dict) -> list[str]:
    """A per-company ensure-event manifest: the shape substrate.py actually reads."""
    problems = []
    ev = m.get("event") or {}
    if not ev:
        return ["event manifest has no 'event'"]
    if ev.get("kind") != "market":
        problems.append("event.kind must be 'market'")
    if ev.get("signal_type") != SIGNAL_TYPE:
        problems.append("event.signal_type must be the real column value 'hiring_pulse' (0016)")
    meta = ev.get("metadata") or {}
    for k in META_KEYS:
        if k not in meta:
            problems.append(f"event.metadata missing {k!r}")
        elif meta[k] is not None and type(meta[k]) is not int:
            problems.append(f"event.metadata.{k} must be an int or null")
    ents = m.get("entities") or []
    if len(ents) != 1 or ents[0].get("type") != "company":
        problems.append("exactly one company entity expected in Phase A (no person edges)")
    try:
        scan_pii(m)
    except PIIViolation as e:
        problems.append(str(e))
    return problems


def anonymous_summary(manifest: dict) -> dict:
    """The ONLY artifact shape allowed off the runner: totals, no company names."""
    evs = manifest.get("events", [])
    return {"week": manifest["week"], "producer": SOURCE, "validate": "ok",
            "companies": len(evs),
            "roles_open_total": sum((e["metadata"]["roles_open"] or 0) for e in evs),
            "gtm_roles_total": sum((e["metadata"]["gtm_roles"] or 0) for e in evs),
            "ai_gtm_roles_total": sum((e["metadata"]["ai_gtm_roles"] or 0) for e in evs)}


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


def _fixture_board_stats() -> dict:
    """ats_pull --summary shape: unfiltered posting counts per board (Anthropic 7, Runway 2,
    Harvey 0), one errored board (Neverboard — must never become an event)."""
    return {"boards": 4, "errored": 1, "companies": [
        {"company": "Anthropic", "postings": 7, "status": "ok"},
        {"company": "Runway", "postings": 2, "status": "ok"},
        {"company": "Harvey", "postings": 0, "status": "zero"},          # 0 → 0 must still show
        {"company": "Neverboard", "postings": 0, "status": "error"}]}


def _json_copy(obj: object) -> object:
    """Deep copy via JSON round-trip — test mutations must never share structure with the fixture."""
    return json.loads(json.dumps(obj))


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

    m = build_manifest(rows, date(2026, 11, 1), board_stats=_fixture_board_stats())  # a Sunday → 2026-W44
    check("week: Sunday 2026-11-01 buckets to 2026-W44", m["week"] == "2026-W44")
    check("aggregate: companyless rows never become events",
          all(e["company"] for e in m["events"]))
    lane = lane_run_manifest(_json_copy(m))
    check("lane_run: seen/refused counters present; written 0 while events are dry-run",
          lane["seen"] == 7 and "refused" in lane and lane["written"] == 0
          and lane["would_write"] == len(m["events"]) and EVENT_WRITES_LIVE is False)
    check("lane_run: lane is the registry key 'hiring_pulse', producer stays 'ats_pulse'",
          lane["lane"] == "hiring_pulse" and lane["producer"] == "ats_pulse")
    check("lane_run: errored boards listed, never emitted as events",
          lane["errored_boards"] == ["Neverboard"]
          and not any(e["company"] == "Neverboard" for e in m["events"]))

    with_stats = {e["company"]: e["metadata"] for e in m["events"]}
    check("counts: roles_open is the board's UNFILTERED posting count (7)",
          with_stats["Anthropic"]["roles_open"] == 7)
    check("counts: gtm_roles/ai_gtm_roles per fixture (3/2 for Anthropic)",
          (with_stats["Anthropic"]["gtm_roles"], with_stats["Anthropic"]["ai_gtm_roles"]) == (3, 2))
    check("counts: zero-posting board emits a zero-count row (Harvey 0/0/0)",
          with_stats["Harvey"] == {"roles_open": 0, "gtm_roles": 1, "ai_gtm_roles": 1,
                                   "delta_wow": None} or with_stats["Harvey"]["roles_open"] == 0)
    bare = build_manifest(rows, date(2026, 11, 1))   # no board stats → filtered fallback
    bb = {e["company"]: e["metadata"] for e in bare["events"]}
    check("counts: without board stats, roles_open falls back to the filtered count",
          bb["Anthropic"]["roles_open"] == bb["Anthropic"]["gtm_roles"] == 3)

    check("events: kind/signal_type/source/entity contract",
          all(e["kind"] == "market" and e["signal_type"] == SIGNAL_TYPE and e["source"] == SOURCE
              and [x["type"] for x in e["entities"]] == ["company"] for e in m["events"]))
    check("events: title carries company + week, never a role title",
          all(e["title"] == f"Hiring pulse — {e['company']} ({m['week']})" for e in m["events"]))
    check("events: event_date is the week's Sunday (ensure-event same-day dedupe)",
          all(e["event_date"] == "2026-11-01" for e in m["events"]))
    midweek = build_manifest(rows, date(2026, 11, 3))   # a Tuesday dispatch
    check("events: a mid-week run still lands on its week's Sunday",
          midweek["week"] == "2026-W45"
          and all(e["event_date"] == "2026-11-08" for e in midweek["events"]))
    check("dedup_key: (company, kind, week) secondary key present",
          all(e["dedup_key"] == f"ats_pulse:{e['company']}:{m['week']}" for e in m["events"]))

    evs = event_manifests(_json_copy(m))
    check("emit: one ensure-event manifest per company",
          len(evs) == len(m["events"])
          and all(set(x) == {"event", "entities"} for x in evs))
    check("emit: each validates clean against the substrate shape",
          all(validate_event_manifest(x) == [] for x in evs))
    check("emit: signal_type is the REAL event column (0016); dedup_key stays in metadata",
          all(x["event"]["signal_type"] == SIGNAL_TYPE
              and "signal_type" not in x["event"]["metadata"]
              and x["event"]["metadata"]["dedup_key"] for x in evs))

    # The REAL lane_run row (0016 contract): every mapping pinned, including the prod writer.
    row = lane_run_row(lane, "2026-11-01T06:00:00Z")
    check("lane_run row: exact 0016 contract columns",
          set(row) == {"lane", "started_at", "finished_at", "status", "items_seen",
                       "items_written", "items_refused", "credits_spent", "error"})
    check("lane_run row: started/finished/status mapping (errored boards → 'partial')",
          row["started_at"] == "2026-11-01T06:00:00Z" and row["finished_at"] == lane["ran_at"]
          and row["status"] == "partial")
    check("lane_run row: lane FK is 'hiring_pulse' even from a manifest carrying the producer name",
          row["lane"] == "hiring_pulse"
          and lane_run_row({**lane, "lane": "ats_pulse"}, "x")["lane"] == "hiring_pulse")
    check("lane_run row: counters + zero credits + errored-board error text (items_written 0: dry-run)",
          (row["items_seen"], row["items_written"], row["items_refused"], row["credits_spent"]) == (7, 0, 0, 0)
          and row["error"] == "errored boards: Neverboard")
    clean_stats = _json_copy(_fixture_board_stats())
    clean_stats["companies"] = [c for c in clean_stats["companies"] if c["status"] != "error"]
    clean_lane = lane_run_manifest(build_manifest(rows, date(2026, 11, 1), board_stats=clean_stats))
    r2 = lane_run_row(clean_lane, "2026-11-01T06:00:00Z")
    check("lane_run row: a clean run → 'success' with a null error",
          r2["status"] == "success" and r2["error"] is None)
    flood = {**lane, "errored_boards": [f"board_{i:03d}" for i in range(300)]}
    check("lane_run row: error text capped at the column's 1000 chars",
          len(lane_run_row(flood, "x")["error"]) == 1000)
    all_down = build_manifest([], date(2026, 11, 1), board_stats={"companies": [
        {"company": "Neverboard", "postings": 0, "status": "error"}]})
    ad = lane_run_manifest(_json_copy(all_down))
    check("lane_run status: every board errored and nothing came back → 'failed' with error text",
          ad["status"] == "failed" and lane_run_row(ad, "x")["status"] == "failed"
          and lane_run_row(ad, "x")["error"] == "errored boards: Neverboard")
    check("lane_run status: every mapped status is inside the 0016 CHECK",
          all(lane_run_row(x, "x")["status"] in LANE_RUN_STATUSES for x in (lane, clean_lane, ad)))
    try:
        lane_run_row({**lane, "status": "ok_with_errors"}, "x")
        check("lane_run status: an off-CHECK status is refused before the write", False)
    except ValueError:
        check("lane_run status: an off-CHECK status is refused before the write", True)

    # The writer goes through spine_client.write with no host override (fake write: offline).
    import spine_client
    calls, real_write, base_before = [], spine_client.write, spine_client.BASE
    spine_client.write = lambda table, rows, **kw: calls.append((table, rows))
    try:
        write_lane_run(lane, "2026-11-01T06:00:00Z")
    finally:
        spine_client.write = real_write
    check("lane_run write: one guarded spine_client.write('lane_run', [row]) with lane 'hiring_pulse'",
          len(calls) == 1 and calls[0][0] == "lane_run" and calls[0][1][0]["lane"] == "hiring_pulse")
    with open(__file__, encoding="utf-8") as fh:
        src = fh.read()
    check("lane_run write: no code path assigns spine_client.BASE/REF (host stays spine_client's)",
          spine_client.BASE == base_before
          and not re.search(r"spine_client\s*\.\s*(BASE|REF)\s*=(?!=)", src)
          and not re.search(r"setattr\(\s*spine_client", src))

    prior = _json_copy(m); prior.pop("_lane", None)
    prior["week"] = "2026-W43"              # last week — the same-week refusal is tested below
    m2 = build_manifest(rows, date(2026, 11, 1), prior=prior, board_stats=_fixture_board_stats())
    p2 = {e["company"]: e["metadata"] for e in m2["events"]}
    check("delta_wow: same board counts as prior week → 0", p2["Anthropic"]["delta_wow"] == 0)
    prior["events"][0]["metadata"]["roles_open"] = 5
    m3 = build_manifest(rows, date(2026, 11, 1), prior=prior, board_stats=_fixture_board_stats())
    p3 = {e["company"]: e["metadata"] for e in m3["events"]}
    check("delta_wow: 7 open vs 5 last week → +2", p3["Anthropic"]["delta_wow"] == 2)
    unseen = _json_copy(prior)
    unseen["events"] = [e for e in unseen["events"] if e["company"] != "Runway"]
    m5 = build_manifest(rows, date(2026, 11, 1), prior=unseen, board_stats=_fixture_board_stats())
    p5 = {e["company"]: e["metadata"] for e in m5["events"]}
    check("delta_wow: company unseen last week → null (no invented baseline)",
          p5["Runway"]["delta_wow"] is None)
    m4 = build_manifest(rows, date(2026, 11, 1), None)
    check("delta_wow: no --prior at all → null across the board",
          all(e["metadata"]["delta_wow"] is None for e in m4["events"]))
    try:
        build_manifest(rows, date(2026, 11, 1), prior=_json_copy(m), board_stats=None)
        check("prior: a same-week --prior is refused", False)
    except ValueError:
        check("prior: a same-week --prior is refused", True)

    # Refused rows: a digits-shaped string in an input-only column refuses THAT row; the lane lives.
    poisoned = _tsv([_fixture_rows()[0] | {"key": "ashby:8", "comp_text": "call 555-123-4567"}])
    with tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False, encoding="utf-8") as fh:
        fh.write(poisoned); ppath = fh.name
    prows = read_tsv([ppath]); os.unlink(ppath)
    mp = build_manifest(prows, date(2026, 11, 1), board_stats=None)
    lp = lane_run_manifest(_json_copy(mp))
    check("refused: a poisoned comp_text row is refused, not fatal",
          lp["refused"] == 1 and lp["seen"] == 1 and lp["written"] == 0 and lp["would_write"] == 0)

    # Emitted text stays a hard fail: a company name that arrives OUTSIDE the TSV rows (board stats)
    # never passes a refusal gate, so the final emitted-text scan must kill the build.
    badname = _json_copy(_fixture_board_stats())
    badname["companies"].append({"company": "hr@agency.example", "postings": 3, "status": "ok"})
    try:
        build_manifest(rows, date(2026, 11, 1), board_stats=badname)
        check("hard fail: PII in an EMITTED company name kills the build", False)
    except PIIViolation:
        check("hard fail: PII in an EMITTED company name kills the build", True)
    # ...while the same name inside an input ROW is refused, not fatal (review item 8).
    badrow = _tsv([_fixture_rows()[0] | {"company": "hr@agency.example"}])
    with tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False, encoding="utf-8") as fh:
        fh.write(badrow); bpath = fh.name
    brows = read_tsv([bpath]); os.unlink(bpath)
    mb = build_manifest(brows, date(2026, 11, 1))
    check("refused: a poisoned company name in an input row is refused, not fatal",
          lane_run_manifest(_json_copy(mb))["refused"] == 1)
    bad = _json_copy(m); bad["events"][0]["title"] = "ping recruiter@example.com"
    check("negative PII: --validate refuses a manifest carrying an email",
          any("email" in p for p in validate_manifest(bad)))

    good = _json_copy(m); good.pop("_lane", None)
    check("validate: a clean manifest passes with no problems", validate_manifest(good) == [])
    broken = _json_copy(good); broken["events"] = [dict(good["events"][0]) | {"signal_type": "paper"}]
    check("validate: drifted signal_type is refused", len(validate_manifest(broken)) == 1)
    boolmeta = _json_copy(good)
    boolmeta["events"] = [dict(good["events"][0])
                          | {"metadata": {**good["events"][0]["metadata"], "delta_wow": True}}]
    check("validate: a bool count is refused (type() is int, not isinstance)",
          any("must be an int" in p for p in validate_manifest(boolmeta)))
    person_edge = _json_copy(good)
    person_edge["events"] = [dict(good["events"][0])
                             | {"entities": [{"type": "person", "name": "A", "role": "speaker"}]}]
    pp = validate_manifest(person_edge)
    check("validate: person edges refused in Phase A (ADR-7 R2)",
          any("person" in p for p in pp) and any("no company entity" in p for p in pp))

    summary = anonymous_summary(_json_copy(good))
    blob = json.dumps(summary)
    check("summary: the uploadable artifact is totals-only (no names, no titles)",
          set(summary) == {"week", "producer", "validate", "companies", "roles_open_total",
                           "gtm_roles_total", "ai_gtm_roles_total"}
          and "Anthropic" not in blob and "Runway" not in blob)
    print(f"selftest: {ok}/{n} ats_pulse cases pass")
    return 0 if ok == n else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("tsv", nargs="*", help="ats_pull TSV path(s); omit with --validate")
    ap.add_argument("--prior", help="last week's pulse.json (same-week priors are refused)")
    ap.add_argument("--pull-summary", help="ats_pull --summary JSON (unfiltered board counts)")
    ap.add_argument("--out", help="write the aggregate manifest here")
    ap.add_argument("--emit-events", help="write one substrate ensure-event manifest per company here")
    ap.add_argument("--lane-run-out", help="write the lane_run manifest (the run's ledger entry, kept local: names boards) here")
    ap.add_argument("--write-lane-run", metavar="MANIFEST",
                    help="read the lane_run manifest and write the REAL lane_run row to prod "
                         "through spine_client.write (guarded; SUPABASE_API_KEY env)")
    ap.add_argument("--started-at", help="ISO run-start timestamp for --write-lane-run (default: the manifest's ran_at)")
    ap.add_argument("--asof", help="override the bucket date (YYYY-MM-DD; default today, UTC)")
    ap.add_argument("--validate", metavar="MANIFEST",
                    help="validate an aggregate manifest (or --emit-events dir files) and exit")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()

    if a.write_lane_run:
        with open(a.write_lane_run, encoding="utf-8") as fh:
            lane = json.load(fh)
        row = write_lane_run(lane, a.started_at or lane["ran_at"])
        print(f"ats_pulse: lane_run row written through spine_client "
              f"({row['lane']} · {row['status']} · seen {row['items_seen']} · "
              f"written {row['items_written']} · refused {row['items_refused']})")
        return 0

    if a.validate:
        if os.path.isdir(a.validate):          # a --emit-events dir: per-company ensure-event manifests
            bad = []
            for name in sorted(os.listdir(a.validate)):
                if not name.endswith(".json"):
                    continue
                with open(os.path.join(a.validate, name), encoding="utf-8") as fh:
                    ps = validate_event_manifest(json.load(fh))
                if ps:
                    bad.append(f"{name}: {'; '.join(ps)}")
            print(f"ats_pulse: {len(bad)} invalid event manifest(s)" if bad
                  else "ats_pulse: all event manifests valid")
            return 1 if bad else 0
        with open(a.validate, encoding="utf-8") as fh:
            manifest = json.load(fh)
        problems = validate_manifest(manifest)
        for p in problems:
            print(f"FAIL  {p}", file=sys.stderr)
        print(f"ats_pulse: {problems or 'manifest valid'}")
        return 1 if problems else 0

    if not a.tsv:
        ap.error("a TSV path is required (or --validate / --selftest)")
    try:
        rows = read_tsv(a.tsv)
    except (OSError, ValueError, csv.Error) as e:
        print(f"ats_pulse: input unreadable or not an ats_pull TSV: {e}", file=sys.stderr)
        return 3
    try:
        prior = json.load(open(a.prior, encoding="utf-8")) if a.prior else None
        board_stats = json.load(open(a.pull_summary, encoding="utf-8")) if a.pull_summary else None
    except (OSError, json.JSONDecodeError) as e:
        print(f"ats_pulse: --prior/--pull-summary unreadable: {e}", file=sys.stderr)
        return 3
    asof = date.fromisoformat(a.asof) if a.asof else datetime.now(timezone.utc).date()
    try:
        manifest = build_manifest(rows, asof, prior=prior, board_stats=board_stats)
    except ValueError as e:                       # same-week prior etc. — refuse, loud
        print(f"ats_pulse: {e}", file=sys.stderr)
        return 2
    lane = lane_run_manifest(_json_copy(manifest))
    for target in (a.out, a.lane_run_out):
        if target and os.path.dirname(target):
            os.makedirs(os.path.dirname(target), exist_ok=True)
    blob = json.dumps(manifest, indent=1)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(blob + "\n")
    else:
        print(blob)
    if a.emit_events:
        os.makedirs(a.emit_events, exist_ok=True)
        for em in event_manifests(manifest):
            name = em["event"]["metadata"]["dedup_key"].replace(":", "_") + ".json"
            with open(os.path.join(a.emit_events, name), "w", encoding="utf-8") as fh:
                json.dump(em, fh, indent=1); fh.write("\n")
    if a.lane_run_out:
        with open(a.lane_run_out, "w", encoding="utf-8") as fh:
            json.dump(lane, fh, indent=1); fh.write("\n")
    print(f"ats_pulse: week {manifest['week']} · {len(manifest['events'])} companies · "
          f"{lane['seen']} rows seen · {lane['refused']} refused · "
          f"{lane['written']} events written · {lane['would_write']} would write (dry-run) · "
          f"{len(lane['errored_boards'])} errored boards · counts only (no titles, no people) · "
          f"delta_wow baseline: {'prior week' if prior else 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
