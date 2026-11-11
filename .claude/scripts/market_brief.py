#!/usr/bin/env python3
"""market_brief.py — Monday Market Brief v1: the weekly reader of the knowledge graph (YED-384). READ-ONLY.

Renders one markdown brief for an ISO week (the week the brief is read in, Monday to Sunday). Seven sections,
each degrading to "No data yet (reason)" when its source is not live:

  1 Bottom line          three sentences: what moved, what came in, what it means for the week's rooms
  2 This week's rooms    `Event Content/MM DD YY <title>` folders dated in the week + the pre-event triage
                         manifests in `.claude/.state/research/` (topic and company entities only; person
                         entities are never read out), each with its theme and what the graph already knows
  3 Themes moving        per-lens facts last week vs the prior 8-week weekly mean (mi.theme_week), then
                         sweep_seed's permutation test over 12 weeks with its shuffle null printed beside it
  4 New to the graph     companies whose `created_at` falls in last week vs the prior 8-week weekly mean,
                         plus validated sweep manifests from --sweeps DIR (sweep_manifest.validate, novelty
                         recomputed against the graph's company names)
  5 Room vs market       claim_relation pairs with exactly one first-hand side
  6 Conflicts            `contradicts`, confidence >= 0.7, both sides first_hand or web_verified, max 5
  7 Graph health         reconcile.py completeness (imported, not shelled), lane freshness from lane_registry +
                         lane_run (runs with 0 writes flagged), use_count coverage vs claim_usage

"Last week" is the ISO week before the brief's week, cut at --today when the brief is run early.

Rules this file keeps:
  * GET only, through spine_client.req. No writes, no Notion. Publishing is a later step.
  * Every number carries its do-nothing baseline (CLAUDE.md null-baseline rule).
  * No person names: claim text is never selected, triage person entities are skipped, sweep items render
    company / kind / date / host only (headline, why, quote and people are page-derived and never echoed).
  * `*.PRIVATE*` folders and manifests are skipped by name and never opened.
  * The finished markdown passes spine_client's EMAIL_RE / PHONE_RE or nothing is written (exit 2).

Usage:
  python3 .claude/scripts/market_brief.py [--week 2026-W47] [--today YYYY-MM-DD] [--root DIR]
                                          [--sweeps DIR] [--out PATH]
  python3 .claude/scripts/market_brief.py --selftest      (offline: fixtures/market_brief/, stubbed req)
Default --out: .claude/.state/market-briefs/market-brief-<isoweek>.md (gitignored). Not `.state/briefs/`:
reconcile.py reads that directory as post-event briefs, so a market brief there would count as one.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import urllib.parse
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import spine_client  # noqa: E402  (module import: the selftest stubs spine_client.req)
from spine_client import EMAIL_RE, EMAIL_ALLOWLIST_RE, PHONE_RE  # noqa: E402  (ADR-9 patterns, one source)
import reconcile  # noqa: E402
import sweep_seed  # noqa: E402
import sweep_manifest  # noqa: E402

FIXTURES = os.path.join(HERE, "fixtures", "market_brief")
OUT_DIR = os.path.join(ROOT, ".claude", ".state", "market-briefs")
PRIOR = 8                     # weeks in the baseline rate
LENSES = ("attended", "research", "market")
CONFLICT_MIN = 0.7
CONFLICT_MAX = 5
CONFLICT_TIERS = {"first_hand", "web_verified"}
LIST_MAX = 15                 # names per list before "and N more"
SWEEP_CAP = 50                # items per manifest the brief will accept
PRIVATE_RE = reconcile.PRIVATE_RE
FOLDER_RE = reconcile.FOLDER_RE
NON_EVENT_RE = reconcile.NON_EVENT_RE
HEADERS = ("Bottom line", "This week's rooms", "Themes moving", "New to the graph", "Room vs market",
           "Conflicts", "Graph health")


class NoData(Exception):
    """A source that is not live. The message is ours (table + status), never response text."""


class PIIRefusal(RuntimeError):
    pass


# ---------------------------------------------------------------------------------------------
# read layer: GET only
# ---------------------------------------------------------------------------------------------
def _get(path: str):
    status, body = spine_client.req("GET", path)
    if status >= 400:
        raise NoData(f"GET /{path.lstrip('/').split('?')[0]} returned HTTP {status}")
    return body


def _get_all(path: str, page: int = 1000) -> list:
    out, off = [], 0
    while True:
        rows = _get(f"{path}&limit={page}&offset={off}") or []
        out += rows
        if len(rows) < page:
            return out
        off += page


def _in(ids) -> str:
    return "in.(" + ",".join(sorted(ids)) + ")"


def _chunks(xs, n=50):
    xs = list(xs)
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


# ---------------------------------------------------------------------------------------------
# weeks
# ---------------------------------------------------------------------------------------------
def week_monday(isoweek: str) -> date:
    m = re.fullmatch(r"(\d{4})-W(\d{2})", isoweek)
    if not m:
        raise ValueError("--week must look like 2026-W47")
    return date.fromisocalendar(int(m.group(1)), int(m.group(2)), 1)


def iso_label(d: date) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def default_week(today: date) -> str:
    """The week of the next Monday on or after today (the brief is read on Monday)."""
    return iso_label(today + timedelta(days=(7 - today.weekday()) % 7))


def short(d: date) -> str:
    return f"{d:%a} {d.month}/{d.day}"


# ---------------------------------------------------------------------------------------------
# gather: every source is fetched once; a source that fails is stored as its NoData
# ---------------------------------------------------------------------------------------------
def _try(fn, *a):
    try:
        return fn(*a)
    except NoData as e:
        return e
    except (RuntimeError, OSError, ValueError, KeyError, TypeError) as e:
        return NoData(f"{type(e).__name__} while reading")


def fetch_theme_rows(today: date, as_of: date) -> list[dict]:
    weeks = min(104, sweep_seed.WEEKS + max(0, (today - as_of).days // 7 + 1))
    qs = urllib.parse.urlencode({"view": "mi.theme_week",
                                 "filters": json.dumps({"weeks": weeks, "limit": 5000}, separators=(",", ":"))})
    payload = _get(f"/rpc/mi_slice?{qs}")
    if not isinstance(payload, dict) or payload.get("view") != "mi.theme_week":
        raise NoData("mi_slice returned another view")
    return payload.get("rows") or []


def fetch_companies() -> list[dict]:
    return _get_all("/company?select=id,name,created_at&order=id")


def local_rooms(root: str, mon: date, sun: date) -> list[dict]:
    """Folders and triage manifests dated mon..sun. Manifests give topics and companies (never people);
    a folder is the display name when one matches a manifest on the same day."""
    folders, manifests = [], []
    ec = os.path.join(root, "Event Content")
    for name in sorted(os.listdir(ec)) if os.path.isdir(ec) else []:
        m = FOLDER_RE.match(name)
        if PRIVATE_RE.search(name) or not m or not os.path.isdir(os.path.join(ec, name)):
            continue
        if NON_EVENT_RE.search(m.group(4)):
            continue
        try:
            d = date(2000 + int(m.group(3)), int(m.group(1)), int(m.group(2)))
        except ValueError:
            continue
        if mon <= d <= sun:
            folders.append({"name": name, "title": m.group(4).strip(), "date": d})
    rd = os.path.join(root, ".claude", ".state", "research")
    for fn in sorted(os.listdir(rd)) if os.path.isdir(rd) else []:
        if not fn.endswith(".manifest.json") or PRIVATE_RE.search(fn):
            continue
        try:
            with open(os.path.join(rd, fn), encoding="utf-8") as fh:
                doc = json.load(fh)
            ev, ents = doc["event"], doc.get("entities") or []
            d = sweep_seed._date(reconcile.local_day(ev.get("event_date")))
        except (OSError, ValueError, KeyError, TypeError):
            continue
        if d is None or not mon <= d <= sun:
            continue
        manifests.append({"title": str(ev.get("title") or fn[:-14]), "date": d, "ref": fn,
                          "topics": [e["name"] for e in ents if e.get("type") == "topic" and e.get("name")],
                          "companies": [e["name"] for e in ents if e.get("type") == "company" and e.get("name")]})
    rooms, used = [], set()
    for mf in manifests:
        tk = sweep_seed._tokens(mf["title"])
        hit = next((f for f in folders if f["date"] == mf["date"] and f["name"] not in used
                    and tk & sweep_seed._tokens(f["title"])), None)
        if hit:
            used.add(hit["name"])
        rooms.append({**mf, "name": hit["name"] if hit else mf["title"], "folder": bool(hit)})
    rooms += [{"name": f["name"], "title": f["title"], "date": f["date"], "topics": [], "companies": [],
               "ref": None, "folder": True} for f in folders if f["name"] not in used]
    return sorted(rooms, key=lambda r: (r["date"], r["name"]))


def fetch_room_graph(rooms: list[dict], companies: list[dict]) -> dict:
    """topic name -> theme_id, and company name -> (company_id, claims about it). GET only."""
    topic_theme = sweep_seed.fetch_topic_themes(spine_client, [t for r in rooms for t in r["topics"]])
    by_name = {c["name"].strip().lower(): c["id"] for c in companies if c.get("name")}
    wanted = {by_name[n.strip().lower()] for r in rooms for n in r["companies"] if n.strip().lower() in by_name}
    claims: dict[str, int] = {}
    for chunk in _chunks(sorted(wanted)):
        for row in _get_all(f"/claim_entity?select=entity_id&entity_type=eq.company&entity_id={_in(chunk)}"):
            claims[row["entity_id"]] = claims.get(row["entity_id"], 0) + 1
    return {"topic_theme": topic_theme, "company_ids": by_name, "claims": claims}


def fetch_relations() -> dict:
    rels = _get_all("/claim_relation?select=from_claim_id,to_claim_id,relation,method,confidence,created_at&order=id")
    ids = {r["from_claim_id"] for r in rels} | {r["to_claim_id"] for r in rels}
    claims, about = {}, {}
    for chunk in _chunks(sorted(ids)):
        for c in _get(f"/claim?select=id,provenance_tier,event_id&id={_in(chunk)}") or []:
            claims[c["id"]] = c                                   # never claim_text / quote
        for ce in _get(f"/claim_entity?select=claim_id,entity_id&entity_type=eq.company&claim_id={_in(chunk)}") or []:
            about.setdefault(ce["claim_id"], set()).add(ce["entity_id"])
    return {"rows": rels, "claims": claims, "about": about}


def fetch_lanes() -> dict:
    reg = _get("/lane_registry?select=lane,active,freshness_flag_days,freshness_fail_days&order=lane") or []
    runs = _get_all("/lane_run?select=lane,started_at,status,items_seen,items_written&order=started_at.desc")
    return {"registry": reg, "runs": runs}


def fetch_usage(inv) -> dict:
    total = len(inv["claims"]) if isinstance(inv, dict) else len(_get_all("/claim?select=id&order=id"))
    used = _get_all("/claim?select=id&use_count=gt.0&order=id")
    logged = {r["claim_id"] for r in _get_all("/claim_usage?select=claim_id&order=id")}
    return {"total": total, "use_count_pos": len(used), "logged": len(logged)}


def load_sweeps(sweeps_dir: str | None, companies, mon: date, sun: date):
    """Validated, normalized manifests whose window overlaps the read week (last week included). Invalid ones are
    counted, never rendered. Each is validated against its own window and theme (there is no parent dispatch to
    hold here) and a cap; novelty is recomputed against the graph's company names."""
    if not sweeps_dir:
        return NoData("no --sweeps directory given")
    if not os.path.isdir(sweeps_dir):
        return NoData("the --sweeps directory does not exist")
    known = ({sweep_manifest.norm_name(c["name"]) for c in companies if c.get("name")}
             if isinstance(companies, list) else set())
    lo = mon - timedelta(days=7)
    out = {"valid": [], "invalid": 0, "out_of_window": 0, "files": 0, "novelty_from_graph": bool(known)}
    for fn in sorted(os.listdir(sweeps_dir)):
        if not fn.endswith(".json") or PRIVATE_RE.search(fn):
            continue
        out["files"] += 1
        try:
            m = sweep_manifest.load_manifest(os.path.join(sweeps_dir, fn))
            w = m["window"]
            tid = m.get("theme_id")
            window = (str(w["from"]), str(w["to"]))
        except (OSError, ValueError, UnicodeDecodeError, KeyError, TypeError):
            out["invalid"] += 1
            continue
        r, norm = sweep_manifest.validate(m, known, cap=SWEEP_CAP, window=window,
                                          theme_id=tid if sweep_manifest.is_uuid(tid) else None)
        if r.errors or not norm:
            out["invalid"] += 1
            continue
        f, t = sweep_manifest.parse_date(window[0]), sweep_manifest.parse_date(window[1])
        if t < lo or f > sun:
            out["out_of_window"] += 1
            continue
        out["valid"].append(norm)
    return out


