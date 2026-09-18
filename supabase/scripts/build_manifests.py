#!/usr/bin/env python3
"""build_manifests.py — Notion rows -> substrate.py manifests (the backfill's input side).

Spec: .claude/notes/knowledge-substrate-review-2026-09-18.md ("backfill runs THROUGH the producers")
+ ADR-10. This script does NOT write to the graph. It only turns Notion data (pulled in the parent
thread — the Notion connector is unavailable to subagents and scripts) into manifests, which are
then fed to .claude/scripts/substrate.py, the same producer /post-event-content Step 3.8b calls.

Inputs (produced by the parent thread from Notion; see /post-event-content Step 3.8b for the query
recipe and its two gotchas — the SQL `url` column has no /p/, and SQL queries are quota-limited on
the free plan):
  --events    JSON list: [{id, name, d, loc, gcal, attended: true|false|null, P:[ids], C:[ids], T:[ids]}]
  --entities  JSON: {"P": {id: [name, title, company_id, linkedin_url, roles]},
                     "C": {id: [name, website]}, "T": {id: name}}

Output (--out DIR), one file per event:
  <date>_<slug>.event.json      attended == true  -> run `substrate.py ensure-event`
  <date>_<slug>.entities.json   attended != true  -> run `substrate.py ensure-entity`
Attendance is never inferred: only events with confirmed attendance get an `attended` event row.
Research knowledge (companies, people, topics) is written either way.

Rules applied here so the producer receives clean input:
  * person role: speaker if 'speaker' in Role Context, else host (host/organizer), else attendee
  * linkedin_url kept only if it is actually a linkedin.com URL
  * topic entities with no known name carry only notion_page_id; substrate.py links them if the
    graph already knows that page and skips (counted) otherwise — re-run after names are filled.
"""
import argparse, json, os, re


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]


def person_role(roles: list[str]) -> str:
    r = [x.lower() for x in roles or []]
    return "speaker" if "speaker" in r else "host" if ("host" in r or "organizer" in r) else "attendee"


def build(events: list, ents: dict) -> tuple[dict, dict]:
    P, C, T = ents.get("P", {}), ents.get("C", {}), ents.get("T", {})
    out, stats = {}, {"event": 0, "entities_only": 0, "person": 0, "company": 0, "topic_named": 0,
                      "topic_id_only": 0, "missing_person_rows": 0, "missing_company_rows": 0}
    for e in events:
        entities = []
        for pid in e.get("P", []):
            row = P.get(pid)
            if not row:
                stats["missing_person_rows"] += 1
                continue
            name, title, cid, li, roles = row
            company = C.get(cid, [None])[0] if cid else None
            entities.append({k: v for k, v in {
                "type": "person", "name": name, "role": person_role(roles), "notion_page_id": pid,
                "title": title, "company": company,
                "linkedin_url": li if li and "linkedin.com" in li else None}.items() if v})
            stats["person"] += 1
        for cid in e.get("C", []):
            row = C.get(cid)
            if not row:
                stats["missing_company_rows"] += 1
                continue
            entities.append({k: v for k, v in {"type": "company", "name": row[0], "role": "subject",
                                                 "notion_page_id": cid, "website": row[1]}.items() if v})
            stats["company"] += 1
        for tid in e.get("T", []):
            ent = {"type": "topic", "role": "tagged_topic", "notion_page_id": tid}
            if T.get(tid):
                ent["name"] = T[tid]
                stats["topic_named"] += 1
            else:
                stats["topic_id_only"] += 1
            entities.append(ent)
        day = e["d"][:10]
        base = f"{day}_{slug(e['name'])}"
        if e.get("attended") is True:
            date = e["d"] if "T" in e["d"] else f"{e['d']}T00:00:00Z"
            ev = {k: v for k, v in {"notion_page_id": e["id"], "title": e["name"], "kind": "attended",
                                    "event_date": date, "location": e.get("loc"),
                                    "google_calendar_event_id": e.get("gcal")}.items() if v}
            out[f"{base}.event.json"] = {"event": ev, "entities": entities}
            stats["event"] += 1
        else:
            out[f"{base}.entities.json"] = {"source_event": {"notion_page_id": e["id"], "title": e["name"],
                                                              "attended": e.get("attended")},
                                            "entities": entities}
            stats["entities_only"] += 1
    return out, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True)
    ap.add_argument("--entities", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out, stats = build(json.load(open(a.events, encoding="utf-8")), json.load(open(a.entities, encoding="utf-8")))
    os.makedirs(a.out, exist_ok=True)
    for name, m in out.items():
        with open(os.path.join(a.out, name), "w", encoding="utf-8") as f:
            json.dump(m, f, indent=1, ensure_ascii=False)
    print(f"wrote {len(out)} manifests to {a.out}")
    for k, v in stats.items():
        print(f"  {k:22s} {v}")


if __name__ == "__main__":
    main()
