#!/usr/bin/env python3
"""
rehearse_0017.py: prove migration 0017 (international-phone PII backstop,
YED-309) on the Phantom-Test-Case twin before Alex pastes it into the prod
dashboard (CLAUDE.md invariant 2). Alex approved rehearsing on the current
(pre-2B) twin on 2026-11-04: 0017 touches only public.assert_no_contact_pii(),
which the S-04 D1 rehearsal (#259) left applied there.

Gates (all must pass, in order):
  0  preflight   refuse prod; twin reachable; the S-04 backstop is present
                 (2 functions + 2 triggers on public.person); the live
                 function carries the PRE-0017 pattern (twin == prod today);
                 regex parity spine vs proposal (check_pii_regex_parity.py)
  1  snapshot A  md5 of both assert_no_* bodies + trigger list + row counts
  2  probe 0     the full client PHONE_RE (AST-read from spine_client.py) in
                 Postgres on 15 strings: every row ok, NBSP included
  3  probe 1     rows (public + cv2) the new alternative would refuse: 0
  4  apply       0017, verbatim
  5  verify      staging/0017_verify.sql (intl refusals, regressions, passes,
                 cv2 leg) AND staging/s04_d1_verify.sql (no S-04 regression)
  6  re-apply    0017 again: idempotent; verify again
  7  rollback    Part 1 of pii-db-check.sql at 622a221 (the live pre-0017 body)
  8  snapshot C  must EQUAL snapshot A: the rollback is PROVEN only if so;
                 plus a behavioural leg: an intl number is ACCEPTED again and
                 a US number still REFUSED (inside a rolled-back transaction)
  9  leave       re-apply 0017 + verify: the twin ends in the post-promotion
                 state prod will be in (default; --no-leave to stop at C)

HARD REFUSAL: never touches prod (oicikjyzmxqfomrrqkvf). No override flag.
Env: PHANTOM_TEST_DB_PASSWORD (required, from .env); TWIN_DB_HOST /
TWIN_DB_PORT / TWIN_DB_USER overrides (session pooler for IPv4:
aws-1-us-east-2.pooler.supabase.com, user postgres.ytfzzsxcxxbejnowmkmk).
"""
from __future__ import annotations
import argparse, ast, datetime as dt, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SUPA = os.path.dirname(HERE)
REPO = os.path.dirname(SUPA)
PSQL = os.environ.get("PSQL_BIN", "psql")

TWIN_REF = "ytfzzsxcxxbejnowmkmk"
PROD_REF = "oicikjyzmxqfomrrqkvf"
LIVE_REV = "622a221"   # the pii-db-check.sql revision prod has run since 2026-11-02

MIGRATION = os.path.join(SUPA, "migrations", "0017_pii_backstop_intl_phone.sql")
VERIFY_0017 = os.path.join(SUPA, "staging", "0017_verify.sql")
VERIFY_S04 = os.path.join(SUPA, "staging", "s04_d1_verify.sql")
PARITY = os.path.join(REPO, ".claude", "scripts", "check_pii_regex_parity.py")
SPINE = os.path.join(REPO, ".claude", "scripts", "spine_client.py")

TWIN_HOST = os.environ.get("TWIN_DB_HOST", f"db.{TWIN_REF}.supabase.co")
TWIN_PORT = os.environ.get("TWIN_DB_PORT", "5432")
TWIN_USER = os.environ.get("TWIN_DB_USER", "postgres")
TWIN_CONN = (f"host={TWIN_HOST} port={TWIN_PORT} user={TWIN_USER} "
             f"dbname=postgres sslmode=require connect_timeout=30")

PROBE0 = [  # (string-as-SQL-expression, expected)
    ("'+44 20 7946 0958'", True), ("'+44-20-7946-0958'", True),
    ("'+49 (0)30 1234 5678'", True), ("'call +33 1 99 00 12 34 today'", True),
    ("'555-123-4567'", True), ("'+15551234567'", True),
    ("'+44' || chr(160) || '20 7946 0958'", True),
    ("'revenue +12 345 678 EUR'", True), ("'+1 234 567 890 shares'", True),
    ("'+44 20'", False), ("'+1.2.3.4.5.6.7'", False), ("'2026-11-04 12:30:45'", False),
    ("'v2.3.4'", False), ("'+40.7128 -74.0060'", False), ("'x'", False),
]

SNAPSHOT_SQL = """
select 'fn.contact', coalesce(md5(prosrc),'-') from pg_proc
 where pronamespace='public'::regnamespace and proname='assert_no_contact_pii'
union all select 'fn.columns', coalesce(md5(prosrc),'-') from pg_proc
 where pronamespace='public'::regnamespace and proname='assert_no_pii_columns'
union all select 'triggers', coalesce(md5(string_agg(tgrelid::regclass::text||':'||tgname::text||':'||tgenabled::text, ',' order by 1)),'-')
  from pg_trigger where not tgisinternal and tgname like '%no\\_%pii%'
union all select 'count.public.person', count(*)::text from public.person
union all select 'cv2.exists', (to_regclass('canonical_v2.person') is not null)::text;
"""


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
        sys.exit(f"REFUSED: target must be the twin ({TWIN_REF}); this script never touches prod.")


