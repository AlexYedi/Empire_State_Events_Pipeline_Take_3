#!/usr/bin/env python3
"""retrieve — the ONE retrieval interface over the Knowledge Substrate (ADR-10; YED-170).

Spec: .claude/notes/knowledge-substrate-architecture-2026-09-18.md §3.1–3.3, as amended by
.claude/notes/knowledge-substrate-review-2026-09-18.md (findings 5 + 6). W1 ships ONE lens (`event`);
the other lenses are six weights each and land once this one has proven out on a real brief (A/B).

    .venv/bin/python .claude/scripts/retrieve.py --lens event --seed seed.json [--budget-tokens 6000]
                     [--out pack.md] [--json]

seed.json: {"entities": [{"type": "person|company|topic", "name": "...", "notion_page_id": "..."}],
            "text": "<VERBATIM invite / question>", "focus": "<Alex's stated focus>", "window_days": 365}

What it does:
  1 resolve seed entities (notion_page_id, else exact name) — unresolved names are REPORTED, never guessed
  2 relational pull — RPC entity_neighborhood (0010); before 0010 lands, a REST fallback serves the
    events + roster half from today's tables and the audit line says so
  3 semantic pull — embed `text` locally (bge-small, the pinned doc_chunks model) -> RPC
    match_claims_hybrid (dense ∪ keyword, reciprocal-rank fusion); approved + candidate, never rejected
  4 score each claim once: w_sem·semantic + w_rel·relational + w_rec·recency + w_prov·provenance
    + w_conf·confidence + w_use·utility — w_use = 0 in every lens (ADR-10 decision 5)
  5 fill a TOKEN budget in score order (not a row count); list the cut tail by title
  6 emit the Context Pack (Continuity Ledger · People/Company/Topic cards · Claims · Audit); every
    claim line carries [tier · status · date] c:<8> so later usage can be traced
LOUD FAILURE (exit 5): the graph holds claims for these entities but the pack kept none — the
"filled substrate silently stops being read" failure the review named (finding 6). Never a shrug.
"""
from __future__ import annotations
import argparse, datetime as dt, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from spine_client import q, req  # noqa: E402
from substrate import norm_text, pid_variants  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DOCKB = os.path.join(ROOT, ".claude", "skills", "doc-knowledge-base")

LENSES = {  # the weights ARE the lens. w_use is 0 everywhere until >=20 outcome rows (decision 5)
    "event": {"sem": .30, "rel": .35, "rec": .15, "prov": .10, "conf": .10, "use": 0.0, "budget": 6000},
}
PROV = {"first_hand": 1.0, "web_verified": .9, "email_signal": .7, "notion_prior": .6, "reference": .5,
        "model_inferred": .3}
HALF_LIFE_DAYS = 90


def tokens(s: str) -> int:
    return math.ceil(len(s) / 4)


def get(path: str):
    st, body = req("GET", path)
    return body if st == 200 else None


def rpc(name: str, args: dict):
    st, body = req("POST", f"/rpc/{name}", args)
    return (st, body)


def resolve(seed: list[dict]) -> tuple[list[dict], list[str]]:
    table = {"person": "person", "company": "company", "topic": "topic"}
    found, missing = [], []
    for e in seed:
        t = table.get(e.get("type"))
        if not t:
            missing.append(f"{e.get('type')}:{e.get('name')}")
            continue
        row = None
        v = pid_variants(e.get("notion_page_id"))
        if v:
            rows = get(f"/{t}?notion_page_id=in.({','.join(q(x) for x in v)})&select=id,name&limit=1") or []
            row = rows[0] if rows else None
        if not row and e.get("name"):
            rows = get(f"/{t}?name=ilike.{q(e['name'])}&select=id,name&limit=5") or []
            rows = [r for r in rows if norm_text(r["name"]) == norm_text(e["name"])]
            row = rows[0] if len(rows) == 1 else None
        if row:
            found.append({"type": t, "id": row["id"], "name": row["name"]})
        else:
            missing.append(f"{t}:{e.get('name') or e.get('notion_page_id')}")
    return found, missing


