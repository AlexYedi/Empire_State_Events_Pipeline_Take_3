#!/usr/bin/env python3
"""identity_probe — the standing identity-hygiene probe for the Market-Intelligence graph (YED-47, item 4).

READ-ONLY. Every request is a GET through spine_client (ADR-9); the probe never writes. Run it by hand
(the weekly rigor review that used to call it was retired 2026-09-28); its rows are the "identity ambiguity"
and "identity duplicates" counts.

What it measures, per table (company · person · topic):
  rows                    live rows (tombstones excluded from every duplicate count below)
  exact_dupes             groups sharing lower(name)            — person only can hold these (company/topic have
                                                                  lower(name) uniqueness live)
  qualifier_twins         groups whose names differ only by a trailing '(Qualifier)': 'AWS' / 'AWS (Amazon)'
  host_collisions         (company) groups sharing a website host — the tier's own signal
  linkedin_collisions     (person) groups sharing a linkedin_url
  tombstones              rows with metadata.merged_into (soft-merged away; ADR-4 D3 — never deleted)
  tombstones_with_edges   tombstones that still carry an edge or a person.company_id — a merge left a
                          colliding edge behind (by design) or a producer wrote to a tombstone (a bug)
And two windowed counts from the ledgers:
  ambiguity_30d           DISTINCT (table, name) entries in .claude/artifacts/identity-ambiguity.jsonl in the
                          window — the DDL re-trigger (>=10 in 30 days reopens the parked name_norm/alias/merge
                          DDL). Distinct, so one ambiguity re-surfaced by re-runs cannot fire it.
  merges_30d / reverts_30d  from .claude/artifacts/identity-merges.jsonl

Null baseline (registry rule, YED-212): a do-nothing policy scores ambiguity_30d = 0 — because nothing RAN,
not because identity is clean. So the probe prints the number of producer ledger sessions in the window next
to it; 0 ambiguities over 0 runs is "no data", never "healthy". The duplicate counts have a real floor: the
2026-09-27 baseline is 1 exact person dupe · 3 company twins · 3 topic twins · 2 host collisions.

Usage:
  .venv/bin/python .claude/scripts/identity_probe.py            # human report
  .venv/bin/python .claude/scripts/identity_probe.py --json     # machine summary (one object)
  .venv/bin/python .claude/scripts/identity_probe.py --window-days 30 --selftest
Exit 0 always — it reports; the registry names the action and Alex takes it.
"""
from __future__ import annotations
import argparse, collections, datetime, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from spine_client import req  # noqa: E402
from substrate import AMBIGUITY_LEDGER, MERGE_LOG, ROOT, split_qualifier, web_host  # noqa: E402

SELECT = {
    "company": "id,name,website,source,metadata,created_at",
    "person": "id,name,linkedin_url,company_id,source,metadata,created_at",
    "topic": "id,name,source,metadata,created_at",
}
EDGE_TABLES = ("event_entity", "claim_entity", "document_entity")
RE_TRIGGER = 10          # distinct ambiguities in the window that reopen the parked DDL half


def all_rows(table: str, select: str, page: int = 1000) -> list[dict]:
    out, off = [], 0
    while True:
        st, rows = req("GET", f"/{table}?select={select}&limit={page}&offset={off}")
        if st != 200 or not isinstance(rows, list):
            raise SystemExit(f"identity_probe: GET /{table} -> {st}: {str(rows)[:200]}")
        out += rows
        if len(rows) < page:
            return out
        off += page


def _key(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip().lower())


def _li(url: str | None) -> str | None:
    if not url:
        return None
    return re.sub(r"^https?://(www\.)?", "", url.strip().lower()).rstrip("/") or None


def group(rows: list[dict], fn) -> dict[str, list[dict]]:
    """Groups of size >= 2 keyed by fn(row); rows where fn returns None are skipped."""
    g: dict[str, list[dict]] = collections.defaultdict(list)
    for r in rows:
        k = fn(r)
        if k:
            g[k].append(r)
    return {k: v for k, v in g.items() if len(v) > 1}


