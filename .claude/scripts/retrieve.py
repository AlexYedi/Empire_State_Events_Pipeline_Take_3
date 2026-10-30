#!/usr/bin/env python3
"""retrieve — the ONE retrieval interface over the Knowledge Substrate (ADR-10; YED-170).

Spec: docs/archive/notes/knowledge-substrate-architecture-2026-09-18.md §3.1–3.3, as amended by
docs/archive/notes/knowledge-substrate-review-2026-09-18.md (findings 5 + 6). W1 ships ONE lens (`event`);
the other lenses are six weights each and land once this one has proven out on a real brief (A/B).
The A/B (YED-172) kept the legacy pre-event pull, so no command calls this today; it stays as ADR-10
D4's one retrieval path (Amendment 1: the job-search lens), not removed without a successor ADR.

    .venv/bin/python .claude/scripts/retrieve.py --lens event --seed seed.json [--budget-tokens 6000]
                     [--out pack.md] [--json]
    .venv/bin/python .claude/scripts/retrieve.py --selftest      (offline: job-lens isolation, YED-149)

seed.json: {"entities": [{"type": "person|company|topic", "name": "...", "notion_page_id": "..."}],
            "text": "<VERBATIM invite / question>", "focus": "<Alex's stated focus>", "window_days": 365}

What it does (for every lens):
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

The `company` lens (YED-260; spec of record docs/prd-company-dossier.md §4) adds the missing person
hop on top of the same pull/score/budget path: person.company_id = seed -> their asserted_by/about
claims, plus first-hand claims whose text names the company (whole words only, kept only when the
claim's event also involves the company or a person at the company is linked — §9 mitigation).
Company-specific claims are ordered first, room context after; the weights are the only knob (ADR-10).
"""
from __future__ import annotations
import argparse, datetime as dt, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from spine_client import q, req  # noqa: E402
from substrate import JOB_LENS_KINDS, norm_text, pid_variants  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

LENSES = {  # the weights ARE the lens. w_use is 0 everywhere until >=20 outcome rows (decision 5)
    "event": {"sem": .30, "rel": .35, "rec": .15, "prov": .10, "conf": .10, "use": 0.0, "budget": 6000},
    # company (YED-260, docs/prd-company-dossier.md §4): relational + provenance up, semantic down —
    # the pack is a documented graph walk (people at the company, then text-named first-hand claims),
    # so provenance/relational carry it and the semantic rank is a tiebreaker, not the spine.
    "company": {"sem": .10, "rel": .40, "rec": .10, "prov": .25, "conf": .15, "use": 0.0, "budget": 6000},
}
PROV = {"first_hand": 1.0, "web_verified": .9, "email_signal": .7, "notion_prior": .6, "reference": .5,
        "model_inferred": .3}
HALF_LIFE_DAYS = 90


def tokens(s: str) -> int:
    return math.ceil(len(s) / 4)


CLAIM_COLS = ("id,claim_text,claim_type,provenance_tier,confidence,asserted_at,event_id,"
              "document_id,status,metadata")


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
        flt += f"&kind=not.in.({','.join(JOB_LENS_KINDS)})"      # YED-149: the job lens never fills the ledger
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
    # hiring=[] (not None): this path already excluded the job lens in its query, so there is nothing to count here —
    # isolate_job_lens must not label it "client-side, counts partial" (judge, 2026-09-27).
    return ({"events": events, "edges": edges, "documents": [], "claims": [], "hiring": [], "_hiring_path": "rest-fallback"},
            "rest-fallback (0010 not applied)")


def claim_layer_live() -> bool:
    st, _ = req("GET", "/claim?select=id&limit=1")
    return st == 200


def fetch_claims(ids: list[str]) -> list[dict]:
    """Claim rows by id (chunked), excluding rejected. Empty ids -> no call."""
    out: list[dict] = []
    for i in range(0, len(ids), 80):
        out += get(f"/claim?id=in.({','.join(ids[i:i + 80])})&status=neq.rejected&select={CLAIM_COLS}") or []
    return out


