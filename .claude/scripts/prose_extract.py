#!/usr/bin/env python3
"""prose_extract — the deterministic cage around prose claim extraction from research briefs (YED-384).

Design: the 2026-11-11 prose-extraction design note (hybrid: deterministic pre-pass -> no-tools LLM extractor ->
deterministic gate). This file is everything EXCEPT the writer. It never writes to the spine: `substrate.py
stage-prose` is the writer (pilot iter2 cleared the floor: precision 1.00 vs the splitter's 0.43).

Verbs:
  prepass  <brief_dir> [--out packet.json]
           research_brief.md + manifest.json -> a packet: knowledge sections only (Topics / Primer / Landscape /
           Topic Foundations / People / Companies; playbook headings and mostly-imperative paragraphs dropped),
           numbered paragraphs, roster-matched entity headings, URLs per paragraph with `[n]` footnotes resolved
           through Endnotes. Briefs under 300 words exit 3 (stub).
  splitter <packet> [--out claims.json]
           the NULL BASELINE: every sentence of every kept paragraph is one claim (quote = its first 25 words). Same
           output schema as the LLM extractor, so `check` scores both identically.
  check    <packet> <claims.json> [--extractor claude|splitter] [--model ID] [--out checked.json]
           the gate. Drops (never downgrades) anything off-schema, non-verbatim, off-roster, over-length or carrying
           contact PII; downgrades a URL not in the claim's own paragraph to `reference`; flags low claim/quote
           overlap. Output rows are in stage-research's claim shape, status 'candidate', lane 'research'.
  sample   <checked.json ...> [--n 100] [--stratify] [--seed N] [--packets p.json ...] [--out sample.json]
           draws the pilot labelling sample; --stratify = equal allocation per (extractor, brief).
  batch    --briefs-dir D --out-dir O [--model sonnet] [--concurrency 4]
           prepass -> headless tool-less LLM (the pilot's `claude -p` command) -> check, for every brief dir that has
           a manifest and a research_brief.md, is not skip_staging, not an interview dossier, and has no ledger claims
           (GET-only prod read). Writes files + O/batch-summary.json, nothing else. Staging is a separate step.

Provenance (decided by the parent, 2026-11-11): URL in the same paragraph -> web_verified @0.55; otherwise
reference @0.40; questions are always reference @0.40; every confidence is hard-capped at 0.60 here, in code.

Self-test (offline, fake fixtures under fixtures/prose/): python3 .claude/scripts/prose_extract.py --selftest
"""
from __future__ import annotations
import argparse, io, json, os, random, re, sys, tempfile
from contextlib import redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from substrate import (ROSTER_TIE, claim_key, clean_md, norm_text, pid_variants, redact_body,  # noqa: E402
                       research_source_key, roster_match, strip_paren)
from spine_client import EMAIL_ALLOWLIST_RE, EMAIL_RE, PHONE_RE  # noqa: E402  (ADR-9 patterns, never copied)

MIN_WORDS = 300
QUOTE_MAX_WORDS = 25          # the claim.quote licensing guard (0009), producer-enforced
TEXT_MAX_WORDS = 30
CONF_CAP = 0.60
CONF = {"web_verified": 0.55, "reference": 0.40}
JACCARD_FLAG = 0.30
CLAIM_KEYS = {"text", "quote", "para_idx", "url_ref", "entity", "entity_type", "claim_type"}
ENTITY_TYPES = {"person", "company", "topic"}
CLAIM_TYPES = {"fact", "statistic", "thesis", "prediction", "question"}

# A level-1..3 heading naming one of these opens a section. Playbook and exclusion win over keep ('People' never
# rescues 'Verification Flags'; 'Topic' never rescues 'Topic pitches'). Synthesis and Alex's playbook are not world
# facts (design §1). Pilot 1 (2026-11-11): 16 of 18 extractor failures were advice/questions from playbook sections.
KEEP_RE = re.compile(r"\b(topics?|topic foundations|primer|landscape|people|companies)\b")
# Matched on heading WORDS with parentheticals removed: '(contested questions inside each)' and '(opener for the
# hosts)' qualify a factual section, they do not make it a playbook.
PLAYBOOK_RE = re.compile(r"\b(questions?|conversation kits?|pitch(?:es)?|talking points?|hooks?|angles?|asks?|"
                         r"openers?|what to say|playbook|prep|your move|plays)\b")
EXCLUDE_RE = re.compile(r"quick take|\bframe\b|cross-event|documentarian|hooks?\b|success signals|verification"
                        r"|confidential|endnotes|sources|references|guards|retro|who to prioriti|gaps to close"
                        r"|signal log|why this matters|⛔")
# A sentence opening with one of these is advice to Alex, not a world fact (prepass paragraph filter + check).
IMPERATIVE_VERBS = frozenset("""ask lead mention open start bring use say try avoid frame pitch position raise probe
push offer skip drop follow reference cite tell introduce connect highlight emphasize emphasise steer anchor listen
watch prepare consider don't do keep make pick share flag acknowledge compliment invite pivot mirror lean name close
remember expect skim read check request propose suggest""".split())
IMPERATIVE_LEAD_RE = re.compile(r"^[\W_]*(?:(?:Q\d+|A|B|C|\d+)[:.)]\s*)?[\W_]*([A-Za-z][A-Za-z'’-]*)")
# Noun compounds that open factual lines in real briefs ('Use Cases: …', 'Lead time: …', a 'Name | Title' header).
NOT_IMPERATIVE_RE = re.compile(r"(?i)^(?:use cases?|lead (?:times?|investors?|authors?|engineers?)|name \|)")
ENDNOTE_SECTION_RE = re.compile(r"endnotes|sources|references")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d{1,3}[.)])\s+")
TABLE_SEP_RE = re.compile(r"^\s*\|?(\s*:?-{2,}:?\s*\|)+\s*:?-*:?\s*\|?\s*$")
ENDNOTE_LINE_RE = re.compile(r"^\s*(?:[-*]\s*)?\[(\d{1,3})\]\s*(.*)$")
FOOTNOTE_RE = re.compile(r"\[(\d{1,3}(?:\s*(?:[,–-]|and)\s*\d{1,3})*)\](?!\()")
MD_LINK_URL_RE = re.compile(r"\]\((https?://[^)\s]+)\)")
BARE_URL_RE = re.compile(r"(?<![(\[])\bhttps?://[^\s)\]>|]+")
WORD_RE = re.compile(r"[a-z0-9][a-z0-9'.-]*")
STOP = set("""a an the and or but of to in on at for by with from as is are was were be been being it its this that
these those their there they them he she his her we our you your not no than then so if into over under about after
before per via also which who whom whose what when where how all any each more most some such can could would should
will may might has have had do does did just only very""".split())


