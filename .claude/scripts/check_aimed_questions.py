#!/usr/bin/env python3
"""Mechanical check for a Prior-Context Pack's `## Aimed Questions` section (YED-217).

Turns "every question is traceable to a carried claim" from an eyeball call into a
repeatable one. For each question it checks:
  1. ANCHOR  — the Anchor line quotes the claim, and every quoted fragment (split on
               the "…" elision) appears word-for-word in the raw pull (--raw). The raw
               pull is the source of truth: cards paraphrase, so without --raw it falls
               back to the pack outside the Aimed Questions section. A claim id
               (c:xxxxxxxx) cited on the question must exist in the raw pull.
               Anchors over 25 words WARN (spec: ≤25, elide with …).
  2. TRUST   — a KNOWN/STALE/UNVERIFIED tag is present.
  3. TARGET  — the target is a name from the verbatim invite, or the room / the format.
  4. SHAPE   — a non-KNOWN question must not open with a premise ("Given that…").

Matching compares words, not typography (punctuation, quote style, emphasis are
dropped), so a curly-vs-straight quote never fails a real anchor — but an inserted,
dropped, or changed word does.

Usage:
  check_aimed_questions.py PACK.md --invite INVITE.txt [--raw RAW.md]
  check_aimed_questions.py --selftest    # proves it catches 5 planted defect classes
Exit 0 = all pass · 1 = at least one failure · 2 = no Aimed Questions section.
"""
import argparse
import re
import sys

PREMISE = re.compile(r"^\s*(given that|given|since|because|now that|as)\b", re.I)
TRUST = re.compile(r"(KNOWN|STALE|UNVERIFIED)")
QUOTE = re.compile(r"[\"“](.+?)[\"”](?=\s*(?:[,.;:—–-]|combined|from|$))")
ELISION = re.compile(r"…|\.\.\.")


