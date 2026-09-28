# YED-149 — roles -> MI graph (the third producer) + job-lens isolation

## Purpose
Role-radar roles lived only in the Notion Roles DB. This build mirrors each Roles row into the Supabase MI graph as a `role_posted` event through the existing producer library (`substrate.py ensure-roles`, reusing `ensure_event`), keyed ONLY by the Roles page id, and isolates the job lens from the event lens so hundreds of fresh roles cannot crowd attended/market history out of `/event-deep-research` Context Packs (Alex chose: exclude from the ledger + one count line per seed company). Spec with numbered decisions + pre-mortem: `.claude/notes/yed-149-spec-2026-09-27.md`. Migration 0011 is applied by Alex by SQL-editor paste (DDL via MCP declined), so retrieve.py also filters client-side and labels the path.

## Verification already run
- `substrate.py --selftest` 144/144 (14 new roles/registry checks) · `retrieve.py --selftest` 7/7 · `spine_client.py --selftest` 39/39 + `--check-writers` 0 offenders
- live `retrieve.py` pack on Anthropic+Clay seeds: unchanged ledger, audit line reports `job-lens filter=client-side (0011 not applied ...)`
- live dry run of ensure-roles over 200 transcribed Roles rows: in progress at bundle time (network-latency bound), NOT yet part of this evidence
- NOT run: migration 0011 against any database; the live (non-dry) backfill

## Diff (merge-base..HEAD)
```diff
diff --git a/.claude/notes/yed-149-spec-2026-09-27.md b/.claude/notes/yed-149-spec-2026-09-27.md
new file mode 100644
index 0000000..d32adb6
--- /dev/null
+++ b/.claude/notes/yed-149-spec-2026-09-27.md
@@ -0,0 +1,68 @@
+# YED-149 — roles → MI graph (the third producer) · spec 2026-09-27
+
+**Type:** infra build (an in-repo spec satisfies DoD item 1, per YED-129). **Linear:** YED-149 (pre-flight
+comment 2026-09-27 has the evidence behind every decision below). **Producer:** `substrate.py ensure-roles`,
+running the same `ensure_event` code as every other producer; there is no bespoke writer.
+
+## Problem
+Roles live only in the Notion Roles DB, so the job-search lens can't be queried in the graph: you can't ask
+"who is hiring at the companies whose people I keep meeting". The Notion side has proved its dedup: 203 rows
+over 5 scans, 0 duplicate ATS keys. That was the v1.1 gate.
+
+## Decisions
+1. **Idempotency key = the Roles DB page id.** Pre-flight showed one Roles row maps to exactly one ATS
+   posting, so `notion_page_id` stands in for `{ats_vendor}:{job_id}`, and the ATS key goes into
+   `metadata.ats_key` for traceability. For `role_posted`, `find_event` matches **by page id only**. The title +
+   kind + same-day fallback that attended events use is disabled: it merges same-title roles across
+   companies and locations, and Greenhouse rows have no date to match on. A `role_posted` manifest with no page
+   id is a hard failure.
+2. **One row per role, dated by the ATS posted date.** `event_date` = Posted Date, or null for Greenhouse
+   (it has no posted date; `updated_at` is never used). `confidence = 1.0` (a posting is a fact). Title reads
+   `<Role> — <Company>`. `source = role-radar:<ats>`. A re-run matches and only fills fields that are still
+   missing, so it's a no-op.
+3. **What goes in:** every Roles row except ICP Tier `drop` (counted, not written). Status (applied /
+   archived…) goes to `metadata.status` as a snapshot. It is NOT a lifecycle: `application`/`interview`
+   events are a separate, later decision.
+4. **Edges:** `company —subject→ role`. Topics are **never minted** from the role path: a topic entity
+   carrying `must_exist` resolves or is skipped (counted). v1 emits no topic edges, because the Roles DB has
+   no archetype field and there is no controlled archetype→topic list yet. That list is its own decision, not
+   something to improvise here.
+5. **Volume isolation (Alex, option 1):** the event lens excludes job-lens kinds (`role_posted`,
+   `application`, `interview`) from the Continuity Ledger and adds **one count line per seed company**
+   ("Harvey — 6 tracked roles (A:2 B:3 C:1)"). Applications and interviews never appear in a brief. The
+   exclusion is done in the RPC (migration 0011, which Alex applies; DDL through the MCP stays declined). This
+   matters because only the server side stops roles from using up the `limit 60`. `retrieve.py` also filters
+   on the client, so a pack is correct before 0011 lands; the audit line says which path ran.
+6. Already scoped by kind, so no change needed: the topic-intelligence compute (attended only), the Hub feed
+   and producer health (market only), and `recompute_relevance` (market/attended, and ensure-event never bumps
+   engagement).
+
+## Failure modes → guard
+- Rescan insert-storm → page-id-only match, `role_posted` without a page id fails, and the selftest proves a
+  second run creates 0.
+- Cross-company collapse → no title fallback for this kind (selftest: two identical titles at two companies
+  give two rows).
+- Topic sprawl → `must_exist` (selftest: an unknown topic creates 0 topics).
+- Brief crowding → migration 0011 plus the client filter (selftest: the pack has no job-lens rows plus a
+  roll-up line).
+- PII → every write goes through `spine_client.guard`, and role rows carry no person fields.
+
+## Pre-mortem (DoD item 3): "It's Dec 12 and the role graph is wrong. Why?"
+1. **Company spelling minted duplicates.** Early scans wrote board slugs (`claylabs`, `gleanwork`), and the graph
+   says `Cursor (Anysphere)` and `Modal Labs`. Found in the live data during the build → `--aliases-from` resolves
+   slugs and names against the graph deterministically, and the dry run prints every company it would create
+   for a person to check. Not fuzzy-resolved: `Modal` vs `Modal Labs` (the registry name should be fixed).
+2. **One posting, two Notion pages.** Five archived legacy rows keyed by `title|company` duplicate ATS-keyed
+   rows under slightly different titles, which the title+company dedup query missed → rows without an ATS key
+   are skipped. Also found live.
+3. **A mistyped page id in Step 5.5's transcription** is still valid hex, so it would create a second event on
+   the next rescan → an ATS key already on a different page id is refused and printed.
+4. **0011 never gets applied** → the client-side filter still keeps roles out of the ledger, but the hiring
+   counts are partial and roles still use up the RPC's limit. The audit line says so on every pack, and the
+   Linear follow-up holds the apply.
+5. **Step 5.5 silently skipped** on a scan → no hard gate by design (additive producer; declined alert
+   mechanisms, 2026-09-27). The Step 6 summary line is the trace.
+
+## Build-time detail (deliberately deferred)
+Wiring Step 5.5 into role-radar (the parent thread turns the Notion rows it just wrote into a manifest), and
+the one-time backfill of the 203 existing rows, which uses that same verb.
diff --git a/.claude/references/market-intel-spine.md b/.claude/references/market-intel-spine.md
index b2ca379..7155682 100644
--- a/.claude/references/market-intel-spine.md
+++ b/.claude/references/market-intel-spine.md
@@ -38,7 +38,11 @@ Plan of record: `.claude/references/roadmap.md` (the former `~/.claude/plans/whe
 - **`event`** — first-class **temporal hyperedge AND the signal model**. `kind` splits it:
   `attended` (Alex participates — meetups) vs `market` / `funding` / `launch` / `exec_move` (happens *to*
   entities) vs `role_posted` / `application` / `interview` (job-lens lifecycle). **A signal IS an event**