def ws(s: str) -> str:
    """Whitespace normalisation ONLY: the one transform the containment check allows."""
    return re.sub(r"\s+", " ", s or "").strip()


def words(s: str) -> int:
    return len(ws(s).split())


# ---------------------------------------------------------------------------------------------------------------
# prepass
# ---------------------------------------------------------------------------------------------------------------
def classify(title: str) -> str | None:
    t = re.sub(r"^[\W\d_]+", "", clean_md(title).lower())
    if PLAYBOOK_RE.search(re.sub(r"\([^()]*\)", " ", t)):
        return "playbook"
    if EXCLUDE_RE.search(t):
        return "exclude"
    if KEEP_RE.search(t):
        return "keep"
    return None


def is_imperative(sentence: str) -> bool:
    m = IMPERATIVE_LEAD_RE.match(sentence or "")
    return bool(m) and m.group(1).lower().replace("’", "'") in IMPERATIVE_VERBS \
        and not NOT_IMPERATIVE_RE.match(sentence[m.start(1):])


def mostly_imperative(text: str) -> bool:
    """Most (strictly more than half) of the paragraph's sentences open with an imperative verb ('Ask…', 'Lead
    with…'). A fact followed by one 'Ask…' survives; the prompt and the check handle the ask."""
    sents = sentences(text)
    return 2 * sum(map(is_imperative, sents)) > len(sents)


def resolve_entity(name: str, roster: list[tuple[str, str, str]]):
    """A heading or an extractor's entity -> (type, roster name), ROSTER_TIE, or None. Tries the whole string, then
    the name part of 'Name — Title, Company (role) · pronouns'. People stay exact-only via roster_match (ADR-4 D3)."""
    s = clean_md(name or "").strip(" #*")
    head = re.split(r"\s+[—–|·]\s+", s)[0]
    # name part FIRST: on the whole heading, company containment would claim 'Dana — CEO, Acme' for Acme
    cands = [head.split(",")[0], strip_paren(head), head, s]
    for c in dict.fromkeys(x.strip() for x in cands if x.strip()):
        hit = roster_match(c, roster)
        if hit is ROSTER_TIE:
            return ROSTER_TIE
        if hit:
            return hit
    return None


def endnote_map(md: str) -> dict[str, str]:
    """'[n] Publisher, title — [url](url)' lines inside an Endnotes/Sources section -> {n: first url}."""
    out, inside = {}, False
    for line in md.splitlines():
        h = HEADING_RE.match(line)
        if h:
            inside = bool(ENDNOTE_SECTION_RE.search(h.group(2).lower()))
            continue
        m = ENDNOTE_LINE_RE.match(line) if inside else None
        if m:
            u = MD_LINK_URL_RE.search(m.group(2)) or BARE_URL_RE.search(m.group(2))
            if u:
                out.setdefault(m.group(1), u.group(1) if u.re is MD_LINK_URL_RE else u.group(0))
    return out


def footnote_numbers(raw: str) -> list[str]:
    nums = []
    for grp in FOOTNOTE_RE.findall(raw):
        for part in re.split(r"\s*(?:,|and)\s*", grp):
            r = re.match(r"(\d+)\s*[–-]\s*(\d+)$", part.strip())
            if r and int(r.group(2)) - int(r.group(1)) < 50:
                nums += [str(i) for i in range(int(r.group(1)), int(r.group(2)) + 1)]
            elif part.strip().isdigit():
                nums.append(part.strip())
    return nums


def para_urls(raw: str, notes: dict[str, str]) -> list[str]:
    found = MD_LINK_URL_RE.findall(raw) + BARE_URL_RE.findall(raw)
    found += [notes[n] for n in footnote_numbers(raw) if n in notes]
    return list(dict.fromkeys(u.rstrip(".,;:") for u in found))


def _blocks(lines: list[str]) -> list[str]:
    """Kept-section lines -> raw paragraphs: one per non-empty line (the Notion export writes one block per line with
    no blank line between paragraphs), list markers stripped, table rows joined by ' | ', separator rows dropped."""
    out = []
    for line in lines:
        if not line.strip() or TABLE_SEP_RE.match(line):
            continue
        if line.strip().startswith("|"):
            out.append(" | ".join(c.strip() for c in line.strip().strip("|").split("|")))
        else:
            out.append(LIST_ITEM_RE.sub("", line, count=1))
    return out


