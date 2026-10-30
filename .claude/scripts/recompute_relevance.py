#!/usr/bin/env python3
"""
Relevance recompute for the Market-Intelligence graph (YED-115 prereq 2).

Pure math, no LLM, no API tokens — reads the graph over REST, computes a
`relevance_score` per topic, and writes back only the topics whose score changed.
This is what turns the graph from a flat list into an *evolving viewpoint*: the
dashboard ranks by real relevance instead of raw engagement_count.

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
Idempotent: same data -> same scores. Safe to re-run.
"""
import json, math, os, sys, urllib.request, urllib.error
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # ADR-9: the one write path
from spine_client import req, q  # guarded REST client (YED-81)

# ---- tunables ----
HALF_LIFE_DAYS = 14.0          # a topic re-engaged 14d ago weighs half of one touched today
PROXIMITY_WINDOW_DAYS = 30.0   # upcoming attended events within this window boost their topics
PROXIMITY_MAX_BOOST = 2.0      # boost for an event happening today; decays to ~0 at the window edge
WRITE_EPSILON = 1e-4           # only write if |new - old| exceeds this (avoids no-op churn)


def parse_ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None

# ---- pure scoring functions (no I/O; E-07 item 4 — S-01 depends on these) ----
def recency_weight(last_engaged, now):
    """recency_decay: 1.0 when engaged now, halving every HALF_LIFE_DAYS; 0.0 when never engaged."""
    return 0.5 ** (((now - last_engaged).total_seconds() / 86400.0) / HALF_LIFE_DAYS) if last_engaged else 0.0

def engagement_weight(mass):
    """engagement_weight: 1.0 baseline, log-scaled in the confidence mass (or raw count fallback)."""
    return 1.0 + math.log1p(mass)

def proximity_boost(days_until):
    """event_proximity_boost: PROXIMITY_MAX_BOOST for an event today, halving every half-window; 0 outside [0, window]."""
    if 0 <= days_until <= PROXIMITY_WINDOW_DAYS:
        return PROXIMITY_MAX_BOOST * (0.5 ** (days_until / (PROXIMITY_WINDOW_DAYS / 2)))
    return 0.0

def relevance_score(recency, engagement, prox):
    return round(recency * engagement + prox, 4)

def main():
    if "--selftest" in sys.argv:
        return selftest()
    dry = "--dry-run" in sys.argv
    top_n = 15
    if "--top" in sys.argv:
        try:
            top_n = int(sys.argv[sys.argv.index("--top") + 1])
        except (ValueError, IndexError):
            pass

    now = datetime.now(timezone.utc)

    # 1. all topics
    _, topics = req("GET", "/topic?select=id,name,engagement_count,last_engaged_at,relevance_score,metadata&limit=2000")
    if not isinstance(topics, list):
        sys.exit(f"failed to read topics: {topics}")
    # YED-47: soft-merged topics (metadata.merged_into) are tombstones — their engagement was transferred to
    # the target and their relevance_score nulled at merge time. Scoring them would resurrect them in the hub.
    topics = [t for t in topics if not (t.get("metadata") or {}).get("merged_into")]

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
            b = proximity_boost(days_until)
            if b:
                ev_boost[e["id"]] = b
        if ev_boost:
            ids = ",".join(ev_boost)
            _, links = req("GET", f"/event_entity?select=event_id,entity_id&entity_type=eq.topic&event_id=in.({ids})")
            for l in (links or []):
                b = ev_boost.get(l["event_id"], 0)
                proximity[l["entity_id"]] = max(proximity.get(l["entity_id"], 0), b)

    # 2b. confidence mass — sum of each topic's signal confidences (signal STRENGTH, richer than raw count,
    #     so a strong signal outranks a weak one and same-day topics differentiate).
    _, sig_links = req("GET", "/event_entity?select=entity_id,event_id&entity_type=eq.topic")
    _, sig_events = req("GET", "/event?select=id,confidence&kind=eq.market")
    conf_by_event = {e["id"]: float(e.get("confidence") or 0) for e in (sig_events or [])}
    conf_mass = {}
    for l in (sig_links or []):
        if l["event_id"] in conf_by_event:
            conf_mass[l["entity_id"]] = conf_mass.get(l["entity_id"], 0.0) + conf_by_event[l["event_id"]]

    # 3. compute
    rows = []
    for t in topics:
        d = parse_ts(t.get("last_engaged_at"))
        recency = recency_weight(d, now)
        # engagement weight from confidence mass; fall back to raw count if a topic has no scored signals
        mass = conf_mass.get(t["id"], 0.0) or float(t.get("engagement_count") or 0)
        engagement = engagement_weight(mass)
        prox = proximity.get(t["id"], 0.0)
        rel = relevance_score(recency, engagement, prox)
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


