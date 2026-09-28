# YED-236 — keep gitignored private files out of the public System Map (two repos)

## Purpose
The pipeline's ADR-8 system graph (build_graph.py) feeds the public hub's System Map (gen-system-map.mjs -> src/data/system-map.files.json, served publicly). Building the graph from a working checkout indexed gitignored private files (.claude/references/me-model.md, target-companies.md, inbox-allowlist.md, inbox-denylist.md), which leaked their names into the public data. Fix = defense in depth: (1) pipeline source: never index gitignored files; ignored reference targets count as absent; (2) hub boundary: generator drops any gitignored path and fails closed if the check can't run; verifier (in pnpm check) fails on any gitignored path, skips with a note where no pipeline checkout exists (Vercel build).

## Pipeline diff (Empire_State_Events_Pipeline_Take_3, PR #146)
```diff
diff --git a/.claude/scripts/build_graph.py b/.claude/scripts/build_graph.py
index a52d801..f5def67 100755
--- a/.claude/scripts/build_graph.py
+++ b/.claude/scripts/build_graph.py
@@ -209,7 +209,13 @@ def walk_artifacts():
                     rels.append(os.path.relpath(os.path.join(dirpath, fn), ROOT))
     if os.path.isfile(os.path.join(ROOT, "CLAUDE.md")):
         rels.append("CLAUDE.md")
-    return sorted(set(r.replace(os.sep, "/") for r in rels))
+    rels = sorted(set(r.replace(os.sep, "/") for r in rels))
+    # YED-236: never index a gitignored file. The graph feeds the PUBLIC hub's System Map; indexing
+    # what's on disk leaked private, deliberately-untracked files (me-model, target-companies, the
+    # inbox lists) into it whenever the graph was built from a working checkout. The graph must be
+    # the same whether it's built from a clean clone or from Alex's checkout.
+    ignored = gitignored(rels)
+    return [r for r in rels if r not in ignored]
 def adr_status(text: str):
     """The whole Status LINE, not its first word. Two reasons, both found the hard way: the first
     word is often a bold marker (`**Accepted`), which the old word-capture missed entirely; and an
@@ -272,7 +278,9 @@ def build():
             exists, norm = os.path.exists(os.path.expanduser(path)), None
         else:
             norm = path[2:] if path.startswith("./") else path
-            exists = os.path.exists(os.path.join(ROOT, norm))
+            # YED-236: a gitignored target counts as absent, so a local build matches a clean clone
+            # (and the private file's existence never reaches the public graph).
+            exists = os.path.exists(os.path.join(ROOT, norm)) and norm not in ignored
         subtype = nodes.get(src, {}).get("subtype")
         src_is_proposed = subtype == "proposal" or adr_proposed.get(src, False)
 
```