def psql(args, stdin=None, check=True):
    pw = os.environ.get("PHANTOM_TEST_DB_PASSWORD") or ENV.get("PHANTOM_TEST_DB_PASSWORD")
    if not pw:
        sys.exit("PHANTOM_TEST_DB_PASSWORD not set: refusing to proceed.")
    p = subprocess.run([PSQL, TWIN_CONN, "-v", "ON_ERROR_STOP=1"] + args, input=stdin, text=True,
                       capture_output=True, env=dict(os.environ, PGPASSWORD=pw))
    if check and p.returncode != 0:
        sys.stderr.write(p.stdout[-2000:] + p.stderr[-2000:])
        sys.exit(f"psql failed (rc={p.returncode}) on {args[:2]}")
    return p


def kv(sql):
    out = psql(["-tA", "-F", "\t", "-c", sql]).stdout
    return dict(line.split("\t", 1) for line in out.splitlines() if "\t" in line)


def client_phone_re() -> str:
    t = ast.parse(open(SPINE).read())
    for node in ast.walk(t):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "PHONE_RE":
            return ast.literal_eval(node.value.args[0])
    sys.exit("PHONE_RE not found in spine_client.py")


def alt3(pattern: str) -> str:
    depth, parts, cur = 0, [], ""
    i = 0
    while i < len(pattern):
        ch = pattern[i]
        if ch == "\\":
            cur += pattern[i:i + 2]; i += 2; continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "|" and depth == 0:
            parts.append(cur); cur = ""
        else:
            cur += ch
        i += 1
    parts.append(cur)
    if "".join(p + "|" for p in parts)[:-1] != pattern or len(parts) != 3:
        sys.exit(f"expected exactly 3 top-level alternatives in PHONE_RE, got {len(parts)}")
    return parts[2]


def snapshot(label):
    s = kv(SNAPSHOT_SQL)
    print(f"  {label}: contact={s.get('fn.contact','?')[:12]}… columns={s.get('fn.columns','?')[:12]}… "
          f"triggers={s.get('triggers','?')[:12]}… person={s.get('count.public.person','?')} "
          f"cv2={s.get('cv2.exists','?')}")
    return s


def run_verify(path, marker, label):
    p = psql(["-f", path], check=False)
    text = p.stdout + p.stderr
    ok = p.returncode == 0 and f"{marker}: PASS" in text
    line = next((ln for ln in text.splitlines() if marker in ln or "FAIL" in ln), text.strip()[-300:])
    print(f"  {label} -> {'PASS' if ok else 'FAIL'} :: {line.strip().split('NOTICE:')[-1].strip()}")
    return ok


def apply_file(path, label):
    p = psql(["-q", "-f", path], check=False)
    ok = p.returncode == 0
    print(f"  {'OK ' if ok else 'ERR'} {label}" + ("" if ok else f" :: {(p.stdout + p.stderr)[-400:]}"))
    return ok


def live_part1() -> str:
    src = subprocess.run(["git", "-C", REPO, "show", f"{LIVE_REV}:docs/adr/proposals/pii-db-check.sql"],
                         capture_output=True, text=True, check=True).stdout.splitlines()
    start = next(i for i, l in enumerate(src) if l.startswith("-- Part 1"))
    end = next(i for i, l in enumerate(src) if l.startswith("-- Part 2"))
    body = "\n".join(src[start:end]).rstrip()
    # drop the trailing comment-rule line that opens Part 2's header box, if any
    lines = body.splitlines()
    while lines and lines[-1].startswith("-- ="):
        lines.pop()
    return "\n".join(lines) + "\n"