def prepass(brief_dir: str) -> tuple[dict | None, str]:
    md = open(os.path.join(brief_dir, "research_brief.md"), encoding="utf-8").read()
    manifest = json.load(open(os.path.join(brief_dir, "manifest.json"), encoding="utf-8"))
    ev = manifest.get("event") or {}
    if not ev.get("notion_page_id"):
        return None, "manifest_missing_event_page_id"
    n_words = len(md.split())
    if n_words < MIN_WORDS:
        return None, f"stub_under_{MIN_WORDS}_words ({n_words})"
    rb = ((manifest.get("notion_export") or {}).get("briefs") or {}).get("research_brief") or {}
    roster = [(e["type"], e["name"], e["name"]) for e in manifest.get("entities", []) if e.get("name")]
    notes = endnote_map(md)
    # Heading stack: the deepest level-1..3 heading that names a known section is the section; the deepest heading
    # below it is the entity heading. Covers both '## People / ### Name' and '### People / #### Name' generations.
    stack: list[tuple[int, str, str | None]] = []      # (level, title, 'keep'|'exclude'|'playbook'|None)
    groups: list[tuple[tuple, list[str]]] = []          # consecutive lines sharing (kind, section, heading)
    dropped = {"playbook_section": 0, "excluded_section": 0, "outside_known_section": 0, "tiny_or_url_only": 0,
               "imperative": 0}
    for line in redact_body(md).splitlines():          # the same confidentiality rules as stage-research
        h = HEADING_RE.match(line)
        if h:
            lvl, title = len(h.group(1)), clean_md(h.group(2))
            while stack and stack[-1][0] >= lvl:
                stack.pop()
            stack.append((lvl, title, classify(title) if lvl <= 3 else None))
            groups.append(((None, None, None), []))     # a heading always ends the paragraph above it
            continue
        known = [i for i, s in enumerate(stack) if s[2]]
        si = known[-1] if known else None
        key = (stack[si][2], stack[si][1], stack[-1][1] if stack[-1] is not stack[si] else None) if known else (None,) * 3
        if not groups or groups[-1][0] != key:
            groups.append((key, []))
        groups[-1][1].append(line)
    paragraphs = []
    for (kind, section, heading), lines in groups:
        blocks = _blocks(lines)
        if kind != "keep":
            why = {"exclude": "excluded_section", "playbook": "playbook_section"}.get(kind, "outside_known_section")
            dropped[why] += len(blocks)
            continue
        hit = resolve_entity(heading, roster) if heading else None
        for raw in blocks:
            text = clean_md(raw)
            if words(BARE_URL_RE.sub("", text)) < 4:
                dropped["tiny_or_url_only"] += 1
                continue
            if mostly_imperative(text):
                dropped["imperative"] += 1
                continue
            paragraphs.append({"idx": len(paragraphs), "section": section, "entity_hint": hit[1] if hit else None,
                               "entity_type_hint": hit[0] if hit else None, "heading": heading, "text": text,
                               "urls": para_urls(raw, notes)})
    return {"schema": "prose-packet/1", "source_key": research_source_key(ev["notion_page_id"]),
            "brief_ref": rb.get("brief_ref"),
            "event": {"notion_page_id": ev["notion_page_id"], "title": ev.get("title"),
                      "event_date": ev.get("event_date")},
            "roster": [{"type": t, "name": n} for t, n, _ in roster], "words": n_words,
            "dropped_paragraphs": dropped, "paragraphs": paragraphs}, "ok"


# ---------------------------------------------------------------------------------------------------------------
# splitter (null baseline)
# ---------------------------------------------------------------------------------------------------------------
ABBREV_RE = re.compile(r"(?:\b(?:e\.g|i\.e|etc|vs|inc|ltd|co|corp|dr|mr|ms|mrs|st|jr|sr|no|approx|ph\.d|u\.s|"
                       r"u\.k|a\.i)|\b[A-Z])\.$", re.I)
SENT_SPLIT_RE = re.compile(r"(?<=[.!?])[\"”')\]]*\s+(?=[\"“(\[]?[A-Z0-9])")


def sentences(text: str) -> list[str]:
    out = []
    for piece in SENT_SPLIT_RE.split(text):
        if out and ABBREV_RE.search(out[-1]):
            out[-1] = f"{out[-1]} {piece}"
        else:
            out.append(piece)
    return [s.strip() for s in out if s.strip()]


def splitter(packet: dict) -> dict:
    claims = []
    roster = [(r["type"], r["name"], r["name"]) for r in packet["roster"]]
    for p in packet["paragraphs"]:
        for s in sentences(p["text"]):
            if words(s) < 4:
                continue
            ent, etype = p["entity_hint"], p["entity_type_hint"]
            if not ent:                                 # name the one roster entity the sentence mentions, if exactly one
                named = {(t, n) for t, n, _ in roster if norm_text(strip_paren(n)) in norm_text(s)}
                etype, ent = next(iter(named)) if len(named) == 1 else (None, None)
            ctype = ("question" if s.rstrip().endswith("?") or "question" in (p["section"] or "").lower()
                     else "statistic" if re.search(r"\d[\d,.]*\s*(?:%|percent|[kmb]n?\b)|[$€£]\s?\d", s, re.I)
                     else "fact")
            claims.append({"text": s, "quote": " ".join(s.split()[:QUOTE_MAX_WORDS]), "para_idx": p["idx"],
                           "url_ref": p["urls"][0] if p["urls"] else None, "entity": ent or "",
                           "entity_type": etype or "topic", "claim_type": ctype})
    return {"claims": claims}


# ---------------------------------------------------------------------------------------------------------------
# check (the gate)
# ---------------------------------------------------------------------------------------------------------------
def content_tokens(s: str) -> set[str]:
    return {w.strip(".'-") for w in WORD_RE.findall((s or "").lower()) if w.strip(".'-") not in STOP and len(w) > 2}


def jaccard(a: str, b: str) -> float:
    x, y = content_tokens(a), content_tokens(b)
    return len(x & y) / len(x | y) if x | y else 1.0


def has_pii(*vals) -> bool:
    for v in vals:
        if not isinstance(v, str):
            continue
        if any(not EMAIL_ALLOWLIST_RE.search(m.group(0)) for m in EMAIL_RE.finditer(v)) or PHONE_RE.search(v):
            return True
    return False


class GateError(Exception):
    """A whole-file failure. Messages name a reason only, never claim text or an unknown key (design §3)."""


