#!/usr/bin/env python3
"""route_brief.py: /post-event-content Step 3.8e, the post-event router (YED-387).

Parses the synthesizer's ⟦routing⟧ block (contract: .claude/references/post-event-routing.md), validates it,
strips it from the brief before the Notion write, and turns it into a write plan. It writes nothing external:
the parent creates the Linear issues (search before create) and dispatches notion-writer with the payload
this script emits (CLAUDE.md invariants 5 and 8). The only files it writes are local and gitignored: the
plan, the Notion payload and the private stories file.

  extract <brief.md> [--json]      validate; exit 0 valid, 2 invalid, 3 no block
  strip   <brief.md>               print the brief without the block (what goes to Notion)
  plan    <brief.md> --event NAME --event-date YYYY-MM-DD [--notion-event-url URL] [--state-dir DIR]
                                   write routing-plan.json, routing-notion-payload.json (if build ideas),
                                   stories.md (if stories); print a summary
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_state  # noqa: E402

START, END = "⟦routing⟧", "⟦/routing⟧"
TYPES = ("decision", "followup", "upskill", "open-loop", "content-backlog", "build-idea", "story")
COMPLEXITY = ("prototype", "small_tool", "MVP", "full_project")
MAX_ITEMS = 12
PROJECT_IDEAS_DS = "0956e6ed-8555-4d8f-8856-388966dedaab"
LINEAR_TEAM = "EMPIRE-STATE"
BASE_LABELS = ["Track: Empire"]
TYPE_LABELS = {  # one label per thread group (P/S/B/R are one group in Linear: pick exactly one)
    "decision": ["P · Pipeline", "decision"],
    "followup": ["P · Pipeline"],
    "upskill": ["B · Builds"],
    "open-loop": ["P · Pipeline"],
    "content-backlog": ["R · Rooms & Voice"],
}
LIMITS = {"title": 100, "evidence": 240, "why": 240, "body": 800}
# ADR-9: contact details never ride along. Email, phone-like digit runs, @handles.
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?:\+?\d[\s().-]?){9,}\d")
SOURCE = re.compile(r"^§\d{1,2}([.\w :/&,-]*)$")


class RoutingError(Exception):
    pass


def split(text: str) -> tuple[str, str | None]:
    """(brief without block, block body or None). Exactly one block, at most."""
    n = text.count(START)
    if n == 0:
        return text, None
    if n > 1 or text.count(END) != 1:
        raise RoutingError(f"expected exactly one {START} … {END} pair, found {n} start / {text.count(END)} end")
    a, b = text.index(START), text.index(END)
    if b < a:
        raise RoutingError(f"{END} comes before {START}")
    return (text[:a].rstrip() + "\n" + text[b + len(END):].lstrip("\n")).rstrip() + "\n", text[a + len(START):b]


def _str(item: dict, key: str, errs: list[str], where: str, required: bool = True) -> None:
    v = item.get(key)
    if v is None:
        if required:
            errs.append(f"{where}: missing {key}")
        return
    if not isinstance(v, str) or not v.strip():
        errs.append(f"{where}: {key} must be a non-empty string")
        return
    if key in LIMITS and len(v) > LIMITS[key]:
        errs.append(f"{where}: {key} is {len(v)} chars (max {LIMITS[key]})")
    if EMAIL.search(v) or PHONE.search(v):
        errs.append(f"{where}: {key} contains contact details (ADR-9)")


def validate(block: str) -> tuple[dict, list[dict], list[str]]:
    lines = [ln.strip() for ln in block.strip().splitlines() if ln.strip()]
    errs: list[str] = []
    if not lines:
        return {}, [], ["empty routing block"]
    rows = []
    for i, ln in enumerate(lines, 1):
        try:
            obj = json.loads(ln)
        except ValueError as e:
            errs.append(f"line {i}: not JSON ({e.msg})")
            continue
        if not isinstance(obj, dict):
            errs.append(f"line {i}: not an object")
            continue
        rows.append((i, obj))
    if not rows:
        return {}, [], errs
    (hi, header), body = rows[0], rows[1:]
    if header.get("routing_version") != 1:
        errs.append(f"line {hi}: header needs routing_version 1")
    if not isinstance(header.get("recap"), bool):
        errs.append(f"line {hi}: header needs recap true/false")
    if len(body) > MAX_ITEMS:
        errs.append(f"{len(body)} items (max {MAX_ITEMS}): merge or drop the weakest")
    items = []
    allowed = {"type", "title", "source", "evidence", "why", "owner", "due_days", "person", "complexity", "body"}
    for i, it in body:
        w = f"line {i}"
        t = it.get("type")
        if t not in TYPES:
            errs.append(f"{w}: type {t!r} not one of {', '.join(TYPES)}")
            continue
        extra = set(it) - allowed
        if extra:
            errs.append(f"{w}: unknown field(s) {', '.join(sorted(extra))}")
        for k in ("title", "source", "evidence", "why"):
            _str(it, k, errs, w)
        _str(it, "body", errs, w, required=False)
        if isinstance(it.get("source"), str) and not SOURCE.match(it["source"].strip()):
            errs.append(f"{w}: source must cite a brief section as §N (got {it['source']!r})")
        if it.get("owner") not in ("Alex", "session"):
            errs.append(f"{w}: owner must be Alex or session")
        d = it.get("due_days")
        if d is not None and (not isinstance(d, int) or isinstance(d, bool) or not 1 <= d <= 60):
            errs.append(f"{w}: due_days must be an integer 1-60")
        if t in ("followup", "decision") and d is None:
            errs.append(f"{w}: {t} needs due_days")
        if t == "followup":
            _str(it, "person", errs, w)
            if header.get("recap") is not True:
                errs.append(f"{w}: followup without Alex's recap (header recap false): not allowed")
        elif "person" in it:
            errs.append(f"{w}: person is only for followup")
        if t == "build-idea":
            if it.get("complexity") not in COMPLEXITY:
                errs.append(f"{w}: build-idea needs complexity in {', '.join(COMPLEXITY)}")
        elif "complexity" in it:
            errs.append(f"{w}: complexity is only for build-idea")
        items.append(it)
    titles = [i.get("title", "").strip().lower() for i in items]
    dups = sorted({t for t in titles if t and titles.count(t) > 1})
    if dups:
        errs.append("duplicate titles: " + "; ".join(dups))
    return header, items, errs


def extract(text: str) -> tuple[dict, list[dict]]:
    _, block = split(text)
    if block is None:
        raise LookupError("no routing block")
    header, items, errs = validate(block)
    if errs:
        raise RoutingError("\n".join(errs))
    return header, items


def _due(event_date: str, days: int | None) -> str | None:
    if days is None:
        return None
    return (dt.date.fromisoformat(event_date) + dt.timedelta(days=days)).isoformat()


def _description(it: dict, event: str, event_date: str) -> str:
    parts = [f"**Why:** {it['why']}", f"**From:** {event} ({event_date}), brief {it['source']}: {it['evidence']}"]
    if it.get("body"):
        parts.append(it["body"])
    parts.append(f"Owner: {it['owner']}. Routed by `/post-event-content` Step 3.8e (YED-387).")
    return "\n\n".join(parts)


def plan(header: dict, items: list[dict], event: str, event_date: str, notion_event_url: str | None = None) -> dict:
    dt.date.fromisoformat(event_date)  # raises on a bad date
    slug = run_state.slugify(event)
    linear, backlog, ideas, stories = [], [], [], []
    for it in items:
        t = it["type"]
        if t == "content-backlog":
            backlog.append(it)
        elif t == "build-idea":
            ideas.append(it)
        elif t == "story":
            stories.append(it)
        else:
            title = it["title"]
            if t == "followup":  # name the person once: prefix only when the title doesn't already
                title = f"Follow-up: {title}" if it["person"] in title else f"Follow-up: {it['person']}: {title}"
            linear.append({"type": t, "team": LINEAR_TEAM, "title": title,
                           "labels": BASE_LABELS + TYPE_LABELS[t], "assignee": "me" if it["owner"] == "Alex" else None,
                           "dueDate": _due(event_date, it.get("due_days")),
                           "description": _description(it, event, event_date)})
    if backlog:
        lines = [f"- **{b['title']}** ({b['source']}). {b['why']}" for b in backlog]
        due = min((b.get("due_days") for b in backlog if b.get("due_days")), default=14)
        linear.append({"type": "content-backlog", "team": LINEAR_TEAM,
                       "title": f"{event}: which unused angles are worth a second post?",
                       "labels": BASE_LABELS + TYPE_LABELS["content-backlog"], "assignee": "me",
                       "dueDate": _due(event_date, due),
                       "description": "Unused angles from the post-event brief:\n\n" + "\n".join(lines)
                       + "\n\nRouted by `/post-event-content` Step 3.8e (YED-387)."})
    payload = None
    if ideas:
        ops = []
        for it in ideas:
            props = {"Project Name": it["title"], "Status": "needs_review", "Proposal Type": "feasible",
                     "Complexity Band": it["complexity"],
                     "Architecture Summary": (it["why"] + (" " + it["body"] if it.get("body") else ""))[:1900]}
            if notion_event_url:
                props["Event"] = json.dumps([notion_event_url])
            ops.append({"key": f"project-idea:{run_state.slugify(it['title'])}", "op": "create",
                        "parent": {"data_source_id": PROJECT_IDEAS_DS},
                        "dedup": {"query": it["title"], "match_title": it["title"]},
                        "properties": props,
                        "content": f"From {event} ({event_date}), brief {it['source']}: {it['evidence']}"})
        payload = {"run": f"{slug}-routing", "manifest": f".claude/.state/notion-manifests/{slug}-routing.json",
                   "operations": ops}
    return {"event": event, "slug": slug, "event_date": event_date, "recap": header.get("recap"),
            "counts": {"items": len(items), "linear": len(linear), "build_ideas": len(ideas), "stories": len(stories)},
            "linear": linear, "notion_payload": payload, "stories": stories}


def stories_md(p: dict) -> str:
    out = [f"# Interview stories: {p['event']} ({p['event_date']})", "",
           "Private (gitignored). Move the keepers into me-model.md by hand.", ""]
    for s in p["stories"]:
        out += [f"## {s['title']}", "", f"- From: brief {s['source']}: {s['evidence']}", f"- Why it lands: {s['why']}"]
        if s.get("body"):
            out.append(f"- {s['body']}")
        out.append("")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract"); e.add_argument("brief"); e.add_argument("--json", action="store_true")
    s = sub.add_parser("strip"); s.add_argument("brief")
    p = sub.add_parser("plan"); p.add_argument("brief"); p.add_argument("--event", required=True)
    p.add_argument("--event-date", required=True); p.add_argument("--notion-event-url")
    p.add_argument("--state-dir", default=None)
    a = ap.parse_args(argv)
    text = open(a.brief, encoding="utf-8").read()
    try:
        if a.cmd == "strip":
            sys.stdout.write(split(text)[0])
            return 0
        header, items = extract(text)
    except LookupError as ex:
        print(f"route_brief: {ex}; run the synthesizer in routing-only mode", file=sys.stderr)
        return 3
    except RoutingError as ex:
        print("route_brief: INVALID\n" + str(ex), file=sys.stderr)
        return 2
    if a.cmd == "extract":
        if a.json:
            print(json.dumps({"header": header, "items": items}, indent=1, ensure_ascii=False))
        else:
            kinds = {t: sum(1 for i in items if i["type"] == t) for t in TYPES}
            print(f"VALID: {len(items)} items · " + " · ".join(f"{k} {v}" for k, v in kinds.items() if v))
        return 0
    pl = plan(header, items, a.event, a.event_date, a.notion_event_url)
    d = os.path.join(a.state_dir or run_state.STATE_DIR, pl["slug"])
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "routing-plan.json"), "w", encoding="utf-8") as f:
        json.dump(pl, f, indent=1, ensure_ascii=False)
    if pl["notion_payload"]:
        with open(os.path.join(d, "routing-notion-payload.json"), "w", encoding="utf-8") as f:
            json.dump(pl["notion_payload"], f, indent=1, ensure_ascii=False)
    if pl["stories"]:
        with open(os.path.join(d, "stories.md"), "w", encoding="utf-8") as f:
            f.write(stories_md(pl))
    c = pl["counts"]
    print(f"plan → {d}: {c['linear']} Linear issue(s), {c['build_ideas']} Project Ideas row(s), "
          f"{c['stories']} stor{'y' if c['stories'] == 1 else 'ies'} (local)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