def name_pattern(name: str) -> re.Pattern:
    """PRD §9 (common-word names): a company name matches as whole words only, case-insensitive,
    whitespace-normalized — 'Seek' matches 'what Seek announced', never 'seeking' or 'Seekr'."""
    words = [re.escape(w) for w in name.split() if w]
    return re.compile(r"(?<![A-Za-z0-9])" + r"\s+".join(words) + r"(?![A-Za-z0-9])", re.I)


def text_match_qualifies(claim: dict, name: str, nb_event_ids: set[str], person_claim_ids: set[str]) -> bool:
    """PRD §4 text pull with the §9 mitigation: the whole-word name match counts only when the claim's
    event also involves the company (in the seed neighborhood) or a person at the company is linked —
    a text match alone is never enough. Pure."""
    if not name_pattern(name).search(claim.get("claim_text") or ""):
        return False
    return claim.get("event_id") in nb_event_ids or claim.get("id") in person_claim_ids


def prioritize_company(ranked: list[dict], company_specific: set[str]) -> list[dict]:
    """PRD §4 ordering: company-specific claims first, room context from the same events after.
    ranked arrives score-sorted; stable bucket concatenation keeps score order inside each bucket."""
    return ([c for c in ranked if c["id"] in company_specific]
            + [c for c in ranked if c["id"] not in company_specific])


def company_hop(found: list[dict], nb: dict) -> tuple[list[dict], set[str], list[dict]]:
    """YED-260 — the missing hop (PRD §4, evidenced §6): the `event` lens kept 28 company-relevant
    claims but 0 of the 8 people at the company. This pulls, for the company seeds:
      1 people at the company (person.company_id = seed),
      2 the claims those people asserted (asserted_by) or are about,
      3 first-hand claims whose text names a seed company (whole words + §9 mitigation).
    Returns (extra claims, company-specific claim ids, company people). Company-specific covers the
    person-hop and text pulls PLUS claims already linked directly to a seed company. No DDL, no writer.
    Pure when `found` holds no company (returns empty without touching the network)."""
    cos = [f for f in found if f["type"] == "company"]
    if not cos:
        return [], set(), []
    co_ids = [c["id"] for c in cos]
    direct: set[str] = set()
    for i in range(0, len(co_ids), 80):
        direct |= {r["claim_id"] for r in get(f"/claim_entity?entity_id=in.({','.join(co_ids[i:i + 80])})"
                                              f"&entity_type=eq.company&select=claim_id") or []}
    people: list[dict] = []
    for i in range(0, len(co_ids), 80):
        people += get(f"/person?company_id=in.({','.join(co_ids[i:i + 80])})&select=id,name,title") or []
    person_ids = sorted({p["id"] for p in people if p.get("id")})
    person_claims: set[str] = set()
    for i in range(0, len(person_ids), 80):
        person_claims |= {r["claim_id"] for r in
                          get(f"/claim_entity?entity_id=in.({','.join(person_ids[i:i + 80])})&entity_type=eq.person"
                              f"&role=in.(asserted_by,about)&select=claim_id") or []}
    extra: dict[str, dict] = {}
    for c in fetch_claims(sorted(person_claims - direct)):      # nb claims arrive separately; skip doubles
        extra[c["id"]] = {**c, "_direct": True, "_person_hop": True}
    nb_ev = {e["id"] for e in nb.get("events", [])}
    for co in cos:
        rows = get(f"/claim?claim_text=ilike.{q('*' + co['name'] + '*')}&provenance_tier=eq.first_hand"
                   f"&status=neq.rejected&select={CLAIM_COLS}&order=asserted_at.desc&limit=200") or []
        for c in rows:
            if c["id"] in extra or c["id"] in direct:
                continue
            if text_match_qualifies(c, co["name"], nb_ev, person_claims):
                extra[c["id"]] = {**c, "_text_match": co["name"]}
    return list(extra.values()), direct | set(extra), [p for p in people if p.get("id")]


def semantic_claims(text: str, ids: list[str], n: int) -> list[dict]:
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


