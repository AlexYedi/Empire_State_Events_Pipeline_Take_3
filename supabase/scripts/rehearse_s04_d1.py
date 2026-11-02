#!/usr/bin/env python3
"""
rehearse_s04_d1.py — prove the S-04 D1 pair on the Phantom-Test-Case twin
before anyone pastes either file into the prod dashboard (CLAUDE.md
invariant 2). Alex approved the sequence 2026-11-01 (YED-183, comment
dd28915c); this script is the rehearsal instrument, not the promotion.

Migrations under rehearsal:
  A. docs/adr/proposals/pii-db-check.sql — the PII Phase-2 DB backstop, as
     fixed in PR #249 (YED-279): populated-column refusal (not column
     existence), catalog-guarded cv2 triggers, spine regexes verbatim.
  B. supabase/migrations/0014_drop_legacy_person_email.sql — drop the legacy,
     empty public.person.email column (PR #252; the backstop's promotion
     prerequisite).

Gates (all must pass, in order):
  0  preflight   twin reachable; public.person shape matches prod (only
                 id+name are NOT NULL without default); the legacy email
                 column is present pre-drop with 0 populated rows (0014's
                 own rehearsal probe — STOP if not 0); canonical_v2.person
                 existence recorded; regex parity vs spine clean
                 (check_pii_regex_parity.py — the byte-for-byte evidence);
                 prod REST counts printed for currency (advisory, read-only)
  1  snapshot A  person-column fingerprint + PII trigger/function fingerprint
                 + row counts (BEFORE)
  2  apply A     pii-db-check.sql, applied verbatim
  3  verify      staging/s04_d1_verify.sql — behavioural: clean spine write
                 passes; email / US-phone / E.164 patterns refused with ADR-9
                 messages; populating the legacy email column refused; the
                 nulling update passes; cv2 triggers exist IFF the table does
  4  re-apply A  a second paste is a clean no-op (idempotency, review
                 finding 1c doctrine)
  5  apply B     0014 — catalog post-condition: no email column on either
                 person table; verify re-run (post-drop leg) passes
  6  rollback    staging/s04_d1_rollback.sql
  7  snapshot C  must EQUAL snapshot A — the rollback is PROVEN only if this
                 holds (fingerprint + counts)
  8  (optional)  --leave-applied: re-apply A then B and verify — leaves the
                 twin in the post-D1 state for Alex's inspection

HARD REFUSAL: this script never touches prod (oicikjyzmxqfomrrqkvf). Prod DDL
is Alex's dashboard paste after this rehearsal is green (CLAUDE.md invariant
2). There is no override flag.

Env (from .env or the environment, never hardcoded):
  PHANTOM_TEST_DB_PASSWORD  the twin's postgres password (required)
  SUPABASE_API_KEY          prod service key — OPTIONAL, preflight currency
                            counts only (read-only REST)
  TWIN_DB_HOST / TWIN_DB_PORT / TWIN_DB_USER
                            connection overrides. Supabase direct db.<ref>
                            connections are IPv6-only on newer setups and
                            GitHub runners can't use them at all — for IPv4
                            point at the session pooler, e.g.
                              TWIN_DB_HOST=aws-0-<region>.pooler.supabase.com
                              TWIN_DB_USER=postgres.<TWIN_REF>
                            (same overrides rehearse_s1a.py accepts;
                             hostname is DASHED, not dotted — and the
                             pooler tenant must exist: a disabled pooler
                             reports "FATAL: (ENOTFOUND) tenant/user
                             <user> not found" from every region).

Usage:
  python supabase/scripts/rehearse_s04_d1.py --preflight-only
  python supabase/scripts/rehearse_s04_d1.py                    # full gate, ends rolled back
  python supabase/scripts/rehearse_s04_d1.py --leave-applied    # full gate, ends applied
  python supabase/scripts/rehearse_s04_d1.py --reset-first      # after an interrupted rehearsal
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SUPA = os.path.dirname(HERE)
REPO = os.path.dirname(SUPA)
PSQL = os.environ.get("PSQL_BIN", "psql")

TWIN_REF = "ytfzzsxcxxbejnowmkmk"
PROD_REF = "oicikjyzmxqfomrrqkvf"

BACKSTOP = os.path.join(REPO, "docs", "adr", "proposals", "pii-db-check.sql")
COLUMN_DROP = os.path.join(SUPA, "migrations", "0014_drop_legacy_person_email.sql")
VERIFY = os.path.join(SUPA, "staging", "s04_d1_verify.sql")
ROLLBACK = os.path.join(SUPA, "staging", "s04_d1_rollback.sql")
PARITY = os.path.join(REPO, ".claude", "scripts", "check_pii_regex_parity.py")

COUNT_TABLES = ["company", "person", "topic", "event", "event_entity"]

TWIN_HOST = os.environ.get("TWIN_DB_HOST", f"db.{TWIN_REF}.supabase.co")
TWIN_PORT = os.environ.get("TWIN_DB_PORT", "5432")
TWIN_USER = os.environ.get("TWIN_DB_USER", "postgres")
TWIN_CONN = (f"host={TWIN_HOST} port={TWIN_PORT} user={TWIN_USER} "
             f"dbname=postgres sslmode=require connect_timeout=30")

# The columns pii-db-check.sql's scan and allowlist assume on public.person.
EXPECTED_PERSON_COLUMNS = {
    "id", "name", "title", "bio", "role_context", "metadata",
    "company_id", "linkedin_url", "notion_page_id", "source",
    "engagement_count", "last_engaged_at", "relevance_score",
    "created_at", "updated_at", "email",
}


def load_env(path):
    env = {}
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k] = v.strip().strip('"').strip("'")
    return env


ENV = load_env(os.path.join(REPO, ".env"))


def refuse_prod():
    if PROD_REF in TWIN_CONN or TWIN_REF not in TWIN_CONN:
        sys.exit(f"REFUSED: target must be the twin ({TWIN_REF}). "
                 f"This script never touches prod. (conn: {TWIN_CONN})")


def psql(args, stdin=None, check=True):
    pw = os.environ.get("PHANTOM_TEST_DB_PASSWORD") or ENV.get("PHANTOM_TEST_DB_PASSWORD")
    if not pw:
        sys.exit("PHANTOM_TEST_DB_PASSWORD not set (.env or environment) — refusing to proceed.")
    env = dict(os.environ, PGPASSWORD=pw)
    p = subprocess.run([PSQL, TWIN_CONN, "-v", "ON_ERROR_STOP=1"] + args,
                       input=stdin, text=True, capture_output=True, env=env)
    if check and p.returncode != 0:
        sys.stderr.write(p.stdout[-2000:] + p.stderr[-2000:])
        sys.exit(f"psql failed (rc={p.returncode}) on {args}")
    return p


def kv(sql):
    out = psql(["-tA", "-F", "\t", "-c", sql]).stdout
    return dict(line.split("\t", 1) for line in out.splitlines() if "\t" in line)


def run_file(path, label):
    p = psql(["-f", path], check=False)
    ok = p.returncode == 0
    print(f"  {'OK ' if ok else 'ERR'} {label}")
    if not ok:
        sys.stderr.write(p.stdout[-3000:] + p.stderr[-3000:])
    return ok, p


# Person-shape fingerprint: columns (order-insensitive), the PII triggers, the
# assert functions, and row counts. Snapshots A and C compare these exactly.
SNAPSHOT_SQL = """
select 'cols', md5(coalesce(string_agg(
         table_schema||'.'||table_name||'.'||column_name||':'||data_type||':'||
         is_nullable||':'||coalesce(column_default,'-'), '|' order by table_schema, table_name, column_name), ''))
  from information_schema.columns
 where (table_schema='public' and table_name='person')
    or (table_schema='canonical_v2' and table_name='person');
