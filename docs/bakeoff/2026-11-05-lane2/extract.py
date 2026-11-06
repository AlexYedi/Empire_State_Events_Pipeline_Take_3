import json, re, sys
src, dst = sys.argv[1], sys.argv[2]
PAT = r"(?m)^\s*(\d+) ([ABCD]) ([A-Z])\s*$"
def strings(o):
    if isinstance(o, str): yield o
    elif isinstance(o, dict):
        for v in o.values(): yield from strings(v)
    elif isinstance(o, list):
        for v in o: yield from strings(v)
best = ""
for line in open(src):
    try: o = json.loads(line)
    except Exception: continue
    m = o.get("message") or {}
    if m.get("role") != "assistant": continue
    for t in strings(m.get("content")):
        if len(re.findall(PAT, t)) > len(re.findall(PAT, best)): best = t
rows = re.findall(PAT, best)
open(dst, "w").write("".join(f"{k} {c} {d}\n" for k, c, d in rows))
print(dst.split("/")[-1], len(rows), "DONE" in best)
