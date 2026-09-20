#!/usr/bin/env python3
"""cold_export.py — read-only JSON export of the MI graph before any prod DDL.

Spec: docs/migration-playbook.md ("measure before; keep a cold copy") + the knowledge-substrate
review finding 1 fix step 1. READ-ONLY (GETs through spine_client.req). Writes OUTSIDE the repo by
default — `person` rows name people and the repo is public (project_public_repos_private_data).

    .venv/bin/python supabase/scripts/cold_export.py [--out ~/Documents/esep-exports/<date>]
"""
import argparse, datetime as dt, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", ".claude", "scripts"))
from spine_client import req  # noqa: E402

TABLES = ["company", "person", "topic", "event", "event_entity", "documents", "doc_claims"]
PAGE = 1000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.expanduser(f"~/Documents/esep-exports/{dt.date.today().isoformat()}"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for t in TABLES:
        rows, off = [], 0
        while True:
            st, body = req("GET", f"/{t}?select=*&order=id&limit={PAGE}&offset={off}")
            if st != 200:
                sys.exit(f"export failed on {t}: {st} {str(body)[:200]}")
            rows += body
            if len(body) < PAGE:
                break
            off += PAGE
        with open(os.path.join(a.out, f"{t}.json"), "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False)
        print(f"  {t:14s} {len(rows):>6} rows")
    print(f"cold export -> {a.out}  (outside the repo; contains names — do not commit)")


if __name__ == "__main__":
    main()
