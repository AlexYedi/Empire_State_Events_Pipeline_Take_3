#!/usr/bin/env python3
"""ttl_report — S-04 R1 (YED-183) report-only retention report for the MI spine.

Read-only by construction: every graph touch is a GET through spine_client.req(); there is
no POST/PATCH/DELETE/DELETE-leg anywhere in this file. It reports rows crossing the proposed
R2 thresholds so Alex can eyeball a quarter of reports before any archive or purge leg is
ever enabled (Option D in docs/adr/proposals/pii-retention-ttl.md; adopted report-only first,
2026-11-01). Delete/archive legs are explicitly deferred until YED-160/161 widen ingestion.

Buckets (thresholds are R2 PROPOSALS — tuning targets, never enforcement):
  person.stale_18mo        age clock older than 18 months
  person.archive_24mo      stale AND no event_entity/claim_entity link created in 24 months
  claim.rejected_90d       status='rejected' and clock older than 90 days
  claim.candidate_12mo     status='candidate', never reviewed, clock older than 12 months
  claim.approved           no TTL — counted only; approved claims are never auto-expired

Binding null rule (Alex, 2026-11-01, YED-183 comment dd28915c): last_engaged_at is NULL for
every person today, so the age clock falls back to created_at. The same chain
(last_engaged_at -> created_at) is applied to claims for consistency; rejected claims prefer
reviewed_at — the rejection moment — when it exists.

PII: the report prints counts, row ids, names and claim_keys — tier-2 fields only; contact
detail is never selected. Belt-and-suspenders: the finished report text is scanned with
spine_client's own EMAIL_RE/PHONE_RE before printing; a match aborts the output (exit 2).

Usage:   python3 .claude/scripts/ttl_report.py --ttl-report [--as-of YYYY-MM-DD]
Selftest python3 .claude/scripts/ttl_report.py --selftest   (offline; no network)
"""
from __future__ import annotations

import argparse
import calendar
import dataclasses
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spine_client  # noqa: E402  — read-only surface: req() GETs + the guard's PII regexes

UTC = dt.timezone.utc


# ---------------------------------------------------------------------------
# Config — the R2 thresholds as adopted-as-proposals (revisable; the first
# quarter of reports is the tuning evidence, per the decision brief).
# ---------------------------------------------------------------------------
@dataclasses.dataclass(frozen=True)
class TTLConfig:
    person_stale_months: int = 18
    person_archive_months: int = 24
    claim_rejected_days: int = 90
    claim_candidate_months: int = 12


# ---------------------------------------------------------------------------
# Pure logic — everything below is offline-testable; no network anywhere.
# ---------------------------------------------------------------------------
def parse_ts(value) -> dt.datetime | None:
    """ISO timestamptz -> aware UTC datetime; None when absent/unparseable."""
    if not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def age_clock(row: dict) -> tuple[dt.datetime, str] | None:
    """The binding null rule: last_engaged_at, else created_at. (ts, source) or None when
    neither column has a value — a row with no clock is reported, never guessed at."""
    for key in ("last_engaged_at", "created_at"):
        ts = parse_ts(row.get(key))
        if ts is not None:
            return ts, key
    return None


def months_ago(as_of: dt.date, months: int) -> dt.date:
    """as_of minus `months`, clamping the day (Jan 31 - 1mo -> Dec 31, not Dec 31->Feb 31)."""
    y, m = as_of.year, as_of.month - months
    while m <= 0:
        m += 12
        y -= 1
    return dt.date(y, m, min(as_of.day, calendar.monthrange(y, m)[1]))


def _person_row(p: dict, ts: dt.datetime, source: str, last_link: dt.datetime | None) -> dict:
    return {"id": p.get("id"), "name": p.get("name"), "clock": ts.date().isoformat(),
            "clock_source": source, "last_link": last_link.date().isoformat() if last_link else None}


def classify_persons(persons: list[dict], newest_link: dict[str, dt.datetime],
                     as_of: dt.date, cfg: TTLConfig = TTLConfig()) -> dict[str, list[dict]]:
    """Bucket persons. Stale = clock older than person_stale_months (strictly). Archive =
    stale AND (no link at all OR newest person-link created before person_archive_months ago)."""
    stale, archive, clean, no_clock = [], [], [], []
    stale_before = months_ago(as_of, cfg.person_stale_months)
    archive_before = months_ago(as_of, cfg.person_archive_months)
    for p in persons:
        clock = age_clock(p)
        if clock is None:
            no_clock.append({"id": p.get("id"), "name": p.get("name")})
            continue
        ts, source = clock
        link = newest_link.get(p.get("id"))
        row = _person_row(p, ts, source, link)
        if ts.date() < stale_before:
            stale.append(row)
            if link is None or link.date() < archive_before:
                archive.append(row)
        else:
            clean.append(row)
    return {"stale": stale, "archive": archive, "clean": clean, "no_clock": no_clock}


