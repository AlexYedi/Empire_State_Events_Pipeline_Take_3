#!/usr/bin/env python3
"""
rehearse_0021.py: prove migration 0021 (re-describe the company_signals lane: schedule +
kill_rule text on ONE public.lane_registry row, YED-349) on the Phantom-Test-Case twin,
before Alex pastes it into the prod dashboard (CLAUDE.md invariant 2).

Gates (all must pass, in order):
  0  preflight   refuse prod; twin reachable; the six original lanes present; company_signals
                 carries the 0016 seed text (else: --reset-first). Records, without acting on,
                 whether 0020 (feed_items) or 0022 (extra lanes) objects are on the twin.
  1  snapshot A  fingerprint: lane_registry rows (md5 of every row) + relacl + RLS, lane_run
                 count, public-schema catalog (columns, constraints, relations+ACL, policies)
  1b negative    VERIFY on the UN-migrated twin: the two value checks
                 (company_signals_schedule, company_signals_kill_rule) must be FALSE and every
                 keep-style check TRUE (a check that passes without the fix proves nothing)
  2  apply       0021, verbatim; then VERIFY: every row t
  3  re-apply    0021 again: snapshot identical to after step 2; VERIFY all t
  4  faults      plant each fault, VERIFY must flag its named check, fix it, the snapshot must
                 equal the post-apply snapshot and VERIFY must be all t again
  5  rollback    the migration's ROLLBACK block, verbatim
  6  snapshot C  must EQUAL snapshot A: the rollback is PROVEN only if so
  The twin is left in its pre-0021 state (no --leave-applied: prod has not taken 0021 yet).

HARD REFUSAL: this script only ever connects to the twin's session pooler, as the twin's tenant
user, with the twin's password. Host and user are constants (no env overrides) and are checked
before every connection. psql child processes get an environment scrubbed of every variable
that names or holds prod material. There is no override flag.

Default is a dry run: print the plan from the migration file and exit, with NO connection.

Usage:
  python supabase/scripts/rehearse_0021.py                    # dry run: plan only, no connection
  python supabase/scripts/rehearse_0021.py --preflight-only   # connect, preflight, stop
  python supabase/scripts/rehearse_0021.py --execute          # full gate, ends rolled back
  python supabase/scripts/rehearse_0021.py --execute --reset-first   # after an interrupted run

Env: PHANTOM_TEST_DB_PASSWORD (from .env or the environment; never printed). PSQL_BIN optional.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SUPA = os.path.dirname(HERE)
REPO = os.path.dirname(SUPA)
PSQL = os.environ.get("PSQL_BIN", "/opt/homebrew/opt/libpq/bin/psql")

TWIN_REF = "ytfzzsxcxxbejnowmkmk"
PROD_REF = "oicikjyzmxqfomrrqkvf"
TWIN_HOST = "aws-1-us-east-2.pooler.supabase.com"
TWIN_USER = f"postgres.{TWIN_REF}"
TWIN_CONN = (f"host={TWIN_HOST} port=5432 user={TWIN_USER} dbname=postgres "
             "sslmode=require connect_timeout=30")
PROD_SECRET_KEYS = {"MARKET_INTEL_SUPABASE_DB_PASSWORD", "SUPABASE_API_KEY", "MI_SUPABASE_URL",
                    "MI_SUPABASE_ANON_KEY", "MI_DB_DSN", "DATABASE_URL", "PGHOST", "PGUSER",
                    "PGSERVICE", "PGPASSFILE"}

MIGRATION = os.path.join(SUPA, "migrations", "0021_lane_registry_company_signals.sql")
ORIGINAL_SIX = ("corpus_mine", "hiring_pulse", "company_signals", "research_frontier", "feeds",
                "segment_enrichment")
# 0016 seed text for company_signals (what 0021's ROLLBACK restores).
SEED_SCHEDULE = "weekly, Monday session (akta MCP); credit cap per run"
SEED_KILL_RULE = ("over the credit cap Alex set -> pause; <60% watchlist coverage at 90 days -> "
                  "widen sources before widening the list")
VALUE_CHECKS = ["company_signals_schedule", "company_signals_kill_rule"]

FAULTS = [
    ("4a", "update public.lane_registry set active = true where lane = 'company_signals';",
     "company_signals_still_inactive",
     "update public.lane_registry set active = false where lane = 'company_signals';"),
    ("4b", "grant select on public.lane_registry to anon;",
     "registry_no_api_grants",
     "revoke select on public.lane_registry from anon;"),
]

SIX = ",".join(f"'{l}'" for l in ORIGINAL_SIX)
PREFLIGHT_SQL = f"""
select 'six_present', (count(*) = 6)::text from public.lane_registry where lane in ({SIX});
select 'registry_rows', count(*)::text from public.lane_registry;
select 'extra_lanes', coalesce(string_agg(lane, ',' order by lane), '-') from public.lane_registry
 where lane not in ({SIX});
