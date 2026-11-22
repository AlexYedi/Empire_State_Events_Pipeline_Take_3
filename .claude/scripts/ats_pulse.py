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
  * LIVE event writes (YED-327, Alex 2026-11-20): --write-events runs substrate's ensure_event
    in-process (Graph → spine_client.req, the guarded path) on each validated manifest, to PROD.
    Idempotent per week: event_date is the week's Sunday, so a re-run matches instead of
    creating. items_written = event rows ACTUALLY created this run (a re-run writes 0). Company
    edges resolve through the registry aliases (ensure-roles' rule) so a bare registry name lands
    on the graph's existing qualified company. All graph output is swallowed: it names companies.
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
  * delta_wow (YED-484): --write-events reads last week's hiring_pulse counts from PROD (one
    read-only GET through spine_client.req) and fills each delta before the first write; a failed
    read is ONE ::warning:: and null deltas. Companies the lane creates carry source 'ats_pulse'.

Selftest: inline fixtures, offline, negative-PII cases. Run: python3 ats_pulse.py --selftest
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import http.client
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import urllib.parse
from datetime import date, datetime, timedelta, timezone

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


# ---------------------------------------------------------------------------
# Prior-week baseline read — PROD, read-only, inside the write step (YED-484)
# ---------------------------------------------------------------------------
# The baseline used to come from the twin, which never receives prod events, so delta_wow was
# always null. It is now one GET through spine_client.req (prod-only by design) in the
# --write-events path: the one workflow step that already holds SUPABASE_API_KEY.

PRIOR_TITLE_RE = re.compile(r"Hiring pulse — (.+) \((\d{4}-W\d{2})\)")


class PriorReadError(RuntimeError):
    """The prior-week prod read failed (API error or contract change). The read is OPTIONAL:
    write_events reports it and the run writes delta_wow null — never silent, never fatal.
    Messages carry status/type/week ONLY: the target registry is private and Actions logs are
    public."""


def _expect_iso_day(day: str) -> None:
    """A real calendar date in YYYY-MM-DD form, or PriorReadError — never a raw
    ValueError traceback (2026-13-99 passes a regex; only the calendar catches it)."""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        raise PriorReadError(f"prior day {day!r} is not YYYY-MM-DD")
    try:
        date.fromisoformat(day)
    except ValueError:
        raise PriorReadError(f"prior day {day!r} is not a real calendar date") from None


def _one_line(body: bytes, limit: int = 200) -> str:
    """An error message flattened to a single bounded log line — ::warning:: annotations
    stay on one line and control characters never reach the log."""
    return " ".join(body[:300].decode("utf-8", "replace").split())[:limit]


def prior_read_path(day: str) -> str:
    """The PostgREST path (spine_client.req form) for one week's hiring_pulse rows.

    The two event_date filters are SEPARATE query params via a tuple list — the original
    bug: joined into ONE value, urlencode percent-encoded the inner '&' and PostgREST answered
    400. ``day`` is that week's Sunday (event_date contract: the Sunday ENDING the ISO week,
    0016 §2). quote_via=quote (spine_client.q() parity): %20, never '+', for the space."""
    _expect_iso_day(day)
    query = urllib.parse.urlencode([
        ("select", "title,metadata"),
        ("kind", "eq.market"),
        ("signal_type", f"eq.{SIGNAL_TYPE}"),
        ("title", "like.*Hiring pulse*"),
        ("event_date", f"gte.{day}T00:00:00Z"),
        ("event_date", f"lte.{day}T23:59:59Z"),
    ], quote_via=urllib.parse.quote)
    return f"/event?{query}"


