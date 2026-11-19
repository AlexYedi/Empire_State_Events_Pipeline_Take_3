#!/usr/bin/env python3
"""YED-411 step 4: one-way Claude memory, laptop -> mini, with an inbox for what the mini learns.

The laptop holds the master copy of Claude's auto-memory (`~/.claude/projects/<slug>/memory/`). Auto-memory is
machine-local by design (code.claude.com/docs/en/memory), so this script makes the mini follow the laptop while
keeping every note a mini session wrote:

  1. INBOX first. Any mini note that is new, or changed since the last install, and does not match the laptop's
     current copy, is copied to <inbox>/<date>/ (deduplicated by content). New lines in the mini's MEMORY.md index
     go to <inbox>/<date>/MEMORY.additions.md. Nothing is lost; Alex promotes from the inbox at the Friday review.
  2. INSTALL the laptop's notes into the mini's memory dir (atomic replace per file). Mini-only notes are kept, and
     their index lines are re-appended to the installed MEMORY.md, so mini sessions still see them until promoted.
  3. BASELINE := the laptop copy just installed, so the next run can tell mini changes from laptop changes.
  --extra DIR: other mini memory dirs (e.g. a session started outside the repo) are inbox-only, never installed into.

Never deletes a note anywhere. Stdlib only. Prints one summary line; exit 0, or 3 on a usage error.
"""
import argparse, hashlib, os, shutil, sys, tempfile
from datetime import date
from pathlib import Path

INDEX = "MEMORY.md"
PENDING = " (mini note, awaiting promotion)"


def h(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def notes(d: Path) -> dict:
    return {p.name: p for p in sorted(d.glob("*.md")) if p.is_file()} if d.is_dir() else {}


def atomic_copy(src: Path, dst: Path) -> None:
    fd, tmp = tempfile.mkstemp(dir=dst.parent, prefix=f".{dst.name}.")
    os.close(fd)
    shutil.copy2(src, tmp)
    os.replace(tmp, dst)


def index_lines(p: Path) -> list:
    return [l.rstrip("\n") for l in p.read_text(encoding="utf-8").splitlines()] if p.is_file() else []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--laptop", required=True, type=Path, help="fresh mirror of the laptop memory dir")
    ap.add_argument("--target", required=True, type=Path, action="append", help="mini memory dir to install into")
    ap.add_argument("--baseline", required=True, type=Path)
    ap.add_argument("--inbox", required=True, type=Path)
    ap.add_argument("--extra", type=Path, action="append", default=[])
    a = ap.parse_args()
    lap = notes(a.laptop)
    if INDEX not in lap:
        print(f"memory sync SKIP: no {INDEX} in the laptop mirror (empty or failed pull); nothing changed")
        return 0
    today = a.inbox / date.today().isoformat()
    # Dedupe against the live inbox, everything already handled (memory-inbox-done, a sibling of the inbox), and the
    # laptop's notes themselves: a note that was promoted or archived must not bounce back every hour (bug found 11/18).
    done = a.inbox.parent / (a.inbox.name + "-done")
    seen = {h(p) for d in (a.inbox, done) if d.is_dir() for p in d.rglob("*.md")}
    seen |= {h(p) for p in lap.values()}
    inboxed = 0

    def to_inbox(src: Path, label: str) -> None:
        nonlocal inboxed
        d = h(src)
        if d in seen:
            return
        today.mkdir(parents=True, exist_ok=True)
        dst = today / label
        n = 1
        while dst.exists():
            dst = today / f"{dst.stem.split('~')[0]}~{n}.md"; n += 1
        shutil.copy2(src, dst)
        seen.add(d); inboxed += 1

    base = notes(a.baseline)
    lap_index = index_lines(lap[INDEX])
    base_index = set(index_lines(base[INDEX])) if INDEX in base else set()
    installed = 0
    for tgt in a.target:
        tgt.mkdir(parents=True, exist_ok=True)
        mini = notes(tgt)
        # 1. inbox mini-originated notes
        for name, p in mini.items():
            if name == INDEX:
                continue
            if name in lap and h(p) == h(lap[name]):
                continue                                    # already identical to the laptop
            if name in base and h(p) == h(base[name]):
                continue                                    # unchanged since last install: the laptop moved, not the mini
            to_inbox(p, f"{tgt.parent.name[-24:]}__{name}" if len(a.target) > 1 else name)
        mini_index = index_lines(tgt / INDEX)
        added = [l for l in mini_index if l.strip() and l not in lap_index and l not in base_index
                 and not l.endswith(PENDING)]
        if added:
            tmp = Path(tempfile.mkstemp(suffix=".md")[1]); tmp.write_text("\n".join(added) + "\n", encoding="utf-8")
            to_inbox(tmp, "MEMORY.additions.md"); tmp.unlink()
        # 2. install the laptop's notes; keep mini-only notes reachable from the index
        for name, p in lap.items():
            if name != INDEX and (name not in mini or h(mini[name]) != h(p)):
                atomic_copy(p, tgt / name); installed += 1
        mini_only = {n for n in notes(tgt) if n not in lap and n != INDEX}
        keep = []
        for l in mini_index:
            core = l[: -len(PENDING)] if l.endswith(PENDING) else l
            if core in lap_index:
                continue
            if any(f"({n})" in core for n in mini_only):
                keep.append(core + PENDING)
        merged = lap_index + [l for l in dict.fromkeys(keep)]
        tmp = tgt / f".{INDEX}.new"
        tmp.write_text("\n".join(merged) + "\n", encoding="utf-8")
        if not (tgt / INDEX).is_file() or (tgt / INDEX).read_text(encoding="utf-8") != tmp.read_text(encoding="utf-8"):
            os.replace(tmp, tgt / INDEX); installed += 1
        else:
            tmp.unlink()
    # extra dirs: inbox only
    for d in a.extra:
        for name, p in notes(d).items():
            to_inbox(p, f"{d.parent.name[-24:]}__{name}")
    # 3. baseline := laptop copy just installed
    a.baseline.mkdir(parents=True, exist_ok=True)
    for name in notes(a.baseline):
        if name not in lap:
            (a.baseline / name).unlink()
    for name, p in lap.items():
        shutil.copy2(p, a.baseline / name)
    total = sum(1 for _ in a.inbox.rglob("*.md")) if a.inbox.is_dir() else 0
    print(f"memory sync OK: {len(lap)} laptop notes, {installed} files updated, {inboxed} new to inbox, inbox total {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
