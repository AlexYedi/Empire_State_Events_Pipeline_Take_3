#!/usr/bin/env python3
"""Score the bake-off. Inputs: all_items.json + labels_NN.txt ("k CLS KIND" per line). Prints the metric table, writes result.json.
True signal = class A or B. Recall vs akta is measured inside each company's akta window (akta returned its 25 most recent,
so high-volume companies only cover 1-2 days). Match = same canonical URL, or same (company, kind) within ±3 days."""
import json, os, glob, random, statistics, datetime as dt
from collections import defaultdict, Counter
D = os.path.dirname(os.path.abspath(__file__)) + "/"
IT = {i["k"]: i for i in json.load(open(D + "all_items.json"))}
L = {}
for f in sorted(glob.glob(D + "labels_*.txt")):
    for line in open(f):
        p = line.split()
        if len(p) >= 3 and p[0].isdigit(): L[int(p[0])] = (p[1].upper(), p[2].upper())
missing = [k for k in IT if k not in L]
print(f"items {len(IT)} labelled {len(L)} missing {len(missing)}")
for k, (c, kd) in L.items():
    if k in IT: IT[k]["cls"], IT[k]["kind"] = c, kd
d = lambda s: dt.date.fromisoformat(s[:10]) if s else None
COS = [c["name"] for c in json.load(open(D + "companies.json"))]
true = lambda i: i.get("cls") in ("A", "B") and i.get("kind") not in (None, "O")
by_src = defaultdict(list)
for i in IT.values(): by_src[i["src"]].append(i)
ak = by_src["akta"]
win = {}
for i in ak:
    t = d(i["published"]); lo, hi = win.get(i["company"], (t, t)); win[i["company"]] = (min(lo, t), max(hi, t))
ak_true = [i for i in ak if true(i)]


def match(a, pool):
    for c in pool:
        if c["company"] != a["company"]: continue
        if a["curl"] and c["curl"] == a["curl"]: return c
        if c["kind"] == a["kind"] and abs((d(c["published"]) - d(a["published"])).days) <= 3: return c
    return None


def metrics(name, items, cost=0.0):
    labelled = [i for i in items if "cls" in i]
    t = [i for i in labelled if true(i)]
    prec = len(t) / len(labelled) if labelled else 0
    cov_cos = {i["company"] for i in t}
    hits = [(a, match(a, t)) for a in ak_true]
    rec = sum(1 for a, m in hits if m) / len(ak_true) if ak_true else 0
    lags = [(d(m["published"]) - d(a["published"])).days for a, m in hits if m]
    # novelty: true items with no akta true match of same company+kind ±3d
    nov = sum(1 for c in t if not any(a["company"] == c["company"] and a["kind"] == c["kind"] and abs((d(a["published"]) - d(c["published"])).days) <= 3 for a in ak_true))
    # permutation null: shuffle company labels across candidate true items
    rng, null = random.Random(13), []
    cos = [c["company"] for c in t]
    for _ in range(200):
        rng.shuffle(cos)
        sh = [dict(c, company=co) for c, co in zip(t, cos)]
        null.append(sum(1 for a in ak_true if match(a, sh)) / len(ak_true) if ak_true else 0)
    return {"candidate": name, "items": len(items), "labelled": len(labelled), "true": len(t), "precision": round(prec, 3),
            "coverage": round(len(cov_cos) / len(COS), 3), "companies_covered": len(cov_cos), "recall_vs_akta": round(rec, 3),
            "recall_null_mean": round(statistics.mean(null), 3), "novel_true": nov,
            "median_lag_days_vs_akta": statistics.median(lags) if lags else None, "cost_usd": cost,
            "kinds": dict(Counter(i["kind"] for i in t))}


zero = [i for s, v in by_src.items() if s != "akta" for i in v]
rows = [metrics("akta (reference)", ak)]
for s in sorted(by_src):
    if s != "akta": rows.append(metrics(f"$0: {s}", by_src[s]))
rows.append(metrics("$0 stack (union)", zero))
ak_cov = {i["company"] for i in ak_true}
rows[0]["recall_vs_akta"] = 1.0
for r in rows:
    print(f"{r['candidate']:20} items {r['items']:5} true {r['true']:4} P {r['precision']:.2f} cov {r['coverage']:.2f} "
          f"R {r['recall_vs_akta']:.2f} (null {r['recall_null_mean']:.2f}) novel {r['novel_true']:4} lag {r['median_lag_days_vs_akta']} kinds {r['kinds']}")
# per-company coverage table for the union vs akta
zt = {i["company"] for i in zero if true(i)}
print("akta-only companies:", sorted(ak_cov - zt)); print("$0-only companies:", sorted(zt - ak_cov))
print("neither:", sorted(set(COS) - ak_cov - zt))
json.dump({"rows": rows, "akta_true": len(ak_true), "akta_only": sorted(ak_cov - zt), "zero_only": sorted(zt - ak_cov),
           "neither": sorted(set(COS) - ak_cov - zt)}, open(D + "result.json", "w"), indent=1)