select 'cs_seed_schedule', (schedule = $s${SEED_SCHEDULE}$s$)::text from public.lane_registry
 where lane = 'company_signals';
select 'cs_seed_kill_rule', (kill_rule = $s${SEED_KILL_RULE}$s$)::text from public.lane_registry
 where lane = 'company_signals';
select 'cs_active', active::text from public.lane_registry where lane = 'company_signals';
select 'active_lanes', coalesce(string_agg(lane, ',' order by lane), '-') from public.lane_registry
 where active;
select 'has_0020_feed_items', (to_regclass('public.feed_items') is not null)::text;
select 'lane_run_rows', count(*)::text from public.lane_run;
"""

SNAPSHOT_SQL = """
select 'lane_registry.rows', md5(coalesce(string_agg(row_to_json(l)::text, '|' order by lane), ''))
  from public.lane_registry l;
select 'lane_registry.count', count(*)::text from public.lane_registry;
select 'lane_registry.acl_rls', coalesce(relacl::text, '-') || ' rls=' || relrowsecurity::text
  from pg_class where oid = 'public.lane_registry'::regclass;
select 'lane_run.count', count(*)::text from public.lane_run;
select 'public.cols', md5(coalesce(string_agg(table_name||'.'||column_name||':'||data_type||':'||
         is_nullable||':'||coalesce(column_default,''), '|' order by table_name, column_name), ''))
  from information_schema.columns where table_schema = 'public';
select 'public.constraints', md5(coalesce(string_agg(conrelid::regclass::text||'.'||conname||':'||
         pg_get_constraintdef(oid), '|' order by conrelid::regclass::text, conname), ''))
  from pg_constraint where connamespace = 'public'::regnamespace;
select 'public.relations', md5(coalesce(string_agg(c.relname||':'||c.relkind::text||':'||
         c.relrowsecurity::text||':'||coalesce(c.relacl::text,''), '|' order by c.relname), ''))
  from pg_class c where c.relnamespace = 'public'::regnamespace and c.relkind in ('r','v','m','p');
select 'public.policies', md5(coalesce(string_agg(tablename||'.'||policyname, '|' order by 1), ''))
  from pg_policies where schemaname = 'public';
