#!/usr/bin/env python3
"""slice.py — rendering-only slice explorer over public.mi_slice (YED-304, ADR-13).

Reads ONLY through the one door: GET public.mi_slice(view, filters) over Supabase REST.
No writes, no DDL, no direct table reads. What it adds on top of the RPC is contract
validation (fail closed) and honest rendering (§3.3 of the market-lens design):

  lenses    attended · research · market render as adjacent columns, never summed; a
            `--lens` filter excludes other lenses with a count, it never merges them.
  general   (general)-topic counts are labelled (`N (M general)` / explicit rows), never
            merged into named-topic counts (PR #267 rule).
  floors    a cell the view graded `insufficient_data` (<3 facts in the window) prints
            `insufficient_data` — the number is suppressed, not shown "for context".
  lead/lag  lives in its own view (mi.theme_lead_lag). `market_lead_weeks` renders only
            when `lead_lag_shown` is true (both lenses clear the 3-fact floor). When it
            is false — the correct null state, e.g. a market lens with 0 facts in the
            window — the lead prints `insufficient_data` while the underlying 8-week
            counts stay visible: rendered, not hidden, not special-cased away.
  segment   mi.company_cohort carries the CURRENT segment (open row): stage/industry/
            headcount_band/hq_metro. NO target tier anywhere — the private target list
            leaves the DB only as the aggregate watchlist counts in the market
            denominators (0016, ADR-13 F1).

Public.mi_slice contract (migration 0016 `mi_semantic_layer` — the live source of truth):

  views    allowlist: mi.theme_week · mi.theme_lead_lag · mi.company_timeline ·
           mi.company_cohort. Anything else raises server-side (mi.hiring_around_theme
           is deferred to lane 1's PR).
  filters  {weeks 1..104 (default 8) · lens attended|research|market · theme_id uuid ·
           company_id uuid · limit 1..5000 (default 1000)}. Unknown keys raise — the
           client pre-flights the same allowlist and fails closed before the call.
  returns  {"view": "mi.theme_week",                       # echoes the request
            "rows": [...],                                 # per-view columns (below)
            "denominators": {"attended": {"events": 12}, "research": {"briefs": 3},
                             "market": {"facts_by_source": {"gh": 40}, "watchlist_covered": 9,
                                        "watchlist_size": 40}, "job": {"boards_scanned": 5}},
            "window": {"from_week": "2026-W37", "to_week": "2026-W44", "anchored_on": "2026-11-04"}}
  window   `weeks` ISO weeks ending in the week of current_date — anchored on today,
           never on the latest row. It filters the week-grained views and scopes every
           denominator. theme_lead_lag carries its own fixed 8-week window;
           company_cohort is all-time.

Row shapes (0016 view definitions):
  mi.theme_week        theme_id, theme, iso_week, lens, facts, distinct_companies,
                       distinct_sources, general_facts, floor_flag, theme_resolved
  mi.theme_lead_lag    theme_id, theme, market_first_seen, attended_first_seen,
                       market_lead_weeks, attended_count_8w, market_count_8w, lead_lag_shown
  mi.company_timeline  company_id, company_name, lens, iso_week, facts, kinds, signal_types,
                       distinct_sources, first_asserted_at, last_asserted_at
  mi.company_cohort    company_id, company_name, first_seen_any, first_seen_quarter,
                       first_seen_{attended,research,market}_quarter, stage, industry,
                       headcount_band, hq_metro   (NO target_tier — ADR-13 F1)

Target: TWIN by default (`ytfzzsxcxxbejnowmkmk`, per supabase/2B_REHEARSAL_RUNBOOK.md naming).
Credentials: `SLICE_API_KEY` env or `--key-file F` (twin service key). A prod target is
refused without --allow-prod. The repo `.env` holds the PROD key and is deliberately NOT
read — a prod key must never ride a twin-bound request.
"""
from __future__ import annotations

import argparse
import http.client
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SLICES_MD = os.path.join(ROOT, ".claude", "references", "slices.md")
FIXTURES = os.path.join(ROOT, "supabase", "fixtures", "mi_slice_fixtures.json")

TWIN_REF = "ytfzzsxcxxbejnowmkmk"          # Phantom Test Case DB — the safe default target
PROD_REF = "oicikjyzmxqfomrrqkvf"          # The-Prod-Brain — refused without --allow-prod
LENSES = ("attended", "research", "market", "job")
GENERAL_TOPIC = "(general)"                # the per-theme catch-all topic (PR #267)
FLOOR_FLAG = "insufficient_data"           # <3 facts in the window (§3.3 rule 3, same floor as 0012)
REST_PREFIX = "/rest/v1"                   # PostgREST path prefix (read-only GET rpc below)

