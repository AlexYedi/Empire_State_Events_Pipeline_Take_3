#!/usr/bin/env python3
"""Lane 0 pilot writer: claim → topic links (claim_entity, role='about') through spine_client.

Tiers (calibrated on 368 held-out claims, 2026-11-04):
  T1 agree   LLM top theme == embedding-centroid theme            (~92% agreement)
  T2 conf    LLM top-topic confidence >= 0.8                       (~90% combined)
  T3 hold    everything else -> NOT written; queued for Fable adjudication
A secondary topic is written only if its own confidence >= 0.7.

Usage: lane0_write.py <dir> [--apply]   (default: dry run, prints the plan)
Writes <dir>/pilot_manifest.json (ids + tier + confidence only; no claim text).
"""
import json, sys, os, datetime as dt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spine_client  # noqa: E402  (the one guarded writer)

d = sys.argv[1].rstrip("/") + "/"
APPLY = "--apply" in sys.argv
V = {v["topic_id"]: v for v in json.load(open(d + "vocab.json"))}
E = {e["claim_id"]: e for e in json.load(open(d + "pilot_claims_full.json"))}
P = {p["claim_id"]: p for p in json.load(open(d + "pilot_pred.json"))}
assert set(P) == set(E), "prediction set != pilot set"

rows, manifest, held = [], [], []
for cid, p in P.items():
    tops = p.get("topics") or []
    if not tops:
        held.append({"claim_id": cid, "why": "none"}); continue
    t1 = tops[0]
    assert t1["topic_id"] in V, f"unknown topic {t1['topic_id']}"
    agree = V[t1["topic_id"]]["theme"] == E[cid]["emb_theme"]
    tier = "T1_agree" if agree else ("T2_conf" if t1["confidence"] >= 0.8 else None)
    if not tier:
        held.append({"claim_id": cid, "why": "low_conf_disagree", "lens": E[cid]["lens"]}); continue
    picks = [t1] + [t for t in tops[1:] if t["confidence"] >= 0.7]
    for t in picks:
        assert t["topic_id"] in V
        rows.append({"claim_id": cid, "entity_type": "topic", "entity_id": t["topic_id"], "role": "about"})
        manifest.append({"claim_id": cid, "topic_id": t["topic_id"], "tier": tier,
                         "confidence": t["confidence"], "lens": E[cid]["lens"],
                         "emb_margin": E[cid]["margin"]})

by = lambda k: {x: sum(1 for m in manifest if m[k] == x) for x in sorted({m[k] for m in manifest})}
claims_linked = len({m["claim_id"] for m in manifest})
print(f"plan: {len(rows)} link rows for {claims_linked}/{len(P)} claims; held {len(held)} "
      f"(none={sum(h['why']=='none' for h in held)}); tiers {by('tier')}; lens {by('lens')}")

if not APPLY:
    spine_client.write("claim_entity", rows, dry_run=True)  # runs the guard on every row
    print("dry run: guard passed on all rows; nothing written"); sys.exit(0)

stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
written = 0
for i in range(0, len(rows), 100):
    status, body = spine_client.write("claim_entity", rows[i:i + 100],
                                      prefer="resolution=ignore-duplicates,return=representation")
    written += len(body) if isinstance(body, list) else 0
    print(f"batch {i // 100}: HTTP {status}, {len(body) if isinstance(body, list) else body} rows")
json.dump({"run": "lane0-pilot", "started_at": stamp, "rows_planned": len(rows), "rows_written": written,
           "held": held, "links": manifest}, open(d + "pilot_manifest.json", "w"), indent=1)
print(f"written {written}/{len(rows)}; manifest -> {d}pilot_manifest.json")