-  with `kind` + `source` (citation) + `confidence`.
+  with `kind` + `source` (citation) + `confidence`. **Job-lens isolation (YED-149):** `role_posted` is written by
+  role-radar Step 5.5 (`substrate.py ensure-roles`) and is keyed ONLY by the Roles page id, never by title+date.
+  Job-lens kinds never appear in an event-lens ledger: `entity_neighborhood` (0011) excludes them before its
+  limit and returns a per-seed-company `hiring` count instead. Any new consumer that counts events must scope
+  by `kind` for the same reason (hundreds of roles against a handful of signals).
 - **`event_entity`** — the hyperedge join. One event links N entities at a point in time:
   `(event_id, entity_type ∈ {company,person,topic}, entity_id, role)`. Polymorphic (activity-stream
   pattern). The investor↔portfolio link emerges through `funding` events (no separate edge table).
diff --git a/.claude/scripts/retrieve.py b/.claude/scripts/retrieve.py
index df6110e..a36af43 100644
--- a/.claude/scripts/retrieve.py
+++ b/.claude/scripts/retrieve.py
@@ -7,6 +7,7 @@ the other lenses are six weights each and land once this one has proven out on a
 
     .venv/bin/python .claude/scripts/retrieve.py --lens event --seed seed.json [--budget-tokens 6000]
                      [--out pack.md] [--json]
+    .venv/bin/python .claude/scripts/retrieve.py --selftest      (offline: job-lens isolation, YED-149)
 
 seed.json: {"entities": [{"type": "person|company|topic", "name": "...", "notion_page_id": "..."}],
             "text": "<VERBATIM invite / question>", "focus": "<Alex's stated focus>", "window_days": 365}
@@ -31,7 +32,7 @@ import argparse, datetime as dt, json, math, os, sys
 HERE = os.path.dirname(os.path.abspath(__file__))
 sys.path.insert(0, HERE)
 from spine_client import q, req  # noqa: E402
-from substrate import norm_text, pid_variants  # noqa: E402
+from substrate import JOB_LENS_KINDS, norm_text, pid_variants  # noqa: E402
 
 ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
 DOCKB = os.path.join(ROOT, ".claude", "skills", "doc-knowledge-base")
@@ -105,6 +106,7 @@ def neighborhood(ids: list[str], since: str | None) -> tuple[dict, str]:
     events = []
     if eids:
         flt = f"&event_date=gte.{since}" if since else ""
+        flt += f"&kind=not.in.({','.join(JOB_LENS_KINDS)})"      # YED-149: the job lens never fills the ledger
         events = get(f"/event?id=in.({','.join(eids)}){flt}&select=id,title,kind,event_date,source,url"
                      f"&order=event_date.desc&limit=60") or []
     edges = []
@@ -149,6 +151,41 @@ def score_claims(claims: list[dict], seed_ids: set[str], nb_event_ids: set[str],
     return sorted(claims, key=lambda c: -c["_score"])
 
 
+def isolate_job_lens(nb: dict, seed_companies: dict[str, str]) -> tuple[dict, list[dict], str]:
+    """YED-149 (Alex, option 1): job-lens kinds never reach a brief's ledger — the seed companies get one COUNT line
+    each instead ("Harvey — 6 tracked roles"), and applications/interviews appear nowhere. Migration 0011 does this
+    server-side (before the `limit`, so roles can't crowd events out) and returns `hiring`; before 0011 lands the
+    same filter runs here and the counts are partial (only roles that fit under the old limit). Pure."""
+    job = {e["id"] for e in nb.get("events", []) if e.get("kind") in JOB_LENS_KINDS}
+    hiring = nb.get("hiring")
+    path = "rpc (0011)" if hiring is not None else "client-side (0011 not applied: counts partial, crowding possible)"
+    if hiring is None:
+        per: dict[str, dict] = {}
+        roles = {e["id"]: e for e in nb.get("events", []) if e.get("kind") == "role_posted"}
+        for x in nb.get("edges", []):
+            if x["event_id"] in roles and x["entity_type"] == "company" and x["entity_id"] in seed_companies:
+                h = per.setdefault(x["entity_id"], {"company_id": x["entity_id"], "name": seed_companies[x["entity_id"]],
+                                                    "roles": 0, "latest_posted": None})
+                h["roles"] += 1
+                d = roles[x["event_id"]].get("event_date")
+                h["latest_posted"] = max(filter(None, (h["latest_posted"], d)), default=None)
+        hiring = list(per.values())
+    kept = {**nb, "events": [e for e in nb.get("events", []) if e["id"] not in job],
+            "edges": [x for x in nb.get("edges", []) if x["event_id"] not in job],
+            "claims": [c for c in nb.get("claims", []) if c.get("event_id") not in job]}
+    return kept, hiring, path
+
+
+def hiring_lines(hiring: list[dict]) -> list[str]:
+    out = []
+    for h in sorted(hiring, key=lambda r: (-int(r.get("roles") or 0), r.get("name") or "")):
+        tiers = " ".join(f"{t}:{h[k]}" for t, k in (("A", "tier_a"), ("B", "tier_b"), ("C", "tier_c")) if h.get(k))
+        latest = f", latest posted {str(h['latest_posted'])[:10]}" if h.get("latest_posted") else ""
+        out.append(f"- **{h['name']}** — {h['roles']} tracked role{'s' if int(h['roles']) != 1 else ''}"
+                   f"{f' ({tiers})' if tiers else ''}{latest}")
+    return out
+
+
 def build_pack(seed: dict, lens: str, budget: int) -> tuple[str, dict, int]:
     w = LENSES[lens]
     found, missing = resolve(seed.get("entities", []))
@@ -157,6 +194,7 @@ def build_pack(seed: dict, lens: str, budget: int) -> tuple[str, dict, int]:
     if seed.get("window_days"):
         since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=int(seed["window_days"]))).strftime("%Y-%m-%dT00:00:00Z")
     nb, mode = neighborhood(ids, since) if ids else ({"events": [], "edges": [], "documents": [], "claims": []}, "no seeds")
+    nb, hiring, job_path = isolate_job_lens(nb, {f["id"]: f["name"] for f in found if f["type"] == "company"})
     live = claim_layer_live()
     claims = {c["id"]: {**c, "_direct": True} for c in nb.get("claims", [])}
     if live and seed.get("text"):
@@ -193,8 +231,10 @@ def build_pack(seed: dict, lens: str, budget: int) -> tuple[str, dict, int]:
     tcards = ["## Topics recurring across these occasions", ""] + [
         f"- {name} — {len(evs)} occasions" for name, evs in sorted(topics.items(), key=lambda kv: -len(kv[1]))[:15]]
 
+    hire = (["## Hiring at seed companies — job lens, counts only", ""] + hiring_lines(hiring)) if hiring else []
+
     # ---- claims under the token budget ------------------------------------------------------------
-    used = sum(tokens("\n".join(s)) for s in (ledger, cards, tcards))
+    used = sum(tokens("\n".join(s)) for s in (ledger, cards, tcards, hire))
     def render(c: dict) -> str:
         flag = " ⚠ do-not-publish" if (c.get("metadata") or {}).get("do_not_publish") else ""
         ev = ev_by_id.get(c.get("event_id"))
