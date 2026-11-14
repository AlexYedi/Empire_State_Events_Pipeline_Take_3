#!/usr/bin/env python3
"""claim_extract_v2 — graph-v2 claim extraction from research briefs (YED-384, ADR-15 decisions 2, 3, 4, 8).

The pilot-proven extractor (judge pilot 2026-11-12/13: extract-v4 prompt, check_v3, Claude judge) moved into the repo.
Like prose_extract.py, this file never writes to the spine: `substrate.py stage-v2` is the writer, and it re-runs
`check` against the brief itself, so nothing here is trusted by the writer.

Verbs:
  extract <brief_dir> [--model sonnet] [--out claims.json] [--packet-out packet.json]
          prose_extract.prepass_doc packet -> references/claim-extractor-v2-prompt.md -> headless tool-less
          `claude -p` (prose_extract.llm_cmd, from an empty temp dir) -> {"claims": [...]}.
  check   <packet> <claims.json> [--model ID] [--out checked.json]
          the mechanical gate (DROPS, never rewrites): exact keys, claim_type vocab, evidence 1-8 spans of
          {para_idx, quote}, each quote <= 25 words and verbatim (whitespace aside) in its paragraph, every number
          in the claim present in a cited paragraph / as_of / the event line, no contact PII (raw + normalized), no
          URL or `@` in the text. attribution_unquoted ("X says" with no attribution in any cited quote) is a FLAG,
          never a drop. claim_key = prose_extract.prose_claim_key(first para_idx, first quote).
  judge   <packet> <checked.json> [--model claude-fable-5-2] [--batch 20] [--out judged.json]
          the ADR-15 d4 judge (references/claim-judge-v2-prompt.md), batched, span-scoped (claim + every cited
          paragraph + event line). Each row gets {verdict supported|unsupported|abstain, model, prompt_hash (sha256 of
          the template file), judged_at, standalone, useful, why}. A pid the judge leaves out -> abstain. A batch
          whose call fails twice raises: no judged file is written, so a rerun retries it.
  batch   --briefs-dir D --out-dir O [--model sonnet] [--judge-model claude-fable-5-2] [--concurrency 4]
          prepass -> extract -> check -> judge for every eligible brief (prose_extract.batch's rules: no dossier,
          manifest + research_brief.md present, not skip_staging, event page id, no ledger). Files only.
Staging: `substrate.py stage-v2 --checked O/<brief>.v2.judged.json --manifest D/<brief>/manifest.json [--dry-run]`.

Self-test (offline, fixtures under fixtures/claim_v2/ + fixtures/prose/, LLM stubbed):
  python3 .claude/scripts/claim_extract_v2.py --selftest
"""
from __future__ import annotations
import argparse, datetime as _dt, hashlib, json, os, re, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from prose_extract import (DOSSIER_PREFIX, URL_OR_AT_RE, LLMError, has_pii, llm_cmd, parse_reply,  # noqa: E402
                           prepass, prepass_doc, prose_claim_key, ws, words)
from substrate import research_source_key  # noqa: E402

SCHEMA = "claimify-v2/1"
EXTRACTION = "claimify_v2"                      # claim.metadata.extraction for every v2 row
REFS = os.path.join(HERE, "..", "references")
EXTRACT_PROMPT_PATH = os.path.join(REFS, "claim-extractor-v2-prompt.md")
JUDGE_PROMPT_PATH = os.path.join(REFS, "claim-judge-v2-prompt.md")
EXTRACT_MODEL, JUDGE_MODEL = "sonnet", "claude-fable-5-2"
KEYS = {"text", "evidence", "entity", "claim_type", "as_of", "time_sensitive"}
TYPES = {"launch", "funding", "metric", "adoption", "partnership", "people_move", "company_fact", "thesis", "prediction"}
TEXT_MAX_WORDS, QUOTE_MAX_WORDS, MAX_SPANS = 40, 25, 8   # 25 = the 0009 licensing guard, per span (0023 CHECK)
CONF_CAP = 0.60
CONF = {"web_verified": 0.55, "reference": 0.40}           # prose_extract's tiers
VERDICTS = ("supported", "unsupported", "abstain")
NUM = re.compile(r"\$?\d[\d,.]*\s*(?:%|[kKmMbB]n?\b|billion|million|thousand)?")       # pilot.py, unchanged
ATTRIB = re.compile(r"\b(says|said|reports|reported|claims|claimed|according to|states|stated|announced)\b", re.I)
ATTRIB_SRC = re.compile(r"\b(say|says|said|report|reports|reported|claim|claims|claimed|according|per|states|stated|"
                        r"told|announc\w*)\b|[\"\u201c]", re.I)