# The live 0016 contract, pinned client-side (the server raises on the same rules).
ALLOWLISTED_VIEWS = ("mi.theme_week", "mi.theme_lead_lag", "mi.company_timeline", "mi.company_cohort")
ALLOWED_FILTER_KEYS = ("weeks", "lens", "theme_id", "company_id", "limit")
MI_LENS_VALUES = ("attended", "research", "market")   # mi_slice's lens filter takes no 'job'
CANONICAL_DENOM_KEYS = ("attended", "research", "market", "job")  # 0016 always returns all four
LENSLESS_VIEWS = ("mi.theme_lead_lag", "mi.company_cohort")       # rows carry no lens column
FLOOR_VIEWS = ("mi.theme_week",)                       # views that grade rows with floor_flag
WINDOW_KEYS = ("from_week", "to_week", "anchored_on")

MEASURE_FIELDS = {"facts", "distinct_companies", "distinct_sources", "general_facts",
                  "attended_count_8w", "market_count_8w"}
ID_FIELDS = ("theme_id", "company_id")     # join keys, not facts — carried but not displayed
MARKER_FIELDS = ("theme_resolved",)        # labels, not dimension columns


# ---------------------------------------------------------------- pure: registry (slices.md)

def load_registry(md_text: str) -> dict[str, dict]:
    """Fenced ```json blocks in slices.md → {name: descriptor}. A block holds one descriptor or a
    list of them. Descriptors missing name/view are skipped loudly via the returned errors."""
    out: dict[str, dict] = {}
    for block in re.findall(r"```json\n(.*?)```", md_text, re.S):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        for d in data if isinstance(data, list) else [data]:
            if isinstance(d, dict) and d.get("name") and d.get("view"):
                out[d["name"]] = d
    return out


# ---------------------------------------------------------------- pure: request shaping

def filters_error(filters: dict) -> str:
    """Client-side pre-flight of mi_slice filters — the same allowlist 0016 enforces
    server-side. Failing closed here means a bad filter never leaves the machine."""
    if not isinstance(filters, dict):
        return "filters must be a JSON object"
    bad = sorted(k for k in filters if k not in ALLOWED_FILTER_KEYS)
    if bad:
        return f"unknown filter key(s) {bad}; allowed: {list(ALLOWED_FILTER_KEYS)} (0016)"
    if "lens" in filters and filters["lens"] not in MI_LENS_VALUES:
        return f"lens must be one of {list(MI_LENS_VALUES)} (got {filters['lens']!r})"
    for k, hi in (("weeks", 104), ("limit", 5000)):
        v = filters.get(k)
        if k in filters and (not isinstance(v, int) or isinstance(v, bool) or not 1 <= v <= hi):
            return f"{k} must be an int in 1..{hi} (got {v!r})"
    return ""


def rpc_request_parts(view: str, filters: dict) -> tuple[str, str]:
    """(path_with_query, body) for the mi_slice call. GET carries filters as a jsonb query param —
    a GET cannot carry a write body, which is the point: mi_slice is STABLE and GET-callable
    (0016), so no request body is ever built. body is always \"\"."""
    import urllib.parse
    qs = urllib.parse.urlencode({"view": view, "filters": json.dumps(filters, separators=(",", ":"))})
    return f"{REST_PREFIX}/rpc/mi_slice?{qs}", ""


def http_get(url: str, key: str, timeout: int = 30) -> tuple[int, str]:
    """One read-only HTTPS exchange. http.client (the same socket layer spine_client._send uses)
    with a GET verb — no request body is ever built."""
    host = re.sub(r"^https?://", "", url).split("/")[0]
    path = "/" + url.split("/", 3)[3] if url.count("/") > 2 else "/"
    conn = http.client.HTTPSConnection(host, 443, timeout=timeout)
    try:
        conn.request("GET", path, headers={"apikey": key, "Authorization": f"Bearer {key}",
                                           "Accept": "application/json"})
        resp = conn.getresponse()
        return resp.status, resp.read().decode()
    finally:
        conn.close()


def fetch_slice(ref: str, view: str, filters: dict, key: str) -> dict:
    """mi_slice over REST → payload dict. GET only; any non-200 is an error, never a retry
    with a request body. Refuses a response whose view does not match the request — another
    slice's rows must never render."""
    if view not in ALLOWLISTED_VIEWS:
        raise RuntimeError(f"mi_slice: view {view!r} is not in the allowlist {list(ALLOWLISTED_VIEWS)} (ADR-13)")
    fe = filters_error(filters)
    if fe:
        raise RuntimeError(f"mi_slice: {fe}")
    path, _ = rpc_request_parts(view, filters)
    url = f"https://{ref}.supabase.co{path}"
    status, txt = http_get(url, key)
    if status != 200:
        raise RuntimeError(f"mi_slice {view}: HTTP {status}: {txt[:300]} "
                           f"(mi_slice is GET-callable per 0016 — check the migration is applied)")
    try:
        payload = json.loads(txt)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"mi_slice {view}: response is not JSON: {e}: {txt[:200]}")
    if not isinstance(payload, dict) or payload.get("view") != view:
        raise RuntimeError(f"mi_slice {view}: response view {payload.get('view') if isinstance(payload, dict) else payload!r} "
                           f"does not match the requested view — refusing to render another slice's rows")
    return payload