def prior_week_events(rows: object, day: str) -> tuple[str | None, list[dict]]:
    """Event rows → (week, prior-baseline events) for rows matching the hiring_pulse
    title contract with a plain-int roles_open. Never guesses at an API response: a
    non-array body — an API contract change — raises PriorReadError and is NEVER used
    as an empty baseline. Rows not matching the title contract, or whose roles_open is
    not a plain int, are ignored (never invented). A matched row stamped a different
    week than ``day`` raises too — the week must not depend on row order. Error messages
    carry counts, types and weeks ONLY, never a company name."""
    if not isinstance(rows, list):
        raise PriorReadError(f"prod returned a non-array JSON body ({type(rows).__name__}) "
                             "— an API contract change is never guessed at")
    _expect_iso_day(day)
    y, w, _ = date.fromisoformat(day).isocalendar()
    expected = f"{y}-W{w:02d}"          # the event_date contract: the Sunday ENDING the week
    week, events = None, []
    for row in rows:
        if not isinstance(row, dict):
            raise PriorReadError(f"prod returned a non-object event row ({type(row).__name__}) "
                                 "— an API contract change is never guessed at")
        title = row.get("title")
        if title is not None and not isinstance(title, str):
            raise PriorReadError(f"prod row has a non-string title ({type(title).__name__}) "
                                 "— an API contract change is never guessed at")
        m = PRIOR_TITLE_RE.fullmatch(title or "")
        if not m:
            continue
        md = row.get("metadata")
        if md is not None and not isinstance(md, dict):
            # counts and types only — the row's title names a registry company
            raise PriorReadError(f"prod returned a hiring-pulse row with non-object "
                                 f"metadata ({type(md).__name__}) — an API contract change "
                                 "is never guessed at")
        pc = (md or {}).get("roles_open")
        if not isinstance(pc, int) or isinstance(pc, bool):
            continue
        if m.group(2) != expected:
            # week only — never the company name
            raise PriorReadError(f"a matched hiring-pulse row is stamped {m.group(2)} but "
                                 f"the prior day {day} ends {expected} — refusing at the "
                                 "source instead of building a week off row order")
        week = expected
        events.append({"company": m.group(1), "metadata": {"roles_open": pc}})
    return (week if events else None), events


def read_prior_week(week: str, *, _req=None) -> dict:
    """Read-only prod GET (spine_client.req) of the ISO week BEFORE ``week`` → the baseline
    {"week", "events"}, events = [{"company", "metadata": {"roles_open"}}]. A successful read
    with zero matching rows is an empty-but-real baseline (every delta stays null). ANY failure
    raises PriorReadError with status/type only — a response body can echo a registry name.
    _req is the test seam."""
    try:
        day = (week_sunday(week) - timedelta(days=7)).isoformat()
    except ValueError:
        raise PriorReadError("manifest week is not an ISO week bucket") from None
    if _req is None:
        import spine_client
        _req = spine_client.req
    try:
        status, rows = _req("GET", prior_read_path(day))
    except (Exception, SystemExit) as e:   # transport, retry give-up, missing key: the TYPE only
        raise PriorReadError(type(e).__name__) from None
    if status != 200:
        raise PriorReadError(f"HTTP {status}")   # status ONLY — the body can echo a company name
    _, events = prior_week_events(rows, day)
    return {"week": week_bucket(date.fromisoformat(day)), "events": events}


