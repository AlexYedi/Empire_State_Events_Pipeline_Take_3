#!/usr/bin/env python3
"""deep_read_slices — Step 4.5a of /event-deep-research: cut the synthesizer's Evidence Set into one evidence slice per
Deep-Read section, and give The Frame a code-built source index (YED-476).

Why the index: the synthesizer writes The Frame as a short pointer summary with no URLs, while the URLs sit in the
Evidence Ledgers under the other sections. Rendered from its slice alone, The Frame footnoted every fact as "URL not in
pack" (Dec 8-10 2026 run: 0/22 Frame endnotes carried a URL). With every URL-carrying ledger row appended as a
"Sources available" list, the same renderer cited 35/35 with a URL, all 35 present verbatim in the index, and its gap
notes turned from plumbing noise into real findings (A/B 2026-11-21, n=3 events, one Opus render each). Code builds the
index, so a URL that exists in any ledger always reaches the Frame renderer; no prompt has to remember to copy it.

  python3 .claude/scripts/deep_read_slices.py --evidence <slug>.evidence.md --out-dir <scratch>/<slug>.slices
      writes one file per section (01-the-frame.md ... 05-cross-event-threads.md) and prints sizes + warnings
  python3 .claude/scripts/deep_read_slices.py --selftest

Pure text in, text out: no network, no writes outside --out-dir.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

SECTIONS = [  # (render-section name, heading prefixes the synthesizer uses for it)
    ("The Frame", ("The Frame",)),
    ("Primer / Landscape", ("Primer", "Landscape", "Topics")),
    ("Companies", ("Companies",)),
    ("People", ("People",)),
    ("Cross-Event Threads", ("Cross-Event", "Cross Event")),
]
LEDGER_HEAD = re.compile(r"^##### Evidence Ledger — (.+?)\s*$")


def source_index(evidence: str) -> list[str]:
    """Every Evidence Ledger row that carries an http(s) URL, as one line each, de-duplicated on (claim, url)."""
    out, seen, entity = [], set(), None
    for line in evidence.splitlines():
        m = LEDGER_HEAD.match(line)
        if m:
            entity = m.group(1)
            continue
        if not line.startswith("- claim:"):
            continue
        f = {}
        for part in line[2:].split(" | "):
            k, _, v = part.partition(":")
            f[k.strip()] = v.strip()
        url = f.get("url", "")
        if not url.startswith(("http://", "https://")):
            continue
        key = (f.get("claim"), url)
        if key in seen:
            continue
        seen.add(key)
        out.append(f"- [{entity}] {f.get('claim')} — {f.get('source')} · {f.get('date')} · {url}")
    return out


def section_slices(evidence: str) -> tuple[dict[str, str], list[str]]:
    """Split on the synthesizer's '### <Section>' headings. A section with no heading gets the whole Evidence Set
    plus a scoping note (loud warning), so a renderer is never handed an empty slice by a formatting slip."""
    lines = evidence.splitlines(keepends=True)
    starts = []
    for i, line in enumerate(lines):
        if line.startswith("### "):
            title = line[4:].strip()
            for name, prefixes in SECTIONS:
                if title.startswith(prefixes):
                    starts.append((i, name))
                    break
    # An unrelated ### heading (e.g. the scanner's "Pattern signals") stays inside the section it follows.
    out, warn = {}, []
    for n, (i, name) in enumerate(starts):
        if name in out:
            continue
        end = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
        body = "".join(lines[i:end]).strip()
        if body:
            out[name] = body
    for name, _ in SECTIONS:
        if name not in out:
            warn.append(f"WARNING: no '### {name}' heading in the Evidence Set; that slice is the whole set, scoped by note")
            out[name] = (f"> Section heading missing from the Evidence Set: render only the {name} material from it.\n\n"
                         + evidence.strip())
    idx = source_index(evidence)
    if idx:
        out["The Frame"] += ("\n\n#### Sources available (every URL-carrying Evidence Ledger row in this event's "
                             "Evidence Set; cite from these)\n" + "\n".join(idx))
    else:
        warn.append("WARNING: no URL-carrying ledger rows found; The Frame has no source index")
    return {name: out[name] for name, _ in SECTIONS}, warn


def selftest() -> bool:
    ev = ("## Evidence Set\n### The Frame (pointer)\n- Room: Acme hosts.\n### Primer/Landscape (topics)\n#### Topic: X\n"
          "##### Evidence Ledger — X\n- claim: X grew | tier: web-verified | source: Blog | url: https://x.example/a | date: 2026-11-01\n"
          "- claim: X grew | tier: web-verified | source: Blog | url: https://x.example/a | date: 2026-11-01\n"
          "### Companies\n##### Evidence Ledger — Acme\n- claim: Acme raised $4M | tier: web-verified | source: TC | url: https://tc.example/b | date: 2026-10-01\n"
          "- claim: private note | tier: email-signal | source: Gmail | url: n/a | date: 2026-10-02\n"
          "### Pattern signals\n- noise\n### People\n#### Jane Doe\n### Cross-Event Threads\n- prior room\n")
    s, w = section_slices(ev)
    checks = [
        ("five slices, Frame first", list(s) == [n for n, _ in SECTIONS]),
        ("index: URL rows only, de-duplicated", source_index(ev) == [
            "- [X] X grew — Blog · 2026-11-01 · https://x.example/a",
            "- [Acme] Acme raised $4M — TC · 2026-10-01 · https://tc.example/b"]),
        ("Frame slice carries the index", "https://tc.example/b" in s["The Frame"] and "Sources available" in s["The Frame"]),
        ("an unrelated ### heading stays with the section it follows", "noise" in s["Companies"] and "noise" not in s["People"]),
        ("no warnings on a well-formed set", w == []),
    ]
    s2, w2 = section_slices("## Evidence Set\n### The Frame\n- r\n#### DAYTONA\n- d\n")
    checks.append(("missing heading -> whole set + note + warning", "#### DAYTONA" in s2["Companies"]
                   and s2["Companies"].startswith("> Section heading missing") and len(w2) == 5))
    for name, okv in checks:
        print(("  ✓ " if okv else "  ✗ ") + name)
    print(f"selftest: {sum(v for _, v in checks)}/{len(checks)} pass")
    return all(v for _, v in checks)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--evidence")
    ap.add_argument("--out-dir")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return 0 if selftest() else 1
    if not (a.evidence and a.out_dir):
        ap.error("--evidence and --out-dir are required (or --selftest)")
    s, warn = section_slices(open(a.evidence, encoding="utf-8").read())
    os.makedirs(a.out_dir, exist_ok=True)
    for n, name in enumerate([nm for nm, _ in SECTIONS], 1):
        body = s[name]
        fn = os.path.join(a.out_dir, f"{n:02d}-{re.sub(r'[^a-z]+', '-', name.lower()).strip('-')}.md")
        with open(fn, "w", encoding="utf-8") as f:
            f.write(body + "\n")
        print(f"{fn}  {len(body)} chars")
    for w in warn:
        print(w, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