def neighborhood(ids: list[str], since: str | None) -> tuple[dict, str]:
    st, body = rpc("entity_neighborhood", {"seed_ids": ids, "since": since})
    if st == 200 and isinstance(body, dict):
        return body, "rpc"
    # REST fallback (0010 not applied yet): events + roster from today's tables; no claims/docs
    links = get(f"/event_entity?entity_id=in.({','.join(ids)})&select=event_id") or []
    eids = sorted({l["event_id"] for l in links})
    events = []
    if eids:
        flt = f"&event_date=gte.{since}" if since else ""
        events = get(f"/event?id=in.({','.join(eids)}){flt}&select=id,title,kind,event_date,source,url"
                     f"&order=event_date.desc&limit=60") or []
    edges = []
    if events:
        ee = get(f"/event_entity?event_id=in.({','.join(e['id'] for e in events)})"
                 f"&select=event_id,entity_type,entity_id,role") or []
        names = {}
        for t in ("person", "company", "topic"):
            want = sorted({r["entity_id"] for r in ee if r["entity_type"] == t})
            for i in range(0, len(want), 80):
                for r in get(f"/{t}?id=in.({','.join(want[i:i + 80])})&select=id,name") or []:
                    names[r["id"]] = r["name"]
        edges = [{**r, "name": names.get(r["entity_id"])} for r in ee]
    return {"events": events, "edges": edges, "documents": [], "claims": []}, "rest-fallback (0010 not applied)"


def claim_layer_live() -> bool:
    st, _ = req("GET", "/claim?select=id&limit=1")
    return st == 200


def semantic_claims(text: str, ids: list[str], n: int) -> list[dict]:
    sys.path.insert(0, DOCKB)
    from dockb_common import embed_query, vec_literal
    st, body = rpc("match_claims_hybrid", {"query_embedding": vec_literal(embed_query(text)), "query_text": text,
                                           "match_count": n, "filter_entity_ids": None})
    return body if st == 200 and isinstance(body, list) else []


def score_claims(claims: list[dict], seed_ids: set[str], nb_event_ids: set[str], w: dict) -> list[dict]:
    now = dt.datetime.now(dt.timezone.utc)
    n = max(len(claims), 1)
    for rank, c in enumerate(claims, 1):
        sem = 1 - (rank - 1) / n if c.get("_semantic") else 0.0
        rel = 1.0 if c.get("_direct") else 0.5 if c.get("event_id") in nb_event_ids else 0.0
        when = c.get("asserted_at")
        age = (now - dt.datetime.fromisoformat(when.replace("Z", "+00:00"))).days if when else 365
        rec = 0.5 ** (max(age, 0) / HALF_LIFE_DAYS)
        c["_score"] = round(w["sem"] * sem + w["rel"] * rel + w["rec"] * rec
                            + w["prov"] * PROV.get(c.get("provenance_tier"), .5)
                            + w["conf"] * float(c.get("confidence") or .5) + w["use"] * 0.0, 4)
    return sorted(claims, key=lambda c: -c["_score"])