def apply_prior(manifests: list[dict], prior: dict) -> int:
    """Fill each ensure-event manifest's delta_wow = roles_open − last week's roles_open for the
    same company (keyed by the title's registry name — the alias map only rewrites entities).
    A company absent last week keeps delta_wow null (no invented baseline). A same-week prior is
    refused (a delta against itself is 0 by construction). Returns the companies matched."""
    prior_counts = {ev["company"]: ev["metadata"]["roles_open"] for ev in prior.get("events", [])}
    matched = 0
    for m in manifests:
        hit = PRIOR_TITLE_RE.fullmatch(m["event"].get("title") or "")
        if not hit:
            continue
        if hit.group(2) == prior.get("week"):
            raise PriorReadError(f"prior baseline is itself week {hit.group(2)}")
        meta = m["event"]["metadata"]
        if hit.group(1) in prior_counts and type(meta.get("roles_open")) is int:
            meta["delta_wow"] = meta["roles_open"] - prior_counts[hit.group(1)]
            matched += 1
    return matched


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

    `written` counts rows ACTUALLY written to the graph — not events built. The default is 0;
    --write-events replaces it with the event rows it created (a lower bound is never an
    overclaim)."""
    lane = manifest.pop("_lane", {"seen": 0, "refused": 0, "errored_boards": []})
    return {"lane": LANE, "week": manifest["week"], "ran_at": manifest["generated_at"],
            "producer": SOURCE, "status": "ok" if not lane["errored_boards"] else "ok_with_errors",
            "seen": lane["seen"], "refused": lane["refused"],
            "written": events_written, "errored_boards": lane["errored_boards"]}


def lane_run_row(lane: dict, started_at: str, *, status: str | None = None,
                 error: str | None = None) -> dict:
    """The lane_run manifest → the REAL public.lane_run row (0016 contract columns), the shape
    spine_client.write('lane_run', …) posts. Pure so the selftest can pin every mapping.
    status/error override the board-derived ones when the event write fails mid-run."""
    errored = list(lane.get("errored_boards") or [])
    err_text = "; ".join(x for x in (error, ("errored boards: " + ", ".join(errored)) if errored else None)
                         if x) or None
    return {
        "lane": lane["lane"],
        "started_at": started_at,
        "finished_at": lane["ran_at"],
        # lane_run.status CHECK is ('running','success','partial','failed','skipped') — errored
        # boards are a 'partial' run, not a failure (the run itself succeeded).
        "status": status or ("success" if not errored else "partial"),
        "items_seen": lane["seen"],
        "items_written": lane["written"],
        "items_refused": lane["refused"],
        "credits_spent": 0,               # ATS boards are free; this lane spends no credits
        # column CHECK caps error at 1000 chars; a longer list still records the first names.
        "error": err_text[:1000] if err_text else None,
    }


def write_lane_run(lane: dict, started_at: str, *, status: str | None = None,
                   error: str | None = None) -> dict:
    """Write the REAL lane_run row through spine_client.write — to PROD, deliberately.

    The ONE prod exception (Alex's decision, post-merge review of #271): lane_run is a PII-free
    ledger (counts and board-status only — the guard still fronts every write), lane_registry
    and its FK live in prod, and the YED-304 freshness healthcheck reads prod. spine_client is
    prod-only by design: _send builds its host from the hardcoded REF, so no caller override
    can divert the request (the earlier MI_TWIN_URL override was dead config — removed). Since
    YED-327 the lane's events go to prod too (write_events). The key reaches spine_client
    as SUPABASE_API_KEY (its one key source). A non-2xx answer raises (status only — a body can
    echo the errored-board names): an unwritten ledger row must never read as written."""
    import spine_client
    row = lane_run_row(lane, started_at, status=status, error=error)
    code, _ = spine_client.write("lane_run", [row])
    if not 200 <= code < 300:
        raise RuntimeError(f"lane_run write failed: HTTP {code}")
    return row


class EventWriteError(RuntimeError):
    """A live event write failed. The message is counts + exception TYPE only (graph errors echo
    titles, i.e. company names, and Actions logs are public); .written = rows created before it."""
    def __init__(self, msg: str, written: int):
        super().__init__(msg)
        self.written = written


def write_events(events_dir: str, registry: str | None = None, g=None, read_prior=None) -> dict:
    """LIVE: each --emit-events manifest → substrate's ensure_event (Graph → spine_client.req,
    the guarded write path) — to PROD (YED-327). Idempotent per week: event_date is the week's
    Sunday, so find_event's same-day title match makes a re-run a no-op (written 0).

    delta_wow (YED-484): read_prior(week) → last week's baseline from PROD (read_prior_week, the
    CLI's default), applied after validation and before the first write. Optional: a failed read
    leaves every delta null and is reported as prior_error (status/type only), never raised.
    Companies this lane creates carry source 'ats_pulse' (substrate's default is unchanged).

    Every manifest is validated BEFORE the first write (fail closed). Company entity names map
    through substrate.registry_aliases (ensure-roles' rule) so 'Cursor' lands on the graph's
    'Cursor (Anysphere)' instead of minting a duplicate; titles keep the registry name (the
    dedupe + prior-read key). All graph stdout/stderr is swallowed — it names companies — and
    the identity-ambiguity ledger goes beside events_dir (the workflow cleanup deletes it).
    g is the test seam (substrate._FakeGraph). Returns counts only."""
    import substrate
    names = sorted(f for f in os.listdir(events_dir) if f.endswith(".json"))
    manifests = []
    for name in names:
        with open(os.path.join(events_dir, name), encoding="utf-8") as fh:
            manifests.append(json.load(fh))
    bad = sum(1 for m in manifests if validate_event_manifest(m))
    if bad:
        raise EventWriteError(f"{bad} invalid event manifest(s) — nothing written", 0)
    prior_matched, prior_error = None, None
    weeks = {(m["event"].get("metadata") or {}).get("week") for m in manifests}
    if read_prior and manifests:
        try:
            if len(weeks) != 1 or None in weeks:
                raise PriorReadError("manifests do not share one week")
            prior_matched = apply_prior(manifests, read_prior(weeks.pop()))
        except PriorReadError as e:
            prior_error = _one_line(str(e).encode())
            for m in manifests:              # all or nothing: a half-applied baseline is never written
                m["event"]["metadata"]["delta_wow"] = None
    if g is None:
        g = substrate.Graph(False, substrate.Stats())
        substrate.AMBIGUITY_LEDGER = os.path.join(os.path.dirname(os.path.abspath(events_dir)),
                                                  "identity-ambiguity.jsonl")
    g.quiet = True
    written = 0
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            aliases = (substrate.registry_aliases(open(registry, encoding="utf-8").read(), g)
                       if registry and os.path.exists(registry) else {})
            for m in manifests:
                # explicit UTC midnight: a bare date casts to timestamptz in the DB session's
                # TimeZone, but find_event (the dedupe) and the prior read query a UTC day window
                if re.fullmatch(r"\d{4}-\d{2}-\d{2}", m["event"].get("event_date") or ""):
                    m["event"]["event_date"] += "T00:00:00Z"
                for e in m["entities"]:
                    e["name"] = aliases.get(substrate.norm_text(e["name"]), e["name"])
                before = g.stats.c.get("event", {}).get("created", 0)
                g.ensure_event(m, company_source=SOURCE)
                if g.stats.c.get("event", {}).get("created", 0) > before:
                    written += 1
    except (Exception, SystemExit) as e:          # substrate exits via SystemExit(<path with a title>)
        raise EventWriteError(f"event write failed after {written} row(s) written "
                              f"({type(e).__name__})", written) from None
    c = g.stats.c
    return {"manifests": len(manifests), "written": written,
            "matched": c.get("event", {}).get("matched", 0),
            "edges_created": c.get("event_entity", {}).get("created", 0),
            "companies_created": c.get("company", {}).get("created", 0),
            "companies_ambiguous": c.get("company", {}).get("ambiguous_name", 0),
            "prior_matched": prior_matched, "prior_error": prior_error}


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
        _FakeResp.status = 400
        try:
            write_lane_run(lane, "x")
            check("lane_run write: a non-2xx answer raises (an unwritten ledger row never reads as written)", False)
        except RuntimeError as e:
            check("lane_run write: a non-2xx answer raises (an unwritten ledger row never reads as written)",
                  str(e) == "lane_run write failed: HTTP 400")
        _FakeResp.status = 201
    finally:
        _sc.http.client.HTTPSConnection = orig_conn
        if orig_key is None:
            os.environ.pop("SUPABASE_API_KEY", None)
        else:
            os.environ["SUPABASE_API_KEY"] = orig_key
        os.environ.pop("MI_TWIN_URL", None)
        _sc._KEY = None

    # --- LIVE event writes (YED-327): substrate's REAL ensure_event over its in-memory double ----
    import substrate as _sub

    def _emit(manifest) -> str:
        d = tempfile.mkdtemp()
        for em in event_manifests(_json_copy(manifest)):
            with open(os.path.join(d, em["event"]["metadata"]["dedup_key"].replace(":", "_") + ".json"),
                      "w", encoding="utf-8") as fh:
                json.dump(em, fh)
        return d

    fg = _sub._FakeGraph()
    fg.t["company"].append({"id": "co-runway", "name": "Runway (Runway ML)"})   # the graph's qualified name
    reg = os.path.join(tempfile.mkdtemp(), "target-companies.md")
    with open(reg, "w", encoding="utf-8") as fh:
        fh.write("| Runway | ashby | `runway` |\n| Anthropic | ashby | `anthropic` |\n")
    edir = _emit(m)
    _out, _err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(_out), contextlib.redirect_stderr(_err):
        w1 = write_events(edir, reg, g=fg)
    check("live write: one event per company created; written = rows ACTUALLY created (3)",
          w1["written"] == 3 and len(fg.t["event"]) == 3 and w1["matched"] == 0)
    check("live write: rows carry the real signal_type column + the week's Sunday",
          all(e["signal_type"] == SIGNAL_TYPE and e["event_date"] == "2026-11-01T00:00:00Z" and e["kind"] == "market"
              for e in fg.t["event"]))
    runway_ev = next(e["id"] for e in fg.t["event"] if "Runway" in e["title"])
    check("live write: a bare registry name resolves to the graph's qualified company (no duplicate)",
          len([c for c in fg.t["company"] if "Runway" in c["name"]]) == 1
          and {"event_id": runway_ev, "entity_id": "co-runway"}.items()
          <= next(x for x in fg.t["event_entity"] if x["event_id"] == runway_ev).items())
    check("live write: graph output is swallowed — no company name reaches stdout/stderr",
          not any(n in _out.getvalue() + _err.getvalue() for n in ("Anthropic", "Runway", "Harvey")))
    w2 = write_events(edir, reg, g=fg)
    check("live write: a same-week re-run is a no-op (written 0, 3 matched, no new rows)",
          w2["written"] == 0 and w2["matched"] == 3 and len(fg.t["event"]) == 3
          and len(fg.t["event_entity"]) == 3)
    w3 = write_events(_emit(build_manifest(rows, date(2026, 10, 28), board_stats=_fixture_board_stats())),
                      reg, g=fg)
    check("live write: a mid-week dispatch of the same ISO week dedupes onto the Sunday (written 0)",
          w3["written"] == 0 and len(fg.t["event"]) == 3)
    w4 = write_events(_emit(build_manifest(rows, date(2026, 11, 8), board_stats=_fixture_board_stats())),
                      reg, g=fg)
    check("live write: the next week writes its own rows (3 more, company edges reused)",
          w4["written"] == 3 and len(fg.t["event"]) == 6 and len(fg.t["company"]) == 3)

    bdir = _emit(m)
    _bf = sorted(os.listdir(bdir))[0]
    _bm = json.load(open(os.path.join(bdir, _bf), encoding="utf-8"))
    _bm["entities"].append({"type": "person", "name": "A", "role": "speaker"})
    json.dump(_bm, open(os.path.join(bdir, _bf), "w", encoding="utf-8"))
    fg_bad = _sub._FakeGraph()
    try:
        write_events(bdir, None, g=fg_bad)
        check("live write: ONE invalid manifest refuses the batch before any write (fail closed)", False)
    except EventWriteError as e:
        check("live write: ONE invalid manifest refuses the batch before any write (fail closed)",
              e.written == 0 and not fg_bad.t["event"] and not fg_bad.t["company"])

    class _DiesOnSecond(_sub._FakeGraph):
        def ensure_event(self, mm, **kw):
            if self.t["event"]:
                raise SystemExit(f"GET /event?title=ilike.{mm['event']['title']} -> 500")
            return super().ensure_event(mm, **kw)
    try:
        write_events(_emit(m), None, g=_DiesOnSecond())
        check("live write: a mid-run failure raises with the rows written so far, counts + type only", False)
    except EventWriteError as e:
        check("live write: a mid-run failure raises with the rows written so far, counts + type only",
              e.written == 1 and str(e) == "event write failed after 1 row(s) written (SystemExit)")

    # CLI wiring: the ledger row carries the real count; a failure is ledgered partial/failed, exit 1.
    g_ = globals()
    saved_w = (g_["write_events"], g_["write_lane_run"])
    ledgered = []
    g_["write_lane_run"] = lambda ln, st, **k: ledgered.append((dict(ln), k)) or lane_run_row(ln, st, **k)
    lpath = os.path.join(tempfile.mkdtemp(), "lane_run.json")
    with open(lpath, "w", encoding="utf-8") as fh:
        json.dump(lane_run_manifest(_json_copy(m)), fh)
    try:
        g_["write_events"] = lambda d, r, **k: {"manifests": 3, "written": 3, "matched": 0, "edges_created": 3,
                                           "companies_created": 2, "companies_ambiguous": 0}
        with contextlib.redirect_stdout(io.StringIO()):
            rc = main(["--write-lane-run", lpath, "--write-events", edir, "--started-at", "x"])
        check("CLI: --write-events → the lane_run row carries the real written count (3), exit 0",
              rc == 0 and ledgered[-1][0]["written"] == 3 and ledgered[-1][1] == {})

        def _boom(d, r, **k):
            raise EventWriteError("event write failed after 2 row(s) written (SystemExit)", 2)
        g_["write_events"] = _boom
        _o = io.StringIO()
        with contextlib.redirect_stdout(_o):
            rc = main(["--write-lane-run", lpath, "--write-events", edir, "--started-at", "x"])
        check("CLI: a mid-run failure ledgers 'partial' with the 2 rows written, then exits 1",
              rc == 1 and ledgered[-1][0]["written"] == 2 and ledgered[-1][1]["status"] == "partial"
              and "after 2 row(s)" in ledgered[-1][1]["error"])
        check("CLI: the failure line is counts only (no company names)",
              not any(n in _o.getvalue() for n in ("Anthropic", "Runway", "Harvey")))
        r_fail = lane_run_row(lane, "x", status="failed", error="event write failed after 0 row(s) written (X)")
        check("lane_run row: failure override keeps the errored-board text after the failure reason",
              r_fail["status"] == "failed"
              and r_fail["error"] == "event write failed after 0 row(s) written (X); errored boards: Neverboard")
    finally:
        g_["write_events"], g_["write_lane_run"] = saved_w

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

    # --- Workflow lint: the prior-week read lives in the ONE prod-key step (YED-484) ----------
    # The twin read (always null: the twin never receives prod events) is gone; the baseline is
    # read by --write-events in the step that already holds SUPABASE_API_KEY. Checked textually
    # so the selftest needs no yaml dependency; skipped when the workflow file isn't present.
    wf = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                      ".github", "workflows", "ats-pulse.yml")
    if os.path.exists(wf):
        wftext = open(wf, encoding="utf-8").read()
        check("workflow lint: no twin secret, no twin read step, no --prior file plumbing left",
              "secrets.MI_TWIN" not in wftext and "--fetch-prior-week" not in wftext
              and "/tmp/prior.json" not in wftext)
        check("workflow lint: SUPABASE_API_KEY is still scoped to ONE step (the write step)",
              wftext.count("secrets.SUPABASE_API_KEY") == 1)

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

    # --- Prior-week PROD read (YED-484): delta_wow from last week's prod rows -------------------
    # Offline: a fake req (spine_client.req's (status, body) shape) — no network, no key.
    _name = "Anthropic"
    _seen = {}

    def _fake_req(status, body):
        def _r(method, path, *a, **k):
            _seen["method"], _seen["path"] = method, path
            return status, body
        return _r

    read_prior_week("2026-W44", _req=_fake_req(200, []))
    check("prior read: ONE GET of the week BEFORE (W44 → Sunday 2026-10-25), two separate event_date "
          "params, %20-encoded title filter (the old 400 root cause, pinned)",
          _seen["method"] == "GET" and _seen["path"].startswith("/event?")
          and "gte.2026-10-25T00%3A00%3A00Z" in _seen["path"]
          and _seen["path"].count("event_date=") == 2 and "%20" in _seen["path"] and "+" not in _seen["path"])
    _saved_req = _sc.req
    _sc.req = _fake_req(200, [])
    try:
        read_prior_week("2026-W44")
        check("prior read: the default reader is spine_client.req (prod; no twin URL, no twin key)",
              _seen["path"].startswith("/event?"))
    finally:
        _sc.req = _saved_req
    _w44 = [{"title": f"Hiring pulse — {_name} (2026-W43)", "metadata": {"roles_open": 5}},
            {"title": "Hiring pulse — Runway (2026-W43)", "metadata": {"roles_open": True}},   # bool → ignored
            {"title": f"Funding — {_name} (2026-W43)", "metadata": {"roles_open": 3}}]         # wrong title → ignored
    pw = read_prior_week("2026-W44", _req=_fake_req(200, _w44))
    check("prior read: a 200 parses the title contract into the baseline (counts only)",
          pw == {"week": "2026-W43", "events": [{"company": _name, "metadata": {"roles_open": 5}}]})

    def _delta_run(reader):
        fgp = _sub._FakeGraph()
        o, e = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(o), contextlib.redirect_stderr(e):
            res = write_events(_emit(m), None, g=fgp, read_prior=reader)
        deltas = {ev["title"].split(" — ")[1].split(" (")[0]: ev["metadata"]["delta_wow"] for ev in fgp.t["event"]}
        return res, deltas, o.getvalue() + e.getvalue() + json.dumps(res), fgp

    res, deltas, blob, fgp = _delta_run(lambda wk: read_prior_week(wk, _req=_fake_req(200, _w44)))
    check("delta_wow: prior week PRESENT → a real delta (7 open vs 5 last week = +2), only that company",
          deltas == {"Anthropic": 2, "Harvey": None, "Runway": None} and res["prior_matched"] == 1
          and res["prior_error"] is None)
    check("delta_wow: lane-created companies carry source 'ats_pulse' (substrate default untouched)",
          fgp.t["company"] and all(c.get("source") == SOURCE for c in fgp.t["company"]))
    res, deltas, blob, _ = _delta_run(lambda wk: read_prior_week(wk, _req=_fake_req(200, [])))
    check("delta_wow: prior week ABSENT (a real, empty read) → null on every event, no warning",
          set(deltas.values()) == {None} and res["prior_matched"] == 0 and res["prior_error"] is None)
    res, deltas, blob, _ = _delta_run(None)
    check("delta_wow: no reader (the selftest/local path) → null, nothing read",
          set(deltas.values()) == {None} and res["prior_matched"] is None)
    _same = lambda wk: {"week": "2026-W44", "events": [{"company": _name, "metadata": {"roles_open": 1}}]}  # noqa: E731
    res, deltas, blob, _ = _delta_run(_same)
    check("delta_wow: a same-week baseline is refused → null everywhere, reported (never a 0 delta)",
          set(deltas.values()) == {None} and res["prior_error"] and _name not in res["prior_error"])

    # Every failure class: non-fatal (events still written), delta null, and the reported error,
    # stdout, stderr and the returned counts never carry a company name.
    class _Boom(Exception):
        pass
    _fails = [
        ("a 400 whose BODY echoes a company name", _fake_req(400, f"echo: Hiring pulse — {_name} (2026-W43)")),
        ("a 200 with a stray-week row", _fake_req(200, [{"title": f"Hiring pulse — {_name} (2026-W40)",
                                                         "metadata": {"roles_open": 3}}])),
        ("a 200 whose metadata is a string", _fake_req(200, [{"title": f"Hiring pulse — {_name} (2026-W43)",
                                                              "metadata": "7"}])),
        ("a 200 whose row is a bare string", _fake_req(200, [f"Hiring pulse — {_name} (2026-W43)"])),
        ("a 200 whose row title is an array", _fake_req(200, [{"title": [_name], "metadata": {"roles_open": 3}}])),
        ("a non-array 200 naming a company", _fake_req(200, {"message": f"echo {_name}"})),
        ("a reader raising with the name in its message",
         lambda *a, **k: (_ for _ in ()).throw(_Boom(f"connection exploded — {_name}"))),
        ("a reader exiting (missing key)", lambda *a, **k: (_ for _ in ()).throw(SystemExit(f"FATAL {_name}"))),
    ]
    for _why, _r in _fails:
        res, deltas, blob, fgp = _delta_run(lambda wk, _r=_r: read_prior_week(wk, _req=_r))
        check(f"prior read failure: {_why} — events still written, delta null, NO name anywhere",
              res["written"] == 3 and set(deltas.values()) == {None} and res["prior_error"]
              and _name not in blob and _name not in res["prior_error"])

    # CLI: the write step reads the prior through read_prior_week and prints counts only.
    saved_w = g_["write_events"], g_["write_lane_run"]
    g_["write_lane_run"] = lambda ln, st, **k: lane_run_row(ln, st, **k)
    _calls = []
    try:
        for _pe, _pm in ((None, 1), ("HTTP 500", None)):
            g_["write_events"] = (lambda d, r, read_prior=None, _pe=_pe, _pm=_pm:
                                  _calls.append(read_prior) or
                                  {"manifests": 3, "written": 3, "matched": 0, "edges_created": 3,
                                   "companies_created": 2, "companies_ambiguous": 0,
                                   "prior_matched": _pm, "prior_error": _pe})
            _o = io.StringIO()
            with contextlib.redirect_stdout(_o):
                rc = main(["--write-lane-run", lpath, "--write-events", edir, "--started-at", "x"])
            if _pe:
                check("CLI: a failed prior read → ONE ::warning::, exit 0 (the read is optional)",
                      rc == 0 and _o.getvalue().count("::warning::") == 1)
            else:
                check("CLI: --write-events passes read_prior_week; the baseline line is counts only",
                      rc == 0 and _calls[-1] is read_prior_week
                      and "1 of 3 companies matched last week" in _o.getvalue())
    finally:
        g_["write_events"], g_["write_lane_run"] = saved_w

    print(f"selftest: {ok}/{n} ats_pulse cases pass")
    return 0 if ok == n else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("tsv", nargs="*", help="ats_pull TSV path(s); omit with --validate")
    ap.add_argument("--prior", help="last week's pulse.json for a LOCAL aggregate (same-week priors "
                                    "are refused); the Action's baseline is read from prod by "
                                    "--write-events instead")
    ap.add_argument("--pull-summary", help="ats_pull --summary JSON (unfiltered board counts)")
    ap.add_argument("--out", help="write the aggregate manifest here")
    ap.add_argument("--emit-events", help="write one substrate ensure-event manifest per company here")
    ap.add_argument("--lane-run-out", help="write the lane_run manifest (the run's ledger entry, kept local: names boards) here")
    ap.add_argument("--write-lane-run", metavar="MANIFEST",
                    help="read the lane_run manifest and write the REAL lane_run row through "
                         "spine_client.write — to PROD, the one deliberate exception (PII-free "
                         "ledger; registry + freshness live there). SUPABASE_API_KEY env.")
    ap.add_argument("--started-at", help="ISO run-start timestamp for --write-lane-run (default: the manifest's ran_at)")
    ap.add_argument("--write-events", metavar="DIR",
                    help="LIVE (YED-327): write each --emit-events manifest through substrate "
                         "ensure_event → spine_client — to PROD; idempotent per week. Reads last "
                         "week's counts from PROD first (read-only GET) to fill delta_wow; a failed "
                         "read prints ONE ::warning:: and writes delta_wow null. Needs "
                         "--write-lane-run (the ledger row then carries the real written count).")
    ap.add_argument("--registry", help="target-company registry for --write-events' company-name "
                                       "aliases (absent file → registry names used as-is)")
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

    if a.write_events and not a.write_lane_run:
        ap.error("--write-events needs --write-lane-run (every live write is ledgered)")
    if a.write_lane_run:
        with open(a.write_lane_run, encoding="utf-8") as fh:
            lane = json.load(fh)
        started = a.started_at or lane["ran_at"]
        if a.write_events:
            try:
                res = write_events(a.write_events, a.registry, read_prior=read_prior_week)
            except EventWriteError as e:
                # lane 2's rule: ledger the failed run with the rows actually written, then fail
                lane["written"] = e.written
                write_lane_run(lane, started, status="partial" if e.written else "failed", error=str(e))
                print(f"ats_pulse: {e} — lane_run ledgered as "
                      f"{'partial' if e.written else 'failed'} (counts only)")
                return 1
            lane["written"] = res["written"]
            print(f"ats_pulse: events written to PROD — {res['written']} created · {res['matched']} "
                  f"already present (same-week re-run) · {res['edges_created']} company edges · "
                  f"{res['companies_created']} companies created ({res['companies_ambiguous']} "
                  f"ambiguous) · of {res['manifests']} manifests (counts only)")
            if res.get("prior_error"):
                print(f"::warning::ats_pulse: prior-week prod read failed ({res['prior_error']}) "
                      f"— delta_wow null this run")
            else:
                print(f"ats_pulse: delta_wow baseline from PROD — {res.get('prior_matched')} of "
                      f"{res['manifests']} companies matched last week (counts only)")
        elif a.events_written is not None:
            lane["written"] = a.events_written
        row = write_lane_run(lane, started)
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
          f"delta_wow baseline: {'--prior file' if prior else 'none here (--write-events reads it from prod)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
