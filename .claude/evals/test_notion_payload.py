#!/usr/bin/env python3
"""test_notion_payload.py — the notion-writer payload validator (YED-259 rollout). Offline, free.

Pins what the parent may hand the one Notion writer:
- creates only into the 8 known databases, with search-before-create (invariant 8);
- updates only to pages the run already knows (in the manifest or the payload's allowed_page_ids), by bare UUID;
- body edits only as bounded content_updates on a marker the parent wrote (no append-at-end);
- no research-written Email / Phone on People (ADR-9 tier 1) unless the op says alex_provided;
- the two formatting traps that land silently: literal \\n in update bodies (gotcha m), code fences in draft copy (gotcha p).
"""
import importlib.util, json, sys, tempfile
from pathlib import Path

VALIDATOR = Path(__file__).resolve().parents[1] / "scripts" / "notion_payload.py"
spec = importlib.util.spec_from_file_location("np", VALIDATOR)
np_ = importlib.util.module_from_spec(spec); spec.loader.exec_module(np_)
ok = n = 0
DRAFTS = {"data_source_id": "6c24c9f5-66c9-4eed-a61d-3f9b87c3f775"}
PEOPLE = {"data_source_id": "4a1af67f-9141-4ba5-aa9d-88b07dcd5f86"}
PID = "3e8d3699-c2db-81c7-aef6-d002d5cdcf26"           # in allowed_page_ids
PERSON_PID = "3ffd3699-c2db-8198-8ecd-ffa26b7f2dec"    # in the manifest as person:max-freeman
UNKNOWN = "11111111-2222-3333-4444-555555555555"

manifest = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
json.dump({"person:max-freeman": {"page_id": PERSON_PID, "url": "https://app.notion.com/p/x", "op": "skip", "at": "2026-10-24"}},
          manifest); manifest.close()


def ck(name, cond):
    global ok, n; n += 1; ok += bool(cond); print(("  ✓ " if cond else "  ✗ ") + name)


def errs(*ops, allowed=(PID,)):
    return np_.problems({"run": "test", "manifest": manifest.name, "allowed_page_ids": list(allowed), "operations": list(ops)})


def has(es, needle):
    return any(needle in e for e in es)


def upd(**kw):
    return dict({"key": "a", "op": "update", "page_id": PID}, **kw)


MARK = "⟦deep-read: pending⟧\n⟦/deep-read⟧"
DONE = "⟦deep-read: 2026-10-24⟧\nThe Frame...\n⟦/deep-read⟧"
LEGACY = "\\<!-- deep\\_read\\_rendered: pending -->"   # how Notion stores the old HTML comment (sandbox 2026-10-24)

# --- base contract
ck("a create into a data source without dedup is refused (invariant 8)",
   has(errs({"key": "a", "op": "create", "parent": DRAFTS, "properties": {"Content Type": "research_brief"}}), "dedup"))
ck("an update without page_id is refused", has(errs({"key": "a", "op": "update", "properties": {"X": "y"}}), "page_id"))
ck("a plain property update to an allowed page is valid", errs(upd(properties={"X": "y"})) == [])

# --- item 10: allowlists
ck("a create into an unknown data source is refused",
   has(errs({"key": "a", "op": "create", "parent": {"data_source_id": "deadbeef-0000-0000-0000-000000000000"},
             "dedup": {"query": "x", "match_title": "x"}}), "not one of the 8"))
ck("an update to a page in neither the manifest nor allowed_page_ids is refused",
   has(errs(upd(page_id=UNKNOWN, properties={"X": "y"})), "not in the manifest"))
ck("an update to a page known from the manifest is valid",
   errs(upd(key="person:max-freeman:2026-10-24", page_id=PERSON_PID, properties={"Current Title": "SVP"})) == [])
ck("page_id given as a URL is refused (gotcha o)",
   has(errs(upd(page_id="https://app.notion.com/p/3e8d3699c2db81c7aef6d002d5cdcf26", properties={"X": "y"})), "bare UUID"))

# --- item 9 negatives
ck("an update with no properties and no body edit is refused", has(errs(upd()), "nothing to do"))
ck("frozen_statuses as a string is refused", has(errs(upd(properties={"X": "y"}, frozen_statuses="scheduled")), "frozen_statuses"))
ck("a fenced body on a draft create lacking Content Type is refused",
   has(errs({"key": "d", "op": "create", "parent": DRAFTS, "dedup": {"query": "X", "match_title": "X"},
             "properties": {"Title": "X"}, "content": "```\nhi\n```"}), "Content Type"))

# --- item 1: append_content is gone; content_updates only
ck("append_content is refused (use content_updates on a marker)", has(errs(upd(append_content="## A\nB")), "append_content"))
ck("content_updates on a marker is valid", errs(upd(content_updates=[{"old_str": MARK, "new_str": DONE}])) == [])
ck("content_updates must be a non-empty list", has(errs(upd(content_updates=[])), "content_updates"))
ck("a no-op content_update (old == new) is refused",
   has(errs(upd(content_updates=[{"old_str": MARK, "new_str": MARK}])), "identical"))
ck("replace_content plus content_updates on the same op is refused",
   has(errs(upd(replace_content=True, content="x", content_updates=[{"old_str": MARK, "new_str": DONE}])), "replace_content"))
ck("content_updates on a create is refused",
   has(errs({"key": "a", "op": "create", "parent": None, "content_updates": [{"old_str": MARK, "new_str": DONE}]}), "update-only"))

