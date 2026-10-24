#!/usr/bin/env python3
"""lint_agent_tools — every agent declares a minimal `tools:` line, and no agent that reads untrusted
text also holds a write tool (SEC-03, 10-15 routing audit; CLAUDE.md invariants 5-6).

Rules, per agent .md (frontmatter between the first two `---` lines):
  1. A non-empty `tools:` line. Missing, empty, or any `*` wildcard fails (not minimal).
  2. READERS (untrusted text in): WebSearch, WebFetch, any Gmail MCP tool, and any MCP tool whose name
     contains `search` or `fetch` on a server that is not INTERNAL_SERVERS.
     WRITERS (external effect out): Bash (it can curl/POST anywhere), any MCP tool whose name contains
     create/update/delete/write/send/manage/set/save (case-insensitive), plus every HubSpot/Supabase
     tool that is not a plain read (get_/list_/search_/fetch_/read_ prefix). A server-level grant
     (`mcp__x` with no tool part) counts as both. Local file tools (Read, Write, Edit) are not writers.
     An agent holding any READER and any WRITER fails.
  3. Every failure prints `file: reason`; exit 1 if any failed, 0 if clean.

Notion is INTERNAL: notion-fetch/search read Alex's own workspace (the human-reviewed store), not
open-web or inbox text. That is what lets `notion-writer`, the one sanctioned writer (invariant 5),
pass on the rule itself rather than on an allowlisted name.

Usage:  python3 lint_agent_tools.py [DIR_OR_FILE ...]   (default: .claude/agents, else agents)
        python3 lint_agent_tools.py --selftest
Stdlib only. The same file lives in the pipeline (.claude/scripts/) and the plugin (scripts/).
"""
from __future__ import annotations
import glob, os, re, sys

INTERNAL_SERVERS = {"notion", "claude_ai_notion"}          # invariant 5: internal reads, not untrusted text
GUARDED_SERVERS = ("hubspot", "supabase")                    # any non-read tool here is a write
READ_PREFIXES = ("get", "list", "search", "fetch", "read")
WRITE_VERBS = re.compile(r"create|update|delete|write|send|manage|set|save", re.I)
EXTERNAL_READ = re.compile(r"search|fetch", re.I)


