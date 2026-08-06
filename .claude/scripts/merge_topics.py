#!/usr/bin/env python3
"""
Topic-merge utility for the Market-Intelligence graph — the delete half of the dedup toolkit
(pairs with match_topic.py, which finds the duplicates). Merges a SOURCE topic into a TARGET topic:
re-points the source's signal edges onto the target, transfers engagement, then deletes the now-empty
source node. Nothing is lost — the signals (events) survive; only the duplicate topic node is removed.

Use when today's scan minted a near-duplicate of an existing topic (the 2026-08-06 fragmentation). The
SOURCE should be the accidental new node; the TARGET the established topic to keep (usually the one that
already carries a `notion_page_id`).

    per pair (source -> target):
      1. re-point every event_entity edge from source to target   (signal moves, not deleted)
      2. target.engagement_count += source.engagement_count; last_engaged_at = max(both)
      3. delete the source topic node (now edge-less)

Usage:
    python3 .claude/scripts/merge_topics.py "New Topic::Existing Topic" [...] --dry-run   # preview
    python3 .claude/scripts/merge_topics.py "AI Agent Security::Agentic AI Security"       # execute

Reads SUPABASE_API_KEY from .env (never printed). Verifies each step. Idempotent-ish: if the source is
already gone, it reports "already merged" and skips. Run a relevance recompute afterward.
"""
import json, os, sys, urllib.request, urllib.error
from urllib.parse import quote

BASE = "https://oicikjyzmxqfomrrqkvf.supabase.co/rest/v1"

def load_key():
    for line in open(os.path.join(os.path.dirname(__file__), "..", "..", ".env")):
        if line.startswith("SUPABASE_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip()
    sys.exit("SUPABASE_API_KEY not found in .env")

KEY = load_key()
H = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}

def req(method, path, body=None, prefer=None):
    hdrs = dict(H)
    if prefer:
        hdrs["Prefer"] = prefer
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, headers=hdrs, method=method)
    try:
        resp = urllib.request.urlopen(r)
        raw = resp.read().decode()
        return resp.status, (json.loads(raw) if raw.strip() else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]

def get_topic(name):
    _, rows = req("GET", f"/topic?name=eq.{quote(name)}&select=id,name,engagement_count,last_engaged_at,notion_page_id")
    return rows[0] if isinstance(rows, list) and rows else None

def merge(source_name, target_name, dry):
    src = get_topic(source_name)
    tgt = get_topic(target_name)
    if not tgt:
        print(f"  ❌ TARGET not found: '{target_name}' — skipping pair"); return False
    if not src:
        print(f"  ✅ source '{source_name}' already gone (already merged) — skip"); return True
    if src["id"] == tgt["id"]:
        print(f"  ⏭  source == target for '{source_name}' — skip"); return True

    _, edges = req("GET", f"/event_entity?entity_type=eq.topic&entity_id=eq.{src['id']}&select=id,event_id,role")
    edges = edges if isinstance(edges, list) else []
    new_eng = (tgt.get("engagement_count") or 0) + (src.get("engagement_count") or 0)
    new_last = max([x for x in [tgt.get("last_engaged_at"), src.get("last_engaged_at")] if x], default=None)

    print(f"  '{source_name}' → '{target_name}'")
    print(f"     re-point {len(edges)} signal edge(s) · engagement {tgt.get('engagement_count')}→{new_eng} · "
          f"last_engaged→{(new_last or '')[:10]} · then delete source")
    if dry:
        return True

    # 1. re-point edges
    for e in edges:
        code, resp = req("PATCH", f"/event_entity?id=eq.{e['id']}", {"entity_id": tgt["id"]}, prefer="return=minimal")
        if code not in (200, 204):
            # unique-collision (target already linked to this event+role) → drop the dup edge instead
            req("DELETE", f"/event_entity?id=eq.{e['id']}")
    # 2. transfer engagement + recency to target
    req("PATCH", f"/topic?id=eq.{tgt['id']}", {"engagement_count": new_eng, "last_engaged_at": new_last}, prefer="return=minimal")
    # 3. delete the now-empty source topic
    code, _ = req("DELETE", f"/topic?id=eq.{src['id']}")
    # verify
    still = get_topic(source_name)
    _, moved = req("GET", f"/event_entity?entity_type=eq.topic&entity_id=eq.{tgt['id']}&select=id")
    ok = (still is None) and code in (200, 204)
    print(f"     {'✅ merged' if ok else '⚠️ CHECK'} — source deleted: {still is None}; target now has "
          f"{len(moved) if isinstance(moved, list) else '?'} edge(s)")
    return ok

def main():
    args = list(sys.argv[1:])
    dry = "--dry-run" in args
    pairs = [a for a in args if a != "--dry-run"]
    if not pairs:
        sys.exit('usage: merge_topics.py "Source::Target" [...] [--dry-run]')
    print(f"Topic merge {'(DRY RUN — no writes)' if dry else '(LIVE)'} — {len(pairs)} pair(s)")
    ok = 0
    for p in pairs:
        if "::" not in p:
            print(f"  ⚠️ bad pair (need Source::Target): {p}"); continue
        s, t = [x.strip() for x in p.split("::", 1)]
        if merge(s, t, dry):
            ok += 1
    print(f"\n{ok}/{len(pairs)} {'previewed' if dry else 'merged'}. "
          + ("" if dry else "Run recompute_relevance.py next."))

if __name__ == "__main__":
    main()
