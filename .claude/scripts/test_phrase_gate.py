#!/usr/bin/env python3
"""test_phrase_gate.py — offline regression for phrase_gate.py (E-09 P2, YED-220). Free; fictional companies only.

Fixture postings pin the four gate rules: full-description matching with enumerated inflections (the harvest's
"cold call 996 vs cold calling 2,065" miss), title-only matches never counted, role-family gating, and the
liveness precondition (no URL / no posted date / dead URL → the role is never scored). Also pins the privacy
grep gate: the gitignored private-input filenames never appear inside fixture data.

Usage: python3 .claude/scripts/test_phrase_gate.py [path/to/phrase_gate.py] [--selftest]
"""
import argparse
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# Fictional postings — every company and JD below is synthetic; nothing here is a real posting or a
# private input (fixture contract: fictional people/companies; private inputs are read by path at run time).
P_CLEAN = {   # inflection-miss case: canonical forms absent, only inflected forms present — still matched
    "title": "Enterprise Account Executive",
    "company": "Meridian Analytics (fictional)",
    "description": "You will be cold calling into named territories and expanding an existing book of "
                   "business. Quotas are set quarterly on a product led growth motion with BDR support.",
    "family": "all-channel-ae", "url": "https://boards.example.com/meridian/1234",
    "posted": "2026-10-29", "liveness": "live",
}
P_TITLE_ONLY = {   # the title raises the question; the description answers it — and here it does not
    "title": "Cold Call Hunter AE",
    "company": "Harborview Robotics (fictional)",
    "description": "Own a personal quota across enterprise accounts with BDR and inbound support.",
    "family": "quota-csm", "url": "https://boards.example.com/harborview/77",
    "posted": "2026-10-28", "liveness": "live",
}
P_DEAD = {   # dead-URL case: a complete, in-family posting whose URL no longer resolves is never scored
    "title": "Account Manager",
    "company": "Cobalt Fixtures Inc (fictional)",
    "description": "Own and expand an existing book of business; expansion targets against a named account list.",
    "family": "account-manager", "url": "https://boards.example.com/cobalt/404",
    "posted": "2026-10-20", "liveness": "dead",
}
P_NO_DATE = {   # missing posted_date case: Greenhouse-style row with no true posted date is never scored
    "title": "Account Director",
    "company": "Harborview Robotics (fictional)",
    "description": "Own a book of business with expansion targets alongside two BDRs.",
    "family": "account-director", "url": "https://boards.example.com/harborview/88",
    "posted": "", "liveness": "live",
}
P_NO_URL = dict(P_NO_DATE, url="", posted="2026-10-27")
P_UNVERIFIED = dict(P_CLEAN, liveness=None)          # no probe this run: unverified is not live (fail-closed)
P_NO_FAMILY = dict(P_CLEAN, family="")
P_OUT_FAMILY = dict(P_CLEAN, family="solutions-engineer")
P_STEM_TRAP = dict(P_CLEAN, description="Expansionary revenue and reexpansion of territories only.")  # whole-phrase precision


def load_pg(path):
    spec = importlib.util.spec_from_file_location("phrase_gate_under_test", path)
    pg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pg)
    return pg


