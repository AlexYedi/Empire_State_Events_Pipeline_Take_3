#!/usr/bin/env python3
"""seat_prep: turn a pipeline file (research brief, Scan head, drafts, a post-event brief) into the public-only copy
the other two models see (YED-517).

  seat_prep.py SRC.md --out OUT.md [--keep-section NAME ...]
  seat_prep.py --selftest

What it removes, before second_opinion.gate even looks:
* whole sections whose heading names private material: Success Signals (they carry the job-search focus), Author
  Steer, the Prior-Context Pack and its parts (Continuity Ledger, Graph Signals, Audit), Prior Snapshots, anything
  about inbox, Gmail, email or off-the-record material, and outreach / connection notes (real messages to real
  people stay with Claude);
* attendee lists and rosters (people who came to a public talk are not public figures);
* single lines that name a private file or carry a private marker (the gate's own list), and lines that carry an
  inbox-derived provenance tag, and lines about hiring, recruiting, referrals or the job
  search (which company the operator is weighing can itself reveal a target) (`tier: email-signal`, `[gmail`, `[email`, `inbox`).
Then it writes `visibility: public` as line 1 and runs the gate. Exit 0 = OUT.md may go to a seat; exit 2 = refused
(the reason is printed, OUT.md is not written). It prints what it removed so the run can record it.

It cannot see the Notion "Off the record" checkbox: if the event has it checked, do not call a seat at all.
"""
from __future__ import annotations
import argparse, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import second_opinion as so  # noqa: E402

DROP_SECTIONS = re.compile(
    r"success signals|author steer|prior[- ]context|continuity ledger|graph signals|^audit\b|prior snapshots|"
    r"inbox|gmail|e-?mail|off[- ]the[- ]record|connection (request )?notes?|outreach|\bdms?\b|follow-?ups? to|"
    r"private track|relationship|attendees?|roster|people met|contacts?\b|bucket [ab]", re.I)
DROP_LINE = re.compile(r"hiring|recruit|job[- ]search|referral|open roles?\b|\bresume\b|interview(ing)? (loop|prep|process)|"
                       r"tier:\s*email-signal|\[(gmail|email|inbox)\b|\bgmail\b|\binbox\b|email-signal", re.I)
HEAD = re.compile(r"^(#{1,6})\s+(.*)$")


def strip(text: str, keep: tuple[str, ...] = ()) -> tuple[str, list[str]]:
    out, removed, skip_level = [], [], None
    keep_l = tuple(k.lower() for k in keep)
    for line in text.splitlines():
        if line.strip() == "visibility: public":
            continue
        m = HEAD.match(line)
        if m:
            level, title = len(m.group(1)), m.group(2).strip()
            if skip_level is not None and level > skip_level:
                continue                       # still inside a dropped section
            skip_level = None
            if DROP_SECTIONS.search(title) and not title.lower().startswith(keep_l or ("\0",)):
                skip_level = level
                removed.append(f"section: {title}")
                continue
        elif skip_level is not None:
            continue
        if DROP_LINE.search(line) or any(m in line.lower() for m in so.MARKERS):
            removed.append("line: " + line.strip()[:60])
            continue
        out.append(line)
    return "visibility: public\n" + "\n".join(out).strip() + "\n", removed


def prep(src: str, out: str, keep=()) -> int:
    text, removed = strip(open(src, encoding="utf-8").read(), tuple(keep))
    try:
        so.gate(text)
    except so.Refused as e:
        print(f"REFUSED: {e}. Nothing written; fix the source or leave the seats out of this one and say so.")
        return 2
    open(out, "w", encoding="utf-8").write(text)
    print(f"OK {out}: {len(text.split())} words; removed {len(removed)} item(s)")
    for r in removed:
        print("  -", r)
    return 0


def selftest() -> int:
    sample = """# Event Research Brief: Demo Night
### Quick Take
Go. Two speakers ship agent evals in production.
### People at-a-glance
#### Ada Example — CTO, Acme (speaker)
- claim: Acme raised a seed round | tier: web-verified | source: acme.com | url: https://acme.com/x | date: 2026-10-01
- claim: Ada replied about the demo | tier: email-signal | source: inbox | url: - | date: 2026-11-01
### Success Signals
- Meet the hiring manager for the solutions role at Acme.
### Author Steer — 2026-11-27
- Anything else: I want to land well with Ada.
### Questions to ask
1. How do you grade agent runs?
"""
    text, removed = strip(sample)
    ok = True
    def check(cond, name):
        nonlocal ok
        print(("pass " if cond else "FAIL ") + name)
        ok &= cond
    check(text.startswith("visibility: public\n"), "marker is line 1")
    check("hiring manager" not in text, "Success Signals removed")
    check("land well" not in text, "Author Steer removed")
    check("email-signal" not in text and "replied about" not in text, "inbox-derived ledger row removed")
    check("seed round" in text and "grade agent runs" in text, "public research kept")
    check(len([r for r in removed if r.startswith("section")]) == 2, "two sections reported")
    t3, r3 = strip("# A\nKeep the me-model.md file out of git.\nPublic line.\n")
    check("me-model" not in t3 and "Public line" in t3 and bool(r3), "line naming a private file dropped, rest kept")
    t4, _ = strip("# A\n- *De-prioritize:* not a hiring-manager lane.\n- Talk on evals.\n")
    check("hiring" not in t4 and "Talk on evals" in t4, "job-search line dropped")
    nested = "# A\n## Outreach\n### Ada\nnote text\n## Questions to ask\nq1\n"
    t2, _ = strip(nested)
    check("note text" not in t2 and "q1" in t2, "nested subsections of a dropped section removed, siblings kept")
    try:
        so.gate(text.replace("Go.", "Go. ada@example.com"), shingles=set(), identity=())
        check(False, "gate still refuses an email after strip")
    except so.Refused:
        check(True, "gate still refuses an email after strip")
    print("selftest:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", nargs="?"); ap.add_argument("--out"); ap.add_argument("--keep-section", action="append",
                                                                                  default=[])
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not a.src or not a.out:
        ap.error("SRC and --out are required")
    sys.exit(prep(a.src, a.out, a.keep_section))
