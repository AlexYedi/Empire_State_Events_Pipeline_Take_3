#!/usr/bin/env python3
"""
rehearse_0031.py — prove migration 0031 (public.v_public_spine_stats: one row of 4 aggregate numbers, owner rights,
SELECT to anon/authenticated/service_role; GTM-34) on the Phantom-Test-Case twin before Alex pastes it into prod
(invariant 2).

Twin connection, refusal logic, snapshot, parity setup and REST key checks are IMPORTED from rehearse_0030.py, not
copied, so they stay byte-identical with the harness that rehearsed 0030 (which copied them from 0029).

0031 needs the 0030 end state (anon holds nothing on company/person/event/claim). The twin lags prod (0028, 0029 and
0030 were left rolled back after their rehearsals), so the harness first brings the twin to prod parity exactly the
way rehearse_0030.py does, then applies 0030 verbatim, proves parity against the prod step-0 evidence file,
rehearses 0031, rolls 0031 back, then undoes 0030 and the parity setup and proves the twin is back to exactly what it
found.

Gates (all must pass, in order):
  0  as found      twin reachable; snapshot Z (rehearse_0030.snapshot: raw + canonical ACLs, defaults, policies,
                   view options over public/mi/signal_read/topic_intelligence)
  P  parity        0028, 0029 verbatim, rehearse_0030.PARITY_SQL, then 0030 verbatim (postflight OK each).
                   staging/0031_verify.sql step 0 on the twin must EQUAL
                   supabase/evidence/0031_prod_step0_before-20261122.tsv (read-only on prod via the MCP)
  1  snapshot A    raw + canonical fingerprint; negative control: the view does not exist (anon SET ROLE 42P01,
                   REST GET 404); anon REST GET person is refused (0030 state)
  1b guard probes  (rolled back) PART 1 passes clean; refuses when anon holds SELECT on person (0030 state broken);
                   refuses a pre-existing relation of that name with another shape; PART 1 + PART 3 without PART 2
                   makes the postflight raise
  2  apply 0031    the migration file verbatim
  3  re-apply      second paste is a NOTICE no-op (snapshot unchanged)
  4  verify        step 1 every row ok = t; step 0 equals the prod baseline transformed by exactly the intended change
  4a anon after    SET ROLE anon / authenticated: exactly 1 row, non-zero, equal to the direct aggregates; anon still
                   42501 on the 4 base tables and cannot write the view; REST GET of the view with the twin
                   publishable key 200 + 1 row equal to the DB values; REST GET person still refused; REST POST to
                   the view refused
  5  rollback      the ROLLBACK-BEGIN..ROLLBACK-END block from the migration header, verbatim
  6  snapshot C    raw + canonical byte-identical to snapshot A; step 0 equals the prod baseline; PART 1 sees PRE;
                   REST GET of the view is 404 again
  7  teardown      0030's rollback block, rehearse_0030.PARITY_UNDO, then 0029's and 0028's rollback blocks: the twin
                   equals snapshot Z (as found)

Usage:
  python3 supabase/scripts/rehearse_0031.py                   # dry run, no connection
  python3 supabase/scripts/rehearse_0031.py --preflight-only  # gate 0 only (read-only)
  TWIN_PUBLISHABLE_KEY=sb_publishable_... python3 supabase/scripts/rehearse_0031.py --execute   # full gate, twin ends as found
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rehearse_0030 as r30  # noqa: E402  (shared twin-only connection, refusal logic, snapshot and parity setup)

SUPA, REPO = r30.SUPA, r30.REPO
MIGRATION = os.path.join(SUPA, "migrations", "0031_public_spine_stats_view.sql")
M0030 = r30.MIGRATION
VERIFY = os.path.join(SUPA, "staging", "0031_verify.sql")
PROD_STEP0 = os.path.join(SUPA, "evidence", "0031_prod_step0_before-20261122.tsv")
VIEW = "public.v_public_spine_stats"
COLS = "entity_count,event_count,signal_count,last_signal_at"
BASE = ["company", "person", "event", "claim"]

VIEW_ROW_SQL = ("select count(*)::text||'|'||coalesce(max(entity_count)::text,'')||'|'||coalesce(max(event_count)::text,'')"
                "||'|'||coalesce(max(signal_count)::text,'')||'|'||coalesce((max(last_signal_at) is not null)::text,'') "
                f"from {VIEW}")
DIRECT_SQL = ("select '1|'||((select count(*) from public.company) + (select count(*) from public.person))::text"
              "||'|'||(select count(*) from public.event)::text"
              "||'|'||(select count(*) from public.claim where status = 'approved')::text"
              "||'|'||((select max(created_at) from public.claim where status = 'approved') is not null)::text")

# expected step-0 rows after apply (the shape PART 2 builds)
AFTER_VIEW = {
    "view\tpublic.v_public_spine_stats": "kind=v owner=postgres opts=security_barrier=true,security_invoker=off",
    "view_acl\tpublic.v_public_spine_stats": ("anon:SELECT,authenticated:SELECT,postgres:DELETE,postgres:INSERT,"
                                               "postgres:MAINTAIN,postgres:REFERENCES,postgres:SELECT,postgres:TRIGGER,"
                                               "postgres:TRUNCATE,postgres:UPDATE,service_role:SELECT"),
    "view_cols\tpublic.v_public_spine_stats": ("entity_count:bigint,event_count:bigint,signal_count:bigint,"
                                                "last_signal_at:timestamp with time zone"),
    "view_deps\tpublic.v_public_spine_stats": ("public.claim.created_at,public.claim.status,public.company,"
                                                "public.event,public.person"),
    "exposure\tpublic.v_public_spine_stats": "anon:SELECT,authenticated:SELECT",
}


def verify_statements() -> list[str]:
    text = "\n".join(l for l in open(VERIFY, encoding="utf-8").read().splitlines() if not l.lstrip().startswith("--"))
    return [s.strip() for s in re.split(r";\s*\n", text) if s.strip()]


def step0() -> dict:
    return {f"{r[0]}\t{r[1]}": (r[2] if len(r) > 2 else "") for r in r30.rows(verify_statements()[0])}


def prod_step0() -> dict:
    out = {}
    for line in open(PROD_STEP0, encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        sec, obj, priv = line.rstrip("\n").split("\t")
        out[f"{sec}\t{obj}"] = priv
    return out


def expected_after(before: dict) -> dict:
    out = dict(before)
    out.update(AFTER_VIEW)
    return out


def verify_step1() -> bool:
    out = r30.rows(verify_statements()[1])
    for r in out:
        print(f"    {'ok ' if r[-1] == 't' else 'BAD'} {r[0]}")
    bad = [r[0] for r in out if r[-1] != "t"]
    print(f"  {'PASS' if out and not bad else 'FAIL'} step 1: {len(out) - len(bad)}/{len(out)} ok {bad or ''}")
    return bool(out) and not bad


def run_sql(path_or_sql: str, label: str, is_file: bool = True, tag: str = "0031"):
    return r30.run_sql(path_or_sql, label, is_file=is_file, tag=tag)


def rest(key: str, rel: str, method: str = "GET", query: str = "", body=None) -> dict:
    url = f"{r30.TWIN_REST}/{rel}" + (f"?{query}" if query else "")
    if r30.TWIN_REF not in url or r30.PROD_REF in url or not url.split("?")[0].endswith("/" + rel):
        sys.exit(f"REFUSED: bad REST probe URL {url}")
    hdr = {"apikey": key, "Accept": "application/json", "Accept-Profile": "public", "Content-Profile": "public"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        hdr["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=hdr)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            status, raw = r.status, r.read()
    except urllib.error.HTTPError as e:
        status, raw = e.code, e.read()
    try:
        payload = json.loads(raw or b"null")
    except ValueError:
        payload = None
    res = {"url": url, "method": method, "status": status, "payload": payload}
    res["code"] = (payload.get("code") or "") if isinstance(payload, dict) else ""
    print(f"    {method} {url} -> HTTP {status}"
          + (f" rows={len(payload)}" if isinstance(payload, list) else f" {res['code']}"))
    return res


def rest_view(key: str, want_status: int, tries: int = 8) -> dict:
    """GET the view; retry while PostgREST reloads its schema cache (pg_notify / pgrst_ddl_watch)."""
    q = "select=" + urllib.parse.quote(COLS, safe=",")
    for i in range(tries):
        r = rest(key, "v_public_spine_stats", query=q)
        if r["status"] == want_status:
            return r
        time.sleep(2)
    return r


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--preflight-only", action="store_true")
    ap.add_argument("--teardown-only", action="store_true",
                    help="recovery: drop the view, roll back 0030, parity, 0029, 0028 after a failed run")
    ap.add_argument("--publishable-key", default=None, help="twin publishable key (else TWIN_PUBLISHABLE_KEY)")
    a = ap.parse_args()
    for f in (MIGRATION, M0030, r30.M0028, r30.M0029, VERIFY, PROD_STEP0):
        if not os.path.exists(f):
            sys.exit(f"missing {f}")
    r30.refuse_non_twin()
    pre_block, post_block = r30.block(MIGRATION, "PART 1", "pre"), r30.block(MIGRATION, "PART 3", "post")
    print(f"twin {r30.TWIN_HOST} as {r30.TWIN_USER}; migration {os.path.relpath(MIGRATION, REPO)}; "
          f"verify statements: {len(verify_statements())}; PART 1: {len(pre_block)} chars; PART 3: "
          f"{len(post_block)} chars; rollback block: {len(r30.rollback_block(MIGRATION).splitlines())} lines; "
          f"prod baseline rows: {len(prod_step0())}")
    if len(verify_statements()) != 2:
        sys.exit("verify file must hold exactly 2 statements (step 0, step 1)")

    def teardown(rpc_restore: str) -> bool:
        good = True
        for sql, label in ((r30.rollback_block(MIGRATION), "0031 rollback block (verbatim from its header)"),
                           (r30.rollback_block(M0030), "0030 rollback block (verbatim from its header)"),
                           (r30.PARITY_UNDO.format(rpc_restore=rpc_restore), "parity undo (rehearse_0030.PARITY_UNDO)"),
                           (r30.rollback_block(r30.M0029), "0029 rollback block (verbatim from its header)"),
                           (r30.rollback_block(r30.M0028), "0028 rollback block (verbatim from its header)")):
            good &= run_sql(sql, label, is_file=False)[0]
        return good

    if a.teardown_only:
        _, rpc_restore, _ = r30.rpc_parity_sql()
        if not teardown(rpc_restore):
            return 1
        T = r30.snapshot()
        print(f"    keys: {len(T)}; md5 {hashlib.md5(json.dumps(T, sort_keys=True).encode()).hexdigest()}")
        return 0
    if not (a.execute or a.preflight_only):
        print("dry run: no connection. Use --preflight-only or --execute.")
        return 0

    print("[0] as found: snapshot Z")
    Z = r30.snapshot()
    print(f"    keys: {len(Z)}; md5 {hashlib.md5(json.dumps(Z, sort_keys=True).encode()).hexdigest()}")
    d = r30.diff(prod_step0(), step0())
    print(f"  INFO twin step 0 vs prod baseline before parity: {len(d)} rows differ (expected: the twin lags prod)")
    if a.preflight_only:
        r30.print_diff(d)
        print("PREFLIGHT OK (read-only)")
        return 0

    key = r30.publishable_key(a.publishable_key)
    ok = True
    rpc_revoke, rpc_restore, rpc_fns = r30.rpc_parity_sql()
    print("[P] parity setup (twin-only): 0028, 0029 verbatim; rehearse_0030 parity grants; 0030 verbatim")
    for path, tag in ((r30.M0028, "0028"), (r30.M0029, "0029")):
        good, n = run_sql(path, f"apply {tag} verbatim", tag=tag)
        if not good or not any("postflight OK" in x for x in n):
            print(f"  FAIL {tag} did not apply cleanly on the twin (run --teardown-only)")
            return 1
    good, _ = run_sql(r30.PARITY_SQL.format(rpc_revoke=rpc_revoke), "parity grants", is_file=False)
    if not good:
        return 1
    good, n = run_sql(M0030, "apply 0030 verbatim", tag="0030")
    if not good or not any("postflight OK" in x for x in n):
        print("  FAIL 0030 did not apply cleanly on the twin (run --teardown-only)")
        return 1
    d = r30.diff(prod_step0(), step0())
    print(f"  {'PASS' if not d else 'FAIL'} twin step 0 EQUALS the prod baseline "
          f"({os.path.relpath(PROD_STEP0, REPO)}, {len(prod_step0())} rows)")
    r30.print_diff(d)
    if d:
        return 1

    print("[1] snapshot A + negative control")
    A = r30.snapshot()
    print(f"    keys: {len(A)}; md5 {hashlib.md5(json.dumps(A, sort_keys=True).encode()).hexdigest()}")
    neg = {"anon:view": r30.as_role("anon", VIEW_ROW_SQL)}
    neg.update({f"anon:table:{t}": r30.as_role("anon", f"select count(*) from public.{t}") for t in BASE})
    for k, v in neg.items():
        print(f"    {k:<30} {v}")
    nc = neg["anon:view"] == "err 42P01" and all(v == "err 42501" for k, v in neg.items() if ":table:" in k)
    print(f"  {'PASS' if nc else 'FAIL'} before apply: the view does not exist (42P01); anon is denied (42501) on the "
          f"4 base tables (0030 state)")
    print(f"[1c] REST as anon before apply ({r30.TWIN_REST}, twin publishable key)")
    rv_a = rest_view(key, 404, tries=1)
    rp_a = rest(key, "person", query="select=id")
    rb = rv_a["status"] == 404 and rp_a["status"] in (401, 403)
    print(f"  {'PASS' if rb else 'FAIL'} REST view -> {rv_a['status']} {rv_a['code']} (absent); person -> "
          f"{rp_a['status']} {rp_a['code']}")
    if not (nc and rb):
        return 1

    print("[1b] guard probes (rolled back)")
    ok &= r30.guard_probe(None, pre_block, "PART 1 passes on the parity twin", "preflight OK: PRE state", True)
    ok &= r30.guard_probe("grant select on public.person to anon", pre_block, "0030 state broken refused",
                          "the 0030 state does not hold", False)
    ok &= r30.guard_probe("create view public.v_public_spine_stats as select 1 as x", pre_block,
                          "a relation of that name with another shape refused", "unexpected shape", False)
    ok &= r30.guard_probe(None, pre_block + "\n" + post_block, "wrong end state (PART 2 skipped): postflight raises",
                          "postflight FAILED", False)
    if not ok:
        return 1

    print("[2] apply 0031")
    good, n = run_sql(MIGRATION, "apply")
    if not good or not any("postflight OK" in x for x in n):
        print("  FAIL apply (or no 'postflight OK' notice)")
        return 1
    B = r30.snapshot()
    print("  catalog entries that changed (A -> B), canonical:")
    r30.print_diff(r30.diff(r30.canon_only(A), r30.canon_only(B)))

    print("[3] re-apply (idempotent)")
    good, n = run_sql(MIGRATION, "re-apply")
    if not good:
        return 1
    d = r30.diff(B, r30.snapshot())
    noop = not d and any("already applied" in x for x in n)
    print(f"  {'PASS' if noop else 'FAIL'} re-apply is a no-op (raw + canonical unchanged, 'already applied' notice)")
    r30.print_diff(d)
    ok &= noop

    print("[4] verify (staging/0031_verify.sql)")
    ok &= verify_step1()
    d = r30.diff(expected_after(prod_step0()), step0())
    print(f"  {'PASS' if not d else 'FAIL'} step 0 equals the prod baseline transformed by exactly the intended change "
          f"(view rows built; one exposure row public.v_public_spine_stats=anon:SELECT,authenticated:SELECT; all else "
          f"identical)")
    r30.print_diff(d)
    ok &= not d

    print("[4a] anon after apply")
    direct = r30.rows(DIRECT_SQL)[0][0]
    print(f"    direct aggregates (postgres): rows|entities|events|approved claims|last_signal_at set = {direct}")
    reads = {r: r30.as_role(r, VIEW_ROW_SQL) for r in ("anon", "authenticated")}
    for k, v in reads.items():
        print(f"    {k:<14} view -> {v}")
    vals = direct.split("|")
    nz = vals[0] == "1" and all(x not in ("", "0") for x in vals[1:4]) and vals[4] == "true"
    same = all(v == f"ok {direct}" for v in reads.values())
    print(f"  {'PASS' if same and nz else 'FAIL'} anon and authenticated read exactly 1 row, non-zero, equal to the "
          f"direct aggregates (owner rights; an invoker view would be 42501 or a false zero)")
    ok &= same and nz
    denied = {t: r30.as_role("anon", f"select count(*) from public.{t}") for t in BASE}
    denied["write view"] = r30.as_role("anon", f"delete from {VIEW}")
    for k, v in denied.items():
        print(f"    anon {k:<12} {v}")
    dn = all(v == "err 42501" for k, v in denied.items() if k != "write view") and denied["write view"].startswith("err ")
    print(f"  {'PASS' if dn else 'FAIL'} anon still 42501 on company/person/event/claim; writing the view is refused "
          f"(an aggregate view is not updatable: 55000 or 42501)")
    ok &= dn
    rv = rest_view(key, 200)
    p = rv["payload"]
    row = p[0] if isinstance(p, list) and len(p) == 1 else {}
    if row:
        print(f"      row: entity_count={row.get('entity_count')} event_count={row.get('event_count')} "
              f"signal_count={row.get('signal_count')} last_signal_at set={row.get('last_signal_at') is not None}; "
              f"keys={sorted(row)}")
    rg = (rv["status"] == 200 and bool(row) and sorted(row) == sorted(COLS.split(","))
          and [str(row.get(c)) for c in ("entity_count", "event_count", "signal_count")] == vals[1:4]
          and row.get("last_signal_at") is not None)
    print(f"  {'PASS' if rg else 'FAIL'} REST GET view as anon: HTTP {rv['status']}, exactly 1 row, exactly the 4 columns, "
          f"counts equal the direct aggregates")
    ok &= rg
    rp = rest(key, "person", query="select=id")
    rw = rest(key, "v_public_spine_stats", method="POST", body={"entity_count": 1})
    shut = rp["status"] in (401, 403) and rw["status"] not in (200, 201, 204)
    print(f"  {'PASS' if shut else 'FAIL'} REST person -> HTTP {rp['status']} {rp['code']}; POST view -> HTTP "
          f"{rw['status']} {rw['code']}")
    ok &= shut

    print("[5] rollback (header block, verbatim)")
    good, _ = run_sql(r30.rollback_block(MIGRATION), "rollback", is_file=False)
    if not good:
        return 1
    print("[6] snapshot C == snapshot A")
    C = r30.snapshot()
    d = r30.diff(A, C)
    print(f"  {'PASS' if not d else 'FAIL'} raw + canonical byte-identical to snapshot A ({len(A)} keys)")
    r30.print_diff(d)
    ok &= not d
    d = r30.diff(prod_step0(), step0())
    print(f"  {'PASS' if not d else 'FAIL'} step 0 equals the prod baseline again")
    r30.print_diff(d)
    ok &= not d
    ok &= r30.guard_probe(None, pre_block, "PART 1 sees the PRE state again", "preflight OK: PRE state", True)
    rv_c = rest_view(key, 404)
    back = rv_c["status"] == 404
    print(f"  {'PASS' if back else 'FAIL'} REST view -> HTTP {rv_c['status']} {rv_c['code']} (gone again)")
    ok &= back
    print(f"  {'PASS ROLLBACK PROVEN' if ok else 'FAIL'}")

    print("[7] teardown: 0030 rollback, parity undo, 0029 rollback, 0028 rollback -> twin as found")
    good = True
    for sql, label in ((r30.rollback_block(M0030), "0030 rollback block (verbatim from its header)"),
                       (r30.PARITY_UNDO.format(rpc_restore=rpc_restore), "parity undo (rehearse_0030.PARITY_UNDO)"),
                       (r30.rollback_block(r30.M0029), "0029 rollback block (verbatim from its header)"),
                       (r30.rollback_block(r30.M0028), "0028 rollback block (verbatim from its header)")):
        good &= run_sql(sql, label, is_file=False)[0]
    if not good:
        print("  FAIL teardown step errored: twin NOT as found (run --teardown-only, then inspect)")
        return 1
    Zc = r30.snapshot()
    d = r30.diff(r30.canon_only(Z), r30.canon_only(Zc))
    print(f"  {'PASS' if not d else 'FAIL'} canonical ACLs, defaults, policies and view options equal snapshot Z "
          f"({len(r30.canon_only(Z))} keys)")
    r30.print_diff(d)
    ok &= not d
    draw = r30.diff({k: v for k, v in Z.items() if k.startswith("raw.")},
                    {k: v for k, v in Zc.items() if k.startswith("raw.")})
    print(f"  {'PASS' if not draw else 'INFO'} raw ACL text equals snapshot Z "
          f"({'byte-identical' if not draw else str(len(draw)) + ' differ in item order only (canonical equal above)'})")
    r30.print_diff(draw, 10)
    gone = r30.rows(f"select (to_regclass('{VIEW}') is null)::text")[0][0]
    print(f"  {'PASS' if gone == 'true' else 'FAIL'} {VIEW} absent on the twin (rolled back)")
    ok &= gone == "true"

    print(f"\nREHEARSAL 0031: {'PASS' if ok else 'FAIL'} (twin left as found, 0031 rolled back)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
