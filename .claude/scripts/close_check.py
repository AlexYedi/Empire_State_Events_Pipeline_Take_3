#!/usr/bin/env python3
"""close_check.py: /post-event-content Step 6.5, real-state verdict on the unenforced steps (YED-372).

Read-only, never blocks: exit 0 always (`--strict` exits 1 on FAIL, for tests only). It turns "a skipped graph
write closes green" into a counted line. Each check is PASS / FAIL / SKIPPED (with reason) / SELF-REPORTED
(read from run-state meta because the fact lives in Notion, which a script can't reach: MCP only).

  graph-event    the event row exists in the MI graph (substrate.Graph read path, GET only)
  claims         claims under substrate.source_key_for_event(notion_id) > 0, or run-state `claims` skipped+reason
  themes         every live topic linked to the event has a theme (topic.cluster_id); topics the session judged
                 "none fits" are covered when run-state `themes` carries meta none_fits=N
  themes-prop    `Themes` set on the post draft: SELF-REPORTED from run-state `notion-write` meta themes_prop=set
  routing-rows   Linear / Notion routing rows: SELF-REPORTED from meta routing_rows=N; SKIPPED until 3.8e exists
  run-state      canonical steps neither done nor skipped are gaps

Writes exactly one thing: the `close-check` step into run-state (local, gitignored), result in meta.
The Rooms check was removed on 2026-11-11 (YED-374: Rooms cut from post-event).
Usage: close_check.py <event> --notion-event-id <id> [--json] [--strict]
"""
from __future__ import annotations
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_state  # noqa: E402



class GraphReader:
    """Thin read-only adapter over substrate.Graph (GET only). Tests substitute a fake with the same methods."""

    def __init__(self):
        import substrate
        self.sub = substrate
        self.g = substrate.Graph(dry_run=True, stats=substrate.Stats())

    def source_key(self, notion_id: str) -> str:
        return self.sub.source_key_for_event(notion_id)

    def event_row(self, notion_id: str) -> dict | None:
        return self.g.by_pid("event", notion_id, select="id,title,event_date,notion_page_id,metadata")

    def claim_count(self, source_key: str) -> int:
        return len(self.g.get(f"/claim?source_key=eq.{source_key}&select=id"))

    def topics(self, event_id: str) -> list[dict]:
        links = self.g.get(f"/event_entity?select=entity_id&entity_type=eq.topic&event_id=eq.{event_id}")
        ids = ",".join(l["entity_id"] for l in links)
        if not ids:
            return []
        rows = self.g.get(f"/topic?select=id,name,cluster_id,metadata&id=in.({ids})")
        return [t for t in rows if not (t.get("metadata") or {}).get("merged_into")]


def _r(check: str, status: str, detail: str) -> dict:
    return {"check": check, "status": status, "detail": detail}


