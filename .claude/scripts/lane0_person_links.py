#!/usr/bin/env python3
"""Lane 0 phase 4: roster-only claim→person links (YED-332). Existing person rows only; no person created.
Rule: Fable verdict conf >= 0.7 and role != none; 'both' writes about + asserted_by. Usage: write_person.py [--apply]"""
import json, sys, os, datetime as dt
REPO = "/Users/sameoldexpressions/Documents/GitHub/Empire_State_Events_Pipeline_Take_3"
sys.path.insert(0, os.path.join(REPO, ".claude", "scripts")); import spine_client
D = os.path.dirname(os.path.abspath(__file__)) + "/"
H = json.load(open(D + "hits.json")); V = {v["k"]: v for v in json.load(open(D + "adjudicate_out.json"))}
assert len(V) == len(H)
rows, man, skipped = [], [], []
for k, h in enumerate(H):
    v = V[k]
    if v["role"] == "none" or v["conf"] < 0.7:
        skipped.append({"claim_id": h["claim_id"], "person_id": h["person_id"], "role": v["role"], "conf": v["conf"]}); continue
    for role in (["about", "asserted_by"] if v["role"] == "both" else [v["role"]]):
        rows.append({"claim_id": h["claim_id"], "entity_type": "person", "entity_id": h["person_id"], "role": role})
        man.append({"claim_id": h["claim_id"], "person_id": h["person_id"], "role": role, "conf": v["conf"], "lens": h["lens"], "tier": "roster-name+fable"})
print(f"plan {len(rows)} rows / {len({m['claim_id'] for m in man})} claims / {len({m['person_id'] for m in man})} people; skipped {len(skipped)}")
if "--apply" not in sys.argv:
    spine_client.write("claim_entity", rows, dry_run=True); print("dry run ok"); sys.exit()
st, body = spine_client.write("claim_entity", rows, prefer="resolution=ignore-duplicates,return=representation")
assert st in (200, 201), (st, body)
n = len(body) if isinstance(body, list) else 0
json.dump({"run": "lane0-phase4-person", "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "rows_planned": len(rows), "rows_written": n, "skipped": skipped, "links": man}, open(D + "manifest_person.json", "w"), indent=1)
print("written", n, "/", len(rows))
