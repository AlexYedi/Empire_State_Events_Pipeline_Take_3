import json, re, sys, time, urllib.parse, datetime as dt
sys.argv = ["x"]; import fetch0 as f
log = open(f.D + "log_gdelt.txt").read()
failed = sorted(set(re.findall(r"(?:gdelt retry |^)(\S[^;\n]*?) (?:0 )?HTTP Error 429", log)) | {"Apollo.io"})
have = json.load(open(f.D + "items_gdelt.json"))
done = {i["company"] for i in have}
todo = [c for c in f.CO if c["name"] in failed and c["name"] not in done]
print("retrying", len(todo))
for c in todo:
    q = urllib.parse.quote(c["q"] + " sourcelang:english")
    url = (f"https://api.gdeltproject.org/api/v2/doc/doc?query={q}&mode=artlist&maxrecords=75&sort=hybridrel"
           f"&format=json&startdatetime=20261006000000&enddatetime=20261105235959")
    arts, status = [], "fail"
    for attempt in range(4):
        try:
            body = f.get(url, timeout=60)
            if body.strip().startswith("{"):
                arts = json.loads(body).get("articles", []); status = "ok"
            else:
                status = "nonjson:" + body[:100].replace("\n", " ")
            break
        except Exception as e:
            status = str(e); time.sleep(90)
    for a in arts:
        t = dt.datetime.strptime(a["seendate"], "%Y%m%dT%H%M%SZ").replace(tzinfo=dt.timezone.utc)
        have.append(f.item("gdelt", c["name"], a.get("title"), a.get("url"), t))
    print(c["name"], len(arts), status, flush=True)
    json.dump(have, open(f.D + "items_gdelt.json", "w"), indent=1)
    time.sleep(45)
print("== gdelt total", len(have))