def isolate_job_lens(nb: dict, seed_companies: dict[str, str]) -> tuple[dict, list[dict], str]:
    """YED-149 (Alex, option 1): job-lens kinds never reach a brief's ledger — the seed companies get one COUNT line
    each instead ("Harvey — 6 tracked roles"), and applications/interviews appear nowhere. Migration 0011 does this
    server-side (before the `limit`, so roles can't crowd events out) and returns `hiring`; before 0011 lands the
    same filter runs here and the counts are partial (only roles that fit under the old limit). Pure."""
    job = {e["id"] for e in nb.get("events", []) if e.get("kind") in JOB_LENS_KINDS}
    hiring = nb.get("hiring")
    path = ("rest-fallback (no hiring counts)" if nb.get("_hiring_path") == "rest-fallback" else
            "rpc (0011)" if hiring is not None else "client-side (0011 not applied: counts partial, crowding possible)")
    if hiring is None:
        per: dict[str, dict] = {}
        roles = {e["id"]: e for e in nb.get("events", []) if e.get("kind") == "role_posted"}
        for x in nb.get("edges", []):
            if x["event_id"] in roles and x["entity_type"] == "company" and x["entity_id"] in seed_companies:
                h = per.setdefault(x["entity_id"], {"company_id": x["entity_id"], "name": seed_companies[x["entity_id"]],
                                                    "roles": 0, "latest_posted": None})
                h["roles"] += 1
                d = roles[x["event_id"]].get("event_date")
                h["latest_posted"] = max(filter(None, (h["latest_posted"], d)), default=None)
        hiring = list(per.values())
    kept = {**nb, "events": [e for e in nb.get("events", []) if e["id"] not in job],
            "edges": [x for x in nb.get("edges", []) if x["event_id"] not in job],
            "claims": [c for c in nb.get("claims", []) if c.get("event_id") not in job]}
    return kept, hiring, path


def hiring_lines(hiring: list[dict]) -> list[str]:
    out = []
    for h in sorted(hiring, key=lambda r: (-int(r.get("roles") or 0), r.get("name") or "")):
        tiers = " ".join(f"{t}:{h[k]}" for t, k in (("A", "tier_a"), ("B", "tier_b"), ("C", "tier_c")) if h.get(k))
        latest = f", latest posted {str(h['latest_posted'])[:10]}" if h.get("latest_posted") else ""
        out.append(f"- **{h['name']}** — {h['roles']} tracked role{'s' if int(h['roles']) != 1 else ''}"
                   f"{f' ({tiers})' if tiers else ''}{latest}")
    return out


