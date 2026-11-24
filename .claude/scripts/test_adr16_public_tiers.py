#!/usr/bin/env python3
"""test_adr16_public_tiers.py — offline regression for ADR-16 Decision 2 (YED-459): email_signal never public.

Seeds ONE email_signal claim (fictional) into each reader's fixture and checks every layer ALONE, because a flaw in
one layer of a privacy control is a defect even when another layer would catch it:

  public   market_brief (Monday Market Brief)
    server  every `claim` GET carries public_tiers.PUBLIC_TIER_FILTER
    client  a stub that IGNORES the filter hands the email_signal row back anyway: the reader raises
            PublicTierViolation and the rendered brief does not count the row
    output  a stub that honours the filter: the brief's counts are the same as with no email_signal row at all
  private  retrieve.py Prior-Context Pack and deep_read_slices' Frame source index tag the line
           `[private: email_signal]`; other tiers are untagged
  mutation each layer's check is re-run with that layer removed (filter blanked, assert made a no-op, tag blanked)
           and must FAIL, so a test that cannot fail is caught
  evaluator the output-evaluator fixture (fixtures/adr16/) has a tagged brief line that the draft uses, and an expected
           verdict naming ADR-16; the agent itself is proven from a fresh session (command in expected.md)

No network, no writes outside a temp dir.

Usage: python3 .claude/scripts/test_adr16_public_tiers.py [--selftest]
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import urllib.parse
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import public_tiers  # noqa: E402
import market_brief  # noqa: E402
import spine_client  # noqa: E402
import retrieve  # noqa: E402
import deep_read_slices  # noqa: E402

FILTER = public_tiers.PUBLIC_TIER_FILTER          # captured before any mutation
EMAIL_ID = "00000007-aaaa-4aaa-8aaa-000000000007"
ROOM_ID = "00000001-aaaa-4aaa-8aaa-000000000001"   # a first_hand claim about company c1 in the fixture
FIX = os.path.join(HERE, "fixtures", "adr16")


def seeded_prod() -> dict:
    with open(os.path.join(market_brief.FIXTURES, "prod.json"), encoding="utf-8") as fh:
        prod = json.load(fh)
    prod["claim"].append({"id": EMAIL_ID, "event_id": None, "provenance_tier": "email_signal", "use_count": 0,
                          "nid": None})
    prod["claim_entity"].append({"claim_id": EMAIL_ID, "entity_type": "company", "entity_id": "c1"})
    # the one relation in the graph pairs a room claim with the email_signal claim: leaked, it is a room-vs-market link
    prod["claim_relation"] = [{"from_claim_id": ROOM_ID, "to_claim_id": EMAIL_ID, "relation": "corroborates",
                               "method": "fixture", "confidence": 0.9, "created_at": "2026-11-12T00:00:00+00:00"}]
    return prod


def stub(prod: dict, seen: list, honour: bool):
    """market_brief's own PostgREST stand-in, plus the ADR-16 filter: honoured (honour=True) or ignored."""
    base = market_brief._stub_req(prod, seen)
    private = json.loads(json.dumps(prod))
    private["claim"] = [c for c in prod["claim"] if public_tiers.is_public_tier(c["provenance_tier"])]
    base_filtered = market_brief._stub_req(private, [])

    def req(method, path, body=None, **kw):
        table = path.lstrip("/").split("?")[0]
        if honour and table == "claim" and FILTER in urllib.parse.unquote(path):
            seen.append((method, path))
            return base_filtered(method, path, body, **kw)
        return base(method, path, body, **kw)
    return req


class Brief:
    """One fixture tree + the market brief built over a given stub."""
    def __init__(self):
        with open(os.path.join(market_brief.FIXTURES, "tree.json"), encoding="utf-8") as fh:
            spec = json.load(fh)
        self.tmp = tempfile.mkdtemp(prefix="adr16_")
        market_brief._materialize(spec, self.tmp)

    def build(self, prod: dict, honour: bool) -> tuple[str, list]:
        seen: list = []
        real = spine_client.req
        spine_client.req = stub(prod, seen, honour)
        try:
            return market_brief.build(self.tmp, "2026-W47", date(2026, 11, 16), None), seen
        finally:
            spine_client.req = real

    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


