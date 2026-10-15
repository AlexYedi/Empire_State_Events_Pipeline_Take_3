#!/usr/bin/env python3
"""Dispatch record (build_session contract v3, YED-259): one metadata row per subagent dispatch.

Called by the Stop hook (`.claude/hooks/build-session-emit.sh`). Rebuilds the session's whole
dispatch file from the transcript on every Stop, so reruns are idempotent and a background agent's
final status lands on a later Stop. Content-gated by construction: no prompt, tool input or result
bodies, only metadata and counts (the 3-5 word dispatch description is kept; it is parent-authored).

Usage: dispatch_record.py <transcript.jsonl> <session_id> <out_dir>
Contract: .claude/references/build-session-contract.md (v3).
"""
import json
import os
import re
import sys
import tempfile

CONTRACT_VERSION = "3"
WRITE_TOOL = re.compile(r"(create|update|delete|manage|save|send|write|publish|upload|move|share)", re.I)
TASK_ID = re.compile(r"<tool-use-id>([^<]+)</tool-use-id>")
TASK_STATUS = re.compile(r"<status>([^<]+)</status>")
ROUTE = re.compile(r"^\s*`?(route|gap):\s*[^\n]+", re.I | re.M)  # agent-routing.md §1: a line that starts with route:/gap:


def load(path):
    rows = []
    try:
        with open(path, errors="ignore") as fh:
            for line in fh:
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    pass
    except OSError:
        pass
    return rows


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content
                         if isinstance(b, dict) and b.get("type") == "text")
    return ""


def error_class(status, is_error, text):
    t = (text or "")[:4000].lower()
    if "concurrent subagent limit" in t:
        return "cap"
    if "spend" in t and "limit" in t or "usage limit" in t:
        return "spend"
    if status in ("killed", "timeout", "timed_out", "stalled"):
        return "stall"
    if ("agent type" in t or "subagent_type" in t) and "not found" in t:
        return "registry"
    if is_error or status in ("failed", "error"):
        return "other"
    return None


def sub_stats(path):
    rows = load(path)
    if not rows:
        return {}
    tools, stamps = [], []
    for r in rows:
        if r.get("timestamp"):
            stamps.append(r["timestamp"])
        content = (r.get("message") or {}).get("content")
        if isinstance(content, list):
            for b in content:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    tools.append(b.get("name", ""))
    return {
        "sub_turns": len(rows),
        "sub_tool_calls": len(tools),
        "sub_tool_names": sorted(set(tools)),
        "mcp_write_tool_names": sorted({t for t in tools if t.startswith("mcp__") and WRITE_TOOL.search(t.split("__")[-1])}),
        "sub_first_ts": stamps[0] if stamps else None,
        "sub_last_ts": stamps[-1] if stamps else None,
    }


def seconds_between(a, b):
    from datetime import datetime
    try:
        fa = datetime.fromisoformat(a.replace("Z", "+00:00"))
        fb = datetime.fromisoformat(b.replace("Z", "+00:00"))
        return round((fb - fa).total_seconds(), 1)
    except (AttributeError, ValueError):
        return None