@@ -233,14 +273,16 @@ def build_pack(seed: dict, lens: str, budget: int) -> tuple[str, dict, int]:
     audit = {"lens": lens, "mode": mode, "claims_layer": "live" if live else "not migrated (S1a pending)",
              "seeds_resolved": len(found), "seeds_unresolved": missing, "events": len(nb["events"]),
              "edges": len(nb["edges"]), "claims_candidates": len(ranked), "claims_kept": len(kept),
-             "claims_cut": len(cut), "tokens": used, "budget": budget}
+             "claims_cut": len(cut), "tokens": used, "budget": budget,
+             "hiring_companies": len(hiring), "job_lens_filter": job_path}
     audit_line = (f"AUDIT · lens={lens} · seeds={len(found)} resolved/{len(missing)} unresolved · "
                   f"events={audit['events']} · claims {len(kept)} kept/{len(cut)} cut · docs={len(nb.get('documents', []))} · "
-                  f"tokens {used}/{budget} · graph={mode} · claims-layer={audit['claims_layer']}")
+                  f"tokens {used}/{budget} · graph={mode} · claims-layer={audit['claims_layer']} · "
+                  f"job-lens filter={job_path}")
     lines += [f"_{audit_line}_", ""]
     if missing:
         lines += [f"**Unresolved seeds (reported, not guessed):** {', '.join(missing)}", ""]
-    lines += ledger + [""] + cards + [""] + tcards + [""] + cl + [""]
+    lines += ledger + [""] + cards + [""] + tcards + [""] + (hire + [""] if hire else []) + cl + [""]
 
     # ---- loud failure (review finding 6) --------------------------------------------------------
     rc = 0
@@ -258,7 +300,39 @@ def build_pack(seed: dict, lens: str, budget: int) -> tuple[str, dict, int]:
     return "\n".join(lines), {**audit, "audit_line": audit_line}, rc
 
 
+def selftest() -> bool:
+    """Offline (no network): the job-lens isolation contract (YED-149)."""
+    nb = {"events": [{"id": "e1", "kind": "attended", "title": "Demo Night", "event_date": "2026-09-01"},
+                     {"id": "r1", "kind": "role_posted", "title": "AE — Harvey", "event_date": "2026-09-20"},
+                     {"id": "r2", "kind": "role_posted", "title": "CSM — Harvey", "event_date": "2026-09-22"},
+                     {"id": "a1", "kind": "application", "title": "Applied — Harvey", "event_date": "2026-09-23"}],
+          "edges": [{"event_id": i, "entity_type": "company", "entity_id": "co1", "role": "subject", "name": "Harvey"}
+                    for i in ("e1", "r1", "r2", "a1")],
+          "claims": [{"id": "c1", "event_id": "a1"}, {"id": "c2", "event_id": "e1"}], "documents": []}
+    kept, hiring, path = isolate_job_lens(nb, {"co1": "Harvey"})
+    rpc_kept, rpc_hiring, rpc_path = isolate_job_lens({**nb, "hiring": [{"name": "Harvey", "roles": 6, "tier_a": 2,
+                                                                          "tier_b": 4, "latest_posted": "2026-09-22"}]}, {})
+    checks = [
+        ("no job-lens kind in the ledger", [e["id"] for e in kept["events"]] == ["e1"]),
+        ("job-lens edges + claims dropped", {x["event_id"] for x in kept["edges"]} == {"e1"}
+         and [c["id"] for c in kept["claims"]] == ["c2"]),
+        ("client-side count: roles only, never applications", hiring == [{"company_id": "co1", "name": "Harvey", "roles": 2,
+                                                                          "latest_posted": "2026-09-22"}]),
+        ("client-side path is labelled partial", path.startswith("client-side")),
+        ("rpc hiring wins + labelled", rpc_path == "rpc (0011)" and rpc_hiring[0]["roles"] == 6),
+        ("count line format", hiring_lines(rpc_hiring) == ["- **Harvey** — 6 tracked roles (A:2 B:4), latest posted 2026-09-22"]),
+        ("no seed company -> no hiring lines", isolate_job_lens(nb, {})[1] == []),
+    ]
+    for name, good in checks:
+        print(f"  {'✓' if good else '✗'} {name}")
+    fail = sum(1 for _, g in checks if not g)
+    print(f"selftest: {len(checks) - fail}/{len(checks)} pass")
+    return fail == 0
+
+
 def main(argv: list[str]) -> int:
+    if "--selftest" in argv:
+        return 0 if selftest() else 1
     ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
     ap.add_argument("--lens", choices=sorted(LENSES), default="event")
     ap.add_argument("--seed", required=True)
diff --git a/.claude/scripts/substrate.py b/.claude/scripts/substrate.py
index 81cac22..03a77b7 100644
--- a/.claude/scripts/substrate.py
+++ b/.claude/scripts/substrate.py
@@ -23,6 +23,10 @@ Verbs (W1 four + the S1b-lite `merge`; record-usage / record-outcome stay out of
                   everything else skipped + counted). NO event row — attendance is never inferred (ADR-10 D9); the
                   post-event ensure-event attaches these claims when the attended row appears.
                   Spec: .claude/notes/yed-205-spec-2026-09-27.md
+  ensure-roles    --manifest r.json   (YED-149) {"roles": [Notion Roles rows, SQL shape], "company_aliases": {slug|name: Name}}
+                  -> one `role_posted` event each +
+                  a company edge; keyed ONLY by the Roles page id; ICP Tier `drop` skipped. Spec:
+                  .claude/notes/yed-149-spec-2026-09-27.md
   merge           --table company|person|topic --from <id|name> --into <id|name> --reason "…" [--dry-run]
                   HUMAN-ONLY, REVERSIBLE soft-merge (YED-47, ADR-4 D3): re-points every edge it can, transfers
                   engagement, tombstones the source (metadata.merged_into + an edge snapshot). Deletes nothing.
@@ -69,6 +73,14 @@ ROLE_MAP = {  # manifest role -> the graph's existing vocabulary
     "company": {"host": "subject", "sponsor": "subject", "subject": "subject", "mentioned": "subject"},
 }
 
+# YED-149 — the job lens (spec: .claude/notes/yed-149-spec-2026-09-27.md).
+# JOB_LENS_KINDS never enter an event brief's ledger (retrieve.py + migration 0011 filter them out and add a
+# per-company count instead). PAGE_KEYED_KINDS match ONLY by notion_page_id: the title+kind+same-day fallback
+# collapses same-title roles across companies/locations, and Greenhouse roles have no date to match on.
+JOB_LENS_KINDS = ("role_posted", "application", "interview")
+PAGE_KEYED_KINDS = ("role_posted",)
+ROLE_SKIP_TIERS = ("drop",)            # ICP Tier `drop` = not a target role; counted, never written
+
 # post_event_brief section -> claim_type. Briefs drifted across sessions (verified against real
 # briefs 2026-09-18: Postgres Sep-16 · Agents Behaving Badly Jun-25 · Shortlist Aug-24), so each
 # kind has aliases. A heading matches when it STARTS WITH an alias.
@@ -130,7 +142,7 @@ FREEZE_LOG = os.path.join(ROOT, ".claude", "artifacts", "graph-freeze-overrides.
 # Verbs that change graph state. `waive` and `preview-claims` are absent on purpose (see above);
 # --dry-run is exempted at the call site, not here.
 FREEZE_BLOCKS = ("ensure-entity", "ensure-event", "ensure-document", "stage-claims",
-                 "backfill", "backfill-questions", "approve-claims", "merge", "stage-research")
+                 "backfill", "backfill-questions", "approve-claims", "merge", "stage-research", "ensure-roles")
 
 
 def freeze_state() -> dict | None:
@@ -741,15 +753,22 @@ class Graph:
         return [vec_literal(v) for v in embed_passages(texts)]
 
     def get(self, path: str) -> list:
+        cache = getattr(self, "_rcache", None)      # opt-in per-run read cache (ensure-roles); writes clear it
+        if cache is not None and path in cache:
+            return [dict(r) for r in cache[path]]
         st, body = req("GET", path)
         if st != 200:
             raise SystemExit(f"GET {path} -> {st}: {str(body)[:300]}")
+        if cache is not None:
+            cache[path] = [dict(r) for r in (body or [])]
         return body or []
 
     def post(self, table: str, row: dict | list, prefer: str = "return=representation", on_conflict: str | None = None):
         rows = row if isinstance(row, list) else [row]
         for r in rows:
             guard(table, r)                                          # fail before any network call
+        if getattr(self, "_rcache", None):
+            self._rcache.clear()
         if self.dry:
             self._n += 1
             return [{**r, "id": r.get("id") or f"dry:{table}:{self._n}:{i}"} for i, r in enumerate(rows)]
@@ -761,6 +780,8 @@ class Graph:
 
     def patch(self, table: str, flt: str, row: dict):
         guard(table, row, op="update")
+        if getattr(self, "_rcache", None):
+            self._rcache.clear()
         if self.dry:
             return
         st, body = req("PATCH", f"/{table}?{flt}", row, prefer="return=minimal")
@@ -860,6 +881,9 @@ class Graph:
             self.stats.bump("topic", "matched")
             self._fill_missing("topic", row, {k: v for k, v in fields.items() if k != "name"})
             return row["id"]
+        if e.get("must_exist"):                      # YED-149: a controlled-vocabulary edge never mints a topic
+            self.stats.bump("topic", "skipped_not_in_vocab")
+            return None
         if (hit := self._cached("topic", e["name"])):
             return hit
         self.stats.bump("topic", "created")
@@ -1085,7 +1109,7 @@ class Graph:
     # -- events ----------------------------------------------------------------------------------
     def find_event(self, ev: dict) -> dict | None:
         row = self.by_pid("event", ev.get("notion_page_id"))