# ---- the checks (each returns bool, so the mutation block can re-run it with a layer removed) ------------------
# Claim GETs that may run WITHOUT the filter: graph-health sizes in section 7, never about a company, theme or claim.
# reconcile's completeness inventory (share of research claims carrying an event_id, etc.) and the use_count
# coverage total. A new unfiltered claim read anywhere in the brief fails the server check until it is named here
# and justified in review.
COUNT_ONLY = ("/claim?select=event_id,lane,provenance_tier,nid:metadata->>notion_event_id&order=id",
              "/claim?select=id&use_count=gt.0&order=id")


def check_server_layer(b: Brief) -> bool:
    """Every GET of `claim` the public reader issues carries the filter, except the named count-only reads."""
    _, seen = b.build(seeded_prod(), honour=True)
    claim_gets = [p for _, p in seen if p.lstrip("/").startswith("claim?")]
    rows = [p for p in claim_gets if not p.startswith(COUNT_ONLY)]
    return (len(rows) >= 2 and all(FILTER in urllib.parse.unquote(p) for p in rows)
            and len(claim_gets) - len(rows) <= len(COUNT_ONLY))


def check_client_layer() -> bool:
    """With the server filter IGNORED, both public row readers raise instead of returning the email_signal row."""
    real = spine_client.req
    spine_client.req = stub(seeded_prod(), [], honour=False)
    try:
        raised = 0
        for fn, args in ((market_brief.fetch_relations, ()),
                         (market_brief.fetch_room_graph, ([{"topics": [], "companies": ["Knownco"]}],
                                                          [{"id": "c1", "name": "Knownco"}]))):
            try:
                fn(*args)
            except public_tiers.PublicTierViolation:
                raised += 1
        return raised == 2
    finally:
        spine_client.req = real


def check_client_output(b: Brief) -> bool:
    """With the server filter IGNORED, the rendered brief still counts no email_signal row (sections fail closed)."""
    text, _ = b.build(seeded_prod(), honour=False)
    return ("with 4 claims" not in text and "room-vs-market links of 1 claim relations" not in text
            and "PublicTierViolation" in text)


def check_output(b: Brief) -> bool:
    """With the filter honoured, the brief reads exactly as if the email_signal row did not exist."""
    text, _ = b.build(seeded_prod(), honour=True)
    return ("The graph knows 1 of 2 by name, with 3 claims" in text and "claim_relation has 0 rows" in text
            and EMAIL_ID[:8] not in text)


def pack_text() -> str:
    """retrieve.build_pack over a stubbed network: one company seed, two neighbourhood claims (web + email)."""
    claims = [{"id": "aaaaaaaa-1111", "claim_text": "Northwind Labs shipped an agent SDK", "claim_type": "fact",
               "provenance_tier": "web_verified", "confidence": .7, "asserted_at": "2026-11-01T00:00:00Z",
               "event_id": None, "document_id": "d1", "status": "approved", "metadata": {}},
              {"id": "bbbbbbbb-2222", "claim_text": "Northwind Labs is closing a $12M Series A", "claim_type": "fact",
               "provenance_tier": "email_signal", "confidence": .5, "asserted_at": "2026-11-10T00:00:00Z",
               "event_id": None, "document_id": "d2", "status": "approved", "metadata": {}}]

    def req(method, path, body=None, **kw):
        if method == "POST" and path == "/rpc/entity_neighborhood":
            return 200, {"events": [], "edges": [], "documents": [], "claims": claims, "hiring": []}
        if path.startswith("/company?"):
            return 200, [{"id": "co1", "name": "Northwind Labs", "metadata": {}}]
        return 200, []
    real = retrieve.req
    retrieve.req = req
    try:
        text, _, _ = retrieve.build_pack({"entities": [{"type": "company", "name": "Northwind Labs"}]}, "event", 6000)
        return text
    finally:
        retrieve.req = real


def check_private_pack() -> bool:
    lines = {l for l in pack_text().splitlines() if l.startswith("- Northwind")}
    email = [l for l in lines if "$12M" in l]
    web = [l for l in lines if "agent SDK" in l]
    return (len(email) == 1 and "[private: email_signal]" in email[0]
            and len(web) == 1 and "[private:" not in web[0])


