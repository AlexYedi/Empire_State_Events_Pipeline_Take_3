#!/usr/bin/env python3
"""test_notion_payload.py — the notion-writer payload validator (YED-259 rollout). Offline, free.

Pins what the parent may hand the one Notion writer: creates with search-before-create, updates with a page id,
and the two body edits the research flow needs (append a section · replace one marked section), plus the two
formatting traps that land silently in Notion (literal \\n in update bodies, gotcha m; code fences in draft copy,
gotcha p).
"""
import importlib.util, json, sys, tempfile

spec = importlib.util.spec_from_file_location("np", ".claude/scripts/notion_payload.py")
np_ = importlib.util.module_from_spec(spec); spec.loader.exec_module(np_)
ok = n = 0
DRAFTS = {"data_source_id": "6c24c9f5-66c9-4eed-a61d-3f9b87c3f775"}
PID = "3e8d3699-c2db-81c7-aef6-d002d5cdcf26"


def ck(name, cond):
    global ok, n; n += 1; ok += bool(cond); print(("  ✓ " if cond else "  ✗ ") + name)


def pay(*ops):
    return {"run": "test", "manifest": "/tmp/m.json", "operations": list(ops)}


def errs(*ops):
    return np_.problems(pay(*ops))


def has(es, needle):
    return any(needle in e for e in es)


# --- existing contract still holds
ck("a create into a data source without dedup is refused (invariant 8)",
   has(errs({"key": "a", "op": "create", "parent": DRAFTS, "properties": {}}), "dedup"))
ck("an update without page_id is refused",
   has(errs({"key": "a", "op": "update", "properties": {}}), "page_id"))
ck("a plain property update is valid", errs({"key": "a", "op": "update", "page_id": PID, "properties": {"X": "y"}}) == [])

# --- append_content: add a section at the end of an existing page body
ck("update with append_content is valid",
   errs({"key": "a", "op": "update", "page_id": PID, "append_content": "## Refresh 2026-10-24\nnew research"}) == [])
ck("append_content must be a non-empty string",
   has(errs({"key": "a", "op": "update", "page_id": PID, "append_content": ""}), "append_content"))
ck("append_content on a create is refused (put it in content)",
   has(errs({"key": "a", "op": "create", "parent": None, "append_content": "x"}), "append_content"))

# --- content_updates: replace one marked section (Deep Read, Research Brief re-run)
good_cu = [{"old_str": "## Deep Read\n<!-- deep_read_rendered: pending -->",
            "new_str": "## Deep Read\n<!-- deep_read_rendered: 2026-10-24 -->\n\nThe Frame..."}]
ck("update with content_updates is valid", errs({"key": "a", "op": "update", "page_id": PID, "content_updates": good_cu}) == [])
ck("content_updates needs a non-empty old_str",
   has(errs({"key": "a", "op": "update", "page_id": PID, "content_updates": [{"old_str": "", "new_str": "x"}]}), "old_str"))
ck("content_updates must be a non-empty list",
   has(errs({"key": "a", "op": "update", "page_id": PID, "content_updates": []}), "content_updates"))
ck("a no-op content_update (old == new) is refused",
   has(errs({"key": "a", "op": "update", "page_id": PID, "content_updates": [{"old_str": "x", "new_str": "x"}]}), "identical"))
ck("replace_content plus a section edit on the same op is refused (ambiguous)",
   has(errs({"key": "a", "op": "update", "page_id": PID, "replace_content": True, "content": "x",
             "append_content": "y"}), "replace_content"))

# --- gotcha m: notion-update-page turns literal \n into a stray "n"
ck("a literal backslash-n in an update body is refused (gotcha m)",
   has(errs({"key": "a", "op": "update", "page_id": PID, "append_content": "## A\\nB"}), "gotcha m"))
ck("...but a create body may carry it (create-pages handles \\n)",
   errs({"key": "a", "op": "create", "parent": None, "content": "## A\\nB"}) == [])

# --- gotcha p: draft copy is plain paragraphs, never code blocks
post = {"key": "d", "op": "create", "parent": DRAFTS, "dedup": {"query": "X", "match_title": "X — Pre-Event Post"},
        "properties": {"Title": "X — Pre-Event Post", "Content Type": "linkedin_post_pre"}}
ck("a post draft in plain paragraphs is valid", errs(dict(post, content="Variant 1\n\nPara one.\n\nPara two.")) == [])
ck("a post draft wrapped in a code fence is refused (gotcha p)",
   has(errs(dict(post, content="Variant 1\n\n```\nPara one.\n```")), "gotcha p"))
note = dict(post, properties={"Title": "Connection Note — A", "Content Type": "linkedin_dm_speaker"})
ck("a connection note in a code fence is refused too", has(errs(dict(note, content="```\nhi\n```")), "gotcha p"))
brief = dict(post, properties={"Title": "X — Research Brief", "Content Type": "research_brief"})
ck("a non-copy draft (research_brief) is not fence-checked", errs(dict(brief, content="```\nx\n```")) == [])

# --- CLI end to end
f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
json.dump(pay({"key": "a", "op": "update", "page_id": PID, "content_updates": good_cu}), f); f.close()
sys.argv = ["notion_payload.py", f.name]
ck("CLI exits 0 on a valid payload", np_.main() == 0)

print(f"\n{ok}/{n} passed")
sys.exit(0 if ok == n else 1)