-        if row or not ev.get("event_date"):
+        if row or not ev.get("event_date") or ev.get("kind") in PAGE_KEYED_KINDS:
             return row
         day = ev["event_date"][:10]
         rows = self.get(f"/event?title=ilike.{q(ev['title'].replace('*', ''))}&kind=eq.{ev.get('kind', 'attended')}"
@@ -1094,10 +1118,20 @@ class Graph:
 
     def ensure_event(self, m: dict) -> str:
         ev = m["event"]
+        if ev.get("kind") in PAGE_KEYED_KINDS and not pid_variants(ev.get("notion_page_id")):
+            raise SystemExit(f"ensure-event: {ev.get('kind')} {ev.get('title')!r} has no notion_page_id — refusing "
+                             "(the page id IS this kind's idempotency key; a title match would collapse roles)")
         row = self.find_event(ev)
         if row:
             self.stats.bump("event", "matched")
             eid = row["id"]
+            if ev.get("kind") in PAGE_KEYED_KINDS:   # a rescan only fills what an earlier write lacked...
+                self._fill_missing("event", row, {k: ev.get(k) for k in ("event_date", "url", "confidence")})
+                meta, new = row.get("metadata") or {}, ev.get("metadata") or {}
+                moved = {k: new[k] for k in ("status", "icp_tier") if k in new and meta.get(k) != new[k]}
+                if moved and not str(eid).startswith("dry:"):   # ...plus the two fields Alex moves in Notion
+                    self.patch("event", f"id=eq.{eid}", {"metadata": {**meta, **moved}})
+                    self.stats.bump("event", "status_refreshed")
         else:
             if not ev.get("kind"):   # ADR-10 decision 9: attendance is never inferred — the caller must say so
                 raise SystemExit(f"ensure-event: manifest for {ev.get('title')!r} has no 'kind'; refusing to "
@@ -1105,9 +1139,11 @@ class Graph:
             self.stats.bump("event", "created")
             eid = self.post("event", {k: v for k, v in {
                 "title": ev["title"], "kind": ev["kind"], "event_date": ev.get("event_date"),
-                "description": ev.get("description"), "url": ev.get("url"), "source": SOURCE,
+                "description": ev.get("description"), "url": ev.get("url"),
+                "source": ev.get("source") or SOURCE, "confidence": ev.get("confidence"),
                 "notion_page_id": (pid_variants(ev.get("notion_page_id")) or [None])[-1],
-                "metadata": {k2: ev[k2] for k2 in ("location", "google_calendar_event_id") if ev.get(k2)},
+                "metadata": {**{k2: ev[k2] for k2 in ("location", "google_calendar_event_id") if ev.get(k2)},
+                             **(ev.get("metadata") or {})},
             }.items() if v not in (None, "", {})})[0]["id"]
         existing = set()
         if not str(eid).startswith("dry:"):
@@ -1393,6 +1429,138 @@ def stage_research(g: Graph, md: str, manifest: dict, *, brief_ref: str | None)
     return 0
 
 
+# ---------------------------------------------------------------------------------------------
+# YED-149 — roles -> graph (spec: .claude/notes/yed-149-spec-2026-09-27.md). Input = Notion Roles DB rows in the
+# SQL-mode shape `notion-query-data-sources` returns (column names verbatim), so role-radar Step 5.5 and the
+# one-time backfill feed the SAME verb. Output = one ordinary ensure-event manifest per role.
+# ---------------------------------------------------------------------------------------------
+ATS_SLUG_RE = re.compile(r"(?:jobs\.ashbyhq\.com|job-boards\.greenhouse\.io|boards\.greenhouse\.io|jobs\.lever\.co|"
+                         r"apply\.workable\.com)/([^/?#]+)", re.I)
+
+
+def canonical_company(r: dict, aliases: dict[str, str]) -> str:
+    """The graph name for a Roles row's company. Early scans wrote the ATS board slug (`claylabs`, `gleanwork`) or a
+    lower-cased name into `Company`; written as-is those mint duplicate companies. `aliases` maps a normalized name
+    OR board slug -> canonical name (Step 5.5 builds it from the target-company registry). No alias -> unchanged
+    (the graph's case-insensitive name match still absorbs `anthropic` vs `Anthropic`)."""
+    company = (r.get("Company") or "").strip()
+    amap = {norm_text(k): v for k, v in (aliases or {}).items()}
+    if norm_text(company) in amap:
+        return amap[norm_text(company)]
+    m = ATS_SLUG_RE.search(r.get("userDefined:URL") or r.get("URL") or "")
+    if m and norm_text(m.group(1)) in amap and norm_text(company) == norm_text(m.group(1)):
+        return amap[norm_text(m.group(1))]
+    return company
+
+
+def role_manifest(r: dict, aliases: dict[str, str] | None = None) -> tuple[dict | None, str | None]:
+    """One Roles row -> (manifest, None) or (None, skip_reason). Pure; covered by --selftest.
+    Professional fields only: `Notes` (Alex's free text) never leaves Notion."""
+    title, company = (r.get("Role Title") or "").strip(), canonical_company(r, aliases or {})
+    if not (title and company):
+        return None, "missing_title_or_company"
+    if (r.get("ICP Tier") or "") in ROLE_SKIP_TIERS:
+        return None, "tier_drop"
+    if not pid_variants(r.get("url")) or len(pid_variants(r.get("url"))) != 2:
+        return None, "no_page_id"
+    key = (r.get("Content Hash") or "").strip()
+    if not re.match(r"^(greenhouse|ashby|lever|workable):\S+$", key):
+        # A `title|company` hash is a pre-ATS legacy row, not a verified posting — and in practice each one is an
+        # archived twin of an ATS-keyed row for the SAME posting (titles differ slightly, so name-dedup misses it).
+        return None, "no_ats_key"
+    meta = {k: v for k, v in {
+        "ats_key": key,
+        "company": company, "status": r.get("Status"), "icp_tier": r.get("ICP Tier"),
+        "icp_score": r.get("ICP Score"), "workplace": r.get("Workplace"),
+    }.items() if v not in (None, "")}
+    posted = r.get("date:Posted Date:start") or None     # Greenhouse: empty by design (updated_at is not a posted date)
+    ev = {"notion_page_id": r["url"], "title": f"{title} — {company}", "kind": "role_posted",
+          "event_date": posted, "url": r.get("userDefined:URL") or r.get("URL"), "confidence": 1.0,
+          "source": f"role-radar:{r.get('Source') or 'unknown'}", "location": r.get("Location"), "metadata": meta}
+    return {"event": {k: v for k, v in ev.items() if v not in (None, "")},
+            "entities": [{"type": "company", "name": company, "role": "subject"}]}, None
+
+
+REGISTRY_ROW_RE = re.compile(r"^\|\s*\**([^|*]+?)\**\s*\|\s*(greenhouse|ashby|lever|workable)\s*\|\s*`([^`]+)`", re.I)
+
+
+def registry_aliases(md: str, g: Graph) -> dict[str, str]:
+    """Parse the target-company registry's `| Company | ATS | <backticked slug> |` rows and map each board slug AND each
+    registry name to the name the graph ALREADY uses for that company (so `cursor` -> `Cursor (Anysphere)`),
+    else to the registry name. Deterministic: exact name, then a unique qualified twin, then a qualifier's base.
+    Never fuzzy — `Modal` vs `Modal Labs` is NOT resolved here; the dry run's new-company list is where a human
+    catches it (fix the registry name, then re-run)."""
+    out: dict[str, str] = {}
+    for line in md.splitlines():
+        m = REGISTRY_ROW_RE.match(line.strip())
+        if not m:
+            continue
+        name, slug = m.group(1).strip(), m.group(3).strip()
+        hit = g.live_by_name("company", name)
+        if not hit:
+            twins = [t for t in g.get(
+                f"/company?name=ilike.{q(name.replace('*', '') + ' (*')}&select=*&limit=5")
+                if not (t.get("metadata") or {}).get("merged_into")]
+            hit = twins if len(twins) == 1 else []
+        if not hit:
+            base, qual = split_qualifier(name)
+            if qual:
+                b = g.live_by_name("company", base)
+                hit = b if len(b) == 1 else []
+        canon = hit[0]["name"] if len(hit) == 1 else name
+        for k in (slug, name, split_qualifier(name)[0]):
+            out.setdefault(norm_text(k), canon)
+    return out
+
+
+def _role_current(row: dict, ev: dict, edged: set) -> bool:
+    """True when an existing role row already says everything this manifest would write (the rescan fast path)."""
+    meta, new = row.get("metadata") or {}, ev.get("metadata") or {}
+    return (row["id"] in edged and all(meta.get(k) == new.get(k) for k in ("status", "icp_tier"))
+            and all(row.get(k) not in (None, "") or ev.get(k) in (None, "") for k in ("event_date", "url", "confidence")))
+
+
+def ensure_roles(g: Graph, rows: list[dict], aliases: dict[str, str] | None = None) -> int:
+    """One bulk read of the existing role rows (+ their company edges) lets a rescan skip every unchanged role
+    without a per-role round trip; anything new or changed goes through the ordinary ensure_event path."""
+    skipped: dict[str, int] = {}
+    g._rcache = {}
+    existing = {pid_variants(e["notion_page_id"])[0]: e for e in g.get(
+        "/event?kind=eq.role_posted&select=id,notion_page_id,metadata,event_date,url,confidence&limit=10000")
+        if pid_variants(e.get("notion_page_id"))}
+    ids, edged = [e["id"] for e in existing.values()], set()
+    for i in range(0, len(ids), 80):
+        edged |= {x["event_id"] for x in g.get(f"/event_entity?entity_type=eq.company&event_id=in.({','.join(ids[i:i + 80])})"
+                                               f"&select=event_id")}
+    by_ats = {(e.get("metadata") or {}).get("ats_key"): pid for pid, e in existing.items()}
+    for r in rows:
+        m, why = role_manifest(r, aliases)
+        if why:
+            skipped[why] = skipped.get(why, 0) + 1
+            continue
+        pid, ats = pid_variants(m["event"]["notion_page_id"])[0], m["event"]["metadata"]["ats_key"]
+        if by_ats.get(ats, pid) != pid:
+            # The same posting under a DIFFERENT page id: a second Notion row for it, or a mistyped id. Either way a
+            # write would duplicate the role — refuse it loudly; the fix is in Notion (or the manifest), not here.
+            print(f"REFUSED {ats}: already in the graph under page {by_ats[ats][:8]}…, this row is page {pid[:8]}…")
+            skipped["ats_key_on_other_page"] = skipped.get("ats_key_on_other_page", 0) + 1
+            continue
+        by_ats[ats] = pid
+        cur = existing.get(pid)
+        if cur and _role_current(cur, m["event"], edged):
+            g.stats.bump("event", "matched")
+            continue
+        g.ensure_event(m)
+    g._rcache = None
+    g.stats.bump("role", "input", len(rows))
+    for why, n in skipped.items():
+        g.stats.bump("role", f"skipped_{why}", n)
+    new_cos = sorted(n for (t, n) in g._made if t == "company")
+    if new_cos:   # the review surface: a would-create company that already exists under another name is a duplicate
+        print(f"{'would create' if g.dry else 'created'} {len(new_cos)} companies: {', '.join(new_cos)}")
+    return 0
+
+
 def source_key_for_topic_questions(notion_topic_id: str) -> str:
     return sha("notion_topic_questions:" + pid_variants(notion_topic_id)[0])
 
@@ -1781,6 +1949,68 @@ MIXED_SAMPLE = """
 """
 
 
+def _roles_selftest(ok) -> None:
+    """YED-149 acceptance, offline: idempotent rescan, no cross-company collapse, no topic minting, page id required."""
+    def row(pid, title, co, key, tier="B", posted="2026-09-20", src="ashby", notes="call recruiter at 555"):
+        return {"url": f"https://app.notion.com/p/{pid * 32}"[:61], "Role Title": title, "Company": co,
+                "Content Hash": key, "ICP Tier": tier, "date:Posted Date:start": posted, "Source": src,
+                "userDefined:URL": f"https://jobs.example/{key}", "Status": "new", "Notes": notes}
+    m, why = role_manifest(row("a", "Enterprise AE", "Harvey", "ashby:1"))
+    ok("roles: manifest = role_posted, conf 1.0, company edge", why is None and m["event"]["kind"] == "role_posted"
+       and m["event"]["confidence"] == 1.0 and m["entities"] == [{"type": "company", "name": "Harvey", "role": "subject"}])
+    ok("roles: Notes never leave Notion", "555" not in json.dumps(m))
+    ok("roles: ICP Tier drop -> skipped", role_manifest(row("b", "SDR", "Harvey", "ashby:2", tier="drop"))[1] == "tier_drop")
+    ok("roles: legacy title|company hash -> skipped (not a verified posting)",
+       role_manifest(row("c", "AE", "Zip", "ae|zip"))[1] == "no_ats_key")
+    ok("roles: Greenhouse (no posted date) -> no event_date",
+       "event_date" not in role_manifest(row("d", "AE", "Vercel", "greenhouse:9", posted="", src="greenhouse"))[0]["event"])
+    fg = _FakeGraph()
+    fg.t["company"].append({"id": "co-harvey", "name": "Harvey", "metadata": {}})
+    rows = [row("1", "Account Executive", "Harvey", "ashby:10"), row("2", "Account Executive", "Baseten", "ashby:11"),
+            row("3", "Account Executive", "Harvey", "ashby:12"), row("4", "AE", "Vercel", "greenhouse:13", posted="", src="greenhouse"),
+            row("5", "SDR", "Harvey", "ashby:14", tier="drop")]
+    ensure_roles(fg, rows)
+    evs = [e for e in fg.t["event"] if e["kind"] == "role_posted"]
+    ok("roles: same title at 2 companies + 2 locations -> 4 rows (no title collapse), drop skipped", len(evs) == 4)
+    ok("roles: existing company reused, new one created once",
+       sum(c["name"] == "Harvey" for c in fg.t["company"]) == 1 and sum(c["name"] == "Baseten" for c in fg.t["company"]) == 1)
+    fg.stats = Stats()
+    ensure_roles(fg, rows)
+    ok("roles: rescan is a no-op (created 0)", fg.stats.created() == 0 and len(fg.t["event"]) == 4
+       and not fg.stats.c.get("event", {}).get("status_refreshed"))
+    fg.stats = Stats()
+    ensure_roles(fg, [{**rows[0], "Status": "archived"}])
+    ok("roles: a status moved in Notion is refreshed, still created 0", fg.stats.created() == 0
+       and fg.stats.c["event"].get("status_refreshed") == 1
+       and next(e for e in fg.t["event"] if e["title"] == "Account Executive — Harvey")["metadata"]["status"] == "archived")
+    try:
+        fg.ensure_event({"event": {"title": "AE — Harvey", "kind": "role_posted", "event_date": "2026-09-20"}, "entities": []})
+        refused = False
+    except SystemExit:
+        refused = True
+    ok("roles: role_posted without a page id -> refused", refused)
+    fg.stats = Stats()
+    ensure_roles(fg, [row("9", "Account Executive", "Harvey", "ashby:10")])   # ashby:10 already lives on page 1…
+    ok("roles: same ATS key on a different page id -> refused, nothing written",
+       fg.stats.c["role"].get("skipped_ats_key_on_other_page") == 1 and fg.stats.created() == 0)
+    fg.ensure_event({"event": {**role_manifest(row("6", "CSM", "Harvey", "ashby:15"))[0]["event"]},
+                     "entities": [{"type": "topic", "name": "Brand New Archetype", "must_exist": True}]})
+    ok("roles: must_exist topic never minted", not fg.t["topic"])
+    al = {"claylabs": "Clay", "gleanwork": "Glean"}
+    slug = {**row("7", "AE", "claylabs", "ashby:16"), "userDefined:URL": "https://jobs.ashbyhq.com/claylabs/16"}
+    ok("roles: board-slug company -> canonical via alias", role_manifest(slug, al)[0]["entities"][0]["name"] == "Clay"
+       and role_manifest(slug, al)[0]["event"]["title"] == "AE — Clay")
+    fg2 = _FakeGraph()
+    fg2.t["company"] += [{"id": "c1", "name": "Cursor (Anysphere)", "metadata": {}}, {"id": "c2", "name": "Clay", "metadata": {}}]
+    reg = ("| Company | ATS | Token / board |\n|---|---|---|\n| Clay | ashby | `claylabs` |\n"
+           "| Cursor | ashby | `cursor` |\n| **Runway** | ashby | `runway-ml` |\n| Cyera | Comeet | `x` |")
+    ra = registry_aliases(reg, fg2)
+    ok("registry: slug -> graph name; bare name -> unique qualified twin; unknown -> registry name",
+       ra.get("claylabs") == "Clay" and ra.get("cursor") == "Cursor (Anysphere)" and ra.get("runway-ml") == "Runway"
+       and "x" not in ra)
+    ok("roles: no alias -> name unchanged", role_manifest(row("8", "AE", "Harvey", "ashby:17"), al)[0]["entities"][0]["name"] == "Harvey")
+
+
 def _research_selftest(ok) -> None:
     """YED-205, offline, against _FakeGraph + a sample Evidence Set in the specialists' documented format."""
     items, skipped = parse_ledger(RESEARCH_SAMPLE)
@@ -2074,7 +2304,7 @@ def selftest() -> bool:
     ok("freeze: preview-claims is offline, never blocked", freeze_check("preview-claims", False, None) == 0)
     ok("freeze: every mutating verb is covered",
        set(FREEZE_BLOCKS) == {"ensure-entity", "ensure-event", "ensure-document", "stage-claims",
-                              "backfill", "backfill-questions", "approve-claims", "merge", "stage-research"})
+                              "backfill", "backfill-questions", "approve-claims", "merge", "stage-research", "ensure-roles"})
     _saved_freeze = FREEZE_PATH
     try:                                              # unreadable marker must fail CLOSED
         globals()["FREEZE_PATH"] = os.path.join(ROOT, ".claude", "references", "__nonexistent__.json")
