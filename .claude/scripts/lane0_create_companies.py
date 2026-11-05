#!/usr/bin/env python3
"""Lane 0 phase 3: create missing operating companies (>=3 claim mentions) via spine_client. Search-before-create done (prod lower(name) like + akta company_search)."""
import json, sys, os, datetime as dt, collections
sys.path.insert(0, "/Users/sameoldexpressions/Documents/GitHub/Empire_State_Events_Pipeline_Take_3/.claude/scripts")
import spine_client
d = os.path.dirname(os.path.abspath(__file__)) + "/"
APPLY = "--apply" in sys.argv
mentions = dict((n, k) for n, k in json.load(open(d + "unlisted_ranked.json")))
rows = []
for name, akta, web, desc in json.load(open(d + "new_companies.json")):
    rows.append({"name": name, "website": web, "description": desc, "industry": [],
                 "company_type": "operating", "source": "lane0_company_gap",
                 "metadata": {"created_by": "lane0-phase3", "claim_mentions": mentions[name], "akta_uuid": akta}})
print(len(rows), "rows")
if not APPLY:
    spine_client.write("company", rows, dry_run=True); print("dry run ok"); sys.exit()
st, body = spine_client.write("company", rows, prefer="resolution=ignore-duplicates,return=representation")
assert st in (200, 201), (st, body)
json.dump({"run": "lane0-company-create", "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "created": [{"id": b["id"], "name": b["name"]} for b in body]}, open(d + "manifest_company_create.json", "w"), indent=1)
print("created", len(body))
