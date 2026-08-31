#!/usr/bin/env python3
"""
Feed the signal stream with REAL data: poll Hacker News (Algolia API) for recent stories and
produce each to the `raw_signals` topic via the Confluent Cloud Kafka REST v3 records endpoint.

No native deps — stdlib urllib only (matches the repo's stdlib ethos). Datagen (Layer 0) proves the
plumbing with fake data; this is what makes Layer 1 a genuine GTM signal agent.

Usage:
    python3 signal-stream/producers/hn_producer.py --dry-run           # show what would be produced
    python3 signal-stream/producers/hn_producer.py --limit 20          # produce 20 recent stories
    python3 signal-stream/producers/hn_producer.py --query "AI agents" --limit 10

Emits value shape the Flink SQL expects: { id, title, url, source, text, ts }

⚠️ VERIFY: the Kafka REST v3 produce path used here is
   POST {REST_ENDPOINT}/kafka/v3/clusters/{CLUSTER_ID}/topics/{TOPIC}/records
   Confirm your cluster's REST endpoint (Console → Cluster settings). Auth = Basic base64(key:secret).
   For REST produce a *cluster-scoped* key also works; the Global key should too.
"""
import argparse, base64, json, os, sys, urllib.request, urllib.error, urllib.parse

ENV = os.path.join(os.path.dirname(__file__), "..", ".env")
HN = "https://hn.algolia.com/api/v1/search_by_date"

def load_env():
    # Tolerant: dry-run needs no creds (only produce() requires them). Returns {} if .env is absent.
    env = {}
    if os.path.exists(ENV):
        for line in open(ENV):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env

def fetch_hn(query, limit):
    q = f"?tags=story&hitsPerPage={limit}"
    if query:
        q += "&query=" + urllib.parse.quote(query)
    with urllib.request.urlopen(HN + q, timeout=15) as r:
        hits = json.loads(r.read().decode()).get("hits", [])
    out = []
    for h in hits:
        oid = h.get("objectID")
        out.append({
            "id": oid,
            "title": h.get("title") or h.get("story_title") or "",
            "url": h.get("url") or f"https://news.ycombinator.com/item?id={oid}",
            "source": "hackernews",
            "text": (h.get("story_text") or "")[:2000],
            "ts": h.get("created_at"),
        })
    return out

def produce(env, records, dry):
    endpoint = env.get("CONFLUENT_KAFKA_REST_ENDPOINT")
    cluster = env.get("CONFLUENT_CLUSTER_ID")
    topic = env.get("RAW_TOPIC", "raw_signals")
    key, secret = env.get("CONFLUENT_CLOUD_API_KEY"), env.get("CONFLUENT_CLOUD_API_SECRET")
    if not dry and not all([endpoint, cluster, key, secret]):
        sys.exit("Missing CONFLUENT_KAFKA_REST_ENDPOINT / CONFLUENT_CLUSTER_ID / API key+secret in .env")

    url = f"{endpoint}/kafka/v3/clusters/{cluster}/topics/{topic}/records" if endpoint else "(dry)"
    auth = base64.b64encode(f"{key}:{secret}".encode()).decode() if key else ""
    ok = 0
    for rec in records:
        body = {"key": {"type": "JSON", "data": {"id": rec["id"]}},
                "value": {"type": "JSON", "data": rec}}
        if dry:
            print(json.dumps(rec, ensure_ascii=False))
            ok += 1
            continue
        req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json",
                                              "Authorization": f"Basic {auth}"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status in (200, 201):
                    ok += 1
        except urllib.error.HTTPError as ex:
            print(f"  produce failed [{ex.code}] for {rec['id']}: {ex.read().decode()[:160]}", file=sys.stderr)
    return ok

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", default="", help="optional HN search term")
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    env = load_env()
    records = fetch_hn(a.query, a.limit)
    n = produce(env, records, a.dry_run)
    verb = "would produce" if a.dry_run else "produced"
    print(f"\n{verb} {n}/{len(records)} records to '{env.get('RAW_TOPIC','raw_signals')}'"
          + (" (dry run)" if a.dry_run else ""), file=sys.stderr)

if __name__ == "__main__":
    main()