# ---------------------------------------------------------------- pure: contract validation

def validate_payload(payload) -> list[str]:
    """Slice-contract violations, or [] when the payload is renderable. Fail closed: an invalid
    payload renders nothing (a dishonest table is worse than no table — §3.3)."""
    errs: list[str] = []
    if not isinstance(payload, dict):
        return ["payload is not an object"]
    view = payload.get("view")
    if not isinstance(view, str) or not view.startswith("mi."):
        errs.append(f"payload.view {view!r} is not a qualified view name ('mi.…') — the contract echoes the requested view")
    elif view not in ALLOWLISTED_VIEWS:
        errs.append(f"payload.view {view!r} is not in the mi_slice allowlist {list(ALLOWLISTED_VIEWS)} (ADR-13)")
    window = payload.get("window")
    if not isinstance(window, dict) or any(k not in window for k in WINDOW_KEYS):
        errs.append("payload.window must carry from_week, to_week, anchored_on — the anchored window is the slice's time scope (0016)")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        return ["payload.rows is not a list"]
    denoms = payload.get("denominators")
    if not isinstance(denoms, dict):
        return ["payload.denominators missing — every rate names its denominator (§3.3 rule 2)"]
    missing_den = [k for k in CANONICAL_DENOM_KEYS if k not in denoms]
    if missing_den:
        errs.append(f"denominators missing canonical lens key(s) {missing_den} — 0016 returns all four (§3.3 rule 2)")
    lensed = view in FLOOR_VIEWS or view == "mi.company_timeline"
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            errs.append(f"row {i}: not an object")
            continue
        if lensed:
            lens = row.get("lens")
            if lens is None:
                errs.append(f"row {i}: missing lens — lenses are never implied or merged (§3.3 rule 1)")
            elif lens not in LENSES:
                errs.append(f"row {i}: lens {lens!r} not in {list(LENSES)} ('all' is forbidden — never blend)")
        if view in FLOOR_VIEWS:
            flag = row.get("floor_flag")
            if flag is None:
                errs.append(f"row {i}: missing floor_flag — fail closed; the view must grade every row (§3.3 rule 3)")
            elif flag not in ("ok", FLOOR_FLAG):
                errs.append(f"row {i}: unknown floor_flag {flag!r}")
        if "market_lead_weeks" in row or view == "mi.theme_lead_lag":
            gate = row.get("lead_lag_shown")
            if not isinstance(gate, bool):
                errs.append(f"row {i}: theme_lead_lag row without boolean lead_lag_shown — the lead renders only when both lenses clear the floor")
            elif gate and row.get("market_lead_weeks") is None:
                errs.append(f"row {i}: lead_lag_shown true but market_lead_weeks missing")
    return errs


LENS_LESS_VIEWS = {"mi.theme_lead_lag", "mi.company_cohort"}


def descriptor_lens_error(payload: dict, descriptor: dict) -> str:
    """Named-slice guard, view-aware. A lensed view called without a lens filter legitimately
    returns EVERY lens that has rows (live: {attended, research}) — the renderer filters
    client-side to the slice's lens set and excludes the rest, so extra lenses are NOT an
    error here. What stays fail-closed: invalid lens values on a lensed view, and any lens on
    a lens-less view (mi.theme_lead_lag, mi.company_cohort)."""
    view = payload.get("view")
    rows = [r for r in payload.get("rows", []) if isinstance(r, dict)]
    got = sorted({r.get("lens") for r in rows} - {None})
    if view in LENS_LESS_VIEWS:
        if got:
            return (f"lens-less view {view!r} returned lensed rows {got} — the payload is not "
                    f"the slice the registry describes")
        return ""
    bad = sorted(set(got) - set(LENSES))
    if bad:
        return (f"rows carry invalid lens values {bad} (lensed views render {sorted(LENSES)}) — "
                f"the payload is not the slice the registry describes")
    return ""


# ---------------------------------------------------------------- pure: rendering

def _fmt_cell(row: dict) -> str:
    """One lens's cell: measures, general-topic counts labelled, floor applied. A floored cell
    suppresses its numbers — 'insufficient_data', never a naked ratio."""
    if row.get("floor_flag") == FLOOR_FLAG:
        return FLOOR_FLAG
    parts = []
    facts = row.get("facts")
    if facts is not None:
        g = row.get("general_facts")
        parts.append(f"{facts} ({g} general)" if g else str(facts))
    for k, label in (("distinct_companies", "co="), ("distinct_sources", "src=")):
        if row.get(k) is not None:
            parts.append(f"{label}{row[k]}")
    return " ".join(parts) if parts else "—"


