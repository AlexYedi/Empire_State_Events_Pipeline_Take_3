#!/usr/bin/env python3
"""
carry_forward_canonical.py — copy gtm-os's topic-intelligence into
canonical.topic_intelligence (oicikjyzmxqfomrrqkvf) over REST.

Read source (gtm-signal-spine, schema `signal`) via PostgREST GET; write target
(canonical, schema `topic_intelligence`) via PostgREST POST with the Empire
SUPABASE_API_KEY (service_role). Idempotent (Prefer: resolution=merge-duplicates).
Canonical has no psql access from here, so this is the REST equivalent of load_twin.py.

Requires topic_intelligence to be transiently in canonical's exposed schemas (for the write).
"""
import os, sys, json, urllib.request, urllib.error

REPO = "/Users/sameoldexpressions/Documents/GitHub/Empire_State_Events_Pipeline_Take_3"
GTM  = "/Users/sameoldexpressions/Documents/GitHub/gtm-os"

def load_env(path):
    env = {}
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1); env[k] = v.strip().strip('"').strip("'")
    return env

E, GE = load_env(REPO + "/.env"), load_env(GTM + "/.env")
CANON = "https://oicikjyzmxqfomrrqkvf.supabase.co/rest/v1"
CANON_KEY = E["SUPABASE_API_KEY"]
SPINE = GE.get("SUPABASE_SPINE_URL", "https://abkvgihlbwfloentugtd.supabase.co").rstrip("/")
if not SPINE.endswith("/rest/v1"): SPINE += "/rest/v1"
SPINE_KEY = GE.get("SUPABASE_SPINE_SERVICE_KEY") or GE.get("SUPABASE_SPINE_PUBLISHABLE_KEY")

# FK-safe order: topic_cluster before topics (topics.cluster_id -> topic_cluster).
TABLES = ["topic_cluster", "topics", "topic_trend", "topic_pair_metric"]

def rest_get(base, table, key, profile):
    req = urllib.request.Request(f"{base}/{table}?select=*&limit=100000",
        headers={"apikey": key, "Authorization": f"Bearer {key}", "Accept-Profile": profile})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)

def target_columns(table):
    req = urllib.request.Request(f"{CANON}/",
        headers={"apikey": CANON_KEY, "Authorization": f"Bearer {CANON_KEY}",
                 "Accept-Profile": "topic_intelligence"})
    with urllib.request.urlopen(req, timeout=60) as r:
        spec = json.load(r)
    props = ((spec.get("definitions") or {}).get(table) or {}).get("properties") or {}
    return set(props.keys())

def rest_post(table, rows):
    if not rows:
        return 0
    data = json.dumps(rows).encode()
    req = urllib.request.Request(f"{CANON}/{table}", data=data, method="POST",
        headers={"apikey": CANON_KEY, "Authorization": f"Bearer {CANON_KEY}",
                 "Content-Type": "application/json", "Content-Profile": "topic_intelligence",
                 "Prefer": "resolution=merge-duplicates,return=minimal"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return len(rows)
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"POST {table} failed {e.code}: {e.read().decode()[:600]}\n")
        raise

def main():
    print(f"source spine: {SPINE}  (key set: {bool(SPINE_KEY)})")
    print(f"target canonical: {CANON}\n")
    for t in TABLES:
        src = rest_get(SPINE, t, SPINE_KEY, "signal")
        cols = target_columns(t)
        filtered = [{k: v for k, v in row.items() if k in cols} for row in src]
        n = rest_post(t, filtered)
        print(f"  {t:20s} carried {n:>4} rows")
    print("\ncarry-forward complete.")

if __name__ == "__main__":
    main()
