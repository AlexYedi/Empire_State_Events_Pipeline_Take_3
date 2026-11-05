#!/usr/bin/env python3
"""Lane 0 phase 3: link claims to the 39 new companies. conf>=0.7 -> write (tier llm>=0.7); <0.7 -> Fable queue."""
import json, sys, os, datetime as dt
sys.path.insert(0, "/Users/sameoldexpressions/Documents/GitHub/Empire_State_Events_Pipeline_Take_3/.claude/scripts")
import spine_client
d = os.path.dirname(os.path.abspath(__file__)) + "/"
APPLY = "--apply" in sys.argv
ids = json.load(open(d + "new_ids.json"))
B = {b["claim_id"]: b for b in json.load(open(d + "relink_batch.json"))}
rows, man, q = [], [], []
for p in json.load(open(d + "pred_new.json")):
    for l in p["links"]:
        assert l["company"] in ids
        if l["link"] and l["confidence"] >= 0.7:
            rows.append({"claim_id": p["claim_id"], "entity_type": "company", "entity_id": ids[l["company"]], "role": "about"})
            man.append({"claim_id": p["claim_id"], "company_id": ids[l["company"]], "tier": "llm>=0.7", "confidence": l["confidence"]})
        elif l["link"]:
            q.append({"claim_id": p["claim_id"], "text": B[p["claim_id"]]["text"], "company": l["company"]})
json.dump(q, open(d + "new_lowconf.json", "w"), indent=1)
print(len(rows), "rows;", len(q), "queued")
if not APPLY:
    spine_client.write("claim_entity", rows, dry_run=True); print("dry ok"); sys.exit()
st, body = spine_client.write("claim_entity", rows, prefer="resolution=ignore-duplicates,return=representation")
assert st in (200, 201), (st, body)
json.dump({"run": "lane0-company-new", "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "rows_planned": len(rows), "rows_written": len(body), "links": man}, open(d + "manifest_company_new.json", "w"), indent=1)
print("written", len(body))
