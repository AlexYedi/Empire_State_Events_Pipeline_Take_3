#!/usr/bin/env python3
"""run_state.py: per-event step ledger for /post-event-content (YED-372). Detection, never prevention.

THE FAILURE THIS COUNTS. Agentics 11/4: a session held the claim for 3h, stalled, and left no record of which
steps had finished; a second session saw "held" and nothing else. Separately, unenforced steps (3.8b/c/d, the
`Themes` property, the Rooms entry) were skipped and the run still "closed green". This file is the record a
second session resumes from, and the input `close_check.py` (Step 6.5) counts gaps against.
Spec: docs/proposals/2026-11-05-post-event-robustness-and-value.md (rows "Stalled session", "Silent drift").

State: .claude/.state/post-event/<slug>/run-state.json (gitignored). The slug is event-claim.py's `slugify`, so
the claim and the run-state for one event always agree. Writes are atomic (temp file + os.replace).

Usage:
  run_state.py mark <event> <step> --status done|skipped|failed [--reason T] [--duration-s N] [--meta k=v ...]
  run_state.py show <event>              # table + resume point
  run_state.py resume-point <event>      # next step id to run (`resolve` for a fresh event, `none` when complete)
  run_state.py preflight-agent <name>    # exit 0 if the Agent type resolves, 1 with a fix hint otherwise
Nothing here blocks a turn: `mark` refuses only malformed input (unknown step, skipped/failed without reason).
"""
from __future__ import annotations
import argparse, datetime, glob, importlib.util, json, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
STATE_DIR = os.environ.get("RUN_STATE_DIR") or os.path.join(ROOT, ".claude", ".state", "post-event")
PLUGINS_DIR = os.path.expanduser("~/.claude/plugins")
PROJECT_AGENTS = os.path.join(ROOT, ".claude", "agents")
USER_AGENTS = os.path.expanduser("~/.claude/agents")
BUILTIN_AGENTS = {"general-purpose", "Explore", "Plan", "statusline-setup"}

# Canonical order: (step id, command step number). Unknown ids are rejected so a typo can't hide a gap.
STEPS = [
    ("resolve", "1"), ("transcript", "2"), ("anchor", "3"), ("condition", "3.5"), ("enrich", "3.6"),
    ("synthesize", "3.7"), ("notion-kg", "3.8a"), ("graph-event", "3.8b"), ("claims", "3.8c"),
    ("themes", "3.8d"), ("steer", "3.9"), ("draft", "4"), ("output-check", "4.5"), ("notion-write", "5"),
    ("hubspot", "5.5"), ("deep-dives", "5.6"), ("close-check", "6.5"),
]
STEP_IDS = [s for s, _ in STEPS]
STEP_NUM = dict(STEPS)
STATUSES = ("done", "skipped", "failed")
FINISHED = ("done", "skipped")


def _load_slugify():
    p = os.path.join(ROOT, ".claude", "hooks", "event-claim.py")
    spec = importlib.util.spec_from_file_location("event_claim", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.slugify


slugify = _load_slugify()


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def path_for(event: str, state_dir: str | None = None) -> str:
    return os.path.join(state_dir or STATE_DIR, slugify(event), "run-state.json")


def load(event: str, state_dir: str | None = None) -> dict | None:
    try:
        with open(path_for(event, state_dir), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def save(event: str, state: dict, state_dir: str | None = None) -> str:
    """Atomic: write a sibling temp file, fsync, then os.replace. A crash mid-write leaves the old file intact."""
    p = path_for(event, state_dir)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".run-state.", suffix=".tmp", dir=os.path.dirname(p))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=1)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, p)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return p


def parse_meta(pairs: list[str] | None) -> dict:
    out = {}
    for kv in pairs or []:
        if "=" not in kv:
            raise ValueError(f"--meta expects k=v, got {kv!r}")
        k, v = kv.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def mark(event: str, step: str, status: str, reason: str | None = None, duration_s: float | None = None,
         meta: dict | None = None, state_dir: str | None = None) -> dict:
    if step not in STEP_NUM:
        raise ValueError(f"unknown step {step!r}; valid: {', '.join(STEP_IDS)}")
    if status not in STATUSES:
        raise ValueError(f"unknown status {status!r}; valid: {', '.join(STATUSES)}")
    if status in ("skipped", "failed") and not (reason or "").strip():
        raise ValueError(f"--status {status} requires --reason (a silent skip is the failure this file counts)")
    st = load(event, state_dir) or {"event": event, "slug": slugify(event), "created_at": now(), "steps": {},
                                    "history": []}
    entry = {"status": status, "at": now()}
    if reason:
        entry["reason"] = reason.strip()
    if duration_s is not None:
        entry["duration_s"] = duration_s
    if meta:
        entry["meta"] = meta
    st["steps"][step] = entry
    st.setdefault("history", []).append({"step": step, **entry})
    st["updated_at"] = entry["at"]
    save(event, st, state_dir)
    return st


def resume_point(state: dict | None) -> str:
    """First canonical step neither done nor skipped. Fresh event -> `resolve`; everything finished -> `none`."""
    steps = (state or {}).get("steps", {})
    for s in STEP_IDS:
        if steps.get(s, {}).get("status") not in FINISHED:
            return s
    return "none"


