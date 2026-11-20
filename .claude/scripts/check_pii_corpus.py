#!/usr/bin/env python3
"""check_pii_corpus — run the shared PII probe corpus against each layer's OWN contract (YED-392 rework).
PRIVACY-LAYER CODE: changes need a human read.

fixtures/pii_probe_corpus.jsonl rows: {input, field, table, expect_py, expect_db, clause}
  input       a string, or any JSON value (an integer, an object with a contact as its key) placed at `field`
  field       dotted path inside the row (`claim_text`, `metadata.wa_id`); `table` is the spine table
  expect_py   refuse | allow   what spine_client.guard() (L1/L2, the full Python contract) must do
  expect_db   refuse | allow | out_of_contract   what public.no_contact_pii_v2 (L3, canonical form only) must do
  clause      why the row exists; generated rows are `default_ignorable:<template>:U+XXXX`

  python3 .claude/scripts/check_pii_corpus.py              every row through guard() + the Python model of L3
  python3 .claude/scripts/check_pii_corpus.py --emit-sql   one read-only SELECT (no DDL) that evaluates
                                                           no_contact_pii_v2's expression inline, lifted verbatim
                                                           from migration 0025, over every row; run it on prod
                                                           and every row must report ok = true
  python3 .claude/scripts/check_pii_corpus.py --regen      rewrite the generated default-ignorable rows (one email
                                                           and one phone template x every code point in
                                                           pii_normalize.IGNORABLE), keeping every hand-written row

Exit 0 when every row matches; 1 on any mismatch. Generated rows whose code point this Python's Unicode version
does not know (an older unicodedata) are reported as skipped, never as passed.
"""
from __future__ import annotations
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
CORPUS = os.path.join(REPO, "fixtures", "pii_probe_corpus.jsonl")
MIGRATION = os.path.join(REPO, "supabase", "migrations", "0025_pii_backstop_normalized.sql")
sys.path.insert(0, HERE)
import spine_client as sc  # noqa: E402
import pii_normalize as pn  # noqa: E402

# Each template puts the code point where the RAW text no longer matches (inside the TLD, inside a digit group),
# so only the canonical form's strip can catch it.
TEMPLATES = {"email": ("dana@example.c", "om"), "phone": ("call 555-1", "23-0100")}
GEN_PREFIX = "default_ignorable:"
VERDICTS_PY, VERDICTS_DB = {"refuse", "allow"}, {"refuse", "allow", "out_of_contract"}


def load(path: str = CORPUS) -> list[dict]:
    rows = [json.loads(x) for x in open(path, encoding="utf-8") if x.strip()]
    for i, r in enumerate(rows):
        if set(r) != {"input", "field", "table", "expect_py", "expect_db", "clause"} \
                or r["expect_py"] not in VERDICTS_PY or r["expect_db"] not in VERDICTS_DB:
            raise SystemExit(f"check_pii_corpus: row {i + 1} is malformed: {sorted(r)}")
    return rows


def generated(cps) -> list[dict]:
    return [{"input": pre + chr(cp) + post, "field": "claim_text", "table": "claim", "expect_py": "refuse",
             "expect_db": "refuse", "clause": f"{GEN_PREFIX}{name}:U+{cp:04X}"}
            for name, (pre, post) in TEMPLATES.items() for cp in sorted(cps)]


def _cp(clause: str) -> int:
    return int(clause.rsplit("U+", 1)[1], 16)


def row_of(r: dict) -> dict:
    """The guard() row: `input` placed at the dotted `field` path."""
    keys = r["field"].split(".")
    out = cur = {}
    for k in keys[:-1]:
        cur[k] = {}
        cur = cur[k]
    cur[keys[-1]] = r["input"]
    return out


def py_verdict(r: dict) -> str:
    try:
        sc.guard(r["table"], row_of(r))
    except sc.PIIViolation:
        return "refuse"
    return "allow"


def db_text(v) -> str:
    """The text L3 sees: a string as is; any other JSON value as Postgres renders jsonb::text."""
    return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)


def l3_model(text: str) -> str:
    """Python model of no_contact_pii_v2: the raw text and the L3 form against EMAIL_RE (minus the allowlist) and
    PHONE_RE. The real proof is --emit-sql on Postgres; this keeps the corpus labels honest between runs."""
    for f in (text, pn.l3_form(text)):
        if sc.PHONE_RE.search(f) or any(not sc.EMAIL_ALLOWLIST_RE.search(m.group(0)) for m in sc.EMAIL_RE.finditer(f)):
            return "refuse"
    return "allow"


def check(rows: list[dict]) -> int:
    sc.telemetry(False)
    py_bad, db_bad, skipped, n_db = [], [], [], 0
    for i, r in enumerate(rows, 1):
        if r["clause"].startswith(GEN_PREFIX) and _cp(r["clause"]) not in pn.IGNORABLE:
            skipped.append(r["clause"])
            continue
        if py_verdict(r) != r["expect_py"]:
            py_bad.append((i, r))
        if r["expect_db"] != "out_of_contract":
            n_db += 1
            if l3_model(db_text(r["input"])) != r["expect_db"]:
                db_bad.append((i, r))
    n = len(rows) - len(skipped)
    for label, bad in (("L1/L2 guard()", py_bad), ("L3 model", db_bad)):
        for i, r in bad[:40]:
            want = r["expect_py"] if label.startswith("L1") else r["expect_db"]
            print(f"  MISMATCH {label} row {i}: want {want}  {r['table']}.{r['field']}  {r['clause']}")
    print(f"check_pii_corpus: {len(rows)} rows ({sum(r['clause'].startswith(GEN_PREFIX) for r in rows)} generated)")
    print(f"  L1/L2 guard():       {n - len(py_bad)}/{n} match")
    print(f"  L3 model (Python):   {n_db - len(db_bad)}/{n_db} match "
          f"({sum(r['expect_db'] == 'out_of_contract' for r in rows)} rows out of L3's contract, not asserted)")
    if skipped:
        print(f"  SKIPPED {len(skipped)} generated row(s): code point unknown to this Python's Unicode "
              f"{__import__('unicodedata').unidata_version}, e.g. {skipped[0]}")
    return 1 if py_bad or db_bad else 0