select 'triggers', md5(coalesce(string_agg(tgrelid::regclass::text||'.'||tgname, '|'
         order by tgrelid::regclass::text, tgname), ''))
  from pg_trigger
 where not tgisinternal
   and tgname in ('person_no_contact_pii','person_no_pii_columns',
                  'cv2_person_no_contact_pii','cv2_person_no_pii_columns');
select 'functions', md5(coalesce(string_agg(p.oid::regprocedure::text, '|' order by 1), ''))
  from pg_proc p
 where p.pronamespace = 'public'::regnamespace
   and p.proname in ('assert_no_contact_pii','assert_no_pii_columns');
""" + "\n".join(
    f"select 'count.public.{t}', count(*)::text from public.{t};" for t in COUNT_TABLES
) + """
select 'count.canonical_v2.person', case
  when to_regclass('canonical_v2.person') is null then 'absent'
  else (select count(*)::text from canonical_v2.person) end;
select 'email_col.public', (exists (select 1 from information_schema.columns
  where table_schema='public' and table_name='person' and column_name='email'))::text;
select 'email_col.canonical_v2', case
  when to_regclass('canonical_v2.person') is null then 'absent'
  else (select (exists (select 1 from information_schema.columns
         where table_schema='canonical_v2' and table_name='person' and column_name='email'))::text) end;
