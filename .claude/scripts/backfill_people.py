#!/usr/bin/env python3
"""
People backfill — Notion People DB → Market-Intelligence graph `person` table (YED-106 subtask 1 remainder).

Reads parsed People records + a company-resolution map, dedups, resolves each person's `company_id` via the
company's `notion_page_id`, flags unresolved/incomplete names, and BULK-inserts the new `person` rows (one
POST, not 240). Search-before-insert dedup (people share names) on (name, company_id). Idempotent: existing
persons are skipped, so re-runs are safe.

    person fields written: name, title, linkedin_url, email, bio, role_context (comma-joined), company_id,
    notion_page_id, source='notion_backfill', metadata (unresolved_name flag). relevance_score/engagement=0.

Usage:
    python3 .claude/scripts/backfill_people.py --dry-run   # preview: counts, resolution, flagged names
    python3 .claude/scripts/backfill_people.py             # bulk-insert the new persons

Inputs (produced upstream): people_all.json (parsed records), company_map.json (notion_page_id→company_id).
Reads SUPABASE_API_KEY from .env (never printed).
"""
import json, os, re, sys, urllib.request, urllib.error
from urllib.parse import quote

BASE = "https://oicikjyzmxqfomrrqkvf.supabase.co/rest/v1"
SCRATCH = "/private/tmp/claude-501/-Users-sameoldexpressions-Documents-GitHub-Empire-State-Events-Pipeline-Take-3/141aa1f6-c2bf-45a8-8ad8-c0636ed44272/scratchpad"
UNRESOLVED = re.compile(r"\(|unresolved|\bTBC\b|surname|last name|\bTBD\b", re.I)

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
        return e.code, e.read().decode()[:300]

def norm(x):
    return (x or "").replace("-", "").lower().strip()

def main():
    dry = "--dry-run" in sys.argv
    people = json.load(open(os.path.join(SCRATCH, "people_all.json")))
    cmap = json.load(open(os.path.join(SCRATCH, "company_map.json")))
    by_notion = cmap["by_notion_pageid"]

    # name corrections (Alex, on the fly) + names that look flagged but are actually fine
    OVERRIDES = {
        "Udaya (AWS — surname unresolved)": {"name": "Udaya Ghai", "title": "Senior Machine Learning Scientist"},
        "Jack (Insight Partners)": {"name": "Jack Rohrer", "title": "Vice President | Office of AI"},
    }
    FLAG_OK = {"Regan Jayne (Plekenpol)", "Jon Berger (Jonathan P. Berger)"}

    # existing persons (idempotency) — dedup on NAME only (same person appears across event contexts)
    _, existing = req("GET", "/person?select=name&limit=5000")
    existing_names = {e["name"].strip().lower() for e in existing} if isinstance(existing, list) else set()

    by_name, dup_collapsed, no_company = {}, 0, 0
    for p in people:
        orig = (p.get("name") or "").strip()
        if not orig:
            continue
        ov = OVERRIDES.get(orig, {})
        name = ov.get("name", orig)
        title = ov.get("title") or p.get("title") or None
        cid = None
        for pid in (p.get("company_page_ids") or []):
            hit = by_notion.get(norm(pid))
            if hit:
                cid = hit["id"]; break
        if not p.get("company_page_ids"):
            no_company += 1
        k = name.lower()
        if k in existing_names:
            continue
        if k in by_name:
            dup_collapsed += 1
            if not by_name[k]["company_id"] and cid:
                by_name[k]["company_id"] = cid  # backfill company from a later page of the same person
            continue
        unresolved = (orig not in FLAG_OK) and (orig not in OVERRIDES) and bool(UNRESOLVED.search(name))
        by_name[k] = {
            "name": name,
            "title": title,
            "linkedin_url": p.get("linkedin") or None,
            "email": p.get("email") or None,
            "bio": p.get("bio") or None,
            "role_context": ",".join(p.get("role_context") or []) or None,
            "company_id": cid,
            "notion_page_id": p.get("person_page_id") or None,
            "source": "notion_backfill",
            "metadata": {"unresolved_name": True} if unresolved else {},
        }
    to_insert = list(by_name.values())
    flagged = [r["name"] for r in to_insert if r["metadata"].get("unresolved_name")]

    resolved = sum(1 for r in to_insert if r["company_id"])
    print(f"People backfill {'(DRY RUN)' if dry else '(LIVE)'}")
    print(f"  parsed: {len(people)} | to insert: {len(to_insert)} | dup-collapsed (name): {dup_collapsed} "
          f"| company resolved: {resolved}/{len(to_insert)} | no-company rows: {no_company}")
    print(f"  ⚑ unresolved/incomplete names flagged ({len(flagged)}):")
    for n in flagged:
        print(f"      - {n}")

    if not dry and to_insert:
        code, resp = req("POST", "/person", to_insert, prefer="return=minimal")
        if code in (200, 201, 204):
            _, cnt = req("GET", "/person?select=id&limit=1")
            n = req("GET", "/person?select=id", prefer="count=exact")
            print(f"\n  ✅ inserted {len(to_insert)} persons (HTTP {code}).")
        else:
            print(f"\n  ⚠️ bulk insert failed (HTTP {code}): {str(resp)[:200]}")

if __name__ == "__main__":
    main()
