#!/usr/bin/env python3
"""
load_twin.py — populate the MI staging twin (ytfzzsxcxxbejnowmkmk, A.Yedi).

Reads source rows over PostgREST and loads them into the twin over psql
(COPY FROM STDIN, TEXT format) so we bypass all REST-write permission issues.

  Group 1  public clone       : canonical mi-canonical-prod (oicikjyzmxqfomrrqkvf) -> twin.public
  Group 2  intelligence carry : gtm-signal-spine (abkvgihlbwfloentugtd, schema signal) -> twin.topic_intelligence

Env (from .env files, never hardcoded):
  this repo/.env : SUPABASE_API_KEY (canonical read), PHANTOM_TEST_DB_PASSWORD (twin psql)
  gtm-os/.env    : SUPABASE_SPINE_URL, SUPABASE_SPINE_SERVICE_KEY (spine read)

Idempotent: TRUNCATE ... CASCADE before each group, then COPY. Safe to re-run.
"""
import os, sys, json, subprocess, urllib.request, urllib.parse

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
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k] = v.strip().strip('"').strip("'")
    return env

E   = load_env(REPO + "/.env")
GE  = load_env(GTM + "/.env")
CANON_BASE = "https://oicikjyzmxqfomrrqkvf.supabase.co/rest/v1"
CANON_KEY  = E["SUPABASE_API_KEY"]
def _spine_base():
    u = GE.get("SUPABASE_SPINE_URL", "https://abkvgihlbwfloentugtd.supabase.co").rstrip("/")
    return u if u.endswith("/rest/v1") else u + "/rest/v1"
SPINE_BASE = _spine_base()
SPINE_KEY  = GE.get("SUPABASE_SPINE_SERVICE_KEY") or GE.get("SUPABASE_SPINE_PUBLISHABLE_KEY")
TWIN_PW    = E["PHANTOM_TEST_DB_PASSWORD"]

# source table -> (rest base, key, accept-profile, target schema)
GROUPS = [
    ("public", None, CANON_BASE, CANON_KEY,
     ["company", "person", "topic", "event", "event_entity"]),
    ("topic_intelligence", "signal", SPINE_BASE, SPINE_KEY,
     ["topic_cluster", "topics", "topic_trend", "topic_pair_metric"]),
]

def rest_get(base, table, key, profile=None):
    url = f"{base}/{table}?select=*&limit=100000"
    req = urllib.request.Request(url, headers={"apikey": key, "Authorization": f"Bearer {key}"})
    if profile:
        req.add_header("Accept-Profile", profile)
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)

def psql(sql_or_stdin, capture=True):
    env = dict(os.environ, PGPASSWORD=TWIN_PW)
    p = subprocess.run([PSQL, TWIN_CONN, "-v", "ON_ERROR_STOP=1", "-q"],
                       input=sql_or_stdin, text=True, capture_output=capture, env=env)
    if p.returncode != 0:
        sys.stderr.write(p.stdout or ""); sys.stderr.write(p.stderr or "")
        raise SystemExit(f"psql failed (rc={p.returncode})")
    return (p.stdout or "")

def target_columns(schema, table):
    """Return [(name, data_type, udt_name)] in ordinal order."""
    out = psql(f"\\pset format unaligned\n\\pset fieldsep '|'\n\\pset tuples_only on\n"
               f"select column_name, data_type, udt_name from information_schema.columns "
               f"where table_schema='{schema}' and table_name='{table}' order by ordinal_position;\n")
    cols = []
    for line in out.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        name, dt, udt = line.split("|")
        cols.append((name, dt, udt))
    return cols

def enc(val, dt, udt):
    """Encode a value for Postgres COPY TEXT format."""
    if val is None:
        return r"\N"
    if dt == "ARRAY":
        items = val if isinstance(val, list) else json.loads(val)
        return "{" + ",".join(str(x) for x in items) + "}"
    if udt in ("json", "jsonb") or isinstance(val, (dict, list)):
        s = json.dumps(val, ensure_ascii=False)
    elif dt == "boolean" or isinstance(val, bool):
        s = "t" if val else "f"
    else:
        s = str(val)
    return (s.replace("\\", "\\\\").replace("\n", "\\n")
             .replace("\r", "\\r").replace("\t", "\\t"))

def copy_into(schema, table, rows):
    cols = target_columns(schema, table)
    if not cols:
        raise SystemExit(f"no target columns for {schema}.{table}")
    names = [c[0] for c in cols]
    src_keys = set(rows[0].keys()) if rows else set()
    use = [c for c in cols if c[0] in src_keys] if rows else cols
    use_names = [c[0] for c in use]
    lines = [f"\\copy {schema}.{table} ({', '.join(use_names)}) FROM STDIN"]
    for row in rows:
        lines.append("\t".join(enc(row.get(n), dt, udt) for (n, dt, udt) in use))
    lines.append("\\.")
    psql("\n".join(lines) + "\n")
    dropped = [n for n in names if n not in use_names]
    return use_names, dropped

def main():
    print(f"twin psql: {TWIN_CONN.split()[0]}")
    print(f"spine base: {SPINE_BASE}  (key set: {bool(SPINE_KEY)})\n")
    summary = []
    for schema, profile, base, key, tables in GROUPS:
        print(f"### group -> {schema}")
        psql(f"TRUNCATE {', '.join(schema + '.' + t for t in tables)} CASCADE;\n")
        for t in tables:
            rows = rest_get(base, t, key, profile)
            use, dropped = copy_into(schema, t, rows)
            note = f"  (dropped cols not in target: {dropped})" if dropped else ""
            print(f"  {schema}.{t:18s} loaded {len(rows):>4} rows{note}")
            summary.append((f"{schema}.{t}", len(rows)))
        print()
    print("=== loaded counts ===")
    for name, n in summary:
        print(f"  {name:38s} {n}")

if __name__ == "__main__":
    main()
