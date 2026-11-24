#!/usr/bin/env python3
"""public_tiers — ADR-16 Decision 2 in code: an `email_signal` claim never reaches public output (YED-459).

The one place that says which provenance tiers are private by construction. Every reader that builds output which
can become public (the Monday Market Brief today) uses BOTH layers, and each layer is tested alone
(test_adr16_public_tiers.py), because a flaw in one layer of a privacy control is a defect even when the other
would catch it:

  server   PUBLIC_TIER_FILTER goes on every PostgREST GET of `claim`, so the rows never leave the database
  client   assert_public(rows, where) fails closed if a row of an excluded tier (or a row with no tier at all)
           arrives anyway: the caller's section degrades to "no data", it never renders the row

Private readers whose text can be passed on into drafting (retrieve.py's Prior-Context Pack, the Deep Read source
index) keep the claim but mark it with private_tag(tier): `[private: email_signal]`. output-evaluator (mode source)
fails any public line that traces to a tagged line or to an email_signal claim (reason "ADR-16: email_signal never
public").

Pure: no network, no writes. Changing the set is an ADR change (ADR-16), not an edit here.
"""
from __future__ import annotations

PUBLIC_EXCLUDED_TIERS = frozenset({"email_signal"})
# PostgREST: provenance_tier is NOT NULL (migration 0009), so not.in drops nothing but the excluded tiers.
PUBLIC_TIER_FILTER = "provenance_tier=not.in.(" + ",".join(sorted(PUBLIC_EXCLUDED_TIERS)) + ")"
ADR16_REASON = "ADR-16: email_signal never public"


class PublicTierViolation(RuntimeError):
    """A row of a private-by-construction tier reached a public-bound reader. The message names the reader and the
    tier, never the row's text."""


def norm_tier(tier) -> str:
    """Ledger rows write `email-signal`, the spine writes `email_signal`; both mean the same tier."""
    return str(tier or "").strip().lower().replace("-", "_")


def is_public_tier(tier) -> bool:
    return norm_tier(tier) not in PUBLIC_EXCLUDED_TIERS


def assert_public(rows, where: str) -> list:
    """Client-side layer. Returns rows unchanged, or raises PublicTierViolation. A row without provenance_tier fails
    too: a reader that forgot to select the column cannot prove the row is public."""
    rows = list(rows or [])
    for r in rows:
        if not isinstance(r, dict) or "provenance_tier" not in r:
            raise PublicTierViolation(f"{where}: claim row without provenance_tier; cannot prove it public ({ADR16_REASON})")
        if not is_public_tier(r["provenance_tier"]):
            raise PublicTierViolation(f"{where}: a {norm_tier(r['provenance_tier'])} claim reached a public reader "
                                      f"({ADR16_REASON})")
    return rows


def private_tag(tier) -> str:
    """' [private: email_signal]' for an excluded tier, '' otherwise. Appended to a rendered line on private paths."""
    t = norm_tier(tier)
    return f" [private: {t}]" if t in PUBLIC_EXCLUDED_TIERS else ""
