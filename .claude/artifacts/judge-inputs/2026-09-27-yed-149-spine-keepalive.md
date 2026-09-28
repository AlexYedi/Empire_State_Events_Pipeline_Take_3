# YED-149 follow-up — spine_client keep-alive + NotSent retry, substrate read-cache scoping

## Purpose
Measured (Fable diagnosis): ~10% of FRESH TCP connects from this network stall on SYN (all hosts). spine_client opened one urllib connection per call, so a 455-call dry run took ~24 min (93% stalls). Change: retry-safe calls (GET, set-PATCH, upsert POST) reuse one keep-alive http.client connection (connect timeout 10s; a dropped connection is closed and rebuilt by the retry loop). Non-retryable calls (plain insert, /rpc/) keep a fresh connection per call, because a reused socket dying mid-send leaves it unknowable whether the insert landed. A failure during connect() raises NotSent: nothing left the machine, so it is retried for ANY method. substrate Graph read-cache now invalidates only the written table, only on real (non-dry) writes. spine_client is the single guarded write path (ADR-9); the PII guard and freeze checks run before _send and are untouched.

## Verification run
- spine_client --selftest 39/39 (retry case now stubs _send; asserts plain POST uses a fresh connection, fails on the 1st non-NotSent stall, and is retried on NotSent) · --check-writers 0 · substrate --selftest 145/145
- Live: dry run 24 min -> 48.8s; live backfill: first run died on a plain POST connect timeout (pre-NotSent), resumed run hit one NotSent on POST /company and retried successfully; idempotent re-run created 0 in 6.5s; integrity query: 174 rows, 0 dup ATS keys, 0 dup page ids, 174/174 company edges, 0 duplicate company names.

