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
      writes one file per section (01-the-frame.md ... 05-cross-event-threads.md) and prints sizes;
      exit 2 if the five exact '### <Section>' headings (written by the fanout workflow, YED-498) are not all there once
  python3 .claude/scripts/deep_read_slices.py --selftest

Pure text in, text out: no network, no writes outside --out-dir.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

SECTIONS = ["The Frame", "Primer / Landscape", "Companies", "People", "Cross-Event Threads"]
# YED-498: the event-research-fanout workflow writes these five headings in code, from five required synthesizer fields,
# so the split is exact. A missing heading means the Evidence Set did not come from the workflow (or was hand-edited):
# that is an error, never a silent whole-set fallback (the fallback hid a heading drift on 2026-11-22).
EMPTY = "(none researched)"
LEDGER_HEAD = re.compile(r"^##### Evidence Ledger — (.+?)\s*$")


class SliceError(ValueError):
    pass


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


def section_slices(evidence: str) -> dict[str, str]:
    """Split on the exact '### <Section>' headings. Raises SliceError if any of the five is missing or repeated.
    A section whose body is empty or EMPTY comes back as '' (the renderer skips it)."""
    lines = evidence.splitlines(keepends=True)
    starts = [(i, line[4:].strip()) for i, line in enumerate(lines) if line.startswith("### ") and line[4:].strip() in SECTIONS]
    names = [n for _, n in starts]
    missing = [n for n in SECTIONS if n not in names]
    dup = sorted({n for n in names if names.count(n) > 1})
    if missing or dup:
        raise SliceError(f"Evidence Set headings wrong: missing {missing or 'none'}, repeated {dup or 'none'}. "
                         "It must come from the event-research-fanout workflow, which writes the five headings in code.")
    out = {}
    for n, (i, name) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
        body = "".join(lines[i + 1:end]).strip()
        out[name] = "" if body in ("", EMPTY) else f"### {name}\n{body}"
    idx = source_index(evidence)
    if idx:
        out["The Frame"] = (out["The Frame"] or "### The Frame") + (
            "\n\n#### Sources available (every URL-carrying Evidence Ledger row in this event's Evidence Set; cite from these)\n"
            + "\n".join(idx))
    return {name: out[name] for name in SECTIONS}


def selftest() -> bool:
    ev = ("## Evidence Set\n### The Frame\n- Room: Acme hosts.\n### Primer / Landscape\n#### Topic: X\n"
          "##### Evidence Ledger — X\n- claim: X grew | tier: web-verified | source: Blog | url: https://x.example/a | date: 2026-11-01\n"
          "- claim: X grew | tier: web-verified | source: Blog | url: https://x.example/a | date: 2026-11-01\n"
          "### Companies\n##### Evidence Ledger — Acme\n- claim: Acme raised $4M | tier: web-verified | source: TC | url: https://tc.example/b | date: 2026-10-01\n"
          "- claim: private note | tier: email-signal | source: Gmail | url: n/a | date: 2026-10-02\n"
          "### Pattern signals\n- noise\n### People\n(none researched)\n### Cross-Event Threads\n- prior room\n")
    s = section_slices(ev)
    checks = [
        ("five slices in order", list(s) == SECTIONS),
        ("index: URL rows only, de-duplicated", source_index(ev) == [
            "- [X] X grew — Blog · 2026-11-01 · https://x.example/a",
            "- [Acme] Acme raised $4M — TC · 2026-10-01 · https://tc.example/b"]),
        ("Frame slice carries the index", "https://tc.example/b" in s["The Frame"] and "Sources available" in s["The Frame"]),
        ("an unrelated ### heading stays with the section it follows", "noise" in s["Companies"] and "noise" not in s["People"]),
        ("an empty section comes back empty", s["People"] == ""),
    ]
    def raises(text):
        try:
            section_slices(text)
        except SliceError:
            return True
        return False
    checks.append(("drifted heading ('### → Primer/Landscape') raises", raises(ev.replace("### Primer / Landscape", "### → Primer/Landscape"))))
    checks.append(("missing section raises", raises(ev.replace("### Cross-Event Threads\n", ""))))
    checks.append(("repeated section raises", raises(ev + "### People\n- again\n")))
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
    try:
        s = section_slices(open(a.evidence, encoding="utf-8").read())
    except SliceError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    os.makedirs(a.out_dir, exist_ok=True)
    for n, name in enumerate(SECTIONS, 1):
        body = s[name]
        fn = os.path.join(a.out_dir, f"{n:02d}-{re.sub(r'[^a-z]+', '-', name.lower()).strip('-')}.md")
        with open(fn, "w", encoding="utf-8") as f:
            f.write(body + "\n")
        print(f"{fn}  {len(body)} chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())