# --- item 4: bounded anchors
ck("a short old_str with no marker is refused (unbounded anchor)",
   has(errs(upd(content_updates=[{"old_str": "## Deep Read", "new_str": "## Deep Read\nx"}])), "anchor"))
ck("a start marker without its end marker is refused (header-only match)",
   has(errs(upd(content_updates=[{"old_str": "⟦deep-read: 2026-10-01⟧",
                                   "new_str": "⟦deep-read: 2026-10-24⟧\nnew\n⟦/deep-read⟧"}])), "end marker"))
ck("a replacement that drops the end marker is refused (next re-render would be unbounded)",
   has(errs(upd(content_updates=[{"old_str": MARK, "new_str": "⟦deep-read: 2026-10-24⟧\nnew"}])), "end marker"))
ck("research-brief start without its end marker is refused",
   has(errs(upd(content_updates=[{"old_str": "⟦research-brief⟧\n## Research Brief\nold",
                                   "new_str": "⟦research-brief⟧\n## Research Brief\nnew\n⟦/research-brief⟧"}])), "end marker"))
ck("a terminal-marker insert (before ⟦/research-log⟧) is valid",
   errs(upd(content_updates=[{"old_str": "⟦/research-log⟧",
                              "new_str": "## Refresh 2026-10-24\nnew\n\n⟦/research-log⟧"}])) == [])

# --- sandbox 2026-10-24: Notion escapes HTML comments, so a raw <!-- --> anchor never matches
ck("a raw HTML-comment old_str is refused (Notion stores it escaped)",
   has(errs(upd(content_updates=[{"old_str": "<!-- /research_log -->", "new_str": "x\n<!-- /research_log -->"}])), "escaped"))
ck("a raw HTML comment in new_str is refused (would land as visible text)",
   has(errs(upd(content_updates=[{"old_str": MARK, "new_str": DONE + "\n<!-- note -->"}])), "escaped"))
ck("legacy page: the escaped stored marker bounded by the next ## heading (kept in new_str) is valid",
   errs(upd(content_updates=[{"old_str": LEGACY + "\n\n## Prior Snapshots",
                              "new_str": DONE + "\n\n## Prior Snapshots"}])) == [])
ck("legacy page: the escaped marker alone (no heading bound) is refused",
   has(errs(upd(content_updates=[{"old_str": LEGACY, "new_str": DONE}])), "end marker"))
ck("legacy replace must write the new ⟦⟧ form, not the escaped comment back",
   has(errs(upd(content_updates=[{"old_str": LEGACY + "\n\n## Prior Snapshots",
                                   "new_str": "\\<!-- deep\\_read\\_rendered: 2026-10-24 -->\nx\n\n## Prior Snapshots"}])), "⟦deep-read"))

# --- item 2: PII on People
ck("Email on a People create is refused (ADR-9 tier 1)",
   has(errs({"key": "person:a", "op": "create", "parent": PEOPLE, "dedup": {"query": "A", "match_title": "A"},
             "properties": {"Name": "A", "Email": "a@x.com"}}), "ADR-9"))
ck("...unless the op says alex_provided",
   errs({"key": "person:a", "op": "create", "parent": PEOPLE, "dedup": {"query": "A", "match_title": "A"},
         "properties": {"Name": "A", "Email": "a@x.com"}, "alex_provided": True}) == [])
ck("Phone on an update to a People page known from the manifest is refused",
   has(errs(upd(key="refresh:x", page_id=PERSON_PID, properties={"Phone": "555"})), "ADR-9"))
ck("Phone Number on an update keyed person: is refused",
   has(errs(upd(key="person:b:2026-10-24", properties={"Phone Number": "555"})), "ADR-9"))
ck("Email on a non-People page is not a PII refusal", not has(errs(upd(properties={"Email": "a@x.com"})), "ADR-9"))

ck("a raw HTML comment in a create body is refused (lands as visible text)",
   has(errs({"key": "a", "op": "create", "parent": None, "content": "## A\n<!-- x -->"}), "escaped"))

# --- gotcha m / p
ck("a literal backslash-n in an update body is refused (gotcha m)",
   has(errs(upd(content_updates=[{"old_str": MARK, "new_str": DONE + "\\nmore"}])), "gotcha m"))
ck("...but a create body may carry it (create-pages handles \\n)",
   errs({"key": "a", "op": "create", "parent": None, "content": "## A\\nB"}) == [])
post = {"key": "d", "op": "create", "parent": DRAFTS, "dedup": {"query": "X", "match_title": "X — Pre-Event Post"},
        "properties": {"Title": "X — Pre-Event Post", "Content Type": "linkedin_post_pre"}}
ck("a post draft in plain paragraphs is valid", errs(dict(post, content="Variant 1\n\nPara one.\n\nPara two.")) == [])
ck("a post draft wrapped in a code fence is refused (gotcha p)", has(errs(dict(post, content="```\nPara one.\n```")), "gotcha p"))
brief = dict(post, properties={"Title": "X — Research Brief", "Content Type": "research_brief"})
ck("a non-copy draft (research_brief) is not fence-checked", errs(dict(brief, content="```\nx\n```")) == [])

# --- CLI end to end
f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
json.dump({"run": "t", "manifest": manifest.name, "allowed_page_ids": [PID],
           "operations": [upd(content_updates=[{"old_str": MARK, "new_str": DONE}])]}, f); f.close()
sys.argv = ["notion_payload.py", f.name]
ck("CLI exits 0 on a valid payload", np_.main() == 0)

print(f"\n{ok}/{n} passed")
sys.exit(0 if ok == n else 1)