def probe_table(table: str, rows: list[dict]) -> dict:
    tomb = [r for r in rows if (r.get("metadata") or {}).get("merged_into")]
    live = [r for r in rows if not (r.get("metadata") or {}).get("merged_into")]
    out = {"rows": len(live), "tombstones": len(tomb),
           "exact_dupes": group(live, lambda r: _key(r["name"])),
           "qualifier_twins": {k: v for k, v in group(live, lambda r: _key(split_qualifier(r["name"])[0])).items()
                               if len({_key(x["name"]) for x in v}) > 1}}
    if table == "company":
        out["host_collisions"] = group(live, lambda r: web_host(r.get("website")))
    if table == "person":
        out["linkedin_collisions"] = group(live, lambda r: _li(r.get("linkedin_url")))
    out["_tombstone_ids"] = [r["id"] for r in tomb]
    return out


def tombstones_with_edges(table: str, ids: list[str]) -> dict[str, int]:
    """id -> number of edges (+ person.company_id refs for a company) still pointing at the tombstone."""
    counts: dict[str, int] = collections.Counter()
    for i in range(0, len(ids), 50):
        chunk = ",".join(ids[i:i + 50])
        for et in EDGE_TABLES:
            st, rows = req("GET", f"/{et}?entity_type=eq.{table}&entity_id=in.({chunk})&select=entity_id")
            for r in (rows if isinstance(rows, list) else []):
                counts[r["entity_id"]] += 1
        if table == "company":
            st, rows = req("GET", f"/person?company_id=in.({chunk})&select=company_id")
            for r in (rows if isinstance(rows, list) else []):
                counts[r["company_id"]] += 1
    return dict(counts)