def run(pg, script_path):
    ok = n = 0

    def ck(name, cond):
        nonlocal ok, n
        n += 1
        ok += bool(cond)
        print(("  ✓ " if cond else "  ✗ ") + name)

    def gated(p, **over):
        args = {**p, **over}
        return pg.gate(args.get("title", ""), args["description"], args.get("family", ""),
                       args["url"], args["posted"], args.get("liveness"))

    # (b) inflection-miss: every family matches on inflected forms alone; canonical strings never appear.
    r = gated(P_CLEAN)
    families = set(r["description_matches"])
    ck("inflection-miss: all families matched on inflected forms",
       families == {"cold call", "book of business", "expansion", "quota", "PLG"})
    ck("inflection-miss: matched surface forms are the inflections",
       r["description_matches"]["cold call"] == {"cold calling": 1}
       and "expand" not in r["description_matches"]["expansion"]
       and r["description_matches"]["quota"] == {"quotas": 1}
       and r["description_matches"]["PLG"] == {"product-led growth": 1})
    ck("clean posting with URL + posted date + live → SCORABLE", r["verdict"] == "SCORABLE" and not r["reasons"])
    ck("notes_line is a ready Notes line", r["notes_line"].startswith("Phrase gate: SCORABLE"))

    # (a) title-only hits are surfaced separately and never counted as mechanism evidence.
    r = gated(P_TITLE_ONLY)
    ck("title-only match never counted in the description evidence",
       "cold call" not in r["description_matches"] and "cold call" in r["title_only_matches"])
    ck("title-only posting still scores on its own description evidence", r["verdict"] == "SCORABLE")

    # (d) dead URL → NOT_SCOREABLE before any scoring.
    r = gated(P_DEAD)
    ck("dead-URL case: role not scored", r["verdict"] == "NOT_SCOREABLE" and "dead_url" in r["reasons"])
    ck("dead-URL case: notes line says not scored", "Not scored" in r["notes_line"])

    # (d) missing posted_date → NOT_SCOREABLE.
    r = gated(P_NO_DATE)
    ck("missing posted_date case: role not scored",
       r["verdict"] == "NOT_SCOREABLE" and "missing_posted_date" in r["reasons"])

    # (d) missing posting_url and unverified liveness (fail-closed) → NOT_SCOREABLE.
    r = gated(P_NO_URL)
    ck("missing posting_url case: role not scored",
       r["verdict"] == "NOT_SCOREABLE" and "missing_posting_url" in r["reasons"])
    r = gated(P_UNVERIFIED)
    ck("unverified liveness is not live: role not scored",
       r["verdict"] == "NOT_SCOREABLE" and "unverified_liveness" in r["reasons"])

    # (c) role-family gating: unclassified and out-of-scope slugs never score.
    r = gated(P_NO_FAMILY)
    ck("unclassified role family: role not scored",
       r["verdict"] == "NOT_SCOREABLE" and "missing_role_family" in r["reasons"])
    r = gated(P_OUT_FAMILY)
    ck("out-of-scope family slug: role not scored",
       r["verdict"] == "NOT_SCOREABLE" and "out_of_scope_family" in r["reasons"])

    # Drift guard (PR #244 review): every IN_SCOPE_FAMILIES slug must be named in role-radar's SKILL.md
    # (THE FIVE SHAPES carries each shape's slug). The script gates the slug; the skill defines the shape —
    # if either side renames, this fails loudly instead of the run-time guess ending in a silent Drop.
    skill_md = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(script_path)),
                                             "..", "skills", "role-radar", "SKILL.md"))
    try:
        with open(skill_md, encoding="utf-8") as fh:
            skill_text = fh.read()
    except OSError as exc:
        ck(f"role-radar SKILL.md readable at {skill_md}", False)
        print(f"    ({exc})")
    else:
        ck("every gate slug is named in role-radar SKILL.md (no drift)",
           all(slug in skill_text for slug in pg.IN_SCOPE_FAMILIES))

    # Whole-phrase precision: stems and compounds across word boundaries never match.
    r = gated(P_STEM_TRAP)
    ck("whole-phrase precision: 'expansionary'/'reexpansion' never match",
       "expansion" not in r["description_matches"] and r["verdict"] == "SCORABLE")

    # CLI path: one JSON verdict on stdout, exit 0 (the verdict is the signal, like comp_gate).
    out = io_capture(lambda: pg.main(["--title", P_CLEAN["title"], "--text", P_CLEAN["description"],
                                      "--family", P_CLEAN["family"], "--url", P_CLEAN["url"],
                                      "--posted", P_CLEAN["posted"], "--live"]))
    verdict = json.loads(out)["verdict"]
    ck("CLI run emits the JSON verdict", verdict == "SCORABLE")

    # Privacy grep gate: the gitignored private-input filenames never appear inside fixture data.
    banned = ("me-model", "target-companies")
    fixture_blob = json.dumps([P_CLEAN, P_TITLE_ONLY, P_DEAD, P_NO_DATE, P_NO_URL, P_UNVERIFIED,
                               P_NO_FAMILY, P_OUT_FAMILY, P_STEM_TRAP])
    ck("privacy grep gate: no gitignored input filename inside fixtures",
       not any(b in fixture_blob.lower() for b in banned))

    # Registry hygiene: every family enumerates at least one non-empty surface form.
    ck("registry hygiene: every family has enumerated forms",
       all(forms and all(f.strip() for f in forms) for forms in pg.PHRASE_FAMILIES.values()))

    print(f"tests: {ok}/{n} pass")
    return 0 if ok == n else 1


def io_capture(fn):
    import io
    buf, real = io.StringIO(), sys.stdout
    sys.stdout = buf
    try:
        fn()
    finally:
        sys.stdout = real
    return buf.getvalue()


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("script", nargs="?", default=os.path.join(HERE, "phrase_gate.py"),
                    help="path to phrase_gate.py (default: alongside this test)")
    ap.add_argument("--selftest", action="store_true", help="accepted for the CI selftests loop; runs the suite")
    a = ap.parse_args(argv)
    return run(load_pg(a.script), a.script)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
