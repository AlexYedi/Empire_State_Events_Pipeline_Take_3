#!/usr/bin/env python3
r"""Deterministic read-back of a notion-writer run (YED-286, YED-380).

The notion-writer is a model: it retypes every payload string into a tool call, and its own read-back is the same
model checking its own work. Two failures got past it: properties silently dropped when one update call carried
both properties and a body edit (YED-286), and payload text retyped with drift ("Kyndril" for "Kyndryl", YED-380).
This script closes that gap with code. After the writer returns, the PARENT runs it on the same payload; it fetches
every page the manifest says was created or updated over the Notion REST API (no model in the loop) and compares:

  * properties: every property the payload set must read back with the same value;
  * body: a create's `content` (or an update's replace_content `content`) must match the page word for word;
    each `content_updates[].new_str` must appear on the page as a contiguous word run.

Comparison is on word tokens, so Notion's stored-form changes (`<br />`, backslash escapes, markdown marks, link
syntax, tag wrappers, whitespace) are not drift. Mentions are skipped on both sides (a mention renders as the target
page's title). Any other difference is a FAIL: the write is not done until this prints PASS.

  python3 .claude/scripts/notion_readback.py <payload.json> [--manifest PATH] [--json] [--props-only]
  python3 .claude/scripts/notion_readback.py --selftest

Exit 0 = PASS, 1 = at least one FAIL, 2 = could not run (no token, unreadable payload). Read-only against Notion.
Token: NOTION_TOKEN from the environment, else NOTION_PAT_TOKEN / NOTION_API from the repo .env (never printed).
Contact properties (email, phone) are never read or compared (ADR-9); diff snippets pass through pii_normalize.
"""
from __future__ import annotations
import argparse, difflib, json, os, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import notion_export as nx      # noqa: E402  REST transport, pagination, PII-safe property access
import pii_normalize            # noqa: E402

WRITE_OPS = {"create", "update"}
SKIP_PROP_TYPES = {"email", "phone_number", "files", "people", "formula", "rollup", "created_time",
                   "last_edited_time", "created_by", "last_edited_by", "unique_id", "button", "verification"}
CTX = 6   # words of context either side of a diff


# ---------------------------------------------------------------------------------------------
# tokenizing: both sides reduced to the words a reader sees
# ---------------------------------------------------------------------------------------------
MD_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
MENTION_TAG = re.compile(r"<mention-[^>]*>.*?</mention-[^>]*>|<mention-[^>]*/>", re.S)
TAG = re.compile(r"</?[a-zA-Z][^>]*>")
URL = re.compile(r"https?://\S+")
LIST_NUM = re.compile(r"(?m)^[ \t]*\d+\\?[.)][ \t]+")    # Notion numbers list items itself; the digits are not text
WORD = re.compile(r"[^\W_]+(?:['’][^\W_]+)*")


def tokens(text: str) -> list[str]:
    s = text or ""
    s = LIST_NUM.sub(" ", s)
    s = MENTION_TAG.sub(" ", s)
    s = MD_LINK.sub(r" \1 ", s)
    s = TAG.sub(" ", s)
    s = URL.sub(" ", s)
    s = s.replace("\\", " ")
    return WORD.findall(s)


def page_text(blocks: list) -> str:
    """Plain text of a block tree, mentions dropped (they render as the target's title, not payload text)."""
    out = []

    def rich(r):
        return "".join(t.get("plain_text", "") for t in r or [] if t.get("type") != "mention")

    def walk(bs):
        for b in bs:
            t = b.get("type")
            body = b.get(t, {}) or {}
            if t == "table_row":
                out.extend(rich(c) for c in body.get("cells", []))
            elif t in ("child_page", "child_database"):
                pass
            else:
                out.append(rich(body.get("rich_text")))
                if body.get("caption"):
                    out.append(rich(body["caption"]))
            walk(b.get("_children") or [])
    walk(blocks)
    return "\n".join(out)


