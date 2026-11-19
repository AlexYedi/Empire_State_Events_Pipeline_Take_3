#!/usr/bin/env python3
"""test_run_state.py — offline regression for run_state.py (YED-372). No network; temp dirs only.

Pins: mark/show/resume-point, atomic write (no temp file left, old file survives a failed write), reason required
for skipped/failed, unknown step rejected, slug parity with event-claim.py, and the agent preflight's bare vs
prefixed case (the Agentics 11/4 failure: bare `content-correspondent` exists only as `alex:content-correspondent`).

Usage: python3 .claude/scripts/test_run_state.py [--selftest]
"""
import importlib.util
import json
import os
import sys
import tempfile
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
EVENT = "Fictional Spotlight: Agents & Harnesses"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fake_plugins(base):
    """A plugins dir with one plugin `alex` shipping agents/content-correspondent.md, registered like the real one."""
    inst = os.path.join(base, "cache", "mkt", "alex", "0.1.0")
    os.makedirs(os.path.join(inst, "agents"))
    open(os.path.join(inst, "agents", "content-correspondent.md"), "w").close()
    with open(os.path.join(base, "installed_plugins.json"), "w") as f:
        json.dump({"version": 2, "plugins": {"alex@mkt": [{"installPath": inst}]}}, f)
    return base


def run():
    rs = load("run_state", os.path.join(HERE, "run_state.py"))
    ec = load("event_claim", os.path.join(ROOT, ".claude", "hooks", "event-claim.py"))
    n = ok = 0

    def ck(name, cond):
        nonlocal n, ok
        n += 1
        ok += bool(cond)
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")

    with tempfile.TemporaryDirectory() as d:
        ck("slug matches event-claim.py", rs.slugify(EVENT) == ec.slugify(EVENT))
        ck("state path is <dir>/<slug>/run-state.json",
           rs.path_for(EVENT, d) == os.path.join(d, ec.slugify(EVENT), "run-state.json"))
        ck("fresh event: resume point is resolve", rs.resume_point(rs.load(EVENT, d)) == "resolve")
        ck("fresh event: show says no prior run", "no prior run" in rs.render(EVENT, rs.load(EVENT, d)))

        rs.mark(EVENT, "resolve", "done", state_dir=d)
        rs.mark(EVENT, "transcript", "done", duration_s=12.5, meta={"source": "supercut"}, state_dir=d)
        st = rs.load(EVENT, d)
        ck("mark persists status + meta + duration",
           st["steps"]["transcript"] == {**st["steps"]["transcript"], "status": "done", "duration_s": 12.5,
                                         "meta": {"source": "supercut"}})
        ck("history is append-only", [h["step"] for h in st["history"]] == ["resolve", "transcript"])
        ck("resume point advances to anchor", rs.resume_point(st) == "anchor")

        rs.mark(EVENT, "anchor", "skipped", reason="anchor unambiguous", state_dir=d)
        ck("skipped counts as finished", rs.resume_point(rs.load(EVENT, d)) == "condition")
        rs.mark(EVENT, "condition", "failed", reason="roster missing", state_dir=d)
        ck("failed does NOT advance the resume point", rs.resume_point(rs.load(EVENT, d)) == "condition")
        out = rs.render(EVENT, rs.load(EVENT, d))
        ck("show lists steps, last finished and resume point",
           "transcript" in out and "last finished: anchor" in out and "resume point: condition (Step 3.5)" in out)

        for s in rs.STEP_IDS:
            rs.mark(EVENT, s, "done", state_dir=d)
        ck("all steps finished: resume point is none", rs.resume_point(rs.load(EVENT, d)) == "none")

        for status in ("skipped", "failed"):
            try:
                rs.mark(EVENT, "claims", status, state_dir=d)
                ck(f"{status} without reason refused", False)
            except ValueError:
                ck(f"{status} without reason refused", True)
            try:
                rs.mark(EVENT, "claims", status, reason="   ", state_dir=d)
                ck(f"{status} with blank reason refused", False)
            except ValueError:
                ck(f"{status} with blank reason refused", True)
        try:
            rs.mark(EVENT, "graph", "done", state_dir=d)
            ck("unknown step refused", False)
        except ValueError as e:
            ck("unknown step refused (names the valid ids)", "graph-event" in str(e))
        ck("CLI: unknown step exits 2", rs.main(["mark", EVENT, "3.8b", "--status", "done"]) == 2)

        # atomic write: no temp left behind; a failed replace leaves the previous file intact
        sdir = os.path.dirname(rs.path_for(EVENT, d))
        ck("no temp file left after writes", [f for f in os.listdir(sdir) if f.endswith(".tmp")] == [])
        before = open(rs.path_for(EVENT, d)).read()
        with mock.patch.object(rs.os, "replace", side_effect=OSError("disk full")):
            try:
                rs.mark(EVENT, "hubspot", "skipped", reason="no contact cleared the bar", state_dir=d)
                ck("failed replace raises", False)
            except OSError:
                ck("failed replace raises", True)
        ck("failed replace leaves the old file intact", open(rs.path_for(EVENT, d)).read() == before)
        ck("failed replace cleans its temp file", [f for f in os.listdir(sdir) if f.endswith(".tmp")] == [])

    with tempfile.TemporaryDirectory() as nd:
        rs.mark("Fictional Night: Harnesses & Agent Identity", "resolve", "done", state_dir=nd)
        ck("near match flags the same event typed without 'and'",
           rs.near_matches("Fictional Night: Harnesses Agent Identity", nd) == ["fictional-night-harnesses-and-agent-identity"])
        ck("exact slug is not a near match", rs.near_matches("Fictional Night: Harnesses & Agent Identity", nd) == [])
        ck("a different event is not a near match", rs.near_matches("Fictional Demo Day: Voice Agents", nd) == [])

    ck("meta parses k=v (value may contain '=')", rs.parse_meta(["a=1", "b=x=y"]) == {"a": "1", "b": "x=y"})
    ck("canonical order covers 1 through 6.5", rs.STEP_IDS[0] == "resolve" and rs.STEP_IDS[-1] == "close-check"
       and len(rs.STEP_IDS) == 18 and rs.STEP_IDS.index("route") == rs.STEP_IDS.index("themes") + 1)

    with tempfile.TemporaryDirectory() as d:
        plugins = fake_plugins(os.path.join(d, "plugins"))
        agents = os.path.join(d, "agents", "ops")
        os.makedirs(agents)
        open(os.path.join(agents, "notion-writer.md"), "w").close()
        adirs = [os.path.join(d, "agents")]
        okb, msg = rs.preflight_agent("content-correspondent", plugins, adirs)
        ck("bare plugin-only agent FAILS", not okb)
        ck("bare plugin-only agent hints the prefix", "did you mean alex:content-correspondent?" in msg)
        ck("prefixed plugin agent resolves", rs.preflight_agent("alex:content-correspondent", plugins, adirs)[0])
        ck("project agent in a subfolder resolves", rs.preflight_agent("notion-writer", plugins, adirs)[0])
        okp, msg = rs.preflight_agent("alex:notion-writer", plugins, adirs)
        ck("project agent with a wrong prefix FAILS with a no-prefix hint", not okp and "no prefix" in msg)
        ck("built-in general-purpose resolves", rs.preflight_agent("general-purpose", plugins, adirs)[0])
        ck("unknown agent FAILS", not rs.preflight_agent("ghost-writer", plugins, adirs)[0])

    print(f"tests: {ok}/{n} pass")
    return 0 if ok == n else 1


if __name__ == "__main__":
    sys.exit(run())
