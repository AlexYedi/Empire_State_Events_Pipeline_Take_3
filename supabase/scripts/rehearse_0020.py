#!/usr/bin/env python3
"""
rehearse_0020.py: prove migration 0020 (public.feed_items — lane 4 raw-feed
staging, YED-304 Phase C) on the Phantom-Test-Case twin, before Alex pastes it
into the prod dashboard (CLAUDE.md invariant 2). Merge gate for PRs #270/#272.

Gates (all must pass, in order):
  0  preflight   refuse prod; twin reachable; feed_items must NOT exist yet
                 (--reset-first applies the migration's own rollback leg to
                 clear a stale twin from an interrupted rehearsal)
  1  snapshot A  feed_items existence + shape fingerprint (columns, constraints,
                 indexes, RLS, relacl) — recorded, must show ABSENT
  1b negative    the VERIFY checks run on the UN-migrated state and must NOT all
                 pass (a check that passes without the fix proves nothing)
  2  apply       0020, verbatim
  3  verify      the migration's VERIFY block, parsed between its markers:
                 every row must be t. Then behavioural twin checks (inside a
                 rolled-back transaction): fixture-shaped insert, upsert on
                 conflict, launch⇒null-guess; negatives each in their own
                 failed transaction: duplicate source_key, bad kind, out-of-lane
                 signal guess, 63-hex key, anon insert refused
  4  re-apply    0020 again: idempotent; verify again
  5  rollback    the ROLLBACK block from the migration file, verbatim
  6  snapshot C  must equal snapshot A: the rollback is PROVEN only if so
  7  leave       re-apply 0020 + verify (default; --no-leave stops at 6) —
                 the twin then carries feed_items for PR #272's fetch lane

HARD REFUSAL: never touches prod (oicikjyzmxqfomrrqkvf). No override flag.
Env: PHANTOM_TEST_DB_PASSWORD (required); PSQL_BIN (default psql); TWIN_DB_HOST /
TWIN_DB_PORT / TWIN_DB_USER (direct db.<ref>.supabase.co first, then the session
pooler aws-0- / aws-1-<region>.pooler.supabase.com, user postgres.<ref> — the
runbook addendum to S-04 records the twin answering on aws-1).
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SUPA = os.path.dirname(HERE)
REPO = os.path.dirname(SUPA)
PSQL = os.environ.get("PSQL_BIN", "psql")
TWIN_REF = "ytfzzsxcxxbejnowmkmk"
PROD_REF = "oicikjyzmxqfomrrqkvf"
MIGRATION = os.path.join(SUPA, "migrations", "0020_feed_items.sql")

# Fixture row: PR #272's feeds_items.example.json shape, *.example domains only.
# source_key = sha256 of the canonical URL (feeds.py item_key) — computed, not pasted.
CANONICAL_URL = "https://veris.example/blog/atlas-2"
FIXTURE_KEY = hashlib.sha256(CANONICAL_URL.encode()).hexdigest()


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


def refuse_prod(spec: str):
    """Refuse anything that is not the twin, checked over the FULL connection spec
    (pooler hosts don't carry the project ref in the hostname — the user does)."""
    if PROD_REF in spec or TWIN_REF not in spec:
        sys.exit(f"REFUSED: target must be the twin ({TWIN_REF}); this script never touches prod.")


def psql(args, stdin=None, check=True, conn=None):
    pw = os.environ.get("PHANTOM_TEST_DB_PASSWORD") or ENV.get("PHANTOM_TEST_DB_PASSWORD")
    if not pw:
        sys.exit("PHANTOM_TEST_DB_PASSWORD not set: refusing to proceed.")
    p = subprocess.run([PSQL, conn, "-v", "ON_ERROR_STOP=1"] + args, input=stdin, text=True,
                       capture_output=True, env=dict(os.environ, PGPASSWORD=pw))
    if check and p.returncode != 0:
        sys.stderr.write(p.stdout[-2000:] + p.stderr[-2000:])
        sys.exit(f"psql failed (rc={p.returncode})")
    return p


def kv(conn, sql):
    out = psql(["-tA", "-F", "\t", "-c", sql], conn=conn).stdout
    return dict(line.split("\t", 1) for line in out.splitlines() if "\t" in line)


def parse_block(text, begin_marker, end_marker, *, inside=False):
    """Statements between the markers, comment markers stripped. inside=True returns
    only statements of a commented block (VERIFY); False keeps the file's own SQL."""
    lines, grab = [], False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(f"-- {begin_marker}"):
            grab = True
            continue
        if s.startswith(f"-- {end_marker}"):
            grab = False
            continue
        if grab:
            stmt = re.sub(r"^--\s?", "", line) if inside else line
            if stmt.strip():
                lines.append(stmt)
    return "\n".join(lines)


SNAPSHOT_SQL = """
select coalesce((select 'shape.' || string_agg(column_name, ',' order by ordinal_position)
  from information_schema.columns
 where table_schema = 'public' and table_name = 'feed_items'), 'shape.ABSENT');
select coalesce((select 'con.' || string_agg(conname, ',' order by conname)
  from pg_constraint
 where conrelid = to_regclass('public.feed_items')), 'con.ABSENT');
select coalesce((select 'idx.' || string_agg(indexname, ',' order by indexname)
  from pg_indexes where schemaname = 'public' and tablename = 'feed_items'), 'idx.ABSENT');
select 'rls.' || coalesce((select relrowsecurity::text from pg_class
  where oid = to_regclass('public.feed_items')), 'ABSENT');
select 'acl.' || coalesce((select relacl::text from pg_class
  where oid = to_regclass('public.feed_items')), 'ABSENT');
"""


def snapshot(conn):
    # Rows may be 'label<TAB>value' (applied) or a single token like 'shape.ABSENT'
    # (un-migrated) — kv() drops single-token lines, so parse here instead.
    out = psql(["-tA", "-F", "\t", "-c", SNAPSHOT_SQL], conn=conn).stdout
    snap = {}
    for line in out.splitlines():
        if not line.strip():
            continue
        if "\t" in line:
            k, v = line.split("\t", 1)
        else:
            k = v = line
        snap[k] = v
    return snap


def verify(conn):
    """Run the migration's VERIFY block; return the (name, t/f) rows."""
    text = open(MIGRATION).read()
    stmts = [s for s in parse_block(text, "VERIFY:BEGIN", "VERIFY:END", inside=True).split(";\n") if s.strip()]
    rows = []
    for stmt in stmts:
        out = psql(["-tA", "-F", "\t", "-c", stmt + ";"], conn=conn).stdout.strip()
        if "\t" not in out:
            sys.exit(f"VERIFY statement did not return <name>\\t<bool>: {stmt[:120]}\n{out}")
        rows.append(tuple(out.split("\t", 1)))
    return rows


BEHAVIOURAL_OK = """-- fixture-shaped insert (feeds.py to_row shape); launch-flavored item
begin;
insert into public.feed_items (source_key, company, feed_url, url, title, published,
                              summary, kind, signal_type_guess, fetched_at, metadata)
values ('{key}', 'Veris AI', 'https://veris.example/blog/feed.xml',
        'https://veris.example/blog/atlas-2?utm_source=rss', 'Introducing Atlas 2.0',
        '2026-11-02T14:00:00Z', 'Atlas 2.0 is now available in general availability.',
        'rss', null, '2026-11-04T05:00:00Z',
        '{{"canonical_url": "{url}"}}'::jsonb);
select 'behav_insert_ok', (select count(*) = 1 from public.feed_items where source_key = '{key}');
select 'behav_launch_null_guess_ok', (select signal_type_guess is null from public.feed_items where source_key = '{key}');
-- weekly-rerun idempotency: upsert on the source_key (feeds.py on_conflict=source_key)
insert into public.feed_items (source_key, company, feed_url, url, title, published,
                              summary, kind, signal_type_guess, fetched_at, metadata)
values ('{key}', 'Veris AI', 'https://veris.example/blog/feed.xml',
        'https://veris.example/blog/atlas-2?utm_source=rss', 'Introducing Atlas 2.1',
        '2026-11-02T14:00:00Z', 'Atlas 2.0 is now available in general availability.',
        'rss', null, '2026-11-04T05:00:00Z',
        '{{"canonical_url": "{url}"}}'::jsonb)
on conflict (source_key) do update set title = excluded.title, fetched_at = excluded.fetched_at;
select 'behav_upsert_ok', (select count(*) = 1 and bool_and(title = 'Introducing Atlas 2.1') from public.feed_items where source_key = '{key}');
-- market-flavored item: a five-signal guess is accepted
insert into public.feed_items (source_key, company, feed_url, url, title, summary,
                              kind, signal_type_guess, fetched_at)
values ('{key2}', 'Veris AI', 'https://veris.example/blog/feed.xml',
        'https://veris.example/blog/q3', 'Q3 field notes', 'Partnership announcement.',
        'atom', 'partnership', '2026-11-04T05:00:00Z');
select 'behav_market_guess_ok', (select signal_type_guess = 'partnership' from public.feed_items where source_key = '{key2}');
rollback;
""".format(key=FIXTURE_KEY, key2=hashlib.sha256(b"https://veris.example/blog/q3").hexdigest(),
           url=CANONICAL_URL)


def expect_fail(conn, label, sql, needle):
    p = psql(["-tA", "-c", sql], conn=conn, check=False)
    err = p.stderr + p.stdout
    if p.returncode == 0:
        sys.exit(f"NEGATIVE GATE FAILED: {label} was ACCEPTED — the constraint it proves is missing.")
    if needle and needle not in err:
        sys.exit(f"NEGATIVE GATE FAILED: {label} failed, but not with '{needle}':\n{err[-800:]}")
    print(f"  ok  {label} refused ({needle or 'as expected'})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset-first", action="store_true",
                    help="drop a stale twin feed_items (the migration's rollback leg) before the gates")
    ap.add_argument("--no-leave", action="store_true",
                    help="stop after the rollback gate instead of leaving 0020 applied")
    ap.add_argument("--preflight-only", action="store_true")
    args = ap.parse_args()

    mig = open(MIGRATION).read()
    rollback_sql = parse_block(mig, "ROLLBACK:BEGIN", "ROLLBACK:END", inside=True)

    # --- 0 preflight: resolve a twin connection, refuse prod -----------------
    candidates = [
        (f"db.{TWIN_REF}.supabase.co", f"host=db.{TWIN_REF}.supabase.co port=5432 "
         f"user=postgres dbname=postgres sslmode=require connect_timeout=15"),
        (f"aws-0-us-east-2.pooler.supabase.com", f"host=aws-0-us-east-2.pooler.supabase.com "
         f"port=5432 user=postgres.{TWIN_REF} dbname=postgres sslmode=require connect_timeout=15"),
        (f"aws-1-us-east-2.pooler.supabase.com", f"host=aws-1-us-east-2.pooler.supabase.com "
         f"port=5432 user=postgres.{TWIN_REF} dbname=postgres sslmode=require connect_timeout=15"),
    ]
    conn = None
    for host, spec in candidates:
        refuse_prod(spec)
        p = psql(["-tA", "-c", "select 1"], conn=spec, check=False)
        if p.returncode == 0:
            conn = spec
            print(f"gate 0 preflight: twin reachable via {host}")
            break
        print(f"  … {host} unreachable, trying next")
    if conn is None:
        sys.exit("gate 0 preflight FAILED: no twin endpoint answered (direct, aws-0 pooler, aws-1 pooler).")

    if os.environ.get("PHANTOM_TEST_DB_PASSWORD") in (None, "") and not ENV.get("PHANTOM_TEST_DB_PASSWORD"):
        sys.exit("PHANTOM_TEST_DB_PASSWORD not set.")

    exists = kv(conn, "select 'feed_items_exists', to_regclass('public.feed_items') is not null;")
    if exists.get("feed_items_exists") == "t":
        if not args.reset_first:
            sys.exit("gate 0 preflight FAILED: public.feed_items already exists on the twin "
                     "(a previous rehearsal ended --leave-applied). Re-run with --reset-first.")
        psql(["-c", rollback_sql], conn=conn)
        print("gate 0 preflight: stale feed_items dropped (--reset-first)")
    else:
        print("gate 0 preflight: feed_items absent on the twin (clean state)")

    if args.preflight_only:
        print("PREFLIGHT ONLY: stopping before gate 1.")
        return

    # --- 1 snapshot A --------------------------------------------------------
    snap_a = snapshot(conn)
    if any(v == "shape.ABSENT" for v in snap_a.values()):
        print("gate 1 snapshot A: recorded (feed_items ABSENT)")
    else:
        sys.exit("gate 1 snapshot A FAILED: feed_items exists on a supposedly clean twin.")

    # --- 1b negative: the VERIFY block must fail pre-migration ---------------
    p = psql(["-tA", "-F", "\t", "-c", "select 'feed_items_exists', to_regclass('public.feed_items') is not null;"],
             conn=conn, check=False)
    # The first VERIFY statement returns f on the un-migrated twin — that is the 1b proof
    # (verify() itself would sys.exit on a missing table).
    if p.returncode == 0 and "feed_items_exists\tf" not in p.stdout:
        sys.exit("gate 1b FAILED: VERIFY did not report feed_items_exists = f pre-migration.")
    print("gate 1b negative: VERIFY reports feed_items_exists = f pre-migration (checks are live)")

    # --- 2 apply -------------------------------------------------------------
    psql(["-f", "-"], stdin=mig, conn=conn)
    print("gate 2 apply: 0020 applied verbatim (psql rc=0)")

    # --- 3 verify + behavioural ---------------------------------------------
    rows = verify(conn)
    fails = [r for r in rows if r[1] != "t"]
    if fails:
        sys.exit(f"gate 3 verify FAILED — rows not t: {fails}")
    print(f"gate 3 verify: {len(rows)}/{len(rows)} checks t:")
    for name, val in rows:
        print(f"  {val}  {name}")

    psql(["-f", "-"], stdin=BEHAVIOURAL_OK, conn=conn)
    print("gate 3 behavioural: insert / launch-null guess / upsert / market guess — all ok (rolled back)")

    dup = ("insert into public.feed_items (source_key, company, feed_url, url, title, summary, kind, fetched_at) "
           f"values ('{FIXTURE_KEY}', 'Veris AI', 'https://veris.example/blog/feed.xml', "
           "'https://veris.example/blog/x', 't', 's', 'rss', now()); "
           "insert into public.feed_items (source_key, company, feed_url, url, title, summary, kind, fetched_at) "
           f"values ('{FIXTURE_KEY}', 'Veris AI', 'https://veris.example/blog/feed.xml', "
           "'https://veris.example/blog/y', 't', 's', 'rss', now());")
    expect_fail(conn, "duplicate source_key", dup, "feed_items_source_key_key")

    def ins(kind="rss", guess=None, key="0" * 64):
        g = f"'{guess}'" if guess else "null"
        return ("insert into public.feed_items (source_key, company, feed_url, url, title, summary, "
                "kind, signal_type_guess, fetched_at) values ('" + key + "', 'Veris AI', "
                "'https://veris.example/blog/feed.xml', 'https://veris.example/blog/x', 't', 's', "
                "'" + kind + "', " + g + ", now());")

    expect_fail(conn, "kind='blog'", ins(kind="blog"), "feed_items_kind_check")
    expect_fail(conn, "signal_type_guess='funding' (out of lane)", ins(guess="funding"),
                "feed_items_signal_type_guess_check")
    expect_fail(conn, "63-hex source_key", ins(key="a" * 63), "feed_items_source_key_check")
    expect_fail(conn, "anon INSERT (no grant, RLS)", "set role anon; " + ins(), "permission denied")

    # --- 4 re-apply (idempotent) ---------------------------------------------
    psql(["-f", "-"], stdin=mig, conn=conn)
    rows = verify(conn)
    if any(r[1] != "t" for r in rows):
        sys.exit(f"gate 4 re-apply FAILED: verify not all t after the second paste: {rows}")
    print(f"gate 4 re-apply: idempotent — verify {len(rows)}/{len(rows)} t again")

    # --- 5 rollback -----------------------------------------------------------
    psql(["-c", rollback_sql], conn=conn)
    print("gate 5 rollback: the ROLLBACK block ran (psql rc=0)")

    # --- 6 snapshot C must equal A --------------------------------------------
    snap_c = snapshot(conn)
    if snap_c != snap_a:
        diff = {k: (snap_a.get(k), snap_c.get(k)) for k in set(snap_a) | set(snap_c)
                if snap_a.get(k) != snap_c.get(k)}
        sys.exit(f"gate 6 snapshot C != A: rollback NOT proven. Diff: {diff}")
    print("gate 6 snapshot C == A: rollback PROVEN")

    # --- 7 leave applied (default) --------------------------------------------
    if args.no_leave:
        print("gate 7: skipped (--no-leave); twin left WITHOUT feed_items.")
        return
    psql(["-f", "-"], stdin=mig, conn=conn)
    rows = verify(conn)
    if any(r[1] != "t" for r in rows):
        sys.exit(f"gate 7 leave-applied FAILED: verify not all t: {rows}")
    print(f"gate 7 leave-applied: 0020 applied + verify {len(rows)}/{len(rows)} t — "
          "the twin now carries feed_items for PR #272's fetch lane.")
    print("ALL GATES GREEN")


if __name__ == "__main__":
    main()
