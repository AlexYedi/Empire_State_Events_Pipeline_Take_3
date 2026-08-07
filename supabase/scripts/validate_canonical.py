#!/usr/bin/env python3
"""validate_canonical.py — AC1a fidelity + render checks for canonical, over REST.

AC1a: the carried computed tables must exactly match the frozen gtm spine. Order-independent
content_hash fingerprint (md5 of sorted content_hash) computed on BOTH sides over REST.
"""
import os, sys, json, hashlib, urllib.request

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

def col(base, key, profile, table, c):
    req = urllib.request.Request(f"{base}/{table}?select={c}&limit=100000",
        headers={"apikey": key, "Authorization": f"Bearer {key}", "Accept-Profile": profile})
    with urllib.request.urlopen(req, timeout=120) as r:
        return [row[c] for row in json.load(r)]

def count(base, key, profile, table):
    req = urllib.request.Request(f"{base}/{table}?select=*&limit=1", method="HEAD",
        headers={"apikey": key, "Authorization": f"Bearer {key}", "Accept-Profile": profile,
                 "Prefer": "count=exact", "Range": "0-0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        cr = r.headers.get("content-range", "*/0")
    return int(cr.split("/")[1])

ok = True
print("=== counts on canonical (expect 30 / 170 / 96 / 286) ===")
for t, exp in [("topic_cluster", 30), ("topics", 170), ("topic_trend", 96), ("topic_pair_metric", 286)]:
    n = count(CANON, CANON_KEY, "topic_intelligence", t)
    good = n == exp; ok &= good
    print(f"  {t:20s} {n:>4}  {'OK' if good else f'EXPECTED {exp}'}")

print("\n=== AC1a content_hash fingerprint (canonical vs frozen spine) ===")
for t in ["topic_trend", "topic_pair_metric"]:
    c_fp = hashlib.md5(",".join(sorted(h for h in col(CANON, CANON_KEY, "topic_intelligence", t, "content_hash") if h)).encode()).hexdigest()
    s_fp = hashlib.md5(",".join(sorted(h for h in col(SPINE, SPINE_KEY, "signal", t, "content_hash") if h)).encode()).hexdigest()
    match = c_fp == s_fp; ok &= match
    print(f"  {t:20s} canonical={c_fp[:16]}  spine={s_fp[:16]}  -> {'MATCH' if match else 'MISMATCH'}")

print("\n=== signal_read views render on canonical ===")
for v in ["v_topic_movement", "v_topic_intersections"]:
    n = count(CANON, CANON_KEY, "signal_read", v)
    print(f"  {v:24s} {n} rows (k>=5 surviving)")

print("\n=== VERDICT:", "PASS" if ok else "FAIL", "===")
sys.exit(0 if ok else 1)
