#!/usr/bin/env python3
"""Lane 2 bake-off, $0 candidate: GDELT DOC 2.0 · HN Algolia · company RSS/Atom · SEC EDGAR 8-K · GitHub releases.
Read-only against public APIs; writes local JSON only (bake/items_<src>.json). Nothing touches the spine.
Window 2026-10-06 → 2026-11-05 (same as akta run 1). Usage: fetch0.py <src|all>
"""
import json, os, re, sys, time, urllib.parse, urllib.request, html, datetime as dt
import xml.etree.ElementTree as ET

D = os.path.dirname(os.path.abspath(__file__)) + "/"
START, END = dt.datetime(2026, 10, 6, tzinfo=dt.timezone.utc), dt.datetime(2026, 11, 5, 23, 59, 59, tzinfo=dt.timezone.utc)
UA = "EmpireStateEventsPipeline-bakeoff/0.1 (research; contact via github.com/AlexYedi)"
CO = json.load(open(D + "companies.json"))  # [{name, domain, q, gh, cik}]


def get(url, timeout=25, accept="application/json"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def in_window(t):
    return t is not None and START <= t <= END


def item(src, co, title, url, published, summary=""):
    return {"src": src, "company": co, "title": html.unescape(title or "").strip()[:300], "url": url,
            "published": published.isoformat(timespec="seconds") if published else None,
            "summary": re.sub(r"<[^>]+>", " ", html.unescape(summary or ""))[:400].strip()}


def gdelt():
    out = []
    for c in CO:
        q = urllib.parse.quote(c["q"] + " sourcelang:english")
        url = (f"https://api.gdeltproject.org/api/v2/doc/doc?query={q}&mode=artlist&maxrecords=75&sort=hybridrel"
               f"&format=json&startdatetime=20261006000000&enddatetime=20261105235959")
        for attempt in range(3):
            try:
                body = get(url, timeout=40)
                arts = json.loads(body).get("articles", []) if body.strip().startswith("{") else []
                if not body.strip().startswith("{"):
                    print("  gdelt non-json", c["name"], body[:120].replace("\n", " "))
                break
            except Exception as e:
                print("  gdelt retry", c["name"], e); time.sleep(10); arts = []
        for a in arts:
            t = dt.datetime.strptime(a["seendate"], "%Y%m%dT%H%M%SZ").replace(tzinfo=dt.timezone.utc)
            out.append(item("gdelt", c["name"], a.get("title"), a.get("url"), t))
        print(f"gdelt {c['name']}: {len(arts)}")
        time.sleep(6)
    return out


def hn():
    out = []
    a, b = int(START.timestamp()), int(END.timestamp())
    for c in CO:
        qs = urllib.parse.urlencode({"query": c.get("hn", c["name"]), "tags": "story", "hitsPerPage": 50,
                                     "numericFilters": f"created_at_i>{a},created_at_i<{b}"})
        try:
            hits = json.loads(get("https://hn.algolia.com/api/v1/search?" + qs))["hits"]
        except Exception as e:
            print("  hn fail", c["name"], e); hits = []
        n = 0
        for h in hits:
            if (h.get("points") or 0) < 5: continue  # HN noise floor
            t = dt.datetime.fromtimestamp(h["created_at_i"], dt.timezone.utc)
            out.append(item("hn", c["name"], h.get("title"), h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}", t))
            n += 1
        print(f"hn {c['name']}: {n}/{len(hits)}")
        time.sleep(0.5)
    return out


FEED_PATHS = ["/rss.xml", "/feed.xml", "/feed", "/blog/rss.xml", "/blog/feed", "/blog/rss", "/blog/feed.xml",
              "/news/rss.xml", "/index.xml", "/blog/index.xml", "/atom.xml", "/news/feed", "/changelog/rss.xml"]


def parse_date(s):
    if not s: return None
    s = s.strip()
    for f in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z",
              "%Y-%m-%d", "%a, %d %b %Y %H:%M %z"):
        try:
            t = dt.datetime.strptime(s.replace("Z", "+0000") if "T" in s else s, f)
            return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)
        except ValueError:
            continue
    return None


def parse_feed(body):
    root = ET.fromstring(body.encode("utf-8"))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    rows = []
    for it in root.iter("item"):
        rows.append((it.findtext("title"), it.findtext("link"), parse_date(it.findtext("pubDate") or it.findtext("{http://purl.org/dc/elements/1.1/}date")), it.findtext("description")))
    for e in root.iter("{http://www.w3.org/2005/Atom}entry"):
        link = e.find("a:link", ns)
        rows.append((e.findtext("a:title", namespaces=ns), link.get("href") if link is not None else None,
                     parse_date(e.findtext("a:published", namespaces=ns) or e.findtext("a:updated", namespaces=ns)),
                     e.findtext("a:summary", namespaces=ns)))
    return rows


