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
  * the lane_run ledger row is REAL: written through spine_client.write to PROD — the one
    deliberate exception (Alex's decision, post-merge review of #271): lane_run is a PII-free
    ledger, lane_registry and its FK live in prod, and the YED-304 freshness healthcheck reads
    prod. spine_client is prod-only by design (its host is built from the hardcoded REF, so no
    caller override can divert the request — the earlier MI_TWIN_URL override was dead config).
    Every OTHER write in this lane stays twin-only/dry-run (event manifests stay validate-only
    until the guarded REF override lands). items_written counts rows ACTUALLY written — 0 while
    event writes are dry-run.
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
import subprocess
import sys
import tempfile
import textwrap
from datetime import date, datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
import ats_pull  # noqa: E402  (parse/projection only — the pulse never fetches boards itself)
from spine_client import EMAIL_ALLOWLIST_RE, EMAIL_RE, PHONE_RE, PIIViolation  # noqa: E402

SOURCE = "ats_pulse"
SIGNAL_TYPE = "hiring_pulse"
# the lane's registry key (public.lane_registry.lane, seeded by 0016) — NOT the producer name
# (SOURCE = 'ats_pulse' is the event source / producer tag; the FK wants the registry key).
LANE = "hiring_pulse"
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


def lane_run_manifest(manifest: dict, events_written: int = 0) -> dict:
    """The run's ledger entry in manifest form (kept local: it names boards in errored_boards).

    `written` counts rows ACTUALLY written to the graph — not events built. Event writes are
    dry-run (validate-only) until the guarded spine REF override lands, so the default is 0;
    the live-write era passes the real count (a lower bound is never an overclaim)."""
    lane = manifest.pop("_lane", {"seen": 0, "refused": 0, "errored_boards": []})
    return {"lane": LANE, "week": manifest["week"], "ran_at": manifest["generated_at"],
            "producer": SOURCE, "status": "ok" if not lane["errored_boards"] else "ok_with_errors",
            "seen": lane["seen"], "refused": lane["refused"],
            "written": events_written, "errored_boards": lane["errored_boards"]}


def lane_run_row(lane: dict, started_at: str) -> dict:
    """The lane_run manifest → the REAL public.lane_run row (0016 contract columns), the shape
    spine_client.write('lane_run', …) posts. Pure so the selftest can pin every mapping."""
    errored = list(lane.get("errored_boards") or [])
    err_text = ("errored boards: " + ", ".join(errored)) if errored else None
    return {
        "lane": lane["lane"],
        "started_at": started_at,
        "finished_at": lane["ran_at"],
        # lane_run.status CHECK is ('running','success','partial','failed','skipped') — errored
        # boards are a 'partial' run, not a failure (the run itself succeeded).
        "status": "success" if not errored else "partial",
        "items_seen": lane["seen"],
        "items_written": lane["written"],
        "items_refused": lane["refused"],
        "credits_spent": 0,               # ATS boards are free; this lane spends no credits
        # column CHECK caps error at 1000 chars; a longer list still records the first names.
        "error": err_text[:1000] if err_text else None,
    }


def write_lane_run(lane: dict, started_at: str) -> dict:
    """Write the REAL lane_run row through spine_client.write — to PROD, deliberately.

    The ONE prod exception (Alex's decision, post-merge review of #271): lane_run is a PII-free
    ledger (counts and board-status only — the guard still fronts every write), lane_registry
    and its FK live in prod, and the YED-304 freshness healthcheck reads prod. spine_client is
    prod-only by design: _send builds its host from the hardcoded REF, so no caller override
    can divert the request (the earlier MI_TWIN_URL override was dead config — removed). The
    twin-only rule still governs every other write in this lane. The key reaches spine_client
    as SUPABASE_API_KEY (its one key source)."""
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


# --- Workflow shell lint -------------------------------------------------------------------
# Both production incidents (runs 41943575924 and 41945700887) were hand-edits to the YAML's
# shell that no check caught before merge. These lints run in the selftest on every
# 'run: |' block in ats-pulse.yml. bash -n ALONE is not enough: bash treats a heredoc closed
# by end-of-file as a WARNING (exit 0) — exactly the hole run 41945700887 fell through.

_HEREDOC_OPEN = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def shell_script_problems(script: str) -> list[str]:
    """Lint one shell script: heredoc open/close pairing + bash -n (stderr included)."""
    problems: list[str] = []
    stack: list[str] = []
    for line in script.splitlines():
        stripped = line.strip()
        if stack and stripped == stack[-1]:
            stack.pop()
            continue
        m = _HEREDOC_OPEN.search(line)
        if m:
            stack.append(m.group(2))
    for delim in stack:
        problems.append(f"heredoc <<'{delim}' never terminated (delimited by end-of-file)")
    try:
        r = subprocess.run(["bash", "-n"], input=script, capture_output=True,
                           text=True, timeout=15)
    except OSError as e:  # bash missing — never swallow it, surface as a lint problem
        return problems + [f"bash -n could not run: {e}"]
    if r.returncode != 0:
        detail = r.stderr.strip().splitlines()[-1] if r.stderr.strip() else f"exit {r.returncode}"
        problems.append(f"bash -n syntax error: {detail}")
    if "here-document" in r.stderr:
        problems.append("bash -n heredoc warning: " + r.stderr.strip().splitlines()[-1])
    return problems


def workflow_run_blocks(path: str) -> list[tuple[str, str]]:
    """Extract (step name, script) for every 'run: |' block — textually, no yaml dependency."""
    blocks: list[tuple[str, str]] = []
    lines = open(path, encoding="utf-8").read().splitlines()
    run_re = re.compile(r"^(\s*)(?:- )?run: (\||>)")
    name_re = re.compile(r"^\s*(?:- )?name:\s*(.*)$")
    current_name = ""
    i = 0
    while i < len(lines):
        m = run_re.match(lines[i])
        if not m:
            nm = name_re.match(lines[i])
            if nm:
                current_name = nm.group(1).strip().strip("'\"")
            i += 1
            continue
        indent = len(m.group(1))
        body: list[str] = []
        j = i + 1
        while j < len(lines):
            line = lines[j]
            if not line.strip():
                body.append("")
                j += 1
                continue
            if len(line) - len(line.lstrip(" ")) > indent:
                body.append(line)
                j += 1
            else:
                break
        blocks.append((current_name, textwrap.dedent("\n".join(body))))
        i = j
    return blocks


def lint_workflow_shell(path: str) -> list[str]:
    """Every shell problem in a workflow file, labeled by step name."""
    problems: list[str] = []
    for name, script in workflow_run_blocks(path):
        for p in shell_script_problems(script):
            problems.append(f"{name}: {p}")
    return problems


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
    check("lane_run: seen/refused counters present; written counts rows ACTUALLY written (0 in dry-run)",
          lane["seen"] == 7 and "refused" in lane and lane["written"] == 0)
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

    # The REAL lane_run row (0016 contract): every mapping pinned, including the prod-by-decision writer.
    check("lane_run manifest: the FK key is 'hiring_pulse' (the registry key, not the producer name)",
          lane["lane"] == "hiring_pulse" and lane["producer"] == "ats_pulse")
    check("lane_run manifest: dry-run era — written counts rows ACTUALLY written (0), not events built",
          lane["written"] == 0 and len(m["events"]) == 3)
    live = lane_run_manifest(_json_copy(m), events_written=3)
    check("lane_run manifest: the live-write era passes the real count (no under- or overclaim)",
          live["written"] == 3)
    row = lane_run_row(lane, "2026-11-01T06:00:00Z")
    check("lane_run row: exact 0016 contract columns",
          set(row) == {"lane", "started_at", "finished_at", "status", "items_seen",
                       "items_written", "items_refused", "credits_spent", "error"})
    check("lane_run row: started/finished/status mapping (errored boards → 'partial')",
          row["started_at"] == "2026-11-01T06:00:00Z" and row["finished_at"] == lane["ran_at"]
          and row["status"] == "partial")
    check("lane_run row: counters + zero credits + errored-board error text",
          (row["items_seen"], row["items_written"], row["items_refused"], row["credits_spent"]) == (7, 0, 0, 0)
          and row["error"] == "errored boards: Neverboard")
    clean_lane = {**lane, "errored_boards": []}
    r2 = lane_run_row(clean_lane, "2026-11-01T06:00:00Z")
    check("lane_run row: a clean run → 'success' with a null error",
          r2["status"] == "success" and r2["error"] is None)
    flood = {**lane, "errored_boards": [f"board_{i:03d}" for i in range(300)]}
    check("lane_run row: error text capped at the column's 1000 chars",
          len(lane_run_row(flood, "x")["error"]) == 1000)
    # The writer is PROD by decision: stub the connection layer and assert the host the request
    # ACTUALLY reaches. spine_client._send builds its host from the hardcoded REF — a decoy
    # MI_TWIN_URL must have NO effect on any write path (the removed override stays removed).
    class _FakeResp:
        status = 201
        def read(self):
            return b"[]"
    class _FakeConn:
        def __init__(self, host, *a, **k):
            captured.append(host)
            # _send touches conn.sock.settimeout() right after connect()
            self.sock = type("_FakeSock", (), {"settimeout": staticmethod(lambda t: None)})()
        def connect(self): pass
        def settimeout(self, t): pass
        def request(self, *a, **k): pass
        def getresponse(self): return _FakeResp()
        def close(self): pass
    import spine_client as _sc
    captured = []
    orig_conn, orig_key = _sc.http.client.HTTPSConnection, os.environ.get("SUPABASE_API_KEY")
    os.environ["SUPABASE_API_KEY"] = "selftest-key"
    os.environ["MI_TWIN_URL"] = "https://decoy-not-prod.supabase.co"   # a decoy override must not matter
    _sc.http.client.HTTPSConnection = _FakeConn
    try:
        write_lane_run(lane, "x")
        check("lane_run write: the request reaches the PROD host (REF-built; no caller override)",
              captured == [f"{_sc.REF}.supabase.co"]
              and f"{_sc.REF}.supabase.co" != "decoy-not-prod.supabase.co")
        # a DIFFERENT write path (any producer calling spine_client.write directly) with the decoy
        # still set must land on the same prod host — the env var is dead on every path.
        _sc.write("lane_run", [lane_run_row(lane, "x")])
        check("lane_run write: MI_TWIN_URL has no effect on ANY write path — all reach prod",
              captured == [f"{_sc.REF}.supabase.co"] * 2)
    finally:
        _sc.http.client.HTTPSConnection = orig_conn
        if orig_key is None:
            os.environ.pop("SUPABASE_API_KEY", None)
        else:
            os.environ["SUPABASE_API_KEY"] = orig_key
        os.environ.pop("MI_TWIN_URL", None)
        _sc._KEY = None

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
          lp["refused"] == 1 and lp["seen"] == 1 and lp["written"] == 0)

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

    # --- First-run / no-prior-file path (run 41943575924 dress rehearsal) ------------------
    # The workflow's guard must test FILE REALITY, and the CLI must keep refusing an
    # explicitly-passed --prior that doesn't exist (exit 3). These cases pin both halves.
    with tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False, encoding="utf-8") as fh:
        fh.write(_tsv(_fixture_rows())); fpath = fh.name
    try:
        outdir = tempfile.mkdtemp()
        rc = main([fpath, "--prior", "/tmp/definitely-missing-prior.json",
                   "--out", f"{outdir}/pulse.json"])
        check("prior: a MISSING --prior file is refused with exit 3 (never silently ignored)",
              rc == 3)
        rc2 = main([fpath, "--pull-summary", "/tmp/definitely-missing-board-stats.json",
                    "--out", f"{outdir}/pulse.json"])
        check("pull-summary: a MISSING --pull-summary file is refused with exit 3", rc2 == 3)
        rc3 = main([fpath, "--out", f"{outdir}/pulse.json", "--emit-events", f"{outdir}/events",
                    "--lane-run-out", f"{outdir}/lane_run.json"])
        check("first run: no --prior and no --pull-summary → exit 0, delta_wow null (the no-file path works end to end)",
              rc3 == 0)
        with open(f"{outdir}/pulse.json", encoding="utf-8") as fh:
            check("first run: the emitted manifest carries delta_wow null on every event",
                  all(e["metadata"]["delta_wow"] is None
                      for e in json.load(open(f"{outdir}/pulse.json", encoding="utf-8"))["events"]))
    finally:
        os.unlink(fpath)

    # --- Workflow lint: the Action's guard stays file-reality-based ------------------------
    # Guards against re-introducing a string-compare on the prior step's OUTPUT (which lied:
    # the twin-read step exits 0 without writing the file when the read fails) — the crash
    # behind run 41943575924. Checked textually so the selftest needs no yaml dependency;
    # skipped when the workflow file isn't in the repo (e.g. running from a bare checkout).
    wf = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                      ".github", "workflows", "ats-pulse.yml")
    if os.path.exists(wf):
        wftext = open(wf, encoding="utf-8").read()
        check("workflow lint: the aggregate guard tests [ -s /tmp/prior.json ] (file reality), "
              "never the prior step's output string",
              "if [ -s /tmp/prior.json ]; then PRIOR=\"--prior /tmp/prior.json\"; fi" in wftext
              and 'steps.prior.outputs.prior }}' not in wftext
              and '!= "none"' not in wftext)
        check("workflow lint: the prior step sets its output ONLY when it actually wrote the file",
              'if [ -s /tmp/prior.json ]; then echo "prior=/tmp/prior.json"' in wftext)

        # --- Workflow lint: bash -n + heredoc pairing on EVERY run block -------------------
        # bash -n alone is insufficient: an EOF-terminated heredoc is only a WARNING (exit 0),
        # which is how run 41945700887's unterminated heredoc reached main. Both checks run.
        check("workflow shell lint: a healthy script with a closed heredoc passes",
              shell_script_problems("python3 - <<'EOF'\nprint('hi')\nEOF\necho done") == [])
        broken = ("python3 - <<'EOF'\nprint('hi')\n"
                  "if [ -s /tmp/prior.json ]; then echo ok; fi")  # no EOF — the 41945700887 shape
        check("workflow shell lint: an UNTERMINATED heredoc is flagged (would have caught run 41945700887)",
              any("never terminated" in p or "here-document" in p
                  for p in shell_script_problems(broken)))
        check("workflow shell lint: a heredoc closed by the WRONG delimiter is flagged",
              any("here-document" in p or "never terminated" in p
                  for p in shell_script_problems("cat <<'EOF'\nhi\neof")))
        wf_problems = lint_workflow_shell(wf)
        check("workflow shell lint: every run: block in ats-pulse.yml passes bash -n + heredoc pairing"
              + (f" — PROBLEMS: {wf_problems}" if wf_problems else ""),
              not wf_problems)

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
                    help="read the lane_run manifest and write the REAL lane_run row through "
                         "spine_client.write — to PROD, the one deliberate exception (PII-free "
                         "ledger; registry + freshness live there). SUPABASE_API_KEY env.")
    ap.add_argument("--started-at", help="ISO run-start timestamp for --write-lane-run (default: the manifest's ran_at)")
    ap.add_argument("--events-written", type=int, default=None,
                    help="rows ACTUALLY written to the graph for --write-lane-run (default: the "
                         "manifest's written count — 0 while event writes are dry-run)")
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
        if a.events_written is not None:
            lane["written"] = a.events_written
        row = write_lane_run(lane, a.started_at or lane["ran_at"])
        print(f"ats_pulse: lane_run row written to PROD "
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
          f"{len(lane['errored_boards'])} errored boards · counts only (no titles, no people) · "
          f"delta_wow baseline: {'prior week' if prior else 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
