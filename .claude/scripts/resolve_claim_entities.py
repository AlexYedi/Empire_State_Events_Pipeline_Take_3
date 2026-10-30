#!/usr/bin/env python3
"""resolve_claim_entities — link claims to entities via claim.proposed_entities (YED-264; S-01).

docs/specs/shared/S-01-graph-read-loop.md item 2. The live read found 1,004 claims (22%) linked to
no entity. This script reads the claim layer's `proposed_entities` jsonb
([{type: company|person|topic, name, existing_id}, ...] — supabase/migrations/0009; plain strings
accepted defensively) and proposes `claim_entity` rows for links that do not exist yet.

Matching follows the dedup rules in .claude/references/market-intel-spine.md ("Dedup-before-create"):
  * company / topic — lower(name) exact, the unique-index target; more than one survivor is
    ambiguous (should not happen while the index holds — reported, never guessed)
  * person — people share names and there is no hard unique, so the claim's event roster pins the
    "name + company" context (the same scoping substrate.py uses to make speaker matching safe).
    A unique roster match wins; a shared name is ambiguous; with no roster a globally unique name
    matches and a shared name stays ambiguous.
  * no match — unmatched. Ambiguous and unmatched are REPORTED, never guessed.

--dry-run IS the default: it prints matched / ambiguous / unmatched counts plus the ambiguous list
and writes nothing. Writes (--apply) go ONLY through spine_client.write() (ADR-9) — one claim_entity
row per (claim_id, entity_type, entity_id, role="about"), read-before-write so a re-run is a no-op.
The factory never runs this live; verification is the fixture selftest.

Usage:
    python3 .claude/scripts/resolve_claim_entities.py --selftest
    python3 .claude/scripts/resolve_claim_entities.py                 # dry-run report (default)
    python3 .claude/scripts/resolve_claim_entities.py --apply         # write the matched links
    [--limit N] [--claim-id <uuid>] [--json]
"""
from __future__ import annotations
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from spine_client import q, req, write  # noqa: E402  ADR-9: the one write path
from substrate import norm_text  # noqa: E402

ROLE = "about"          # proposed entities are what a claim is about (substrate.py uses the same role)
CHUNK = 80

# ---- pure core (covered by --selftest on inline fixtures; no network) -------------------------


def normalize_proposals(raw) -> list[dict]:
    """[{type, name} | "Name", ...] -> [{"type": "company"|"person"|"topic"|None, "name": str}].
    Junk (non-lists — a bare string would otherwise iterate per character — non-strings/objects,
    blank names) is dropped. An UNKNOWN type keeps the name as untyped: it is matched across the
    kinds and any ambiguity lands in the report, never silently dropped nor forced into one kind."""
    if isinstance(raw, str) or not isinstance(raw, (list, tuple)):
        return []
    out: list[dict] = []
    for item in raw or []:
        if isinstance(item, str):
            name, etype = item, None
        elif isinstance(item, dict):
            name, etype = item.get("name"), item.get("type")
        else:
            continue
        if not isinstance(name, str) or not name.strip():
            continue
        out.append({"type": etype if etype in ("company", "person", "topic") else None,
                    "name": name.strip()})
    return out


def match_lower(name: str, rows: list[tuple]) -> tuple[str, list[str]]:
    """company/topic: lower(name) exact per the spine's unique index. -> (status, ids)."""
    ids = [r[0] for r in rows if norm_text(r[1]) == norm_text(name)]
    if len(ids) == 1:
        return "matched", ids
    return ("ambiguous", ids) if ids else ("unmatched", [])


def match_person(name: str, roster: list[tuple], all_persons: list[tuple]) -> tuple[str, list[str]]:
    """Dedup rule 'name (+ company)': the claim's event roster pins the company context. Roster hit
    must be unique; with NO roster a globally unique name matches, a shared name stays ambiguous.
    A non-empty roster that misses is UNMATCHED — never a global fallback across events."""
    n = norm_text(name)
    cands = [(pid, nm) for pid, nm in roster if norm_text(nm) == n]
    if not cands and not roster:
        cands = [(pid, nm) for pid, nm in all_persons if norm_text(nm) == n]
    if len(cands) == 1:
        return "matched", [cands[0][0]]
    return ("ambiguous", [pid for pid, _ in cands]) if cands else ("unmatched", [])


