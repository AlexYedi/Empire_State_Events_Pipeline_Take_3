#!/usr/bin/env python3
"""Append Clay items to all_items.json with fresh k values, and write batch_clay.txt for the blinded labeller:
the Clay items shuffled together with 60 already-labelled anchor items (to measure labeller agreement with run 1)."""
import json, os, glob, random, re
D = os.path.dirname(os.path.abspath(__file__)) + "/"
IT = json.load(open(D + "all_items.json"))
IT = [i for i in IT if i["src"] != "clay"]  # idempotent
CL = json.load(open(D + "items_clay.json"))
L = {}
for f in sorted(glob.glob(D + "labels_0*.txt")):
    for line in open(f):
        p = line.split()
        if len(p) >= 3 and p[0].isdigit(): L[int(p[0])] = (p[1].upper(), p[2].upper())
k0 = max(i["k"] for i in IT) + 1
for n, c in enumerate(CL):
    c["k"] = k0 + n; c["curl"] = ""
IT += CL
json.dump(IT, open(D + "all_items.json", "w"), indent=1)
rng = random.Random(11)
anchors = rng.sample([i for i in IT if i["k"] in L], 60)
json.dump([a["k"] for a in anchors], open(D + "clay_anchor_keys.json", "w"))
rows = CL + anchors
rng.shuffle(rows)
with open(D + "batch_clay.txt", "w") as fh:
    for it in rows:
        t = re.sub(r"\s+", " ", it["title"] or "")[:200]
        s = ""  # titles only for every row, so Clay rows (no summary) are indistinguishable from anchors
        fh.write(f"{it['k']}|{it['company']}|{(it['published'] or '')[:10]}|{t}|{s}\n")
print("clay items", len(CL), "anchors", len(anchors), "batch rows", len(rows))
