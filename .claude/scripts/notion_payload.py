#!/usr/bin/env python3
"""Validate a notion-writer payload before dispatch (YED-259, CLAUDE.md invariant 5).

The parent decides every write; the notion-writer agent only executes this file. A payload that
fails validation is never dispatched. Exit 0 = valid (prints a one-line summary), 1 = invalid
(prints every problem).

Payload shape (JSON):
{
  "run": "<event or batch label>",
  "manifest": "<path to the run manifest .json; created if missing>",
  "operations": [
    {
      "key": "<stable id for this write, e.g. company:surrealdb>",   # idempotency key in the manifest
      "op": "create" | "update",
      "parent": {"data_source_id": "<uuid>"} | {"page_id": "<uuid>"} | null,   # create only; null = private page
      "page_id": "<uuid>",                     # update only (or resolved from the manifest by key)
      "dedup": {"query": "<search text>", "match_title": "<exact title>"},  # create into a data source: required
      "properties": { ... },                   # Notion MCP property format (see notion-write-gotchas.md)
      "content": "<markdown body>",            # optional; create only, or update with "replace_content": true
      "frozen_statuses": ["scheduled", "published"]  # optional; never touch a page whose status is one of these
    }
  ]
}

Usage: notion_payload.py <payload.json>
"""
import json
import sys

OPS = {"create", "update"}


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
        if op == "create":
            parent = o.get("parent", "MISSING")
            if parent == "MISSING":
                out.append(f"{tag} create needs 'parent' (null for a private page)")
            elif isinstance(parent, dict) and "data_source_id" in parent:
                d = o.get("dedup") or {}
                if not d.get("query") or not d.get("match_title"):
                    out.append(f"{tag} create into a data source needs dedup.query and dedup.match_title (invariant 8)")
        if op == "update" and not o.get("page_id"):
            out.append(f"{tag} update needs 'page_id' (or a manifest entry for its key; parent resolves before dispatch)")
        if "properties" in o and not isinstance(o["properties"], dict):
            out.append(f"{tag} 'properties' must be an object")
        if "content" in o and not isinstance(o["content"], str):
            out.append(f"{tag} 'content' must be a string")
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