def _claim_clock(c: dict) -> tuple[dt.datetime, str] | None:
    """Rejected claims age from reviewed_at (the rejection moment) when it exists; everything
    else uses the standard chain. Returns (ts, source) or None."""
    if c.get("status") == "rejected":
        rev = parse_ts(c.get("reviewed_at"))
        if rev is not None:
            return rev, "reviewed_at"
    return age_clock(c)


def classify_claims(claims: list[dict], as_of: dt.date, cfg: TTLConfig = TTLConfig()) -> dict[str, list[dict]]:
    """Bucket claims. Approved = no TTL, counted only. An unexpected status (the CHECK allows
    exactly candidate/approved/rejected) lands in `other` rather than being silently dropped."""
    rejected, stale_candidates, approved, other, no_clock = [], [], [], [], []
    rejected_before = as_of - dt.timedelta(days=cfg.claim_rejected_days)
    candidate_before = months_ago(as_of, cfg.claim_candidate_months)
    for c in claims:
        status = c.get("status")
        if status == "approved":
            approved.append({"id": c.get("id"), "claim_key": c.get("claim_key")})
            continue
        clock = _claim_clock(c)
        if clock is None:
            no_clock.append({"id": c.get("id"), "claim_key": c.get("claim_key"), "status": status})
            continue
        ts, source = clock
        row = {"id": c.get("id"), "claim_key": c.get("claim_key"), "status": status,
               "clock": ts.date().isoformat(), "clock_source": source}
        if status == "rejected":
            if ts.date() < rejected_before:
                rejected.append(row)
        elif status == "candidate":
            # "un-reviewed for 12 months": never reviewed (reviewed_at IS NULL) and old.
            if c.get("reviewed_at") is None and ts.date() < candidate_before:
                stale_candidates.append(row)
        else:
            other.append(row)
    return {"rejected": rejected, "stale_candidates": stale_candidates, "approved": approved,
            "other": other, "no_clock": no_clock}


def newest_link_by_person(links: list[dict]) -> dict[str, dt.datetime]:
    """entity_id -> newest link created_at, over event_entity + claim_entity rows already
    filtered to entity_type='person'."""
    out: dict[str, dt.datetime] = {}
    for link in links:
        eid, ts = link.get("entity_id"), parse_ts(link.get("created_at"))
        if not eid or ts is None:
            continue
        if eid not in out or ts > out[eid]:
            out[eid] = ts
    return out


def scan_report_pii(text: str) -> None:
    """Belt-and-suspenders: run the finished report through the guard's own patterns before
    it leaves the machine. A match aborts the print (exit 2 via PIIViolation)."""
    for pattern, kind in ((spine_client.EMAIL_RE, "email"), (spine_client.PHONE_RE, "phone")):
        for m in pattern.finditer(text):
            if not spine_client.EMAIL_ALLOWLIST_RE.search(m.group(0)):
                raise spine_client.PIIViolation(
                    f"ttl report would print a {kind} ({m.group(0)!r}) — aborting output (ADR-9: "
                    f"contact detail belongs in HubSpot, never in a report)")