def gather(root: str, isoweek: str, today: date, sweeps_dir: str | None) -> dict:
    mon = week_monday(isoweek)
    sun = mon + timedelta(days=6)
    as_of = min(today, mon - timedelta(days=1))
    data = {"week": isoweek, "mon": mon, "sun": sun, "as_of": as_of, "today": today}
    data["themes"] = _try(fetch_theme_rows, today, as_of)
    data["companies"] = _try(fetch_companies)
    data["rooms"] = _try(local_rooms, root, mon, sun)
    data["room_graph"] = (_try(fetch_room_graph, data["rooms"],
                               data["companies"] if isinstance(data["companies"], list) else [])
                          if isinstance(data["rooms"], list) and data["rooms"] else {})
    data["relations"] = _try(fetch_relations)
    inv = _try(reconcile.prod_inventory)
    data["events"] = {e["id"]: e for e in inv["events"]} if isinstance(inv, dict) else {}
    data["recon"] = _try(lambda: reconcile.reconcile(root, inv, today.isoformat())) if isinstance(inv, dict) else inv
    data["lanes"] = _try(fetch_lanes)
    data["usage"] = _try(fetch_usage, inv)
    data["sweeps"] = load_sweeps(sweeps_dir, data["companies"], mon, sun)
    return data


# ---------------------------------------------------------------------------------------------
# compute (pure)
# ---------------------------------------------------------------------------------------------
def theme_stats(rows: list[dict], as_of: date) -> dict:
    """Per-lens last week vs the prior 8-week weekly mean, then sweep_seed's permutation test (same seed,
    same per-theme RNG, so the labels and the null match `sweep_seed.py` on the same day)."""
    weeks = sweep_seed.iso_weeks(as_of)
    ser = sweep_seed.series(rows, weeks)
    names = sweep_seed.theme_names(rows)
    lens = {}
    for ln in LENSES:
        keys = [k for k in ser if k[1] == ln]
        lens[ln] = {"last": sum(ser[k][-1] for k in keys),
                    "prior_mean": sum(sum(ser[k][-1 - PRIOR:-1]) for k in keys) / PRIOR, "themes": len(keys)}
    flagged = []
    for k in sorted(k for k in ser if k[1] in sweep_seed.VELOCITY_LENSES):
        lab, p = sweep_seed.label(ser[k], sweep_seed.perm_dist(ser[k], sweep_seed.key_rng(7, k, "dist")))
        if lab:
            obs, rate, _ = sweep_seed.stats(ser[k])
            flagged.append({"theme_id": k[0], "theme": names.get(k[0]) or "(unnamed theme)", "lens": k[1],
                            "label": lab, "obs": obs, "rate": rate, "p": p})
    _, report = sweep_seed.velocity_queries(rows, as_of)
    flagged.sort(key=lambda f: (f["label"] != "new", f["p"], -f["obs"]))
    eight = {}
    for (tid, ln), c in ser.items():
        eight.setdefault(tid, {})[ln] = sum(c[-PRIOR:])
    return {"weeks": weeks, "lens": lens, "flagged": flagged, "report": report, "names": names, "eight": eight}


