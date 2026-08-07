#!/usr/bin/env python3
"""
carry_forward_topic_intelligence.py
===================================
MI data-layer consolidation — Increment 1 (YED-130 / ADR-1). CARRY-FORWARD COPY.

Idempotently COPIES the four already-computed topic-intelligence tables from the
FROZEN gtm-os signal spine into the canonical Empire project's `topic_intelligence`
schema, preserving gtm-os's internal PK/FK VALUES so the fidelity test (AC1a) is an
exact-match against the frozen spine.

  source  (READ) : gtm-os spine  abkvgihlbwfloentugtd,  schema `signal`
                   PostgREST GET, header  Accept-Profile: signal
                   env: SUPABASE_SPINE_URL, SUPABASE_SPINE_SERVICE_KEY   (gtm-os/.env)
  target  (WRITE): canonical      oicikjyzmxqfomrrqkvf,  schema `topic_intelligence`
                   PostgREST POST upsert, header  Content-Profile: topic_intelligence
                   env: SUPABASE_URL (or default below), SUPABASE_API_KEY   (Empire/.env)

ADDITIVE ONLY. Writes to `topic_intelligence` exclusively; never touches `public`.

*** RUN ORDER ***
  This script runs AFTER migrations 0001/0002/0003 are applied to the Supabase BRANCH
  of oicikjyzmxqfomrrqkvf (DDL cannot be applied over PostgREST — see supabase/APPLY.md).
  For the PostgREST write path to accept `Content-Profile: topic_intelligence`, that
  schema must be TEMPORARILY in the Data API exposed-schemas list for the duration of the
  load (APPLY.md sequences this; anon stays safe throughout). Alternatively load via psql.

Idempotency: upserts on each table's primary key (Prefer: resolution=merge-duplicates).
Because the payload is the full source row and the target has NO moddatetime trigger
(intentional — 0001 header), re-runs land byte-identical values -> AC1a stays exact.

FK-safe load order: topic_cluster -> topics -> topic_trend -> topic_pair_metric.

Secrets: ALL keys are read from the environment at runtime. Nothing is hardcoded.

Usage:
  python carry_forward_topic_intelligence.py --dry-run   # source counts only, no writes
  python carry_forward_topic_intelligence.py             # perform the carry-forward
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

# Canonical project ref is NOT a secret (it is in committed docs). Used only to derive
# the default target PostgREST base URL when SUPABASE_URL is not set in the environment.
CANONICAL_PROJECT_REF = "oicikjyzmxqfomrrqkvf"
DEFAULT_TARGET_URL = f"https://{CANONICAL_PROJECT_REF}.supabase.co"

SOURCE_SCHEMA = "signal"
TARGET_SCHEMA = "topic_intelligence"

# (table, primary-key column) in FK-safe load order.
TABLES: list[tuple[str, str]] = [
    ("topic_cluster", "cluster_id"),
    ("topics", "topic_id"),
    ("topic_trend", "trend_id"),
    ("topic_pair_metric", "pair_metric_id"),
]

PAGE = 1000          # source read page size
BATCH = 500          # target upsert batch size


def _require_env(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        sys.exit(f"ERROR: required environment variable {name} is not set.")
    return val


def _source_headers(key: str, *, write_profile: bool = False) -> dict:
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Accept-Profile": SOURCE_SCHEMA,
        "Accept": "application/json",
    }


def _target_headers(key: str) -> dict:
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Profile": TARGET_SCHEMA,
        "Content-Type": "application/json",
        # merge-duplicates => upsert on the target PK; missing=default fills omitted cols.
        "Prefer": "resolution=merge-duplicates,return=minimal,missing=default",
    }


def _get(url: str, headers: dict) -> tuple[list, dict]:
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            data = json.loads(body) if body else []
            return data, dict(resp.headers)
    except urllib.error.HTTPError as e:
        sys.exit(f"ERROR GET {url} -> HTTP {e.code}: {e.read().decode('utf-8', 'replace')}")
    except urllib.error.URLError as e:
        sys.exit(f"ERROR GET {url} -> {e.reason}")


def _post(url: str, headers: dict, payload: list) -> None:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            resp.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"ERROR POST {url} -> HTTP {e.code}: {e.read().decode('utf-8', 'replace')}")
    except urllib.error.URLError as e:
        sys.exit(f"ERROR POST {url} -> {e.reason}")


def source_count(base: str, headers: dict, table: str) -> int:
    """Exact row count via PostgREST Content-Range (Prefer: count=exact, HEAD-like GET)."""
    url = f"{base}/rest/v1/{table}?select=*&limit=1"
    h = dict(headers)
    h["Prefer"] = "count=exact"
    h["Range-Unit"] = "items"
    h["Range"] = "0-0"
    _, resp_headers = _get(url, h)
    cr = resp_headers.get("Content-Range", "")  # e.g. "0-0/286"
    if "/" in cr:
        tail = cr.split("/")[-1]
        if tail.isdigit():
            return int(tail)
    return -1


def fetch_all(base: str, headers: dict, table: str, pk: str) -> list[dict]:
    """Page through the whole table, ordered by PK for stable, canonical output."""
    rows: list[dict] = []
    offset = 0
    while True:
        q = urllib.parse.urlencode({"select": "*", "order": pk, "limit": PAGE, "offset": offset})
        page, _ = _get(f"{base}/rest/v1/{table}?{q}", headers)
        if not page:
            break
        rows.extend(page)
        if len(page) < PAGE:
            break
        offset += PAGE
    return rows


def upsert_all(base: str, headers: dict, table: str, rows: list[dict]) -> None:
    for i in range(0, len(rows), BATCH):
        _post(f"{base}/rest/v1/{table}", headers, rows[i : i + BATCH])


def main() -> int:
    ap = argparse.ArgumentParser(description="Carry gtm-os topic-intelligence forward into the canonical project.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Report SOURCE row counts only. No reads of full rows, no writes.")
    args = ap.parse_args()

    # ---- source (gtm-os spine) ----
    src_base = _require_env("SUPABASE_SPINE_URL").rstrip("/")
    src_key = _require_env("SUPABASE_SPINE_SERVICE_KEY")
    src_headers = _source_headers(src_key)

    print(f"SOURCE : {src_base}  (schema `{SOURCE_SCHEMA}`)")

    if args.dry_run:
        print("\n--dry-run: SOURCE counts only (no target connection, no writes)\n")
        total = 0
        for table, _pk in TABLES:
            n = source_count(src_base, src_headers, table)
            total += max(n, 0)
            print(f"  {table:<20} {n:>6} rows")
        print(f"  {'TOTAL':<20} {total:>6} rows")
        print("\nExpected (gtm-os frozen spine): topic_cluster 30 / topics 170 / "
              "topic_trend 96 / topic_pair_metric 286.")
        return 0

    # ---- target (canonical project) ----
    tgt_base = os.environ.get("SUPABASE_URL", DEFAULT_TARGET_URL).rstrip("/")
    tgt_key = _require_env("SUPABASE_API_KEY")
    tgt_headers = _target_headers(tgt_key)

    print(f"TARGET : {tgt_base}  (schema `{TARGET_SCHEMA}`)\n")
    print("Carrying forward in FK-safe order (cluster -> topics -> trend -> pair_metric):\n")

    grand = 0
    for table, pk in TABLES:
        rows = fetch_all(src_base, src_headers, table, pk)
        upsert_all(tgt_base, tgt_headers, table, rows)
        grand += len(rows)
        print(f"  {table:<20} copied {len(rows):>6} rows (upsert on {pk})")

    print(f"\nDone. {grand} rows carried forward. "
          f"Now run the AC1a exact-match validation in supabase/APPLY.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
