#!/usr/bin/env python3
"""Pull Clay 'Third-party news Oct6-Nov5 2026' values out of the session transcript (get-task-context results),
map entities to watchlist companies by domain, parse 'YYYY-MM-DD | kind | headline | url' lines -> items_clay.json.
Usage: clay_extract.py <transcript.jsonl>"""
import json, os, re, sys, datetime as dt
D = os.path.dirname(os.path.abspath(__file__)) + "/"
CO = json.load(open(D + "companies.json"))
dom = lambda s: (s or "").lower().removeprefix("https://").removeprefix("http://").removeprefix("www.").split("/")[0]
BYDOM = {dom(c["domain"]): c["name"] for c in CO}
FIELD = "Third-party news Oct6-Nov5 2026"
vals = {}  # domain -> text (latest completed wins)


def walk(o):
    if isinstance(o, dict):
        if "companies" in o and isinstance(o["companies"], dict):
            for e in o["companies"].values():
                d = dom(e.get("domain")); en = e.get("enrichments") or {}
                for x in (en.values() if isinstance(en, dict) else en):
                    if x.get("name") == FIELD and x.get("state") == "completed" and x.get("value"):
                        # only entities we enriched carry a value, so sub-pages sharing a domain are skipped
                        if d in BYDOM:
                            vals[d] = x["value"]
        for v in o.values(): walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
    elif isinstance(o, str) and o.startswith("{") and FIELD in o:
        try: walk(json.loads(o))
        except Exception: pass


for line in open(sys.argv[1]):
    if FIELD in line:
        try: walk(json.loads(line))
        except Exception: pass
out, lo, hi = [], dt.date(2026, 10, 6), dt.date(2026, 11, 5)
for d, txt in vals.items():
    for ln in txt.splitlines():
        p = [s.strip() for s in ln.split("|")]
        if len(p) < 4 or not re.match(r"\d{4}-\d{2}-\d{2}$", p[0]): continue
        day = dt.date.fromisoformat(p[0])
        if not (lo <= day <= hi): continue
        url = re.sub(r"[\)\]>]+$", "", p[-1].split()[0]) if p[-1] else ""
        out.append({"src": "clay", "company": BYDOM[d], "title": " | ".join(p[2:-1])[:300], "url": url,
                    "published": day.isoformat() + "T00:00:00+00:00", "summary": p[1]})
json.dump(out, open(D + "items_clay.json", "w"), indent=1)
print("companies with values", len(vals), "of", len(BYDOM), "items", len(out))
print("missing:", sorted(n for dd, n in BYDOM.items() if dd not in vals))
