#!/usr/bin/env python3
"""
rehearse_0032.py — prove migration 0032 (mi.fact's claim branch excludes provenance_tier = 'email_signal'; ADR-16,
YED-509) on the Phantom-Test-Case twin before Alex pastes it into prod (invariant 2).

Twin connection, refusal logic, ACL snapshot, guard probes and SET ROLE probes are IMPORTED from rehearse_0030.py; the
broad schema + reader fingerprint and the commented-block parser are IMPORTED from rehearse_0024.py. Nothing is copied,
so the refusal logic stays byte-identical with the harnesses that rehearsed 0024 and 0030.

0032 needs the 0024 end state (mi.fact reads claim_current, which has is_retired). The twin lags prod: 0024 was left
rolled back after its rehearsal, and 0026 later added claim.source_quote there. 0024's claim_current is `select c.*, ...`,
so replayed on the twin today it would pull source_quote in and fail (a view cannot rename a column). Prod applied 0024
BEFORE 0026, so prod's claim_current froze the pre-0026 column list. The parity step therefore applies 0024 verbatim
with ONE twin-only substitution: `select c.*,` in the claim_current statement becomes the explicit list of the
claim_current columns the twin had as found (asserted: exactly one occurrence, in the body and in 0024's ROLLBACK block).
That reproduces prod's claim_current exactly; nothing in 0032 reads those columns.

Gates (all must pass, in order):
  0  as found      twin reachable; snapshot Z (rehearse_0024 schema + reader fingerprint and reader results;
                   rehearse_0030 raw + canonical ACLs); PART 1 on the as-found twin refuses (no is_retired: needs 0024)
  P  parity        0024 verbatim except the one claim_current substitution; mi.fact now reads claim_current
  1  snapshot A    catalog fingerprint + data (count + md5 of mi.fact, fact_topic, fact_company, theme_week,
                   theme_lead_lag, company_timeline, company_cohort, and mi_slice('mi.theme_week', 104 weeks));
                   NEGATIVE CONTROL: the twin holds >= 1 email_signal claim AND >= 1 inbox_miner event in mi.fact
                   (natural, not seeded); step 1's 6 gated rows read false and its keep_ rows true; anon /
                   authenticated denied on mi.fact and mi_slice
  1b guard probes  (rolled back) PART 1 passes clean; refuses a nullable provenance_tier, the 0016 mi.fact shape, a
                   half-applied shape (claim filter only) and a dropped security_invoker; PART 1 + PART 3 without
                   PART 2 makes the postflight raise
  2  apply 0032    the migration file verbatim
  3  re-apply      second paste is a NOTICE no-op (catalog + data unchanged, mi.fact OID unchanged)
  4  verify        step 1 every row ok = t; step 0 differs from A by exactly the four intended rows; the catalog
                   fingerprint differs only in the view-definition hash (owner, ACL, options identical)
  4b deltas        mi.fact claim rows drop by exactly the email_signal claim count and event rows by exactly the
                   inbox_miner event count; mi.fact / fact_topic / fact_company EQUAL snapshot A minus every
                   email_signal row (count + md5); theme_week facts drop by exactly the email_signal facts per
                   theme x lens x week (untouched cells identical
                   apart from floor_flag); theme_lead_lag / company_timeline / company_cohort change only on
                   themes / companies that had email_signal facts; anon / authenticated still denied
  5  rollback      the ROLLBACK-BEGIN..ROLLBACK-END block from the migration header, verbatim
  6  snapshot C    catalog + data identical to snapshot A; step 0 equals A; PART 1 sees PRE
  7  teardown      0024's ROLLBACK block (same one substitution): the twin equals snapshot Z (as found)

No REST gate: schema mi has no API usage and mi_slice is service_role only, so the anon surface is the SET ROLE probe.

Usage:
  python3 supabase/scripts/rehearse_0032.py                   # dry run, no connection
  python3 supabase/scripts/rehearse_0032.py --preflight-only  # gate 0 only (read-only; probes are rolled back)
  python3 supabase/scripts/rehearse_0032.py --execute         # full gate, twin ends as found
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rehearse_0024 as r24  # noqa: E402  (schema + reader fingerprint, commented-block parser)
import rehearse_0030 as r30  # noqa: E402  (shared twin-only connection, refusal logic, ACL snapshot, probes)

SUPA, REPO = r30.SUPA, r30.REPO
MIGRATION = os.path.join(SUPA, "migrations", "0032_mi_fact_excludes_email_signal.sql")
M0024 = r24.MIGRATION
VERIFY = os.path.join(SUPA, "staging", "0032_verify.sql")

CC_STAR = "select c.*,\n       v.outcome"           # the one claim_current line that expands claim's columns
CC_TAIL_0023 = ["last_check_outcome", "last_checked_at", "is_current", "is_overdue"]
ES = "provenance_tier = 'email_signal'"  # either fact_type: email_signal claims and inbox_miner events
RELS = ["mi.fact", "mi.fact_topic", "mi.fact_company", "mi.theme_week", "mi.theme_lead_lag", "mi.company_timeline",
        "mi.company_cohort"]
SLICE = "public.mi_slice('mi.theme_week', '{\"weeks\": 104, \"limit\": 5000}'::jsonb)"


def md5_of(rel: str, where: str = "") -> str:
    w = f" where {where}" if where else ""
    return f"select count(*)||':'||md5(coalesce(string_agg(x::text, '|' order by x::text), '')) from {rel} x{w}"


DATA_SQL = "\n".join(f"select 'data.{v}', ({md5_of(v)});" for v in RELS) + f"""
select 'data.mi_slice.theme_week', jsonb_array_length(s->'rows')||' rows:'||md5((s->'rows')::text) from {SLICE} s;
select 'data.mi_slice.denominators', (s->'denominators')::text from {SLICE} s;
select 'data.mi_fact.claim_rows', count(*)::text from mi.fact where fact_type = 'claim';
select 'data.mi_fact.event_rows', count(*)::text from mi.fact where fact_type = 'event';
select 'data.mi_fact.event_email_signal', count(*)::text from mi.fact where fact_type = 'event' and provenance_tier = 'email_signal';
select 'data.mi_fact.claim_email_signal', count(*)::text from mi.fact where fact_type = 'claim' and provenance_tier = 'email_signal';
"""
# snapshot A minus every email_signal row (claims and inbox_miner events): what B must equal exactly
WANT_SQL = "\n".join(f"select 'want.{v}', ({md5_of(v, 'not (' + ES + ')')});"
                     for v in ("mi.fact", "mi.fact_topic", "mi.fact_company"))
ES_CLAIMS_SQL = ("select count(*) from public.claim_current c where c.status <> 'rejected' and not c.is_retired "
                 "and c.provenance_tier = 'email_signal'")
INBOX_SQL = "select count(*) from public.event where source like 'inbox_miner%'"
TAGGED = ("from mi.fact_topic ft join public.topic t on t.id = ft.topic_id "
          "join topic_intelligence.topic_cluster tc on tc.cluster_id = ft.theme_id "
          "where ft.theme_id is not null and ft.asserted_week is not null and ft.lens in ('attended', 'research', 'market')")
DROP_SQL = (f"select ft.theme_id||'|'||ft.lens||'|'||to_char(ft.asserted_week, 'IYYY-\"W\"IW'), count(distinct (ft.fact_type, ft.fact_id)) "
            f"{TAGGED} and ft.provenance_tier = 'email_signal' group by 1 order by 1")
TW_SQL = ("select theme_id||'|'||lens||'|'||iso_week, facts::text, concat_ws('|', theme, distinct_companies, distinct_sources, "
          "general_facts, theme_resolved), floor_flag from mi.theme_week order by 1")
KEYED = {
    "mi.theme_lead_lag": "select theme_id::text, md5(x::text) from mi.theme_lead_lag x",
    "mi.company_timeline": "select company_id||'|'||lens||'|'||iso_week, md5(x::text) from mi.company_timeline x",
    "mi.company_cohort": "select company_id::text, md5(x::text) from mi.company_cohort x",
}
TOUCHED = {
    "mi.theme_lead_lag": ("select distinct theme_id::text from mi.fact_topic where " + ES +
                          " and theme_id is not null and asserted_at is not null and lens in ('attended', 'market')"),
    "mi.company_timeline": ("select distinct company_id||'|'||lens||'|'||to_char(asserted_week, 'IYYY-\"W\"IW') "
                            "from mi.fact_company where " + ES +
                            " and asserted_week is not null and lens in ('attended', 'research', 'market')"),
    "mi.company_cohort": ("select distinct company_id::text from mi.fact_company where " + ES +
                          " and asserted_at is not null and lens in ('attended', 'research', 'market')"),
}
OID_SQL = "select oid::text from pg_class where oid = 'mi.fact'::regclass"
DENY = {"anon:mi.fact": "select count(*) from mi.fact",
        "anon:mi_slice": f"select {SLICE} is not null",
        "authenticated:mi.fact": "select count(*) from mi.fact",
        "authenticated:mi_slice": f"select {SLICE} is not null"}


def verify_statements() -> list[str]:
    text = "\n".join(l for l in open(VERIFY, encoding="utf-8").read().splitlines() if not l.lstrip().startswith("--"))
    return [s.strip() for s in text.split(";\n") if s.strip()]


def step0() -> dict:
    return {f"{r[0]}\t{r[1]}": (r[2] if len(r) > 2 else "") for r in r30.rows(verify_statements()[0])}


def step1() -> dict:
    return {r[0]: r[-1] for r in r30.rows(verify_statements()[1])}


def catalog() -> dict:
    return {**r30.snapshot(), **{f"schema.{k}": v for k, v in r24.kv(r24.SNAPSHOT_SQL).items()}}


def data() -> dict:
    return r30.kv(DATA_SQL)


def fp(d: dict) -> str:
    return hashlib.md5(json.dumps(d, sort_keys=True).encode()).hexdigest()


def keyed(sql: str) -> dict:
    return {r[0]: r[1:] for r in r30.rows(sql)}


def denials() -> bool:
    got = {k: r30.as_role(k.split(":")[0], sql) for k, sql in DENY.items()}
    for k, v in got.items():
        print(f"    {k:<26} {v}")
    ok = all(v == "err 42501" for v in got.values())
    print(f"  {'PASS' if ok else 'FAIL'} anon / authenticated denied (42501) on mi.fact and public.mi_slice")
    return ok


def twin_0024(sql: str, cols: list[str], label: str) -> str:
    if sql.count(CC_STAR) != 1:
        sys.exit(f"REFUSED: expected exactly one `select c.*,` claim_current line in {label}, found {sql.count(CC_STAR)}")
    return sql.replace(CC_STAR, "select " + ", ".join(f"c.{c}" for c in cols) + ",\n       v.outcome")


EV_WHERE = "    WHERE e.source IS NULL OR e.source NOT LIKE 'inbox_miner%'"


def half_applied() -> str:
    """PART 2's own view statement with the event-branch WHERE removed: the claim-only shape PART 1 must refuse."""
    src = open(MIGRATION, encoding="utf-8").read()
    p2 = src.index("-- PART 2")
    stmt = r24.stmt_between(src[p2:], "create or replace view mi.fact", "'email_signal'::text;", "0032 PART 2 view")
    lines = [l for l in stmt.splitlines() if not l.startswith(EV_WHERE)]
    if len(lines) != len(stmt.splitlines()) - 1:
        sys.exit("could not find exactly one event-branch WHERE line in PART 2")
    return "\n".join(lines)


