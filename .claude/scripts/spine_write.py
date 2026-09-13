#!/usr/bin/env python3
"""spine_write — CLI front door to the guarded spine write path (ADR-9). Commands and skills call
this instead of hand-rolling curl, so every prose-instructed write passes the same guard.

  python3 .claude/scripts/spine_write.py <table> --json '{"name": "…"}'            # POST one row
  python3 .claude/scripts/spine_write.py <table> --json '[{…},{…}]'                # POST a batch
  python3 .claude/scripts/spine_write.py <table> --patch 'id=eq.<uuid>' --json '{…}' # PATCH by filter
  echo '{…}' | python3 .claude/scripts/spine_write.py <table> --stdin
  add --dry-run to guard + print without writing; --prefer to override the Prefer header
  (default return=representation; use 'resolution=ignore-duplicates,return=minimal' for idempotent inserts).

Exit codes: 0 ok · 2 PIIViolation (nothing written) · 3 HTTP error (status printed).
"""
import argparse, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spine_client as sc


def main() -> int:
    ap = argparse.ArgumentParser(description="guarded write to the MI spine (ADR-9)")
    ap.add_argument("table")
    ap.add_argument("--json", help="row object or array of rows")
    ap.add_argument("--stdin", action="store_true", help="read the JSON body from stdin")
    ap.add_argument("--patch", metavar="FILTER", help="PATCH rows matching this PostgREST filter, e.g. id=eq.<uuid>")
    ap.add_argument("--prefer", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    raw = sys.stdin.read() if a.stdin else a.json
    if not raw:
        ap.error("provide --json or --stdin")
    body = json.loads(raw)
    prefer = a.prefer or ("return=minimal" if a.patch else "return=representation")
    try:
        status, resp = sc.write(a.table, body, prefer=prefer, patch_filter=a.patch, dry_run=a.dry_run)
    except sc.PIIViolation as e:
        print(f"PIIViolation: {e}", file=sys.stderr)
        return 2
    print(json.dumps({"status": status, "response": resp}, indent=1, default=str))
    return 0 if (a.dry_run or (isinstance(status, int) and status < 400)) else 3


if __name__ == "__main__":
    sys.exit(main())