def _fmt_den(lens: str, den) -> str:
    """One lens's denominator, printed as named key=value pairs — a rate never prints alone."""
    if not isinstance(den, dict):
        return f"denominator {lens}: {den}"
    return "denominator {}: {}".format(lens, "; ".join(
        f"{k}={json.dumps(v, sort_keys=True) if isinstance(v, dict) else v}" for k, v in den.items()))


def _window_line(payload: dict) -> str:
    w = payload.get("window") or {}
    return "window: {} → {} (anchored on {})".format(w.get("from_week"), w.get("to_week"), w.get("anchored_on"))


def _render_lead_lag(payload: dict, title: str) -> str:
    """mi.theme_lead_lag: one row per theme. The lead prints ONLY on lead_lag_shown=true;
    when false the cell reads insufficient_data and the 8-week counts stay in their own
    columns — the null state is rendered, not hidden (0016: the view still returns
    market_lead_weeks, consumers must not render it)."""
    rows = [r for r in payload["rows"] if isinstance(r, dict)]
    head = f"{'theme':<40} | {'attended 8w':>12} | {'market 8w':>10} | {'market lead':>28}"
    lines = [f"== {title} ==", head, "-" * len(head)]
    for r in sorted(rows, key=lambda r: str(r.get("theme"))):
        a, m = r.get("attended_count_8w"), r.get("market_count_8w")
        if r.get("lead_lag_shown") is True and r.get("market_lead_weeks") is not None:
            lead = f"market led by {r['market_lead_weeks']}w"
        else:
            lead = f"{FLOOR_FLAG} (a={a}, m={m})"  # the correct null state — visible, not hidden
        lines.append(f"{str(r.get('theme')):<40} | {str(a):>12} | {str(m):>10} | {lead:>28}")
    lines.append("-" * len(head))
    lines.append(_window_line(payload))
    lines.append("note: lead renders only when BOTH lenses clear the 3-fact floor (lead_lag_shown); "
                 "otherwise insufficient_data with the counts beside it — never a naked ratio")
    return "\n".join(lines) + "\n"


def _render_cohort(payload: dict, title: str) -> str:
    """mi.company_cohort: all-time rows, no lens, no floor — first-seen quarters plus the
    CURRENT segment (open row). No target tier column exists (ADR-13 F1)."""
    rows = [r for r in payload["rows"] if isinstance(r, dict)]
    cols = [k for k in rows[0] if k not in ID_FIELDS] if rows else []
    lines = [f"== {title} ==", " | ".join(cols), "-" * 80]
    for r in sorted(rows, key=lambda r: str(r.get("first_seen_any")), reverse=True):
        lines.append(" | ".join(str(r.get(c)) if r.get(c) is not None else "—" for c in cols))
    lines.append("-" * 80)
    lines.append(_window_line(payload))
    lines.append("note: all-time cohort; segments are the CURRENT open segment row, not as-of the fact")
    return "\n".join(lines) + "\n"


