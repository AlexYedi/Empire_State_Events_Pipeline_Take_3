#!/usr/bin/env python3
"""test_route_brief.py — offline regression for route_brief.py (YED-387). Fictional fixtures only.

Pins: a valid block extracts and plans; no block → exit 3; strip removes the block and nothing else; contact
details, followups without a recap, unknown types, missing due_days, bad sources, >12 items, duplicate titles
and stray fields are refused; content-backlog items collapse into one Linear issue; due dates count from the
event date; labels keep one thread label; the Notion payload passes notion_payload.py; stories stay local.

Usage: python3 .claude/scripts/test_route_brief.py
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
EVENT = "Fictional Builders Night: Harnesses & Identity"


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def item(**kw):
    base = {"type": "open-loop", "title": "Verify the eval-harness claim", "source": "§17",
            "evidence": "Talk 1 · Speaker A · 23:31, said evals run nightly", "why": "Rule 12 before it goes public",
            "owner": "session"}
    base.update(kw)
    return base


def block(items, recap=True):
    rows = [{"routing_version": 1, "event": EVENT, "recap": recap}] + items
    return "⟦routing⟧\n" + "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n⟦/routing⟧\n"


BRIEF = "# Post-Event Brief — Fictional\n\n## 1. Quick Take\nA room.\n\n### Gaps\n- none\n\n"
GOOD = [
    item(),
    item(type="followup", title="Day 7 touch on the harness talk", person="Pat Example", owner="Alex", due_days=7,
         source="§17", evidence="Recap: spoke after the talk about harness design"),
    item(type="decision", title="Add Example Labs to the target list?", owner="Alex", due_days=9, source="§14"),
    item(type="upskill", title="Try rationalization tables on two of our skills", source="§7"),
    item(type="content-backlog", title="Series arc: verify then trust", source="§16", due_days=10),
    item(type="content-backlog", title="Factories vs swarms", source="§16"),
    item(type="build-idea", title="Skill trigger tester", source="§7", complexity="small_tool", owner="Alex"),
    item(type="story", title="In the room for the identity debate", source="§12", owner="Alex"),
]


def run():
    rb = load("route_brief")
    n = ok = 0

    def ck(name, cond, detail=""):
        nonlocal n, ok
        n += 1
        ok += bool(cond)
        print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"\n        {detail}" if not cond and detail else ""))

    def errs_for(items, recap=True):
        return rb.validate(block(items, recap).split("⟦routing⟧")[1].split("⟦/routing⟧")[0])[2]

    text = BRIEF + block(GOOD)
    header, items = rb.extract(text)
    ck("valid block extracts every item", len(items) == len(GOOD) and header["recap"] is True)
    stripped, b = rb.split(text)
    ck("strip removes the block and keeps the brief", "⟦routing⟧" not in stripped and "## 1. Quick Take" in stripped
       and stripped.endswith("- none\n"), repr(stripped[-40:]))
    try:
        rb.extract(BRIEF)
        ck("no block → LookupError", False)
    except LookupError:
        ck("no block → LookupError", True)
    try:
        rb.split(BRIEF + block(GOOD) + block(GOOD))
        ck("two blocks → RoutingError", False)
    except rb.RoutingError:
        ck("two blocks → RoutingError", True)

    e = errs_for([item(evidence="reach me at pat@example.com")])
    ck("email in a field → refused (ADR-9)", any("contact details" in x for x in e), e)
    e = errs_for([item(why="call +1 212 555 0100 tomorrow")])
    ck("phone number in a field → refused", True, e)
    e = errs_for([item(evidence="Talk 1 · 41:42–44:22 on 2026-11-04, 1,392 claims")])
    ck("timestamps, dates and counts are not mistaken for phones", e == [], e)
    e = errs_for([GOOD[1]], recap=False)
    ck("followup without recap → refused", any("without Alex's recap" in x for x in e), e)
    e = errs_for([item(type="memo")])
    ck("unknown type → refused", any("not one of" in x for x in e), e)
    e = errs_for([item(type="decision", owner="Alex")])
    ck("decision without due_days → refused", any("needs due_days" in x for x in e), e)
    e = errs_for([item(source="the talk")])
    ck("source must cite §N", any("source must cite" in x for x in e), e)
    e = errs_for([item(title=f"Loop {i}") for i in range(13)])
    ck(">12 items → refused", any("max 12" in x for x in e), e)
    e = errs_for([item(), item()])
    ck("duplicate titles → refused", any("duplicate titles" in x for x in e), e)
    e = errs_for([item(person="Pat Example")])
    ck("person on a non-followup → refused", any("only for followup" in x for x in e), e)
    e = errs_for([item(type="build-idea", complexity="huge")])
    ck("build-idea needs a valid complexity", any("needs complexity" in x for x in e), e)
    e = errs_for([item(owner="Alex", extra="x")])
    ck("unknown field → refused", any("unknown field" in x for x in e), e)
    e = errs_for([item(due_days=90)])
    ck("due_days out of range → refused", any("1-60" in x for x in e), e)

    pl = rb.plan(header, items, EVENT, "2026-11-04", "https://www.notion.so/abc0123456789abcdef0123456789abc")
    lin = pl["linear"]
    ck("content-backlog collapses into one Linear issue", sum(1 for x in lin if x["type"] == "content-backlog") == 1
       and len(lin) == 5, [x["title"] for x in lin])
    fu = next(x for x in lin if x["type"] == "followup")
    ck("followup due = event date + due_days, title names the person",
       fu["dueDate"] == "2026-11-11" and fu["title"].startswith("Follow-up: Pat Example"), fu)
    h2, i2 = rb.validate(block([item(type="followup", title="Send Pat Example a note", person="Pat Example",
                                     owner="Alex", due_days=7)]).split("⟦routing⟧")[1].split("⟦/routing⟧")[0])[:2]
    t2 = rb.plan(h2, i2, EVENT, "2026-11-04")["linear"][0]["title"]
    ck("followup title names the person once", t2 == "Follow-up: Send Pat Example a note", t2)
    dec = next(x for x in lin if x["type"] == "decision")
    ck("decision carries the decision label and one thread label",
       "decision" in dec["labels"] and sum(1 for l in dec["labels"] if "·" in l) == 1, dec["labels"])
    ck("session-owned items are unassigned, Alex-owned assigned to me",
       next(x for x in lin if x["type"] == "open-loop")["assignee"] is None and dec["assignee"] == "me")
    cb = next(x for x in lin if x["type"] == "content-backlog")
    ck("backlog issue lists both angles, due from the earliest due_days",
       "Series arc" in cb["description"] and "Factories vs swarms" in cb["description"] and cb["dueDate"] == "2026-11-14",
       cb)
    ck("every Linear description cites the brief section", all("brief §" in x["description"] or "(§" in x["description"]
                                                              for x in lin))
    ck("counts add up", pl["counts"] == {"items": 8, "linear": 5, "build_ideas": 1, "stories": 1}, pl["counts"])

    with tempfile.TemporaryDirectory() as d:
        brief = os.path.join(d, "brief.md")
        with open(brief, "w", encoding="utf-8") as f:
            f.write(text)
        cli = [sys.executable, os.path.join(HERE, "route_brief.py")]
        r = subprocess.run(cli + ["plan", brief, "--event", EVENT, "--event-date", "2026-11-04",
                                  "--notion-event-url", "https://www.notion.so/abc0123456789abcdef0123456789abc",
                                  "--state-dir", d], capture_output=True, text=True)
        slugdir = os.path.join(d, pl["slug"])
        ck("plan CLI exits 0 and writes plan, payload and stories",
           r.returncode == 0 and all(os.path.exists(os.path.join(slugdir, f))
                                     for f in ("routing-plan.json", "routing-notion-payload.json", "stories.md")),
           r.stdout + r.stderr)
        pay = os.path.join(slugdir, "routing-notion-payload.json")
        v = subprocess.run([sys.executable, os.path.join(HERE, "notion_payload.py"), pay], capture_output=True, text=True)
        ck("Notion payload passes notion_payload.py", v.returncode == 0, v.stdout + v.stderr)
        props = json.load(open(pay, encoding="utf-8"))["operations"][0]["properties"]
        ck("build idea links the event via the live relation name 'Event' (Project Ideas has no 'Events')",
           "Event" in props and "Events" not in props, sorted(props))
        r = subprocess.run(cli + ["strip", brief],
                           capture_output=True, text=True)
        ck("strip CLI prints the brief without the block", r.returncode == 0 and "⟦routing⟧" not in r.stdout)
        nob = os.path.join(d, "nob.md")
        with open(nob, "w", encoding="utf-8") as f:
            f.write(BRIEF)
        r = subprocess.run(cli + ["extract", nob], capture_output=True, text=True)
        ck("extract CLI exits 3 with no block", r.returncode == 3, r.stderr)
        bad = os.path.join(d, "bad.md")
        with open(bad, "w", encoding="utf-8") as f:
            f.write(BRIEF + block([item(type="memo")]))
        r = subprocess.run(cli + ["extract", bad], capture_output=True, text=True)
        ck("extract CLI exits 2 on an invalid block", r.returncode == 2 and "INVALID" in r.stderr, r.stderr)

    print(f"tests: {ok}/{n} pass")
    return 0 if ok == n else 1


if __name__ == "__main__":
    sys.exit(run())