def snippet(words: list[str], i: int, j: int) -> str:
    lo, hi = max(0, i - CTX), min(len(words), j + CTX)
    s = ("… " if lo else "") + " ".join(words[lo:i]) + " [" + " ".join(words[i:j]) + "] " + " ".join(words[j:hi])
    s = s + (" …" if hi < len(words) else "")
    red, _ = pii_normalize.redact(s)
    return red.strip()


def diff_full(want: list[str], got: list[str]) -> list[str]:
    """Word-level differences between the payload body and the whole page body."""
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, want, got, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        out.append(f"{tag}: payload {snippet(want, i1, i2)!r} -> page {snippet(got, j1, j2)!r}")
    return out


def find_run(needle: list[str], hay: list[str]) -> bool:
    n = len(needle)
    if n == 0:
        return True
    first = needle[0]
    for k in range(len(hay) - n + 1):
        if hay[k] == first and hay[k:k + n] == needle:
            return True
    return False


def diff_fragment(want: list[str], got: list[str]) -> list[str]:
    """`want` (a new_str) must appear in `got` as one contiguous run; else show where it diverges."""
    if find_run(want, got):
        return []
    sm = difflib.SequenceMatcher(None, got, want, autojunk=False)
    blocks = [b for b in sm.get_matching_blocks() if b.size]
    if not blocks:
        return [f"new_str not on page: {snippet(want, 0, min(len(want), 2 * CTX))!r}"]
    # anchor on the longest match, then diff the page window that aligns with the whole fragment
    best = max(blocks, key=lambda b: b.size)
    start = max(0, best.a - best.b)
    window = got[start:start + len(want) + 2 * CTX]
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, want, window, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        if tag == "insert" and i1 == len(want):
            continue                                 # page text after the fragment ends: not drift
        out.append(f"{tag}: payload {snippet(want, i1, i2)!r} -> page {snippet(window, j1, j2)!r}")
    return out or [f"new_str words found but not contiguous: {snippet(want, 0, min(len(want), 2 * CTX))!r}"]


# ---------------------------------------------------------------------------------------------
# properties: payload (MCP flat format) vs REST page properties
# ---------------------------------------------------------------------------------------------
def ids_in(v) -> set[str]:
    if isinstance(v, str):
        try:
            v = json.loads(v)
        except ValueError:
            v = [v]
    found = set()
    for x in v if isinstance(v, list) else [v]:
        m = re.findall(r"[0-9a-f]{32}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", str(x).lower())
        if m:
            found.add(m[-1].replace("-", ""))
    return found


def as_list(v) -> list[str]:
    if isinstance(v, list):
        return [str(x) for x in v]
    if isinstance(v, str):
        try:
            j = json.loads(v)
            if isinstance(j, list):
                return [str(x) for x in j]
        except ValueError:
            pass
        return [x.strip() for x in v.split(",") if x.strip()]
    return [str(v)]