@@ -2096,6 +2326,7 @@ def selftest() -> bool:
     _identity_selftest(ok)
     # ---- the pre-event write path (YED-205) --------------------------------------------------------
     _research_selftest(ok)
+    _roles_selftest(ok)
 
     fail = 0
     for name, good in checks:
@@ -2112,7 +2343,7 @@ def main(argv: list[str]) -> int:
     ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
     ap.add_argument("verb", choices=["ensure-entity", "ensure-event", "ensure-document", "stage-claims", "waive",
                                      "backfill", "backfill-questions", "preview-claims", "approve-claims", "merge",
-                                     "expect-research", "stage-research"])
+                                     "expect-research", "stage-research", "ensure-roles"])
     ap.add_argument("--evidence", help="(stage-research) the Evidence Set, or the raw specialist returns, as markdown")
     ap.add_argument("--phase", choices=["post_event", "pre_event"], default="post_event",
                     help="(waive) which gate row: post_event (default) or pre_event (the research row)")
@@ -2136,6 +2367,9 @@ def main(argv: list[str]) -> int:
     ap.add_argument("--brief-ref", help="external_ref for the brief document, e.g. notion:<page id>")
     ap.add_argument("--approve", action="store_true",
                     help="inherited approval: brief-derived claims land approved (do_not_publish ones never do)")
+    ap.add_argument("--aliases-from", metavar="REGISTRY.md",
+                    help="(ensure-roles) the target-company registry; board slugs + names resolve to the graph's "
+                         "existing company names (explicit company_aliases in the manifest win)")
     ap.add_argument("--dry-run", action="store_true")
     ap.add_argument("--json", action="store_true")
     a = ap.parse_args(argv)