def behaviour_after_rollback() -> bool:
    sql = """
begin;
do $b$
begin
  begin
    insert into public.person (id, name, bio, source)
    values (gen_random_uuid(), '__0017_rb__', 'Call +44 20 7946 0958', '0017_rb');
  exception when raise_exception then
    raise exception 'FAIL: intl number still refused after rollback';
  end;
  begin
    insert into public.person (id, name, bio, source)
    values (gen_random_uuid(), '__0017_rb__', 'Call (212) 555-0134', '0017_rb');
    raise exception 'FAIL: US number ACCEPTED after rollback';
  exception when raise_exception then
    if sqlerrm not like 'ADR-9 tier-2 violation%' then raise; end if;
  end;
  raise notice '0017 ROLLBACK BEHAVIOUR: PASS';
end $b$;
rollback;
"""
    p = psql([], stdin=sql, check=False)
    ok = p.returncode == 0 and "0017 ROLLBACK BEHAVIOUR: PASS" in (p.stdout + p.stderr)
    print(f"  behaviour after rollback (intl accepted, US refused; txn rolled back) -> {'PASS' if ok else 'FAIL'}")
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--no-leave", action="store_true", help="stop after the rollback proof")
    a = ap.parse_args()
    refuse_prod()
    print(f"TARGET twin: {TWIN_HOST}:{TWIN_PORT} as {TWIN_USER} (ref {TWIN_REF})  "
          f"at {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n")
    full = client_phone_re()
    a3 = alt3(full)

    print("[0] preflight")
    pre = kv("""select 'fns', count(*)::text from pg_proc where pronamespace='public'::regnamespace
                  and proname in ('assert_no_contact_pii','assert_no_pii_columns')
                union all select 'trg', count(*)::text from pg_trigger where not tgisinternal
                  and tgrelid='public.person'::regclass and tgname in ('person_no_contact_pii','person_no_pii_columns')
                union all select 'has_alt3', (position('\\(0\\)' in prosrc) > 0)::text from pg_proc
                  where pronamespace='public'::regnamespace and proname='assert_no_contact_pii';""")
    print(f"  S-04 backstop functions={pre.get('fns')} triggers={pre.get('trg')} "
          f"live body already has alt 3={pre.get('has_alt3')}")
    if pre.get("fns") != "2" or pre.get("trg") != "2":
        sys.exit("STOP: the twin is not in the S-04 post-D1 state; rehearse S-04 first.")
    if pre.get("has_alt3") != "false":
        sys.exit("STOP: the twin already carries 0017 (or a variant); rerun after rolling back.")
    par = subprocess.run([sys.executable, PARITY], capture_output=True, text=True)
    print(f"  regex parity (spine vs proposal): {'OK' if par.returncode == 0 else 'FAIL'} :: "
          f"{(par.stdout or par.stderr).strip().splitlines()[-1] if (par.stdout or par.stderr).strip() else ''}")
    if par.returncode != 0:
        sys.exit("STOP: parity failed")

    print("\n[1] snapshot A (before)")
    A = snapshot("A")

    print("\n[2] probe 0: full client PHONE_RE in Postgres")
    vals = ",".join(f"({e},{str(x).lower()})" for e, x in PROBE0)
    rows = psql(["-tA", "-F", "\t", "-c",
                 f"select (s ~ $re${full}$re$) = expected from (values {vals}) v(s, expected);"]).stdout.split()
    ok0 = len(rows) == 15 and all(r == "t" for r in rows)
    print(f"  {rows.count('t')}/{len(rows)} ok -> {'PASS' if ok0 else 'FAIL'}")
    if not ok0:
        sys.exit("STOP: probe 0 failed: do not apply")

    print("\n[3] probe 1: existing rows the new alternative would refuse")
    surf = ("coalesce(name,'')||' '||coalesce(title,'')||' '||coalesce(bio,'')||' '||"
            "coalesce(role_context,'')||' '||coalesce(metadata::text,'{}')")
    p1 = psql(["-tA", "-c", f"select count(*) from public.person where {surf} ~ $re${a3}$re$;"]).stdout.strip()
    cv2 = A.get("cv2.exists") == "true"
    p1c = (psql(["-tA", "-c", f"select count(*) from canonical_v2.person where {surf} ~ $re${a3}$re$;"])
           .stdout.strip() if cv2 else "n/a")
    print(f"  public.person={p1} canonical_v2.person={p1c} (expect 0)")
    if p1 != "0" or p1c not in ("0", "n/a"):
        sys.exit("STOP: existing rows match the new alternative: scrub or report on YED-309 first")

    print("\n[4] apply 0017")
    if not apply_file(MIGRATION, "0017_pii_backstop_intl_phone.sql"):
        sys.exit("STOP: apply failed")

    print("\n[5] behavioural verify")
    v1 = run_verify(VERIFY_0017, "0017 VERIFY", "0017_verify.sql")
    v2 = run_verify(VERIFY_S04, "S-04 D1 VERIFY", "s04_d1_verify.sql (no regression)")

    print("\n[6] re-apply 0017 (idempotency)")
    r = apply_file(MIGRATION, "0017 (re-apply)")
    v3 = run_verify(VERIFY_0017, "0017 VERIFY", "0017_verify.sql (post re-apply)")

    print(f"\n[7] rollback: Part 1 of pii-db-check.sql at {LIVE_REV}")
    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as f:
        f.write(live_part1())
        rb_path = f.name
    rb = apply_file(rb_path, f"pii-db-check.sql@{LIVE_REV} Part 1")
    os.unlink(rb_path)

    print("\n[8] snapshot C (after rollback): must EQUAL snapshot A")
    C = snapshot("C")
    same = all(A.get(k) == C.get(k) for k in A)
    print(f"  snapshot C == snapshot A: {'rollback PROVEN' if same else 'MISMATCH'}")
    b = behaviour_after_rollback()

    gates = [v1, v2, r, v3, rb, same, b]
    if not a.no_leave:
        print("\n[9] leave applied: re-apply 0017 + verify (twin ends in prod's post-promotion state)")
        la = apply_file(MIGRATION, "0017 (leave applied)")
        lv = run_verify(VERIFY_0017, "0017 VERIFY", "0017_verify.sql (leave applied)")
        gates += [la, lv]
        print("  twin left with 0017 applied." if la and lv else "  WARNING: leave-applied leg failed.")

    print("\n0017 REHEARSAL: " + ("ALL GATES GREEN" if all(gates) else "FAILED"))
    sys.exit(0 if all(gates) else 1)


if __name__ == "__main__":
    main()
