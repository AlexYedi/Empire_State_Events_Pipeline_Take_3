#!/usr/bin/env python3
"""test_sweep_plan.py — offline regression for sweep_plan.py (YED-443). No network; temp dirs only.

Pins the 2026-11-18 failure: an event-folder seed with theme = theme_id = null (MONEY TALKS 3, no matching
theme) crashed the plan step with AttributeError on theme.lower(). Also: seed-order grouping, one group per
unthemed row, unique slugs, TSV-safe labels, and that every input file round-trips through the CLI.

Usage: python3 .claude/scripts/test_sweep_plan.py [--selftest]
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("sweep_plan", os.path.join(HERE, "sweep_plan.py"))
sp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sp)

W7 = {"from": "2026-11-11", "to": "2026-11-18"}
T1, T2 = "9f4dce3c-3f31-48cf-a7fe-01eb2a033e43", "00000000-0000-4000-8000-000000000002"


def row(theme, tid, kind, query, ref, w=W7):
    return {"theme": theme, "theme_id": tid, "kind": kind, "query": query, "seed_ref": ref, "window": w}


# Shape of the real 11-18 seeds.json: velocity, themed event, UNTHEMED event, gaps, room_entity.
SEEDS = [
    row("AI Engineering Practice", T1, "velocity", "AI Engineering Practice: what happened", "mi.theme_week:x"),
    row("MCP & Agent-Ready APIs", T2, "event", "Some Meetup (2026-11-20): MCP in the last 7 days", "triage:a"),
    row(None, None, "event", "MONEY TALKS 3 AI x Finance Hackathon (2026-11-21): the topic, the host",
        "event_folder:11 21 26 MONEY TALKS 3 AI x Finance Hackathon"),
    row("AI Engineering Practice", T1, "gap", "AI Engineering Practice: gap query", "gap:x"),
    row(None, None, "room_entity", "Fixtureco: funding, launches", "event:e1/company:c1"),
    row(None, None, "room_entity", "Fixtureco: funding, launches", "event:e2/company:c1"),
]

fails = 0


def check(name, ok):
    global fails
    print(("PASS " if ok else "FAIL ") + name)
    fails += 0 if ok else 1


p = sp.plan(SEEDS, 3, 15)
check("11-18 regression: null-theme event seed does not crash and gets slot 3",
      [s for s, _ in p] == ["ai-engineering-practice", "mcp-agent-ready-apis", "money-talks-3-ai-x-finance-hackathon-2026-11-21"])
check("unthemed group: theme = event title, theme_id stays null",
      p[2][1]["theme"] == "MONEY TALKS 3 AI x Finance Hackathon (2026-11-21)" and p[2][1]["theme_id"] is None)
check("themed rows group across kinds (velocity + gap share one input)",
      [q["kind"] for q in p[0][1]["seed_queries"]] == ["velocity", "gap"])
check("input carries cap, window and the exact seed_queries keys",
      p[0][1]["cap"] == 15 and p[0][1]["window"] == W7
      and all(set(q) == {"kind", "query", "seed_ref"} for _, i in p for q in i["seed_queries"]))

allp = sp.plan(SEEDS, 99, 15)
check("each unthemed row is its own group (2 room_entity rows -> 2 groups)", len(allp) == 5)
check("slugs are unique when labels collide", len({s for s, _ in allp}) == len(allp) and allp[-1][0] == "fixtureco-2")

check("label is TSV-safe (tabs/newlines collapsed)",
      sp.label(row(None, None, "event", "A\tB\nC: x", "r")) == "A B C")
check("label falls back to seed_ref, then 'unthemed'",
      sp.label(row(None, None, "event", "", "event_folder:x")) == "event_folder:x"
      and sp.label(row(None, None, "event", "", "")) == "unthemed")
check("all-unthemed seeds plan without error", len(sp.plan([SEEDS[2], SEEDS[4]], 3, 15)) == 2)
check("empty seeds -> empty plan", sp.plan([], 3, 15) == [])

with tempfile.TemporaryDirectory() as d:
    json.dump(SEEDS, open(os.path.join(d, "seeds.json"), "w"))
    r = subprocess.run([sys.executable, os.path.join(HERE, "sweep_plan.py"), d, "3", "15"],
                       capture_output=True, text=True)
    lines = r.stdout.splitlines()
    cols = [ln.split("\t") for ln in lines]
    check("CLI exits 0 and prints 3 five-column TSV rows", r.returncode == 0 and len(cols) == 3
          and all(len(c) == 5 for c in cols))
    check("CLI prints 'null' for an unthemed theme_id", cols[2][1] == "null" if len(cols) == 3 else False)
    check("CLI writes one input file per row, each valid JSON",
          all(json.load(open(os.path.join(d, f"{c[0]}.input.json")))["theme"] == c[4] for c in cols))

print(f"\n{'OK' if not fails else 'FAILED'}: {fails} failure(s)")
sys.exit(1 if fails else 0)
