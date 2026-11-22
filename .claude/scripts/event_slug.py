#!/usr/bin/env python3
"""event_slug — the ONE event-title -> slug function (YED-498).

Used by the event claim (.claude/hooks/event-claim.py), the Step 1.7a usage sidecar (retrieve.py) and the Step 4.2b
sidecar check (substrate.py stage-research). Before this, event-claim and substrate each had their own slugger and
they disagreed on `&` and on length, and the parent hand-typed the sidecar's event slug: on 2026-11-22 it typed the
shorter claim slug and usage was NOT LOGGED.

Rules (only what is unambiguous): lower-case, `&` -> `and` (two people typing one event name differ there), every
other non-alphanumeric run -> `-`, trimmed, capped at 80 characters. No stopword stripping or fuzzy matching: a false
collision locks a legitimate run, which is worse than the miss it prevents.

  python3 .claude/scripts/event_slug.py "<title>"     prints the slug
  python3 .claude/scripts/event_slug.py --selftest

Stdlib only, no I/O: the hook imports it on every claim.
"""
from __future__ import annotations

import re
import sys

MAX_LEN = 80


def event_slug(s: str | None) -> str:
    """'Madison Avenue: ... Plug & Play VC and Base44' -> 'madison-avenue-...-plug-and-play-vc-and-base44'."""
    s = (s or "").lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:MAX_LEN].strip("-")


def selftest() -> bool:
    t = "Madison Avenue: The Media and Advertising Hackathon: Powered by Plug & Play VC and Base44"
    checks = [
        ("basic", event_slug("The Shortlist: September Showcase") == "the-shortlist-september-showcase"),
        ("& -> and", event_slug("Plug & Play") == event_slug("Plug and Play") == "plug-and-play"),
        ("capped at 80, no trailing dash", len(event_slug(t)) <= MAX_LEN and not event_slug(t).endswith("-")),
        ("idempotent", event_slug(event_slug(t)) == event_slug(t)),
        ("None and empty", event_slug(None) == "" and event_slug("  ") == ""),
    ]
    for name, ok in checks:
        print(("  ✓ " if ok else "  ✗ ") + name)
    print(f"selftest: {sum(v for _, v in checks)}/{len(checks)} pass")
    return all(v for _, v in checks)


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        sys.exit(0 if selftest() else 1)
    print(event_slug(" ".join(sys.argv[1:])))
