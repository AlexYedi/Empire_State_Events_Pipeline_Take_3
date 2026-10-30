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
    python3 .claude/scripts/recompute_relevance.py --selftest # offline: scoring functions on fixtures

Runs nightly from GitHub Actions (`.github/workflows/relevance-recompute.yml`, YED-265) with
`SUPABASE_API_KEY` from repo secrets. Reads SUPABASE_API_KEY from .env (never printed). REST-only,
so no DDL / dashboard step. Idempotent: same data -> same scores. Safe to re-run.
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


# ---- pure scoring (covered by --selftest on fixtures; no network) ------------------------------

def is_tombstone(row: dict) -> bool:
    """YED-47: a soft-merged topic (metadata.merged_into) is a tombstone — scoring it would resurrect it."""
    return bool((row.get("metadata") or {}).get("merged_into"))


def recency_decay(last_engaged_at, now: datetime) -> float:
    """Half-life decay on last engagement; never engaged -> 0.0."""
    d = parse_ts(last_engaged_at)
    return 0.5 ** (((now - d).total_seconds() / 86400.0) / HALF_LIFE_DAYS) if d else 0.0


def engagement_weight(mass: float) -> float:
    """Log-scaled signal mass: a topic nobody engaged with still weighs 1.0."""
    return 1.0 + math.log1p(max(float(mass or 0), 0.0))


def proximity_boost(days_until: float | None) -> float:
    """Upcoming attended event within the window boosts its topics; full boost today, halving every
    half-window. Past or out-of-window dates boost nothing."""
    if days_until is None or not (0 <= days_until <= PROXIMITY_WINDOW_DAYS):
        return 0.0
    return PROXIMITY_MAX_BOOST * (0.5 ** (days_until / (PROXIMITY_WINDOW_DAYS / 2)))


def relevance_score(recency: float, engagement: float, prox: float) -> float:
    return round(recency * engagement + prox, 4)


def score_changed(new: float, old: float) -> bool:
    """Only write past WRITE_EPSILON, so unchanged graphs produce no write churn."""
    return abs(new - float(old or 0)) > WRITE_EPSILON


def main(argv=None):
    args = list(argv) if argv is not None else sys.argv[1:]
    if "--selftest" in args:
        return 0 if selftest() else 1
    dry = "--dry-run" in args
    top_n = 15
    if "--top" in args:
        try:
            top_n = int(args[args.index("--top") + 1])
        except (ValueError, IndexError):
            pass

    now = datetime.now(timezone.utc)

    # 1. all topics
    _, topics = req("GET", "/topic?select=id,name,engagement_count,last_engaged_at,relevance_score,metadata&limit=2000")
    if not isinstance(topics, list):
        sys.exit(f"failed to read topics: {topics}")
    # YED-47: soft-merged topics (metadata.merged_into) are tombstones — their engagement was transferred to
    # the target and their relevance_score nulled at merge time. Scoring them would resurrect them in the hub.
    topics = [t for t in topics if not is_tombstone(t)]

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
            boost = proximity_boost(days_until)
            if boost > 0:
                ev_boost[e["id"]] = boost
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
        recency = recency_decay(t.get("last_engaged_at"), now)
        # engagement weight from confidence mass; fall back to raw count if a topic has no scored signals
        mass = conf_mass.get(t["id"], 0.0) or float(t.get("engagement_count") or 0)
        engagement = engagement_weight(mass)
        prox = proximity.get(t["id"], 0.0)
        rel = relevance_score(recency, engagement, prox)
        old = float(t.get("relevance_score") or 0)
        rows.append({"id": t["id"], "name": t["name"], "rel": rel, "old": old,
                     "recency": round(recency, 3), "eng": round(engagement, 2), "prox": round(prox, 3)})

    rows.sort(key=lambda r: r["rel"], reverse=True)
    changed = [r for r in rows if score_changed(r["rel"], r["old"])]

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
        arrow = f"{r['old']}→{r['rel']}" if score_changed(r['rel'], r['old']) else f"{r['rel']}"
        px = f" +prox{r['prox']}" if r["prox"] else ""
        print(f"  {r['rel']:>6.3f}  {r['name'][:44]:46} (recency {r['recency']} × eng {r['eng']}{px})  [{arrow}]")
    active = [r for r in rows if r["rel"] > 0]
    print(f"\n{len(active)} topics have non-zero relevance (currently active); {len(rows)-len(active)} dormant at 0.")

def selftest() -> bool:
    """Offline: the scoring functions on inline fixtures — no network, no .env, no writes (YED-265).
    The nightly workflow depends on these being pure; this proves they are."""
    now = datetime(2026, 10, 30, 12, 0, 0, tzinfo=timezone.utc)
    checks = [
        ("recency: halves every HALF_LIFE_DAYS (14d), 0 for never-engaged",
         abs(recency_decay("2026-10-16T12:00:00+00:00", now) - 0.5) < 1e-6
         and recency_decay(None, now) == 0.0),
        ("recency: future timestamp (clock skew) slightly exceeds 1, never negative",
         1.0 < recency_decay("2026-10-30T13:00:00+00:00", now) < 1.01),
        ("engagement: log-scaled, mass 0 weighs 1.0, monotonic in mass",
         engagement_weight(0) == 1.0 and engagement_weight(-5) == 1.0
         and 1.0 < engagement_weight(1) < engagement_weight(10)),
        ("proximity: full boost today, halves every half-window, 0 outside window",
         proximity_boost(0) == PROXIMITY_MAX_BOOST
         and abs(proximity_boost(PROXIMITY_WINDOW_DAYS / 2) - PROXIMITY_MAX_BOOST / 2) < 1e-9
         and proximity_boost(-0.1) == 0.0
         and proximity_boost(PROXIMITY_WINDOW_DAYS + 0.1) == 0.0
         and proximity_boost(None) == 0.0),
        ("relevance: recency × engagement + proximity, rounded to 4dp",
         relevance_score(0.5, 2.0, 0.1) == 1.1 and relevance_score(0.123456, 1.0, 0) == 0.1235),
        ("tombstone: metadata.merged_into present is skipped, absent/None is scored",
         is_tombstone({"metadata": {"merged_into": "t9"}})
         and not is_tombstone({"metadata": {}}) and not is_tombstone({})
         and not is_tombstone({"metadata": None})),
        ("score_changed: only past WRITE_EPSILON counts as changed (no write churn)",
         score_changed(0.5, 0.5) is False and score_changed(0.5, 0.5 + WRITE_EPSILON / 2) is False
         and score_changed(0.5, 0.5 + WRITE_EPSILON * 3) is True and score_changed(0.5, None) is True),
    ]
    fail = sum(1 for _, good in checks if not good)
    for name, good in checks:
        print(f"  {'✓' if good else '✗'} {name}")
    print(f"selftest: {len(checks) - fail}/{len(checks)} pass")
    return fail == 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