def build_pack(seed: dict, lens: str, budget: int) -> tuple[str, dict, int]:
    w = LENSES[lens]
    found, missing = resolve(seed.get("entities", []))
    ids = [f["id"] for f in found]
    since = None
    if seed.get("window_days"):
        since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=int(seed["window_days"]))).strftime("%Y-%m-%dT00:00:00Z")
    nb, mode = neighborhood(ids, since) if ids else ({"events": [], "edges": [], "documents": [], "claims": []}, "no seeds")
    live = claim_layer_live()
    claims = {c["id"]: {**c, "_direct": True} for c in nb.get("claims", [])}
    if live and seed.get("text"):
        for c in semantic_claims(seed["text"], ids, 30):
            claims.setdefault(c["id"], c)["_semantic"] = True
    nb_ev = {e["id"] for e in nb["events"]}
    ranked = score_claims(list(claims.values()), set(ids), nb_ev, w)
    ev_by_id = {e["id"]: e for e in nb["events"]}

    # ---- sections -------------------------------------------------------------------------------
    seed_names = {f["id"]: f["name"] for f in found}
    lines = [f"# Context Pack — lens: {lens}", ""]
    ledger = ["## Continuity Ledger — prior occasions involving the seeds", ""]
    for e in nb["events"]:
        hits = [f"{seed_names[x['entity_id']]} ({x['role']})" for x in nb["edges"]
                if x["event_id"] == e["id"] and x["entity_id"] in seed_names]
        ledger.append(f"- {str(e.get('event_date') or '')[:10]} · {e['kind']} · **{e['title']}** — {', '.join(hits)} "
                      f"[source: {e.get('source')}]")
    people: dict[str, dict] = {}
    for x in nb["edges"]:
        if x["entity_type"] == "person" and x.get("name"):
            p = people.setdefault(x["entity_id"], {"name": x["name"], "seen": []})
            ev = ev_by_id.get(x["event_id"])
            if ev:
                p["seen"].append(f"{str(ev.get('event_date') or '')[:10]} {ev['title'][:48]} ({x['role']})")
    cards = ["## People — seeds and returning faces", ""]
    for pid, p in sorted(people.items(), key=lambda kv: (-len(kv[1]["seen"]), kv[1]["name"])):
        if pid in seed_names or len(p["seen"]) >= 2:
            cards.append(f"- **{p['name']}** — seen at {len(p['seen'])}: " + "; ".join(p["seen"][:4]))
    topics: dict[str, set] = {}
    for x in nb["edges"]:
        if x["entity_type"] == "topic" and x.get("name"):
            topics.setdefault(x["name"], set()).add(x["event_id"])
    tcards = ["## Topics recurring across these occasions", ""] + [
        f"- {name} — {len(evs)} occasions" for name, evs in sorted(topics.items(), key=lambda kv: -len(kv[1]))[:15]]

    # ---- claims under the token budget ------------------------------------------------------------
    used = sum(tokens("\n".join(s)) for s in (ledger, cards, tcards))
    kept, cut = [], []
    per_doc: dict[str, int] = {}
    for c in ranked:
        doc = c.get("document_id") or c.get("event_id") or "none"
        flag = " ⚠ do-not-publish" if (c.get("metadata") or {}).get("do_not_publish") else ""
        ev = ev_by_id.get(c.get("event_id"))
        where = f" — {ev['title'][:40]}" if ev else ""
        line = (f"- {c['claim_text']}{where} [{c.get('provenance_tier')} · "
                f"{'unreviewed' if c.get('status') == 'candidate' else c.get('status')} · "
                f"{str(c.get('asserted_at') or '')[:10]}]{flag} c:{str(c['id'])[:8]}")
        if per_doc.get(doc, 0) >= 3 or used + tokens(line) > budget:   # diversity: <=3 per source
            cut.append(c)
            continue
        per_doc[doc] = per_doc.get(doc, 0) + 1
        used += tokens(line)
        kept.append(line)
    cl = ["## Claims (scored)", ""] + (kept or ["- (none)"])
    if cut:
        cl += ["", f"_Cut for budget/diversity: {len(cut)} more claims._"]

    audit = {"lens": lens, "mode": mode, "claims_layer": "live" if live else "not migrated (S1a pending)",
             "seeds_resolved": len(found), "seeds_unresolved": missing, "events": len(nb["events"]),
             "edges": len(nb["edges"]), "claims_candidates": len(ranked), "claims_kept": len(kept),
             "claims_cut": len(cut), "tokens": used, "budget": budget}
    audit_line = (f"AUDIT · lens={lens} · seeds={len(found)} resolved/{len(missing)} unresolved · "
                  f"events={audit['events']} · claims {len(kept)} kept/{len(cut)} cut · docs={len(nb.get('documents', []))} · "
                  f"tokens {used}/{budget} · graph={mode} · claims-layer={audit['claims_layer']}")
    lines += [f"_{audit_line}_", ""]
    if missing:
        lines += [f"**Unresolved seeds (reported, not guessed):** {', '.join(missing)}", ""]
    lines += ledger + [""] + cards + [""] + tcards + [""] + cl + [""]

    # ---- loud failure (review finding 6) --------------------------------------------------------
    rc = 0
    if live and ids and not kept:
        ev_ids = list(nb_ev)
        has = 0
        if ev_ids:
            has += len(get(f"/claim?event_id=in.({','.join(ev_ids)})&status=neq.rejected&select=id&limit=1") or [])
        has += len(get(f"/claim_entity?entity_id=in.({','.join(ids)})&select=claim_id&limit=1") or [])
        if has:
            rc = 5
            lines.insert(2, "> ⚠️ **RETRIEVAL FAILURE** — the graph holds claims for these entities but this pack "
                            "kept none. Do not proceed as if there were no prior knowledge; investigate "
                            "(embedding model mismatch? RPC error? budget too small?).\n")
    return "\n".join(lines), {**audit, "audit_line": audit_line}, rc


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--lens", choices=sorted(LENSES), default="event")
    ap.add_argument("--seed", required=True)
    ap.add_argument("--budget-tokens", type=int)
    ap.add_argument("--out")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    seed = json.load(open(a.seed, encoding="utf-8"))
    pack, audit, rc = build_pack(seed, a.lens, a.budget_tokens or LENSES[a.lens]["budget"])
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(pack)
        print(f"pack -> {a.out}")
    else:
        print(pack)
    print(audit["audit_line"], file=sys.stderr)
    if a.json:
        print(json.dumps(audit))
    if rc == 5:
        print("RETRIEVAL FAILURE (exit 5): claims exist for these entities but none were kept.", file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
