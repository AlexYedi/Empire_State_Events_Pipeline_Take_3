#!/usr/bin/env python3
r"""Validate a notion-writer payload before dispatch (YED-259, CLAUDE.md invariant 5).

The parent decides every write; the notion-writer agent only executes this file. A payload that
fails validation is never dispatched. Exit 0 = valid (prints a one-line summary), 1 = invalid
(prints every problem).

Payload shape (JSON):
{
  "run": "<event or batch label>",
  "manifest": "<path to the run manifest .json; created if missing>",
  "allowed_page_ids": ["<uuid>", ...],         # optional; existing pages this run may update (REFRESH targets
                                               # from triage). Pages already in the manifest need not be listed.
  "operations": [
    {
      "key": "<stable id for this write, e.g. company:surrealdb>",   # idempotency key in the manifest
      "op": "create" | "update",
      "parent": {"data_source_id": "<one of the 8 DBs>"} | {"page_id": "<known uuid>"} | null,  # create only; null = private page
      "page_id": "<bare uuid>",                # update only; must be in the manifest or allowed_page_ids
      "dedup": {"query": "<search text>", "match_title": "<exact title>"},  # create into a data source: required
      "properties": { ... },                   # Notion MCP property format (see notion-write-gotchas.md)
      "content": "<markdown body>",            # optional; create only, or update with "replace_content": true
      "content_updates": [{"old_str": "<exact stored text>", "new_str": "<replacement>"}],
                                               # optional; update only: replace a marker-bounded section, or insert
                                               # before a terminal marker the parent wrote at create time
      "alex_provided": true,                   # optional; only when Alex gave the Email / Phone himself (ADR-9)
      "frozen_statuses": ["scheduled", "published"]  # optional; never touch a page whose status is one of these
    }
  ]
}

Markers are ⟦name⟧ / ⟦/name⟧ with hyphenated names (Notion stores them byte-identical). Notion does NOT keep
HTML comments: <!-- x_y --> is stored and fetched back as visible text \<!-- x\_y --> (sandbox 2026-10-24), so a raw
<!-- in any body or anchor is refused.
Body-edit rules (content_updates):
- Bounded: each old_str is >= 20 chars or contains a ⟦marker⟧ (or the escaped legacy form \<!--).
- A section start marker (⟦deep-read: ...⟧, ⟦research-brief⟧) in old_str or new_str must come with its end
  marker (⟦/deep-read⟧, ⟦/research-brief⟧).
- Legacy pages carry the escaped Deep Read marker \<!-- deep\_read\_rendered: pending --> (JSON:
  "\\<!-- deep\\_read\\_rendered: pending -->") with no end marker: old_str must run from it through the next "## "
  heading, new_str must end on the same heading and write the new ⟦deep-read: ...⟧ … ⟦/deep-read⟧ pair.
- Real newlines only (a literal backslash-n lands as a stray "n", gotcha m).
People pages never get Email / Phone / Phone Number unless "alex_provided": true (ADR-9 tier 1).
Post / connection-note / DM copy (Content Type linkedin_*) is plain paragraphs, never code fences (gotcha p).

Usage: notion_payload.py <payload.json>
"""
import json
import re
import sys
from pathlib import Path

OPS = {"create", "update"}
DATA_SOURCES = {  # CLAUDE.md §3
    "9dcbc999-b4ed-4a51-b48a-10aaf171f1ba": "Events",
    "4a1af67f-9141-4ba5-aa9d-88b07dcd5f86": "People",
    "d5910dc3-8327-4b49-9294-fc9499709a98": "Companies",
    "d61ce9df-94b3-4637-aa09-d77e09ab3a74": "Topics",
    "6c24c9f5-66c9-4eed-a61d-3f9b87c3f775": "Content Drafts",
    "0956e6ed-8555-4d8f-8856-388966dedaab": "Project Ideas",
    "3a174257-e90b-48be-b4bb-097ba5dc4231": "Roles",
    "1cd6d576-8a9e-4332-bb81-13a28b55f151": "To-dos",
}
PEOPLE_DS = "4a1af67f-9141-4ba5-aa9d-88b07dcd5f86"
DRAFTS_DS = "6c24c9f5-66c9-4eed-a61d-3f9b87c3f775"
PII_PROPS = {"Email", "Phone", "Phone Number"}
COPY_TYPE_PREFIX = "linkedin_"   # Content Drafts copy Alex reviews by inline comment (gotcha p)
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
SECTIONS = {"⟦deep-read:": "⟦/deep-read⟧", "⟦research-brief⟧": "⟦/research-brief⟧"}
LEGACY_STARTS = {"\\<!-- deep\\_read\\_rendered:": ("⟦deep-read:", "⟦/deep-read⟧")}  # as Notion stores the old comment
MARKER_RE = re.compile(r"⟦[^⟧\n]+⟧")
RAW_COMMENT_RE = re.compile(r"(?<!\\)<!--")
MIN_ANCHOR = 20