def build_pack(seed: dict, lens: str, budget: int) -> tuple[str, dict, int]:
    w = LENSES[lens]
    found, missing = resolve(seed.get("entities", []))
    ids = [f["id"] for f in found]
    since = None
    if seed.get("window_days"):
        since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=int(seed["window_days"]))).strftime("%Y-%m-%dT00:00:00Z")
    nb, mode = neighborhood(ids, since) if ids else ({"events": [], "edges": [], "documents": [], "claims": []}, "no seeds")
    nb, hiring, job_path = isolate_job_lens(nb, {f["id"]: f["name"] for f in found if f["type"] == "company"})
    live = claim_layer_live()
    claims = {c["id"]: {**c, "_direct": True} for c in nb.get("claims", [])}
    company_specific: set[str] = set()
    company_people: list[dict] = []
    if lens == "company":                          # YED-260: the person hop + text pull (PRD §4)
        extra, company_specific, company_people = company_hop(found, nb)
        for c in extra:
            claims.setdefault(c["id"], c)
    if live and seed.get("text"):
        for c in semantic_claims(seed["text"], ids, 30):
            claims.setdefault(c["id"], c)["_semantic"] = True
    nb_ev = {e["id"] for e in nb["events"]}
    ranked = score_claims(list(claims.values()), set(ids), nb_ev, w)
    if lens == "company":                          # PRD §4: company-specific first, room context after
        ranked = prioritize_company(ranked, company_specific)
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
    if lens == "company":      # YED-260: people at the company get cards even without a shared occasion
        for p in company_people:
            if p["id"] not in people and p["id"] not in seed_names:
                people[p["id"]] = {"name": p["name"], "seen": [], "title": p.get("title"),
                                   "_company_roster": True}
    cards = ["## People — seeds and returning faces", ""]
    for pid, p in sorted(people.items(), key=lambda kv: (-len(kv[1]["seen"]), kv[1]["name"])):
        if pid in seed_names or len(p["seen"]) >= 2 or p.get("_company_roster"):
            title = f" ({p['title']})" if p.get("title") else ""
            seen = (f" — seen at {len(p['seen'])}: " + "; ".join(p["seen"][:4]) if p["seen"]
                    else " — person at the company (no shared occasion in this pack)")
            cards.append(f"- **{p['name']}**{title}{seen}")
    topics: dict[str, set] = {}
    for x in nb["edges"]:
        if x["entity_type"] == "topic" and x.get("name"):
            topics.setdefault(x["name"], set()).add(x["event_id"])
    tcards = ["## Topics recurring across these occasions", ""] + [
        f"- {name} — {len(evs)} occasions" for name, evs in sorted(topics.items(), key=lambda kv: -len(kv[1]))[:15]]

    hire = (["## Hiring at seed companies — job lens, counts only", ""] + hiring_lines(hiring)) if hiring else []

    # ---- claims under the token budget ------------------------------------------------------------
    used = sum(tokens("\n".join(s)) for s in (ledger, cards, tcards, hire))
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
    kept_ids: list[str] = []                       # YED-262: what a read kept, so usage can be logged
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
        kept_ids.append(c["id"])
    for c, line in deferred:
        if used + tokens(line) > budget:
            cut.append(c)
            continue
        used += tokens(line)
        kept.append(line)
        kept_ids.append(c["id"])
    cl = ["## Claims (scored)", ""] + (kept or ["- (none)"])
    if cut:
        cl += ["", f"_Cut for budget/diversity: {len(cut)} more claims._"]

    audit = {"lens": lens, "mode": mode, "claims_layer": "live" if live else "not migrated (S1a pending)",
             "seeds_resolved": len(found), "seeds_unresolved": missing, "events": len(nb["events"]),
             "edges": len(nb["edges"]), "claims_candidates": len(ranked), "claims_kept": len(kept),
             "claims_cut": len(cut), "tokens": used, "budget": budget,
             "hiring_companies": len(hiring), "job_lens_filter": job_path, "kept_claim_ids": kept_ids}
    if lens == "company":
        audit["company_specific"] = len(company_specific)
        audit["company_people"] = len(company_people)
    audit_line = (f"AUDIT · lens={lens} · seeds={len(found)} resolved/{len(missing)} unresolved · "
                  f"events={audit['events']} · claims {len(kept)} kept/{len(cut)} cut · docs={len(nb.get('documents', []))} · "
                  f"tokens {used}/{budget} · graph={mode} · claims-layer={audit['claims_layer']} · "
                  f"job-lens filter={job_path}")
    if lens == "company":
        audit_line += f" · company-specific={len(company_specific)} · company-people={len(company_people)}"
    lines += [f"_{audit_line}_", ""]
    if missing:
        lines += [f"**Unresolved seeds (reported, not guessed):** {', '.join(missing)}", ""]
    lines += ledger + [""] + cards + [""] + tcards + [""] + (hire + [""] if hire else []) + cl + [""]

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
    """Offline (no network): the job-lens isolation contract (YED-149)."""
    nb = {"events": [{"id": "e1", "kind": "attended", "title": "Demo Night", "event_date": "2026-09-01"},
                     {"id": "r1", "kind": "role_posted", "title": "AE — Harvey", "event_date": "2026-09-20"},
                     {"id": "r2", "kind": "role_posted", "title": "CSM — Harvey", "event_date": "2026-09-22"},
                     {"id": "a1", "kind": "application", "title": "Applied — Harvey", "event_date": "2026-09-23"}],
          "edges": [{"event_id": i, "entity_type": "company", "entity_id": "co1", "role": "subject", "name": "Harvey"}
                    for i in ("e1", "r1", "r2", "a1")],
          "claims": [{"id": "c1", "event_id": "a1"}, {"id": "c2", "event_id": "e1"}], "documents": []}
    kept, hiring, path = isolate_job_lens(nb, {"co1": "Harvey"})
    rpc_kept, rpc_hiring, rpc_path = isolate_job_lens({**nb, "hiring": [{"name": "Harvey", "roles": 6, "tier_a": 2,
                                                                          "tier_b": 4, "latest_posted": "2026-09-22"}]}, {})
    checks = [
        ("no job-lens kind in the ledger", [e["id"] for e in kept["events"]] == ["e1"]),
        ("job-lens edges + claims dropped", {x["event_id"] for x in kept["edges"]} == {"e1"}
         and [c["id"] for c in kept["claims"]] == ["c2"]),
        ("client-side count: roles only, never applications", hiring == [{"company_id": "co1", "name": "Harvey", "roles": 2,
                                                                          "latest_posted": "2026-09-22"}]),
        ("client-side path is labelled partial", path.startswith("client-side")),
        ("rpc hiring wins + labelled", rpc_path == "rpc (0011)" and rpc_hiring[0]["roles"] == 6),
        ("count line format", hiring_lines(rpc_hiring) == ["- **Harvey** — 6 tracked roles (A:2 B:4), latest posted 2026-09-22"]),
        ("no seed company -> no hiring lines", isolate_job_lens(nb, {})[1] == []),
        ("rest-fallback path is labelled as such, never 'partial'",
         isolate_job_lens({**nb, "hiring": [], "_hiring_path": "rest-fallback"}, {"co1": "Harvey"})[2]
         == "rest-fallback (no hiring counts)"),
    ]
    # ---- company lens (YED-260) — pure helpers on inline fixtures, no network --------------------
    w_ev, w_co = LENSES["event"], LENSES["company"]
    ranked = [{"id": "a", "_score": .9}, {"id": "b", "_score": .8}, {"id": "c", "_score": .7}]
    checks += [
        ("company lens: rel+prov up, sem down, w_use still 0 (ADR-10 decision 5)",
         w_co["rel"] > w_ev["rel"] and w_co["prov"] > w_ev["prov"] and w_co["sem"] < w_ev["sem"]
         and w_co["use"] == 0),
        ("company lens: weights still sum to 1", abs(sum(v for k, v in w_co.items() if k != "budget") - 1) < 1e-9),
        ("name_pattern: whole words only, case-insensitive, multi-space ok",
         bool(name_pattern("Seek").search("what Seek announced"))
         and not name_pattern("Seek").search("seeking")
         and not name_pattern("Seek").search("Seekr builds")
         and bool(name_pattern("Veris AI").search("when  VERIS   ai  shipped"))),
        ("text_match_qualifies: event overlap or person link required (PRD §9)",
         text_match_qualifies({"claim_text": "Seek ships X", "id": "t1", "event_id": "e1"}, "Seek", {"e1"}, set())
         and text_match_qualifies({"claim_text": "Seek ships X", "id": "t1", "event_id": None}, "Seek", set(), {"t1"})
         and not text_match_qualifies({"claim_text": "Seek ships X", "id": "t1", "event_id": None},
                                      "Seek", {"e1"}, set())
         and not text_match_qualifies({"claim_text": "Seeking teams", "id": "t1", "event_id": "e1"},
                                      "Seek", {"e1"}, set())),
        ("prioritize_company: specific first, score order kept in each bucket",
         [c["id"] for c in prioritize_company(ranked, {"b"})] == ["b", "a", "c"]),
        ("company_hop: no company seed -> empty, no network", company_hop([], {}) == ([], set(), [])),
    ]
    for name, good in checks:
        print(f"  {'✓' if good else '✗'} {name}")
    fail = sum(1 for _, g in checks if not g)
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