## Diff
```diff
diff --git a/.claude/scripts/spine_client.py b/.claude/scripts/spine_client.py
index af25b31..4c3c141 100755
--- a/.claude/scripts/spine_client.py
+++ b/.claude/scripts/spine_client.py
@@ -321,6 +321,61 @@
 REQ_BACKOFF = (1.0, 3.0)         # seconds before attempt 2, 3
 _TRANSIENT = (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException)
 
+# Persistent connection (YED-149 diagnosis, 2026-09-27, measured): ~10% of FRESH TCP connects from Alex's network
+# hang on the SYN — to every host, not just Supabase — and each hang cost the full 30s timeout. One urllib connection
+# per call turned a 200-role dry run (455 calls) into ~24 min, 93% of it stalls; over one reused connection the same
+# calls took 65s with 0 stalls. So retry-safe calls (GET / set-PATCH / upsert) reuse ONE keep-alive connection, and a
+# dropped one is closed and rebuilt by the retry loop. A NON-retryable call (plain insert, /rpc/) always gets its own
+# fresh connection, exactly as before: if a reused socket died mid-send we could not know whether the insert landed.
+CONNECT_TIMEOUT = 10             # a stalled SYN now costs 10s once, not 30s per call
+
+
+class NotSent(ConnectionError):
+    """The connection never opened, so not one byte of the request left this machine. Retrying is safe for ANY
+    method, including a plain insert: nothing can have landed (first live backfill died on exactly this, 2026-09-27)."""
+_CONN: http.client.HTTPSConnection | None = None
+
+
+def _drop_conn() -> None:
+    global _CONN
+    if _CONN is not None:
+        try:
+            _CONN.close()
+        except Exception:
+            pass
+    _CONN = None
+
+
+def _send(method: str, path: str, data, headers: dict, timeout: int, reuse: bool) -> tuple[int, str]:
+    """One HTTP exchange -> (status, body text). Raises a _TRANSIENT error when there is no answer at all.
+    The only socket code in this file; --selftest stubs it."""
+    global _CONN
+    host = f"{REF}.supabase.co"
+    conn = _CONN if reuse else None
+    if conn is None:
+        conn = http.client.HTTPSConnection(host, 443, timeout=min(timeout, CONNECT_TIMEOUT))
+        try:
+            conn.connect()
+        except _TRANSIENT as e:
+            conn.close()
+            raise NotSent(f"connect failed before sending: {type(e).__name__}: {e}") from e
+        if reuse:
+            _CONN = conn
+    conn.sock.settimeout(timeout)
+    try:
+        conn.request(method, "/rest/v1" + path, body=data, headers=headers)
+        resp = conn.getresponse()
+        return resp.status, resp.read().decode()
+    except Exception:
+        if reuse:
+            _drop_conn()
+        else:
+            conn.close()
+        raise
+    finally:
+        if not reuse:
+            conn.close()
+
 
 def _retryable(method: str, path: str, prefer: str | None) -> bool:
     """Idempotent-by-construction only: GET, PATCH (set-to-value), and upsert POSTs (`resolution=` in Prefer).
@@ -347,21 +402,22 @@
     if extra_headers:
         headers.update(extra_headers)
     data = json.dumps(body).encode() if body is not None else None
-    attempts = REQ_RETRIES if _retryable(method, path, prefer) else 1
+    retryable = _retryable(method, path, prefer)
+    attempts = REQ_RETRIES           # a non-retryable call still retries a NotSent failure (see NotSent), nothing else
     for attempt in range(1, attempts + 1):
-        r = urllib.request.Request(BASE + path, data=data, method=method, headers=headers)
         try:
-            with urllib.request.urlopen(r, timeout=timeout) as resp:
-                txt = resp.read().decode()
-                return resp.status, (json.loads(txt) if txt else None)
-        except urllib.error.HTTPError as e:            # a real HTTP answer: never retried (subclass of URLError)
-            txt = e.read().decode()
-            if raise_on_error:
-                raise RuntimeError(f"Supabase {method} {path} -> {e.code}: {txt[:500]}")
-            return e.code, txt
+            code, txt = _send(method, path, data, headers, timeout, reuse=retryable)
+            if code >= 400:                            # a real HTTP answer: never retried
+                if raise_on_error:
+                    raise RuntimeError(f"Supabase {method} {path} -> {code}: {txt[:500]}")
+                return code, txt
+            return code, (json.loads(txt) if txt else None)
         except _TRANSIENT as e:                        # no answer at all: stall / reset / dropped socket
+            made = attempt
+            if not retryable and not isinstance(e, NotSent):
+                attempt = attempts                     # may have landed: fail loud on the first stall, as before
             if attempt >= attempts:
-                sys.stderr.write(f"req: gave up after {attempts} attempt(s) on {method} {path[:90]} — {type(e).__name__}: "
+                sys.stderr.write(f"req: gave up after {made} attempt(s) on {method} {path[:90]} — {type(e).__name__}: "
                                  f"{str(e)[:120]}. Nothing after this call ran; a re-run is idempotent (upserts "
                                  f"and GETs), and any gate row stays PENDING until it succeeds.\n")
                 raise
@@ -493,21 +549,16 @@
         g = globals()
         calls = {"n": 0}
 
-        class _Resp:
-            status = 200
-            def read(self): return b"[]"
-            def __enter__(self): return self
-            def __exit__(self, *a): return False
-
-        def fake_urlopen(r, timeout=None):
+        def fake_send(method, path, data, headers, timeout, reuse):
             calls["n"] += 1
+            calls.setdefault("reuse", []).append(reuse)
             if calls["n"] < 3:
-                raise urllib.error.URLError("timed out")
-            return _Resp()
+                raise NotSent("connect failed") if calls.get("notsent") else urllib.error.URLError("timed out")
+            return 200, "[]"
         # The freeze cases below arm a TEMP "active" marker at registration time, so a write-path call here
         # would be refused at the door before it reaches the stubbed socket — same escape as `_absent()`.
-        saved = (g["REQ_BACKOFF"], urllib.request.urlopen, g["load_key"], g["FREEZE_PATH"])
-        g["REQ_BACKOFF"], urllib.request.urlopen, g["load_key"] = (0, 0), fake_urlopen, (lambda: "test-key")
+        saved = (g["REQ_BACKOFF"], g["_send"], g["load_key"], g["FREEZE_PATH"])
+        g["REQ_BACKOFF"], g["_send"], g["load_key"] = (0, 0), fake_send, (lambda: "test-key")
         g["FREEZE_PATH"] = os.path.join(ROOT, "__no_such_freeze__.json")
         try:
             st, body = req("GET", "/person?select=id&limit=1")
@@ -532,9 +583,17 @@
             except urllib.error.URLError:
                 if calls["n"] != 1:
                     raise PIIViolation(f"plain POST made {calls['n']} calls")
+                if calls["reuse"][-1] is not False:
+                    raise PIIViolation("plain POST went over the shared keep-alive connection")
+            # ...but a plain POST whose connection never opened IS retried: nothing was sent.
+            calls["n"], calls["notsent"] = 0, True
+            st, _ = req("POST", "/person", [{"name": "Plain Insert"}], prefer="return=representation")
+            if not (st == 200 and calls["n"] == 3):
+                raise PIIViolation(f"NotSent plain POST not retried: calls={calls['n']}")
         finally:
-            g["REQ_BACKOFF"], urllib.request.urlopen, g["load_key"], g["FREEZE_PATH"] = saved
-    add("retry loop: 2 stalls then success on GET; plain POST fails on the 1st stall", _retry_loop_case, False)
+            g["REQ_BACKOFF"], g["_send"], g["load_key"], g["FREEZE_PATH"] = saved
+    add("retry loop: 2 stalls then success on GET; plain POST fails on the 1st stall unless nothing was sent",
+        _retry_loop_case, False)
     add("prose scan catches `POST /doc_claims`",
         lambda: None if _PROSE_VERB_RE.search("then `POST /doc_claims` with") else (_ for _ in ()).throw(PIIViolation("miss")), False)
 
diff --git a/.claude/scripts/substrate.py b/.claude/scripts/substrate.py
index 03a77b7..ea86028 100644
--- a/.claude/scripts/substrate.py
+++ b/.claude/scripts/substrate.py
@@ -741,6 +741,7 @@
 
     def _remember(self, table: str, name: str, rid: str) -> str:
         self._made[(table, norm_text(name))] = rid
+        self._made_names = getattr(self, "_made_names", []) + [(table, name)]   # display casing, for review output
         return rid
 
     def embed(self, texts: list[str]) -> list[str]:
@@ -752,6 +753,13 @@
         from dockb_common import embed_passages, vec_literal
         return [vec_literal(v) for v in embed_passages(texts)]
 
+    def _invalidate(self, table: str) -> None:
+        """Drop only the written table's cached reads (a company write can't change an event read)."""
+        cache = getattr(self, "_rcache", None)
+        if cache:
+            for k in [k for k in cache if k.startswith(f"/{table}?")]:
+                del cache[k]
+
     def get(self, path: str) -> list:
         cache = getattr(self, "_rcache", None)      # opt-in per-run read cache (ensure-roles); writes clear it
         if cache is not None and path in cache:
@@ -767,11 +775,10 @@
         rows = row if isinstance(row, list) else [row]
         for r in rows:
             guard(table, r)                                          # fail before any network call
-        if getattr(self, "_rcache", None):
-            self._rcache.clear()
         if self.dry:
             self._n += 1
             return [{**r, "id": r.get("id") or f"dry:{table}:{self._n}:{i}"} for i, r in enumerate(rows)]
+        self._invalidate(table)                   # after the dry return: a dry write changes nothing server-side
         path = f"/{table}" + (f"?on_conflict={on_conflict}" if on_conflict else "")
         st, body = req("POST", path, rows, prefer=prefer)
         if st not in (200, 201):
@@ -780,10 +787,9 @@
 
     def patch(self, table: str, flt: str, row: dict):
         guard(table, row, op="update")
-        if getattr(self, "_rcache", None):
-            self._rcache.clear()
         if self.dry:
             return
+        self._invalidate(table)
         st, body = req("PATCH", f"/{table}?{flt}", row, prefer="return=minimal")
         if st not in (200, 204):
             raise SystemExit(f"PATCH /{table}?{flt} -> {st}: {str(body)[:400]}")
@@ -1533,8 +1539,15 @@
         edged |= {x["event_id"] for x in g.get(f"/event_entity?entity_type=eq.company&event_id=in.({','.join(ids[i:i + 80])})"
                                                f"&select=event_id")}
     by_ats = {(e.get("metadata") or {}).get("ats_key"): pid for pid, e in existing.items()}
-    for r in rows:
+    refused = 0
+    for n, r in enumerate(rows, 1):
+        if n % 50 == 0 or n == len(rows):
+            print(f"  … {n}/{len(rows)} roles", flush=True)
         m, why = role_manifest(r, aliases)
+        if why == "no_page_id":                  # spec decision 1: a hard failure, not a quiet skip
+            print(f"REFUSED no page id: {r.get('Role Title')!r} at {r.get('Company')!r} (url={r.get('url')!r})")
+            refused += 1
+            continue
         if why:
             skipped[why] = skipped.get(why, 0) + 1
             continue
@@ -1555,9 +1568,13 @@
     g.stats.bump("role", "input", len(rows))
     for why, n in skipped.items():
         g.stats.bump("role", f"skipped_{why}", n)
-    new_cos = sorted(n for (t, n) in g._made if t == "company")
+    new_cos = sorted(n for (t, n) in getattr(g, "_made_names", []) if t == "company")
     if new_cos:   # the review surface: a would-create company that already exists under another name is a duplicate
         print(f"{'would create' if g.dry else 'created'} {len(new_cos)} companies: {', '.join(new_cos)}")
+    if refused:
+        g.stats.bump("role", "refused_no_page_id", refused)
+        print(f"ensure-roles: {refused} row(s) REFUSED for a missing/invalid page id — every other row was processed; exit 3")
+        return 3
     return 0
 
 
@@ -1991,6 +2008,8 @@
     ok("roles: role_posted without a page id -> refused", refused)
     fg.stats = Stats()
     ensure_roles(fg, [row("9", "Account Executive", "Harvey", "ashby:10")])   # ashby:10 already lives on page 1…
+    ok("roles: a row with no page id fails the run (exit 3), nothing written for it",
+       ensure_roles(fg, [{**row("x", "AE", "Harvey", "ashby:99"), "url": "not-a-page"}]) == 3)
     ok("roles: same ATS key on a different page id -> refused, nothing written",
        fg.stats.c["role"].get("skipped_ats_key_on_other_page") == 1 and fg.stats.created() == 0)
     fg.ensure_event({"event": {**role_manifest(row("6", "CSM", "Harvey", "ashby:15"))[0]["event"]},
@@ -2431,6 +2450,7 @@
         aliases = {} if isinstance(m, list) else dict(m.get("company_aliases", {}))
         if a.aliases_from:                         # the local target-company registry (gitignored; path passed in)
             aliases = {**registry_aliases(open(a.aliases_from, encoding="utf-8").read(), g), **aliases}
+            print(f"  aliases: {len(aliases)} names/slugs resolved against the graph", flush=True)
         rc = ensure_roles(g, m if isinstance(m, list) else m.get("roles", []), aliases)
         print(("DRY-RUN " if a.dry_run else "") + f"ensure-roles: created={stats.created()}")
         print(stats.report())
```
