#!/usr/bin/env python3
"""test_field_presence.py — YED-257 field-presence check (E-09, offline, stdlib-only).

Asserts that the interview-prep-dossier skill defines the seven commercial-depth fields and the
"Likely Rounds and Questions" section, and that the synthetic fixture renders every one of them —
including the honest-gap comp-band behaviour and a comp_gate verdict that cites (never restates)
the gate. Also runs the privacy grep gates: the gitignored private-input filenames and any PII
must never appear inside fixture files.

Run:  python3 .claude/skills/interview-prep-dossier/fixtures/test_field_presence.py
Exit 0 = all pass; exit 1 = any failure printed with its name.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_MD = HERE.parent / "SKILL.md"
FIXTURE_MD = HERE / "fixture-dossier.md"

SEVEN_FIELDS = [
    "Growth stage + headcount band",
    "GTM motion",
    "GTM-engineering function",
    "CRM of record + named stack",
    "Leadership metric",
    "Leadership AI posture",
    "Comp band",
]

GITIGNORED_INPUTS = ["me-model.md", "target-companies.md"]

EMAIL_RX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RX = re.compile(r"(?<!\w)(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}(?!\w)")

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    if not ok:
        failures.append(f"{name}{(' — ' + detail) if detail else ''}")


def main() -> int:
    skill = SKILL_MD.read_text(encoding="utf-8")
    fixture = FIXTURE_MD.read_text(encoding="utf-8")
    fixture_lower = fixture.lower()

    # --- SKILL.md: the seven fields + the Likely Rounds section are defined -------------------
    for field in SEVEN_FIELDS:
        check(f"SKILL.md defines field: {field}", field in skill)
    check("SKILL.md defines 'Likely Rounds and Questions' section",
          "8. **Likely Rounds and Questions**" in skill)
    check("SKILL.md comp-band rule cites comp_gate.py", "comp_gate.py" in skill)
    check("SKILL.md comp-band rule says the gate is never the band's source",
          "never the band's source" in skill)

    # --- Fixture: renders every field ----------------------------------------------------------
    for field in SEVEN_FIELDS:
        check(f"fixture renders field: {field}", field.lower() in fixture_lower)
    check("fixture renders 'Likely Rounds and Questions' section",
          "Likely Rounds and Questions" in fixture)

    # --- Comp band: range + source + gate verdict cited, not restated --------------------------
    check("fixture comp band shows a range", re.search(r"\$\d{2,3}[Kk]", fixture) is not None)
    check("fixture comp band names its source", "sourced from" in fixture_lower)
    check("fixture cites the comp gate invocation", "comp_gate.py --text" in fixture)
    check("fixture shows the gate verdict", '"verdict"' in fixture)
    check("fixture states the gate is not restated here", "not restated here" in fixture_lower)

    # --- Honest-gap behaviour -------------------------------------------------------------------
    check("fixture demonstrates honest-gap comp behaviour", "honest gap" in fixture_lower)

    # --- Client-name hygiene (E-09 addition 2) ---------------------------------------------------
    check("fixture carries a 'Key accounts' logo line", "**Key accounts:**" in fixture)

    # --- Privacy grep gates -----------------------------------------------------------------------
    for name in GITIGNORED_INPUTS:
        check(f"fixture never names gitignored input {name}", name not in fixture_lower)
    check("fixture contains no email addresses", EMAIL_RX.search(fixture) is None)
    check("fixture contains no phone numbers", PHONE_RX.search(fixture) is None)

    print("field-presence checks:")
    for line in failures:
        print(f"  FAIL {line}")
    print(f"{len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