def _schema_reason(c) -> str | None:
    if not isinstance(c, dict) or set(c) - CLAIM_KEYS:
        return "schema_unknown_or_bad_shape"
    if CLAIM_KEYS - set(c):
        return "schema_missing_key"
    if not all(isinstance(c[k], str) for k in ("text", "quote", "entity", "entity_type", "claim_type")) \
            or isinstance(c["para_idx"], bool) or not isinstance(c["para_idx"], int) \
            or not (c["url_ref"] is None or isinstance(c["url_ref"], str)):
        return "schema_type"
    if c["entity_type"] not in ENTITY_TYPES or c["claim_type"] not in CLAIM_TYPES:
        return "schema_enum"
    return None


def check(packet: dict, claims_doc, *, extractor: str = "claude", model: str | None = None) -> dict:
    if not isinstance(claims_doc, dict) or set(claims_doc) != {"claims"} or not isinstance(claims_doc["claims"], list):
        raise GateError("claims file must be exactly {\"claims\": [...]} (top-level schema)")
    if extractor not in ("claude", "splitter"):
        raise GateError("extractor must be claude or splitter")
    paras = {p["idx"]: p for p in packet["paragraphs"]}
    roster = [(r["type"], r["name"], r["name"]) for r in packet["roster"]]
    ev = packet["event"]
    dropped: dict[str, int] = {}
    flags = {"url_downgraded": 0, "low_overlap": 0, "entity_type_corrected": 0}
    accepted, seen = [], set()

    def drop(why: str):
        dropped[why] = dropped.get(why, 0) + 1
    for c in claims_doc["claims"]:
        why = _schema_reason(c)
        if why:
            drop(why)
            continue
        p = paras.get(c["para_idx"])
        if p is None:
            drop("para_idx_out_of_range")
            continue
        if has_pii(c["text"], c["quote"], c["entity"], c["url_ref"]):
            drop("pii_contact_detail")
            continue
        if not ws(c["quote"]) or words(c["quote"]) > QUOTE_MAX_WORDS:
            drop("quote_empty_or_over_25_words")
            continue
        if not ws(c["text"]) or words(c["text"]) > TEXT_MAX_WORDS:
            drop("text_empty_or_over_30_words")
            continue
        if is_imperative(c["text"]) or ws(c["text"]).endswith("?"):
            drop("not_declarative")
            continue
        if ws(c["quote"]) not in ws(p["text"]):
            drop("quote_not_verbatim")
            continue
        hit = resolve_entity(c["entity"], roster)
        if hit is ROSTER_TIE:
            drop("entity_roster_tie")
            continue
        if not hit:
            drop("entity_unresolved")
            continue
        etype, ename = hit
        if etype != c["entity_type"]:
            flags["entity_type_corrected"] += 1
        url = c["url_ref"] if c["url_ref"] in p["urls"] else None
        if c["url_ref"] and not url:
            flags["url_downgraded"] += 1
        tier = "web_verified" if url and c["claim_type"] != "question" else "reference"
        conf = min(CONF[tier], CONF_CAP)
        text = ws(c["text"])
        if norm_text(strip_paren(ename)) not in norm_text(text):
            text = f"{ename}: {text}"                       # stands alone in retrieval, as stage-research does
        key = claim_key(text)
        if key in seen:
            drop("duplicate_claim")
            continue
        seen.add(key)
        low = jaccard(c["text"], c["quote"]) < JACCARD_FLAG
        flags["low_overlap"] += low
        meta = {"phase": "pre_event", "extraction": "prose", "notion_event_id": pid_variants(ev["notion_page_id"])[0],
                "brief_ref": packet.get("brief_ref"), "url": url}
        if low:
            meta["low_overlap"] = True
        row = {"source_key": packet["source_key"], "claim_key": key, "claim_text": text,
               "claim_type": c["claim_type"], "quote": ws(c["quote"]),
               "locator": {"section": p["section"], "entity": ename, "heading": p["heading"],
                           "para_idx": p["idx"], "url": url},
               "provenance_tier": tier, "confidence": conf,
               "asserted_at": (ev.get("event_date") or "")[:10] or None, "status": "candidate",
               "extractor": extractor, "extractor_model": model if extractor == "claude" else None,
               "lane": "research", "entity_type": etype, "metadata": {k: v for k, v in meta.items() if v is not None}}
        accepted.append({k: v for k, v in row.items() if v is not None})
    return {"source_key": packet["source_key"], "extractor": extractor, "claims_in": len(claims_doc["claims"]),
            "accepted_n": len(accepted), "dropped": dropped, "flags": flags, "accepted": accepted}


# ---------------------------------------------------------------------------------------------------------------
# sample
# ---------------------------------------------------------------------------------------------------------------
def sample(checked: list[dict], *, n: int, stratify: bool, seed: int, packets: list[dict] | None = None) -> dict:
    rng = random.Random(seed)
    text_of = {(pk["source_key"], p["idx"]): p["text"] for pk in (packets or []) for p in pk["paragraphs"]}
    strata: dict[tuple, list[dict]] = {}
    for doc in checked:
        for r in doc["accepted"]:
            strata.setdefault((r["extractor"], r["source_key"]), []).append(r)
    for rows in strata.values():
        rng.shuffle(rows)
    if stratify:                       # equal allocation; a short stratum's shortfall goes round-robin to the rest
        picked, keys = [], sorted(strata)
        while len(picked) < n and any(strata[k] for k in keys):
            for k in keys:
                if strata[k] and len(picked) < n:
                    picked.append(strata[k].pop())
    else:
        pool = [r for rows in strata.values() for r in rows]
        picked = rng.sample(pool, min(n, len(pool)))
    out = []
    for i, r in enumerate(picked):
        item = {"sample_id": i, "extractor": r["extractor"], "source_key": r["source_key"],
                "para_idx": r["locator"]["para_idx"], "claim_text": r["claim_text"], "quote": r["quote"],
                "provenance_tier": r["provenance_tier"], "label": None}
        if (r["source_key"], r["locator"]["para_idx"]) in text_of:
            item["paragraph"] = text_of[(r["source_key"], r["locator"]["para_idx"])]
        out.append(item)
    by: dict[str, int] = {}
    for it in out:
        by[it["extractor"]] = by.get(it["extractor"], 0) + 1
    return {"n": len(out), "by_extractor": by, "strata": len(strata), "seed": seed,
            "label_rule": "faithful to the brief paragraph (not true in the world): yes | no", "sample": out}


