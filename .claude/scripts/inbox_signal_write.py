#!/usr/bin/env python3
"""
inbox_signal_write.py — the MI-graph writer for inbox-miner (Stage B, Supabase side).

Reads a manifest JSON (a list of resolved+deduped signals from the write gate) and writes each to the
Market-Intelligence graph via PostgREST, idempotently:

  1. upsert `company` (GET by exact name → PATCH engagement, or POST create)   [alias-resolve upstream]
  2. dedup + insert the signal `event` (dedup KEY = canonical_url; GET-before-POST)
  3. link the `event_entity` hyperedge (company as subject)

REST-only, never the Supabase MCP (ADR-0). SUPABASE_API_KEY read from repo-root .env. Additive, never a
gate; a failure on one signal is logged and the run continues. Leaves `relevance_score` at 0 (computed
downstream). Notion Companies + Gmail labels are handled by the caller (parent-thread MCP), not here.

Usage:  python3 inbox_signal_write.py <manifest.json> [--dry]
"""
import json, os, sys, time, urllib.request, urllib.parse, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # ADR-9: the one write path
from spine_client import req, q  # guarded REST client (YED-81)


def upsert_company(name, source):
    st, rows = req("GET", f"/company?name=eq.{q(name)}&select=id,engagement_count")
    if isinstance(rows, list) and rows:
        cid = rows[0]["id"]
        ec = (rows[0].get("engagement_count") or 0) + 1
        req("PATCH", f"/company?id=eq.{q(cid)}",
            {"engagement_count": ec, "last_engaged_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")},
            prefer="return=minimal")
        return cid, "matched"
    st, created = req("POST", "/company",
                      {"name": name, "source": source, "engagement_count": 1,
                       "last_engaged_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")},
                      prefer="return=representation")
    if isinstance(created, list) and created:
        return created[0]["id"], "created"
    return None, f"company-error:{st}:{created}"


def dedup_event(canonical_url, kind):
    # dedup KEY = canonical_url (the v1-cohort finding); merges same event across newsletters.
    st, rows = req("GET", f"/event?url=eq.{q(canonical_url)}&kind=eq.{q(kind)}&select=id")
    if isinstance(rows, list) and rows:
        return rows[0]["id"]
    return None


def write_signal(sig):
    name = sig["company_name"]
    # Dedup FIRST (by canonical_url) — a no-op re-run must not touch the company (no engagement inflation on cron).
    existing = dedup_event(sig["canonical_url"], sig["kind"])
    if existing:
        return {"company": name, "event": sig["title"], "status": "event-exists (deduped)", "event_id": existing}
    cid, cstatus = upsert_company(name, "inbox_miner")
    if not cid:
        return {"company": name, "status": cstatus}
    ev = {
        "title": sig["title"], "kind": sig["kind"], "event_date": sig["event_date"],
        "description": sig["description"], "url": sig["canonical_url"],
        "source": f"inbox_miner:{sig['kind']}", "confidence": sig["confidence"],
        "metadata": sig.get("metadata", {}),
    }
    st, created = req("POST", "/event", ev, prefer="return=representation")
    if not (isinstance(created, list) and created):
        return {"company": name, "event": sig["title"], "status": f"event-error:{st}:{created}"}
    eid = created[0]["id"]
    st2, _ = req("POST", "/event_entity",
                 {"event_id": eid, "entity_type": "company", "entity_id": cid, "role": "subject"},
                 prefer="resolution=ignore-duplicates,return=minimal")
    return {"company": f"{name} ({cstatus})", "event": sig["title"], "status": "WRITTEN",
            "event_id": eid, "edge": st2}


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: inbox_signal_write.py <manifest.json> [--dry]")
    dry = "--dry" in sys.argv
    with open(sys.argv[1]) as f:
        manifest = json.load(f)
    print(f"{'DRY-RUN — ' if dry else ''}{len(manifest)} signals\n" + "-" * 60)
    for sig in manifest:
        if dry:
            print(f"[dry] {sig['company_name']:12} {sig['kind']:10} {sig['title']}")
            continue
        print(json.dumps(write_signal(sig), ensure_ascii=False))


if __name__ == "__main__":
    main()