def new_companies(companies: list[dict], as_of: date) -> dict:
    """Companies whose created_at (New York day) falls in as_of's ISO week, vs the prior 8 weeks' weekly mean."""
    weeks = sweep_seed.iso_weeks(as_of, PRIOR + 1)
    idx = {w: i for i, w in enumerate(weeks)}
    counts, this = [0] * len(weeks), []
    for c in companies:
        d = sweep_seed._date(reconcile.local_day(c.get("created_at")))
        if d is None or d > as_of:
            continue
        i = idx.get(iso_label(d))
        if i is None:
            continue
        counts[i] += 1
        if i == len(weeks) - 1:
            this.append(c.get("name") or "(unnamed)")
    return {"week": weeks[-1], "count": counts[-1], "prior": counts[:-1], "prior_mean": sum(counts[:-1]) / PRIOR,
            "names": sorted(this, key=str.lower)}


def lane_status(registry: list[dict], runs: list[dict], today: date) -> list[dict]:
    out = []
    for lane in registry:
        rs = [r for r in runs if r.get("lane") == lane["lane"]]          # newest first
        row = {"lane": lane["lane"], "active": lane.get("active"), "flag": lane["freshness_flag_days"],
               "fail": lane["freshness_fail_days"], "runs": len(rs),
               "written": sum(int(r.get("items_written") or 0) for r in rs),
               "seen": sum(int(r.get("items_seen") or 0) for r in rs)}
        zero = 0
        for r in rs:
            if int(r.get("items_written") or 0):
                break
            zero += 1
        row["zero_streak"] = zero
        if rs:
            last = sweep_seed._date(reconcile.local_day(rs[0]["started_at"]))
            row["last"] = last
            row["age"] = (today - last).days if last else None
        if not rs:
            row["state"] = "never run"
        elif row["age"] is not None and row["age"] >= row["fail"]:
            row["state"] = "FAIL (stale)"
        elif zero >= 3:
            row["state"] = "FAIL (0 writes in last 3+ runs)"
        elif zero >= 2 or (row["age"] is not None and row["age"] >= row["flag"]):
            row["state"] = "FLAG" + (" (0 writes)" if zero >= 2 else " (stale)")
        elif zero:
            row["state"] = "watch (0 writes in the last run)"
        else:
            row["state"] = "ok"
        out.append(row)
    return out


