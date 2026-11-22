#!/usr/bin/env python3
"""YED-484 one-off: relabel the companies lane 1's first live run created with substrate's default
source ('substrate:notion') to 'ats_pulse'. DRY RUN by default; --apply writes. Alex runs it.

Run 44968840303 (2026-11-22, write step 00:54:00-00:54:38Z) logged "5 companies created". Selection,
all read-only GETs through spine_client.req:
  1. hiring_pulse events (signal_type hiring_pulse, source ats_pulse) -> their company edges
  2. those companies whose source is still 'substrate:notion' AND created inside the run window
     (default 2026-11-22T00:54:00Z..00:55:00Z) — a company lane 1 matched (older, any source) is
     never touched.
--apply PATCHes source only, one row at a time, through spine_client.write (the guarded path),
with source=eq.substrate:notion in the filter, so a re-run or a row relabelled meanwhile is a no-op.
Prints counts and row ids only, never company names (the target registry is private)."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spine_client  # noqa: E402

OLD, NEW = "substrate:notion", "ats_pulse"


def get(path: str) -> list:
    st, body = spine_client.req("GET", path)
    if st != 200:
        sys.exit(f"GET failed: HTTP {st}")       # status only — a body can echo a name
    return body or []


def targets(since: str, until: str) -> list[dict]:
    events = get("/event?signal_type=eq.hiring_pulse&source=eq.ats_pulse&select=id&limit=10000")
    if not events:
        return []
    ids = ",".join(e["id"] for e in events)
    edges = get(f"/event_entity?event_id=in.({ids})&entity_type=eq.company&select=entity_id&limit=10000")
    cids = sorted({e["entity_id"] for e in edges})
    if not cids:
        return []
    rows = get(f"/company?id=in.({','.join(cids)})&source=eq.{spine_client.q(OLD)}"
               f"&created_at=gte.{since}&created_at=lt.{until}&select=id,source,created_at&order=created_at")
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--apply", action="store_true", help="write the relabel (default: dry run)")
    ap.add_argument("--since", default="2026-11-22T00:54:00Z", help="run window start (created_at >=)")
    ap.add_argument("--until", default="2026-11-22T00:55:00Z", help="run window end (created_at <)")
    a = ap.parse_args(argv)
    rows = targets(a.since, a.until)
    print(f"{len(rows)} lane-1 compan{'y' if len(rows) == 1 else 'ies'} with source {OLD!r} created "
          f"{a.since}..{a.until} (ids only):")
    for r in rows:
        print(f"  {r['id']}  created {r['created_at']}")
    flt = lambda r: f"id=eq.{r['id']}&source=eq.{spine_client.q(OLD)}"  # noqa: E731
    if not a.apply:
        for r in rows:                                # the guard checks every payload, nothing is sent
            spine_client.write("company", {"source": NEW}, patch_filter=flt(r), dry_run=True)
        print(f"dry run: {len(rows)} PATCH(es) to source {NEW!r} pass the guard; nothing written. "
              "Re-run with --apply to write.")
        return 0
    done = 0
    for r in rows:
        st, _ = spine_client.write("company", {"source": NEW}, patch_filter=flt(r), prefer="return=minimal")
        if st not in (200, 204):
            print(f"PATCH failed for {r['id']}: HTTP {st} — {done} relabelled before it")
            return 1
        done += 1
    print(f"relabelled {done} compan{'y' if done == 1 else 'ies'} to source {NEW!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
