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

--lens content (YED-208, .claude/notes/yed-208-spec-2026-09-27.md) adds "What you've already said": Alex's prior
published posts on the theme, found relationally (a `published` event sharing a seed entity) and by meaning
(match_doc_chunks over linkedin_post chunks). Every entry carries the post's real URL from the graph; a draft
may back-link only these URLs, never an invented one. Offline check: retrieve.py --selftest
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
    # architecture note §3.2 row `content`, EXCEPT use: the table says .20, ADR-10 decision 8 says 0 until >=20
    # outcome rows exist. The ADR outranks the table.
    "content": {"sem": .30, "rel": .20, "rec": .15, "prov": .10, "conf": .05, "use": 0.0, "budget": 5000},
}
POST_SIM_FLOOR = 0.55   # PROVISIONAL: bge-small cosine; revisit once the lens has run on real events
MAX_PRIOR_POSTS = 6
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


def follow_tombstone(t: str, row: dict | None, depth: int = 5) -> dict | None:
    """YED-47 spec item 3: a seed that names a soft-merged row (metadata.merged_into) resolves to its live
    target, so the pack is built around the surviving entity. Read path: a dangling target is left as-is
    (the producer's resolver fails loud; retrieval degrades quietly and the probe reports it)."""
    while row and (row.get("metadata") or {}).get("merged_into") and depth:
        nxt = get(f"/{t}?id=eq.{q(row['metadata']['merged_into'])}&select=id,name,metadata&limit=1") or []
        if not nxt:
            break
        row, depth = nxt[0], depth - 1
    return row


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
            rows = get(f"/{t}?notion_page_id=in.({','.join(q(x) for x in v)})&select=id,name,metadata&limit=1") or []
            row = follow_tombstone(t, rows[0]) if rows else None
        if not row and e.get("name"):
            rows = get(f"/{t}?name=ilike.{q(e['name'])}&select=id,name,metadata&limit=5") or []
            rows = [follow_tombstone(t, r) for r in rows if norm_text(r["name"]) == norm_text(e["name"])]
            rows = list({r["id"]: r for r in rows}.values())          # a tombstone + its target count once
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


def merge_prior_posts(rel_docs: list[dict], sem_hits: list[dict], docs: dict[str, dict],
                      outcomes: dict[str, str], seed_names: dict[str, str], rel_why: dict[str, list[str]],
                      floor: float = POST_SIM_FLOOR, cap: int = MAX_PRIOR_POSTS) -> list[dict]:
    """Pure (offline-tested). rel_docs: documents tied to a `published` event that shares a seed entity.
    sem_hits: match_doc_chunks rows {document_id, similarity}. docs: document rows by id. A post needs a URL
    in its metadata or it is dropped (a back-link without a URL is useless). Relational hits rank first, then
    by best chunk similarity; semantic-only hits must clear `floor`. One entry per document."""
    out: dict[str, dict] = {}
    for d in rel_docs:
        out[d["id"]] = {"doc": d, "rel": True, "sim": 0.0, "why": rel_why.get(d["id"], [])}
    for h in sem_hits:
        did, sim = h.get("document_id"), float(h.get("similarity") or 0)
        if did not in docs:
            continue                                  # not a current linkedin_post document
        e = out.setdefault(did, {"doc": docs[did], "rel": False, "sim": 0.0, "why": []})
        e["sim"] = max(e["sim"], sim)
    kept = [e for e in out.values() if (e["doc"].get("metadata") or {}).get("published_url")
            and (e["rel"] or e["sim"] >= floor)]
    # Ranking (pre-mortem 2026-09-27): relational first; among relational, MORE shared seed entities first, so a
    # focused post sharing three of this event's topics beats a weekly roundup that inherited one of them from
    # eight covered events. Then best text similarity, then newest.
    kept.sort(key=lambda e: str(e["doc"].get("doc_date") or ""), reverse=True)
    kept.sort(key=lambda e: (not e["rel"], -len(set(e["why"])), -e["sim"]))
    res = []
    for e in kept[:cap]:
        d = e["doc"]
        why = ([f"shares {', '.join(sorted(set(e['why'])))}"] if e["why"] else []) + \
              ([f"similar text {e['sim']:.2f}"] if e["sim"] >= floor else [])
        res.append({"id": d["id"], "title": d.get("title"), "url": d["metadata"]["published_url"],
                    "date": str(d.get("doc_date") or "")[:10], "outcome": outcomes.get(d["id"]), "why": why})
    return res