# ---------------------------------------------------------------------------------------------------------------
# batch (no writes: prepass -> headless LLM -> check, per brief; staging stays `substrate.py stage-prose`)
# ---------------------------------------------------------------------------------------------------------------
PROMPT_PATH = os.path.join(HERE, "..", "references", "prose-extractor-prompt.md")
DOSSIER_PREFIX = "undated-interview-dossier-"


def llm_cmd(model: str) -> list[str]:
    """The pilot's headless command (iter2 run_llm_pilot.sh): no tools, no MCP, no slash commands, text out."""
    return ["claude", "-p", "--model", model, "--tools", "", "--strict-mcp-config", "--mcp-config",
            '{"mcpServers":{}}', "--disable-slash-commands", "--output-format", "text"]


def run_llm(packet: dict, model: str) -> tuple[dict, str, str]:
    """One tool-less extraction. Runs from an empty temp dir (outside every repo: no CLAUDE.md, no project agents).
    Returns (claims doc, raw stdout, stderr); an unparseable reply becomes {"claims": []}, as in the pilot."""
    import subprocess
    prompt = open(PROMPT_PATH, encoding="utf-8").read().replace(
        "{PACKET_JSON}", json.dumps(packet, indent=1, ensure_ascii=False) + "\n")
    with tempfile.TemporaryDirectory() as cwd:
        p = subprocess.run(llm_cmd(model), input=prompt, capture_output=True, text=True, cwd=cwd, timeout=1200)
    m = re.search(r"\{.*\}", p.stdout, re.S)
    try:
        doc = json.loads(m.group(0)) if m else {"claims": []}
    except json.JSONDecodeError:
        doc = {"claims": []}
    return doc, p.stdout, p.stderr + (f"\n[exit {p.returncode}]" if p.returncode else "")


def _prod_ledger_count():
    """GET-only ledger lookup against prod through substrate's Graph in dry-run mode (it never writes)."""
    from substrate import Graph, Stats, ledger_claim_count
    g = Graph(dry_run=True, stats=Stats())
    return lambda skey: ledger_claim_count(g, skey)


def batch(briefs_dir: str, out_dir: str, *, model: str = "sonnet", concurrency: int = 4,
          ledger_count=None, llm=None) -> dict:
    """Every eligible brief dir -> <slug>.packet.json, .llm.raw.txt, .llm.claims.json, .llm.checked.json in out_dir,
    plus batch-summary.json. Skips (counted, never crashing): interview dossiers, no manifest, no research_brief.md,
    skip_staging (YED-391), no event page id, ledger present (ledger beats prose), already checked, stubs."""
    from concurrent.futures import ThreadPoolExecutor
    ledger_count = ledger_count or _prod_ledger_count()
    llm = llm or run_llm
    os.makedirs(out_dir, exist_ok=True)
    skipped: dict[str, list[str]] = {}
    todo: list[tuple[str, dict]] = []

    def skip(why: str, name: str):
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
        if os.path.exists(os.path.join(out_dir, f"{name}.llm.checked.json")):
            skip("already_checked", name); continue
        pk, why = prepass(d)
        if pk is None:
            skip(why.split(" ")[0], name); continue
        _emit(pk, os.path.join(out_dir, f"{name}.packet.json"))
        todo.append((name, pk))

    def one(item):
        name, pk = item
        try:
            doc, raw, err = llm(pk, model)
            for suffix, body in ((".llm.raw.txt", raw), (".llm.err.txt", err)):
                with open(os.path.join(out_dir, name + suffix), "w", encoding="utf-8") as f:
                    f.write(body or "")
            _emit(doc, os.path.join(out_dir, f"{name}.llm.claims.json"))
            res = check(pk, doc, extractor="claude", model=model)
            _emit(res, os.path.join(out_dir, f"{name}.llm.checked.json"))
            return {"brief": name, "claims_in": res["claims_in"], "accepted_n": res["accepted_n"],
                    "dropped": res["dropped"]}
        except Exception as e:                       # one brief failing never stops the batch; reason only, no content
            return {"brief": name, "error": type(e).__name__}
    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as ex:
        results = list(ex.map(one, todo))
    summary = {"briefs_seen": len(names), "model": model, "extracted": [r for r in results if "error" not in r],
               "errors": [r for r in results if "error" in r],
               "skipped_counts": {k: len(v) for k, v in sorted(skipped.items())}, "skipped": skipped,
               "accepted_total": sum(r.get("accepted_n", 0) for r in results)}
    _emit(summary, os.path.join(out_dir, "batch-summary.json"))
    return summary


# ---------------------------------------------------------------------------------------------------------------
# self-test
# ---------------------------------------------------------------------------------------------------------------
FIX = os.path.join(HERE, "fixtures", "prose")


