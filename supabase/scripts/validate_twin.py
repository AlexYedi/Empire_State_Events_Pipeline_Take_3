#!/usr/bin/env python3
"""validate_twin.py — AC1a fidelity + integrity checks for the MI staging twin.

AC1a (port fidelity): the carried-forward computed tables must exactly match the
frozen gtm-os spine. We prove it with an order-independent content_hash fingerprint:
  md5( content_hash values, sorted, comma-joined )   computed on BOTH sides.
Also checks FK integrity on the twin and that the signal_read views render.
"""
import os, sys, json, hashlib, subprocess, urllib.request

REPO = "/Users/sameoldexpressions/Documents/GitHub/Empire_State_Events_Pipeline_Take_3"
GTM  = "/Users/sameoldexpressions/Documents/GitHub/gtm-os"
PSQL = "/opt/homebrew/opt/libpq/bin/psql"
TWIN_CONN = ("host=db.ytfzzsxcxxbejnowmkmk.supabase.co port=5432 user=postgres "
             "dbname=postgres sslmode=require connect_timeout=30")

def load_env(path):
    env = {}
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1); env[k] = v.strip().strip('"').strip("'")
    return env

E, GE = load_env(REPO + "/.env"), load_env(GTM + "/.env")
TWIN_PW = E["PHANTOM_TEST_DB_PASSWORD"]
SPINE_BASE = GE.get("SUPABASE_SPINE_URL", "https://abkvgihlbwfloentugtd.supabase.co").rstrip("/")
if not SPINE_BASE.endswith("/rest/v1"): SPINE_BASE += "/rest/v1"
SPINE_KEY = GE.get("SUPABASE_SPINE_SERVICE_KEY") or GE.get("SUPABASE_SPINE_PUBLISHABLE_KEY")

def psql(sql):
    env = dict(os.environ, PGPASSWORD=TWIN_PW)
    p = subprocess.run([PSQL, TWIN_CONN, "-tAc", sql], text=True, capture_output=True, env=env)
    if p.returncode != 0: raise SystemExit(p.stderr)
    return p.stdout.strip()

def spine_col(table, col):
    url = f"{SPINE_BASE}/{table}?select={col}&limit=100000"
    req = urllib.request.Request(url, headers={"apikey": SPINE_KEY,
          "Authorization": f"Bearer {SPINE_KEY}", "Accept-Profile": "signal"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return [row[col] for row in json.load(r)]

ok = True
print("=== AC1a — content_hash fingerprint (twin vs frozen spine) ===")
for t in ["topic_trend", "topic_pair_metric"]:
    spine = sorted(h for h in spine_col(t, "content_hash") if h is not None)
    spine_fp = hashlib.md5(",".join(spine).encode()).hexdigest()
    twin_fp = psql(f"select md5(string_agg(content_hash, ',' order by content_hash)) "
                   f"from topic_intelligence.{t};")
    match = spine_fp == twin_fp
    ok &= match
    print(f"  {t:20s} spine={spine_fp[:16]}  twin={twin_fp[:16]}  -> {'MATCH' if match else 'MISMATCH'}")

print("\n=== FK integrity on twin (expect 0 orphans) ===")
checks = {
    "person.company_id -> company":
      "select count(*) from public.person p left join public.company c on p.company_id=c.id "
      "where p.company_id is not null and c.id is null;",
    "topics.cluster_id -> topic_cluster":
      "select count(*) from topic_intelligence.topics t "
      "left join topic_intelligence.topic_cluster c on t.cluster_id=c.cluster_id "
      "where t.cluster_id is not null and c.cluster_id is null;",
    "event_entity.event_id -> event":
      "select count(*) from public.event_entity ee "
      "left join public.event e on ee.event_id=e.id where e.id is null;",
}
for label, q in checks.items():
    n = psql(q); ok &= (n == "0")
    print(f"  {label:38s} orphans={n}  -> {'OK' if n=='0' else 'FAIL'}")

print("\n=== signal_read views (k>=5 suppression applied in-view) ===")
for v in ["v_topic_movement", "v_topic_intersections"]:
    n = psql(f"select count(*) from signal_read.{v};")
    print(f"  {v:24s} rows surviving suppression = {n}")
# show a couple sample movement rows if any
sample = psql("select theme_name||' | '||window_type||' | ev='||coalesce(event_count::text,'?')||"
              "' | spk='||coalesce(distinct_speaker_count::text,'NULL')||' | '||coalesce(trend_label,'') "
              "from signal_read.v_topic_movement order by event_count desc nulls last limit 5;")
if sample:
    print("  sample v_topic_movement (top by event_count):")
    for line in sample.splitlines(): print("    " + line)

print("\n=== VERDICT:", "PASS ✅" if ok else "FAIL ❌", "===")
sys.exit(0 if ok else 1)