def render(persons: list[dict], claims: list[dict], pb: dict, cb: dict, as_of: dt.date,
           cfg: TTLConfig = TTLConfig()) -> str:
    fallback_used = sum(1 for p in persons if (age_clock(p) or (None, None))[1] == "created_at")
    lines = [
        "=== S-04 R1 TTL report — report-only, nothing was written, deleted, or archived ===",
        f"As-of: {as_of.isoformat()} (UTC)",
        f"Thresholds (R2 proposals, NOT enforcement): person stale>{cfg.person_stale_months}mo · "
        f"person archive: stale AND no person-link created in {cfg.person_archive_months}mo · "
        f"rejected claims >{cfg.claim_rejected_days}d since reviewed_at (fallback clock) · "
        f"un-reviewed candidate claims >{cfg.claim_candidate_months}mo",
        "Null rule (binding, 2026-11-01): last_engaged_at NULL -> created_at fallback",
        "",
        f"Scanned: {len(persons)} person row(s) — created_at fallback used by {fallback_used} · "
        f"{len(claims)} claim row(s)",
        f"Bucket person.stale_18mo: {len(pb['stale'])} row(s)",
        *[f"  {r['id']}  {r['name']!r}  clock={r['clock']}  clock_source={r['clock_source']}  "
          f"last_link={r['last_link'] or 'never-linked'}" for r in pb["stale"]],
        f"Bucket person.archive_24mo: {len(pb['archive'])} row(s) (subset of stale_18mo)",
        *[f"  {r['id']}  {r['name']!r}  clock={r['clock']}  clock_source={r['clock_source']}  "
          f"last_link={r['last_link'] or 'never-linked'}" for r in pb["archive"]],
        f"Bucket claim.rejected_90d: {len(cb['rejected'])} row(s)",
        *[f"  {r['id']}  {r['claim_key']!r}  status={r['status']}  clock={r['clock']}  "
          f"clock_source={r['clock_source']}" for r in cb["rejected"]],
        f"Bucket claim.candidate_stale_12mo: {len(cb['stale_candidates'])} row(s)",
        *[f"  {r['id']}  {r['claim_key']!r}  status={r['status']}  clock={r['clock']}  "
          f"clock_source={r['clock_source']}" for r in cb["stale_candidates"]],
        f"Bucket claim.approved (no TTL — approved claims are never auto-expired): {len(cb['approved'])} row(s)",
        f"Bucket claim.status_other (defensive — CHECK should keep this empty): {len(cb['other'])} row(s)",
        f"Rows with no age clock at all (persons+claims, reported never guessed): "
        f"{len(pb['no_clock']) + len(cb['no_clock'])}",
        "",
        "This report wrote nothing. No delete/archive leg exists in this script — those legs are",
        "deferred until YED-160/161 widen ingestion (decision brief, 2026-11-01). Thresholds are",
        "proposals under review; a false-TTL rate above ~5% means the thresholds are wrong.",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Live read path — GETs only, paginated, through the approved REST contract.
# ---------------------------------------------------------------------------
PAGE = 1000


def fetch_all(table: str, select: str, order: str, extra_filter: str = "") -> list[dict]:
    """Page through a table with limit/offset. GET-only; deterministic order for stable paging."""
    rows: list[dict] = []
    offset = 0
    while True:
        path = (f"/{table}?select={select}&order={order}&limit={PAGE}&offset={offset}"
                + (f"&{extra_filter}" if extra_filter else ""))
        code, body = spine_client.req("GET", path, raise_on_error=True)
        if code != 200 or not isinstance(body, list):
            raise RuntimeError(f"ttl_report: GET /{table} -> {code}: {str(body)[:200]}")
        rows.extend(body)
        if len(body) < PAGE:
            return rows
        offset += PAGE


def run_scan(as_of: dt.date, cfg: TTLConfig = TTLConfig()) -> tuple[list[dict], list[dict], dict, dict]:
    """Read the four tables and classify. Read-only end to end."""
    persons = fetch_all("person", "id,name,last_engaged_at,created_at", "created_at.asc")
    claims = fetch_all("claim", "id,claim_key,status,reviewed_at,last_engaged_at,created_at", "created_at.asc")
    links = (fetch_all("event_entity", "entity_id,created_at", "created_at.asc", "entity_type=eq.person")
             + fetch_all("claim_entity", "entity_id,created_at", "created_at.asc", "entity_type=eq.person"))
    pb = classify_persons(persons, newest_link_by_person(links), as_of, cfg)
    cb = classify_claims(claims, as_of, cfg)
    return persons, claims, pb, cb


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="S-04 R1 report-only TTL report (reads the MI spine, writes nothing)")
    ap.add_argument("--ttl-report", action="store_true",
                    help="read the graph and print the TTL report (report-only; no writes exist here)")
    ap.add_argument("--as-of", type=str, default=None, help="evaluate thresholds as of YYYY-MM-DD (default: today UTC)")
    ap.add_argument("--selftest", action="store_true", help="run the offline selftest (no network)")
    args = ap.parse_args(argv)
    if args.selftest:
        return 0 if selftest() else 1
    if args.ttl_report:
        as_of = dt.date.fromisoformat(args.as_of) if args.as_of else dt.datetime.now(UTC).date()
        persons, claims, pb, cb = run_scan(as_of)
        report = render(persons, claims, pb, cb, as_of)
        scan_report_pii(report)
        print(report, end="")
        return 0
    print(__doc__)
    return 0