"""


# ----------------------------------------------------------------------------- file parsing
def read_migration() -> str:
    with open(MIGRATION, encoding="utf-8") as fh:
        return fh.read()


def commented_block(src: str, tag: str) -> str:
    m = re.search(rf"^-- {tag}:BEGIN\n(.*?)^-- {tag}:END", src, re.S | re.M)
    if not m:
        sys.exit(f"migration has no -- {tag}:BEGIN/END block")
    return "\n".join(line[3:] if line.startswith("-- ") else line.lstrip("-")
                     for line in m.group(1).splitlines())


def verify_names(sql: str) -> list[str]:
    return re.findall(r"^select '([a-z0-9_]+)'", sql, re.M)


# ----------------------------------------------------------------------------- env + psql
def load_env(path: str) -> dict:
    env = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


ENV = load_env(os.path.join(REPO, ".env"))


def refuse_non_twin(conninfo: str = TWIN_CONN) -> None:
    host = re.search(r"\bhost=(\S+)", conninfo)
    user = re.search(r"\buser=(\S+)", conninfo)
    if (PROD_REF in conninfo or not host or host.group(1) != TWIN_HOST
            or not user or user.group(1) != TWIN_USER):
        sys.exit(f"REFUSED: target must be the twin pooler {TWIN_HOST} as {TWIN_USER}. "
                 "This script never touches prod.")


def twin_password() -> str:
    pw = ENV.get("PHANTOM_TEST_DB_PASSWORD") or os.environ.get("PHANTOM_TEST_DB_PASSWORD")
    if not pw:
        sys.exit("PHANTOM_TEST_DB_PASSWORD not set (.env). Is .env symlinked into this worktree?")
    prod_pw = ENV.get("MARKET_INTEL_SUPABASE_DB_PASSWORD") or os.environ.get("MARKET_INTEL_SUPABASE_DB_PASSWORD")
    if prod_pw and pw == prod_pw:
        sys.exit("REFUSED: the twin password equals the prod password; refusing to guess which DB this is.")
    return pw


def child_env() -> dict:
    """os.environ minus anything that names or holds prod material, plus the twin password."""
    env = {k: v for k, v in os.environ.items()
           if k not in PROD_SECRET_KEYS and PROD_REF not in v}
    env.pop("PGOPTIONS", None)
    env.update(PGPASSWORD=twin_password())
    return env


def psql(args: list[str], stdin: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    refuse_non_twin()
    p = subprocess.run([PSQL, TWIN_CONN, "-X", "-v", "ON_ERROR_STOP=1"] + args,
                       input=stdin, text=True, capture_output=True, env=child_env())
    if check and p.returncode != 0:
        sys.stderr.write(p.stderr[-1500:])
        sys.exit(f"psql failed (rc={p.returncode})")
    return p


def kv(sql: str) -> dict:
    out = psql(["-tA", "-F", "\t"], stdin=sql).stdout
    return dict(line.split("\t", 1) for line in out.splitlines() if "\t" in line)


def run_sql(sql: str, label: str) -> bool:
    p = psql([], stdin=sql, check=False)
    ok = p.returncode == 0
    print(f"  {'OK ' if ok else 'ERR'} {label}")
    if not ok:
        print("      " + (p.stderr.strip().splitlines() or ["?"])[-1])
    return ok


def apply(label: str) -> bool:
    refuse_non_twin()
    p = subprocess.run([PSQL, TWIN_CONN, "-X", "-q", "-v", "ON_ERROR_STOP=1", "-f", MIGRATION],
                       text=True, capture_output=True, env=child_env())
    ok = p.returncode == 0
    print(f"  {'OK ' if ok else 'ERR'} {label}")
    if not ok:
        print("      " + (p.stderr.strip().splitlines() or ["?"])[-1])
    return ok


def run_verify(verify_sql: str, expected: list[str]) -> dict:
    """VERIFY in a read-only session. Returns {check: 't'|'f'|<missing>}; prints every row."""
    p = psql(["-tA", "-F", "\t"], stdin="set session characteristics as transaction read only;\n"
             + verify_sql, check=False)
    got = dict(line.split("\t", 1) for line in p.stdout.splitlines() if "\t" in line)
    if p.returncode != 0:
        print("      psql error: " + (p.stderr.strip().splitlines() or ["?"])[-1])
    rows = {n: got.get(n, "<missing>") for n in expected}
    print("    " + "  ".join(f"{n}={v}" for n, v in rows.items()))
    return rows


def all_t(rows: dict, label: str) -> bool:
    bad = [n for n, v in rows.items() if v != "t"]
    print(f"  VERIFY({label}) -> {'PASS' if not bad else 'FAIL'} "
          f"({len(rows) - len(bad)}/{len(rows)} t)" + (f" :: not t: {bad}" if bad else ""))
    return not bad


def diff(a: dict, b: dict) -> dict:
    return {k: (a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)}


def show_diff(d: dict) -> None:
    for k, (x, y) in d.items():
        print(f"    DIFF {k}: before={x} after={y}")


# ----------------------------------------------------------------------------- plan
def plan(src: str, verify_sql: str, rollback_sql: str) -> None:
    sha = hashlib.sha256(src.encode()).hexdigest()[:16]
    names = verify_names(verify_sql)
    print("rehearse_0021 — DRY RUN (no connection made)\n")
    print(f"  target           twin {TWIN_REF} via {TWIN_HOST} as {TWIN_USER} (hard-coded; prod refused)")
    print(f"  migration        {os.path.relpath(MIGRATION, REPO)}  sha256:{sha}…  {len(src.splitlines())} lines")
    print(f"  verify checks    {len(names)}: {', '.join(names)}")
    print(f"  value checks     must be f before apply: {', '.join(VALUE_CHECKS)}; all others t")
    print(f"  rollback stmts   {len([l for l in rollback_sql.splitlines() if l.strip()])} lines")
    print("  planted faults   " + "; ".join(f"{s} `{f}` -> must flag {n}" for s, f, n, _ in FAULTS))
    print("\n  steps: 0 preflight · 1 snapshot A · 1b negative control · 2 apply + verify · "
          "3 re-apply idempotent · 4 planted faults + fix · 5 rollback · 6 snapshot C == A")
    print("\n  run with --execute to perform it (twin only).")


# ----------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description="Rehearse migration 0021 on the twin.")
    ap.add_argument("--dry-run", action="store_true", help="print the plan only (default)")
    ap.add_argument("--execute", action="store_true", help="run the full gate against the twin")
    ap.add_argument("--preflight-only", action="store_true", help="connect, run preflight, stop")
    ap.add_argument("--reset-first", action="store_true",
                    help="run the ROLLBACK block before preflight (twin left with 0021 applied); idempotent")
    a = ap.parse_args()

    src = read_migration()
    verify_sql = commented_block(src, "VERIFY")
    rollback_sql = commented_block(src, "ROLLBACK")
    expected = verify_names(verify_sql)
    if not expected:
        sys.exit("VERIFY block parsed to zero checks")
    for _, _, name, _ in FAULTS:
        if name not in expected:
            sys.exit(f"fault target {name} is not a VERIFY check in the migration")

    if not (a.execute or a.preflight_only) or a.dry_run:
        plan(src, verify_sql, rollback_sql)
        return 0

    refuse_non_twin()
    print(f"TARGET twin: {TWIN_HOST} as {TWIN_USER}  at "
          f"{dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    print(f"migration sha256:{hashlib.sha256(src.encode()).hexdigest()[:16]}…")
    if a.reset_first:
        print("\n[-] reset: running the ROLLBACK block first")
        if not run_sql(rollback_sql, "rollback (reset)"):
            sys.exit("reset failed")

    print("\n[0] preflight")
    ver = psql(["-tA", "-c", "show server_version"]).stdout.strip()
    print(f"  {'server_version':22s} {ver} (prod 17.6)")
    pf = kv(PREFLIGHT_SQL)
    for k, v in pf.items():
        print(f"  {k:22s} {v}")
    if pf.get("six_present") != "true":
        sys.exit("PREFLIGHT FAIL — the six original lanes are not all on the twin; reload it first")
    if pf.get("cs_seed_schedule") != "true" or pf.get("cs_seed_kill_rule") != "true":
        sys.exit("PREFLIGHT FAIL — company_signals does not carry the 0016 seed text; re-run with --reset-first")
    print("  NOTE 0020 (feed_items) on twin: " + ("yes" if pf.get("has_0020_feed_items") == "true" else
          "no (independent of 0021; not applied here)"))
    if a.preflight_only:
        return 0

    gates: list[tuple[str, bool]] = []

    print("\n[1] snapshot A (before)")
    snap_a = kv(SNAPSHOT_SQL)
    for k, v in snap_a.items():
        print(f"  {k:22s} {v}")

    print("\n[1b] negative control: VERIFY on the un-migrated twin")
    rows = run_verify(verify_sql, expected)
    vals_f = all(rows[n] == "f" for n in VALUE_CHECKS)
    keep_t = all(v == "t" for n, v in rows.items() if n not in VALUE_CHECKS)
    ok = vals_f and keep_t
    print(f"  value checks f: {vals_f}; keep-style checks t: {keep_t} -> "
          f"{'PASS (the checks discriminate)' if ok else 'FAIL'}")
    gates.append(("1b negative control", ok))
    if not ok:
        sys.exit("GATE FAIL at step 1b")

    print("\n[2] apply 0021")
    ok = apply("0021_lane_registry_company_signals.sql") and all_t(run_verify(verify_sql, expected), "post-apply")
    gates.append(("2 apply + verify", ok))
    if not ok:
        sys.exit("GATE FAIL at step 2")
    snap_b = kv(SNAPSHOT_SQL)
    print(f"  lane_registry.rows after apply: {snap_b.get('lane_registry.rows')}")

    print("\n[3] re-apply 0021 (idempotency)")
    ok = apply("0021 second paste")
    d = diff(snap_b, kv(SNAPSHOT_SQL))
    if d:
        show_diff(d)
    print(f"  snapshot after re-apply == after apply: {not d}")
    ok = ok and not d and all_t(run_verify(verify_sql, expected), "post-reapply")
    gates.append(("3 re-apply idempotent", ok))
    if not ok:
        sys.exit("GATE FAIL at step 3")

    print("\n[4] planted faults: VERIFY must flag each one; the fix must restore the applied state")
    for step, fault_sql, must_fail, fix_sql in FAULTS:
        print(f"  [{step}] plant: {fault_sql}")
        psql([], stdin=fault_sql)
        rows = run_verify(verify_sql, expected)
        flagged = [n for n, v in rows.items() if v != "t"]
        caught = rows.get(must_fail) == "f"
        print(f"  flagged: {flagged} -> {must_fail} {'caught' if caught else 'NOT caught'}")
        print(f"  [{step}] fix:   {fix_sql}")
        psql([], stdin=fix_sql)
        d = diff(snap_b, kv(SNAPSHOT_SQL))
        if d:
            show_diff(d)
        restored = not d and all_t(run_verify(verify_sql, expected), f"after fix {step}")
        print(f"  snapshot after fix == applied state: {not d}")
        gates.append((f"{step} fault -> {must_fail}", caught and restored))
        if not (caught and restored):
            sys.exit(f"GATE FAIL at step {step}")

    print("\n[5] rollback (the migration's ROLLBACK block, verbatim)")
    ok = run_sql(rollback_sql, "ROLLBACK block")
    gates.append(("5 rollback runs", ok))
    if not ok:
        sys.exit("GATE FAIL at step 5")

    print("\n[6] snapshot C (after rollback): must EQUAL snapshot A")
    d = diff(snap_a, kv(SNAPSHOT_SQL))
    if d:
        show_diff(d)
    print(f"  snapshot C == snapshot A: {'ROLLBACK PROVEN' if not d else 'MISMATCH'}")
    gates.append(("6 snapshot C == A", not d))
    if d:
        sys.exit("GATE FAIL at step 6")

    print("\n[7] cleanup: twin left in its pre-0021 state (snapshot A); no re-apply")
    print("\ngates: " + "  ".join(f"{n}={'PASS' if ok else 'FAIL'}" for n, ok in gates))
    print("\n0021 REHEARSAL: GREEN — safe for Alex to paste 0021 into prod (The-Prod-Brain) outside "
          "07:00–09:00 UTC, then run the VERIFY block there.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
