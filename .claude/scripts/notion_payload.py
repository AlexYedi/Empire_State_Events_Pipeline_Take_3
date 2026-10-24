#!/usr/bin/env python3
"""Validate a notion-writer payload before dispatch (YED-259, CLAUDE.md invariant 5).

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

Body-edit rules (content_updates):
- Bounded: each old_str is >= 20 chars or contains an HTML-comment marker.
- A section start marker (<!-- deep_read_rendered: ... -->, <!-- research_brief -->) in old_str must come with
  its end marker (<!-- /deep_read -->, <!-- /research_brief -->), or, on a legacy page without one, old_str must
  end on the next "## " heading and new_str must end on the same heading; new_str always carries both markers.
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
SECTIONS = {"<!-- deep_read_rendered:": "<!-- /deep_read -->", "<!-- research_brief -->": "<!-- /research_brief -->"}
MIN_ANCHOR = 20


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
    if len(old) < MIN_ANCHOR and "<!--" not in old:
        out.append(f"{tag} content_updates[{j}] old_str is a short anchor with no marker (needs >= {MIN_ANCHOR} chars "
                   "or an HTML-comment marker)")
    for start, end in SECTIONS.items():
        if start in old and end not in old:
            legacy = last_heading(old)
            if not (legacy and last_heading(new) == legacy):
                out.append(f"{tag} content_updates[{j}] old_str has {start} without its end marker {end} "
                           "(or, on a legacy page, the next ## heading kept in new_str)")
        if start in new and end not in new:
            out.append(f"{tag} content_updates[{j}] new_str has {start} without its end marker {end}")
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


def main():
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