# --- E-08: payload truncation check -----------------------------------------
# The 10/18 batch wrote Topic "Current Events" values cut off mid-word ("AI Sales
# Coaches", "Accelerator Ecosystem", "AI for VC Workflows") because a length cut was
# applied upstream. The rule, stated precisely: a text property value looks cut
# mid-word when (a) its length is >= TRUNCATION_CUT_LENGTH — the upstream cut
# observed in that batch, floored at 100 chars so no short legitimate value can
# trip it; (b) after stripping trailing whitespace and closing quotes/brackets,
# its final character is alphanumeric (terminal punctuation — . ! ? … : ; , — or a
# closing symbol after the strip means the sentence was finished).
TRUNCATION_CUT_LENGTH = 100
_TERMINAL_STRIP = " \t\n'\"”’)]}»"


def looks_cut_mid_word(text):
    trimmed = text.rstrip(_TERMINAL_STRIP)
    return len(text) >= TRUNCATION_CUT_LENGTH and trimmed != "" and trimmed[-1].isalnum()


def text_property_values(props):
    """Yield (property_name, content) for every title/rich_text text item in a
    Notion-format properties object."""
    for name, v in props.items():
        if not isinstance(v, dict):
            continue
        for kind in ("title", "rich_text"):
            arr = v.get(kind)
            if not isinstance(arr, list):
                continue
            for item in arr:
                content = item.get("text", {}).get("content") if isinstance(item, dict) else None
                if isinstance(content, str) and content.strip():
                    yield name, content


def truncation_problems(tag, o):
    """Flag text property values that end mid-word after a length cut (E-08)."""
    out = []
    props = o.get("properties") if isinstance(o.get("properties"), dict) else {}
    for name, val in text_property_values(props):
        if looks_cut_mid_word(val):
            out.append(f"{tag} (key '{o.get('key')}') property '{name}' looks cut mid-word (E-08): "
                       f"length {len(val)} >= {TRUNCATION_CUT_LENGTH} with a final alphanumeric "
                       f"character and no terminal punctuation — value ends: ...{val[-40:]}")
    return out


def norm(pid):
    return str(pid).replace("-", "").lower()


def load_manifest(path):
    """Manifest entries keyed by normalized page id -> manifest key. Missing manifest = empty."""
    p = Path(path)
    if not p.is_absolute() and not p.exists():
        p = Path(__file__).resolve().parents[2] / p   # repo root
    try:
        m = json.load(open(p))
    except (OSError, ValueError):
        return {}
    return {norm(v["page_id"]): k for k, v in m.items() if isinstance(v, dict) and v.get("page_id")}


def last_heading(s):
    lines = [ln for ln in s.rstrip().splitlines() if ln.strip()]
    return lines[-1] if lines and lines[-1].startswith("## ") else None


