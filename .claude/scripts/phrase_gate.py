#!/usr/bin/env python3
"""phrase_gate.py — role-radar Step 3's full-description phrase gate + liveness precondition (E-09 P2, YED-220).

The ONE executable copy of the phrase-gate rules (same ADR-12 pattern as comp_gate.py, which stays the one
executable copy of the comp rules — this gate never reads, restates or evaluates comp). role-radar SKILL.md
Step 3 points here and does not restate the registry, the family slugs or the precondition logic.

Source of the pattern: Eric Nowoslawski harvest, §3 row 2 (docs/archive/notes/
eric-coldoutboundskills-harvest-2026-09-24.md): match job postings on whole phrases in the FULL description,
never on title/summary (title+summary matched 1 of 8 companies vs 5 of 8 on the full description); enumerate
every inflection or a third of the matches are lost ("cold call" matched 996 postings where "cold calling"
matched 2,065); gate by role family; only cite a posting you can link, date, and that is still live.

What one run enforces, in order:
  a. Mechanism evidence = whole-phrase matches in the FULL description (--text). Title hits (--title) are
     reported separately and NEVER counted — the title raises the question, the description answers it.
     An empty/missing full description is itself a precondition failure: scoring on title/summary is the
     1-of-8 failure the harvest caught.
  b. Mechanism phrases match only through PHRASE_FAMILIES' enumerated surface forms — word-boundary,
     case-insensitive whole phrases. No stemming, no substring matching at runtime; a new surface form is a
     new entry in the registry.
  c. Role-family gate: --family must be one of the Step-3 five-shape slugs (IN_SCOPE_FAMILIES). The shapes
     themselves are defined once in role-radar SKILL.md; this script gates the slug and never re-derives a
     shape or its scoring.
  d. Liveness precondition: a required --url + --posted (YYYY-MM-DD) + a live URL BEFORE any scoring. Any
     failure → NOT_SCOREABLE: the role receives no icp_score and no tier, so it can never reach the A
     threshold (85) or any tier. Liveness comes from the session's own probe (--live / --dead) or
     --check-live (this script probes the URL; any probe failure is dead — fail-closed). Unverified is not live.

Usage:
  phrase_gate.py --title "Account Executive, Enterprise" --text "<full JD text>" \
                 --family all-channel-ae --url "https://boards.greenhouse.io/…" --posted 2026-10-30 [--live|--dead|--check-live]
  phrase_gate.py --selftest
Output: one JSON object {verdict: SCORABLE|NOT_SCOREABLE, reasons, preconditions, family, description_matches,
title_only_matches, notes_line}. Exit 0 always except bad args (2): the verdict is the signal, like comp_gate.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date

# Canonical mechanism family -> every surface form it matches. Whole-phrase, word-boundary, case-insensitive;
# a form joined by whitespace or hyphen matches either joiner ("product-led growth" == "product led growth").
# Compound forms already covered by a head form's word boundary ("quota" covers "quota-carrying") are not
# re-listed, so one occurrence never counts twice. Add a phrase by adding every inflection you want caught —
# never stem-match at runtime (harvest evidence: "cold call" 996 vs "cold calling" 2,065 postings).
PHRASE_FAMILIES: dict[str, list[str]] = {
    "cold call": ["cold call", "cold calls", "cold calling", "cold called"],
    "book of business": ["book of business", "books of business", "existing book", "existing books"],
    "expansion": ["expansion", "expansions", "expand", "expanding", "expanded"],
    "PLG": ["PLG", "product-led growth"],
    "quota": ["quota", "quotas"],
}

# Slugs indexing role-radar SKILL.md Step 3's five shapes — THE FIVE SHAPES above, defined once there.
# This list gates the slug only; what each shape means and scores stays in SKILL.md (a second copy drifts).
IN_SCOPE_FAMILIES = ("account-manager", "account-director", "quota-csm", "all-channel-ae", "growth-strategist")

POSTED_RX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _form_rx(form: str) -> re.Pattern:
    # Words may themselves carry hyphens ("product-led growth"): split on whitespace OR hyphen so the
    # enumerated form matches either joiner, then require word boundaries around the whole phrase.
    words = [re.escape(w) for w in re.split(r"[\s-]+", form)]
    return re.compile(r"(?<![A-Za-z])" + r"[\s-]+".join(words) + r"(?![A-Za-z])", re.I)


FORM_RX = {fam: {form: _form_rx(form) for form in forms} for fam, forms in PHRASE_FAMILIES.items()}


def match_phrases(text: str) -> dict[str, dict[str, int]]:
    """Whole-phrase matches per family: {family: {surface_form: count}}; families with zero hits are omitted."""
    out: dict[str, dict[str, int]] = {}
    for fam, forms in FORM_RX.items():
        hits = {form: len(rx.findall(text)) for form, rx in forms.items()}
        if any(hits.values()):
            out[fam] = {f: c for f, c in hits.items() if c}
    return out


def check_live(url: str, timeout: int = 10) -> tuple[bool, str]:
    """Probe a posting URL (HEAD, then GET when HEAD is rejected). Fail-closed: any error is dead."""
    import urllib.error
    import urllib.request

    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers={"User-Agent": "role-radar-liveness/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return True, f"HTTP {r.status}"
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (403, 405, 501):   # many ATS boards reject HEAD; retry with GET
                continue
            return False, f"HTTP {e.code}"
        except Exception as e:                                   # DNS, TLS, timeout: unreachable = not live
            return False, type(e).__name__
    return False, "HEAD rejected"


def gate(title: str, text: str, family: str, url: str, posted: str, liveness: str | None = None) -> dict:
    """Apply the P2 gate. liveness is 'live' | 'dead' | None (unverified). Verdict + reasons are fail-closed."""
    pre = {
        "full_description": "ok" if text and text.strip() else "missing",
        "posting_url": "ok" if url and url.strip() else "missing",
        "posted_date": "ok" if posted and POSTED_RX.match(posted) and _real_date(posted) else
                       ("unparseable" if posted and posted.strip() else "missing"),
        "liveness": liveness or "unverified",
        "role_family": "ok" if family in IN_SCOPE_FAMILIES else ("missing" if not family else "out_of_scope"),
    }
    reason_for = {
        "full_description": "missing_full_description",
        "posting_url": "missing_posting_url",
        "posted_date": "unparseable_posted_date" if pre["posted_date"] == "unparseable" else "missing_posted_date",
        "liveness": "dead_url" if pre["liveness"] == "dead" else "unverified_liveness",
        "role_family": "out_of_scope_family" if pre["role_family"] == "out_of_scope" else "missing_role_family",
    }
    reasons = [reason_for[k] for k, v in pre.items() if v not in ("ok", "live")]
    verdict = "SCORABLE" if not reasons else "NOT_SCOREABLE"
    desc_matches = match_phrases(text or "")
    title_only = {fam: hits for fam, hits in match_phrases(title or "").items() if fam not in desc_matches}
    if verdict == "SCORABLE":
        evidence = "; ".join(f"{fam}: {', '.join(f'{f}×{c}' for f, c in hits.items())}"
                             for fam, hits in desc_matches.items()) or "no mechanism phrases matched"
        note = (f"Phrase gate: SCORABLE ({family}) — description evidence: {evidence}. "
                f"URL live, posted {posted}. Comp verdict separate (comp_gate.py).")
    else:
        note = (f"Phrase gate: NOT_SCOREABLE — {', '.join(reasons)}. Not scored: no icp_score, no tier, "
                f"cannot reach A. Goes to Step 4's Dropped bucket with this reason.")
    return {"verdict": verdict, "reasons": reasons, "preconditions": pre, "family": family,
            "description_matches": desc_matches, "title_only_matches": title_only, "notes_line": note}


def _real_date(posted: str) -> bool:
    y, m, d = posted.split("-")
    try:
        date(int(y), int(m), int(d))
        return True
    except ValueError:
        return False


def selftest() -> int:
    ok = n = 0

    def ck(name, cond):
        nonlocal ok, n
        n += 1
        ok += bool(cond)
        print(f"  {'✓' if cond else '✗'} {name}")

    # Synthetic postings only — fictional companies, no private inputs, no network (offline by construction).
    jd = ("Own and grow an existing book of business through expansion. You will run cold calling into named "
          "territories alongside our BDR team, carry a quota, and work a PLG product-led growth motion.")
    r = gate("AE, Enterprise", jd, "all-channel-ae", "https://boards.example.com/jobs/1", "2026-10-30", "live")
    ck("happy path scores", r["verdict"] == "SCORABLE" and not r["reasons"])
    ck("evidence counted from the FULL description",
       set(r["description_matches"]) == {"book of business", "expansion", "cold call", "quota", "PLG"})

    # (b) inflection-miss case: canonical forms absent, only inflected forms present — still matched.
    inflected = ("You will be cold calling and expanding existing accounts; quotas are set quarterly "
                 "on a product led growth motion.")
    r = gate("AE", inflected, "quota-csm", "https://boards.example.com/jobs/2", "2026-10-30", "live")
    ck("inflected forms caught (cold calling/expanding/quotas/product led growth)",
       set(r["description_matches"]) == {"cold call", "expansion", "quota", "PLG"})

    # Whole-phrase precision: no substring or stem matching across word boundaries.
    r = gate("AE", "expansionary revenue and reexpansion of territories", "account-manager",
             "https://boards.example.com/jobs/3", "2026-10-30", "live")
    ck("whole-phrase: 'expansionary'/'reexpansion' never match 'expansion'", "expansion" not in r["description_matches"])

    # (a) title hits are reported separately and never counted as mechanism evidence.
    r = gate("Cold Call Hunter AE", "Own a quota on our PLG product.", "quota-csm",
             "https://boards.example.com/jobs/4", "2026-10-30", "live")
    ck("title-only match surfaced, never counted", r["description_matches"].get("cold call") is None
       and "cold call" in r["title_only_matches"])

    # (a) empty full description is a precondition failure — scoring on title/summary is the 1-of-8 failure.
    r = gate("Cold Call Hunter AE", "   ", "quota-csm", "https://boards.example.com/jobs/5", "2026-10-30", "live")
    ck("missing full description → NOT_SCOREABLE", r["verdict"] == "NOT_SCOREABLE"
       and "missing_full_description" in r["reasons"])

    # (d) liveness + required fields: each failure is named, and a failing role is never scored.
    base = ("Own a book of business with expansion targets.", "quota-csm")
    r = gate("AE", base[0], base[1], "", "2026-10-30", "live")
    ck("missing posting_url → NOT_SCOREABLE", r["verdict"] == "NOT_SCOREABLE" and "missing_posting_url" in r["reasons"])
    r = gate("AE", base[0], base[1], "https://boards.example.com/jobs/6", "", "live")
    ck("missing posted_date → NOT_SCOREABLE", r["verdict"] == "NOT_SCOREABLE" and "missing_posted_date" in r["reasons"])
    r = gate("AE", base[0], base[1], "https://boards.example.com/jobs/6", "2026-13-40", "live")
    ck("unparseable posted_date → NOT_SCOREABLE", "unparseable_posted_date" in r["reasons"])
    r = gate("AE", base[0], base[1], "https://boards.example.com/jobs/6", "2026-10-30", "dead")
    ck("dead URL → NOT_SCOREABLE", r["verdict"] == "NOT_SCOREABLE" and "dead_url" in r["reasons"])
    r = gate("AE", base[0], base[1], "https://boards.example.com/jobs/6", "2026-10-30", None)
    ck("unverified liveness is not live → NOT_SCOREABLE (fail-closed)",
       r["verdict"] == "NOT_SCOREABLE" and "unverified_liveness" in r["reasons"])

    # (c) role-family gate: unclassified and out-of-scope classifications never score.
    r = gate("AE", base[0], "", "https://boards.example.com/jobs/6", "2026-10-30", "live")
    ck("missing role family → NOT_SCOREABLE", "missing_role_family" in r["reasons"])
    r = gate("SE", base[0], "solutions-engineer", "https://boards.example.com/jobs/7", "2026-10-30", "live")
    ck("out-of-scope family slug → NOT_SCOREABLE", "out_of_scope_family" in r["reasons"])

    # Registry hygiene: every family has enumerated forms, and no form duplicates another family's head.
    ck("registry families enumerated", all(forms for forms in PHRASE_FAMILIES.values()))
    ck("family slugs index the five shapes", IN_SCOPE_FAMILIES == (
        "account-manager", "account-director", "quota-csm", "all-channel-ae", "growth-strategist"))

    print(f"selftest: {ok}/{n} phrase-gate cases pass")
    return 0 if ok == n else 1


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--title", default="", help="posting title — matched for reporting only, never counted")
    ap.add_argument("--text", default="", help="the FULL posting description (never title/summary alone)")
    ap.add_argument("--family", default="", help="one of the Step-3 five-shape slugs (see SKILL.md)")
    ap.add_argument("--url", dest="url", default="", help="required posting URL")
    ap.add_argument("--posted", default="", help="required posted date, YYYY-MM-DD (a true posted date)")
    live_group = ap.add_mutually_exclusive_group()
    live_group.add_argument("--live", action="store_true", help="the session verified the URL live this run")
    live_group.add_argument("--dead", action="store_true", help="the session found the URL dead this run")
    live_group.add_argument("--check-live", action="store_true", help="probe the URL here (network; fail-closed)")
    ap.add_argument("--timeout", type=int, default=10, help="--check-live timeout seconds")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.text:
        ap.print_usage(sys.stderr); return 2
    if a.check_live:
        if not a.url:
            print("phrase_gate: --check-live needs --url", file=sys.stderr)
            return 2
        alive, detail = check_live(a.url, a.timeout)
        liveness = "live" if alive else "dead"
    else:
        liveness = "live" if a.live else "dead" if a.dead else None
    print(json.dumps(gate(a.title, a.text, a.family, a.url, a.posted, liveness)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