def read_jsonl(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except ValueError:
                out.append({"_corrupt": line})
    return out


def windowed(rows: list[dict], days: int, now: datetime.datetime | None = None) -> list[dict]:
    now = now or datetime.datetime.now(datetime.timezone.utc)
    since = now - datetime.timedelta(days=days)
    keep = []
    for r in rows:
        ts = r.get("ts")
        try:
            when = datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
        except (TypeError, ValueError):
            continue
        if when >= since:
            keep.append(r)
    return keep


def ledger_summary(days: int) -> dict:
    amb = read_jsonl(AMBIGUITY_LEDGER)
    mrg = read_jsonl(MERGE_LOG)
    w = windowed(amb, days)
    distinct = {(r.get("table"), _key(r.get("name", ""))) for r in w}
    return {"ledger_exists": os.path.exists(AMBIGUITY_LEDGER), "ambiguity_entries_window": len(w),
            "ambiguity_distinct_window": len(distinct),
            "ambiguity_sessions_window": len({r.get("session") for r in w}),
            "merges_window": sum(1 for r in windowed(mrg, days) if r.get("event") == "merge"),
            "reverts_window": sum(1 for r in windowed(mrg, days) if r.get("event") == "revert"),
            "re_trigger": RE_TRIGGER, "re_trigger_fired": len(distinct) >= RE_TRIGGER}


def run(days: int) -> dict:
    report: dict = {"probed_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "window_days": days, "tables": {}}
    for table, sel in SELECT.items():
        t = probe_table(table, all_rows(table, sel))
        ids = t.pop("_tombstone_ids")
        t["tombstones_with_edges"] = tombstones_with_edges(table, ids) if ids else {}
        report["tables"][table] = t
    report["ledgers"] = ledger_summary(days)
    report["pairs_total"] = sum(len(t["exact_dupes"]) + len(t["qualifier_twins"]) for t in report["tables"].values())
    return report


def _fmt_group(v: list[dict]) -> str:
    return " | ".join(f"{r['name']} [{r['id'][:8]} · {r.get('source') or '—'}"
                      + (f" · {web_host(r.get('website'))}" if r.get("website") else "") + "]" for r in v)


def print_report(rep: dict) -> None:
    print(f"identity probe — {rep['probed_at']} · window {rep['window_days']}d · READ-ONLY")
    for table, t in rep["tables"].items():
        extra = ""
        if "host_collisions" in t:
            extra += f" host_collisions={len(t['host_collisions'])}"
        if "linkedin_collisions" in t:
            extra += f" linkedin_collisions={len(t['linkedin_collisions'])}"
        print(f"  {table:8s} rows={t['rows']} exact_dupes={len(t['exact_dupes'])} qualifier_twins={len(t['qualifier_twins'])}"
              f"{extra} tombstones={t['tombstones']} tombstones_with_edges={len(t['tombstones_with_edges'])}")
        for label in ("exact_dupes", "qualifier_twins", "host_collisions", "linkedin_collisions"):
            for k, v in (t.get(label) or {}).items():
                print(f"     {label[:-1] if label.endswith('s') else label:17s} {_fmt_group(v)}")
        for tid, n in t["tombstones_with_edges"].items():
            print(f"     tombstone-with-edges {tid[:8]} still carries {n} edge(s)/ref(s) — a merge kept colliding edges (ok) or a producer wrote to it (bug)")
    L = rep["ledgers"]
    if not L["ledger_exists"]:
        print(f"  ledger   {os.path.relpath(AMBIGUITY_LEDGER, ROOT)} ABSENT — no live producer run has surfaced an ambiguity yet "
              f"(that is 'no data', not 'no ambiguities')")
    else:
        print(f"  ledger   ambiguities in window: {L['ambiguity_entries_window']} entries / {L['ambiguity_distinct_window']} distinct "
              f"across {L['ambiguity_sessions_window']} session(s) · re-trigger at {L['re_trigger']} distinct → "
              f"{'FIRED — reopen the parked DDL half' if L['re_trigger_fired'] else 'not fired'}")
    print(f"  merges   {L['merges_window']} merge(s), {L['reverts_window']} revert(s) in window")
    acts = []
    if rep["pairs_total"]:
        acts.append(f"{rep['pairs_total']} candidate pair(s) → propose each with "
                    f"`substrate.py merge --table T --from A --into B --dry-run`; Alex approves every merge")
    if any(t["tombstones_with_edges"] for t in rep["tables"].values()):
        acts.append("tombstones still carrying edges → confirm they are merge-kept collisions, not producer writes")
    if L["re_trigger_fired"]:
        acts.append("DDL re-trigger fired → move the parked YED-47 DDL issue to Todo")
    print("  action   " + ("; ".join(acts) if acts else "none — identity holding"))


def selftest() -> bool:
    checks = []

    def ok(name, cond):
        checks.append((name, bool(cond)))
    rows = [{"id": "a" * 36, "name": "AWS", "website": "https://aws.amazon.com", "metadata": {}},
            {"id": "b" * 36, "name": "AWS (Amazon)", "website": "https://www.aws.amazon.com/", "metadata": {}},
            {"id": "c" * 36, "name": "Zed", "website": None, "metadata": {"merged_into": "a" * 36}},
            {"id": "d" * 36, "name": "Nori", "website": "https://noriagentic.com", "metadata": None}]
    t = probe_table("company", rows)
    ok("tombstone excluded from live rows", t["rows"] == 3 and t["tombstones"] == 1 and t["_tombstone_ids"] == ["c" * 36])
    ok("qualifier twin found", list(t["qualifier_twins"]) == ["aws"])
    ok("host collision found (www folded)", list(t["host_collisions"]) == ["aws.amazon.com"])
    ok("no exact dupes", t["exact_dupes"] == {})
    p = probe_table("person", [{"id": "e" * 36, "name": "Angie Jones", "metadata": {}}, {"id": "f" * 36, "name": "angie  jones", "metadata": {}},
                               {"id": "g" * 36, "name": "Pat", "linkedin_url": "https://www.linkedin.com/in/pat/", "metadata": {}},
                               {"id": "h" * 36, "name": "Pat L", "linkedin_url": "linkedin.com/in/pat", "metadata": {}}])
    ok("exact person dupe found across case/spacing", list(p["exact_dupes"]) == ["angie jones"])
    ok("linkedin collision found across scheme/www/slash", list(p["linkedin_collisions"]) == ["linkedin.com/in/pat"])
    now = datetime.datetime(2026, 9, 27, tzinfo=datetime.timezone.utc)
    w = windowed([{"ts": "2026-09-20T00:00:00Z"}, {"ts": "2026-08-01T00:00:00Z"}, {"ts": "bad"}, {}], 30, now)
    ok("window keeps only in-window, well-formed timestamps", len(w) == 1)
    ok("re-trigger counts DISTINCT (table,name), not lines",
       len({(r.get("table"), _key(r.get("name", ""))) for r in [{"table": "company", "name": "X"}] * 12}) == 1)
    fail = sum(0 if g else 1 for _, g in checks)
    for name, g in checks:
        print(f"  {'✓' if g else '✗'} {name}")
    print(f"selftest: {len(checks) - fail}/{len(checks)} pass")
    return fail == 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--window-days", type=int, default=30)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return 0 if selftest() else 1
    rep = run(a.window_days)
    if a.json:
        print(json.dumps(rep, default=str))
    else:
        print_report(rep)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