def prior_posts(seed: dict, ids: list[str], nb: dict, seed_names: dict[str, str]) -> list[dict]:
    """YED-208 — Alex's own published posts on this theme (graph reads only)."""
    pub_ev = [e["id"] for e in nb.get("events", []) if e.get("kind") == "published"]
    rel_why: dict[str, list[str]] = {}
    rel_docs = []
    if pub_ev:
        rel_docs = get(f"/documents?event_id=in.({','.join(pub_ev)})&source_type=eq.linkedin_post&is_current=is.true"
                       f"&select=id,title,doc_date,metadata,event_id") or []
        by_ev = {}
        for x in nb.get("edges", []):
            if x["event_id"] in pub_ev and x["entity_id"] in seed_names:
                by_ev.setdefault(x["event_id"], []).append(seed_names[x["entity_id"]])
        for d in rel_docs:
            rel_why[d["id"]] = by_ev.get(d["event_id"], [])
    sem_hits = []
    if seed.get("text"):
        sys.path.insert(0, DOCKB)
        from dockb_common import embed_query, vec_literal
        st, body = rpc("match_doc_chunks", {"query_embedding": vec_literal(embed_query(seed["text"])), "match_count": 40})
        sem_hits = body if st == 200 and isinstance(body, list) else []
    cand = sorted({h["document_id"] for h in sem_hits} - {d["id"] for d in rel_docs})
    docs = {d["id"]: d for d in rel_docs}
    if cand:
        for d in get(f"/documents?id=in.({','.join(cand)})&source_type=eq.linkedin_post&is_current=is.true"
                     f"&select=id,title,doc_date,metadata,event_id") or []:
            docs[d["id"]] = d
    outcomes = {}
    if docs:
        for o in get(f"/artifact_outcome?document_id=in.({','.join(docs)})&select=document_id,outcome") or []:
            if o.get("outcome"):
                outcomes[o["document_id"]] = o["outcome"]
    return merge_prior_posts(rel_docs, sem_hits, docs, outcomes, seed_names, rel_why)


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

    # ---- YED-208: what Alex has already published on this theme (content lens only) ----------------
    said: list[str] = []
    posts: list[dict] = []
    if lens == "content":
        posts = prior_posts(seed, ids, nb, seed_names)
        said = ["## What you've already said — your prior posts on this theme", "",
                "_Back-link only where a post genuinely extends the new one's thesis. Use these URLs verbatim; never invent one._", ""]
        said += [f"- {p['date']} · **{p['title']}** — {p['url']}" + (f" · outcome: {p['outcome']}" if p["outcome"] else "")
                 + (f" · {'; '.join(p['why'])}" if p["why"] else "") for p in posts] or ["- (none yet on this theme)"]

    # ---- claims under the token budget ------------------------------------------------------------
    used = sum(tokens("\n".join(s)) for s in (ledger, cards, tcards, said))
    def render(c: dict) -> str:
        flag = " ⚠ do-not-publish" if (c.get("metadata") or {}).get("do_not_publish") else ""
        ev = ev_by_id.get(c.get("event_id"))
        where = f" — {ev['title'][:40]}" if ev else ""
        return (f"- {c['claim_text']}{where} [{c.get('provenance_tier')} · "
                f"{'unreviewed' if c.get('status') == 'candidate' else c.get('status')} · "
                f"{str(c.get('asserted_at') or '')[:10]}]{flag} c:{str(c['id'])[:8]}")

    # Two-pass fill. Pass 1: <=3 claims per source so one long brief cannot crowd out other sources.
    # Pass 2: spend the remaining budget in score order. (Acceptance run 2026-09-18: a one-source
    # neighborhood kept 3/46 claims at 352/6000 tokens under a hard cap — diversity must not starve depth.)
    kept, deferred, cut = [], [], []
    per_src: dict[str, int] = {}
    for c in ranked:
        src = c.get("document_id") or c.get("event_id") or "none"
        line = render(c)
        if per_src.get(src, 0) >= 3:
            deferred.append((c, line))
            continue
        if used + tokens(line) > budget:
            cut.append(c)
            continue
        per_src[src] = per_src.get(src, 0) + 1
        used += tokens(line)
        kept.append(line)
    for c, line in deferred:
        if used + tokens(line) > budget:
            cut.append(c)
            continue
        used += tokens(line)
        kept.append(line)
    cl = ["## Claims (scored)", ""] + (kept or ["- (none)"])
    if cut:
        cl += ["", f"_Cut for budget/diversity: {len(cut)} more claims._"]

    audit = {"lens": lens, "mode": mode, "claims_layer": "live" if live else "not migrated (S1a pending)",
             "seeds_resolved": len(found), "seeds_unresolved": missing, "events": len(nb["events"]),
             "edges": len(nb["edges"]), "claims_candidates": len(ranked), "claims_kept": len(kept),
             "claims_cut": len(cut), "tokens": used, "budget": budget, "prior_posts": len(posts)}
    audit_line = (f"AUDIT · lens={lens} · seeds={len(found)} resolved/{len(missing)} unresolved · "
                  f"events={audit['events']} · claims {len(kept)} kept/{len(cut)} cut · docs={len(nb.get('documents', []))} · "
                  f"tokens {used}/{budget} · graph={mode} · claims-layer={audit['claims_layer']}"
                  + (f" · prior_posts={len(posts)}" if lens == "content" else ""))
    lines += [f"_{audit_line}_", ""]
    if missing:
        lines += [f"**Unresolved seeds (reported, not guessed):** {', '.join(missing)}", ""]
    lines += (said + [""] if said else []) + ledger + [""] + cards + [""] + tcards + [""] + cl + [""]

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