def render(payload: dict, title: str, lens_filter: str | None = None,
           lens_columns: list[str] | None = None, limit: int | None = None) -> str:
    """Payload → text table. Lensed views: dimension columns, one column per lens (adjacent,
    never summed), denominator line per lens. Columns come from the SLICE's lenses, not the
    lenses present — an empty lens still renders, as 'no information (0 facts in window)' with
    its denominator: that null state is the baseline, hiding it is the failure. Lens-less views
    dispatch to their own renderers."""
    view = payload.get("view")
    if view == "mi.theme_lead_lag":
        return _render_lead_lag(payload, title)
    if view == "mi.company_cohort":
        return _render_cohort(payload, title)

    rows = [dict(r) for r in payload["rows"]]
    total = len(rows)
    excluded = 0
    if lens_columns:  # named slice: rows of lenses the slice didn't ask for are excluded, not merged
        kept = [r for r in rows if r.get("lens") in lens_columns]
        excluded += len(rows) - len(kept)
        rows = kept
    if lens_filter:
        kept = [r for r in rows if r["lens"] == lens_filter]
        excluded += len(rows) - len(kept)
        rows = kept
    lenses = lens_columns or [l for l in LENSES if any(r["lens"] == l for r in rows)]
    if not rows and not lenses:
        return f"== {title} ==\n(no rows)\n"
    dim_keys: list[str] = []
    for r in rows:
        for k in r:
            if k not in ("lens", "floor_flag", *MARKER_FIELDS, *ID_FIELDS) and k not in MEASURE_FIELDS and k not in dim_keys:
                dim_keys.append(k)

    def _hashable(v):
        return tuple(v) if isinstance(v, list) else v  # timeline kinds/signal_types are arrays

    groups: dict[tuple, dict[str, dict]] = {}
    for r in rows:
        key = tuple((k, _hashable(r.get(k))) for k in dim_keys)
        groups.setdefault(key, {})[r["lens"]] = r

    def group_label(key: tuple, group: dict | None = None) -> str:
        vals = dict(key)
        base = " ".join(str(v) for v in vals.values())
        rows_iter = group.values() if group else ()
        if any(r.get("topic") == GENERAL_TOPIC or r.get("theme") == GENERAL_TOPIC for r in rows_iter):
            base += " [general]"
        if any(r.get("theme_resolved") == "seed" for r in rows_iter):
            base += " [seed]"  # theme_resolved marker — a label, never a dimension column
        return base

    width = max([len(group_label(k, groups[k])) for k in groups] + [len("dimension")])
    head = f"{'dimension':<{width}} | " + " | ".join(f"{l:>18}" for l in lenses)
    lines = [f"== {title} ==", head, "-" * len(head)]
    for key in sorted(groups, key=lambda k: [(v is None, str(v)) for _, v in k]):
        cells = [_fmt_cell(groups[key][l]) if l in groups[key]
                 else "no information (0 facts in window)" for l in lenses]
        lines.append(f"{group_label(key, groups[key]):<{width}} | " + " | ".join(f"{c:>18}" for c in cells))
    lines.append("-" * len(head))
    lines.append(f"dimensions: {' | '.join(dim_keys)}")
    lines.append(_window_line(payload))
    lines.append("-" * len(head))
    for lens in lenses:  # every requested lens prints its denominator — even a 0-row lens
        if payload["denominators"].get(lens):
            lines.append(_fmt_den(lens, payload["denominators"][lens]))
    if any(dict(k).get("topic") == GENERAL_TOPIC or dict(k).get("theme") == GENERAL_TOPIC for k in groups):
        lines.append(f"note: rows marked [general] count the theme's {GENERAL_TOPIC} topic — labelled, never merged into named topics")
    if excluded:
        basis = f"--lens {lens_filter}" if lens_filter else "the slice's lens set"
        lines.append(f"note: {excluded} row(s) outside {basis} excluded, not merged")
    if limit is not None and total == limit and total:
        lines.append(f"note: response returned exactly {limit} row(s) (the limit filter) — it may be truncated; raise the limit to confirm")
    lines.append("note: lenses are adjacent counts, never summed or blended — one number per lens, no combined column (§3.3 rule 1)")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- selftest (offline, fixtures only)