# ---------------------------------------------------------------------------------------------
# render (pure)
# ---------------------------------------------------------------------------------------------
def _nodata(x) -> str:
    return f"_No data yet ({x})._"


def _nodata_inline(label: str, x) -> str:
    return f"{label}: no data yet ({x})."


def _names(xs: list[str], cap: int = LIST_MAX) -> str:
    xs = list(xs)
    return ", ".join(xs[:cap]) + (f", and {len(xs) - cap} more" if len(xs) > cap else "")


def _f(x: float) -> str:
    return f"{x:.1f}".rstrip("0").rstrip(".") if x != int(x) else str(int(x))


def chance_verdict(rep: dict) -> tuple[int, str]:
    flagged = rep["rising_observed"] + rep["new_observed"]
    n = rep["null"]
    if flagged <= n["p95"]:
        return flagged, "no information: chance alone flags that many"
    return flagged, "more than chance alone would flag"


def room_theme(room: dict, rg: dict, names: dict) -> tuple[str | None, str | None]:
    votes: dict[str, int] = {}
    for t in room["topics"]:
        tid = rg.get("topic_theme", {}).get(t.lower())
        if tid in names:
            votes[tid] = votes.get(tid, 0) + 1
    if votes:
        tid = max(sorted(votes), key=lambda k: votes[k])
        return tid, names[tid]
    return sweep_seed.match_theme(" ".join([room["title"], *room["topics"]]), names)


