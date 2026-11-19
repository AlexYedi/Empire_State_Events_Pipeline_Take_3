#!/usr/bin/env python3
"""Lane 0 phase 3: create missing operating companies (>=3 claim mentions) via spine_client. Search-before-create done (prod lower(name) like + akta company_search).
0022 (YED-384): rows whose name key (substrate.norm_company = public.norm_name_v1) matches an existing company,
or an earlier row in this batch, are skipped before the POST. `ignore-duplicates` only covers the primary key, so a
name-key collision would otherwise fail the whole batch on company_name_norm_uq."""
import json, sys, os, datetime as dt, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spine_client
from substrate import norm_company
d = os.path.dirname(os.path.abspath(__file__)) + "/"
APPLY = "--apply" in sys.argv
mentions = dict((n, k) for n, k in json.load(open(d + "unlisted_ranked.json")))
st, existing = spine_client.req("GET", "/company?select=name&limit=10000")
assert st == 200, (st, existing)
taken = {norm_company(r["name"]) for r in existing} - {None}
rows, skipped = [], []
for name, akta, web, desc in json.load(open(d + "new_companies.json")):
    key = norm_company(name)
    if key in taken:
        skipped.append(name)
        continue
    taken.add(key)
    rows.append({"name": name, "website": web, "description": desc, "industry": [],
                 "company_type": "operating", "source": "lane0_company_gap",
                 "metadata": {"created_by": "lane0-phase3", "claim_mentions": mentions[name], "akta_uuid": akta}})
print(len(rows), "rows;", len(skipped), "skipped (name key already in the graph):", skipped)
if not APPLY:
    spine_client.write("company", rows, dry_run=True); print("dry run ok"); sys.exit()
st, body = spine_client.write("company", rows, prefer="resolution=ignore-duplicates,return=representation")
assert st in (200, 201), (st, body)
json.dump({"run": "lane0-company-create", "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "created": [{"id": b["id"], "name": b["name"]} for b in body]}, open(d + "manifest_company_create.json", "w"), indent=1)
print("created", len(body))
