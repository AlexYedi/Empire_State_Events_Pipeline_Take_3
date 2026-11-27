#!/usr/bin/env python3
"""seat_prep: build the public-only copy of a pipeline file that the other two models see (YED-517).

  seat_prep.py SRC.md --out OUT.md [--keep-section HEADING ...]
  seat_prep.py --selftest

Allowlist first (PR review X2, 27 Nov): a section reaches a seat only if its heading is on KEEP_SECTIONS (the
public parts of a research brief, Deep Read, post-event brief or draft) or was named with --keep-section after
Claude read it. A heading nobody listed is a container: its own body is dropped and reported, and its listed
subsections are kept. Text before the first heading is dropped.

Inside a kept section, these still come out:
* subsections whose heading names private material (Success Signals, which carry the job-search focus; Author
  Steer; the Prior-Context Pack and its parts; Prior Snapshots; inbox, Gmail, email or off-the-record material;
  outreach and connection notes; rosters and attendee lists);
* whole blocks (a list item with its continuation lines, or a paragraph) that carry an inbox-derived provenance tag,
  a private marker or a private file name, or talk about hiring, recruiting, referrals or the job search. A match
  on any line of a wrapped block drops the whole block (PR review G4).
Code fences are tracked, so a `# comment` inside a fence is never read as a heading (G2).
Then `visibility: public` goes on line 1, markers split across lines refuse, and second_opinion.gate runs.
Exit 0 = OUT.md may go to a seat; exit 2 = refused, OUT.md removed, no seat call.

It cannot see the Notion "Off the record" checkbox: check it once per run before any seat call.
"""
from __future__ import annotations
import argparse, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import second_opinion as so  # noqa: E402

KEEP_SECTIONS = re.compile(
    r"^(quick take|people at[- ]a[- ]glance|questions to ask|verification flags|evidence (set|ledger)|"
    r"the frame|primer|landscape|companies|people|cross[- ]event threads|deep read|talks?\b|sessions?\b|"
    r"speakers?\b|topics?\b|quote bank|glossary|key (claims|quotes|takeaways)|what (was|got) said|themes?\b|"
    r"documentarian|signals? log|company|person|topic|variant|post|draft|carousel|visual brief|x (post|thread)|"
    r"triage|entities|plan\b)", re.I)
DROP_SECTIONS = re.compile(
    r"success signals|author steer|prior[- ]context|continuity ledger|graph signals|^audit\b|prior snapshots|"
    r"inbox|gmail|e-?mail|off[- ]the[- ]record|connection (request )?notes?|outreach|\bdms?\b|follow-?ups? to|"
    r"private track|relationship|attendees?|roster|people met|contacts?\b|bucket [ab]", re.I)
DROP_BLOCK = re.compile(
    r"hiring|recruit|job[- ]search|referral|open roles?\b|\bcandidacy\b|interview(ing)? (loop|prep|process)|"
    r"off[- ]the[- ]record|tier:\s*email-signal|email-signal|\[(gmail|email|inbox)\b|\bgmail\b|"
    r"\b(my|his|alex's|the operator's) inbox\b|inbox[- ](list|allowlist|denylist)", re.I)
HEAD = re.compile(r"^(#{1,6})\s+(.*)$")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
ITEM = re.compile(r"^\s*([-*+]|\d+[.)])\s")


def _norm(s: str) -> str:
    return re.sub(r"[-_\s]+", " ", s.lower())


def _private(text: str) -> bool:
    n = _norm(text)
    return bool(DROP_BLOCK.search(text) or DROP_BLOCK.search(n) or any(_norm(m) in n for m in so.MARKERS))


def _blocks(lines):
    """Paragraphs and list items (with their indented continuation lines) as units."""
    out, cur = [], []
    for line in lines:
        if not line.strip():
            if cur:
                out.append(cur); cur = []
            out.append([line]); continue
        if ITEM.match(line) and cur:
            out.append(cur); cur = []
        cur.append(line)
    if cur:
        out.append(cur)
    return out


def strip(text: str, keep=()):
    keep_l = tuple(k.lower() for k in keep)
    stack = []                 # (level, state); state: keep | drop | container
    st = {"state": "preamble", "body": []}
    out, removed = [], []
    in_fence = False

    def flush():
        body, state = st["body"], st["state"]
        if state == "keep":
            for b in _blocks(body):
                if _private("\n".join(b)):
                    removed.append("block: " + b[0].strip()[:60])
                else:
                    out.extend(b)
        elif any(l.strip() for l in body):
            removed.append(f"{state} text: " + next(l for l in body if l.strip()).strip()[:60])
        st["body"] = []

    for line in text.splitlines():
        if line.strip() == "visibility: public":
            continue
        if FENCE.match(line):
            in_fence = not in_fence
            st["body"].append(line); continue
        m = None if in_fence else HEAD.match(line)
        if not m:
            st["body"].append(line); continue
        flush()
        level, title = len(m.group(1)), m.group(2).strip()
        while stack and stack[-1][0] >= level:
            stack.pop()
        parent = stack[-1][1] if stack else None
        t = re.sub(r"^[^a-z0-9]*(block \d+:?\s*)?", "", title.lower())
        if parent == "drop":
            new = "drop"
        elif DROP_SECTIONS.search(title):
            new = "drop"; removed.append(f"section: {title}")
        elif KEEP_SECTIONS.search(t) or (keep_l and t.startswith(keep_l)) or parent == "keep":
            new = "keep"
        else:
            new = "container"; removed.append(f"unlisted section (body dropped): {title}")
        stack.append((level, new))
        st["state"] = new
        if new in ("keep", "container") and not _private(title):
            out.append(line)
    flush()
    return "visibility: public\n" + "\n".join(out).strip() + "\n", removed