def prompt_hash(path: str = JUDGE_PROMPT_PATH) -> str:
    """sha256 of the exact judge prompt template (ITEMS placeholder included) = claim.judge_prompt_hash."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------------------------------------------
class GateError(Exception):
    """A whole-file failure. Messages name a reason only, never claim text."""


def _reason(c, paras: dict) -> str | None:
    if not isinstance(c, dict) or set(c) != KEYS:
        return "schema_keys"
    if not (isinstance(c["text"], str) and isinstance(c["entity"], str) and c["entity"].strip()
            and (c["as_of"] is None or isinstance(c["as_of"], str)) and isinstance(c["time_sensitive"], bool)):
        return "schema_type"
    if c["claim_type"] not in TYPES:
        return "claim_type"
    ev = c["evidence"]
    if not isinstance(ev, list) or not 1 <= len(ev) <= MAX_SPANS or any(
            not isinstance(e, dict) or set(e) != {"para_idx", "quote"} or not isinstance(e["quote"], str)
            or isinstance(e["para_idx"], bool) or not isinstance(e["para_idx"], int) for e in ev):
        return "evidence_shape"
    if any(e["para_idx"] not in paras for e in ev):
        return "evidence_para_idx"
    if has_pii(c["text"], c["entity"], c["as_of"], *(e["quote"] for e in ev)):
        return "pii_contact_detail"
    if any(not ws(e["quote"]) or words(e["quote"]) > QUOTE_MAX_WORDS for e in ev):
        return "evidence_quote_empty_or_over_25_words"
    if not ws(c["text"]) or words(c["text"]) > TEXT_MAX_WORDS:
        return "text_empty_or_over_40_words"
    if URL_OR_AT_RE.search(c["text"]):
        return "text_has_url_or_at"
    if any(ws(e["quote"]) not in ws(paras[e["para_idx"]]["text"]) for e in ev):
        return "evidence_not_verbatim"
    return None


def event_line(packet: dict) -> str:
    return " ".join(str(v) for v in (packet.get("event") or {}).values() if isinstance(v, (str, int)))


def check(packet: dict, claims_doc, *, model: str | None = None) -> dict:
    """claims doc -> checked doc. Accepted rows keep the extractor's fields plus source_key, claim_key, the derived
    provenance (a URL only when the first span's paragraph has exactly one), the entity's roster resolution and the
    attribution_unquoted flag."""
    from prose_extract import resolve_entity
    from substrate import ROSTER_TIE
    if not isinstance(claims_doc, dict) or set(claims_doc) != {"claims"} or not isinstance(claims_doc["claims"], list):
        raise GateError('claims file must be exactly {"claims": [...]} (top-level schema)')
    paras = {p["idx"]: p for p in packet["paragraphs"]}
    roster = [(r["type"], r["name"], r["name"]) for r in packet["roster"]]
    ev_line = event_line(packet)
    dropped: dict[str, int] = {}
    flags = {"attribution_unquoted": 0, "entity_off_roster": 0, "multi_span": 0}
    accepted, seen = [], set()
    for c in claims_doc["claims"]:
        why = _reason(c, paras)
        if not why:
            src = " ".join(paras[e["para_idx"]]["text"] for e in c["evidence"]) + " " + ev_line
            nums = [n.strip().rstrip(".,") for n in NUM.findall(c["text"]) if any(ch.isdigit() for ch in n)]
            if any(n and n not in src and n not in (c["as_of"] or "") for n in nums):
                why = "number_not_in_source"
        key = None if why else prose_claim_key(c["evidence"][0]["para_idx"], c["evidence"][0]["quote"])
        if not why and key in seen:
            why = "duplicate_claim"
        if why:
            dropped[why] = dropped.get(why, 0) + 1
            continue
        seen.add(key)
        ev = [{"para_idx": e["para_idx"], "quote": ws(e["quote"])} for e in c["evidence"]]
        # Flag, never drop (pilot v3: 3 real errors, 6 correct research-source claims). Oversampled in 4b labels.
        unquoted = bool(ATTRIB.search(c["text"]) and not any(ATTRIB_SRC.search(e["quote"]) for e in ev))
        hit = resolve_entity(c["entity"], roster)
        etype, ename = (None, None) if hit is None or hit is ROSTER_TIE else hit
        first = paras[ev[0]["para_idx"]]
        url = first["urls"][0] if len(first.get("urls") or []) == 1 else None
        tier = "web_verified" if url else "reference"
        flags["attribution_unquoted"] += unquoted
        flags["entity_off_roster"] += ename is None
        flags["multi_span"] += len({e["para_idx"] for e in ev}) > 1
        accepted.append({"source_key": packet["source_key"], "claim_key": key, "text": ws(c["text"]), "evidence": ev,
                         "entity": c["entity"], "entity_type": etype, "entity_name": ename,
                         "claim_type": c["claim_type"], "as_of": c["as_of"], "time_sensitive": c["time_sensitive"],
                         "attribution_unquoted": unquoted, "url": url, "provenance_tier": tier,
                         "confidence": min(CONF[tier], CONF_CAP), "extractor": "claude", "extractor_model": model})
    return {"schema": SCHEMA, "source_key": packet["source_key"], "extractor": "claude", "extractor_model": model,
            "claims_in": len(claims_doc["claims"]), "accepted_n": len(accepted), "dropped": dropped, "flags": flags,
            "accepted": accepted}


def as_claim(r: dict) -> dict:
    """A checked row back into the extractor's schema, so `check` can judge it again from scratch (stage-v2)."""
    return {k: r.get(k) for k in KEYS}


# ---------------------------------------------------------------------------------------------------------------
# freshness v0 (ADR-15 d8 baseline: claim_type + time_sensitive lookup) and validity
# ---------------------------------------------------------------------------------------------------------------
STABLE_TYPES = ("launch", "funding", "people_move", "partnership")


def freshness_v0(claim_type: str, time_sensitive: bool, now: _dt.datetime) -> tuple[str, str | None]:
    """-> (freshness_class, next_check_at). Order matters: an opinion is never re-verified, even if time-sensitive."""
    if claim_type in ("thesis", "prediction"):
        return "opinion", None
    if time_sensitive:
        return "fast_moving", (now + _dt.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    if claim_type in STABLE_TYPES:
        return "historical", None
    return "slow_moving", (now + _dt.timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%SZ")


def valid_from(as_of) -> str | None:
    """A full calendar date only ('2026-02-03'); a month, quarter or year is too coarse to start a window."""
    if not isinstance(as_of, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", as_of.strip()):
        return None
    try:
        return _dt.date.fromisoformat(as_of.strip()).isoformat() + "T00:00:00Z"
    except ValueError:
        return None


# ---------------------------------------------------------------------------------------------------------------
# LLM calls (same isolation as prose_extract.run_llm: no tools, no MCP, no setting sources, empty temp cwd)
# ---------------------------------------------------------------------------------------------------------------
def call_llm(prompt: str, model: str, timeout: int = 1800) -> tuple[dict, str, str]:
    import subprocess
    with tempfile.TemporaryDirectory() as cwd:
        p = subprocess.run(llm_cmd(model), input=prompt, capture_output=True, text=True, cwd=cwd, timeout=timeout)
    return parse_reply(p.stdout, p.returncode), p.stdout, p.stderr


def extract_prompt(packet: dict) -> str:
    """The pilot's exact substitution (pilot.py _extract_one): indent 1, no trailing newline."""
    return open(EXTRACT_PROMPT_PATH, encoding="utf-8").read().replace(
        "{PACKET_JSON}", json.dumps(packet, indent=1, ensure_ascii=False))


def extract(packet: dict, *, model: str = EXTRACT_MODEL, llm=None) -> tuple[dict, str, str]:
    """One extraction, redispatched once on a failed call or an unparseable reply (pilot: 2 tries)."""
    llm = llm or call_llm
    try:
        return llm(extract_prompt(packet), model)
    except LLMError:
        return llm(extract_prompt(packet), model)


def doc_of(r: dict, paras: dict, ev: dict) -> str:
    """judges.doc_of, span-scoped: event title + date, then every cited paragraph under its section / heading."""
    idxs = list(dict.fromkeys(e["para_idx"] for e in r["evidence"]))
    spans = "\n\n".join(f"[{i}] {' / '.join(x for x in (paras[i].get('section'), paras[i].get('heading')) if x)}\n"
                        f"{paras[i]['text']}" for i in idxs)
    return f"Event: {ev.get('title') or ''}\nDate: {ev.get('event_date') or ''}\n\n{spans}"


def judge(packet: dict, checked: dict, *, model: str = JUDGE_MODEL, batch: int = 20, llm=None) -> dict:
    """checked doc -> judged doc (same shape; every accepted row gains `judge`)."""
    llm = llm or call_llm
    template = open(JUDGE_PROMPT_PATH, encoding="utf-8").read()
    h = prompt_hash()
    paras = {p["idx"]: p for p in packet["paragraphs"]}
    rows = [dict(r) for r in checked.get("accepted") or []]
    counts = {v: 0 for v in VERDICTS}
    for i in range(0, len(rows), max(1, batch)):
        chunk = rows[i:i + batch]
        items = [{"pid": f"c{i + j:03d}", "claim": r["text"], "passage": doc_of(r, paras, packet.get("event") or {})}
                 for j, r in enumerate(chunk)]
        prompt = template.replace("ITEMS", json.dumps(items, indent=1, ensure_ascii=False))
        try:
            doc, _, _ = llm(prompt, model)
        except LLMError:
            doc, _, _ = llm(prompt, model)                # twice failed -> raises: no judged file, rerun retries
        at = utcnow()
        labels = {l.get("pid"): l for l in (doc.get("labels") or []) if isinstance(l, dict)}
        for j, r in enumerate(chunk):
            lab = labels.get(f"c{i + j:03d}") or {}
            sup = lab.get("supported")
            verdict = {"yes": "supported", "no": "unsupported"}.get(sup, "abstain")
            useful = lab.get("useful") if lab.get("useful") in (1, 2, 3) else None
            r["judge"] = {"verdict": verdict, "model": model, "prompt_hash": h, "judged_at": at,
                          "standalone": {"yes": True, "no": False}.get(lab.get("standalone")), "useful": useful,
                          "why": lab.get("why") if isinstance(lab.get("why"), str) else None}
            counts[verdict] += 1
    return {**checked, "accepted": rows, "judge": {"model": model, "prompt_hash": h, **counts}}


# ---------------------------------------------------------------------------------------------------------------
# batch (files only; staging stays `substrate.py stage-v2`)
# ---------------------------------------------------------------------------------------------------------------
def batch_run(briefs_dir: str, out_dir: str, *, model: str = EXTRACT_MODEL, judge_model: str = JUDGE_MODEL,
              concurrency: int = 4, ledger_count=None, llm=None) -> dict:
    from concurrent.futures import ThreadPoolExecutor
    from notion_export import ensure_ignored
    from prose_extract import _emit, _prod_ledger_count
    ensure_ignored(out_dir)                          # packets and replies carry brief text: never into a tracked path
    ledger_count = ledger_count or _prod_ledger_count()
    os.makedirs(out_dir, exist_ok=True)
    skipped: dict[str, list[str]] = {}
    todo = []

    def skip(why, name):
        skipped.setdefault(why, []).append(name)
    names = sorted(d for d in os.listdir(briefs_dir) if os.path.isdir(os.path.join(briefs_dir, d)))
    for name in names:
        d = os.path.join(briefs_dir, name)
        if name.startswith(DOSSIER_PREFIX):
            skip("interview_dossier", name); continue
        if not os.path.exists(os.path.join(d, "manifest.json")):
            skip("no_manifest", name); continue
        if not os.path.exists(os.path.join(d, "research_brief.md")):
            skip("no_research_brief", name); continue
        manifest = json.load(open(os.path.join(d, "manifest.json"), encoding="utf-8"))
        if (manifest.get("notion_export") or {}).get("skip_staging") is True:
            skip("skip_staging_otr", name); continue
        pid = (manifest.get("event") or {}).get("notion_page_id")
        if not pid:
            skip("manifest_missing_event_page_id", name); continue
        if ledger_count(research_source_key(pid)) > 0:
            skip("ledger_present", name); continue
        if os.path.exists(os.path.join(out_dir, f"{name}.v2.judged.json")):
            skip("already_judged", name); continue
        pk, why = prepass(d)
        if pk is None:
            skip(why.split(" ")[0], name); continue
        _emit(pk, os.path.join(out_dir, f"{name}.packet.json"))
        todo.append((name, pk))

    def one(item):
        name, pk = item
        try:
            doc, raw, err = extract(pk, model=model, llm=llm)
            for suffix, body in ((".v2.raw.txt", raw), (".v2.err.txt", err)):
                with open(os.path.join(out_dir, name + suffix), "w", encoding="utf-8") as f:
                    f.write(body or "")
            _emit(doc, os.path.join(out_dir, f"{name}.v2.claims.json"))
            ck = check(pk, doc, model=model)
            _emit(ck, os.path.join(out_dir, f"{name}.v2.checked.json"))
            jd = judge(pk, ck, model=judge_model, llm=llm)
            _emit(jd, os.path.join(out_dir, f"{name}.v2.judged.json"))
            return {"brief": name, "claims_in": ck["claims_in"], "accepted_n": ck["accepted_n"],
                    "dropped": ck["dropped"], "judge": {v: jd["judge"][v] for v in VERDICTS}}
        except Exception as e:                       # reason only, never content; a rerun retries it
            return {"brief": name, "error": type(e).__name__}
    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as ex:
        results = list(ex.map(one, todo))
    summary = {"briefs_seen": len(names), "model": model, "judge_model": judge_model,
               "extracted": [r for r in results if "error" not in r], "errors": [r for r in results if "error" in r],
               "skipped_counts": {k: len(v) for k, v in sorted(skipped.items())}, "skipped": skipped,
               "accepted_total": sum(r.get("accepted_n", 0) for r in results)}
    _emit(summary, os.path.join(out_dir, "batch-v2-summary.json"))
    return summary


# ---------------------------------------------------------------------------------------------------------------
# self-test
# ---------------------------------------------------------------------------------------------------------------
FIX = os.path.join(HERE, "fixtures", "claim_v2")
PROSE_FIX = os.path.join(HERE, "fixtures", "prose")


def fixture_packet() -> dict:
    md = open(os.path.join(PROSE_FIX, "brief_ok", "research_brief.md"), encoding="utf-8").read()
    man = json.load(open(os.path.join(PROSE_FIX, "brief_ok", "manifest.json"), encoding="utf-8"))
    return prepass_doc(md, man)[0]


def selftest() -> bool:
    fails = []

    def ok(name, cond):
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")
        if not cond:
            fails.append(name)
    pk = fixture_packet()
    claims = json.load(open(os.path.join(FIX, "claims_mixed.json"), encoding="utf-8"))
    r = check(pk, claims, model="sonnet-fixture")
    acc = {a["text"]: a for a in r["accepted"]}
    d = r["dropped"]
    ok("check: the 4 good fixture claims are accepted", r["accepted_n"] == 4)
    good = next((a for t, a in acc.items() if "founded Acme Widgets in 2019" in t), None)
    ok("check: claim_key = prose_claim_key(first para_idx, first quote)",
       good and good["claim_key"] == prose_claim_key(good["evidence"][0]["para_idx"], good["evidence"][0]["quote"]))
    ok("check: roster entity resolved (type + name); off-roster subject kept and flagged",
       good and good["entity_type"] == "person" and good["entity_name"] == "Dana Fixture"
       and r["flags"]["entity_off_roster"] == 1)
    ok("check: first span's paragraph with exactly one URL -> web_verified @0.55; none -> reference @0.40",
       good and good["provenance_tier"] == "web_verified" and good["confidence"] == 0.55
       and good["url"] == "https://acme.example.com/about"
       and any(a["provenance_tier"] == "reference" and a["confidence"] == 0.40 and a["url"] is None for a in acc.values()))
    multi = next((a for a in acc.values() if len(a["evidence"]) == 2), None)
    ok("check: a multi-span claim (2 paragraphs) passes and is counted", multi is not None and r["flags"]["multi_span"] == 1)
    ok("check: 'says' with no attribution in any cited quote -> FLAG attribution_unquoted, still accepted",
       r["flags"]["attribution_unquoted"] == 1 and any(a["attribution_unquoted"] for a in acc.values()))
    for why, n in (("schema_keys", 2), ("claim_type", 1), ("evidence_shape", 2), ("evidence_para_idx", 1),
                   ("evidence_quote_empty_or_over_25_words", 1), ("evidence_not_verbatim", 1),
                   ("number_not_in_source", 1), ("pii_contact_detail", 2), ("text_has_url_or_at", 1),
                   ("text_empty_or_over_40_words", 1), ("duplicate_claim", 1), ("schema_type", 1)):
        ok(f"check: {why} dropped x{n}", d.get(why) == n)
    ok("check: every claim accounted for (accepted + dropped == in)",
       r["accepted_n"] + sum(d.values()) == r["claims_in"])
    ok("check: no dropped claim's text echoes into the output", "SENTINEL_DROPPED" not in json.dumps(r))
    base = {"text": "Acme Widgets sells configurable industrial widgets.", "entity": "Acme Widgets",
            "claim_type": "company_fact", "as_of": None, "time_sensitive": False,
            "evidence": [{"para_idx": 5, "quote": "Acme Widgets sells configurable industrial widgets"}]}
    for pii in ("dana [at] example [dot] com", "555\u2011123\u20114567", "dana\uff20example.com"):
        rr = check(pk, {"claims": [{**base, "evidence": [{"para_idx": 5, "quote": f"configurable {pii}"}]}]})
        ok(f"check: obfuscated contact {pii.encode('unicode_escape').decode()!r} in an evidence quote -> PII drop",
           rr["dropped"] == {"pii_contact_detail": 1})
    nine = {**base, "evidence": [{"para_idx": 5, "quote": "Acme Widgets"}] * 9}
    ok("check: 9 spans -> evidence_shape (the 0023 CHECK allows 1-8)", check(pk, {"claims": [nine]})["dropped"]
       == {"evidence_shape": 1})
    ok("check: hard confidence cap is code", all(a["confidence"] <= CONF_CAP for a in r["accepted"]))
    for bad in ({"claims": [], "x": 1}, [], {"claims": {}}):
        try:
            check(pk, bad)
            ok(f"check: top-level {type(bad).__name__} rejected", False)
        except GateError:
            ok(f"check: top-level {type(bad).__name__} rejected", True)
    ok("as_claim: a checked row round-trips through check to the same key",
       check(pk, {"claims": [as_claim(good)]})["accepted"][0]["claim_key"] == good["claim_key"])

    # pilot regression: real v4 output (public-source facts, PII-scanned) on a trimmed packet with the original idx
    pilot = json.load(open(os.path.join(FIX, "pilot_v4.json"), encoding="utf-8"))
    pr = check(pilot["packet"], {"claims": pilot["claims"]}, model="sonnet")
    ok("pilot: the 3 real v4 claims pass the gate unchanged (4-span NIST claim, McKinsey 'says', RevGenius)",
       pr["accepted_n"] == 3 and pr["flags"]["multi_span"] == 1)
    ok("pilot: the McKinsey 'says' claim is flagged attribution_unquoted, as pilot check_v3 flagged it (W082)",
       [a["attribution_unquoted"] for a in pr["accepted"]] == [False, True, False])

    # freshness lookup + validity
    now = _dt.datetime(2026, 11, 14, 12, 0, tzinfo=_dt.timezone.utc)
    ok("freshness: thesis / prediction -> opinion, never re-checked (even if time_sensitive)",
       freshness_v0("thesis", True, now) == ("opinion", None) and freshness_v0("prediction", False, now) == ("opinion", None))
    ok("freshness: time_sensitive -> fast_moving, +30 d", freshness_v0("metric", True, now)
       == ("fast_moving", "2026-12-14T12:00:00Z") and freshness_v0("funding", True, now)[0] == "fast_moving")
    ok("freshness: launch / funding / people_move / partnership, not time_sensitive -> historical, none",
       all(freshness_v0(t, False, now) == ("historical", None) for t in STABLE_TYPES))
    ok("freshness: everything else -> slow_moving, +90 d", freshness_v0("company_fact", False, now)
       == ("slow_moving", "2027-02-12T12:00:00Z") and freshness_v0("adoption", False, now)[0] == "slow_moving")
    ok("valid_from: a full date only", valid_from("2026-02-03") == "2026-02-03T00:00:00Z" and valid_from("2026-02") is None
       and valid_from("Q2 2026") is None and valid_from("2024") is None and valid_from("2026-02-30") is None
       and valid_from(None) is None)

    # judge (stubbed LLM): verdict mapping, abstain on a missing pid, record fields, batching, retry, hard fail
    seen_prompts = []

    def fake(prompt, model):
        seen_prompts.append(prompt)
        items = json.loads(prompt.split("<items>\n", 1)[1].rsplit("\n</items>", 1)[0])
        labs = [{"pid": it["pid"], "supported": "no" if "Fictional Ventures" in it["claim"] else "yes",
                 "standalone": "yes", "useful": 3, "why": "ok"} for it in items[:-1]]   # last pid left out -> abstain
        return {"labels": labs}, "", ""
    jd = judge(pk, r, model="claude-fixture", batch=3, llm=fake)
    v = [a["judge"]["verdict"] for a in jd["accepted"]]
    ok("judge: batched (4 rows, batch 3 -> 2 calls); the prompt is the template with ITEMS filled",
       len(seen_prompts) == 2 and "ITEMS" not in seen_prompts[0] and seen_prompts[0].startswith("You are labelling claims"))
    ok("judge: yes -> supported, no -> unsupported, a pid left out -> abstain",
       v.count("abstain") == 2 and "unsupported" in v and "supported" in v
       and jd["judge"]["abstain"] == 2 and sum(jd["judge"][k] for k in VERDICTS) == 4)
    rec = jd["accepted"][0]["judge"]
    ok("judge: record = model + sha256(template) + judged_at (ISO Z)", rec["model"] == "claude-fixture"
       and rec["prompt_hash"] == hashlib.sha256(open(JUDGE_PROMPT_PATH, "rb").read()).hexdigest()
       and re.fullmatch(r"[0-9a-f]{64}", rec["prompt_hash"]) and re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", rec["judged_at"]))
    ok("judge: the passage is span-scoped (event line + every cited paragraph)",
       "Event: Widget Night (fixture)\\nDate: 2026-01-15" in seen_prompts[0] and seen_prompts[0].count("[") >= 4)
    ok("judge: checked rows are not mutated", "judge" not in r["accepted"][0])
    calls = []

    def flaky(prompt, model):
        calls.append(1)
        if len(calls) == 1:
            raise LLMError("no JSON object in the reply")
        return fake(prompt, model)
    ok("judge: one failed call is retried once", len(judge(pk, r, batch=20, llm=flaky)["accepted"]) == 4 and len(calls) == 2)

    def dead(prompt, model):
        raise LLMError("exited 1")
    try:
        judge(pk, r, llm=dead)
        ok("judge: a batch failing twice raises (no all-abstain file)", False)
    except LLMError:
        ok("judge: a batch failing twice raises (no all-abstain file)", True)
    ok("extract: the prompt is the v4 template with the packet substituted (pilot shape)",
       extract_prompt(pk).startswith("You extract claims from one research brief") and "{PACKET_JSON}" not in extract_prompt(pk)
       and json.dumps(pk, indent=1, ensure_ascii=False) + "\n</packet>" in extract_prompt(pk))
    ok("extract: the reply parser takes the first JSON object", extract(pk, llm=lambda p, m: (
        parse_reply('x {"claims": []} {"y": 1}', 0), "", ""))[0] == {"claims": []})

    # batch over a temp tree (LLM + ledger stubbed): only the eligible brief spends, files written, rerun skips
    import shutil
    with tempfile.TemporaryDirectory() as td:
        bd, od = os.path.join(td, "briefs"), os.path.join(td, "out")
        os.makedirs(bd)
        for name, mut in (("2026-10-01-ok", None), ("2026-10-02-otr", "otr"), ("2026-10-03-ledgered", "ledger")):
            shutil.copytree(os.path.join(PROSE_FIX, "brief_ok"), os.path.join(bd, name))
            mp = os.path.join(bd, name, "manifest.json")
            m = json.load(open(mp))
            if mut == "otr":
                m.setdefault("notion_export", {})["skip_staging"] = True
            if mut == "ledger":
                m["event"]["notion_page_id"] = "00000000-0000-4000-8000-00000000e1e1"
            json.dump(m, open(mp, "w"))
        ledgered = research_source_key("00000000-0000-4000-8000-00000000e1e1")
        spent = []

        def both(prompt, model):
            spent.append(model)
            if prompt.startswith("You extract"):
                return claims, json.dumps(claims), ""
            return fake(prompt, model)
        res = batch_run(bd, od, model="sonnet-fx", judge_model="judge-fx", ledger_count=lambda k: 2 if k == ledgered else 0,
                        llm=both)
        ok("batch: only the eligible brief is extracted + judged; OTR and ledger skipped + counted",
           [x["brief"] for x in res["extracted"]] == ["2026-10-01-ok"] and res["skipped_counts"]
           == {"ledger_present": 1, "skip_staging_otr": 1} and spent[0] == "sonnet-fx" and "judge-fx" in spent)
        ok("batch: packet, raw, claims, checked, judged + summary files written",
           all(os.path.exists(os.path.join(od, f"2026-10-01-ok{s}")) for s in
               (".packet.json", ".v2.raw.txt", ".v2.claims.json", ".v2.checked.json", ".v2.judged.json"))
           and os.path.exists(os.path.join(od, "batch-v2-summary.json")))
        spent.clear()
        res2 = batch_run(bd, od, ledger_count=lambda k: 2 if k == ledgered else 0, llm=both)
        ok("batch: a rerun skips briefs already judged (no second spend)", res2["skipped_counts"].get("already_judged") == 1
           and not spent and not res2["extracted"])
        shutil.rmtree(od)
        res3 = batch_run(bd, od, ledger_count=lambda k: 0, llm=lambda p, m: (_ for _ in ()).throw(RuntimeError("SECRET")))
        ok("batch: an LLM failure is recorded by type only; no judged file", res3["errors"] and "SECRET" not in json.dumps(res3)
           and not os.path.exists(os.path.join(od, "2026-10-01-ok.v2.judged.json")))
    cmd = llm_cmd("sonnet")
    ok("llm: the isolated headless call (no tools, no setting sources, strict empty MCP)",
       cmd[cmd.index("--tools") + 1] == "" and cmd[cmd.index("--setting-sources") + 1] == "" and "--strict-mcp-config" in cmd)
    print(f"selftest: {'PASS' if not fails else 'FAIL'} ({len(fails)} failing)")
    return not fails


# ---------------------------------------------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    if argv[:1] == ["--selftest"]:
        return 0 if selftest() else 1
    from prose_extract import _emit
    ap = argparse.ArgumentParser(prog="claim_extract_v2.py", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="verb", required=True)
    a = sub.add_parser("extract"); a.add_argument("brief_dir"); a.add_argument("--model", default=EXTRACT_MODEL)
    a.add_argument("--out"); a.add_argument("--packet-out")
    a = sub.add_parser("check"); a.add_argument("packet"); a.add_argument("claims"); a.add_argument("--model")
    a.add_argument("--out")
    a = sub.add_parser("judge"); a.add_argument("packet"); a.add_argument("checked")
    a.add_argument("--model", default=JUDGE_MODEL); a.add_argument("--batch", type=int, default=20); a.add_argument("--out")
    a = sub.add_parser("batch"); a.add_argument("--briefs-dir", required=True); a.add_argument("--out-dir", required=True)
    a.add_argument("--model", default=EXTRACT_MODEL); a.add_argument("--judge-model", default=JUDGE_MODEL)
    a.add_argument("--concurrency", type=int, default=4)
    a = ap.parse_args(argv)
    load = lambda p: json.load(open(p, encoding="utf-8"))   # noqa: E731
    if a.verb == "extract":
        pk, why = prepass(a.brief_dir)
        if pk is None:
            sys.stderr.write(f"extract: skipped {os.path.basename(a.brief_dir.rstrip('/'))}: {why}\n")
            return 3
        if a.packet_out:
            _emit(pk, a.packet_out)
        doc, _, _ = extract(pk, model=a.model)
        _emit(doc, a.out)
        sys.stderr.write(f"extract: {len(doc.get('claims') or [])} claims ({a.model})\n")
    elif a.verb == "check":
        try:
            res = check(load(a.packet), load(a.claims), model=a.model)
        except (GateError, json.JSONDecodeError) as e:
            sys.stderr.write(f"check: REJECTED whole file: {type(e).__name__}\n")
            return 2
        _emit(res, a.out)
        sys.stderr.write(f"check: {res['accepted_n']}/{res['claims_in']} accepted · dropped {res['dropped']} · "
                         f"flags {res['flags']}\n")
    elif a.verb == "judge":
        res = judge(load(a.packet), load(a.checked), model=a.model, batch=a.batch)
        _emit(res, a.out)
        sys.stderr.write(f"judge: {res['judge']}\n")
    elif a.verb == "batch":
        res = batch_run(a.briefs_dir, a.out_dir, model=a.model, judge_model=a.judge_model, concurrency=a.concurrency)
        sys.stderr.write(f"batch: {res['briefs_seen']} dirs · extracted {len(res['extracted'])} · errors "
                         f"{len(res['errors'])} · accepted {res['accepted_total']} · skipped {res['skipped_counts']}\n")
        return 1 if res["errors"] else 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