def selftest() -> bool:
    fails = []

    def ok(name, cond):
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")
        if not cond:
            fails.append(name)
    pk, why = prepass(os.path.join(FIX, "brief_ok"))
    ok("prepass: fixture brief yields a packet", pk is not None and why == "ok")
    paras = pk["paragraphs"]
    blob = " ".join(p["text"] for p in paras)
    ok("prepass: source_key == substrate.research_source_key(event page id)",
       pk["source_key"] == research_source_key("00000000-0000-4000-8000-00000000f1f1"))
    ok("prepass: brief_ref from the manifest's notion_export block",
       pk["brief_ref"] == "notion:00000000-0000-4000-8000-00000000d0d0")
    ok("prepass: synthesis sections excluded (Quick Take, Verification Flags, Success, Frame, Threads)",
       not any(s in blob for s in ("QUICKTAKE_", "VERIFLAG_", "SUCCESS_", "FRAME_", "THREADS_")))
    ok("prepass: confidential line redacted (redact_body)", "confidential" not in blob.lower())
    ok("prepass: endnotes are not paragraphs", "Freight Weekly" not in blob)
    ok("prepass: idx is 0..n-1", [p["idx"] for p in paras] == list(range(len(paras))))
    by_head = {p["heading"]: p for p in paras}
    ok("prepass: 'Name — Title, Co (role) · pronouns' heading -> roster person",
       by_head.get("Dana Fixture — CEO, Acme Widgets (speaker) · she/her", {}).get("entity_hint") == "Dana Fixture")
    ok("prepass: 'Name, Title, Co (role)' heading -> roster person",
       by_head.get("Omar Placeholder, Partner, Fictional Ventures (host)", {}).get("entity_hint") == "Omar Placeholder")
    ok("prepass: off-roster primer heading -> entity_hint None",
       by_head.get("Where it is heading", {"entity_hint": "x"})["entity_hint"] is None)
    ok("prepass: primer heading containing a roster topic's tokens -> that topic",
       by_head.get("How widget pricing got here", {}).get("entity_hint") == "Widget Pricing")
    first = next(p for p in paras if p["text"].startswith("Industrial widget prices"))
    ok("prepass: [2–3] range footnote resolves to both endnote URLs",
       first["urls"] == ["https://trade.example.com/index", "https://freight.example.com/2025"])
    omar = next(p for p in paras if p["text"].startswith("Omar Placeholder"))
    ok("prepass: inline markdown link harvested", omar["urls"] == ["https://fictional.example.org/team"])
    noref = next(p for p in paras if p["text"].startswith("Most buyers"))
    ok("prepass: paragraph without a marker has no URLs (no brief-wide promotion)", noref["urls"] == [])
    ok("prepass: playbook sections dropped (Questions to ask, Conversation kit)",
       not any("?" in p["text"] or "KIT_SENTINEL" in p["text"] for p in paras)
       and pk["dropped_paragraphs"]["playbook_section"] == 3)
    ok("prepass: mostly-imperative paragraph dropped and counted",
       "Lead with the 18%" not in blob and pk["dropped_paragraphs"]["imperative"] == 1)
    ok("prepass: playbook words inside a parenthetical do not make a section playbook",
       classify("THE SIX ENABLING TECHNOLOGIES (contested questions inside each)") is None
       and classify("Hard-negatives primer (opener for the hosts)") == "keep"
       and classify("Topic pitches (if proposing in an unconference)") == "playbook"
       and classify("Conversation kits (9 topics)") == "playbook")
    ok("prepass: one imperative sentence does not drop a factual paragraph",
       not mostly_imperative("Acme Widgets raised $6M in 2024. Ask about pricing.")
       and not is_imperative("Use Cases: widget pricing, freight quotes") and is_imperative("*Ask* Dana about steel."))
    ok("prepass: table rows kept, separator dropped", any(p["text"] == "Customers served | about 1,400 in the Northeast" for p in paras)
       and not any("---" in p["text"] for p in paras))
    stub, swhy = prepass(os.path.join(FIX, "brief_stub"))
    ok("prepass: brief under 300 words is skipped", stub is None and swhy.startswith("stub_under_300"))

    # splitter output must clear its own gate, and its quotes are verbatim by construction
    sp = splitter(pk)
    res = check(pk, sp, extractor="splitter")
    ok("splitter: emits claims in the extractor schema", sp["claims"] and all(set(c) == CLAIM_KEYS for c in sp["claims"]))
    ok("splitter: no quote fails containment", "quote_not_verbatim" not in res["dropped"])
    ok("splitter: its own output never trips a schema check", not any(k.startswith("schema") for k in res["dropped"]))
    ok("splitter: an un-hinted paragraph naming one roster entity is attributed to it, with its type",
       any(c["para_idx"] == 4 and c["entity"] == "Acme Widgets" and c["entity_type"] == "company" for c in sp["claims"]))
    ok("prepass: consecutive lines are separate paragraphs (Notion export: one block per line)",
       sum(p["heading"] == "Acme Widgets" for p in paras) == 4)
    ok("splitter: abbreviation guard ('e.g.') does not split", sentences("Use a tool, e.g. Acme, for this. Next one.")
       == ["Use a tool, e.g. Acme, for this.", "Next one."])
    ok("splitter rows: extractor 'splitter', no model", all(r["extractor"] == "splitter" and "extractor_model" not in r
                                                            for r in res["accepted"]))

    claims = json.load(open(os.path.join(FIX, "claims_mixed.json"), encoding="utf-8"))
    err = io.StringIO()
    with redirect_stderr(err):
        r = check(pk, claims, extractor="claude", model="claude-sonnet-fixture")
    acc = {a["claim_text"]: a for a in r["accepted"]}
    d = r["dropped"]
    good = next((a for t, a in acc.items() if "founded Acme Widgets in 2019" in t), None)
    ok("check: URL in the same paragraph -> web_verified @0.55", good and good["provenance_tier"] == "web_verified"
       and good["confidence"] == 0.55 and good["locator"]["url"] == "https://acme.example.com/about")
    ok("check: stage shape (candidate, lane research, extractor claude, model kept)",
       good and good["status"] == "candidate" and good["lane"] == "research" and good["extractor"] == "claude"
       and good["extractor_model"] == "claude-sonnet-fixture" and good["claim_key"] == claim_key(good["claim_text"]))
    ref = next((a for t, a in acc.items() if "by phone or email" in t), None)
    ok("check: no URL in paragraph -> reference @0.40", ref and ref["provenance_tier"] == "reference"
       and ref["confidence"] == 0.40)
    ok("check: entity prefixed when the claim text does not name it", ref and ref["claim_text"].startswith("Acme Widgets: "))
    ok("check: url_ref from ANOTHER paragraph -> downgraded to reference, not dropped", r["flags"]["url_downgraded"] == 1
       and any("raised a $6M seed" in t and a["provenance_tier"] == "reference" for t, a in acc.items()))
    ok("check: a question and an imperative claim are dropped as not_declarative",
       d.get("not_declarative") == 2 and not any(a["claim_text"].endswith("?") for a in acc.values()))
    ok("check: non-verbatim quote dropped and counted", d.get("quote_not_verbatim") == 1)
    ok("check: unknown key dropped (strict schema)", d.get("schema_unknown_or_bad_shape") == 1)
    ok("check: missing key dropped", d.get("schema_missing_key") == 1)
    ok("check: bad enum dropped", d.get("schema_enum") == 1)
    ok("check: off-roster entity dropped", d.get("entity_unresolved") == 1)
    ok("check: email in claim text dropped (spine_client EMAIL_RE)", d.get("pii_contact_detail") == 2)
    ok("check: quote over 25 words dropped", d.get("quote_empty_or_over_25_words") == 1)
    ok("check: para_idx out of range dropped", d.get("para_idx_out_of_range") == 1)
    ok("check: duplicate claim dropped", d.get("duplicate_claim") == 1)
    ok("check: low claim/quote overlap flagged, not dropped", r["flags"]["low_overlap"] >= 1
       and any(a["metadata"].get("low_overlap") for a in acc.values()))
    ok("check: entity_type taken from the roster when the extractor mislabels it", r["flags"]["entity_type_corrected"] == 1)
    dumped = json.dumps(r) + err.getvalue()
    ok("check: no dropped claim's text or unknown key echoes into output or stderr",
       "SENTINEL_DROPPED" not in dumped and "sneaky_key" not in dumped)
    ok("check: every confidence <= 0.60", all(a["confidence"] <= CONF_CAP for a in r["accepted"]))
    orig = dict(CONF)
    try:                               # the cap is code, not data: a raised tier constant still cannot exceed it
        CONF["web_verified"] = 0.95
        hi = check(pk, {"claims": [claims["claims"][0]]})["accepted"][0]["confidence"]
    except Exception:
        hi = None
    finally:
        CONF.update(orig)
    ok("check: hard cap holds even if a tier constant is raised", hi == CONF_CAP)
    for bad in ({"claims": [], "extra": 1}, [], {"claims": {}}):
        try:
            check(pk, bad)
            ok(f"check: top-level {type(bad).__name__} rejected", False)
        except GateError as e:
            ok(f"check: top-level schema rejected ({type(bad).__name__}), message names no content",
               "extra" not in str(e))

    s = sample([r, res], n=10, stratify=True, seed=1, packets=[pk])
    ok("sample: stratified across (extractor, brief) strata", s["n"] == 10 and set(s["by_extractor"]) == {"claude", "splitter"}
       and abs(s["by_extractor"]["claude"] - s["by_extractor"]["splitter"]) <= 1)
    ok("sample: deterministic for a seed", sample([r, res], n=10, stratify=True, seed=1)["sample"][0]["claim_text"]
       == s["sample"][0]["claim_text"])
    ok("sample: paragraph attached when packets passed", all("paragraph" in it for it in s["sample"]))
    with tempfile.TemporaryDirectory() as td:          # CLI round trip
        pp = os.path.join(td, "p.json")
        rc = main(["prepass", os.path.join(FIX, "brief_ok"), "--out", pp])
        ok("cli: prepass writes the packet", rc == 0 and json.load(open(pp))["source_key"] == pk["source_key"])
        with redirect_stderr(io.StringIO()):
            rc3 = main(["prepass", os.path.join(FIX, "brief_stub"), "--out", os.path.join(td, "s.json")])
        ok("cli: stub exits 3 and writes nothing", rc3 == 3 and not os.path.exists(os.path.join(td, "s.json")))
    _batch_selftest(ok)
    print(f"selftest: {'PASS' if not fails else 'FAIL'} ({len(fails)} failing)")
    return not fails


