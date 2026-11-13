#!/usr/bin/env python3
"""YED-354 re-score of run 1b. Same private inputs as score.py (all_items.json, labels_0*.txt, labels_clay.txt,
companies.json; optional targets.json = {"targets": [names]}). Prints aggregates only.

What it changes versus score.py:
1. Labels: run-1 items keep their run-1 label; labels_clay.txt only labels the Clay items. score.py let the 60 anchor
   relabels in labels_clay.txt overwrite run-1 labels (1 true/false flip: 321 -> 320 $0 true signals).
2. Recall three ways: item many-to-one (score.py's number), item one-to-one (maximum bipartite matching), and
   fact level one-to-one. A fact = same company + same kind, dates chaining within 3 days, clustered per side, so
   syndicated copies across outlets and sources count once.
3. The pre-registered permutation null (shuffle company labels across the candidate's true items, 200x, seed 13)
   for every recall column, with its 95th percentile. Precision and coverage do not change under that shuffle
   by construction (it permutes company labels; it neither adds items nor changes the set of companies covered),
   so for those two columns the do-nothing baseline is the reference instead."""
import json, os, glob, random, statistics, sys, datetime as dt
from collections import defaultdict, Counter
sys.setrecursionlimit(10000)
D = os.path.dirname(os.path.abspath(__file__)) + "/"


def load(files):
    L = {}
    for f in files:
        for line in open(f):
            p = line.split()
            if len(p) >= 3 and p[0].isdigit(): L[int(p[0])] = (p[1].upper(), p[2].upper())
    return L


IT = {i["k"]: i for i in json.load(open(D + "all_items.json"))}
L1, LC = load(sorted(glob.glob(D + "labels_0*.txt"))), load([D + "labels_clay.txt"])
istrue = lambda lab: lab[0] in ("A", "B") and lab[1] != "O"
anchors = [k for k in LC if k in L1]
print(f"anchors {len(anchors)}: exact agree {sum(L1[k] == LC[k] for k in anchors)}, true/false flips "
      f"{sum(istrue(L1[k]) != istrue(LC[k]) for k in anchors)}")
for k, i in IT.items():
    i["cls"], i["kind"] = L1[k] if k in L1 else LC[k]
d = lambda s: dt.date.fromisoformat(s[:10])
COS = [c["name"] for c in json.load(open(D + "companies.json"))]
TG = set(json.load(open(D + "targets.json"))["targets"]) & set(COS) if os.path.exists(D + "targets.json") else set()
true = lambda i: istrue((i["cls"], i["kind"]))
ak_true = [i for i in IT.values() if i["src"] == "akta" and true(i)]
ok = lambda a, c: a["company"] == c["company"] and ((a.get("curl") and a["curl"] == c.get("curl")) or
                                                    (a["kind"] == c["kind"] and abs((d(a["published"]) - d(c["published"])).days) <= 3))


def facts(items):
    g = defaultdict(list)
    for i in items: g[(i["company"], i["kind"])].append(i)
    out = []
    for xs in g.values():
        xs.sort(key=lambda i: i["published"]); cur = [xs[0]]
        for x in xs[1:]:
            if (d(x["published"]) - d(cur[-1]["published"])).days <= 3: cur.append(x)
            else: out.append(cur); cur = [x]
        out.append(cur)
    return [{"company": c[0]["company"], "kind": c[0]["kind"], "dates": sorted({d(x["published"]) for x in c})} for c in out]


fok = lambda a, c: a["company"] == c["company"] and a["kind"] == c["kind"] and any(abs((x - y).days) <= 3 for x in a["dates"] for y in c["dates"])


def one_to_one(A, C, rel):
    adj, mc = [[j for j, c in enumerate(C) if rel(a, c)] for a in A], {}
    def aug(u, seen):
        for v in adj[u]:
            if v not in seen:
                seen.add(v)
                if v not in mc or aug(mc[v], seen): mc[v] = u; return True
        return False
    return sum(1 for u in range(len(A)) if aug(u, set()))


AF = facts(ak_true)
def recalls(t):
    return {"item_many_to_one": sum(1 for a in ak_true if any(ok(a, c) for c in t)) / len(ak_true),
            "item_one_to_one": one_to_one(ak_true, t, ok) / len(ak_true),
            "fact_one_to_one": one_to_one(AF, facts(t), fok) / len(AF)}
def null(t, n=200):
    rng, cos, acc = random.Random(13), [c["company"] for c in t], defaultdict(list)
    for _ in range(n):
        rng.shuffle(cos)
        for k, v in recalls([dict(c, company=co) for c, co in zip(t, cos)]).items(): acc[k].append(v)
    return {k: (statistics.mean(v), sorted(v)[int(0.95 * n)]) for k, v in acc.items()}


zero = [i for i in IT.values() if i["src"] not in ("akta", "clay")]
clay = [i for i in IT.values() if i["src"] == "clay"]
print(f"akta: {len(ak_true)} true items -> {len(AF)} facts")
for name, items in [("$0 union", zero), ("Clay alone", clay), ("$0 + Clay", zero + clay)]:
    t = [i for i in items if true(i)]; cov = {i["company"] for i in t}; CF = facts(t)
    r, nl = recalls(t), null(t)
    print(f"\n{name}: items {len(items)} true {len(t)} facts {len(CF)} precision {len(t) / len(items):.3f} "
          f"coverage {len(cov) / len(COS):.3f}" + (f" targets {len(cov & TG)}/{len(TG)}" if TG else ""))
    for k in r: print(f"  recall {k:17} {r[k]:.3f}   shuffle null mean {nl[k][0]:.3f}  p95 {nl[k][1]:.3f}   excess {r[k] - nl[k][0]:+.3f}")
    ak_k = Counter(f["kind"] for f in AF)
    print("  fact recall by kind:", " · ".join(f"{k} {one_to_one([f for f in AF if f['kind'] == k], [c for c in CF if c['kind'] == k], fok)}/{ak_k[k]}" for k in sorted(ak_k)))