def wrapped_marker(text: str):
    """A multi-word marker split across a line break or written with hyphens/underscores (G4, G5)."""
    flat = _norm(text)
    return next((m for m in so.MARKERS if _norm(m) in flat), None)


def prep(src: str, out: str, keep=()) -> int:
    if os.path.exists(out) and os.path.samefile(src, out):
        print("REFUSED: --out is the source file; write the seat copy somewhere else."); return 2
    raw = open(src, encoding="utf-8").read()          # read before removing any old output (G2)
    if os.path.exists(out):
        os.remove(out)                                # a refused retry never leaves an older copy to send (X4)
    text, removed = strip(raw, tuple(keep))
    try:
        m = wrapped_marker(text)
        if m:
            raise so.Refused(f"private marker '{m}' (wrapped or hyphenated)")
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
    ok = True

    def check(cond, name):
        nonlocal ok
        print(("pass " if cond else "FAIL ") + name)
        ok &= bool(cond)

    sample = """Preamble note to self.
# Event Research Brief: Demo Night
### Quick Take
Go. Two speakers ship agent evals in production.
### People at-a-glance
#### Ada Example — CTO, Acme (speaker)
- claim: Acme raised a seed round | tier: web-verified | source: acme.com | url: https://acme.com/x | date: 2026-10-01
- claim: Ada replied about the demo | tier: email-signal | source: inbox | url: - | date: 2026-11-01
- *De-prioritize:* not a hiring-manager
  lane for this quarter.
### Success Signals
- Meet the hiring manager for the solutions role at Acme.
### Author Steer — 2026-11-27
- Anything else: I want to land well with Ada.
### Notes I jotted
- my private aside under a heading nobody listed
### Questions to ask
1. How do you grade agent runs?
- Tracewise ships an AI inbox for agents.
"""
    text, removed = strip(sample)
    check(text.startswith("visibility: public\n"), "marker is line 1")
    check("Preamble" not in text, "text before the first heading dropped")
    check("hiring manager for" not in text, "Success Signals removed")
    check("land well" not in text, "Author Steer removed")
    check("private aside" not in text, "an unlisted section's body is dropped (allowlist)")
    check("replied about" not in text, "inbox-derived ledger row removed")
    check("lane for this quarter" not in text, "a wrapped job-search bullet is dropped whole")
    check("seed round" in text and "grade agent runs" in text, "public research kept")
    check("AI inbox" in text, "a product called an inbox is kept")
    fenced = "# A\n## Quick Take\nkeep me\n## Author Steer\n```\n# not a heading\nsteer text\n```\n## Questions to ask\nq1\n"
    t2, _ = strip(fenced)
    check("steer text" not in t2 and "q1" in t2, "a # line inside a fence doesn't reopen a dropped section")
    t3, _ = strip("# A\n## Quick Take\nKeep the me-model.md file out of git.\n\nPublic line.\n")
    check("me-model" not in t3 and "Public line" in t3, "block naming a private file dropped, rest kept")
    t4, _ = strip("# A\n## Quick Take\nThis quote is off-the-\nrecord, per the host.\n\nPublic line.\n")
    check("per the host" not in t4 and "Public line" in t4, "hyphen-wrapped off-the-record block dropped")
    check(wrapped_marker("x me_model y") is not None, "underscore/hyphen marker variants caught")
    nested = "# A\n## Quick Take\nx\n## Outreach\n### Ada\nnote text\n## Questions to ask\nq1\n"
    t5, _ = strip(nested)
    check("note text" not in t5 and "q1" in t5, "nested subsections of a dropped section removed, siblings kept")
    t6, _ = strip("# A\n## My Notes\nprivate\n", keep=("my notes",))
    check("private" in t6, "--keep-section opts a heading in after Claude read it")
    try:
        so.gate(text.replace("Go.", "Go. ada@example.com"), shingles=set(), identity=())
        check(False, "gate still refuses an email after strip")
    except so.Refused:
        check(True, "gate still refuses an email after strip")
    print("selftest:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", nargs="?"); ap.add_argument("--out")
    ap.add_argument("--keep-section", action="append", default=[])
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not a.src or not a.out:
        ap.error("SRC and --out are required")
    sys.exit(prep(a.src, a.out, a.keep_section))
