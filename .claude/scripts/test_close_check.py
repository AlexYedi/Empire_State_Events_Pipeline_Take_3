#!/usr/bin/env python3
"""test_close_check.py — offline regression for close_check.py (YED-372). No network: the graph reader is a fake.

Pins: PASS on a complete run, FAIL on zero claims, PASS when claims were skipped with a reason, no Rooms check
(cut 2026-11-11, YED-374), unreachable graph → SKIPPED (never a crash), unthemed topics → FAIL unless covered by none_fits,
the close-check step written back into run-state, and exit 0 always without --strict.

Usage: python3 .claude/scripts/test_close_check.py [--selftest]
"""
import importlib.util
import json
import os
import sys
import tempfile
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
EVENT = "Fictional Builders Night: Harnesses & Identity"
NID = "0123456789abcdef0123456789abcdef"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class FakeReader:
    def __init__(self, event=True, claims=118, topics=None, boom=None):
        self.ev = {"id": "ev-1", "title": "Fictional Builders Night", "event_date": "2026-11-04T23:00:00Z"} if event else None
        self.n = claims
        self.tops = topics if topics is not None else [{"id": "t1", "name": "Agent identity", "cluster_id": "c1"}]
        self.boom = boom

    def source_key(self, nid):
        return "e4825821a997" + "0" * 52

    def event_row(self, nid):
        if self.boom:
            raise SystemExit(self.boom)
        return self.ev

    def claim_count(self, sk):
        return self.n

    def topics(self, eid):
        return self.tops


def complete(rs, sd, **over):
    for s in rs.STEP_IDS[:-1]:
        if s in over:
            continue
        meta = {"themes_prop": "set"} if s == "notion-write" else {"routing_rows": "5"} if s == "route" else None
        rs.mark(EVENT, s, "done", meta=meta, state_dir=sd)
    for s, (status, reason) in over.items():
        rs.mark(EVENT, s, status, reason=reason, state_dir=sd)