def render(d: dict) -> str:
    mon, sun, as_of = d["mon"], d["sun"], d["as_of"]
    last_week = iso_label(as_of)
    partial = as_of < mon - timedelta(days=1)
    ts = theme_stats(d["themes"], as_of) if isinstance(d["themes"], list) else d["themes"]
    nc = new_companies(d["companies"], as_of) if isinstance(d["companies"], list) else d["companies"]
    rooms = d["rooms"]
    rg = d["room_graph"] if isinstance(d["room_graph"], dict) else {}
    rising_ids = {f["theme_id"] for f in ts["flagged"]} if isinstance(ts, dict) else set()
    names = ts["names"] if isinstance(ts, dict) else {}

    L = [f"# Monday Market Brief: {d['week']} (week of {short(mon)})", "",
         f"Read-only render from the knowledge graph on {d['today'].isoformat()}. \"Last week\" means {last_week}"
         + (f", counted only through {short(as_of)} because the week is not over yet." if partial else ".")
         + " Every number sits beside its do-nothing baseline: what you would see if nothing had changed, "
           "or if chance alone were at work.", ""]

    # 1 Bottom line
    L += ["## Bottom line", ""]
    s = []
    if isinstance(ts, dict):
        flagged, verdict = chance_verdict(ts["report"])
        n = ts["report"]["null"]
        s.append(f"{flagged} of {ts['report']['themes']} themes {'looks' if flagged == 1 else 'look'} like they are rising over the last 4 weeks, "
                 f"against {_f(n['mean'])} that shuffled weeks flag on average, so the list is "
                 f"{'no information yet' if verdict.startswith('no') else 'worth reading'}.")
    else:
        s.append(f"Theme movement is not measurable this week ({ts}).")
    if isinstance(nc, dict):
        s.append(f"{nc['count']} companies entered the graph in {nc['week']}, against a prior 8-week average "
                 f"of {_f(nc['prior_mean'])} a week.")
    else:
        s.append(f"New-company counts are unavailable ({nc}).")
    if isinstance(rooms, list) and rooms:
        on_rising = [r for r in rooms if room_theme(r, rg, names)[0] in rising_ids]
        s.append(f"{len(rooms)} rooms are on file for the week of {short(mon)}; "
                 + (f"{len(on_rising)} sit on a theme flagged above, so expect the room to be talking about it."
                    if on_rising else "none sit on a theme flagged above, so walk in with what the graph already "
                                      "knows, not a trend story."))
    elif isinstance(rooms, list):
        s.append(f"No rooms are on file for the week of {short(mon)} yet, so there is nothing to prepare against "
                 f"until the week's events are researched.")
    else:
        s.append(f"This week's rooms could not be read ({rooms}).")
    L += [" ".join(s), ""]

    # 2 This week's rooms
    L += ["## This week's rooms", ""]
    if not isinstance(rooms, list):
        L += [_nodata(rooms), ""]
    elif not rooms:
        L += [f"No event folders or pre-event triage manifests are dated {short(mon)} to {short(sun)} yet. "
              f"Baseline: 0 rooms, which is what an unresearched week looks like.", ""]
    else:
        researched = sum(1 for r in rooms if r["ref"])
        L += [f"{len(rooms)} rooms, {researched} with a pre-event triage manifest (the rest have a folder only; "
              f"baseline: every room researched before the week starts).", ""]
        if isinstance(d["room_graph"], NoData):
            L += [f"Graph lookups failed ({d['room_graph']}); themes come from title words only.", ""]
        for r in rooms:
            tid, theme = room_theme(r, rg, names)
            line = f"- **{r['name']}** ({short(r['date'])}). Theme: {theme or 'no single theme matched'}"
            if tid and isinstance(ts, dict):
                e = ts["eight"].get(tid, {})
                line += (f" ({' · '.join(f'{ln} {e.get(ln, 0)}' for ln in LENSES)} facts in the last 8 weeks"
                         f"{'; flagged as rising' if tid in rising_ids else ''}).")
            else:
                line += "."
            L.append(line)
            if r["topics"]:
                L.append(f"  - Topics: {_names(r['topics'], 6)}.")
            if r["companies"]:
                ids = rg.get("company_ids", {})
                known = [ids[c.strip().lower()] for c in r["companies"] if c.strip().lower() in ids]
                claims = sum(rg.get("claims", {}).get(i, 0) for i in known)
                L.append(f"  - Companies: {_names(r['companies'], 8)}. The graph knows {len(known)} of "
                         f"{len(r['companies'])} by name, with {claims} claims about them (baseline: 0 of "
                         f"{len(r['companies'])}, a room the graph has never seen).")
            elif not r["ref"]:
                L.append("  - No triage manifest yet, so no topics or companies to look up.")
        L.append("")

    # 3 Themes moving
    L += ["## Themes moving", ""]
    if not isinstance(ts, dict):
        L += [_nodata(ts), ""]
    else:
        L += [f"Facts per lens in {last_week} against the weekly average of the 8 weeks before it "
              f"({ts['weeks'][-1 - PRIOR]} to {ts['weeks'][-2]}). A fact is one claim or one event tied to a theme. "
              f"Lenses are never added together: attended is what Alex heard in the room, research is what pre-event "
              f"research found, market is what the outside world did.", "",
              "| lens | facts last week | prior 8-week weekly mean (baseline) | themes with any fact |",
              "|---|---:|---:|---:|"]
        for ln in LENSES:
            x = ts["lens"][ln]
            L.append(f"| {ln} | {x['last']} | {_f(round(x['prior_mean'], 1))} | {x['themes']} |")
        rep, n = ts["report"], ts["report"]["null"]
        flagged, verdict = chance_verdict(rep)
        L += ["", f"**Rising or new themes (last 4 weeks vs the 8 before, permutation test): {flagged} "
                  f"({rep['rising_observed']} rising, {rep['new_observed']} new) of {rep['themes']} themes. "
                  f"Shuffle null: {_f(n['mean'])} on average, 95th percentile {n['p95']}, from {n['shuffles']} "
                  f"shuffles.** That is {verdict}.",
              "",
              "How to read it: the test shuffles each theme's 12 weekly counts and asks how often the last 4 weeks "
              "come out this high by luck. Doing that across every theme shows how many themes luck alone would flag. "
              "When the real count is not above that, the flags are noise until more weeks of data arrive.", ""]
        for f in ts["flagged"]:
            L.append(f"- {f['theme']} ({f['lens']} lens): {f['obs']} facts in the last 4 weeks vs {_f(round(f['rate'], 1))} "
                     f"expected from the prior rate; {f['label']}, p = {f['p']:.3f}.")
        if not ts["flagged"]:
            L.append("- No theme passes the test this week.")
        L.append("")

    # 4 New to the graph
    L += ["## New to the graph", ""]
    if not isinstance(nc, dict):
        L += [_nodata(nc), ""]
    else:
        L += [f"**{nc['count']} companies first seen in {nc['week']}** (by when their row was created), against a "
              f"prior 8-week average of {_f(round(nc['prior_mean'], 1))} a week (weekly: "
              f"{', '.join(str(x) for x in nc['prior'])}). Bulk backfills raise the average, so a quiet week can "
              f"sit well under it.", ""]
        if nc["names"]:
            L += [f"New: {_names(nc['names'])}.", ""]
    sw = d["sweeps"]
    if isinstance(sw, NoData):
        L += [_nodata_inline("Sweep manifests", sw), ""]
    else:
        items = [it for m in sw["valid"] for it in m.get("items", [])]
        ents = [e for m in sw["valid"] for e in m.get("new_entities", [])]
        nov = sum(1 for it in items if it.get("novel"))
        L += [f"**Sweeps:** {len(sw['valid'])} valid manifest{'' if len(sw['valid']) == 1 else 's'} of {sw['files']} files ({sw['invalid']} failed "
              f"validation and are not shown, {sw['out_of_window']} cover another week). {len(items)} items, {nov} "
              f"about a company the graph does not have yet (baseline: every item is novel when the graph knows "
              f"nothing; novelty is rechecked against the graph's {'company names' if sw['novelty_from_graph'] else 'company names, which could not be read, so all items count as novel'}). "
              f"Only company, kind, date and source are shown; headlines are web text and stay in the manifest.", ""]
        for m in sw["valid"]:
            for it in m.get("items", []):
                host = urllib.parse.urlsplit(it.get("canonical_url") or it.get("url") or "").hostname or "?"
                L.append(f"- {'**NEW** ' if it.get('novel') else ''}{it.get('company')} · {it.get('event_kind')}"
                         f"{'/' + it['signal_type'] if it.get('signal_type') else ''} · {it.get('date')} · {host}")
        if ents:
            L.append(f"- Proposed new entities: {_names([('**NEW** ' if e.get('novel') else '') + str(e.get('name')) for e in ents])}.")
        L.append("")

    # 5 Room vs market
    L += ["## Room vs market", ""]
    rel = d["relations"]
    if isinstance(rel, NoData):
        L += [_nodata(rel), ""]
    else:
        def room_side(r):
            t = [rel["claims"].get(r["from_claim_id"], {}).get("provenance_tier"),
                 rel["claims"].get(r["to_claim_id"], {}).get("provenance_tier")]
            return t.count("first_hand") == 1
        rvm = [r for r in rel["rows"] if room_side(r)]
        cor = sum(1 for r in rvm if r["relation"] == "corroborates")
        con = sum(1 for r in rvm if r["relation"] == "contradicts")
        if not rel["rows"]:
            L += ["claim_relation has 0 rows, so no claim heard in a room has been checked against the web or the "
                  "market yet. Baseline: 0, which is where it stays until the claim reviewer (ADR-14) runs.", ""]
        else:
            L += [f"{len(rvm)} room-vs-market links of {len(rel['rows'])} claim relations: the room corroborated the "
                  f"market {cor} times and contradicted it {con} times (baseline: 0 before the reviewer ran).", ""]

    # 6 Conflicts
    L += ["## Conflicts", ""]
    if isinstance(rel, NoData):
        L += [_nodata(rel), ""]
    else:
        conf = [r for r in rel["rows"] if r["relation"] == "contradicts" and (r.get("confidence") or 0) >= CONFLICT_MIN
                and {rel["claims"].get(r["from_claim_id"], {}).get("provenance_tier"),
                     rel["claims"].get(r["to_claim_id"], {}).get("provenance_tier")} <= CONFLICT_TIERS]
        conf.sort(key=lambda r: -float(r.get("confidence") or 0))
        comp = {c["id"]: c["name"] for c in d["companies"]} if isinstance(d["companies"], list) else {}
        if not conf:
            L += [f"No contradictions at confidence {CONFLICT_MIN} or above between first-hand or web-verified "
                  f"claims. Baseline: 0.", ""]
        else:
            L.append(f"{len(conf)} contradictions at confidence {CONFLICT_MIN} or above; showing "
                     f"{min(len(conf), CONFLICT_MAX)}. Claim ids open with `retrieve.py`; resolve by Notion comment.")
            L.append("")
            for r in conf[:CONFLICT_MAX]:
                sides = []
                for cid in (r["from_claim_id"], r["to_claim_id"]):
                    c = rel["claims"].get(cid, {})
                    ev = d["events"].get(c.get("event_id"), {}).get("title")
                    sides.append(f"c:{cid[:8]} ({c.get('provenance_tier', '?')}{', ' + ev if ev else ''})")
                about = sorted({comp.get(e, "?") for cid in (r["from_claim_id"], r["to_claim_id"])
                                for e in rel["about"].get(cid, ())})
                L.append(f"- {sides[0]} contradicts {sides[1]} · confidence {float(r['confidence']):.2f}"
                         + (f" · about {_names(about, 4)}" if about else ""))
            L.append("")

    # 7 Graph health
    L += ["## Graph health", ""]
    rc = d["recon"]
    if isinstance(rc, NoData):
        L += [_nodata_inline("Completeness", rc), ""]
    else:
        sm = rc["summary"]
        L += ["| completeness (reconcile.py) | now | baseline |", "|---|---:|---:|"]
        for k, label in reconcile.METRIC_LABELS.items():
            b = (reconcile._pct(reconcile.BASELINE_2026_11_10[k]) + " (2026-11-10)"
                 if k in reconcile.BASELINE_2026_11_10 else "none yet: this run is the first")
            L.append(f"| {label} | {reconcile._pct(sm['metrics'][k])} | {b} |")
        L += ["", f"Open gaps: {sum(sm['gaps'].values())} across {sm['event_rows']} event rows "
                  f"({', '.join(f'{g} {n}' for g, n in sm['gaps'].items() if n) or 'none'}).", ""]
    ln = d["lanes"]
    if isinstance(ln, NoData):
        L += [_nodata_inline("Lanes", ln), ""]
    else:
        L += ["| lane | active | last run | age (flag / fail days) | runs | seen | written | state |",
              "|---|---|---|---|---:|---:|---:|---|"]
        for r in lane_status(ln["registry"], ln["runs"], d["today"]):
            last = r["last"].isoformat() if r.get("last") else "never"
            age = f"{r['age']} ({r['flag']} / {r['fail']})" if r.get("age") is not None else f"- ({r['flag']} / {r['fail']})"
            L.append(f"| {r['lane']} | {'yes' if r['active'] else 'no'} | {last} | {age} | {r['runs']} | {r['seen']} | "
                     f"{r['written']} | {r['state']} |")
        zero = [r["lane"] for r in lane_status(ln["registry"], ln["runs"], d["today"]) if r["runs"] and not r["written"]]
        L += ["", (f"Lanes that ran but never wrote a row: {', '.join(zero)}. The kill rule is 0 writes in 2 runs = "
                   f"FLAG, 3 = FAIL; the baseline for a live lane is at least one write per run." if zero else
                   "Every lane that ran has written at least one row."), ""]
    us = d["usage"]
    if isinstance(us, NoData):
        L += [_nodata_inline("use_count", us), ""]
    else:
        pct = f"{100 * us['use_count_pos'] / us['total']:.1f}%" if us["total"] else "n/a"
        L += [f"use_count coverage: {us['use_count_pos']} of {us['total']} claims ({pct}) show use_count above 0, "
              f"while claim_usage has logged {us['logged']} distinct used claims. Baseline: 0, because no trigger "
              f"copies claim_usage into use_count yet (migration 0021 plans it). The gap between the two numbers is "
              f"the trigger's job.", ""]
    L += ["---", "", "Publishing to Notion is a later step; this file is the review copy."]
    return "\n".join(L) + "\n"