def _batch_selftest(ok) -> None:
    """batch over a temp tree of fixture copies; LLM and ledger lookup stubbed (no network, no subprocess)."""
    import shutil
    with tempfile.TemporaryDirectory() as td:
        bd, od = os.path.join(td, "briefs"), os.path.join(td, "out")
        os.makedirs(bd)

        def clone(name, src="brief_ok", pid=None, otr=False, drop=None):
            d = os.path.join(bd, name)
            shutil.copytree(os.path.join(FIX, src), d)
            m = json.load(open(os.path.join(d, "manifest.json")))
            if pid:
                m["event"]["notion_page_id"] = pid
            if otr:
                m.setdefault("notion_export", {})["skip_staging"] = True
            json.dump(m, open(os.path.join(d, "manifest.json"), "w"))
            if drop:
                os.remove(os.path.join(d, drop))
        clone("2026-10-01-eligible")
        clone("2026-10-02-ledgered", pid="00000000-0000-4000-8000-00000000e1e1")
        clone("2026-10-03-otr", otr=True)
        clone("2026-10-04-no-manifest", drop="manifest.json")
        clone("2026-10-05-no-brief", drop="research_brief.md")
        clone("2026-10-06-stub", src="brief_stub")
        clone(DOSSIER_PREFIX + "someone")
        ledgered = research_source_key("00000000-0000-4000-8000-00000000e1e1")
        calls = []

        def fake_llm(pk, model):
            calls.append(pk["source_key"])
            return splitter(pk), "{}", ""
        res = batch(bd, od, model="sonnet-fixture", ledger_count=lambda k: 3 if k == ledgered else 0, llm=fake_llm)
        sc = res["skipped_counts"]
        ok("batch: only the eligible brief reaches the LLM", len(calls) == 1 and [r["brief"] for r in res["extracted"]]
           == ["2026-10-01-eligible"] and res["accepted_total"] > 0)
        ok("batch: no manifest / no research_brief.md skipped + counted, never a FileNotFoundError",
           sc.get("no_manifest") == 1 and sc.get("no_research_brief") == 1 and not res["errors"])
        ok("batch: skip_staging, interview dossier, ledger present, stub each skipped + counted",
           sc.get("skip_staging_otr") == 1 and sc.get("interview_dossier") == 1 and sc.get("ledger_present") == 1
           and sc.get("stub_under_300_words") == 1)
        ok("batch: checked file + summary written", os.path.exists(os.path.join(od, "2026-10-01-eligible.llm.checked.json"))
           and os.path.exists(os.path.join(od, "batch-summary.json")))
        calls.clear()
        res2 = batch(bd, od, ledger_count=lambda k: 3 if k == ledgered else 0, llm=fake_llm)
        ok("batch: a rerun skips briefs already checked (no second LLM spend)",
           not calls and res2["skipped_counts"].get("already_checked") == 1)

        def boom(pk, model):
            raise RuntimeError("SECRET_BRIEF_TEXT")
        shutil.rmtree(od)
        res3 = batch(bd, od, ledger_count=lambda k: 0, llm=boom)
        ok("batch: one LLM failure is recorded by type, no content, and does not stop the batch",
           res3["errors"] and all(e["error"] == "RuntimeError" for e in res3["errors"])
           and "SECRET_BRIEF_TEXT" not in json.dumps(res3))
    ok("batch: the LLM command is the pilot's tool-less headless call",
       llm_cmd("sonnet")[:4] == ["claude", "-p", "--model", "sonnet"] and "--strict-mcp-config" in llm_cmd("sonnet")
       and llm_cmd("sonnet")[llm_cmd("sonnet").index("--tools") + 1] == "")