def selftest() -> int:
    ok, n = 0, 0

    def check(name, cond):
        nonlocal ok, n
        n += 1; ok += bool(cond)
        print(f"  {'✓' if cond else '✗'} {name}")

    try:
        fixtures = json.load(open(FIXTURES, encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"slice.py selftest: cannot load fixtures {FIXTURES}: {e}", file=sys.stderr)
        return 1
    good = {k: v for k, v in fixtures.items() if not k.startswith("_")}
    bad = {k: v for k, v in fixtures.items() if k.startswith("_")}

    # registry: the canonical §4 slices parse from slices.md
    reg = load_registry(open(SLICES_MD, encoding="utf-8").read())
    canonical = {"attended_vs_market_by_theme_8w", "funded_not_attended_90d", "target_companies_heating_qtd",
                 "companies_heating_8w", "new_nyc_companies_by_quarter", "research_without_room_corroboration",
                 "frontier_vs_room", "theme_lead_lag_8w"}
    check("slices.md: all canonical slices parse with name+view", canonical <= set(reg))
    check("slices.md: every descriptor's view is in the 0016 allowlist",
          all(d["view"] in ALLOWLISTED_VIEWS for d in reg.values()))
    check("slices.md: every descriptor's filters pass the client pre-flight",
          all(filters_error(d.get("filters", {})) == "" for d in reg.values()))
    check("slices.md: descriptors never ask for a blended 'all' lens",
          all("all" not in (d.get("lenses") or []) for d in reg.values()))
    check("slices.md: lensed descriptors name lenses; the lens-less one names none",
          all((d.get("lenses") or []) == [] for n_, d in reg.items() if n_ == "theme_lead_lag_8w")
          and all(d.get("lenses") for n_, d in reg.items() if n_ != "theme_lead_lag_8w"))
    check("slices.md: exactly three runnable descriptors; the rest blocked_on_rpc (original questions kept)",
          {n_ for n_, d in reg.items() if d.get("status") != "blocked_on_rpc"}
          == {"attended_vs_market_by_theme_8w", "companies_heating_8w", "theme_lead_lag_8w"})
    check("slices.md: runnable descriptors carry no target_tier (ADR-13 F1) — blocked ones name it only in blocked_filters",
          all("target_tier" not in json.dumps(d.get("filters", {})) for d in reg.values())
          and "target_tier" not in json.dumps(good))

    # contract: every good fixture validates, every negative fixture fails for the right reason
    for name, payload in sorted(good.items()):
        check(f"contract: {name} validates", validate_payload(payload) == [])
    check("contract: missing denominators rejected",
          any("denominators" in e for e in validate_payload(bad["_invalid_missing_denominator"])))
    check("contract: denominators missing a canonical lens key rejected",
          any("canonical" in e for e in validate_payload(bad["_invalid_denominator_gap"])))
    check("contract: blended lens 'all' rejected",
          any("never blend" in e for e in validate_payload(bad["_invalid_blended_lens"])))
    check("contract: missing lens on a lensed row rejected",
          any("missing lens" in e for e in validate_payload(bad["_invalid_missing_lens"])))
    check("contract: non-dict payload rejected", validate_payload([1, 2]) != [])
    check("contract: payload without window rejected",
          any("window" in e for e in validate_payload(bad["_invalid_missing_window"])))
    check("contract: unqualified view name rejected",
          any("qualified view" in e for e in validate_payload(bad["_invalid_unqualified_view"])))
    check("contract: view outside the allowlist rejected",
          any("allowlist" in e for e in validate_payload(bad["_invalid_unknown_view"])))
    check("contract: missing floor_flag rejected (fail closed)",
          any("missing floor_flag" in e for e in validate_payload(bad["_invalid_missing_floor_flag"])))
    check("contract: lead row without boolean lead_lag_shown rejected",
          any("lead_lag_shown" in e for e in validate_payload(bad["_invalid_lead_without_gate"])))
    check("descriptor: frontier_vs_room names market+attended (papers are market events; research = claims)",
          sorted(reg["frontier_vs_room"]["lenses"]) == ["attended", "market"])
    check("descriptor: every canonical fixture's lens set is a subset of its descriptor's",
          all(descriptor_lens_error(good[name], reg[name]) == "" for name in good if name in reg))
    check("descriptor: live lens distribution accepted — extra research rows are a subset, not a mismatch",
          descriptor_lens_error(good["attended_vs_market_by_theme_8w"],
                                reg["attended_vs_market_by_theme_8w"]) == "")
    fp = json.loads(json.dumps(good["frontier_vs_room"]))
    fp["rows"][0]["lens"] = "all"  # invalid lens value: not a slice the registry can describe
    check("descriptor: invalid lens value rejected (fail closed)",
          descriptor_lens_error(fp, reg["frontier_vs_room"]) != "")
    fl = json.loads(json.dumps(good["theme_lead_lag_8w"]))
    fl["rows"][0]["lens"] = "market"  # a lens on a lens-less view: not the slice the registry describes
    check("descriptor: lensed rows on a lens-less view rejected (fail closed)",
          descriptor_lens_error(fl, reg["theme_lead_lag_8w"]) != "")
    check("run: blocked_on_rpc slice refuses before any fetch (needs an RPC extension)",
          main(["run", "funded_not_attended_90d"]) == 2)

    # §4 slice-contract examples, rendered — columns from the SLICE's lenses, so the empty
    # market lens still renders its column and denominator (live: 0 market facts in 8 weeks)
    avm = render(good["attended_vs_market_by_theme_8w"], "attended_vs_market_by_theme_8w",
                 lens_columns=reg["attended_vs_market_by_theme_8w"]["lenses"])
    check("render: lenses are adjacent columns", "attended" in avm and "market" in avm)
    check("render: empty lens renders its column as the null state, not hidden",
          "no information (0 facts in window)" in avm)
    check("render: denominators printed for every requested lens — including the empty one",
          "denominator attended:" in avm and "denominator market:" in avm)
    check("render: rows of lenses the slice didn't ask for are excluded with a count, not merged",
          "2 row(s) outside the slice's lens set excluded" in avm)
    check("render: general-topic count labelled with its own number", "(2 general)" in avm)
    check("render: floored cell reads insufficient_data, numbers suppressed", "insufficient_data" in avm)
    check("render: (general) topic row is marked, not folded in", "[general]" in avm)
    check("render: theme_resolved seed marker printed, not a column", "[seed]" in avm)
    check("render: anchored window printed (live-verified W38–W45)",
          "window: 2026-W38 → 2026-W45 (anchored on 2026-11-04)" in avm)
    check("render: id columns are join keys, not displayed", "theme_id" not in avm.split("dimensions")[0])
    check("render: response hitting the limit filter is flagged as possibly truncated",
          "may be truncated" in render(good["attended_vs_market_by_theme_8w"],
                                       "attended_vs_market_by_theme_8w",
                                       lens_columns=["attended", "market"], limit=7))

    # lead/lag: its own view; the false gate is the correct null state (live: false everywhere —
    # 0 market facts) and is rendered, not hidden
    ll = render(good["theme_lead_lag_8w"], "theme_lead_lag_8w")
    check("lead/lag: false gate renders insufficient_data WITH the counts beside it (nothing hidden)",
          "insufficient_data (a=9, m=0)" in ll and "insufficient_data (a=4, m=0)" in ll)
    check("lead/lag: gated lead number absent everywhere when the gate is false",
          not any("market led by" in ln for ln in ll.splitlines()))
    check("lead/lag: 8-week counts always visible", "market 8w" in ll)
    check("lead/lag: lead shown when both lenses clear the floor (gate-true fixture)",
          "market led by 6.0w" in render(fixtures["_lead_lag_gate_true"], "lead gate true"))

    ht = render(good["companies_heating_8w"], "companies_heating_8w")
    check("time: asserted and observed times both carried to the table",
          "first_asserted_at" in ht and "last_asserted_at" in ht)

    cc = render(good["new_nyc_companies_by_quarter"], "new_nyc_companies_by_quarter")
    check("cohort: lens-less render — no lens column implied", "lens" not in cc.split("==")[1])
    check("segment: current segment columns render (open row, not as-of)",
          "seed" in cc and "series_a" in cc)
    check("cohort: no target tier anywhere (ADR-13 F1)",
          "target_tier" not in cc and "target_tier" not in json.dumps(good))

    rc = render(good["research_without_room_corroboration"], "research_without_room_corroboration")
    check("research lens: renders alone, no attended column implied", "market" not in rc.split("==")[1])

    # --lens filter: excludes, never merges (on top of the slice's own lens set)
    avm_att = render(good["attended_vs_market_by_theme_8w"], "attended_vs_market_by_theme_8w",
                     lens_filter="attended", lens_columns=["attended", "market"])
    check("--lens: other-lens rows excluded with a count, not merged",
          "2 row(s) outside --lens attended excluded" in avm_att)
    check("--lens: remaining rows are only the requested lens",
          all(("| market" not in ln) for ln in avm_att.splitlines()[2:-1]))

    # filters: the client pre-flights the same allowlist 0016 enforces server-side
    check("filters: unknown key rejected client-side", "unknown filter" in filters_error({"kinds": ["funding"]}))
    check("filters: bad lens value rejected client-side", filters_error({"lens": "all"}) != "")
    check("filters: out-of-range weeks rejected client-side", filters_error({"weeks": 0}) != "")
    check("filters: live filter keys accepted", filters_error({"weeks": 8, "lens": "market", "limit": 100}) == "")

    # request shaping: GET path, jsonb filters encoded, twin default, prod gate
    import urllib.parse
    path, body = rpc_request_parts("mi.theme_week", {"weeks": 8, "lens": "attended"})
    check("rpc: GET request path carries view + filters, empty body",
          path.startswith(f"{REST_PREFIX}/rpc/mi_slice?") and "view=mi.theme_week" in path
          and json.loads(urllib.parse.parse_qs(path.split("?")[1])["filters"][0]) == {"weeks": 8, "lens": "attended"}
          and body == "")
    check("rpc: no request-body path exists — mi_slice is GET-callable (0016 contract)",
          not re.search(r'conn\.request\(\s*"POST"', open(__file__, encoding="utf-8").read()))
    check("rpc: prod ref refused without --allow-prod (enforced in main, pinned here)",
          PROD_REF != TWIN_REF and PROD_REF == "oicikjyzmxqfomrrqkvf")

    # fixtures hygiene: no PII anywhere (AGENTS.md rule 4 — *.example domains only)
    blob = json.dumps(fixtures)
    check("fixtures: no email addresses", not re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}", blob))
    check("fixtures: no phone numbers", not re.search(r"\+?\d{3}[-. ]\d{3}[-. ]\d{4}", blob))

    print(f"selftest: {ok}/{n} slice.py cases pass")
    return 0 if ok == n else 1


# ---------------------------------------------------------------- main

def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", nargs="?", choices=["run", "adhoc", "list"], help="run a named slice / one-off / list registry")
    ap.add_argument("name", nargs="?", help="canonical slice name (see `slice.py list`)")
    ap.add_argument("--view", help="adhoc: mi view to slice (must be in the 0016 allowlist)")
    ap.add_argument("--filters", help="adhoc: filters JSON for mi_slice (default {})")
    ap.add_argument("--sql-ref", help="adhoc: path to a descriptor JSON file ({name, view, filters, lenses})")
    ap.add_argument("--lens", choices=LENSES, help="render only this lens (server-side filter + client exclusion, never merged)")
    ap.add_argument("--url", help=f"override target REST base (default: twin {TWIN_REF}.supabase.co)")
    ap.add_argument("--key-file", help="path to a service key file (default: SLICE_API_KEY env)")
    ap.add_argument("--allow-prod", action="store_true",
                    help=f"permit targeting prod ({PROD_REF}) — read-only mi_slice GETs only")
    ap.add_argument("--json", action="store_true", help="print the validated payload instead of the table")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()

    if a.cmd == "list":
        try:
            reg = load_registry(open(SLICES_MD, encoding="utf-8").read())
        except OSError as e:
            print(f"slice.py: cannot read {SLICES_MD}: {e}", file=sys.stderr)
            return 3
        for name_, d in sorted(reg.items()):
            lenses = ",".join(d.get("lenses") or ["(lens-less)"])
            status = "blocked_on_rpc — needs an RPC extension" if d.get("status") == "blocked_on_rpc" else "runnable"
            print(f"{name_}  [{lenses}]  {d['view']}  <{status}>\n    {d.get('question', '')}")
        return 0

    d = None
    if a.cmd == "adhoc":
        if not a.view and not a.sql_ref:
            print("slice.py adhoc: pass --view V (and optional --filters JSON) or --sql-ref F", file=sys.stderr)
            return 2
        if a.sql_ref:
            try:
                d = json.load(open(a.sql_ref, encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as e:
                print(f"slice.py: cannot read --sql-ref {a.sql_ref}: {e}", file=sys.stderr)
                return 3
            view, filters = d["view"], dict(d.get("filters", {}))
        else:
            view, filters = a.view, json.loads(a.filters) if a.filters else {}
    elif a.cmd == "run":
        if not a.name:
            print("slice.py run: pass a slice name (`slice.py list`)", file=sys.stderr)
            return 2
        try:
            reg = load_registry(open(SLICES_MD, encoding="utf-8").read())
        except OSError as e:
            print(f"slice.py: cannot read {SLICES_MD}: {e}", file=sys.stderr)
            return 3
        d = reg.get(a.name)
        if not d:
            print(f"slice.py: unknown slice {a.name!r} — see `slice.py list`", file=sys.stderr)
            return 2
        if d.get("status") == "blocked_on_rpc":
            print(f"slice.py: refusing {a.name!r} — it is blocked_on_rpc: its filters need an RPC "
                  f"extension the mi_slice signature does not express yet "
                  f"(see .claude/references/slices.md; a target_tier filter also needs an ADR-13 "
                  f"privacy review). It stays listed so the intent is versioned.", file=sys.stderr)
            return 2
        view, filters = d["view"], dict(d.get("filters", {}))
    else:
        ap.print_help()
        return 2

    if a.lens and view != "mi.theme_lead_lag" and view != "mi.company_cohort":
        filters["lens"] = a.lens  # server-side single-lens filter; the renderer also excludes
    fe = filters_error(filters)
    if fe:
        print(f"slice.py: {fe}", file=sys.stderr)
        return 2

    ref = TWIN_REF
    if a.url:
        if PROD_REF in a.url and not a.allow_prod:
            print(f"slice.py: refusing prod target without --allow-prod "
                  f"(mi_slice GETs are read-only; still, prod is opt-in)", file=sys.stderr)
            return 3
        m = re.search(r"https://([a-z0-9]{20})\.supabase\.co", a.url)
        if not m:
            print(f"slice.py: --url must be a Supabase REST base (https://<ref>.supabase.co)", file=sys.stderr)
            return 2
        ref = m.group(1)

    key = os.environ.get("SLICE_API_KEY", "")
    if a.key_file:
        try:
            key = open(a.key_file, encoding="utf-8").read().strip()
        except OSError as e:
            print(f"slice.py: cannot read --key-file {a.key_file}: {e}", file=sys.stderr)
            return 3
    if not key:
        print("slice.py: no key — set SLICE_API_KEY (twin service key) or pass --key-file. "
              "The repo .env holds the PROD key and is deliberately not read here.", file=sys.stderr)
        return 3

    try:
        payload = fetch_slice(ref, view, filters, key)
    except (RuntimeError, OSError) as e:
        print(f"slice.py: {e}", file=sys.stderr)
        return 3

    errs = validate_payload(payload)
    if not errs and a.cmd == "run" and d:
        dl = descriptor_lens_error(payload, d)
        if dl:
            errs = [dl]
    if errs:
        print("slice.py: slice-contract violation — rendering nothing (fail closed):", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 3

    if a.json:
        print(json.dumps(payload, indent=2))
        return 0
    sys.stdout.write(render(payload, a.name or view, lens_filter=a.lens,
                            lens_columns=(d.get("lenses") or None) if d else None,
                            limit=filters.get("limit")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