def parse_tools(text: str) -> list[str] | None:
    """Return the tools list, [] if the line is present but empty, None if missing (or no frontmatter)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return None
    fm = lines[1:end]
    for i, line in enumerate(fm):
        m = re.match(r"^tools\s*:(.*)$", line)
        if not m:
            continue
        val = m.group(1).strip()
        if val:                                            # inline: `a, b` or `[a, b]`
            return [t.strip().strip("'\"") for t in val.strip("[]").split(",") if t.strip()]
        items = []                                         # block list: `- a` lines
        for nxt in fm[i + 1:]:
            b = re.match(r"^\s+-\s*(.+)$", nxt)
            if not b:
                break
            items.append(b.group(1).strip().strip("'\""))
        return items
    return None


def split_mcp(tool: str) -> tuple[str, str] | None:
    """mcp__<server>__<tool> -> (server, tool); tool == '' for a server-level grant. None if not MCP."""
    if not tool.startswith("mcp__"):
        return None
    parts = tool.split("__", 2)
    return parts[1].lower(), (parts[2] if len(parts) > 2 else "")


def is_reader(tool: str) -> bool:
    if tool in ("WebSearch", "WebFetch"):
        return True
    mcp = split_mcp(tool)
    if not mcp:
        return False
    server, name = mcp
    if "gmail" in server or "gmail" in name.lower():
        return True
    if server in INTERNAL_SERVERS:
        return False
    return name == "" or bool(EXTERNAL_READ.search(name))


def is_writer(tool: str) -> bool:
    if tool == "Bash" or tool.startswith("Bash("):          # shell = arbitrary network egress
        return True
    mcp = split_mcp(tool)
    if not mcp:
        return False
    server, name = mcp
    if name == "" or WRITE_VERBS.search(name):
        return True
    if any(g in server for g in GUARDED_SERVERS):
        return not name.lower().startswith(READ_PREFIXES)
    return False


def check(path: str) -> list[str]:
    with open(path, encoding="utf-8") as f:
        tools = parse_tools(f.read())
    if tools is None:
        return ["no `tools:` line in frontmatter (rule 1: every agent declares a minimal tools list)"]
    if not tools:
        return ["`tools:` line is empty (rule 1)"]
    wild = [t for t in tools if "*" in t]
    if wild:
        return [f"wildcard in `tools:` ({', '.join(wild)}) is not minimal (rule 1)"]
    readers = [t for t in tools if is_reader(t)]
    writers = [t for t in tools if is_writer(t)]
    if readers and writers:
        return [f"reads untrusted text ({', '.join(readers)}) AND holds write tools ({', '.join(writers)}) "
                "(rule 2; CLAUDE.md invariant 5)"]
    return []


def collect(args: list[str]) -> list[str]:
    if not args:
        args = [d for d in (".claude/agents", "agents") if os.path.isdir(d)][:1]
    files = []
    for a in args:
        files += [a] if os.path.isfile(a) else glob.glob(os.path.join(a, "**", "*.md"), recursive=True)
    return sorted(files)


def selftest() -> int:
    fm = lambda t: f"---\nname: x\n{t}\n---\nbody\n"
    cases = [
        (fm("tools: Read"), True),
        (fm("description: no tools"), False),
        (fm("tools:"), False),
        (fm("tools: *"), False),
        (fm("tools: Read, mcp__notion__*"), False),
        (fm("tools: Read, Write, mcp__notion__notion-fetch, mcp__notion__notion-search, "
            "mcp__notion__notion-create-pages, mcp__notion__notion-update-page"), True),   # notion-writer
        (fm("tools: WebSearch, WebFetch, Read, mcp__claude_ai_Gmail__search_threads"), True),
        (fm("tools: WebFetch, Write, Edit"), True),                       # local Write is not an MCP write
        (fm("tools: WebFetch, mcp__notion__notion-create-pages"), False),
        (fm("tools: mcp__claude_ai_Gmail__get_thread, mcp__hubspot__manage_crm_objects"), False),
        (fm("tools: WebSearch, mcp__supabase__execute_sql"), False),
        (fm("tools: WebSearch, mcp__supabase__list_tables"), True),
        (fm("tools: mcp__linear__search_issues, mcp__linear__save_issue"), False),  # `save` is a write verb
        (fm("tools: WebFetch, Read, Bash"), False),                       # Bash can POST anywhere
        (fm("tools: Read, Write, Edit, Bash"), True),                     # Bash alone, no reader
        (fm("tools: mcp__exa__web_search, mcp__linear__create_issue"), False),
        (fm("tools: WebFetch, mcp__claude_ai_HubSpot"), False),             # server-level grant
        (fm("tools:\n  - WebFetch\n  - mcp__notion__notion-update-page"), False),
        ("no frontmatter\n", False),
    ]
    import tempfile
    bad = 0
    with tempfile.TemporaryDirectory() as d:
        for i, (text, ok) in enumerate(cases):
            p = os.path.join(d, f"c{i}.md")
            with open(p, "w") as f:
                f.write(text)
            got = not check(p)
            if got != ok:
                bad += 1
                print(f"FAIL case {i}: expected {'pass' if ok else 'fail'}: {text!r}")
    print(f"selftest: {len(cases) - bad}/{len(cases)} passed")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["--selftest"]:
        return selftest()
    files = collect(argv)
    if not files:
        print("lint_agent_tools: no agent files found", file=sys.stderr)
        return 1
    failures = [(f, r) for f in files for r in check(f)]
    for f, r in failures:
        print(f"{f}: {r}")
    print(f"lint_agent_tools: {len(files)} agent file(s), {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
