#!/usr/bin/env python3
"""Lane 0 phase 2 planner: compare the new tagger against legacy topic links. Read-only; writes plan files.
keep    old topic is among the new tags (any confidence)
add     new topics at conf >= 0.7 that the claim doesn't already carry (pure additions)
dispute old topic not among the new tags -> blinded Fable chooses between old / new / both / NONE
"""
import json, sys, glob, random, collections
d = sys.argv[1].rstrip("/") + "/"
V = {v["topic_id"]: v for v in json.load(open(d + "vocab.json"))}
L = {x["claim_id"]: x for x in json.load(open(d + "retag/legacy.json"))}
P = {}
for f in sorted(glob.glob(d + "retag/pred_*.json")):
    for p in json.load(open(f)): P[p["claim_id"]] = p
missing = set(L) - set(P)
print("legacy", len(L), "predicted", len(P), "missing", len(missing))
keep, add, disputes = [], [], []
stat = collections.Counter()
rng = random.Random(13)
for cid, x in L.items():
    if cid not in P: continue
    old = set(x["old_topics"]); new = P[cid].get("topics") or []
    new_ids = {t["topic_id"] for t in new}
    for t in new:
        if t["topic_id"] not in old and t["confidence"] >= 0.7:
            add.append({"claim_id": cid, "topic_id": t["topic_id"], "confidence": t["confidence"]})
    for o in old:
        if o in new_ids:
            keep.append({"claim_id": cid, "topic_id": o}); stat["keep"] += 1; continue
        stat["dispute_none" if not new else "dispute"] += 1
        opts = [("old", o)] + [("new", t["topic_id"]) for t in new if t["topic_id"] != o][:2]
        opts = [(s, t) for s, t in opts if t in V] or opts
        rng.shuffle(opts)
        letters = "ABC"
        disputes.append({"claim_id": cid, "text": x["text"],
                         "options": {letters[i]: {"topic": V[t]["topic"] if t in V else "(retired topic)",
                                                  "theme": V[t]["theme"] if t in V else "(none)"} for i, (s, t) in enumerate(opts)},
                         "_key": {letters[i]: {"src": s, "topic_id": t} for i, (s, t) in enumerate(opts)}})
stat["add_rows"] = len(add)
print(dict(stat), "disputes", len(disputes))
json.dump({"keep": keep, "add": add}, open(d + "retag/plan_keep_add.json", "w"))
json.dump([{k: v for k, v in q.items() if k != "_key"} for q in disputes], open(d + "retag/disputes.json", "w"))
json.dump({q["claim_id"]: q["_key"] for q in disputes}, open(d + "retag/disputes_key.json", "w"))
