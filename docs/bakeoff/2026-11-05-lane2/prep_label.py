#!/usr/bin/env python3
"""Build labeller batches: akta reference + every $0 candidate item, with a global key k. Writes all_items.json + batch_NN.txt."""
import json, os, glob, re, urllib.parse
D = os.path.dirname(os.path.abspath(__file__)) + "/"
AK = json.load(open(D + "../akta/run1.json"))["articles"]


def canon(u):
    if not u: return ""
    p = urllib.parse.urlsplit(u.strip())
    q = "&".join(x for x in p.query.split("&") if x and not x.lower().startswith(("utm_", "ref=", "src=")))
    return (p.netloc.lower().removeprefix("www.") + p.path.rstrip("/") + ("?" + q if q else "")).lower()


items = [{"src": "akta", "company": a["company"], "title": a["title"], "url": a["url"], "published": a["published_date"],
          "summary": (a.get("ai_summary") or "")[:300]} for a in AK]
for f in sorted(glob.glob(D + "items_*.json")):
    items += json.load(open(f))
# drop exact duplicate (src, company, canonical url)
seen, uniq = set(), []
for it in items:
    key = (it["src"], it["company"], canon(it["url"]) or it["title"])
    if key in seen: continue
    seen.add(key); it["curl"] = canon(it["url"]); uniq.append(it)
import random
random.Random(7).shuffle(uniq)
for k, it in enumerate(uniq): it["k"] = k
json.dump(uniq, open(D + "all_items.json", "w"), indent=1)
B = 450
for i in range(0, len(uniq), B):
    with open(D + f"batch_{i // B:02d}.txt", "w") as fh:
        for it in uniq[i:i + B]:
            t = re.sub(r"\s+", " ", it["title"] or "")[:200]
            s = re.sub(r"\s+", " ", it.get("summary") or "")[:220]
            fh.write(f"{it['k']}|{it['company']}|{(it['published'] or '')[:10]}|{t}|{s}\n")
from collections import Counter
print(len(uniq), Counter(i["src"] for i in uniq), "batches", (len(uniq) + B - 1) // B)