def prop_problems(want: dict, page: dict) -> tuple[list[str], list[str]]:
    """(failures, notes). Every payload property is compared unless its type cannot be read back."""
    props = nx.public_props(page)
    all_props = page.get("properties") or {}
    fails, notes = [], []
    title_name = next((k for k, v in all_props.items() if v.get("type") == "title"), None)
    for raw, val in (want or {}).items():
        name, part = raw, None
        m = re.match(r"^date:(.+):(start|end|is_datetime)$", raw)
        if m:
            name, part = m.group(1), m.group(2)
        elif raw.startswith("userDefined:"):
            name = raw[len("userDefined:"):]
        elif raw == "title" and title_name:
            name = title_name
        if name not in all_props:
            fails.append(f"property {raw!r}: not on the page")
            continue
        if name not in props:
            notes.append(f"property {raw!r}: contact field, not read (ADR-9)")
            continue
        p = props[name]
        t = p.get("type")
        if t in SKIP_PROP_TYPES:
            notes.append(f"property {raw!r}: type {t} not compared")
            continue
        got: object
        if t in ("title", "rich_text"):
            got_t, want_t = tokens(nx.plain(p.get(t))), tokens(str(val) if val is not None else "")
            if got_t != want_t:
                fails.append(f"property {raw!r}: " + "; ".join(diff_full(want_t, got_t)[:3]))
            continue
        if t == "date":
            d = p.get("date") or {}
            if part == "is_datetime":
                continue
            got, exp = (d.get(part) or "")[:10], (str(val) if val is not None else "")[:10]
        elif t in ("select", "status"):
            got, exp = ((p.get(t) or {}).get("name") or ""), ("" if val is None else str(val))
        elif t == "multi_select":
            got, exp = sorted(o.get("name", "") for o in p.get("multi_select") or []), sorted(as_list(val or []))
        elif t == "url":
            got, exp = (p.get("url") or "").rstrip("/"), ("" if val is None else str(val)).rstrip("/")
        elif t == "number":
            got, exp = p.get("number"), (None if val is None else float(val))
            got = None if got is None else float(got)
        elif t == "checkbox":
            got, exp = bool(p.get("checkbox")), str(val).strip().upper() in ("__YES__", "TRUE", "YES", "1")
        elif t == "relation":
            got = {r.get("id", "").replace("-", "") for r in p.get("relation") or []}
            exp = ids_in(val or [])
            if p.get("has_more"):
                notes.append(f"property {raw!r}: relation has more than 25 links, checked the first page only")
                if exp - got:
                    notes.append(f"property {raw!r}: {len(exp - got)} expected link(s) not in the first page")
                continue
        else:
            notes.append(f"property {raw!r}: type {t} not compared")
            continue
        if got != exp:
            fails.append(f"property {raw!r}: payload {exp!r} -> page {got!r}")
    return fails, notes


# ---------------------------------------------------------------------------------------------
# one operation
# ---------------------------------------------------------------------------------------------
def check_op(op: dict, page: dict, blocks: list | None) -> dict:
    fails, notes = prop_problems(op.get("properties") or {}, page)
    body = None
    if blocks is not None:
        got = tokens(page_text(blocks))
        if op.get("content") is not None and (op["op"] == "create" or op.get("replace_content")):
            body = "content"
            fails += [f"body {d}" for d in diff_full(tokens(op["content"]), got)[:8]]
        for n, cu in enumerate(op.get("content_updates") or []):
            body = "content_updates"
            fails += [f"content_updates[{n}] {d}" for d in diff_fragment(tokens(cu.get("new_str", "")), got)[:5]]
    return {"key": op.get("key"), "op": op.get("op"), "result": "FAIL" if fails else "PASS",
            "checked": {"properties": len(op.get("properties") or {}), "body": body}, "fails": fails, "notes": notes}


def wants_body(op: dict) -> bool:
    return bool(op.get("content_updates")) or (op.get("content") is not None and
                                              (op["op"] == "create" or bool(op.get("replace_content"))))


def resolve_manifest(payload_path: Path, payload: dict, override: str | None) -> Path:
    m = Path(override or payload.get("manifest") or "")
    if m.is_absolute():
        return m
    for base in (Path.cwd(), ROOT, payload_path.parent):
        if (base / m).exists():
            return base / m
    return ROOT / m