def anchor_problems(tag, j, old, new):
    out = []
    for name, text in (("old_str", old), ("new_str", new)):
        if RAW_COMMENT_RE.search(text):
            out.append(f"{tag} content_updates[{j}] {name} has a raw <!-- comment; Notion stores comments escaped "
                       "(\\<!-- …), so use a ⟦name⟧ marker (or the escaped fetched form for a legacy anchor)")
    if len(old) < MIN_ANCHOR and not MARKER_RE.search(old) and "\\<!--" not in old:
        out.append(f"{tag} content_updates[{j}] old_str is a short anchor with no marker (needs >= {MIN_ANCHOR} chars "
                   "or a ⟦marker⟧)")
    for start, end in SECTIONS.items():
        if start in old and end not in old:
            out.append(f"{tag} content_updates[{j}] old_str has {start} without its end marker {end}")
        if start in new and end not in new:
            out.append(f"{tag} content_updates[{j}] new_str has {start} without its end marker {end}")
    for start, (new_start, new_end) in LEGACY_STARTS.items():
        if start in old:
            bound = last_heading(old)
            if not (bound and last_heading(new) == bound):
                out.append(f"{tag} content_updates[{j}] legacy {start} has no end marker: old_str must run through the "
                           "next ## heading and new_str must end on the same heading")
            if new_start not in new or new_end not in new:
                out.append(f"{tag} content_updates[{j}] legacy replace must write {new_start} … {new_end} in new_str")
    return out


def body_problems(tag, o):
    out = []
    op = o.get("op")
    if "append_content" in o:
        out.append(f"{tag} 'append_content' was removed; use content_updates on a marker written at create time")
    has_cu = "content_updates" in o
    if has_cu and op != "update":
        out.append(f"{tag} content_updates is update-only (a create puts its body in 'content')")
    updates = []
    if has_cu:
        cu = o["content_updates"]
        if not isinstance(cu, list) or not cu:
            out.append(f"{tag} 'content_updates' must be a non-empty list of {{old_str, new_str}}")
        else:
            for j, u in enumerate(cu):
                if not isinstance(u, dict) or not isinstance(u.get("old_str"), str) or not u["old_str"].strip() \
                        or not isinstance(u.get("new_str"), str):
                    out.append(f"{tag} content_updates[{j}] needs a non-empty old_str and a string new_str")
                    continue
                updates.append(u)
                if u["old_str"] == u["new_str"]:
                    out.append(f"{tag} content_updates[{j}] old_str and new_str are identical (no-op)")
                else:
                    out += anchor_problems(tag, j, u["old_str"], u["new_str"])
    if o.get("replace_content") and has_cu:
        out.append(f"{tag} replace_content replaces the whole body; do not combine it with content_updates")
    if isinstance(o.get("content"), str) and RAW_COMMENT_RE.search(o["content"]):
        out.append(f"{tag} content has a raw <!-- comment; Notion stores it as visible escaped text, use a ⟦name⟧ marker")
    texts = [o.get("content")] + [u["new_str"] for u in updates]
    if op == "update" and any(isinstance(t, str) and "\\n" in t for t in texts):
        out.append(f"{tag} update body contains a literal backslash-n; use real newlines (gotcha m)")
    props = o.get("properties") if isinstance(o.get("properties"), dict) else {}
    ctype = props.get("Content Type")
    parent = o.get("parent") if isinstance(o.get("parent"), dict) else {}
    if op == "create" and parent.get("data_source_id") == DRAFTS_DS and not ctype:
        out.append(f"{tag} a Content Drafts create needs a 'Content Type'")
    if isinstance(ctype, str) and ctype.startswith(COPY_TYPE_PREFIX) \
            and any(isinstance(t, str) and "```" in t for t in texts):
        out.append(f"{tag} {ctype} copy contains a code fence; drafts are plain paragraphs (gotcha p)")
    out += truncation_problems(tag, o)
    return out


