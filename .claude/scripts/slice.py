#!/usr/bin/env python3
"""slice.py — YED-304 Phase A slice renderer: read-only explorer over public.mi_slice (PR #268 design, §4).

Renders canonical market-lens slices from the `mi` semantic layer. Rendering ONLY: every read is a
GET to the `mi_slice(view, filters)` RPC (a security-definer reader; `mi` itself is not exposed to
PostgREST). slice.py writes nothing anywhere, holds no credentials in git, and points at the twin
by default — prod requires --allow-prod (the migration that creates mi_slice is 0016, not yet
applied at the time this script landed).

  slice.py run <name> [--since YYYY-MM-DD] [--lens LENS] [--json]
  slice.py adhoc --view mi.theme_week [--filters '{"lens":"attended"}'] [--sql-ref F] [run flags]
  slice.py list
  slice.py --selftest

The canonical slice registry lives in `.claude/references/slices.md` as fenced JSON descriptors
(reviewable, versioned); `adhoc --sql-ref F` reads one descriptor-shaped JSON file for one-offs.

Slice contract (PR #268 §3–§4) — what this renderer enforces on every payload, failing closed:
  lens      every row carries lens ∈ attended · research · market · job. "all" or a missing lens is
            a contract error: lenses are NEVER summed or blended (§3.3 rule 1) — they render as
            adjacent columns, each with its own denominator.
  theme     rows grouped by their dimension fields; counts on a theme's `(general)` topic are
            labelled (`… (2 general)`, rows marked `[general]`), never folded into named-topic
            counts (PR #267 rule).
  time      slices bucket on `asserted_at` (when it was true); `observed_at` (when we learned it)
            prints beside it wherever a row carries both (§3.1).
  floor     a cell the view flags `insufficient_data` (<3 facts / 8 weeks, §3.3 rule 3) renders as
            `insufficient_data`, and a lead/lag figure on a floored cell renders as
            `no information (floor)` — the number is suppressed, not shown "for context".
  segment   company rows carry stage/industry/headcount band as ordinary columns (Type 2 segment
            as-of the fact; the view supplies the as-of values).

RPC payload contract (pinned here for migration 0016 to implement):
  {"view": "mi.theme_week",
   "rows": [ {"theme": "...", "iso_week": "2026-W40", "lens": "attended",
              "facts": 12, "companies": 5, "sources": 3, "general_facts": 2,
              "floor_flag": "ok", "asserted_at": "...", "observed_at": "..."} ],
   "denominators": {"attended": "events in window: 12", "market": "facts from 6 sources; watchlist 12/40"}}
  denominators must have an entry for EVERY lens present in rows (§3.3 rule 2) — a rate without
  its denominator is a contract error, not a rendering nicety.

Target: TWIN by default (`ytfzzsxcxxbejnowmkmk`, per supabase/2B_REHEARSAL_RUNBOOK.md naming).
Credentials: `SLICE_API_KEY` env or `--key-file F` (twin service key; the repo `.env` holds the
PROD key and is deliberately NOT read — a prod key must never ride a twin-bound request).
Exit codes: 0 = rendered, 2 = bad args, 3 = env/network/contract failure (nothing rendered).
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
MEASURE_FIELDS = {"facts", "companies", "sources", "general_facts", "lead_weeks"}
REST_PREFIX = "/rest/v1"                   # PostgREST path prefix (read-only GET rpc below)


# ---------------------------------------------------------------- pure: registry (slices.md)

def load_registry(md_text: str) -> dict[str, dict]:
    """Fenced ```json blocks in slices.md → {name: descriptor}. A block holds one descriptor or a
    list of them. Descriptors missing name/view/lenses are skipped loudly via the returned errors."""
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

def rpc_request_parts(view: str, filters: dict) -> tuple[str, str]:
    """(path_with_query, body) for the mi_slice call. GET carries filters as a jsonb query param —
    a GET cannot carry a write body, which is the point: this client is structurally read-only.
    body is "" for GET; callers fall back to the same path with a POST body only on HTTP 405."""
    import urllib.parse
    qs = urllib.parse.urlencode({"view": view, "filters": json.dumps(filters, separators=(",", ":"))})
    return f"{REST_PREFIX}/rpc/mi_slice?{qs}", ""


def http_get(url: str, key: str, timeout: int = 30) -> tuple[int, str]:
    """One read-only HTTPS exchange. http.client (the same socket layer spine_client._send uses)
    with a GET verb — no POST body is ever built unless the server demands it (see fetch_slice)."""
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
    """mi_slice over REST → payload dict. GET first; a 405 (function not GET-enabled) retries once
    with a POST body — still read-only intent, still no guard bypass (the body is {view, filters})."""
    path, _ = rpc_request_parts(view, filters)
    url = f"https://{ref}.supabase.co{path}"
    status, txt = http_get(url, key)
    if status == 405:
        body = json.dumps({"view": view, "filters": filters})
        conn = http.client.HTTPSConnection(f"{ref}.supabase.co", 443, timeout=30)
        try:
            conn.request("POST", f"{REST_PREFIX}/rpc/mi_slice", body=body,
                         headers={"apikey": key, "Authorization": f"Bearer {key}",
                                  "Content-Type": "application/json", "Accept": "application/json"})
            resp = conn.getresponse()
            status, txt = resp.status, resp.read().decode()
        finally:
            conn.close()
    if status != 200:
        raise RuntimeError(f"mi_slice {view}: HTTP {status}: {txt[:300]}")
    try:
        return json.loads(txt)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"mi_slice {view}: response is not JSON: {e}: {txt[:200]}")


# ---------------------------------------------------------------- pure: contract validation

def validate_payload(payload) -> list[str]:
    """Slice-contract violations, or [] when the payload is renderable. Fail closed: an invalid
    payload renders nothing (a dishonest table is worse than no table — §3.3)."""
    errs: list[str] = []
    if not isinstance(payload, dict):
        return ["payload is not an object"]
    rows = payload.get("rows")
    if not isinstance(rows, list):
        return ["payload.rows is not a list"]
    denoms = payload.get("denominators")
    if not isinstance(denoms, dict) or not denoms:
        return ["payload.denominators missing or empty — every rate names its denominator (§3.3 rule 2)"]
    lenses_seen: set[str] = set()
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            errs.append(f"row {i}: not an object")
            continue
        lens = row.get("lens")
        if lens is None:
            errs.append(f"row {i}: missing lens — lenses are never implied or merged (§3.3 rule 1)")
        elif lens not in LENSES:
            errs.append(f"row {i}: lens {lens!r} not in {list(LENSES)} ('all' is forbidden — never blend)")
        else:
            lenses_seen.add(lens)
        flag = row.get("floor_flag")
        if flag is not None and flag not in ("ok", FLOOR_FLAG):
            errs.append(f"row {i}: unknown floor_flag {flag!r}")
    missing_den = sorted(lenses_seen - set(denoms))
    if missing_den:
        errs.append(f"denominators missing for lens(es) {missing_den} present in rows (§3.3 rule 2)")
    return errs


# ---------------------------------------------------------------- pure: rendering

def _fmt_cell(row: dict) -> str:
    """One lens's cell: measures, general-topic counts labelled, floor applied. A floored cell
    suppresses its numbers (including lead_weeks) — 'no information', never a naked ratio."""
    if row.get("floor_flag") == FLOOR_FLAG:
        return "insufficient_data" if "lead_weeks" not in row else "no information (floor)"
    parts = []
    facts = row.get("facts")
    if facts is not None:
        g = row.get("general_facts")
        parts.append(f"{facts} ({g} general)" if g else str(facts))
    for k in ("companies", "sources", "lead_weeks"):
        if row.get(k) is not None:
            parts.append(f"{k[:2]}={row[k]}" if k != "lead_weeks" else f"lead {row[k]}w")
    return " ".join(parts) if parts else "—"


def render(payload: dict, title: str, lens_filter: str | None = None) -> str:
    """Payload → text table: dimension columns, one column per lens (adjacent, never summed),
    denominator line per lens, notes for (general) rows and --lens exclusions."""
    rows = [dict(r) for r in payload["rows"]]
    excluded = 0
    if lens_filter:
        kept = [r for r in rows if r["lens"] == lens_filter]
        excluded = len(rows) - len(kept)
        rows = kept
    if not rows:
        return f"== {title} ==\n(no rows)\n"
    dim_keys: list[str] = []
    for r in rows:
        for k in r:
            if k not in ("lens", "floor_flag") and k not in MEASURE_FIELDS and k not in dim_keys:
                dim_keys.append(k)
    lenses = [l for l in LENSES if any(r["lens"] == l for r in rows)]
    groups: dict[tuple, dict[str, dict]] = {}
    for r in rows:
        key = tuple((k, r.get(k)) for k in dim_keys)
        groups.setdefault(key, {})[r["lens"]] = r

    def group_label(key: tuple) -> str:
        vals = dict(key)
        base = " ".join(str(v) for v in vals.values())
        if vals.get("topic") == GENERAL_TOPIC:
            base += " [general]"
        return base

    width = max([len(group_label(k)) for k in groups] + [len("dimension")])
    head = f"{'dimension':<{width}} | " + " | ".join(f"{l:>18}" for l in lenses)
    lines = [f"== {title} ==", head, "-" * len(head)]
    for key in sorted(groups, key=lambda k: [(v is None, str(v)) for _, v in k]):
        cells = [_fmt_cell(groups[key][l]) if l in groups[key] else "—" for l in lenses]
        lines.append(f"{group_label(key):<{width}} | " + " | ".join(f"{c:>18}" for c in cells))
    lines.append("-" * len(head))
    lines.append(f"dimensions: {' | '.join(dim_keys)}")
    lines.append("-" * len(head))
    for lens in lenses:
        if payload["denominators"].get(lens):
            lines.append(f"denominator {lens}: {payload['denominators'][lens]}")
    if any(dict(k).get("topic") == GENERAL_TOPIC for k in groups):
        lines.append(f"note: rows marked [general] count the theme's {GENERAL_TOPIC} topic — labelled, never merged into named topics")
    if lens_filter:
        lines.append(f"note: --lens {lens_filter}; {excluded} row(s) of other lenses excluded, not merged")
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

    # registry: the six canonical §4 slices parse from slices.md
    reg = load_registry(open(SLICES_MD, encoding="utf-8").read())
    canonical = {"attended_vs_market_by_theme_8w", "funded_not_attended_90d", "target_companies_heating_qtd",
                 "new_nyc_companies_by_quarter", "research_without_room_corroboration", "frontier_vs_room"}
    check("slices.md: all six canonical slices parse with name+view", canonical <= set(reg))
    check("slices.md: every descriptor names its expected lenses",
          all(isinstance(d.get("lenses"), list) and d["lenses"] for d in reg.values()))
    check("slices.md: descriptors never ask for a blended 'all' lens",
          all("all" not in d["lenses"] for d in reg.values()))

    # contract: every good fixture validates, every negative fixture fails for the right reason
    for name, payload in sorted(good.items()):
        check(f"contract: {name} validates", validate_payload(payload) == [])
    check("contract: missing denominators rejected",
          any("denominators" in e for e in validate_payload(bad["_invalid_missing_denominator"])))
    check("contract: blended lens 'all' rejected",
          any("never blend" in e for e in validate_payload(bad["_invalid_blended_lens"])))
    check("contract: missing lens on a row rejected",
          any("missing lens" in e for e in validate_payload(bad["_invalid_missing_lens"])))
    check("contract: denominator missing for a present lens rejected",
          any("§3.3 rule 2" in e for e in validate_payload(bad["_invalid_denominator_gap"])))
    check("contract: non-dict payload rejected", validate_payload([1, 2]) != [])

    # §4 slice-contract examples, rendered
    avm = render(good["attended_vs_market_by_theme_8w"], "attended_vs_market_by_theme_8w")
    check("render: lenses are adjacent columns", "attended" in avm and "market" in avm)
    check("render: no total column — lenses never summed", "total" not in avm.lower())
    check("render: denominators printed per lens",
          "denominator attended:" in avm and "denominator market:" in avm)
    check("render: general-topic count labelled with its own number", "(2 general)" in avm)
    check("render: floored cell reads insufficient_data, numbers suppressed", "insufficient_data" in avm)
    check("render: (general) topic row is marked, not folded in", "[general]" in avm)

    fv = render(good["frontier_vs_room"], "frontier_vs_room")
    check("lead/lag: lead shown when both lenses clear the floor", "lead 6w" in fv)
    check("lead/lag: floored lead suppressed as 'no information (floor)'", "no information (floor)" in fv)
    check("lead/lag: suppressed lead number absent from output",
          not any(ln.strip().endswith("lead 14w") for ln in fv.splitlines()))

    tl = render(good["target_companies_heating_qtd"], "target_companies_heating_qtd")
    check("time: asserted_at and observed_at both carried to the table",
          "asserted_at" in tl and "observed_at" in tl)
    check("segment: company segment columns render (stage as-of the fact)",
          "seed" in tl and "series_a" in tl)

    rc = render(good["research_without_room_corroboration"], "research_without_room_corroboration")
    check("research lens: renders alone, no attended column implied", "market" not in rc.split("==")[1])
    check("time: research slices bucket on asserted_at, observed_at printed beside",
          "asserted_at" in rc and "observed_at" in rc)

    # --lens filter: excludes, never merges
    avm_att = render(good["attended_vs_market_by_theme_8w"], "attended_vs_market_by_theme_8w",
                     lens_filter="attended")
    check("--lens: other-lens rows excluded with a count, not merged",
          "3 row(s) of other lenses excluded" in avm_att)
    check("--lens: remaining rows are only the requested lens",
          all(("| market" not in ln) for ln in avm_att.splitlines()[2:-1]))

    # request shaping: GET path, jsonb filters encoded, twin default, prod gate
    path, body = rpc_request_parts("mi.theme_week", {"lenses": ["attended", "market"], "window_weeks": 8})
    check("rpc: GET request path carries view + filters, empty body",
          path.startswith(REST_PREFIX + "/rpc/mi_slice?") and body == ""
          and "view=mi.theme_week" in path and "window_weeks" in path)
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
    ap.add_argument("--view", help="adhoc: mi view to slice (e.g. mi.theme_week)")
    ap.add_argument("--filters", help="adhoc: filters JSON for mi_slice (default {})")
    ap.add_argument("--sql-ref", help="adhoc: path to a descriptor JSON file ({name, view, filters, lenses})")
    ap.add_argument("--since", help="narrow the slice to facts asserted on/after YYYY-MM-DD")
    ap.add_argument("--lens", choices=LENSES, help="render only this lens (others excluded, never merged)")
    ap.add_argument("--url", help=f"override target REST base (default: twin {TWIN_REF}.supabase.co)")
    ap.add_argument("--key-file", help="path to a service key file (default: SLICE_API_KEY env)")
    ap.add_argument("--allow-prod", action="store_true",
                    help=f"permit targeting prod ({PROD_REF}) — only after migration 0016 is applied")
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
            print(f"{name_}  [{','.join(d['lenses'])}]  {d['view']}\n    {d.get('question', '')}")
        return 0

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
            view, filters = d["view"], d.get("filters", {})
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
        view, filters = d["view"], dict(d.get("filters", {}))
    else:
        ap.print_help()
        return 2

    if a.since:
        filters["since"] = a.since   # asserted_at floor — slices bucket on when it was true (§3.1)

    ref = TWIN_REF
    if a.url:
        if PROD_REF in a.url and not a.allow_prod:
            print(f"slice.py: refusing prod target without --allow-prod "
                  f"(mi_slice arrives with migration 0016; until then this stays on the twin)", file=sys.stderr)
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
    if errs:
        print("slice.py: slice-contract violation — rendering nothing (fail closed):", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 3

    if a.json:
        print(json.dumps(payload, indent=2))
        return 0
    sys.stdout.write(render(payload, a.name or view, lens_filter=a.lens))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