def assert_clean(text: str) -> None:
    """Fail closed: an email- or phone-shaped string anywhere means nothing is written."""
    for m in EMAIL_RE.finditer(text):
        if not EMAIL_ALLOWLIST_RE.search(m.group(0)):
            raise PIIRefusal("market_brief: an email-shaped string reached the brief; refusing to write it")
    if PHONE_RE.search(text):
        raise PIIRefusal("market_brief: a phone-shaped string reached the brief; refusing to write it")


def build(root: str, isoweek: str, today: date, sweeps_dir: str | None) -> str:
    text = render(gather(root, isoweek, today, sweeps_dir))
    assert_clean(text)
    return text


def main(argv: list[str]) -> int:
    if argv[:1] == ["--selftest"]:
        return 0 if selftest() else 1
    ap = argparse.ArgumentParser(description="Render the Monday Market Brief for an ISO week (read-only).")
    ap.add_argument("--week", help="ISO week, e.g. 2026-W47 (default: the week of the next Monday)")
    ap.add_argument("--today", default=date.today().isoformat(), help="cut-off date (default: today)")
    ap.add_argument("--root", default=ROOT, help="checkout whose Event Content/ and .claude/.state/ are read")
    ap.add_argument("--sweeps", metavar="DIR", help="directory of theme-sweeper manifests (*.json)")
    ap.add_argument("--out", help="output path (default .claude/.state/market-briefs/market-brief-<week>.md)")
    a = ap.parse_args(argv)
    today = date.fromisoformat(a.today)
    week = a.week or default_week(today)
    try:
        week_monday(week)
    except ValueError as e:
        ap.error(str(e))
    try:
        text = build(os.path.abspath(a.root), week, today, a.sweeps)
    except PIIRefusal as e:
        print(str(e), file=sys.stderr)
        return 2
    out = a.out or os.path.join(OUT_DIR, f"market-brief-{week}.md")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"market_brief: {week} -> {out}")
    return 0


