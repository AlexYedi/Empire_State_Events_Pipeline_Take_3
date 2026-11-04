#!/usr/bin/env python3
"""assign_clusters.py: in-session theme (cluster) assignment for topics (YED-307, #267 Phase 0 item 2).

The session that mints a topic assigns its theme (docs/proposals/2026-11-03-dynamic-topic-taxonomy.md §2).
The only writer here is spine_client (guarded PATCH), and only for rows that are still unassigned
(`cluster_id=is.null`), so it can never overwrite an existing assignment.

  list    --event <notion_page_id>     the event's linked live topics with no theme, plus the theme names
  apply   --file a.json [--apply]      write assignments; dry-run unless --apply. Prints "topic → theme"
                                       lines for the Step 6 summary.
  --selftest                           offline checks (no network)

a.json: [{"topic_id": "<uuid>", "topic": "<name>", "theme": "<exact theme name>" | "NONE",
          "confidence": 0.5–1.0, "reason": "<one line, required when theme is NONE>"}]
A concept that fits a theme but doesn't warrant its own topic is tagged to "<Theme> (general)" at 3.8b
instead (must_exist entity). It is not assigned here.
"""
from __future__ import annotations
import json, os, re, sys, urllib.parse

UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "references", "topic-themes.json")
BY = "session"   # ADR-13 vocabulary: bootstrap · llm · embedding_auto · session · human · merge


def load_themes(path: str = REF) -> dict[str, str]:
    with open(path, encoding="utf-8") as f:
        # a list of {name, id}, not a name->id map: a map keyed by names like "...APIs" / "...Access"
        # with uuid values trips gitleaks' generic-api-key rule (CI scan, #276)
        return {t["name"]: t["id"] for t in json.load(f)["themes"]}


def validate(rows, themes: dict[str, str]) -> list[str]:
    """Pure: return problems (empty = valid)."""
    probs = []
    if not isinstance(rows, list):
        return ["file must be a JSON list"]
    seen = set()
    for i, r in enumerate(rows):
        tag = f"row {i}"
        if not isinstance(r, dict):
            probs.append(f"{tag}: not an object"); continue
        if r.get("topic_id") in seen:
            probs.append(f"{tag}: duplicate topic_id (one decision per topic)")
        seen.add(r.get("topic_id"))
        if not isinstance(r.get("topic"), str) or not r.get("topic", "").strip():
            probs.append(f"{tag}: topic (name) is required")
        extra = set(r) - {"topic_id", "topic", "theme", "confidence", "reason"}
        if extra:
            probs.append(f"{tag}: unknown keys {sorted(extra)}")
        if not isinstance(r.get("topic_id"), str) or not UUID.match(r.get("topic_id", "")):
            probs.append(f"{tag}: topic_id must be a uuid string")
        th = r.get("theme")
        if th != "NONE" and th not in themes:
            probs.append(f"{tag}: theme {th!r} is not a known theme (refresh topic-themes.json after a birth)")
        if th == "NONE" and not (r.get("reason") or "").strip():
            probs.append(f"{tag}: theme NONE needs a one-line reason (it seeds theme proposals)")
        c = r.get("confidence")
        if th != "NONE" and not (isinstance(c, (int, float)) and not isinstance(c, bool) and 0.5 <= c <= 1.0):
            probs.append(f"{tag}: confidence must be 0.5–1.0")
        reason = r.get("reason") or ""
        if len(reason) > 300 or any(ord(ch) < 32 for ch in reason):
            probs.append(f"{tag}: reason must be ≤300 printable chars")
    return probs


def _pid_forms(raw: str) -> list[str]:
    """Accept a Notion URL, a dashed or an undashed id; return both stored forms (substrate stores both)."""
    h = re.sub(r"[^0-9a-f]", "", raw.lower().split("?")[0].split("/")[-1])[-32:]
    if len(h) != 32:
        return []
    return [h, f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}"]


def _get(sc, path: str):
    st, body = sc.req("GET", path)
    if st != 200 or not isinstance(body, list):
        raise SystemExit(f"GET {path.split('?')[0]} failed ({st}): {str(body)[:200]}")
    return body


def cmd_list(event_pid: str) -> int:
    sys.path.insert(0, HERE); import spine_client as sc
    forms = _pid_forms(event_pid)
    if not forms:
        print(f"not a Notion page id: {event_pid}", file=sys.stderr); return 1
    ev = _get(sc, f"/event?select=id,title&notion_page_id=in.({','.join(forms)})")
    if not ev:
        print(f"no event with notion_page_id {event_pid}", file=sys.stderr); return 1
    links = _get(sc, f"/event_entity?select=entity_id&entity_type=eq.topic&event_id=eq.{ev[0]['id']}")
    ids = ",".join(l["entity_id"] for l in links)
    out = []
    if ids:
        tops = _get(sc, f"/topic?select=id,name,description,cluster_id,metadata&id=in.({ids})")
        out = [{"topic_id": t["id"], "topic": t["name"], "description": (t.get("description") or "")[:200]}
               for t in tops if t.get("cluster_id") is None and not (t.get("metadata") or {}).get("merged_into")]
    print(json.dumps({"event": ev[0]["title"], "unassigned": out, "themes": sorted(load_themes())}, indent=1))
    return 0