def resolve_proposal(proposal: dict, tables: dict, roster: list[tuple]) -> tuple[str | None, str, list[str]]:
    """One proposal -> (entity_type, status, candidate_ids). entity_type is None only when the
    proposal was untyped AND nothing matched (there is no kind to report)."""
    t, name = proposal["type"], proposal["name"]
    if t in ("company", "topic"):
        status, ids = match_lower(name, tables[t])
        return t, status, ids
    if t == "person":
        status, ids = match_person(name, roster, tables["person"])
        return t, status, ids
    # untyped: company/topic by lower(name) everywhere; person only through the roster (safe scoping)
    hits = ([(k, r[0]) for k in ("company", "topic") for r in tables[k] if norm_text(r[1]) == norm_text(name)]
            + [("person", pid) for pid, nm in roster if norm_text(nm) == norm_text(name)])
    if len(hits) == 1:
        return hits[0][0], "matched", [hits[0][1]]
    if hits:
        return None, "ambiguous", [pid for _, pid in hits]
    return None, "unmatched", []


def resolve_claim(claim: dict, tables: dict) -> tuple[list[dict], list[dict], list[dict]]:
    """Pure. One claim -> (link_rows, ambiguous, unmatched). roster rides on the claim as `_roster`."""
    links, ambiguous, unmatched = [], [], []
    for p in normalize_proposals(claim.get("proposed_entities")):
        kind, status, ids = resolve_proposal(p, tables, claim.get("_roster") or [])
        if status == "matched":
            links.append({"claim_id": claim["id"], "entity_type": kind, "entity_id": ids[0], "role": ROLE})
        elif status == "ambiguous":
            ambiguous.append({"claim": claim["id"], "name": p["name"], "kind": kind or "untyped",
                              "candidates": ids})
        else:
            unmatched.append({"claim": claim["id"], "name": p["name"], "kind": kind or "untyped"})
    return links, ambiguous, unmatched


def plan_links(claims: list[dict], tables: dict, existing: set[tuple]) -> dict:
    """Pure aggregation over claims; drops pairs already linked (read-before-write, idempotent)."""
    links: list[dict] = []
    ambiguous: list[dict] = []
    unmatched: list[dict] = []
    already = 0
    proposals = 0
    seen: set[tuple] = set()
    for c in claims:
        lk, amb, unm = resolve_claim(c, tables)
        proposals += len(normalize_proposals(c.get("proposed_entities")))
        for row in lk:
            key = (row["claim_id"], row["entity_type"], row["entity_id"], row["role"])
            if key in existing:
                already += 1
                continue
            if key in seen:                     # the same proposal twice on one claim
                continue
            seen.add(key)
            links.append(row)
        ambiguous += amb
        unmatched += unm
    return {"links": links, "ambiguous": ambiguous, "unmatched": unmatched, "already": already,
            "proposals": proposals}


# ---- live fetch + persist (never exercised live by the factory; the selftest stubs both) ------


def _get(path: str) -> list | None:
    st, body = req("GET", path)
    return body if st == 200 and isinstance(body, list) else None


def _fetch_all(limit: int | None, claim_id: str | None) -> tuple[list[dict], dict, set[tuple]]:
    """Claims carrying proposals + the entity tables + the claim_entity pairs that already exist."""
    path = f"/claim?proposed_entities=not.is.null&status=neq.rejected&select=id,event_id,proposed_entities" \
           f"&order=created_at.desc"
    if claim_id:
        path += f"&id=eq.{q(claim_id)}"
    if limit:
        path += f"&limit={int(limit)}"
    claims = [c for c in (_get(path) or []) if c.get("proposed_entities")]
    tables = {"company": [], "topic": [], "person": []}
    for t in ("company", "topic", "person"):
        tables[t] = [(r["id"], r["name"]) for r in
                     (_get(f"/{t}?select=id,name&limit=2000") or [])]
    # roster per claim event: the person-hop context that makes person matching safe
    ev_ids = sorted({c["event_id"] for c in claims if c.get("event_id")})
    roster_ids: set[str] = set()
    ev_person: dict[str, list[str]] = {}
    for i in range(0, len(ev_ids), CHUNK):
        for r in _get(f"/event_entity?event_id=in.({','.join(ev_ids[i:i + CHUNK])})&entity_type=eq.person"
                      f"&select=event_id,entity_id") or []:
            ev_person.setdefault(r["event_id"], []).append(r["entity_id"])
            roster_ids.add(r["entity_id"])
    names = {r["id"]: r["name"] for r in (_get(f"/person?id=in.({','.join(sorted(roster_ids))})&select=id,name")
                                          or [])} if roster_ids else {}
    for c in claims:
        c["_roster"] = [(pid, names[pid]) for pid in ev_person.get(c.get("event_id"), []) if pid in names]
    existing: set[tuple] = set()
    cids = [c["id"] for c in claims]
    for i in range(0, len(cids), CHUNK):
        for r in _get(f"/claim_entity?claim_id=in.({','.join(cids[i:i + CHUNK])})"
                      f"&select=claim_id,entity_type,entity_id,role") or []:
            existing.add((r["claim_id"], r["entity_type"], r["entity_id"], r["role"]))
    return claims, tables, existing


