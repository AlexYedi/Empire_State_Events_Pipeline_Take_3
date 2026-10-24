#!/usr/bin/env python3
"""Score extracted Q3 metrics against the answer key, always next to the do-nothing baseline.

    python3 eval/score.py PREDICTIONS [--key answer_key/q3_2026_metrics.json]
                                      [--baseline eval/baseline_carry_forward.json] [--verbose]

PREDICTIONS is a directory of <company_id>.json files (one schema-shaped record each)
or a single JSON file with {"companies": [...]}. Missing companies or fields count as null.
Stdlib only. Rules:
  money (monthly_revenue, arr, monthly_burn, cash): within 1% and same currency
  runway_months: within 0.5;  headcount, customers: exact;  revenue_type: exact
  truth null -> correct only if the prediction is null too (abstention is scored)
  traceback: correct, reported value whose span is in the key's file and overlaps the key span
"""

import argparse
import json
import os
import sys

PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUMERIC = ["monthly_revenue", "arr", "monthly_burn", "cash", "runway_months", "headcount", "customers"]
MONEY = {"monthly_revenue", "arr", "monthly_burn", "cash"}
SCORED = NUMERIC + ["revenue_type"]


def load(path):
    if os.path.isdir(path):
        recs = []
        for name in sorted(os.listdir(path)):
            if name.endswith(".json"):
                with open(os.path.join(path, name), encoding="utf-8") as fh:
                    obj = json.load(fh)
                recs.extend(obj["companies"] if isinstance(obj, dict) and "companies" in obj else [obj])
    else:
        with open(path, encoding="utf-8") as fh:
            obj = json.load(fh)
        recs = obj["companies"] if isinstance(obj, dict) and "companies" in obj else obj
    return {r["company_id"]: r for r in recs}


def num(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v.replace(",", ""))
        except ValueError:
            return None
    return None


def value_ok(field, truth, pred):
    tv = truth.get("value")
    pv = pred.get("value") if pred else None
    if tv is None:
        return pv is None
    p = num(pv)
    if p is None:
        return False
    if field in MONEY:
        if (pred.get("currency") or "USD") != (truth.get("currency") or "USD"):
            return False
        return p == 0 if tv == 0 else abs(p - tv) <= 0.01 * abs(tv)
    if field == "runway_months":
        return abs(p - tv) <= 0.5
    return p == tv


def span_ok(truth, pred):
    if not pred or not truth.get("source_span") or not pred.get("source_span"):
        return False
    if os.path.normpath(pred.get("source_file") or "") != os.path.normpath(truth["source_file"]):
        return False
    ps, pe = pred["source_span"].get("start"), pred["source_span"].get("end")
    if not isinstance(ps, int) or not isinstance(pe, int):
        return False
    spans = [truth["source_span"]] + [{"start": a["start"], "end": a["end"]} for a in truth.get("alt_spans", [])]
    return any(ps < s["end"] and s["start"] < pe for s in spans)


def score(key, preds):
    c = {"cells": 0, "correct": 0, "rep": 0, "rep_ok": 0, "null": 0, "null_ok": 0, "trace_n": 0, "trace_ok": 0,
         "tp": 0, "fp": 0, "fn": 0}
    per_field = {f: [0, 0] for f in SCORED}
    misses = []
    for cid, t in sorted(key.items()):
        p = preds.get(cid, {})
        pf = p.get("fields", {}) if isinstance(p.get("fields"), dict) else {}
        for f in SCORED:
            if f == "revenue_type":
                tv, ok = t.get("revenue_type"), t.get("revenue_type") == p.get("revenue_type")
            else:
                tv = t["fields"][f]["value"]
                ok = value_ok(f, t["fields"][f], pf.get(f))
            c["cells"] += 1
            c["correct"] += ok
            per_field[f][0] += ok
            per_field[f][1] += 1
            if tv is None:
                c["null"] += 1
                c["null_ok"] += ok
            else:
                c["rep"] += 1
                c["rep_ok"] += ok
                if ok and f != "revenue_type":
                    c["trace_n"] += 1
                    c["trace_ok"] += span_ok(t["fields"][f], pf.get(f))
            if not ok:
                pv = p.get("revenue_type") if f == "revenue_type" else (pf.get(f) or {}).get("value")
                misses.append(f"{cid} {f}: expected {tv!r}, got {pv!r}")
        tf = {x["flag"] for x in t.get("flags", [])}
        pfl = {x["flag"] if isinstance(x, dict) else x for x in p.get("flags", []) or []}
        c["tp"] += len(tf & pfl)
        c["fp"] += len(pfl - tf)
        c["fn"] += len(tf - pfl)
        for fl in sorted(tf - pfl):
            misses.append(f"{cid} flag missed: {fl}")
        for fl in sorted(pfl - tf):
            misses.append(f"{cid} flag spurious: {fl}")
    prec = c["tp"] / (c["tp"] + c["fp"]) if c["tp"] + c["fp"] else 0.0
    rec = c["tp"] / (c["tp"] + c["fn"]) if c["tp"] + c["fn"] else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return {
        "field_accuracy": c["correct"] / c["cells"],
        "reported_field_accuracy": c["rep_ok"] / c["rep"],
        "abstention_accuracy": c["null_ok"] / c["null"] if c["null"] else None,
        "flag_precision": prec, "flag_recall": rec, "flag_f1": f1,
        "traceback_rate": c["trace_ok"] / c["trace_n"] if c["trace_n"] else 0.0,
        "per_field": {f: v[0] / v[1] for f, v in per_field.items()},
        "counts": {"cells": c["cells"], "reported": c["rep"], "null": c["null"], "traceback_eligible": c["trace_n"]},
    }, misses


def pct(x):
    return "   n/a" if x is None else f"{100 * x:5.1f}%"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("predictions")
    ap.add_argument("--key", default=os.path.join(PACK, "answer_key", "q3_2026_metrics.json"))
    ap.add_argument("--baseline", default=os.path.join(PACK, "eval", "baseline_carry_forward.json"))
    ap.add_argument("--verbose", action="store_true", help="list every miss for the predictions")
    a = ap.parse_args()

    key = load(a.key)
    pred_s, misses = score(key, load(a.predictions))
    base_s, _ = score(key, load(a.baseline))

    rows = [("Field accuracy (all cells)", "field_accuracy"),
            ("  on reported fields", "reported_field_accuracy"),
            ("  abstention (truth = null)", "abstention_accuracy"),
            ("Flag precision", "flag_precision"), ("Flag recall", "flag_recall"), ("Flag F1", "flag_f1"),
            ("Traceback (span overlaps key)", "traceback_rate")]
    n = pred_s["counts"]
    print(f"Scoring {a.predictions}")
    print(f"against {a.key}  ({len(key)} companies, {n['cells']} cells: {n['reported']} reported, {n['null']} null)\n")
    print(f"{'Metric':34} {'Predictions':>11} {'Baseline':>9} {'Delta':>8}")
    print("-" * 65)
    for label, k in rows:
        pv, bv = pred_s[k], base_s[k]
        d = "" if pv is None or bv is None else f"{100 * (pv - bv):+6.1f}pt"
        print(f"{label:34} {pct(pv):>11} {pct(bv):>9} {d:>8}")
    print("\nPer field")
    for f in SCORED:
        print(f"  {f:32} {pct(pred_s['per_field'][f]):>11} {pct(base_s['per_field'][f]):>9}")
    print("\nBaseline = Q2 values carried forward unchanged. Read every number against it.")
    if a.verbose and misses:
        print(f"\nMisses ({len(misses)}):")
        for m in misses:
            print("  " + m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