def problems(p):
    out = []
    if not isinstance(p, dict):
        return ["payload is not a JSON object"]
    for k in ("run", "manifest", "operations"):
        if k not in p:
            out.append(f"missing top-level '{k}'")
    ops = p.get("operations") or []
    if not isinstance(ops, list) or not ops:
        out.append("'operations' must be a non-empty list")
        return out
    allowed = p.get("allowed_page_ids", [])
    if not isinstance(allowed, list):
        out.append("'allowed_page_ids' must be a list of page UUIDs")
        allowed = []
    known = load_manifest(p.get("manifest", "")) if isinstance(p.get("manifest"), str) else {}
    known_ids = set(known) | {norm(a) for a in allowed}
    keys = set()
    for i, o in enumerate(ops):
        tag = f"operations[{i}]"
        if not isinstance(o, dict):
            out.append(f"{tag} is not an object")
            continue
        key = o.get("key")
        if not key:
            out.append(f"{tag} missing 'key' (idempotency)")
        elif key in keys:
            out.append(f"{tag} duplicate key '{key}'")
        keys.add(key)
        op = o.get("op")
        if op not in OPS:
            out.append(f"{tag} 'op' must be create or update")
        people = False
        if op == "create":
            parent = o.get("parent", "MISSING")
            if parent == "MISSING":
                out.append(f"{tag} create needs 'parent' (null for a private page)")
            elif isinstance(parent, dict) and "data_source_id" in parent:
                ds = parent["data_source_id"]
                if ds not in DATA_SOURCES:
                    out.append(f"{tag} parent data_source_id '{ds}' is not one of the 8 known databases (CLAUDE.md §3)")
                people = ds == PEOPLE_DS
                d = o.get("dedup") or {}
                if not d.get("query") or not d.get("match_title"):
                    out.append(f"{tag} create into a data source needs dedup.query and dedup.match_title (invariant 8)")
            elif isinstance(parent, dict) and "page_id" in parent:
                if norm(parent["page_id"]) not in known_ids:
                    out.append(f"{tag} parent page_id is not in the manifest or allowed_page_ids")
        if op == "update":
            pid = o.get("page_id")
            if not pid:
                out.append(f"{tag} update needs 'page_id' (or a manifest entry for its key; parent resolves before dispatch)")
            elif not UUID_RE.match(str(pid).lower()):
                out.append(f"{tag} page_id must be a bare UUID, not a URL (gotcha o)")
            elif norm(pid) not in known_ids:
                out.append(f"{tag} page_id {pid} is not in the manifest or allowed_page_ids")
            else:
                people = known.get(norm(pid), "").startswith("person:")
            if not o.get("properties") and not o.get("content_updates") and not o.get("replace_content"):
                out.append(f"{tag} update has nothing to do (no properties, no content_updates, no replace_content)")
        if isinstance(key, str) and key.startswith("person:"):
            people = True
        if "properties" in o and not isinstance(o["properties"], dict):
            out.append(f"{tag} 'properties' must be an object")
        elif people and o.get("alex_provided") is not True:
            pii = sorted(PII_PROPS & set(o.get("properties") or {}))
            if pii:
                out.append(f"{tag} People page gets {', '.join(pii)} without \"alex_provided\": true (ADR-9 tier 1)")
        if "content" in o and not isinstance(o["content"], str):
            out.append(f"{tag} 'content' must be a string")
        fs = o.get("frozen_statuses")
        if fs is not None and (not isinstance(fs, list) or not all(isinstance(s, str) for s in fs)):
            out.append(f"{tag} 'frozen_statuses' must be a list of status strings")
        out += body_problems(tag, o)
    return out