@@ -2193,6 +2427,16 @@ def main(argv: list[str]) -> int:
     if not a.manifest:
         ap.error(f"{a.verb} needs --manifest")
     m = json.load(open(a.manifest, encoding="utf-8"))
+    if a.verb == "ensure-roles":                   # YED-149: {"roles": [Notion Roles rows, SQL shape]} or a bare list
+        aliases = {} if isinstance(m, list) else dict(m.get("company_aliases", {}))
+        if a.aliases_from:                         # the local target-company registry (gitignored; path passed in)
+            aliases = {**registry_aliases(open(a.aliases_from, encoding="utf-8").read(), g), **aliases}
+        rc = ensure_roles(g, m if isinstance(m, list) else m.get("roles", []), aliases)
+        print(("DRY-RUN " if a.dry_run else "") + f"ensure-roles: created={stats.created()}")
+        print(stats.report())
+        if a.json:
+            print(json.dumps({"verb": a.verb, "dry_run": a.dry_run, "created": stats.created(), "stats": stats.c}))
+        return rc
     rc = 0
     ev = m.get("event") or {}
     gate_key = (pid_variants(ev.get("notion_page_id")) or [None])[0]
diff --git a/.claude/skills/role-radar/SKILL.md b/.claude/skills/role-radar/SKILL.md
index 9fa7938..bfeaa44 100644
--- a/.claude/skills/role-radar/SKILL.md
+++ b/.claude/skills/role-radar/SKILL.md
@@ -1,6 +1,6 @@
 ---
 name: role-radar
-description: "Signal scanner — job search & tracking. Aggregates roles from legitimate sources (ATS boards APIs — Greenhouse/Lever/Ashby/Workable via curl — primary; + Apollo-at-targets, credit-gated, optional), dedupes on the ATS job-id, scores each against Alex's Target-Role ICP (me-model §1.5), and lands them in a Notion Roles DB as a status Kanban. Notion-only, manual trigger, human-in-the-loop. No LinkedIn scraping."
+description: "Signal scanner — job search & tracking. Aggregates roles from legitimate sources (ATS boards APIs — Greenhouse/Lever/Ashby/Workable via curl — primary; + Apollo-at-targets, credit-gated, optional), dedupes on the ATS job-id, scores each against Alex's Target-Role ICP (me-model §1.5), and lands them in a Notion Roles DB as a status Kanban, mirrored to the MI graph as role_posted events (Step 5.5). Manual trigger, human-in-the-loop. No LinkedIn scraping."
 ---
 
 # Role Radar Skill