def check_private_deep_read() -> bool:
    ev = ("##### Evidence Ledger — Northwind Labs\n"
          "- claim: Northwind Labs is closing a $12M Series A | tier: email-signal | source: Gmail | "
          "url: https://northwind.example/news | date: 2026-11-10\n"
          "- claim: Northwind Labs shipped an agent SDK | tier: web-verified | source: Blog | "
          "url: https://northwind.example/blog | date: 2026-11-01\n")
    idx = deep_read_slices.source_index(ev)
    return (len(idx) == 2 and idx[0].endswith("[private: email_signal]") and "[private:" not in idx[1])


def check_evaluator_fixture() -> bool:
    with open(os.path.join(FIX, "brief.md"), encoding="utf-8") as fh:
        brief = fh.read()
    with open(os.path.join(FIX, "draft.md"), encoding="utf-8") as fh:
        draft = fh.read()
    with open(os.path.join(FIX, "expected.md"), encoding="utf-8") as fh:
        expected = fh.read()
    tagged = [l for l in brief.splitlines() if "[private: email_signal]" in l]
    return (len(tagged) == 1 and "$12M" in tagged[0] and "$12M" in draft
            and public_tiers.ADR16_REASON in expected and "FAIL 1" in expected
            and "EMAIL-SIGNAL" in expected and "claude -p" in expected)


def check_unit() -> bool:
    ok = True
    try:
        public_tiers.assert_public([{"id": "x"}], "t")          # no tier column -> cannot prove public
        ok = False
    except public_tiers.PublicTierViolation:
        pass
    try:
        public_tiers.assert_public([{"provenance_tier": "email-signal"}], "t")   # ledger spelling is the same tier
        ok = False
    except public_tiers.PublicTierViolation:
        pass
    return (ok and public_tiers.assert_public([{"provenance_tier": "web_verified"}], "t") == [{"provenance_tier": "web_verified"}]
            and FILTER == "provenance_tier=not.in.(email_signal)"
            and public_tiers.private_tag("first_hand") == "" and public_tiers.private_tag(None) == "")


# ---- mutation: remove one layer, its check must fail; then restore --------------------------------------------
def mutated(attr: str, value, fn, *a) -> bool:
    saved = getattr(public_tiers, attr)
    setattr(public_tiers, attr, value)
    try:
        return fn(*a)
    finally:
        setattr(public_tiers, attr, saved)


def main() -> int:
    b = Brief()
    try:
        checks = [
            ("unit: no tier column and the ledger spelling both fail closed; filter string pinned", check_unit()),
            ("public/server: every market_brief claim GET carries the ADR-16 filter (bar the named count-only reads)", check_server_layer(b)),
            ("public/client: filter ignored -> fetch_relations and fetch_room_graph raise", check_client_layer()),
            ("public/client: filter ignored -> the brief counts no email_signal row", check_client_output(b)),
            ("public/output: filter honoured -> the brief reads as if the row never existed", check_output(b)),
            ("private: retrieve pack tags the email_signal line, not the web line", check_private_pack()),
            ("private: deep_read source index tags the email-signal row, not the web row", check_private_deep_read()),
            ("evaluator fixture: tagged brief line used by the draft; expected verdict cites ADR-16", check_evaluator_fixture()),
            ("mutation: filter blanked -> server check FAILS", not mutated("PUBLIC_TIER_FILTER", "", check_server_layer, b)),
            ("mutation: assert made a no-op -> client checks FAIL",
             not mutated("assert_public", lambda rows, where: list(rows or []), check_client_layer)
             and not mutated("assert_public", lambda rows, where: list(rows or []), check_client_output, b)),
            ("mutation: tag blanked -> private checks FAIL",
             not mutated("private_tag", lambda t: "", check_private_pack)
             and not mutated("private_tag", lambda t: "", check_private_deep_read)),
            ("restore: every layer back in place, checks pass again",
             check_server_layer(b) and check_client_layer() and check_private_pack()),
        ]
    finally:
        b.close()
    for name, good in checks:
        print(f"  {'✓' if good else '✗'} {name}")
    fail = sum(1 for _, g in checks if not g)
    print(f"selftest: {len(checks) - fail}/{len(checks)} pass")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