# ---------------------------------------------------------------------------------------------
# selftest — offline: fixture tree in a temp dir + a GET-only stub of spine_client.req
# ---------------------------------------------------------------------------------------------
def _stub_req(prod: dict, seen: list, fail: set = frozenset()):
    """PostgREST stand-in: GET only; honours select (aliases), eq/gt/gte/in/is filters; one page."""
    def match(row, col, op_val):
        op, _, val = op_val.partition(".")
        v = row.get(col)
        if op == "eq":
            return str(v) == val
        if op in ("gt", "gte"):
            try:
                return (float(v) > float(val)) if op == "gt" else (float(v) >= float(val))
            except (TypeError, ValueError):
                return (str(v) > val) if op == "gt" else (str(v) >= val)
        if op == "in":
            vals = [x.strip().strip('"') for x in val.strip("()").split(",")]
            return str(v) in vals
        if op == "is":
            return v is None
        return True

    def req(method, path, body=None, **kw):
        seen.append((method, path))
        if method != "GET" or body is not None:
            raise AssertionError(f"market_brief issued a non-GET: {method}")
        table, _, qs = path.lstrip("/").partition("?")
        if table in fail:
            return 404, "not found"
        if table == "rpc/mi_slice":
            return 200, prod["mi_slice"]
        if re.search(r"offset=(?!0(&|$))\d+", qs):
            return 200, []
        params = urllib.parse.parse_qsl(qs, keep_blank_values=True)
        rows = list(prod.get(table, []))
        for k, v in params:
            if k not in ("select", "order", "limit", "offset"):
                rows = [r for r in rows if match(r, k, v)]
        sel = dict(params).get("select", "*")
        if sel != "*":
            out = []
            for r in rows:
                o = {}
                for f in sel.split(","):
                    alias, _, expr = f.partition(":")
                    o[alias] = r.get(alias) if expr else r.get(f)
                out.append(o)
            rows = out
        return 200, rows
    return req