def cmd_apply(path: str, apply: bool) -> int:
    themes = load_themes()
    with open(path, encoding="utf-8") as f:
        rows = json.load(f)
    probs = validate(rows, themes)
    if probs:
        print("INVALID:\n  " + "\n  ".join(probs), file=sys.stderr); return 1
    sys.path.insert(0, HERE); import spine_client as sc
    lines, written, skipped, nonefits, rc = [], 0, 0, 0, 0
    for r in rows:
        if r["theme"] == "NONE":
            nonefits += 1
            lines.append(f"  {r['topic']} → none fits ({r['reason']})"); continue
        body = {"cluster_id": themes[r["theme"]], "cluster_assignment_confidence": round(float(r["confidence"]), 3),
                "cluster_assigned_by": BY}
        # compare-and-set: only a live (non-tombstoned) topic that is still unassigned; read back what changed
        flt = (f"id=eq.{urllib.parse.quote(r['topic_id'], safe='-')}&cluster_id=is.null"
               f"&metadata->>merged_into=is.null")
        st, out = sc.write("topic", body, patch_filter=flt, prefer="return=representation", dry_run=not apply)
        if apply and st not in (200, 201):
            lines.append(f"  {r['topic']} → WRITE FAILED ({st})"); rc = 2; break
        if apply and not out:   # 0 rows matched: already assigned, tombstoned, or wrong id — never report it as done
            skipped += 1
            lines.append(f"  {r['topic']} → skipped (already assigned / tombstoned / not found)"); continue
        written += 1
        lines.append(f"  {r['topic']} → {r['theme']} ({r['confidence']})")
    head = "Theme assignment (3.8d): " if apply else "DRY-RUN theme assignment (3.8d, nothing written): "
    print(head + f"{written} {'assigned' if apply else 'would assign'} · {skipped} skipped · {nonefits} none-fits")
    print("\n".join(lines))
    return rc


def selftest() -> int:
    th = {"Coding Agents": "89497368-6e31-4dc5-b163-f3339170f1e2"}
    u = "00000000-0000-4000-8000-000000000001"
    cases = [
        ("valid row passes", [{"topic_id": u, "topic": "x", "theme": "Coding Agents", "confidence": 0.9}], True),
        ("unknown theme refused", [{"topic_id": u, "topic": "x", "theme": "Made Up", "confidence": 0.9}], False),
        ("NONE without reason refused", [{"topic_id": u, "topic": "x", "theme": "NONE"}], False),
        ("NONE with reason passes", [{"topic_id": u, "topic": "x", "theme": "NONE", "reason": "model layer"}], True),
        ("confidence below 0.5 refused", [{"topic_id": u, "topic": "x", "theme": "Coding Agents", "confidence": 0.3}], False),
        ("bool confidence refused", [{"topic_id": u, "topic": "x", "theme": "Coding Agents", "confidence": True}], False),
        ("unknown key refused", [{"topic_id": u, "topic": "x", "theme": "Coding Agents", "confidence": 0.9, "x": 1}], False),
        ("control char in reason refused", [{"topic_id": u, "topic": "x", "theme": "NONE", "reason": "a\nb"}], False),
        ("bad uuid refused", [{"topic_id": "nope", "topic": "x", "theme": "Coding Agents", "confidence": 0.9}], False),
        ("36-char non-uuid refused", [{"topic_id": "0000000-0000-4000-8000-000000000&a=b", "topic": "x",
                                       "theme": "Coding Agents", "confidence": 0.9}], False),
        ("missing topic name refused", [{"topic_id": u, "theme": "Coding Agents", "confidence": 0.9}], False),
        ("duplicate topic_id refused", [{"topic_id": u, "topic": "x", "theme": "Coding Agents", "confidence": 0.9},
                                        {"topic_id": u, "topic": "y", "theme": "Coding Agents", "confidence": 0.7}], False),
    ]
    ok = 0
    for name, rows, want in cases:
        got = not validate(rows, th)
        ok += got == want
        print(f"  {'✓' if got == want else '✗'} {name}")
    pf = _pid_forms("https://app.notion.com/p/3d5d3699c2db81bbaff3e4f2c696c37b")
    pf_ok = pf == ["3d5d3699c2db81bbaff3e4f2c696c37b", "3d5d3699-c2db-81bb-aff3-e4f2c696c37b"] \
        and _pid_forms("3d5d3699-c2db-81bb-aff3-e4f2c696c37b") == pf and _pid_forms("nope") == []
    ok += pf_ok; print(f"  {'✓' if pf_ok else '✗'} notion page id → both stored forms (URL, dashed, undashed)")
    real = load_themes()
    ref_ok = len(real) >= 30 and all(len(v) == 36 for v in real.values())
    ok += ref_ok; print(f"  {'✓' if ref_ok else '✗'} topic-themes.json loads ({len(real)} themes, uuid ids)")
    n = len(cases) + 2
    print(f"selftest: {ok}/{n} assign_clusters cases pass")
    return 0 if ok == n else 1


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    if argv[:1] == ["list"] and "--event" in argv:
        return cmd_list(argv[argv.index("--event") + 1])
    if argv[:1] == ["apply"] and "--file" in argv:
        return cmd_apply(argv[argv.index("--file") + 1], "--apply" in argv)
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