def run():
    rs = load("run_state", os.path.join(HERE, "run_state.py"))
    cc = load("close_check", os.path.join(HERE, "close_check.py"))
    n = ok = 0

    def ck(name, cond, out=None):
        nonlocal n, ok
        n += 1
        ok += bool(cond)
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")
        if not cond and out:
            print("        " + cc.render(out).replace("\n", "\n        "))

    def status(out, check):
        return next(r["status"] for r in out["results"] if r["check"] == check)

    with tempfile.TemporaryDirectory() as d:
        sd = os.path.join(d, "state")
        complete(rs, sd)
        out = cc.run(EVENT, NID, reader=FakeReader(), state_dir=sd)
        ck("complete run → CLOSE-CHECK: PASS", out["verdict"] == "CLOSE-CHECK: PASS", out)
        ck("Themes prop is SELF-REPORTED", status(out, "themes-prop") == "SELF-REPORTED", out)
        ck("routing rows SELF-REPORTED from the route step", status(out, "routing-rows") == "SELF-REPORTED", out)
        ck("no rooms check any more (YED-374)", all(r["check"] != "rooms" for r in out["results"]), out)
        cs = rs.load(EVENT, sd)["steps"]["close-check"]
        ck("close-check step written to run-state with result", cs["status"] == "done" and cs["meta"]["result"] == "PASS")
        ck("resume point is none after a passing close-check", rs.resume_point(rs.load(EVENT, sd)) == "none")

        out = cc.run(EVENT, NID, reader=FakeReader(claims=0), state_dir=sd)
        ck("zero claims → FAIL naming claims", status(out, "claims") == "FAIL"
           and out["verdict"] == "CLOSE-CHECK: FAIL (1) — claims", out)
        ck("FAIL recorded in run-state meta", rs.load(EVENT, sd)["steps"]["close-check"]["meta"]
           == {"result": "FAIL 1", "items": "claims"})

        out = cc.run(EVENT, NID, reader=FakeReader(event=False, claims=0), state_dir=sd)
        ck("missing graph event row → FAIL graph-event, themes SKIPPED",
           status(out, "graph-event") == "FAIL" and status(out, "themes") == "SKIPPED", out)

        tops = [{"id": "t1", "name": "Agent identity", "cluster_id": None},
                {"id": "t2", "name": "Harnesses", "cluster_id": "c1"}]
        out = cc.run(EVENT, NID, reader=FakeReader(topics=tops), state_dir=sd)
        ck("unthemed topic → FAIL themes naming it", status(out, "themes") == "FAIL"
           and "Agent identity" in out["results"][2]["detail"], out)
        rs.mark(EVENT, "themes", "done", meta={"none_fits": "1"}, state_dir=sd)
        out = cc.run(EVENT, NID, reader=FakeReader(topics=tops), state_dir=sd)
        ck("unthemed topic covered by none_fits → PASS", status(out, "themes") == "PASS", out)

    with tempfile.TemporaryDirectory() as d:
        sd = os.path.join(d, "state")
        complete(rs, sd, claims=("skipped", "walk-in, no transcript"))
        out = cc.run(EVENT, NID, reader=FakeReader(claims=0), state_dir=sd)
        ck("zero claims but claims skipped with reason → PASS", out["verdict"] == "CLOSE-CHECK: PASS"
           and status(out, "claims") == "SKIPPED", out)

        out = cc.run(EVENT, NID, reader=FakeReader(boom="GET /event -> 401"), state_dir=sd)
        ck("unreachable graph → graph checks SKIPPED, no crash",
           status(out, "graph-event") == "SKIPPED" and status(out, "themes") == "SKIPPED", out)

    with tempfile.TemporaryDirectory() as d:
        sd = os.path.join(d, "state")
        complete(rs, sd, route=("skipped", "walk-in: nothing routable"))
        out = cc.run(EVENT, NID, reader=FakeReader(), state_dir=sd)
        ck("route skipped with reason → routing-rows SKIPPED, run still PASS",
           status(out, "routing-rows") == "SKIPPED" and out["verdict"] == "CLOSE-CHECK: PASS", out)
        rs.mark(EVENT, "route", "done", state_dir=sd)
        out = cc.run(EVENT, NID, reader=FakeReader(), state_dir=sd)
        ck("route done without routing_rows → FAIL", status(out, "routing-rows") == "FAIL", out)

    with tempfile.TemporaryDirectory() as d:
        sd = os.path.join(d, "state")
        rs.mark(EVENT, "resolve", "done", state_dir=sd)
        rs.mark(EVENT, "notion-write", "done", state_dir=sd)
        out = cc.run(EVENT, NID, reader=FakeReader(), state_dir=sd)
        ck("partial run: run-state gaps listed", status(out, "run-state") == "FAIL"
           and "graph-event(missing)" in out["results"][-1]["detail"], out)
        ck("Themes prop not reported → FAIL", status(out, "themes-prop") == "FAIL", out)
        ck("verdict counts every FAIL", out["verdict"].startswith("CLOSE-CHECK: FAIL (2) — "), out)

        # exit codes through main(): 0 always, 1 only with --strict on FAIL
        with mock.patch.object(cc, "GraphReader", lambda: FakeReader(claims=0)), \
                mock.patch.object(rs, "STATE_DIR", sd), mock.patch("sys.stdout"):
            ck("main exits 0 on FAIL without --strict", cc.main([EVENT, "--notion-event-id", NID]) == 0)
            ck("main exits 1 on FAIL with --strict",
               cc.main([EVENT, "--notion-event-id", NID, "--strict"]) == 1)
            ck("--json exits 0", cc.main([EVENT, "--notion-event-id", NID, "--json"]) == 0)

    print(f"tests: {ok}/{n} pass")
    return 0 if ok == n else 1


if __name__ == "__main__":
    sys.exit(run())