## Hub diff (empire-state-hub, PR #24)
```diff
diff --git a/scripts/gen-system-map.mjs b/scripts/gen-system-map.mjs
index fbb639a..f899fd6 100644
--- a/scripts/gen-system-map.mjs
+++ b/scripts/gen-system-map.mjs
@@ -208,6 +208,21 @@ function matcher(pattern) {
   return (id) => id === pattern;
 }
 
+// YED-236: which of these repo paths are gitignored in the pipeline repo? Exits the generator on any git
+// failure — a privacy check that can't run must not publish (fail closed).
+function gitIgnored(paths) {
+  const repoPaths = [...new Set(paths.filter((p) => p && !p.startsWith("~") && !p.startsWith("/")))];
+  if (!repoPaths.length) return new Set();
+  try {
+    const out = execFileSync("git", ["-C", PIPELINE_DIR, "check-ignore", "--stdin"], { input: repoPaths.join("\n"), encoding: "utf8" });
+    return new Set(out.split("\n").map((s) => s.trim()).filter(Boolean));
+  } catch (e) {
+    if (e.status === 1) return new Set(); // git check-ignore exits 1 when nothing matched
+    console.error(`✗ privacy guard: git check-ignore failed in ${PIPELINE_DIR} — refusing to publish (YED-236)`);
+    process.exit(1);
+  }
+}
+
 function main() {
   if (!existsSync(join(GRAPH_DIR, "nodes.jsonl"))) {
     console.error(
@@ -218,8 +233,14 @@ function main() {
   const curated = JSON.parse(readFileSync(CURATED, "utf8"));
   let prev = { components: [], buildPath: { items: [] } };
   try { prev = JSON.parse(readFileSync(OUT, "utf8")); } catch { /* first run */ }
-  const nodes = readJsonl(join(GRAPH_DIR, "nodes.jsonl")).filter((n) => n.exists !== false);
-  const edges = readJsonl(join(GRAPH_DIR, "edges.jsonl")).filter((e) => e.exists !== false);
+  const rawNodes = readJsonl(join(GRAPH_DIR, "nodes.jsonl")).filter((n) => n.exists !== false);
+  const rawEdges = readJsonl(join(GRAPH_DIR, "edges.jsonl")).filter((e) => e.exists !== false);
+  // YED-236 privacy guard (fail-closed): nothing gitignored in the pipeline repo may reach the public map,
+  // even if the graph was built from a working checkout that holds private, untracked files.
+  const ignored = gitIgnored([...rawNodes.map((n) => n.id), ...rawEdges.flatMap((e) => [e.src, e.dst])]);
+  const nodes = rawNodes.filter((n) => !ignored.has(n.id));
+  const edges = rawEdges.filter((e) => !ignored.has(e.src) && !ignored.has(e.dst));
+  if (ignored.size) console.log(`  ! privacy guard: dropped ${ignored.size} gitignored path(s) from the public map`);
   const meta = existsSync(join(GRAPH_DIR, "meta.json")) ? JSON.parse(readFileSync(join(GRAPH_DIR, "meta.json"), "utf8")) : {};
   const nodeIds = nodes.map((n) => n.id);
   const { first, last, sha } = gitDates();
diff --git a/scripts/verify-system-map.mjs b/scripts/verify-system-map.mjs
index ecc6b2a..1de201a 100644
--- a/scripts/verify-system-map.mjs
+++ b/scripts/verify-system-map.mjs
@@ -4,7 +4,9 @@
 // Warns (does not fail) on overlay entries whose files changed after they were last reviewed — the
 // rot signal the topic-intelligence incident taught us to surface, not hide.
 // Run: node scripts/verify-system-map.mjs   (wired into `pnpm check`)
-import { readFileSync } from "node:fs";
+import { readFileSync, existsSync } from "node:fs";
+import { join } from "node:path";
+import { execFileSync } from "node:child_process";
 
 const ROOT = new URL("..", import.meta.url).pathname;
 const map = JSON.parse(readFileSync(`${ROOT}src/data/system-map.json`, "utf8"));
@@ -31,6 +33,27 @@ if (!map.buildPath.anchors.length) problems.push("no anchors parsed from roadmap
 // unreconciled state (the YED-226 defect the judge caught on 2026-09-27) — refuse it.
 for (const it of curated.buildPath.items) if (/\bP[0-3]\b|\(P[0-3]\)|Phase [0-3]/.test(it.why)) problems.push(`${it.issue}: phase tag written in prose ("${it.why.match(/\(?P[0-3]\)?|Phase [0-3]/)[0]}") — the generator derives phase from roadmap.md; remove it`);
 
+// YED-236: no path in the public files map may be gitignored in the pipeline repo. Runs wherever the
+// pipeline checkout is present (every local generate); skipped with a note where it isn't (Vercel build).
+let privacyNote = "";
+const PIPELINE_DIR = process.env.PIPELINE_DIR || join(ROOT, "..", "Empire_State_Events_Pipeline_Take_3");
+if (existsSync(join(PIPELINE_DIR, ".git"))) {
+  const files = JSON.parse(readFileSync(`${ROOT}src/data/system-map.files.json`, "utf8"));
+  const paths = [...new Set([...files.nodes.map((n) => n.id), ...files.edges.flatMap((e) => [e.src, e.dst])])]
+    .filter((p) => p && !p.startsWith("~") && !p.startsWith("/"));
+  let hits = [];
+  try {
+    hits = execFileSync("git", ["-C", PIPELINE_DIR, "check-ignore", "--stdin"], { input: paths.join("\n"), encoding: "utf8" })
+      .split("\n").map((s) => s.trim()).filter(Boolean);
+  } catch (e) {
+    if (e.status !== 1) problems.push(`privacy check could not run (git check-ignore failed in ${PIPELINE_DIR})`);
+  }
+  for (const h of hits) problems.push(`privacy: ${h} is gitignored in the pipeline repo but appears in system-map.files.json (YED-236)`);
+  privacyNote = ` · privacy ✓ (${paths.length} paths)`;
+} else {
+  privacyNote = " · privacy check skipped (no pipeline checkout)";
+}
+
 const stale = map.components.filter((c) => c.overlayStale).map((c) => c.id);
 
 if (problems.length) {
@@ -38,5 +61,5 @@ if (problems.length) {
   for (const p of problems) console.log("  " + p);
   process.exit(1);
 }
-console.log(`✓ verify-system-map: ${map.components.length} components · ${map.edges.length} edges · ${map.buildPath.items.length} planned · anchors ${map.buildPath.anchors.map((a) => a.id).join(",")}`);
+console.log(`✓ verify-system-map: ${map.components.length} components · ${map.edges.length} edges · ${map.buildPath.items.length} planned · anchors ${map.buildPath.anchors.map((a) => a.id).join(",")}${privacyNote}`);
 if (stale.length) console.log(`  ! ${stale.length} curated entr${stale.length === 1 ? "y" : "ies"} may lag the code (files changed after reviewed_at): ${stale.join(", ")}`);
```

## Test evidence (run 2026-09-27, author-reported)
- Patched build_graph on the dirty main checkout: 322 artifacts / 906 refs / 96 classified dangling — identical to a clean worktree; same 4 actionable dangling refs; 0 private nodes; 18 edges to private files now exists=false.
- Leaky graph (old script, dirty checkout) -> generator: 'privacy guard: dropped 17 gitignored path(s)'; 0 private names in output.
- Planted .claude/references/me-model.md node in files.json -> verify-system-map exit 1 naming the file.
- Clean run -> output identical to prior generation except graph_built_at; 'privacy ✓ (390 paths)'.