# ---------------------------------------------------------------------------------------------------------------
def _emit(obj, out: str | None) -> None:
    s = json.dumps(obj, indent=1, ensure_ascii=False)
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(s + "\n")
    else:
        print(s)


def main(argv: list[str]) -> int:
    if argv[:1] == ["--selftest"]:
        return 0 if selftest() else 1
    ap = argparse.ArgumentParser(prog="prose_extract.py", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="verb", required=True)
    a = sub.add_parser("prepass"); a.add_argument("brief_dir"); a.add_argument("--out")
    a = sub.add_parser("splitter"); a.add_argument("packet"); a.add_argument("--out")
    a = sub.add_parser("check"); a.add_argument("packet"); a.add_argument("claims")
    a.add_argument("--extractor", default="claude", choices=["claude", "splitter"]); a.add_argument("--model")
    a.add_argument("--out")
    a = sub.add_parser("sample"); a.add_argument("checked", nargs="+"); a.add_argument("--n", type=int, default=100)
    a.add_argument("--stratify", action="store_true"); a.add_argument("--seed", type=int, default=384)
    a.add_argument("--packets", nargs="*"); a.add_argument("--out")
    a = sub.add_parser("batch"); a.add_argument("--briefs-dir", required=True); a.add_argument("--out-dir", required=True)
    a.add_argument("--model", default="sonnet"); a.add_argument("--concurrency", type=int, default=4)
    a = ap.parse_args(argv)
    load = lambda p: json.load(open(p, encoding="utf-8"))   # noqa: E731
    if a.verb == "prepass":
        pk, why = prepass(a.brief_dir)
        if pk is None:
            sys.stderr.write(f"prepass: skipped {os.path.basename(a.brief_dir.rstrip('/'))}: {why}\n")
            return 3
        _emit(pk, a.out)
        n_url = sum(bool(p["urls"]) for p in pk["paragraphs"])
        sys.stderr.write(f"prepass: {len(pk['paragraphs'])} paragraphs · {n_url} with a URL · "
                         f"dropped {pk['dropped_paragraphs']}\n")
    elif a.verb == "splitter":
        out = splitter(load(a.packet))
        _emit(out, a.out)
        sys.stderr.write(f"splitter: {len(out['claims'])} sentence claims\n")
    elif a.verb == "check":
        try:
            res = check(load(a.packet), load(a.claims), extractor=a.extractor, model=a.model)
        except (GateError, json.JSONDecodeError) as e:
            sys.stderr.write(f"check: REJECTED whole file: {type(e).__name__}: "
                             f"{e if isinstance(e, GateError) else 'not valid JSON'}\n")
            return 2
        _emit(res, a.out)
        sys.stderr.write(f"check: {res['accepted_n']}/{res['claims_in']} accepted · dropped {res['dropped']} · "
                         f"flags {res['flags']}\n")
    elif a.verb == "sample":
        res = sample([load(p) for p in a.checked], n=a.n, stratify=a.stratify, seed=a.seed,
                     packets=[load(p) for p in a.packets or []])
        _emit(res, a.out)
        sys.stderr.write(f"sample: {res['n']} claims from {res['strata']} strata · {res['by_extractor']}\n")
    elif a.verb == "batch":
        res = batch(a.briefs_dir, a.out_dir, model=a.model, concurrency=a.concurrency)
        sys.stderr.write(f"batch: {res['briefs_seen']} dirs · extracted {len(res['extracted'])} · errors "
                         f"{len(res['errors'])} · accepted {res['accepted_total']} · skipped {res['skipped_counts']}\n")
        return 1 if res["errors"] else 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
