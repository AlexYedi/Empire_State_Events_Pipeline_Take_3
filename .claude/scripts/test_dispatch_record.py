#!/usr/bin/env python3
"""test_dispatch_record.py — offline regression for dispatch_record.py. Free, synthetic transcripts only.

Pins the stale-attribution bug: a `gap:` line written before dispatch N used to be credited to every later
dispatch until new assistant text appeared. Also pins model_source and the skill_load rows.

Usage: python3 .claude/scripts/test_dispatch_record.py [path/to/dispatch_record.py]
"""
import importlib.util, json, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("dr", sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "dispatch_record.py"))
dr = importlib.util.module_from_spec(spec); spec.loader.exec_module(dr)
ok = n = 0


def ck(name, cond):
    global ok, n; n += 1; ok += bool(cond); print(("  ✓ " if cond else "  ✗ ") + name)


def asst(*blocks, ts="2026-10-24T00:00:00Z"):
    return {"type": "assistant", "timestamp": ts, "message": {"content": list(blocks)}}


def text(t):
    return {"type": "text", "text": t}


def agent(tid, agent_type=None, model=None):
    inp = {"description": "d", "prompt": "p"}
    if agent_type:
        inp["subagent_type"] = agent_type
    if model:
        inp["model"] = model
    return {"type": "tool_use", "id": tid, "name": "Agent", "input": inp}


def result(tid, agent_id):
    return {"type": "user", "timestamp": "2026-10-24T00:00:01Z", "toolUseResult": {"agentId": agent_id, "status": "completed"},
            "message": {"content": [{"type": "tool_result", "tool_use_id": tid, "content": "done"}]}}


def skill(tid, name):
    return {"type": "tool_use", "id": tid, "name": "Skill", "input": {"skill": name, "args": "SECRET-ARGS"}}


tmp = tempfile.mkdtemp(prefix="dispatch-test-")
transcript = os.path.join(tmp, "sess.jsonl")
rows = [
    asst(text("gap: no fitting agent · interim general-purpose"), agent("t1")),  # turn 1: line, then dispatch
    result("t1", "a1"),
    asst(agent("t2")),                                                         # turn 2: no line (the bug)
    result("t2", "a2"),
    asst(text("Fan out.\ngap: no fitting agent · interim general-purpose"), agent("t3"), agent("t4")),  # one line, two calls
    result("t3", "a3"), result("t4", "a4"),
    asst(text("route: alex:research-analyst"), agent("t5", "alex:research-analyst", model="fable")),  # old prefix still parses
    result("t5", "a5"),
    asst(agent("t6", "company-researcher"), agent("t7", "alex:builder"), skill("s1", "post-event-content")),
]
with open(transcript, "w") as fh:
    fh.write("\n".join(json.dumps(r) for r in rows) + "\n")
os.makedirs(os.path.join(tmp, "sess", "subagents"))
with open(os.path.join(tmp, "sess", "subagents", "agent-a5.jsonl"), "w") as fh:
    fh.write(json.dumps(asst(skill("s2", "alex:systems-thinking"))) + "\n")

print("route/gap attribution")
recs = {r["tool_use_id"]: r for r in dr.build(transcript, "sess")}
ck("a gap: line before the call is credited to it", recs["t1"]["route_line"] and recs["t1"]["unexplained"] is False)
ck("a LATER dispatch with no line of its own is not credited (stale-attribution bug)", recs["t2"]["route_line"] is None)
ck("...and that general-purpose dispatch is flagged unexplained", recs["t2"]["unexplained"] is True)
ck("one line, two calls in the same turn: the first call consumes it", recs["t3"]["route_line"] and not recs["t3"]["unexplained"])
ck("...the second needs its own line", recs["t4"]["route_line"] is None and recs["t4"]["unexplained"] is True)
ck("the dropped route: prefix still parses (old transcripts)", (recs["t5"]["route_line"] or "").startswith("route:"))

print("model_requested / model_source")
models = {"company-researcher": "sonnet", "alex:builder": None, "alex:research-analyst": None}
recs = {r["tool_use_id"]: r for r in dr.build(transcript, "sess", models=models)}
ck("input.model on the call -> source call", (recs["t5"]["model_requested"], recs["t5"]["model_source"]) == ("fable", "call"))
ck("no call model, frontmatter model: -> frontmatter-default", (recs["t6"]["model_requested"], recs["t6"]["model_source"]) == ("sonnet", "frontmatter-default"))
ck("no call model, no frontmatter model -> default", (recs["t7"]["model_requested"], recs["t7"]["model_source"]) == (None, "default"))
ck("frontmatter parser reads name and model", dr.frontmatter(os.path.join(HERE, "..", "agents", "research", "company-researcher.md"))[0] == "company-researcher")

print("skill_load rows")
skills = dr.skill_loads(transcript, "sess", list(recs.values()))
by = {s["tool_use_id"]: s for s in skills}
ck("parent Skill call logged", by.get("s1", {}).get("where") == "parent" and by["s1"]["skill"] == "post-event-content")
ck("subagent Skill call logged with its agent", by.get("s2", {}).get("where") == "subagent" and by["s2"]["agent"] == "alex:research-analyst")
ck("skill args never recorded", "SECRET-ARGS" not in json.dumps(skills))

print(f"\n{ok}/{n} passed")
sys.exit(0 if ok == n else 1)
