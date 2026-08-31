#!/usr/bin/env python3
"""
Land classified signals into Notion. Reads newline-delimited JSON on stdin — one gtm_signals value
per line — and creates a Notion page per row. Stdlib urllib only.

The clean demo pipe (avoids the fiddly Kafka REST consumer API — use the Confluent CLI to consume):
    confluent kafka topic consume gtm_signals --value-format json -o latest \\
      | python3 signal-stream/sinks/notion_sink.py

Or from a file / preview:
    python3 signal-stream/sinks/notion_sink.py --file samples.ndjson --dry-run

Each input line is expected to look like the gtm_signals value:
    { "id","title","url","source","classification": "<json string>","ts" }
where `classification` is the model's JSON: {"relevant","signal_type","company","why","confidence"}.

Notion setup (once): create an internal integration (notion.so/my-integrations), copy its token into
NOTION_TOKEN, create a "Signal Inbox" database with a title property named "Name" (or set
NOTION_TITLE_PROP), and SHARE that database with the integration. Put its id in NOTION_SIGNAL_DB.
"""
import argparse, json, os, sys, urllib.request, urllib.error

ENV = os.path.join(os.path.dirname(__file__), "..", ".env")
NOTION_API = "https://api.notion.com/v1/pages"
NOTION_VERSION = "2022-06-28"

def load_env():
    env = {}
    if os.path.exists(ENV):
        for line in open(ENV):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env

def parse_classification(row):
    c = row.get("classification")
    if isinstance(c, str):
        try:
            return json.loads(c)
        except Exception:
            return {}
    return c or {}

def build_page(row, db, title_prop):
    cls = parse_classification(row)
    title = row.get("title") or cls.get("company") or "(untitled signal)"
    bullets = []
    for label, val in (("Why", cls.get("why")), ("Signal", cls.get("signal_type")),
                       ("Company", cls.get("company")), ("Confidence", cls.get("confidence")),
                       ("Source", row.get("source")), ("URL", row.get("url"))):
        if val is not None and val != "":
            bullets.append({"object": "block", "type": "bulleted_list_item",
                            "bulleted_list_item": {"rich_text": [
                                {"type": "text", "text": {"content": f"{label}: {val}"}}]}})
    return {"parent": {"database_id": db},
            "properties": {title_prop: {"title": [{"text": {"content": title[:1900]}}]}},
            "children": bullets}

def post(payload, token):
    req = urllib.request.Request(NOTION_API, data=json.dumps(payload).encode(),
                                 headers={"Authorization": f"Bearer {token}",
                                          "Notion-Version": NOTION_VERSION,
                                          "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="read NDJSON from a file instead of stdin")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    env = load_env()
    db = env.get("NOTION_SIGNAL_DB")
    token = env.get("NOTION_TOKEN")
    title_prop = env.get("NOTION_TITLE_PROP", "Name")
    if not a.dry_run and not (db and token):
        sys.exit("Missing NOTION_TOKEN / NOTION_SIGNAL_DB in .env")

    stream = open(a.file) if a.file else sys.stdin
    ok = seen = 0
    for line in stream:
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        seen += 1
        page = build_page(row, db, title_prop)
        if a.dry_run:
            print(json.dumps(page, ensure_ascii=False)[:400])
            ok += 1
            continue
        try:
            if post(page, token) == 200:
                ok += 1
        except urllib.error.HTTPError as ex:
            print(f"  notion write failed [{ex.code}]: {ex.read().decode()[:160]}", file=sys.stderr)
    print(f"\n{'would write' if a.dry_run else 'wrote'} {ok}/{seen} signal rows to Notion", file=sys.stderr)

if __name__ == "__main__":
    main()