def run(payload: dict, manifest: dict, fetch_page, fetch_blocks, props_only: bool = False) -> list[dict]:
    rows = []
    for op in payload.get("operations") or []:
        if op.get("op") not in WRITE_OPS:
            continue
        entry = manifest.get(op.get("key"))
        if not isinstance(entry, dict) or not entry.get("page_id"):
            rows.append({"key": op.get("key"), "op": op.get("op"), "result": "FAIL", "checked": {},
                         "fails": ["not in the manifest: the writer did not record this write"], "notes": []})
            continue
        if entry.get("op") == "skip" or str(entry.get("result", "")).startswith("skipped"):
            rows.append({"key": op.get("key"), "op": op.get("op"), "result": "SKIP", "checked": {},
                         "fails": [], "notes": [f"manifest says {entry.get('result') or entry.get('op')}"]})
            continue
        pid = entry["page_id"]
        try:
            page = fetch_page(pid)
            blocks = fetch_blocks(pid) if wants_body(op) and not props_only else None
        except nx.NotionError as e:
            rows.append({"key": op.get("key"), "op": op.get("op"), "result": "FAIL", "checked": {},
                         "fails": [f"fetch failed: {e}"], "notes": []})
            continue
        row = check_op(op, page, blocks)
        row["url"] = entry.get("url")
        edited, at = str(page.get("last_edited_time") or "")[:16], str(entry.get("at") or "")[:16]
        if row["fails"] and len(at) == 16 and edited > at:   # manifests that record only a date cannot be compared
            row["notes"].append(f"page edited at {edited} after this write ({at}): a later run may explain the diff; "
                                "run the read-back right after the writer returns")
        rows.append(row)
    return rows


def load_token() -> str | None:
    if os.environ.get("NOTION_TOKEN"):
        return os.environ["NOTION_TOKEN"]
    env = ROOT / ".env"
    vals = {}
    try:
        for line in env.read_text().splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                vals[k.strip().removeprefix("export ").strip()] = v.strip().strip("'\"")
    except OSError:
        return None
    return vals.get("NOTION_PAT_TOKEN") or vals.get("NOTION_API")