def build(transcript, session_id):
    rows = load(transcript)
    subdir = os.path.join(transcript[:-len(".jsonl")] if transcript.endswith(".jsonl") else transcript, "subagents")
    by_id, order = {}, []
    last_text = ""  # most recent assistant text, for the routing file's `route:` / `gap:` line
    for r in rows:
        ts = r.get("timestamp")
        content = (r.get("message") or {}).get("content")
        if r.get("type") == "assistant" and isinstance(content, list):
            for b in content:
                if isinstance(b, dict) and b.get("type") == "text" and b.get("text", "").strip():
                    last_text = b["text"]
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") in ("Agent", "Task"):
                    inp = b.get("input") or {}
                    rec = {
                        "event": "subagent_dispatch", "contract_version": CONTRACT_VERSION,
                        "session_id": session_id, "tool_use_id": b.get("id"),
                        "dispatched_at": ts, "agent": inp.get("subagent_type") or "general-purpose",
                        "description": (inp.get("description") or "")[:80],
                        "model_requested": inp.get("model"), "model_resolved": None,
                        "background": inp.get("run_in_background"), "isolation": inp.get("isolation"),
                        "prompt_chars": len(inp.get("prompt") or ""),
                        "agent_id": None, "status": "dispatched", "is_error": False,
                        "error_class": None, "handback_chars": None, "ended_at": None,
                    }
                    m_route = ROUTE.search(last_text or "")
                    rec["route_line"] = m_route.group(0)[:120] if m_route else None
                    rec["unexplained"] = rec["agent"] == "general-purpose" and not (m_route and m_route.group(1).lower() == "gap")
                    by_id[b.get("id")] = rec
                    order.append(b.get("id"))
        if r.get("type") == "user":
            tur = r.get("toolUseResult") if isinstance(r.get("toolUseResult"), dict) else {}
            if isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id") in by_id:
                        rec = by_id[b["tool_use_id"]]
                        body = b.get("content")
                        body_text = body if isinstance(body, str) else text_of(body)
                        rec["agent_id"] = tur.get("agentId") or rec["agent_id"]
                        rec["model_resolved"] = tur.get("resolvedModel") or rec["model_resolved"]
                        rec["status"] = tur.get("status") or ("error" if b.get("is_error") else "completed")
                        rec["is_error"] = bool(b.get("is_error"))
                        rec["error_class"] = error_class(rec["status"], rec["is_error"], body_text)
                        if rec["status"] != "async_launched":
                            rec["handback_chars"] = len(body_text or "")
                            rec["ended_at"] = ts
        # background completions arrive as <task-notification> in user text, queued attachments
        # or queue operations, depending on harness version; read all three, first one wins
        note = ""
        if r.get("type") == "user":
            note = text_of(content)
        elif r.get("type") == "queue-operation" and r.get("operation") == "enqueue":
            note = r.get("content") if isinstance(r.get("content"), str) else ""
        elif r.get("type") == "attachment":
            note = (r.get("attachment") or {}).get("prompt") or ""
        if "<task-notification>" in note:
            m_id, m_st = TASK_ID.search(note), TASK_STATUS.search(note)
            if m_id and m_id.group(1) in by_id and by_id[m_id.group(1)]["status"] == "async_launched":
                rec = by_id[m_id.group(1)]
                st = m_st.group(1).strip() if m_st else "completed"
                rec["status"] = st
                rec["ended_at"] = ts
                rec["error_class"] = rec["error_class"] or error_class(st, st != "completed", note)
    out = []
    for seq, tid in enumerate(order, 1):
        rec = by_id[tid]
        rec["seq"] = seq
        # concurrency at dispatch: earlier dispatches still running when this one launched
        live = 0
        for other in order[:seq - 1]:
            o = by_id[other]
            if o["dispatched_at"] and rec["dispatched_at"] and o["dispatched_at"] <= rec["dispatched_at"] \
                    and (o["ended_at"] is None or o["ended_at"] > rec["dispatched_at"]):
                live += 1
        rec["concurrent_at_dispatch"] = live
        if rec["agent_id"]:
            stats = sub_stats(os.path.join(subdir, f"agent-{rec['agent_id']}.jsonl"))
            rec.update({k: v for k, v in stats.items() if not k.startswith("sub_") or k in ("sub_turns", "sub_tool_calls", "sub_tool_names")})
            if rec["ended_at"] is None and rec["status"] == "async_launched":
                rec["ended_at"] = stats.get("sub_last_ts")  # still running, or completion not yet seen
            if stats.get("sub_first_ts") and stats.get("sub_last_ts"):
                rec["duration_s"] = seconds_between(stats["sub_first_ts"], stats["sub_last_ts"])
        out.append(rec)
    return out


def main():
    if len(sys.argv) != 4:
        return 0
    transcript, session_id, out_dir = sys.argv[1:4]
    recs = build(transcript, session_id)
    if not recs:
        return 0
    os.makedirs(out_dir, exist_ok=True)
    shard = re.sub(r"[^A-Za-z0-9._-]", "_", session_id)
    target = os.path.join(out_dir, f"{shard}.jsonl")
    fd, tmp = tempfile.mkstemp(dir=out_dir, prefix=".tmp-")
    with os.fdopen(fd, "w") as fh:
        for r in recs:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    os.replace(tmp, target)  # whole-file rewrite = idempotent across Stops
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # telemetry must never break a turn
        sys.exit(0)