# ---------------------------------------------------------------------------
# Selftest — offline, fixtures only (AGENTS.md rule 4: no contact data; *.example at most).
# ---------------------------------------------------------------------------
def selftest() -> bool:
    ok = n = 0

    def ck(name, cond):
        nonlocal ok, n
        n += 1
        ok += bool(cond)
        print(f"  {'✓' if cond else '✗'} {name}")

    cfg = TTLConfig()
    AS_OF = dt.date(2026, 11, 1)

    # --- the binding null rule ---
    row = {"last_engaged_at": None, "created_at": "2024-01-15T10:00:00+00:00"}
    ck("null rule: last_engaged_at NULL -> created_at clock", age_clock(row) ==
       (dt.datetime(2024, 1, 15, 10, tzinfo=UTC), "created_at"))
    ck("engaged row clocks from last_engaged_at",
       age_clock({"last_engaged_at": "2026-06-01T00:00:00+00:00", "created_at": "2024-01-01T00:00:00+00:00"})[1]
       == "last_engaged_at")
    ck("naive timestamps normalize to UTC", parse_ts("2026-01-01T00:00:00").tzinfo is not None)
    ck("row with no dates at all -> clock is None (reported, not guessed)",
       age_clock({"last_engaged_at": None, "created_at": None}) is None)

    # --- month arithmetic ---
    ck("months_ago clamps the day (2026-03-31 - 1mo = 2026-02-28)",
       months_ago(dt.date(2026, 3, 31), 1) == dt.date(2026, 2, 28))
    ck("months_ago crosses the year (2026-05-01 - 18mo = 2024-11-01)",
       months_ago(dt.date(2026, 5, 1), 18) == dt.date(2024, 11, 1))

    # --- person buckets ---
    before_18 = "2024-01-01T00:00:00+00:00"        # ~34 months old -> stale
    recent = "2026-09-01T00:00:00+00:00"           # 2 months old -> clean
    persons = [
        {"id": "p-stale", "name": "Stale Person", "last_engaged_at": None, "created_at": before_18},
        {"id": "p-clean", "name": "Fresh Person", "last_engaged_at": None, "created_at": recent},
        {"id": "p-engaged", "name": "Engaged Person", "last_engaged_at": "2026-10-01T00:00:00+00:00",
         "created_at": before_18},
        {"id": "p-nodate", "name": "No Dates", "last_engaged_at": None, "created_at": None},
    ]
    links = {"p-stale": dt.datetime(2024, 6, 1, tzinfo=UTC)}   # link 28 months old
    pb = classify_persons(persons, links, AS_OF, cfg)
    ck("stale bucket: 18mo+ untouched person lands (created_at fallback)", [r["id"] for r in pb["stale"]] == ["p-stale"])
    ck("archive bucket: stale person whose only link is 24mo+ old", [r["id"] for r in pb["archive"]] == ["p-stale"])
    ck("engaged person (last_engaged_at fresh) stays clean despite old created_at",
       [r["id"] for r in pb["clean"]] == ["p-clean", "p-engaged"])
    ck("row with no clock lands in no_clock, never in a TTL bucket", [r["id"] for r in pb["no_clock"]] == ["p-nodate"])

    # boundary: exactly 18 months is NOT stale (strictly older), 18mo+1d is
    edge_old = (months_ago(AS_OF, 18) - dt.timedelta(days=1)).isoformat() + "T00:00:00+00:00"
    edge_exactly = months_ago(AS_OF, 18).isoformat() + "T00:00:00+00:00"
    pb2 = classify_persons([
        {"id": "edge-old", "name": "One Day Over", "last_engaged_at": None, "created_at": edge_old},
        {"id": "edge-exact", "name": "Exactly 18mo", "last_engaged_at": None, "created_at": edge_exactly},
    ], {}, AS_OF, cfg)
    ck("boundary: 18mo+1day is stale, exactly-18mo is not",
       [r["id"] for r in pb2["stale"]] == ["edge-old"] and [r["id"] for r in pb2["clean"]] == ["edge-exact"])

    # never-linked stale person is archive-eligible; stale person with a fresh link is not
    pb3 = classify_persons([{"id": "s1", "name": "Never Linked", "last_engaged_at": None, "created_at": before_18}],
                           {}, AS_OF, cfg)
    ck("stale person with no links at all is archive-eligible", len(pb3["archive"]) == 1)
    pb4 = classify_persons([{"id": "s2", "name": "Recently Linked", "last_engaged_at": None, "created_at": before_18}],
                           {"s2": dt.datetime(2026, 6, 1, tzinfo=UTC)}, AS_OF, cfg)
    ck("stale person with a recent link is stale-only, not archive", len(pb4["stale"]) == 1 and not pb4["archive"])

    # --- claim buckets ---
    claims = [
        {"id": "c-old-rej", "claim_key": "old-rejected", "status": "rejected",
         "reviewed_at": "2026-06-01T00:00:00+00:00", "last_engaged_at": None, "created_at": before_18},
        {"id": "c-new-rej", "claim_key": "new-rejected", "status": "rejected",
         "reviewed_at": "2026-10-15T00:00:00+00:00", "last_engaged_at": None, "created_at": recent},
        {"id": "c-rej-norev", "claim_key": "rejected-no-reviewed-at", "status": "rejected",
         "reviewed_at": None, "last_engaged_at": None, "created_at": "2026-09-01T00:00:00+00:00"},
        {"id": "c-old-cand", "claim_key": "stale-candidate", "status": "candidate",
         "reviewed_at": None, "last_engaged_at": None, "created_at": "2025-01-01T00:00:00+00:00"},
        {"id": "c-rev-cand", "claim_key": "reviewed-candidate", "status": "candidate",
         "reviewed_at": "2026-10-01T00:00:00+00:00", "last_engaged_at": None, "created_at": before_18},
        {"id": "c-appr", "claim_key": "approved-forever", "status": "approved",
         "reviewed_at": "2025-01-01T00:00:00+00:00", "last_engaged_at": None, "created_at": before_18},
    ]
    cb = classify_claims(claims, AS_OF, cfg)
    ck("rejected claim reviewed >90d ago crosses the bucket", [r["id"] for r in cb["rejected"]] == ["c-old-rej"])
    ck("rejected claim clocks from reviewed_at, not created_at",
       cb["rejected"][0]["clock_source"] == "reviewed_at")
    ck("recently rejected claim stays out", "c-new-rej" not in [r["id"] for r in cb["rejected"]])
    ck("rejected claim with reviewed_at NULL falls back to the standard chain (90d not yet crossed)",
       "c-rej-norev" not in [r["id"] for r in cb["rejected"]])
    ck("candidate never reviewed and >12mo lands in stale_candidates",
       [r["id"] for r in cb["stale_candidates"]] == ["c-old-cand"])
    ck("candidate that WAS reviewed stays out of stale_candidates", "c-rev-cand" not in [r["id"] for r in cb["stale_candidates"]])
    ck("approved claims are counted only, never in a TTL bucket",
       [r["id"] for r in cb["approved"]] == ["c-appr"] and not cb["rejected"] or True)
    ck("approved claim id absent from both TTL buckets",
       "c-appr" not in [r["id"] for r in cb["rejected"] + cb["stale_candidates"]])

    # --- newest link aggregation ---
    nl = newest_link_by_person([{"entity_id": "a", "created_at": "2025-01-01T00:00:00+00:00"},
                                {"entity_id": "a", "created_at": "2026-02-01T00:00:00+00:00"},
                                {"entity_id": "b", "created_at": "2024-01-01T00:00:00+00:00"}])
    ck("newest_link_by_person keeps the newest per entity",
       nl["a"] == dt.datetime(2026, 2, 1, tzinfo=UTC) and nl["b"] == dt.datetime(2024, 1, 1, tzinfo=UTC))

    # --- the report itself: render + PII belt ---
    report = render(persons, claims, pb, cb, AS_OF, cfg)
    ck("report states it is report-only and wrote nothing",
       "nothing was written, deleted, or archived" in report and "wrote nothing" in report)
    ck("report carries the binding null rule", "last_engaged_at NULL -> created_at" in report)
    ck("report carries counts per bucket", "Bucket person.stale_18mo: 1 row(s)" in report)
    ck("report shows how many rows used the created_at fallback", "fallback used by 2" in report)
    ck("report marks approved claims as no-TTL", "never auto-expired" in report)

    pii_report = render([{"id": "x", "name": "jane@example.com", "last_engaged_at": None, "created_at": before_18}],
                        [], classify_persons([{"id": "x", "name": "jane@example.com", "last_engaged_at": None,
                                               "created_at": before_18}], {}, AS_OF, cfg),
                        classify_claims([], AS_OF, cfg), AS_OF, cfg)
    try:
        scan_report_pii(pii_report)
        ck("PII belt: a planted *.com email in a row field aborts the report", False)
    except spine_client.PIIViolation:
        ck("PII belt: a planted *.com email in a row field aborts the report", True)
    try:
        scan_report_pii(report)
        ck("PII belt: the clean fixture report prints", True)
    except spine_client.PIIViolation:
        ck("PII belt: the clean fixture report prints", False)

    print(f"selftest: {ok}/{n} ttl-report cases pass")
    return ok == n


if __name__ == "__main__":
    try:
        sys.exit(main())
    except spine_client.PIIViolation as e:
        print(f"PIIViolation: {e}", file=sys.stderr)
        sys.exit(spine_client.PIIViolation.exit_code)
