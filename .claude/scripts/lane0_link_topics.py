#!/usr/bin/env python3
"""Lane 0 full-run writer (Phase 1: unlinked claims). claim_entity(role='about') via spine_client only.

Rule (Fable-calibrated 2026-11-04: LLM conf>=0.7 endorsed 95% on the hardest held-out cases):
  write   top topic conf >= 0.7 (+ any secondary topic with its own conf >= 0.7)   tier "llm>=0.7"
  queue   top topic conf <  0.7  -> fable_queue.json (adjudicated later, then written as "fable")
  none    no topical subject      -> recorded, never linked
Usage: lane0_full_write.py <dir> <pred_NN.json>... [--apply]
Manifests: <dir>/full/manifest_<NN>.json (ids, tier, confidence, lens; no claim text).
"""
import json, sys, os, datetime as dt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spine_client  # noqa: E402

d = sys.argv[1].rstrip("/") + "/"
APPLY = "--apply" in sys.argv
preds = [a for a in sys.argv[2:] if a.endswith(".json")]
V = {v["topic_id"]: v for v in json.load(open(d + "vocab.json"))}
LENS = json.load(open(d + "full/lens.json"))
qpath = d + "full/fable_queue.json"
queue = json.load(open(qpath)) if os.path.exists(qpath) else []
qids = {q["claim_id"] for q in queue}
tot = {"rows": 0, "claims": 0, "queued": 0, "none": 0}
for pf in preds:
    tag = os.path.basename(pf).replace("pred_", "").replace(".json", "")
    P = json.load(open(pf))
    rows, man, none = [], [], []
    for p in P:
        cid, tops = p["claim_id"], p.get("topics") or []
        assert cid in LENS, f"{cid} not in the unlinked set"
        if not tops:
            none.append(cid); continue
        assert all(t["topic_id"] in V for t in tops), f"unknown topic in {cid}"
        if tops[0]["confidence"] < 0.7:
            if cid not in qids:
                queue.append({"claim_id": cid, "llm_topics": tops}); qids.add(cid)
            continue
        for t in [tops[0]] + [t for t in tops[1:] if t["confidence"] >= 0.7]:
            rows.append({"claim_id": cid, "entity_type": "topic", "entity_id": t["topic_id"], "role": "about"})
            man.append({"claim_id": cid, "topic_id": t["topic_id"], "tier": os.environ.get("LANE0_TIER", "llm>=0.7"),
                        "confidence": t["confidence"], "lens": LENS[cid]})
    linked = len({m["claim_id"] for m in man})
    print(f"[{tag}] {len(P)} claims: write {len(rows)} rows/{linked} claims · queue "
          f"{sum(1 for p in P if p['claim_id'] in qids)} · none {len(none)}")
    if not APPLY:
        spine_client.write("claim_entity", rows, dry_run=True); continue
    written = 0
    for i in range(0, len(rows), 200):
        st, body = spine_client.write("claim_entity", rows[i:i + 200],
                                      prefer="resolution=ignore-duplicates,return=representation")
        assert st in (200, 201), f"HTTP {st}: {body}"
        written += len(body) if isinstance(body, list) else 0
    json.dump({"run": f"lane0-full-{tag}", "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
               "rows_planned": len(rows), "rows_written": written, "none": none, "links": man},
              open(d + f"full/manifest_{tag}.json", "w"), indent=1)
    print(f"[{tag}] written {written}/{len(rows)}")
    tot["rows"] += written; tot["claims"] += linked
    tot["none"] += len(none)
json.dump(queue, open(qpath, "w"), indent=1)
tot["queued"] = len(queue)
print("totals" + (" (APPLIED)" if APPLY else " (dry run)"), tot)