def report(rows: list[dict]) -> str:
    lines = []
    for r in rows:
        lines.append(f"{r['result']:4}  {r['op']:6}  {r['key']}")
        lines += [f"        x {f}" for f in r["fails"]]
        lines += [f"        · {n}" for n in r["notes"]]
    n_fail = sum(r["result"] == "FAIL" for r in rows)
    n_pass = sum(r["result"] == "PASS" for r in rows)
    n_skip = sum(r["result"] == "SKIP" for r in rows)
    lines.append(("FAIL" if n_fail else "PASS") + f": {n_pass} pass · {n_fail} fail · {n_skip} skipped (manifest)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------------------------
# selftest (offline)
# ---------------------------------------------------------------------------------------------
def _rt(s, mention=False):
    return [{"type": "mention" if mention else "text", "plain_text": s}]


def _para(s, **kw):
    return {"type": "paragraph", "paragraph": {"rich_text": _rt(s)}, **kw}


def selftest() -> int:
    checks = []

    def ok(name, cond):
        checks.append((name, bool(cond)))

    page = {"properties": {
        "Name": {"type": "title", "title": _rt("Kyndryl — Prepared Questions")},
        "Content Status": {"type": "select", "select": {"name": "needs_review"}},
        "Tags": {"type": "multi_select", "multi_select": [{"name": "a"}, {"name": "b"}]},
        "Event Date": {"type": "date", "date": {"start": "2026-11-30"}},
        "Website": {"type": "url", "url": "https://kyndryl.com/"},
        "Score": {"type": "number", "number": 3},
        "Done": {"type": "checkbox", "checkbox": True},
        "Email": {"type": "email", "email": "x@y.test"},
        "Event": {"type": "relation", "relation": [{"id": "366d3699-c2db-8182-ac36-e12596874bd8"}], "has_more": False},
        "Notes": {"type": "rich_text", "rich_text": _rt("Ask about the **hybrid** cloud play.")},
    }}
    good_props = {"Name": "Kyndryl — Prepared Questions", "Content Status": "needs_review", "Tags": '["b","a"]',
                  "date:Event Date:start": "2026-11-30", "date:Event Date:is_datetime": 0,
                  "Website": "https://kyndryl.com", "Score": 3, "Done": "__YES__",
                  "Event": '["https://app.notion.com/p/366d3699c2db8182ac36e12596874bd8"]',
                  "Notes": "Ask about the hybrid cloud play."}
    f, n = prop_problems(good_props, page)
    ok("properties: every type reads back equal (formatting, order, trailing slash, url-vs-id ignored)", f == [])
    f, _ = prop_problems({"Name": "Kyndril — Prepared Questions"}, page)
    ok("properties: retyped title 'Kyndril' is a FAIL (YED-380)", f and "Kyndril" in f[0])
    f, _ = prop_problems({"Content Status": "ready"}, page)
    ok("properties: a dropped select update is a FAIL (YED-286)", f and "needs_review" in f[0])
    f, _ = prop_problems({"date:Event Date:start": "2026-12-01"}, page)
    ok("properties: stale date is a FAIL (YED-286 Last Researched)", bool(f))
    f, _ = prop_problems({"Missing": "x"}, page)
    ok("properties: a property the page lacks is a FAIL", f and "not on the page" in f[0])
    f, n = prop_problems({"Email": "x@y.test"}, page)
    ok("properties: contact fields are never read (ADR-9 note, not a compare)", f == [] and "ADR-9" in n[0])
    f, _ = prop_problems({"Event": '["https://app.notion.com/p/0000000000000000000000000000beef"]'}, page)
    ok("properties: a wrong relation is a FAIL", bool(f))

    blocks = [
        {"type": "heading_2", "heading_2": {"rich_text": _rt("Questions for Kyndryl")}},
        _para("First line"), _para("second line after a <br />"),
        {"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": _rt("See ") + _rt("Some Page", True)},
         "_children": [_para("nested child")]},
        {"type": "table", "table": {}, "_children": [
            {"type": "table_row", "table_row": {"cells": [_rt("cell one"), _rt("cell two")]}}]},
        _para("⟦deep-read: 2026-11-25⟧ The Frame text here. ⟦/deep-read⟧"),
    ]
    content = ("## Questions for **Kyndryl**\n\nFirst line<br />second line after a \\<br />\n"
               "- See <mention-page url=\"https://app.notion.com/p/abc\">Some Page</mention-page>\n\t- nested child\n"
               "<table><tr><td>cell one</td><td>cell two</td></tr></table>\n"
               "⟦deep-read: 2026-11-25⟧ The [Frame](https://x.test) text here. ⟦/deep-read⟧")
    r = check_op({"key": "k", "op": "create", "content": content}, {"properties": {}}, blocks)
    ok("body: Notion stored-form changes (<br />, escapes, marks, links, tags, mentions, tables, nesting) pass",
       r["result"] == "PASS")
    r = check_op({"key": "k", "op": "create", "content": content.replace("Kyndryl", "Kyndril")}, {"properties": {}},
                 blocks)
    ok("body: one retyped word in the body is a FAIL with the word in the report",
       r["result"] == "FAIL" and "Kyndril" in r["fails"][0])
    r = check_op({"key": "k", "op": "create", "content": content + "\n\nA dropped final paragraph."},
                 {"properties": {}}, blocks)
    ok("body: a dropped paragraph is a FAIL", r["result"] == "FAIL")
    cu = {"key": "k", "op": "update",
          "content_updates": [{"old_str": "⟦deep-read: pending⟧", "new_str": "⟦deep-read: 2026-11-25⟧ The Frame text"}]}
    ok("content_updates: a new_str present as a contiguous run passes", check_op(cu, {"properties": {}}, blocks)
       ["result"] == "PASS")
    cu["content_updates"][0]["new_str"] = "⟦deep-read: 2026-11-25⟧ The Frame texts"
    r = check_op(cu, {"properties": {}}, blocks)
    ok("content_updates: a retyped word inside new_str is a FAIL", r["result"] == "FAIL" and "texts" in r["fails"][0])
    cu["content_updates"][0]["new_str"] = "Nothing like this is anywhere"
    ok("content_updates: a new_str that never landed is a FAIL",
       check_op(cu, {"properties": {}}, blocks)["result"] == "FAIL")
    both = {"key": "k", "op": "update", "properties": {"Content Status": "ready"},
            "content_updates": [{"old_str": "x" * 20, "new_str": "First line second line"}]}
    r = check_op(both, page, blocks)
    ok("YED-286 shape: body landed but property dropped is still a FAIL",
       r["result"] == "FAIL" and any("Content Status" in x for x in r["fails"]))

    pl = {"operations": [{"key": "a", "op": "create", "properties": {"Name": "Kyndryl — Prepared Questions"}},
                         {"key": "b", "op": "update", "properties": {}},
                         {"key": "c", "op": "create", "properties": {}}]}
    man = {"a": {"page_id": "p1", "url": "u"}, "b": {"page_id": "p2", "op": "skip"}}
    rows = run(pl, man, lambda pid: page, lambda pid: blocks)
    ok("run: manifest write -> PASS, seeded skip -> SKIP, missing from manifest -> FAIL",
       [x["result"] for x in rows] == ["PASS", "SKIP", "FAIL"])
    ok("report: any FAIL makes the summary FAIL", report(rows).splitlines()[-1].startswith("FAIL"))
    ok("tokens: numbered-list digits are dropped (Notion numbers items itself)",
       tokens("1. HIT if\n  2) Missed\n3\\. Esc") == ["HIT", "if", "Missed", "Esc"] and tokens("in 2026 we") == ["in", "2026", "we"])
    stale = run({"operations": [{"key": "a", "op": "create", "properties": {"Name": "Other"}}]},
                {"a": {"page_id": "p1", "at": "2026-11-25T10:00:00Z"}},
                lambda pid: dict(page, last_edited_time="2026-11-25T12:00:00.000Z"), lambda pid: blocks)
    ok("run: a FAIL on a page edited after the write carries the later-edit note",
       stale[0]["result"] == "FAIL" and any("after this write" in n for n in stale[0]["notes"]))
    ok("tokens: underscores and markdown marks are not words", tokens("**a_b** `c`") == ["a", "b", "c"])
    ok("snippet: contacts in a diff snippet are redacted", "x@y.test" not in snippet(["mail", "x@y.test"], 0, 2)
       or not pii_normalize.has_pii("x@y.test"))

    fails = [c for c in checks if not c[1]]
    for name, good in checks:
        print(("ok   " if good else "FAIL ") + name)
    print(f"selftest: {len(checks) - len(fails)}/{len(checks)} notion-readback cases pass")
    return 0 if not fails else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("payload", nargs="?")
    ap.add_argument("--manifest", help="override payload.manifest")
    ap.add_argument("--json", action="store_true", help="print the rows as JSON")
    ap.add_argument("--props-only", action="store_true",
                    help="compare properties only (sweeping old runs whose bodies later writes have changed)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.payload:
        ap.error("payload required (or --selftest)")
    pp = Path(a.payload)
    try:
        payload = json.loads(pp.read_text())
    except (OSError, ValueError) as e:
        print(f"notion_readback: cannot read payload: {e}", file=sys.stderr)
        return 2
    mpath = resolve_manifest(pp, payload, a.manifest)
    try:
        manifest = json.loads(mpath.read_text())
    except (OSError, ValueError):
        print(f"notion_readback: cannot read manifest {mpath}", file=sys.stderr)
        return 2
    token = load_token()
    if not token:
        print("notion_readback: no Notion token (NOTION_TOKEN, or NOTION_PAT_TOKEN / NOTION_API in .env)",
              file=sys.stderr)
        return 2
    nc = nx.Notion(token)

    def blocks_of(bid):
        out = []
        for b in nx.paged(nc, "GET", f"/blocks/{bid}/children"):
            if b.get("has_children") and b.get("type") not in nx.NO_CHILD_FETCH:
                b["_children"] = blocks_of(b["id"])
            out.append(b)
        return out

    rows = run(payload, manifest, lambda pid: nc.call("GET", f"/pages/{pid}"), blocks_of, a.props_only)
    print(json.dumps(rows, indent=1, ensure_ascii=False) if a.json else report(rows))
    return 1 if any(r["result"] == "FAIL" for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