# --------------------------------------------------------------------------------------------- --emit-sql
def _u(s: str) -> str:
    """An ASCII-only Postgres U&'' literal (invisible and astral characters survive copy and paste)."""
    out = []
    for c in s:
        o = ord(c)
        if c == "'":
            out.append("''")
        elif c == "\\":
            out.append("\\\\")
        elif 0x20 <= o < 0x7F:
            out.append(c)
        else:
            out.append(f"\\{o:04X}" if o <= 0xFFFF else f"\\+{o:06X}")
    return "U&'" + "".join(out) + "'"


def migration_parts(src: str) -> tuple[dict, str]:
    lits = {}
    for name in ("email_re", "phone_re", "allow_re", "at_re", "ign_re", "esc_re"):
        m = re.search(rf"^\s*{name} text := (\$re\$.+?\$re\$);", src, re.M)
        if not m:
            raise SystemExit(f"check_pii_corpus: {name} not found in the migration")
        lits[name] = m.group(1)
    m = re.search(r"^\s*-- <v2-expr>[^\n]*\n(.*?)^\s*-- </v2-expr>", src, re.M | re.S)
    if not m:
        raise SystemExit("check_pii_corpus: the -- <v2-expr> markers are missing from the migration")
    return lits, m.group(1).rstrip()


def emit_sql(rows: list[dict], migration_src: str) -> str:
    lits, expr = migration_parts(migration_src)
    hand = [(i, r) for i, r in enumerate(rows, 1) if not r["clause"].startswith(GEN_PREFIX)]
    gen = {name: sorted(_cp(r["clause"]) for r in rows if r["clause"].startswith(f"{GEN_PREFIX}{name}:"))
           for name in TEMPLATES}
    if any(r["expect_db"] != "refuse" for r in rows if r["clause"].startswith(GEN_PREFIX)):
        raise SystemExit("check_pii_corpus: generated rows must all expect refuse")
    values = ",\n".join(
        f"  ('r{i:05d}', {_u(r['clause'])}, '{r['expect_db']}', "
        + (_u(r["input"]) if isinstance(r["input"], str) else _u(db_text(r["input"])) + "::jsonb::text") + ")"
        for i, r in hand)
    gens = ",\n".join(f"  ('{name}', {_u(TEMPLATES[name][0])}, {_u(TEMPLATES[name][1])}, "
                      f"array[{','.join(map(str, cps))}]::int[])" for name, cps in gen.items() if cps)
    ind = lambda s: "\n".join("    " + x.strip() for x in s.splitlines())   # noqa: E731
    return f"""-- check_pii_corpus.py --emit-sql: {len(rows)} corpus rows ({len(hand)} hand-written, {sum(map(len, gen.values()))} generated)
-- against public.no_contact_pii_v2's expression, lifted verbatim from {os.path.relpath(MIGRATION, REPO)}.
-- READ-ONLY: one SELECT, no DDL, no table reads. Every row must report ok = true (out_of_contract rows: ok is null).
with lit as (
  select {lits['email_re']}::text as email_re,
         {lits['phone_re']}::text as phone_re,
         {lits['allow_re']}::text as allow_re,
         {lits['at_re']}::text as at_re,
         {lits['ign_re']}::text as ign_re,
         {lits['esc_re']}::text as esc_re
),
probe(id, clause, expect_db, t) as (values
{values}
),
gen(tpl, pre, post, cps) as (values
{gens}
),
hand as (
  select p.id, p.clause, p.expect_db, e.ok_db
  from probe p cross join lit
  cross join lateral (select (
{ind(expr)}
  ) as ok_db) e
),
gen_rows as (
  select g.tpl, c.cp, e.ok_db
  from gen g cross join lit
  cross join lateral unnest(g.cps) as c(cp)
  cross join lateral (select g.pre || chr(c.cp) || g.post as t) tt
  cross join lateral (select (
{ind(expr)}
  ) as ok_db) e
)
select id, clause, expect_db, case when ok_db then 'allow' else 'refuse' end as got,
       case when expect_db = 'out_of_contract' then null else (expect_db = 'refuse') = (not ok_db) end as ok
from hand
union all
select 'gen:' || tpl, 'default_ignorable x ' || count(*), 'refuse',
       'refuse ' || count(*) filter (where not ok_db) || ' / allow ' || count(*) filter (where ok_db)
         || coalesce(' / allowed U+' || string_agg(upper(to_hex(cp)), ',' order by cp) filter (where ok_db), ''),
       bool_and(not ok_db)
from gen_rows group by tpl
order by 1;
"""


def main(argv: list[str]) -> int:
    if "--regen" in argv:
        hand = [r for r in load() if not r["clause"].startswith(GEN_PREFIX)]
        rows = hand + generated(pn.IGNORABLE)
        with open(CORPUS, "w", encoding="utf-8") as f:
            f.writelines(json.dumps(r, ensure_ascii=True) + "\n" for r in rows)
        print(f"check_pii_corpus: wrote {len(rows)} rows ({len(hand)} hand-written + {len(rows) - len(hand)} generated)")
        return 0
    rows = load()
    if "--emit-sql" in argv:
        print(emit_sql(rows, open(MIGRATION, encoding="utf-8").read()))
        return 0
    return check(rows)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
