#!/usr/bin/env python3
"""
Relevance recompute for the Market-Intelligence graph (YED-115 prereq 2).

Pure math, no LLM, no API tokens — reads the graph over REST, computes a
`relevance_score` per topic, and writes back only the topics whose score changed.
This is what turns the graph from a flat list into an *evolving viewpoint*: the
dashboard + /morning-refresh rank by real relevance instead of raw engagement_count.

    relevance = recency_decay(last_engaged_at)      # recent signals weigh more (half-life)
              * engagement_weight(engagement_count)   # more signals -> higher (log-scaled)
              + event_proximity_boost                 # linked to an upcoming attended event -> boost

`coverage_penalty` ("uncovered" — down-rank topics already posted about) is a
deliberate fast-follow (needs the Content-Drafts join); not in this V1.

Usage:
    python3 .claude/scripts/recompute_relevance.py            # live: recompute + write changed
    python3 .claude/scripts/recompute_relevance.py --dry-run  # preview only, no writes
    python3 .claude/scripts/recompute_relevance.py --top 25   # show N in the report (default 15)

Reads SUPABASE_API_KEY from .env (never printed). REST-only, so no DDL / dashboard step.
Idempotent: same data -> same scores. Safe to re-run (and to call from /morning-refresh).
"""
import json, math, os, sys, urllib.request, urllib.error
from datetime import datetime, timezone

# ---- tunables ----
HALF_LIFE_DAYS = 14.0          # a topic re-engaged 14d ago weighs half of one touched today
PROXIMITY_WINDOW_DAYS = 30.0   # upcoming attended events within this window boost their topics
PROXIMITY_MAX_BOOST = 2.0      # boost for an event happening today; decays to ~0 at the window edge
WRITE_EPSILON = 1e-4           # only write if |new - old| exceeds this (avoids no-op churn)

BASE = "https://oicikjyzmxqfomrrqkvf.supabase.co/rest/v1"

def load_key():
    for line in open(os.path.join(os.path.dirname(__file__), "..", "..", ".env")):
        if line.startswith("SUPABASE_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip()
    sys.exit("SUPABASE_API_KEY not found in .env")

KEY = load_key()
H = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}

def req(method, path, body=None, prefer=None):
    hdrs = dict(H)
    if prefer:
        hdrs["Prefer"] = prefer
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, headers=hdrs, method=method)
    try:
        resp = urllib.request.urlopen(r)
        raw = resp.read().decode()
        return resp.status, (json.loads(raw) if raw.strip() else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]

def parse_ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None

def main():
    dry = "--dry-run" in sys.argv
    top_n = 15
    if "--top" in sys.argv:
        try:
            top_n = int(sys.argv[sys.argv.index("--top") + 1])
        except (ValueError, IndexError):
            pass

    now = datetime.now(timezone.utc)

    # 1. all topics
    _, topics = req("GET", "/topic?select=id,name,engagement_count,last_engaged_at,relevance_score&limit=2000")
    if not isinstance(topics, list):
        sys.exit(f"failed to read topics: {topics}")

    # 2. event-proximity: topics linked to an UPCOMING attended event within the window
    now_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    _, up_events = req("GET", f"/event?select=id,event_date&kind=eq.attended&event_date=gt.{now_iso}")
    proximity = {}  # topic_id -> best boost
    if isinstance(up_events, list) and up_events:
        ev_boost = {}
        for e in up_events:
            d = parse_ts(e.get("event_date"))
            if not d:
                continue
            days_until = (d - now).total_seconds() / 86400.0
            if 0 <= days_until <= PROXIMITY_WINDOW_DAYS:
                ev_boost[e["id"]] = PROXIMITY_MAX_BOOST * (0.5 ** (days_until / (PROXIMITY_WINDOW_DAYS / 2)))
        if ev_boost:
            ids = ",".join(ev_boost)
            _, links = req("GET", f"/event_entity?select=event_id,entity_id&entity_type=eq.topic&event_id=in.({ids})")
            for l in (links or []):
                b = ev_boost.get(l["event_id"], 0)
                proximity[l["entity_id"]] = max(proximity.get(l["entity_id"], 0), b)

    # 3. compute
    rows = []
    for t in topics:
        d = parse_ts(t.get("last_engaged_at"))
        recency = 0.5 ** (((now - d).total_seconds() / 86400.0) / HALF_LIFE_DAYS) if d else 0.0
        engagement = 1.0 + math.log1p(t.get("engagement_count") or 0)
        prox = proximity.get(t["id"], 0.0)
        rel = round(recency * engagement + prox, 4)
        old = float(t.get("relevance_score") or 0)
        rows.append({"id": t["id"], "name": t["name"], "rel": rel, "old": old,
                     "recency": round(recency, 3), "eng": round(engagement, 2), "prox": round(prox, 3)})

    rows.sort(key=lambda r: r["rel"], reverse=True)
    changed = [r for r in rows if abs(r["rel"] - r["old"]) > WRITE_EPSILON]

    # 4. write changed
    written = 0
    if not dry:
        for r in changed:
            code, _ = req("PATCH", f"/topic?id=eq.{r['id']}", {"relevance_score": r["rel"]}, prefer="return=minimal")
            if code in (200, 204):
                written += 1
            else:
                print(f"  ⚠️ write failed for {r['name']}: {code}")

    # 5. report
    print(f"Relevance recompute {'(DRY RUN)' if dry else ''} — {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"topics: {len(topics)} | changed: {len(changed)} | written: {written if not dry else 0} | "
          f"upcoming-event boosts: {len(proximity)}")
    print(f"\nTop {top_n} by relevance:")
    for r in rows[:top_n]:
        arrow = f"{r['old']}→{r['rel']}" if abs(r['rel'] - r['old']) > WRITE_EPSILON else f"{r['rel']}"
        px = f" +prox{r['prox']}" if r["prox"] else ""
        print(f"  {r['rel']:>6.3f}  {r['name'][:44]:46} (recency {r['recency']} × eng {r['eng']}{px})  [{arrow}]")
    active = [r for r in rows if r["rel"] > 0]
    print(f"\n{len(active)} topics have non-zero relevance (currently active); {len(rows)-len(active)} dormant at 0.")

if __name__ == "__main__":
    main()