def run(event: str, notion_id: str, reader=None, state_dir: str | None = None) -> dict:
    state = run_state.load(event, state_dir) or {}
    steps = state.get("steps", {})
    results: list[dict] = []

    def step(sid: str) -> dict:
        return steps.get(sid, {})

    def skipped_reason(sid: str) -> str | None:
        e = step(sid)
        return e.get("reason") if e.get("status") == "skipped" and e.get("reason") else None

    # --- graph reads (all GET; any failure becomes SKIPPED with the reason, never a crash) ---
    ev, graph_err = None, None
    try:
        reader = reader or GraphReader()
        ev = reader.event_row(notion_id)
    except (Exception, SystemExit) as e:   # Graph.get raises SystemExit on non-200
        graph_err = f"graph unreachable: {str(e)[:160]}"

    if graph_err:
        results.append(_r("graph-event", "SKIPPED", graph_err))
    elif ev:
        results.append(_r("graph-event", "PASS", f"event {ev.get('id')} \"{ev.get('title')}\""))
    elif skipped_reason("graph-event"):
        results.append(_r("graph-event", "SKIPPED", f"run-state: {skipped_reason('graph-event')}"))
    else:
        results.append(_r("graph-event", "FAIL", f"no graph event row for notion_page_id {notion_id} (3.8b)"))

    if skipped_reason("claims"):
        results.append(_r("claims", "SKIPPED", f"run-state: {skipped_reason('claims')}"))
    elif graph_err:
        results.append(_r("claims", "SKIPPED", graph_err))
    else:
        try:
            sk = reader.source_key(notion_id)
            n = reader.claim_count(sk)
            results.append(_r("claims", "PASS" if n > 0 else "FAIL",
                              f"{n} claims under source_key {sk[:12]}…" + ("" if n else " (3.8c)")))
        except (Exception, SystemExit) as e:
            results.append(_r("claims", "SKIPPED", f"claim read failed: {str(e)[:160]}"))

    if skipped_reason("themes"):
        results.append(_r("themes", "SKIPPED", f"run-state: {skipped_reason('themes')}"))
    elif graph_err or not ev:
        results.append(_r("themes", "SKIPPED", graph_err or "no graph event row, so no linked topics to check"))
    else:
        try:
            tops = reader.topics(ev["id"])
            bare = [t for t in tops if not t.get("cluster_id")]
            try:
                none_fits = int((step("themes").get("meta") or {}).get("none_fits", 0))
            except ValueError:
                none_fits = 0
            if not bare:
                results.append(_r("themes", "PASS", f"{len(tops)} linked topics, all themed"))
            elif len(bare) <= none_fits:
                results.append(_r("themes", "PASS", f"{len(tops)} linked topics; {len(bare)} unthemed, covered by "
                                  f"none_fits={none_fits} in run-state"))
            else:
                names = ", ".join(t.get("name", "?") for t in bare[:5]) + (" …" if len(bare) > 5 else "")
                results.append(_r("themes", "FAIL", f"{len(bare)} of {len(tops)} linked topics unthemed (3.8d): {names}"))
        except (Exception, SystemExit) as e:
            results.append(_r("themes", "SKIPPED", f"topic read failed: {str(e)[:160]}"))

    # --- Notion facts: self-reported from run-state meta ---
    nw = step("notion-write")
    prop = (nw.get("meta") or {}).get("themes_prop")
    if nw.get("status") == "skipped":
        results.append(_r("themes-prop", "SKIPPED", f"notion-write skipped: {nw.get('reason')}"))
    elif prop == "set":
        results.append(_r("themes-prop", "SELF-REPORTED", "Themes set on the post draft (run-state notion-write meta)"))
    else:
        results.append(_r("themes-prop", "FAIL", "Themes on the post draft not reported "
                          f"(got themes_prop={prop!r}; mark notion-write --meta themes_prop=set once it is)"))

    routed = next((e["meta"]["routing_rows"] for e in steps.values() if (e.get("meta") or {}).get("routing_rows")), None)
    if routed is not None:
        results.append(_r("routing-rows", "SELF-REPORTED", f"routing_rows={routed} (run-state meta)"))
    else:
        results.append(_r("routing-rows", "SKIPPED", "no Step 3.8e router yet; nothing to count"))

    gaps = [f"{s}({e.get('status', 'missing')})" for s in run_state.STEP_IDS if s != "close-check"
            for e in [steps.get(s, {})] if e.get("status") not in run_state.FINISHED]
    if not state:
        results.append(_r("run-state", "FAIL", "no run-state recorded for this event"))
    elif gaps:
        results.append(_r("run-state", "FAIL", "steps neither done nor skipped: " + ", ".join(gaps)))
    else:
        results.append(_r("run-state", "PASS", "every canonical step done or skipped"))

    fails = [r["check"] for r in results if r["status"] == "FAIL"]
    verdict = "CLOSE-CHECK: PASS" if not fails else f"CLOSE-CHECK: FAIL ({len(fails)}) — {', '.join(fails)}"
    run_state.mark(event, "close-check", "done", state_dir=state_dir,
                   meta={"result": "PASS" if not fails else f"FAIL {len(fails)}", "items": ",".join(fails) or "-"})
    return {"event": event, "slug": run_state.slugify(event), "notion_event_id": notion_id,
            "results": results, "fails": fails, "verdict": verdict}


def render(out: dict) -> str:
    lines = [f"close-check (Step 6.5): {out['event']} [{out['slug']}]"]
    lines += [f"  {r['status']:<13} {r['check']:<13} {r['detail']}" for r in out["results"]]
    lines.append(out["verdict"])
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("event")
    ap.add_argument("--notion-event-id", required=True)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="exit 1 on FAIL (tests only; the pipeline never blocks)")
    a = ap.parse_args(argv)
    out = run(a.event, a.notion_event_id)
    print(json.dumps(out, indent=1) if a.json else render(out))
    return 1 if (a.strict and out["fails"]) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
