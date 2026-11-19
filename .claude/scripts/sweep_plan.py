#!/usr/bin/env python3
"""sweep_plan.py — the theme sweep's plan step (YED-384), split out of theme-sweep.sh for YED-443.

Reads seeds.json from sweep_seed.py and writes one <slug>.input.json per theme for the top N groups, in seed
order (velocity, then event, then gap, then room). Prints one TSV row per group for the shell loop:
    slug \t theme_id-or-"null" \t window.from \t window.to \t theme

Unthemed seeds are part of the sweep_seed contract: an event folder that matches no theme, and every
room_entity row, carry theme = theme_id = null. Each one becomes its own group, labelled from its query
(the event title or company name before the first ':'), with theme_id null, which sweep_manifest.py accepts.
Before YED-443 the plan step called theme.lower() on them and the whole sweep died (2026-11-18, exit 6).

Usage: python3 .claude/scripts/sweep_plan.py <out_dir> <n_themes> <cap>
"""
import json
import re
import sys


def _clean(s: str) -> str:
    """One line, no tabs: the label goes into a TSV row read by `while IFS=$'\\t' read`."""
    return re.sub(r"\s+", " ", s).strip()


def label(row: dict) -> str:
    """The group name for a seed row: its theme, else the query's subject (text before the first ':')."""
    if row.get("theme"):
        return _clean(str(row["theme"]))
    subject = _clean(str(row.get("query") or "").split(":", 1)[0])
    return subject[:120] or _clean(str(row.get("seed_ref") or "")) [:120] or "unthemed"


def plan(seeds: list[dict], n: int, cap: int) -> list[tuple[str, dict]]:
    """Pure. seeds -> [(slug, input_dict)] for the first n groups in seed order. Themed rows group by
    theme_id (else theme name); each unthemed row is its own group. Slugs are unique."""
    groups: dict[tuple, list[dict]] = {}
    for i, r in enumerate(seeds):
        if r.get("theme_id"):
            key = ("id", r["theme_id"])
        elif r.get("theme"):
            key = ("name", r["theme"])
        else:
            key = ("row", i)
        groups.setdefault(key, []).append(r)
    out, used = [], set()
    for rows in list(groups.values())[:n]:
        theme = label(rows[0])
        base = re.sub(r"[^a-z0-9]+", "-", theme.lower()).strip("-")[:60] or "theme"
        slug, k = base, 2
        while slug in used:
            slug, k = f"{base}-{k}", k + 1
        used.add(slug)
        inp = {"theme": theme, "theme_id": rows[0].get("theme_id"), "query_id": None, "window": rows[0]["window"],
               "seed_queries": [{k: r[k] for k in ("kind", "query", "seed_ref")} for r in rows],
               "known_entities": [], "cap": cap}
        out.append((slug, inp))
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    out_dir, n, cap = argv[1], int(argv[2]), int(argv[3])
    with open(f"{out_dir}/seeds.json", encoding="utf-8") as f:
        seeds = json.load(f)
    for slug, inp in plan(seeds, n, cap):
        with open(f"{out_dir}/{slug}.input.json", "w", encoding="utf-8") as f:
            json.dump(inp, f, indent=1)
        w = inp["window"]
        print("\t".join([slug, inp["theme_id"] or "null", w["from"], w["to"], inp["theme"]]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