"""

PREFLIGHT_SQL = """
select 'person.notnull_nodes', coalesce(string_agg(column_name, ',' order by column_name), '')
  from information_schema.columns
 where table_schema='public' and table_name='person'
   and is_nullable='NO' and column_default is null;
select 'person.cols_missing', coalesce(string_agg(c, ',' order by c), '')
  from unnest(ARRAY['""" + "','".join(sorted(EXPECTED_PERSON_COLUMNS)) + """']) as c
 where not exists (select 1 from information_schema.columns
   where table_schema='public' and table_name='person' and column_name=c);
select 'person.email_populated', count(*)::text from public.person where email is not null;
select 'cv2.person_exists', (to_regclass('canonical_v2.person') is not null)::text;
select 'count_tables_missing', coalesce(string_agg(t, ',' order by t), '')
  from unnest(ARRAY['""" + "','".join(COUNT_TABLES) + """']) as t
 where to_regclass('public.'||t) is null;
"""


def prod_counts():
    """Advisory currency check — read-only REST counts on prod. Never required."""
    key = os.environ.get("SUPABASE_API_KEY") or ENV.get("SUPABASE_API_KEY")
    if not key:
        return {}
    out = {}
    for t in COUNT_TABLES:
        req = urllib.request.Request(
            f"https://{PROD_REF}.supabase.co/rest/v1/{t}?select=id",
            headers={"apikey": key, "Authorization": f"Bearer {key}",
                     "Prefer": "count=exact", "Range": "0-0"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                out[t] = r.headers.get("content-range", "?/?").split("/")[-1]
        except Exception as e:  # prod read is advisory only
            out[t] = f"err:{type(e).__name__}"
    return out


def diff(a, b):
    return {k: (a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)}


def snapshot(label):
    s = kv(SNAPSHOT_SQL)
    print(f"  {label}: cols={s.get('cols', '?')[:12]}… triggers={s.get('triggers', '?')[:12]}… "
          f"functions={s.get('functions', '?')[:12]}… email_col={s.get('email_col.public', '?')}/"
          f"{s.get('email_col.canonical_v2', '?')} person={s.get('count.public.person', '?')} "
          f"cv2.person={s.get('count.canonical_v2.person', '?')}")
    return s


def verify(label):
    p = psql(["-f", VERIFY], check=False)
    text = p.stdout + p.stderr
    passed = p.returncode == 0 and "S-04 D1 VERIFY: PASS" in text
    line = next((ln for ln in text.splitlines() if "S-04 D1 VERIFY" in ln or "FAIL:" in ln),
                text.strip()[-300:])
    print(f"  verify({label}) -> {'PASS' if passed else 'FAIL'} :: {line.strip()}")
    return passed, text


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--preflight-only", action="store_true")
    ap.add_argument("--reset-first", action="store_true",
                    help="run staging/s04_d1_rollback.sql before snapshot A "
                         "(after an interrupted rehearsal); every statement is 'if exists'")
    ap.add_argument("--leave-applied", action="store_true",
                    help="after the rollback proof, re-apply both migrations and verify — "
                         "leaves the twin in the post-D1 state")
    ap.add_argument("--skip-parity", action="store_true",
                    help="skip the check_pii_regex_parity.py preflight leg (already CI-enforced)")
    a = ap.parse_args()

    refuse_prod()
    for f in (BACKSTOP, COLUMN_DROP, VERIFY, ROLLBACK):
        if not os.path.exists(f):
            sys.exit(f"missing artifact: {f}")

    print(f"TARGET twin: {TWIN_HOST}:{TWIN_PORT} as {TWIN_USER} (ref {TWIN_REF})")

    if a.reset_first:
        print("\n[-] reset: rolling back any partial S-04 D1 state first")
        if not run_file(ROLLBACK, "s04_d1_rollback.sql (reset)")[0]:
            sys.exit("reset failed")

    print("\n[0] preflight")
    reach = psql(["-tAc", "select 1;"]).stdout.strip()
    if reach != "1":
        sys.exit("twin unreachable (select 1 failed)")
    print("  reachable: OK")

    pf = kv(PREFLIGHT_SQL)
    for k, v in pf.items():
        print(f"  {k:26s} {v}")

    if pf.get("person.cols_missing"):
        sys.exit(f"STOP: public.person is missing expected column(s): {pf['person.cols_missing']} "
                 f"(rehearsal check 1 of pii-db-check.sql: verify live, do not assume)")
    # Probes supply id+name explicitly, so any of these shapes is probe-safe.
    if pf.get("person.notnull_nodes") not in ("", "id", "name", "id,name", "name,id"):
        sys.exit(f"STOP: public.person has unexpected NOT-NULL-no-default columns: "
                 f"{pf['person.notnull_nodes']} — the verify probes would fail; re-clone the twin")
    if pf.get("person.email_populated") != "0":
        sys.exit(f"STOP: person.email has {pf.get('person.email_populated')} populated row(s) — "
                 f"0014's rehearsal probe failed. Re-run the YED-81 export + nulling PATCH "
                 f"(through the guard) before this rehearsal can proceed.")
    print("  legacy email column present and empty: OK (pre-drop leg)")

    if not a.skip_parity:
        p = subprocess.run([sys.executable, PARITY], text=True, capture_output=True)
        if p.returncode != 0:
            sys.stderr.write(p.stdout + p.stderr)
            sys.exit("STOP: PII regex parity drifted — the backstop no longer carries "
                     "spine's regexes byte-for-byte")
        print("  regex parity (spine vs backstop, byte-for-byte): OK")

    pc = prod_counts()
    if pc:
        twin = kv("\n".join(f"select '{t}', count(*)::text from public.{t};" for t in COUNT_TABLES))
        print("  currency (prod REST advisory vs twin):")
        for t in COUNT_TABLES:
            prod_v = pc.get(t, "?")
            twin_v = twin.get(t, "?")
            print(f"    {t:14s} prod={prod_v:>8} twin={twin_v:>8}")
    else:
        print("  currency: skipped (no SUPABASE_API_KEY)")

    if a.preflight_only:
        print("\nPREFLIGHT-ONLY: stopped before snapshot A.")
        return

    print("\n[1] snapshot A (before)")
    snap_a = snapshot("A")

    print("\n[2] apply pii-db-check.sql (the backstop)")
    ok_a, p_a = run_file(BACKSTOP, "pii-db-check.sql")
    if not ok_a:
        sys.exit("backstop apply FAILED — the rehearsal stops here")
    for ln in p_a.stdout.splitlines():
        if "canonical_v2" in ln or "NOTICE" in ln:
            print(f"    {ln.strip()}")

    print("\n[3] behavioural verify (pre-drop leg)")
    if not verify("pre-drop")[0]:
        sys.exit("verify FAILED on the pre-drop leg — a gate does not behave as documented")

    print("\n[4] re-apply pii-db-check.sql (idempotency)")
    if not run_file(BACKSTOP, "pii-db-check.sql (re-apply)")[0]:
        sys.exit("re-apply FAILED — the backstop is not idempotent")
    if not verify("post-reapply")[0]:
        sys.exit("verify FAILED after re-apply")

    print("\n[5] apply 0014_drop_legacy_person_email.sql")
    ok_b, p_b = run_file(COLUMN_DROP, "0014_drop_legacy_person_email.sql")
    if not ok_b:
        sys.exit("column-drop apply FAILED — the rehearsal stops here")
    for ln in p_b.stdout.splitlines():
        if "canonical_v2" in ln or "NOTICE" in ln:
            print(f"    {ln.strip()}")
    post = kv("select 'email_gone', (exists (select 1 from information_schema.columns "
              "where table_schema='public' and table_name='person' "
              "and column_name='email'))::text;")
    if post.get("email_gone") != "false":
        sys.exit("post-condition FAILED: public.person.email still exists after 0014")
    print("  catalog post-condition (email gone on public.person): OK")
    if not verify("post-drop")[0]:
        sys.exit("verify FAILED on the post-drop leg")

    print("\n[6] rollback (staging/s04_d1_rollback.sql)")
    if not run_file(ROLLBACK, "s04_d1_rollback.sql")[0]:
        sys.exit("rollback FAILED")

    print("\n[7] snapshot C (after rollback) — must EQUAL snapshot A")
    snap_c = snapshot("C")
    d = diff(snap_a, snap_c)
    if d:
        for k, (va, vb) in d.items():
            print(f"    DIFF {k}: A={va} C={vb}")
        sys.exit("rollback NOT proven: snapshot C differs from snapshot A")
    print("  snapshot C == snapshot A: rollback PROVEN")

    if a.leave_applied:
        print("\n[8] --leave-applied: re-apply both migrations and verify")
        if not run_file(BACKSTOP, "pii-db-check.sql")[0]:
            sys.exit("re-apply of the backstop failed")
        if not run_file(COLUMN_DROP, "0014_drop_legacy_person_email.sql")[0]:
            sys.exit("re-apply of the column drop failed")
        if not verify("leave-applied")[0]:
            sys.exit("verify FAILED on the leave-applied leg")
        print("  twin left in the post-D1 state (backstop + column drop applied).")

    print("\nS-04 D1 REHEARSAL: ALL GATES GREEN")


if __name__ == "__main__":
    main()