def selftest() -> bool:
    """Offline: the prior-post merge (YED-208)."""
    checks = []
    docs = {d["id"]: d for d in [
        {"id": "d1", "title": "Shortlist Aug recap", "doc_date": "2026-08-25", "metadata": {"published_url": "https://li/1"}, "event_id": "e1"},
        {"id": "d2", "title": "Memory for agents", "doc_date": "2026-09-10", "metadata": {"published_url": "https://li/2"}, "event_id": "e2"},
        {"id": "d3", "title": "No URL draft", "doc_date": "2026-09-01", "metadata": {}, "event_id": "e3"},
        {"id": "d4", "title": "Weak match", "doc_date": "2026-07-01", "metadata": {"published_url": "https://li/4"}, "event_id": "e4"}]}
    res = merge_prior_posts([docs["d1"]], [{"document_id": "d2", "similarity": .71}, {"document_id": "d2", "similarity": .60},
                                           {"document_id": "d3", "similarity": .90}, {"document_id": "d4", "similarity": .40},
                                           {"document_id": "zz", "similarity": .99}],
                            docs, {"d1": "hit"}, {"t1": "Founder Hiring"}, {"d1": ["Founder Hiring"]})
    checks.append(("relational hit ranks first, carries why + outcome",
                   res[0]["id"] == "d1" and res[0]["outcome"] == "hit" and res[0]["why"] == ["shares Founder Hiring"]))
    checks.append(("semantic hit kept at its BEST chunk similarity, once", [r["id"] for r in res] == ["d1", "d2"]
                   and res[1]["why"] == ["similar text 0.71"]))
    checks.append(("a post without a URL is never offered (no back-link possible)", "d3" not in [r["id"] for r in res]))
    checks.append(("a semantic hit below the floor is dropped", "d4" not in [r["id"] for r in res]))
    checks.append(("a chunk whose document is not a current linkedin_post is ignored", "zz" not in [r["id"] for r in res]))
    focused = {"id": "f", "title": "Focused", "doc_date": "2026-06-01", "metadata": {"published_url": "u1"}}
    roundup = {"id": "r", "title": "Roundup", "doc_date": "2026-09-01", "metadata": {"published_url": "u2"}}
    order = merge_prior_posts([roundup, focused], [], {"f": focused, "r": roundup}, {}, {},
                              {"f": ["A", "B", "C"], "r": ["A"]})
    checks.append(("more shared seed entities outranks a newer roundup sharing one", [r["id"] for r in order] == ["f", "r"]))
    checks.append(("cap respected", len(merge_prior_posts([], [{"document_id": f"x{i}", "similarity": .9} for i in range(9)],
                                                          {f"x{i}": {"id": f"x{i}", "metadata": {"published_url": "u"}} for i in range(9)},
                                                          {}, {}, {})) == MAX_PRIOR_POSTS))
    checks.append(("content lens keeps w_use = 0 (ADR-10 D8 over the architecture table)", LENSES["content"]["use"] == 0.0))
    fail = 0
    for name, good in checks:
        fail += 0 if good else 1
        print(f"  {'✓' if good else '✗'} {name}")
    print(f"selftest: {len(checks) - fail}/{len(checks)} pass")
    return fail == 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return 0 if selftest() else 1
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