def norm(s):
    s = re.sub(r"[^\w\s]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def fragments(anchor_line):
    """Normalized word-runs from every quoted span on the Anchor line, split on elisions."""
    spans = QUOTE.findall(anchor_line)
    frags = [norm(f) for sp in spans for f in ELISION.split(sp)]
    return [f for f in frags if len(f.split()) >= 3], sum(len(sp.split()) for sp in spans)


def split_section(pack):
    m = re.search(r"^## Aimed Questions.*?$", pack, re.M)
    if not m:
        return None, pack
    rest = pack[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    body = rest[: nxt.start()] if nxt else rest
    outside = pack[: m.start()] + (rest[nxt.start():] if nxt else "")
    return body, outside


def parse(body):
    """Return question dicts; targets come from `### → X` headers."""
    target, items, cur = None, [], None
    for line in body.splitlines():
        h = re.match(r"^###\s*→?\s*(.+)$", line)
        if h:
            target = h.group(1).strip()
            continue
        if re.match(r"^\s*-\s*\*\*Q", line):
            cur = {"target": target, "lines": [line]}
            items.append(cur)
        elif cur is not None and line.strip():
            cur["lines"].append(line)
    return items


SELFTEST_INVITE = "Speakers: Dale Seo (Sr Software Engineer, Apollo GraphQL), Dan Boerner (Head of Customer Advocacy)."
SELFTEST_RAW = """- Monolithic MCP servers don't scale organizationally (Yak). [first_hand · 2026-07-28] c:eaa3504a
- Managed MCP removes the self-host tax. Google offers managed MCP for its DBs. [first_hand · 2026-05-27] c:1fdbd097
"""
SELFTEST_GOOD = """## Aimed Questions
### → Dale Seo, Sr Software Engineer
- **Q:** Does "monolithic servers don't scale organizationally" hold for GraphOS, or is one server fine at this size?
  - **Anchor:** "Monolithic MCP servers don't scale organizationally" — from Topic: MCP at Enterprise Scale · c:eaa3504a
  - **Trust:** `STALE` `[first_hand · 2026-07-28]`
### → The room
- **Q:** Is anyone here self-hosting MCP, and would a managed server change that?
  - **Anchor:** "Managed MCP removes the self-host tax." — from Topic: MCP at Enterprise Scale · c:1fdbd097
  - **Trust:** `KNOWN` `[first_hand · 2026-05-27]`
"""
# Each bad question plants exactly one defect class; all must FAIL.
SELFTEST_BAD = """## Aimed Questions
### → Dale Seo, Sr Software Engineer
- **Q:** Given that monolithic MCP servers don't scale organizationally, how did you split GraphOS?
  - **Anchor:** "Monolithic MCP servers don't scale organizationally" — from Topic · c:eaa3504a
  - **Trust:** `UNVERIFIED`
- **Q:** Why is managed better?
  - **Anchor:** "Google offers managed MCP for its own DBs" — from Topic · c:1fdbd097
  - **Trust:** `KNOWN`
- **Q:** How many teams own it?
  - **Anchor:** "Monolithic MCP servers don't scale organizationally" — from Topic · c:deadbeef
  - **Trust:** `KNOWN`
### → Jane Nobody, CEO
- **Q:** What's your vision for agents?
  - **Anchor:** "Monolithic MCP servers don't scale organizationally" — from Topic
  - **Trust:** `KNOWN`
### → The room
- **Q:** Does anyone run more than one MCP server?
  - **Anchor:** "Monolithic MCP servers don't scale organizationally" — from Topic
"""


def selftest():
    import os
    import tempfile

    d = tempfile.mkdtemp()
    paths = {}
    for name, text in {"invite": SELFTEST_INVITE, "raw": SELFTEST_RAW,
                       "good": SELFTEST_GOOD, "bad": SELFTEST_BAD}.items():
        paths[name] = os.path.join(d, name)
        open(paths[name], "w").write(text)
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        good = run(paths["good"], paths["invite"], paths["raw"])
        bad = run(paths["bad"], paths["invite"], paths["raw"])
    out = buf.getvalue()
    n_fail = out.count("[FAIL]")
    ok = good == 0 and bad == 1 and n_fail == 5
    print(out if not ok else "", end="")
    print(f"selftest: good exit={good} (want 0) · bad exit={bad} (want 1) · "
          f"planted defects caught {n_fail}/5 → {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pack", nargs="?")
    ap.add_argument("--invite", help="file holding the VERBATIM SOURCE text")
    ap.add_argument("--raw", help="raw pull the pack was conditioned from (source of truth)")
    ap.add_argument("--selftest", action="store_true", help="prove the checker catches planted defects")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not (a.pack and a.invite):
        ap.error("PACK and --invite are required (or use --selftest)")
    return run(a.pack, a.invite, a.raw)


def run(pack_path, invite_path, raw_path):
    pack = open(pack_path).read()
    invite = norm(open(invite_path).read())
    raw_text = open(raw_path).read() if raw_path else None

    body, outside = split_section(pack)
    if body is None:
        print("NO SECTION: pack has no '## Aimed Questions' section")
        return 2
    source = norm(raw_text) if raw_text is not None else norm(outside)
    source_name = "raw pull" if raw_text is not None else "pack"
    items = parse(body)
    if not items:
        print("ZERO QUESTIONS (valid per spec if the section says why)")
        return 0

    fails = 0
    for i, it in enumerate(items, 1):
        block = "\n".join(it["lines"])
        q = re.sub(r"^\s*-\s*\*\*Q:?\*\*:?\s*", "", it["lines"][0]).strip()
        problems, warns = [], []

        aline = next((l for l in it["lines"] if "**Anchor" in l), "")
        frags, nwords = fragments(aline)
        if not frags:
            problems.append("no quoted anchor")
        for f in frags:
            if f not in source:
                problems.append(f"anchor text not in {source_name}: '{f[:80]}'")
        if nwords > 25:
            warns.append(f"anchor is {nwords} words (spec: <=25, elide with …)")
        for cid in re.findall(r"\bc:[0-9a-f]{8}\b", block):
            if raw_text is not None and cid not in raw_text:
                problems.append(f"claim id {cid} not in raw pull")

        tline = next((l for l in it["lines"] if "**Trust" in l), "")
        tm = TRUST.search(tline)
        trust = tm.group(1) if tm else None
        if not trust:
            problems.append("no trust tag")

        tgt = (it["target"] or "").lower()
        if "room" in tgt or "format" in tgt:
            kind = "room/format"
        else:
            name = norm(re.split(r"[,(—–]", it["target"] or "")[0])
            kind = "named" if name and name in invite else None
            if not kind:
                problems.append(f"target '{it['target']}' not named in invite")

        if trust and trust != "KNOWN" and PREMISE.match(q):
            problems.append(f"{trust} anchor but premise-shaped wording")

        fails += bool(problems)
        print(f"[{'FAIL' if problems else 'PASS'}] Q{i} → {it['target']} ({kind or '?'}, {trust or '?'}): {q[:100]}")
        for p in problems:
            print(f"        - {p}")
        for w in warns:
            print(f"        ~ warn: {w}")

    print(f"\n{len(items) - fails}/{len(items)} pass")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