def _materialize(spec: dict, tmp: str) -> None:
    for rel in spec["files"]:
        p = os.path.join(tmp, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").close()
    for rel, doc in spec["json"].items():
        p = os.path.join(tmp, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)


def selftest() -> bool:
    checks = []

    def ok(name, cond):
        checks.append((name, bool(cond)))

    with open(os.path.join(FIXTURES, "prod.json"), encoding="utf-8") as fh:
        prod = json.load(fh)
    with open(os.path.join(FIXTURES, "tree.json"), encoding="utf-8") as fh:
        spec = json.load(fh)
    sweeps = os.path.join(FIXTURES, "sweeps")
    real_req = spine_client.req
    tmp = tempfile.mkdtemp(prefix="market_brief_")
    try:
        _materialize(spec, tmp)
        today = date(2026, 11, 16)
        seen: list = []
        spine_client.req = _stub_req(prod, seen)
        text = build(tmp, "2026-W47", today, sweeps)

        ok("all seven section headers, in order",
           [h for h in re.findall(r"^## (.+)$", text, re.M)] == list(HEADERS))
        ok("only GETs were issued", seen and all(m == "GET" for m, _ in seen))
        ok("claim text is never selected", not any("claim_text" in p or "quote" in p for _, p in seen))
        ok("default week: Wed 2026-11-11 -> 2026-W47", default_week(date(2026, 11, 11)) == "2026-W47")
        ok("as_of: a Monday brief reads last week through Sunday", "Last week\" means 2026-W46." in text)
        # rooms
        ok("rooms: folder name is the display name when a manifest matches",
           "**11 17 26 Voice Agents Night**" in text)
        ok("rooms: folder-only room listed", "**11 19 26 Robotics Demo Day**" in text)
        ok("rooms: out-of-week folder excluded", "Last Week Party" not in text and "Next Month" not in text)
        ok("rooms: content folder (Upcoming Week) excluded", "Upcoming Week" not in text)
        ok("rooms: PRIVATE folder and manifest never surface", "Secret" not in text and "Hidden Co" not in text)
        ok("rooms: person entities from the manifest never surface", "Pat Speakerson" not in text)
        ok("rooms: theme from topic membership", "Theme: Voice AI Infrastructure (attended" in text)
        ok("rooms: graph knowledge counts claims", "The graph knows 1 of 2 by name, with 3 claims" in text)
        # themes
        ok("themes: shuffle null printed beside the rising count", re.search(r"Shuffle null: [\d.]+ on average", text))
        nul = {"shuffles": 2000, "mean": 2.3, "p95": 4, "max": 6}
        ok("themes: verdict is 'no information' at or under the null p95 (today's prod shape: 1 vs 2.3)",
           chance_verdict({"rising_observed": 1, "new_observed": 0, "null": nul})[1].startswith("no information"))
        ok("themes: verdict is 'more than chance' above the null p95",
           chance_verdict({"rising_observed": 4, "new_observed": 1, "null": nul})[1].startswith("more than chance"))
        ok("themes: per-lens table carries the prior 8-week mean", "| attended | 2 | 0.5 |" in text)
        rows = prod["mi_slice"]["rows"]
        ts = theme_stats(rows, date(2026, 11, 15))
        _, rep = sweep_seed.velocity_queries(rows, date(2026, 11, 15))
        ok("themes: labels agree with sweep_seed's own counts",
           sum(1 for f in ts["flagged"] if f["label"] == "rising") >= rep["rising_observed"]
           and rep["rising_observed"] + rep["new_observed"] <= len(ts["flagged"]))
        ok("themes: a burst with zero prior weeks is labelled new", any(f["label"] == "new" for f in ts["flagged"]))
        ok("themes: the rendered verdict is the computed one", f"That is {chance_verdict(rep)[1]}." in text)
        # new to graph
        ok("new: companies created last week counted with baseline",
           "**2 companies first seen in 2026-W46**" in text and "prior 8-week average of 1 a week" in text)
        ok("sweeps: valid manifest rendered, invalid one counted and hidden",
           "1 valid manifest of 3 files (1 failed validation" in text and "1 cover another week" in text)
        ok("sweeps: novelty recomputed against graph names", "- **NEW** Quillstack Labs" in text
           and "- Knownco Inc." in text)
        ok("sweeps: no headline, people or quote text", "Dana Example" not in text and "low-latency" not in text
           and "fastest model" not in text)
        # relations
        ok("room vs market: honest empty line on 0 rows", "claim_relation has 0 rows" in text)
        ok("conflicts: empty with baseline", "No contradictions at confidence 0.7" in text)
        # health
        ok("health: completeness table with plan baseline", "attended events with >=1 first-hand claim" in text
           and "(2026-11-10)" in text)
        ok("health: lane with runs and 0 writes flagged", "| hiring_pulse | yes |" in text
           and "FAIL (0 writes in last 3+ runs)" in text and "never wrote a row: hiring_pulse" in text)
        ok("health: never-run lane shown", "| feeds | no | never |" in text)
        ok("health: one run with writes and a stale age flags stale, not ok", "| research_frontier | no | 2026-11-09 | 7 (7 / 14) | 1 | 250 | 5 | FLAG (stale) |" in text)
        ok("health: a lane with 1 run and 0 writes is 'watch', never 'ok'",
           lane_status([{"lane": "x", "active": False, "freshness_flag_days": 7, "freshness_fail_days": 14}],
                       [{"lane": "x", "started_at": "2026-11-15T12:00:00+00:00", "items_written": 0}],
                       date(2026, 11, 16))[0]["state"].startswith("watch"))
        ok("no doubled period after an inline no-data line", ".." not in text)
        ok("health: use_count coverage vs claim_usage", "use_count coverage: 0 of 6 claims (0.0%)" in text
           and "logged 2 distinct used claims" in text)
        ok("publishing is noted as a later step", "Publishing to Notion is a later step" in text)

        # conflicts populated: >=0.7, both tiers allowed, max 5, no claim text
        prod2 = json.loads(json.dumps(prod))
        prod2["claim_relation"] = prod["_claim_relation_populated"]
        spine_client.req = _stub_req(prod2, [])
        t2 = build(tmp, "2026-W47", today, None)
        ok("conflicts: only >=0.7 between first_hand/web_verified, capped at 5",
           "7 contradictions at confidence 0.7 or above; showing 5." in t2 and t2.count(" contradicts c:") == 5)
        ok("conflicts: the 0.6 and the reference-tier relation are left out", "0.60" not in t2)
        ok("room vs market counts one-first-hand pairs", "room-vs-market links of 10 claim relations" in t2)
        ok("conflicts: about-company names resolved", "about Knownco" in t2)
        ok("sweeps: absent --sweeps degrades with a reason", "no --sweeps directory given" in t2)

        # degrade: sources not live
        spine_client.req = _stub_req(prod, [], fail={"rpc/mi_slice", "claim_relation", "lane_run"})
        t3 = build(tmp, "2026-W47", today, None)
        ok("degrade: themes say no data with a reason", "_No data yet (GET /rpc/mi_slice returned HTTP 404)._" in t3)
        ok("degrade: relations and conflicts say no data", t3.count("GET /claim_relation returned HTTP 404") == 2)
        ok("degrade: lanes say no data", "Lanes: no data yet (GET /lane_run returned HTTP 404)." in t3)
        ok("degrade: all seven headers still render", re.findall(r"^## (.+)$", t3, re.M) == list(HEADERS))

        # PII fail closed
        prod4 = json.loads(json.dumps(prod))
        prod4["company"].append({"id": "c-pii", "name": "Contact ops@acme-example.com",
                                 "created_at": "2026-11-12T15:00:00+00:00"})
        spine_client.req = _stub_req(prod4, [])
        try:
            build(tmp, "2026-W47", today, None)
            ok("PII: an email-shaped company name refuses the whole brief", False)
        except PIIRefusal:
            ok("PII: an email-shaped company name refuses the whole brief", True)
        out = os.path.join(tmp, "out.md")
        rc = main(["--week", "2026-W47", "--today", "2026-11-16", "--root", tmp, "--out", out])
        ok("PII: main exits 2 and writes nothing", rc == 2 and not os.path.exists(out))
        ok("PII: noreply addresses are allowed", assert_clean("noreply@github.com") is None)
        try:
            assert_clean("call +1 212-555-0147")
            ok("PII: a phone number refuses", False)
        except PIIRefusal:
            ok("PII: a phone number refuses", True)
        spine_client.req = _stub_req(prod, [])
        rc = main(["--week", "2026-W47", "--today", "2026-11-16", "--root", tmp, "--out", out])
        ok("main writes the brief to --out", rc == 0 and os.path.exists(out))
        ok("default output is outside .state/briefs (reconcile reads that dir)",
           os.path.basename(OUT_DIR) == "market-briefs")
    finally:
        spine_client.req = real_req
        shutil.rmtree(tmp, ignore_errors=True)

    failed = [n for n, c in checks if not c]
    for n, c in checks:
        print(f"{'ok  ' if c else 'FAIL'} {n}")
    print(f"selftest: {len(checks) - len(failed)}/{len(checks)} passed")
    return not failed


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
