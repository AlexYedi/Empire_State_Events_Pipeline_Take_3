#!/usr/bin/env python3
"""check-tombstones.py: flag live references to removed tools/decisions (YED-201 Fix 2A).

Why: a removal recorded only in the canonical spec never reaches the files that use it. The 08-07 Gamma
removal left 6 skills/commands still calling Gamma. Models under-enforce human-authored strictness (the
same lesson as check-refs / bf17), so this is a mechanical check, not a rubric line.

Source of truth: the "## Tombstones" table in .claude/references/platform-constraints.md.
A line is flagged when it matches a tombstone pattern and carries NO removal marker on the same line.
Conservative by design: under-flagging is the safe bias (a marker anywhere on the line clears it).

Usage:
  check-tombstones.py --artifact <path>   # judge Step 0: one file
  check-tombstones.py --all               # rigor-review: repo-wide, docs + code/config (SCAN_EXT) under .claude/ + docs/, history dirs skipped
Hits are a LOWER BOUND, not exhaustive: a removal marker within WINDOW chars clears a match. Treat hits as verified facts, never as proof of absence.
stdout: one "path:line: [term] text" per hit     stderr: "check-tombstones: N hit(s) in M file(s)"
exit 0 always (advisory; the caller decides).
"""
import os, re, sys

REGISTRY = ".claude/references/platform-constraints.md"
# A removal marker only clears a hit when it sits NEAR the matched term (within WINDOW chars either side).
# The first version cleared on any "not"/"no"/"don't" anywhere on the line. The 2026-09-19 judge showed that
# silently passes live violations ("don't spend Gamma credits", a 300-char-away "not"), so proximity is required.
MARKER = re.compile(r"remov|retir|ripped|deprecat|tombston|vestigial|killed|reject|disabl|supersed|replac|demot|"
                    r"garbl|defer|learned|no longer|legacy|historical|was the default|\bno\b|\bnot\b|never|"
                    r"instead of", re.I)
WINDOW = 40
# history / logs / generated data: describing the past there is correct, not drift
SKIP_DIRS = (".claude/artifacts/", ".claude/evals/logs/", ".claude/notes/",
             ".claude/proposals/", "docs/adr/", ".claude/data/", ".claude/.state/")
SKIP_FILES = {REGISTRY, ".claude/evals/correction-recurrence.md", ".claude/hooks/check-tombstones.py"}
# text files where a live call to a removed tool can hide: docs AND executable code/config
SCAN_EXT = (".md", ".py", ".sh", ".mjs", ".js", ".ts", ".json", ".yml", ".yaml", ".toml")

def load_tombstones():
    rows, in_table = [], False
    for line in open(REGISTRY, encoding="utf-8"):
        if line.startswith("## "):
            in_table = line.startswith("## Tombstones")
            continue
        if not in_table or not line.startswith("|") or line.startswith("|---") or line.startswith("| Term"):
            continue
        cells = [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]]
        if len(cells) >= 2:
            rows.append((cells[0], re.compile(cells[1].strip("`"))))  # case-sensitive: product names are capitalized; re.I flagged ML "gamma"
    return rows

SENTENCE_END = re.compile(r"[.;!?](?:\s|$)")

def _window(text, m):
    """WINDOW chars either side of the match, clipped to the match's own sentence, so a marker word in a
    neighbouring sentence can't clear a live claim (round-2 judge: 'Legacy note aside. Gamma MCP renders …')."""
    lo, hi = max(0, m.start() - WINDOW), min(len(text), m.end() + WINDOW)
    before = [e.end() for e in SENTENCE_END.finditer(text, lo, m.start())]
    after = SENTENCE_END.search(text, m.end(), hi)
    return text[(before[-1] if before else lo):(after.start() if after else hi)]

def scan(path, tombs):
    hits = []
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except (UnicodeDecodeError, OSError):
        return hits
    for i, text in enumerate(lines, 1):
        for term, rx in tombs:
            live = [m for m in rx.finditer(text) if not MARKER.search(_window(text, m))]
            if live:
                hits.append(f"{path}:{i}: [{term}] {text.strip()[:160]}")
                break
    return hits

def main(argv):
    os.chdir(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
    tombs = load_tombstones()
    if not tombs:
        print("check-tombstones: no Tombstones table found in " + REGISTRY, file=sys.stderr); return 0
    if argv[:1] == ["--artifact"] and len(argv) > 1:
        files = [argv[1]]
    elif argv[:1] == ["--all"]:
        files = []
        for root in (".claude", "docs"):
            for d, _, fs in os.walk(root):
                for f in fs:
                    p = os.path.join(d, f)
                    if f.endswith(SCAN_EXT) and not p.startswith(SKIP_DIRS) and p not in SKIP_FILES:
                        files.append(p)
    else:
        print(__doc__, file=sys.stderr); return 2
    hits = [h for f in sorted(files) for h in scan(f, tombs)]
    print("\n".join(hits)) if hits else None
    print(f"check-tombstones: {len(hits)} hit(s) in {len({h.split(':')[0] for h in hits})} file(s)", file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