@@ -20,7 +20,7 @@ This is one of three **signal scanners** feeding the Empire State pipeline (alon
 - **Notion plan constraint (re-verified 2026-09-27):** `notion-query-data-sources` SQL **does** work on this plan but is **quota-capped** — the shared workspace limit tripped after ~12 queries in one session. Spend it on ONE bulk pass per run (Content Hash + Tier + Status + Notes for every row — a few LIMIT/OFFSET pages of the same query, ~100 rows each), then use `notion-fetch` per page for anything else. Never design a step that needs SQL more than once; when the cap hits mid-run, fall back to `notion-fetch` — it has no such cap.
 - **No fabricated numbers / honest gaps:** if a source errors, say so.
 
-**Scope:** ATS boards APIs (primary) + Apollo-at-targets (credit-gated, optional); Notion-only; manual trigger. **Dice and RSS.app were REMOVED 2026-09-27 (Alex):** never used in any scan to date — the Dice connector was never authenticated and no RSS.app feed was ever generated — and the 31-board ATS registry covers the target list directly. Do not re-add them without a coverage case. The **graph-producer** (roles → MI spine) and scheduled ingestion are **deferred to v1.1** (Linear "Job-Search Engine" YED-149) — roles first prove out in the Notion Roles DB before writing the shared graph.
+**Scope:** ATS boards APIs (primary) + Apollo-at-targets (credit-gated, optional); Notion-only; manual trigger. **Dice and RSS.app were REMOVED 2026-09-27 (Alex):** never used in any scan to date — the Dice connector was never authenticated and no RSS.app feed was ever generated — and the 31-board ATS registry covers the target list directly. Do not re-add them without a coverage case. The **graph-producer** (roles → MI graph) is **live as Step 5.5** (YED-149, 2026-09-27 — shipped once the Roles DB proved its dedup: 203 rows, 0 duplicate ATS keys). Scheduled ingestion stays deferred.
 
 ---
 
@@ -210,6 +210,37 @@ End with: **"Add which roles to the Roles DB? (A-tier / all / numbers / none)"**
 
 ---
 
+## Step 5.5 — Mirror the written roles into the MI graph (YED-149)
+
+Every Roles row written or re-keyed in Step 5 becomes one `role_posted` event in the graph, plus a `company —subject→`
+edge. Spec + the reasoning behind every rule: `.claude/notes/yed-149-spec-2026-09-27.md`. Runs inline in this thread
+(REST through `spine_client`; never the Supabase MCP). Additive, never a gate: if `SUPABASE_API_KEY` is unset, print
+`graph write skipped: SUPABASE_API_KEY not set` in Step 6 and stop here.
+
+1. **Pull the rows just written, SQL shape.** `notion-query-data-sources` on the Roles data source, selecting
+   `url, "Role Title", "Company", "Content Hash", "ICP Tier", "ICP Score", "date:Posted Date:start", "Source",
+   "userDefined:URL", "Status", "Location", "Workplace"` and filtering to this run's pages. **Never select `Notes`**:
+   Alex's free text stays in Notion.
+2. **Write them to a scratch file** as `{"roles": [<rows verbatim>]}` (in the session scratchpad, never the repo).
+3. **Dry-run, then live:**
+   `.venv/bin/python .claude/scripts/substrate.py ensure-roles --manifest <file> --aliases-from .claude/references/target-companies.md --dry-run`,
+   then the same without `--dry-run`. `--aliases-from` maps board slugs and registry names (`claylabs`, `cursor`) to
+   the name the graph already uses (`Clay`, `Cursor (Anysphere)`). Read the dry run's `would create N companies:`
+   line first. A listed company that already exists in the graph under another name (e.g. `Modal` vs `Modal Labs`)
+   is a duplicate in the making: add `"company_aliases": {"modal": "Modal Labs"}` to the manifest (or fix the
+   registry name), re-run the dry run, and only then write. A `REFUSED <ats key>` line means the same posting sits
+   on two Notion pages; resolve that in Notion.
+4. **Rules the verb enforces (don't re-implement them):** the Roles page id is the only idempotency key (a rescan
+   creates 0; a missing page id is refused); ICP Tier `drop` is skipped and counted; Greenhouse rows get no
+   `event_date`; `confidence = 1.0`; topics are never minted from this path.
+5. Step 6 summary line: `Graph: N role events (created X · matched Y · skipped drop Z)`.
+
+What the graph does with them: `/event-deep-research`'s Context Pack **never lists roles in the ledger**. A seed
+company gets one count line instead ("Harvey — 6 tracked roles (A:2 B:4)"), and applications/interviews appear
+nowhere (migration 0011 + `retrieve.py`).
+
+---
+
 ## Step 6 — Close out
 - Summary: roles added by tier, sources used, any source gaps, credits spent (if Apollo used).
 - **Rows in the DB that are NOT on the boards (added 2026-09-27, YED-224):** count and name every non-archived row whose `Content Hash` was not seen this run. Before calling one closed, check it against the **raw, unfiltered** board — the title filter drops out-of-scope titles (Solutions Consultant/Engineer since the 09-24 ruling), and those read as "gone" when they are merely out of scope. Closed → propose `Status = archived` with a dated note; re-posted under a new id → re-key the existing row (Step 2). Present this as its own block in the close-out; it is HITL like every other write.
@@ -231,5 +262,5 @@ End with: **"Add which roles to the Roles DB? (A-tier / all / numbers / none)"**
 - **`.claude/references/target-companies.md`** — the target-company list + company→ATS registry (board tokens).
 - `alex:lead-prioritization`, `alex:firmographic-analysis` — fit-scoring discipline.
 - Notion DBs — **Roles `collection://3a174257-e90b-48be-b4bb-097ba5dc4231`** (this skill's tracking Kanban); Companies `collection://d5910dc3-8327-4b49-9294-fc9499709a98`, People `collection://4a1af67f-9141-4ba5-aa9d-88b07dcd5f86` (for later relations).
-- Graph-producer (deferred v1.1): `trend-radar/SKILL.md` Step 5.5 pattern + `.claude/references/market-intel-spine.md`.
+- Graph-producer (Step 5.5): `substrate.py ensure-roles` · spec `.claude/notes/yed-149-spec-2026-09-27.md` · `.claude/references/market-intel-spine.md`.
 - Tools — `curl` + `jq` (ATS boards), `mcp__claude_ai_Apollo_io__apollo_organizations_job_postings` (optional), `notion-search`/`notion-fetch`/`notion-create-database`/`notion-create-pages`/`notion-update-page`.
diff --git a/supabase/migrations/0011_job_lens_isolation.sql b/supabase/migrations/0011_job_lens_isolation.sql
new file mode 100644
index 0000000..8f7d317
--- /dev/null
+++ b/supabase/migrations/0011_job_lens_isolation.sql
@@ -0,0 +1,92 @@
+-- =====================================================================
+-- 0011 — YED-149: isolate the job lens from the event lens. ADDITIVE (one function, re-defined).
+--
+-- Apply AFTER 0010. Prod by Alex's SQL-Editor paste (DDL via MCP is declined). Re-runnable:
+-- `create or replace`, identical signature, so callers (retrieve.py) need no change to keep working.
+-- Spec: .claude/notes/yed-149-spec-2026-09-27.md decision 5.
+--
+-- Why: role-radar now writes `role_posted` events (hundreds, freshly dated). entity_neighborhood
+-- ordered ALL kinds by event_date desc under `limit max_events`, so roles at a seed company would
+-- crowd attended/market history out of every /event-deep-research Context Pack — and a future
+-- `application`/`interview` row would surface in a brief. Two changes:
+--   1. `ev` excludes the job-lens kinds (role_posted, application, interview) BEFORE the limit;
+--   2. a new `hiring` key: one count row per SEED company (role_posted only — never applications
+--      or interviews; archived roles excluded), with ICP-tier split and the latest posted date.
+--      Counts, not titles.
+-- Everything else is byte-for-byte 0010.
+-- =====================================================================
+begin;
+
+create or replace function public.entity_neighborhood (
+  seed_ids    uuid[],
+  since       timestamptz default null,
+  max_events  int default 60,
+  max_claims  int default 120,
+  max_docs    int default 40
+)
+returns jsonb language sql stable as $$
+  with ev as (
+    select distinct e.id, e.title, e.kind, e.event_date, e.source, e.url, e.confidence
+    from public.event e join public.event_entity ee on ee.event_id = e.id
+    where ee.entity_id = any(seed_ids) and (since is null or e.event_date >= since)
+      and e.kind <> all (array['role_posted', 'application', 'interview'])
+    order by e.event_date desc nulls last limit max_events
+  ),
+  co as (
+    select ee.event_id, ee.entity_type, ee.entity_id, ee.role,
+           coalesce(c.name, p.name, t.name) as name
+    from public.event_entity ee
+    left join public.company c on c.id = ee.entity_id and ee.entity_type = 'company'
+    left join public.person  p on p.id = ee.entity_id and ee.entity_type = 'person'
+    left join public.topic   t on t.id = ee.entity_id and ee.entity_type = 'topic'
+    where ee.event_id in (select id from ev)
+  ),
+  docs as (
+    select distinct d.id, d.title, d.source_type, d.doc_date, d.external_ref, d.event_id
+    from public.documents d
+    left join public.document_entity de on de.document_id = d.id
+    where d.is_current and (de.entity_id = any(seed_ids) or d.event_id in (select id from ev))
+    order by d.doc_date desc nulls last limit max_docs
+  ),
+  cl as (
+    select distinct c.id, c.claim_text, c.claim_type, c.provenance_tier, c.confidence, c.status,
+           c.event_id, c.document_id, c.asserted_at, c.metadata
+    from public.claim c
+    left join public.claim_entity ce on ce.claim_id = c.id
+    where c.status in ('approved', 'candidate')
+      and (ce.entity_id = any(seed_ids) or c.event_id in (select id from ev))
+    order by c.asserted_at desc nulls last limit max_claims
+  ),
+  hiring as (
+    select c.id as company_id, c.name, count(distinct e.id) as roles,
+           count(distinct e.id) filter (where e.metadata->>'icp_tier' = 'A') as tier_a,
+           count(distinct e.id) filter (where e.metadata->>'icp_tier' = 'B') as tier_b,
+           count(distinct e.id) filter (where e.metadata->>'icp_tier' = 'C') as tier_c,
+           max(e.event_date) as latest_posted
+    from public.event e
+    join public.event_entity ee on ee.event_id = e.id and ee.entity_type = 'company'
+    join public.company c on c.id = ee.entity_id
+    where ee.entity_id = any(seed_ids) and e.kind = 'role_posted'
+      and coalesce(e.metadata->>'status', '') <> 'archived'   -- archived in Notion = closed or not pursued
+    group by c.id, c.name
+  )
+  select jsonb_build_object(
+    'events',    (select coalesce(jsonb_agg(to_jsonb(ev)),     '[]'::jsonb) from ev),
+    'edges',     (select coalesce(jsonb_agg(to_jsonb(co)),     '[]'::jsonb) from co),
+    'documents', (select coalesce(jsonb_agg(to_jsonb(docs)),   '[]'::jsonb) from docs),
+    'claims',    (select coalesce(jsonb_agg(to_jsonb(cl)),     '[]'::jsonb) from cl),
+    'hiring',    (select coalesce(jsonb_agg(to_jsonb(hiring)), '[]'::jsonb) from hiring)
+  );
+$$;
+alter function public.entity_neighborhood(uuid[], timestamptz, int, int, int) set search_path = public;
+
+commit;
+
+-- ============================ VERIFY ============================
+-- the new key is present (empty array until role_posted rows exist):
+-- select public.entity_neighborhood(array[(select id from public.company limit 1)]) ? 'hiring';
+-- no job-lens kind can reach `events` (expect 0):
+-- select count(*) from jsonb_array_elements(
+--   public.entity_neighborhood(array(select entity_id from public.event_entity ee join public.event e
+--     on e.id = ee.event_id where e.kind = 'role_posted' and ee.entity_type = 'company'))->'events') x
+--   where x->>'kind' in ('role_posted', 'application', 'interview');
```