def _persist(rows: list[dict]) -> tuple[int, object]:
    # the one write path (ADR-9): guarded POST via spine_client.write()
    return write("claim_entity", rows, prefer="return=minimal")


_FETCH = _fetch_all    # module-level indirection so --selftest can drive the pipeline offline
_PERSIST = _persist


def report_lines(plan: dict, claims_n: int, dry: bool) -> list[str]:
    lines = [f"resolve_claim_entities — {'DRY RUN (nothing written)' if dry else 'APPLY'}"]
    lines.append(f"claims considered: {claims_n} · proposals: {plan['proposals']}")
    lines.append(f"matched: {len(plan['links'])} · ambiguous: {len(plan['ambiguous'])} · "
                 f"unmatched: {len(plan['unmatched'])} · already linked: {plan['already']}")
    if plan["ambiguous"]:
        lines.append("ambiguous (reported, never guessed):")
        for a in plan["ambiguous"]:
            lines.append(f"  - claim c:{str(a['claim'])[:8]} {a['kind']} \"{a['name']}\" — "
                         f"{len(a['candidates'])} candidates: {', '.join(a['candidates'])}")
    return lines


def run(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--apply", action="store_true", help="write the matched links (default: dry-run)")
    ap.add_argument("--limit", type=int, help="consider only the N newest claims")
    ap.add_argument("--claim-id", help="consider one claim")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    claims, tables, existing = _FETCH(a.limit, a.claim_id)
    if claims is None:
        print("fetch failed — no claims read (loud stop; nothing written)", file=sys.stderr)
        return 1
    plan = plan_links(claims, tables, existing)
    if a.json:
        print(json.dumps({"dry_run": not a.apply, "claims": len(claims), **{k: plan[k] for k in plan}}))
    else:
        print("\n".join(report_lines(plan, len(claims), not a.apply)))
    if not a.apply:
        return 0
    if not plan["links"]:
        print("nothing to write (0 matched links)")
        return 0
    written = 0
    for i in range(0, len(plan["links"]), CHUNK):
        code, body = _PERSIST(plan["links"][i:i + CHUNK])
        if code not in (200, 201):
            print(f"write FAILED at rows {i}..{i + CHUNK}: {code} {str(body)[:200]} — "
                  f"re-run is safe (read-before-write skips what landed)", file=sys.stderr)
            return 1
        written += len(plan["links"][i:i + CHUNK])
    print(f"wrote {written} claim_entity row(s) via spine_client (ADR-9)")
    return 0


def selftest() -> bool:
    """Offline fixtures end-to-end: fetch + persist are stubbed, the dry-run/apply contract is
    exercised against sampled data. The factory never runs the live path."""
    calls: dict = {}

    def fake_fetch(limit, claim_id):
        calls["fetch"] = (limit, claim_id)
        claims = [
            {"id": "c1", "event_id": "e1", "proposed_entities": [{"type": "company", "name": "Harvey"},
                                                                 {"type": "person", "name": "Jane Doe"}],
             "_roster": [("p1", "Jane Doe"), ("p2", "John Roe")]},
            {"id": "c2", "event_id": "e1", "proposed_entities": [{"type": "person", "name": "Jane Doe"},
                                                                 "Veris AI"],
             "_roster": [("p1", "Jane Doe"), ("p3", "Jane Doe")]},          # shared name -> ambiguous
            {"id": "c3", "event_id": None, "proposed_entities": [{"type": "topic", "name": " Agentic AI "}],
             "_roster": []},
            {"id": "c4", "event_id": "e2", "proposed_entities": [{"type": "person", "name": "Nobody Here"}],
             "_roster": [("p2", "John Roe")]},                              # roster misses -> unmatched
            {"id": "c5", "event_id": None, "proposed_entities": [{"type": "company", "name": "Linked Co"}],
             "_roster": []},                                                # already linked -> skipped
            {"id": "c6", "event_id": None, "proposed_entities": ["Acme", "harvey"],  # untyped, one hit + one dup
             "_roster": []},
            {"id": "c7", "event_id": None, "proposed_entities": [{"type": "person", "name": "Ritiz Tambi"}],
             "_roster": []},                                                # no roster, globally unique
            {"id": "c8", "event_id": None, "proposed_entities": "not a list", "_roster": []},  # junk dropped
            {"id": "c9", "event_id": None, "proposed_entities": [], "_roster": []},            # empty
        ]
        return claims[:limit] if limit else claims, {
            "company": [("co1", "Harvey"), ("co2", "VERIS AI"), ("co3", "Linked Co"), ("co4", "Acme")],
            "topic": [("t1", "agentic ai"), ("t2", "harvey")],
            "person": [("p1", "Jane Doe"), ("p2", "John Roe"), ("p3", "Jane Doe"), ("p4", "Ritiz Tambi")],
        }, {("c5", "company", "co3", "about")}

    def fake_persist(rows):
        calls.setdefault("persisted", []).append(rows)
        return 201, "ok"

    global _FETCH, _PERSIST
    saved = (_FETCH, _PERSIST)
    _FETCH, _PERSIST = fake_fetch, fake_persist
    try:
        plan = plan_links(*fake_fetch(None, None)[:2], existing=fake_fetch(None, None)[2])
        checks = [
            ("normalize: typed objects, plain strings, junk + empties dropped; unknown type -> untyped",
             normalize_proposals([{"type": "company", "name": "A"}, "B", {"type": "alien", "name": "C"},
                                  {"name": " "}, 42, {"type": "topic", "name": "D"}])
             == [{"type": "company", "name": "A"}, {"type": None, "name": "B"}, {"type": None, "name": "C"},
                 {"type": "topic", "name": "D"}]),
            ("company/topic: lower(name) exact, whitespace-normalized",
             match_lower("Harvey", [("co1", "harvey")])[0] == "matched"
             and match_lower("Harvey", [("co1", "Harvey"), ("co2", "HARVEY")])[0] == "ambiguous"
             and match_lower("nope", [("co1", "harvey")]) == ("unmatched", [])),
            ("person: unique roster match wins", match_person("jane doe", [("p1", "Jane Doe")], [])[0] == "matched"),
            ("person: shared roster name is ambiguous, never guessed",
             match_person("Jane Doe", [("p1", "Jane Doe"), ("p3", "Jane Doe")], [])[0] == "ambiguous"),
            ("person: non-empty roster miss stays unmatched (no global fallback)",
             match_person("Nobody Here", [("p2", "John Roe")], [("p4", "Nobody Here")]) == ("unmatched", [])),
            ("person: no roster + globally unique name matches",
             match_person("Ritiz Tambi", [], [("p4", "Ritiz Tambi")]) == ("matched", ["p4"])),
            ("untyped string matching two kinds is ambiguous (company 'Harvey' vs topic 'harvey')",
             resolve_proposal({"type": None, "name": "harvey"}, {
                 "company": [("co1", "Harvey")], "topic": [("t2", "harvey")], "person": []}, [])[0] is None
             and resolve_proposal({"type": None, "name": "harvey"}, {
                 "company": [("co1", "Harvey")], "topic": [("t2", "harvey")], "person": []}, [])[1] == "ambiguous"),
            ("plan: links carry role=about and allowlisted keys only",
             all(set(r) == {"claim_id", "entity_type", "entity_id", "role"} and r["role"] == "about"
                 for r in plan["links"])),
            ("plan: already-linked pair skipped (read-before-write, idempotent)",
             all(not (r["claim_id"] == "c5" and r["entity_id"] == "co3") for r in plan["links"])
             and plan["already"] == 1),
            ("plan: roster ambiguity reported with candidates, not resolved",
             any(a["claim"] == "c2" and a["kind"] == "person" and len(a["candidates"]) == 2
                 for a in plan["ambiguous"])),
            ("plan: roster-miss and no-roster-dup resolve to unmatched/unambiguous as designed",
             any(u["claim"] == "c4" and u["kind"] == "person" for u in plan["unmatched"])),
            ("plan: counts on the sampled fixtures (6 matched, 2 ambiguous, 1 unmatched)",
             len(plan["links"]) == 6 and len(plan["ambiguous"]) == 2 and len(plan["unmatched"]) == 1),
        ]
        # end-to-end through run(): dry-run writes nothing; --apply writes exactly the matched links
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_dry = run(["--json"])
        checks.append(("run() dry-run: exit 0, persist never called, report is JSON with dry_run",
                       rc_dry == 0 and "persisted" not in calls
                       and json.loads(buf.getvalue().strip())["dry_run"] is True))
        buf2 = io.StringIO()
        with contextlib.redirect_stdout(buf2):
            rc_apply = run(["--apply"])
        rows = calls.get("persisted", [])
        checks.append(("run() --apply: exit 0, exactly the matched links written via spine_client.write",
                       rc_apply == 0 and len(rows) == 1 and len(rows[0]) == 6))
        report = "\n".join(report_lines(plan, 9, True))
        checks.append(("dry-run report prints matched/ambiguous/unmatched counts + the ambiguous list",
                       "matched: 6" in report and "ambiguous: 2" in report and "unmatched: 1" in report
                       and "ambiguous (reported, never guessed):" in report))
    finally:
        _FETCH, _PERSIST = saved
    fail = 0
    for name, good in checks:
        print(f"  {'✓' if good else '✗'} {name}")
        fail += 0 if good else 1
    print(f"selftest: {len(checks) - fail}/{len(checks)} pass")
    return fail == 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return 0 if selftest() else 1
    return run(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
