#!/usr/bin/env python3
"""runtime_ledgers.py — which missing `.claude/artifacts/*.jsonl` references are runtime-created ledgers.

Spec: YED-227. Shared by check-refs.sh and build_graph.py so the two dangling-ref tools cannot
drift (ADR-8 D2 — one rule, one implementation, not two copies kept "in sync" by a comment).

WHY: an append-only audit ledger (identity-ambiguity.jsonl, substrate-gate-failures.jsonl,
graph-freeze-overrides.jsonl, …) does not exist until its first write. check-refs.sh flagged it as
dangling and the judge capped completeness at 0.60 — on YED-47 (2026-09-27) that turned two passes
into flags. A placeholder file is the wrong fix: identity_probe.py reads an ABSENT ledger as "no data
yet" and an EMPTY one as "a producer ran and found nothing", so a placeholder would lie.

RULE (all must hold, else the reference still flags):
  1. the reference is `.claude/artifacts/<name>.jsonl` (directly under artifacts/, .jsonl);
  2. some TRACKED file under .claude/scripts/ or .claude/hooks/ names `<name>.jsonl` together with
     an `artifacts` path component, AND
  3. that same file performs an append-mode write (`open(..., "a"…)` / `open(..., mode="a"…)` / `>>`).

KNOWN LIMITATION (recorded, not hidden): (2)+(3) are file-level co-occurrence, not dataflow. A file
that appends to ledger A and only READS ledger B would excuse a missing B. Writers here bind the path to
a constant and append through the constant, so per-line matching would miss every real writer; the
co-occurrence is the honest approximation. A typo'd name, or a ledger with no appending writer
anywhere, still flags — which is what the cap exists to catch.

Usage:
  runtime_ledgers.py --list            print the runtime ledger paths, one per line
  runtime_ledgers.py --check <ref>...  print each ref that IS a runtime ledger
  runtime_ledgers.py --selftest
"""
import os
import re
import subprocess
import sys

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or subprocess.run(
    ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip() or os.getcwd()

LEDGER_REF_RE = re.compile(r"^(?:\./)?\.claude/artifacts/([A-Za-z0-9._-]+\.jsonl)$")
APPEND_RE = re.compile(r"""open\([^)\n]*?,\s*(?:mode\s*=\s*)?["']a[b+t]*["']|>>""")
NAME_RE = re.compile(r"([A-Za-z0-9._-]+\.jsonl)")
WRITER_DIRS = (".claude/scripts", ".claude/hooks")


def ledgers_from_texts(texts):
    """{path: text} -> set of ledger basenames that some appending file names beside `artifacts`."""
    names = set()
    for text in texts.values():
        if not APPEND_RE.search(text):
            continue
        for line in text.splitlines():
            if "artifacts" not in line:
                continue
            names.update(NAME_RE.findall(line))
    return names


def tracked_writer_texts(root=ROOT):
    p = subprocess.run(["git", "ls-files", *WRITER_DIRS], cwd=root, capture_output=True, text=True)
    out = {}
    for rel in p.stdout.split():
        if not rel.endswith((".py", ".sh")):
            continue
        try:
            out[rel] = open(os.path.join(root, rel), encoding="utf-8", errors="ignore").read()
        except OSError:
            pass
    return out


_CACHE = None


def runtime_ledger_names(root=ROOT):
    global _CACHE
    if _CACHE is None:
        _CACHE = ledgers_from_texts(tracked_writer_texts(root))
    return _CACHE


def is_runtime_ledger(ref, names=None):
    m = LEDGER_REF_RE.match(ref)
    if not m:
        return False
    return m.group(1) in (names if names is not None else runtime_ledger_names())


def selftest():
    # Fixture paths are built by concatenation so they never appear as literal `.claude/…` tokens in
    # this file — a literal would become a real dangling reference in the system graph (the test data
    # polluting the thing under test, the trap build_graph.py's EXTRACTOR_CASES comment records).
    A = ".claude/" + "artifacts/"
    texts = {
        "writer.py": 'LOG = os.path.join(ROOT, ".claude", "artifacts", "gate-failures.jsonl")\n'
                     'with open(LOG, "a", encoding="utf-8") as f:\n    f.write(x)\n',
        "shell.sh": 'FAIL_LOG="' + A + 'shell-fails.jsonl"\necho "$row" >> "$FAIL_LOG"\n',
        "reader.py": 'P = os.path.join(ROOT, ".claude", "artifacts", "read-only.jsonl")\n'
                     'for line in open(P, encoding="utf-8"):\n    pass\n',
        "writer_w.py": 'P = os.path.join(ROOT, ".claude", "artifacts", "overwritten.jsonl")\n'
                       'with open(P, "w") as f:\n    f.write(x)\n',
    }
    names = ledgers_from_texts(texts)
    cases = [
        (A + "gate-failures.jsonl", True, "python append-mode writer via a constant"),
        ("./" + A + "shell-fails.jsonl", True, "shell >> writer"),
        (A + "gate-failure.jsonl", False, "typo'd name, no writer"),
        (A + "read-only.jsonl", False, "only ever read"),
        (A + "overwritten.jsonl", False, "written with 'w', not append"),
        (A + "sub/gate-failures.jsonl", False, "not directly under artifacts/"),
        (".claude/" + "references/gate-failures.jsonl", False, "not under artifacts/"),
        (A + "gate-failures.md", False, "not .jsonl"),
    ]
    fails = 0
    for ref, want, why in cases:
        got = is_runtime_ledger(ref, names)
        if got != want:
            fails += 1
            print(f"FAIL  {ref}: expected {want}, got {got} ({why})", file=sys.stderr)
    live = runtime_ledger_names()
    for must in ("substrate-gate-failures.jsonl", "identity-ambiguity.jsonl",
                 "identity-merges.jsonl", "graph-freeze-overrides.jsonl"):
        if must not in live:
            fails += 1
            print(f"FAIL  live repo: {must} not recognised as a runtime ledger", file=sys.stderr)
    n = len(cases) + 4
    print(f"runtime_ledgers selftest: {n - fails}/{n} pass", file=sys.stderr)
    return fails == 0


def main(argv):
    if "--selftest" in argv:
        return 0 if selftest() else 1
    if "--list" in argv:
        for n in sorted(runtime_ledger_names()):
            print(f".claude/artifacts/{n}")
        return 0
    if "--check" in argv:
        for ref in argv[argv.index("--check") + 1:]:
            if is_runtime_ledger(ref):
                print(ref)
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