# ---------------------------------------------------------------------------
# selftest — the pure scoring functions on inline fixtures, no DB (E-07 item 4)
# ---------------------------------------------------------------------------
def selftest():
    """--selftest: pin recency_weight / engagement_weight / proximity_boost /
    relevance_score / parse_ts on inline fixtures. No DB access, no network, no writes."""
    from datetime import timedelta

    checks = []

    def ck(name, cond):
        checks.append((name, bool(cond)))

    now = datetime(2026, 10, 30, 12, 0, 0, tzinfo=timezone.utc)

    ck("parse_ts: an ISO-Z timestamp parses to an aware datetime",
       parse_ts("2026-10-01T10:00:00Z") == datetime(2026, 10, 1, 10, 0, 0, tzinfo=timezone.utc))
    ck("parse_ts: empty and malformed timestamps yield None",
       parse_ts("") is None and parse_ts(None) is None and parse_ts("not-a-date") is None)

    ck("recency: a never-engaged topic weighs 0", recency_weight(None, now) == 0.0)
    ck("recency: engaged now weighs 1", recency_weight(now, now) == 1.0)
    ck("recency: one half-life ago weighs 0.5",
       abs(recency_weight(now - timedelta(days=HALF_LIFE_DAYS), now) - 0.5) < 1e-9)
    ck("recency: two half-lives ago weighs 0.25",
       abs(recency_weight(now - timedelta(days=2 * HALF_LIFE_DAYS), now) - 0.25) < 1e-9)

    ck("engagement: zero mass keeps the 1.0 baseline", engagement_weight(0.0) == 1.0)
    ck("engagement: log-scaled, not linear (mass 9 -> 1 + ln 10)",
       abs(engagement_weight(9.0) - (1.0 + math.log(10))) < 1e-9)
    ck("engagement: doubling the mass never doubles the weight",
       engagement_weight(20.0) < 2 * engagement_weight(10.0))

    ck("proximity: an event today boosts the max", proximity_boost(0.0) == PROXIMITY_MAX_BOOST)
    ck("proximity: at the half-window the boost halves",
       abs(proximity_boost(PROXIMITY_WINDOW_DAYS / 2) - PROXIMITY_MAX_BOOST / 2) < 1e-9)
    ck("proximity: at the window edge it halves again; outside [0, window] it is 0",
       abs(proximity_boost(PROXIMITY_WINDOW_DAYS) - PROXIMITY_MAX_BOOST * 0.25) < 1e-9
       and proximity_boost(-1.0) == 0.0 and proximity_boost(PROXIMITY_WINDOW_DAYS + 1) == 0.0)

    ck("relevance: recency x engagement + prox, rounded to 4dp",
       relevance_score(1.0, 1.0, 0.1) == 1.1
       and relevance_score(recency_weight(now - timedelta(days=HALF_LIFE_DAYS), now),
                           engagement_weight(9.0), 0.0) == round(0.5 * engagement_weight(9.0), 4))

    fails = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  {'✓' if ok else '✗'} {n}")
    print(f"selftest: {len(checks) - len(fails)}/{len(checks)} relevance-scoring cases pass")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