def last_finished(state: dict | None) -> str | None:
    hist = [h for h in (state or {}).get("history", []) if h.get("status") in FINISHED]
    return hist[-1]["step"] if hist else None


def render(event: str, state: dict | None) -> str:
    if not state:
        return f"run-state: no prior run for '{slugify(event)}' — start at Step 1 (resolve)."
    lines = [f"run-state: {state.get('event')} ({state.get('slug')}) · updated {state.get('updated_at', '?')}",
             f"  {'step':<13} {'#':<5} {'status':<8} {'at':<21} note"]
    for s, n in STEPS:
        e = state.get("steps", {}).get(s)
        if not e:
            lines.append(f"  {s:<13} {n:<5} {'-':<8}")
            continue
        note = e.get("reason", "")
        if e.get("meta"):
            note = (note + " " if note else "") + " ".join(f"{k}={v}" for k, v in e["meta"].items())
        if e.get("duration_s") is not None:
            note = (note + " " if note else "") + f"({e['duration_s']}s)"
        lines.append(f"  {s:<13} {n:<5} {e['status']:<8} {e.get('at', ''):<21} {note}".rstrip())
    rp = resume_point(state)
    lf = last_finished(state)
    lines.append(f"last finished: {lf or '-'}" + (f" (Step {STEP_NUM[lf]})" if lf else ""))
    lines.append(f"resume point: {rp}" + (f" (Step {STEP_NUM[rp]})" if rp != "none" else " — every step finished"))
    return "\n".join(lines)


# --- agent preflight -------------------------------------------------------------------------------------------

def _plugin_roots(plugin: str | None, plugins_dir: str) -> list[str]:
    """Install paths for `plugin` (or every plugin when None), from installed_plugins.json plus a cache glob."""
    roots: list[str] = []
    try:
        with open(os.path.join(plugins_dir, "installed_plugins.json"), encoding="utf-8") as f:
            data = json.load(f).get("plugins", {})
        for key, installs in data.items():
            if plugin is None or key.split("@", 1)[0] == plugin:
                roots += [i.get("installPath") for i in installs if i.get("installPath")]
    except (OSError, ValueError, AttributeError):
        pass
    pat = os.path.join(plugins_dir, "cache", "*", plugin or "*", "*")
    roots += [p for p in glob.glob(pat) if p not in roots]
    return roots


def _agent_in(root: str, agent: str) -> bool:
    return bool(glob.glob(os.path.join(root, "agents", "**", f"{agent}.md"), recursive=True))


def _local_agent(name: str, agent_dirs: list[str]) -> bool:
    return any(glob.glob(os.path.join(d, "**", f"{name}.md"), recursive=True) for d in agent_dirs if os.path.isdir(d))


def preflight_agent(name: str, plugins_dir: str = PLUGINS_DIR, agent_dirs: list[str] | None = None) -> tuple[bool, str]:
    agent_dirs = agent_dirs if agent_dirs is not None else [PROJECT_AGENTS, USER_AGENTS]
    if ":" in name:
        plugin, agent = name.split(":", 1)
        if any(_agent_in(r, agent) for r in _plugin_roots(plugin, plugins_dir)):
            return True, f"ok: {name} resolves (plugin '{plugin}')"
        owners = sorted({os.path.basename(os.path.dirname(r)) for r in _plugin_roots(None, plugins_dir)
                         if _agent_in(r, agent)})
        hint = f" — did you mean {owners[0]}:{agent}?" if owners else ""
        if not hint and _local_agent(agent, agent_dirs):
            hint = f" — did you mean {agent}? (a project agent, no prefix)"
        return False, f"FAIL: no agent '{agent}' in plugin '{plugin}'{hint}"
    if name in BUILTIN_AGENTS:
        return True, f"ok: {name} is a built-in agent type"
    if _local_agent(name, agent_dirs):
        return True, f"ok: {name} resolves (project/user agent)"
    owners = sorted({os.path.basename(os.path.dirname(r)) for r in _plugin_roots(None, plugins_dir)
                     if _agent_in(r, name)})
    if owners:
        return False, (f"FAIL: '{name}' exists only as a plugin agent; plugin agents need the prefix — "
                       f"did you mean {owners[0]}:{name}?")
    return False, f"FAIL: no agent named '{name}' (checked .claude/agents/, ~/.claude/agents/, installed plugins)"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("mark")
    m.add_argument("event"); m.add_argument("step")
    m.add_argument("--status", required=True, choices=STATUSES)
    m.add_argument("--reason"); m.add_argument("--duration-s", type=float)
    m.add_argument("--meta", nargs="*", default=[])
    for c in ("show", "resume-point"):
        sub.add_parser(c).add_argument("event")
    sub.add_parser("preflight-agent").add_argument("name")
    a = ap.parse_args(argv)

    if a.cmd == "mark":
        try:
            st = mark(a.event, a.step, a.status, a.reason, a.duration_s, parse_meta(a.meta))
        except ValueError as e:
            print(f"run_state: {e}", file=sys.stderr)
            return 2
        print(f"marked {a.step} (Step {STEP_NUM[a.step]}) {a.status} · resume point: {resume_point(st)}")
        return 0
    if a.cmd == "show":
        print(render(a.event, load(a.event)))
        return 0
    if a.cmd == "resume-point":
        print(resume_point(load(a.event)))
        return 0
    ok, msg = preflight_agent(a.name)
    print(msg, file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