# ---------------------------------------------------------------------------
# selftest — pin every rejection branch + one valid payload (E-07)
# ---------------------------------------------------------------------------
def selftest():
    """--selftest: at least one case per rejection branch of problems()/body_problems()/
    anchor_problems(), plus one valid payload end-to-end through main(). Fixtures are
    synthetic and *.example-only; nothing is dispatched, no network, and the only files
    written are tempfiles this function removes."""
    import contextlib
    import io
    import os
    import shutil
    import tempfile

    EV_DS = "9dcbc999-b4ed-4a51-b48a-10aaf171f1ba"  # Events
    good_uuid = "44444444-4444-4444-4444-444444444444"

    checks = []
    TRACKED_VALUES = []  # every fixture text value seen this run — E-08 false-positive measurement

    def ck(name, cond):
        checks.append((name, bool(cond)))

    def hits(p, needle):
        return [e for e in problems(p) if needle in e]

    def create_op(**o):
        op = {"key": "event:selftest", "op": "create",
              "parent": {"data_source_id": EV_DS},
              "dedup": {"query": "Selftest Event", "match_title": "Selftest Event"},
              "properties": {"Name": {"title": [{"text": {"content": "Selftest Event"}}]}}}
        op.update(o)
        if isinstance(op["properties"], dict):
            TRACKED_VALUES.extend(v for _, v in text_property_values(op["properties"]))
        return op

    def update_op(**o):
        op = {"key": "update:selftest", "op": "update", "page_id": good_uuid,
              "properties": {"Name": {"rich_text": [{"text": {"content": "Selftest Co"}}]}}}
        op.update(o)
        if isinstance(op["properties"], dict):
            TRACKED_VALUES.extend(v for _, v in text_property_values(op["properties"]))
        return op

    def pay(ops, **o):
        p = {"run": "selftest", "manifest": "selftest-no-such-manifest.json", "operations": ops}
        p.update(o)
        return p

    ck("top-level: non-object payload rejected",
       problems(["nope"]) == ["payload is not a JSON object"])
    for k in ("run", "manifest", "operations"):
        p = pay([create_op()])
        del p[k]
        ck(f"top-level: missing '{k}' rejected", bool(hits(p, f"missing top-level '{k}'")))
    ck("top-level: empty operations rejected",
       bool(hits(pay([], allowed_page_ids=[good_uuid]), "'operations' must be a non-empty list")))
    ck("top-level: allowed_page_ids that is not a list rejected",
       bool(hits(pay([create_op()], allowed_page_ids="x"), "'allowed_page_ids' must be a list")))

    ck("op: unknown op rejected", bool(hits(pay([create_op(op="delete")]), "'op' must be create or update")))
    p = pay([create_op()])
    del p["operations"][0]["key"]
    ck("idempotency: missing key rejected", bool(hits(p, "missing 'key'")))
    ck("idempotency: duplicate key rejected",
       bool(hits(pay([create_op(), create_op(key="event:selftest")]), "duplicate key")))

    p = pay([create_op()])
    del p["operations"][0]["parent"]
    ck("create: missing parent rejected", bool(hits(p, "create needs 'parent'")))
    ck("create: unknown data_source_id rejected",
       bool(hits(pay([create_op(parent={"data_source_id": "not-a-uuid"})]),
                 "not one of the 8 known databases")))
    p = pay([create_op()])
    del p["operations"][0]["dedup"]
    ck("create: missing dedup rejected",
       bool(hits(p, "needs dedup.query and dedup.match_title")))
    ck("create: parent page_id outside the manifest/allowlist rejected",
       bool(hits(pay([create_op(parent={"page_id": good_uuid})]),
                 "parent page_id is not in the manifest or allowed_page_ids")))

    p = pay([update_op()])
    del p["operations"][0]["page_id"]
    ck("update: missing page_id rejected", bool(hits(p, "update needs 'page_id'")))
    ck("update: URL instead of bare UUID rejected (gotcha o)",
       bool(hits(pay([update_op(page_id="https://notion.so/" + good_uuid)]),
                 "must be a bare UUID")))
    ck("update: page_id outside manifest/allowlist rejected",
       bool(hits(pay([update_op(page_id="33333333-3333-3333-3333-333333333333")], allowed_page_ids=[]),
                 "is not in the manifest or allowed_page_ids")))
    p = pay([update_op()])
    del p["operations"][0]["properties"]
    ck("update: nothing-to-do rejected",
       bool(hits(p, "update has nothing to do")))
    ck("update: properties that are not an object rejected",
       bool(hits(pay([update_op(properties="oops")]), "'properties' must be an object")))
    ck("update: content that is not a string rejected",
       bool(hits(pay([update_op(content=5)]), "'content' must be a string")))
    ck("frozen_statuses: non-list rejected",
       bool(hits(pay([update_op(frozen_statuses="scheduled")]), "'frozen_statuses' must be a list")))

    # PII (ADR-9 tier 1) — three detection routes, plus the alex_provided escape hatch
    pii_prop = {"Email": {"rich_text": [{"text": {"content": "someone@example.com"}}]}}
    ck("PII: People data-source create with Email refused without alex_provided",
       bool(hits(pay([create_op(parent={"data_source_id": "4a1af67f-9141-4ba5-aa9d-88b07dcd5f86"},
                                properties=pii_prop)]), "ADR-9 tier 1")))
    ck("PII: person:-prefixed key with Email refused without alex_provided",
       bool(hits(pay([create_op(key="person:selftest", properties=pii_prop)]), "ADR-9 tier 1")))
    ck("PII: alex_provided=true lets a People page carry Email",
       not hits(pay([create_op(parent={"data_source_id": "4a1af67f-9141-4ba5-aa9d-88b07dcd5f86"},
                               properties=pii_prop, alex_provided=True)]), "ADR-9 tier 1"))

    ck("body: removed append_content refused",
       bool(hits(pay([create_op(append_content="x")]), "'append_content' was removed")))
    ck("body: content_updates on a create refused",
       bool(hits(pay([create_op(content_updates=[{"old_str": "x", "new_str": "y"}])]),
                 "content_updates is update-only")))
    ck("body: empty content_updates refused",
       bool(hits(pay([update_op(content_updates=[])]), "must be a non-empty list")))
    ck("body: content_updates entry without old_str refused",
       bool(hits(pay([update_op(content_updates=[{"old_str": "", "new_str": "y"}])]),
                 "needs a non-empty old_str")))
    ck("body: identical old_str/new_str (no-op) refused",
       bool(hits(pay([update_op(content_updates=[{"old_str": "same text same text same text",
                                                  "new_str": "same text same text same text"}])]),
                 "are identical")))

    # anchor_problems branches
    ck("anchor: raw <!-- in old_str refused",
       bool(hits(pay([update_op(content_updates=[{"old_str": "x " * 20 + " <!--",
                                                  "new_str": "y " * 25}])]),
                 "has a raw <!-- comment")))
    ck("anchor: short old_str with no marker refused",
       bool(hits(pay([update_op(content_updates=[{"old_str": "short",
                                                  "new_str": "short but different"}])]),
                 "short anchor with no marker")))
    ck("anchor: section start without its end marker in old_str refused",
       bool(hits(pay([update_op(content_updates=[
           {"old_str": "⟦deep-read: 2026-10-01⟧ " + "body " * 10, "new_str": "fresh " * 12}])]),
           "old_str has ⟦deep-read: without its end marker")))
    ck("anchor: section start without its end marker in new_str refused",
       bool(hits(pay([update_op(content_updates=[
           {"old_str": "⟦research-brief⟧ old body one two three ⟦/research-brief⟧",
            "new_str": "⟦research-brief⟧ new body one two three four"}])]),
           "new_str has ⟦research-brief⟧ without its end marker")))

    # legacy Deep Read marker: old_str must run through the next ## heading and new_str must
    # end on the same heading with the fresh ⟦deep-read⟧ pair written
    legacy_old = "\\<!-- deep\\_read\\_rendered: pending -->\nLegacy body line one two three four\n\n## Deep Read"
    ck("anchor: legacy marker whose new_str ends on a different heading refused",
       bool(hits(pay([update_op(content_updates=[
           {"old_str": legacy_old,
            "new_str": "⟦deep-read: 2026-10-01⟧\nNew body one two three\n⟦/deep-read⟧\n\n## Other"}])]),
           "must run through the next ## heading")))
    ck("anchor: legacy replace that writes no fresh marker pair refused",
       bool(hits(pay([update_op(content_updates=[
           {"old_str": legacy_old,
            "new_str": "Replacement body one two three four\n\n## Deep Read"}])]),
           "legacy replace must write")))
    ck("anchor: a well-formed legacy replace is accepted",
       not hits(pay([update_op(content_updates=[
           {"old_str": legacy_old,
            "new_str": "⟦deep-read: 2026-10-01⟧\nFresh body one two three\n⟦/deep-read⟧\n\n## Deep Read"}])]),
           "legacy"))

    ck("body: replace_content combined with content_updates refused",
       bool(hits(pay([update_op(replace_content=True,
                                content_updates=[{"old_str": "long enough old_str here",
                                                  "new_str": "long enough new_str here"}])]),
                 "do not combine it with content_updates")))
    ck("body: raw <!-- in content refused",
       bool(hits(pay([create_op(content="<!-- hidden note -->")]), "content has a raw <!-- comment")))
    ck("body: literal backslash-n in an update body refused (gotcha m)",
       bool(hits(pay([update_op(content="line one\\nline two")]), "literal backslash-n")))
    ck("body: Content Drafts create without a Content Type refused",
       bool(hits(pay([create_op(parent={"data_source_id": "6c24c9f5-66c9-4eed-a61d-3f9b87c3f775"})]),
                 "a Content Drafts create needs a 'Content Type'")))
    ck("body: linkedin_* copy with a code fence refused (gotcha p)",
       bool(hits(pay([create_op(parent={"data_source_id": "6c24c9f5-66c9-4eed-a61d-3f9b87c3f775"},
                                properties={"Content Type": "linkedin_post"},
                                content="paragraph one\n```\nfenced\n```")]),
                 "code fence")))

    # E-08: truncation check — a value cut mid-word fails; a complete value of the same
    # length that ends in punctuation passes
    trunc_val = ("AI Sales Coaches " * 10)[:100]
    assert len(trunc_val) == TRUNCATION_CUT_LENGTH and trunc_val[-1].isalnum()
    complete_val = trunc_val[:-1] + "."
    ck("truncation: value cut mid-word after a length cut is flagged (E-08)",
       bool(hits(pay([create_op(key="event:trunc",
                                properties={"Current Events": {"rich_text": [
                                    {"text": {"content": trunc_val}}]}})]), "cut mid-word")))
    ck("truncation: same-length value ending in terminal punctuation passes (E-08)",
       not hits(pay([create_op(key="event:complete",
                               properties={"Current Events": {"rich_text": [
                                   {"text": {"content": complete_val}}]}})]), "cut mid-word"))

    # manifest-resolved people detection: an update to a page the manifest keys as person:*
    tmpdir = tempfile.mkdtemp(prefix="notion_payload_selftest_")
    try:
        person_uuid = "22222222-2222-2222-2222-222222222222"
        manifest_path = os.path.join(tmpdir, "manifest.json")
        with open(manifest_path, "w") as fh:
            json.dump({"person:jane-doe": {"page_id": person_uuid}}, fh)
        p = pay([update_op(key="person:jane-doe", page_id=person_uuid, properties=pii_prop)],
                manifest=manifest_path)
        ck("PII: update to a manifest-keyed person page refused without alex_provided",
           bool(hits(p, "ADR-9 tier 1")))

        # the one valid payload, end-to-end through main(): prints VALID and exits 0
        good = pay(
            [create_op(content="A plain body paragraph."),
             update_op()],
            allowed_page_ids=[good_uuid])
        ck("valid payload: problems() is clean", problems(good) == [])
        payload_path = os.path.join(tmpdir, "payload.json")
        with open(payload_path, "w") as fh:
            json.dump(good, fh)
        old_argv = sys.argv
        sys.argv = ["notion_payload.py", payload_path]
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = main()
            out = buf.getvalue()
        finally:
            sys.argv = old_argv
        ck("valid payload: main() exits 0 and prints VALID with the create/update counts",
           code == 0 and out.startswith("VALID: 2 operations (1 create, 1 update)"))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    fails = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  {'✓' if ok else '✗'} {n}")
    print(f"selftest: {len(checks) - len(fails)}/{len(checks)} notion-payload cases pass")
    intentional = sum(1 for v in TRACKED_VALUES if looks_cut_mid_word(v))
    false_positives = max(intentional - 2, 0)  # exactly the two intentional E-08 truncation fixtures
    print(f"E-08 false-positive check: {len(TRACKED_VALUES)} fixture text values, "
          f"{intentional} flagged ({false_positives} unintended) — "
          f"false-positive rate {false_positives}/{len(TRACKED_VALUES)}")
    return 0 if not fails else 1


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    try:
        payload = json.load(open(sys.argv[1]))
    except (OSError, ValueError) as e:
        print(f"INVALID: cannot read JSON: {e}")
        return 1
    errs = problems(payload)
    if errs:
        print("INVALID:\n- " + "\n- ".join(errs))
        return 1
    ops = payload["operations"]
    print(f"VALID: {len(ops)} operations ({sum(o['op'] == 'create' for o in ops)} create, "
          f"{sum(o['op'] == 'update' for o in ops)} update) · manifest {payload['manifest']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