def claim_current_cols() -> list[str]:
    cols = [r[0] for r in r30.rows("select attname from pg_attribute where attrelid = 'public.claim_current'::regclass "
                                   "and attnum > 0 and not attisdropped order by attnum")]
    if cols[-4:] != CC_TAIL_0023 or "is_retired" in cols:
        sys.exit(f"twin claim_current is not at the 0023 shape (tail {cols[-4:]}); run --teardown-only or inspect")
    return cols[:-4]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--preflight-only", action="store_true")
    ap.add_argument("--teardown-only", action="store_true",
                    help="recovery: 0032 rollback, then 0024 rollback (twin substitution) after a failed run")
    a = ap.parse_args()
    for f in (MIGRATION, M0024, VERIFY):
        if not os.path.exists(f):
            sys.exit(f"missing {f}")
    r30.refuse_non_twin()
    r24.refuse_non_twin()
    pre_block, post_block = r30.block(MIGRATION, "PART 1", "pre"), r30.block(MIGRATION, "PART 3", "post")
    src24 = r24.read_migration()
    rb24 = r24.commented_block(src24, "ROLLBACK")
    print(f"twin {r30.TWIN_HOST} as {r30.TWIN_USER}; migration {os.path.relpath(MIGRATION, REPO)}; "
          f"verify statements: {len(verify_statements())}; PART 1: {len(pre_block)} chars; PART 3: "
          f"{len(post_block)} chars; rollback block: {len(r30.rollback_block(MIGRATION).splitlines())} lines")
    if len(verify_statements()) != 2:
        sys.exit("verify file must hold exactly 2 statements (step 0, step 1)")

    if a.teardown_only:
        state = r30.rows("select (regexp_replace(pg_get_viewdef('mi.fact'::regclass, true), '\\s+', ' ', 'g') "
                         "~ 'provenance_tier <> ''email_signal''')::text, exists (select 1 from pg_attribute where "
                         "attrelid = 'public.claim_current'::regclass and attname = 'is_retired')::text")[0]
        if state[0] == "true":
            r30.run_sql(r30.rollback_block(MIGRATION), "0032 rollback block (verbatim)", is_file=False, tag="0032")
        if state[1] == "true":
            cols = [r[0] for r in r30.rows("select attname from pg_attribute where attrelid = 'public.claim_current'"
                                           "::regclass and attnum > 0 and not attisdropped order by attnum")][:-5]
            r30.run_sql(twin_0024(rb24, cols, "0024 ROLLBACK"), "0024 rollback block (twin substitution)",
                        is_file=False, tag="0024")
        print(f"    catalog md5 {fp(catalog())}")
        return 0
    if not (a.execute or a.preflight_only):
        print("dry run: no connection. Use --preflight-only or --execute.")
        return 0

    ok = True
    print("[0] as found: snapshot Z")
    Z, Zacl = r24.snapshot(), r30.snapshot()
    print(f"    rehearse_0024 fingerprint keys: {len(Z)}; md5 {fp(Z)} | ACL keys: {len(Zacl)}; md5 {fp(Zacl)}")
    cols = claim_current_cols()
    print(f"    claim_current as found: {len(cols)} claim columns + {', '.join(CC_TAIL_0023)} (0023 shape, no is_retired)")
    ok &= r30.guard_probe(None, pre_block, "PART 1 on the as-found twin refuses (no is_retired)",
                          "Apply 0024 first", False)
    if a.preflight_only:
        print("PREFLIGHT OK (read-only)" if ok else "PREFLIGHT FAIL")
        return 0 if ok else 1
    if not ok:
        return 1

    print("[P] parity setup (twin-only): 0024 verbatim except `select c.*,` -> the as-found claim_current columns")
    good, _ = r30.run_sql(twin_0024(src24, cols, "0024"), "apply 0024 (twin substitution)", is_file=False, tag="0024")
    par = r30.rows("select (regexp_replace(pg_get_viewdef('mi.fact'::regclass, true), '\\s+', ' ', 'g') "
                   "~ 'FROM (public\\.)?claim_current c .* AND NOT c\\.is_retired;$')::text")[0][0]
    print(f"  {'PASS' if good and par == 'true' else 'FAIL'} twin at the 0024 shape (mi.fact reads claim_current, "
          f"NOT c.is_retired)")
    if not (good and par == "true"):
        print("  run --teardown-only")
        return 1

    print("[1] snapshot A + negative control")
    A, DA, S0A = catalog(), data(), step0()
    WA = r30.kv(WANT_SQL)
    n_es = int(r30.rows(ES_CLAIMS_SQL)[0][0])
    n_inbox = int(r30.rows(INBOX_SQL)[0][0])
    drop = {r[0]: int(r[1]) for r in r30.rows(DROP_SQL)}
    TWA = {r[0]: r[1:] for r in r30.rows(TW_SQL)}
    KA = {v: keyed(q) for v, q in KEYED.items()}
    touched = {v: {r[0] for r in r30.rows(q)} for v, q in TOUCHED.items()}
    oid_a = r30.rows(OID_SQL)[0][0]
    print(f"    catalog keys: {len(A)}; md5 {fp(A)}")
    for k, v in DA.items():
        print(f"    {k:<34} {v[:150]}")
    print(f"    email_signal claims in claim_current (non-rejected, non-retired): {n_es}; inbox_miner events: {n_inbox}; "
          f"theme_week cells touched: {len(drop)} ({sum(drop.values())} fact-cell drops); touched: "
          + ", ".join(f"{v} {len(s)}" for v, s in touched.items()))
    neg_c = int(DA["data.mi_fact.claim_email_signal"])
    neg_e = int(DA["data.mi_fact.event_email_signal"])
    s1 = step1()
    gated = ["mi_fact_claim_rows", "mi_fact_event_rows", "no_email_signal_claims_in_mi_fact",
             "no_email_signal_events_in_mi_fact", "mi_fact_claim_branch_excludes_email_signal",
             "mi_fact_event_branch_excludes_inbox_miner"]
    for k, v in s1.items():
        print(f"    {'t' if v == 't' else 'f'} {k}")
    nc = (neg_c >= 1 and neg_c == n_es and neg_e >= 1 and neg_e == n_inbox
          and all(s1.get(k) == "f" for k in gated) and all(v == "t" for k, v in s1.items() if k not in gated))
    print(f"  {'PASS' if nc else 'FAIL'} negative control: {neg_c} email_signal claims and {neg_e} inbox_miner events in "
          f"mi.fact before apply (natural twin data, nothing seeded); the {len(gated)} gated step-1 rows read f, the "
          f"{len(s1) - len(gated)} keep rows read t")
    ok &= nc and denials()
    if not ok:
        return 1

    print("[1b] guard probes (rolled back)")
    old_fact = r24.stmt_between(rb24, "create or replace view mi.fact", "WHERE c.status <> 'rejected'::text;", "0016 mi.fact")
    ok &= r30.guard_probe(None, pre_block, "PART 1 passes on the 0024-parity twin", "preflight OK: PRE state", True)
    ok &= r30.guard_probe("alter table public.claim alter column provenance_tier drop not null", pre_block,
                          "nullable provenance_tier refused", "is nullable", False)
    ok &= r30.guard_probe(old_fact, pre_block, "mi.fact at the 0016 shape (reads claim) refused",
                          "not at the 0024 or the 0032 shape", False)
    ok &= r30.guard_probe(half_applied(), pre_block, "half-applied shape (claim filter only, event branch open) refused",
                          "not at the 0024 or the 0032 shape", False)
    ok &= r30.guard_probe("alter view mi.fact reset (security_invoker)", pre_block,
                          "mi.fact without security_invoker refused", "unexpected owner, options", False)
    ok &= r30.guard_probe(None, pre_block + "\n" + post_block, "wrong end state (PART 2 skipped): postflight raises",
                          "postflight FAILED", False)
    if not ok:
        return 1

    print("[2] apply 0032")
    good, n = r30.run_sql(MIGRATION, "apply", tag="0032")
    if not good or not any("postflight OK" in x for x in n):
        print("  FAIL apply (or no 'postflight OK' notice); run --teardown-only")
        return 1
    B, DB = catalog(), data()

    print("[3] re-apply (idempotent)")
    good, n = r30.run_sql(MIGRATION, "re-apply", tag="0032")
    d = r30.diff({**B, **DB}, {**catalog(), **data()})
    noop = good and not d and any("already applied" in x for x in n) and r30.rows(OID_SQL)[0][0] == oid_a
    print(f"  {'PASS' if noop else 'FAIL'} re-apply is a no-op (catalog + data unchanged, 'already applied' notice, "
          f"mi.fact OID {oid_a} unchanged)")
    r30.print_diff(d)
    ok &= noop

    print("[4] verify (staging/0032_verify.sql)")
    s1 = step1()
    for k, v in s1.items():
        print(f"    {'ok ' if v == 't' else 'BAD'} {k}")
    good = bool(s1) and all(v == "t" for v in s1.values())
    print(f"  {'PASS' if good else 'FAIL'} step 1: {sum(v == 't' for v in s1.values())}/{len(s1)} ok")
    ok &= good
    want0 = dict(S0A)
    want0["def\tclaim_branch_excludes_email_signal"] = "true"
    want0["def\tevent_branch_excludes_inbox_miner"] = "true"
    want0.pop("count\tclaim:email_signal", None)
    want0.pop("count\tevent:email_signal", None)
    d = r30.diff(want0, step0())
    tab = chr(9)
    print(f"  {'PASS' if not d else 'FAIL'} step 0 = snapshot A with exactly 4 rows changed (claim_branch_excludes_"
          f"email_signal and event_branch_excludes_inbox_miner false -> true; count claim:email_signal "
          f"{S0A.get('count' + tab + 'claim:email_signal')} -> absent; count event:email_signal "
          f"{S0A.get('count' + tab + 'event:email_signal')} -> absent)")
    r30.print_diff(d)
    ok &= not d
    d = r30.diff(A, B)
    good = set(d) == {"schema.views"}
    print(f"  {'PASS' if good else 'FAIL'} catalog fingerprint: only the view-definition hash changed "
          f"(owner, ACL, options, columns, functions, grants identical): changed keys {sorted(d)}")
    ok &= good

    print("[4b] expected deltas")
    ca, cb = int(DA["data.mi_fact.claim_rows"]), int(DB["data.mi_fact.claim_rows"])
    good = ca - cb == n_es and n_es >= 1
    print(f"  {'PASS' if good else 'FAIL'} mi.fact claim rows {ca} -> {cb}: dropped {ca - cb} = the {n_es} email_signal claims")
    ok &= good
    for v in ("mi.fact", "mi.fact_topic", "mi.fact_company"):
        good = DB[f"data.{v}"] == WA[f"want.{v}"]
        print(f"  {'PASS' if good else 'FAIL'} {v} after = snapshot A minus every email_signal row "
              f"({DA[f'data.{v}'].split(':')[0]} -> {DB[f'data.{v}'].split(':')[0]} rows, md5 equal)")
        ok &= good
    ea, eb = int(DA["data.mi_fact.event_rows"]), int(DB["data.mi_fact.event_rows"])
    good = ea - eb == n_inbox and n_inbox >= 1 and DB["data.mi_fact.event_email_signal"] == "0"
    print(f"  {'PASS' if good else 'FAIL'} mi.fact event rows {ea} -> {eb}: dropped {ea - eb} = the {n_inbox} inbox_miner "
          f"events; event:email_signal now {DB['data.mi_fact.event_email_signal']}")
    ok &= good

    TWB = {r[0]: r[1:] for r in r30.rows(TW_SQL)}
    new = set(TWB) - set(TWA)
    bad, flips, gone = [], 0, 0
    for k, (facts, rest, flag) in TWA.items():
        want = int(facts) - drop.get(k, 0)
        got = int(TWB[k][0]) if k in TWB else 0
        if want != got or (want == 0) != (k not in TWB):
            bad.append(f"{k}: facts {facts} - drop {drop.get(k, 0)} = {want}, got {got}")
        if k not in TWB:
            gone += 1
            continue
        if k not in drop and TWB[k][1] != rest:
            bad.append(f"{k}: untouched cell changed [{rest}] -> [{TWB[k][1]}]")
        flips += TWB[k][2] != flag
    stray = sorted(set(drop) - set(TWA))
    good = not bad and not new and not stray and bool(drop)
    print(f"  {'PASS' if good else 'FAIL'} theme_week: {len(TWA)} -> {len(TWB)} cells; facts dropped by exactly the "
          f"email_signal facts in each of {len(drop)} cells ({gone} cells emptied and gone); untouched cells identical "
          f"apart from floor_flag; no new cells")
    for x in (bad + [f"new cell {k}" for k in sorted(new)] + [f"drop key not in theme_week {k}" for k in stray])[:20]:
        print(f"    BAD {x}")
    print(f"  INFO theme_week floor_flag flips (trailing-8-week window lost facts): {flips}")
    ok &= good
    for v, q in KEYED.items():
        kb = keyed(q)
        changed = {k for k in set(KA[v]) | set(kb) if KA[v].get(k) != kb.get(k)}
        gone_k = set(KA[v]) - set(kb)
        good = changed <= touched[v]
        print(f"  {'PASS' if good else 'FAIL'} {v}: {len(KA[v])} -> {len(kb)} rows; {len(changed)} changed "
              f"({len(gone_k)} gone, {len(changed - gone_k)} values moved), all on the {len(touched[v])} keys that had "
              f"email_signal facts")
        ok &= good
        for k in sorted(changed - touched[v])[:10]:
            print(f"    BAD changed outside the touched set: {k}")
    print(f"  INFO mi_slice('mi.theme_week', 104 weeks): {DA['data.mi_slice.theme_week'].split(':')[0]} -> "
          f"{DB['data.mi_slice.theme_week'].split(':')[0]}")
    print(f"  INFO mi_slice denominators before: {DA['data.mi_slice.denominators']}")
    print(f"  INFO mi_slice denominators after : {DB['data.mi_slice.denominators']}")
    ok &= denials()

    print("[5] rollback (header block, verbatim)")
    good, _ = r30.run_sql(r30.rollback_block(MIGRATION), "rollback", is_file=False, tag="0032")
    if not good:
        return 1
    print("[6] snapshot C == snapshot A")
    d = r30.diff({**A, **DA}, {**catalog(), **data()})
    print(f"  {'PASS' if not d else 'FAIL'} catalog + data identical to snapshot A ({len(A) + len(DA)} keys)")
    r30.print_diff(d)
    ok &= not d
    d = r30.diff(S0A, step0())
    print(f"  {'PASS' if not d else 'FAIL'} step 0 equals snapshot A again")
    r30.print_diff(d)
    ok &= not d
    ok &= r30.guard_probe(None, pre_block, "PART 1 sees the PRE state again", "preflight OK: PRE state", True)
    print(f"  {'PASS ROLLBACK PROVEN' if ok else 'FAIL'}")

    print("[7] teardown: 0024 rollback block (same twin substitution) -> twin as found")
    good, _ = r30.run_sql(twin_0024(rb24, cols, "0024 ROLLBACK"), "0024 rollback block", is_file=False, tag="0024")
    if not good:
        print("  FAIL teardown errored: twin NOT as found (run --teardown-only, then inspect)")
        return 1
    d = r24.gated_diff(Z, r24.snapshot())
    print(f"  {'PASS' if not d else 'FAIL'} rehearse_0024 fingerprint (schema, readers, reader results, counts) equals "
          f"snapshot Z ({len(Z)} keys)")
    r24.print_diff(d)
    ok &= not d
    Zc = r30.snapshot()
    d = r30.diff(r30.canon_only(Zacl), r30.canon_only(Zc))
    print(f"  {'PASS' if not d else 'FAIL'} canonical ACLs, defaults, policies and view options equal snapshot Z")
    r30.print_diff(d)
    ok &= not d
    draw = r30.diff({k: v for k, v in Zacl.items() if k.startswith("raw.")},
                    {k: v for k, v in Zc.items() if k.startswith("raw.")})
    print(f"  {'PASS' if not draw else 'INFO'} raw ACL text equals snapshot Z "
          f"({'byte-identical' if not draw else str(len(draw)) + ' differ in item order only (canonical equal above)'})")
    r30.print_diff(draw, 10)

    print(f"\nREHEARSAL 0032: {'PASS' if ok else 'FAIL'} (twin left as found, 0032 and the 0024 parity rolled back)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
