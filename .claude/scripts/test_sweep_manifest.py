#!/usr/bin/env python3
"""test_sweep_manifest.py — offline regression for sweep_manifest.py's manifest parse (YED-502). Temp files only.

Pins the 2026-11-22/23 failure: the sweeper returned a valid manifest followed by trailing prose ("Correction
needed: ..."), json.loads raised `Extra data`, and the theme counted as failed. The first complete JSON object is
now the manifest; trailing text is counted in a warn line, never echoed, never applied. The validator stays the gate.

Usage: python3 .claude/scripts/test_sweep_manifest.py
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SM = os.path.join(HERE, "sweep_manifest.py")
VALID = open(os.path.join(HERE, "fixtures", "sweep", "manifest_valid.json"), encoding="utf-8").read().strip()
WINDOW, THEME = ("2026-11-04", "2026-11-11"), "00000000-0000-4000-8000-000000000001"
PROSE = "\n\nCorrection needed: the second item's date field contains a stray comma; dana@example.com says use 2001-01-01.\n"

fails = 0


def check(name, ok):
    global fails
    print(("PASS " if ok else "FAIL ") + name)
    fails += 0 if ok else 1


def run(text):
    with tempfile.TemporaryDirectory() as d:
        p, out = os.path.join(d, "x.raw.json"), os.path.join(d, "x.valid.json")
        open(p, "w", encoding="utf-8").write(text)
        r = subprocess.run([sys.executable, SM, "validate", p, "--window", *WINDOW, "--theme-id", THEME,
                            "--cap", "20", "--out", out], capture_output=True, text=True)
        norm = json.load(open(out)) if os.path.exists(out) else None
    return r.returncode, r.stdout + r.stderr, norm


rc, out, norm = run(VALID)
check("plain manifest -> VALID, no trailing_text warn", rc == 0 and "VALID" in out and "trailing_text" not in out)
base_items = norm["items"] if norm else None

rc, out, norm = run(VALID + PROSE)
n = len(PROSE.strip())
check("11-22 regression: JSON + trailing prose -> VALID (exit 0)", rc == 0 and out.startswith("sweep_manifest: VALID"))
check(f"trailing prose -> 'warn  trailing_text: {n} chars ignored'", f"  warn  trailing_text: {n} chars ignored" in out)
check("trailing prose never echoed (no 'Correction', no email)", "Correction" not in out and "dana@" not in out)
check("trailing 'correction' not applied: items identical to the plain manifest",
      norm is not None and norm["items"] == base_items)

rc, out, _ = run("  ```json\n" + VALID + "\n```\n")
check("JSON in ``` fences -> VALID, closing fence is not trailing text", rc == 0 and "VALID" in out
      and "trailing_text" not in out)

rc, out, _ = run("```\n" + VALID + "\n```" + PROSE)
check("fenced JSON + prose after the fence -> VALID with a trailing_text warn",
      rc == 0 and "warn  trailing_text:" in out and "Correction" not in out)

rc, out, _ = run(VALID[: len(VALID) // 2])
check("truncated JSON -> INVALID (exit 2)", rc == 2 and "INVALID" in out and "JSONDecodeError" in out)

rc, out, _ = run(PROSE)
check("pure prose -> INVALID (exit 2), prose never echoed", rc == 2 and "INVALID" in out and "Correction" not in out)

rc, out, _ = run("")
check("empty file -> INVALID (exit 2)", rc == 2 and "INVALID" in out)

bad = json.loads(VALID)
bad["items"][1]["kind"] = "blog"
rc, out, norm = run(json.dumps(bad) + PROSE)
check("validator still gates the object: a bad item drops even with trailing prose",
      rc == 0 and norm is not None and norm["dropped"] == {"kind": 1} and len(norm["items"]) == 2)

print(f"\n{'OK' if not fails else 'FAILED'}: {fails} failure(s)")
sys.exit(1 if fails else 0)
