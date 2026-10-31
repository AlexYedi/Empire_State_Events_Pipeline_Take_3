#!/usr/bin/env python3
"""test_render_contract.py — YED-258 PR B render-contract check (E-09, offline, stdlib-only).

Asserts that the tailor-resume synthetic fixture still satisfies the whole render contract
the way CI runs it: schema validation, the seven locked content rules, reading order, the
posting-tailored reweighting (reorder-only), the PDF reading-order gate, and the default
me-model mapping documented in SKILL.md. Also runs the privacy grep gates: the gitignored
private-input filenames and any PII must never appear inside fixture files.

Run:  python3 .claude/skills/tailor-resume/fixtures/test_render_contract.py
Exit 0 = all pass; exit 1 = any failure printed with its name.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_MD = HERE.parent / "SKILL.md"
FIXTURE_JSON = HERE / "resume-input-fixture.json"
SCRIPTS = HERE.parent.parent.parent / "scripts"

sys.path.insert(0, str(SCRIPTS))
import render_resume as rr  # noqa: E402  (module-level defs only; no side effects)

GITIGNORED_INPUTS = ["me-model.md", "target-companies.md"]

EMAIL_RX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RX = re.compile(r"(?<!\w)(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}(?!\w)")

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    if not ok:
        failures.append(f"{name}{(' — ' + detail) if detail else ''}")


def main() -> int:
    fixture_text = FIXTURE_JSON.read_text(encoding="utf-8")
    me = json.loads(fixture_text)
    skill = SKILL_MD.read_text(encoding="utf-8")
    html = rr.build_resume_html(me)

    # Schema + locked rules + reading order on the committed fixture.
    check("fixture validates against the resume-input schema",
          rr.validate_resume_input(me) == [])
    check("fixture passes every locked content rule",
          rr.check_content_rules(html, fixture_text) == [],
          str(rr.check_content_rules(html, fixture_text)))
    check("fixture keeps the reading order", rr.check_reading_order(html) == [])

    # Rule 4 shape: no bare GitHub profile among the fixture proof links.
    check("fixture proof links are never the bare GitHub profile",
          all(not re.fullmatch(r"https?://github\.com/[^/\s]+/?", u) for u in me["proof_links"]))

    # Default mapping is documented in the SKILL.md (PR B states it for Alex's review).
    check("SKILL.md states the default mapping as a default (not settled)",
          "default mapping" in skill.lower() and "PR B default" in skill)
    for needle in ("quota-carrying post-sales", "proof of account growth", "logo list"):
        check(f"SKILL.md mapping covers {needle!r}", needle in skill)

    # Reweighting: reorder-only, deterministic, no-op on a disjoint JD.
    jd = "Own analytics pilots and multi-team rollout; unstick a stalled pilot into a rollout."
    reweighted = rr.reweight_for_jd(me, jd)
    check("reweight promotes the JD-relevant role first",
          reweighted["roles"][0]["company"] == me["roles"][1]["company"])
    texts_before = sorted(b["text"] for r in me["roles"] for b in r["bullets"])
    texts_after = sorted(b["text"] for r in reweighted["roles"] for b in r["bullets"])
    check("reweight never rewrites a word", texts_before == texts_after)
    check("reweight is a no-op on a disjoint JD",
          rr.reweight_for_jd(me, "xyzzy plugh zork")["roles"] == me["roles"])

    # PDF gate: pure reading-order check over extracted text.
    good = f'{me["name"]} {me["positioning"]} ' + " ".join(r["title"] for r in me["roles"]) \
        + " Key accounts: trailing section"
    scrambled = 'Key accounts first. ' + f'{me["name"]} {me["positioning"]} ' \
        + " ".join(r["title"] for r in me["roles"])
    check("PDF reading-order check passes ordered text",
          rr.pdf_reading_order_errors(good, me) == [])
    check("PDF reading-order check catches scrambled roles",
          rr.pdf_reading_order_errors(scrambled, me) != [])

    # Privacy grep gates over every file in this fixtures directory.
    for path in HERE.iterdir():
        if not path.is_file() or path.name == Path(__file__).name:
            continue
        blob = path.read_text(encoding="utf-8", errors="replace")
        low = blob.lower()
        for needle in GITIGNORED_INPUTS:
            check(f"{path.name}: gitignored input {needle!r} absent", needle not in low)
        check(f"{path.name}: no email", not EMAIL_RX.search(blob))
        check(f"{path.name}: no phone", not PHONE_RX.search(blob))

    if failures:
        for f in failures:
            print(f"FAIL {f}")
        print(f"fixture-test: {len(failures)} failure(s)")
        return 1
    print("fixture-test: all render-contract cases pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
