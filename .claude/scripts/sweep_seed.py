#!/usr/bin/env python3
"""sweep_seed.py — the day's theme-sweep query list (YED-384, ADR-14 §2.1 + §2.8). Read-only.

Deterministic, no model. Four seed sources, each a `kind` of the planned `sweep_query` ledger:

  velocity     mi.theme_week, per theme PER LENS (attended, research; never summed, ADR-13 rule 1):
               obs = facts in the last 4 ISO weeks. Permutation test per theme-lens: shuffle the
               12 week labels 2000x (seeded); p = share of shuffles whose last-4 sum reaches obs.
               Seeded when p < 0.05 and obs >= 5 (label `rising`), or when the prior 8 weeks hold
               0 facts and obs >= 5 (label `new`). Order: new by obs, then rising by p, then z;
               top 5. Each theme-lens draws from its own RNG (sha256 of seed + key), so adding a
               theme never moves another theme's p. (The draft's Poisson band fired on 13/31
               themes against a shuffle null of 13.1: no information on bursty counts.) The
               aggregate null re-runs the same rules on shuffled series; stderr.
               Resolution limit: 12 weeks choose 4 recent = 495 arrangements, and 2000 shuffles
               put the floor on p at 1/2001 ~ 0.0005. Facts in only 1 or 2 distinct weeks can never
               reach p < 0.05 (all-recent odds 4/12 and 6/66), so a theme needs facts in >= 3 weeks,
               clustered recently, to be `rising`; a brand-new theme is why `new` exists.
  gap          themes with attended or research facts >= 3 over 12 weeks and market facts < 3.
  event        pre-event triage manifests (`.claude/.state/research/*.manifest.json`: event title,
               date, topic and company entities; person entities are skipped at load) dated
               today..today+7, themed through the graph's topic -> cluster membership. Fallback:
               `Event Content/` folders `MM DD YY <title>` in range that no manifest covers and that
               are not content folders (NON_EVENT_RE, copied from reconcile.py).
  room_topic   topics and companies linked to attended events of the last 7 days
  room_entity  (event_entity GETs; person links are never read).

Output: a JSON list of {theme, theme_id, kind, query, seed_ref, window}, matching the planned
sweep_query columns (kind values: velocity|gap|event|entity|room_topic|room_entity|open_question|
room_vs_market; this script emits EMITTED_KINDS). Stdout, or --out FILE. Summary and the
null report go to stderr so stdout stays parseable.

Reads go through spine_client.req with GET only (mi_slice is GET-callable, 0016); `_get` refuses any
other verb. Nothing is written to any database.

Usage:
  python3 sweep_seed.py [--events-dir DIR] [--state-dir DIR] [--today YYYY-MM-DD] [--out FILE]
  python3 sweep_seed.py --selftest          (offline, fixtures under fixtures/sweep/)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import re
import sys
import urllib.parse
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
FIXTURES = os.path.join(HERE, "fixtures", "sweep")
sys.path.insert(0, HERE)

EMITTED_KINDS = ("velocity", "gap", "event", "room_topic", "room_entity")   # sweep_query also plans entity,
                                                                           # open_question, room_vs_market
WEEKS = 12            # 4 recent + 8 prior
RECENT = 4
OBS_FLOOR = 5         # a 1 -> 4 jump does not count
FACT_FLOOR = 3        # the mi floor (insufficient_data below it)
VELOCITY_TOP = 5
SHUFFLES = 2000  # Monte Carlo error near alpha 0.05 ~ +-0.005 (was 200: +-0.015, flipped borderline themes)
ALPHA = 0.05
ROOM_DAYS = 7
EVENT_DAYS = 7
ROOM_CAP = 15         # per kind
VELOCITY_LENSES = ("attended", "research")
FOLDER_RE = re.compile(r"^(\d{2}) (\d{2}) (\d{2}) (.+)$")
# Copied from reconcile.py (feat/yed-384-reconcile-report), not imported across branches: content
# folders, not occasions. Keep the two in step.
NON_EVENT_RE = re.compile(r"upcoming week|roundup|visual prompts|elevated posts|combined .*events|"
                          r"^\w+day nyc ai events$|chain test", re.I)
STOP = {"the", "and", "of", "for", "a", "an", "in", "on", "with", "to", "by", "at", "nyc", "ai", "night",
        "live", "week", "events", "event", "x", "&", "-", "—"}


def window(today: date, days: int) -> dict:
    return {"from": (today - timedelta(days=days)).isoformat(), "to": today.isoformat()}


def iso_weeks(today: date, n: int = WEEKS) -> list[str]:
    """The n ISO week labels ending in today's week, oldest first (mi_slice's anchoring)."""
    out = []
    for k in range(n - 1, -1, -1):
        y, w, _ = (today - timedelta(weeks=k)).isocalendar()
        out.append(f"{y}-W{w:02d}")
    return out


def series(rows: list[dict], weeks: list[str]) -> dict[tuple[str, str], list[int]]:
    """(theme_id, lens) -> weekly fact counts over `weeks` (missing weeks are 0)."""
    idx = {w: i for i, w in enumerate(weeks)}
    out: dict[tuple[str, str], list[int]] = {}
    for r in rows:
        i = idx.get(r.get("iso_week"))
        if i is None or not r.get("theme_id"):
            continue
        out.setdefault((r["theme_id"], r["lens"]), [0] * len(weeks))[i] += int(r.get("facts") or 0)
    return out


def stats(counts: list[int]) -> tuple[int, float, float]:
    """(obs, rate_prior, z) for one theme-lens series of WEEKS buckets. z is descriptive only."""
    obs = sum(counts[-RECENT:])
    rate = sum(counts[:-RECENT]) / ((len(counts) - RECENT) / RECENT)
    return obs, rate, (obs - rate) / math.sqrt(max(rate, 1.0))


def poisson_rising(counts: list[int]) -> bool:
    """The ADR-14 draft rule, kept only so the selftest can show where it misfires on bursty series."""
    obs, rate, _ = stats(counts)
    return obs > rate + 2 * math.sqrt(max(rate, 1.0)) and obs >= OBS_FLOOR


def perm_dist(counts: list[int], rng: random.Random, n: int = SHUFFLES) -> list[int]:
    """Recent-window sums under n week-label permutations of one series (its own null)."""
    out = []
    for _ in range(n):
        c = counts[:]
        rng.shuffle(c)
        out.append(sum(c[-RECENT:]))
    return out


def key_rng(seed: int, key: tuple[str, str], salt: str) -> random.Random:
    """An RNG per theme-lens (and per use), so one theme's shuffles never depend on another's."""
    return random.Random(int(hashlib.sha256(f"{seed}|{key[0]}|{key[1]}|{salt}".encode()).hexdigest()[:16], 16))


def label(counts: list[int], dist: list[int]) -> tuple[str | None, float]:
    """(`new` | `rising` | None, p) for one series against its own permutation null."""
    obs = sum(counts[-RECENT:])
    p = p_value(obs, dist)
    if obs < OBS_FLOOR:
        return None, p
    if sum(counts[:-RECENT]) == 0:
        return "new", p
    return ("rising" if p < ALPHA else None), p


def p_value(obs: int, dist: list[int]) -> float:
    """One-sided permutation p, (1 + #{null >= obs}) / (1 + n): never 0 (Phipson & Smyth 2010)."""
    return (1 + sum(1 for x in dist if x >= obs)) / (1 + len(dist))


def theme_names(rows: list[dict]) -> dict[str, str]:
    return {r["theme_id"]: r["theme"] for r in rows if r.get("theme_id") and r.get("theme")}


def velocity_queries(rows: list[dict], today: date, seed: int = 7) -> tuple[list[dict], dict]:
    """Per theme-lens permutation test: shuffle the 12 week labels SHUFFLES times (seeded), p = share of
    shuffles whose last-4-week sum reaches the observed one. Seeds a theme when p < ALPHA and
    obs >= OBS_FLOOR, ranked by p then z. The aggregate null re-applies the same test to shuffled
    series, so the stderr line compares the observed rising count with what chance alone yields."""
    weeks = iso_weeks(today)
    ser = series(rows, weeks)
    names = theme_names(rows)
    keys = sorted(k for k in ser if k[1] in VELOCITY_LENSES)
    dists = {k: perm_dist(ser[k], key_rng(seed, k, "dist")) for k in keys}

    def rank(lab, obs, p, z):          # new first (by obs), then rising (by p, then z)
        return (0, -obs, 0.0) if lab == "new" else (1, p, -z)

    best: dict[str, tuple] = {}
    for k in keys:
        tid, lens = k
        lab, p = label(ser[k], dists[k])
        if lab is None:
            continue
        obs, rate, z = stats(ser[k])
        if tid not in best or rank(lab, obs, p, z) < rank(best[tid][0], best[tid][2], best[tid][4], best[tid][5]):
            best[tid] = (lab, lens, obs, rate, p, z)
    ranked = sorted(best.items(), key=lambda kv: rank(kv[1][0], kv[1][2], kv[1][4], kv[1][5]))
    out = [{"theme": names.get(tid), "theme_id": tid, "kind": "velocity",
            "query": f"{names.get(tid)}: what happened in the last 7 days (funding, launches, releases, papers, exec moves)",
            "seed_ref": f"mi.theme_week:{tid}:{lens} {lab} obs={obs} prior_rate={rate:.1f} p={p:.3f} z={z:.1f}",
            "window": window(today, 7)} for tid, (lab, lens, obs, rate, p, z) in ranked[:VELOCITY_TOP]]
    shufflers = {k: key_rng(seed, k, "null") for k in keys}
    null = []
    for _ in range(SHUFFLES):
        hit = set()
        for k in keys:
            c = ser[k][:]
            shufflers[k].shuffle(c)
            if label(c, dists[k])[0]:
                hit.add(k[0])
        null.append(len(hit))
    null.sort()
    report = {"rising_observed": sum(1 for v in best.values() if v[0] == "rising"),
              "new_observed": sum(1 for v in best.values() if v[0] == "new"), "themes": len({k[0] for k in ser}),
              "null": {"shuffles": SHUFFLES, "mean": round(sum(null) / SHUFFLES, 2),
                       "p95": null[int(0.95 * (SHUFFLES - 1))], "max": null[-1]}}
    return out, report


def gap_queries(rows: list[dict], today: date) -> list[dict]:
    weeks = set(iso_weeks(today))
    tot: dict[str, dict[str, int]] = {}
    for r in rows:
        if r.get("iso_week") in weeks and r.get("theme_id"):
            t = tot.setdefault(r["theme_id"], {"attended": 0, "research": 0, "market": 0})
            if r.get("lens") in t:
                t[r["lens"]] += int(r.get("facts") or 0)
    names = theme_names(rows)
    out = []
    for tid, t in sorted(tot.items(), key=lambda kv: -(kv[1]["attended"] + kv[1]["research"])):
        if (t["attended"] >= FACT_FLOOR or t["research"] >= FACT_FLOOR) and t["market"] < FACT_FLOOR:
            out.append({"theme": names.get(tid), "theme_id": tid, "kind": "gap",
                        "query": f"{names.get(tid)}: funding, launches, partnerships, papers and releases in the last 28 days",
                        "seed_ref": f"mi.theme_week:{tid} attended={t['attended']} research={t['research']} "
                                    f"market={t['market']} ({WEEKS}w)",
                        "window": window(today, 28)})
    return out


def _tokens(s: str) -> set[str]:
    return {w.rstrip("s") for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP and len(w) > 2}


def match_theme(title: str, names: dict[str, str]) -> tuple[str | None, str | None]:
    """The one theme sharing the most content words with the title; None on a tie or no overlap."""
    tt = _tokens(title)
    scored = sorted(((len(tt & _tokens(n)), tid, n) for tid, n in names.items()), reverse=True)
    if not scored or scored[0][0] == 0 or (len(scored) > 1 and scored[1][0] == scored[0][0]):
        return None, None
    return scored[0][1], scored[0][2]


def _date(s) -> date | None:
    try:
        return date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


def event_queries(triage: list[dict], folders: list[str], today: date, names: dict[str, str],
                  topic_theme: dict[str, str]) -> list[dict]:
    """Pure. triage rows: {title, date, topics[], companies[], ref}; topic_theme: lower(topic name) ->
    theme_id. Theme = the commonest theme among the event's topics, else a title/topic word match."""
    out, covered = [], []
    hi = today + timedelta(days=EVENT_DAYS)
    for t in sorted(triage, key=lambda t: (t["date"], t["title"])):
        d = _date(t["date"])
        if d is None or not today <= d <= hi:
            continue
        votes: dict[str, int] = {}
        for name in t["topics"]:
            tid = topic_theme.get(name.lower())
            if tid in names:
                votes[tid] = votes.get(tid, 0) + 1
        if votes:
            tid = max(sorted(votes), key=lambda k: votes[k])
            theme = names[tid]
        else:
            tid, theme = match_theme(" ".join([t["title"], *t["topics"]]), names)
        terms = "; ".join(x for x in (", ".join(t["topics"][:4]), ", ".join(t["companies"][:6])) if x)
        out.append({"theme": theme, "theme_id": tid, "kind": "event",
                    "query": f"{t['title']} ({d.isoformat()}): {terms or 'the topic and the host'} in the last 7 days",
                    "seed_ref": f"triage:{t['ref']}", "window": window(today, 7)})
        covered.append((d, _tokens(t["title"])))
    for f in sorted(folders):
        m = FOLDER_RE.match(f)
        if not m or NON_EVENT_RE.search(m.group(4)):
            continue
        try:
            d = date(2000 + int(m.group(3)), int(m.group(1)), int(m.group(2)))
        except ValueError:
            continue
        title = m.group(4).strip()
        if not today <= d <= hi or any(cd == d and ct & _tokens(title) for cd, ct in covered):
            continue
        tid, theme = match_theme(title, names)
        out.append({"theme": theme, "theme_id": tid, "kind": "event",
                    "query": f"{title} ({d.isoformat()}): the topic, the host and the speakers' companies in the last 7 days",
                    "seed_ref": f"event_folder:{f}", "window": window(today, 7)})
    return out


def load_triage(state_dir: str) -> list[dict]:
    """Pre-event triage manifests -> {title, date, topics, companies, ref}. Only event title/date and
    the names of topic and company entities are kept; person entities are never copied out."""
    out = []
    try:
        files = sorted(f for f in os.listdir(os.path.join(state_dir, "research")) if f.endswith(".manifest.json"))
    except OSError:
        return out
    for fn in files:
        try:
            d = json.load(open(os.path.join(state_dir, "research", fn), encoding="utf-8"))
            ev = d["event"]
            ents = d.get("entities") or []
            out.append({"title": str(ev["title"]), "date": str(ev["event_date"]), "ref": fn,
                        "topics": [e["name"] for e in ents if e.get("type") == "topic" and e.get("name")],
                        "companies": [e["name"] for e in ents if e.get("type") == "company" and e.get("name")]})
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return out


def room_queries(events: list[dict], links: list[dict], topics: dict[str, str], companies: dict[str, str],
                 topic_theme: dict[str, str], names: dict[str, str], today: date) -> list[dict]:
    """Pure: raw GET rows -> room_topic / room_entity seeds. Only topic and company links are read."""
    title = {e["id"]: e.get("title") or "" for e in events}
    seen, topics_out, ents_out = set(), [], []
    for ln in links:
        et, eid, ev = ln.get("entity_type"), ln.get("entity_id"), ln.get("event_id")
        if ev not in title or (et, eid) in seen:
            continue
        if et == "topic" and eid in topics:
            seen.add((et, eid))
            tid = topic_theme.get(eid)
            theme = names.get(tid) if tid else None
            topics_out.append({"theme": theme, "theme_id": tid, "kind": "room_topic",
                               "query": f"{theme + ': ' if theme else ''}{topics[eid]}: what is happening outside the room "
                                        f"in the last 14 days",
                               "seed_ref": f"event:{ev}/topic:{eid}", "window": window(today, 14)})
        elif et == "company" and eid in companies:
            seen.add((et, eid))
            ents_out.append({"theme": None, "theme_id": None, "kind": "room_entity",
                             "query": f"{companies[eid]}: funding, launches, partnerships and hires in the last 28 days",
                             "seed_ref": f"event:{ev}/company:{eid}", "window": window(today, 28)})
    return topics_out[:ROOM_CAP] + ents_out[:ROOM_CAP]


# ---------------------------------------------------------------------------
# Read layer: GET only, through spine_client (prod REST, .env key). Never exercised by --selftest
# except with a stubbed req.
# ---------------------------------------------------------------------------
def _get(sc, path: str):
    status, body = sc.req("GET", path)
    if status != 200:
        raise RuntimeError(f"GET {path.split('?')[0]} -> HTTP {status}")
    return body


def _in(ids) -> str:
    return "in.(" + ",".join(sorted(ids)) + ")"


def fetch_theme_week(sc) -> list[dict]:
    qs = urllib.parse.urlencode({"view": "mi.theme_week",
                                 "filters": json.dumps({"weeks": WEEKS, "limit": 5000}, separators=(",", ":"))})
    payload = _get(sc, f"/rpc/mi_slice?{qs}")
    if not isinstance(payload, dict) or payload.get("view") != "mi.theme_week":
        raise RuntimeError("mi_slice returned another view; refusing")
    return payload["rows"]


def fetch_room(sc, today: date) -> tuple:
    lo = (today - timedelta(days=ROOM_DAYS)).isoformat()
    events = _get(sc, f"/event?select=id,title,event_date&kind=eq.attended&event_date=gte.{lo}"
                      f"&event_date=lte.{today.isoformat()}T23:59:59Z&order=event_date.desc")
    if not events:
        return [], [], {}, {}, {}
    links = _get(sc, f"/event_entity?select=event_id,entity_type,entity_id&event_id={_in(e['id'] for e in events)}"
                     f"&entity_type=in.(topic,company)")
    tids = {ln["entity_id"] for ln in links if ln["entity_type"] == "topic"}
    cids = {ln["entity_id"] for ln in links if ln["entity_type"] == "company"}
    topics, companies, topic_theme = {}, {}, {}
    for chunk in _chunks(sorted(tids)):
        topics.update({t["id"]: t["name"] for t in _get(sc, f"/topic?select=id,name&id={_in(chunk)}")})
        topic_theme.update({m["topic_id"]: m["cluster_id"] for m in
                            _get(sc, f"/topic_cluster_membership?select=topic_id,cluster_id&topic_id={_in(chunk)}"
                                     f"&valid_to=is.null")})
    for chunk in _chunks(sorted(cids)):
        companies.update({c["id"]: c["name"] for c in _get(sc, f"/company?select=id,name&id={_in(chunk)}")})
    return events, links, topics, companies, topic_theme


def fetch_topic_themes(sc, topic_names: list[str]) -> dict[str, str]:
    """lower(topic name) -> theme_id (open cluster membership), GET only."""
    names = sorted({n for n in topic_names if n})
    out: dict[str, str] = {}
    for chunk in _chunks(names):
        quoted = ",".join('"' + n.replace('\\', '\\\\').replace('"', '\\"') + '"' for n in chunk)
        rows = _get(sc, "/topic?select=id,name&name=in." + urllib.parse.quote(f"({quoted})", safe="(),"))
        ids = {r["id"]: r["name"] for r in rows}
        if not ids:
            continue
        for m in _get(sc, f"/topic_cluster_membership?select=topic_id,cluster_id&topic_id={_in(ids)}&valid_to=is.null"):
            out[ids[m["topic_id"]].lower()] = m["cluster_id"]
    return out


def _chunks(xs, n=50):
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


def build(theme_rows, room, triage, folders, triage_themes, today) -> tuple[list[dict], dict]:
    names = theme_names(theme_rows)
    vel, report = velocity_queries(theme_rows, today)
    events, links, topics, companies, topic_theme = room
    seeds = (vel + event_queries(triage, folders, today, names, triage_themes)
             + room_queries(events, links, topics, companies, topic_theme, names, today)
             + gap_queries(theme_rows, today))
    assert all(s["kind"] in EMITTED_KINDS for s in seeds)
    report["by_kind"] = {k: sum(1 for s in seeds if s["kind"] == k) for k in EMITTED_KINDS if any(s["kind"] == k for s in seeds)}
    report["room_events"] = len(events)
    return seeds, report


def list_folders(events_dir: str) -> list[str]:
    try:
        return [f for f in os.listdir(events_dir) if os.path.isdir(os.path.join(events_dir, f))]
    except OSError:
        return []


def selftest() -> bool:
    fx = json.load(open(os.path.join(FIXTURES, "seed_fixture.json"), encoding="utf-8"))
    today = date.fromisoformat(fx["today"])
    rows = fx["theme_week"]
    ok = True

    def check(name, cond):
        nonlocal ok
        ok &= bool(cond)
        print(f"{'ok  ' if cond else 'FAIL'} {name}")

    weeks = iso_weeks(today)
    check("iso_weeks: 12 labels ending in today's week", len(weeks) == 12 and weeks[-1] == "2026-W46")
    vel, rep = velocity_queries(rows, today)
    vids = [q["theme_id"] for q in vel]
    check("velocity: steady-then-jump theme is rising (obs 12 vs prior_rate 4)", "t-rise" in vids)
    check("velocity: obs under the floor of 5 does not count", "t-small" not in vids)
    check("velocity: lenses never summed (3 attended + 3 research stays quiet)", "t-split" not in vids)
    check("velocity: market lens never seeds velocity", "t-market" not in vids)
    burst = series(rows, weeks)[("t-burst", "research")]
    check("velocity: bursty-but-flat theme stays quiet (the Poisson band fires on it, the permutation does not)",
          poisson_rising(burst) and "t-burst" not in vids)
    check("velocity: real step-up seeds with p < 0.05", any(q["theme_id"] == "t-rise" and " rising " in q["seed_ref"]
                                                              and float(re.search(r"p=([\d.]+)", q["seed_ref"]).group(1)) < ALPHA
                                                              for q in vel))
    check("velocity: new theme (0 prior facts, obs 6) seeds, labelled new",
          any(q["theme_id"] == "t-new" and " new obs=6" in q["seed_ref"] for q in vel))
    check("velocity: new-theme counter-case (0 prior, obs 4 < floor) stays quiet", "t-small" not in vids)
    extra = rows + [{"theme_id": "t-zzz", "theme": "Unrelated", "lens": "research", "iso_week": f"2026-W{w}", "facts": w % 3}
                    for w in range(35, 47)]
    ref = lambda qs: [q["seed_ref"] for q in qs if q["theme_id"] == "t-rise"]
    check("velocity: adding a theme never moves another theme's p (one RNG per theme-lens)",
          ref(vel) and ref(vel) == ref(velocity_queries(extra, today)[0]))
    check("velocity: null band reported, deterministic under the seed",
          rep["null"] == velocity_queries(rows, today)[1]["null"] and rep["null"]["shuffles"] == SHUFFLES)
    gids = [q["theme_id"] for q in gap_queries(rows, today)]
    check("gap: attended/research above the floor with market < 3 is a gap", "t-rise" in gids and "t-split" in gids)
    check("gap: market >= 3 is not a gap", "t-market" not in gids)
    triage = load_triage(os.path.join(FIXTURES, "state"))
    check("triage: unreadable manifest skipped; person entities never copied out",
          len(triage) == 3 and "Pat Placeholder" not in json.dumps(triage) and "example.com/in" not in json.dumps(triage))
    ev = event_queries(triage, fx["folders"], today, theme_names(rows), fx["triage_topic_theme"])
    refs = [q["seed_ref"] for q in ev]
    check("event: triage manifests in today..today+7 seed first; covered, past, far and content folders do not",
          refs == ["triage:rising-theme-meetup.manifest.json", "triage:mystery-evening.manifest.json",
                   "event_folder:11 14 26 Unmatched Social"])
    check("event: theme from triage topic -> cluster; no topic and no word match -> null",
          ev[0]["theme_id"] == "t-rise" and ev[1]["theme_id"] is None and "Fixtureco" in ev[0]["query"])
    check("event: NON_EVENT_RE skips roundup folders", all(NON_EVENT_RE.search(x) for x in
                                                           ("Thursday NYC AI Events", "Upcoming Week (Sep 1-3)")))
    r = fx["room"]
    room = room_queries(r["events"], r["links"], r["topics"], r["companies"], r["topic_theme"], theme_names(rows), today)
    kinds = [q["kind"] for q in room]
    check("room: one room_topic and one room_entity; person links ignored, duplicates folded",
          kinds == ["room_topic", "room_entity"] and not any("person" in q["seed_ref"] for q in room))
    check("room: topic carries its theme via cluster membership", room[0]["theme_id"] == "t-rise")
    seeds, _ = build(rows, (r["events"], r["links"], r["topics"], r["companies"], r["topic_theme"]),
                     triage, fx["folders"], fx["triage_topic_theme"], today)
    check("output: every row has exactly {theme, theme_id, kind, query, seed_ref, window}",
          all(set(s) == {"theme", "theme_id", "kind", "query", "seed_ref", "window"} for s in seeds))

    class StubSC:  # proves the read layer issues GETs only
        verbs = []

        def req(self, method, path, *a, **k):
            self.verbs.append(method)
            if path.startswith("/rpc/mi_slice"):
                return 200, {"view": "mi.theme_week", "rows": rows}
            if path.startswith("/event?"):
                return 200, r["events"]
            if path.startswith("/event_entity"):
                return 200, r["links"]
            if path.startswith("/topic?"):
                return 200, [{"id": k_, "name": v} for k_, v in r["topics"].items()]
            if path.startswith("/topic_cluster_membership"):
                return 200, [{"topic_id": k_, "cluster_id": v} for k_, v in r["topic_theme"].items()]
            if path.startswith("/company?"):
                return 200, [{"id": k_, "name": v} for k_, v in r["companies"].items()]
            return 404, None

    stub = StubSC()
    fetch_theme_week(stub)
    fetch_room(stub, today)
    fetch_topic_themes(stub, ["Speech routing", 'Odd "quoted", name'])
    check("read layer: every call is a GET", stub.verbs and set(stub.verbs) == {"GET"})
    print(f"selftest: {'PASS' if ok else 'FAIL'}")
    return ok


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--selftest"]:
        return 0 if selftest() else 1
    ap = argparse.ArgumentParser(description="Generate the day's theme-sweep queries (read-only).")
    ap.add_argument("--events-dir", default=os.path.join(ROOT, "Event Content"))
    ap.add_argument("--state-dir", default=os.path.join(ROOT, ".claude", ".state"))
    ap.add_argument("--today", default=date.today().isoformat())
    ap.add_argument("--out", help="write the JSON list here instead of stdout")
    a = ap.parse_args(argv)
    today = date.fromisoformat(a.today)
    import spine_client as sc
    triage = load_triage(a.state_dir)
    upcoming = [t for t in triage if (d := _date(t["date"])) and today <= d <= today + timedelta(days=EVENT_DAYS)]
    triage_themes = fetch_topic_themes(sc, [n for t in upcoming for n in t["topics"]])
    seeds, report = build(fetch_theme_week(sc), fetch_room(sc, today), triage, list_folders(a.events_dir),
                          triage_themes, today)
    text = json.dumps(seeds, indent=2)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        print(text)
    n = report["null"]
    print(f"sweep_seed: {len(seeds)} queries {json.dumps(report['by_kind'])} · rising {report['rising_observed']} + new "
          f"{report['new_observed']} of {report['themes']} themes vs shuffle null mean {n['mean']} / p95 {n['p95']} ({n['shuffles']}x) · "
          f"room events (last {ROOM_DAYS}d) {report['room_events']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