def discover(domain):
    base = "https://" + domain
    cands = []
    try:
        page = get(base, accept="text/html")
        cands += [urllib.parse.urljoin(base, m) for m in re.findall(
            r'<link[^>]+type=["\']application/(?:rss|atom)\+xml["\'][^>]*href=["\']([^"\']+)', page)]
        cands += [urllib.parse.urljoin(base, m) for m in re.findall(
            r'<link[^>]+href=["\']([^"\']+)["\'][^>]*type=["\']application/(?:rss|atom)\+xml', page)]
    except Exception:
        pass
    cands += [base + p for p in FEED_PATHS]
    seen = set()
    for u in cands:
        if u in seen: continue
        seen.add(u)
        try:
            body = get(u, timeout=12, accept="application/rss+xml, application/atom+xml, application/xml, text/xml")
            if "<rss" in body[:500] or "<feed" in body[:800] or "<rdf" in body[:500].lower():
                rows = parse_feed(body)
                if rows: return u, rows
        except Exception:
            continue
    return None, []


def rss():
    out, found = [], {}
    for c in CO:
        if not c.get("domain"): continue
        u, rows = discover(c["domain"])
        found[c["name"]] = u
        n = 0
        for title, link, t, desc in rows:
            if in_window(t):
                out.append(item("rss", c["name"], title, link, t, desc)); n += 1
        print(f"rss {c['name']}: {u} → {n}/{len(rows)} in window")
    json.dump(found, open(D + "feed_sources.json", "w"), indent=1)
    return out


ITEM_NAMES = {"1.01": "material agreement", "1.02": "agreement terminated", "2.01": "acquisition/disposition completed",
              "2.02": "results of operations (earnings)", "2.05": "exit/restructuring costs", "2.06": "impairment",
              "5.02": "director/officer change", "5.07": "shareholder vote", "7.01": "Reg FD disclosure", "8.01": "other events",
              "9.01": "exhibits"}


def edgar():
    out = []
    for c in CO:
        if not c.get("cik"): continue
        cik = str(c["cik"]).zfill(10)
        try:
            sub = json.loads(get(f"https://data.sec.gov/submissions/CIK{cik}.json"))
        except Exception as e:
            print("  edgar fail", c["name"], e); continue
        r = sub["filings"]["recent"]
        n = 0
        for form, date, acc, doc, items in zip(r["form"], r["filingDate"], r["accessionNumber"], r["primaryDocument"], r.get("items", [""] * len(r["form"]))):
            if form not in ("8-K", "10-Q", "10-K"): continue
            t = dt.datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc)
            if not in_window(t): continue
            desc = "; ".join(ITEM_NAMES.get(i.strip(), i.strip()) for i in (items or "").split(",") if i.strip() and i.strip() != "9.01")
            url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-', '')}/{doc}"
            out.append(item("edgar", c["name"], f"{c['name']} {form}: {desc or form}", url, t)); n += 1
        print(f"edgar {c['name']}: {n}")
        time.sleep(0.3)
    return out


def github():
    out = []
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    for c in CO:
        for org in c.get("gh", []):
            try:
                req = urllib.request.Request(f"https://api.github.com/orgs/{org}/repos?sort=stars&per_page=100&type=public",
                                             headers={"User-Agent": UA, **({"Authorization": f"Bearer {tok}"} if tok else {})})
                repos = json.loads(urllib.request.urlopen(req, timeout=20).read())
                repos = sorted(repos, key=lambda r: -r.get("stargazers_count", 0))[:3]
            except Exception as e:
                print("  gh fail", org, e); continue
            for rp in repos:
                try:
                    req = urllib.request.Request(f"https://api.github.com/repos/{rp['full_name']}/releases?per_page=30",
                                                 headers={"User-Agent": UA, **({"Authorization": f"Bearer {tok}"} if tok else {})})
                    rels = json.loads(urllib.request.urlopen(req, timeout=20).read())
                except Exception:
                    continue
                for rl in rels:
                    t = parse_date(rl.get("published_at"))
                    tag = rl.get("tag_name", "")
                    m = re.search(r"(\d+)\.(\d+)\.(\d+)", tag)
                    if m and m.group(3) != "0": continue  # patch releases are not launches
                    if rl.get("prerelease") or not in_window(t): continue
                    out.append(item("github", c["name"], f"{rp['full_name']} {rl.get('name') or tag}", rl.get("html_url"), t, rl.get("body") or ""))
        print(f"github {c['name']}: {sum(1 for o in out if o['company'] == c['name'])}")
    return out


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    for name, fn in [("gdelt", gdelt), ("hn", hn), ("rss", rss), ("edgar", edgar), ("github", github)]:
        if which in ("all", name):
            rows = fn()
            json.dump(rows, open(D + f"items_{name}.json", "w"), indent=1)
            print(f"== {name}: {len(rows)} items")
